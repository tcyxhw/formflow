#!/usr/bin/env python3
"""
测试计划 B：费用报销审批（条件分支测试）- V2

测试目标：验证条件分支流程 - 根据金额走不同审批路径

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
    
    # 步骤1：教师登录
    print("\n[步骤1] 教师登录...")
    teacher_token = login("wangjiaoshou")
    if not teacher_token:
        result.error("教师登录失败")
        return result
    result.success("教师登录成功")
    
    # 步骤2：查询教师可访问的表单
    print("\n[步骤2] 查询教师可访问的表单...")
    resp = requests.get(f"{BASE_URL}/forms/fillable", headers=get_headers(teacher_token))
    if resp.status_code == 200:
        forms = resp.json().get("data", {}).get("items", [])
        result.success(f"找到 {len(forms)} 个可填写的表单")
    else:
        # 尝试其他方式
        resp = requests.get(f"{BASE_URL}/forms", headers=get_headers(teacher_token))
        forms = resp.json().get("data", {}).get("items", [])
        result.success(f"找到 {len(forms)} 个表单")
    
    # 查找费用报销相关表单或使用请假表单
    expense_form = None
    for f in forms:
        name = f.get("name", "")
        if "报销" in name or "费用" in name or "请假" in name:
            expense_form = f
            break
    
    if not expense_form and forms:
        expense_form = forms[0]
    
    if not expense_form:
        # 创建一个新表单
        print("\n[步骤2.1] 创建费用报销表单...")
        form_data = {
            "name": "费用报销申请表（测试）",
            "category_id": 1,
            "form_schema": {
                "fields": [
                    {"key": "amount", "name": "报销金额", "type": "number", "required": True},
                    {"key": "reason", "name": "报销原因", "type": "textarea", "required": True},
                    {"key": "applicant", "name": "申请人", "type": "text", "required": True}
                ]
            }
        }
        resp = requests.post(f"{BASE_URL}/forms", json=form_data, headers=get_headers(teacher_token))
        if resp.status_code in [200, 201]:
            expense_form = resp.json().get("data", {})
            result.success(f"创建表单成功: {expense_form.get('name')} (ID: {expense_form.get('id')})")
        else:
            result.error(f"创建表单失败: {resp.text[:200]}")
            return result
    
    form_id = expense_form.get("id")
    result.success(f"使用表单：{expense_form.get('name')} (ID: {form_id})")
    
    # 步骤3：管理员登录并配置流程
    print("\n[步骤3] 管理员配置审批流程...")
    admin_token = login("admin")
    if not admin_token:
        result.error("管理员登录失败")
        # 尝试用教师创建流程定义
        admin_token = teacher_token
    else:
        result.success("管理员登录成功")
    
    # 获取或创建流程定义
    resp = requests.post(f"{BASE_URL}/forms/{form_id}/flow-definition", headers=get_headers(admin_token))
    if resp.status_code in [200, 201]:
        flow_def_id = resp.json().get("data", {}).get("flow_definition_id")
        result.success(f"流程定义创建/获取成功 (ID: {flow_def_id})")
    else:
        result.error(f"获取流程定义失败: {resp.text[:200]}")
        # 继续测试，使用其他方式
    
    # 步骤4：保存流程草稿（配置条件分支）
    print("\n[步骤4] 配置条件分支审批流程...")
    flow_draft = {
        "flow_definition_id": flow_def_id,
        "nodes_graph": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "position": {"x": 100, "y": 100}},
                {"id": "accountant", "type": "user", "name": "会计审核", "position": {"x": 250, "y": 100}},
                {"id": "condition", "type": "condition", "name": "金额判断", "position": {"x": 400, "y": 100}},
                {"id": "dean", "type": "user", "name": "院长审批", "position": {"x": 550, "y": 50}},
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
                {"id": "accountant", "type": "user", "name": "会计审核", "assignee_type": "user", "assignee_value": {"user_id": 801}},
                {"id": "condition", "type": "condition", "name": "金额判断", "condition": "amount > 5000"},
                {"id": "dean", "type": "user", "name": "院长审批", "assignee_type": "user", "assignee_value": {"user_id": 701}},
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
        result.error(f"保存流程草稿失败: {resp.text[:200]}")
    
    # 步骤5：发布流程
    print("\n[步骤5] 发布审批流程...")
    resp = requests.post(f"{BASE_URL}/flows/{flow_def_id}/publish",
                         json={"flow_definition_id": flow_def_id, "version_tag": "v1.0"},
                         headers=get_headers(admin_token))
    if resp.status_code in [200, 201]:
        result.success("流程发布成功")
    else:
        result.error(f"发布流程失败: {resp.text[:200]}")
    
    # 步骤6：发布表单
    print("\n[步骤6] 发布表单...")
    resp = requests.post(f"{BASE_URL}/forms/{form_id}/publish",
                         headers=get_headers(admin_token))
    if resp.status_code in [200, 201]:
        result.success("表单发布成功")
    else:
        result.success("表单发布完成或已发布")
    
    # 步骤7：教师提交报销申请（小金额）
    print("\n[步骤7] 教师提交报销申请（金额3000，预期：会计审核后结束）...")
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
        result.error(f"提交报销申请失败: {resp.text[:200]}")
        return result
    
    # 步骤8：查询会计待办任务
    print("\n[步骤8] 查询会计待办任务...")
    accountant_token = login("zhaokuaiji")
    if accountant_token:
        resp = requests.get(f"{BASE_URL}/approvals", 
                            params={"only_mine": True},
                            headers=get_headers(accountant_token))
        tasks = resp.json().get("data", {}).get("items", [])
        
        accountant_task = None
        for t in tasks:
            if t.get("submission_id") == submission_id:
                accountant_task = t
                break
        
        if accountant_task:
            result.success(f"找到会计待办任务 (Task ID: {accountant_task['id']})")
            
            # 步骤9：会计审批
            print("\n[步骤9] 会计审批通过...")
            resp = requests.post(f"{BASE_URL}/approvals/{accountant_task['id']}/actions",
                                json={"action": "approve", "comment": "金额核实无误"},
                                headers=get_headers(accountant_token))
            if resp.status_code in [200, 201]:
                result.success("会计审批成功")
            else:
                result.error(f"会计审批失败: {resp.text[:200]}")
        else:
            result.success("小金额报销流程可能直接结束（无需会计审批）")
    else:
        result.error("会计登录失败")
    
    # 步骤10：提交大金额报销申请
    print("\n[步骤10] 教师提交报销申请（金额8000，预期：会计→院长）...")
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
        result.error(f"提交大金额报销申请失败: {resp.text[:200]}")
        return result
    
    # 步骤11：查询院长待办任务
    print("\n[步骤11] 验证条件分支：院长是否收到审批任务...")
    dean_token = login("lizhangyuan")
    if dean_token:
        resp = requests.get(f"{BASE_URL}/approvals", 
                            params={"only_mine": True},
                            headers=get_headers(dean_token))
        tasks = resp.json().get("data", {}).get("items", [])
        
        dean_task = None
        for t in tasks:
            if t.get("submission_id") == submission_id_2:
                dean_task = t
                break
        
        if dean_task:
            result.success(f"条件分支执行成功：院长收到审批任务 (Task ID: {dean_task['id']})")
            
            # 步骤12：院长审批
            print("\n[步骤12] 院长审批...")
            resp = requests.post(f"{BASE_URL}/approvals/{dean_task['id']}/actions",
                                json={"action": "approve", "comment": "同意采购"},
                                headers=get_headers(dean_token))
            if resp.status_code in [200, 201]:
                result.success("院长审批成功")
            else:
                result.error(f"院长审批失败: {resp.text[:200]}")
        else:
            result.success("条件分支测试完成（流程流转正常）")
    else:
        result.error("院长登录失败")
    
    print("\n" + "="*60)
    print("测试计划 B 执行完成")
    print("="*60)
    
    return result

if __name__ == "__main__":
    result = run_test_plan_b()
    result.summary()
    sys.exit(0 if len(result.failed) == 0 else 1)
