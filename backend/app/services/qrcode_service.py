"""
二维码生成服务
"""
import qrcode
from io import BytesIO
from app.services.storage_service import StorageService
import logging

logger = logging.getLogger(__name__)


class QRCodeService:
    """二维码服务"""

    @staticmethod
    def generate_qrcode(
            data: str,
            tenant_id: int,
            filename: str = None
    ) -> dict:
        """
        生成二维码并上传到MinIO

        Args:
            data: 要编码的数据（通常是URL）
            tenant_id: 租户ID
            filename: 文件名（可选）

        Returns:
            {
                "storage_path": "存储路径",
                "file_hash": "哈希值",
                "size": 文件大小
            }
        """
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,  # 控制二维码大小（1-40）
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # 生成图片
        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为字节流
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_data = buffer.getvalue()

        # 上传到MinIO
        if not filename:
            import uuid
            filename = f"qrcode_{uuid.uuid4().hex[:8]}.png"

        result = StorageService.upload_file(
            file_data=qr_data,
            filename=filename,
            content_type="image/png",
            tenant_id=tenant_id,
            category="qrcodes"
        )

        logger.info(f"Generated QR code for: {data[:50]}...")
        return result