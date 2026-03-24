# SLA Timezone Fix Bugfix Design

## Overview

修复审批控制台中 SLA 时间计算错误的 bug。当前系统在 `approval_service.py` 和 `sla_service.py` 中混用了 `datetime.now()` (本地时间) 和 `datetime.utcnow()` (UTC 时间)，导致在 UTC+8 时区下 SLA 剩余时间计算出现 8 小时的偏差。修复策略是统一使用 timezone-aware 的 UTC 时间进行所有 SLA 相关计算，确保时区一致性。

## Glossary

- **Bug_Condition (C)**: 当系统使用 `datetime.utcnow()` 计算 SLA 剩余时间，而数据库中的 `due_at` 字段存储的是本地时间（或混合时区）时触发
- **Property (P)**: SLA 剩余时间计算应基于一致的时区（UTC），并在前端显示时转换为用户本地时区
- **Preservation**: 审批任务的其他时间字段（created_at、updated_at、claimed_at、completed_at）、SLA 超时判断逻辑、审批流程功能必须保持不变
- **TaskService**: `backend/app/services/approval_service.py` 中的服务类，负责审批任务的业务逻辑
- **SLAService**: `backend/app/services/sla_service.py` 中的服务类，负责 SLA 计算和超时处理
- **_calc_remaining_minutes**: TaskService 中计算 SLA 剩余分钟数的静态方法
- **calculate_due_at**: SLAService 中根据 SLA 时长计算到期时间的静态方法
- **is_overdue**: SLAService 中判断任务是否逾期的静态方法
- **timezone-aware datetime**: 包含时区信息的 datetime 对象，使用 `datetime.timezone.utc` 或 `pytz`

## Bug Details

### Bug Condition


当系统计算 SLA 剩余时间时，`_calc_remaining_minutes` 函数使用 `datetime.utcnow()` 获取当前时间，但与之比较的 `due_at` 时间可能是基于本地时区的，或者 `calculate_due_at` 函数使用 `datetime.utcnow()` 生成的时间在数据库中被误解为本地时间。这导致在 UTC+8 时区下，时间差计算出现 8 小时的系统性偏差。

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type {current_time: datetime, due_at: datetime}
  OUTPUT: boolean
  
  RETURN (current_time is naive datetime from datetime.utcnow())
         AND (due_at is naive datetime)
         AND (system timezone is UTC+8)
         AND (calculated_remaining_time != actual_remaining_time)
         AND (abs(calculated_remaining_time - actual_remaining_time) == 8 hours)
