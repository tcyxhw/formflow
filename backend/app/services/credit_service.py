"""
模块用途: 学分管理与入账服务
依赖配置: 无
数据流向: AwardRecord -> 学分计算 -> LedgerDetail入账
函数清单:
    - calculate_and_issue_credits(): 计算并发放学分
    - batch_issue_credits(): 批量发放学分
    - reverse_credit_entry(): 冲销学分记录
    - get_student_credit_summary(): 获取学生学分汇总
    - get_credit_ledger(): 获取学分明细台账
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, NotFoundError
from app.models.activity import (
    Activity,
    AwardMapping,
    AwardRecord,
    LedgerDetail,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class CreditService:
    """学分管理服务"""

    @staticmethod
    def get_award_score_value(
        tenant_id: int,
        activity_type: str,
        term: str,
        award_level: str,
        score_type: str,
        db: Session,
    ) -> float:
        """获取奖项对应的分值

        :param tenant_id: 租户ID
        :param activity_type: 活动类型
        :param term: 学期
        :param award_level: 奖项等级
        :param score_type: 分值类型
        :param db: 数据库会话
        :return: 分值

        Time: O(1), Space: O(1)
        """

        mapping = db.query(AwardMapping).filter(
            AwardMapping.tenant_id == tenant_id,
            AwardMapping.activity_type == activity_type,
            AwardMapping.term == term,
            AwardMapping.award_level == award_level,
            AwardMapping.score_type == score_type,
            AwardMapping.valid_from <= datetime.utcnow(),
            AwardMapping.valid_to >= datetime.utcnow(),
        ).first()

        if not mapping:
            # 返回默认值或抛出异常
            default_values = {
                "一等奖": 3.0,
                "二等奖": 2.0,
                "三等奖": 1.0,
                "参与奖": 0.5,
            }
            return default_values.get(award_level, 0.0)

        return mapping.score_value

    @staticmethod
    def calculate_and_issue_credits(
        activity_id: int,
        student_user_id: int,
        operator_user_id: int,
        tenant_id: int,
        db: Session,
        term: Optional[str] = None,
    ) -> LedgerDetail:
        """计算并发放学分

        :param activity_id: 活动ID
        :param student_user_id: 学生ID
        :param operator_user_id: 操作人ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :param term: 学期（默认当前学期）
        :return: 学分入账记录

        Time: O(1), Space: O(1)
        """

        activity = db.query(Activity).filter(
            Activity.id == activity_id,
            Activity.tenant_id == tenant_id,
        ).first()

        if not activity:
            raise NotFoundError("活动不存在")

        # 获取学生获奖记录
        award_record = db.query(AwardRecord).filter(
            AwardRecord.activity_id == activity_id,
            AwardRecord.student_user_id == student_user_id,
            AwardRecord.tenant_id == tenant_id,
            AwardRecord.status == "finalized",
        ).first()

        if not award_record:
            raise BusinessError("该学生没有获奖记录或未Finalize")

        # 确定学期
        if not term:
            # 根据当前日期自动判断学期
            now = datetime.utcnow()
            year = now.year
            month = now.month
            if month >= 9:
                term = f"{year}-{year + 1}-1"  # 上学期
            elif month <= 2:
                term = f"{year - 1}-{year}-1"  # 上学期
            else:
                term = f"{year - 1}-{year}-2"  # 下学期

        # 获取分值
        score_value = CreditService.get_award_score_value(
            tenant_id=tenant_id,
            activity_type=activity.type,
            term=term,
            award_level=award_record.award_level,
            score_type="activity",
            db=db,
        )

        # 创建入账记录
        ledger_entry = LedgerDetail(
            tenant_id=tenant_id,
            student_user_id=student_user_id,
            term=term,
            score_type="activity",
            delta_value=score_value,
            source_type="activity_award",
            source_ref_id=award_record.id,
            activity_id=activity_id,
            operator_user_id=operator_user_id,
        )

        db.add(ledger_entry)
        db.commit()
        db.refresh(ledger_entry)

        logger.info(
            f"学分发放成功: student={student_user_id}, activity={activity_id}, "
            f"score={score_value}, term={term}"
        )

        return ledger_entry

    @staticmethod
    def batch_issue_credits(
        activity_id: int,
        operator_user_id: int,
        tenant_id: int,
        db: Session,
    ) -> List[LedgerDetail]:
        """批量发放学分（给所有获奖学生）

        :param activity_id: 活动ID
        :param operator_user_id: 操作人ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 学分入账记录列表

        Time: O(N), Space: O(N)
        """

        # 获取所有获奖学生
        award_records = db.query(AwardRecord).filter(
            AwardRecord.activity_id == activity_id,
            AwardRecord.tenant_id == tenant_id,
            AwardRecord.status == "finalized",
        ).all()

        if not award_records:
            raise BusinessError("该活动没有获奖记录")

        ledger_entries = []
        for record in award_records:
            try:
                entry = CreditService.calculate_and_issue_credits(
                    activity_id=activity_id,
                    student_user_id=record.student_user_id,
                    operator_user_id=operator_user_id,
                    tenant_id=tenant_id,
                    db=db,
                )
                ledger_entries.append(entry)
            except Exception as e:
                logger.error(f"学分发放失败: student={record.student_user_id}, error={e}")
                continue

        logger.info(f"批量学分发放完成: activity={activity_id}, count={len(ledger_entries)}")

        return ledger_entries

    @staticmethod
    def reverse_credit_entry(
        ledger_id: int,
        operator_user_id: int,
        tenant_id: int,
        reason: str,
        db: Session,
    ) -> LedgerDetail:
        """冲销学分记录

        :param ledger_id: 原入账记录ID
        :param operator_user_id: 操作人ID
        :param tenant_id: 租户ID
        :param reason: 冲销原因
        :param db: 数据库会话
        :return: 冲销记录

        Time: O(1), Space: O(1)
        """

        original_entry = db.query(LedgerDetail).filter(
            LedgerDetail.id == ledger_id,
            LedgerDetail.tenant_id == tenant_id,
        ).first()

        if not original_entry:
            raise NotFoundError("入账记录不存在")

        if original_entry.reversed_of_id:
            raise BusinessError("该记录已经是冲销记录")

        # 创建冲销记录（负值）
        reverse_entry = LedgerDetail(
            tenant_id=tenant_id,
            student_user_id=original_entry.student_user_id,
            term=original_entry.term,
            score_type=original_entry.score_type,
            delta_value=-original_entry.delta_value,  # 负值冲销
            source_type=f"reverse:{original_entry.source_type}",
            source_ref_id=original_entry.source_ref_id,
            activity_id=original_entry.activity_id,
            operator_user_id=operator_user_id,
            reversed_of_id=original_entry.id,
        )

        db.add(reverse_entry)
        db.commit()
        db.refresh(reverse_entry)

        logger.info(f"学分冲销成功: original={ledger_id}, reverse={reverse_entry.id}, reason={reason}")

        return reverse_entry

    @staticmethod
    def get_student_credit_summary(
        student_user_id: int,
        tenant_id: int,
        db: Session,
        term: Optional[str] = None,
    ) -> Dict:
        """获取学生学分汇总

        :param student_user_id: 学生ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :param term: 学期（None表示全部学期）
        :return: 学分汇总信息

        Time: O(1), Space: O(1)
        """

        base_query = db.query(LedgerDetail).filter(
            LedgerDetail.student_user_id == student_user_id,
            LedgerDetail.tenant_id == tenant_id,
        )

        if term:
            base_query = base_query.filter(LedgerDetail.term == term)

        # 计算总分
        total_score = db.query(func.sum(LedgerDetail.delta_value)).filter(
            LedgerDetail.student_user_id == student_user_id,
            LedgerDetail.tenant_id == tenant_id,
        ).scalar() or 0.0

        # 按类型统计
        type_breakdown = db.query(
            LedgerDetail.score_type,
            func.sum(LedgerDetail.delta_value),
            func.count(LedgerDetail.id),
        ).filter(
            LedgerDetail.student_user_id == student_user_id,
            LedgerDetail.tenant_id == tenant_id,
        ).group_by(LedgerDetail.score_type).all()

        return {
            "student_id": student_user_id,
            "term": term or "all",
            "total_score": round(total_score, 2),
            "entry_count": base_query.count(),
            "type_breakdown": [
                {
                    "score_type": t,
                    "total": round(s, 2),
                    "count": c,
                }
                for t, s, c in type_breakdown
            ],
        }

    @staticmethod
    def get_credit_ledger(
        student_user_id: int,
        tenant_id: int,
        db: Session,
        term: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[LedgerDetail], int]:
        """获取学分明细台账

        :param student_user_id: 学生ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :param term: 学期筛选
        :param page: 页码
        :param page_size: 每页数量
        :return: (明细列表, 总数)

        Time: O(N), Space: O(N)
        """

        base_query = db.query(LedgerDetail).filter(
            LedgerDetail.student_user_id == student_user_id,
            LedgerDetail.tenant_id == tenant_id,
        )

        if term:
            base_query = base_query.filter(LedgerDetail.term == term)

        # 统计总数
        total = base_query.count()

        # 分页查询
        entries = (
            base_query.order_by(desc(LedgerDetail.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return entries, total
