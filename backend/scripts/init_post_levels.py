"""
初始化岗位层级数据
根据plan1.md的要求，为每个部门的每个岗位设置层级

用法:
    python scripts/init_post_levels.py [--tenant-id TENANT_ID]

参数:
    --tenant-id: 租户ID，默认为1
"""
import sys
import os
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import SessionLocal
from app.models.user import Department, Position, DepartmentPost, DepartmentPostLevel


def init_department_post_levels(db: Session, tenant_id: int):
    """
    为每个部门的每个岗位设置层级
    
    层级定义（越小越高）：
    - 学院级别：院长(1) > 书记(2) > 副院长(3) > 副书记(4) > 教学秘书(5) > 辅导员(6)
    - 系/教研室：系主任(1) > 教研室主任(2) > 专任教师(3) > 实验员(3)
    - 行政级别：处长/主任(1) > 副处长/副主任(2) > 专员(3)
    """
    
    # 岗位层级映射（岗位名称 -> 层级）
    post_level_map = {
        # 校级岗位
        "校长": 1,
        "党委书记": 2,
        "副校长": 3,
        
        # 学院级别岗位
        "院长": 1,
        "书记": 2,
        "副院长": 3,
        "副书记": 4,
        "教学秘书": 5,
        "辅导员": 6,
        
        # 系/教研室岗位
        "系主任": 1,
        "教研室主任": 2,
        "专任教师": 3,
        "实验员": 3,
        
        # 行政岗位
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
    
    # 获取所有部门-岗位关系
    department_posts = db.query(DepartmentPost).filter(
        DepartmentPost.tenant_id == tenant_id
    ).all()
    
    # 获取所有岗位
    positions = db.query(Position).filter(
        Position.tenant_id == tenant_id
    ).all()
    pos_name_to_id = {p.name: p.id for p in positions}
    
    for dp in department_posts:
        # 获取岗位名称
        post = db.query(Position).filter(Position.id == dp.post_id).first()
        if not post:
            continue
        
        # 获取岗位层级
        level = post_level_map.get(post.name)
        if level is None:
            # 默认层级为10（未知岗位）
            level = 10
            print(f"警告: 岗位 '{post.name}' 未定义层级，使用默认层级 {level}")
        
        # 检查是否已存在层级记录
        existing = db.query(DepartmentPostLevel).filter(
            and_(
                DepartmentPostLevel.tenant_id == tenant_id,
                DepartmentPostLevel.department_id == dp.department_id,
                DepartmentPostLevel.post_id == dp.post_id
            )
        ).first()
        
        if existing:
            # 更新层级
            existing.level = level
            print(f"更新层级: 部门ID={dp.department_id}, 岗位={post.name}, 层级={level}")
        else:
            # 创建层级记录
            post_level = DepartmentPostLevel(
                tenant_id=tenant_id,
                department_id=dp.department_id,
                post_id=dp.post_id,
                level=level
            )
            db.add(post_level)
            print(f"创建层级: 部门ID={dp.department_id}, 岗位={post.name}, 层级={level}")
    
    db.commit()
    print(f"岗位层级初始化完成，共处理 {len(department_posts)} 条记录")


def main():
    parser = argparse.ArgumentParser(description="初始化岗位层级数据")
    parser.add_argument("--tenant-id", type=int, default=1, help="租户ID")
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        init_department_post_levels(db, args.tenant_id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
