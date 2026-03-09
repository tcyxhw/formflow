# app/middleware/auth.py
"""
认证中间件 - 处理双 Token 验证和自动刷新

功能概述:
- 自动验证每个HTTP请求的访问令牌
- 实现访问令牌过期时的无感知自动刷新
- 在请求上下文中注入用户身份信息
- 提供灵活的路径白名单机制

主要类和方法:
└─ AuthMiddleware (认证中间件)
    ├─ __call__()                   # 中间件主处理逻辑
    │   ├─ 检查路径是否需要认证
    │   ├─ 提取和验证访问令牌
    │   ├─ 处理令牌刷新流程
    │   └─ 注入用户信息到请求上下文
    ├─ _extract_token()             # 从Authorization头提取Bearer Token
    └─ _should_skip_auth()          # 判断路径是否跳过认证

├─ get_current_user()               # FastAPI依赖注入函数，获取当前用户信息

工作流程:
1. 检查请求路径是否在白名单中
2. 提取Authorization头中的Bearer Token
3. 验证访问令牌有效性
4. 如访问令牌无效，尝试使用刷新令牌自动刷新
5. 在响应头返回新的访问令牌
6. 将用户信息注入到request.state中

使用场景:
- FastAPI应用的全局认证中间件
- 前端应用的无感知token续期
- API请求的统一身份验证
- 多租户应用的用户身份识别

依赖关系:
- 依赖: TokenService (令牌验证和刷新)
- 被依赖: FastAPI应用, API路由
"""
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware  # 添加这个导入
from app.services.token_service import TokenService
from app.core.exceptions import AuthenticationError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""

    async def dispatch(self, request: Request, call_next: Callable):
        # 跳过 OPTIONS 请求
        if request.method == "OPTIONS":
            return await call_next(request)

        # 跳过不需要认证的路径
        if self._should_skip_auth(request.url.path):
            return await call_next(request)

        # 获取 tokens
        access_token = self._extract_token(request.headers.get("Authorization"))
        refresh_token = request.headers.get("X-Refresh-Token")

        logger.debug(f"🔍 请求: {request.method} {request.url.path}")
        logger.debug(f"🔑 访问令牌: {'✅' if access_token else '❌缺失'}")
        logger.debug(f"🔄 刷新令牌: {'✅' if refresh_token else '❌缺失'}")

        if not access_token:
            # ✅ 使用辅助函数创建带 CORS 头的错误响应
            return self._create_error_response(
                request,
                status.HTTP_401_UNAUTHORIZED,
                "未提供访问令牌"
            )

        # 验证访问令牌
        from app.services.token_service import TokenService
        access_payload = await TokenService.verify_access_token(access_token)

        if access_payload:
            # 访问令牌有效
            request.state.user_id = access_payload.get("user_id")
            request.state.tenant_id = access_payload.get("tenant_id")
            request.state.family_id = access_payload.get("family_id")

            # 预防性刷新逻辑
            from datetime import datetime
            exp_timestamp = access_payload.get("exp", 0)
            current_timestamp = datetime.utcnow().timestamp()
            time_remaining = exp_timestamp - current_timestamp

            response = await call_next(request)

            # 剩余时间少于30秒时预防性刷新
            if time_remaining < 30 and refresh_token:
                try:
                    logger.info(
                        f"⏰ 预防性刷新 - 用户: {access_payload.get('user_id')}, "
                        f"剩余: {time_remaining:.1f}秒"
                    )

                    new_tokens = await TokenService.refresh_access_token(refresh_token)

                    if new_tokens:
                        response.headers["X-New-Access-Token"] = new_tokens["access_token"]
                        response.headers["X-Token-Refreshed"] = "true"

                        if new_tokens.get("token_rotated"):
                            response.headers["X-New-Refresh-Token"] = new_tokens["refresh_token"]
                            response.headers["X-Token-Rotated"] = "true"
                            logger.info(f"🔄 刷新令牌已轮转")

                except Exception as e:
                    logger.warning(f"⚠️ 预防性刷新失败: {str(e)}")

            return response

        # 访问令牌无效，尝试刷新
        logger.warning("⚠️ 访问令牌无效或已过期")

        if not refresh_token:
            logger.error("❌ 刷新令牌缺失")
            # ✅ 使用辅助函数创建带 CORS 头的错误响应
            return self._create_error_response(
                request,
                status.HTTP_401_UNAUTHORIZED,
                "访问令牌已过期，未提供刷新令牌"
            )

        try:
            logger.info("🔄 尝试使用刷新令牌获取新访问令牌")
            new_tokens = await TokenService.refresh_access_token(refresh_token)

            if not new_tokens:
                logger.error("❌ 刷新令牌无效或已过期")
                # ✅ 使用辅助函数创建带 CORS 头的错误响应
                return self._create_error_response(
                    request,
                    status.HTTP_401_UNAUTHORIZED,
                    "刷新令牌无效或已过期，请重新登录"
                )

            # 从新的访问令牌获取用户信息
            new_access_payload = await TokenService.verify_access_token(
                new_tokens["access_token"]
            )

            if not new_access_payload:
                logger.error("❌ 新访问令牌验证失败")
                return self._create_error_response(
                    request,
                    status.HTTP_401_UNAUTHORIZED,
                    "令牌刷新失败"
                )

            # 设置用户信息
            request.state.user_id = new_access_payload.get("user_id")
            request.state.tenant_id = new_access_payload.get("tenant_id")
            request.state.family_id = new_access_payload.get("family_id")

            logger.info(f"✅ 令牌刷新成功 - 用户: {new_access_payload.get('user_id')}")

            # 执行请求
            response = await call_next(request)

            # 返回新令牌
            response.headers["X-New-Access-Token"] = new_tokens["access_token"]
            response.headers["X-Token-Refreshed"] = "true"

            if new_tokens.get("token_rotated"):
                response.headers["X-New-Refresh-Token"] = new_tokens["refresh_token"]
                response.headers["X-Token-Rotated"] = "true"

            return response

        except Exception as e:
            logger.error(f"❌ Token刷新异常: {str(e)}", exc_info=True)
            return self._create_error_response(
                request,
                status.HTTP_401_UNAUTHORIZED,
                "认证失败，请重新登录"
            )

    def _extract_token(self, auth_header: str | None) -> str | None:
        """从 Authorization 头提取 token"""
        if not auth_header:
            return None
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None

    def _should_skip_auth(self, path: str) -> bool:
        """判断是否跳过认证"""
        skip_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/tenants",
            "/api/v1/auth/validate-tenant",
            "/api/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        return any(path.startswith(p) for p in skip_paths)

    # ✅ 新增：创建带 CORS 头的错误响应
    def _create_error_response(
            self,
            request: Request,
            status_code: int,
            detail: str
    ) -> JSONResponse:
        """
        创建带 CORS 头的错误响应

        ⚠️ 重要：即使是错误响应，也必须设置 CORS 头
        否则浏览器会因为跨域策略拦截响应，前端收到 Network Error
        """
        response = JSONResponse(
            status_code=status_code,
            content={"detail": detail}
        )

        # ✅ 手动添加 CORS 头（与 CORSMiddleware 保持一致）
        origin = request.headers.get("origin")

        # 从配置中获取允许的源
        from app.config import settings
        allowed_origins = settings.BACKEND_CORS_ORIGINS

        # 检查请求源是否在允许列表中
        if origin and (origin in allowed_origins or "*" in allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = ", ".join([
                "X-New-Access-Token",
                "X-New-Refresh-Token",
                "X-Token-Refreshed",
                "X-Token-Rotated"
            ])

        return response


# 用于依赖注入的函数
async def get_current_user(request: Request) -> dict:
    """获取当前用户信息"""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证"
        )

    return {
        "user_id": request.state.user_id,
        "tenant_id": request.state.tenant_id,
        "family_id": request.state.family_id  # 🔧 修改: 统一字段名
    }


# 🔧 新增: 获取当前令牌的依赖函数
async def get_current_token(request: Request) -> str:
    """获取当前请求的访问令牌"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供访问令牌"
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌格式"
        )

    return parts[1]
