#!/usr/bin/env python3
"""
检查学生请假申请表的流程配置状态
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import get_db
from app.models.user import User, Department
from app.models.form import Form
from app.models.workflow import FlowDefinition, FlowNode, FlowRoute, ProcessInstance, Task
from sqlalchemy.orm import Session

def check_flow_config():
    """检查流程配置状态"""
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("学生请假申请表流程配置检查")
        print("=" * 80)
        
        # 1. 查询表单信息
        print("\n【1. 表单信息】")
        print("-" * 40)
        forms = db.query(Form).filter(
            Form.name.like('%请假%')
        ).all()
        
        if not forms:
            print("未找到包含'请假'的表单")
            return
        
        for form in forms:
            print(f"表单ID: {form.id}")
            print(f"表单名称: {form.name}")
            print(f"表单状态: {form.status}")
            print(f"关联流程定义ID: {form.flow_definition_id}")
            print()
        
        # 2. 检查流程定义
        print("\n【2. 流程定义】")
        print("-" * 40)
        for form in forms:
            flow_defs = db.query(FlowDefinition).filter(
                FlowDefinition.form_id == form.id
            ).all()
            
            if not flow_defs:
                print(f"表单 '{form.name}' 没有流程定义")
            else:
                for fd in flow_defs:
                    print(f"流程定义ID: {fd.id}")
                    print(f"流程名称: {fd.name}")
                    print(f"版本: {fd.version}")
                    print(f"激活快照ID: {fd.active_snapshot_id}")
                    print()
        
        # 3. 检查流程节点
        print("\n【3. 流程节点】")
        print("-" * 40)
        for form in forms:
            flow_defs = db.query(FlowDefinition).filter(
                FlowDefinition.form_id == form.id
            ).all()
            
            for fd in flow_defs:
                nodes = db.query(FlowNode).filter(
                    FlowNode.flow_definition_id == fd.id
                ).all()
                
                if not nodes:
                    print(f"流程定义 '{fd.name}' 没有节点")
                else:
                    print(f"流程定义 '{fd.name}' 的节点:")
                    for node in nodes:
                        print(f"  - 节点ID: {node.id}")
                        print(f"    节点名称: {node.name}")
                        print(f"    节点类型: {node.type}")
                        print(f"    指派类型: {node.assignee_type}")
                        print(f"    指派值: {node.assignee_value}")
                        print()
        
        # 4. 检查辅导员用户
        print("\n【4. 辅导员用户信息】")
        print("-" * 40)
        counselors = db.query(User).filter(
            User.phone == '13800000004'
        ).all()
        
        if not counselors:
            print("未找到手机号为13800000004的用户")
        else:
            for user in counselors:
                print(f"用户ID: {user.id}")
                print(f"用户名: {user.name}")
                print(f"手机号: {user.phone}")
                print(f"部门ID: {user.department_id}")
                print(f"是否激活: {user.is_active}")
                
                # 查询部门信息
                if user.department_id:
                    dept = db.query(Department).filter(
                        Department.id == user.department_id
                    ).first()
                    if dept:
                        print(f"部门名称: {dept.name}")
                print()
        
        # 5. 检查最近的提交记录
        print("\n【5. 最近的提交记录】")
        print("-" * 40)
        for form in forms:
            submissions_query = text("""
                SELECT 
                    s.id as submission_id,
                    s.form_id,
                    s.status as submission_status,
                    s.created_at as submit_time,
                    pi.id as process_instance_id,
                    pi.state as process_state,
                    t.id as task_id,
                    t.status as task_status,
                    t.assignee_user_id,
                    u.name as assignee_name
                FROM submission s
                LEFT JOIN process_instance pi ON pi.submission_id = s.id
                LEFT JOIN task t ON t.process_instance_id = pi.id
                LEFT JOIN "user" u ON t.assignee_user_id = u.id
                WHERE s.form_id = :form_id
                ORDER BY s.created_at DESC
                LIMIT 5
            """)
            
            results = db.execute(submissions_query, {"form_id": form.id}).fetchall()
            
            if not results:
                print(f"表单 '{form.name}' 没有提交记录")
            else:
                print(f"表单 '{form.name}' 的最近提交记录:")
                for row in results:
                    print(f"  提交ID: {row.submission_id}")
                    print(f"  提交时间: {row.submit_time}")
                    print(f"  提交状态: {row.submission_status}")
                    print(f"  流程实例ID: {row.process_instance_id}")
                    print(f"  流程状态: {row.process_state}")
                    print(f"  任务ID: {row.task_id}")
                    print(f"  任务状态: {row.task_status}")
                    print(f"  指派人ID: {row.assignee_user_id}")
                    print(f"  指派人姓名: {row.assignee_name}")
                    print()
        
        print("=" * 80)
        print("检查完成")
        print("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    check_flow_config()
