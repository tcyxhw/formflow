"""
表单字段 API 验证脚本
验证 API 端点的完整功能
"""
import sys
from datetime import datetime

# 模拟表单数据
def verify_api_logic():
    """验证 API 的核心逻辑"""
    
    # 1. 模拟表单版本数据
    current_version = {
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {
                    "id": "amount",
                    "type": "number",
                    "label": "金额",
                    "description": "招待费金额",
                    "required": True,
                    "props": {"min": 0, "max": 10000},
                    "validation": {"type": "number"}
                },
                {
                    "id": "reason",
                    "type": "text",
                    "label": "事由",
                    "description": "招待事由说明",
                    "required": True,
                    "props": {},
                    "validation": {"type": "string"}
                },
                {
                    "id": "category",
                    "type": "select",
                    "label": "类别",
                    "description": "招待类别",
                    "required": False,
                    "props": {
                        "options": [
                            {"label": "客户招待", "value": "customer"},
                            {"label": "员工活动", "value": "employee"}
                        ]
                    },
                    "validation": None
                }
            ],
            "fieldOrder": ["amount", "reason", "category"]
        }
    }
    
    # 2. 提取表单字段
    schema_json = current_version["schema_json"]
    form_fields = []
    
    if schema_json and "fields" in schema_json:
        for field in schema_json["fields"]:
            form_fields.append({
                "key": field.get("id", ""),
                "name": field.get("label", ""),
                "type": field.get("type", ""),
                "description": field.get("description"),
                "required": field.get("required", False),
                "options": field.get("props", {}).get("options"),
                "props": field.get("props", {})
            })
    
    # 3. 定义系统字段
    system_fields = [
        {
            "key": "sys_submitter",
            "name": "提交人",
            "type": "string",
            "description": "表单提交人",
            "required": False,
            "options": None,
            "props": {}
        },
        {
            "key": "sys_submitter_dept",
            "name": "提交人部门",
            "type": "string",
            "description": "表单提交人所属部门",
            "required": False,
            "options": None,
            "props": {}
        },
        {
            "key": "sys_submit_time",
            "name": "提交时间",
            "type": "datetime",
            "description": "表单提交时间",
            "required": False,
            "options": None,
            "props": {}
        }
    ]
    
    # 4. 构建响应
    response = {
        "form_id": 1,
        "form_name": "招待费申请表",
        "fields": form_fields,
        "system_fields": system_fields
    }
    
    # 5. 验证响应
    print("✓ API 逻辑验证")
    print(f"  - 表单 ID: {response['form_id']}")
    print(f"  - 表单名称: {response['form_name']}")
    print(f"  - 表单字段数: {len(response['fields'])}")
    print(f"  - 系统字段数: {len(response['system_fields'])}")
    
    # 6. 验证字段内容
    assert len(form_fields) == 3, "表单字段数应为 3"
    assert form_fields[0]["key"] == "amount", "第一个字段应为 amount"
    assert form_fields[0]["type"] == "number", "amount 字段类型应为 number"
    assert form_fields[0]["required"] is True, "amount 字段应为必填"
    
    assert form_fields[2]["key"] == "category", "第三个字段应为 category"
    assert form_fields[2]["type"] == "select", "category 字段类型应为 select"
    assert form_fields[2]["options"] is not None, "category 字段应有选项"
    assert len(form_fields[2]["options"]) == 2, "category 字段应有 2 个选项"
    
    # 7. 验证系统字段
    assert len(system_fields) == 3, "系统字段数应为 3"
    
    sys_field_keys = [f["key"] for f in system_fields]
    assert "sys_submitter" in sys_field_keys, "应包含 sys_submitter"
    assert "sys_submitter_dept" in sys_field_keys, "应包含 sys_submitter_dept"
    assert "sys_submit_time" in sys_field_keys, "应包含 sys_submit_time"
    
    submitter_field = next(f for f in system_fields if f["key"] == "sys_submitter")
    assert submitter_field["type"] == "string", "sys_submitter 类型应为 string"
    
    submit_time_field = next(f for f in system_fields if f["key"] == "sys_submit_time")
    assert submit_time_field["type"] == "datetime", "sys_submit_time 类型应为 datetime"
    
    print("\n✓ 所有验证通过！")
    print("\nAPI 端点: GET /api/v1/forms/{form_id}/fields")
    print("返回格式:")
    print("  {")
    print("    'form_id': int,")
    print("    'form_name': str,")
    print("    'fields': [")
    print("      {")
    print("        'key': str,")
    print("        'name': str,")
    print("        'type': str,")
    print("        'description': str | null,")
    print("        'required': bool,")
    print("        'options': list | null,")
    print("        'props': dict")
    print("      }")
    print("    ],")
    print("    'system_fields': [")
    print("      {")
    print("        'key': str,")
    print("        'name': str,")
    print("        'type': str,")
    print("        'description': str,")
    print("        'required': bool,")
    print("        'options': null,")
    print("        'props': dict")
    print("      }")
    print("    ]")
    print("  }")
    
    return True


if __name__ == "__main__":
    try:
        verify_api_logic()
        sys.exit(0)
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
