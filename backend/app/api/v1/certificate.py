"""
模块用途: 证书管理API路由
依赖配置: FastAPI, SQLAlchemy
数据流向: HTTP请求 -> CertificateService -> 数据库
路由清单:
    - POST   /certificate-templates      创建证书模板
    - GET    /certificate-templates      模板列表
    - POST   /certificates/generate      生成证书
    - GET    /certificates               证书列表
    - GET    /certificates/:id/download  下载证书PDF
    - GET    /certificates/verify/:code  验证证书（公开）
    - GET    /certificates/student/:id   学生证书列表
"""
from typing import Optional
from fastapi import APIRouter, Depends, Path, Body, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_tenant_id
from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.exceptions import NotFoundError, BusinessError
from app.models.user import User
from app.schemas.base import ResponseSchema
from app.services.certificate_service import CertificateService

router = APIRouter()


@router.post("/certificate-templates", response_model=ResponseSchema, summary="创建证书模板")
async def create_template(
    name: str = Body(..., description="模板名称"),
    template_type: str = Body(..., description="模板类型：participation/award"),
    html_content: str = Body(..., description="HTML模板内容"),
    css_content: Optional[str] = Body(None, description="CSS样式"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """创建证书模板"""
    try:
        template = CertificateService.create_certificate_template(
            tenant_id=tenant_id,
            name=name,
            template_type=template_type,
            html_content=html_content,
            css_content=css_content,
            created_by=current_user.id,
            db=db,
        )
        return success_response(
            data={"id": template.id, "name": template.name},
            message="模板创建成功"
        )
    except Exception as e:
        return error_response(str(e), 5001)


@router.get("/certificate-templates", response_model=ResponseSchema, summary="证书模板列表")
async def list_templates(
    template_type: Optional[str] = Query(None, description="类型筛选"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """查询证书模板列表"""
    try:
        # TODO: 实现模板列表查询
        return success_response(data={"items": [], "total": 0})
    except Exception as e:
        return error_response(str(e), 5001)


@router.post("/certificates/generate", response_model=ResponseSchema, summary="生成证书")
async def generate_certificate(
    activity_id: int = Body(..., description="活动ID"),
    student_user_id: int = Body(..., description="学生ID"),
    template_id: int = Body(..., description="模板ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """为单个学生生成证书"""
    try:
        certificate = CertificateService.generate_certificate(
            activity_id=activity_id,
            student_user_id=student_user_id,
            template_id=template_id,
            tenant_id=tenant_id,
            operator_user_id=current_user.id,
            db=db,
        )
        return success_response(
            data={
                "id": certificate.id,
                "certificate_no": certificate.certificate_no,
                "verification_code": certificate.verification_code,
            },
            message="证书生成成功"
        )
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except BusinessError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(str(e), 5001)


@router.post("/activities/{activity_id}/certificates/batch", response_model=ResponseSchema, summary="批量生成证书")
async def batch_generate_certificates(
    activity_id: int = Path(..., description="活动ID"),
    template_id: int = Body(..., description="模板ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """为活动所有获奖学生批量生成证书"""
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
            message=f"批量生成成功，共{len(certificates)}份证书"
        )
    except BusinessError as e:
        return error_response(str(e), 4001)
    except Exception as e:
        return error_response(str(e), 5001)


@router.get("/certificates", response_model=ResponseSchema, summary="证书列表")
async def list_certificates(
    activity_id: Optional[int] = Query(None, description="活动ID筛选"),
    student_id: Optional[int] = Query(None, description="学生ID筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """查询证书列表（管理员）"""
    try:
        # TODO: 实现证书列表查询
        return success_response(data={"items": [], "total": 0})
    except Exception as e:
        return error_response(str(e), 5001)


@router.get("/certificates/{certificate_id}/download", summary="下载证书PDF")
async def download_certificate(
    certificate_id: int = Path(..., description="证书ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """下载证书PDF文件"""
    try:
        from fastapi.responses import Response
        
        certificate = CertificateService.get_certificate_by_code("", db)  # TODO: 改为按ID查询
        if not certificate:
            raise NotFoundError("证书不存在")
        
        return Response(
            content=certificate.pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=certificate_{certificate.certificate_no}.pdf"
            }
        )
    except NotFoundError as e:
        return error_response(str(e), 4041)
    except Exception as e:
        return error_response(str(e), 5001)


@router.get("/certificates/student/{student_id}", response_model=ResponseSchema, summary="学生证书列表")
async def get_student_certificates(
    student_id: int = Path(..., description="学生ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """获取学生的所有证书"""
    try:
        certificates = CertificateService.get_student_certificates(
            student_user_id=student_id,
            tenant_id=tenant_id,
            db=db,
        )
        return success_response(
            data=[
                {
                    "id": c.id,
                    "certificate_no": c.certificate_no,
                    "certificate_type": c.certificate_type,
                    "activity_id": c.activity_id,
                    "issued_at": c.issued_at.isoformat() if c.issued_at else None,
                    "status": c.status,
                }
                for c in certificates
            ]
        )
    except Exception as e:
        return error_response(str(e), 5001)


@router.get("/verify/{verification_code}", response_model=ResponseSchema, summary="验证证书（公开）")
async def verify_certificate(
    verification_code: str = Path(..., description="验证码"),
    db: Session = Depends(get_db),
):
    """公开验证证书真伪（无需登录）"""
    try:
        result = CertificateService.verify_certificate(verification_code, db)
        return success_response(data=result)
    except Exception as e:
        return error_response(str(e), 5001)
