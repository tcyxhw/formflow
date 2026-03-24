"""
Bug Condition 探索性测试 - 审计日志阻塞异步请求

目标: 在未修复的代码上运行，验证审计日志装饰器在异步上下文中使用同步 SessionLocal() 导致请求阻塞

测试策略:
1. 模拟登录请求（使用 @audit_log 装饰器的异步路由）
2. 设置 5 秒超时
3. 观察请求是否超时（未修复代码上会超时）
4. 记录反例以理解根本原因

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
from app.core.database import get_db, SessionLocal
from app.models.user import User, Tenant
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
    tenant = test_db.query(Tenant).filter(Tenant.name == "测试租户_审计日志").first()
    if not tenant:
        tenant = Tenant(name="测试租户_审计日志")
        test_db.add(tenant)
        test_db.commit()
        test_db.refresh(tenant)
    
    # 创建测试用户
    user = test_db.query(User).filter(
        User.account == "audit_test_user",
        User.tenant_id == tenant.id
    ).first()
    
    if not user:
        from app.core.security import get_password_hash
        user = User(
            account="audit_test_user",
            password_hash=get_password_hash("test123456"),
            name="审计测试用户",
            tenant_id=tenant.id,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
    
    yield {"tenant_id": tenant.id, "user": user}
    
    # 清理（可选）
    # test_db.delete(user)
    # test_db.delete(tenant)
    # test_db.commit()


@pytest.mark.asyncio
async def test_login_request_timeout_bug_condition(setup_test_data):
    """
    Property 1: Bug Condition - 审计日志阻塞异步请求
    
    Bug Condition: 
    - 路由使用 @audit_log 装饰器
    - 路由是异步函数
    - db 参数为 None（装饰器内部会调用 SessionLocal()）
    
    Expected Behavior (修复后):
    - 请求在 5 秒内完成
    - 返回 200 状态码
    - 审计日志在后台任务中创建
    
    Current Behavior (未修复):
    - 请求阻塞，超时（> 5 秒）
    - 可能返回 504 Gateway Timeout
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
                        "account": "audit_test_user",
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
            反例记录：
            - 请求：POST /api/v1/auth/login
            - 账号：audit_test_user
            - 租户ID：{tenant_id}
            - 耗时：{elapsed_time:.2f} 秒（超时）
            - 问题：请求在 5 秒内未完成，触发超时
            - 根本原因：审计日志装饰器在异步上下文中调用同步 SessionLocal()
            """
            logger.error(counterexample)
            
            # 测试失败（未修复代码上的预期行为）
            pytest.fail(f"❌ Bug 确认：登录请求超时（{elapsed_time:.2f} 秒）\n{counterexample}")


@pytest.mark.asyncio
async def test_audit_log_decorator_blocking_with_no_db_parameter():
    """
    Property 1: Bug Condition - 审计日志装饰器在没有 db 参数时阻塞
    
    测试场景：
    - 创建一个使用 @audit_log 装饰器的测试路由
    - 不传递 db 参数
    - 验证是否阻塞
    
    这是一个更直接的测试，隔离了审计日志装饰器的问题
    """
    from fastapi import APIRouter, Request
    from app.utils.audit import audit_log
    from app.core.response import success_response
    
    # 创建测试路由
    test_router = APIRouter()
    
    @test_router.post("/test-audit-blocking")
    @audit_log(
        action="test_action",
        resource_type="test_resource",
        record_after=True
    )
    async def test_route_with_audit(request: Request):
        """测试路由：使用审计日志装饰器但不传递 db 参数"""
        return success_response(data={"message": "test"})
    
    # 将测试路由添加到应用
    app.include_router(test_router, prefix="/api/v1/test")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        start_time = time.time()
        
        try:
            # 发送请求，设置 5 秒超时
            response = await asyncio.wait_for(
                client.post("/api/v1/test/test-audit-blocking"),
                timeout=5.0
            )
            
            elapsed_time = time.time() - start_time
            
            # 断言：请求应在 5 秒内完成
            assert elapsed_time < 5.0, f"请求耗时 {elapsed_time:.2f} 秒，超过 5 秒阈值"
            assert response.status_code == 200
            
            logger.info(f"✅ 测试通过：审计日志装饰器未阻塞请求（{elapsed_time:.2f} 秒）")
            
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            
            counterexample = f"""
            反例记录：
            - 请求：POST /api/v1/test/test-audit-blocking
            - 装饰器：@audit_log(action="test_action", resource_type="test_resource")
            - db 参数：None（未传递）
            - 耗时：{elapsed_time:.2f} 秒（超时）
            - 问题：审计日志装饰器调用 create_audit_log 时，db=None 导致调用 SessionLocal()
            - 根本原因：SessionLocal() 是同步的，在异步上下文中阻塞事件循环
            """
            logger.error(counterexample)
            
            pytest.fail(f"❌ Bug 确认：审计日志装饰器阻塞请求（{elapsed_time:.2f} 秒）\n{counterexample}")


@pytest.mark.asyncio
async def test_concurrent_login_requests_bug_condition(setup_test_data):
    """
    Property 1: Bug Condition - 并发登录请求全部阻塞
    
    测试场景：
    - 发送多个并发登录请求
    - 验证是否全部阻塞
    
    预期结果（未修复）:
    - 所有请求都超时
    - 证明问题不是偶发的，而是系统性的
    
    预期结果（修复后）:
    - 所有请求都在 5 秒内完成
    """
    tenant_id = setup_test_data["tenant_id"]
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 创建 3 个并发请求
        tasks = []
        for i in range(3):
            task = client.post(
                "/api/v1/auth/login",
                json={
                    "account": "audit_test_user",
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
            反例记录：
            - 并发请求数：3
            - 请求：POST /api/v1/auth/login
            - 总耗时：{elapsed_time:.2f} 秒（超时）
            - 问题：所有并发请求都被阻塞
            - 根本原因：审计日志装饰器在每个请求中都调用同步 SessionLocal()，阻塞事件循环
            - 影响：系统无法处理并发请求，严重影响性能
            """
            logger.error(counterexample)
            
            pytest.fail(f"❌ Bug 确认：并发登录请求全部超时（{elapsed_time:.2f} 秒）\n{counterexample}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
