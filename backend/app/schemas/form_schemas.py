"""
表单相关的 Pydantic 模型
用于请求验证和响应序列化
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ========== 枚举类型 ==========
class FormStatus(str, Enum):
    """表单状态"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AccessMode(str, Enum):
    """访问模式"""
    AUTHENTICATED = "authenticated"  # 需要登录
    PUBLIC = "public"  # 公开访问


# ========== 基础模型 ==========
class FormFieldBase(BaseModel):
    """字段定义基础模型"""
    id: str = Field(..., description="字段唯一标识")
    type: str = Field(..., description="字段类型")
    label: str = Field(..., description="字段标签")
    description: Optional[str] = Field(None, description="帮助文本")
    required: bool = Field(False, description="是否必填")
    props: Dict[str, Any] = Field(default_factory=dict, description="组件属性")
    validation: Optional[Dict[str, Any]] = Field(None, description="校验规则")
    defaultValue: Optional[Any] = Field(None, description="默认值")


class FormSchemaBase(BaseModel):
    """表单Schema基础模型"""
    version: str = Field("1.0.0", description="Schema版本")
    fields: List[FormFieldBase] = Field(..., description="字段列表")
    fieldOrder: Optional[List[str]] = Field(None, description="字段顺序")


class UISchemaBase(BaseModel):
    """UI Schema基础模型"""
    layout: Dict[str, Any] = Field(..., description="布局配置")
    rows: Optional[List[Dict[str, Any]]] = Field(None, description="行配置")
    groups: Optional[List[Dict[str, Any]]] = Field(None, description="分组配置")
    theme: Optional[Dict[str, Any]] = Field(None, description="主题配置")


class LogicRuleBase(BaseModel):
    """逻辑规则基础模型"""
    id: str = Field(..., description="规则ID")
    name: Optional[str] = Field(None, description="规则名称")
    trigger: Dict[str, Any] = Field(..., description="触发配置")
    condition: str = Field(..., description="条件表达式")
    actions: List[Dict[str, Any]] = Field(..., description="动作列表")


class LogicSchemaBase(BaseModel):
    """逻辑Schema基础模型"""
    rules: List[LogicRuleBase] = Field(default_factory=list, description="规则列表")
    validations: Optional[List[Dict[str, Any]]] = Field(None, description="跨字段校验")


# ========== 请求模型 ==========
class FormCreateRequest(BaseModel):
    """创建表单请求"""
    name: str = Field(..., min_length=1, max_length=100, description="表单名称")
    category_id: Optional[int] = Field(None, ge=1, description="分类ID")
    access_mode: AccessMode = Field(AccessMode.AUTHENTICATED, description="访问模式")
    submit_deadline: Optional[datetime] = Field(None, description="填写截止时间")
    allow_edit: bool = Field(True, description="提交后是否可修改")
    max_edit_count: int = Field(10, ge=0, description="最大修改次数")
    allow_repeat_submit: bool = Field(True, description="允许反复提交")
    max_submit_count: int = Field(0, ge=0, description="最大提交次数，0表示不限制")

    # 表单配置（可选，创建时可以为空）
    form_schema: Optional[FormSchemaBase] = Field(None, description="字段结构")
    ui_schema: Optional[UISchemaBase] = Field(None, description="界面布局")
    logic_json: Optional[LogicSchemaBase] = Field(None, description="联动逻辑")

    @validator('submit_deadline')
    def validate_deadline(cls, v):
        if v and v < datetime.now():
            raise ValueError("截止时间不能早于当前时间")
        return v


class FormUpdateRequest(BaseModel):
    """更新表单请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category_id: Optional[int] = Field(None, ge=1, description="分类ID")
    access_mode: Optional[AccessMode] = None
    submit_deadline: Optional[datetime] = None
    allow_edit: Optional[bool] = None
    max_edit_count: Optional[int] = Field(None, ge=0)
    allow_repeat_submit: Optional[bool] = Field(None, description="允许反复提交")
    max_submit_count: Optional[int] = Field(None, ge=0, description="最大提交次数")
    version_tag: Optional[str] = Field(None, max_length=50, description="版本标签（如 v1, v1.1）")

    form_schema: Optional[FormSchemaBase] = None
    ui_schema: Optional[UISchemaBase] = None
    logic_json: Optional[LogicSchemaBase] = None

    @validator('submit_deadline')
    def validate_deadline(cls, v):
        if v and v < datetime.now():
            raise ValueError("截止时间不能早于当前时间")
        return v


class FormPublishRequest(BaseModel):
    """发布表单请求"""
    flow_definition_id: Optional[int] = Field(None, ge=1, description="关联流程定义ID（可选）")


class FormQueryRequest(BaseModel):
    """查询表单请求"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    category: Optional[int] = Field(None, description="分类ID筛选")
    status: Optional[FormStatus] = Field(None, description="状态筛选")
    owner_user_id: Optional[int] = Field(None, description="创建者筛选")


