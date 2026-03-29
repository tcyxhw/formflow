"""
提交相关API端点
"""
from fastapi import APIRouter, Depends, Query, Path, Body, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_tenant_id
from app.schemas.submission_schemas import *
from app.services.submission_service import SubmissionService
from app.services.draft_service import DraftService
from app.services.attachment_service import AttachmentService
from app.services.export_service import ExportService
from app.core.response import success_response, error_response
from app.core.exceptions import ValidationError, BusinessError, NotFoundError
from app.models.user import User
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
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """创建提交"""
    try:
        logger.info(f"创建提交请求: form_id={request.form_id}, user_id={current_user.id}, data_keys={list(request.data.keys())}")
        
        # 获取IP和设备信息
        ip_address = req.client.host if req else None
        device_info = {
            "user_agent": req.headers.get("user-agent") if req else None
        }

        submission = SubmissionService.create_submission(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.id,
            ip_address=ip_address,
            device_info=device_info,
            db=db
        )

        return success_response(
            data=SubmissionResponse.from_orm(submission).dict(),
            message="提交成功"
        )
    except ValidationError as e:
        logger.error(f"Validation error in create_submission: {str(e)}")
        return error_response(str(e), 4001)
    except BusinessError as e:
        logger.error(f"Business error in create_submission: {str(e)}")
        return error_response(str(e), 4002)
    except Exception as e:
        logger.error(f"Create submission error: {e}", exc_info=True)
        return error_response("提交失败", 5001)


