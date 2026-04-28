#!/usr/bin/env python3
"""
列出所有用户和角色
"""
import sys
sys.path.insert(0, '/home/tcyuuu/code/formflow修改版/backend')

from app.core.database import SessionLocal
from app.models.user import User, Role, UserRole
from sqlalchemy import select

def list_users():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("用户列表:")
        print("=" * 60)
        users = db.query(User).limit(20).all()
        for u in users:
            print(f"  id={u.id}, account={u.account}, name={u.name}, tenant_id={u.tenant_id}")
        
        print("\n" + "=" * 60)
        print("角色列表:")
        print("=" * 60)
        roles = db.query(Role).all()
        for r in roles:
            print(f"  id={r.id}, name={r.name}, tenant_id={r.tenant_id}")
        
        print("\n" + "=" * 60)
        print("用户角色关联:")
        print("=" * 60)
        user_roles = db.query(UserRole).join(User).limit(20).all()
        for ur in user_roles:
            role = db.query(Role).filter(Role.id == ur.role_id).first()
            user = db.query(User).filter(User.id == ur.user_id).first()
            if role and user:
                print(f"  user_id={user.id}({user.account}) -> role={role.id}({role.name})")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()