"""
初始化组织结构数据
根据plan1.md的要求，创建部门、岗位、角色、用户等基础数据

用法:
    python scripts/init_organization_data.py [--tenant-id TENANT_ID]

参数:
    --tenant-id: 租户ID，默认为1
"""
import sys
import os
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import (
    Department, Position, Role, User, UserRole, 
    DepartmentPost, UserDepartmentPost, Tenant
)
from app.core.security import hash_password


def get_or_create_tenant(db: Session, tenant_id: int, tenant_name: str = "示例大学") -> Tenant:
    """获取或创建租户"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        tenant = Tenant(id=tenant_id, name=tenant_name)
        db.add(tenant)
        db.flush()
        print(f"创建租户: {tenant_name} (id={tenant_id})")
    return tenant


def init_departments(db: Session, tenant_id: int) -> dict:
    """初始化部门数据
    
    返回: {部门名称: 部门ID} 的映射
    """
    departments_data = [
        # (id, name, parent_name, type, is_root, sort_order)
        (1, "学校", None, "school", True, 0),
        (2, "党政办公室", "学校", "office", False, 1),
        (3, "教务处", "学校", "office", False, 2),
        (4, "学生工作处", "学校", "office", False, 3),
        (5, "人事处", "学校", "office", False, 4),
        (6, "财务处", "学校", "office", False, 5),
        (7, "资产后勤处", "学校", "office", False, 6),
        (8, "信息化中心", "学校", "office", False, 7),
        (20, "计算机学院", "学校", "college", False, 10),
        (21, "学院办公室", "计算机学院", "department", False, 1),
        (22, "教学办公室", "计算机学院", "department", False, 2),
        (23, "学工办公室", "计算机学院", "department", False, 3),
        (24, "软件工程系", "计算机学院", "department", False, 4),
        (25, "软件工程教研室", "软件工程系", "class", False, 1),
        (26, "实验中心", "计算机学院", "department", False, 5),
        (30, "艺术学院", "学校", "college", False, 20),
        (31, "艺术学院办公室", "艺术学院", "department", False, 1),
        (32, "艺术学院教学办", "艺术学院", "department", False, 2),
        (33, "艺术学院学工办", "艺术学院", "department", False, 3),
        (34, "视觉传达系", "艺术学院", "department", False, 4),
        (35, "视觉传达教研室", "视觉传达系", "class", False, 1),
        (36, "实训中心", "艺术学院", "department", False, 5),
    ]
    
    # 创建部门名称到ID的映射
    dept_name_to_id = {}
    
    for dept_id, name, parent_name, dept_type, is_root, sort_order in departments_data:
        existing = db.query(Department).filter(
            Department.tenant_id == tenant_id,
            Department.id == dept_id
        ).first()
        
        if not existing:
            parent_id = dept_name_to_id.get(parent_name) if parent_name else None
            dept = Department(
                id=dept_id,
                tenant_id=tenant_id,
                name=name,
                parent_id=parent_id,
                type=dept_type,
                is_root=is_root,
                sort_order=sort_order
            )
            db.add(dept)
            print(f"创建部门: {name} (id={dept_id}, parent={parent_name})")
        
        dept_name_to_id[name] = dept_id
    
    db.flush()
    return dept_name_to_id


def init_positions(db: Session, tenant_id: int) -> dict:
    """初始化岗位数据
    
    返回: {岗位名称: 岗位ID} 的映射
    """
    positions_data = [
        # (id, name)
        (1, "校长"),
        (2, "党委书记"),
        (3, "副校长"),
        (10, "院长"),
        (11, "书记"),
        (12, "副院长"),
        (14, "辅导员"),  # 修改ID避免与已有数据冲突
        (15, "教学秘书"),
        (16, "系主任"),
        (17, "教研室主任"),
        (18, "专任教师"),
        (19, "实验员"),
        (20, "处长"),
        (21, "副处长"),
        (22, "会计"),
        (23, "出纳"),
        (24, "主任"),
        (25, "副主任"),
        (26, "行政秘书"),
        (27, "系统管理员"),
        (28, "运维工程师"),
        (29, "教务专员"),
        (30, "学生管理专员"),
        (31, "人事专员"),
        (32, "采购专员"),
        (33, "后勤专员"),
        (34, "实训教师"),
        (35, "副书记"),  # 使用新ID
    ]
    
    pos_name_to_id = {}
    
    for pos_id, name in positions_data:
        # 先按名称查找
        existing_by_name = db.query(Position).filter(
            Position.tenant_id == tenant_id,
            Position.name == name
        ).first()
        
        if existing_by_name:
            pos_name_to_id[name] = existing_by_name.id
            print(f"岗位已存在: {name} (id={existing_by_name.id})")
            continue
        
        # 检查ID是否被占用
        existing_by_id = db.query(Position).filter(
            Position.tenant_id == tenant_id,
            Position.id == pos_id
        ).first()
        
        if not existing_by_id:
            pos = Position(id=pos_id, tenant_id=tenant_id, name=name)
            db.add(pos)
            print(f"创建岗位: {name} (id={pos_id})")
            pos_name_to_id[name] = pos_id
        else:
            # ID被占用，查找已有的同名岗位或跳过
            print(f"跳过岗位 {name}，ID {pos_id} 已被 {existing_by_id.name} 占用")
    
    db.flush()
    return pos_name_to_id


def init_roles(db: Session, tenant_id: int) -> dict:
    """初始化系统角色
    
    返回: {角色名称: 角色ID} 的映射
    """
    roles_data = [
        # (name, description)
        ("管理员", "系统管理员，拥有所有权限"),
        ("老师", "教师角色，可创建表单和审批"),
        ("学生", "学生角色，可填写和提交表单"),
    ]
    
    role_name_to_id = {}
    
    for name, description in roles_data:
        existing = db.query(Role).filter(
            Role.tenant_id == tenant_id,
            Role.name == name
        ).first()
        
        if not existing:
            role = Role(tenant_id=tenant_id, name=name, description=description)
            db.add(role)
            db.flush()
            print(f"创建角色: {name} (id={role.id})")
        else:
            role = existing
        
        role_name_to_id[name] = role.id
    
    db.flush()
    return role_name_to_id


def init_department_posts(db: Session, tenant_id: int, dept_name_to_id: dict, pos_name_to_id: dict):
    """初始化部门-岗位关系"""
    department_posts_data = [
        # (部门名称, 岗位名称, 是否主负责人)
        
        # 学校（根部门）- 校级岗位
        ("学校", "校长", True),
        ("学校", "党委书记", False),
        ("学校", "副校长", False),
        
        # 党政办公室
        ("党政办公室", "主任", True),
        ("党政办公室", "副主任", False),
        ("党政办公室", "行政秘书", False),
        
        # 教务处
        ("教务处", "处长", True),
        ("教务处", "副处长", False),
        ("教务处", "教务专员", False),
        
        # 学生工作处
        ("学生工作处", "处长", True),
        ("学生工作处", "副处长", False),
        ("学生工作处", "学生管理专员", False),
        
        # 人事处
        ("人事处", "处长", True),
        ("人事处", "副处长", False),
        ("人事处", "人事专员", False),
        
        # 财务处
        ("财务处", "处长", True),
        ("财务处", "副处长", False),
        ("财务处", "会计", False),
        ("财务处", "出纳", False),
        
        # 资产后勤处
        ("资产后勤处", "处长", True),
        ("资产后勤处", "副处长", False),
        ("资产后勤处", "采购专员", False),
        ("资产后勤处", "后勤专员", False),
        
        # 信息化中心
        ("信息化中心", "主任", True),
        ("信息化中心", "副主任", False),
        ("信息化中心", "系统管理员", False),
        ("信息化中心", "运维工程师", False),
        
        # 计算机学院 - 关键：辅导员和教学秘书挂在学院级别
        ("计算机学院", "院长", True),
        ("计算机学院", "书记", False),
        ("计算机学院", "副院长", False),
        ("计算机学院", "副书记", False),
        ("计算机学院", "辅导员", False),  # 链路岗位
        ("计算机学院", "教学秘书", False),  # 链路岗位
        
        # 学院办公室
        ("学院办公室", "主任", True),
        ("学院办公室", "行政秘书", False),
        
        # 教学办公室（不再挂教学秘书）
        ("教学办公室", "主任", True),
        
        # 学工办公室（不再挂辅导员）
        ("学工办公室", "主任", True),
        
        # 软件工程系
        ("软件工程系", "系主任", True),
        
        # 软件工程教研室
        ("软件工程教研室", "教研室主任", True),
        ("软件工程教研室", "专任教师", False),
        
        # 实验中心
        ("实验中心", "主任", True),
        ("实验中心", "实验员", False),
        
        # 艺术学院
        ("艺术学院", "院长", True),
        ("艺术学院", "书记", False),
        ("艺术学院", "副院长", False),
        ("艺术学院", "副书记", False),
        ("艺术学院", "辅导员", False),  # 链路岗位
        ("艺术学院", "教学秘书", False),  # 链路岗位
        
        # 艺术学院办公室
        ("艺术学院办公室", "主任", True),
        ("艺术学院办公室", "行政秘书", False),
        
        # 艺术学院教学办
        ("艺术学院教学办", "主任", True),
        
        # 艺术学院学工办
        ("艺术学院学工办", "主任", True),
        
        # 视觉传达系
        ("视觉传达系", "系主任", True),
        
        # 视觉传达教研室
        ("视觉传达教研室", "教研室主任", True),
        ("视觉传达教研室", "专任教师", False),
        
        # 实训中心
        ("实训中心", "主任", True),
        ("实训中心", "实训教师", False),
    ]
    
    for dept_name, pos_name, is_head in department_posts_data:
        dept_id = dept_name_to_id.get(dept_name)
        pos_id = pos_name_to_id.get(pos_name)
        
        if not dept_id or not pos_id:
            print(f"警告: 部门 '{dept_name}' 或岗位 '{pos_name}' 不存在")
            continue
        
        existing = db.query(DepartmentPost).filter(
            DepartmentPost.tenant_id == tenant_id,
            DepartmentPost.department_id == dept_id,
            DepartmentPost.post_id == pos_id
        ).first()
        
        if not existing:
            dept_post = DepartmentPost(
                tenant_id=tenant_id,
                department_id=dept_id,
                post_id=pos_id,
                is_head=is_head
            )
            db.add(dept_post)
            print(f"创建部门-岗位关系: {dept_name} - {pos_name} (is_head={is_head})")
    
    db.flush()


def init_users(db: Session, tenant_id: int, role_name_to_id: dict) -> dict:
    """初始化示例用户
    
    返回: {用户名: 用户ID} 的映射
    """
    users_data = [
        # (id, account, name, role_name, email)
        (100, "admin", "系统管理员", "管理员", "admin@example.com"),
        (301, "xiaoming", "小明", "学生", "xiaoming@example.com"),
        (302, "xiaohong", "小红", "学生", "xiaohong@example.com"),
        (501, "zhanglaoshi", "张老师", "老师", "zhang@example.com"),
        (601, "wangjiaoshou", "王教授", "老师", "wang@example.com"),
        (701, "lizhangyuan", "李院长", "老师", "li@example.com"),
        (801, "zhaokuaiji", "赵会计", "老师", "zhao@example.com"),
        (901, "sunfudaoyuan", "孙辅导员", "老师", "sun@example.com"),
        (1001, "zhoujiaoxue", "周教学秘书", "老师", "zhou@example.com"),
    ]
    
    user_name_to_id = {}
    
    for user_id, account, name, role_name, email in users_data:
        existing = db.query(User).filter(
            User.tenant_id == tenant_id,
            User.id == user_id
        ).first()
        
        if not existing:
            user = User(
                id=user_id,
                tenant_id=tenant_id,
                account=account,
                name=name,
                password_hash=hash_password("123456"),  # 默认密码
                email=email,
                is_active=True
            )
            db.add(user)
            db.flush()
            print(f"创建用户: {name} (id={user_id}, account={account})")
            
            # 分配角色
            role_id = role_name_to_id.get(role_name)
            if role_id:
                user_role = UserRole(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    role_id=role_id
                )
                db.add(user_role)
                print(f"  分配角色: {role_name}")
        else:
            user_id = existing.id
        
        user_name_to_id[name] = user_id
    
    db.flush()
    return user_name_to_id


def init_user_department_posts(db: Session, tenant_id: int, user_name_to_id: dict, 
                                dept_name_to_id: dict, pos_name_to_id: dict):
    """初始化用户-部门-岗位关系"""
    user_dept_posts_data = [
        # (用户名, 部门名称, 岗位名称)
        
        # 学生挂在学院或系
        ("小明", "软件工程系", None),  # 学生没有岗位
        ("小红", "艺术学院", None),
        
        # 老师的部门岗位关系
        ("张老师", "计算机学院", "辅导员"),  # 辅导员挂在学院
        ("王教授", "软件工程教研室", "专任教师"),
        ("李院长", "计算机学院", "院长"),
        ("赵会计", "财务处", "会计"),
        ("孙辅导员", "艺术学院", "辅导员"),  # 艺术学院的辅导员
        ("周教学秘书", "计算机学院", "教学秘书"),  # 教学秘书挂在学院
    ]
    
    for user_name, dept_name, pos_name in user_dept_posts_data:
        user_id = user_name_to_id.get(user_name)
        dept_id = dept_name_to_id.get(dept_name)
        pos_id = pos_name_to_id.get(pos_name) if pos_name else None
        
        if not user_id or not dept_id:
            print(f"警告: 用户 '{user_name}' 或部门 '{dept_name}' 不存在")
            continue
        
        existing = db.query(UserDepartmentPost).filter(
            UserDepartmentPost.tenant_id == tenant_id,
            UserDepartmentPost.user_id == user_id,
            UserDepartmentPost.department_id == dept_id,
            UserDepartmentPost.post_id == pos_id
        ).first()
        
        if not existing:
            user_dept_post = UserDepartmentPost(
                tenant_id=tenant_id,
                user_id=user_id,
                department_id=dept_id,
                post_id=pos_id
            )
            db.add(user_dept_post)
            print(f"创建用户-部门-岗位关系: {user_name} - {dept_name} - {pos_name or '无岗位'}")
    
    db.flush()


def main():
    parser = argparse.ArgumentParser(description="初始化组织结构数据")
    parser.add_argument("--tenant-id", type=int, default=1, help="租户ID")
    args = parser.parse_args()
    
    tenant_id = args.tenant_id
    db = SessionLocal()
    
    try:
        print("=" * 50)
        print(f"开始初始化组织结构数据 (tenant_id={tenant_id})")
        print("=" * 50)
        
        # 1. 创建租户
        get_or_create_tenant(db, tenant_id)
        
        # 2. 初始化部门
        print("\n--- 初始化部门 ---")
        dept_name_to_id = init_departments(db, tenant_id)
        
        # 3. 初始化岗位
        print("\n--- 初始化岗位 ---")
        pos_name_to_id = init_positions(db, tenant_id)
        
        # 4. 初始化角色
        print("\n--- 初始化角色 ---")
        role_name_to_id = init_roles(db, tenant_id)
        
        # 5. 初始化部门-岗位关系
        print("\n--- 初始化部门-岗位关系 ---")
        init_department_posts(db, tenant_id, dept_name_to_id, pos_name_to_id)
        
        # 6. 初始化用户
        print("\n--- 初始化用户 ---")
        user_name_to_id = init_users(db, tenant_id, role_name_to_id)
        
        # 7. 初始化用户-部门-岗位关系
        print("\n--- 初始化用户-部门-岗位关系 ---")
        init_user_department_posts(db, tenant_id, user_name_to_id, dept_name_to_id, pos_name_to_id)
        
        # 提交事务
        db.commit()
        
        print("\n" + "=" * 50)
        print("初始化完成！")
        print("=" * 50)
        print("\n测试场景:")
        print("1. 学生请假找辅导员 (ORG_CHAIN_UP)")
        print("   发起人: 小明 (department_id=24 软件工程系)")
        print("   节点配置: matchMode=ORG_CHAIN_UP, postId=14 (辅导员)")
        print("   预期结果: 找到张老师 (department_id=20 计算机学院)")
        print("\n2. 学生请假找院长 (ORG_CHAIN_UP)")
        print("   发起人: 小明 (department_id=24 软件工程系)")
        print("   节点配置: matchMode=ORG_CHAIN_UP, postId=10 (院长)")
        print("   预期结果: 找到李院长 (department_id=20 计算机学院)")
        print("\n3. 报销找财务会计 (FIXED)")
        print("   节点配置: matchMode=FIXED, departmentId=6, postId=22")
        print("   预期结果: 找到赵会计")
        print("\n默认用户密码: 123456")
        
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
