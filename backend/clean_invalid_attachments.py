#!/usr/bin/env python3
"""
清理数据库中 MinIO 不存在的附件记录

使用方法：
cd backend
python clean_invalid_attachments.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.core.database import SessionLocal
from app.models.form import Attachment
from app.services.storage_service import StorageService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_file_exists(storage_path: str) -> bool:
    """检查文件是否存在于 MinIO 中"""
    try:
        return StorageService.file_exists(storage_path)
    except Exception as e:
        logger.error(f"检查文件失败: {storage_path}, error: {e}")
        return False


def clean_invalid_attachments(dry_run: bool = True):
    """
    清理无效的附件记录

    Args:
        dry_run: 如果为 True，只打印要删除的记录，不实际删除
    """
    db = SessionLocal()
    try:
        # 查询所有附件记录
        attachments = db.query(Attachment).all()
        logger.info(f"数据库中共有 {len(attachments)} 条附件记录")

        invalid_attachments = []
        valid_count = 0

        for attachment in attachments:
            if check_file_exists(attachment.storage_path):
                valid_count += 1
                logger.debug(f"文件存在: id={attachment.id}, path={attachment.storage_path}")
            else:
                invalid_attachments.append(attachment)
                logger.warning(f"文件不存在: id={attachment.id}, path={attachment.storage_path}")

        logger.info(f"检查完成: 有效={valid_count}, 无效={len(invalid_attachments)}")

        if not invalid_attachments:
            logger.info("没有需要清理的附件记录")
            return

        if dry_run:
            logger.info("=== 以下附件记录将被删除（dry_run 模式）===")
            for att in invalid_attachments:
                logger.info(f"  ID={att.id}, filename={att.file_name}, path={att.storage_path}")
            logger.info(f"共 {len(invalid_attachments)} 条记录")
            logger.info("如需实际删除，请运行: python clean_invalid_attachments.py --execute")
        else:
            logger.info("=== 开始删除无效附件记录 ===")
            for att in invalid_attachments:
                try:
                    db.delete(att)
                    logger.info(f"已删除: ID={att.id}, filename={att.file_name}")
                except Exception as e:
                    logger.error(f"删除失败: ID={att.id}, error={e}")

            db.commit()
            logger.info(f"清理完成，共删除 {len(invalid_attachments)} 条记录")

    except Exception as e:
        logger.error(f"清理过程出错: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # 检查命令行参数
    execute_mode = "--execute" in sys.argv
    clean_invalid_attachments(dry_run=not execute_mode)
