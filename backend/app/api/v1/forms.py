"""
表单相关API端点
"""
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_tenant_id
from app.models.user import User
from app.schemas.form_schemas import (
    FormCreateRequest, FormUpdateRequest, FormPublishRequest, FormQueryRequest,
    FormResponse, FormDetailResponse, FormListResponse,
    FormVersionResponse, FormTemplateResponse, FormTemplateDetailResponse, AccessMode,
    FormSchemaBase, UISchemaBase, LogicSchemaBase
)
from app.schemas.form_permission_schemas import (
    FormPermissionCreateRequest,
    FormPermissionUpdateRequest,
    FormPermissionResponse,
    PermissionType,
)
from app.services.form_service import FormService
from app.services.form_version_service import FormVersionService
from app.services.form_permission_service import FormPermissionService
from app.core.response import success_response, error_response
from app.core.exceptions import ValidationError, BusinessError, AuthorizationError, NotFoundError
from app.utils.audit import audit_log
from app.data.form_templates import list_all_templates, get_template_by_id
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 表单模板（放在最前面，因为是固定路径） ==========

@router.get("/templates", summary="获取表单模板列表")
async def list_templates():
    """获取预置表单模板列表"""
    try:
        templates = list_all_templates()
        return success_response(
            data=[FormTemplateResponse(**t).dict() for t in templates]
        )
    except Exception as e:
        logger.error(f"List templates error: {e}")
        return error_response("查询失败", 5001)


@router.get("/templates/{template_id}", summary="获取模板详情")
async def get_template(
        template_id: str = Path(..., description="模板ID")
):
    """获取模板的完整配置"""
    try:
        template = get_template_by_id(template_id)
        if not template:
            return error_response("模板不存在", 4041)

        return success_response(
            data=FormTemplateDetailResponse(**template).dict()
        )
    except Exception as e:
        logger.error(f"Get template error: {e}")
        return error_response("查询失败", 5001)


