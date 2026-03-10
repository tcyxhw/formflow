"""
提交相关API端点
"""
from fastapi import APIRouter, Depends, Query, Path, Body, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_tenant_id
from app.schemas.submission_schemas import *
from app.services.submission_service import SubmissionService
from app.services.draft_service import DraftService
from app.services.attachment_service import AttachmentService
from app.services.export_service import ExportService
from app.core.response import success_response, error_response
from app.core.exceptions import ValidationError, BusinessError, NotFoundError
from app.utils.audit import audit_log
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 提交管理 ==========

@router.post("", summary="创建提交")
@audit_log(action="create_submission", resource_type="submission", record_after=True)
async def create_submission(
        request: "SubmissionCreateRequest" = Body(...),
        req: Request = None,
        current_user: dict = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """创建提交"""
    try:
        # 获取IP和设备信息
        ip_address = req.client.host if req else None
        device_info = {
            "user_agent": req.headers.get("user-agent") if req else None
        }

        submission = SubmissionService.create_submission(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.get("user_id"),
            ip_address=ip_address,
            device_info=device_info,
            db=db
        )

        return success_response(
            data=SubmissionResponse.from_orm(submission).dict(),
            message="提交成功"
        )
    except ValidationError as e:
        return error_response(str(e), 4001)
    except BusinessError as e:
        return error_response(str(e), 4002)
    except Exception as e:
        logger.error(f"Create submission error: {e}")
        return error_response("提交失败", 5001)


@router.put("/{submission_id}", summary="更新提交")
@audit_log(action="update_submission", resource_type="submission", record_before=True, record_after=True)
async def update_submission(
        submission_id: int = Path(...),
        request: "SubmissionUpdateRequest" = Body(...),
        current_user: dict = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """更新提交"""
    try:
        submission = SubmissionService.update_submission(
            submission_id=submission_id,
            request=request,
            tenant_id=tenant_id,
            user_id=current_user["user_id"],
            db=db
        )

        return success_response(
            data=SubmissionResponse.from_orm(submission).dict(),
            message="更新成功"
        )
    except ValidationError as e:
        return error_response(str(e), 4001)
    except BusinessError as e:
        return error_response(str(e), 4002)
    except Exception as e:
        logger.error(f"Update submission error: {e}")
        return error_response("更新失败", 5001)


@router.delete("/{submission_id}", summary="删除提交")
@audit_log(action="delete_submission", resource_type="submission", record_before=True)
async def delete_submission(
        submission_id: int = Path(...),
        current_user: dict = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """删除提交"""
    try:
        SubmissionService.delete_submission(
            submission_id=submission_id,
            tenant_id=tenant_id,
            user_id=current_user["user_id"],
            db=db
        )

        return success_response(message="删除成功")
    except BusinessError as e:
        return error_response(str(e), 4002)
    except Exception as e:
        logger.error(f"Delete submission error: {e}")
        return error_response("删除失败", 5001)


@router.get("/{submission_id}", summary="获取提交详情")
async def get_submission(
        submission_id: int = Path(...),
        current_user: dict = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """获取提交详情"""
    try:
        submission = SubmissionService.get_submission_by_id(
            submission_id=submission_id,
            tenant_id=tenant_id,
            db=db
        )

        # 获取附件
        attachments = AttachmentService.list_attachments(
            owner_type="submission",
            owner_id=submission_id,
            tenant_id=tenant_id,
            db=db
        )

        response_data = SubmissionDetailResponse.from_orm(submission).dict()
        response_data["attachments"] = [
            AttachmentResponse.from_orm(att).dict() for att in attachments
        ]
        process_instance_id, process_state = SubmissionService.get_process_overview(
            submission_id=submission_id,
            tenant_id=tenant_id,
            db=db,
        )
        response_data["process_instance_id"] = process_instance_id
        response_data["process_state"] = process_state

        return success_response(data=response_data)
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except Exception as e:
        logger.error(f"Get submission error: {e}")
        return error_response("查询失败", 5001)


@router.get("", summary="查询提交列表")
async def list_submissions(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        form_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        submitter_user_id: Optional[int] = Query(None),
        keyword: Optional[str] = Query(None),
        date_from: Optional[datetime] = Query(None),
        date_to: Optional[datetime] = Query(None),
        current_user: dict = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """查询提交列表"""
    try:
        request = SubmissionQueryRequest(
            page=page,
            page_size=page_size,
            form_id=form_id,
            status=status,
            submitter_user_id=submitter_user_id,
            keyword=keyword,
            date_from=date_from,
            date_to=date_to
        )

        submissions, total = SubmissionService.list_submissions(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user["user_id"],
            db=db
        )

        items = [SubmissionResponse.from_orm(s).dict() for s in submissions]

        response = SubmissionListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

        return success_response(data=response.dict())
    except Exception as e:
        logger.error(f"List submissions error: {e}")
        return error_response("查询失败", 5001)


# ========== 草稿管理 ==========

@router.post("/drafts", summary="保存草稿")
async def save_draft(
        request: "DraftSaveRequest" = Body(...),
        current_user: dict = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """保存草稿"""
    try:
        draft = DraftService.save_draft(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.get("user_id"),
            session_id=None,
            db=db
        )

        return success_response(
            data=DraftResponse.from_orm(draft).dict(),
            message="草稿已保存"
        )
    except Exception as e:
        logger.error(f"Save draft error: {e}")
        return error_response("保存失败", 5001)


@router.get("/drafts/{form_id}", summary="获取草稿")
async def get_draft(
        form_id: int = Path(...),
        current_user: dict = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """获取草稿"""
    try:
        draft = DraftService.get_draft(
            form_id=form_id,
            tenant_id=tenant_id,
            user_id=current_user.get("user_id"),
            session_id=None,
            db=db
        )

        if not draft:
            return success_response(data=None, message="无草稿")

        return success_response(data=DraftResponse.from_orm(draft).dict())
    except Exception as e:
        logger.error(f"Get draft error: {e}")
        return error_response("查询失败", 5001)


@router.delete("/drafts/{draft_id}", summary="删除草稿")
async def delete_draft(
        draft_id: int = Path(...),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """删除草稿"""
    try:
        DraftService.delete_draft(draft_id, tenant_id, db)
        return success_response(message="删除成功")
    except Exception as e:
        logger.error(f"Delete draft error: {e}")
        return error_response("删除失败", 5001)


# ========== 统计分析 ==========

@router.get("/statistics/{form_id}", summary="提交统计")
async def get_statistics(
        form_id: int = Path(...),
        current_user: dict = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """提交统计"""
    try:
        stats = SubmissionService.get_submission_statistics(
            form_id=form_id,
            tenant_id=tenant_id,
            db=db
        )

        return success_response(data=stats)
    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        return error_response("查询失败", 5001)


# ========== 数据导出 ==========

@router.post("/export", summary="导出数据")
async def export_submissions(
        request: "ExportRequest" = Body(...),
        current_user: dict = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """导出数据"""
    try:
        result = ExportService.export_submissions(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user["user_id"],
            db=db
        )

        return success_response(data=result)
    except Exception as e:
        logger.error(f"Export submissions error: {e}")
        return error_response("导出失败", 5001)


@router.get("/export/{task_id}", summary="查询导出任务")
async def get_export_task(
        task_id: str = Path(...),
        tenant_id: int = Depends(get_current_tenant_id)
):
    """查询导出任务状态"""
    try:
        status = ExportService.get_export_task_status(task_id, tenant_id)
        return success_response(data=status)
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except Exception as e:
        logger.error(f"Get export task error: {e}")
        return error_response("查询失败", 5001)