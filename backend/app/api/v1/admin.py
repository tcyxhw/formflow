# app/api/v1/admin.py
"""
管理员通用CRUD接口
提供对白名单内表的通用增删改查功能
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query, Path, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect, or_
import json
from app.core.database import get_db, Base
from app.core.response import success_response, paginated_response
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    AuthorizationError,
    BusinessError
)
from app.config import settings
from app.api.deps import RequireSuperAdmin, RequireAdmin, get_current_tenant_id, get_current_user
from app.models.user import User
from app.utils.audit import audit_log
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_model_class(table_name: str):
    """
    根据表名获取模型类

    Args:
        table_name: 表名

    Returns:
        模型类

    Raises:
        NotFoundError: 表不存在或不在白名单中
    """
    # 检查白名单
    if table_name not in settings.ADMIN_CRUD_WHITELIST:
        raise AuthorizationError(f"表 {table_name} 不在访问白名单中")

    # 遍历所有模型类
    for mapper in Base.registry.mappers:
        model = mapper.class_
        if model.__tablename__ == table_name:
            return model

    raise NotFoundError(f"表 {table_name} 不存在")


def filter_sensitive_fields(data: Dict, table_name: str) -> Dict:
    """
    过滤敏感字段

    Args:
        data: 原始数据
        table_name: 表名

    Returns:
        过滤后的数据
    """
    # 定义敏感字段
    sensitive_fields = {
        "user": ["password_hash"],
        "refresh_token": ["jti_hash"],
        "*": ["password", "secret", "token"]  # 通用敏感字段
    }

    # 获取该表的敏感字段
    fields_to_remove = set()
    if table_name in sensitive_fields:
        fields_to_remove.update(sensitive_fields[table_name])
    fields_to_remove.update(sensitive_fields.get("*", []))

    # 过滤数据
    filtered_data = {}
    for key, value in data.items():
        if key not in fields_to_remove:
            filtered_data[key] = value

    return filtered_data


@router.get("/crud/{table_name}", summary="查询数据列表")
async def list_records(
        table_name: str = Path(..., description="表名"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页大小"),
        filters: Optional[str] = Query(None, description="筛选条件(JSON格式)"),
        sort: Optional[str] = Query(None, description="排序字段"),
        order: Optional[str] = Query("asc", pattern="^(asc|desc)$", description="排序方向"),
        current_user: User = Depends(RequireSuperAdmin),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    通用查询接口（仅系统管理员）

    路径参数:
    - table_name: 表名（必须在白名单中）

    查询参数:
    - page: 页码
    - size: 每页大小
    - filters: 筛选条件，JSON格式，如 {"status":"active","tenant_id":1}
    - sort: 排序字段
    - order: 排序方向（asc/desc）

    返回值:
    - items: 数据列表
    - total: 总数量
    - page: 当前页
    - size: 每页大小
    - pages: 总页数
    """
    # 获取模型类
    model_class = get_model_class(table_name)

    # 构建查询
    query = db.query(model_class)

    # 如果模型有tenant_id字段，自动添加租户过滤
    if hasattr(model_class, 'tenant_id'):
        query = query.filter(model_class.tenant_id == tenant_id)

    # 解析筛选条件
    if filters:
        try:
            filter_dict = json.loads(filters)
            for key, value in filter_dict.items():
                if hasattr(model_class, key):
                    column = getattr(model_class, key)
                    if isinstance(value, list):
                        query = query.filter(column.in_(value))
                    elif isinstance(value, dict):
                        # 支持范围查询
                        if "min" in value:
                            query = query.filter(column >= value["min"])
                        if "max" in value:
                            query = query.filter(column <= value["max"])
                    else:
                        query = query.filter(column == value)
        except json.JSONDecodeError:
            raise ValidationError("筛选条件格式错误")

    # 获取总数
    total = query.count()

    # 排序
    if sort and hasattr(model_class, sort):
        sort_column = getattr(model_class, sort)
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    # 分页
    offset = (page - 1) * size
    records = query.offset(offset).limit(size).all()

    # 转换为字典并过滤敏感字段
    items = []
    for record in records:
        data = record.to_dict() if hasattr(record, 'to_dict') else {
            c.name: getattr(record, c.name)
            for c in record.__table__.columns
        }
        items.append(filter_sensitive_fields(data, table_name))

    return paginated_response(
        items=items,
        total=total,
        page=page,
        size=size
    )