END FUNCTION
```

### Examples

- **示例 1**: 当前时间为 2026-03-14 09:41 (UTC+8 本地时间)，截止时间为 2026-03-15 17:30 (UTC+8 本地时间)
  - **预期行为**: 剩余时间应为约 31 小时 49 分钟
  - **实际行为**: 系统显示 39 小时 49 分钟（多了 8 小时）
  - **原因**: `datetime.utcnow()` 返回 2026-03-14 01:41 (UTC)，与 due_at 2026-03-15 17:30 比较时被当作同一时区

- **示例 2**: 创建一个 SLA 为 24 小时的审批任务
  - **预期行为**: 24 小时后到期
  - **实际行为**: 由于时区混淆，可能在 32 小时后才显示到期（或 16 小时后错误显示到期）

- **示例 3**: 判断任务是否逾期
  - **预期行为**: 准确判断是否超过截止时间
  - **实际行为**: 可能提前 8 小时或延后 8 小时判断为逾期

- **边缘情况**: 在 UTC 时区（UTC+0）运行的系统不会出现此 bug，因为 `datetime.utcnow()` 和本地时间一致

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- 审批任务的其他时间字段（created_at、updated_at、claimed_at、completed_at）必须继续正确记录和显示
- SLA 超时判断逻辑（is_overdue）在修复后必须保持相同的判断标准（基于 UTC 时间）
- 审批流程的其他功能（任务分配、认领、完成、转交、委派、加签）必须完全不受影响
- 表单截止时间验证（submission_service.py 中的 submit_deadline 检查）必须继续正常工作
- 定时任务调度（scheduler.py）的时间计算必须保持不变

**Scope:**
所有不涉及 SLA 剩余时间计算的功能应完全不受此修复影响。这包括：
- 任务创建、更新、删除操作
- 任务状态流转（open -> claimed -> completed）
- 任务查询和过滤（包括按 SLA 等级过滤）
- 任务操作日志记录
- 用户权限验证
- 多租户隔离

## Hypothesized Root Cause

基于代码分析，最可能的问题是：

1. **Naive Datetime 混用**: Python 的 `datetime.utcnow()` 和 `datetime.now()` 都返回 naive datetime（不包含时区信息），当这两种时间在不同模块中混用时，系统无法区分它们的实际时区，导致计算错误。

2. **数据库时区假设不一致**: SQLAlchemy 的 `DateTime` 列类型默认不存储时区信息。当 `calculate_due_at` 使用 `datetime.utcnow()` 生成时间并存入数据库时，数据库可能将其解释为本地时间，而读取时又被当作 UTC 时间。

3. **缺少时区转换层**: 系统没有统一的时区转换层，导致：
   - `sla_service.py` 使用 `datetime.utcnow()` 生成 due_at
   - `approval_service.py` 使用 `datetime.utcnow()` 计算剩余时间
   - 但两者之间的 due_at 在数据库存储和读取过程中可能发生时区解释偏差

4. **PostgreSQL 时区配置**: PostgreSQL 的 `timestamp without time zone` 类型不存储时区信息，如果数据库服务器配置为 UTC+8，而应用代码假设为 UTC，就会产生 8 小时偏差。

## Correctness Properties

Property 1: Bug Condition - SLA 剩余时间计算正确性

_For any_ 审批任务，当计算 SLA 剩余时间时，修复后的系统 SHALL 使用 timezone-aware 的 UTC datetime 对象进行计算，确保在任何时区下（包括 UTC+8）计算结果都与实际剩余时间一致，误差不超过 1 分钟（由于取整导致）。

**Validates: Requirements 2.1, 2.2, 2.3, 2.5**

Property 2: Preservation - 非 SLA 计算功能保持不变

_For any_ 审批任务操作（创建、认领、完成、转交等）和时间字段（created_at、updated_at、claimed_at、completed_at），修复后的系统 SHALL 产生与原系统完全相同的行为和数据，保持所有非 SLA 计算相关功能的正确性。

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

假设我们的根因分析正确，需要进行以下修改：

**File**: `backend/app/services/sla_service.py`

**Function**: `calculate_due_at`

**Specific Changes**:
1. **使用 timezone-aware datetime**: 将 `datetime.utcnow()` 替换为 `datetime.now(timezone.utc)`
   - 修改前: `return datetime.utcnow() + timedelta(hours=sla_hours)`
   - 修改后: `return datetime.now(timezone.utc) + timedelta(hours=sla_hours)`

2. **确保返回值包含时区信息**: 返回的 datetime 对象应明确标记为 UTC 时区

**File**: `backend/app/services/sla_service.py`

**Function**: `is_overdue`

**Specific Changes**:
3. **使用 timezone-aware datetime**: 将 `datetime.utcnow()` 替换为 `datetime.now(timezone.utc)`
   - 修改前: `return datetime.utcnow() > due_at`
   - 修改后: `return datetime.now(timezone.utc) > due_at`

4. **处理 naive datetime**: 如果 due_at 是 naive datetime，需要先将其转换为 UTC timezone-aware datetime

**File**: `backend/app/services/sla_service.py`

**Function**: `get_escalation_threshold`

**Specific Changes**:
5. **使用 timezone-aware datetime**: 将 `datetime.utcnow()` 替换为 `datetime.now(timezone.utc)`

**File**: `backend/app/services/approval_service.py`

**Function**: `_calc_remaining_minutes`

**Specific Changes**:
6. **使用 timezone-aware datetime**: 将 `datetime.utcnow()` 替换为 `datetime.now(timezone.utc)`
   - 修改前: `delta = due_at - datetime.utcnow()`
   - 修改后: `delta = due_at - datetime.now(timezone.utc)`

7. **处理 naive datetime**: 如果 due_at 是 naive datetime（来自旧数据），需要先假设其为 UTC 并添加时区信息

**File**: `backend/app/services/approval_service.py`

**Function**: `_apply_sla_level_filter`, `claim_task`, `perform_task_action`, `_build_task_response`

**Specific Changes**:
8. **统一时区处理**: 所有使用 `datetime.utcnow()` 的地方都替换为 `datetime.now(timezone.utc)`

9. **添加时区转换辅助函数**: 创建一个辅助函数 `ensure_utc_aware(dt: datetime) -> datetime`，用于将 naive datetime 转换为 UTC timezone-aware datetime

10. **数据库迁移考虑**: 虽然不需要修改数据库 schema（DateTime 列可以存储 timezone-aware datetime），但需要确保 SQLAlchemy 配置正确处理时区

## Testing Strategy

### Validation Approach

测试策略分为两个阶段：首先在未修复的代码上运行探索性测试，观察 bug 的具体表现并验证根因分析；然后在修复后的代码上运行修复验证测试和保持性测试，确保 bug 已修复且未引入回归。

### Exploratory Bug Condition Checking

**Goal**: 在未修复的代码上演示 bug，确认时区偏差确实为 8 小时，并验证根因假设。

**Test Plan**: 编写单元测试，模拟在 UTC+8 时区环境下创建审批任务并计算 SLA 剩余时间。使用 mock 或 freezegun 库固定当前时间，观察计算结果与预期的偏差。在未修复的代码上运行这些测试，预期会失败并显示 8 小时偏差。

**Test Cases**:
1. **基础时区偏差测试**: 固定当前时间为 2026-03-14 09:41 (UTC+8)，due_at 为 2026-03-15 17:30 (UTC+8)，计算剩余时间（在未修复代码上会失败，显示 39h49m 而非 31h49m）

2. **calculate_due_at 时区测试**: 调用 `calculate_due_at(24)` 创建 24 小时 SLA，检查返回的 due_at 是否为 timezone-aware 且为 UTC（在未修复代码上会返回 naive datetime）

3. **is_overdue 时区测试**: 创建一个已过期的任务（due_at 在 1 小时前），检查 `is_overdue` 是否正确判断（在未修复代码上可能因时区偏差误判）

4. **跨时区一致性测试**: 在不同时区环境（UTC+0, UTC+8, UTC-5）下运行相同的 SLA 计算，检查结果是否一致（在未修复代码上会不一致）

**Expected Counterexamples**:
- 在 UTC+8 环境下，剩余时间计算多出 8 小时
- `datetime.utcnow()` 返回的是 naive datetime，无法与 timezone-aware datetime 正确比较
- 不同时区环境下计算结果不一致

### Fix Checking

**Goal**: 验证修复后的代码在所有时区环境下都能正确计算 SLA 剩余时间。

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := _calc_remaining_minutes_fixed(input.due_at)
  expected := calculate_expected_remaining_minutes(input.due_at, input.current_time)
  ASSERT abs(result - expected) <= 1  # 允许 1 分钟误差（取整）
END FOR
```

