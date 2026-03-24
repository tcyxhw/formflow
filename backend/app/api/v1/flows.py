"""
流程配置相关 API。
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.api.deps import RequireFlowConfiguration, get_current_tenant_id, get_db
from app.models.user import User
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import error_response, success_response
from app.schemas.flow_schemas import FlowDraftSaveRequest, FlowPublishRequest
from app.services.flow_service import FlowService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{flow_definition_id}", summary="获取流程定义详情")
async def get_flow_definition(
    flow_definition_id: int = Path(..., ge=1, description="流程定义 ID"),
    current_user: User = Depends(RequireFlowConfiguration),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """查询流程定义详情，包含草稿与快照信息。"""

    try:
        detail = FlowService.get_definition_detail(
            flow_definition_id=flow_definition_id,
            tenant_id=tenant_id,
            db=db,
        )
        return success_response(data=detail.model_dump())
    except NotFoundError as exc:
        return error_response(str(exc), 4041)
    except Exception as exc:  # pragma: no cover - 防御性兜底
        logger.exception("查询流程详情失败")
        return error_response("查询失败", 5001)


@router.get("/{flow_definition_id}/draft", summary="获取流程草稿")
async def get_flow_draft(
    flow_definition_id: int = Path(..., ge=1, description="流程定义 ID"),
    current_user=Depends(RequireFlowConfiguration),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """查询当前流程草稿。"""

    try:
        draft = FlowService.get_draft(
            flow_definition_id=flow_definition_id,
            tenant_id=tenant_id,
            db=db,
        )
        return success_response(data=draft.model_dump() if draft else None)
    except NotFoundError as exc:
        return error_response(str(exc), 4041)
    except Exception as exc:  # pragma: no cover
        logger.exception("查询草稿失败")
        return error_response("查询失败", 5001)


@router.put("/{flow_definition_id}/draft", summary="保存流程草稿")
async def save_flow_draft(
    request: "FlowDraftSaveRequest" = Body(..., description="草稿内容"),
    flow_definition_id: int = Path(..., ge=1, description="流程定义 ID"),
    current_user=Depends(RequireFlowConfiguration),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """保存流程草稿，使用乐观锁控制版本。"""

    if request.flow_definition_id != flow_definition_id:
        return error_response("流程 ID 不匹配", 4001)

    try:
        draft = FlowService.save_draft(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db,
        )
        return success_response(data=draft.model_dump(), message="草稿保存成功")
    except BusinessError as exc:
        return error_response(str(exc), 4001)
    except NotFoundError as exc:
        return error_response(str(exc), 4041)
    except Exception as exc:  # pragma: no cover
        logger.exception("保存草稿失败")
        return error_response("保存失败", 5001)


@router.post("/{flow_definition_id}/publish", summary="发布流程快照")
async def publish_flow(
    request: "FlowPublishRequest" = Body(..., description="发布参数"),
    flow_definition_id: int = Path(..., ge=1, description="流程定义 ID"),
    current_user=Depends(RequireFlowConfiguration),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """发布流程，生成快照并设置为当前生效版本。"""

    if request.flow_definition_id != flow_definition_id:
        return error_response("流程 ID 不匹配", 4001)

    try:
        snapshot = FlowService.publish_flow(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db,
        )
        return success_response(
            data=snapshot.model_dump(),
            message="流程已发布",
        )
    except BusinessError as exc:
        return error_response(str(exc), 4001)
    except NotFoundError as exc:
        return error_response(str(exc), 4041)
    except Exception as exc:  # pragma: no cover
        logger.exception("发布流程失败")
        return error_response("发布失败", 5001)


@router.get("/{flow_definition_id}/snapshots", summary="列出流程快照")
async def list_flow_snapshots(
    flow_definition_id: int = Path(..., ge=1, description="流程定义 ID"),
    current_user=Depends(RequireFlowConfiguration),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """列出该流程的所有快照。"""

    try:
        definition = FlowService.get_definition_detail(
            flow_definition_id=flow_definition_id,
            tenant_id=tenant_id,
            db=db,
        )
        return success_response(data=[snap.model_dump() for snap in definition.snapshots])
    except NotFoundError as exc:
        return error_response(str(exc), 4041)
    except Exception as exc:  # pragma: no cover
        logger.exception("查询快照列表失败")
        return error_response("查询失败", 5001)
