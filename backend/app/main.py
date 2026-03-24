# app/main.py
"""
FastAPI主应用入口
配置路由、中间件、异常处理等
"""
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

print(">>> [1] 日志配置完成", flush=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings

print(f">>> [2] 配置加载完成, LOG_LEVEL={settings.LOG_LEVEL}", flush=True)
from app.core.database import init_db, sync_engine
from app.core.redis_client import redis_client
from app.api.v1 import router as api_v1_router
from app.middleware.logging import LoggingMiddleware
from app.middleware.tenant import TenantMiddleware
from app.middleware.auth import AuthMiddleware
from app.tasks.scheduler import scheduler

from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
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
async def lifespan(_app: FastAPI):
    print(">>> [3] lifespan 启动阶段开始", flush=True)
    
    print(">>> [4] FormFlow 应用启动中...", flush=True)

    try:
        print(">>> [5] 初始化数据库...", flush=True)
        init_db()
        print(">>> [6] 数据库初始化完成", flush=True)

        print(">>> [7] 连接Redis...", flush=True)
        await redis_client.connect()
        print(">>> [8] Redis连接完成", flush=True)

        print(">>> [9] 启动定时任务...", flush=True)
        scheduler.start()
        print(">>> [10] 定时任务启动完成", flush=True)

        print(">>> [11] FormFlow 应用启动成功！", flush=True)

    except Exception as e:
        print(f">>> [X] 应用启动失败: {str(e)}", flush=True)
        raise

    yield

    print(">>> [12] FormFlow 应用关闭中...", flush=True)

    scheduler.shutdown()
    logger.info("定时任务已关闭")

    await redis_client.disconnect()
    logger.info("Redis 连接已关闭")

    sync_engine.dispose()
    logger.info("数据库连接已关闭")

    logger.info("FormFlow 应用已关闭")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Refresh-Token"],
    expose_headers=[
        "X-New-Access-Token",
        "X-New-Refresh-Token",
        "X-Token-Refreshed",
        "X-Token-Rotated"
    ]
)

app.add_middleware(AuthMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(LoggingMiddleware)


app.add_exception_handler(BaseError, base_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


app.include_router(
    api_v1_router,
    prefix=settings.API_V1_STR
)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"欢迎使用 {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health", tags=["系统"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
