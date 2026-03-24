# app/core/database.py
"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator, Generator
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# 创建异步数据库引擎
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前检测
    echo=False  # 生产环境设为False
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 创建同步数据库引擎（用于数据库迁移和初始化）
sync_engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

# 创建同步会话工厂（用于数据库迁移和初始化）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# 创建基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取同步数据库会话
    用于FastAPI的依赖注入
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"数据库会话异常: {str(e)}")
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_sync_db() -> Generator[Session, None, None]:
    """
    获取同步数据库会话
    仅用于数据库迁移和初始化
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话异常: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库
    创建所有表
    """
    try:
        # 导入所有模型，确保它们被注册
        import app.models

        # 使用同步引擎创建所有表
        Base.metadata.create_all(bind=sync_engine)
        logger.info("数据库表创建成功")

    except ImportError as e:
        logger.error(f"模型导入失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise


def reset_db() -> None:
    """
    重置数据库 - 删除所有表并重新创建
    ⚠️ 警告：这会删除所有数据！
    """
    try:
        logger.warning("⚠️ 开始重置数据库，将删除所有数据...")

        # 导入所有模型
        import app.models

        # 删除所有表
        logger.info("正在删除所有表...")
        Base.metadata.drop_all(bind=sync_engine)
        logger.info("所有表已删除")

        # 重新创建所有表
        logger.info("正在重新创建所有表...")
        Base.metadata.create_all(bind=sync_engine)
        logger.info("✅ 数据库重置完成")

    except Exception as e:
        logger.error(f"❌ 数据库重置失败: {str(e)}")
        raise