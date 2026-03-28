# app/models/user.py
"""
用户与组织相关模型
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index, Text, JSON
)
from sqlalchemy.orm import relationship
from app.models.base import DBBaseModel, Base, TimestampMixin
from datetime import datetime


class Tenant(Base, TimestampMixin):
    """租户表 - 支持多学校"""
    __tablename__ = "tenant"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="学校/机构名称")

    # 简化 relationship 定义
    # departments = relationship("Department", back_populates="tenant")
    # users = relationship("User", back_populates="tenant")


class Department(DBBaseModel):
    """部门表 - 组织架构，支持树形结构"""
    __tablename__ = "department"
    __table_args__ = (
        Index("idx_tenant_name", "tenant_id", "name"),
    )

    name = Column(String(100), nullable=False, comment="部门名称")
    parent_id = Column(Integer, ForeignKey("department.id"), nullable=True, comment="上级部门ID")
    type = Column(String(20), nullable=False, comment="类型：college/office/department/class")
    is_root = Column(Boolean, default=False, nullable=False, comment="是否是根部门")
    sort_order = Column(Integer, default=0, comment="排序")

    # 关系定义 - 修复自引用关系
    # tenant = relationship("Tenant", back_populates="departments")
    # parent = relationship(
    #     "Department",
    #     remote_side="Department.id",  # 使用字符串形式
    #     back_populates="children"
    # )
    # children = relationship(
    #     "Department",
    #     back_populates="parent"
    # )
    # users = relationship("User", back_populates="department")


class Position(DBBaseModel):
    """岗位字典表"""
    __tablename__ = "position"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_position"),
    )

    name = Column(String(50), nullable=False, comment="岗位名称")

    # 关系
    # user_positions = relationship("UserPosition", back_populates="position")


class User(DBBaseModel):
    """用户表"""
    __tablename__ = "user"
    __table_args__ = (
        Index("idx_tenant_account", "tenant_id", "account"),
        Index("idx_tenant_dept", "tenant_id", "department_id"),
    )

    account = Column(String(50), nullable=False, comment="登录账号")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    name = Column(String(50), nullable=False, comment="真实姓名")
    email = Column(String(100), nullable=True, comment="邮箱")
    phone = Column(String(20), nullable=True, comment="手机号")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    department_id = Column(Integer, ForeignKey("department.id"), nullable=True, comment="主属部门ID")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    # 关系定义 - 修复：指定 foreign_keys
    # tenant = relationship("Tenant", back_populates="users")
    # department = relationship("Department", back_populates="users")
    # profile = relationship(
    #     "UserProfile",
    #     uselist=False,
    #     back_populates="user",
    #     foreign_keys="UserProfile.user_id"  # 明确指定使用 user_id 外键
    # )
    # positions = relationship("UserPosition", back_populates="user")
    # roles = relationship("UserRole", back_populates="user")


class UserProfile(DBBaseModel):
    """用户扩展信息表"""
    __tablename__ = "user_profile"
    __table_args__ = (
        Index("idx_identity_no", "identity_no"),
    )

    user_id = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False)
    identity_no = Column(String(50), nullable=True, comment="学号/工号")
    identity_type = Column(String(20), nullable=True, comment="身份类型：student/teacher/admin")
    entry_year = Column(Integer, nullable=True, comment="入学/入职年份")
    grade = Column(String(20), nullable=True, comment="年级")
    major = Column(String(50), nullable=True, comment="专业")
    supervisor_id = Column(Integer, ForeignKey("user.id"), nullable=True, comment="导师ID")
    title = Column(String(30), nullable=True, comment="职称")
    research_area = Column(String(200), nullable=True, comment="研究方向")
    office = Column(String(100), nullable=True, comment="办公室")
    emergency_contact = Column(String(50), nullable=True, comment="紧急联系人")
    emergency_phone = Column(String(20), nullable=True, comment="紧急联系电话")

    # 关系 - 修复：明确指定外键
    # user = relationship(
    #     "User",
    #     foreign_keys="UserProfile.user_id",
    #     back_populates="profile"
    # )
    # supervisor = relationship(
    #     "User",
    #     foreign_keys="UserProfile.supervisor_id"
    # # )


# 其余类保持不变，都已经正确继承 BaseModel
class UserPosition(DBBaseModel):
    """用户岗位关联表"""
    __tablename__ = "user_position"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "position_id", "effective_from", name="uq_user_position"),
    )

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("position.id"), nullable=False)
    effective_from = Column(DateTime, nullable=True, comment="生效开始日期")
    effective_to = Column(DateTime, nullable=True, comment="生效结束日期")

    # 关系
    # user = relationship("User", back_populates="positions")
    # position = relationship("Position", back_populates="user_positions")


class Role(DBBaseModel):
    """系统角色表"""
    __tablename__ = "role"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_role"),
    )

    name = Column(String(50), nullable=False, comment="角色名称")
    description = Column(String(200), nullable=True, comment="角色描述")

    # 关系
    # user_roles = relationship("UserRole", back_populates="role")


class UserRole(DBBaseModel):
    """用户角色关联表"""
    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "role_id", name="uq_user_role"),
    )

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False)

    # 关系
    # user = relationship("User", back_populates="roles")
    # role = relationship("Role", back_populates="user_roles")


class UserDepartment(DBBaseModel):
    """用户部门关联表 - 支持用户多部门关联"""
    __tablename__ = "user_department"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "department_id", name="uq_user_department"),
    )

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("department.id"), nullable=False)
    is_primary = Column(Boolean, default=False, comment="是否为主属部门")

    # 关系
    # user = relationship("User", back_populates="user_departments")
    # department = relationship("Department", back_populates="user_departments")


class ApprovalGroup(DBBaseModel):
    """审批小组表"""
    __tablename__ = "approval_group"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_group"),
    )

    name = Column(String(50), nullable=False, comment="小组名称")
    department_id = Column(Integer, ForeignKey("department.id"), nullable=True, comment="所属部门ID")

    # 关系
    # members = relationship("ApprovalGroupMember", back_populates="group")


class ApprovalGroupMember(DBBaseModel):
    """审批小组成员表"""
    __tablename__ = "approval_group_member"
    __table_args__ = (
        UniqueConstraint("tenant_id", "group_id", "user_id", name="uq_group_member"),
    )

    group_id = Column(Integer, ForeignKey("approval_group.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    # 关系
    # group = relationship("ApprovalGroup", back_populates="members")
    # user = relationship("User")


class Delegation(DBBaseModel):
    """代理人设置表"""
    __tablename__ = "delegation"
    __table_args__ = (
        Index("idx_delegator", "delegator_user_id", "enabled"),
        Index("idx_delegate", "delegate_user_id", "enabled"),
    )

    delegator_user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="委托人ID")
    delegate_user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="代理人ID")
    type = Column(String(20), nullable=False, default="all", comment="代理类型：all/specific")
    scope = Column(JSON, nullable=True, comment="代理范围")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=False, comment="结束时间")
    enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")

    # 关系
    # delegator = relationship("User", foreign_keys="Delegation.delegator_user_id")
    # delegate = relationship("User", foreign_keys="Delegation.delegate_user_id")


class DepartmentPost(DBBaseModel):
    """部门-岗位关系表"""
    __tablename__ = "department_post"
    __table_args__ = (
        UniqueConstraint("tenant_id", "department_id", "post_id", name="uq_department_post"),
    )

    department_id = Column(Integer, ForeignKey("department.id"), nullable=False, comment="部门ID")
    post_id = Column(Integer, ForeignKey("position.id"), nullable=False, comment="岗位ID")
    is_head = Column(Boolean, default=False, nullable=False, comment="是否是主负责人岗位")


class DepartmentPostLevel(DBBaseModel):
    """部门-岗位-层级关系表"""
    __tablename__ = "department_post_level"
    __table_args__ = (
        UniqueConstraint("tenant_id", "department_id", "post_id", name="uq_department_post_level"),
    )

    department_id = Column(Integer, ForeignKey("department.id"), nullable=False, comment="部门ID")
    post_id = Column(Integer, ForeignKey("position.id"), nullable=False, comment="岗位ID")
    level = Column(Integer, nullable=False, comment="层级（越小越高）")


class UserDepartmentPost(DBBaseModel):
    """用户-部门-岗位关系表"""
    __tablename__ = "user_department_post"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "department_id", "post_id", name="uq_user_department_post"),
    )

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="用户ID")
    department_id = Column(Integer, ForeignKey("department.id"), nullable=False, comment="部门ID")
    post_id = Column(Integer, ForeignKey("position.id"), nullable=True, comment="岗位ID（学生可为空）")
