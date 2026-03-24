"""
安全迁移脚本 - 保留已有数据并补充新结构
用于数据库已有数据的情况

用法:
    python scripts/migrate_existing_data.py [--tenant-id TENANT_ID]

功能:
    1. 给已有部门设置is_root字段
    2. 根据已有的user_position数据生成user_department_post记录
    3. 生成department_post关系（如果不存在）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import (
    Department, Position, UserPosition, 
    DepartmentPost, UserDepartmentPost
)


def migrate_departments(db: Session, tenant_id: int):
    """给已有部门设置is_root字段"""
    # 查找没有parent_id的部门，设为根部门
    root_depts = db.query(Department).filter(
        Department.tenant_id == tenant_id,
        Department.parent_id.is_(None),
        Department.is_root == False
    ).all()
    
    for dept in root_depts:
        dept.is_root = True
        print(f"设置根部门: {dept.name} (id={dept.id})")
    
    if root_depts:
        db.flush()
        print(f"共设置 {len(root_depts)} 个根部门")
    else:
        print("没有需要更新的根部门")


def migrate_user_positions(db: Session, tenant_id: int):
    """将user_position数据迁移到user_department_post"""
    # 获取用户的主属部门
    users_with_dept = db.query(
        UserPosition.user_id,
        UserPosition.position_id
    ).filter(
        UserPosition.tenant_id == tenant_id
    ).all()
    
    migrated_count = 0
    for user_id, position_id in users_with_dept:
        # 获取用户的部门（从User表的department_id）
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.department_id:
            continue
        
        # 检查是否已存在
        existing = db.query(UserDepartmentPost).filter(
            UserDepartmentPost.tenant_id == tenant_id,
            UserDepartmentPost.user_id == user_id,
            UserDepartmentPost.department_id == user.department_id,
            UserDepartmentPost.post_id == position_id
        ).first()
        
        if not existing:
            new_record = UserDepartmentPost(
                tenant_id=tenant_id,
                user_id=user_id,
                department_id=user.department_id,
                post_id=position_id
            )
            db.add(new_record)
            migrated_count += 1
    
    if migrated_count > 0:
        db.flush()
        print(f"迁移了 {migrated_count} 条用户-部门-岗位关系")
    else:
        print("没有需要迁移的用户岗位关系")


def generate_department_posts(db: Session, tenant_id: int):
    """根据已有的Position和Department生成department_post关系"""
    # 获取所有部门和岗位
    departments = db.query(Department).filter(Department.tenant_id == tenant_id).all()
    
    # 从UserDepartmentPost中推断哪些岗位在哪些部门
    existing_relations = db.query(
        UserDepartmentPost.department_id,
        UserDepartmentPost.post_id
    ).filter(
        UserDepartmentPost.tenant_id == tenant_id,
        UserDepartmentPost.post_id.isnot(None)
    ).distinct().all()
    
    created_count = 0
    for dept_id, post_id in existing_relations:
        existing = db.query(DepartmentPost).filter(
            DepartmentPost.tenant_id == tenant_id,
            DepartmentPost.department_id == dept_id,
            DepartmentPost.post_id == post_id
        ).first()
        
        if not existing:
            new_record = DepartmentPost(
                tenant_id=tenant_id,
                department_id=dept_id,
                post_id=post_id,
                is_head=False  # 默认不是主负责人，需要手动设置
            )
            db.add(new_record)
            created_count += 1
    
    if created_count > 0:
        db.flush()
        print(f"创建了 {created_count} 条部门-岗位关系")
    else:
        print("没有需要创建的部门-岗位关系")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="安全迁移已有数据")
    parser.add_argument("--tenant-id", type=int, default=1, help="租户ID")
    args = parser.parse_args()
    
    tenant_id = args.tenant_id
    db = SessionLocal()
    
    try:
        print("=" * 50)
        print(f"开始安全迁移 (tenant_id={tenant_id})")
        print("=" * 50)
        
        # 1. 迁移部门
        print("\n--- 步骤1: 设置根部门 ---")
        migrate_departments(db, tenant_id)
        
        # 2. 迁移用户岗位
        print("\n--- 步骤2: 迁移用户岗位关系 ---")
        migrate_user_positions(db, tenant_id)
        
        # 3. 生成部门岗位关系
        print("\n--- 步骤3: 生成部门岗位关系 ---")
        generate_department_posts(db, tenant_id)
        
        db.commit()
        
        print("\n" + "=" * 50)
        print("迁移完成！")
        print("=" * 50)
        print("\n后续步骤:")
        print("1. 检查department_post表，设置正确的is_head字段")
        print("2. 对于辅导员、教学秘书等岗位，确保挂在学院级别")
        print("3. 测试ORG_CHAIN_UP功能")
        
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
