"""
证书相关模型
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    LargeBinary,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.models.base import DBBaseModel


class CertificateTemplate(DBBaseModel):
    """证书模板表"""
    __tablename__ = "certificate_template"

    name = Column(String(100), nullable=False, comment="模板名称")
    template_type = Column(String(20), nullable=False, comment="模板类型：participation/award")
    html_content = Column(Text, nullable=False, comment="HTML模板内容")
    css_content = Column(Text, nullable=True, comment="CSS样式内容")
    created_by = Column(Integer, ForeignKey("user.id"), nullable=False, comment="创建人ID")


class Certificate(DBBaseModel):
    """证书实例表"""
    __tablename__ = "certificate"
    __table_args__ = (
        Index("idx_certificate_code", "verification_code"),
        Index("idx_certificate_student", "student_user_id", "status"),
    )

    template_id = Column(Integer, ForeignKey("certificate_template.id"), nullable=False, comment="模板ID")
    student_user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="学生ID")
    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=False, comment="活动ID")
    award_record_id = Column(Integer, ForeignKey("award_record.id"), nullable=True, comment="评奖记录ID")

    certificate_type = Column(String(20), nullable=False, comment="证书类型")
    certificate_no = Column(String(50), unique=True, nullable=False, comment="证书编号")
    pdf_content = Column(LargeBinary, nullable=False, comment="PDF内容")
    verification_code = Column(String(20), unique=True, nullable=False, comment="验证码")
    verification_url = Column(String(500), nullable=False, comment="验证URL")

    issued_by = Column(Integer, ForeignKey("user.id"), nullable=False, comment="颁发人ID")
    issued_at = Column(DateTime, nullable=False, comment="颁发时间")
    status = Column(String(20), default="active", comment="状态：active/revoked/expired")
    revoked_at = Column(DateTime, nullable=True, comment="撤销时间")
    revoke_reason = Column(String(500), nullable=True, comment="撤销原因")

    # 关系
    # template = relationship("CertificateTemplate")
    # student = relationship("User", foreign_keys="Certificate.student_user_id")
    # activity = relationship("Activity")
    # award_record = relationship("AwardRecord")
