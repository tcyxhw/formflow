# 登录请求超时修复设计文档

## Overview

本次修复针对审计日志装饰器在异步上下文中使用同步数据库会话导致的请求阻塞问题。核心策略是将审计日志记录改为后台任务异步执行，避免阻塞主请求流程，同时保持审计日志功能的完整性。

## Glossary

- **Bug_Condition (C)**: 审计日志装饰器在异步路由中被调用且 `db` 参数为 `None` 时，使用同步 `SessionLocal()` 创建会话
- **Property (P)**: 审计日志记录应该在后台异步执行，不阻塞主请求流程，请求应在 5 秒内完成
- **Preservation**: 现有的审计日志记录功能、数据格式、错误处理机制必须保持不变
- **SessionLocal()**: SQLAlchemy 的同步会话工厂，在异步上下文中调用会导致阻塞
- **create_audit_log**: 异步函数，用于创建审计日志记录，当前在 `db=None` 时会调用同步的 `SessionLocal()`
- **@audit_log**: 装饰器，自动为路由添加审计日志记录功能
- **BackgroundTasks**: FastAPI 提供的后台任务机制，用于在响应返回后执行任务

## Bug Details

### Bug Condition

当使用 `@audit_log` 装饰器的异步路由被调用时，如果装饰器内部的 `create_audit_log` 函数没有接收到有效的 `db` 参数，会在异步上下文中调用同步的 `SessionLocal()` 创建数据库会话，导致事件循环阻塞。

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type RouteRequest
  OUTPUT: boolean
  
  RETURN input.route.has_decorator('@audit_log')
         AND input.route.is_async
         AND input.db_parameter IS None
         AND create_audit_log_calls_SessionLocal()
END FUNCTION
```

### Examples

- **登录接口**: 用户调用 `/api/v1/auth/login`，审计日志装饰器尝试记录日志，因为 `db=None`，调用 `SessionLocal()` 导致请求永久阻塞直到超时（30秒）
- **其他使用审计日志的接口**: 任何使用 `@audit_log` 装饰器且未正确传递 `db` 参数的异步路由都会触发相同问题
- **边缘情况**: 如果路由正确传递了 `db` 参数（通过 `Depends(get_db)`），则不会触发此问题

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- 审计日志的数据格式和字段必须保持不变（`tenant_id`, `actor_user_id`, `action`, `resource_type`, `resource_id`, `before_json`, `after_json`, `ip`, `ua`）
- 审计日志记录失败时，主请求流程不应受影响（现有的 try-except 错误处理逻辑）
- 其他不使用审计日志装饰器的接口应继续正常工作
- 审计日志装饰器的参数和使用方式应保持向后兼容

**Scope:**
所有不涉及审计日志装饰器的请求应完全不受影响。这包括：
- 不使用 `@audit_log` 装饰器的路由
- 直接调用数据库的业务逻辑
- 其他中间件和依赖注入

## Hypothesized Root Cause

基于代码分析，问题的根本原因是：

1. **同步会话在异步上下文中的使用**: `create_audit_log` 是异步函数，但在 `db=None` 时调用同步的 `SessionLocal()` 创建会话。在异步事件循环中，同步的数据库操作会阻塞整个事件循环。

2. **装饰器设计缺陷**: 装饰器依赖于路由通过 `kwargs` 传递 `db` 参数，但这种隐式依赖容易被遗漏，导致 `db=None` 的情况。

3. **缺少异步会话支持**: 当前项目只配置了同步的 `SessionLocal`，没有配置异步数据库引擎和会话工厂。

4. **审计日志阻塞主流程**: 审计日志记录在主请求流程中同步执行，即使使用异步函数，仍然会等待数据库操作完成才返回响应。

## Correctness Properties

Property 1: Bug Condition - 审计日志不阻塞请求

_For any_ 使用 `@audit_log` 装饰器的异步路由请求，审计日志记录 SHALL 在后台任务中异步执行，主请求 SHALL 在 5 秒内完成并返回响应，不被审计日志记录阻塞。

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - 审计日志功能完整性

_For any_ 成功的审计日志记录，数据库中 SHALL 保存完整的审计记录，包含所有必需字段（`tenant_id`, `actor_user_id`, `action`, `resource_type`, `resource_id`, `before_json`, `after_json`, `ip`, `ua`），且格式与原有实现完全一致。

**Validates: Requirements 3.1, 3.3**

## Fix Implementation

### Changes Required

假设我们的根因分析正确，需要进行以下修改：

**File**: `backend/app/utils/audit.py`

**Function**: `audit_log` 装饰器和 `create_audit_log` 函数

**Specific Changes**:

1. **引入后台任务机制**: 
   - 在装饰器中检测 FastAPI 的 `BackgroundTasks` 参数
   - 将审计日志记录改为后台任务，避免阻塞主请求流程

2. **创建独立的后台任务函数**:
   - 新增 `_background_create_audit_log` 函数，在后台任务中创建新的数据库会话
   - 该函数接收所有必需的审计信息作为参数，不依赖请求上下文

3. **修改装饰器逻辑**:
   - 在 `async_wrapper` 中提取所有审计所需信息（`action`, `resource_type`, `resource_id`, `tenant_id`, `actor_user_id`, `ip`, `ua`, `before_data`, `after_data`）
   - 如果检测到 `BackgroundTasks` 参数，将审计日志记录添加到后台任务
   - 如果没有 `BackgroundTasks`，记录警告日志并跳过审计记录（降级处理）

4. **保持向后兼容**:
   - 如果路由传递了 `db` 参数且没有 `BackgroundTasks`，保持原有的同步记录逻辑（用于同步路由）
   - 保持所有现有的错误处理逻辑

5. **移除阻塞性的 SessionLocal() 调用**:
   - 在 `create_audit_log` 中，如果 `db=None` 且在异步上下文中，不再调用 `SessionLocal()`
   - 改为记录警告日志，提示应使用后台任务

### Implementation Details

**新增函数签名**:
```python
def _background_create_audit_log(
    action: str,
    resource_type: str,
    resource_id: Optional[int],
    before_data: Optional[dict],
    after_data: Optional[dict],
    tenant_id: Optional[int],
    actor_user_id: Optional[int],
    ip: Optional[str],
    ua: Optional[str]
) -> None:
    """在后台任务中创建审计日志（使用独立的同步会话）"""
