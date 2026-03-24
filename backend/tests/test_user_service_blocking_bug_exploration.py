"""
Bug Condition 探索性测试 - UserService 同步方法阻塞异步请求

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

目标: 在未修复的代码上运行，验证 UserService 的同步数据库方法在异步上下文中导致事件循环阻塞

Bug Condition:
- UserService 的所有方法都是同步的（使用 def 而不是 async def）
- 这些方法在异步上下文中被调用（AuthService.login(), AuthMiddleware 等）
- 同步的 SQLAlchemy 数据库查询阻塞异步事件循环
- 请求在中间件层就被阻塞，永远无法到达路由层

测试策略:
1. 模拟登录请求（AuthService.login() 调用 UserService.find_user_by_account()）
2. 模拟认证中间件场景（需要认证的请求调用 UserService.find_user_by_id()）
3. 模拟注册请求（AuthService.register() 调用 UserService.create_user()）
4. 模拟并发登录请求
5. 设置 5 秒超时
6. 观察请求是否超时（未修复代码上会超时）
7. 记录反例以理解根本原因

预期结果（未修复代码）:
- 测试失败（请求超时或响应时间 > 5 秒）
- 这证明 bug 存在

预期结果（修复后）:
- 测试通过（请求在 5 秒内完成）
- 这证明 bug 已修复
"""
import pytest
import asyncio
import time
from httpx import AsyncClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, Tenant, UserProfile
from sqlalchemy.orm import Session
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
    """设置测试数据：租户和用户"""
    # 创建测试租户
    tenant = test_db.query(Tenant).filter(Tenant.name == "测试租户_UserService阻塞").first()
    if not tenant:
        tenant = Tenant(name="测试租户_UserService阻塞")
        test_db.add(tenant)
        test_db.commit()
        test_db.refresh(tenant)
    
    # 创建测试用户
    user = test_db.query(User).filter(
        User.account == "userservice_test_user",
        User.tenant_id == tenant.id
    ).first()
    
    if not user:
        from app.core.security import hash_password
        user = User(
            account="userservice_test_user",
            password_hash=hash_password("test123456"),
            name="UserService测试用户",
            email="userservice@test.com",
            phone="13800000001",
            tenant_id=tenant.id,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        # 创建用户扩展信息
        profile = test_db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile:
            from datetime import datetime
            profile = UserProfile(
                tenant_id=tenant.id,
                user_id=user.id,
                identity_type="student",
                entry_year=datetime.now().year
            )
            test_db.add(profile)
            test_db.commit()
    
    yield {"tenant_id": tenant.id, "user": user}


@pytest.mark.asyncio
async def test_login_request_timeout_bug_condition(setup_test_data):
    """
    Property 1: Bug Condition - 登录请求中 UserService.find_user_by_account() 阻塞
    
    测试场景：
    - AuthService.login() (异步) 调用 UserService.find_user_by_account() (同步)
    - 同步的数据库查询阻塞异步事件循环
    
    Bug Condition: 
    - context.is_async == True (AuthService.login 是 async def)
    - method_call.target == UserService
    - method_call.method.is_sync == True (find_user_by_account 是 def)
    - method_call.method.performs_database_query == True
    
    Expected Behavior (修复后):
    - 请求在 5 秒内完成
    - 返回 200 状态码
    - 返回有效的访问令牌
    
    Current Behavior (未修复):
    - 请求阻塞，超时（> 5 秒）
    - 后端没有任何日志输出（请求在中间件层就被阻塞）
    """
    tenant_id = setup_test_data["tenant_id"]
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 发送登录请求，设置 5 秒超时
            response = await asyncio.wait_for(
                client.post(
                    "/api/v1/auth/login",
                    json={
                        "account": "userservice_test_user",
                        "password": "test123456",
                        "tenant_id": tenant_id
                    }
                ),
                timeout=5.0
            )
            
            elapsed_time = time.time() - start_time
            
            # 断言：请求应在 5 秒内完成
            assert elapsed_time < 5.0, f"请求耗时 {elapsed_time:.2f} 秒，超过 5 秒阈值"
            
            # 断言：应返回成功状态码
            assert response.status_code == 200, f"期望状态码 200，实际 {response.status_code}"
            
            # 断言：应返回有效的响应数据
            data = response.json()
            assert "data" in data, "响应缺少 data 字段"
            assert "access_token" in data["data"], "响应缺少 access_token"
            
            logger.info(f"✅ 测试通过：登录请求在 {elapsed_time:.2f} 秒内完成")
            
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            
            # 记录反例
            counterexample = f"""
            反例记录 - 登录场景：
            - 请求：POST /api/v1/auth/login
            - 账号：userservice_test_user
            - 租户ID：{tenant_id}
            - 耗时：{elapsed_time:.2f} 秒（超时）
            - 问题：请求在 5 秒内未完成，触发超时
            - 调用链：AuthService.login() (async) -> UserService.find_user_by_account() (sync)
            - 根本原因：UserService.find_user_by_account() 是同步方法，使用 db.query() 进行同步数据库查询
            - 影响：同步的 SQLAlchemy 查询在异步事件循环中执行，阻塞整个事件循环
            - 后端日志：无（请求在到达路由层之前就被阻塞）
            """
            logger.error(counterexample)
            
            # 测试失败（未修复代码上的预期行为）
            pytest.fail(f"❌ Bug 确认：登录请求超时（{elapsed_time:.2f} 秒）\n{counterexample}")


@pytest.mark.asyncio
async def test_register_request_timeout_bug_condition(setup_test_data):
    """
    Property 1: Bug Condition - 注册请求中 UserService.create_user() 阻塞
    
    测试场景：
    - AuthService.register() (异步) 调用 UserService.create_user() (同步)
    - 同步的数据库操作阻塞异步事件循环
    
    Bug Condition:
    - context.is_async == True (AuthService.register 是 async def)
    - method_call.target == UserService
    - method_call.method.is_sync == True (create_user 是 def)
    - method_call.method.performs_database_query == True
    
    Expected Behavior (修复后):
    - 请求在 5 秒内完成
    - 返回 200 状态码
    - 成功创建新用户
    
    Current Behavior (未修复):
    - 请求阻塞，超时（> 5 秒）
    """
    tenant_id = setup_test_data["tenant_id"]
    
    # 生成唯一的账号名（避免重复）
    import uuid
    unique_account = f"new_user_{uuid.uuid4().hex[:8]}"
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        start_time = time.time()
        
        try:
            # 发送注册请求，设置 5 秒超时
            response = await asyncio.wait_for(
                client.post(
                    "/api/v1/auth/register",
                    json={
                        "account": unique_account,
                        "password": "test123456",
                        "name": "新用户",
                        "email": f"{unique_account}@test.com",
                        "phone": f"138{uuid.uuid4().hex[:8]}",
                        "tenant_id": tenant_id
                    }
                ),
                timeout=5.0
            )
            
            elapsed_time = time.time() - start_time
            
            # 断言：请求应在 5 秒内完成
            assert elapsed_time < 5.0, f"请求耗时 {elapsed_time:.2f} 秒，超过 5 秒阈值"
            
            # 断言：应返回成功状态码
            assert response.status_code == 200, f"期望状态码 200，实际 {response.status_code}"
            
            # 断言：应返回有效的响应数据
            data = response.json()
            assert "data" in data, "响应缺少 data 字段"
            assert "account" in data["data"], "响应缺少 account"
            
            logger.info(f"✅ 测试通过：注册请求在 {elapsed_time:.2f} 秒内完成")
            
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            
            counterexample = f"""
            反例记录 - 注册场景：
            - 请求：POST /api/v1/auth/register
            - 账号：{unique_account}
            - 租户ID：{tenant_id}
            - 耗时：{elapsed_time:.2f} 秒（超时）
            - 问题：请求在 5 秒内未完成，触发超时
            - 调用链：AuthService.register() (async) -> UserService.create_user() (sync)
            - 根本原因：UserService.create_user() 是同步方法，使用 db.add() 和 db.flush() 进行同步数据库操作
            - 影响：同步的数据库操作阻塞异步事件循环
            """
            logger.error(counterexample)
            
            pytest.fail(f"❌ Bug 确认：注册请求超时（{elapsed_time:.2f} 秒）\n{counterexample}")


@pytest.mark.asyncio
async def test_concurrent_login_requests_bug_condition(setup_test_data):
    """
    Property 1: Bug Condition - 并发登录请求全部阻塞
    
    测试场景：
    - 发送多个并发登录请求
    - 验证是否全部阻塞
    
    Bug Condition:
    - 多个异步请求同时调用 UserService 的同步方法
    - 每个请求都阻塞事件循环
    
    预期结果（未修复）:
    - 所有请求都超时
    - 证明问题不是偶发的，而是系统性的
    
    预期结果（修复后）:
    - 所有请求都在合理时间内完成
    - 并发请求能够正常处理
    """
    tenant_id = setup_test_data["tenant_id"]
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 创建 3 个并发请求
        tasks = []
        for i in range(3):
            task = client.post(
                "/api/v1/auth/login",
                json={
                    "account": "userservice_test_user",
                    "password": "test123456",
                    "tenant_id": tenant_id
                }
            )
            tasks.append(task)
        
        start_time = time.time()
        
        try:
            # 等待所有请求完成，设置 10 秒总超时
            responses = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=10.0
            )
            
            elapsed_time = time.time() - start_time
            
            # 检查每个响应
            success_count = 0
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(f"请求 {i+1} 失败：{response}")
                else:
                    assert response.status_code == 200, f"请求 {i+1} 状态码错误"
                    success_count += 1
            
            # 断言：所有请求都应成功
            assert success_count == 3, f"只有 {success_count}/3 个请求成功"
            
            # 断言：总耗时应在合理范围内（并发执行，不应是 3 * 5 秒）
            assert elapsed_time < 10.0, f"并发请求总耗时 {elapsed_time:.2f} 秒，超过阈值"
            
            logger.info(f"✅ 测试通过：3 个并发登录请求在 {elapsed_time:.2f} 秒内完成")
            
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            
            counterexample = f"""
            反例记录 - 并发场景：
            - 并发请求数：3
            - 请求：POST /api/v1/auth/login
            - 总耗时：{elapsed_time:.2f} 秒（超时）
            - 问题：所有并发请求都被阻塞
            - 调用链：每个请求都调用 AuthService.login() -> UserService.find_user_by_account()
            - 根本原因：UserService 的同步方法在每个请求中都阻塞事件循环
            - 影响：系统无法处理并发请求，严重影响性能和可用性
            - 预期行为：FastAPI 的异步特性应该允许并发处理多个请求
            """
            logger.error(counterexample)
            
            pytest.fail(f"❌ Bug 确认：并发登录请求全部超时（{elapsed_time:.2f} 秒）\n{counterexample}")


