"""
Preservation 保持性测试 - UserService 数据库查询功能完整性

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

目标: 验证修复后，UserService 的数据库查询返回的数据格式、内容、错误处理逻辑保持不变

测试策略（观察优先方法）:
1. 在未修复代码上观察各个方法的行为
2. 记录成功查询的返回格式和失败查询的错误处理
3. 编写属性测试捕获这些行为模式
4. 在未修复代码上运行测试，验证通过（确认基线行为）
5. 修复后再次运行，确认行为保持不变（无回归）

观察到的行为（未修复代码）:
- find_user_by_account(): 成功时返回 User 对象，失败时返回 None
- find_user_by_id(): 成功时返回 User 对象，失败时返回 None
- check_account_exists(): 返回布尔值（True/False）
- check_email_exists(): 返回布尔值（True/False）
- check_phone_exists(): 返回布尔值（True/False）
- create_user(): 成功时返回新创建的 User 对象
- create_user_profile(): 成功时返回新创建的 UserProfile 对象
- get_user_positions(): 返回字符串列表（岗位名称）
- get_user_profile(): 成功时返回 UserProfile 对象，失败时返回 None

预期结果（未修复和修复后都应通过）:
- 所有方法的返回数据格式保持不变
- 错误处理逻辑保持不变
- 数据库事务处理保持不变
"""
import pytest
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, Tenant, UserProfile, Position, UserPosition
from app.services.user_service import UserService
from app.core.security import hash_password
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@pytest.fixture
def test_db():
    """创建测试数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def setup_test_data(test_db: Session):
    """设置测试数据：租户、用户、岗位"""
    # 创建测试租户
    tenant = test_db.query(Tenant).filter(Tenant.name == "UserService保持性测试租户").first()
    if not tenant:
        tenant = Tenant(name="UserService保持性测试租户")
        test_db.add(tenant)
        test_db.commit()
        test_db.refresh(tenant)
    
    # 创建测试用户
    user = test_db.query(User).filter(
        User.account == "preservation_user",
        User.tenant_id == tenant.id
    ).first()
    
    if not user:
        user = User(
            account="preservation_user",
            password_hash=hash_password("test123456"),
            name="保持性测试用户",
            email="preservation@test.com",
            phone="13900000001",
            tenant_id=tenant.id,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
    
    # 创建用户扩展信息
    profile = test_db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(
            tenant_id=tenant.id,
            user_id=user.id,
            identity_type="student",
            entry_year=datetime.now().year,
            grade="2024",
            major="计算机科学"
        )
        test_db.add(profile)
        test_db.commit()
        test_db.refresh(profile)
    
    # 创建测试岗位
    position = test_db.query(Position).filter(
        Position.name == "测试岗位",
        Position.tenant_id == tenant.id
    ).first()
    
    if not position:
        position = Position(
            tenant_id=tenant.id,
            name="测试岗位"
        )
        test_db.add(position)
        test_db.commit()
        test_db.refresh(position)
    
    # 创建用户岗位关联
    user_position = test_db.query(UserPosition).filter(
        UserPosition.user_id == user.id,
        UserPosition.position_id == position.id
    ).first()
    
    if not user_position:
        user_position = UserPosition(
            tenant_id=tenant.id,
            user_id=user.id,
            position_id=position.id,
            effective_from=datetime.now()
        )
        test_db.add(user_position)
        test_db.commit()
    
    yield {
        "tenant_id": tenant.id,
        "user": user,
        "profile": profile,
        "position": position
    }


def test_find_user_by_account_success_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - find_user_by_account() 成功时返回 User 对象
    
    验证点：
    - 返回类型是 User 对象
    - 包含所有必需字段（id, account, name, email, phone, tenant_id, is_active）
    - 字段值正确
    """
    tenant_id = setup_test_data["tenant_id"]
    expected_user = setup_test_data["user"]
    
    # 测试：通过账号查找
    result = UserService.find_user_by_account("preservation_user", tenant_id, test_db)
    
    # 断言：应返回 User 对象
    assert result is not None, "find_user_by_account() 应返回 User 对象"
    assert isinstance(result, User), f"返回类型应为 User，实际为 {type(result)}"
    
    # 断言：验证所有必需字段
    assert result.id == expected_user.id, f"id 不匹配：期望 {expected_user.id}，实际 {result.id}"
    assert result.account == expected_user.account, f"account 不匹配"
    assert result.name == expected_user.name, f"name 不匹配"
    assert result.email == expected_user.email, f"email 不匹配"
    assert result.phone == expected_user.phone, f"phone 不匹配"
    assert result.tenant_id == expected_user.tenant_id, f"tenant_id 不匹配"
    assert result.is_active == expected_user.is_active, f"is_active 不匹配"
    
    logger.info("✅ 保持性测试通过：find_user_by_account() 成功时返回正确的 User 对象")