@router.put("/{submission_id}", summary="更新提交")
@audit_log(action="update_submission", resource_type="submission", record_before=True, record_after=True)
async def update_submission(
        submission_id: int = Path(...),
        request: "SubmissionUpdateRequest" = Body(...),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """更新提交"""
    try:
        submission = SubmissionService.update_submission(
            submission_id=submission_id,
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.id,
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
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """删除提交"""
    try:
        SubmissionService.delete_submission(
            submission_id=submission_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
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
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """获取提交详情"""
    try:
        from app.models.form import Form, FormVersion
        
        submission = SubmissionService.get_submission_by_id(
            submission_id=submission_id,
            tenant_id=tenant_id,
            db=db
        )

        # 获取表单信息
        form = db.query(Form).filter(Form.id == submission.form_id).first()
        form_name = form.name if form else "未知表单"

        # 获取附件
        attachments = AttachmentService.list_attachments(
            owner_type="submission",
            owner_id=submission_id,
            tenant_id=tenant_id,
            db=db
        )

        response_data = SubmissionDetailResponse.from_orm(submission).dict()
        response_data["form_name"] = form_name
        
        # 获取提交人姓名
        if submission.submitter_user_id:
            submitter = db.query(User).filter(User.id == submission.submitter_user_id).first()
            response_data["submitter_name"] = submitter.name if submitter else "未知用户"
        else:
            response_data["submitter_name"] = "匿名用户"
        
        # 为附件生成下载URL
        attachments_with_url = []
        for att in attachments:
            att_dict = AttachmentResponse.from_orm(att).dict()
            att_dict["download_url"] = AttachmentService.get_download_url(
                att.id, tenant_id, db=db
            )
            attachments_with_url.append(att_dict)
        response_data["attachments"] = attachments_with_url
        
        form_version = db.query(FormVersion).filter(
            FormVersion.id == submission.form_version_id
        ).first()

        if form_version and form_version.schema_json:
            schema = form_version.schema_json
            if isinstance(schema, dict) and "fields" in schema:
                if not response_data.get("snapshot_json"):
                    response_data["snapshot_json"] = {}
                
                snapshot = response_data["snapshot_json"]
                
                if not snapshot.get("field_labels"):
                    field_labels = {}
                    for field in schema["fields"]:
                        if isinstance(field, dict) and "id" in field:
                            field_labels[field["id"]] = field.get("label", field["id"])
                    snapshot["field_labels"] = field_labels
                
                if not snapshot.get("field_types"):
                    field_types = {}
                    for field in schema["fields"]:
                        if isinstance(field, dict) and "id" in field:
                            field_types[field["id"]] = field.get("type", "text")
                    snapshot["field_types"] = field_types
                
                if not snapshot.get("field_options"):
                    field_options = {}
                    for field in schema["fields"]:
                        if isinstance(field, dict) and "id" in field:
                            if field.get("type") in ["select", "radio", "checkbox"]:
                                options = field.get("props", {}).get("options", [])
                                field_options[field["id"]] = options
                    snapshot["field_options"] = field_options
        
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
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """查询提交列表"""
    try:
        from app.models.form import Form
        from app.models.user import User
        from app.models.workflow import ProcessInstance, Task

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
            user_id=current_user.id,
            db=db
        )

        # 批量查询关联的流程实例
        submission_ids = [s.id for s in submissions]
        process_instances = {}
        if submission_ids:
            processes = db.query(ProcessInstance).filter(
                ProcessInstance.submission_id.in_(submission_ids)
            ).all()
            for p in processes:
                process_instances[p.submission_id] = p

        # 批量查询当前进行中的任务（获取 SLA 信息）
        process_instance_ids = [p.id for p in process_instances.values()]
        current_tasks = {}
        now = datetime.utcnow()
        if process_instance_ids:
            tasks = db.query(Task).filter(
                Task.process_instance_id.in_(process_instance_ids),
                Task.status.in_(["open", "claimed"])
            ).all()
            for task in tasks:
                # 每个流程实例只取第一个未完成的任务
                if task.process_instance_id not in current_tasks:
                    current_tasks[task.process_instance_id] = task

        items = []
        for s in submissions:
            item_dict = SubmissionResponse.from_orm(s).dict()

            # 获取表单名称
            form = db.query(Form).filter(Form.id == s.form_id).first()
            item_dict["form_name"] = form.name if form else "未知表单"

            # 获取提交人名称
            if s.submitter_user_id:
                user = db.query(User).filter(User.id == s.submitter_user_id).first()
                item_dict["submitter_name"] = user.name if user else "未知用户"
            else:
                item_dict["submitter_name"] = "匿名用户"

            # 获取流程实例信息
            process = process_instances.get(s.id)
            if process:
                item_dict["process_instance_id"] = process.id
                item_dict["process_state"] = process.state
                item_dict["flow_definition_id"] = process.flow_definition_id

                # 获取当前任务的 SLA 信息
                current_task = current_tasks.get(process.id)
                if current_task:
                    item_dict["due_at"] = current_task.due_at.isoformat() if current_task.due_at else None
                    item_dict["is_overdue"] = bool(current_task.due_at and now > current_task.due_at)
                else:
                    item_dict["due_at"] = None
                    item_dict["is_overdue"] = False
            else:
                item_dict["process_instance_id"] = None
                item_dict["process_state"] = None
                item_dict["flow_definition_id"] = None
                item_dict["due_at"] = None
                item_dict["is_overdue"] = False

            items.append(item_dict)

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


@router.get("/forms/{form_id}/latest", summary="获取用户最新提交")
async def get_latest_submission(
        form_id: int = Path(...),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """获取当前用户对指定表单的最新提交记录"""
    try:
        submission = SubmissionService.get_latest_submission_by_user(
            form_id=form_id,
            user_id=current_user.id,
            tenant_id=tenant_id,
            db=db
        )

        if not submission:
            return success_response(data=None, message="无历史提交")

        return success_response(data=SubmissionResponse.from_orm(submission).dict())
    except Exception as e:
        logger.error(f"Get latest submission error: {e}")
        return error_response("查询失败", 5001)


# ========== 草稿管理 ==========

@router.post("/drafts", summary="保存草稿")
async def save_draft(
        request: "DraftSaveRequest" = Body(...),
        current_user: User = Depends(get_current_user),
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
        current_user: User = Depends(get_current_user),
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
        current_user: User = Depends(get_current_user),
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
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """导出数据"""
    try:
        result = ExportService.export_submissions(
            request=request,
            tenant_id=tenant_id,
            user_id=current_user.id,
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


# ========== 审批流程 ==========

@router.post("/{submission_id}/start-approval", summary="发起审批")
@audit_log(action="start_approval", resource_type="submission", record_before=True, record_after=True)
async def start_approval(
        submission_id: int = Path(...),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """手动发起审批流程（用于 pending_approval 状态的提交）"""
    try:
        submission = SubmissionService.start_approval(
            submission_id=submission_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        return success_response(
            data=SubmissionResponse.from_orm(submission).dict(),
            message="审批流程已发起"
        )
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except BusinessError as e:
        return error_response(str(e), 4002)
    except Exception as e:
        logger.error(f"Start approval error: {e}", exc_info=True)
        return error_response("发起审批失败", 5001)