**Test Cases**:
1. **UTC+8 环境修复验证**: 重新运行探索性测试用例 1，验证剩余时间计算正确为 31h49m
2. **Timezone-aware 验证**: 验证 `calculate_due_at` 返回的 datetime 对象包含 UTC 时区信息
3. **跨时区一致性验证**: 在多个时区环境下运行相同测试，验证结果一致
4. **边界条件测试**: 测试 due_at 为当前时间、过去时间、未来很远时间的情况

### Preservation Checking

**Goal**: 验证修复后的代码对于所有非 SLA 计算相关的功能，行为与原代码完全一致。

**Pseudocode:**
```
FOR ALL operation WHERE NOT affects_sla_calculation(operation) DO
  result_original := execute_on_original_code(operation)
  result_fixed := execute_on_fixed_code(operation)
  ASSERT result_original == result_fixed
END FOR
```

**Testing Approach**: 使用属性测试（Property-Based Testing）生成大量随机的审批任务操作序列，在修复前后的代码上执行，比较除 SLA 剩余时间外的所有输出是否一致。这能有效捕获意外的副作用。

**Test Plan**: 首先在未修复代码上观察并记录各种操作的行为（任务创建、认领、完成等），然后编写测试用例验证修复后这些行为保持不变。

**Test Cases**:
1. **任务创建时间保持**: 验证 created_at、updated_at 字段在修复前后记录的时间一致（格式可能变化但实际时刻相同）

2. **任务状态流转保持**: 验证任务从 open -> claimed -> completed 的状态流转逻辑不受影响

3. **SLA 超时判断保持**: 验证 `is_overdue` 的判断结果在修复前后一致（都基于 UTC 时间）

4. **任务查询过滤保持**: 验证按 SLA 等级过滤任务的结果在修复前后一致

5. **其他时间字段保持**: 验证 claimed_at、completed_at 等字段的记录逻辑不受影响

6. **表单截止时间保持**: 验证 submission_service.py 中的 submit_deadline 检查逻辑不受影响

### Unit Tests

- 测试 `calculate_due_at` 在不同 SLA 时长下返回正确的 timezone-aware UTC datetime
- 测试 `_calc_remaining_minutes` 在不同 due_at 值下计算正确的剩余分钟数
- 测试 `is_overdue` 正确判断任务是否逾期
- 测试时区转换辅助函数 `ensure_utc_aware` 正确处理 naive 和 aware datetime
- 测试边界条件：due_at 为 None、过去时间、当前时间、未来时间

### Property-Based Tests

- 生成随机的 SLA 时长（1-168 小时），验证 `calculate_due_at` 返回的时间始终在未来且时区为 UTC
- 生成随机的当前时间和 due_at，验证 `_calc_remaining_minutes` 计算结果与手动计算一致
- 生成随机的任务操作序列，验证修复前后除 SLA 计算外的所有行为一致
- 在多个时区环境（UTC+0, UTC+8, UTC-5, UTC+12）下运行相同测试，验证结果一致性

### Integration Tests

- 创建完整的审批流程，从任务创建到完成，验证 SLA 时间在整个流程中正确计算和显示
- 测试 SLA 升级（escalation）功能，验证超时任务能被正确识别和处理
- 测试前端显示，验证 UTC 时间能正确转换为用户本地时区显示（需要前端配合）
- 测试数据库持久化，验证 timezone-aware datetime 能正确存储和读取
- 测试历史数据兼容性，验证修复后的代码能正确处理数据库中已存在的 naive datetime 数据