def test_find_user_by_account_with_email_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - find_user_by_account() 支持邮箱查找
    
    验证点：
    - 使用邮箱作为 account 参数应该能找到用户
    - 返回的是同一个用户对象
    """
    tenant_id = setup_test_data["tenant_id"]
    expected_user = setup_test_data["user"]
    
    # 测试：通过邮箱查找
    result = UserService.find_user_by_account("preservation@test.com", tenant_id, test_db)
    
    # 断言：应返回同一个用户
    assert result is not None, "通过邮箱应该能找到用户"
    assert result.id == expected_user.id, "应返回同一个用户"
    
    logger.info("✅ 保持性测试通过：find_user_by_account() 支持邮箱查找")


def test_find_user_by_account_with_phone_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - find_user_by_account() 支持手机号查找
    
    验证点：
    - 使用手机号作为 account 参数应该能找到用户
    - 返回的是同一个用户对象
    """
    tenant_id = setup_test_data["tenant_id"]
    expected_user = setup_test_data["user"]
    
    # 测试：通过手机号查找
    result = UserService.find_user_by_account("13900000001", tenant_id, test_db)
    
    # 断言：应返回同一个用户
    assert result is not None, "通过手机号应该能找到用户"
    assert result.id == expected_user.id, "应返回同一个用户"
    
    logger.info("✅ 保持性测试通过：find_user_by_account() 支持手机号查找")


def test_find_user_by_account_not_found_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - find_user_by_account() 失败时返回 None
    
    验证点：
    - 用户不存在时返回 None
    - 不抛出异常
    """
    tenant_id = setup_test_data["tenant_id"]
    
    # 测试：查找不存在的用户
    result = UserService.find_user_by_account("nonexistent_user", tenant_id, test_db)
    
    # 断言：应返回 None
    assert result is None, "用户不存在时应返回 None"
    
    logger.info("✅ 保持性测试通过：find_user_by_account() 失败时返回 None")


def test_find_user_by_account_wrong_tenant_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - find_user_by_account() 租户隔离
    
    验证点：
    - 使用错误的 tenant_id 应该找不到用户
    - 返回 None
    """
    # 测试：使用错误的 tenant_id
    result = UserService.find_user_by_account("preservation_user", 99999, test_db)
    
    # 断言：应返回 None（租户隔离）
    assert result is None, "错误的 tenant_id 应该找不到用户"
    
    logger.info("✅ 保持性测试通过：find_user_by_account() 租户隔离正确")


def test_find_user_by_id_success_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - find_user_by_id() 成功时返回 User 对象
    
    验证点：
    - 返回类型是 User 对象
    - 包含所有必需字段
    - 字段值正确
    """
    expected_user = setup_test_data["user"]
    
    # 测试：通过 ID 查找
    result = UserService.find_user_by_id(expected_user.id, test_db)
    
    # 断言：应返回 User 对象
    assert result is not None, "find_user_by_id() 应返回 User 对象"
    assert isinstance(result, User), f"返回类型应为 User，实际为 {type(result)}"
    
    # 断言：验证字段
    assert result.id == expected_user.id
    assert result.account == expected_user.account
    assert result.name == expected_user.name
    
    logger.info("✅ 保持性测试通过：find_user_by_id() 成功时返回正确的 User 对象")


def test_find_user_by_id_not_found_preservation(test_db: Session):
    """
    Property 2: Preservation - find_user_by_id() 失败时返回 None
    
    验证点：
    - 用户不存在时返回 None
    - 不抛出异常
    """
    # 测试：查找不存在的用户 ID
    result = UserService.find_user_by_id(999999, test_db)
    
    # 断言：应返回 None
    assert result is None, "用户不存在时应返回 None"
    
    logger.info("✅ 保持性测试通过：find_user_by_id() 失败时返回 None")


def test_check_account_exists_true_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - check_account_exists() 返回布尔值（存在时为 True）
    
    验证点：
    - 返回类型是 bool
    - 账号存在时返回 True
    """
    tenant_id = setup_test_data["tenant_id"]
    
    # 测试：检查存在的账号
    result = UserService.check_account_exists("preservation_user", tenant_id, test_db)
    
    # 断言：应返回 True
    assert isinstance(result, bool), f"返回类型应为 bool，实际为 {type(result)}"
    assert result is True, "账号存在时应返回 True"
    
    logger.info("✅ 保持性测试通过：check_account_exists() 存在时返回 True")


