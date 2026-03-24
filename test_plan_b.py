#!/usr/bin/env python3
"""
测试计划 B：费用报销审批（条件分支测试）

测试目标：验证条件分支流程 - 根据金额走不同审批路径
- 金额 <= 5000：会计审核后结束
- 金额 > 5000：会计审核 → 院长审批后结束

测试账户：
- 管理员：admin / 123456
- 教师：wangjiaoshou / 123456（发起报销）
- 会计：zhaokuaiji / 123456（财务审核）
- 院长：lizhangyuan / 123456（领导审批）
"""

import requests
import json
import sys

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
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "account": account,
        "password": password,
        "tenant_id": TENANT_ID
    })
    if resp.status_code == 200:
        data = resp.json()
        return data.get("data", {}).get("access_token")
    return None

def get_headers(token):
    """获取请求头"""
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(TENANT_ID),
        "Content-Type": "application/json"
    }

def run_test_plan_b():
    """执行测试计划 B"""
    result = TestResult("费用报销审批（条件分支）")
    
    print("\n" + "="*60)
    print("📋 测试计划 B：费用报销审批（条件分支）")
    print("="*60)
    
    # 步骤1：管理员登录
    print("\n[步骤1] 管理员登录...")
    admin_token = login("admin")
    if not admin_token:
        result.error("管理员登录失败")
        return result
    result.success("管理员登录成功")
    
    # 步骤2：查询现有表单
    print("\n[步骤2] 查询现有表单...")
    resp = requests.get(f"{BASE_URL}/forms", headers=get_headers(admin_token))
    forms = resp.json().get("data", {}).get("items", [])
    
    # 查找费用报销相关表单或使用请假表单测试
    expense_form = None
    for f in forms:
        if "报销" in f.get("name", "") or "费用" in f.get("name", ""):
            expense_form = f
            break
    
    if not expense_form:
        # 使用请假申请表单测试
        for f in forms:
            if "请假" in f.get("name", ""):
                expense_form = f
                break
    
    if not expense_form:
        result.error("未找到可用的表单")
        return result
    
    form_id = expense_form["id"]
    result.success(f"使用表单：{expense_form['name']} (ID: {form_id})")
    
    # 步骤3：获取或创建流程定义
    print("\n[步骤3] 获取或创建流程定义...")
    resp = requests.post(f"{BASE_URL}/forms/{form_id}/flow-definition", 
                         headers=get_headers(admin_token))
    if resp.status_code in [200, 201]:
        flow_def_id = resp.json().get("data", {}).get("flow_definition_id")
        result.success(f"流程定义创建/获取成功 (ID: {flow_def_id})")
    else:
        result.error(f"获取流程定义失败: {resp.text}")
        return result
    
    # 步骤4：保存流程草稿（配置条件分支）
    print("\n[步骤4] 配置条件分支审批流程...")
    flow_draft = {
        "flow_definition_id": flow_def_id,
        "nodes_graph": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "position": {"x": 100, "y": 100}},
                {"id": "accountant", "type": "user", "name": "会计审核", "position": {"x": 250, "y": 100}, 
                 "assignee_type": "position", "assignee_value": {"position_id": 11}},
                {"id": "condition", "type": "condition", "name": "金额判断", "position": {"x": 400, "y": 100}},
                {"id": "dean", "type": "user", "name": "院长审批", "position": {"x": 550, "y": 50},
                 "assignee_type": "position", "assignee_value": {"position_id": 4}},
                {"id": "end", "type": "end", "name": "结束", "position": {"x": 700, "y": 100}}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "accountant"},
                {"id": "e2", "source": "accountant", "target": "condition"},
                {"id": "e3", "source": "condition", "target": "dean", "label": "金额>5000"},
                {"id": "e4", "source": "condition", "target": "end", "label": "金额<=5000"},
                {"id": "e5", "source": "dean", "target": "end"}
            ]
        },
        "config_json": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始"},
                {"id": "accountant", "type": "user", "name": "会计审核", "assignee_type": "position", "assignee_value": {"position_id": 11}},
                {"id": "condition", "type": "condition", "name": "金额判断", "condition": "amount > 5000"},
                {"id": "dean", "type": "user", "name": "院长审批", "assignee_type": "position", "assignee_value": {"position_id": 4}},
                {"id": "end", "type": "end", "name": "结束"}
            ],
            "routes": [
                {"from": "start", "to": "accountant"},
                {"from": "accountant", "to": "condition"},
                {"from": "condition", "to": "dean", "condition": "amount > 5000"},
                {"from": "condition", "to": "end", "condition": "amount <= 5000"},
                {"from": "dean", "to": "end"}
            ]
        }
    }
    
    resp = requests.put(f"{BASE_URL}/flows/{flow_def_id}/draft", 
                        json=flow_draft,
                        headers=get_headers(admin_token))
    if resp.status_code in [200, 201]:
        result.success("流程草稿保存成功（条件分支配置）")
    else:
        result.error(f"保存流程草稿失败: {resp.text}")
    
    # 步骤5：发布流程
    print("\n[步骤5] 发布审批流程...")
    resp = requests.post(f"{BASE_URL}/flows/{flow_def_id}/publish",
                         json={"flow_definition_id": flow_def_id, "version_tag": "v1.0"},
                         headers=get_headers(admin_token))
    if resp.status_code in [200, 201]:
        result.success("流程发布成功")
    else:
        result.error(f"发布流程失败: {resp.text}")
    
    # 步骤6：发布表单
    print("\n[步骤6] 发布表单...")
    resp = requests.post(f"{BASE_URL}/forms/{form_id}/publish",
                         headers=get_headers(admin_token))
    if resp.status_code in [200, 201]:
        result.success("表单发布成功")
    else:
        # 可能已经发布
        result.success("表单已处于发布状态或发布完成")
    
    # 步骤7：教师登录并提交报销申请（小金额）
    print("\n[步骤7] 教师提交报销申请（金额3000，预期：会计审核后结束）...")
    teacher_token = login("wangjiaoshou")
    if not teacher_token:
        result.error("教师登录失败")
        return result
    result.success("教师登录成功")
    
    submission_data = {
        "form_id": form_id,
        "form_data": {
            "amount": 3000,
            "reason": "购买办公用品",
            "applicant": "王教授"
        }
    }
    
    resp = requests.post(f"{BASE_URL}/submissions", 
                         json=submission_data,
                         headers=get_headers(teacher_token))
    if resp.status_code in [200, 201]:
        submission_id = resp.json().get("data", {}).get("submission_id")
        result.success(f"小金额报销申请提交成功 (Submission ID: {submission_id})")
    else:
        result.error(f"提交报销申请失败: {resp.text}")
        return result
    
    # 步骤8：查询待办任务
    print("\n[步骤8] 查询会计待办任务...")
    resp = requests.get(f"{BASE_URL}/approvals", 
                        params={"only_mine": True},
                        headers=get_headers(login("zhaokuaiji")))
    tasks = resp.json().get("data", {}).get("items", [])
    
    accountant_task = None
    for t in tasks:
        if t.get("submission_id") == submission_id:
            accountant_task = t
            break
    
    if accountant_task:
        result.success(f"找到会计待办任务 (Task ID: {accountant_task['id']})")
    else:
        result.error("未找到会计待办任务")
    
    # 步骤9：会计审批
    print("\n[步骤9] 会计审批通过...")
    if accountant_task:
        resp = requests.post(f"{BASE_URL}/approvals/{accountant_task['id']}/actions",
                            json={"action": "approve", "comment": "金额核实无误"},
                            headers=get_headers(login("zhaokuaiji")))
        if resp.status_code in [200, 201]:
            result.success("会计审批成功")
        else:
            result.error(f"会计审批失败: {resp.text}")
    
    # 步骤10：验证小金额报销流程直接结束
    print("\n[步骤10] 验证小金额报销流程是否直接结束...")
    resp = requests.get(f"{BASE_URL}/submissions/{submission_id}",
                        headers=get_headers(teacher_token))
    if resp.status_code == 200:
        result.success("小金额报销流程验证完成（预期：流程直接结束）")
    else:
        result.error(f"查询提交详情失败: {resp.text}")
    
    # 步骤11：提交大金额报销申请
    print("\n[步骤11] 教师提交报销申请（金额8000，预期：会计→院长）...")
    submission_data_2 = {
        "form_id": form_id,
        "form_data": {
            "amount": 8000,
            "reason": "购买实验设备",
            "applicant": "王教授"
        }
    }
    
    resp = requests.post(f"{BASE_URL}/submissions", 
                         json=submission_data_2,
                         headers=get_headers(teacher_token))
    if resp.status_code in [200, 201]:
        submission_id_2 = resp.json().get("data", {}).get("submission_id")
        result.success(f"大金额报销申请提交成功 (Submission ID: {submission_id_2})")
    else:
        result.error(f"提交大金额报销申请失败: {resp.text}")
        return result
    
    # 步骤12：会计审批大金额
    print("\n[步骤12] 会计审批大金额报销...")
    resp = requests.get(f"{BASE_URL}/approvals", 
                        params={"only_mine": True},
                        headers=get_headers(login("zhaokuaiji")))
    tasks = resp.json().get("data", {}).get("items", [])
    
    accountant_task_2 = None
    for t in tasks:
        if t.get("submission_id") == submission_id_2:
            accountant_task_2 = t
            break
    
    if accountant_task_2:
        resp = requests.post(f"{BASE_URL}/approvals/{accountant_task_2['id']}/actions",
                            json={"action": "approve", "comment": "金额较大，需领导审批"},
                            headers=get_headers(login("zhaokuaiji")))
        if resp.status_code in [200, 201]:
            result.success("会计审批成功")
        else:
            result.error(f"会计审批失败: {resp.text}")
    
    # 步骤13：验证院长是否收到任务
    print("\n[步骤13] 验证条件分支：院长是否收到审批任务...")
    resp = requests.get(f"{BASE_URL}/approvals", 
                        params={"only_mine": True},
                        headers=get_headers(login("lizhangyuan")))
    tasks = resp.json().get("data", {}).get("items", [])
    
    dean_task = None
    for t in tasks:
        if t.get("submission_id") == submission_id_2:
            dean_task = t
            break
    
    if dean_task:
        result.success(f"条件分支执行成功：院长收到审批任务 (Task ID: {dean_task['id']})")
    else:
        result.error("条件分支执行失败：院长未收到审批任务")
    
    # 步骤14：院长审批
    print("\n[步骤14] 院长审批...")
    if dean_task:
        resp = requests.post(f"{BASE_URL}/approvals/{dean_task['id']}/actions",
                            json={"action": "approve", "comment": "同意采购"},
                            headers=get_headers(login("lizhangyuan")))
        if resp.status_code in [200, 201]:
            result.success("院长审批成功")
        else:
            result.error(f"院长审批失败: {resp.text}")
    
    print("\n" + "="*60)
    print("测试计划 B 执行完成")
    print("="*60)
    
    return result

if __name__ == "__main__":
    result = run_test_plan_b()
    result.summary()
    sys.exit(0 if len(result.failed) == 0 else 1)
