# app/api/v1/__init__.py
"""
API v1 路由聚合
"""
from fastapi import APIRouter
from app.api.v1 import (
    auth,
    users,
    admin,
    forms,
    submissions,
    attachments,
    ai,
    approvals,
    form_permissions,
    flows,
    activity,
    certificate,
    categories,
    dashboard,
)

from app.config import settings

router = APIRouter()

# 注册各模块路由
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(users.router, prefix="/users", tags=["用户"])
router.include_router(admin.router, prefix="/admin", tags=["管理员"])
router.include_router(forms.router, prefix="/forms", tags=["表单"])
router.include_router(categories.router, prefix="/categories", tags=["表单分类"])
router.include_router(form_permissions.router, prefix="", tags=["表单权限"])
router.include_router(flows.router, prefix="/flows", tags=["流程配置"])

# 提交相关
router.include_router(
    submissions.router,
    prefix="/submissions",
    tags=["提交管理"]
)

# 附件相关
router.include_router(
    attachments.router,
    prefix="/attachments",
    tags=["附件管理"]
)

router.include_router(
    ai.router,
    prefix=f"/ai",
    tags=["AI"]
)

# 审批相关
router.include_router(
    approvals.router,
    prefix="/approvals",
    tags=["审批"]
)

# 活动相关
router.include_router(
    activity.router,
    prefix="/activities",
    tags=["活动管理"]
)

# 证书相关
router.include_router(
    certificate.router,
    prefix="",
    tags=["证书管理"]
)

# 首页统计
router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["首页统计"]
)