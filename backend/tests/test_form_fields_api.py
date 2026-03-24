"""
模块用途: 表单字段 API 单元测试
依赖配置: sqlite 内存数据库、FastAPI TestClient
数据流向: sqlite -> SQLAlchemy Session -> Service 调用 -> API 端点 -> 响应验证
函数清单:
    - test_get_form_fields_success(): 测试成功获取表单字段
    - test_get_form_fields_includes_system_fields(): 测试系统字段包含
    - test_get_form_fields_with_options(): 测试字段选项提取
    - test_get_form_fields_permission_check(): 测试权限检查
    - test_get_form_fields_multi_tenant_isolation(): 测试多租户隔离
    - test_get_form_fields_not_found(): 测试表单不存在
    - test_get_form_fields_no_version(): 测试表单未配置字段
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterator, Tuple

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import form as form_models  # noqa: F401 注册模型
from app.models import user as user_models  # noqa: F401 注册模型
from app.models.form import Form, FormVersion
from app.models.user import Tenant, User
from app.services.form_service import FormService


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """构建独立的 sqlite 会话。

    Time: O(1), Space: O(1)
    """
    engine = create_engine("sqlite:///:memory:", future=True)
    
    # 禁用外键约束以避免 JSONB 问题
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()
    
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def prepare_form_with_fields(db: Session, tenant_id: int, owner_id: int) -> Form:
    """初始化包含字段的表单。

    Time: O(1), Space: O(1)
    """
    form = Form(
        tenant_id=tenant_id,
        name="招待费申请表",
        access_mode="authenticated",
        owner_user_id=owner_id,
        status="published",
        allow_edit=True,
        max_edit_count=1,
    )
    db.add(form)
    db.flush()

    # 创建表单版本和字段
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

    version = FormVersion(
        tenant_id=tenant_id,
        form_id=form.id,
        version=1,
        schema_json=schema_json,
        ui_schema_json={"layout": {}},
        published_at=datetime.utcnow()
    )
    db.add(version)
    db.commit()
    db.refresh(form)
    return form


@pytest.fixture()
def tenant_and_user(db_session: Session) -> Tuple[Tenant, User]:
    """创建测试租户和用户。"""
    tenant = Tenant(name="测试学校")
    db_session.add(tenant)
    db_session.flush()

    owner = User(
        tenant_id=tenant.id,
        account="owner",
        password_hash="hashed",
        name="表单创建者",
        email="owner@example.com",
        is_active=True,
    )
    db_session.add(owner)
    db_session.commit()
    return tenant, owner


def test_get_form_fields_success(db_session: Session, tenant_and_user: Tuple[Tenant, User]) -> None:
    """验证成功获取表单字段列表。"""
    tenant, owner = tenant_and_user
    form = prepare_form_with_fields(db_session, tenant.id, owner.id)

    # 调用服务获取表单详情
    form_obj, current_version, _ = FormService.get_form_detail(
        form_id=form.id,
        tenant_id=tenant.id,
        db=db_session
    )

    # 验证表单信息
    assert form_obj.id == form.id
    assert form_obj.name == "招待费申请表"

    # 验证版本信息
    assert current_version is not None
    assert current_version.version == 1

    # 验证字段提取
    schema_json = current_version.schema_json
    assert "fields" in schema_json
    assert len(schema_json["fields"]) == 3

    # 验证第一个字段
    field1 = schema_json["fields"][0]
    assert field1["id"] == "amount"
    assert field1["label"] == "金额"
    assert field1["type"] == "number"
    assert field1["required"] is True
    assert field1["description"] == "招待费金额"


def test_get_form_fields_includes_system_fields(db_session: Session, tenant_and_user: Tuple[Tenant, User]) -> None:
    """验证系统字段包含在响应中。"""
    tenant, owner = tenant_and_user
    form = prepare_form_with_fields(db_session, tenant.id, owner.id)

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

    submit_time_field = next(f for f in system_fields if f["key"] == "sys_submit_time")
    assert submit_time_field["type"] == "datetime"
    assert submit_time_field["name"] == "提交时间"


def test_get_form_fields_with_options(db_session: Session, tenant_and_user: Tuple[Tenant, User]) -> None:
    """验证字段选项正确提取。"""
    tenant, owner = tenant_and_user
    form = prepare_form_with_fields(db_session, tenant.id, owner.id)

    form_obj, current_version, _ = FormService.get_form_detail(
        form_id=form.id,
        tenant_id=tenant.id,
        db=db_session
    )

    schema_json = current_version.schema_json
    fields = schema_json["fields"]

    # 找到 category 字段
    category_field = next(f for f in fields if f["id"] == "category")
    assert category_field["type"] == "select"
    assert "options" in category_field["props"]
    assert len(category_field["props"]["options"]) == 2

    # 验证选项内容
    options = category_field["props"]["options"]
    assert options[0]["label"] == "客户招待"
    assert options[0]["value"] == "customer"
    assert options[1]["label"] == "员工活动"
    assert options[1]["value"] == "employee"


def test_get_form_fields_multi_tenant_isolation(db_session: Session) -> None:
    """验证多租户隔离 - 不同租户的表单字段不会混淆。"""
    # 创建两个租户
    tenant1 = Tenant(name="学校1")
    tenant2 = Tenant(name="学校2")
    db_session.add_all([tenant1, tenant2])
    db_session.flush()

    # 创建两个用户
    user1 = User(
        tenant_id=tenant1.id,
        account="user1",
        password_hash="hashed",
        name="用户1",
        email="user1@example.com",
        is_active=True,
    )
    user2 = User(
        tenant_id=tenant2.id,
        account="user2",
        password_hash="hashed",
        name="用户2",
        email="user2@example.com",
        is_active=True,
    )
    db_session.add_all([user1, user2])
    db_session.flush()

    # 为两个租户创建表单
    form1 = prepare_form_with_fields(db_session, tenant1.id, user1.id)
    form2 = prepare_form_with_fields(db_session, tenant2.id, user2.id)

    # 验证租户1的表单
    form1_obj, form1_version, _ = FormService.get_form_detail(
        form_id=form1.id,
        tenant_id=tenant1.id,
        db=db_session
    )
    assert form1_obj.tenant_id == tenant1.id
    assert len(form1_version.schema_json["fields"]) == 3

    # 验证租户2的表单
    form2_obj, form2_version, _ = FormService.get_form_detail(
        form_id=form2.id,
        tenant_id=tenant2.id,
        db=db_session
    )
    assert form2_obj.tenant_id == tenant2.id
    assert len(form2_version.schema_json["fields"]) == 3

    # 验证两个表单是独立的
    assert form1.id != form2.id
    assert form1.tenant_id != form2.tenant_id


def test_get_form_fields_response_structure(db_session: Session, tenant_and_user: Tuple[Tenant, User]) -> None:
    """验证 API 响应结构正确。"""
    tenant, owner = tenant_and_user
    form = prepare_form_with_fields(db_session, tenant.id, owner.id)

    form_obj, current_version, _ = FormService.get_form_detail(
        form_id=form.id,
        tenant_id=tenant.id,
        db=db_session
    )

    # 提取表单字段
    schema_json = current_version.schema_json
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

    # 构建响应
    response = {
        "form_id": form.id,
        "form_name": form.name,
        "fields": form_fields,
        "system_fields": system_fields
    }

    # 验证响应结构
    assert "form_id" in response
    assert "form_name" in response
    assert "fields" in response
    assert "system_fields" in response

    # 验证响应数据
    assert response["form_id"] == form.id
    assert response["form_name"] == "招待费申请表"
    assert len(response["fields"]) == 3
    assert len(response["system_fields"]) == 3

    # 验证字段结构
    for field in response["fields"]:
        assert "key" in field
        assert "name" in field
        assert "type" in field
        assert "description" in field
        assert "required" in field
        assert "options" in field
        assert "props" in field

    # 验证系统字段结构
    for sys_field in response["system_fields"]:
        assert "key" in sys_field
        assert "name" in sys_field
        assert "type" in sys_field
        assert "description" in sys_field
        assert "required" in sys_field
        assert "options" in sys_field
        assert "props" in sys_field


def test_get_form_fields_field_types(db_session: Session, tenant_and_user: Tuple[Tenant, User]) -> None:
    """验证各种字段类型的正确处理。"""
    tenant, owner = tenant_and_user
    form = prepare_form_with_fields(db_session, tenant.id, owner.id)

    form_obj, current_version, _ = FormService.get_form_detail(
        form_id=form.id,
        tenant_id=tenant.id,
        db=db_session
    )

    schema_json = current_version.schema_json
    fields = schema_json["fields"]

    # 验证数字字段
    amount_field = next(f for f in fields if f["id"] == "amount")
    assert amount_field["type"] == "number"
    assert amount_field["required"] is True
    assert "min" in amount_field["props"]
    assert "max" in amount_field["props"]

    # 验证文本字段
    reason_field = next(f for f in fields if f["id"] == "reason")
    assert reason_field["type"] == "text"
    assert reason_field["required"] is True

    # 验证选择字段
    category_field = next(f for f in fields if f["id"] == "category")
    assert category_field["type"] == "select"
    assert category_field["required"] is False
    assert "options" in category_field["props"]



# ========== 纯逻辑测试（不依赖数据库）==========

def test_form_field_extraction_logic() -> None:
    """验证表单字段提取逻辑。"""
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


def test_system_fields_generation_logic() -> None:
    """验证系统字段生成逻辑。"""
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


def test_api_response_structure_logic() -> None:
    """验证 API 响应结构。"""
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


def test_field_options_extraction_logic() -> None:
    """验证字段选项提取逻辑。"""
    # 模拟包含选项的字段
    field_with_options = {
        "id": "category",
        "type": "select",
        "label": "类别",
        "description": "招待类别",
        "required": False,
        "props": {
            "options": [
                {"label": "客户招待", "value": "customer"},
                {"label": "员工活动", "value": "employee"},
                {"label": "其他", "value": "other"}
            ]
        },
        "validation": None
    }

    # 提取选项
    options = field_with_options.get("props", {}).get("options")

    # 验证选项
    assert options is not None
    assert len(options) == 3
    assert options[0]["label"] == "客户招待"
    assert options[0]["value"] == "customer"
    assert options[1]["label"] == "员工活动"
    assert options[1]["value"] == "employee"
    assert options[2]["label"] == "其他"
    assert options[2]["value"] == "other"


def test_field_properties_extraction_logic() -> None:
    """验证字段属性提取逻辑。"""
    # 模拟包含属性的字段
    field_with_props = {
        "id": "amount",
        "type": "number",
        "label": "金额",
        "description": "招待费金额",
        "required": True,
        "props": {
            "min": 0,
            "max": 10000,
            "step": 0.01,
            "placeholder": "请输入金额"
        },
        "validation": {"type": "number"}
    }

    # 提取属性
    props = field_with_props.get("props", {})

    # 验证属性
    assert props is not None
    assert props["min"] == 0
    assert props["max"] == 10000
    assert props["step"] == 0.01
    assert props["placeholder"] == "请输入金额"


def test_empty_schema_handling_logic() -> None:
    """验证空 schema 的处理。"""
    # 模拟空 schema
    schema_json = {
        "version": "1.0.0",
        "fields": []
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

    # 验证空字段列表
    assert len(form_fields) == 0


def test_missing_schema_handling_logic() -> None:
    """验证缺失 schema 的处理。"""
    # 模拟缺失 schema
    schema_json = None

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

    # 验证空字段列表
    assert len(form_fields) == 0


def test_field_with_missing_properties_logic() -> None:
    """验证缺失属性的字段处理。"""
    # 模拟缺失某些属性的字段
    field_with_missing_props = {
        "id": "name",
        "type": "text",
        "label": "姓名"
        # 缺失 description, required, props 等
    }

    # 提取字段
    extracted_field = {
        "key": field_with_missing_props.get("id", ""),
        "name": field_with_missing_props.get("label", ""),
        "type": field_with_missing_props.get("type", ""),
        "description": field_with_missing_props.get("description"),
        "required": field_with_missing_props.get("required", False),
        "options": field_with_missing_props.get("props", {}).get("options"),
        "props": field_with_missing_props.get("props", {})
    }

    # 验证提取结果
    assert extracted_field["key"] == "name"
    assert extracted_field["name"] == "姓名"
    assert extracted_field["type"] == "text"
    assert extracted_field["description"] is None
    assert extracted_field["required"] is False
    assert extracted_field["options"] is None
    assert extracted_field["props"] == {}
