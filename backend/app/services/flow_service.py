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
from app.models.workflow import FlowDefinition, FlowDraft, FlowSnapshot
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

        db.commit()
        db.refresh(snapshot)
        create_audit_log_sync(
            actor_user_id=user_id,
            action="flow_publish",
            resource_type="flow",
            resource_id=definition.id,
            before_data=None,
            after_data={"snapshot_id": snapshot.id, "version_tag": snapshot.version_tag},
        )
        logger.info(
            "发布流程快照",
            extra={"flow_definition_id": definition.id, "snapshot_id": snapshot.id},
        )
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
