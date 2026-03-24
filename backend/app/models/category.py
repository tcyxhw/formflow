"""
模块用途: 表单分类模型
依赖配置: SQLAlchemy ORM, PostgreSQL
数据流向: 数据库 -> ORM模型 -> 业务逻辑
函数清单:
    - Category: 表单分类ORM模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.models.base import DBBaseModel, TenantMixin, TimestampMixin


class Category(DBBaseModel, TenantMixin, TimestampMixin):
    """表单分类表"""
    __tablename__ = "category"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_category_tenant_name"),
        Index("idx_category_tenant", "tenant_id"),
    )

    name = Column(String(50), nullable=False, comment="分类名称")
    is_default = Column(Boolean, default=False, nullable=False, comment="是否为默认分类")

    # 关系
    forms = relationship("Form", back_populates="category_obj", foreign_keys="Form.category_id")
