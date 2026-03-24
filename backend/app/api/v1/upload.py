# app/api/v1/upload.py
# 模块：文件上传 API（单文件与批量上传）
#
# 用途：
# - 提供单文件与批量上传接口
# - 校验扩展名与真实 MIME（python-magic）
# - 流式写盘，限制最大文件大小，计算 MD5
# - 为图片生成缩略图（EXIF 方向纠正、透明图转白底）
# - 元数据入库（Attachment），统一响应 {code, message, data}
#
# 依赖配置：
# - settings.UPLOAD_DIR：上传文件根目录
# - settings.MAX_UPLOAD_SIZE：最大上传大小（字节）
# - 可选 settings.UPLOAD_PUBLIC_BASE_URL：静态访问前缀（未配则回退 "/uploads"）
#
# 数据流：
# 客户端 -> validate_file(扩展名/MIME 快速校验) -> save_file(流式写入/大小限制/MD5/缩略图)
# -> 写入 Attachment -> success_response({code, message, data})
#
# 端点（用途 / 参数 / 返回值 data）：
# 1) POST /upload
#    用途：上传单个文件，校验/保存/入库，返回可访问 URL 与缩略图 URL
#    参数：
#    - file: UploadFile（必填，文件本体）
#    - file_type: Optional[str]（可选；image/document/text/archive）
#    - owner_type: str（可选；默认 "submission"）
#    - owner_id: Optional[int]（可选）
#    - current_user: User（依赖注入）
#    - tenant_id: int（依赖注入）
#    - db: Session（依赖注入）
#    返回值（data）：
#    - { id: int, filename: str, size: int, url: str, thumbnail_url: Optional[str] }
#
# 2) POST /upload/batch
#    用途：批量上传（最多 10 个），逐个事务提交，汇总成功/失败结果
#    参数：
#    - files: List[UploadFile]（必填；最多 10 个）
#    - file_type: Optional[str]（可选；image/document/text/archive）
#    - current_user: User（依赖注入）
#    - tenant_id: int（依赖注入）
#    - db: Session（依赖注入）
#    返回值（data）：
#    - {
#        results: [
#          {success: True, id: int, filename: str, url: str}
#          | {success: False, filename: str, error: str}
#        ],
#        success_count: int,
#        failed_count: int
#      }
#
# 函数清单（用途 / 参数 / 返回值）：
# - build_public_url(relative_path: str) -> str
#   用途：生成可公开访问的文件 URL（优先 UPLOAD_PUBLIC_BASE_URL，回退 "/uploads"）
#   参数：relative_path（相对 settings.UPLOAD_DIR 的存储路径）
#   返回值：URL 字符串
#
# - _detect_mime_from_head(head: bytes, fallback: Optional[str]) -> str
#   用途：从文件头字节检测真实 MIME（失败回退 fallback）
#   参数：head（建议 4~8KB 头部字节）、fallback（回退 MIME）
#   返回值：MIME 字符串（可能为空）
#
# - FileUploadService.validate_file(file: UploadFile, file_type: Optional[str] = None, max_size: Optional[int] = None) -> None
#   用途：扩展名白名单 + 真实 MIME 的快速校验
#   参数：file（上传文件）、file_type（限定类别）、max_size（预留；大小在 save_file 严格控制）
#   返回值：None
#
# - FileUploadService.save_file(file: UploadFile, tenant_id: int, user_id: int, owner_type: str = "submission", owner_id: Optional[int] = None) -> Dict[str, Any]
#   用途：流式写盘、大小限制、计算 MD5、生成缩略图，返回保存结果
#   参数：file（上传文件）、tenant_id（租户ID）、user_id（用户ID）、owner_type（归属类型）、owner_id（归属ID）
#   返回值：{
#     filename: str, storage_path: str, size: int, content_type: str,
#     file_hash: str, thumbnail_path: Optional[str]
#   }
#
# - FileUploadService.create_thumbnail(image_path: Path, file_uuid: str, size: tuple = (200, 200)) -> Optional[str]
#   用途：生成 JPEG 缩略图（EXIF 纠正、透明图转白底）
#   参数：image_path（原图绝对路径）、file_uuid（文件 UUID）、size（缩略图尺寸）
#   返回值：缩略图相对路径（相对于 settings.UPLOAD_DIR），或 None
#
# - upload_file(...) -> JSONResponse
#   用途：单文件上传端点；校验 -> 保存 -> 入库 -> 返回 URL/缩略图 URL
#   参数：file, file_type, owner_type, owner_id, current_user, tenant_id, db
#   返回值：success_response(data = { id, filename, size, url, thumbnail_url })
#
# - upload_files(...) -> JSONResponse
#   用途：批量上传端点；逐个事务提交；返回每个文件处理结果与统计
#   参数：files, file_type, current_user, tenant_id, db
#   返回值：success_response(data = { results, success_count, failed_count })
#
# 响应规范：
# - 所有接口统一返回 { code, message, data }


