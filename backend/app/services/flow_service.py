"""
模块用途: 流程定义草稿与快照管理服务
依赖配置: 无
数据流向: API -> FlowService -> FlowDraft/FlowSnapshot
函数清单:
    - FlowService.get_definition_detail(): 获取流程详情
    - FlowService.get_draft(): 查询草稿
    - FlowService.save_draft(): 保存草稿（乐观锁）
    - FlowService.publish_flow(): 发布流程（生成快照）
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, NotFoundError
from app.models.workflow import FlowDefinition, FlowDraft, FlowSnapshot, FlowNode, FlowRoute
from app.schemas.flow_schemas import (
    FlowDefinitionDetailResponse,
    FlowDefinitionResponse,
    FlowDraftResponse,
    FlowDraftSaveRequest,
    FlowPublishRequest,
    FlowRouteConfig,
    FlowSnapshotResponse,
    FlowNodeConfig,
)
from app.utils.audit import create_audit_log_sync

logger = logging.getLogger(__name__)


class FlowService:
    """流程定义草稿与快照服务。"""

    @staticmethod
    def get_definition_detail(
        flow_definition_id: int,
        tenant_id: int,
        db: Session,
    ) -> FlowDefinitionDetailResponse:
        """获取流程定义详情（含草稿、快照）。

        :param flow_definition_id: 流程定义 ID
        :param tenant_id: 租户 ID
        :param db: 会话
        :return: 详情响应

        Time: O(N), Space: O(N)
        """

        definition = FlowService._get_flow_definition(flow_definition_id, tenant_id, db)
        draft = FlowService._get_draft_model(flow_definition_id, tenant_id, db)
        snapshots = FlowService._list_snapshots(flow_definition_id, tenant_id, db)
        active_snapshot = None
        active_snapshot_tag = None
        if definition.active_snapshot_id:
            active_snapshot = next(
                (snap for snap in snapshots if snap.id == definition.active_snapshot_id),
                None,
            )
            active_snapshot_tag = active_snapshot.version_tag if active_snapshot else None

        response = FlowDefinitionDetailResponse(
            definition=FlowDefinitionResponse(
                id=definition.id,
                form_id=definition.form_id,
                name=definition.name,
                version=definition.version,
                active_snapshot_id=definition.active_snapshot_id,
                active_snapshot_tag=active_snapshot_tag,
                created_at=definition.created_at,
                updated_at=definition.updated_at,
            ),
            draft=FlowService._build_draft_response(draft) if draft else None,
            active_snapshot=FlowSnapshotResponse.from_orm(active_snapshot)
            if active_snapshot
            else None,
            snapshots=[FlowSnapshotResponse.from_orm(item) for item in snapshots],
        )
        return response

    @staticmethod
    def get_draft(
        flow_definition_id: int,
        tenant_id: int,
        db: Session,
    ) -> Optional[FlowDraftResponse]:
        """查询草稿。

        :return: 草稿响应或 None

        Time: O(1), Space: O(1)
        """

        draft = FlowService._get_draft_model(flow_definition_id, tenant_id, db)
        return FlowService._build_draft_response(draft) if draft else None

    @staticmethod
    def save_draft(
        request: FlowDraftSaveRequest,
        tenant_id: int,
        user_id: int,
        db: Session,
    ) -> FlowDraftResponse:
        """保存草稿，使用乐观锁控制版本。

        :raises BusinessError: 乐观锁冲突或参数异常

        Time: O(1), Space: O(1)
        """

        definition = FlowService._get_flow_definition(request.flow_definition_id, tenant_id, db)
        draft = FlowService._get_draft_model(definition.id, tenant_id, db)

        if not request.nodes:
            raise BusinessError("流程至少需要一个节点")

        payload = request.model_dump()

        if draft:
            if request.version != draft.version:
                raise BusinessError("草稿版本已变更，请刷新后重试")
            draft.version += 1
        else:
            draft = FlowDraft(
                tenant_id=tenant_id,
                flow_definition_id=definition.id,
                version=1,
            )
            db.add(draft)

        draft.config_json = {
            "nodes": payload["nodes"],
            "routes": payload["routes"],
        }
        draft.nodes_graph = payload.get("nodes_graph") or {}
        draft.updated_by = user_id
        db.commit()
        db.refresh(draft)
        logger.info("保存流程草稿", extra={"flow_definition_id": definition.id, "draft_id": draft.id})
        return FlowService._build_draft_response(draft)

    @staticmethod
    def publish_flow(
        request: FlowPublishRequest,
        tenant_id: int,
        user_id: int,
        db: Session,
    ) -> FlowSnapshotResponse:
        """发布流程，生成不可变快照。

        :raises BusinessError: 草稿缺失或版本冲突

        Time: O(1), Space: O(1)
        """

        definition = FlowService._get_flow_definition(request.flow_definition_id, tenant_id, db)
        draft = FlowService._get_draft_model(definition.id, tenant_id, db)
        if not draft:
            raise BusinessError("请先保存草稿后再发布")
        if request.version != draft.version:
            raise BusinessError("草稿版本已变更，请刷新后再发布")

        config = draft.config_json or {}
        nodes = config.get("nodes", [])
        if not nodes:
            raise BusinessError("流程缺少节点，无法发布")

        new_version = definition.version + 1
        version_tag = request.version_tag or f"v{new_version}"

        snapshot = FlowSnapshot(
            tenant_id=tenant_id,
            flow_definition_id=definition.id,
            version_tag=version_tag,
            rules_payload=config,
            metadata_json={"changelog": request.changelog} if request.changelog else None,
            created_by=user_id,
        )
        db.add(snapshot)
        db.flush()

        definition.version = new_version
        definition.active_snapshot_id = snapshot.id
        draft.last_snapshot_id = snapshot.id

        FlowService._sync_nodes_and_routes(
            flow_definition_id=definition.id,
            tenant_id=tenant_id,
            nodes=nodes,
            routes=config.get("routes", []),
            db=db,
        )

        db.commit()
        db.refresh(snapshot)

        logger.info(
            "发布流程快照",
            extra={"flow_definition_id": definition.id, "snapshot_id": snapshot.id},
        )

        # 审计日志在事务提交后异步记录，避免阻塞响应
        try:
            create_audit_log_sync(
                actor_user_id=user_id,
                action="flow_publish",
                resource_type="flow",
                resource_id=definition.id,
                before_data=None,
                after_data={"snapshot_id": snapshot.id, "version_tag": snapshot.version_tag},
                tenant_id=tenant_id,
            )
        except Exception as exc:
            logger.warning(f"审计日志记录失败: {exc}")

        return FlowSnapshotResponse.from_orm(snapshot)

    # ---------------------------- 私有方法 ----------------------------
    @staticmethod
    def _get_flow_definition(flow_definition_id: int, tenant_id: int, db: Session) -> FlowDefinition:
        """查询流程定义。"""

        definition = (
            db.query(FlowDefinition)
            .filter(
                FlowDefinition.id == flow_definition_id,
                FlowDefinition.tenant_id == tenant_id,
            )
            .first()
        )
        if not definition:
            raise NotFoundError("流程定义不存在")
        return definition

    @staticmethod
    def _get_draft_model(flow_definition_id: int, tenant_id: int, db: Session) -> Optional[FlowDraft]:
        """查询草稿模型。"""

        return (
            db.query(FlowDraft)
            .filter(
                FlowDraft.flow_definition_id == flow_definition_id,
                FlowDraft.tenant_id == tenant_id,
            )
            .first()
        )

    @staticmethod
    def _list_snapshots(flow_definition_id: int, tenant_id: int, db: Session) -> List[FlowSnapshot]:
        """查询快照列表。"""

        return (
            db.query(FlowSnapshot)
            .filter(
                FlowSnapshot.flow_definition_id == flow_definition_id,
                FlowSnapshot.tenant_id == tenant_id,
            )
            .order_by(FlowSnapshot.created_at.desc())
            .all()
        )

    @staticmethod
    def _build_draft_response(draft: FlowDraft) -> FlowDraftResponse:
        """组装草稿响应。"""

        config: Dict[str, Any] = draft.config_json or {}
        nodes_data = config.get("nodes", [])
        routes_data = config.get("routes", [])
        nodes = [FlowNodeConfig(**item) for item in nodes_data]
        routes = [FlowRouteConfig(**item) for item in routes_data]
        return FlowDraftResponse(
            flow_definition_id=draft.flow_definition_id,
            version=draft.version,
            nodes=nodes,
            routes=routes,
            nodes_graph=draft.nodes_graph or {},
            updated_at=draft.updated_at,
            updated_by=draft.updated_by,
            last_snapshot_id=draft.last_snapshot_id,
        )

    @staticmethod
    def _sync_nodes_and_routes(
        flow_definition_id: int,
        tenant_id: int,
        nodes: List[Dict[str, Any]],
        routes: List[Dict[str, Any]],
        db: Session,
    ) -> None:
        """同步节点和路由到数据库表。

        发布流程时，将快照中的节点和路由配置同步到 flow_node 和 flow_route 表，
        以便 ProcessService 在运行时能够查询到这些配置。

        :param flow_definition_id: 流程定义 ID
        :param tenant_id: 租户 ID
        :param nodes: 节点配置列表
        :param routes: 路由配置列表
        :param db: 数据库会话

        Time: O(N+M), Space: O(N+M)
        """

        db.query(FlowRoute).filter(
            FlowRoute.flow_definition_id == flow_definition_id,
            FlowRoute.tenant_id == tenant_id,
        ).delete(synchronize_session=False)

        db.query(FlowNode).filter(
            FlowNode.flow_definition_id == flow_definition_id,
            FlowNode.tenant_id == tenant_id,
        ).delete(synchronize_session=False)

        node_id_map: Dict[str, int] = {}
        created_nodes: List[FlowNode] = []

        for idx, node_data in enumerate(nodes):
            temp_id = node_data.get("temp_id") or str(node_data.get("id") or f"node_{idx}")
            assignee_type = node_data.get("assignee_type") or node_data.get("assigneeType")
            assignee_value = node_data.get("assignee_value") or node_data.get("assigneeValue")

            node = FlowNode(
                tenant_id=tenant_id,
                flow_definition_id=flow_definition_id,
                name=node_data.get("name", f"节点{idx + 1}"),
                type=node_data.get("type", "user"),
                assignee_type=assignee_type,
                assignee_value=assignee_value,
                approve_policy=node_data.get("approve_policy") or node_data.get("approvePolicy") or "any",
                approve_threshold=node_data.get("approve_threshold") or node_data.get("approveThreshold"),
                sla_hours=node_data.get("sla_hours") or node_data.get("slaHours"),
                allow_delegate=node_data.get("allow_delegate", True) if node_data.get("allow_delegate") is not None else node_data.get("allowDelegate", True),
                route_mode=node_data.get("route_mode") or node_data.get("routeMode") or "exclusive",
                auto_approve_enabled=node_data.get("auto_approve_enabled", False) if node_data.get("auto_approve_enabled") is not None else node_data.get("autoApproveEnabled", False),
                auto_approve_cond=node_data.get("auto_approve_cond") or node_data.get("autoApproveCond"),
                auto_reject_cond=node_data.get("auto_reject_cond") or node_data.get("autoRejectCond"),
                auto_sample_ratio=node_data.get("auto_sample_ratio") or node_data.get("autoSampleRatio") or 0.0,
                reject_strategy=node_data.get("reject_strategy") or node_data.get("rejectStrategy") or "TO_START",
            )
            db.add(node)
            created_nodes.append(node)
            node_id_map[temp_id] = idx

        db.flush()

        for idx, node in enumerate(created_nodes):
            temp_id = None
            for tid, i in node_id_map.items():
                if i == idx:
                    temp_id = tid
                    break
            if temp_id:
                node_id_map[temp_id] = node.id

        for route_data in routes:
            from_node_key = route_data.get("from_node_key") or route_data.get("fromNodeId") or route_data.get("fromNodeKey")
            to_node_key = route_data.get("to_node_key") or route_data.get("toNodeId") or route_data.get("toNodeKey")

            from_node_id = node_id_map.get(from_node_key)
            to_node_id = node_id_map.get(to_node_key)

            if from_node_id is None or to_node_id is None:
                logger.warning(
                    f"路由配置跳过: 无法找到节点映射, from={from_node_key}, to={to_node_key}"
                )
                continue

            condition = route_data.get("condition") or route_data.get("condition_json")
            is_default = route_data.get("is_default", False) if route_data.get("is_default") is not None else route_data.get("isDefault", False)

            route = FlowRoute(
                tenant_id=tenant_id,
                flow_definition_id=flow_definition_id,
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                priority=route_data.get("priority", 1),
                condition_json=condition,
                is_default=is_default,
                enabled=True,
            )
            db.add(route)

        logger.info(
            f"同步流程节点和路由完成: flow_definition_id={flow_definition_id}, "
            f"nodes={len(created_nodes)}, routes={len(routes)}"
        )