def test_check_account_exists_false_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - check_account_exists() 返回布尔值（不存在时为 False）
    
    验证点：
    - 返回类型是 bool
    - 账号不存在时返回 False
    """
    tenant_id = setup_test_data["tenant_id"]
    
    # 测试：检查不存在的账号
    result = UserService.check_account_exists("nonexistent_account", tenant_id, test_db)
    
    # 断言：应返回 False
    assert isinstance(result, bool), f"返回类型应为 bool，实际为 {type(result)}"
    assert result is False, "账号不存在时应返回 False"
    
    logger.info("✅ 保持性测试通过：check_account_exists() 不存在时返回 False")


def test_check_email_exists_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - check_email_exists() 返回布尔值
    
    验证点：
    - 返回类型是 bool
    - 邮箱存在时返回 True
    - 邮箱不存在时返回 False
    """
    tenant_id = setup_test_data["tenant_id"]
    
    # 测试：检查存在的邮箱
    result_exists = UserService.check_email_exists("preservation@test.com", tenant_id, test_db)
    assert isinstance(result_exists, bool)
    assert result_exists is True, "邮箱存在时应返回 True"
    
    # 测试：检查不存在的邮箱
    result_not_exists = UserService.check_email_exists("nonexistent@test.com", tenant_id, test_db)
    assert isinstance(result_not_exists, bool)
    assert result_not_exists is False, "邮箱不存在时应返回 False"
    
    logger.info("✅ 保持性测试通过：check_email_exists() 返回正确的布尔值")


def test_check_phone_exists_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - check_phone_exists() 返回布尔值
    
    验证点：
    - 返回类型是 bool
    - 手机号存在时返回 True
    - 手机号不存在时返回 False
    """
    tenant_id = setup_test_data["tenant_id"]
    
    # 测试：检查存在的手机号
    result_exists = UserService.check_phone_exists("13900000001", tenant_id, test_db)
    assert isinstance(result_exists, bool)
    assert result_exists is True, "手机号存在时应返回 True"
    
    # 测试：检查不存在的手机号
    result_not_exists = UserService.check_phone_exists("13900000099", tenant_id, test_db)
    assert isinstance(result_not_exists, bool)
    assert result_not_exists is False, "手机号不存在时应返回 False"
    
    logger.info("✅ 保持性测试通过：check_phone_exists() 返回正确的布尔值")


def test_create_user_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - create_user() 成功时返回新创建的 User 对象
    
    验证点：
    - 返回类型是 User 对象
    - 返回的对象有 id（已 flush）
    - 包含所有传入的字段
    - 数据库中可以查询到该用户
    """
    tenant_id = setup_test_data["tenant_id"]
    
    # 准备用户数据
    import uuid
    unique_account = f"new_user_{uuid.uuid4().hex[:8]}"
    user_data = {
        "account": unique_account,
        "password_hash": hash_password("test123456"),
        "name": "新用户",
        "email": f"{unique_account}@test.com",
        "phone": f"139{uuid.uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "is_active": True
    }
    
    # 测试：创建用户
    result = UserService.create_user(user_data, test_db)
    
    # 断言：应返回 User 对象
    assert result is not None, "create_user() 应返回 User 对象"
    assert isinstance(result, User), f"返回类型应为 User，实际为 {type(result)}"
    
    # 断言：应该有 id（已 flush）
    assert result.id is not None, "返回的 User 对象应该有 id"
    
    # 断言：验证字段
    assert result.account == unique_account
    assert result.name == "新用户"
    assert result.email == user_data["email"]
    assert result.phone == user_data["phone"]
    assert result.tenant_id == tenant_id
    assert result.is_active is True
    
    # 断言：数据库中应该能查询到
    db_user = test_db.query(User).filter(User.id == result.id).first()
    assert db_user is not None, "数据库中应该能查询到新创建的用户"
    assert db_user.account == unique_account
    
    # 清理：回滚事务（不提交）
    test_db.rollback()
    
    logger.info("✅ 保持性测试通过：create_user() 成功时返回正确的 User 对象")


