# app/models/form.py
"""
表单与数据相关模型
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, JSON,
    ForeignKey, UniqueConstraint, Index, Text, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import DBBaseModel


class Form(DBBaseModel):
    """表单主表"""
    __tablename__ = "form"
    __table_args__ = (
        Index("idx_form_tenant_category", "tenant_id", "category_id"),
        Index("idx_form_tenant_status", "tenant_id", "status"),
    )

    name = Column(String(100), nullable=False, comment="表单名称")
    category_id = Column(Integer, ForeignKey("category.id", ondelete="SET NULL"), nullable=True, comment="分类ID")
    access_mode = Column(String(20), default="authenticated", comment="访问模式：authenticated/public")
    owner_user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="创建者ID")
    status = Column(String(20), default="draft", comment="状态：draft/published/archived")
    submit_deadline = Column(DateTime, nullable=True, comment="填写截止时间")
    allow_edit = Column(Boolean, default=False, comment="提交后是否可修改")
    max_edit_count = Column(Integer, default=0, comment="最大修改次数")
    flow_definition_id = Column(Integer, ForeignKey("flow_definition.id"), nullable=True, comment="关联流程定义ID")

    # 关系
    category_obj = relationship("Category", back_populates="forms", foreign_keys=[category_id])



class FormVersion(DBBaseModel):
    """表单版本表"""
    __tablename__ = "form_version"
    __table_args__ = (
        UniqueConstraint("tenant_id", "form_id", "version", name="uq_form_version"),
    )

    form_id = Column(Integer, ForeignKey("form.id"), nullable=False)
    version = Column(Integer, nullable=False, comment="版本号")
    schema_json = Column(JSONB, nullable=False, comment="字段结构")
    ui_schema_json = Column(JSONB, nullable=True, comment="界面布局")
    logic_json = Column(JSONB, nullable=True, comment="联动逻辑")
    published_at = Column(DateTime, nullable=True, comment="发布时间")



class FormPermission(DBBaseModel):
    """表单权限表"""
    __tablename__ = "form_permission"
    __table_args__ = (
        UniqueConstraint("tenant_id", "form_id", "grant_type", "grantee_id", "permission", name="uq_form_perm"),
    )

    form_id = Column(Integer, ForeignKey("form.id"), nullable=False)
    grant_type = Column(String(20), nullable=False, comment="授权类型：user/role/department/position")
    grantee_id = Column(Integer, nullable=False, comment="授权对象ID")
    permission = Column(String(20), nullable=False, comment="权限类型：view/fill/edit/export/manage")
    include_children = Column(Boolean, default=True, comment="部门类型时是否包含子部门")
    valid_from = Column(DateTime, nullable=True, comment="生效开始时间")
    valid_to = Column(DateTime, nullable=True, comment="生效结束时间")



class FormShare(DBBaseModel):
    """表单分享表"""
    __tablename__ = "form_share"
    __table_args__ = (
        Index("idx_form_status", "form_id", "status"),
    )

    form_id = Column(Integer, ForeignKey("form.id"), nullable=False)
    share_code = Column(String(20), unique=True, nullable=False, comment="分享码")
    share_url = Column(String(500), nullable=True, comment="分享链接")
    qr_code_path = Column(String(500), nullable=True, comment="二维码路径")
    access_password = Column(String(50), nullable=True, comment="访问密码")
    valid_from = Column(DateTime, nullable=True, comment="有效期开始")
    valid_to = Column(DateTime, nullable=True, comment="有效期结束")
    max_submissions = Column(Integer, nullable=True, comment="最大填写次数")
    current_submissions = Column(Integer, default=0, comment="当前填写次数")
    created_by = Column(Integer, ForeignKey("user.id"), nullable=False)
    status = Column(String(20), default="active", comment="状态：active/expired/disabled")



class Submission(DBBaseModel):
    """提交记录表"""
    __tablename__ = "submission"
    __table_args__ = (
        Index("idx_tenant_form_status", "tenant_id", "form_id", "status"),
        Index("idx_form_created", "form_id", "created_at"),
    )

    form_id = Column(Integer, ForeignKey("form.id"), nullable=False)
    form_version_id = Column(Integer, ForeignKey("form_version.id"), nullable=False)
    submitter_user_id = Column(Integer, ForeignKey("user.id"), nullable=True, comment="提交人ID")
    data_jsonb = Column(JSONB, nullable=False, comment="填写数据")
    snapshot_json = Column(JSONB, nullable=True, comment="表单快照")
    status = Column(String(20), default="submitted", comment="状态")
    duration = Column(Integer, nullable=True, comment="填写耗时(秒)")
    source = Column(String(20), nullable=True, comment="来源：pc/mobile/qrcode/link")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    device_info = Column(JSON, nullable=True, comment="设备信息")



class FormDraft(DBBaseModel):
    """表单草稿表"""
    __tablename__ = "form_draft"
    __table_args__ = (
        Index("idx_user_form", "user_id", "form_id"),
        Index("idx_session_form", "session_id", "form_id"),
    )

    form_id = Column(Integer, ForeignKey("form.id"), nullable=False)
    form_version_id = Column(Integer, ForeignKey("form_version.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    session_id = Column(String(100), nullable=True, comment="匿名用户会话ID")
    draft_data = Column(JSONB, nullable=True, comment="草稿数据")
    auto_saved_at = Column(DateTime, nullable=True, comment="自动保存时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    status = Column(String(20), default="active", comment="状态：active/submitted/expired")


class Attachment(DBBaseModel):
    """附件表"""
    __tablename__ = "attachment"
    __table_args__ = (
        Index("idx_owner", "owner_type", "owner_id"),
    )

    owner_type = Column(String(50), nullable=False, comment="归属类型")
    owner_id = Column(Integer, nullable=True, comment="归属ID")
    file_name = Column(String(255), nullable=False, comment="文件名")
    content_type = Column(String(100), nullable=True, comment="媒体类型")
    size = Column(Integer, nullable=False, comment="文件大小(字节)")
    storage_path = Column(String(500), nullable=False, comment="存储路径")
    created_by = Column(Integer, ForeignKey("user.id"), nullable=False)