@router.get("/crud/{table_name}/{record_id}", summary="获取单条记录")
async def get_record(
        table_name: str = Path(..., description="表名"),
        record_id: int = Path(..., description="记录ID"),
        current_user: User = Depends(RequireSuperAdmin),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取单条记录详情（仅系统管理员）

    路径参数:
    - table_name: 表名
    - record_id: 记录ID

    返回值:
    - 记录详情（敏感字段已过滤）
    """
    # 获取模型类
    model_class = get_model_class(table_name)

    # 查询记录
    query = db.query(model_class).filter(model_class.id == record_id)

    # 租户隔离
    if hasattr(model_class, 'tenant_id'):
        query = query.filter(model_class.tenant_id == tenant_id)

    record = query.first()

    if not record:
        raise NotFoundError(f"记录不存在")

    # 转换为字典并过滤敏感字段
    data = record.to_dict() if hasattr(record, 'to_dict') else {
        c.name: getattr(record, c.name)
        for c in record.__table__.columns
    }

    return success_response(
        data=filter_sensitive_fields(data, table_name)
    )


@router.post("/crud/{table_name}", summary="创建记录")
@audit_log(
    action="admin_create",
    resource_type="admin_crud",
    record_after=True
)
async def create_record(
        table_name: str = Path(..., description="表名"),
        record_data: Dict[str, Any] = ...,
        current_user: User = Depends(RequireSuperAdmin),
        tenant_id: int = Depends(get_current_tenant_id),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: Session = Depends(get_db),
        request: Request = None
):
    """
    创建新记录（仅系统管理员）

    路径参数:
    - table_name: 表名

    请求体:
    - 记录数据（JSON格式）

    返回值:
    - 创建的记录
    """
    # 获取模型类
    model_class = get_model_class(table_name)

    # 自动添加tenant_id
    if hasattr(model_class, 'tenant_id'):
        record_data['tenant_id'] = tenant_id

    # 移除ID字段（如果存在）
    record_data.pop('id', None)

    # 验证字段
    inspector = inspect(model_class)
    valid_columns = {c.name for c in inspector.columns}

    for key in record_data.keys():
        if key not in valid_columns:
            raise ValidationError(f"字段 {key} 不存在")

    try:
        # 创建记录
        new_record = model_class(**record_data)
        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        # 转换为字典
        data = new_record.to_dict() if hasattr(new_record, 'to_dict') else {
            c.name: getattr(new_record, c.name)
            for c in new_record.__table__.columns
        }

        logger.info(f"管理员创建记录 - 表: {table_name}, ID: {new_record.id}")

        return success_response(
            data=filter_sensitive_fields(data, table_name),
            message="记录创建成功"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"创建记录失败: {str(e)}")
        raise BusinessError(f"创建失败: {str(e)}")


@router.put("/crud/{table_name}/{record_id}", summary="更新记录")
@audit_log(
    action="admin_update",
    resource_type="admin_crud",
    record_before=True,
    record_after=True
)
async def update_record(
        table_name: str = Path(..., description="表名"),
        record_id: int = Path(..., description="记录ID"),
        record_data: Dict[str, Any] = ...,
        current_user: User = Depends(RequireSuperAdmin),
        tenant_id: int = Depends(get_current_tenant_id),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: Session = Depends(get_db),
        request: Request = None
):
    """
    更新记录（仅系统管理员）

    路径参数:
    - table_name: 表名
    - record_id: 记录ID

    请求体:
    - 更新数据（JSON格式）

    返回值:
    - 更新后的记录
    """
    # 获取模型类
    model_class = get_model_class(table_name)

    # 查询记录
    query = db.query(model_class).filter(model_class.id == record_id)

    # 租户隔离
    if hasattr(model_class, 'tenant_id'):
        query = query.filter(model_class.tenant_id == tenant_id)

    record = query.first()

    if not record:
        raise NotFoundError(f"记录不存在")

    # 移除不可更新的字段
    record_data.pop('id', None)
    record_data.pop('tenant_id', None)
    record_data.pop('created_at', None)

    # 验证字段
    inspector = inspect(model_class)
    valid_columns = {c.name for c in inspector.columns}

    for key in record_data.keys():
        if key not in valid_columns:
            raise ValidationError(f"字段 {key} 不存在")

    try:
        # 更新记录
        for key, value in record_data.items():
            setattr(record, key, value)

        db.commit()
        db.refresh(record)

        # 转换为字典
        data = record.to_dict() if hasattr(record, 'to_dict') else {
            c.name: getattr(record, c.name)
            for c in record.__table__.columns
        }

        logger.info(f"管理员更新记录 - 表: {table_name}, ID: {record_id}")

        return success_response(
            data=filter_sensitive_fields(data, table_name),
            message="记录更新成功"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"更新记录失败: {str(e)}")
        raise BusinessError(f"更新失败: {str(e)}")


@router.delete("/crud/{table_name}/{record_id}", summary="删除记录")
@audit_log(
    action="admin_delete",
    resource_type="admin_crud",
    record_before=True
)
async def delete_record(
        table_name: str = Path(..., description="表名"),
        record_id: int = Path(..., description="记录ID"),
        current_user: User = Depends(RequireSuperAdmin),
        tenant_id: int = Depends(get_current_tenant_id),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: Session = Depends(get_db),
        request: Request = None
):
    """
    删除记录（仅系统管理员）

    路径参数:
    - table_name: 表名
    - record_id: 记录ID

    返回值:
    - success: 是否成功
    """
    # 获取模型类
    model_class = get_model_class(table_name)

    # 查询记录
    query = db.query(model_class).filter(model_class.id == record_id)

    # 租户隔离
    if hasattr(model_class, 'tenant_id'):
        query = query.filter(model_class.tenant_id == tenant_id)

    record = query.first()

    if not record:
        raise NotFoundError(f"记录不存在")

    try:
        # 如果有is_active字段，执行软删除
        if hasattr(record, 'is_active'):
            record.is_active = False
            db.commit()
            message = "记录已禁用"
        else:
            # 硬删除
            db.delete(record)
            db.commit()
            message = "记录已删除"

        logger.info(f"管理员删除记录 - 表: {table_name}, ID: {record_id}")

        return success_response(
            data={"success": True},
            message=message
        )

    except Exception as e:
        db.rollback()
        logger.error(f"删除记录失败: {str(e)}")
        raise BusinessError(f"删除失败: {str(e)}")


@router.get("/crud/{table_name}/schema", summary="获取表结构")
async def get_table_schema(
        table_name: str = Path(..., description="表名"),
        current_user: User = Depends(RequireSuperAdmin)
):
    """
    获取表结构信息（仅系统管理员）

    路径参数:
    - table_name: 表名

    返回值:
    - columns: 字段列表
    - relationships: 关系列表
    """
    # 获取模型类
    model_class = get_model_class(table_name)

    # 获取字段信息
    inspector = inspect(model_class)
    columns = []

    for column in inspector.columns:
        col_info = {
            "name": column.name,
            "type": str(column.type),
            "nullable": column.nullable,
            "primary_key": column.primary_key,
            "foreign_keys": [str(fk) for fk in column.foreign_keys],
            "comment": column.comment
        }
        columns.append(col_info)

    # 获取关系信息
    relationships = []
    for rel in inspector.relationships:
        rel_info = {
            "name": rel.key,
            "target": rel.mapper.class_.__tablename__,
            "direction": rel.direction.name,
            "uselist": rel.uselist
        }
        relationships.append(rel_info)

    return success_response(
        data={
            "table_name": table_name,
            "columns": columns,
            "relationships": relationships
        }
    )


# ==================== 审计日志 API ====================

from app.services.audit_service import AuditService
from app.schemas.audit_schemas import (
    AuditLogQueryRequest,
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogExportRequest,
    AuditLogCompareResponse,
    ChangeComparisonItem,
)


def check_admin_permission(user: User, db: Session) -> bool:
    """检查用户是否为管理员

    简化实现：检查用户角色或特定权限
    实际项目中应该从角色权限系统获取
    """
    # 这里简化处理，实际应该查询用户角色
    # 假设 id=1 或特定角色为管理员
    return True  # 简化处理，实际需要根据业务逻辑判断


@router.get("/audit-logs", summary="查询审计日志")
async def list_audit_logs(
    query: AuditLogQueryRequest = Depends(),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """查询审计日志列表

    权限:
    - 管理员: 可查看全部日志
    - 普通用户: 只能查看自己的日志
    """
    try:
        # 检查是否为管理员
        is_admin = check_admin_permission(current_user, db)

        logs, total = AuditService.list_audit_logs(
            tenant_id=tenant_id,
            current_user_id=current_user.id,
            is_admin=is_admin,
            query=query,
            db=db,
        )

        # 查询用户姓名映射
        user_ids = {log.actor_user_id for log in logs if log.actor_user_id}
        users = db.query(User.id, User.name).filter(User.id.in_(user_ids)).all()
        user_map = {u.id: u.name for u in users}

        # 组装响应
        items = []
        for log in logs:
            item = AuditLogResponse.from_orm(log)
            item.actor_name = user_map.get(log.actor_user_id)
            items.append(item)

        return success_response(
            data={"items": items, "total": total}
        )

    except Exception as e:
        logger.error(f"查询审计日志失败: {str(e)}")
        raise BusinessError(f"查询失败: {str(e)}")


@router.get("/audit-logs/{log_id}", summary="审计日志详情")
async def get_audit_log_detail(
    log_id: int = Path(..., ge=1, description="日志ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """获取审计日志详情及变更对比"""
    try:
        is_admin = check_admin_permission(current_user, db)

        log = AuditService.get_audit_log_detail(
            log_id=log_id,
            tenant_id=tenant_id,
            current_user_id=current_user.id,
            is_admin=is_admin,
            db=db,
        )

        # 查询用户姓名
        actor_name = None
        if log.actor_user_id:
            user = db.query(User).filter(User.id == log.actor_user_id).first()
            if user:
                actor_name = user.name

        # 计算变更对比
        changes = AuditService.compare_changes(log.before_json, log.after_json)

        return success_response(
            data={
                "log": {
                    **AuditLogResponse.from_orm(log).dict(),
                    "actor_name": actor_name,
                },
                "changes": changes,
            }
        )

    except NotFoundError:
        raise
    except AuthorizationError:
        raise
    except Exception as e:
        logger.error(f"查询审计日志详情失败: {str(e)}")
        raise BusinessError(f"查询失败: {str(e)}")


@router.post("/audit-logs/export", summary="导出审计日志")
async def export_audit_logs(
    request: AuditLogExportRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """导出审计日志为CSV（仅管理员可用）"""
    try:
        # 导出功能仅限管理员
        is_admin = check_admin_permission(current_user, db)
        if not is_admin:
            raise AuthorizationError("只有管理员可以导出审计日志")

        csv_content = AuditService.export_audit_logs_to_csv(
            tenant_id=tenant_id,
            current_user_id=current_user.id,
            is_admin=is_admin,
            request=request,
            db=db,
        )

        # 返回CSV文件
        from fastapi.responses import PlainTextResponse

        filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return PlainTextResponse(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"导出审计日志失败: {str(e)}")
        raise BusinessError(f"导出失败: {str(e)}")



@router.get("/roles/list", summary="获取角色列表（简化版）")
async def list_roles(
        keyword: Optional[str] = Query(None, description="搜索关键词"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页大小"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取角色列表（简化版，用于选择器）

    查询参数:
    - keyword: 搜索关键词（角色名称/描述）
    - page: 页码
    - size: 每页大小

    返回值:
    - items: 角色列表 [{ id, name, description }]
    - total: 总数量
    """
    from app.models.user import Role
    from sqlalchemy import or_

    # 构建查询
    query = db.query(Role).filter(Role.tenant_id == tenant_id)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Role.name.contains(keyword),
                Role.description.contains(keyword)
            )
        )

    # 获取总数
    total = query.count()

    # 分页
    offset = (page - 1) * size
    roles = query.offset(offset).limit(size).all()

    # 构造简化响应数据
    items = [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description
        }
        for role in roles
    ]

    return success_response(data={
        "items": items,
        "total": total
    })


