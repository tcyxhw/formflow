"""
模块用途: 证书生成与验证服务
依赖配置: weasyprint, qrcode
数据流向: CertificateTemplate + AwardRecord -> PDF证书 -> 验证查询
函数清单:
    - create_certificate_template(): 创建证书模板
    - generate_certificate(): 生成证书PDF
    - batch_generate_certificates(): 批量生成证书
    - verify_certificate(): 验证证书真伪
    - get_certificate_by_code(): 通过验证码查询证书
"""
from __future__ import annotations

import io
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import qrcode
from qrcode.image.pil import PilImage
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, NotFoundError
from app.models.activity import Activity, AwardRecord
from app.models.certificate import Certificate, CertificateTemplate
from app.models.user import User

logger = logging.getLogger(__name__)

# 尝试导入 WeasyPrint，失败时设置标志
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    logger.warning(f"WeasyPrint 不可用: {e}")


class CertificateService:
    """证书生成与验证服务"""

    @staticmethod
    def create_certificate_template(
        tenant_id: int,
        name: str,
        template_type: str,
        html_content: str,
        css_content: Optional[str],
        created_by: int,
        db: Session,
    ) -> CertificateTemplate:
        """创建证书模板

        :param tenant_id: 租户ID
        :param name: 模板名称
        :param template_type: 模板类型（participation/award）
        :param html_content: HTML模板内容
        :param css_content: CSS样式内容
        :param created_by: 创建人ID
        :param db: 数据库会话
        :return: 模板对象

        Time: O(1), Space: O(1)
        """

        template = CertificateTemplate(
            tenant_id=tenant_id,
            name=name,
            template_type=template_type,
            html_content=html_content,
            css_content=css_content,
            created_by=created_by,
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        logger.info(f"证书模板创建成功: id={template.id}, name={name}")

        return template

    @staticmethod
    def _generate_verification_code() -> str:
        """生成8位验证码

        :return: 验证码字符串

        Time: O(1), Space: O(1)
        """
        return uuid.uuid4().hex[:8].upper()

    @staticmethod
    def _generate_qr_code(verification_url: str, size: int = 200) -> PilImage:
        """生成二维码图片

        :param verification_url: 验证URL
        :param size: 图片尺寸
        :return: PIL图片对象

        Time: O(1), Space: O(1)
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#0b0d12", back_color="white")
        img = img.resize((size, size))

        return img

    @staticmethod
    def generate_certificate(
        activity_id: int,
        student_user_id: int,
        template_id: int,
        tenant_id: int,
        operator_user_id: int,
        db: Session,
        base_url: str = "https://formflow.edu/verify",
    ) -> Certificate:
        """生成证书PDF

        :param activity_id: 活动ID
        :param student_user_id: 学生ID
        :param template_id: 模板ID
        :param tenant_id: 租户ID
        :param operator_user_id: 操作人ID
        :param db: 数据库会话
        :param base_url: 验证基础URL
        :return: 证书对象

        Time: O(1), Space: O(1)
        """

        # 获取活动信息
        activity = db.query(Activity).filter(
            Activity.id == activity_id,
            Activity.tenant_id == tenant_id,
        ).first()

        if not activity:
            raise NotFoundError("活动不存在")

        # 获取学生信息
        student = db.query(User).filter(
            User.id == student_user_id,
            User.tenant_id == tenant_id,
        ).first()

        if not student:
            raise NotFoundError("学生不存在")

        # 获取获奖记录
        award_record = db.query(AwardRecord).filter(
            AwardRecord.activity_id == activity_id,
            AwardRecord.student_user_id == student_user_id,
            AwardRecord.tenant_id == tenant_id,
        ).first()

        # 获取模板
        template = db.query(CertificateTemplate).filter(
            CertificateTemplate.id == template_id,
            CertificateTemplate.tenant_id == tenant_id,
        ).first()

        if not template:
            # 使用默认模板
            template = CertificateService._get_default_template(db)

        # 生成验证码
        verification_code = CertificateService._generate_verification_code()
        verification_url = f"{base_url}/{verification_code}"

        # 生成二维码
        qr_image = CertificateService._generate_qr_code(verification_url)

        # 将二维码转为base64（嵌入HTML）
        import base64
        from io import BytesIO

        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()

        # 渲染HTML
        html_content = template.html_content
        html_content = html_content.replace("{{student_name}}", student.name)
        html_content = html_content.replace("{{activity_name}}", activity.name)
        html_content = html_content.replace("{{award_level}}", award_record.award_level if award_record else "参与")
        html_content = html_content.replace("{{activity_date}}", activity.end_date.strftime("%Y年%m月%d日") if activity.end_date else "")
        html_content = html_content.replace("{{issue_date}}", datetime.now().strftime("%Y年%m月%d日"))
        html_content = html_content.replace("{{verification_code}}", verification_code)
        html_content = html_content.replace("{{qr_code_base64}}", f"data:image/png;base64,{qr_base64}")

        # 生成PDF
        if WEASYPRINT_AVAILABLE:
            html = HTML(string=html_content)
            if template.css_content:
                css = CSS(string=template.css_content)
                pdf_bytes = html.write_pdf(stylesheets=[css])
            else:
                pdf_bytes = html.write_pdf()
        else:
            # WeasyPrint 不可用时，生成占位 PDF（实际项目中应安装 GTK 运行时）
            logger.warning("WeasyPrint unavailable, generating placeholder PDF")
            pdf_bytes = b"%PDF-1.4\n%Placeholder certificate PDF - install GTK3 runtime for real certificates"

        # 保存证书记录
        certificate = Certificate(
            tenant_id=tenant_id,
            template_id=template_id,
            student_user_id=student_user_id,
            activity_id=activity_id,
            award_record_id=award_record.id if award_record else None,
            certificate_type=template.template_type,
            certificate_no=verification_code,
            pdf_content=pdf_bytes,
            verification_code=verification_code,
            verification_url=verification_url,
            issued_by=operator_user_id,
            issued_at=datetime.utcnow(),
        )

        db.add(certificate)
        db.commit()
        db.refresh(certificate)

        logger.info(f"证书生成成功: id={certificate.id}, student={student_user_id}, activity={activity_id}")

        return certificate

    @staticmethod
    def _get_default_template(db: Session) -> CertificateTemplate:
        """获取默认证书模板

        :param db: 数据库会话
        :return: 默认模板

        Time: O(1), Space: O(1)
        """

        default_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: "SimSun", serif;
                    margin: 0;
                    padding: 60px;
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                }
                .certificate {
                    width: 800px;
                    height: 600px;
                    margin: 0 auto;
                    background: white;
                    border: 20px solid #0b0d12;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    position: relative;
                }
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                }
                .title {
                    font-size: 48px;
                    font-weight: bold;
                    color: #0b0d12;
                    letter-spacing: 8px;
                }
                .content {
                    text-align: center;
                    font-size: 24px;
                    line-height: 2;
                    margin: 60px 0;
                }
                .student-name {
                    font-size: 36px;
                    font-weight: bold;
                    color: #ff7a18;
                    border-bottom: 2px solid #ff7a18;
                    padding: 0 20px;
                }
                .footer {
                    position: absolute;
                    bottom: 60px;
                    left: 60px;
                    right: 60px;
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-end;
                }
                .date {
                    font-size: 18px;
                }
                .qr-section {
                    text-align: center;
                }
                .qr-code {
                    width: 120px;
                    height: 120px;
                }
                .verify-code {
                    font-size: 12px;
                    color: #666;
                    margin-top: 8px;
                }
                .stamp {
                    position: absolute;
                    top: 40px;
                    right: 60px;
                    width: 120px;
                    height: 120px;
                    border: 3px solid #ff7a18;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #ff7a18;
                    font-size: 18px;
                    font-weight: bold;
                    transform: rotate(-15deg);
                    opacity: 0.8;
                }
            </style>
        </head>
        <body>
            <div class="certificate">
                <div class="stamp">FormFlow<br>认证</div>
                <div class="header">
                    <div class="title">证 书</div>
                </div>
                <div class="content">
                    <p>兹证明 <span class="student-name">{{student_name}}</span></p>
                    <p>参加 {{activity_name}}</p>
                    <p>获得 <strong>{{award_level}}</strong></p>
                </div>
                <div class="footer">
                    <div class="date">
                        <p>颁发日期：{{issue_date}}</p>
                        <p>证书编号：{{verification_code}}</p>
                    </div>
                    <div class="qr-section">
                        <img class="qr-code" src="{{qr_code_base64}}" alt="验证二维码">
                        <div class="verify-code">扫码验证真伪</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # 创建一个临时模板对象
        template = CertificateTemplate(
            id=0,
            name="default",
            template_type="award",
            html_content=default_html,
            css_content=None,
        )

        return template

    @staticmethod
    def batch_generate_certificates(
        activity_id: int,
        template_id: int,
        tenant_id: int,
        operator_user_id: int,
        db: Session,
    ) -> List[Certificate]:
        """批量生成证书

        :param activity_id: 活动ID
        :param template_id: 模板ID
        :param tenant_id: 租户ID
        :param operator_user_id: 操作人ID
        :param db: 数据库会话
        :return: 证书列表

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

        certificates = []
        for record in award_records:
            try:
                cert = CertificateService.generate_certificate(
                    activity_id=activity_id,
                    student_user_id=record.student_user_id,
                    template_id=template_id,
                    tenant_id=tenant_id,
                    operator_user_id=operator_user_id,
                    db=db,
                )
                certificates.append(cert)
            except Exception as e:
                logger.error(f"证书生成失败: student={record.student_user_id}, error={e}")
                continue

        logger.info(f"批量证书生成完成: activity={activity_id}, count={len(certificates)}")

        return certificates

    @staticmethod
    def get_certificate_by_code(
        verification_code: str,
        db: Session,
    ) -> Optional[Certificate]:
        """通过验证码查询证书

        :param verification_code: 验证码
        :param db: 数据库会话
        :return: 证书对象或None

        Time: O(1), Space: O(1)
        """

        return db.query(Certificate).filter(
            Certificate.verification_code == verification_code.upper(),
        ).first()

    @staticmethod
    def verify_certificate(
        verification_code: str,
        db: Session,
    ) -> Dict:
        """验证证书真伪

        :param verification_code: 验证码
        :param db: 数据库会话
        :return: 验证结果

        Time: O(1), Space: O(1)
        """

        certificate = CertificateService.get_certificate_by_code(verification_code, db)

        if not certificate:
            return {
                "valid": False,
                "message": "证书不存在或验证码错误",
            }

        if certificate.status != "active":
            return {
                "valid": False,
                "message": f"证书状态异常：{certificate.status}",
            }

        # 获取相关信息
        student = db.query(User).filter(User.id == certificate.student_user_id).first()
        activity = db.query(Activity).filter(Activity.id == certificate.activity_id).first()

        return {
            "valid": True,
            "message": "证书真实有效",
            "certificate": {
                "certificate_no": certificate.certificate_no,
                "certificate_type": certificate.certificate_type,
                "issued_at": certificate.issued_at.isoformat() if certificate.issued_at else None,
            },
            "student": {
                "id": student.id if student else None,
                "name": student.name if student else "未知",
            },
            "activity": {
                "id": activity.id if activity else None,
                "name": activity.name if activity else "未知",
            },
        }

    @staticmethod
    def get_student_certificates(
        student_user_id: int,
        tenant_id: int,
        db: Session,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Certificate]:
        """获取学生证书列表

        :param student_user_id: 学生ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :param page: 页码
        :param page_size: 每页数量
        :return: 证书列表

        Time: O(N), Space: O(N)
        """

        certificates = db.query(Certificate).filter(
            Certificate.student_user_id == student_user_id,
            Certificate.tenant_id == tenant_id,
            Certificate.status == "active",
        ).order_by(
            desc(Certificate.issued_at)
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return certificates
