#!/usr/bin/env python3
"""
深入检查流程配置，找出流程启动失败的原因
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import get_db
from app.models.user import User, Department, UserDepartment, UserPosition, Position
from app.models.form import Form
from app.models.workflow import (
    FlowDefinition, FlowNode, FlowRoute, FlowSnapshot, 
    ProcessInstance, Task
)
from sqlalchemy.orm import Session

def deep_check_flow():
    """深入检查流程配置"""
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("深入检查流程配置 - 找出流程启动失败的原因")
        print("=" * 80)
        
        # 1. 检查表单57的流程定义详情
        print("\n【1. 流程定义详情】")
        print("-" * 40)
        
        flow_def = db.query(FlowDefinition).filter(
            FlowDefinition.id == 25
        ).first()
        
        if flow_def:
            print(f"流程定义ID: {flow_def.id}")
            print(f"流程名称: {flow_def.name}")
            print(f"版本: {flow_def.version}")
            print(f"激活快照ID: {flow_def.active_snapshot_id}")
            print(f"表单ID: {flow_def.form_id}")
            print(f"租户ID: {flow_def.tenant_id}")
        else:
            print("流程定义不存在")
            return
        
        # 2. 检查快照
        print("\n【2. 流程快照】")
        print("-" * 40)
        
        snapshot = db.query(FlowSnapshot).filter(
            FlowSnapshot.id == flow_def.active_snapshot_id
        ).first()
        
        if snapshot:
            print(f"快照ID: {snapshot.id}")
            print(f"版本标签: {snapshot.version_tag}")
            print(f"规则载荷: {snapshot.rules_payload}")
        else:
            print("激活快照不存在")
        
        # 3. 检查辅导员用户（13800000004）的完整配置
        print("\n【3. 辅导员用户完整配置】")
        print("-" * 40)
        
        counselor = db.query(User).filter(
            User.phone == '13800000004'
        ).first()
        
        if counselor:
            print(f"用户ID: {counselor.id}")
            print(f"用户名: {counselor.name}")
            print(f"部门ID: {counselor.department_id}")
            print(f"租户ID: {counselor.tenant_id}")
            print(f"是否激活: {counselor.is_active}")
            
            # 检查用户部门关联
            user_depts = db.query(UserDepartment).filter(
                UserDepartment.user_id == counselor.id
            ).all()
            
            print(f"\n用户部门关联 (user_department):")
            for ud in user_depts:
                dept = db.query(Department).filter(Department.id == ud.department_id).first()
                print(f"  - 部门ID: {ud.department_id}, 部门名: {dept.name if dept else '未知'}, 是否主部门: {ud.is_primary}")
            
            # 检查用户岗位
            user_positions = db.query(UserPosition).filter(
                UserPosition.user_id == counselor.id
            ).all()
            
            print(f"\n用户岗位关联 (user_position):")
            for up in user_positions:
                pos = db.query(Position).filter(Position.id == up.position_id).first()
                print(f"  - 岗位ID: {up.position_id}, 岗位名: {pos.name if pos else '未知'}")
        else:
            print("辅导员用户不存在")
        
        # 4. 检查学生用户（提交者）
        print("\n【4. 学生用户（提交者）】")
        print("-" * 40)
        
        # 查询最近提交的学生
        submission_query = text("""
            SELECT s.id, s.submitter_user_id, u.name, u.department_id, d.name as dept_name
            FROM submission s
            JOIN "user" u ON s.submitter_user_id = u.id
            LEFT JOIN department d ON u.department_id = d.id
            WHERE s.form_id = 57
            ORDER BY s.created_at DESC
            LIMIT 1
        """)
        
        result = db.execute(submission_query).fetchone()
        
        if result:
            print(f"提交ID: {result.id}")
            print(f"学生用户ID: {result.submitter_user_id}")
            print(f"学生姓名: {result.name}")
            print(f"学生部门ID: {result.department_id}")
            print(f"学生部门名: {result.dept_name}")
            
            # 检查学生的岗位配置
            student_positions = db.query(UserPosition).filter(
                UserPosition.user_id == result.submitter_user_id
            ).all()
            
            print(f"\n学生岗位关联:")
            for up in student_positions:
                pos = db.query(Position).filter(Position.id == up.position_id).first()
                print(f"  - 岗位ID: {up.position_id}, 岗位名: {pos.name if pos else '未知'}")
        else:
            print("没有提交记录")
        
        # 5. 检查部门层级关系
        print("\n【5. 部门层级关系】")
        print("-" * 40)
        
        # 查询所有部门
        all_depts = db.query(Department).filter(
            Department.tenant_id == flow_def.tenant_id
        ).all()
        
        print(f"租户 {flow_def.tenant_id} 的部门结构:")
        for dept in all_depts:
            print(f"  - ID: {dept.id}, 名称: {dept.name}, 父部门ID: {dept.parent_id}, 是否根部门: {dept.is_root}")
        
        # 6. 检查岗位配置
        print("\n【6. 岗位配置】")
        print("-" * 40)
        
        # 查询岗位2（辅导员）和岗位15（教学秘书）
        positions = db.query(Position).filter(
            Position.id.in_([2, 15])
        ).all()
        
        for pos in positions:
            print(f"  - 岗位ID: {pos.id}, 岗位名: {pos.name}")
        
        # 7. 模拟AssignmentService.select_assignee
        print("\n【7. 模拟任务分配】")
        print("-" * 40)
        
        # 获取辅导员审批节点
        counselor_node = db.query(FlowNode).filter(
            FlowNode.flow_definition_id == flow_def.id,
            FlowNode.name == '辅导员审批节点'
        ).first()
        
        if counselor_node:
            print(f"辅导员审批节点:")
            print(f"  - 节点ID: {counselor_node.id}")
            print(f"  - 指派类型: {counselor_node.assignee_type}")
            print(f"  - 指派值: {counselor_node.assignee_value}")
            
            # 检查是否有用户具有岗位2
            users_with_pos2 = db.query(UserPosition).filter(
                UserPosition.position_id == 2,
                UserPosition.tenant_id == flow_def.tenant_id
            ).all()
            
            print(f"\n具有岗位2（辅导员）的用户:")
            for up in users_with_pos2:
                user = db.query(User).filter(User.id == up.user_id).first()
                if user:
                    print(f"  - 用户ID: {user.id}, 姓名: {user.name}, 部门ID: {user.department_id}")
        
        print("\n" + "=" * 80)
        print("检查完成")
        print("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    deep_check_flow()