@router.get("/departments/list", summary="获取部门列表（简化版）")
async def list_departments(
        keyword: Optional[str] = Query(None, description="搜索关键词"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页大小"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取部门列表（简化版，用于选择器）

    查询参数:
    - keyword: 搜索关键词（部门名称）
    - page: 页码
    - size: 每页大小

    返回值:
    - items: 部门列表 [{ id, name, type, parent_id }]
    - total: 总数量
    """
    from app.models.user import Department

    # 构建查询
    query = db.query(Department).filter(Department.tenant_id == tenant_id)

    # 关键词搜索
    if keyword:
        query = query.filter(Department.name.contains(keyword))

    # 获取总数
    total = query.count()

    # 分页
    offset = (page - 1) * size
    departments = query.offset(offset).limit(size).all()

    # 构造简化响应数据
    items = [
        {
            "id": dept.id,
            "name": dept.name,
            "type": dept.type,
            "parent_id": dept.parent_id
        }
        for dept in departments
    ]

    return success_response(data={
        "items": items,
        "total": total
    })


@router.get("/positions/list", summary="获取岗位列表（简化版）")
async def list_positions(
        keyword: Optional[str] = Query(None, description="搜索关键词"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页大小"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取岗位列表（简化版，用于选择器）

    查询参数:
    - keyword: 搜索关键词（岗位名称）
    - page: 页码
    - size: 每页大小

    返回值:
    - items: 岗位列表 [{ id, name }]
    - total: 总数量
    """
    from app.models.user import Position

    # 构建查询
    query = db.query(Position).filter(Position.tenant_id == tenant_id)

    # 关键词搜索
    if keyword:
        query = query.filter(Position.name.contains(keyword))

    # 获取总数
    total = query.count()

    # 分页
    offset = (page - 1) * size
    positions = query.offset(offset).limit(size).all()

    # 构造简化响应数据
    items = [
        {
            "id": pos.id,
            "name": pos.name
        }
        for pos in positions
    ]

    return success_response(data={
        "items": items,
        "total": total
    })


@router.get("/groups/list", summary="获取审批群组列表（简化版）")
async def list_groups(
        keyword: Optional[str] = Query(None, description="搜索关键词"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页大小"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取审批群组列表（简化版，用于选择器）

    查询参数:
    - keyword: 搜索关键词（群组名称）
    - page: 页码
    - size: 每页大小

    返回值:
    - items: 群组列表 [{ id, name, department_id }]
    - total: 总数量
    """
    from app.models.user import ApprovalGroup

    # 构建查询
    query = db.query(ApprovalGroup).filter(ApprovalGroup.tenant_id == tenant_id)

    # 关键词搜索
    if keyword:
        query = query.filter(ApprovalGroup.name.contains(keyword))

    # 获取总数
    total = query.count()

    # 分页
    offset = (page - 1) * size
    groups = query.offset(offset).limit(size).all()

    # 构造简化响应数据
    items = [
        {
            "id": group.id,
            "name": group.name,
            "department_id": group.department_id
        }
        for group in groups
    ]

    return success_response(data={
        "items": items,
        "total": total
    })



# ==================== 批量导入 API ====================

from fastapi import UploadFile, File, Form
from fastapi.responses import StreamingResponse
from app.services.batch_import_service import BatchImportService
from app.models.batch_import import BatchImportLog


@router.post("/batch-import", summary="批量导入用户")
@audit_log(action="batch_import_users", resource_type="user")
async def batch_import_users(
    file: UploadFile = File(..., description="Excel文件"),
    default_password: str = Form(default="123456", description="默认密码"),
    default_department_id: Optional[int] = Form(default=None, description="默认部门ID"),
    current_user: User = Depends(RequireAdmin),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    批量导入用户（需要管理员权限）

    参数:
    - file: Excel文件（.xlsx格式）
    - default_password: 默认密码（至少6位）
    - default_department_id: 默认部门ID（可选）

    返回:
    - total_rows: 总行数
    - success_count: 成功数量
    - failed_count: 失败数量
    - results: 每行处理结果
    - default_password: 使用的默认密码
    """
    # 验证文件类型
    filename = file.filename or ""
    if not filename.endswith(('.xlsx', '.xls')):
        raise ValidationError("请上传Excel文件（.xlsx或.xls格式）")

    # 验证密码长度
    if len(default_password) < 6:
        raise ValidationError("默认密码至少6位")

    # 读取文件内容
    file_content = await file.read()

    if not file_content:
        raise ValidationError("文件内容为空")

    try:
        # 执行批量导入
        result = BatchImportService.import_users(
            file_content=file_content,
            filename=filename,
            tenant_id=tenant_id,
            default_password=default_password,
            operator_user_id=current_user.id,
            db=db,
            default_department_id=default_department_id
        )

        return success_response(
            data=result.model_dump(),
            message=f"导入完成: 成功{result.success_count}条, 失败{result.failed_count}条"
        )

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"批量导入失败: {str(e)}")
        raise BusinessError(f"批量导入失败: {str(e)}")


@router.get("/batch-import/template", summary="下载批量导入模板")
async def download_import_template(
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    下载批量导入Excel模板

    返回:
    - Excel文件
    """
    try:
        excel_buffer = BatchImportService.generate_template(tenant_id, db)

        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=batch_import_template.xlsx"}
        )
    except Exception as e:
        logger.error(f"生成模板失败: {str(e)}")
        raise BusinessError(f"生成模板失败: {str(e)}")


@router.get("/batch-import/history", summary="获取导入历史记录")
async def get_import_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(RequireSuperAdmin),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    获取批量导入历史记录

    返回:
    - items: 导入记录列表
    - total: 总数量
    """
    try:
        query = db.query(BatchImportLog).filter(
            BatchImportLog.tenant_id == tenant_id
        ).order_by(BatchImportLog.created_at.desc())

        total = query.count()
        logs = query.offset((page - 1) * size).limit(size).all()

        items = []
        for log in logs:
            items.append({
                "id": log.id,
                "filename": log.filename,
                "total_rows": log.total_rows,
                "success_count": log.success_count,
                "failed_count": log.failed_count,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "created_by": log.created_by
            })

        return success_response(data={"items": items, "total": total})

    except Exception as e:
        logger.error(f"查询导入历史失败: {str(e)}")
        raise BusinessError(f"查询失败: {str(e)}")


@router.get("/batch-import/history/{log_id}", summary="获取导入历史详情")
async def get_import_history_detail(
    log_id: int = Path(..., ge=1, description="记录ID"),
    current_user: User = Depends(RequireSuperAdmin),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    获取导入历史详情（包含错误信息）

    返回:
    - 导入记录详情
    """
    try:
        log = db.query(BatchImportLog).filter(
            BatchImportLog.id == log_id,
            BatchImportLog.tenant_id == tenant_id
        ).first()

        if not log:
            raise NotFoundError("导入记录不存在")

        import json
        error_details = []
        if log.error_details:
            error_details = json.loads(log.error_details)

        return success_response(data={
            "id": log.id,
            "filename": log.filename,
            "total_rows": log.total_rows,
            "success_count": log.success_count,
            "failed_count": log.failed_count,
            "default_password": log.default_password,
            "error_details": error_details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "created_by": log.created_by
        })

    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"查询导入详情失败: {str(e)}")
        raise BusinessError(f"查询失败: {str(e)}")


# ==================== 用户管理 API ====================

from app.schemas.user_management import (
    UserListItem, UserListQuery, UserUpdateRequest,
    ManageableScope, ManageableDepartment, ManageablePosition,
    ImportPreviewResponse, ImportConfirmRequest
)
from app.models.user import (
    UserDepartment, UserDepartmentPost, UserRole, Role, Position, Department, DepartmentPost, DepartmentPostLevel
)
from sqlalchemy import and_

# 角色名称映射：英文 -> 中文（用于前端传值与数据库角色名称的转换）
ROLE_NAME_MAP = {
    "admin": "管理员",
    "teacher": "老师",
    "student": "学生",
    "管理员": "管理员",
    "老师": "老师",
    "学生": "学生",
    "系统管理员": "系统管理员",
    "租户管理员": "租户管理员",
}


def normalize_role_name(role_name: str) -> str:
    """
    将角色名称标准化为数据库中使用的中文名称

    Args:
        role_name: 角色名称（可以是英文或中文）

    Returns:
        str: 标准化后的中文角色名称
    """
    return ROLE_NAME_MAP.get(role_name, role_name)


def get_all_child_department_ids(dept_ids: List[int], tenant_id: int, db: Session) -> List[int]:
    """
    递归获取所有子部门ID（包含传入的部门ID本身）

    Args:
        dept_ids: 父部门ID列表
        tenant_id: 租户ID
        db: 数据库会话

    Returns:
        List[int]: 包含所有子部门的ID列表
    """
    from app.models.user import Department

    all_dept_ids = set(dept_ids)
    queue = list(dept_ids)

    while queue:
        current_id = queue.pop(0)
        # 查询当前部门的所有直接子部门
        children = db.query(Department.id).filter(
            Department.tenant_id == tenant_id,
            Department.parent_id == current_id
        ).all()

        for child in children:
            if child.id not in all_dept_ids:
                all_dept_ids.add(child.id)
                queue.append(child.id)

    return list(all_dept_ids)


def check_user_manage_permission(
    current_user: User,
    target_user_id: int,
    tenant_id: int,
    db: Session
) -> bool:
    """
    检查用户是否有权限管理目标用户

    权限规则：
    1. 管理员可管理所有用户
    2. 普通用户只能管理自己部门下岗位层级低于自己的用户
    3. 没有部门/岗位的普通用户无权管理

    Returns:
        bool: 是否有权限
    """
    # 检查是否为管理员（兼容多种角色名称）
    admin_role_names = ["系统管理员", "租户管理员", "admin", "Admin", "管理员"]
    
    admin_roles = db.query(Role).join(UserRole).filter(
        UserRole.user_id == current_user.id,
        UserRole.tenant_id == tenant_id,
        Role.name.in_(admin_role_names)
    ).first()

    if admin_roles:
        return True

    # 检查当前用户是否有部门和岗位
    current_user_dept = db.query(UserDepartment).filter(
        UserDepartment.user_id == current_user.id,
        UserDepartment.tenant_id == tenant_id,
        UserDepartment.is_primary == True
    ).first()

    if not current_user_dept:
        return False

    # 检查目标用户是否在同一部门
    target_user_dept = db.query(UserDepartment).filter(
        UserDepartment.user_id == target_user_id,
        UserDepartment.tenant_id == tenant_id,
        UserDepartment.department_id == current_user_dept.department_id
    ).first()

    if not target_user_dept:
        return False

    # 检查岗位层级（简化实现：有岗位的可以管理没有岗位的）
    current_has_post = db.query(UserDepartmentPost).filter(
        UserDepartmentPost.user_id == current_user.id,
        UserDepartmentPost.tenant_id == tenant_id
    ).first()

    target_has_post = db.query(UserDepartmentPost).filter(
        UserDepartmentPost.user_id == target_user_id,
        UserDepartmentPost.tenant_id == tenant_id
    ).first()

    # 有岗位的可以管理没有岗位的
    if current_has_post and not target_has_post:
        return True

    return False


def get_manageable_user_ids(
    current_user: User,
    tenant_id: int,
    db: Session
) -> Optional[List[int]]:
    """
    获取当前用户可管理的用户ID列表

    Returns:
        Optional[List[int]]: 可管理的用户ID列表，管理员返回None表示无限制
        
    权限规则：
    1. 管理员可管理所有用户
    2. 非管理员用户有岗位时，可以管理同一部门下的所有用户
    3. 没有部门/岗位的用户只能查看自己
    """
    from app.models.user import User, UserDepartment, UserDepartmentPost, UserPosition, Role, UserRole
    
    # 检查是否为管理员（兼容多种角色名称）
    admin_role_names = ["系统管理员", "租户管理员", "admin", "Admin", "管理员"]
    
    # 检查是否为管理员
    admin_roles = db.query(Role).join(UserRole).filter(
        UserRole.user_id == current_user.id,
        UserRole.tenant_id == tenant_id,
        Role.name.in_(admin_role_names)
    ).first()

    if admin_roles:
        return None  # 管理员无限制

    # 获取当前用户的部门
    current_user_depts = db.query(UserDepartment).filter(
        UserDepartment.user_id == current_user.id,
        UserDepartment.tenant_id == tenant_id
    ).all()

    if not current_user_depts:
        # 尝试从 User 表的 department_id 字段获取主属部门
        if current_user.department_id:
            current_user_depts = db.query(UserDepartment).filter(
                UserDepartment.user_id == current_user.id,
                UserDepartment.tenant_id == tenant_id,
                UserDepartment.department_id == current_user.department_id
            ).all()
        
        # 如果仍然没有部门记录，只能查看自己
        if not current_user_depts:
            return [current_user.id]

    dept_ids = [ud.department_id for ud in current_user_depts]

    # 扩展部门ID列表，包含所有子部门
    dept_ids = get_all_child_department_ids(dept_ids, tenant_id, db)

    # 获取当前用户的岗位
    current_user_posts = db.query(UserDepartmentPost).filter(
        UserDepartmentPost.user_id == current_user.id,
        UserDepartmentPost.tenant_id == tenant_id
    ).all()

    # 如果 UserDepartmentPost 表没有数据，尝试从 UserPosition 表获取（兼容旧数据）
    if not current_user_posts:
        user_positions = db.query(UserPosition).filter(
            UserPosition.user_id == current_user.id,
            UserPosition.tenant_id == tenant_id
        ).all()
        
        # 如果找到 UserPosition 记录，使用用户的主属部门构建岗位信息
        if user_positions and current_user.department_id:
            for up in user_positions:
                # 创建一个兼容的对象来存储部门和岗位信息
                class FallbackPost:
                    def __init__(self, dept_id, post_id):
                        self.department_id = dept_id
                        self.post_id = post_id
                
                current_user_posts.append(FallbackPost(current_user.department_id, up.position_id))

    if not current_user_posts:
        # 没有岗位，只能查看自己
        return [current_user.id]

    # 获取当前用户岗位的最低层级（数值越小层级越高）
    current_user_levels = []
    for up in current_user_posts:
        level_info = db.query(DepartmentPostLevel).filter(
            DepartmentPostLevel.tenant_id == tenant_id,
            DepartmentPostLevel.department_id == up.department_id,
            DepartmentPostLevel.post_id == up.post_id
        ).first()
        if level_info:
            current_user_levels.append(level_info.level)
    
    # 如果没有层级信息，返回同一部门的用户
    if not current_user_levels:
        manageable_user_ids = set()
        
        # 优先从 UserDepartment 表查询
        dept_users = db.query(UserDepartment).filter(
            UserDepartment.tenant_id == tenant_id,
            UserDepartment.department_id.in_(dept_ids)
        ).all()
        
        if dept_users:
            for dept_user in dept_users:
                manageable_user_ids.add(dept_user.user_id)
        else:
            # 如果 UserDepartment 表没有记录，尝试从 User 表的 department_id 字段查询
            for dept_id in dept_ids:
                users_in_dept = db.query(User).filter(
                    User.tenant_id == tenant_id,
                    User.department_id == dept_id
                ).all()
                for user in users_in_dept:
                    manageable_user_ids.add(user.id)
        
        manageable_user_ids.add(current_user.id)
        return list(manageable_user_ids)
    
    min_user_level = min(current_user_levels)
    
    # 获取同一部门下岗位层级低于当前用户的用户
    manageable_user_ids = set()
    
    # 获取这些部门下的所有用户
    dept_users = db.query(UserDepartment).filter(
        UserDepartment.tenant_id == tenant_id,
        UserDepartment.department_id.in_(dept_ids)
    ).all()
    
    for dept_user in dept_users:
        # 跳过自己
        if dept_user.user_id == current_user.id:
            manageable_user_ids.add(dept_user.user_id)
            continue
        
        # 获取目标用户的岗位层级
        target_user_posts = db.query(UserDepartmentPost).filter(
            UserDepartmentPost.user_id == dept_user.user_id,
            UserDepartmentPost.tenant_id == tenant_id,
            UserDepartmentPost.department_id == dept_user.department_id
        ).all()
        
        # 如果 UserDepartmentPost 表没有数据，尝试从 UserPosition 表获取（兼容旧数据）
        if not target_user_posts:
            target_user_positions = db.query(UserPosition).filter(
                UserPosition.user_id == dept_user.user_id,
                UserPosition.tenant_id == tenant_id
            ).all()
            
            # 如果找到 UserPosition 记录，使用部门信息构建兼容对象
            if target_user_positions:
                class TargetFallbackPost:
                    def __init__(self, dept_id, post_id):
                        self.department_id = dept_id
                        self.post_id = post_id
                
                for tup in target_user_positions:
                    target_user_posts.append(TargetFallbackPost(dept_user.department_id, tup.position_id))

        # 过滤掉 post_id 为 None 的记录
        target_user_posts = [p for p in target_user_posts if p.post_id is not None]

        # 如果目标用户没有岗位，视为最低层级（学生等），可以被查看
        if not target_user_posts:
            manageable_user_ids.add(dept_user.user_id)
            continue

        # 检查目标用户是否有低于当前用户的岗位
        target_has_lower_level = False
        for tup in target_user_posts:
            level_info = db.query(DepartmentPostLevel).filter(
                DepartmentPostLevel.tenant_id == tenant_id,
                DepartmentPostLevel.department_id == tup.department_id,
                DepartmentPostLevel.post_id == tup.post_id
            ).first()
            if level_info and level_info.level > min_user_level:
                target_has_lower_level = True
                break

        if target_has_lower_level:
            manageable_user_ids.add(dept_user.user_id)
    
    # 确保包含自己
    manageable_user_ids.add(current_user.id)
    
    return list(manageable_user_ids)


@router.get("/users", summary="用户管理列表")
async def list_users(
    query: UserListQuery = Depends(),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    获取用户管理列表

    权限：
    - 管理员可查看所有用户
    - 普通用户只能查看自己部门下岗位层级低于自己的用户
    - 没有部门/岗位的普通用户无权查看

    查询参数：
    - page: 页码
    - size: 每页大小
    - department_id: 部门ID筛选
    - position_id: 岗位ID筛选
    - role: 角色筛选
    - keyword: 关键词搜索（账号/姓名）
    - is_active: 是否启用
    """
    try:
        # 构建基础查询
        base_query = db.query(User).filter(User.tenant_id == tenant_id)

        # 权限过滤
        manageable_ids = get_manageable_user_ids(current_user, tenant_id, db)
        if manageable_ids is not None:
            if not manageable_ids:
                return paginated_response(items=[], total=0, page=query.page, size=query.size)
            base_query = base_query.filter(User.id.in_(manageable_ids))

        # 关键词搜索
        if query.keyword:
            base_query = base_query.filter(
                or_(
                    User.account.contains(query.keyword),
                    User.name.contains(query.keyword)
                )
            )

        # 是否启用筛选
        if query.is_active is not None:
            base_query = base_query.filter(User.is_active == query.is_active)

        # 部门筛选
        if query.department_id:
            dept_user_ids = db.query(UserDepartment.user_id).filter(
                UserDepartment.tenant_id == tenant_id,
                UserDepartment.department_id == query.department_id
            ).subquery()
            base_query = base_query.filter(User.id.in_(dept_user_ids))

        # 岗位筛选
        if query.position_id:
            post_user_ids = db.query(UserDepartmentPost.user_id).filter(
                UserDepartmentPost.tenant_id == tenant_id,
                UserDepartmentPost.post_id == query.position_id
            ).subquery()
            base_query = base_query.filter(User.id.in_(post_user_ids))

        # 角色筛选
        if query.role:
            # 将前端传入的英文角色名转换为中文
            normalized_role = normalize_role_name(query.role)
            role_user_ids = db.query(UserRole.user_id).join(Role).filter(
                UserRole.tenant_id == tenant_id,
                Role.name == normalized_role
            ).subquery()
            base_query = base_query.filter(User.id.in_(role_user_ids))

        # 获取总数
        total = base_query.count()

        # 分页
        offset = (query.page - 1) * query.size
        users = base_query.order_by(User.id.desc()).offset(offset).limit(query.size).all()

        # 获取用户ID列表
        user_ids = [u.id for u in users]

        # 批量获取部门信息
        # 1. 优先获取主部门 (is_primary=True)
        user_depts_primary = db.query(UserDepartment, Department).join(
            Department, UserDepartment.department_id == Department.id
        ).filter(
            UserDepartment.user_id.in_(user_ids),
            UserDepartment.tenant_id == tenant_id,
            UserDepartment.is_primary == True
        ).all()
        dept_map = {ud.user_id: dept for ud, dept in user_depts_primary}
        
        # 2. 对于没有主部门的用户，从 UserDepartmentPost 获取部门（通过岗位关联的部门）
        users_without_primary = [uid for uid in user_ids if uid not in dept_map]
        if users_without_primary:
            user_post_depts = db.query(
                UserDepartmentPost.user_id,
                Department
            ).join(
                Department, UserDepartmentPost.department_id == Department.id
            ).filter(
                UserDepartmentPost.user_id.in_(users_without_primary),
                UserDepartmentPost.tenant_id == tenant_id
            ).distinct(UserDepartmentPost.user_id).all()
            
            for uid, dept in user_post_depts:
                if uid not in dept_map:
                    dept_map[uid] = dept
        
        # 3. 对于仍然没有部门的用户，获取任意一个关联的部门
        users_still_without_dept = [uid for uid in user_ids if uid not in dept_map]
        if users_still_without_dept:
            user_depts_any = db.query(UserDepartment.user_id, UserDepartment, Department).join(
                Department, UserDepartment.department_id == Department.id
            ).filter(
                UserDepartment.user_id.in_(users_still_without_dept),
                UserDepartment.tenant_id == tenant_id
            ).all()
            for uid, ud, dept in user_depts_any:
                if uid not in dept_map:
                    dept_map[uid] = dept

        # 批量获取角色信息
        user_roles = db.query(UserRole, Role).join(
            Role, UserRole.role_id == Role.id
        ).filter(
            UserRole.user_id.in_(user_ids),
            UserRole.tenant_id == tenant_id
        ).all()
        role_map = {}
        for ur, role in user_roles:
            if ur.user_id not in role_map:
                role_map[ur.user_id] = []
            role_map[ur.user_id].append(role.name)

        # 批量获取岗位信息
        user_posts = db.query(UserDepartmentPost, Position).join(
            Position, UserDepartmentPost.post_id == Position.id
        ).filter(
            UserDepartmentPost.user_id.in_(user_ids),
            UserDepartmentPost.tenant_id == tenant_id
        ).all()
        post_map = {}
        for udp, pos in user_posts:
            if udp.user_id not in post_map:
                post_map[udp.user_id] = []
            post_map[udp.user_id].append(pos.name)

        # 构建响应
        items = []
        for user in users:
            dept = dept_map.get(user.id)
            items.append(UserListItem(
                id=user.id,
                account=user.account,
                name=user.name,
                email=user.email,
                phone=user.phone,
                is_active=user.is_active,
                department_name=dept.name if dept else None,
                department_id=dept.id if dept else None,
                roles=role_map.get(user.id, []),
                positions=post_map.get(user.id, []),
                created_at=user.created_at
            ))

        return paginated_response(
            items=[item.model_dump() for item in items],
            total=total,
            page=query.page,
            size=query.size
        )

    except Exception as e:
        logger.error(f"查询用户列表失败: {str(e)}")
        raise BusinessError(f"查询失败: {str(e)}")


@router.put("/users/{user_id}", summary="更新用户信息")
@audit_log(action="update_user", resource_type="user", record_before=True, record_after=True)
async def update_user(
    user_id: int = Path(..., ge=1, description="用户ID"),
    update_data: UserUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    更新用户信息

    权限：同列表API

    请求体：
    - name: 姓名
    - email: 邮箱
    - phone: 手机号
    - department_id: 主属部门ID
    - position_ids: 岗位ID列表
    - role: 角色标识
    - is_active: 是否启用
    """
    try:
        # 检查权限
        if not check_user_manage_permission(current_user, user_id, tenant_id, db):
            raise AuthorizationError("无权管理该用户")

        # 查询用户
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id
        ).first()

        if not user:
            raise NotFoundError("用户不存在")

        # 更新基本字段
        if update_data.name is not None:
            user.name = update_data.name
        if update_data.email is not None:
            user.email = update_data.email
        if update_data.phone is not None:
            user.phone = update_data.phone
        if update_data.is_active is not None:
            user.is_active = update_data.is_active

        # 更新部门
        if update_data.department_id is not None:
            # 检查部门是否存在
            dept = db.query(Department).filter(
                Department.id == update_data.department_id,
                Department.tenant_id == tenant_id
            ).first()
            if not dept:
                raise NotFoundError("部门不存在")

            # 更新用户的主属部门
            user.department_id = update_data.department_id

            # 更新用户-部门关联
            existing_dept = db.query(UserDepartment).filter(
                UserDepartment.user_id == user_id,
                UserDepartment.tenant_id == tenant_id,
                UserDepartment.is_primary == True
            ).first()

            if existing_dept:
                existing_dept.department_id = update_data.department_id
            else:
                new_dept = UserDepartment(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    department_id=update_data.department_id,
                    is_primary=True
                )
                db.add(new_dept)

        # 更新岗位
        if update_data.position_ids is not None:
            # 删除现有岗位关联
            db.query(UserDepartmentPost).filter(
                UserDepartmentPost.user_id == user_id,
                UserDepartmentPost.tenant_id == tenant_id
            ).delete()

            # 添加新岗位关联
            dept_id = update_data.department_id or user.department_id
            if dept_id and update_data.position_ids:
                for pos_id in update_data.position_ids:
                    # 检查岗位是否存在
                    pos = db.query(Position).filter(
                        Position.id == pos_id,
                        Position.tenant_id == tenant_id
                    ).first()
                    if not pos:
                        raise NotFoundError(f"岗位ID {pos_id} 不存在")

                    new_post = UserDepartmentPost(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        department_id=dept_id,
                        post_id=pos_id
                    )
                    db.add(new_post)

        # 更新角色
        if update_data.role is not None:
            # 删除现有角色关联
            db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.tenant_id == tenant_id
            ).delete()

            # 添加新角色
            if update_data.role:
                # 将前端传入的英文角色名转换为中文
                normalized_role = normalize_role_name(update_data.role)
                role = db.query(Role).filter(
                    Role.tenant_id == tenant_id,
                    Role.name == normalized_role
                ).first()
                if not role:
                    raise NotFoundError(f"角色 '{update_data.role}' 不存在")

                new_role = UserRole(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    role_id=role.id
                )
                db.add(new_role)

        db.commit()
        db.refresh(user)

        logger.info(f"更新用户信息: user_id={user_id}")

        return success_response(
            data={"id": user.id, "account": user.account, "name": user.name},
            message="用户信息更新成功"
        )

    except NotFoundError:
        raise
    except AuthorizationError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新用户信息失败: {str(e)}")
        raise BusinessError(f"更新失败: {str(e)}")


@router.delete("/users/{user_id}", summary="删除用户")
@audit_log(action="delete_user", resource_type="user", record_before=True)
async def delete_user(
    user_id: int = Path(..., ge=1, description="用户ID"),
    current_user: User = Depends(RequireSuperAdmin),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    删除用户（仅管理员可用）

    路径参数：
    - user_id: 用户ID
    """
    try:
        # 查询用户
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id
        ).first()

        if not user:
            raise NotFoundError("用户不存在")

        # 软删除（设置is_active为False）
        user.is_active = False
        db.commit()

        logger.info(f"删除用户: user_id={user_id}")

        return success_response(
            data={"id": user.id, "account": user.account},
            message="用户已删除"
        )

    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除用户失败: {str(e)}")
        raise BusinessError(f"删除失败: {str(e)}")


@router.get("/manageable-scope", summary="可管理范围")
async def get_manageable_scope(
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    返回当前用户可管理的部门和岗位列表

    权限：所有用户均可调用，返回自己可管理的范围
    """
    from app.schemas.user_management import ManageableScope, ManageableDepartment, ManageablePosition, CurrentUserPosition
    from app.models.user import UserPosition
    
    try:
        # 检查是否为管理员（兼容多种角色名称）
        admin_role_names = ["系统管理员", "租户管理员", "admin", "Admin", "管理员"]
        
        # 先尝试通过角色表查询
        admin_roles = db.query(Role).join(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.tenant_id == tenant_id,
            Role.name.in_(admin_role_names)
        ).first()

        is_admin = admin_roles is not None

        # 如果通过角色表没找到，尝试检查用户是否没有任何部门限制
        # 如果用户可以访问所有部门，也认为是管理员
        if not is_admin:
            # 检查用户是否有部门（从 UserDepartment 表或 User.department_id 字段）
            user_has_any_dept = db.query(UserDepartment).filter(
                UserDepartment.user_id == current_user.id,
                UserDepartment.tenant_id == tenant_id
            ).first()
            
            # 如果 UserDepartment 表没有记录，检查 User 表的 department_id 字段
            if not user_has_any_dept and not current_user.department_id:
                # 没有部门记录也没有主属部门，可能是管理员
                # 但还需要检查是否有岗位记录
                user_has_position = db.query(UserPosition).filter(
                    UserPosition.user_id == current_user.id,
                    UserPosition.tenant_id == tenant_id
                ).first()
                
                # 只有既没有部门也没有岗位，才认为是管理员
                is_admin = user_has_position is None

        # 获取当前用户的部门和岗位信息
        current_user_dept = None
        current_user_positions = []
        
        # 获取用户所属部门
        user_depts = db.query(UserDepartment).filter(
            UserDepartment.user_id == current_user.id,
            UserDepartment.tenant_id == tenant_id
        ).all()
        
        if user_depts:
            # 取第一个部门作为主部门
            primary_dept = db.query(Department).filter(
                Department.id == user_depts[0].department_id
            ).first()
            if primary_dept:
                current_user_dept = ManageableDepartment(
                    id=primary_dept.id,
                    name=primary_dept.name,
                    type=primary_dept.type,
                    parent_id=primary_dept.parent_id,
                    posts=[]
                )
        
        # 获取用户岗位
        user_posts = db.query(UserDepartmentPost).filter(
            UserDepartmentPost.user_id == current_user.id,
            UserDepartmentPost.tenant_id == tenant_id
        ).all()
        
        # 如果 UserDepartmentPost 表没有数据，尝试从 UserPosition 表获取（兼容旧数据）
        if not user_posts:
            user_positions = db.query(UserPosition).filter(
                UserPosition.user_id == current_user.id,
                UserPosition.tenant_id == tenant_id
            ).all()
            
            # 如果找到 UserPosition 记录，使用用户的主属部门构建岗位信息
            if user_positions and current_user.department_id:
                for up in user_positions:
                    # 创建一个兼容的对象来存储部门和岗位信息
                    class FallbackPost:
                        def __init__(self, dept_id, post_id):
                            self.department_id = dept_id
                            self.post_id = post_id
                    
                    user_posts.append(FallbackPost(current_user.department_id, up.position_id))
        
        for up in user_posts:
            if up.post_id:
                post = db.query(Position).filter(Position.id == up.post_id).first()
                dept = db.query(Department).filter(Department.id == up.department_id).first()
                if post and dept:
                    current_user_positions.append(CurrentUserPosition(
                        id=post.id,
                        name=post.name,
                        department_id=dept.id,
                        department_name=dept.name
                    ))

        if is_admin:
            # 管理员可以管理所有部门和岗位
            departments = db.query(Department).filter(
                Department.tenant_id == tenant_id
            ).all()

            # 为每个部门添加该部门定义的岗位（通过DepartmentPost表）
            dept_list = []
            for d in departments:
                # 获取该部门通过DepartmentPost表定义的岗位
                d_dept_posts = db.query(DepartmentPost).filter(
                    DepartmentPost.department_id == d.id,
                    DepartmentPost.tenant_id == tenant_id
                ).all()
                
                d_post_ids = [dp.post_id for dp in d_dept_posts if dp.post_id]
                
                # 如果DepartmentPost表中有记录，获取这些岗位
                if d_post_ids:
                    # 获取这些岗位的信息
                    d_posts = db.query(Position).filter(
                        Position.id.in_(d_post_ids)
                    ).all()
                    
                    # 获取该部门的岗位层级信息
                    dept_post_levels = db.query(DepartmentPostLevel).filter(
                        DepartmentPostLevel.tenant_id == tenant_id,
                        DepartmentPostLevel.department_id == d.id
                    ).all()
                    post_level_map = {dp.post_id: dp.level for dp in dept_post_levels}
                    
                    dept_position_list = []
                    for p in d_posts:
                        level = post_level_map.get(p.id)
                        dept_position_list.append(ManageablePosition(
                            id=p.id,
                            name=p.name,
                            level=level
                        ))
                    
                    # 按层级排序
                    dept_position_list.sort(key=lambda x: (x.level if x.level is not None else 999, x.name))
                else:
                    # 如果DepartmentPost表中没有记录，该部门没有可导入岗位
                    dept_position_list = []
                
                dept_list.append(ManageableDepartment(
                    id=d.id,
                    name=d.name,
                    type=d.type,
                    parent_id=d.parent_id,
                    posts=dept_position_list
                ))
            
            # 获取所有岗位（用于全局positions字段）
            positions = db.query(Position).filter(
                Position.tenant_id == tenant_id
            ).all()
        else:
            # 普通用户只能管理自己部门下的岗位
            dept_ids = [ud.department_id for ud in user_depts]
            
            # 如果UserDepartment表中没有记录，尝试从User表的department_id字段获取
            if not dept_ids and current_user.department_id:
                dept_ids = [current_user.department_id]

            if not dept_ids:
                dept_list = []
                positions = []
            else:
                # 获取当前用户的最小层级（数值越小层级越高）
                min_user_level = None
                for dept_id in dept_ids:
                    for pos in current_user_positions:
                        level_info = db.query(DepartmentPostLevel).filter(
                            DepartmentPostLevel.tenant_id == tenant_id,
                            DepartmentPostLevel.department_id == dept_id,
                            DepartmentPostLevel.post_id == pos.id
                        ).first()
                        if level_info:
                            if min_user_level is None or level_info.level < min_user_level:
                                min_user_level = level_info.level

                departments = db.query(Department).filter(
                    Department.id.in_(dept_ids)
                ).all()

                # 使用DepartmentPost表获取部门下定义的所有岗位
                dept_posts = db.query(DepartmentPost).filter(
                    DepartmentPost.tenant_id == tenant_id,
                    DepartmentPost.department_id.in_(dept_ids)
                ).all()

                post_ids = list(set([dp.post_id for dp in dept_posts if dp.post_id]))
                
                # 如果DepartmentPost表中没有记录，返回所有岗位
                if not post_ids:
                    positions = db.query(Position).filter(
                        Position.tenant_id == tenant_id
                    ).all()
                else:
                    positions = db.query(Position).filter(
                        Position.id.in_(post_ids)
                    ).all()
                
                # 为每个部门添加岗位列表
                dept_list = []
                for d in departments:
                    # 获取该部门下的所有岗位（通过DepartmentPost表）
                    d_dept_posts = db.query(DepartmentPost).filter(
                        DepartmentPost.department_id == d.id,
                        DepartmentPost.tenant_id == tenant_id
                    ).all()
                    
                    d_post_ids = [dp.post_id for dp in d_dept_posts if dp.post_id]
                    
                    # 如果DepartmentPost表中没有记录，返回所有岗位
                    if not d_post_ids:
                        d_posts = db.query(Position).filter(
                            Position.tenant_id == tenant_id
                        ).all()
                    else:
                        d_posts = db.query(Position).filter(
                            Position.id.in_(d_post_ids)
                        ).all()
                    
                    # 获取该部门的岗位层级信息
                    dept_post_levels = db.query(DepartmentPostLevel).filter(
                        DepartmentPostLevel.tenant_id == tenant_id,
                        DepartmentPostLevel.department_id == d.id
                    ).all()
                    post_level_map = {dp.post_id: dp.level for dp in dept_post_levels}
                    
                    dept_position_list = []
                    for p in d_posts:
                        level = post_level_map.get(p.id)
                        # 只添加层级低于当前用户的岗位（数值越大层级越低）
                        # 如果没有当前用户的层级信息，则显示所有岗位
                        if min_user_level is None or (level is not None and level > min_user_level):
                            dept_position_list.append(ManageablePosition(
                                id=p.id,
                                name=p.name,
                                level=level
                            ))
                    
                    # 按层级排序
                    dept_position_list.sort(key=lambda x: (x.level if x.level is not None else 999, x.name))
                    
                    dept_list.append(ManageableDepartment(
                        id=d.id,
                        name=d.name,
                        type=d.type,
                        parent_id=d.parent_id,
                        posts=dept_position_list
                    ))

        return success_response(
            data=ManageableScope(
                departments=dept_list,
                positions=[ManageablePosition(
                    id=p.id,
                    name=p.name,
                    level=None
                ) for p in positions],
                is_admin=is_admin,
                current_user_department=current_user_dept,
                current_user_positions=current_user_positions
            ).model_dump()
        )

    except Exception as e:
        logger.error(f"获取可管理范围失败: {str(e)}")
        raise BusinessError(f"查询失败: {str(e)}")


# ==================== 用户导入预览/确认 API ====================

@router.post("/users/preview-import", summary="预览导入用户")
async def preview_import_users(
    file: UploadFile = File(..., description="Excel文件"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    预览导入用户数据

    参数：
    - file: Excel文件（.xlsx格式）

    返回：
    - preview_key: 预览key（用于确认导入）
    - total_rows: 总行数
    - valid_rows: 有效行数
    - invalid_rows: 无效行数
    - rows: 每行预览数据
    """
    # 验证文件类型
    filename = file.filename or ""
    if not filename.endswith(('.xlsx', '.xls')):
        raise ValidationError("请上传Excel文件（.xlsx或.xls格式）")

    # 读取文件内容
    file_content = await file.read()

    if not file_content:
        raise ValidationError("文件内容为空")

    try:
        result = await BatchImportService.preview_import(
            file_content=file_content,
            tenant_id=tenant_id,
            db=db
        )

        return success_response(
            data=result.model_dump(),
            message=f"预览成功: 共{result.total_rows}行，有效{result.valid_rows}行"
        )

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"预览导入失败: {str(e)}")
        raise BusinessError(f"预览失败: {str(e)}")


@router.post("/users/confirm-import", summary="确认导入用户")
@audit_log(action="confirm_import_users", resource_type="user")
async def confirm_import_users(
    request: ImportConfirmRequest = ...,
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    确认导入用户数据

    参数：
    - preview_key: 预览key
    - selected_rows: 选中的行索引列表（为空则导入全部有效行）

    返回：
    - total_rows: 导入行数
    - success_count: 成功数量
    - failed_count: 失败数量
    - results: 每行处理结果
    """
    try:
        result = await BatchImportService.confirm_import(
            preview_key=request.preview_key,
            selected_rows=request.selected_rows,
            tenant_id=tenant_id,
            operator_user_id=current_user.id,
            db=db
        )

        return success_response(
            data=result.model_dump(),
            message=f"导入完成: 成功{result.success_count}条，失败{result.failed_count}条"
        )

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"确认导入失败: {str(e)}")
        raise BusinessError(f"导入失败: {str(e)}")
