"""
模块用途: 用户快捷入口数据模型
依赖配置: 无特殊外部依赖
数据流向: 用户 -> 快捷入口 -> 表单
功能清单:
    - UserQuickAccess: 存储用户的表单快捷入口配置
"""
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index
from app.models.base import DBBaseModel


class UserQuickAccess(DBBaseModel):
    """
    用户快捷入口表
    
    存储用户自定义的表单快捷入口，支持排序和快速访问。
    每个用户在同一租户下对同一表单只能有一个快捷入口记录。
    """
    __tablename__ = "user_quick_access"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "user_id", "form_id",
            name="uq_user_quick_access"
        ),
        Index("idx_user_quick_access_user", "user_id", "tenant_id"),
        Index("idx_user_quick_access_form", "form_id"),
    )

    user_id = Column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
        comment="用户ID"
    )
    form_id = Column(
        Integer,
        ForeignKey("form.id"),
        nullable=False,
        comment="表单ID"
    )
    sort_order = Column(
        Integer,
        default=0,
        nullable=False,
        comment="排序顺序，数值越小越靠前"
    )
