# app/services/submission_service.py
"""
提交业务逻辑服务模块

【模块用途】
- 处理表单提交的核心业务逻辑（创建、更新、删除、查询）
- 提供提交数据验证和计算字段功能
- 管理提交附件的绑定和解绑
- 提供提交统计分析功能
- 构建表单版本快照用于归档

【依赖说明】
- 数据库: PostgreSQL (依赖 JSONB 字段类型)
- ORM: SQLAlchemy (用于数据库操作)
- 关联服务: FormService (表单查询), FormulaService (公式计算), AttachmentService (附件管理)

【业务流程】
1. 创建提交: 验证表单 -> 验证数据 -> 计算字段 -> 保存 -> 绑定附件 -> 删除草稿
2. 更新提交: 权限检查 -> 验证数据 -> 计算字段 -> 更新 -> 重新绑定附件
3. 删除提交: 权限检查 -> 软删除（设置状态为 deleted）
4. 查询列表: 构建查询条件 -> 分页查询 -> 返回数据和总数

【核心功能清单】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
函数名                       用途                    返回值类型
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
create_submission           创建提交记录            Submission
update_submission           更新提交记录            Submission
delete_submission           软删除提交记录          int (form_id)
get_submission_by_id        查询提交详情            Submission
list_submissions            分页查询提交列表        Tuple[List[Submission], int]
get_submission_statistics   获取提交统计数据        Dict[str, Any]
validate_submission_data    验证提交数据            Tuple[bool, List[str]]
calculate_fields            计算所有计算字段        Dict[str, Any]
build_snapshot              构建提交快照            Dict[str, Any]
_bind_attachments           绑定附件到提交          None
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【数据验证规则】
1. 必填字段验证: required=True 的字段不能为空
2. 数字范围验证: number 类型字段的 min/max 限制
3. 字段格式验证: 根据字段类型验证数据格式
4. 逻辑规则验证: 根据 logic_json 验证显示/隐藏逻辑（待实现）

【计算字段处理】
1. 按依赖关系排序计算字段
2. 使用 FormulaService 计算公式
3. 计算失败时设置为 null 并记录日志

【性能优化】
- 使用 JSONB 字段存储动态表单数据（支持索引）
- 批量绑定附件，减少数据库交互
- 统计查询使用聚合函数，避免加载全量数据
- 分页查询使用 offset/limit，控制内存占用

【版本信息】
- 创建时间: 2025-01-10
- 最后更新: 2025-01-10
- 作者: System
- 版本: v1.0.0
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, String
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import logging

# Models
from app.models.form import Submission, Form, FormVersion, Attachment
from app.models.workflow import ProcessInstance

# Schemas
from app.schemas.submission_schemas import (
    SubmissionCreateRequest,
    SubmissionUpdateRequest,
    SubmissionQueryRequest
)

# Services
from app.services.form_service import FormService
from app.services.formula_service import FormulaService
from app.services.form_permission_service import FormPermissionService
from app.services.process_service import ProcessService

# Exceptions
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    BusinessError,
    AuthorizationError
)
from app.schemas.form_permission_schemas import PermissionType

logger = logging.getLogger(__name__)


# ============================================================
# 枚举定义
# ============================================================

class SubmissionStatus(str, Enum):
    """
    提交状态枚举

    :cvar SUBMITTED: 已提交
    :cvar APPROVED: 已批准
    :cvar REJECTED: 已拒绝
    :cvar DELETED: 已删除
    """
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELETED = "deleted"


# ============================================================
# 提交服务类
# ============================================================

class SubmissionService:
    """
    提交业务逻辑服务类

    提供表单提交的完整生命周期管理，包括：
    - 创建、更新、删除、查询提交记录
    - 数据验证和计算字段处理
    - 附件管理和快照构建
    - 统计分析功能
    """

    @staticmethod
    def create_submission(
            request: SubmissionCreateRequest,
            tenant_id: int,
            user_id: Optional[int],
            ip_address: str,
            device_info: dict,
            db: Session
    ) -> Submission:
        """
        创建新的表单提交记录

        【业务流程】
        1. 验证表单是否存在且已发布
        2. 权限与状态校验
        3. 检查截止时间
        4. 获取表单当前版本
        5. 验证提交数据的完整性和格式
        6. 计算所有计算字段
        7. 构建版本快照（用于归档）
        8. 保存提交记录到数据库
        9. 绑定上传的附件
        10. 删除对应的草稿记录
        11. 触发流程

        【验证规则】
        - 表单必须是已发布状态
        - 未超过提交截止时间
        - 必填字段不能为空
        - 数字字段符合范围限制

        :param request: 提交创建请求对象（包含 form_id, data, duration, source）
        :param tenant_id: 租户ID（用于数据隔离）
        :param user_id: 提交用户ID（匿名提交时为 None）
        :param ip_address: 提交来源IP地址
        :param device_info: 设备信息字典（包含 user_agent, platform 等）
        :param db: 数据库会话对象
        :return: 创建成功的 Submission 对象
        :raises BusinessError: 表单未发布、已过期、配置不完整时抛出
        :raises ValidationError: 数据验证失败时抛出
        :raises Exception: 数据库操作失败时抛出

        【示例】
        >>> submission = SubmissionService.create_submission(
        ...     request=SubmissionCreateRequest(
        ...         form_id=1,
        ...         data={"name": "张三", "age": 25},
        ...         duration=120,
        ...         source="web"
        ...     ),
        ...     tenant_id=1,
        ...     user_id=100,
        ...     ip_address="127.0.0.1",
        ...     device_info={"user_agent": "Chrome/120.0"},
        ...     db=db
        ... )
        """
        logger.info(
            f"开始创建提交: form_id={request.form_id}, user_id={user_id}, "
            f"tenant_id={tenant_id}, ip={ip_address}"
        )

        # 1. 获取表单并验证
        form = FormService.get_form_by_id(request.form_id, tenant_id, db)
        logger.debug(f"获取表单成功: form_id={form.id}, status={form.status}")

        # 2. 权限与状态校验
        SubmissionService._ensure_fill_permission(form, tenant_id, user_id, db)
        if form.status != "published":
            logger.warning(f"表单未发布，无法提交: form_id={form.id}, status={form.status}")
            raise BusinessError("表单未发布，无法提交")

        # 3. 检查截止时间
        if form.submit_deadline and datetime.now() > form.submit_deadline:
            logger.warning(f"已超过提交截止时间: form_id={form.id}, deadline={form.submit_deadline}")
            raise BusinessError("已超过提交截止时间")

        # 4. 获取当前版本
        current_version = db.query(FormVersion).filter(
            FormVersion.form_id == request.form_id,
            FormVersion.version > 0
        ).order_by(FormVersion.version.desc()).first()

        if not current_version:
            logger.error(f"表单配置不完整，缺少版本: form_id={request.form_id}")
            raise BusinessError("表单配置不完整")

        logger.debug(f"获取表单版本: version_id={current_version.id}, version={current_version.version}")

        # 5. 验证数据
        is_valid, errors = SubmissionService.validate_submission_data(
            request.data,
            current_version.schema_json,
            current_version.logic_json
        )

        if not is_valid:
            logger.warning(f"数据验证失败: errors={errors}")
            raise ValidationError(f"数据验证失败: {'; '.join(errors)}")

        logger.debug("数据验证通过")

        # 6. 计算字段
        data_with_calculated = SubmissionService.calculate_fields(
            request.data,
            current_version.schema_json
        )
        logger.debug(f"计算字段完成: fields_count={len(data_with_calculated)}")

        # 7. 构建快照
        snapshot = SubmissionService.build_snapshot(current_version)
        logger.debug("快照构建完成")

        # 8. 创建提交记录
        submission = Submission(
            tenant_id=tenant_id,
            form_id=request.form_id,
            form_version_id=current_version.id,
            submitter_user_id=user_id,
            data_jsonb=data_with_calculated,
            snapshot_json=snapshot,
            status=SubmissionStatus.SUBMITTED.value,
            duration=request.duration,
            source=request.source,
            ip_address=ip_address,
            device_info=device_info
        )

        db.add(submission)
        db.flush()  # 获取 submission.id

        logger.info(f"提交记录已创建: submission_id={submission.id}")

        # 9. 绑定附件
        try:
            SubmissionService._bind_attachments(
                submission.id,
                data_with_calculated,
                current_version.schema_json,
                tenant_id,
                db
            )
            logger.debug(f"附件绑定完成: submission_id={submission.id}")
        except Exception as e:
            logger.error(f"绑定附件失败: submission_id={submission.id}, error={e}")
            # 附件绑定失败不影响主流程

        # 10. 删除草稿
        if user_id:
            try:
                from app.services.draft_service import DraftService
                DraftService.delete_draft_by_user_form(user_id, request.form_id, tenant_id, db)
                logger.debug(f"草稿已删除: user_id={user_id}, form_id={request.form_id}")
            except Exception as e:
                logger.warning(f"删除草稿失败: {e}")
                # 草稿删除失败不影响主流程

        # 11. 触发流程
        SubmissionService._trigger_workflow(
            form=form,
            form_version=current_version,
            submission=submission,
            tenant_id=tenant_id,
            db=db,
        )

        db.commit()
        db.refresh(submission)

        logger.info(
            f"提交创建成功: submission_id={submission.id}, form_id={request.form_id}, "
            f"user_id={user_id}, duration={request.duration}s"
        )
        return submission

    @staticmethod
    def _ensure_fill_permission(form: Form, tenant_id: int, user_id: Optional[int], db: Session) -> None:
        """检查用户是否具备填报权限。

        Time: O(1), Space: O(1)
        """

        if user_id:
            FormPermissionService.ensure_permission(
                form_id=form.id,
                tenant_id=tenant_id,
                permission=PermissionType.FILL,
                user_id=user_id,
                db=db,
            )
            return

        if form.access_mode != "public":
            raise AuthorizationError("匿名用户无权提交该表单")

    @staticmethod
    def _trigger_workflow(
        form: Form,
        form_version: FormVersion,
        submission: Submission,
        tenant_id: int,
        db: Session,
    ) -> None:
        """创建流程实例并写入首个任务。"""

        try:
            ProcessService.start_process(
                form_id=form.id,
                form_version_id=form_version.id,
                submission_id=submission.id,
                tenant_id=tenant_id,
                db=db,
            )
        except BusinessError as exc:
            logger.warning(
                "流程未配置或异常，跳过自动审批: form_id=%s, error=%s",
                form.id,
                exc,
            )

    @staticmethod
    def update_submission(
            submission_id: int,
            request: SubmissionUpdateRequest,
            tenant_id: int,
            user_id: int,
            db: Session
    ) -> Submission:
        """
        更新已存在的提交记录

        【业务流程】
        1. 查询提交记录是否存在
        2. 验证用户权限（只能编辑自己的提交）
        3. 检查是否有关联的任务被认领（被认领后不允许编辑）
        4. 验证更新的数据
        5. 计算所有计算字段
        6. 更新提交记录
        7. 重新绑定附件

        【权限规则】
        - 只有提交者本人可以编辑
        - 如果提交记录关联的任务已被审批人认领，则不允许编辑

        :param submission_id: 要更新的提交记录ID
        :param request: 提交更新请求对象（包含 data）
        :param tenant_id: 租户ID
        :param user_id: 当前操作用户ID
        :param db: 数据库会话对象
        :return: 更新后的 Submission 对象
        :raises NotFoundError: 提交记录不存在时抛出
        :raises AuthorizationError: 无权限编辑时抛出
        :raises BusinessError: 任务已被认领时抛出
        :raises ValidationError: 数据验证失败时抛出
        """
        logger.info(f"开始更新提交: submission_id={submission_id}, user_id={user_id}")

        # 1. 查询提交记录
        submission = SubmissionService.get_submission_by_id(submission_id, tenant_id, db)
        logger.debug(f"获取提交记录: status={submission.status}, submitter={submission.submitter_user_id}")

        # 2. 检查权限
        if submission.submitter_user_id != user_id:
            logger.warning(
                f"权限不足: submission_id={submission_id}, "
                f"owner={submission.submitter_user_id}, user={user_id}"
            )
            raise AuthorizationError("只能编辑自己的提交")

        # 3. 检查是否有关联的任务被认领
        from app.models.workflow import ProcessInstance, Task
        process_instance = db.query(ProcessInstance).filter(
            ProcessInstance.submission_id == submission_id,
            ProcessInstance.tenant_id == tenant_id,
            ProcessInstance.state == "running"
        ).first()

        if process_instance:
            # 检查是否有任务被认领
            claimed_task = db.query(Task).filter(
                Task.process_instance_id == process_instance.id,
                Task.claimed_by.isnot(None)
            ).first()

            if claimed_task:
                logger.warning(f"提交记录关联的任务已被认领: submission_id={submission_id}, task_id={claimed_task.id}")
                raise BusinessError("该提交记录已被审批人认领，不允许再编辑")

        # 4. 获取表单和版本
        form = FormService.get_form_by_id(submission.form_id, tenant_id, db)
        version = db.query(FormVersion).filter(
            FormVersion.id == submission.form_version_id
        ).first()

        if not version:
            logger.error(f"表单版本不存在: version_id={submission.form_version_id}")
            raise BusinessError("表单版本不存在")

        # 5. 验证数据
        is_valid, errors = SubmissionService.validate_submission_data(
            request.data,
            version.schema_json,
            version.logic_json
        )

        if not is_valid:
            logger.warning(f"数据验证失败: errors={errors}")
            raise ValidationError(f"数据验证失败: {'; '.join(errors)}")

        logger.debug("数据验证通过")

        # 8. 计算字段
        data_with_calculated = SubmissionService.calculate_fields(
            request.data,
            version.schema_json
        )
        logger.debug(f"计算字段完成: fields_count={len(data_with_calculated)}")

        # 9. 更新数据
        submission.data_jsonb = data_with_calculated
        submission.updated_at = datetime.utcnow()

        # 10. 重新绑定附件
        try:
            SubmissionService._bind_attachments(
                submission.id,
                data_with_calculated,
                version.schema_json,
                tenant_id,
                db
            )
            logger.debug(f"附件重新绑定完成: submission_id={submission.id}")
        except Exception as e:
            logger.error(f"重新绑定附件失败: submission_id={submission.id}, error={e}")

        db.commit()
        db.refresh(submission)

        logger.info(f"提交更新成功: submission_id={submission_id}")
        return submission

    @staticmethod
    def delete_submission(
            submission_id: int,
            tenant_id: int,
            user_id: int,
            db: Session
    ) -> int:
        """
        删除提交记录（软删除，设置状态为 deleted）

        【业务流程】
        1. 查询提交记录是否存在
        2. 查询关联的表单
        3. 验证删除权限（提交者或表单所有者）
        4. 将状态设置为 deleted（软删除）

        【权限规则】
        - 提交者本人可以删除
        - 表单所有者（创建者）可以删除

        :param submission_id: 要删除的提交记录ID
        :param tenant_id: 租户ID
        :param user_id: 当前操作用户ID
        :param db: 数据库会话对象
        :return: 被删除提交所属的表单ID（用于清理缓存）
        :raises NotFoundError: 提交记录不存在时抛出
        :raises AuthorizationError: 无权限删除时抛出
        """
        logger.info(f"开始删除提交: submission_id={submission_id}, user_id={user_id}")

        # 1. 查询提交记录
        submission = SubmissionService.get_submission_by_id(submission_id, tenant_id, db)
        logger.debug(
            f"获取提交记录: form_id={submission.form_id}, "
            f"submitter={submission.submitter_user_id}"
        )

        # 2. 获取表单
        form = FormService.get_form_by_id(submission.form_id, tenant_id, db)

        # 3. 权限检查：提交者或表单创建者
        if submission.submitter_user_id != user_id and form.owner_user_id != user_id:
            logger.warning(
                f"权限不足: submission_id={submission_id}, "
                f"submitter={submission.submitter_user_id}, "
                f"form_owner={form.owner_user_id}, "
                f"user={user_id}"
            )
            raise AuthorizationError("无权删除此提交")

        # 4. 软删除（设置状态）
        submission.status = SubmissionStatus.DELETED.value
        db.commit()

        logger.info(f"提交删除成功: submission_id={submission_id}, form_id={submission.form_id}")

        # 返回 form_id 用于清理缓存
        return submission.form_id

    @staticmethod
    def get_submission_by_id(
            submission_id: int,
            tenant_id: int,
            db: Session,
            include_data: bool = True
    ) -> Submission:
        """
        根据ID查询提交详情

        【查询条件】
        - submission_id: 提交记录ID
        - tenant_id: 租户ID（数据隔离）

        :param submission_id: 提交记录ID
        :param tenant_id: 租户ID
        :param db: 数据库会话对象
        :param include_data: 是否包含 data_jsonb 字段（预留参数，暂未使用）
        :return: Submission 对象
        :raises NotFoundError: 提交记录不存在时抛出
        """
        submission = db.query(Submission).filter(
            Submission.id == submission_id,
            Submission.tenant_id == tenant_id
        ).first()

        if not submission:
            logger.warning(f"提交不存在: submission_id={submission_id}, tenant_id={tenant_id}")
            raise NotFoundError(f"提交不存在: id={submission_id}")

        logger.debug(f"查询提交成功: submission_id={submission_id}, status={submission.status}")
        return submission

    @staticmethod
    def get_latest_submission_by_user(
            form_id: int,
            user_id: int,
            tenant_id: int,
            db: Session
    ) -> Optional[Submission]:
        """获取当前用户对指定表单的最新提交记录。

        :param form_id: 表单 ID
        :param user_id: 用户 ID
        :param tenant_id: 租户 ID
        :param db: 数据库会话
        :return: 最新的 Submission 或 None

        Time: O(log N), Space: O(1)
        """
        submission = (
            db.query(Submission)
            .filter(
                Submission.form_id == form_id,
                Submission.submitter_user_id == user_id,
                Submission.tenant_id == tenant_id,
                Submission.status != SubmissionStatus.DELETED.value,
            )
            .order_by(Submission.created_at.desc())
            .first()
        )
        return submission

    @staticmethod
    def get_process_overview(
            submission_id: int,
            tenant_id: int,
            db: Session
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        获取提交关联的流程实例概要信息。

        :param submission_id: 提交记录ID
        :param tenant_id: 租户ID，确保数据隔离
        :param db: 数据库会话对象
        :return: (流程实例ID, 流程状态)

        Time: O(1), Space: O(1)
        """
        process_instance = (
            db.query(ProcessInstance.id, ProcessInstance.state)
            .filter(
                ProcessInstance.submission_id == submission_id,
                ProcessInstance.tenant_id == tenant_id,
            )
            .order_by(ProcessInstance.created_at.desc())
            .first()
        )

        if not process_instance:
            return None, None

        return process_instance.id, process_instance.state

    @staticmethod
    def list_submissions(
            request: SubmissionQueryRequest,
            tenant_id: int,
            user_id: Optional[int],
            db: Session
    ) -> Tuple[List[Submission], int]:
        """
        分页查询提交列表（支持多条件筛选）

        【查询条件】
        - form_id: 按表单ID筛选（可选）
        - status: 按状态筛选（可选，默认排除已删除）
        - submitter_user_id: 按提交人筛选（可选）
        - date_from: 起始日期（可选）
        - date_to: 结束日期（可选）
        - keyword: 关键词搜索（搜索 JSONB 字段内容，可选）

        【权限规则】
        - 管理员用户：可以看到所有提交
        - 非管理员用户：只能看到自己提交的记录或自己创建的表单的提交记录

        【分页参数】
        - page: 页码（从 1 开始）
        - page_size: 每页数量

        【排序规则】
        - 按创建时间倒序排列（最新的在前）

        :param request: 查询请求对象（包含筛选条件和分页参数）
        :param tenant_id: 租户ID
        :param user_id: 当前用户ID（用于权限过滤）
        :param db: 数据库会话对象
        :return: (提交列表, 总记录数) 元组
        :raises Exception: 数据库查询失败时抛出

        【性能优化】
        - 使用 JSONB 字段的文本搜索（支持 GIN 索引）
        - 分页查询避免加载全量数据
        - 使用 count() 计算总数（不加载数据）
        """
        logger.debug(
            f"查询提交列表: tenant_id={tenant_id}, form_id={request.form_id}, "
            f"status={request.status}, page={request.page}, page_size={request.page_size}"
        )

        query = db.query(Submission).filter(Submission.tenant_id == tenant_id)

        is_admin = FormPermissionService._is_admin(user_id, tenant_id, db) if user_id else False

        if not is_admin and user_id:
            form_ids_owned = (
                db.query(Form.id)
                .filter(Form.owner_user_id == user_id, Form.tenant_id == tenant_id)
                .subquery()
            )
            query = query.filter(
                or_(
                    Submission.submitter_user_id == user_id,
                    Submission.form_id.in_(form_ids_owned)
                )
            )
            logger.debug(f"非管理员用户，添加权限过滤: user_id={user_id}")

        if request.form_id:
            query = query.filter(Submission.form_id == request.form_id)
            logger.debug(f"添加表单筛选: form_id={request.form_id}")

        # 2. 状态筛选
        if request.status:
            # 如果 request.status 是枚举类型，使用 .value
            status_value = request.status.value if isinstance(request.status, Enum) else request.status
            query = query.filter(Submission.status == status_value)
            logger.debug(f"添加状态筛选: status={status_value}")
        else:
            # 默认不显示已删除
            query = query.filter(Submission.status != SubmissionStatus.DELETED.value)

        # 3. 提交者筛选
        if request.submitter_user_id:
            query = query.filter(Submission.submitter_user_id == request.submitter_user_id)
            logger.debug(f"添加提交者筛选: user_id={request.submitter_user_id}")

        # 4. 日期范围筛选
        if request.date_from:
            query = query.filter(Submission.created_at >= request.date_from)
            logger.debug(f"添加起始日期筛选: date_from={request.date_from}")
        if request.date_to:
            query = query.filter(Submission.created_at <= request.date_to)
            logger.debug(f"添加结束日期筛选: date_to={request.date_to}")

        # 5. 关键词搜索（PostgreSQL JSONB 文本搜索）
        if request.keyword:
            # ✅ 修复：使用正确的导入 String
            query = query.filter(
                Submission.data_jsonb.cast(String).ilike(f"%{request.keyword}%")
            )
            logger.debug(f"添加关键词搜索: keyword={request.keyword}")

        # 6. 计算总数
        total = query.count()
        logger.debug(f"查询总数: total={total}")

        # 7. 分页查询
        offset = (request.page - 1) * request.page_size
        submissions = (
            query
            .order_by(Submission.created_at.desc())
            .offset(offset)
            .limit(request.page_size)
            .all()
        )

        logger.info(
            f"查询提交列表成功: total={total}, returned={len(submissions)}, "
            f"page={request.page}, page_size={request.page_size}"
        )

        return submissions, total

    @staticmethod
    def get_submission_statistics(
            form_id: int,
            tenant_id: int,
            db: Session
    ) -> Dict[str, Any]:
        """
        获取指定表单的提交统计数据

        【统计维度】
        1. 总提交数（排除已删除）
        2. 按状态分组统计
        3. 按日期分组统计（最近7天）
        4. 平均填写时长

        【返回数据结构】
        {
            "total": 1000,
            "by_status": {"submitted": 800, "approved": 150, "rejected": 50},
            "by_date": [{"date": "2025-01-01", "count": 10}, ...],
            "avg_duration": 120.5
        }

        :param form_id: 表单ID
        :param tenant_id: 租户ID
        :param db: 数据库会话对象
        :return: 统计数据字典
        :raises Exception: 数据库查询失败时抛出

        【性能优化】
        - 使用聚合函数，避免加载明细数据
        - 日期统计限制在最近7天，减少计算量
        - 结果可缓存（由上层 API 实现）
        """
        logger.debug(f"统计提交数据: form_id={form_id}, tenant_id={tenant_id}")

        # 1. 总数统计（排除已删除）
        total = db.query(func.count(Submission.id)).filter(
            Submission.form_id == form_id,
            Submission.tenant_id == tenant_id,
            Submission.status != SubmissionStatus.DELETED.value
        ).scalar()

        logger.debug(f"总提交数: {total}")

        # 2. 按状态统计
        by_status = {}
        status_stats = db.query(
            Submission.status,
            func.count(Submission.id)
        ).filter(
            Submission.form_id == form_id,
            Submission.tenant_id == tenant_id,
            Submission.status != SubmissionStatus.DELETED.value
        ).group_by(Submission.status).all()

        for status, count in status_stats:
            by_status[status] = count

        logger.debug(f"状态统计: {by_status}")

        # 3. 按日期统计（最近7天）
        seven_days_ago = datetime.now() - timedelta(days=7)
        date_stats = db.query(
            func.date(Submission.created_at).label('date'),
            func.count(Submission.id).label('count')
        ).filter(
            Submission.form_id == form_id,
            Submission.tenant_id == tenant_id,
            Submission.created_at >= seven_days_ago
        ).group_by(func.date(Submission.created_at)).all()

        by_date = [
            {"date": str(date), "count": count}
            for date, count in date_stats
        ]

        logger.debug(f"日期统计: {len(by_date)} 天有数据")

        # 4. 平均填写时长
        avg_duration = db.query(func.avg(Submission.duration)).filter(
            Submission.form_id == form_id,
            Submission.tenant_id == tenant_id,
            Submission.duration.isnot(None)
        ).scalar()

        logger.debug(f"平均时长: {avg_duration}")

        result = {
            "total": total or 0,
            "by_status": by_status,
            "by_date": by_date,
            "avg_duration": float(avg_duration) if avg_duration else None
        }

        logger.info(f"统计完成: form_id={form_id}, total={result['total']}")
        return result

    @staticmethod
    def validate_submission_data(
            data: Dict[str, Any],
            schema_json: Dict[str, Any],
            logic_json: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """
        验证提交数据的完整性和格式

        【验证规则】
        1. 必填字段验证: required=True 的字段不能为空、空字符串、空数组
        2. 数字范围验证: number 类型字段的 min/max 限制
        3. 字段格式验证: 根据字段类型验证数据格式
        4. 逻辑规则验证: 根据 logic_json 验证显示/隐藏逻辑（待实现）

        【返回值】
        - (True, []): 验证通过，无错误
        - (False, ["错误1", "错误2"]): 验证失败，包含错误列表

        :param data: 提交的数据字典 {field_id: value}
        :param schema_json: 表单结构定义（包含字段配置）
        :param logic_json: 逻辑规则定义（可选，暂未实现）
        :return: (是否通过, 错误列表) 元组

        【待优化】
        - 实现更多字段类型的格式验证（邮箱、手机号、URL等）
        - 实现逻辑规则验证（显示/隐藏、必填联动等）
        - 实现自定义验证规则
        """
        errors = []
        fields = schema_json.get("fields", [])

        logger.debug(f"开始验证数据: fields_count={len(fields)}, data_keys={list(data.keys())}")

        # 1. 验证必填字段
        for field in fields:
            field_id = field.get("id")
            field_label = field.get("label", field_id)
            required = field.get("required", False)

            if required:
                value = data.get(field_id)

                # 检查是否为空
                if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
                    error_msg = f"字段 {field_label} 为必填项"
                    errors.append(error_msg)
                    logger.debug(f"必填验证失败: {error_msg}")

        # 2. 验证字段格式
        for field in fields:
            field_id = field.get("id")
            field_type = field.get("type")
            field_label = field.get("label", field_id)
            value = data.get(field_id)

            # 跳过空值
            if value is None:
                continue

            # 数字范围验证
            if field_type == "number":
                props = field.get("props", {})
                min_val = props.get("min")
                max_val = props.get("max")

                try:
                    num_val = float(value)

                    if min_val is not None and num_val < min_val:
                        error_msg = f"字段 {field_label} 不能小于 {min_val}"
                        errors.append(error_msg)
                        logger.debug(f"数字范围验证失败: {error_msg}")

                    if max_val is not None and num_val > max_val:
                        error_msg = f"字段 {field_label} 不能大于 {max_val}"
                        errors.append(error_msg)
                        logger.debug(f"数字范围验证失败: {error_msg}")

                except (ValueError, TypeError):
                    error_msg = f"字段 {field_label} 必须是数字"
                    errors.append(error_msg)
                    logger.debug(f"数字格式验证失败: {error_msg}")

        is_valid = len(errors) == 0
        logger.info(f"数据验证完成: is_valid={is_valid}, errors_count={len(errors)}")

        return is_valid, errors

    @staticmethod
    def calculate_fields(
            data: Dict[str, Any],
            schema_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算所有计算字段的值

        【计算流程】
        1. 从 schema_json 中提取所有 calculated 类型字段
        2. 使用 FormulaService 分析字段依赖关系
        3. 按依赖顺序依次计算（A依赖B，则先算B再算A）
        4. 使用 FormulaService.evaluate 计算公式
        5. 计算失败时设置为 null 并记录日志

        【支持的公式】
        - 数学运算: +, -, *, /, %
        - 字段引用: {field_id}
        - 函数: SUM, AVG, MAX, MIN 等（由 FormulaService 实现）

        :param data: 原始提交数据（不含计算字段）
        :param schema_json: 表单结构定义
        :return: 包含计算字段的完整数据
        :raises Exception: 公式计算失败时捕获并设置为 null

        【示例】
        >>> data = {"price": 100, "quantity": 5}
        >>> schema = {"fields": [
        ...     {"id": "total", "type": "calculated", "props": {"formula": "{price} * {quantity}"}}
        ... ]}
        >>> result = calculate_fields(data, schema)
        >>> result["total"]  # 500
        """
        result = data.copy()
        fields = schema_json.get("fields", [])

        # 1. 获取所有计算字段
        calculated_fields = [f for f in fields if f.get("type") == "calculated"]

        if not calculated_fields:
            logger.debug("无计算字段，跳过计算")
            return result

        logger.debug(f"发现计算字段: count={len(calculated_fields)}")

        # 2. 按依赖顺序计算
        try:
            calculation_order = FormulaService.get_calculation_order(fields)
            logger.debug(f"计算顺序: {calculation_order}")
        except Exception as e:
            logger.error(f"获取计算顺序失败: {e}")
            calculation_order = [f.get("id") for f in calculated_fields]

        # 3. 依次计算每个字段
        for field_id in calculation_order:
            field = next((f for f in fields if f.get("id") == field_id), None)

            if field and field.get("type") == "calculated":
                formula = field.get("props", {}).get("formula")

                if formula:
                    try:
                        # 使用 FormulaService 计算
                        calculated_value = FormulaService.evaluate(formula, result)
                        result[field_id] = calculated_value
                        logger.debug(f"计算字段成功: {field_id} = {calculated_value}")
                    except Exception as e:
                        logger.error(f"计算字段失败: field_id={field_id}, formula={formula}, error={e}")
                        result[field_id] = None

        logger.info(f"计算字段完成: total={len(calculated_fields)}")
        return result

    @staticmethod
    def build_snapshot(form_version: FormVersion) -> Dict[str, Any]:
        """
        构建提交快照（用于归档和显示）

        【快照内容】
        1. 表单版本信息（version_id, version, published_at）
        2. 字段标签映射（field_id -> label）
        3. 选项字段的选项列表（用于显示选项文本）
        4. 计算字段的公式（用于审计）

        【用途】
        - 表单结构变更后，历史提交仍能正确显示
        - 审计和归档用途
        - 导出时恢复字段标签和选项文本

        :param form_version: 表单版本对象
        :return: 快照数据字典

        【示例返回值】
        {
            "form_version_id": 1,
            "version": 2,
            "published_at": "2025-01-01T00:00:00",
            "field_labels": {"name": "姓名", "age": "年龄"},
            "field_options": {
                "gender": [{"value": "M", "label": "男"}, {"value": "F", "label": "女"}]
            },
            "calculated_formulas": {"total": "{price} * {quantity}"}
        }
        """
        logger.debug(f"构建快照: version_id={form_version.id}, version={form_version.version}")

        schema_json = form_version.schema_json
        snapshot = {
            "form_version_id": form_version.id,
            "version": form_version.version,
            "published_at": form_version.published_at.isoformat() if form_version.published_at else None,
            "field_labels": {},
            "field_types": {},
            "field_options": {},
            "calculated_formulas": {}
        }

        fields = schema_json.get("fields", [])

        for field in fields:
            field_id = field.get("id")

            # 1. 保存标签
            snapshot["field_labels"][field_id] = field.get("label")

            # 2. 保存字段类型
            snapshot["field_types"][field_id] = field.get("type")

            # 3. 保存选项类字段的选项
            if field.get("type") in ["select", "radio", "checkbox"]:
                options = field.get("props", {}).get("options", [])
                snapshot["field_options"][field_id] = options
                logger.debug(f"保存选项: {field_id} -> {len(options)} 个选项")

            # 4. 保存计算字段公式
            if field.get("type") == "calculated":
                formula = field.get("props", {}).get("formula")
                if formula:
                    snapshot["calculated_formulas"][field_id] = formula
                    logger.debug(f"保存公式: {field_id} -> {formula}")

        logger.info(
            f"快照构建完成: fields={len(fields)}, "
            f"options={len(snapshot['field_options'])}, "
            f"formulas={len(snapshot['calculated_formulas'])}"
        )

        return snapshot

    @staticmethod
    def _bind_attachments(
            submission_id: int,
            data: Dict[str, Any],
            schema_json: Dict[str, Any],
            tenant_id: int,
            db: Session
    ) -> None:
        """
        绑定附件到提交记录

        【处理流程】
        1. 从 schema_json 中提取所有 upload/image 类型字段
        2. 从提交数据中提取对应的附件ID列表
        3. 调用 AttachmentService 绑定附件
        4. 绑定失败时记录警告日志，不影响主流程

        【字段类型】
        - upload: 通用文件上传字段
        - image: 图片上传字段

        【数据格式】
        data = {
            "files": [1, 2, 3],  # 附件ID列表
            "images": [4, 5]      # 图片ID列表
        }

        :param submission_id: 提交记录ID
        :param data: 提交数据（包含附件ID）
        :param schema_json: 表单结构定义
        :param tenant_id: 租户ID
        :param db: 数据库会话对象
        :return: None
        :raises Exception: 附件绑定失败时记录日志但不抛出异常
        """
        from app.services.attachment_service import AttachmentService

        fields = schema_json.get("fields", [])
        upload_fields = [f for f in fields if f.get("type") in ["upload", "image"]]

        if not upload_fields:
            logger.debug("无上传字段，跳过附件绑定")
            return

        logger.debug(f"开始绑定附件: submission_id={submission_id}, upload_fields={len(upload_fields)}")

        bind_count = 0
        fail_count = 0

        for field in upload_fields:
            field_id = field.get("id")
            attachment_ids = data.get(field_id, [])

            # 确保是列表类型
            if not isinstance(attachment_ids, list):
                logger.warning(f"附件字段格式错误: {field_id}, value={attachment_ids}")
                continue

            # 绑定每个附件
            for att_id in attachment_ids:
                if isinstance(att_id, int):
                    try:
                        AttachmentService.bind_attachment(
                            att_id,
                            "submission",
                            submission_id,
                            tenant_id,
                            db
                        )
                        bind_count += 1
                        logger.debug(f"附件绑定成功: attachment_id={att_id}")
                    except Exception as e:
                        fail_count += 1
                        logger.warning(f"附件绑定失败: attachment_id={att_id}, error={e}")
                else:
                    logger.warning(f"附件ID类型错误: {att_id}, type={type(att_id)}")

        logger.info(
            f"附件绑定完成: submission_id={submission_id}, "
            f"success={bind_count}, failed={fail_count}"
        )