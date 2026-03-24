"""
测试数据生成脚本
用于生成审批待办、表单提交等测试数据
"""
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, get_db
from app.models.user import User, Department, Position, ApprovalGroup, ApprovalGroupMember, Tenant
from app.models.form import Form, FormVersion, FormPermission, Submission
from app.models.workflow import (
    FlowDefinition, FlowNode, FlowRoute, FlowSnapshot,
    ProcessInstance, Task, TaskActionLog
)


def generate_test_data():
    """生成测试数据"""
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 1. 获取或创建测试用户
        print("=== 1. 创建测试用户和部门 ===")
        
        # 创建测试租户
        tenant = db.query(Tenant).filter(Tenant.name == "测试高校").first()
        if not tenant:
            tenant = Tenant(name="测试高校")
            db.add(tenant)
            db.flush()
            print(f"  创建租户: {tenant.name} (ID: {tenant.id})")
        
        # 创建测试部门
        dept = db.query(Department).filter(
            Department.name == "测试部门",
            Department.tenant_id == tenant.id
        ).first()
        if not dept:
            dept = Department(
                name="测试部门",
                type="department",
                tenant_id=tenant.id,
                created_at=datetime.now()
            )
            db.add(dept)
            db.flush()
            print(f"  创建部门: {dept.name} (ID: {dept.id})")
        
        # 创建测试岗位
        position = db.query(Position).filter(
            Position.name == "测试岗位",
            Position.tenant_id == tenant.id
        ).first()
        if not position:
            position = Position(name="测试岗位", tenant_id=tenant.id)
            db.add(position)
            db.flush()
            print(f"  创建岗位: {position.name} (ID: {position.id})")
        
        # 获取当前唯一用户（用于测试）
        user = db.query(User).filter(User.is_active == True).first()
        if not user:
            user = User(
                account="test_user",
                password_hash="test_hash",
                name="测试用户",
                department_id=dept.id,
                tenant_id=tenant.id,
                is_active=True
            )
            db.add(user)
            db.flush()
            print(f"  创建用户: {user.name} (ID: {user.id})")
        else:
            print(f"  使用现有用户: {user.name} (ID: {user.id})")
        
        # 创建第二个用户（用于提交表单）
        user2 = db.query(User).filter(User.account == "submitter").first()
        if not user2:
            user2 = User(
                account="submitter",
                password_hash="test_hash",
                name="表单提交者",
                department_id=dept.id,
                tenant_id=tenant.id,
                is_active=True
            )
            db.add(user2)
            db.flush()
            print(f"  创建提交者用户: {user2.name} (ID: {user2.id})")
        
        # 2. 创建审批小组
        print("\n=== 2. 创建审批小组 ===")
        
        group = db.query(ApprovalGroup).filter(
            ApprovalGroup.name == "测试审批小组",
            ApprovalGroup.tenant_id == tenant.id
        ).first()
        if not group:
            group = ApprovalGroup(
                name="测试审批小组",
                department_id=dept.id,
                tenant_id=tenant.id
            )
            db.add(group)
            db.flush()
            print(f"  创建审批小组: {group.name} (ID: {group.id})")
        
        # 添加小组成员
        member = db.query(ApprovalGroupMember).filter(
            ApprovalGroupMember.group_id == group.id,
            ApprovalGroupMember.user_id == user.id
        ).first()
        if not member:
            member = ApprovalGroupMember(
                group_id=group.id,
                user_id=user.id,
                tenant_id=tenant.id
            )
            db.add(member)
            db.flush()
            print(f"  添加小组成员: {user.name} (ID: {user.id})")
        
        # 3. 创建测试表单
        print("\n=== 3. 创建测试表单 ===")
        
        form1 = db.query(Form).filter(Form.name == "请假申请单").first()
        if not form1:
            form1 = Form(
                name="请假申请单",
                category="人事",
                access_mode="authenticated",
                owner_user_id=user.id,
                status="published",
                allow_edit=False,
                tenant_id=tenant.id
            )
            db.add(form1)
            db.flush()
            print(f"  创建表单: {form1.name} (ID: {form1.id})")
        
        # 创建表单版本
        form_version1 = db.query(FormVersion).filter(
            FormVersion.form_id == form1.id,
            FormVersion.version == 1
        ).first()
        if not form_version1:
            form_version1 = FormVersion(
                form_id=form1.id,
                version=1,
                schema_json={
                    "type": "object",
                    "properties": {
                        "leave_type": {"type": "string", "title": "请假类型"},
                        "start_date": {"type": "string", "title": "开始时间"},
                        "end_date": {"type": "string", "title": "结束时间"},
                        "reason": {"type": "string", "title": "请假原因"}
                    }
                },
                published_at=datetime.now(),
                tenant_id=tenant.id
            )
            db.add(form_version1)
            db.flush()
            print(f"  创建表单版本: v{form_version1.version} (ID: {form_version1.id})")
        
        # 创建第二个表单
        form2 = db.query(Form).filter(Form.name == "费用报销单").first()
        if not form2:
            form2 = Form(
                name="费用报销单",
                category="财务",
                access_mode="authenticated",
                owner_user_id=user.id,
                status="published",
                allow_edit=True,
                max_edit_count=3,
                tenant_id=tenant.id
            )
            db.add(form2)
            db.flush()
            print(f"  创建表单: {form2.name} (ID: {form2.id})")
        
        form_version2 = db.query(FormVersion).filter(
            FormVersion.form_id == form2.id,
            FormVersion.version == 1
        ).first()
        if not form_version2:
            form_version2 = FormVersion(
                form_id=form2.id,
                version=1,
                schema_json={
                    "type": "object",
                    "properties": {
                        "expense_type": {"type": "string", "title": "费用类型"},
                        "amount": {"type": "number", "title": "金额"},
                        "description": {"type": "string", "title": "费用说明"}
                    }
                },
                published_at=datetime.now(),
                tenant_id=tenant.id
            )
            db.add(form_version2)
            db.flush()
            print(f"  创建表单版本: v{form_version2.version} (ID: {form_version2.id})")
        
        # 4. 创建流程定义
        print("\n=== 4. 创建流程定义 ===")
        
        flow_def = db.query(FlowDefinition).filter(
            FlowDefinition.form_id == form1.id,
            FlowDefinition.version == 1
        ).first()
        if not flow_def:
            flow_def = FlowDefinition(
                form_id=form1.id,
                version=1,
                name="请假审批流程",
                tenant_id=tenant.id
            )
            db.add(flow_def)
            db.flush()
            print(f"  创建流程定义: {flow_def.name} (ID: {flow_def.id})")
        
        # 创建流程节点
        start_node = db.query(FlowNode).filter(
            FlowNode.flow_definition_id == flow_def.id,
            FlowNode.type == "start"
        ).first()
        if not start_node:
            start_node = FlowNode(
                flow_definition_id=flow_def.id,
                name="开始",
                type="start",
                tenant_id=tenant.id
            )
            db.add(start_node)
            db.flush()
            print(f"  创建节点: {start_node.name} (ID: {start_node.id})")
        
        # 部门审批节点
        dept_approve_node = db.query(FlowNode).filter(
            FlowNode.flow_definition_id == flow_def.id,
            FlowNode.name == "部门审批"
        ).first()
        if not dept_approve_node:
            dept_approve_node = FlowNode(
                flow_definition_id=flow_def.id,
                name="部门审批",
                type="user",
                assignee_type="group",
                assignee_value=json.dumps({"group_id": group.id}),
                approve_policy="any",
                sla_hours=24,
                allow_delegate=True,
                tenant_id=tenant.id
            )
            db.add(dept_approve_node)
            db.flush()
            print(f"  创建节点: {dept_approve_node.name} (ID: {dept_approve_node.id})")
        
        # 人事审批节点
        hr_approve_node = db.query(FlowNode).filter(
            FlowNode.flow_definition_id == flow_def.id,
            FlowNode.name == "人事审批"
        ).first()
        if not hr_approve_node:
            hr_approve_node = FlowNode(
                flow_definition_id=flow_def.id,
                name="人事审批",
                type="user",
                assignee_type="position",
                assignee_value=json.dumps(["人事主管"]),
                approve_policy="any",
                sla_hours=48,
                tenant_id=tenant.id
            )
            db.add(hr_approve_node)
            db.flush()
            print(f"  创建节点: {hr_approve_node.name} (ID: {hr_approve_node.id})")
        
        # 结束节点
        end_node = db.query(FlowNode).filter(
            FlowNode.flow_definition_id == flow_def.id,
            FlowNode.type == "end"
        ).first()
        if not end_node:
            end_node = FlowNode(
                flow_definition_id=flow_def.id,
                name="结束",
                type="end",
                tenant_id=tenant.id
            )
            db.add(end_node)
            db.flush()
            print(f"  创建节点: {end_node.name} (ID: {end_node.id})")
        
        # 创建流程路由
        route1 = db.query(FlowRoute).filter(
            FlowRoute.from_node_id == start_node.id,
            FlowRoute.to_node_id == dept_approve_node.id
        ).first()
        if not route1:
            route1 = FlowRoute(
                flow_definition_id=flow_def.id,
                from_node_id=start_node.id,
                to_node_id=dept_approve_node.id,
                priority=1,
                is_default=True,
                tenant_id=tenant.id
            )
            db.add(route1)
            db.flush()
            print(f"  创建路由: {start_node.name} -> {dept_approve_node.name}")
        
        route2 = db.query(FlowRoute).filter(
            FlowRoute.from_node_id == dept_approve_node.id,
            FlowRoute.to_node_id == hr_approve_node.id
        ).first()
        if not route2:
            route2 = FlowRoute(
                flow_definition_id=flow_def.id,
                from_node_id=dept_approve_node.id,
                to_node_id=hr_approve_node.id,
                priority=1,
                condition_json={"type": "approve"},
                tenant_id=tenant.id
            )
            db.add(route2)
            db.flush()
            print(f"  创建路由: {dept_approve_node.name} -> {hr_approve_node.name}")
        
        route3 = db.query(FlowRoute).filter(
            FlowRoute.from_node_id == hr_approve_node.id,
            FlowRoute.to_node_id == end_node.id
        ).first()
        if not route3:
            route3 = FlowRoute(
                flow_definition_id=flow_def.id,
                from_node_id=hr_approve_node.id,
                to_node_id=end_node.id,
                priority=1,
                tenant_id=tenant.id
            )
            db.add(route3)
            db.flush()
            print(f"  创建路由: {hr_approve_node.name} -> {end_node.name}")
        
        # 创建流程快照
        snapshot = db.query(FlowSnapshot).filter(
            FlowSnapshot.flow_definition_id == flow_def.id,
            FlowSnapshot.version_tag == "v1"
        ).first()
        if not snapshot:
            snapshot = FlowSnapshot(
                flow_definition_id=flow_def.id,
                version_tag="v1",
                rules_payload={
                    "nodes": [
                        {"id": start_node.id, "type": "start"},
                        {"id": dept_approve_node.id, "type": "user", "assignee": {"type": "group", "value": group.id}},
                        {"id": hr_approve_node.id, "type": "user", "assignee": {"type": "position", "value": ["人事主管"]}},
                        {"id": end_node.id, "type": "end"}
                    ],
                    "routes": [
                        {"from": start_node.id, "to": dept_approve_node.id},
                        {"from": dept_approve_node.id, "to": hr_approve_node.id, "condition": {"type": "approve"}},
                        {"from": hr_approve_node.id, "to": end_node.id}
                    ]
                },
                tenant_id=tenant.id
            )
            db.add(snapshot)
            db.flush()
            print(f"  创建流程快照: {snapshot.version_tag} (ID: {snapshot.id})")
        
        # 更新流程定义的活跃快照
        flow_def.active_snapshot_id = snapshot.id
        
        # 5. 创建流程实例和任务（不同状态）
        print("\n=== 5. 创建不同状态的待办任务 ===")
        
        now = datetime.now()
        
        # 5.1 待办任务（open状态）- 个人待办
        submission1 = Submission(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submitter_user_id=user2.id,
            data_jsonb={
                "leave_type": "年假",
                "start_date": "2024-01-15",
                "end_date": "2024-01-17",
                "reason": "家庭事务"
            },
            status="submitted",
            tenant_id=tenant.id
        )
        db.add(submission1)
        db.flush()
        print(f"  创建提交记录: 请假申请 (ID: {submission1.id})")
        
        process1 = ProcessInstance(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submission_id=submission1.id,
            flow_definition_id=flow_def.id,
            state="running",
            tenant_id=tenant.id
        )
        db.add(process1)
        db.flush()
        print(f"  创建流程实例: 请假审批 (ID: {process1.id})")
        
        task1 = Task(
            process_instance_id=process1.id,
            node_id=dept_approve_node.id,
            assignee_user_id=user.id,
            status="open",
            due_at=now + timedelta(hours=24),
            tenant_id=tenant.id
        )
        db.add(task1)
        print(f"  创建待办任务: 请假审批-部门审批 (open) (ID: {task1.id})")
        
        # 5.2 已认领任务（claimed状态）
        submission2 = Submission(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submitter_user_id=user2.id,
            data_jsonb={
                "leave_type": "病假",
                "start_date": "2024-01-20",
                "end_date": "2024-01-21",
                "reason": "身体不适"
            },
            status="submitted",
            tenant_id=tenant.id
        )
        db.add(submission2)
        db.flush()
        
        process2 = ProcessInstance(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submission_id=submission2.id,
            flow_definition_id=flow_def.id,
            state="running",
            tenant_id=tenant.id
        )
        db.add(process2)
        db.flush()
        
        task2 = Task(
            process_instance_id=process2.id,
            node_id=dept_approve_node.id,
            assignee_user_id=user.id,
            status="claimed",
            due_at=now + timedelta(hours=24),
            claimed_by=user.id,
            claimed_at=now - timedelta(hours=1),
            tenant_id=tenant.id
        )
        db.add(task2)
        print(f"  创建待办任务: 病假审批-部门审批 (claimed) (ID: {task2.id})")
        
        # 5.3 已完成任务（completed状态）
        submission3 = Submission(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submitter_user_id=user2.id,
            data_jsonb={
                "leave_type": "事假",
                "start_date": "2024-01-10",
                "end_date": "2024-01-10",
                "reason": "处理私事"
            },
            status="submitted",
            tenant_id=tenant.id
        )
        db.add(submission3)
        db.flush()
        
        process3 = ProcessInstance(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submission_id=submission3.id,
            flow_definition_id=flow_def.id,
            state="running",
            tenant_id=tenant.id
        )
        db.add(process3)
        db.flush()
        
        task3 = Task(
            process_instance_id=process3.id,
            node_id=dept_approve_node.id,
            assignee_user_id=user.id,
            status="completed",
            action="approve",
            due_at=now - timedelta(days=1),
            completed_by=user.id,
            completed_at=now - timedelta(days=1),
            tenant_id=tenant.id
        )
        db.add(task3)
        
        # 添加操作日志
        action_log = TaskActionLog(
            task_id=task3.id,
            actor_user_id=user.id,
            action="approve",
            detail_json={"comment": "审批通过"},
            tenant_id=tenant.id
        )
        db.add(action_log)
        print(f"  创建待办任务: 事假审批-部门审批 (completed) (ID: {task3.id})")
        
        # 5.4 已取消任务（canceled状态）
        submission4 = Submission(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submitter_user_id=user2.id,
            data_jsonb={
                "leave_type": "调休",
                "start_date": "2024-01-25",
                "end_date": "2024-01-26",
                "reason": "调休申请"
            },
            status="submitted",
            tenant_id=tenant.id
        )
        db.add(submission4)
        db.flush()
        
        process4 = ProcessInstance(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submission_id=submission4.id,
            flow_definition_id=flow_def.id,
            state="canceled",
            tenant_id=tenant.id
        )
        db.add(process4)
        db.flush()
        
        task4 = Task(
            process_instance_id=process4.id,
            node_id=dept_approve_node.id,
            assignee_user_id=user.id,
            status="canceled",
            due_at=now + timedelta(hours=24),
            tenant_id=tenant.id
        )
        db.add(task4)
        print(f"  创建待办任务: 调休审批-部门审批 (canceled) (ID: {task4.id})")
        
        # 6. 小组待办池子
        print("\n=== 6. 创建小组待办池子任务 ===")
        
        submission5 = Submission(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submitter_user_id=user2.id,
            data_jsonb={
                "leave_type": "婚假",
                "start_date": "2024-02-01",
                "end_date": "2024-02-07",
                "reason": "结婚休假"
            },
            status="submitted",
            tenant_id=tenant.id
        )
        db.add(submission5)
        db.flush()
        
        process5 = ProcessInstance(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submission_id=submission5.id,
            flow_definition_id=flow_def.id,
            state="running",
            tenant_id=tenant.id
        )
        db.add(process5)
        db.flush()
        
        task5 = Task(
            process_instance_id=process5.id,
            node_id=dept_approve_node.id,
            assignee_group_id=group.id,
            status="open",
            due_at=now + timedelta(hours=24),
            tenant_id=tenant.id
        )
        db.add(task5)
        print(f"  创建小组待办: 婚假审批-部门审批 (group: {group.name}) (ID: {task5.id})")
        
        # 第二个小组待办
        submission6 = Submission(
            form_id=form2.id,
            form_version_id=form_version2.id,
            submitter_user_id=user2.id,
            data_jsonb={
                "expense_type": "办公用品",
                "amount": 500.00,
                "description": "购买办公文具"
            },
            status="submitted",
            tenant_id=tenant.id
        )
        db.add(submission6)
        db.flush()
        
        process6 = ProcessInstance(
            form_id=form2.id,
            form_version_id=form_version2.id,
            submission_id=submission6.id,
            flow_definition_id=flow_def.id,
            state="running",
            tenant_id=tenant.id
        )
        db.add(process6)
        db.flush()
        
        task6 = Task(
            process_instance_id=process6.id,
            node_id=dept_approve_node.id,
            assignee_group_id=group.id,
            status="open",
            due_at=now + timedelta(hours=48),
            tenant_id=tenant.id
        )
        db.add(task6)
        print(f"  创建小组待办: 费用报销-部门审批 (group: {group.name}) (ID: {task6.id})")
        
        # 7. 已提交表单（用于观察功能）
        print("\n=== 7. 创建已提交的表单 ===")
        
        # 提交者提交的表单
        submission7 = Submission(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submitter_user_id=user2.id,
            data_jsonb={
                "leave_type": "年假",
                "start_date": "2024-02-10",
                "end_date": "2024-02-12",
                "reason": "春节假期"
            },
            status="submitted",
            duration=120,
            source="pc",
            ip_address="192.168.1.100",
            tenant_id=tenant.id
        )
        db.add(submission7)
        db.flush()
        print(f"  创建已提交表单: 春节请假 (ID: {submission7.id})")
        
        submission8 = Submission(
            form_id=form2.id,
            form_version_id=form_version2.id,
            submitter_user_id=user2.id,
            data_jsonb={
                "expense_type": "差旅费",
                "amount": 3500.00,
                "description": "北京出差费用"
            },
            status="submitted",
            duration=180,
            source="mobile",
            ip_address="192.168.1.101",
            tenant_id=tenant.id
        )
        db.add(submission8)
        db.flush()
        print(f"  创建已提交表单: 差旅报销 (ID: {submission8.id})")
        
        # 草稿状态的表单
        submission9 = Submission(
            form_id=form1.id,
            form_version_id=form_version1.id,
            submitter_user_id=user2.id,
            data_jsonb={
                "leave_type": "事假",
                "start_date": "2024-02-15",
                "end_date": "2024-02-15",
                "reason": "待补充"
            },
            status="draft",
            tenant_id=tenant.id
        )
        db.add(submission9)
        db.flush()
        print(f"  创建草稿表单: 事假申请 (ID: {submission9.id})")
        
        # 提交变更
        db.commit()
        
        print("\n=== 测试数据生成完成 ===")
        print(f"用户ID: {user.id} ({user.name})")
        print(f"小组ID: {group.id} ({group.name})")
        print(f"表单ID: {form1.id} ({form1.name}), {form2.id} ({form2.name})")
        
    except Exception as e:
        db.rollback()
        print(f"生成测试数据时出错: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    generate_test_data()