#!/usr/bin/env python3
"""
诊断教学秘书权限问题的脚本

检查用户 13800000009 的数据状态，找出为什么只能看到自己
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import (
    User, UserDepartment, UserDepartmentPost, UserPosition,
    Department, Position, DepartmentPostLevel
)

def check_teaching_secretary_data():
    """检查教学秘书的数据状态"""
    db: Session = SessionLocal()
    
    print("=" * 80)
    print("🔍 教学秘书权限诊断脚本")
    print("=" * 80)
    
    try:
        # 1. 查找教学秘书用户
        print("\n[步骤1] 查找教学秘书用户...")
        teaching_secretary = db.query(User).filter(
            User.account == "13800000009"
        ).first()
        
        if not teaching_secretary:
            print("❌ 未找到账号为 13800000009 的用户")
            # 尝试查找用户名包含"教学秘书"的用户
            teaching_secretary = db.query(User).filter(
                User.name.contains("教学秘书")
            ).first()
            if teaching_secretary:
                print(f"✅ 找到用户名包含'教学秘书'的用户: ID={teaching_secretary.id}, 账号={teaching_secretary.account}, 名称={teaching_secretary.name}")
            else:
                print("❌ 也未找到名称包含'教学秘书'的用户")
                return
        else:
            print(f"✅ 找到用户: ID={teaching_secretary.id}, 名称={teaching_secretary.name}")
        
        user_id = teaching_secretary.id
        tenant_id = teaching_secretary.tenant_id
        department_id = teaching_secretary.department_id
        
        print(f"   用户ID: {user_id}")
        print(f"   租户ID: {tenant_id}")
        print(f"   主属部门ID: {department_id}")
        
        # 2. 检查用户部门信息
        print("\n[步骤2] 检查用户部门信息...")
        
        # UserDepartment 表
        user_depts = db.query(UserDepartment).filter(
            UserDepartment.user_id == user_id,
            UserDepartment.tenant_id == tenant_id
        ).all()
        
        if user_depts:
            print(f"✅ UserDepartment 表中有 {len(user_depts)} 条记录:")
            for ud in user_depts:
                dept = db.query(Department).filter(Department.id == ud.department_id).first()
                dept_name = dept.name if dept else "未知部门"
                print(f"   - 部门ID: {ud.department_id}, 名称: {dept_name}, 是否主部门: {ud.is_primary}")
        else:
            print("❌ UserDepartment 表中无记录")
        
        # User.department_id 字段
        if department_id:
            dept = db.query(Department).filter(Department.id == department_id).first()
            dept_name = dept.name if dept else "未知部门"
            print(f"✅ User.department_id 字段有值: {department_id} ({dept_name})")
        else:
            print("❌ User.department_id 字段为空")
        
        # 3. 检查用户岗位信息
        print("\n[步骤3] 检查用户岗位信息...")
        
        # UserDepartmentPost 表
        user_dept_posts = db.query(UserDepartmentPost).filter(
            UserDepartmentPost.user_id == user_id,
            UserDepartmentPost.tenant_id == tenant_id
        ).all()
        
        if user_dept_posts:
            print(f"✅ UserDepartmentPost 表中有 {len(user_dept_posts)} 条记录:")
            for udp in user_dept_posts:
                post = db.query(Position).filter(Position.id == udp.post_id).first()
                post_name = post.name if post else "未知岗位"
                dept = db.query(Department).filter(Department.id == udp.department_id).first()
                dept_name = dept.name if dept else "未知部门"
                print(f"   - 部门ID: {udp.department_id} ({dept_name}), 岗位ID: {udp.post_id} ({post_name})")
        else:
            print("❌ UserDepartmentPost 表中无记录")
        
        # UserPosition 表
        user_positions = db.query(UserPosition).filter(
            UserPosition.user_id == user_id,
            UserPosition.tenant_id == tenant_id
        ).all()
        
        if user_positions:
            print(f"✅ UserPosition 表中有 {len(user_positions)} 条记录:")
            for up in user_positions:
                post = db.query(Position).filter(Position.id == up.position_id).first()
                post_name = post.name if post else "未知岗位"
                print(f"   - 岗位ID: {up.position_id} ({post_name})")
        else:
            print("❌ UserPosition 表中无记录")
        
        # 4. 检查岗位层级信息
        print("\n[步骤4] 检查岗位层级信息...")
        
        # 获取用户实际使用的部门和岗位
        actual_dept_id = None
        actual_post_id = None
        
        if user_depts:
            actual_dept_id = user_depts[0].department_id
        elif department_id:
            actual_dept_id = department_id
        
        if user_dept_posts:
            actual_post_id = user_dept_posts[0].post_id
        elif user_positions:
            actual_post_id = user_positions[0].position_id
        
        if actual_dept_id and actual_post_id:
            print(f"   使用部门ID: {actual_dept_id}, 岗位ID: {actual_post_id}")
            
            level_info = db.query(DepartmentPostLevel).filter(
                DepartmentPostLevel.tenant_id == tenant_id,
                DepartmentPostLevel.department_id == actual_dept_id,
                DepartmentPostLevel.post_id == actual_post_id
            ).first()
            
            if level_info:
                print(f"✅ 找到层级信息: level={level_info.level}")
            else:
                print(f"❌ 未找到层级信息 (tenant_id={tenant_id}, dept_id={actual_dept_id}, post_id={actual_post_id})")
        else:
            print("❌ 无法确定部门ID或岗位ID")
        
        # 5. 检查同部门下的其他用户
        print("\n[步骤5] 检查同部门下的其他用户...")
        
        if actual_dept_id:
            # 获取同部门的所有用户
            dept_users = db.query(UserDepartment).filter(
                UserDepartment.tenant_id == tenant_id,
                UserDepartment.department_id == actual_dept_id
            ).all()
            
            print(f"   部门ID {actual_dept_id} 下有 {len(dept_users)} 个用户关联:")
            for du in dept_users:
                user = db.query(User).filter(User.id == du.user_id).first()
                if user:
                    print(f"   - 用户ID: {user.id}, 账号: {user.account}, 名称: {user.name}")
        
        # 6. 检查辅导员信息
        print("\n[步骤6] 检查辅导员信息...")
        
        # 查找岗位为"辅导员"的用户
        counselor_positions = db.query(Position).filter(
            Position.name.contains("辅导员"),
            Position.tenant_id == tenant_id
        ).all()
        
        if counselor_positions:
            for cp in counselor_positions:
                print(f"   岗位ID: {cp.id}, 名称: {cp.name}")
                
                # 查找有此岗位的用户
                counselor_users = db.query(UserDepartmentPost).filter(
                    UserDepartmentPost.post_id == cp.id,
                    UserDepartmentPost.tenant_id == tenant_id
                ).all()
                
                for cu in counselor_users:
                    user = db.query(User).filter(User.id == cu.user_id).first()
                    dept = db.query(Department).filter(Department.id == cu.department_id).first()
                    if user and dept:
                        print(f"     用户ID: {user.id}, 名称: {user.name}, 部门: {dept.name}")
        
        print("\n" + "=" * 80)
        print("诊断完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_teaching_secretary_data()