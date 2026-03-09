# app/main.py
"""
FastAPI主应用入口
配置路由、中间件、异常处理等
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.core.database import init_db, engine
from app.core.redis_client import redis_client
from app.api.v1 import router as api_v1_router
from app.middleware.logging import LoggingMiddleware
from app.middleware.tenant import TenantMiddleware
from app.middleware.auth import AuthMiddleware
from app.tasks.scheduler import scheduler

# 异常处理
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException  # ✅ 使用 FastAPI 的 HTTPException 而不是 Starlette 的
from app.core.exceptions import BaseError
from app.core.exception_handlers import (
    base_error_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):  # ✅ 改名避免隐藏外部 app
    """
    应用生命周期管理
    """
    # ========== 启动时执行 ==========
    logger.info("FormFlow 应用启动中...")

    try:
        # 初始化数据库
        logger.info("初始化数据库...")
        init_db()

        # 连接Redis
        logger.info("连接Redis...")
        await redis_client.connect()

        # ✅ 启动定时任务（从 @app.on_event 移到这里）
        logger.info("启动定时任务...")
        scheduler.start()

        logger.info("FormFlow 应用启动成功！")

    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        raise

    yield

    # ========== 关闭时执行 ==========
    logger.info("FormFlow 应用关闭中...")

    # ✅ 关闭定时任务（从 @app.on_event 移到这里）
    scheduler.shutdown()
    logger.info("定时任务已关闭")

    # 断开Redis连接
    await redis_client.disconnect()
    logger.info("Redis 连接已关闭")

    # 关闭数据库连接
    engine.dispose()
    logger.info("数据库连接已关闭")

    logger.info("FormFlow 应用已关闭")


# ========== 创建FastAPI应用 ==========
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)


# ========== 配置中间件（注意顺序）==========
# 1. CORS（最外层）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Refresh-Token"],  # 允许接收自定义请求头
    expose_headers=[  # ✅ 关键：允许前端读取自定义响应头
        "X-New-Access-Token",
        "X-New-Refresh-Token",
        "X-Token-Refreshed",
        "X-Token-Rotated"
    ]
)

# 2. 日志中间件
app.add_middleware(LoggingMiddleware)

# 3. 认证中间件
app.add_middleware(AuthMiddleware)

# 4. 租户中间件（最内层）
app.add_middleware(TenantMiddleware)


# ========== 注册全局异常处理器（顺序很重要）==========
# 1. 自定义业务异常（最具体）
app.add_exception_handler(BaseError, base_error_handler)

# 2. 数据库异常
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

# 3. 参数验证异常
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 4. HTTP异常
app.add_exception_handler(HTTPException, http_exception_handler)  # ✅ 使用 FastAPI 的

# 5. 兜底异常处理器（最后注册）
app.add_exception_handler(Exception, general_exception_handler)


# ========== 注册API路由 ==========
app.include_router(
    api_v1_router,
    prefix=settings.API_V1_STR
)


# ========== 基础接口 ==========
@app.get("/", include_in_schema=False)
async def root():
    """根路径访问"""
    return {
        "message": f"欢迎使用 {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME
    }


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )