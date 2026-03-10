"""
模块用途: 审批任务 API
依赖配置: 无
数据流向: HTTP 请求 -> Service 调用 -> 统一响应
函数清单:
    - list_tasks(): 查询待办任务
    - claim_task(): 认领任务
    - release_task(): 释放任务
    - perform_task_action(): 执行审批动作
    - get_process_timeline(): 查询流程轨迹
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_current_user
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.schemas.approval_schemas import (
    ProcessTimelineResponse,
    SlaLevel,
    TaskActionRequest,
    TaskAddSignRequest,
    TaskDelegateRequest,
    TaskListRequest,
    TaskListResponse,
    TaskSlaSummary,
    TaskStatus,
    TaskTransferRequest,
)
from app.services.approval_service import TaskService
from app.utils.audit import audit_log

router = APIRouter()


@router.get("", summary="查询待办任务", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[TaskStatus] = Query(default=None, description="任务状态"),
    only_mine: bool = Query(True, description="仅查看本人任务"),
    include_group_tasks: bool = Query(True, description="是否包含小组待办池"),
    keyword: Optional[str] = Query(None, description="关键词"),
    sla_level: Optional[SlaLevel] = Query(default=None, description="SLA 等级：unknown/normal/warning/critical/expired"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """查询当前用户可见的审批任务。

    :return: 任务分页结果

    Time: O(N), Space: O(N)
    """

    request_schema = TaskListRequest(
        page=page,
        page_size=page_size,
        status=status,
        only_mine=only_mine,
        include_group_tasks=include_group_tasks,
        keyword=keyword,
        sla_level=sla_level,
    )
    items, total = TaskService.list_tasks(request_schema, tenant_id, current_user, db)

    response = TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )

    return success_response(data=response.model_dump())


@router.get("/summary", summary="查询 SLA 分布", response_model=TaskSlaSummary)
async def get_sla_summary(
    status: Optional[TaskStatus] = Query(default=None, description="任务状态"),
    only_mine: bool = Query(True, description="仅查看本人任务"),
    include_group_tasks: bool = Query(True, description="是否包含小组待办池"),
    keyword: Optional[str] = Query(None, description="关键词"),
    sla_level: Optional[SlaLevel] = Query(default=None, description="额外的 SLA 等级过滤"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """返回当前筛选条件下的任务 SLA 分布。"""

    request_schema = TaskListRequest(
        page=1,
        page_size=1,
        status=status,
        only_mine=only_mine,
        include_group_tasks=include_group_tasks,
        keyword=keyword,
        sla_level=sla_level,
    )
    summary = TaskService.get_sla_summary(request_schema, tenant_id, current_user, db)
    return success_response(data=summary.model_dump())


@router.post("/{task_id}/claim", summary="认领任务")
@audit_log(action="claim_task", resource_type="task")
async def claim_task(
    task_id: int = Path(..., ge=1, description="任务 ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """认领个人或小组待办。

    :return: 最新任务数据

    Time: O(1), Space: O(1)
    """

    task = TaskService.claim_task(task_id, tenant_id, current_user, db)
    return success_response(data=task.model_dump(), message="任务认领成功")


@router.post("/{task_id}/release", summary="释放任务")
@audit_log(action="release_task", resource_type="task")
async def release_task(
    task_id: int = Path(..., ge=1, description="任务 ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """释放已认领的任务。

    :return: 最新任务数据

    Time: O(1), Space: O(1)
    """

    task = TaskService.release_task(task_id, tenant_id, current_user, db)
    return success_response(data=task.model_dump(), message="任务已释放")


@router.post("/{task_id}/actions", summary="执行审批动作")
@audit_log(action="perform_task_action", resource_type="task")
async def perform_task_action(
    task_id: int = Path(..., ge=1, description="任务 ID"),
    request: "TaskActionRequest" = Body(..., description="审批动作请求"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """执行审批动作（通过/驳回/加签等）。

    :return: 最新任务数据

    Time: O(1), Space: O(1)
    """

    task = TaskService.perform_task_action(task_id, tenant_id, request, current_user, db)
    return success_response(data=task.model_dump(), message="操作成功")


@router.post("/{task_id}/transfer", summary="转交任务")
@audit_log(action="transfer_task", resource_type="task")
async def transfer_task(
    task_id: int = Path(..., ge=1, description="任务 ID"),
    request: "TaskTransferRequest" = Body(..., description="转交请求"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """将任务转交给指定用户。"""

    task = TaskService.transfer_task(task_id, tenant_id, request, current_user, db)
    return success_response(data=task.model_dump(), message="任务转交成功")


@router.post("/{task_id}/delegate", summary="委托任务")
@audit_log(action="delegate_task", resource_type="task")
async def delegate_task(
    task_id: int = Path(..., ge=1, description="任务 ID"),
    request: "TaskDelegateRequest" = Body(..., description="委托请求"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """委托当前任务给其他处理人。"""

    task = TaskService.delegate_task(task_id, tenant_id, request, current_user, db)
    return success_response(data=task.model_dump(), message="任务委托成功")


@router.post("/{task_id}/add-sign", summary="任务加签")
@audit_log(action="add_sign_task", resource_type="task")
async def add_sign_task(
    task_id: int = Path(..., ge=1, description="任务 ID"),
    request: "TaskAddSignRequest" = Body(..., description="加签请求"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """为任务添加额外处理人。"""

    tasks = TaskService.add_sign_tasks(task_id, tenant_id, request, current_user, db)
    return success_response(
        data=[task.model_dump() for task in tasks],
        message="加签任务已创建",
    )


@router.get("/group", summary="查询小组待办池", response_model=TaskListResponse)
async def list_group_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """查询当前用户所在小组的待认领任务。"""

    request_schema = TaskListRequest(
        page=page,
        page_size=page_size,
        only_mine=False,
        include_group_tasks=True,
    )
    items, total = TaskService.list_group_tasks(request_schema, tenant_id, current_user, db)
    response = TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )
    return success_response(data=response.model_dump())


@router.get("/processes/{process_instance_id}/timeline", summary="查询流程轨迹")
async def get_process_timeline(
    process_instance_id: int = Path(..., ge=1, description="流程实例 ID"),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """查询流程轨迹。

    :return: 流程轨迹列表

    Time: O(N), Space: O(N)
    """

    timeline: ProcessTimelineResponse = TaskService.get_process_timeline(
        process_instance_id=process_instance_id,
        tenant_id=tenant_id,
        db=db,
    )
    return success_response(data=timeline.model_dump())
