#!/usr/bin/env python3
"""
测试修复后的流程启动逻辑
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.process_service import ProcessService
from app.models.form import Submission

def test_start_process():
    """测试流程启动"""
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("测试修复后的流程启动逻辑")
        print("=" * 80)
        
        # 获取最近的提交记录
        submission = db.query(Submission).filter(
            Submission.form_id == 57  # 学生请假申请表（测试A）
        ).order_by(Submission.created_at.desc()).first()
        
        if not submission:
            print("没有找到提交记录")
            return
        
        print(f"\n提交记录:")
        print(f"  - 提交ID: {submission.id}")
        print(f"  - 表单ID: {submission.form_id}")
        print(f"  - 提交人ID: {submission.submitter_user_id}")
        print(f"  - 租户ID: {submission.tenant_id}")
        
        # 测试启动流程
        print(f"\n测试启动流程...")
        
        try:
            process = ProcessService.start_process(
                form_id=submission.form_id,
                form_version_id=submission.form_version_id,
                submission_id=submission.id,
                tenant_id=submission.tenant_id,
                db=db,
            )
            
            print(f"流程启动成功!")
            print(f"  - 流程实例ID: {process.id}")
            print(f"  - 流程状态: {process.state}")
            print(f"  - 流程定义ID: {process.flow_definition_id}")
            
            # 查询创建的任务
            from app.models.workflow import Task
            tasks = db.query(Task).filter(
                Task.process_instance_id == process.id
            ).all()
            
            print(f"\n创建的任务:")
            for task in tasks:
                print(f"  - 任务ID: {task.id}")
                print(f"  - 节点ID: {task.node_id}")
                print(f"  - 指派用户ID: {task.assignee_user_id}")
                print(f"  - 指派小组ID: {task.assignee_group_id}")
                print(f"  - 任务状态: {task.status}")
            
            # 提交事务
            db.commit()
            
        except Exception as e:
            print(f"流程启动失败: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    test_start_process()
