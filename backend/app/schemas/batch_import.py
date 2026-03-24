"""
批量导入相关Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.base import BaseSchema


class BatchImportUserRow(BaseSchema):
    """批量导入用户行数据"""
    account: str = Field(..., min_length=3, max_length=50, description="登录账号")
    name: str = Field(..., min_length=2, max_length=50, description="真实姓名")
    identity_type: str = Field(..., pattern="^(student|teacher)$", description="身份类型")
    department_name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    position_name: Optional[str] = Field(None, max_length=50, description="岗位名称")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号")
    identity_no: Optional[str] = Field(None, max_length=50, description="学号/工号")
    entry_year: Optional[int] = Field(None, ge=1900, le=2100, description="入学/入职年份")
    grade: Optional[str] = Field(None, max_length=20, description="年级")
    major: Optional[str] = Field(None, max_length=50, description="专业")
    title: Optional[str] = Field(None, max_length=30, description="职称")
    research_area: Optional[str] = Field(None, max_length=200, description="研究方向")
    office: Optional[str] = Field(None, max_length=100, description="办公室")
    emergency_contact: Optional[str] = Field(None, max_length=50, description="紧急联系人")
    emergency_phone: Optional[str] = Field(None, max_length=20, description="紧急联系电话")


class BatchImportRowResult(BaseSchema):
    """批量导入单行结果"""
    row_number: int = Field(..., description="行号")
    success: bool = Field(..., description="是否成功")
    account: Optional[str] = Field(None, description="账号")
    name: Optional[str] = Field(None, description="姓名")
    error_message: Optional[str] = Field(None, description="错误信息")
    user_id: Optional[int] = Field(None, description="创建的用户ID")


class BatchImportResponse(BaseSchema):
    """批量导入响应"""
    total_rows: int = Field(..., description="总行数")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    results: List[BatchImportRowResult] = Field(default_factory=list, description="详细结果")
    default_password: str = Field(..., description="默认密码")


class BatchImportRequest(BaseSchema):
    """批量导入请求"""
    default_password: str = Field(default="123456", min_length=6, description="默认密码")


class ImportHistoryItem(BaseSchema):
    """导入历史记录项"""
    id: int
    filename: str
    total_rows: int
    success_count: int
    failed_count: int
    created_at: datetime
    created_by: int


class ImportHistoryResponse(BaseSchema):
    """导入历史响应"""
    items: List[ImportHistoryItem]
    total: int


class ImportHistoryDetail(BaseSchema):
    """导入历史详情"""
    id: int
    filename: str
    total_rows: int
    success_count: int
    failed_count: int
    default_password: str
    error_details: List[dict] = Field(default_factory=list)
    created_at: datetime
    created_by: int
