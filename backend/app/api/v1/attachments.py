"""
附件相关API端点
"""
from fastapi import APIRouter, Depends, Path, File, UploadFile, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_tenant_id
from app.schemas.submission_schemas import AttachmentResponse
from app.services.attachment_service import AttachmentService
from app.services.storage_service import StorageService
from app.core.response import success_response, error_response
from app.core.exceptions import NotFoundError
from app.utils.audit import audit_log
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", summary="上传附件")
async def upload_attachment(
        file: UploadFile = File(...),
        current_user = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """上传附件"""
    logger.info(f"Upload request: filename={file.filename}, content_type={file.content_type}, tenant_id={tenant_id}, user_id={current_user.id}")
    
    if tenant_id is None:
        logger.error("Upload failed: tenant_id is None")
        return error_response("租户ID缺失", 4001)
    
    if not file.filename:
        logger.error("Upload failed: filename is empty")
        return error_response("文件名不能为空", 4002)
    
    try:
        attachment = await AttachmentService.upload_attachment(
            file=file,
            tenant_id=tenant_id,
            user_id=current_user.id,
            owner_type="temp",
            db=db
        )

        download_url = AttachmentService.get_download_url(
            attachment.id,
            tenant_id,
            db=db
        )

        response_data = AttachmentResponse.from_orm(attachment).dict()
        response_data["download_url"] = download_url

        logger.info(f"Upload success: attachment_id={attachment.id}")
        return success_response(data=response_data, message="上传成功")
    except Exception as e:
        logger.error(f"Upload attachment error: {e}", exc_info=True)
        return error_response(f"上传失败: {str(e)}", 5001)


@router.get("/{attachment_id}", summary="获取附件信息")
async def get_attachment(
        attachment_id: int = Path(...),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """获取附件信息"""
    try:
        attachment = AttachmentService.get_attachment_by_id(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            db=db
        )

        download_url = AttachmentService.get_download_url(
            attachment_id,
            tenant_id,
            db=db
        )

        response_data = AttachmentResponse.from_orm(attachment).dict()
        response_data["download_url"] = download_url

        return success_response(data=response_data)
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except Exception as e:
        logger.error(f"Get attachment error: {e}")
        return error_response("查询失败", 5001)


@router.get("/{attachment_id}/download", summary="下载附件")
async def download_attachment(
        attachment_id: int = Path(...),
        inline: bool = Query(False, description="是否以内联方式显示（用于图片预览）"),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """下载附件"""
    from app.core.exceptions import BusinessError
    try:
        attachment = AttachmentService.get_attachment_by_id(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            db=db
        )

        logger.info(f"Download attachment: id={attachment_id}, storage_path={attachment.storage_path}, bucket={settings.MINIO_BUCKET}")

        # 获取文件数据
        file_data = StorageService.get_file_data(attachment.storage_path)

        # 根据参数决定是内联显示还是下载
        disposition_type = "inline" if inline else "attachment"

        return StreamingResponse(
            iter([file_data]),
            media_type=attachment.content_type,
            headers={
                "Content-Disposition": f'{disposition_type}; filename="{attachment.file_name}"'
            }
        )
    except NotFoundError as e:
        return error_response(str(e), 4041, status_code=404)
    except BusinessError as e:
        error_msg = str(e)
        if "文件读取失败" in error_msg or "文件不存在" in error_msg:
            return error_response("附件文件不存在", 4041, status_code=404)
        return error_response(error_msg, 5001, status_code=500)
    except Exception as e:
        logger.error(f"Download attachment error: {e}")
        return error_response("下载失败", 5001, status_code=500)


@router.delete("/{attachment_id}", summary="删除附件")
@audit_log(action="delete_attachment", resource_type="attachment", record_before=True)
async def delete_attachment(
        attachment_id: int = Path(...),
        current_user = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """删除附件"""
    try:
        AttachmentService.delete_attachment(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            db=db
        )

        return success_response(message="删除成功")
    except Exception as e:
        logger.error(f"Delete attachment error: {e}")
        return error_response("删除失败", 5001)