```

**装饰器修改逻辑**:
```python
# 在 async_wrapper 中
background_tasks = kwargs.get('background_tasks')

if background_tasks:
    # 提取所有审计信息
    audit_info = {
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'before_data': before_data,
        'after_data': after_data,
        'tenant_id': audit_tenant_id,
        'actor_user_id': audit_user_id,
        'ip': ip,
        'ua': ua
    }
    # 添加到后台任务
    background_tasks.add_task(_background_create_audit_log, **audit_info)
else:
    logger.warning(f"审计日志装饰器未检测到 BackgroundTasks，跳过审计记录: {action}")
```

**路由修改**:
所有使用 `@audit_log` 装饰器的异步路由需要添加 `BackgroundTasks` 参数：
```python
from fastapi import BackgroundTasks

@router.post("/login")
@audit_log(...)
async def login(
    login_request: LoginRequest,
    request: Request,
    background_tasks: BackgroundTasks,  # 新增
    db: Session = Depends(get_db)
):
    ...
```

## Testing Strategy

### Validation Approach

测试策略分为两个阶段：首先在未修复的代码上运行探索性测试，验证问题确实存在；然后在修复后验证问题已解决且现有功能未受影响。

### Exploratory Bug Condition Checking

**Goal**: 在实施修复前，通过测试确认问题的存在和根本原因。如果测试结果与假设不符，需要重新分析根因。

**Test Plan**: 编写集成测试，模拟登录请求，在未修复的代码上运行，观察请求是否超时。使用日志和性能监控确认阻塞发生在审计日志记录阶段。

**Test Cases**:
1. **登录请求超时测试**: 调用登录接口，设置 5 秒超时，观察请求是否超时（未修复代码上会失败）
2. **审计日志装饰器阻塞测试**: 创建一个测试路由使用 `@audit_log` 装饰器且不传递 `db` 参数，验证是否阻塞（未修复代码上会失败）
3. **SessionLocal 调用追踪**: 使用日志或调试器确认 `SessionLocal()` 在异步上下文中被调用（未修复代码上会观察到）
4. **正常传递 db 参数的路由**: 验证传递了 `db` 参数的路由不会超时（未修复代码上应该通过）

**Expected Counterexamples**:
- 登录请求在 30 秒后超时，没有返回响应
- 日志显示审计日志记录过程中调用了 `SessionLocal()`
- 可能的根因确认：同步会话在异步上下文中阻塞事件循环

### Fix Checking

**Goal**: 验证修复后，所有触发 bug 条件的输入都能正常工作，请求不再被阻塞。

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  start_time := current_time()
  result := call_route_with_audit_log(input)
  elapsed_time := current_time() - start_time
  
  ASSERT result.status_code == 200
  ASSERT elapsed_time < 5 seconds
  ASSERT audit_log_created_in_background()
END FOR
```

**Test Cases**:
1. **登录接口响应时间**: 调用登录接口，验证响应时间 < 5 秒
2. **审计日志后台记录**: 验证审计日志在后台任务中成功创建
3. **多个并发请求**: 发送多个并发登录请求，验证都能正常完成
4. **审计日志数据完整性**: 验证后台创建的审计日志包含所有必需字段

### Preservation Checking

**Goal**: 验证修复后，所有不触发 bug 条件的输入行为保持不变，现有功能未受影响。

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT route_behavior_after_fix(input) = route_behavior_before_fix(input)
END FOR
```

**Testing Approach**: 使用属性测试（Property-Based Testing）生成各种输入场景，验证审计日志的数据格式、字段内容、错误处理行为与修复前完全一致。

**Test Plan**: 在未修复代码上观察正常工作的场景（如传递了 `db` 参数的路由、不使用审计日志的路由），记录其行为，然后在修复后验证这些行为保持不变。

**Test Cases**:
1. **审计日志数据格式保持不变**: 对比修复前后审计日志记录的字段和格式
2. **错误处理逻辑保持不变**: 模拟审计日志记录失败，验证主请求流程不受影响
3. **不使用审计日志的路由**: 验证其他路由的行为完全不变
4. **同步路由的审计日志**: 如果存在同步路由使用审计日志，验证其行为不变

### Unit Tests

- 测试 `_background_create_audit_log` 函数能正确创建审计日志记录
- 测试装饰器能正确检测 `BackgroundTasks` 参数
- 测试装饰器在没有 `BackgroundTasks` 时的降级处理（记录警告）
- 测试审计信息提取逻辑（`tenant_id`, `actor_user_id`, `ip`, `ua` 等）

### Property-Based Tests

- 生成随机的审计日志数据，验证后台任务能正确处理各种输入
- 生成随机的请求场景，验证装饰器在各种参数组合下都能正常工作
- 测试并发场景下审计日志记录的正确性

### Integration Tests

- 测试完整的登录流程，包括审计日志记录
- 测试多个使用审计日志的接口，验证都能正常工作
- 测试高并发场景下的审计日志记录
- 测试审计日志记录失败时的降级处理