from fastapi import APIRouter, UploadFile, File, Depends
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import uuid
import hashlib
import aiofiles
import logging
import contextlib

import magic
from PIL import Image, ImageOps

from app.core.response import success_response
from app.core.exceptions import ValidationError
from app.config import settings
from app.models.user import User
from app.models.form import Attachment
from app.api.deps import get_current_user, get_current_tenant_id
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.utils.audit import audit_log

router = APIRouter()
logger = logging.getLogger(__name__)

# 允许的文件类型（按类别的扩展名白名单）
ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"],
    "text": [".txt", ".csv", ".json", ".xml"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz"]
}

# 按类别允许的 MIME 前缀/枚举（用于从文件内容判断）
ALLOWED_MIME_RULES = {
    "image": ["image/"],
    "text": ["text/"],
    "document": [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument"
    ],
    "archive": [
        "application/zip",
        "application/x-zip-compressed",
        "application/x-rar", "application/vnd.rar",
        "application/x-7z-compressed",
        "application/gzip",
        "application/x-tar"
    ]
}

# 生成缩略图时支持识别的图片扩展
THUMBNAIL_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def build_public_url(relative_path: str) -> str:
    """
    生成可公开访问的文件 URL

    :param relative_path: 存储相对路径（相对于 settings.UPLOAD_DIR）
    :return: 对外可访问的 URL（优先使用 UPLOAD_PUBLIC_BASE_URL，否则回退 "/uploads"）
    """
    base = getattr(settings, "UPLOAD_PUBLIC_BASE_URL", "").rstrip("/")
    if base:
        return f"{base}/{relative_path}"
    return f"/uploads/{relative_path}"


def _detect_mime_from_head(head: bytes, fallback: Optional[str] = None) -> str:
    """
    从文件头部字节检测真实 MIME

    :param head: 文件头部字节（建议 4-8KB）
    :param fallback: 解析失败时的回退 MIME（如客户端提供的 content_type）
    :return: 检测到的 MIME 字符串（可能为空字符串）
    """
    try:
        mime = magic.from_buffer(head, mime=True)  # type: ignore
        if isinstance(mime, bytes):
            mime = mime.decode("utf-8", "ignore")
        return mime or (fallback or "")
    except Exception:
        return fallback or ""


