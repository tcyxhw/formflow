# app/services/user_service.py
"""
用户服务 - 专门处理用户相关的数据库操作
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User, UserPosition, Position, UserProfile


class UserService:
    """用户数据服务"""

    @staticmethod
    def find_user_by_account(account: str, tenant_id: Optional[int], db: Session) -> Optional[User]:
        """根据账号查找用户（支持账号/邮箱/手机号）"""
        query = db.query(User).filter(
            or_(
                User.account == account,
                User.email == account,
                User.phone == account
            )
        )

        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)

        return query.first()

    @staticmethod
    def find_user_by_id(user_id: int, db: Session) -> Optional[User]:
        """根据ID查找用户"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def check_account_exists(account: str, tenant_id: int, db: Session) -> bool:
        """检查账号是否已存在"""
        return db.query(User).filter(
            User.account == account,
            User.tenant_id == tenant_id
        ).first() is not None

    @staticmethod
    def check_email_exists(email: str, tenant_id: int, db: Session) -> bool:
        """检查邮箱是否已使用"""
        return db.query(User).filter(
            User.email == email,
            User.tenant_id == tenant_id
        ).first() is not None

    @staticmethod
    def check_phone_exists(phone: str, tenant_id: int, db: Session) -> bool:
        """检查手机号是否已使用"""
        return db.query(User).filter(
            User.phone == phone,
            User.tenant_id == tenant_id
        ).first() is not None

    @staticmethod
    def create_user(user_data: dict, db: Session) -> User:
        """创建用户"""
        user = User(**user_data)
        db.add(user)
        db.flush()  # 获取 user_id
        return user

    @staticmethod
    def create_user_profile(profile_data: dict, db: Session) -> UserProfile:
        """创建用户扩展信息"""
        profile = UserProfile(**profile_data)
        db.add(profile)
        return profile

    @staticmethod
    def get_user_positions(user_id: int, db: Session) -> List[str]:
        """获取用户当前有效岗位"""
        user_positions = db.query(UserPosition, Position) \
            .join(Position, UserPosition.position_id == Position.id) \
            .filter(
            UserPosition.user_id == user_id,
            UserPosition.effective_from <= datetime.now(),
            or_(
                UserPosition.effective_to.is_(None),
                UserPosition.effective_to >= datetime.now()
            )
        ).all()

        return [position.name for _, position in user_positions]

    @staticmethod
    def get_user_profile(user_id: int, db: Session) -> Optional[UserProfile]:
        """获取用户扩展信息"""
        return db.query(UserProfile) \
            .filter(UserProfile.user_id == user_id) \
            .first()