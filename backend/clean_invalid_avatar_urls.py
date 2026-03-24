#!/usr/bin/env python3
"""
清理用户表中指向已删除附件的 avatar_url

使用方法：
cd backend
python clean_invalid_avatar_urls.py
"""
import sys
import os
import re

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.models.form import Attachment
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_invalid_avatar_urls(dry_run: bool = True):
    """
    清理用户表中指向已删除附件的 avatar_url

    Args:
        dry_run: 如果为 True，只打印要修改的记录，不实际修改
    """
    db = SessionLocal()
    try:
        # 查询所有有 avatar_url 的用户
        users = db.query(User).filter(User.avatar_url.isnot(None)).all()
        logger.info(f"数据库中共有 {len(users)} 个用户有 avatar_url")

        invalid_users = []
        valid_count = 0

        for user in users:
            avatar_url = user.avatar_url
            
            # 检查是否是附件URL格式
            if "/attachments/" in avatar_url and "/download" in avatar_url:
                match = re.search(r'/attachments/(\d+)/download', avatar_url)
                if match:
                    attachment_id = int(match.group(1))
                    # 检查附件是否存在
                    attachment = db.query(Attachment).filter(
                        Attachment.id == attachment_id
                    ).first()
                    
                    if attachment:
                        valid_count += 1
                        logger.debug(f"头像有效: user_id={user.id}, attachment_id={attachment_id}")
                    else:
                        invalid_users.append(user)
                        logger.warning(f"头像无效: user_id={user.id}, name={user.name}, attachment_id={attachment_id} 不存在")
                else:
                    # URL格式不正确
                    invalid_users.append(user)
                    logger.warning(f"头像URL格式不正确: user_id={user.id}, avatar_url={avatar_url}")
            else:
                # 不是附件URL格式，可能是直接存储路径或其他URL
                valid_count += 1
                logger.debug(f"头像URL非附件格式: user_id={user.id}, avatar_url={avatar_url}")

        logger.info(f"检查完成: 有效={valid_count}, 无效={len(invalid_users)}")

        if not invalid_users:
            logger.info("没有需要清理的用户头像记录")
            return

        if dry_run:
            logger.info("=== 以下用户的 avatar_url 将被清空（dry_run 模式）===")
            for user in invalid_users:
                logger.info(f"  ID={user.id}, name={user.name}, avatar_url={user.avatar_url}")
            logger.info(f"共 {len(invalid_users)} 个用户")
            logger.info("如需实际修改，请运行: python clean_invalid_avatar_urls.py --execute")
        else:
            logger.info("=== 开始清理无效的 avatar_url ===")
            for user in invalid_users:
                try:
                    user.avatar_url = None
                    logger.info(f"已清空: ID={user.id}, name={user.name}")
                except Exception as e:
                    logger.error(f"清空失败: ID={user.id}, error={e}")

            db.commit()
            logger.info(f"清理完成，共清空 {len(invalid_users)} 个用户的 avatar_url")

    except Exception as e:
        logger.error(f"清理过程出错: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # 检查命令行参数
    execute_mode = "--execute" in sys.argv
    clean_invalid_avatar_urls(dry_run=not execute_mode)
