"""
批量导入历史记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.models.base import DBBaseModel


class BatchImportLog(DBBaseModel):
    """批量导入日志表"""
    __tablename__ = "batch_import_log"

    filename = Column(String(255), nullable=False, comment="导入文件名")
    total_rows = Column(Integer, nullable=False, comment="总行数")
    success_count = Column(Integer, nullable=False, default=0, comment="成功数量")
    failed_count = Column(Integer, nullable=False, default=0, comment="失败数量")
    default_password = Column(String(50), nullable=False, comment="使用的默认密码")
    error_details = Column(Text, nullable=True, comment="错误详情（JSON格式）")
    created_by = Column(Integer, ForeignKey("user.id"), nullable=False, comment="操作人ID")
