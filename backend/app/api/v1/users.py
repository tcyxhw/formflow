# app/api/v1/users.py
"""
用户管理API
用户的增删改查等操作
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.core.database import get_db
from app.core.response import success_response, paginated_response
from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
    PasswordChange
)
from app.schemas.base import PaginationParams
from app.models.user import User, UserProfile as UserProfileModel
from app.api.deps import (
    get_current_user,
    PermissionChecker,
    RequireAdmin,
    get_current_tenant_id
)
from app.core.security import hash_password, verify_password
from app.utils.audit import audit_log
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", summary="获取用户列表")
async def get_users(
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页大小"),
        keyword: Optional[str] = Query(None, description="搜索关键词"),
        department_id: Optional[int] = Query(None, description="部门ID"),
        is_active: Optional[bool] = Query(None, description="是否启用"),
        current_user: User = Depends(RequireAdmin),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取用户列表（需要管理员权限）

    查询参数:
    - page: 页码
    - size: 每页大小
    - keyword: 搜索关键词（账号/姓名/邮箱/手机号）
    - department_id: 部门ID筛选
    - is_active: 启用状态筛选

    返回值:
    - items: 用户列表
    - total: 总数量
    - page: 当前页码
    - size: 每页大小
    - pages: 总页数
    """
    # 构建查询
    query = db.query(User).filter(User.tenant_id == tenant_id)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                User.account.contains(keyword),
                User.name.contains(keyword),
                User.email.contains(keyword),
                User.phone.contains(keyword)
            )
        )

    # 部门筛选
    if department_id is not None:
        query = query.filter(User.department_id == department_id)

    # 状态筛选
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # 获取总数
    total = query.count()

    # 分页
    pagination = PaginationParams(page=page, size=size)
    users = query.offset(pagination.offset).limit(size).all()

    # 构造响应数据
    items = []
    for user in users:
        user_dict = user.to_dict()
        # 添加部门名称
        if user.department:
            user_dict["department_name"] = user.department.name
        items.append(user_dict)

    return paginated_response(
        items=items,
        total=total,
        page=page,
        size=size
    )


