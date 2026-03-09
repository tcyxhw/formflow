# app/models/base.py
"""
基础模型类
所有模型都继承自这个基类
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime, timezone
from app.core.database import Base


class TenantMixin:
    """租户隔离混入类"""

    @declared_attr
    def tenant_id(cls):
        return Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True, comment="租户ID")


class TimestampMixin:
    """时间戳混入类"""
    # 修复：使用 timezone-aware 的 datetime
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新时间"
    )


class DBBaseModel(Base, TenantMixin, TimestampMixin):
    """所有模型的基类"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")

    def to_dict(self) -> dict:
        """转换为字典"""
        result = {}
        for c in self.__mapper__.column_attrs:
            value = getattr(self, c.key)
            if isinstance(value, datetime):
                result[c.key] = value.isoformat()
            else:
                result[c.key] = value
        return result
