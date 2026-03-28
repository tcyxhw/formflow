"""
为信息学院补充部门-岗位关联数据

根据同类学院（计算机学院、艺术学院）的岗位配置，为信息学院添加相同的岗位

用法:
    python scripts/init_info_college_posts.py [--tenant-id TENANT_ID]

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


def init_info_college_posts(db: Session, tenant_id: int):
    """
    为信息学院添加部门-岗位关联
    """
    # 查找信息学院
    info_college = db.query(Department).filter(
        Department.tenant_id == tenant_id,
        Department.name == "信息学院"
    ).first()
    
    if not info_college:
        print("错误: 未找到信息学院部门")
        return
    
    print(f"找到信息学院: id={info_college.id}, name={info_college.name}")
    
    # 查找计算机学院作为参考
    cs_college = db.query(Department).filter(
        Department.tenant_id == tenant_id,
        Department.name == "计算机学院"
    ).first()
    
    if not cs_college:
        print("错误: 未找到计算机学院作为参考")
        return
    
    print(f"参考计算机学院: id={cs_college.id}")
    
    # 获取计算机学院的岗位关联
    cs_posts = db.query(DepartmentPost).filter(
        DepartmentPost.tenant_id == tenant_id,
        DepartmentPost.department_id == cs_college.id
    ).all()
    
    print(f"计算机学院有 {len(cs_posts)} 个岗位关联")
    
    # 信息学院的子部门
    info_sub_depts = db.query(Department).filter(
        Department.tenant_id == tenant_id,
        Department.parent_id == info_college.id
    ).all()
    
    print(f"信息学院有 {len(info_sub_depts)} 个子部门: {[d.name for d in info_sub_depts]}")
    
    # 计算机学院的子部门
    cs_sub_depts = db.query(Department).filter(
        Department.tenant_id == tenant_id,
        Department.parent_id == cs_college.id
    ).all()
    
    print(f"计算机学院有 {len(cs_sub_depts)} 个子部门: {[d.name for d in cs_sub_depts]}")
    
    # 岗位层级映射
    post_level_map = {
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
        "主任": 1,
        "副主任": 2,
        "行政秘书": 3,
        "实训教师": 3,
    }
    
    count = 0
    
    # 1. 为信息学院（学院级别）添加岗位
    for cs_post in cs_posts:
        pos = db.query(Position).filter(Position.id == cs_post.post_id).first()
        if not pos:
            continue
        
        # 检查是否已存在
        existing = db.query(DepartmentPost).filter(
            and_(
                DepartmentPost.tenant_id == tenant_id,
                DepartmentPost.department_id == info_college.id,
                DepartmentPost.post_id == cs_post.post_id
            )
        ).first()
        
        if not existing:
            new_dp = DepartmentPost(
                tenant_id=tenant_id,
                department_id=info_college.id,
                post_id=cs_post.post_id,
                is_head=False
            )
            db.add(new_dp)
            print(f"  + 添加岗位: {pos.name} -> 信息学院")
            count += 1
            
            # 添加层级
            level = post_level_map.get(pos.name, 10)
            existing_level = db.query(DepartmentPostLevel).filter(
                and_(
                    DepartmentPostLevel.tenant_id == tenant_id,
                    DepartmentPostLevel.department_id == info_college.id,
                    DepartmentPostLevel.post_id == cs_post.post_id
                )
            ).first()
            if not existing_level:
                new_level = DepartmentPostLevel(
                    tenant_id=tenant_id,
                    department_id=info_college.id,
                    post_id=cs_post.post_id,
                    level=level
                )
                db.add(new_level)
    
    # 2. 为子部门添加岗位（根据同名子部门复制）
    for info_sub in info_sub_depts:
        # 找到计算机学院对应的子部门
        cs_sub = next((d for d in cs_sub_depts if d.name == info_sub.name), None)
        
        if cs_sub:
            # 获取该子部门的岗位
            cs_sub_posts = db.query(DepartmentPost).filter(
                DepartmentPost.tenant_id == tenant_id,
                DepartmentPost.department_id == cs_sub.id
            ).all()
            
            for cs_sub_post in cs_sub_posts:
                pos = db.query(Position).filter(Position.id == cs_sub_post.post_id).first()
                if not pos:
                    continue
                
                # 检查是否已存在
                existing = db.query(DepartmentPost).filter(
                    and_(
                        DepartmentPost.tenant_id == tenant_id,
                        DepartmentPost.department_id == info_sub.id,
                        DepartmentPost.post_id == cs_sub_post.post_id
                    )
                ).first()
                
                if not existing:
                    new_dp = DepartmentPost(
                        tenant_id=tenant_id,
                        department_id=info_sub.id,
                        post_id=cs_sub_post.post_id,
                        is_head=False
                    )
                    db.add(new_dp)
                    print(f"  + 添加岗位: {pos.name} -> {info_sub.name}")
                    count += 1
                    
                    # 添加层级
                    level = post_level_map.get(pos.name, 10)
                    existing_level = db.query(DepartmentPostLevel).filter(
                        and_(
                            DepartmentPostLevel.tenant_id == tenant_id,
                            DepartmentPostLevel.department_id == info_sub.id,
                            DepartmentPostLevel.post_id == cs_sub_post.post_id
                        )
                    ).first()
                    if not existing_level:
                        new_level = DepartmentPostLevel(
                            tenant_id=tenant_id,
                            department_id=info_sub.id,
                            post_id=cs_sub_post.post_id,
                            level=level
                        )
                        db.add(new_level)
        else:
            print(f"  警告: 信息学院的子部门 '{info_sub.name}' 在计算机学院中没有对应的部门")
    
    db.commit()
    print(f"\n完成! 共添加 {count} 条部门-岗位关联记录")


def main():
    parser = argparse.ArgumentParser(description="为信息学院补充岗位数据")
    parser.add_argument("--tenant-id", type=int, default=1, help="租户ID")
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        print("=" * 50)
        print(f"开始为信息学院补充岗位数据 (tenant_id={args.tenant_id})")
        print("=" * 50)
        init_info_college_posts(db, args.tenant_id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
