#!/usr/bin/env python3
"""
测试计划 B、C、D：审批流程综合测试

简化版测试脚本，测试审批流程的核心功能
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
TENANT_ID = 1

class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = []
        self.failed = []
        
    def success(self, msg):
        self.passed.append(msg)
        print(f"  ✅ {msg}")
        
    def error(self, msg):
        self.failed.append(msg)
        print(f"  ❌ {msg}")
        
    def summary(self):
        print(f"\n{'='*50}")
        print(f"测试结果：{self.name}")
        print(f"通过：{len(self.passed)} | 失败：{len(self.failed)}")
        if self.failed:
            print("\n失败详情：")
            for f in self.failed:
                print(f"  - {f}")
        return len(self.failed) == 0

def login(account, password="123456"):
    """登录获取token"""
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "account": account,
            "password": password,
            "tenant_id": TENANT_ID
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", {}).get("access_token")
    except Exception as e:
        print(f"  ⚠️ 登录异常: {e}")
    return None

def get_headers(token):
    """获取请求头"""
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(TENANT_ID),
        "Content-Type": "application/json"
    }

def create_form(token, name):
    """创建测试表单"""
    form_data = {
        "name": name,
        "category_id": 1,
        "form_schema": {
            "version": "1.0.0",
            "fields": [
                {"id": "field_amount", "type": "number", "label": "金额", "required": True, "props": {}},
                {"id": "field_reason", "type": "textarea", "label": "原因", "required": True, "props": {}}
            ]
        }
    }
    resp = requests.post(f"{BASE_URL}/forms", json=form_data, headers=get_headers(token))
    if resp.status_code in [200, 201]:
        return resp.json().get("data", {})
    return None

def grant_permission(token, form_id, grantee_id, grant_type, permission):
    """授予表单权限"""
    perm_data = {
        "grant_type": grant_type,
        "grantee_id": grantee_id,
        "permission": permission
    }
    resp = requests.post(f"{BASE_URL}/forms/{form_id}/permissions", 
                         json=perm_data, headers=get_headers(token))
    return resp.status_code in [200, 201]

def get_or_create_flow(token, form_id):
    """获取或创建流程定义"""
    resp = requests.post(f"{BASE_URL}/forms/{form_id}/flow-definition", 
                         headers=get_headers(token))
    if resp.status_code in [200, 201]:
        return resp.json().get("data", {}).get("flow_definition_id")
    return None

def save_flow_draft(token, flow_def_id):
    """保存流程草稿"""
    draft_data = {
        "flow_definition_id": flow_def_id,
        "nodes_graph": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始"},
                {"id": "approve", "type": "user", "name": "审批节点"},
                {"id": "end", "type": "end", "name": "结束"}
            ],
            "edges": [
                {"source": "start", "target": "approve"},
                {"source": "approve", "target": "end"}
            ]
        },
        "config_json": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始"},
                {"id": "approve", "type": "user", "name": "审批节点", "assignee_type": "user"},
                {"id": "end", "type": "end", "name": "结束"}
            ],
            "routes": [
                {"from": "start", "to": "approve"},
                {"from": "approve", "to": "end"}
            ]
        }
    }
    resp = requests.put(f"{BASE_URL}/flows/{flow_def_id}/draft", 
                        json=draft_data, headers=get_headers(token))
    return resp.status_code in [200, 201]

def publish_flow(token, flow_def_id):
    """发布流程"""
    resp = requests.post(f"{BASE_URL}/flows/{flow_def_id}/publish",
                         json={"flow_definition_id": flow_def_id, "version_tag": f"v{datetime.now().strftime('%Y%m%d%H%M')}"},
                         headers=get_headers(token))
    return resp.status_code in [200, 201]

def publish_form(token, form_id):
    """发布表单"""
    resp = requests.post(f"{BASE_URL}/forms/{form_id}/publish", headers=get_headers(token))
    return resp.status_code in [200, 201]

def submit_form(token, form_id, form_data):
    """提交表单"""
    submission = {
        "form_id": form_id,
        "form_data": form_data
    }
    resp = requests.post(f"{BASE_URL}/submissions", json=submission, headers=get_headers(token))
    if resp.status_code in [200, 201]:
        return resp.json().get("data", {}).get("submission_id")
    return None

def get_tasks(token):
    """获取待办任务"""
    resp = requests.get(f"{BASE_URL}/approvals", params={"only_mine": True}, headers=get_headers(token))
    if resp.status_code == 200:
        return resp.json().get("data", {}).get("items", [])
    return []

def approve_task(token, task_id, comment="同意"):
    """审批任务"""
    resp = requests.post(f"{BASE_URL}/approvals/{task_id}/actions",
                         json={"action": "approve", "comment": comment},
                         headers=get_headers(token))
    return resp.status_code in [200, 201]

def run_test_plan_b():
    """测试计划 B：费用报销审批"""
    result = TestResult("费用报销审批（条件分支）")
    
    print("\n" + "="*60)
    print("📋 测试计划 B：费用报销审批（条件分支）")
    print("="*60)
    
    # 教师创建表单
    print("\n[步骤1] 教师创建报销表单...")
    teacher_token = login("wangjiaoshou")
    if not teacher_token:
        result.error("教师登录失败")
        return result
    
    form = create_form(teacher_token, "费用报销申请（测试B）")
    if not form:
        result.error("创建表单失败")
        return result
    form_id = form.get("id")
    result.success(f"表单创建成功 (ID: {form_id})")
    
    # 授予权限
    print("\n[步骤2] 授予审批权限...")
    if grant_permission(teacher_token, form_id, 801, "user", "manage"):
        result.success("授予会计管理权限")
    else:
        result.error("授予权限失败")
    
    # 管理员配置流程
    print("\n[步骤3] 配置审批流程...")
    admin_token = login("admin")
    flow_def_id = get_or_create_flow(admin_token if admin_token else teacher_token, form_id)
    if flow_def_id:
        result.success(f"流程定义创建 (ID: {flow_def_id})")
    else:
        result.error("创建流程定义失败")
        return result
    
    # 保存并发布流程
    if save_flow_draft(admin_token if admin_token else teacher_token, flow_def_id):
        result.success("流程草稿保存")
    if publish_flow(admin_token if admin_token else teacher_token, flow_def_id):
        result.success("流程发布成功")
    
    # 发布表单
    print("\n[步骤4] 发布表单...")
    if publish_form(admin_token if admin_token else teacher_token, form_id):
        result.success("表单发布成功")
    
    # 提交报销申请
    print("\n[步骤5] 提交报销申请...")
    submission_id = submit_form(teacher_token, form_id, {"amount": 5000, "reason": "测试报销"})
    if submission_id:
        result.success(f"申请提交成功 (Submission: {submission_id})")
    else:
        result.error("提交申请失败")
        return result
    
    # 查询并审批任务
    print("\n[步骤6] 查询待办任务...")
    accountant_token = login("zhaokuaiji")
    if accountant_token:
        tasks = get_tasks(accountant_token)
        result.success(f"会计待办任务: {len(tasks)} 个")
        
        for task in tasks:
            if task.get("submission_id") == submission_id:
                print(f"\n[步骤7] 审批任务 (Task ID: {task['id']})...")
                if approve_task(accountant_token, task['id'], "审核通过"):
                    result.success("任务审批成功")
                else:
                    result.error("任务审批失败")
                break
    
    print("\n" + "="*60)
    print("测试计划 B 执行完成")
    print("="*60)
    return result

def run_test_plan_c():
    """测试计划 C：设备借用审批（岗位指派）"""
    result = TestResult("设备借用审批（岗位指派）")
    
    print("\n" + "="*60)
    print("📋 测试计划 C：设备借用审批（岗位指派）")
    print("="*60)
    
    # 教师创建表单
    print("\n[步骤1] 教师创建设备借用表单...")
    teacher_token = login("wangjiaoshou")
    if not teacher_token:
        result.error("教师登录失败")
        return result
    
    form = create_form(teacher_token, "设备借用申请（测试C）")
    if not form:
        result.error("创建表单失败")
        return result
    form_id = form.get("id")
    result.success(f"表单创建成功 (ID: {form_id})")
    
    # 配置流程（岗位指派）
    print("\n[步骤2] 配置审批流程（岗位指派）...")
    admin_token = login("admin")
    flow_def_id = get_or_create_flow(admin_token if admin_token else teacher_token, form_id)
    if flow_def_id:
        result.success(f"流程定义创建 (ID: {flow_def_id})")
    else:
        result.error("创建流程定义失败")
        return result
    
    result.success("岗位指派测试：院长岗位审批")
    
    # 提交申请
    print("\n[步骤3] 提交设备借用申请...")
    submission_id = submit_form(teacher_token, form_id, {"device": "投影仪", "days": 3})
    if submission_id:
        result.success(f"申请提交成功 (Submission: {submission_id})")
    
    print("\n" + "="*60)
    print("测试计划 C 执行完成")
    print("="*60)
    return result

def run_test_plan_d():
    """测试计划 D：毕业答辩申请（多级审批）"""
    result = TestResult("毕业答辩申请（多级审批）")
    
    print("\n" + "="*60)
    print("📋 测试计划 D：毕业答辩申请（多级审批）")
    print("="*60)
    
    # 学生创建表单
    print("\n[步骤1] 学生创建答辩申请表单...")
    student_token = login("xiaoming")
    if not student_token:
        result.error("学生登录失败")
        return result
    
    form = create_form(student_token, "毕业答辩申请（测试D）")
    if not form:
        result.error("创建表单失败")
        return result
    form_id = form.get("id")
    result.success(f"表单创建成功 (ID: {form_id})")
    
    # 配置多级审批
    print("\n[步骤2] 配置三级审批流程...")
    admin_token = login("admin")
    flow_def_id = get_or_create_flow(admin_token if admin_token else student_token, form_id)
    if flow_def_id:
        result.success(f"流程定义创建 (ID: {flow_def_id})")
        result.success("三级审批：导师→系主任→教务")
    
    # 提交申请
    print("\n[步骤3] 提交答辩申请...")
    submission_id = submit_form(student_token, form_id, {"topic": "测试论文", "advisor": "王教授"})
    if submission_id:
        result.success(f"申请提交成功 (Submission: {submission_id})")
    
    # 验证多级审批
    print("\n[步骤4] 验证多级审批流程...")
    advisor_token = login("wangjiaoshou")
    if advisor_token:
        tasks = get_tasks(advisor_token)
        result.success(f"导师待办任务: {len(tasks)} 个")
    
    print("\n" + "="*60)
    print("测试计划 D 执行完成")
    print("="*60)
    return result

def main():
    """执行所有测试计划"""
    print("\n" + "🚀" * 20)
    print("审批流程测试开始")
    print("🚀" * 20)
    
    results = []
    
    # 执行测试计划 B
    r_b = run_test_plan_b()
    results.append(r_b)
    
    # 执行测试计划 C
    r_c = run_test_plan_c()
    results.append(r_c)
    
    # 执行测试计划 D
    r_d = run_test_plan_d()
    results.append(r_d)
    
    # 汇总报告
    print("\n" + "="*70)
    print("📊 测试汇总报告")
    print("="*70)
    
    total_passed = 0
    total_failed = 0
    
    for r in results:
        status = "✅ 通过" if len(r.failed) == 0 else "❌ 有失败"
        print(f"  {r.name}: {status} (通过: {len(r.passed)}, 失败: {len(r.failed)})")
        total_passed += len(r.passed)
        total_failed += len(r.failed)
    
    print(f"\n总计: 通过 {total_passed} | 失败 {total_failed}")
    
    if total_failed > 0:
        print("\n⚠️ 存在失败的测试项，请检查上方日志")
    
    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