# ========== 响应模型 ==========
class FormVersionResponse(BaseModel):
    """表单版本响应"""
    id: int
    form_id: int
    version: int
    published_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class FormResponse(BaseModel):
    """表单响应"""
    id: int
    tenant_id: int
    name: str
    category_id: Optional[int] = Field(None, description="分类ID")
    access_mode: str
    owner_user_id: int
    status: str
    submit_deadline: Optional[datetime]
    allow_edit: bool
    max_edit_count: int
    allow_repeat_submit: bool = Field(True, description="允许反复提交")
    max_submit_count: int = Field(0, description="最大提交次数，0表示不限制")
    flow_definition_id: Optional[int] = Field(None, description="关联流程定义ID")
    created_at: datetime
    updated_at: datetime

    # 关联数据（可选）
    version_tag: Optional[str] = Field(None, description="版本标签（如 v1, v1.1）")
    current_version: Optional[int] = Field(None, description="当前发布版本号")
    total_submissions: Optional[int] = Field(None, description="提交总数")
    draft_version: Optional[int] = Field(None, description="草稿版本号（存在时为 0）")
    has_unpublished_changes: Optional[bool] = Field(None, description="是否有未发布的表单更改")
    has_flow_changes: Optional[bool] = Field(None, description="是否有未发布的审批流程更改")
    flow_version: Optional[str] = Field(None, description="审批流程版本号")

    class Config:
        from_attributes = True


class FormDetailResponse(FormResponse):
    """表单详情响应（包含配置）"""
    form_schema: Optional[Dict[str, Any]] = None
    ui_schema: Optional[Dict[str, Any]] = None
    logic_json: Optional[Dict[str, Any]] = None

    # 版本历史
    versions: Optional[List[FormVersionResponse]] = None


class FormListResponse(BaseModel):
    """表单列表响应"""
    items: List[FormResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FormTemplateResponse(BaseModel):
    """表单模板响应"""
    id: str
    name: str
    category: str
    description: str


class FormTemplateDetailResponse(FormTemplateResponse):
    """表单模板详情"""
    form_schema: Dict[str, Any]
    ui_schema: Dict[str, Any]
    logic_json: Optional[Dict[str, Any]] = None


# ========== 级联删除相关响应模型 ==========
class FlowDefinitionMetadata(BaseModel):
    """流程定义元数据"""
    id: int
    name: str
    version: int


class CascadeDeleteConflictResponse(BaseModel):
    """级联删除冲突响应（需要用户确认）"""
    form_id: int
    form_name: str
    flow_definition_count: int
    flow_definitions: List[FlowDefinitionMetadata]


class CascadeDeleteSuccessResponse(BaseModel):
    """级联删除成功响应"""
    form_id: int
    form_name: str
    deleted_flow_definitions: int


# ========== 表单字段 API 响应模型 ==========
class FormFieldResponse(BaseModel):
    """表单字段响应"""
    key: str = Field(..., description="字段唯一标识")
    name: str = Field(..., description="字段名称/标签")
    type: str = Field(..., description="字段类型")
    description: Optional[str] = Field(None, description="字段描述")
    required: bool = Field(False, description="是否必填")
    options: Optional[List[Dict[str, Any]]] = Field(None, description="选项列表（用于选择类字段）")
    props: Dict[str, Any] = Field(default_factory=dict, description="字段属性")


class FormFieldsResponse(BaseModel):
    """表单字段列表响应"""
    form_id: int = Field(..., description="表单ID")
    form_name: str = Field(..., description="表单名称")
    fields: List[FormFieldResponse] = Field(..., description="表单字段列表")
    system_fields: List[FormFieldResponse] = Field(..., description="系统字段列表")