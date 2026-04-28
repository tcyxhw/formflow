#!/usr/bin/env python3
"""
为用户添加管理员角色
"""
import sys
sys.path.insert(0, '/home/tcyuuu/code/formflow修改版/backend')

from app.core.database import SessionLocal
from app.models.user import User, Role, UserRole

def add_admin_role(account: str, role_name: str = "租户管理员"):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.account == account).first()
        if not user:
            print(f"用户 {account} 不存在")
            return False
        
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            print(f"角色 {role_name} 不存在")
            return False
        
        existing = db.query(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.role_id == role.id,
            UserRole.tenant_id == user.tenant_id
        ).first()
        
        if existing:
            print(f"用户 {account} 已有角色 {role_name}")
            return True
        
        user_role = UserRole(
            tenant_id=user.tenant_id,
            user_id=user.id,
            role_id=role.id
        )
        db.add(user_role)
        db.commit()
        print(f"✅ 成功为用户 {account} (id={user.id}) 添加角色 {role_name}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    add_admin_role("15018816993", "租户管理员")