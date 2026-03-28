"""
表单相关API端点
"""
from fastapi import APIRouter, Depends, Query, Path, Body, BackgroundTasks
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
from app.services.form_workspace_service import FormWorkspaceService
from app.core.response import success_response, error_response
from app.core.exceptions import ValidationError, BusinessError, AuthorizationError, NotFoundError
from app.utils.audit import audit_log
from app.data.form_templates import list_all_templates, get_template_by_id
from app.schemas.workspace_schemas import FillableFormsQuery
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
        background_tasks: BackgroundTasks = BackgroundTasks(),
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


# ========== 表单填写工作区（固定路径在前） ==========

@router.get("/fillable", summary="获取可填写表单列表")
async def get_fillable_forms(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        keyword: Optional[str] = Query(None, max_length=100, description="搜索关键词"),
        status: Optional[str] = Query(None, description="表单状态筛选"),
        category: Optional[str] = Query(None, description="表单类别筛选"),
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("desc", description="排序方向: asc/desc"),
        search_type: str = Query("name", description="搜索类型: name/owner"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取当前用户有权填写的表单列表
    
    业务逻辑：
    1. 验证用户身份和租户上下文
    2. 调用 FormWorkspaceService.get_fillable_forms() 获取有 FILL 权限的表单
    3. 应用搜索关键词过滤（标题、描述）
    4. 应用状态和类别筛选
    5. 执行排序和分页
    6. 计算每个表单的状态标识（是否过期、是否关闭）
    7. 返回分页结果
    
    权限要求：已认证用户
    """
    try:
        # 构建查询参数
        query = FillableFormsQuery(
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
            category=category,
            sort_by=sort_by,
            sort_order=sort_order,
            search_type=search_type
        )
        
        # 调用服务层获取可填写表单列表
        response = FormWorkspaceService.get_fillable_forms(
            user_id=current_user.id,
            tenant_id=tenant_id,
            query=query,
            db=db
        )
        
        # 返回成功响应
        return success_response(
            data=response.dict(),
            message="查询成功"
        )
    
    except ValidationError as e:
        logger.error(f"Validation error in get_fillable_forms: {e}")
        return error_response(str(e), 4001)
    
    except AuthorizationError as e:
        logger.error(f"Authorization error in get_fillable_forms: {e}")
        return error_response(str(e), 4031)
    
    except Exception as e:
        logger.error(f"Error in get_fillable_forms: {e}", exc_info=True)
        return error_response("查询可填写表单列表失败", 5001)


# ========== 快捷入口管理（固定路径在前） ==========

@router.get("/quick-access", summary="获取快捷入口表单列表")
async def get_quick_access_forms(
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取用户的快捷入口表单列表
    
    业务逻辑：
    1. 查询用户的所有快捷入口记录（按排序顺序）
    2. 获取对应的表单详情
    3. 计算表单状态
    4. 返回表单列表
    
    权限要求：已认证用户
    """
    try:
        # 调用服务层获取快捷入口表单列表
        response = FormWorkspaceService.get_quick_access_forms(
            user_id=current_user.id,
            tenant_id=tenant_id,
            db=db
        )
        
        # 返回成功响应
        return success_response(
            data=response.dict(),
            message="查询成功"
        )
    
    except Exception as e:
        logger.error(f"Error in get_quick_access_forms: {e}", exc_info=True)
        return error_response("查询快捷入口列表失败", 5001)


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
        request: "FormCreateRequest" = Body(...),
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

@router.get("/{form_id}/fields", summary="获取表单字段列表")
async def get_form_fields(
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取表单的所有字段定义，包括表单字段和系统字段
    
    返回格式：
    {
        "form_id": 1,
        "form_name": "招待费申请",
        "fields": [
            {
                "key": "amount",
                "name": "金额",
                "type": "number",
                "required": true,
                "options": null,
                "props": {}
            }
        ],
        "system_fields": [
            {
                "key": "sys_submitter",
                "name": "提交人",
                "type": "string",
                "required": false,
                "options": null,
                "props": {}
            }
        ]
    }
    """
    try:
        form = FormService.get_form_by_id_any_tenant(form_id, db)
        if not form:
            return error_response("表单不存在", 4041)
        
        real_tenant_id = form.tenant_id
        
        has_access = (
            FormPermissionService.has_permission(form_id, real_tenant_id, PermissionType.VIEW, current_user.id, db)
            or FormPermissionService.has_permission(form_id, real_tenant_id, PermissionType.FILL, current_user.id, db)
        )
        if not has_access:
            # 检查用户是否是表单创建者
            if form.owner_user_id == current_user.id:
                has_access = True
        
        if not has_access:
            # 检查用户是否有该表单的审批任务
            from app.models.workflow import Task, ProcessInstance
            from sqlalchemy import and_
            approval_task_exists = db.query(Task).join(
                ProcessInstance, Task.process_instance_id == ProcessInstance.id
            ).filter(
                and_(
                    Task.assignee_user_id == current_user.id,
                    Task.tenant_id == real_tenant_id,
                    ProcessInstance.form_id == form_id,
                    Task.status.in_(["open", "claimed", "completed"])
                )
            ).first()
            has_access = approval_task_exists is not None
        
        if not has_access:
            if form.access_mode != AccessMode.PUBLIC.value:
                raise AuthorizationError("缺少表单访问权限")

        form, current_version, _ = FormService.get_form_detail(
            form_id=form_id,
            tenant_id=real_tenant_id,
            db=db
        )

        if not current_version:
            return error_response("表单未配置字段", 4041)

        # 提取表单字段
        schema_json = current_version.schema_json
        form_fields = []
        
        if schema_json and "fields" in schema_json:
            for field in schema_json["fields"]:
                form_fields.append({
                    "key": field.get("id", ""),
                    "name": field.get("label", ""),
                    "type": field.get("type", ""),
                    "description": field.get("description"),
                    "required": field.get("required", False),
                    "options": field.get("props", {}).get("options"),
                    "props": field.get("props", {})
                })

        # 系统字段定义
        system_fields = [
            {
                "key": "sys_submitter",
                "name": "提交人",
                "type": "user",
                "description": "表单提交人",
                "required": False,
                "options": None,
                "props": {}
            },
            {
                "key": "sys_submitter_dept",
                "name": "提交人部门",
                "type": "department",
                "description": "表单提交人所属部门",
                "required": False,
                "options": None,
                "props": {}
            },
            {
                "key": "sys_submit_time",
                "name": "提交时间",
                "type": "datetime",
                "description": "表单提交时间",
                "required": False,
                "options": None,
                "props": {}
            }
        ]

        # 构建响应
        from app.schemas.form_schemas import FormFieldResponse, FormFieldsResponse
        
        fields_response = FormFieldsResponse(
            form_id=form.id,
            form_name=form.name,
            fields=[FormFieldResponse(**f) for f in form_fields],
            system_fields=[FormFieldResponse(**f) for f in system_fields]
        )

        return success_response(data=fields_response.dict())

    except NotFoundError as e:
        logger.error(f"Get form fields error: {e}")
        return error_response(str(e), 4041)
    except AuthorizationError as e:
        logger.error(f"Get form fields error: {e}")
        return error_response(str(e), 4003)
    except Exception as e:
        logger.error(f"Get form fields error: {e}")
        return error_response("查询失败", 5001)


@router.get("/{form_id}", summary="获取表单详情")
async def get_form_detail(
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """获取表单详情"""
    try:
        # 仅限拥有查看、填写、编辑或管理权限的用户访问
        has_access = (
            FormPermissionService.has_permission(form_id, tenant_id, PermissionType.VIEW, current_user.id, db)
            or FormPermissionService.has_permission(form_id, tenant_id, PermissionType.FILL, current_user.id, db)
            or FormPermissionService.has_permission(form_id, tenant_id, PermissionType.EDIT, current_user.id, db)
            or FormPermissionService.has_permission(form_id, tenant_id, PermissionType.MANAGE, current_user.id, db)
        )
        if not has_access:
            # 对于公开表单允许访问
            try:
                form = FormService.get_form_by_id(form_id, tenant_id, db)
                if form.access_mode != AccessMode.PUBLIC.value:
                    raise AuthorizationError("缺少表单访问权限")
            except NotFoundError:
                # 表单不存在，返回404
                return error_response(f"表单不存在: id={form_id}", 4041)

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
    except NotFoundError as e:
        logger.error(f"Get form detail error: {e}")
        return error_response(str(e), 4041)
    except AuthorizationError as e:
        logger.error(f"Get form detail error: {e}")
        return error_response(str(e), 4003)
    except Exception as e:
        logger.error(f"Get form detail error: {e}")
        return error_response("查询失败", 5001)


@router.put("/{form_id}", summary="更新表单")
@audit_log(action="update_form", resource_type="form", record_before=True, record_after=True)
async def update_form(
        form_id: int = Path(..., description="表单ID"),
        request: "FormUpdateRequest" = Body(...),
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
        cascade: bool = Query(False, description="是否级联删除关联的流程定义"),
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

        result = FormService.delete_form(
            form_id=form_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db,
            cascade=cascade
        )

        return success_response(data=result, message="表单删除成功")
    except BusinessError as e:
        # 处理409 Conflict（需要级联删除确认）
        if e.status_code == 409:
            return error_response(e.message, 4009, data=e.data, status_code=409)
        return error_response(str(e), 4002)
    except Exception as e:
        logger.error(f"Delete form error: {e}")
        return error_response("删除失败", 5001)


@router.post("/{form_id}/publish", summary="发布表单")
@audit_log(action="publish_form", resource_type="form", record_after=True)
async def publish_form(
        request: "FormPublishRequest" = Body(default=None),
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
            flow_definition_id=request.flow_definition_id if request else None
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


@router.post("/{form_id}/quick-access", summary="添加到快捷入口")
@audit_log(action="add_quick_access", resource_type="form")
async def add_quick_access(
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    将表单添加到用户的快捷入口列表
    
    业务逻辑：
    1. 验证表单是否存在
    2. 检查是否已存在该快捷入口（幂等性）
    3. 添加到快捷入口
    
    权限要求：已认证用户
    """
    try:
        # 验证表单是否存在
        form = FormService.get_form_by_id(form_id, tenant_id, db)
        if not form:
            return error_response("表单不存在", 4041)
        
        # 调用服务层添加快捷入口
        FormWorkspaceService.add_quick_access(
            user_id=current_user.id,
            tenant_id=tenant_id,
            form_id=form_id,
            db=db
        )
        
        # 返回成功响应
        return success_response(
            data={"form_id": form_id},
            message="已添加到快捷入口"
        )
    
    except NotFoundError as e:
        logger.error(f"Form not found in add_quick_access: {e}")
        return error_response("表单不存在", 4041)
    
    except Exception as e:
        logger.error(f"Error in add_quick_access: {e}", exc_info=True)
        return error_response("添加快捷入口失败", 5001)


@router.delete("/{form_id}/quick-access", summary="从快捷入口移除")
@audit_log(action="remove_quick_access", resource_type="form")
async def remove_quick_access(
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    从快捷入口列表移除表单
    
    业务逻辑：
    1. 查找对应的快捷入口记录
    2. 如果存在，删除该记录
    3. 返回操作结果
    
    权限要求：已认证用户
    """
    try:
        # 调用服务层移除快捷入口
        removed = FormWorkspaceService.remove_quick_access(
            user_id=current_user.id,
            tenant_id=tenant_id,
            form_id=form_id,
            db=db
        )
        
        # 返回成功响应
        if removed:
            return success_response(message="已从快捷入口移除")
        else:
            return success_response(message="快捷入口不存在")
    
    except Exception as e:
        logger.error(f"Error in remove_quick_access: {e}", exc_info=True)
        return error_response("移除快捷入口失败", 5001)


@router.post("/{form_id}/flow-definition", summary="获取或创建表单流程定义")
async def get_or_create_flow_definition(
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取或创建表单关联的流程定义。

    如果表单已有流程定义，返回其 ID；否则创建新的流程定义并关联。

    权限要求：表单管理权限
    """
    try:
        FormPermissionService.ensure_permission(
            form_id=form_id,
            tenant_id=tenant_id,
            permission=PermissionType.MANAGE,
            user_id=current_user.id,
            db=db
        )

        flow_definition_id = FormService.get_or_create_flow_definition(
            form_id=form_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        return success_response(
            data={"flow_definition_id": flow_definition_id},
            message="流程定义已就绪"
        )

    except NotFoundError as e:
        return error_response(str(e), 4041)
    except Exception as e:
        logger.error(f"Error in get_or_create_flow_definition: {e}")
        return error_response("操作失败", 5001)