def test_create_user_profile_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - create_user_profile() 成功时返回新创建的 UserProfile 对象
    
    验证点：
    - 返回类型是 UserProfile 对象
    - 包含所有传入的字段
    """
    tenant_id = setup_test_data["tenant_id"]
    user = setup_test_data["user"]
    
    # 创建一个新用户用于测试
    import uuid
    unique_account = f"profile_test_{uuid.uuid4().hex[:8]}"
    new_user = User(
        account=unique_account,
        password_hash=hash_password("test123456"),
        name="Profile测试用户",
        tenant_id=tenant_id,
        is_active=True
    )
    test_db.add(new_user)
    test_db.flush()
    
    # 准备 profile 数据
    profile_data = {
        "tenant_id": tenant_id,
        "user_id": new_user.id,
        "identity_type": "teacher",
        "entry_year": 2024,
        "title": "讲师"
    }
    
    # 测试：创建用户扩展信息
    result = UserService.create_user_profile(profile_data, test_db)
    
    # 断言：应返回 UserProfile 对象
    assert result is not None, "create_user_profile() 应返回 UserProfile 对象"
    assert isinstance(result, UserProfile), f"返回类型应为 UserProfile，实际为 {type(result)}"
    
    # 断言：验证字段
    assert result.user_id == new_user.id
    assert result.identity_type == "teacher"
    assert result.entry_year == 2024
    assert result.title == "讲师"
    
    # 清理：回滚事务
    test_db.rollback()
    
    logger.info("✅ 保持性测试通过：create_user_profile() 成功时返回正确的 UserProfile 对象")


def test_get_user_positions_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - get_user_positions() 返回字符串列表
    
    验证点：
    - 返回类型是 list
    - 列表元素是字符串（岗位名称）
    - 只返回当前有效的岗位
    """
    user = setup_test_data["user"]
    
    # 测试：获取用户岗位
    result = UserService.get_user_positions(user.id, test_db)
    
    # 断言：应返回列表
    assert isinstance(result, list), f"返回类型应为 list，实际为 {type(result)}"
    
    # 断言：列表元素应该是字符串
    for position_name in result:
        assert isinstance(position_name, str), f"岗位名称应为字符串，实际为 {type(position_name)}"
    
    # 断言：应该包含测试岗位
    assert "测试岗位" in result, "应该包含测试岗位"
    
    logger.info(f"✅ 保持性测试通过：get_user_positions() 返回正确的字符串列表（共 {len(result)} 个岗位）")


def test_get_user_positions_no_positions_preservation(test_db: Session):
    """
    Property 2: Preservation - get_user_positions() 无岗位时返回空列表
    
    验证点：
    - 用户没有岗位时返回空列表
    - 不返回 None
    """
    # 测试：查询不存在的用户的岗位
    result = UserService.get_user_positions(999999, test_db)
    
    # 断言：应返回空列表
    assert isinstance(result, list), f"返回类型应为 list，实际为 {type(result)}"
    assert len(result) == 0, "无岗位时应返回空列表"
    
    logger.info("✅ 保持性测试通过：get_user_positions() 无岗位时返回空列表")


def test_get_user_profile_success_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - get_user_profile() 成功时返回 UserProfile 对象
    
    验证点：
    - 返回类型是 UserProfile 对象
    - 包含所有字段
    """
    user = setup_test_data["user"]
    expected_profile = setup_test_data["profile"]
    
    # 测试：获取用户扩展信息
    result = UserService.get_user_profile(user.id, test_db)
    
    # 断言：应返回 UserProfile 对象
    assert result is not None, "get_user_profile() 应返回 UserProfile 对象"
    assert isinstance(result, UserProfile), f"返回类型应为 UserProfile，实际为 {type(result)}"
    
    # 断言：验证字段
    assert result.user_id == user.id
    assert result.identity_type == expected_profile.identity_type
    assert result.entry_year == expected_profile.entry_year
    assert result.grade == expected_profile.grade
    assert result.major == expected_profile.major
    
    logger.info("✅ 保持性测试通过：get_user_profile() 成功时返回正确的 UserProfile 对象")


def test_get_user_profile_not_found_preservation(test_db: Session):
    """
    Property 2: Preservation - get_user_profile() 失败时返回 None
    
    验证点：
    - 用户扩展信息不存在时返回 None
    - 不抛出异常
    """
    # 测试：查询不存在的用户的扩展信息
    result = UserService.get_user_profile(999999, test_db)
    
    # 断言：应返回 None
    assert result is None, "用户扩展信息不存在时应返回 None"
    
    logger.info("✅ 保持性测试通过：get_user_profile() 失败时返回 None")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
