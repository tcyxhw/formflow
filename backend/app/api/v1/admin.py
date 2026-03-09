# app/api/v1/admin.py
"""
管理员通用CRUD接口
提供对白名单内表的通用增删改查功能
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
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
from app.api.deps import RequireSuperAdmin, get_current_tenant_id, get_current_user
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
        order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="排序方向"),
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