@pytest.mark.asyncio
async def test_authenticated_request_blocking_bug_condition(setup_test_data):
    """
    Property 1: Bug Condition - 认证中间件中 UserService.find_user_by_id() 阻塞
    
    测试场景：
    - 先登录获取访问令牌
    - 发送需要认证的请求（如获取用户信息）
    - AuthMiddleware 可能调用 UserService.find_user_by_id() 验证用户状态
    
    Bug Condition:
    - context.is_async == True (AuthMiddleware.dispatch 是 async def)
    - method_call.target == UserService
    - method_call.method.is_sync == True (find_user_by_id 是 def)
    - method_call.method.performs_database_query == True
    
    Expected Behavior (修复后):
    - 认证请求在 5 秒内完成
    - 返回正确的用户信息
    
    Current Behavior (未修复):
    - 请求可能阻塞（如果中间件调用了 UserService）
    
    注意：这个测试可能不会失败，因为当前的 AuthMiddleware 实现可能不直接调用 UserService
    但我们仍然测试以确保完整性
    """
    tenant_id = setup_test_data["tenant_id"]
    user = setup_test_data["user"]
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 第一步：登录获取令牌
        try:
            login_response = await asyncio.wait_for(
                client.post(
                    "/api/v1/auth/login",
                    json={
                        "account": "userservice_test_user",
                        "password": "test123456",
                        "tenant_id": tenant_id
                    }
                ),
                timeout=5.0
            )
            
            if login_response.status_code != 200:
                pytest.skip("登录失败，跳过认证请求测试")
            
            data = login_response.json()
            access_token = data["data"]["access_token"]
            
        except asyncio.TimeoutError:
            pytest.skip("登录超时，跳过认证请求测试（登录问题已在其他测试中覆盖）")
        
        # 第二步：发送需要认证的请求
        start_time = time.time()
        
        try:
            # 发送获取用户信息的请求（需要认证）
            response = await asyncio.wait_for(
                client.get(
                    "/api/v1/users/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                ),
                timeout=5.0
            )
            
            elapsed_time = time.time() - start_time
            
            # 断言：请求应在 5 秒内完成
            assert elapsed_time < 5.0, f"请求耗时 {elapsed_time:.2f} 秒，超过 5 秒阈值"
            
            # 断言：应返回成功状态码
            assert response.status_code == 200, f"期望状态码 200，实际 {response.status_code}"
            
            logger.info(f"✅ 测试通过：认证请求在 {elapsed_time:.2f} 秒内完成")
            
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            
            counterexample = f"""
            反例记录 - 认证中间件场景：
            - 请求：GET /api/v1/users/me
            - 用户ID：{user.id}
            - 租户ID：{tenant_id}
            - 耗时：{elapsed_time:.2f} 秒（超时）
            - 问题：需要认证的请求在 5 秒内未完成
            - 可能的调用链：AuthMiddleware.dispatch() (async) -> UserService.find_user_by_id() (sync)
            - 根本原因：如果中间件调用了 UserService 的同步方法，会阻塞事件循环
            """
            logger.error(counterexample)
            
            pytest.fail(f"❌ Bug 确认：认证请求超时（{elapsed_time:.2f} 秒）\n{counterexample}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
