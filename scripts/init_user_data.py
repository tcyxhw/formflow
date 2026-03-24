#!/usr/bin/env python3
"""
用户岗位和部门关联初始化脚本

功能：为租户 1 的测试用户创建岗位和部门关联
执行：python scripts/init_user_data.py
"""

import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 数据库配置
DATABASE_URL = 'postgresql://postgres:13579qwe@localhost:5432/postgres'

def init_user_data():
    """初始化用户数据"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("=" * 60)
    print("🔧 开始初始化用户岗位和部门关联")
    print("=" * 60)

    try:
        # 用户-岗位关联数据
        # 格式: (user_id, position_id, tenant_id)
        user_positions = [
            (501, 2, 1),   # zhanglaoshi → 辅导员
            (701, 10, 1),  # lizhangyuan → 院长
            (801, 22, 1),  # zhaokuaiji → 会计
            (901, 2, 1),   # sunfudaoyuan → 辅导员
            (1001, 15, 1), # zhoujiaoxue → 教学秘书
            (601, 18, 1),  # wangjiaoshou → 专任教师
        ]

        # 用户-部门关联数据
        # 格式: (user_id, department_id)
        user_departments = [
            (100, 1),   # admin → 信息学院
            (301, 24),  # xiaoming → 软件工程系 (学生)
            (302, 30),  # xiaohong → 艺术学院 (学生)
            (501, 23),  # zhanglaoshi → 学工办公室 (辅导员)
            (601, 25),  # wangjiaoshou → 软件工程教研室 (教师)
            (701, 20),  # lizhangyuan → 计算机学院 (院长)
            (801, 6),   # zhaokuaiji → 财务处 (会计)
            (901, 33),  # sunfudaoyuan → 艺术学院学工办 (辅导员)
            (1001, 22), # zhoujiaoxue → 教学办公室 (教学秘书)
        ]

        print("\n[步骤1] 创建用户-岗位关联...")

        # 检查是否已存在
        existing = db.execute(text("SELECT user_id FROM user_position WHERE tenant_id = 1")).fetchall()
        existing_user_ids = [row[0] for row in existing]
        print(f"  已有岗位关联: {existing_user_ids}")

        for user_id, position_id, tenant_id in user_positions:
            if user_id not in existing_user_ids:
                db.execute(text("""
                    INSERT INTO user_position (user_id, position_id, tenant_id, created_at, updated_at)
                    VALUES (:user_id, :position_id, :tenant_id, NOW(), NOW())
                """), {"user_id": user_id, "position_id": position_id, "tenant_id": tenant_id})
                print(f"  ✅ 用户 {user_id} → 岗位 {position_id}")
            else:
                print(f"  ⏭️ 用户 {user_id} 已有关联，跳过")

        print("\n[步骤2] 更新用户部门关联...")

        for user_id, department_id in user_departments:
            db.execute(text("""
                UPDATE "user" SET department_id = :dept_id, updated_at = NOW()
                WHERE id = :user_id AND tenant_id = 1
            """), {"dept_id": department_id, "user_id": user_id})
            print(f"  ✅ 用户 {user_id} → 部门 {department_id}")

        db.commit()
        print("\n" + "=" * 60)
        print("✅ 用户数据初始化完成")
        print("=" * 60)

        # 验证结果
        print("\n[验证] 查看当前用户岗位关联：")
        result = db.execute(text("""
            SELECT up.user_id, u.name, up.position_id, p.name as position_name
            FROM user_position up
            JOIN "user" u ON u.id = up.user_id
            JOIN position p ON p.id = up.position_id
            WHERE up.tenant_id = 1
            ORDER BY up.user_id
        """))
        for row in result:
            print(f"  用户 {row.user_id} ({row.name}) → 岗位 {row.position_id} ({row.position_name})")

        print("\n[验证] 查看当前用户部门关联：")
        result = db.execute(text("""
            SELECT u.id, u.name, u.department_id, d.name as dept_name
            FROM "user" u
            LEFT JOIN department d ON d.id = u.department_id
            WHERE u.tenant_id = 1
            ORDER BY u.id
        """))
        for row in result:
            dept = row.dept_name if row.dept_name else "未分配"
            print(f"  用户 {row.id} ({row.name}) → 部门 {row.department_id} ({dept})")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_user_data()
