"""
提交相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ========== 枚举类型 ==========
class SubmissionStatus(str, Enum):
    """提交状态"""
    SUBMITTED = "submitted"
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELETED = "deleted"


class ExportFormat(str, Enum):
    """导出格式"""
    EXCEL = "excel"
    CSV = "csv"


class ExportTaskStatus(str, Enum):
    """导出任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ========== 请求模型 ==========
class SubmissionCreateRequest(BaseModel):
    """创建提交请求"""
    form_id: int = Field(..., description="表单ID")
    data: Dict[str, Any] = Field(..., description="表单数据")
    duration: Optional[int] = Field(None, ge=0, description="填写耗时(秒)")
    source: Optional[str] = Field("pc", description="来源: pc/mobile/qrcode/link")

    @validator('data')
    def validate_data(cls, v):
        if not v:
            raise ValueError("表单数据不能为空")
        return v


class SubmissionUpdateRequest(BaseModel):
    """更新提交请求"""
    data: Dict[str, Any] = Field(..., description="表单数据")


class SubmissionQueryRequest(BaseModel):
    """查询提交列表"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    form_id: Optional[int] = None
    status: Optional[SubmissionStatus] = None
    submitter_user_id: Optional[int] = None
    keyword: Optional[str] = Field(None, max_length=100, description="搜索提交数据")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class DraftSaveRequest(BaseModel):
    """保存草稿请求"""
    form_id: int = Field(..., description="表单ID")
    data: Dict[str, Any] = Field(..., description="草稿数据")


class ExportRequest(BaseModel):
    """导出请求"""
    form_id: int = Field(..., description="表单ID")
    format: ExportFormat = Field(ExportFormat.EXCEL, description="导出格式")
    field_ids: Optional[List[str]] = Field(None, description="导出字段，None=全部")
    submission_ids: Optional[List[int]] = Field(None, description="指定提交ID，None=全部")
    desensitize: bool = Field(True, description="是否脱敏")


# ========== 响应模型 ==========
class AttachmentResponse(BaseModel):
    """附件响应"""
    id: int
    file_name: str
    content_type: Optional[str]
    size: int
    storage_path: str
    download_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    """提交响应"""
    id: int
    form_id: int
    form_version_id: int
    submitter_user_id: Optional[int]
    status: str
    duration: Optional[int]
    source: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    updated_at: datetime

    # 扩展字段
    form_name: Optional[str] = None
    submitter_name: Optional[str] = None
    version_num: Optional[int] = None

    class Config:
        from_attributes = True


class SubmissionDetailResponse(SubmissionResponse):
    """提交详情响应"""
    data_jsonb: Dict[str, Any]
    snapshot_json: Optional[Dict[str, Any]]
    device_info: Optional[Dict[str, Any]] = None
    attachments: List[AttachmentResponse] = Field(default_factory=list)
    process_instance_id: Optional[int] = Field(default=None, description="关联流程实例ID")
    process_state: Optional[str] = Field(default=None, description="流程状态：running/finished/canceled")


class SubmissionListResponse(BaseModel):
    """提交列表响应"""
    items: List[SubmissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DraftResponse(BaseModel):
    """草稿响应"""
    id: int
    form_id: int
    draft_data: Dict[str, Any]
    auto_saved_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExportTaskResponse(BaseModel):
    """导出任务响应"""
    task_id: str
    status: str
    progress: int = Field(0, ge=0, le=100)
    download_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SubmissionStatisticsResponse(BaseModel):
    """提交统计响应"""
    total: int
    by_status: Dict[str, int]
    by_date: List[Dict[str, Any]]
    avg_duration: Optional[float] = None