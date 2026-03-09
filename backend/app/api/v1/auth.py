# app/api/v1/auth.py
"""
认证相关API - 对外提供认证功能的HTTP接口

功能概述:
- 提供RESTful风格的认证相关API端点
- 实现请求参数验证和响应格式标准化
- 集成审计日志和错误处理
- 支持多租户架构的认证接口

API端点和功能:
├─ POST /login                      # 用户登录接口
│   ├─ 参数: account, password, tenant_id
│   ├─ 返回: access_token, refresh_token, user_info
│   ├─ 功能: 用户身份验证和令牌签发
│   └─ 审计: 记录登录行为日志
│
├─ POST /refresh                    # 令牌刷新接口
│   ├─ 参数: refresh_token
│   ├─ 返回: 新的access_token和refresh_token
│   └─ 功能: 无感知的访问令牌续期
│
├─ POST /register                   # 用户注册接口
│   ├─ 参数: account, password, name, email, phone, tenant_id
│   ├─ 返回: 用户基本信息
│   └─ 功能: 新用户账户创建
│
├─ POST /logout                     # 用户登出接口
│   ├─ 认证: 需要Bearer Token
│   ├─ 返回: 操作成功状态
│   └─ 功能: 令牌撤销和会话清理
│
├─ GET /me                          # 获取当前用户信息
│   ├─ 认证: 需要Bearer Token
│   ├─ 返回: 完整的用户信息、角色、岗位、部门
│   └─ 功能: 用户个人信息查询
│
├─ GET /tenants                     # 获取租户列表
│   ├─ 缓存: Redis缓存1小时
│   ├─ 返回: 所有可用租户列表
│   └─ 功能: 多租户环境的租户选择
│
└─ POST /validate-tenant            # 验证租户有效性
    ├─ 参数: tenant_id
    ├─ 返回: 租户有效性和基本信息
    └─ 功能: 前端租户ID验证

响应格式:
- 成功: {"code": 200, "data": {...}, "message": "操作成功"}
- 错误: {"code": 4xx/5xx, "message": "错误描述"}

安全特性:
- JWT Bearer Token认证
- 参数验证和SQL注入防护
- 频率限制和异常检测
- 审计日志记录

性能优化:
- Redis缓存减少数据库查询
- 异步处理提升响应速度
- 批量操作减少网络开销

使用场景:
- 前端应用的认证功能对接
- 移动端和第三方系统集成
- 微服务架构的认证中心
- 多租户SaaS应用支持

依赖关系:
- 依赖: AuthService (核心业务逻辑)
- 被依赖: 前端应用, 其他微服务
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import success_response, error_response
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    RegisterRequest
)
from app.services.auth import AuthService
from app.api.deps import get_current_user, get_current_token
from app.models.user import User, Tenant, UserRole, Role, UserProfile, UserPosition, Department, Position
from app.utils.audit import audit_log
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", summary="用户登录")
@audit_log(
    action="user_login",
    resource_type="auth",
    get_resource_id=lambda *args, **kwargs: kwargs.get("result", {}).get("user", {}).get("id"),
    record_after=True
)
async def login(
        login_request: LoginRequest,  # 🔧 改名避免混淆
        request: Request,  # 🔧 添加 FastAPI Request 对象
        db: Session = Depends(get_db)
):
    """
    用户登录接口

    请求参数:
    - account: 账号/邮箱/手机号
    - password: 密码
    - tenant_id: 租户ID（可选）

    返回值:
    - access_token: 访问令牌
    - refresh_token: 刷新令牌
    - token_type: 令牌类型
    - expires_in: 过期时间（秒）
    - user: 用户基本信息
    """
    logger.info(f"登录接口拿到的值：{login_request}")
    result = await AuthService.login(login_request, db)  # 🔧 传递正确的参数

    return success_response(
        data=result,
        message="登录成功"
    )


@router.post("/refresh", summary="刷新Token")
async def refresh_token(
        request: RefreshTokenRequest,
        db: Session = Depends(get_db)
):
    """
    刷新访问令牌

    请求参数:
    - refresh_token: 刷新令牌

    返回值:
    - access_token: 新的访问令牌
    - refresh_token: 新的刷新令牌
    - token_type: 令牌类型
    - expires_in: 过期时间（秒）
    """
    result = await AuthService.refresh_token(  # 添加 await
        request.refresh_token,
        db
    )

    return success_response(
        data=result,
        message="Token刷新成功"
    )


@router.post("/register", summary="用户注册")
async def register(
        request: RegisterRequest,
        db: Session = Depends(get_db)
):
    """
    用户注册接口

    请求参数:
    - account: 账号（3-50字符）
    - password: 密码（至少6位）
    - name: 真实姓名
    - email: 邮箱（可选）
    - phone: 手机号（可选）
    - tenant_id: 租户ID

    返回值:
    - id: 用户ID
    - account: 账号
    - name: 姓名
    - email: 邮箱
    - phone: 手机号
    - tenant_id: 租户ID
    """
    result = await AuthService.register(request, db)  # 添加 await

    return success_response(
        data=result,
        message="注册成功"
    )


@router.post("/logout", summary="用户登出")
async def logout(
        current_user: User = Depends(get_current_user),
        token: str = Depends(get_current_token),
        db: Session = Depends(get_db)
):
    """
    用户登出接口

    需要认证: 是

    返回值:
    - success: 是否成功
    """
    # 从 current_user 获取 tenant_id，保持接口参数不变
    result = await AuthService.logout(  # 添加 await
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,  # 添加 tenant_id
        token=token,
        db=db
    )

    return success_response(
        data={"success": result},
        message="登出成功" if result else "登出失败"
    )


@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取当前登录用户信息"""
    # 基本用户信息
    user_data = {
        "id": current_user.id,
        "account": current_user.account,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "department_id": current_user.department_id,
        "tenant_id": current_user.tenant_id,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

    # ✅ 修复：手动查询用户角色
    user_roles = db.query(UserRole, Role) \
        .join(Role, UserRole.role_id == Role.id) \
        .filter(UserRole.user_id == current_user.id) \
        .all()

    roles = [role.name for _, role in user_roles]
    user_data["roles"] = roles

    # ✅ 修复：手动查询用户岗位
    user_positions = db.query(UserPosition, Position) \
        .join(Position, UserPosition.position_id == Position.id) \
        .filter(UserPosition.user_id == current_user.id) \
        .all()

    positions = [position.name for _, position in user_positions]
    user_data["positions"] = positions

    # ✅ 添加：获取用户扩展信息
    user_profile = db.query(UserProfile) \
        .filter(UserProfile.user_id == current_user.id) \
        .first()

    if user_profile:
        user_data["profile"] = {
            "identity_no": user_profile.identity_no,
            "identity_type": user_profile.identity_type,
            "entry_year": user_profile.entry_year,
            "grade": user_profile.grade,
            "major": user_profile.major,
            "title": user_profile.title,
            "research_area": user_profile.research_area,
            "office": user_profile.office
        }

    # ✅ 添加：获取部门信息
    if current_user.department_id:
        department = db.query(Department) \
            .filter(Department.id == current_user.department_id) \
            .first()

        if department:
            user_data["department"] = {
                "id": department.id,
                "name": department.name,
                "type": department.type
            }

    return success_response(
        data=user_data,
        message="获取成功"
    )


@router.get("/tenants", summary="获取租户列表")
async def get_tenants(
        db: Session = Depends(get_db)
):
    """
    获取所有可用租户列表

    无需认证

    返回值:
    - list: 租户列表
        - id: 租户ID
        - name: 租户名称（学校名称）
        - created_at: 创建时间

    性能优化:
    - 使用Redis缓存租户列表，过期时间1小时
    - 租户数据变更频率低，适合缓存

    时间复杂度: O(n) where n is number of tenants
    空间复杂度: O(n)
    """
    try:
        # 尝试从缓存获取
        from app.core.redis_client import redis_client
        cache_key = "tenants:list"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            logger.info("Tenants list retrieved from cache")
            return success_response(
                data=cached_data,
                message="获取成功"
            )

        # 从数据库查询
        tenants = db.query(Tenant).order_by(Tenant.name).all()

        # 构建返回数据
        data = [
            {
                "id": tenant.id,
                "name": tenant.name,
                "created_at": tenant.created_at.isoformat() if tenant.created_at else None
            }
            for tenant in tenants
        ]

        # 存入缓存（1小时过期）
        await redis_client.set(cache_key, data, expire=3600)

        logger.info(f"Retrieved {len(data)} tenants from database")

        return success_response(
            data=data,
            message="获取成功"
        )

    except Exception as e:
        logger.error(f"Failed to get tenants: {str(e)}")
        return error_response(
            message="获取租户列表失败",
            code=500
        )


@router.post("/validate-tenant", summary="验证租户有效性")
async def validate_tenant(
        tenant_id: int,
        db: Session = Depends(get_db)
):
    """
    验证租户ID是否有效

    参数:
    - tenant_id: 租户ID

    返回值:
    - valid: 是否有效
    - tenant: 租户信息（如果有效）

    使用场景:
    - 前端初始化时验证localStorage中的tenant_id
    - 防止租户被删除后前端仍使用旧的tenant_id
    """
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

        if tenant:
            return success_response(
                data={
                    "valid": True,
                    "tenant": {
                        "id": tenant.id,
                        "name": tenant.name
                    }
                },
                message="租户有效"
            )
        else:
            return success_response(
                data={"valid": False},
                message="租户不存在"
            )

    except Exception as e:
        logger.error(f"Failed to validate tenant {tenant_id}: {str(e)}")
        return error_response(
            message="验证失败",
            code=500
        )