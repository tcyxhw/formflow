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

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_current_user
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.models.form import FormPermission
from app.schemas.form_permission_schemas import (
    FormPermissionCreateRequest,
    FormPermissionListResponse,
    FormPermissionMeResponse,
    FormPermissionResponse,
    FormPermissionUpdateRequest,
    GrantType,
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


def _get_grantee_name(grant_type: str, grantee_id: int, tenant_id: int, db: Session) -> str:
    """根据授权类型和ID获取授权对象名称。

    Time: O(1), Space: O(1)
    """
    try:
        if grant_type == GrantType.USER:
            user = db.query(User).filter(User.id == grantee_id, User.tenant_id == tenant_id).first()
            return user.name if user else f"用户#{grantee_id}"
        elif grant_type == GrantType.ROLE:
            from app.models.user import Role
            role = db.query(Role).filter(Role.id == grantee_id, Role.tenant_id == tenant_id).first()
            return role.name if role else f"角色#{grantee_id}"
        elif grant_type == GrantType.DEPARTMENT:
            from app.models.user import Department
            dept = db.query(Department).filter(Department.id == grantee_id, Department.tenant_id == tenant_id).first()
            return dept.name if dept else f"部门#{grantee_id}"
        elif grant_type == GrantType.POSITION:
            from app.models.user import Position
            pos = db.query(Position).filter(Position.id == grantee_id, Position.tenant_id == tenant_id).first()
            return pos.name if pos else f"岗位#{grantee_id}"
    except Exception:
        pass
    return f"{grant_type}#{grantee_id}"


def _format_permission_item(item: FormPermission, tenant_id: int, db: Session) -> Dict[str, Any]:
    """格式化权限记录为响应字典，包含授权对象名称。

    Time: O(1), Space: O(1)
    """
    return {
        "id": item.id,
        "form_id": item.form_id,
        "tenant_id": item.tenant_id,
        "grant_type": item.grant_type,
        "grantee_id": item.grantee_id,
        "grantee_name": _get_grantee_name(item.grant_type, item.grantee_id, tenant_id, db),
        "permission": item.permission,
        "include_children": item.include_children,
        "valid_from": item.valid_from,
        "valid_to": item.valid_to,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.get("/forms/{form_id}/permissions", summary="查询表单权限")
async def list_permissions(
    form_id: int = Path(..., ge=1, description="表单 ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """返回指定表单的权限清单，包含授权对象名称。"""

    _ensure_manage_permission(form_id, tenant_id, current_user.id, db)
    items = FormPermissionService.list_permissions(form_id, tenant_id, db)
    formatted_items = [_format_permission_item(item, tenant_id, db) for item in items]
    return success_response(data={"items": formatted_items, "total": len(formatted_items)})


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

    # 构建更新数据，只包含请求中实际传入的字段
    update_data = {}
    fields_set = request.model_fields_set
    if "valid_from" in fields_set:
        update_data["valid_from"] = request.valid_from
    if "valid_to" in fields_set:
        update_data["valid_to"] = request.valid_to

    permission = FormPermissionService.update_permission(permission_id, tenant_id, update_data, db)
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
