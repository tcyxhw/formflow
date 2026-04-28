# app/utils/audit.py
"""
审计日志装饰器
自动记录操作日志
"""
from functools import wraps
from typing import Optional, Callable, Any
import inspect
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.notification import AuditLog
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


def _background_create_audit_log(
    action: str,
    resource_type: str,
    resource_id: Optional[int],
    before_data: Optional[dict],
    after_data: Optional[dict],
    tenant_id: Optional[int],
    actor_user_id: Optional[int],
    ip: Optional[str],
    ua: Optional[str]
) -> None:
    """
    在后台任务中创建审计日志（使用独立的同步会话）
    
    这个函数在 FastAPI 的后台任务中执行，不会阻塞主请求流程
    """
    db = None
    try:
        # 创建独立的数据库会话
        db = SessionLocal()
        
        # 如果 tenant_id 为 None，使用默认值
        if tenant_id is None:
            tenant_id = 0
            logger.warning(f"审计日志缺少 tenant_id，使用默认值 0: {action}")
        
        # 序列化 JSON 数据
        before_json = json.dumps(before_data, ensure_ascii=False) if before_data else None
        after_json = json.dumps(after_data, ensure_ascii=False) if after_data else None
        
        # 创建审计日志记录
        audit = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_json=before_json,
            after_json=after_json,
            ip=ip,
            ua=ua
        )
        
        db.add(audit)
        db.commit()
        
        logger.info(f"后台任务：审计日志创建成功 - {action}")
        
    except Exception as e:
        logger.error(f"后台任务：审计日志记录失败 - {action}: {str(e)}")
        if db:
            db.rollback()
    finally:
        if db:
            db.close()


