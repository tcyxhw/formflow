# app/core/database.py
"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前检测
    echo=False  # 生产环境设为False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于FastAPI的依赖注入
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
        # 注意：这里只需要导入，不需要使用，目的是让SQLAlchemy知道这些模型
        import app.models  # 导入models包，会自动执行__init__.py

        # 或者更明确的导入
        # from app.models import (
        #     Tenant, Department, User, Role,  # 用户相关
        #     Form, FormVersion, Submission,  # 表单相关
        #     FlowDefinition, FlowNode, Task,  # 流程相关
        #     Activity, AwardRecord,  # 活动相关
        #     Resource, Booking,  # 资源相关
        #     NotificationLog, AuditLog,  # 系统相关
        #     RefreshToken, DictItem
        # )

        # 创建所有表
        Base.metadata.create_all(bind=engine)
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
        Base.metadata.drop_all(bind=engine)
        logger.info("所有表已删除")

        # 重新创建所有表
        logger.info("正在重新创建所有表...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库重置完成")

    except Exception as e:
        logger.error(f"❌ 数据库重置失败: {str(e)}")
        raise