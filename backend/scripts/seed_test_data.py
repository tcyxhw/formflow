"""
测试数据种子脚本：为 tenant_id=1 创建测试所需的部门、岗位和用户

创建内容：
1. 部门：计算机科学系、数学系
2. 岗位：系主任
3. 用户：
   - 计算机科学系系主任（张主任）
   - 计算机科学系老师（李老师）
   - 数学系系主任（王主任）
   - 数学系老师（赵老师）
4. 用户-部门-岗位关联
5. 角色：老师、系主任
"""
import sys
import os

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import settings
from app.models.user import (
    Department, Position, User, UserProfile,
    UserDepartmentPost, Role, UserRole
)
from app.core.security import hash_password


def seed_test_data():
    engine = create_engine(settings.DATABASE_URL)

    with Session(engine) as db:
        tenant_id = 1
        now = datetime.now()

        # ========== 1. 创建岗位：系主任 ==========
        dept_head_pos = db.query(Position).filter(
            Position.tenant_id == tenant_id,
            Position.name == "系主任"
        ).first()

        if not dept_head_pos:
            dept_head_pos = Position(
                tenant_id=tenant_id,
                name="系主任",
                created_at=now,
                updated_at=now,
            )
            db.add(dept_head_pos)
            db.flush()
            print(f"✅ 创建岗位: 系主任 (id={dept_head_pos.id})")
        else:
            print(f"ℹ️  岗位已存在: 系主任 (id={dept_head_pos.id})")

        # ========== 2. 创建部门 ==========
        departments = {}
        dept_configs = [
            {"name": "计算机科学系", "type": "department"},
            {"name": "数学系", "type": "department"},
        ]

        for cfg in dept_configs:
            dept = db.query(Department).filter(
                Department.tenant_id == tenant_id,
                Department.name == cfg["name"]
            ).first()

            if not dept:
                dept = Department(
                    tenant_id=tenant_id,
                    name=cfg["name"],
                    type=cfg["type"],
                    is_root=False,
                    sort_order=0,
                    created_at=now,
                    updated_at=now,
                )
                db.add(dept)
                db.flush()
                print(f"✅ 创建部门: {cfg['name']} (id={dept.id})")
            else:
                print(f"ℹ️  部门已存在: {cfg['name']} (id={dept.id})")

            departments[cfg["name"]] = dept

        # ========== 3. 创建角色 ==========
        roles = {}
        role_configs = [
            {"name": "系统管理员", "description": "系统管理员角色"},
            {"name": "租户管理员", "description": "租户管理员角色"},
            {"name": "老师", "description": "教师角色"},
        ]

        for cfg in role_configs:
            role = db.query(Role).filter(
                Role.tenant_id == tenant_id,
                Role.name == cfg["name"]
            ).first()

            if not role:
                role = Role(
                    tenant_id=tenant_id,
                    name=cfg["name"],
                    description=cfg["description"],
                    created_at=now,
                    updated_at=now,
                )
                db.add(role)
                db.flush()
                print(f"✅ 创建角色: {cfg['name']} (id={role.id})")
            else:
                print(f"ℹ️  角色已存在: {cfg['name']} (id={role.id})")

            roles[cfg["name"]] = role

        # ========== 4. 创建管理员用户 ==========
        admin_users = {}
        admin_configs = [
            {
                "account": "admin",
                "name": "系统管理员",
                "roles": ["系统管理员"],
                "password": "admin123",
                "email": "admin@university.edu",
                "phone": "13900000000",
            },
            {
                "account": "tenant_admin",
                "name": "租户管理员",
                "roles": ["租户管理员"],
                "password": "admin123",
                "email": "tenant_admin@university.edu",
                "phone": "13900000001",
            },
        ]

        for cfg in admin_configs:
            user = db.query(User).filter(
                User.tenant_id == tenant_id,
                User.account == cfg["account"]
            ).first()

            if not user:
                user = User(
                    tenant_id=tenant_id,
                    account=cfg["account"],
                    password_hash=hash_password(cfg["password"]),
                    name=cfg["name"],
                    email=cfg["email"],
                    phone=cfg.get("phone"),
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                db.add(user)
                db.flush()
                print(f"✅ 创建管理员用户: {cfg['name']} ({cfg['account']}) (id={user.id})")
            else:
                print(f"ℹ️  管理员用户已存在: {cfg['name']} ({cfg['account']}) (id={user.id})")

            admin_users[cfg["account"]] = user

            # 关联角色
            for role_name in cfg["roles"]:
                role = roles[role_name]
                existing_ur = db.query(UserRole).filter(
                    UserRole.user_id == user.id,
                    UserRole.role_id == role.id,
                    UserRole.tenant_id == tenant_id,
                ).first()

                if not existing_ur:
                    ur = UserRole(
                        tenant_id=tenant_id,
                        user_id=user.id,
                        role_id=role.id,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(ur)
                    db.flush()
                    print(f"  ✅ 关联管理员角色: {cfg['name']} -> {role_name}")

        # ========== 5. 创建普通用户 ==========
        users = {}
        user_configs = [
            {
                "account": "zhang_zhuren",
                "name": "张主任",
                "department": "计算机科学系",
                "roles": ["老师"],
                "position": "系主任",
                "password": "123456",
                "email": "zhang@university.edu",
                "phone": "13800000001",
            },
            {
                "account": "li_laoshi",
                "name": "李老师",
                "department": "计算机科学系",
                "roles": ["老师"],
                "position": None,
                "password": "123456",
                "email": "li@university.edu",
                "phone": "13800000002",
            },
            {
                "account": "wang_zhuren",
                "name": "王主任",
                "department": "数学系",
                "roles": ["老师"],
                "position": "系主任",
                "password": "123456",
                "email": "wang@university.edu",
                "phone": "13800000003",
            },
            {
                "account": "zhao_laoshi",
                "name": "赵老师",
                "department": "数学系",
                "roles": ["老师"],
                "position": None,
                "password": "123456",
                "email": "zhao@university.edu",
                "phone": "13800000004",
            },
        ]

        for cfg in user_configs:
            user = db.query(User).filter(
                User.tenant_id == tenant_id,
                User.account == cfg["account"]
            ).first()

            if not user:
                user = User(
                    tenant_id=tenant_id,
                    account=cfg["account"],
                    password_hash=hash_password(cfg["password"]),
                    name=cfg["name"],
                    email=cfg["email"],
                    phone=cfg.get("phone"),
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                db.add(user)
                db.flush()
                print(f"✅ 创建用户: {cfg['name']} ({cfg['account']}) (id={user.id})")
            else:
                print(f"ℹ️  用户已存在: {cfg['name']} ({cfg['account']}) (id={user.id})")

            users[cfg["account"]] = user

            # 创建用户扩展信息
            profile = db.query(UserProfile).filter(
                UserProfile.user_id == user.id
            ).first()

            if not profile:
                profile = UserProfile(
                    user_id=user.id,
                    tenant_id=tenant_id,
                    identity_type="teacher",
                    identity_no=f"T{user.id:04d}",
                    created_at=now,
                    updated_at=now,
                )
                db.add(profile)
                db.flush()
                print(f"  ✅ 创建扩展信息: {cfg['name']}")

            dept = departments[cfg["department"]]

            # 关联用户到部门（UserDepartmentPost）
            existing_ud = db.query(UserDepartmentPost).filter(
                UserDepartmentPost.user_id == user.id,
                UserDepartmentPost.department_id == dept.id,
                UserDepartmentPost.tenant_id == tenant_id,
            ).first()

            if not existing_ud:
                post_id = dept_head_pos.id if cfg["position"] else None
                ud = UserDepartmentPost(
                    tenant_id=tenant_id,
                    user_id=user.id,
                    department_id=dept.id,
                    post_id=post_id,
                    created_at=now,
                    updated_at=now,
                )
                db.add(ud)
                db.flush()
                pos_label = cfg["position"] or "无岗位"
                print(f"  ✅ 关联部门岗位: {cfg['name']} -> {cfg['department']} / {pos_label}")

            # 关联角色
            for role_name in cfg["roles"]:
                role = roles[role_name]
                existing_ur = db.query(UserRole).filter(
                    UserRole.user_id == user.id,
                    UserRole.role_id == role.id,
                    UserRole.tenant_id == tenant_id,
                ).first()

                if not existing_ur:
                    ur = UserRole(
                        tenant_id=tenant_id,
                        user_id=user.id,
                        role_id=role.id,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(ur)
                    db.flush()
                    print(f"  ✅ 关联角色: {cfg['name']} -> {role_name}")

        db.commit()

        # ========== 6. 打印测试信息 ==========
        print("\n" + "=" * 60)
        print("📋 测试数据创建完成！")
        print("=" * 60)
        print("\n🔑 管理员账号（密码均为 admin123）：")
        for account, user in admin_users.items():
            roles_str = ", ".join(cfg["roles"][0] for cfg in admin_configs if cfg["account"] == account)
            print(f"  - {account}: {user.name}（{roles_str}）")
        
        print("\n🔑 普通用户账号（密码均为 123456）：")
        for account, user in users.items():
            dept_name = next(
                (k for k, v in departments.items()
                 if v.id == (db.query(UserDepartmentPost.department_id)
                             .filter(UserDepartmentPost.user_id == user.id)
                             .first() or [None])[0]),
                "未知"
            )
            print(f"  - {account}: {user.name}（{dept_name}）")

        print(f"\n📊 部门 ID 映射：")
        for name, dept in departments.items():
            print(f"  - {name}: id={dept.id}")

        print(f"\n📌 岗位 ID：系主任 = {dept_head_pos.id}")

        print(f"\n🔧 审批流程配置建议：")
        print(f"  - 审批节点类型: department_post")
        print(f"  - 匹配模式: CURRENT（使用提交人当前部门）")
        print(f"  - 岗位: 系主任 (id={dept_head_pos.id})")
        print(f"  - 当李老师提交表单时，会自动分配给张主任审批")
        print(f"  - 当赵老师提交表单时，会自动分配给王主任审批")


if __name__ == "__main__":
    seed_test_data()
