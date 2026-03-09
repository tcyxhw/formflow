"""
模块用途: 活动管理服务
依赖配置: 无
数据流向: Activity模型 -> 业务逻辑处理 -> API响应
函数清单:
    - create_activity(): 创建活动
    - publish_activity(): 发布活动
    - register_activity(): 报名活动
    - generate_checkin_code(): 生成签到码
    - submit_award(): 提交评分
    - calculate_credits(): 计算学分
"""
from __future__ import annotations

import logging
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, NotFoundError, ValidationError
from app.models.activity import (
    Activity,
    ActivityCheckInCode,
    ActivityRegistration,
    AwardMapping,
    AwardRecord,
    LedgerDetail,
)
from app.models.user import User
from app.models.workflow import TaskActionLog

logger = logging.getLogger(__name__)


class ActivityService:
    """活动业务服务"""

    @staticmethod
    def create_activity(
        tenant_id: int,
        user_id: int,
        name: str,
        activity_type: str,
        form_id: Optional[int],
        award_form_id: Optional[int],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        register_start: Optional[datetime],
        register_end: Optional[datetime],
        quota: Optional[int],
        location: Optional[str],
        organizer_dept_id: Optional[int],
        description: Optional[str],
        db: Session,
    ) -> Activity:
        """创建活动

        :param tenant_id: 租户ID
        :param user_id: 创建人ID
        :param name: 活动名称
        :param activity_type: 活动类型
        :param form_id: 报名表单ID
        :param award_form_id: 评奖表单ID
        :param start_date: 开始时间
        :param end_date: 结束时间
        :param register_start: 报名开始
        :param register_end: 报名结束
        :param quota: 名额限制
        :param location: 活动地点
        :param organizer_dept_id: 主办部门ID
        :param description: 活动说明
        :param db: 数据库会话
        :return: 活动对象

        Time: O(1), Space: O(1)
        """

        # 参数校验
        if register_start and register_end and register_start >= register_end:
            raise ValidationError("报名开始时间必须早于结束时间")

        if start_date and end_date and start_date >= end_date:
            raise ValidationError("活动开始时间必须早于结束时间")

        activity = Activity(
            tenant_id=tenant_id,
            name=name,
            type=activity_type,
            form_id=form_id,
            award_form_id=award_form_id,
            start_date=start_date,
            end_date=end_date,
            register_start=register_start,
            register_end=register_end,
            quota=quota,
            location=location,
            organizer_dept_id=organizer_dept_id,
            manager_user_id=user_id,
            description=description,
            status="draft",
            registered_count=0,
        )

        db.add(activity)
        db.commit()
        db.refresh(activity)

        logger.info(f"活动创建成功: id={activity.id}, name={name}, tenant={tenant_id}")

        return activity

    @staticmethod
    def publish_activity(
        activity_id: int,
        tenant_id: int,
        user_id: int,
        db: Session,
    ) -> Activity:
        """发布活动

        :param activity_id: 活动ID
        :param tenant_id: 租户ID
        :param user_id: 操作人ID
        :param db: 数据库会话
        :return: 活动对象

        Time: O(1), Space: O(1)
        """

        activity = db.query(Activity).filter(
            Activity.id == activity_id,
            Activity.tenant_id == tenant_id,
        ).first()

        if not activity:
            raise NotFoundError("活动不存在")

        if activity.manager_user_id != user_id:
            raise BusinessError("只有活动负责人可以发布活动")

        if activity.status != "draft":
            raise BusinessError("只有草稿状态的活动可以发布")

        activity.status = "published"
        db.commit()

        logger.info(f"活动发布成功: id={activity_id}")

        return activity

    @staticmethod
    def list_activities(
        tenant_id: int,
        db: Session,
        status: Optional[str] = None,
        activity_type: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Activity], int]:
        """查询活动列表

        :param tenant_id: 租户ID
        :param status: 状态筛选
        :param activity_type: 类型筛选
        :param keyword: 关键词搜索
        :param page: 页码
        :param page_size: 每页数量
        :param db: 数据库会话
        :return: (活动列表, 总数)

        Time: O(N), Space: O(N)
        """

        base_query = db.query(Activity).filter(Activity.tenant_id == tenant_id)

        if status:
            base_query = base_query.filter(Activity.status == status)

        if activity_type:
            base_query = base_query.filter(Activity.type == activity_type)

        if keyword:
            base_query = base_query.filter(Activity.name.ilike(f"%{keyword}%"))

        # 统计总数
        total = base_query.count()

        # 分页查询
        activities = (
            base_query.order_by(desc(Activity.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return activities, total

    @staticmethod
    def get_activity_detail(
        activity_id: int,
        tenant_id: int,
        db: Session,
    ) -> Dict:
        """获取活动详情（包含统计信息）

        :param activity_id: 活动ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 活动详情字典

        Time: O(1), Space: O(1)
        """

        activity = db.query(Activity).filter(
            Activity.id == activity_id,
            Activity.tenant_id == tenant_id,
        ).first()

        if not activity:
            raise NotFoundError("活动不存在")

        # 统计报名情况
        registration_stats = db.query(
            ActivityRegistration.status,
            func.count(ActivityRegistration.id),
        ).filter(
            ActivityRegistration.activity_id == activity_id,
        ).group_by(ActivityRegistration.status).all()

        stats_map = {status: count for status, count in registration_stats}

        return {
            "activity": activity,
            "stats": {
                "total_registrations": sum(stats_map.values()),
                "pending": stats_map.get("pending", 0),
                "approved": stats_map.get("approved", 0),
                "rejected": stats_map.get("rejected", 0),
                "cancelled": stats_map.get("cancelled", 0),
            },
        }

    @staticmethod
    def register_activity(
        activity_id: int,
        user_id: int,
        tenant_id: int,
        db: Session,
    ) -> ActivityRegistration:
        """报名活动

        :param activity_id: 活动ID
        :param user_id: 用户ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 报名记录

        Time: O(1), Space: O(1)
        """

        activity = db.query(Activity).filter(
            Activity.id == activity_id,
            Activity.tenant_id == tenant_id,
        ).first()

        if not activity:
            raise NotFoundError("活动不存在")

        if activity.status != "published":
            raise BusinessError("活动未发布或已结束")

        # 检查报名时间
        now = datetime.utcnow()
        if activity.register_start and now < activity.register_start:
            raise BusinessError("报名尚未开始")

        if activity.register_end and now > activity.register_end:
            raise BusinessError("报名已结束")

        # 检查是否已报名
        existing = db.query(ActivityRegistration).filter(
            ActivityRegistration.activity_id == activity_id,
            ActivityRegistration.user_id == user_id,
        ).first()

        if existing and existing.status not in ["cancelled", "rejected"]:
            raise BusinessError("您已经报名了该活动")

        # 检查名额
        if activity.quota and activity.registered_count >= activity.quota:
            raise BusinessError("活动名额已满")

        registration = ActivityRegistration(
            tenant_id=tenant_id,
            activity_id=activity_id,
            user_id=user_id,
            registered_at=now,
            status="approved",  # 默认直接通过，如需审核改为pending
        )

        db.add(registration)

        # 更新报名计数
        activity.registered_count += 1

        db.commit()
        db.refresh(registration)

        logger.info(f"活动报名成功: activity={activity_id}, user={user_id}")

        return registration

    @staticmethod
    def cancel_registration(
        registration_id: int,
        user_id: int,
        tenant_id: int,
        db: Session,
    ) -> None:
        """取消报名

        :param registration_id: 报名ID
        :param user_id: 用户ID
        :param tenant_id: 租户ID
        :param db: 数据库会话

        Time: O(1), Space: O(1)
        """

        registration = db.query(ActivityRegistration).filter(
            ActivityRegistration.id == registration_id,
            ActivityRegistration.tenant_id == tenant_id,
        ).first()

        if not registration:
            raise NotFoundError("报名记录不存在")

        if registration.user_id != user_id:
            raise BusinessError("只能取消自己的报名")

        if registration.status == "cancelled":
            raise BusinessError("报名已取消")

        registration.status = "cancelled"

        # 更新活动报名计数
        activity = db.query(Activity).filter(
            Activity.id == registration.activity_id,
        ).first()

        if activity and activity.registered_count > 0:
            activity.registered_count -= 1

        db.commit()

        logger.info(f"报名取消成功: registration={registration_id}")

    @staticmethod
    def generate_checkin_code(
        activity_id: int,
        tenant_id: int,
        user_id: int,
        db: Session,
        code_type: str = "qrcode",
        valid_hours: int = 24,
        max_use: Optional[int] = None,
    ) -> ActivityCheckInCode:
        """生成签到码

        :param activity_id: 活动ID
        :param tenant_id: 租户ID
        :param user_id: 操作人ID
        :param code_type: 码类型（qrcode/number）
        :param valid_hours: 有效时长（小时）
        :param max_use: 最大使用次数
        :param db: 数据库会话
        :return: 签到码对象

        Time: O(1), Space: O(1)
        """

        activity = db.query(Activity).filter(
            Activity.id == activity_id,
            Activity.tenant_id == tenant_id,
        ).first()

        if not activity:
            raise NotFoundError("活动不存在")

        if activity.manager_user_id != user_id:
            raise BusinessError("只有活动负责人可以生成签到码")

        # 生成随机码
        if code_type == "number":
            code = ''.join(random.choices(string.digits, k=6))
        else:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        now = datetime.utcnow()

        checkin_code = ActivityCheckInCode(
            tenant_id=tenant_id,
            activity_id=activity_id,
            code=code,
            code_type=code_type,
            valid_from=now,
            valid_to=now + timedelta(hours=valid_hours),
            max_use=max_use,
            status="active",
        )

        db.add(checkin_code)
        db.commit()
        db.refresh(checkin_code)

        logger.info(f"签到码生成成功: activity={activity_id}, code={code}")

        return checkin_code

    @staticmethod
    def checkin(
        code: str,
        user_id: int,
        tenant_id: int,
        db: Session,
    ) -> ActivityRegistration:
        """签到

        :param code: 签到码
        :param user_id: 用户ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 报名记录

        Time: O(1), Space: O(1)
        """

        # 查找签到码
        checkin_code = db.query(ActivityCheckInCode).filter(
            ActivityCheckInCode.code == code,
            ActivityCheckInCode.tenant_id == tenant_id,
            ActivityCheckInCode.status == "active",
        ).first()

        if not checkin_code:
            raise NotFoundError("无效的签到码")

        now = datetime.utcnow()

        if checkin_code.valid_from and now < checkin_code.valid_from:
            raise BusinessError("签到码尚未生效")

        if checkin_code.valid_to and now > checkin_code.valid_to:
            raise BusinessError("签到码已过期")

        if checkin_code.max_use and checkin_code.used_count >= checkin_code.max_use:
            raise BusinessError("签到码已达最大使用次数")

        # 查找报名记录
        registration = db.query(ActivityRegistration).filter(
            ActivityRegistration.activity_id == checkin_code.activity_id,
            ActivityRegistration.user_id == user_id,
            ActivityRegistration.status == "approved",
        ).first()

        if not registration:
            raise BusinessError("您没有该活动的报名记录")

        if registration.checked_in_at:
            raise BusinessError("您已经签到过了")

        # 更新签到信息
        registration.checked_in_at = now
        registration.check_in_method = checkin_code.code_type

        # 更新签到码使用次数
        checkin_code.used_count += 1

        db.commit()

        logger.info(f"签到成功: activity={checkin_code.activity_id}, user={user_id}")

        return registration

    @staticmethod
    def submit_award_score(
        activity_id: int,
        student_user_id: int,
        judge_user_id: int,
        award_level: str,
        score_breakdown: Dict,
        comment: Optional[str],
        tenant_id: int,
        db: Session,
    ) -> AwardRecord:
        """提交评分

        :param activity_id: 活动ID
        :param student_user_id: 学生ID
        :param judge_user_id: 评委ID
        :param award_level: 奖项等级
        :param score_breakdown: 分项评分
        :param comment: 评语
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 评奖记录

        Time: O(1), Space: O(1)
        """

        activity = db.query(Activity).filter(
            Activity.id == activity_id,
            Activity.tenant_id == tenant_id,
        ).first()

        if not activity:
            raise NotFoundError("活动不存在")

        # 检查是否已经评分
        existing = db.query(AwardRecord).filter(
            AwardRecord.activity_id == activity_id,
            AwardRecord.student_user_id == student_user_id,
            AwardRecord.judge_user_id == judge_user_id,
        ).first()

        if existing:
            raise BusinessError("您已经评分过了")

        award_record = AwardRecord(
            tenant_id=tenant_id,
            activity_id=activity_id,
            student_user_id=student_user_id,
            award_level=award_level,
            score_breakdown=score_breakdown,
            comment=comment,
            judge_user_id=judge_user_id,
            judged_at=datetime.utcnow(),
            status="confirmed",
        )

        db.add(award_record)
        db.commit()
        db.refresh(award_record)

        logger.info(f"评分提交成功: activity={activity_id}, student={student_user_id}, judge={judge_user_id}")

        return award_record

    @staticmethod
    def get_activity_award_stats(
        activity_id: int,
        tenant_id: int,
        db: Session,
    ) -> Dict:
        """获取活动评奖统计

        :param activity_id: 活动ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 评奖统计

        Time: O(N), Space: O(N)
        """

        # 查询所有评分记录
        records = db.query(AwardRecord).filter(
            AwardRecord.activity_id == activity_id,
            AwardRecord.tenant_id == tenant_id,
        ).all()

        # 按学生分组计算平均分
        student_scores: Dict[int, List[Dict]] = {}
        for record in records:
            if record.student_user_id not in student_scores:
                student_scores[record.student_user_id] = []
            student_scores[record.student_user_id].append({
                "award_level": record.award_level,
                "score_breakdown": record.score_breakdown,
                "judge_id": record.judge_user_id,
            })

        # 计算每个学生平均分和最终奖项
        results = []
        for student_id, scores in student_scores.items():
            # 多评委时取平均
            avg_score = sum(
                sum(s["score_breakdown"].values()) / len(s["score_breakdown"])
                for s in scores
            ) / len(scores)

            # 取最多评委认定的奖项
            award_levels = [s["award_level"] for s in scores]
            final_award = max(set(award_levels), key=award_levels.count)

            user = db.query(User).filter(User.id == student_id).first()

            results.append({
                "student_id": student_id,
                "student_name": user.name if user else f"用户{student_id}",
                "judge_count": len(scores),
                "average_score": round(avg_score, 2),
                "final_award": final_award,
            })

        # 按分数排序
        results.sort(key=lambda x: x["average_score"], reverse=True)

        return {
            "total_judged": len(student_scores),
            "total_records": len(records),
            "rankings": results,
        }

    @staticmethod
    def finalize_awards(
        activity_id: int,
        user_id: int,
        tenant_id: int,
        db: Session,
    ) -> List[AwardRecord]:
        """Finalize获奖名单

        :param activity_id: 活动ID
        :param user_id: 操作人ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 获奖记录列表

        Time: O(N), Space: O(N)
        """

        activity = db.query(Activity).filter(
            Activity.id == activity_id,
            Activity.tenant_id == tenant_id,
        ).first()

        if not activity:
            raise NotFoundError("活动不存在")

        if activity.manager_user_id != user_id:
            raise BusinessError("只有活动负责人可以Finalize获奖名单")

        # 获取评奖统计
        stats = ActivityService.get_activity_award_stats(activity_id, tenant_id, db)

        # 更新所有评分记录为最终状态
        records = db.query(AwardRecord).filter(
            AwardRecord.activity_id == activity_id,
            AwardRecord.tenant_id == tenant_id,
        ).all()

        for record in records:
            record.status = "finalized"

        db.commit()

        logger.info(f"获奖名单Finalize成功: activity={activity_id}, total={len(records)}")

        return records
