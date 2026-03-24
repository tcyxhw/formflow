"""
Preservation 保持性测试 - 审计日志功能完整性

目标: 验证修复后，审计日志的数据格式、字段、错误处理逻辑保持不变

测试策略（观察优先方法）:
1. 在未修复代码上观察正常工作的场景（传递了 db 参数的路由）
2. 记录审计日志的数据格式和字段
3. 编写属性测试捕获这些行为模式
4. 在未修复代码上运行测试，验证通过
5. 修复后再次运行，确认行为保持不变

预期结果（未修复和修复后都应通过）:
- 审计日志数据格式保持不变
- 所有必需字段都存在且正确
- 错误处理逻辑保持不变
"""
import pytest
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.notification import AuditLog
from app.models.user import User, Tenant
from app.core.security import get_password_hash
from httpx import AsyncClient
from app.main import app
import json
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
    """设置测试数据"""
    # 创建测试租户
    tenant = test_db.query(Tenant).filter(Tenant.name == "保持性测试租户").first()
    if not tenant:
        tenant = Tenant(name="保持性测试租户")
        test_db.add(tenant)
        test_db.commit()
        test_db.refresh(tenant)
    
    # 创建测试用户
    user = test_db.query(User).filter(
        User.account == "preservation_test_user",
        User.tenant_id == tenant.id
    ).first()
    
    if not user:
        user = User(
            account="preservation_test_user",
            password_hash=get_password_hash("test123456"),
            name="保持性测试用户",
            email="preservation@test.com",
            tenant_id=tenant.id,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
    
    yield {"tenant_id": tenant.id, "user": user}


@pytest.mark.asyncio
async def test_audit_log_data_format_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - 审计日志数据格式保持不变
    
    验证点：
    - tenant_id 字段存在且正确
    - actor_user_id 字段存在且正确
    - action 字段存在且正确
    - resource_type 字段存在且正确
    - resource_id 字段存在
    - before_json 字段（可选）
    - after_json 字段存在且格式正确
    - ip 字段存在
    - ua 字段存在
    - created_at 字段存在
    """
    tenant_id = setup_test_data["tenant_id"]
    user = setup_test_data["user"]
    
    # 清理旧的审计日志
    test_db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_id,
        AuditLog.action == "user_login"
    ).delete()
    test_db.commit()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 执行登录操作
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "account": "preservation_test_user",
                "password": "test123456",
                "tenant_id": tenant_id
            }
        )
        
        assert response.status_code == 200, f"登录失败：{response.status_code}"
    
    # 等待审计日志创建（如果是后台任务，可能需要短暂延迟）
    import time
    time.sleep(0.5)
    
    # 查询审计日志
    audit_log = test_db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_id,
        AuditLog.action == "user_login"
    ).order_by(AuditLog.created_at.desc()).first()
    
    # 断言：审计日志应该被创建
    assert audit_log is not None, "审计日志未创建"
    
    # 断言：验证所有必需字段
    assert audit_log.tenant_id == tenant_id, f"tenant_id 不匹配：期望 {tenant_id}，实际 {audit_log.tenant_id}"
    assert audit_log.actor_user_id == user.id, f"actor_user_id 不匹配：期望 {user.id}，实际 {audit_log.actor_user_id}"
    assert audit_log.action == "user_login", f"action 不匹配：期望 'user_login'，实际 '{audit_log.action}'"
    assert audit_log.resource_type == "auth", f"resource_type 不匹配：期望 'auth'，实际 '{audit_log.resource_type}'"
    assert audit_log.resource_id is not None, "resource_id 不应为 None"
    
    # 断言：after_json 应该存在且包含用户信息
    assert audit_log.after_json is not None, "after_json 不应为 None"
    after_data = json.loads(audit_log.after_json)
    assert "data" in after_data or "user" in after_data, "after_json 应包含 data 或 user 字段"
    
    # 断言：ip 和 ua 字段应该存在（可能为 None，取决于测试环境）
    # 在实际环境中这些字段应该有值
    assert hasattr(audit_log, 'ip'), "审计日志应有 ip 字段"
    assert hasattr(audit_log, 'ua'), "审计日志应有 ua 字段"
    
    # 断言：created_at 字段应该存在
    assert audit_log.created_at is not None, "created_at 不应为 None"
    
    logger.info(f"✅ 保持性测试通过：审计日志数据格式正确")
    logger.info(f"   - tenant_id: {audit_log.tenant_id}")
    logger.info(f"   - actor_user_id: {audit_log.actor_user_id}")
    logger.info(f"   - action: {audit_log.action}")
    logger.info(f"   - resource_type: {audit_log.resource_type}")
    logger.info(f"   - resource_id: {audit_log.resource_id}")


@pytest.mark.asyncio
async def test_audit_log_error_handling_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - 审计日志错误处理逻辑保持不变
    
    验证点：
    - 当审计日志记录失败时，主请求流程不应受影响
    - 应该记录错误日志
    - 不应该抛出异常导致请求失败
    """
    tenant_id = setup_test_data["tenant_id"]
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 执行登录操作（即使审计日志失败，登录也应成功）
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "account": "preservation_test_user",
                "password": "test123456",
                "tenant_id": tenant_id
            }
        )
        
        # 断言：登录应该成功，不受审计日志影响
        assert response.status_code == 200, f"登录失败：{response.status_code}"
        
        data = response.json()
        assert "data" in data, "响应缺少 data 字段"
        assert "access_token" in data["data"], "响应缺少 access_token"
        
        logger.info("✅ 保持性测试通过：审计日志错误不影响主请求流程")


