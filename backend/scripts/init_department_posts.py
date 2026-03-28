"""
补全部门-岗位关联数据
为所有部门添加所有岗位的关联，确保每个部门都能看到岗位

用法:
    python scripts/init_department_posts.py [--tenant-id TENANT_ID]

参数:
    --tenant-id: 租户ID，默认为1
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import SessionLocal
from app.models.user import Department, Position, DepartmentPost, DepartmentPostLevel


def init_all_department_posts(db: Session, tenant_id: int):
    """
    为所有部门添加所有岗位的关联
    """
    # 获取所有部门
    departments = db.query(Department).filter(
        Department.tenant_id == tenant_id
    ).all()
    
    # 获取所有岗位
    positions = db.query(Position).filter(
        Position.tenant_id == tenant_id
    ).all()
    
    print(f"找到 {len(departments)} 个部门，{len(positions)} 个岗位")
    
    # 岗位层级映射（岗位名称 -> 层级）
    post_level_map = {
        "校长": 1,
        "党委书记": 2,
        "副校长": 3,
        "院长": 1,
        "书记": 2,
        "副院长": 3,
        "副书记": 4,
        "教学秘书": 5,
        "辅导员": 6,
        "系主任": 1,
        "教研室主任": 2,
        "专任教师": 3,
        "实验员": 3,
        "处长": 1,
        "主任": 1,
        "副处长": 2,
        "副主任": 2,
        "行政秘书": 3,
        "会计": 3,
        "出纳": 3,
        "教务专员": 3,
        "学生管理专员": 3,
        "人事专员": 3,
        "采购专员": 3,
        "后勤专员": 3,
        "系统管理员": 3,
        "运维工程师": 3,
        "实训教师": 3,
    }
    
    dept_post_count = 0
    level_count = 0
    
    # 获取岗位名称映射
    pos_id_to_name = {p.id: p.name for p in positions}
    
    for dept in departments:
        print(f"\n处理部门: {dept.name} (id={dept.id})")
        
        for pos in positions:
            # 检查是否已存在关联
            existing = db.query(DepartmentPost).filter(
                and_(
                    DepartmentPost.tenant_id == tenant_id,
                    DepartmentPost.department_id == dept.id,
                    DepartmentPost.post_id == pos.id
                )
            ).first()
            
            if not existing:
                # 创建关联
                dept_post = DepartmentPost(
                    tenant_id=tenant_id,
                    department_id=dept.id,
                    post_id=pos.id,
                    is_head=False
                )
                db.add(dept_post)
                dept_post_count += 1
                print(f"  + 添加岗位: {pos.name}")
            
            # 获取岗位名称对应的层级
            pos_name = pos_id_to_name.get(pos.id, "")
            level = post_level_map.get(pos_name, 10)
            
            # 检查是否已有层级记录
            existing_level = db.query(DepartmentPostLevel).filter(
                and_(
                    DepartmentPostLevel.tenant_id == tenant_id,
                    DepartmentPostLevel.department_id == dept.id,
                    DepartmentPostLevel.post_id == pos.id
                )
            ).first()
            
            if not existing_level:
                post_level = DepartmentPostLevel(
                    tenant_id=tenant_id,
                    department_id=dept.id,
                    post_id=pos.id,
                    level=level
                )
                db.add(post_level)
                level_count += 1
    
    db.commit()
    print(f"\n完成! 共添加 {dept_post_count} 条部门-岗位关联，{level_count} 条岗位层级记录")


def main():
    parser = argparse.ArgumentParser(description="补全部门-岗位关联数据")
    parser.add_argument("--tenant-id", type=int, default=1, help="租户ID")
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        print("=" * 50)
        print(f"开始补全部门-岗位关联数据 (tenant_id={args.tenant_id})")
        print("=" * 50)
        init_all_department_posts(db, args.tenant_id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