@router.post("/from-template/{template_id}", summary="从模板创建表单")
@audit_log(action="create_form_from_template", resource_type="form", record_after=True)
async def create_from_template(
        template_id: str = Path(..., description="模板ID"),
        name: str = Body(..., embed=True, description="表单名称"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """从模板创建表单"""
    try:
        template = get_template_by_id(template_id)
        if not template:
            return error_response("模板不存在", 4041)

        request = FormCreateRequest(
            name=name,
            category=template["category"],
            access_mode=AccessMode.AUTHENTICATED,
            form_schema=FormSchemaBase(**template["schema_json"]),
            ui_schema=UISchemaBase(**template["ui_schema_json"]),
            logic_json=LogicSchemaBase(**template["logic_json"]) if template.get("logic_json") else None
        )

        form = FormService.create_form(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        return success_response(
            data=FormResponse.from_orm(form).dict(),
            message=f"已从模板「{template['name']}」创建表单"
        )
    except Exception as e:
        logger.error(f"Create from template error: {e}")
        return error_response("创建失败", 5001)


# ========== 版本管理（固定路径在前） ==========

@router.get("/versions/compare", summary="比较版本差异")
async def compare_versions(
        version_id_1: int = Query(..., description="版本1 ID"),
        version_id_2: int = Query(..., description="版本2 ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """比较两个版本的差异"""
    try:
        diff_result = FormVersionService.compare_versions(
            version_id_1=version_id_1,
            version_id_2=version_id_2,
            tenant_id=tenant_id,
            db=db
        )

        return success_response(data=diff_result)
    except Exception as e:
        logger.error(f"Compare versions error: {e}")
        return error_response("比较失败", 5001)


# ========== 表单列表（无参数路由） ==========

@router.get("", summary="查询表单列表")
async def list_forms(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        keyword: Optional[str] = Query(None, description="关键词搜索"),
        category: Optional[str] = Query(None, description="分类筛选"),
        status: Optional[str] = Query(None, description="状态筛选"),
        owner_user_id: Optional[int] = Query(None, description="创建者筛选"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """查询表单列表"""
    try:
        request = FormQueryRequest(
            page=page,
            page_size=page_size,
            keyword=keyword,
            category=category,
            status=status,
            owner_user_id=owner_user_id
        )

        forms, total = FormService.list_forms(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        items = []
        for form in forms:
            item = FormResponse.from_orm(form).dict()
            stats = FormService.get_form_statistics(form.id, tenant_id, db)
            item["current_version"] = stats["current_version"]
            item["total_submissions"] = stats["total_submissions"]
            items.append(item)

        response = FormListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

        return success_response(data=response.dict())
    except Exception as e:
        logger.error(f"List forms error: {e}")
        return error_response("查询失败", 5001)


@router.post("", summary="创建表单")
@audit_log(action="create_form", resource_type="form", record_after=True)
async def create_form(
        request: FormCreateRequest = Body(...),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """创建表单（草稿状态）"""
    try:
        form = FormService.create_form(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        return success_response(
            data=FormResponse.from_orm(form).dict(),
            message="表单创建成功"
        )
    except ValidationError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        logger.error(f"Create form error: {e}")
        return error_response("创建失败", 5001)


# ========== 表单操作（动态参数 {form_id}，放在最后） ==========

@router.get("/{form_id}", summary="获取表单详情")
async def get_form_detail(
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """获取表单详情"""
    try:
        # 仅限拥有管理或查看权限的用户访问
        try:
            FormPermissionService.ensure_permission(
                form_id=form_id,
                tenant_id=tenant_id,
                permission=PermissionType.VIEW,
                user_id=current_user.id,
                db=db
            )
        except AuthorizationError:
            # 对于公开表单允许访问
            form = FormService.get_form_by_id(form_id, tenant_id, db)
            if form.access_mode != AccessMode.PUBLIC.value:
                raise

        form, current_version, versions = FormService.get_form_detail(
            form_id=form_id,
            tenant_id=tenant_id,
            db=db
        )

        response_data = FormResponse.from_orm(form).dict()

        if current_version:
            response_data["schema_json"] = current_version.schema_json
            response_data["ui_schema_json"] = current_version.ui_schema_json
            response_data["logic_json"] = current_version.logic_json
            response_data["current_version"] = current_version.version

        response_data["versions"] = [
            FormVersionResponse.from_orm(v).dict() for v in versions
        ]

        stats = FormService.get_form_statistics(form_id, tenant_id, db)
        response_data["total_submissions"] = stats["total_submissions"]

        return success_response(data=response_data)
    except Exception as e:
        logger.error(f"Get form detail error: {e}")
        return error_response("查询失败", 5001)


@router.put("/{form_id}", summary="更新表单")
@audit_log(action="update_form", resource_type="form", record_before=True, record_after=True)
async def update_form(
        form_id: int = Path(..., description="表单ID"),
        request: FormUpdateRequest = Body(...),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """更新表单"""
    try:
        FormPermissionService.ensure_permission(
            form_id=form_id,
            tenant_id=tenant_id,
            permission=PermissionType.MANAGE,
            user_id=current_user.id,
            db=db
        )

        form = FormService.update_form(
            form_id=form_id,
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        return success_response(
            data=FormResponse.from_orm(form).dict(),
            message="表单更新成功"
        )
    except ValidationError as e:
        return error_response(str(e), 4001)
    except BusinessError as e:
        return error_response(str(e), 4002)
    except Exception as e:
        logger.error(f"Update form error: {e}")
        return error_response("更新失败", 5001)


@router.delete("/{form_id}", summary="删除表单")
@audit_log(action="delete_form", resource_type="form", record_before=True)
async def delete_form(
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """删除表单"""
    try:
        FormPermissionService.ensure_permission(
            form_id=form_id,
            tenant_id=tenant_id,
            permission=PermissionType.MANAGE,
            user_id=current_user.id,
            db=db
        )

        FormService.delete_form(
            form_id=form_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        return success_response(message="表单删除成功")
    except BusinessError as e:
        return error_response(str(e), 4002)
    except Exception as e:
        logger.error(f"Delete form error: {e}")
        return error_response("删除失败", 5001)


@router.post("/{form_id}/publish", summary="发布表单")
@audit_log(action="publish_form", resource_type="form", record_after=True)
async def publish_form(
        request: FormPublishRequest = Body(...),
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """发布表单"""
    try:
        FormPermissionService.ensure_permission(
            form_id=form_id,
            tenant_id=tenant_id,
            permission=PermissionType.MANAGE,
            user_id=current_user.id,
            db=db
        )

        version = FormService.publish_form(
            form_id=form_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db,
            flow_definition_id=request.flow_definition_id
        )

        return success_response(
            data=FormVersionResponse.from_orm(version).dict(),
            message=f"表单发布成功，版本号：{version.version}"
        )
    except ValidationError as e:
        return error_response(str(e), 4001)
    except BusinessError as e:
        return error_response(str(e), 4002)
    except Exception as e:
        logger.error(f"Publish form error: {e}")
        return error_response("发布失败", 5001)


@router.post("/{form_id}/unpublish", summary="取消发布")
@audit_log(action="unpublish_form", resource_type="form")
async def unpublish_form(
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """取消发布（改为草稿状态）"""
    try:
        FormPermissionService.ensure_permission(
            form_id=form_id,
            tenant_id=tenant_id,
            permission=PermissionType.MANAGE,
            user_id=current_user.id,
            db=db
        )

        form = FormService.unpublish_form(
            form_id=form_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        return success_response(
            data=FormResponse.from_orm(form).dict(),
            message="已取消发布"
        )
    except BusinessError as e:
        return error_response(str(e), 4002)
    except Exception as e:
        logger.error(f"Unpublish form error: {e}")
        return error_response("操作失败", 5001)


@router.post("/{form_id}/archive", summary="归档表单")
@audit_log(action="archive_form", resource_type="form")
async def archive_form(
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """归档表单（不再接受新的提交）"""
    try:
        FormPermissionService.ensure_permission(
            form_id=form_id,
            tenant_id=tenant_id,
            permission=PermissionType.MANAGE,
            user_id=current_user.id,
            db=db
        )

        form = FormService.archive_form(
            form_id=form_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        return success_response(
            data=FormResponse.from_orm(form).dict(),
            message="表单已归档"
        )
    except Exception as e:
        logger.error(f"Archive form error: {e}")
        return error_response("归档失败", 5001)


@router.post("/{form_id}/clone", summary="克隆表单")
@audit_log(action="clone_form", resource_type="form", record_after=True)
async def clone_form(
        form_id: int = Path(..., description="源表单ID"),
        new_name: str = Body(..., embed=True, description="新表单名称"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """克隆表单"""
    try:
        FormPermissionService.ensure_permission(
            form_id=form_id,
            tenant_id=tenant_id,
            permission=PermissionType.MANAGE,
            user_id=current_user.id,
            db=db
        )

        new_form = FormService.clone_form(
            form_id=form_id,
            new_name=new_name,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        return success_response(
            data=FormResponse.from_orm(new_form).dict(),
            message="表单克隆成功"
        )
    except Exception as e:
        logger.error(f"Clone form error: {e}")
        return error_response("克隆失败", 5001)


@router.get("/{form_id}/versions", summary="获取版本列表")
async def list_versions(
        form_id: int = Path(..., description="表单ID"),
        include_draft: bool = Query(False, description="是否包含草稿版本"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """获取表单的所有版本"""
    try:
        versions = FormVersionService.list_versions(
            form_id=form_id,
            tenant_id=tenant_id,
            db=db,
            include_draft=include_draft
        )

        return success_response(
            data=[FormVersionResponse.from_orm(v).dict() for v in versions]
        )
    except Exception as e:
        logger.error(f"List versions error: {e}")
        return error_response("查询失败", 5001)


@router.get("/{form_id}/versions/{version_num}", summary="获取指定版本")
async def get_version(
        form_id: int = Path(..., description="表单ID"),
        version_num: int = Path(..., description="版本号"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """获取指定版本的完整配置"""
    try:
        version = FormVersionService.get_version_by_number(
            form_id=form_id,
            version_num=version_num,
            tenant_id=tenant_id,
            db=db
        )

        response_data = FormVersionResponse.from_orm(version).dict()
        response_data["schema_json"] = version.schema_json
        response_data["ui_schema_json"] = version.ui_schema_json
        response_data["logic_json"] = version.logic_json

        return success_response(data=response_data)
    except Exception as e:
        logger.error(f"Get version error: {e}")
        return error_response("查询失败", 5001)