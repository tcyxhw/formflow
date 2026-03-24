# app/models/__init__.py
"""
模型模块
导出所有模型类，便于其他模块使用
"""

# 导入所有模型，确保它们被SQLAlchemy注册
from app.models.base import DBBaseModel, TenantMixin, TimestampMixin
from app.models.user import (
    Tenant,
    Department,
    Position,
    User,
    UserProfile,
    UserPosition,
    Role,
    UserRole,
    ApprovalGroup,
    ApprovalGroupMember,
    Delegation,
    DepartmentPost,
    UserDepartmentPost
)
from app.models.category import Category
from app.models.form import (
    Form,
    FormVersion,
    FormPermission,
    FormShare,
    Submission,
    FormDraft,
    Attachment
)
from app.models.user_quick_access import UserQuickAccess
from app.models.workflow import (
    FlowDefinition,
    FlowNode,
    FlowRoute,
    ProcessInstance,
    Task,
    TaskActionLog,
    ParallelRuntime
)
from app.models.activity import (
    Activity,
    ActivityRegistration,
    ActivityCheckInCode,
    AwardMapping,
    AwardRecord,
    LedgerDetail
)
from app.models.resource import (
    Resource,
    Booking
)
from app.models.notification import (
    NotificationConfig,
    NotificationLog,
    FormStatistics,
    ScheduledJob,
    AuditLog,
    RefreshToken,
    DictItem
)
from app.models.batch_import import BatchImportLog

# 导出所有模型
__all__ = [
    # 基础类
    'DBBaseModel',
    'TenantMixin',
    'TimestampMixin',

    # 用户模块
    'Tenant',
    'Department',
    'Position',
    'User',
    'UserProfile',
    'UserPosition',
    'Role',
    'UserRole',
    'ApprovalGroup',
    'ApprovalGroupMember',
    'Delegation',
    'DepartmentPost',
    'UserDepartmentPost',

    # 表单模块
    'Category',
    'Form',
    'FormVersion',
    'FormPermission',
    'FormShare',
    'Submission',
    'FormDraft',
    'Attachment',
    'UserQuickAccess',

    # 流程模块
    'FlowDefinition',
    'FlowNode',
    'FlowRoute',
    'ProcessInstance',
    'Task',
    'TaskActionLog',
    'ParallelRuntime',

    # 活动模块
    'Activity',
    'ActivityRegistration',
    'ActivityCheckInCode',
    'AwardMapping',
    'AwardRecord',
    'LedgerDetail',

    # 资源模块
    'Resource',
    'Booking',

    # 通知和系统模块
    'NotificationConfig',
    'NotificationLog',
    'FormStatistics',
    'ScheduledJob',
    'AuditLog',
    'RefreshToken',
    'DictItem',

    # 批量导入模块
    'BatchImportLog',
]