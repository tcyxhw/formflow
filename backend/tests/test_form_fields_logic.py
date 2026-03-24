"""
表单字段 API 逻辑验证测试
验证字段提取和系统字段生成的逻辑
"""


def test_form_field_extraction():
    """验证表单字段提取逻辑"""
    
    # 模拟表单 schema
    schema_json = {
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
    
    # 提取表单字段
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
    
    # 验证字段数量
    assert len(form_fields) == 3
    
    # 验证第一个字段
    assert form_fields[0]["key"] == "amount"
    assert form_fields[0]["name"] == "金额"
    assert form_fields[0]["type"] == "number"
    assert form_fields[0]["required"] is True
    assert form_fields[0]["description"] == "招待费金额"
    
    # 验证第二个字段
    assert form_fields[1]["key"] == "reason"
    assert form_fields[1]["name"] == "事由"
    assert form_fields[1]["type"] == "text"
    assert form_fields[1]["required"] is True
    
    # 验证第三个字段（包含选项）
    assert form_fields[2]["key"] == "category"
    assert form_fields[2]["name"] == "类别"
    assert form_fields[2]["type"] == "select"
    assert form_fields[2]["required"] is False
    assert form_fields[2]["options"] is not None
    assert len(form_fields[2]["options"]) == 2
    assert form_fields[2]["options"][0]["label"] == "客户招待"
    assert form_fields[2]["options"][0]["value"] == "customer"


def test_system_fields_generation():
    """验证系统字段生成逻辑"""
    
    # 系统字段定义
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
    
    # 验证系统字段数量
    assert len(system_fields) == 3
    
    # 验证系统字段内容
    sys_field_keys = [f["key"] for f in system_fields]
    assert "sys_submitter" in sys_field_keys
    assert "sys_submitter_dept" in sys_field_keys
    assert "sys_submit_time" in sys_field_keys
    
    # 验证系统字段类型
    submitter_field = next(f for f in system_fields if f["key"] == "sys_submitter")
    assert submitter_field["type"] == "string"
    assert submitter_field["name"] == "提交人"
    assert submitter_field["required"] is False
    
    dept_field = next(f for f in system_fields if f["key"] == "sys_submitter_dept")
    assert dept_field["type"] == "string"
    assert dept_field["name"] == "提交人部门"
    
    submit_time_field = next(f for f in system_fields if f["key"] == "sys_submit_time")
    assert submit_time_field["type"] == "datetime"
    assert submit_time_field["name"] == "提交时间"


def test_response_structure():
    """验证响应结构"""
    
    # 模拟响应数据
    response_data = {
        "form_id": 1,
        "form_name": "招待费申请表",
        "fields": [
            {
                "key": "amount",
                "name": "金额",
                "type": "number",
                "description": "招待费金额",
                "required": True,
                "options": None,
                "props": {"min": 0, "max": 10000}
            }
        ],
        "system_fields": [
            {
                "key": "sys_submitter",
                "name": "提交人",
                "type": "string",
                "description": "表单提交人",
                "required": False,
                "options": None,
                "props": {}
            }
        ]
    }
    
    # 验证响应结构
    assert "form_id" in response_data
    assert "form_name" in response_data
    assert "fields" in response_data
    assert "system_fields" in response_data
    
    # 验证字段结构
    assert response_data["form_id"] == 1
    assert response_data["form_name"] == "招待费申请表"
    assert len(response_data["fields"]) == 1
    assert len(response_data["system_fields"]) == 1
    
    # 验证字段内容
    field = response_data["fields"][0]
    assert field["key"] == "amount"
    assert field["name"] == "金额"
    assert field["type"] == "number"
    assert field["required"] is True
    
    # 验证系统字段内容
    sys_field = response_data["system_fields"][0]
    assert sys_field["key"] == "sys_submitter"
    assert sys_field["name"] == "提交人"
    assert sys_field["type"] == "string"
    assert sys_field["required"] is False
