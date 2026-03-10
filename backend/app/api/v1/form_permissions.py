"""
模块用途: 表单权限管理 API
依赖配置: 无
数据流向: HTTP 请求 -> 权限校验 -> FormPermissionService -> 统一响应
函数清单:
    - list_permissions(): 查询表单权限
    - create_permission(): 新增权限
    - update_permission(): 更新权限
    - delete_permission(): 删除权限
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_current_user
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.schemas.form_permission_schemas import (
    FormPermissionCreateRequest,
    FormPermissionListResponse,
    FormPermissionMeResponse,
    FormPermissionResponse,
    FormPermissionUpdateRequest,
    PermissionType,
)
from app.services.form_permission_service import FormPermissionService
from app.utils.audit import audit_log

router = APIRouter()


def _ensure_manage_permission(
    form_id: int,
    tenant_id: int,
    user_id: int,
    db: Session,
) -> None:
    """确保当前用户具备表单管理权限。"""

    FormPermissionService.ensure_permission(
        form_id=form_id,
        tenant_id=tenant_id,
        permission=PermissionType.MANAGE,
        user_id=user_id,
        db=db,
    )


@router.get("/forms/{form_id}/permissions", summary="查询表单权限", response_model=FormPermissionListResponse)
async def list_permissions(
    form_id: int = Path(..., ge=1, description="表单 ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """返回指定表单的权限清单。"""

    _ensure_manage_permission(form_id, tenant_id, current_user.id, db)
    items = FormPermissionService.list_permissions(form_id, tenant_id, db)
    response = FormPermissionListResponse(
        items=[FormPermissionResponse.from_orm(item) for item in items],
        total=len(items),
    )
    return success_response(data=response.model_dump())


@router.get(
    "/forms/{form_id}/permissions/me",
    summary="查询当前用户的权限概览",
    response_model=FormPermissionMeResponse,
)
async def get_my_permissions(
    form_id: int = Path(..., ge=1, description="表单 ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """返回当前登录用户在指定表单下的权限概览。

    Time: O(N), Space: O(N)
    """

    overview = FormPermissionService.get_user_permissions(
        form_id=form_id,
        tenant_id=tenant_id,
        user_id=current_user.id,
        db=db,
    )
    return success_response(data=overview.model_dump())


@router.post("/forms/{form_id}/permissions", summary="新增表单权限")
@audit_log(action="create_form_permission", resource_type="form_permission", record_after=True)
async def create_permission(
    form_id: int = Path(..., ge=1, description="表单 ID"),
    request: "FormPermissionCreateRequest" = Body(..., description="权限创建请求"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """新增一条表单权限记录。"""

    _ensure_manage_permission(form_id, tenant_id, current_user.id, db)
    permission = FormPermissionService.create_permission(form_id, tenant_id, request, db)
    return success_response(data=FormPermissionResponse.from_orm(permission).model_dump(), message="权限创建成功")


@router.put("/forms/{form_id}/permissions/{permission_id}", summary="更新权限有效期")
@audit_log(action="update_form_permission", resource_type="form_permission", record_after=True)
async def update_permission(
    form_id: int = Path(..., ge=1, description="表单 ID"),
    permission_id: int = Path(..., ge=1, description="权限 ID"),
    request: "FormPermissionUpdateRequest" = Body(..., description="权限更新请求"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """更新权限有效期设置。"""

    _ensure_manage_permission(form_id, tenant_id, current_user.id, db)
    permission = FormPermissionService.update_permission(permission_id, tenant_id, request, db)
    return success_response(data=FormPermissionResponse.from_orm(permission).model_dump(), message="权限更新成功")


@router.delete("/forms/{form_id}/permissions/{permission_id}", summary="删除权限")
@audit_log(action="delete_form_permission", resource_type="form_permission")
async def delete_permission(
    form_id: int = Path(..., ge=1, description="表单 ID"),
    permission_id: int = Path(..., ge=1, description="权限 ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """删除一条表单权限记录。"""

    _ensure_manage_permission(form_id, tenant_id, current_user.id, db)
    FormPermissionService.delete_permission(permission_id, tenant_id, db)
    return success_response(message="权限删除成功")