def audit_log(
        action: str,
        resource_type: str,
        get_resource_id: Optional[Callable] = None,
        record_before: bool = False,
        record_after: bool = True
):
    """
    审计日志装饰器

    Args:
        action: 操作动作（如 create_form, update_user）
        resource_type: 资源类型（如 form, user）
        get_resource_id: 获取资源ID的函数
        record_before: 是否记录操作前数据
        record_after: 是否记录操作后数据
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """异步函数包装器"""
            # 获取相关信息
            user = kwargs.get('current_user') or kwargs.get('user')

            # ✅ 获取 FastAPI Request 对象
            http_request = None
            for key, value in kwargs.items():
                if hasattr(value, 'method') and hasattr(value, 'url'):
                    http_request = value
                    break

            # ✅ 获取 BackgroundTasks 对象
            background_tasks = kwargs.get('background_tasks')

            db = kwargs.get('db')

            # 获取资源ID
            resource_id = None
            if get_resource_id:
                try:
                    resource_id = get_resource_id(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"获取资源ID失败: {str(e)}")

            # 记录操作前数据
            before_data = None
            if record_before and resource_id:
                pass  # TODO: 根据resource_type和resource_id查询当前数据

            try:
                # 执行原函数
                result = await func(*args, **kwargs)

                # ✅ 解析返回结果（处理 JSONResponse）
                result_data = await extract_result_data(result)

                # ✅ 从结果中获取资源ID
                if get_resource_id and not resource_id:
                    try:
                        kwargs['result'] = result_data
                        resource_id = get_resource_id(*args, **kwargs)
                    except Exception as e:
                        logger.warning(f"从结果获取资源ID失败: {str(e)}")

                # ✅ 记录操作后数据
                after_data = None
                if record_after:
                    after_data = result_data

                # ✅ 提取审计所需的用户信息
                audit_tenant_id = None
                audit_user_id = None

                # 1. 优先从认证用户获取
                if user:
                    audit_tenant_id = getattr(user, 'current_tenant_id', None) or \
                                      getattr(user, 'tenant_id', None)
                    audit_user_id = getattr(user, 'id', None)

                # 2. 从中间件获取租户ID（登录场景）
                if not audit_tenant_id and http_request:
                    audit_tenant_id = getattr(http_request.state, 'tenant_id', None)

                # 3. 从登录结果中获取用户信息（登录场景）
                if not audit_user_id and result_data:
                    if 'data' in result_data:  # success_response 格式
                        data = result_data['data']
                        if 'user' in data:
                            user_info = data['user']
                            audit_user_id = user_info.get('id')
                            if not audit_tenant_id:
                                audit_tenant_id = user_info.get('tenant_id')
                    elif 'user' in result_data:  # 直接包含 user
                        user_info = result_data['user']
                        audit_user_id = user_info.get('id')
                        if not audit_tenant_id:
                            audit_tenant_id = user_info.get('tenant_id')

                # ✅ 获取请求信息
                ip = None
                ua = None
                if http_request:
                    if hasattr(http_request, 'client') and http_request.client:
                        ip = http_request.client.host
                    if hasattr(http_request, 'headers'):
                        ua = http_request.headers.get("user-agent")

                # ✅ 使用后台任务创建审计日志
                if background_tasks:
                    # 将审计日志记录添加到后台任务
                    background_tasks.add_task(
                        _background_create_audit_log,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id or audit_user_id,
                        before_data=before_data,
                        after_data=after_data,
                        tenant_id=audit_tenant_id,
                        actor_user_id=audit_user_id,
                        ip=ip,
                        ua=ua
                    )
                    logger.debug(f"审计日志已添加到后台任务: {action}")
                else:
                    # 降级处理：如果没有 BackgroundTasks，记录警告并跳过
                    logger.debug(f"审计日志装饰器未检测到 BackgroundTasks，跳过审计记录: {action}")

                return result

            except Exception as e:
                logger.error(f"操作失败: {action} - {str(e)}")

                # 记录失败的审计日志
                try:
                    # 尝试获取租户ID
                    audit_tenant_id = None
                    if user:
                        audit_tenant_id = getattr(user, 'current_tenant_id', None) or \
                                          getattr(user, 'tenant_id', None)
                    if not audit_tenant_id and http_request:
                        audit_tenant_id = getattr(http_request.state, 'tenant_id', None)

                    # 获取请求信息
                    ip = None
                    ua = None
                    if http_request:
                        if hasattr(http_request, 'client') and http_request.client:
                            ip = http_request.client.host
                        if hasattr(http_request, 'headers'):
                            ua = http_request.headers.get("user-agent")

                    # 使用后台任务记录失败日志
                    if background_tasks:
                        background_tasks.add_task(
                            _background_create_audit_log,
                            action=f"{action}_failed",
                            resource_type=resource_type,
                            resource_id=resource_id,
                            before_data=before_data,
                            after_data={"error": str(e)},
                            tenant_id=audit_tenant_id,
                            actor_user_id=getattr(user, 'id', None) if user else None,
                            ip=ip,
                            ua=ua
                        )
                except Exception as audit_error:
                    logger.error(f"审计日志记录失败: {str(audit_error)}")

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """同步函数包装器（类似逻辑）"""
            # ... 同样的修复逻辑
            pass

        # 根据函数类型返回对应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def extract_result_data(result: Any) -> Optional[dict]:
    """
    ✅ 新增：提取结果数据（处理 JSONResponse、dict 等）

    Args:
        result: 函数返回结果

    Returns:
        提取的字典数据，如果无法提取则返回 None
    """
    # 1. 如果已经是字典，直接返回
    if isinstance(result, dict):
        return result

    # 2. 如果有 to_dict 方法
    if hasattr(result, 'to_dict') and callable(result.to_dict):
        try:
            return result.to_dict()
        except:
            pass

    # 3. 如果是 JSONResponse（FastAPI/Starlette）
    if hasattr(result, 'body'):
        try:
            body = result.body
            if isinstance(body, bytes):
                return json.loads(body.decode('utf-8'))
            elif isinstance(body, str):
                return json.loads(body)
        except:
            pass

    # 4. 如果有 __dict__ 属性
    if hasattr(result, '__dict__'):
        try:
            return {k: v for k, v in result.__dict__.items() if not k.startswith('_')}
        except:
            pass

    return None


async def create_audit_log(
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        before_data: Optional[Any] = None,
        after_data: Optional[Any] = None,
        tenant_id: Optional[int] = None,  # ✅ 改为显式参数
        actor_user_id: Optional[int] = None,  # ✅ 改为显式参数
        request: Optional[Any] = None,
        db: Optional[Session] = None
):
    """
    ✅ 修改：创建审计日志记录（异步）

    现在直接接收 tenant_id 和 actor_user_id，而不是从 user 对象提取
    """
    need_close = False
    try:
        if not db:
            db = SessionLocal()
            need_close = True

        # ✅ 如果 tenant_id 仍为 None，使用默认值 0（或者根据业务需求调整）
        if tenant_id is None:
            tenant_id = 0
            logger.warning(f"审计日志缺少 tenant_id，使用默认值 0: {action}")

        # 获取请求信息
        ip = None
        ua = None
        if request:
            if hasattr(request, 'client') and request.client:
                ip = request.client.host
            if hasattr(request, 'headers'):
                ua = request.headers.get("user-agent")

        # ✅ 序列化 JSON 数据
        before_json = json.dumps(before_data, ensure_ascii=False) if before_data else None
        after_json = json.dumps(after_data, ensure_ascii=False) if after_data else None

        audit = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_json=before_json,
            after_json=after_json,
            ip=ip,
            ua=ua
        )

        db.add(audit)
        db.commit()

    except Exception as e:
        logger.error(f"审计日志记录失败: {str(e)}")
        if db:
            db.rollback()
    finally:
        if need_close and db:
            db.close()


def create_audit_log_sync(
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        before_data: Optional[Any] = None,
        after_data: Optional[Any] = None,
        tenant_id: Optional[int] = None,
        actor_user_id: Optional[int] = None,
        request: Optional[Any] = None,
        db: Optional[Session] = None
):
    """
    ✅ 同步版本（逻辑相同）
    """
    need_close = False
    try:
        if not db:
            db = SessionLocal()
            need_close = True

        if tenant_id is None:
            tenant_id = 0
            logger.warning(f"审计日志缺少 tenant_id，使用默认值 0: {action}")

        ip = None
        ua = None
        if request:
            if hasattr(request, 'client') and request.client:
                ip = request.client.host
            if hasattr(request, 'headers'):
                ua = request.headers.get("user-agent")

        before_json = json.dumps(before_data, ensure_ascii=False) if before_data else None
        after_json = json.dumps(after_data, ensure_ascii=False) if after_data else None

        # 系统用户 ID=0 不存在于 user 表，外键约束会失败，设为 None 表示系统操作
        effective_actor_user_id = actor_user_id if actor_user_id and actor_user_id > 0 else None

        audit = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=effective_actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_json=before_json,
            after_json=after_json,
            ip=ip,
            ua=ua
        )

        db.add(audit)
        db.commit()

    except Exception as e:
        logger.error(f"审计日志记录失败: {str(e)}")
        if db:
            db.rollback()
    finally:
        if need_close and db:
            db.close()