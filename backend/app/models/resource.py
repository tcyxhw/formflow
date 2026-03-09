# app/models/resource.py
"""
资源预约相关模型
"""
from sqlalchemy import (
    Column, Integer, String, DateTime,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.base import DBBaseModel


class Resource(DBBaseModel):
    """资源表"""
    __tablename__ = "resource"
    __table_args__ = (
        UniqueConstraint("tenant_id", "type", "name", name="uq_resource"),
    )

    type = Column(String(50), nullable=False, comment="资源类型：classroom/equipment")
    name = Column(String(100), nullable=False, comment="资源名称")
    location = Column(String(200), nullable=True, comment="位置")
    capacity = Column(Integer, nullable=True, comment="容量")
    attrs_json = Column(JSONB, nullable=True, comment="属性")

    # 关系
    # bookings = relationship("Booking", back_populates="resource")


class Booking(DBBaseModel):
    """预约记录表"""
    __tablename__ = "booking"
    __table_args__ = (
        Index("idx_resource_time", "resource_id", "start_at", "end_at"),
    )

    resource_id = Column(Integer, ForeignKey("resource.id"), nullable=False)
    form_id = Column(Integer, ForeignKey("form.id"), nullable=True, comment="预约表单ID")
    submission_id = Column(Integer, ForeignKey("submission.id"), nullable=True, comment="提交ID")
    start_at = Column(DateTime, nullable=False, comment="开始时间")
    end_at = Column(DateTime, nullable=False, comment="结束时间")
    status = Column(String(20), default="confirmed", comment="状态")
    created_by = Column(Integer, ForeignKey("user.id"), nullable=False, comment="创建人ID")

    # 关系
    # resource = relationship("Resource", back_populates="bookings")
    # creator = relationship("User")