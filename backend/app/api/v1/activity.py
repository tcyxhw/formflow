"""
模块用途: 活动管理API路由
依赖配置: FastAPI, SQLAlchemy
数据流向: HTTP请求 -> ActivityService -> 数据库
路由清单:
    - POST   /activities              创建活动
    - GET    /activities              活动列表
    - GET    /activities/{id}         活动详情
    - PUT    /activities/{id}         更新活动
    - DELETE /activities/{id}         删除活动
    - POST   /activities/{id}/publish 发布活动
    - POST   /activities/{id}/register 报名活动
    - POST   /checkin                 签到
    - POST   /activities/{id}/awards  提交评分
    - POST   /activities/{id}/finalize  Finalize获奖名单
    - POST   /activities/{id}/issue-credits 发放学分
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_tenant_id
from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.exceptions import BusinessError, NotFoundError, ValidationError
from app.models.user import User
from app.schemas.base import ResponseSchema
from app.services.activity_service import ActivityService
from app.services.credit_service import CreditService
from app.services.certificate_service import CertificateService

router = APIRouter()


@router.post("", response_model=ResponseSchema, summary="创建活动")
async def create_activity(
    name: str = Body(..., description="活动名称"),
    activity_type: str = Body(..., description="活动类型"),
    form_id: Optional[int] = Body(None, description="报名表单ID"),
    award_form_id: Optional[int] = Body(None, description="评奖表单ID"),
    start_date: Optional[str] = Body(None, description="开始时间(ISO格式)"),
    end_date: Optional[str] = Body(None, description="结束时间(ISO格式)"),
    register_start: Optional[str] = Body(None, description="报名开始时间"),
    register_end: Optional[str] = Body(None, description="报名结束时间"),
    quota: Optional[int] = Body(None, description="名额限制"),
    location: Optional[str] = Body(None, description="活动地点"),
    organizer_dept_id: Optional[int] = Body(None, description="主办部门ID"),
    description: Optional[str] = Body(None, description="活动说明"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """创建新活动（草稿状态）"""
    try:
        from datetime import datetime
        
        # 解析日期
        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            if not date_str:
                return None
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                return None
        
        activity = ActivityService.create_activity(
            tenant_id=tenant_id,
            user_id=current_user.id,
            name=name,
            activity_type=activity_type,
            form_id=form_id,
            award_form_id=award_form_id,
            start_date=parse_date(start_date),
            end_date=parse_date(end_date),
            register_start=parse_date(register_start),
            register_end=parse_date(register_end),
            quota=quota,
            location=location,
            organizer_dept_id=organizer_dept_id,
            description=description,
            db=db,
        )
        
        return success_response(
            data={
                "id": activity.id,
                "name": activity.name,
                "status": activity.status,
            },
            message="活动创建成功"
        )
    except ValidationError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(f"创建失败: {str(e)}", 5001)


@router.get("", response_model=ResponseSchema, summary="活动列表")
async def list_activities(
    status: Optional[str] = Query(None, description="状态筛选"),
    activity_type: Optional[str] = Query(None, description="类型筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """查询活动列表"""
    try:
        activities, total = ActivityService.list_activities(
            tenant_id=tenant_id,
            db=db,
            status=status,
            activity_type=activity_type,
            keyword=keyword,
            page=page,
            page_size=page_size,
        )
        
        return success_response(
            data={
                "items": [
                    {
                        "id": a.id,
                        "name": a.name,
                        "type": a.type,
                        "status": a.status,
                        "start_date": a.start_date.isoformat() if a.start_date else None,
                        "end_date": a.end_date.isoformat() if a.end_date else None,
                        "quota": a.quota,
                        "registered_count": a.registered_count,
                        "location": a.location,
                    }
                    for a in activities
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        )
    except Exception as e:
        return error_response(str(e), 5001)


@router.get("/{activity_id}", response_model=ResponseSchema, summary="活动详情")
async def get_activity_detail(
    activity_id: int = Path(..., ge=1, description="活动ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """获取活动详情和统计信息"""
    try:
        result = ActivityService.get_activity_detail(
            activity_id=activity_id,
            tenant_id=tenant_id,
            db=db,
        )
        
        activity = result["activity"]
        stats = result["stats"]
        
        return success_response(
            data={
                "id": activity.id,
                "name": activity.name,
                "type": activity.type,
                "status": activity.status,
                "description": activity.description,
                "location": activity.location,
                "start_date": activity.start_date.isoformat() if activity.start_date else None,
                "end_date": activity.end_date.isoformat() if activity.end_date else None,
                "register_start": activity.register_start.isoformat() if activity.register_start else None,
                "register_end": activity.register_end.isoformat() if activity.register_end else None,
                "quota": activity.quota,
                "registered_count": activity.registered_count,
                "stats": stats,
            }
        )
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except Exception as e:
        return error_response(str(e), 5001)


@router.post("/{activity_id}/publish", response_model=ResponseSchema, summary="发布活动")
async def publish_activity(
    activity_id: int = Path(..., ge=1, description="活动ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """发布活动（从草稿变为已发布）"""
    try:
        activity = ActivityService.publish_activity(
            activity_id=activity_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db,
        )
        
        return success_response(
            data={"id": activity.id, "status": activity.status},
            message="活动发布成功"
        )
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except BusinessError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(str(e), 5001)


@router.post("/{activity_id}/register", response_model=ResponseSchema, summary="报名活动")
async def register_activity(
    activity_id: int = Path(..., ge=1, description="活动ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """学生报名参加活动"""
    try:
        registration = ActivityService.register_activity(
            activity_id=activity_id,
            user_id=current_user.id,
            tenant_id=tenant_id,
            db=db,
        )
        
        return success_response(
            data={
                "registration_id": registration.id,
                "status": registration.status,
                "registered_at": registration.registered_at.isoformat(),
            },
            message="报名成功"
        )
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except BusinessError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(str(e), 5001)


@router.post("/{activity_id}/cancel-registration", response_model=ResponseSchema, summary="取消报名")
async def cancel_registration(
    activity_id: int = Path(..., ge=1, description="活动ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """取消活动报名"""
    try:
        # 先查询报名记录
        from app.models.activity import ActivityRegistration
        
        registration = db.query(ActivityRegistration).filter(
            ActivityRegistration.activity_id == activity_id,
            ActivityRegistration.user_id == current_user.id,
            ActivityRegistration.tenant_id == tenant_id,
        ).first()
        
        if not registration:
            return error_response("未找到报名记录", 4041)
        
        ActivityService.cancel_registration(
            registration_id=registration.id,
            user_id=current_user.id,
            tenant_id=tenant_id,
            db=db,
        )
        
        return success_response(message="取消报名成功")
    except BusinessError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(str(e), 5001)


@router.post("/checkin", response_model=ResponseSchema, summary="活动签到")
async def checkin(
    code: str = Body(..., description="签到码"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """使用签到码进行签到"""
    try:
        registration = ActivityService.checkin(
            code=code,
            user_id=current_user.id,
            tenant_id=tenant_id,
            db=db,
        )
        
        return success_response(
            data={
                "registration_id": registration.id,
                "checked_in_at": registration.checked_in_at.isoformat() if registration.checked_in_at else None,
            },
            message="签到成功"
        )
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except BusinessError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(str(e), 5001)


@router.post("/{activity_id}/awards", response_model=ResponseSchema, summary="提交评分")
async def submit_award(
    activity_id: int = Path(..., ge=1, description="活动ID"),
    student_user_id: int = Body(..., description="学生ID"),
    award_level: str = Body(..., description="奖项等级"),
    score_breakdown: dict = Body(default={}, description="分项评分"),
    comment: Optional[str] = Body(None, description="评语"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """评委提交评分"""
    try:
        award_record = ActivityService.submit_award_score(
            activity_id=activity_id,
            student_user_id=student_user_id,
            judge_user_id=current_user.id,
            award_level=award_level,
            score_breakdown=score_breakdown,
            comment=comment,
            tenant_id=tenant_id,
            db=db,
        )
        
        return success_response(
            data={"award_record_id": award_record.id},
            message="评分提交成功"
        )
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except BusinessError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(str(e), 5001)


@router.get("/{activity_id}/award-stats", response_model=ResponseSchema, summary="评奖统计")
async def get_award_stats(
    activity_id: int = Path(..., ge=1, description="活动ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """获取活动评奖统计"""
    try:
        stats = ActivityService.get_activity_award_stats(
            activity_id=activity_id,
            tenant_id=tenant_id,
            db=db,
        )
        
        return success_response(data=stats)
    except Exception as e:
        return error_response(str(e), 5001)


@router.post("/{activity_id}/finalize", response_model=ResponseSchema, summary="Finalize获奖名单")
async def finalize_awards(
    activity_id: int = Path(..., ge=1, description="活动ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """Finalize获奖名单"""
    try:
        records = ActivityService.finalize_awards(
            activity_id=activity_id,
            user_id=current_user.id,
            tenant_id=tenant_id,
            db=db,
        )
        
        return success_response(
            data={"finalized_count": len(records)},
            message="获奖名单已Finalize"
        )
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except BusinessError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(str(e), 5001)


@router.post("/{activity_id}/issue-credits", response_model=ResponseSchema, summary="发放学分")
async def issue_credits(
    activity_id: int = Path(..., ge=1, description="活动ID"),
    student_user_id: Optional[int] = Body(None, description="指定学生ID（不指定则发放给所有获奖学生）"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """发放活动学分"""
    try:
        if student_user_id:
            # 给单个学生发放
            entry = CreditService.calculate_and_issue_credits(
                activity_id=activity_id,
                student_user_id=student_user_id,
                operator_user_id=current_user.id,
                tenant_id=tenant_id,
                db=db,
            )
            entries = [entry]
        else:
            # 批量发放
            entries = CreditService.batch_issue_credits(
                activity_id=activity_id,
                operator_user_id=current_user.id,
                tenant_id=tenant_id,
                db=db,
            )
        
        return success_response(
            data={
                "issued_count": len(entries),
                "entries": [
                    {
                        "id": e.id,
                        "student_id": e.student_user_id,
                        "score": e.delta_value,
                        "term": e.term,
                    }
                    for e in entries
                ],
            },
            message=f"学分发放成功，共{len(entries)}人"
        )
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except BusinessError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(str(e), 5001)


@router.post("/{activity_id}/generate-certificates", response_model=ResponseSchema, summary="生成证书")
async def generate_certificates(
    activity_id: int = Path(..., ge=1, description="活动ID"),
    template_id: int = Body(..., description="证书模板ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """批量生成证书"""
    try:
        certificates = CertificateService.batch_generate_certificates(
            activity_id=activity_id,
            template_id=template_id,
            tenant_id=tenant_id,
            operator_user_id=current_user.id,
            db=db,
        )
        
        return success_response(
            data={
                "generated_count": len(certificates),
                "certificates": [
                    {
                        "id": c.id,
                        "certificate_no": c.certificate_no,
                        "student_id": c.student_user_id,
                    }
                    for c in certificates
                ],
            },
            message=f"证书生成成功，共{len(certificates)}份"
        )
    except BusinessError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(str(e), 5001)
