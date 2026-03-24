#!/usr/bin/env python3
"""
用户登录信息修复脚本

功能：
1. 为测试用户设置有效的手机号（用于登录）
2. 将密码重置为 11223344

执行：python scripts/fix_user_login.py
"""

import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 数据库配置
DATABASE_URL = 'postgresql://postgres:13579qwe@localhost:5432/postgres'

# 11223344 的密码哈希
PASSWORD_HASH = '$2b$12$LapesHj3xWz1ScRTrwtVyuRGXsGqsT7CqD3Fdbe/B/vVCkdjGCCY6'

def fix_user_login():
    """修复用户登录信息"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("=" * 60)
    print("🔧 修复用户登录信息")
    print("=" * 60)

    try:
        # 用户手机号映射
        # 格式: (user_id, phone)
        user_phones = [
            (1, '15018816993'),      # 糖醋鱼 - 已有正确手机号
            (100, '13800000001'),    # admin
            (301, '13800000002'),    # xiaoming
            (302, '13800000003'),    # xiaohong
            (501, '13800000004'),    # zhanglaoshi
            (601, '13800000005'),    # wangjiaoshou
            (701, '13800000006'),    # lizhangyuan
            (801, '13800000007'),    # zhaokuaiji
            (901, '13800000008'),    # sunfudaoyuan
            (1001, '13800000009'),   # zhoujiaoxue
        ]

        print("\n[步骤1] 更新用户手机号...")
        for user_id, phone in user_phones:
            # 检查手机号是否已被其他用户使用
            existing = db.execute(text("""
                SELECT id, name FROM "user"
                WHERE phone = :phone AND id != :user_id AND tenant_id = 1
            """), {"phone": phone, "user_id": user_id}).fetchone()

            if existing:
                print(f"  ⚠️ 手机号 {phone} 已被用户 {existing.id} ({existing.name}) 使用，跳过用户 {user_id}")
                continue

            db.execute(text("""
                UPDATE "user"
                SET phone = :phone, account = :phone, updated_at = NOW()
                WHERE id = :user_id AND tenant_id = 1
            """), {"phone": phone, "user_id": user_id})
            print(f"  ✅ 用户 {user_id} → 手机号 {phone}")

        print("\n[步骤2] 重置用户密码为 11223344...")
        db.execute(text("""
            UPDATE "user"
            SET password_hash = :password_hash, updated_at = NOW()
            WHERE tenant_id = 1
        """), {"password_hash": PASSWORD_HASH})
        print(f"  ✅ 已重置租户 1 的所有用户密码")

        db.commit()
        print("\n" + "=" * 60)
        print("✅ 用户登录信息修复完成")
        print("=" * 60)

        # 验证结果
        print("\n[验证] 查看当前用户登录信息：")
        result = db.execute(text("""
            SELECT id, name, account, phone, department_id
            FROM "user"
            WHERE tenant_id = 1
            ORDER BY id
        """))
        print("\n" + "-" * 80)
        print(f"{'ID':<6} {'姓名':<12} {'账号(手机号)':<15} {'手机号':<15} {'部门ID':<8}")
        print("-" * 80)
        for row in result:
            print(f"{row.id:<6} {row.name:<12} {row.account or '未设置':<15} {row.phone or '未设置':<15} {row.department_id or '未设置':<8}")
        print("-" * 80)

        print("\n📋 登录信息汇总：")
        print("-" * 50)
        result = db.execute(text("""
            SELECT id, name, phone
            FROM "user"
            WHERE tenant_id = 1 AND phone IS NOT NULL
            ORDER BY id
        """))
        for row in result:
            print(f"  {row.name}: {row.phone} / 11223344")
        print("-" * 50)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_user_login()
