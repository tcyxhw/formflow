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
    category: Optional[str] = Field(None, max_length=50, description="业务类别")
    access_mode: AccessMode = Field(AccessMode.AUTHENTICATED, description="访问模式")
    submit_deadline: Optional[datetime] = Field(None, description="填写截止时间")
    allow_edit: bool = Field(False, description="提交后是否可修改")
    max_edit_count: int = Field(0, ge=0, description="最大修改次数")

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
    category: Optional[str] = Field(None, max_length=50)
    access_mode: Optional[AccessMode] = None
    submit_deadline: Optional[datetime] = None
    allow_edit: Optional[bool] = None
    max_edit_count: Optional[int] = Field(None, ge=0)

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
    category: Optional[str] = Field(None, description="分类筛选")
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
    category: Optional[str]
    access_mode: str
    owner_user_id: int
    status: str
    submit_deadline: Optional[datetime]
    allow_edit: bool
    max_edit_count: int
    created_at: datetime
    updated_at: datetime

    # 关联数据（可选）
    current_version: Optional[int] = Field(None, description="当前版本号")
    total_submissions: Optional[int] = Field(None, description="提交总数")

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