@router.get("/list", summary="获取用户列表（简化版）")
async def list_users(
        keyword: Optional[str] = Query(None, description="搜索关键词"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页大小"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取用户列表（简化版，用于选择器）

    查询参数:
    - keyword: 搜索关键词（账号/姓名/邮箱/手机号）
    - page: 页码
    - size: 每页大小

    返回值:
    - items: 用户列表 [{ id, name, account, email }]
    - total: 总数量
    """
    # 构建查询
    query = db.query(User).filter(User.tenant_id == tenant_id, User.is_active == True)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                User.account.contains(keyword),
                User.name.contains(keyword),
                User.email.contains(keyword),
                User.phone.contains(keyword)
            )
        )

    # 获取总数
    total = query.count()

    # 分页
    pagination = PaginationParams(page=page, size=size)
    users = query.offset(pagination.offset).limit(size).all()

    # 构造简化响应数据
    items = [
        {
            "id": user.id,
            "name": user.name,
            "account": user.account,
            "email": user.email
        }
        for user in users
    ]

    return success_response(data={
        "items": items,
        "total": total
    })


@router.get("/{user_id}", summary="获取用户详情")
async def get_user(
        user_id: int = Path(..., description="用户ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取用户详情

    路径参数:
    - user_id: 用户ID

    返回值:
    - 用户完整信息，包括扩展信息、角色、岗位等
    """
    # 权限检查：管理员或查看自己的信息
    if user_id != current_user.id:
        # 检查是否是管理员
        admin_roles = ["系统管理员", "租户管理员"]
        user_roles = [r.role.name for r in current_user.roles if r.role]
        if not any(role in admin_roles for role in user_roles):
            raise AuthorizationError("无权查看其他用户信息")

    # 查询用户
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()

    if not user:
        raise NotFoundError("用户不存在")

    # 构造响应数据
    user_data = user.to_dict()

    # 添加部门信息
    if user.department:
        user_data["department"] = {
            "id": user.department.id,
            "name": user.department.name
        }

    # 添加扩展信息
    if user.profile:
        user_data["profile"] = user.profile.to_dict()

    # 添加角色信息
    user_data["roles"] = [
        {"id": ur.role.id, "name": ur.role.name}
        for ur in user.roles if ur.role
    ]

    # 添加岗位信息
    user_data["positions"] = [
        {
            "id": up.position.id,
            "name": up.position.name,
            "effective_from": up.effective_from,
            "effective_to": up.effective_to
        }
        for up in user.positions if up.position
    ]

    return success_response(data=user_data)


@router.post("", summary="创建用户")
@audit_log(action="create_user", resource_type="user")
async def create_user(
        user_data: UserCreate,
        current_user: User = Depends(RequireAdmin),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    创建新用户（需要管理员权限）

    请求体:
    - account: 账号
    - password: 密码
    - name: 姓名
    - email: 邮箱（可选）
    - phone: 手机号（可选）
    - department_id: 部门ID（可选）

    返回值:
    - 创建的用户信息
    """
    # 检查账号是否已存在
    existing_user = db.query(User).filter(
        User.account == user_data.account,
        User.tenant_id == tenant_id
    ).first()

    if existing_user:
        raise ValidationError("账号已存在")

    # 检查邮箱唯一性
    if user_data.email:
        email_user = db.query(User).filter(
            User.email == user_data.email,
            User.tenant_id == tenant_id
        ).first()
        if email_user:
            raise ValidationError("邮箱已被使用")

    # 检查手机号唯一性
    if user_data.phone:
        phone_user = db.query(User).filter(
            User.phone == user_data.phone,
            User.tenant_id == tenant_id
        ).first()
        if phone_user:
            raise ValidationError("手机号已被使用")

    # 创建用户
    new_user = User(
        tenant_id=tenant_id,
        account=user_data.account,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        department_id=user_data.department_id,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"创建用户成功 - ID: {new_user.id}, 操作人: {current_user.id}")

    return success_response(
        data=new_user.to_dict(),
        message="用户创建成功"
    )


@router.put("/{user_id}", summary="更新用户信息")
@audit_log(
    action="update_user",
    resource_type="user",
    get_resource_id=lambda *args, **kwargs: kwargs.get("user_id")
)
async def update_user(
        user_id: int = Path(..., description="用户ID"),
        user_data: UserUpdate = ...,
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    更新用户信息

    路径参数:
    - user_id: 用户ID

    请求体:
    - name: 姓名
    - email: 邮箱
    - phone: 手机号
    - department_id: 部门ID
    - is_active: 是否启用（仅管理员可修改）

    返回值:
    - 更新后的用户信息
    """
    # 权限检查
    if user_id != current_user.id:
        # 只有管理员可以修改其他用户
        admin_roles = ["系统管理员", "租户管理员"]
        user_roles = [r.role.name for r in current_user.roles if r.role]
        if not any(role in admin_roles for role in user_roles):
            raise AuthorizationError("无权修改其他用户信息")
    else:
        # 普通用户不能修改自己的启用状态
        if user_data.is_active is not None:
            raise AuthorizationError("无权修改启用状态")

    # 查询用户
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()

    if not user:
        raise NotFoundError("用户不存在")

    # 更新字段
    update_dict = user_data.model_dump(exclude_unset=True)

    # 检查邮箱唯一性
    if "email" in update_dict and update_dict["email"] != user.email:
        email_user = db.query(User).filter(
            User.email == update_dict["email"],
            User.tenant_id == tenant_id,
            User.id != user_id
        ).first()
        if email_user:
            raise ValidationError("邮箱已被使用")

    # 检查手机号唯一性
    if "phone" in update_dict and update_dict["phone"] != user.phone:
        phone_user = db.query(User).filter(
            User.phone == update_dict["phone"],
            User.tenant_id == tenant_id,
            User.id != user_id
        ).first()
        if phone_user:
            raise ValidationError("手机号已被使用")

    # 应用更新
    for key, value in update_dict.items():
        setattr(user, key, value)

    # 如果更新了 avatar_url，需要绑定附件到用户
    if "avatar_url" in update_dict:
        from app.services.attachment_service import AttachmentService
        import re
        
        avatar_url = update_dict["avatar_url"]
        # 从 avatar_url 中提取附件ID
        if avatar_url and "/attachments/" in avatar_url and "/download" in avatar_url:
            match = re.search(r'/attachments/(\d+)/download', avatar_url)
            if match:
                attachment_id = int(match.group(1))
                try:
                    # 绑定附件到用户
                    AttachmentService.bind_attachment(
                        attachment_id=attachment_id,
                        owner_type="user",
                        owner_id=user_id,
                        tenant_id=tenant_id,
                        db=db
                    )
                    logger.info(f"头像附件绑定成功: attachment_id={attachment_id}, user_id={user_id}")
                except Exception as e:
                    logger.warning(f"头像附件绑定失败: {e}")

    db.commit()
    db.refresh(user)

    logger.info(f"更新用户成功 - ID: {user_id}, 操作人: {current_user.id}")

    return success_response(
        data=user.to_dict(),
        message="用户信息更新成功"
    )


@router.delete("/{user_id}", summary="删除用户")
@audit_log(
    action="delete_user",
    resource_type="user",
    get_resource_id=lambda *args, **kwargs: kwargs.get("user_id")
)
async def delete_user(
        user_id: int = Path(..., description="用户ID"),
        current_user: User = Depends(RequireAdmin),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    删除用户（需要管理员权限）

    路径参数:
    - user_id: 用户ID

    返回值:
    - success: 是否成功
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise ValidationError("不能删除自己")

    # 查询用户
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()

    if not user:
        raise NotFoundError("用户不存在")

    # 软删除（禁用用户）
    user.is_active = False
    db.commit()

    logger.info(f"删除用户成功 - ID: {user_id}, 操作人: {current_user.id}")

    return success_response(
        data={"success": True},
        message="用户删除成功"
    )


@router.post("/{user_id}/change-password", summary="修改密码")
async def change_password(
        user_id: int = Path(..., description="用户ID"),
        password_data: PasswordChange = ...,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    修改用户密码

    路径参数:
    - user_id: 用户ID

    请求体:
    - old_password: 原密码
    - new_password: 新密码

    返回值:
    - success: 是否成功
    """
    # 只能修改自己的密码
    if user_id != current_user.id:
        raise AuthorizationError("只能修改自己的密码")

    # 验证原密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise ValidationError("原密码错误")

    # 更新密码
    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()

    # 使所有刷新令牌失效（强制重新登录）
    from app.models.notification import RefreshToken
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.active == True
    ).update({"active": False})
    db.commit()

    logger.info(f"修改密码成功 - 用户ID: {user_id}")

    return success_response(
        data={"success": True},
        message="密码修改成功，请重新登录"
    )


@router.put("/{user_id}/profile", summary="更新用户扩展信息")
async def update_user_profile(
        user_id: int = Path(..., description="用户ID"),
        profile_data: UserProfile = ...,
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    更新用户扩展信息

    路径参数:
    - user_id: 用户ID

    请求体:
    - identity_no: 学号/工号
    - identity_type: 身份类型
    - entry_year: 入学/入职年份
    - 其他扩展字段...

    返回值:
    - 更新后的扩展信息
    """
    # 权限检查
    if user_id != current_user.id:
        admin_roles = ["系统管理员", "租户管理员"]
        user_roles = [r.role.name for r in current_user.roles if r.role]
        if not any(role in admin_roles for role in user_roles):
            raise AuthorizationError("无权修改其他用户信息")

    # 查询用户
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()

    if not user:
        raise NotFoundError("用户不存在")

    # 查询或创建扩展信息
    profile = db.query(UserProfileModel).filter(
        UserProfileModel.user_id == user_id
    ).first()

    if not profile:
        profile = UserProfileModel(user_id=user_id)
        db.add(profile)

    # 更新字段
    update_dict = profile_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    return success_response(
        data=profile.to_dict(),
        message="扩展信息更新成功"
    )


@router.get("/me/stats", summary="获取当前用户统计信息")
async def get_current_user_stats(
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取当前用户的统计信息

    返回值:
    - forms_created: 创建的表单数量
    - forms_submitted: 填写的表单数量
    - tasks_pending: 待办审批数量
    - tasks_completed: 已处理审批数量
    """
    from app.models.form import Form, Submission
    from app.models.workflow import Task

    user_id = current_user.id

    # 创建的表单数量
    forms_created = db.query(func.count(Form.id)).filter(
        Form.tenant_id == tenant_id,
        Form.owner_user_id == user_id
    ).scalar() or 0

    # 填写的表单数量（提交记录）
    forms_submitted = db.query(func.count(Submission.id)).filter(
        Submission.tenant_id == tenant_id,
        Submission.submitter_user_id == user_id
    ).scalar() or 0

    # 待办审批数量（status='open' 或 'claimed'）
    tasks_pending = db.query(func.count(Task.id)).filter(
        Task.tenant_id == tenant_id,
        Task.assignee_user_id == user_id,
        Task.status.in_(["open", "claimed"])
    ).scalar() or 0

    # 已处理审批数量（status='completed'）
    tasks_completed = db.query(func.count(Task.id)).filter(
        Task.tenant_id == tenant_id,
        Task.assignee_user_id == user_id,
        Task.status == "completed"
    ).scalar() or 0

    return success_response(
        data={
            "forms_created": forms_created,
            "forms_submitted": forms_submitted,
            "tasks_pending": tasks_pending,
            "tasks_completed": tasks_completed
        }
    )


@router.get("/me/avatar", summary="获取当前用户头像")
async def get_current_user_avatar(
        request: Request,
        token: Optional[str] = Query(None, description="访问令牌（用于img标签）"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取当前用户的头像文件

    支持两种认证方式：
    1. Authorization header（标准方式）
    2. URL 参数 token（用于 img src）

    返回值:
    - 头像图片文件流
    """
    from fastapi.responses import StreamingResponse
    from app.services.storage_service import StorageService
    from app.core.security import decode_token

    if not current_user.avatar_url:
        raise NotFoundError("用户未设置头像")

    avatar_url = current_user.avatar_url

    storage_path = None
    # 处理附件URL格式（支持完整URL和相对路径）
    if "/attachments/" in avatar_url and "/download" in avatar_url:
        import re
        match = re.search(r'/attachments/(\d+)/download', avatar_url)
        if match:
            from app.models.form import Attachment
            attachment_id = int(match.group(1))
            attachment = db.query(Attachment).filter(
                Attachment.id == attachment_id,
                Attachment.tenant_id == tenant_id
            ).first()
            if attachment:
                storage_path = attachment.storage_path
    elif not avatar_url.startswith("http://") and not avatar_url.startswith("https://"):
        # 不是完整URL，假设是存储路径
        storage_path = avatar_url

    if not storage_path:
        raise NotFoundError("头像文件路径无效")

    try:
        file_data = StorageService.get_file_data(storage_path)
        content_type = "image/jpeg"
        if storage_path.lower().endswith(".png"):
            content_type = "image/png"
        elif storage_path.lower().endswith(".gif"):
            content_type = "image/gif"
        elif storage_path.lower().endswith(".webp"):
            content_type = "image/webp"

        return StreamingResponse(
            iter([file_data]),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": f'inline; filename="avatar_{current_user.id}"'
            }
        )
    except Exception as e:
        logger.error(f"获取头像失败: {e}")
        raise NotFoundError("头像文件不存在")
