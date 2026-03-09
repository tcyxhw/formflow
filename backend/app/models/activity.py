# app/models/activity.py
"""
活动与评奖相关模型
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON,
    ForeignKey, UniqueConstraint, Index, Float
)
from sqlalchemy.orm import relationship
from app.models.base import DBBaseModel


class Activity(DBBaseModel):
    """活动表"""
    __tablename__ = "activity"
    __table_args__ = (
        Index("idx_activity_tenant_status", "tenant_id", "status"),  # ✅ 修复：添加表名前缀
        Index("idx_activity_tenant_type", "tenant_id", "type"),      # ✅ 修复：添加表名前缀
    )

    name = Column(String(200), nullable=False, comment="活动名称")
    type = Column(String(50), nullable=False, comment="活动类型")
    form_id = Column(Integer, ForeignKey("form.id"), nullable=True, comment="报名表单ID")
    award_form_id = Column(Integer, ForeignKey("form.id"), nullable=True, comment="评奖表单ID")
    start_date = Column(DateTime, nullable=True, comment="开始时间")
    end_date = Column(DateTime, nullable=True, comment="结束时间")
    register_start = Column(DateTime, nullable=True, comment="报名开始时间")
    register_end = Column(DateTime, nullable=True, comment="报名结束时间")
    quota = Column(Integer, nullable=True, comment="名额限制")
    registered_count = Column(Integer, default=0, comment="当前报名数")
    location = Column(String(200), nullable=True, comment="活动地点")
    organizer_dept_id = Column(Integer, ForeignKey("department.id"), nullable=True, comment="主办部门ID")
    manager_user_id = Column(Integer, ForeignKey("user.id"), nullable=True, comment="负责人ID")
    description = Column(String(2000), nullable=True, comment="活动说明")
    status = Column(String(20), default="draft", comment="状态")

    # 关系
    # registrations = relationship("ActivityRegistration", back_populates="activity")
    # check_in_codes = relationship("ActivityCheckInCode", back_populates="activity")
    # award_records = relationship("AwardRecord", back_populates="activity")


class ActivityRegistration(DBBaseModel):
    """活动报名表"""
    __tablename__ = "activity_registration"
    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uq_activity_user"),
        Index("idx_activity_registration_status", "activity_id", "status"),  # ✅ 修复：使用唯一名称
    )

    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    submission_id = Column(Integer, ForeignKey("submission.id"), nullable=True, comment="报名表单提交ID")
    registered_at = Column(DateTime, nullable=False, comment="报名时间")
    checked_in_at = Column(DateTime, nullable=True, comment="签到时间")
    check_in_method = Column(String(20), nullable=True, comment="签到方式")
    status = Column(String(20), default="registered", comment="状态")
    remark = Column(String(500), nullable=True, comment="备注")

    # 关系
    # activity = relationship("Activity", back_populates="registrations")
    # user = relationship("User")


class ActivityCheckInCode(DBBaseModel):
    """活动签到码表"""
    __tablename__ = "activity_check_in_code"
    __table_args__ = (
        Index("idx_activity_checkin_status", "activity_id", "status"),  # ✅ 修复：使用唯一名称
    )

    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=False)
    code = Column(String(100), unique=True, nullable=False, comment="签到码")
    code_type = Column(String(20), nullable=False, comment="码类型：qrcode/number/nfc")
    qr_image_path = Column(String(500), nullable=True, comment="二维码图片路径")
    valid_from = Column(DateTime, nullable=True, comment="有效开始时间")
    valid_to = Column(DateTime, nullable=True, comment="有效结束时间")
    geo_fence = Column(JSON, nullable=True, comment="地理围栏")
    used_count = Column(Integer, default=0, comment="已使用次数")
    max_use = Column(Integer, nullable=True, comment="最大使用次数")
    status = Column(String(20), default="active", comment="状态")

    # 关系
    # activity = relationship("Activity", back_populates="check_in_codes")


class AwardMapping(DBBaseModel):
    """奖项分值映射表"""
    __tablename__ = "award_mapping"
    __table_args__ = (
        UniqueConstraint("tenant_id", "activity_type", "term", "award_level", "score_type", name="uq_award_mapping"),
    )

    activity_type = Column(String(50), nullable=False, comment="活动类型")
    term = Column(String(20), nullable=False, comment="学期")
    award_level = Column(String(50), nullable=False, comment="奖项等级")
    score_type = Column(String(20), nullable=False, comment="分值类型")
    score_value = Column(Float, nullable=False, comment="分值")
    valid_from = Column(DateTime, nullable=True, comment="生效开始日期")
    valid_to = Column(DateTime, nullable=True, comment="生效结束日期")


class AwardRecord(DBBaseModel):
    """评奖记录表"""
    __tablename__ = "award_record"
    __table_args__ = (
        UniqueConstraint("tenant_id", "activity_id", "student_user_id", name="uq_award_record"),
    )

    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=False)
    student_user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="学生ID")
    award_level = Column(String(50), nullable=True, comment="奖项等级")
    score_breakdown = Column(JSON, nullable=True, comment="分项评分")
    comment = Column(String(1000), nullable=True, comment="评语")
    judge_user_id = Column(Integer, ForeignKey("user.id"), nullable=True, comment="评审老师ID")
    judged_at = Column(DateTime, nullable=True, comment="评审时间")
    status = Column(String(20), default="draft", comment="状态")
    attachment_count = Column(Integer, default=0, comment="附件数量")

    # 关系
    # activity = relationship("Activity", back_populates="award_records")
    # student = relationship("User", foreign_keys="AwardRecord.student_user_id")
    # judge = relationship("User", foreign_keys="AwardRecord.judge_user_id")


class LedgerDetail(DBBaseModel):
    """学分台账明细表"""
    __tablename__ = "ledger_detail"
    __table_args__ = (
        Index("idx_ledger_student_term", "student_user_id", "term", "score_type"),  # ✅ 修复：添加表名前缀
    )

    student_user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="学生ID")
    term = Column(String(20), nullable=False, comment="学期")
    score_type = Column(String(20), nullable=False, comment="分值类型")
    delta_value = Column(Float, nullable=False, comment="变动分值")
    source_type = Column(String(50), nullable=False, comment="来源类型")
    source_ref_id = Column(Integer, nullable=True, comment="来源记录ID")
    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=True, comment="活动ID")
    operator_user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="经办人ID")
    reversed_of_id = Column(Integer, nullable=True, comment="冲销来源ID")

    # 关系
    # student = relationship("User", foreign_keys="ledger_detail.student_user_id")
    # operator = relationship("User", foreign_keys="ledger_detail.operator_user_id")