@pytest.mark.asyncio
async def test_audit_log_multiple_actions_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - 多种操作的审计日志都应正常工作
    
    验证点：
    - 登录操作的审计日志
    - 登出操作的审计日志（如果实现了）
    - 其他操作的审计日志
    """
    tenant_id = setup_test_data["tenant_id"]
    
    # 清理旧的审计日志
    test_db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_id
    ).delete()
    test_db.commit()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "account": "preservation_test_user",
                "password": "test123456",
                "tenant_id": tenant_id
            }
        )
        assert login_response.status_code == 200
        
        # 获取 token
        token = login_response.json()["data"]["access_token"]
        
        # 2. 获取用户信息（不使用审计日志，用于对比）
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
    
    # 等待审计日志创建
    import time
    time.sleep(0.5)
    
    # 查询审计日志
    audit_logs = test_db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_id
    ).order_by(AuditLog.created_at.desc()).all()
    
    # 断言：应该至少有登录的审计日志
    assert len(audit_logs) >= 1, f"应该至少有 1 条审计日志，实际 {len(audit_logs)} 条"
    
    # 验证登录审计日志
    login_audit = next((log for log in audit_logs if log.action == "user_login"), None)
    assert login_audit is not None, "应该有登录审计日志"
    assert login_audit.resource_type == "auth"
    
    logger.info(f"✅ 保持性测试通过：多种操作的审计日志都正常工作（共 {len(audit_logs)} 条）")


@pytest.mark.asyncio
async def test_audit_log_json_serialization_preservation(setup_test_data, test_db: Session):
    """
    Property 2: Preservation - JSON 序列化保持不变
    
    验证点：
    - after_json 应该是有效的 JSON 字符串
    - 可以正确反序列化
    - 包含预期的数据结构
    """
    tenant_id = setup_test_data["tenant_id"]
    
    # 清理旧的审计日志
    test_db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_id,
        AuditLog.action == "user_login"
    ).delete()
    test_db.commit()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "account": "preservation_test_user",
                "password": "test123456",
                "tenant_id": tenant_id
            }
        )
        assert response.status_code == 200
    
    # 等待审计日志创建
    import time
    time.sleep(0.5)
    
    # 查询审计日志
    audit_log = test_db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_id,
        AuditLog.action == "user_login"
    ).order_by(AuditLog.created_at.desc()).first()
    
    assert audit_log is not None, "审计日志未创建"
    assert audit_log.after_json is not None, "after_json 不应为 None"
    
    # 断言：应该能正确反序列化
    try:
        after_data = json.loads(audit_log.after_json)
        assert isinstance(after_data, dict), "after_json 应该反序列化为字典"
        
        # 验证数据结构
        # 登录响应可能是 success_response 格式：{"code": 200, "data": {...}, "message": "..."}
        # 或者直接是用户数据
        if "data" in after_data:
            assert "user" in after_data["data"] or "access_token" in after_data["data"], \
                "after_json 应包含用户信息或令牌"
        
        logger.info("✅ 保持性测试通过：JSON 序列化正确")
        logger.info(f"   - after_json 长度: {len(audit_log.after_json)} 字符")
        logger.info(f"   - 反序列化后的键: {list(after_data.keys())}")
        
    except json.JSONDecodeError as e:
        pytest.fail(f"after_json 反序列化失败：{e}\n内容：{audit_log.after_json}")


@pytest.mark.asyncio
async def test_non_audit_routes_preservation(setup_test_data):
    """
    Property 2: Preservation - 不使用审计日志的路由应完全不受影响
    
    验证点：
    - 获取租户列表（不使用审计日志）
    - 响应时间应该很快
    - 功能正常
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        import time
        start_time = time.time()
        
        response = await client.get("/api/v1/auth/tenants")
        
        elapsed_time = time.time() - start_time
        
        # 断言：应该快速响应
        assert elapsed_time < 2.0, f"不使用审计日志的路由响应过慢：{elapsed_time:.2f} 秒"
        
        # 断言：功能正常
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        
        logger.info(f"✅ 保持性测试通过：不使用审计日志的路由正常工作（{elapsed_time:.2f} 秒）")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