class FileUploadService:
    """
    文件上传服务（校验 / 保存 / 缩略图）

    - validate_file: 扩展名 + 真实 MIME 的快速校验
    - save_file: 流式写盘、大小限制、MD5、缩略图
    - create_thumbnail: 生成图片缩略图（JPEG）
    """

    @staticmethod
    def _validate_file_type_param(file_type: Optional[str]) -> None:
        """
        校验 file_type 参数是否合法

        :param file_type: 文件类型（image/document/text/archive 或 None）
        :return: None
        :raises ValidationError: 非法的 file_type 值
        """
        if file_type is None:
            return
        if file_type not in ALLOWED_EXTENSIONS.keys():
            raise ValidationError(f"无效的文件类型参数: {file_type}")

    @staticmethod
    async def validate_file(
        file: UploadFile,
        file_type: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> None:
        """
        快速验证上传文件（扩展名 + 真实 MIME）

        :param file: 上传文件对象（FastAPI UploadFile）
        :param file_type: 文件类型限制（image/document/text/archive；None 表示仅按扩展名白名单）
        :param max_size: 预留参数（大小限制在 save_file 中严格执行）
        :return: None
        :raises ValidationError: 任一校验不通过（扩展名不在白名单、MIME 不匹配等）
        """
        FileUploadService._validate_file_type_param(file_type)

        filename = file.filename or ""
        file_ext = Path(filename).suffix.lower()

        # 扩展名白名单
        if file_type:
            allowed_exts = ALLOWED_EXTENSIONS[file_type]
            if file_ext not in allowed_exts:
                raise ValidationError(f"不支持的文件类型: {file_ext}")
        else:
            all_exts = {ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts}
            if file_ext not in all_exts:
                raise ValidationError(f"不支持的文件类型: {file_ext}")

        # 读取头部字节用于 MIME 检测
        head = await file.read(8192)
        await file.seek(0)

        detected_mime = _detect_mime_from_head(head, fallback=(file.content_type or ""))

        # 类别 MIME 校验
        if file_type:
            rules = ALLOWED_MIME_RULES.get(file_type, [])
            ok = any(
                detected_mime == rule or detected_mime.startswith(rule)
                for rule in rules
            )
            # 特例容忍：octet-stream 可能来自浏览器/代理，不强拦
            if not ok and detected_mime not in ("application/octet-stream", ""):
                raise ValidationError(f"文件内容类型与 {file_type} 不匹配: {detected_mime}")

        # 文本伪装为图片
        if file_type == "image" and detected_mime.startswith("text/"):
            raise ValidationError("文件内容与类型不匹配（文本文件伪装为图片）")

    @staticmethod
    async def save_file(
        file: UploadFile,
        tenant_id: int,
        user_id: int,
        owner_type: str = "submission",
        owner_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        保存文件到磁盘（流式写入 + 大小限制 + MD5 + 缩略图）

        :param file: 上传文件对象（FastAPI UploadFile）
        :param tenant_id: 租户 ID
        :param user_id: 用户 ID（记录用途）
        :param owner_type: 业务归属类型（记录用途）
        :param owner_id: 业务归属 ID（记录用途）
        :return: 文件信息字典：
            {
              "filename": 原始文件名,
              "storage_path": 相对存储路径,
              "size": 文件大小（字节）,
              "content_type": 检测到的 MIME,
              "file_hash": MD5 字符串,
              "thumbnail_path": 缩略图相对路径或 None
            }
        :raises ValidationError: 文件大小超过限制
        :raises Exception: 写入失败、文件系统异常等
        """
        # 生成路径
        date_path = datetime.now().strftime("%Y/%m/%d")
        file_ext = Path(file.filename or "").suffix.lower()
        file_uuid = str(uuid.uuid4())
        new_filename = f"{file_uuid}{file_ext}"

        relative_path = f"{tenant_id}/{date_path}/{new_filename}"
        absolute_path = Path(settings.UPLOAD_DIR) / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        # 检测 MIME（用于记录/后续决策）
        head = await file.read(8192)
        detected_mime = _detect_mime_from_head(head, fallback=(file.content_type or ""))
        await file.seek(0)

        # 流式写入 + 大小限制 + MD5
        hasher = hashlib.md5()
        size = 0
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024)  # 默认 50MB
        chunk_size = 1024 * 1024  # 1MB

        try:
            async with aiofiles.open(absolute_path, "wb") as f:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_size:
                        raise ValidationError(f"文件大小超过限制 ({max_size / 1024 / 1024:.2f}MB)")
                    hasher.update(chunk)
                    await f.write(chunk)
        except Exception as e:
            # 写入失败时清理半成品
            with contextlib.suppress(Exception):
                if absolute_path.exists():
                    absolute_path.unlink()
            raise e
        finally:
            with contextlib.suppress(Exception):
                await file.seek(0)

        file_hash = hasher.hexdigest()

        # 生成缩略图（针对图片扩展）
        thumbnail_path: Optional[str] = None
        if file_ext in THUMBNAIL_EXTS:
            try:
                thumbnail_path = await FileUploadService.create_thumbnail(
                    absolute_path,
                    file_uuid
                )
            except Exception as e:
                logger.warning(f"生成缩略图失败: {str(e)}")

        return {
            "filename": file.filename or "",
            "storage_path": str(relative_path),
            "size": size,
            "content_type": detected_mime,
            "file_hash": file_hash,
            "thumbnail_path": thumbnail_path
        }

    @staticmethod
    async def create_thumbnail(
        image_path: Path,
        file_uuid: str,
        size: tuple = (200, 200)
    ) -> Optional[str]:
        """
        创建图片缩略图（JPEG）

        :param image_path: 原图绝对路径
        :param file_uuid: 文件 UUID（缩略图命名用）
        :param size: 缩略图尺寸（宽, 高），默认 (200, 200)
        :return: 缩略图相对路径（相对于 settings.UPLOAD_DIR）；失败返回 None
        """
        try:
            # Pillow 兼容：优先使用新枚举，否则回退
            resampling = getattr(
                getattr(Image, "Resampling", Image),
                "LANCZOS",
                getattr(Image, "BICUBIC", 3)
            )

            with Image.open(image_path) as img:
                # 方向纠正
                img = ImageOps.exif_transpose(img)

                # 透明图转白底并转 RGB
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode in ("RGBA", "LA"):
                        bg.paste(img, mask=img.split()[-1])
                    else:
                        img = img.convert("RGBA")
                        bg.paste(img, mask=img.split()[-1])
                    img = bg
                else:
                    img = img.convert("RGB")

                img.thumbnail(size, resampling)

                thumb_filename = f"{file_uuid}_thumb.jpg"
                thumb_path = image_path.parent / thumb_filename
                img.save(thumb_path, "JPEG", quality=85, optimize=True)

            return str(thumb_path.relative_to(Path(settings.UPLOAD_DIR)))
        except Exception as e:
            logger.error(f"创建缩略图失败: {str(e)}")
            return None


@router.post("/upload", summary="上传文件")
@audit_log(action="upload_file", resource_type="file")
async def upload_file(
    file: UploadFile = File(...),
    file_type: Optional[str] = None,
    owner_type: str = "submission",
    owner_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    上传单个文件

    :param file: 文件（FastAPI UploadFile）
    :param file_type: 文件类型限制（image/document/text/archive；None 表示按扩展名白名单）
    :param owner_type: 业务归属类型，默认 "submission"
    :param owner_id: 业务归属 ID
    :param current_user: 当前用户（依赖注入）
    :param tenant_id: 租户 ID（依赖注入）
    :param db: 数据库会话（依赖注入）
    :return: 统一响应结构 JSONResponse：
        {
          "code": 200,
          "message": "文件上传成功",
          "data": {
            "id": int,
            "filename": str,
            "size": int,
            "url": str,
            "thumbnail_url": Optional[str]
          }
        }
    :raises ValidationError: 校验失败（扩展名/MIME/大小超限等）
    """
    # 快速校验
    await FileUploadService.validate_file(file, file_type)

    # 保存文件
    file_info = await FileUploadService.save_file(
        file=file,
        tenant_id=tenant_id,
        user_id=current_user.id,
        owner_type=owner_type,
        owner_id=owner_id
    )

    # 入库
    attachment = Attachment(
        tenant_id=tenant_id,
        owner_type=owner_type,
        owner_id=owner_id or 0,
        file_name=file_info["filename"],
        content_type=file_info["content_type"],
        size=file_info["size"],
        storage_path=file_info["storage_path"],
        created_by=current_user.id
        # 如需去重，可在模型中增加 file_hash 字段并写入 file_info["file_hash"]
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return success_response(
        data={
            "id": attachment.id,
            "filename": attachment.file_name,
            "size": attachment.size,
            "url": build_public_url(attachment.storage_path),
            "thumbnail_url": build_public_url(file_info["thumbnail_path"]) if file_info.get("thumbnail_path") else None
        },
        message="文件上传成功"
    )


@router.post("/upload/batch", summary="批量上传文件")
@audit_log(action="upload_files", resource_type="file")
async def upload_files(
    files: List[UploadFile] = File(...),
    file_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    批量上传文件（一次最多 10 个）

    :param files: 文件列表（FastAPI UploadFile；最多 10 个）
    :param file_type: 文件类型限制（image/document/text/archive）
    :param current_user: 当前用户（依赖注入）
    :param tenant_id: 租户 ID（依赖注入）
    :param db: 数据库会话（依赖注入）
    :return: 统一响应结构 JSONResponse：
        {
          "code": 200,
          "message": "上传完成: 成功X个, 失败Y个",
          "data": {
            "results": [
              {"success": True, "id": int, "filename": str, "url": str}
              | {"success": False, "filename": str, "error": str}
            ],
            "success_count": int,
            "failed_count": int
          }
        }
    :raises ValidationError: 参数非法（如文件数超限）
    """
    if not files:
        raise ValidationError("请至少上传一个文件")

    if len(files) > 10:
        raise ValidationError("一次最多上传10个文件")

    results: List[Dict[str, Any]] = []

    for file in files:
        try:
            await FileUploadService.validate_file(file, file_type)
            file_info = await FileUploadService.save_file(
                file=file,
                tenant_id=tenant_id,
                user_id=current_user.id,
                owner_type="batch",
                owner_id=0
            )

            attachment = Attachment(
                tenant_id=tenant_id,
                owner_type="batch",
                owner_id=0,
                file_name=file_info["filename"],
                content_type=file_info["content_type"],
                size=file_info["size"],
                storage_path=file_info["storage_path"],
                created_by=current_user.id
            )
            db.add(attachment)
            db.commit()
            db.refresh(attachment)

            results.append({
                "success": True,
                "id": attachment.id,
                "filename": attachment.file_name,
                "url": build_public_url(attachment.storage_path)
            })
        except Exception as e:
            db.rollback()
            err_msg = str(e) or "上传失败"
            results.append({
                "success": False,
                "filename": getattr(file, "filename", ""),
                "error": err_msg
            })

    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count

    return success_response(
        data={
            "results": results,
            "success_count": success_count,
            "failed_count": failed_count
        },
        message=f"上传完成: 成功{success_count}个, 失败{failed_count}个"
    )