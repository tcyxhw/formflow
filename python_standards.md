
# Python 智能开发规范 v3.2 (最终定稿)

**核心理念**：思维先行 · 显式契约 · 极简落地

---

## 一、范式速查 (10秒决策)

在动手前，必须根据场景锁定范式：

| 场景特征 | 核心范式 | 关键工具库 | 决策理由 |
|:---|:---|:---|:---|
| **IO 密集** (API/爬虫) | **异步编程** | `asyncio`, `httpx` | 单线程高并发，吞吐量优先 |
| **CPU 密集** (计算) | **多进程** | `ProcessPoolExecutor` | 绕过 GIL，利用多核性能 |
| **大数据流** (ETL) | **生成器** | `yield` | O(1) 空间，防止内存溢出 |
| **核心业务** (领域) | **类型化 OOP** | `Pydantic` | 强数据契约，拒绝脏数据 |
| **胶水代码** (脚本) | **函数式** | 装饰器 | 开发效率优先 |

---

## 二、文档与契约规范

**1. 模块头部 (File Header)**
```python
"""
模块用途: [核心功能简述]
依赖配置: [外部依赖/环境变量]
数据流向: [源] -> [处理逻辑] -> [宿]
函数清单:
    - func_name(): 功能描述
"""
```

**2. 函数文档 (Sphinx Style)**
*必须标注复杂度，倒逼性能思考。*
```python
def process(data: str) -> bool:
    """
    功能描述。
    :param data: 参数说明
    :return: 返回值说明
    :raises ValueError: 触发条件
    
    Time: O(N), Space: O(1)
    """
```

---

## 三、核心法则 (High-Five Rules)

| # | 法则名称 | 具体要求 |
|:---|:---|:---|
| **①** | **拒绝裸奔** | 所有函数参数/返回值必须有 `Type Hints`；禁止无理由的 `Any`。 |
| **②** | **防御编程** | 入口必查边界 (Guard Clauses)；禁止裸 `except`，必须捕获具体异常。 |
| **③** | **资源安全** | 文件、网络、锁、DB 连接必须使用 `with` 上下文管理。 |
| **④** | **数据契约** | 涉及跨函数/跨层的数据传递，**强制使用 Pydantic**，禁止裸 Dict。 |
| **⑤** | **配置分离** | 禁止硬编码 (Hardcoding)，所有配置从 `os.getenv` 或配置类读取。 |

---

## 四、AI 协作协议 (Prompt)

复制此指令给 AI，可获得高质量代码：

```markdown
**[Python 专家模式]**
请遵循以下步骤编写代码：

1. **侦察 (Scout)**: 先分析场景（IO/CPU/流），选择最佳范式并简述理由。
2. **契约 (Contract)**: 
   - 编写标准文件头（用途/依赖/数据流）。
   - 全量 Type Hints + Pydantic 数据模型。
   - Sphinx Docstring + Time/Space 复杂度标注。
3. **稳健 (Robustness)**: 
   - 添加入口边界检查。
   - 使用 `with` 管理资源。
   - 捕获具体异常（非 try-except all）。
4. **交付 (Deliver)**: 提供 `if __name__ == '__main__':` 下的测试用例。
```

---

## 五、黄金样本 (Golden Sample)

```python
# -*- coding: utf-8 -*-
"""
模块用途: 订单日志流式分析器
依赖配置: 环境变量 LOG_PATH
数据流向: 日志文件 -> Generator流式读取 -> Pydantic清洗 -> 聚合统计
函数清单:
    - analyze_orders(path): 核心统计入口
"""

import os
import json
import logging
from typing import Generator, Dict, Any
from collections import defaultdict
from pydantic import BaseModel, Field, ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. 数据契约 ---
class OrderLog(BaseModel):
    id: str
    amount: float = Field(gt=0, description="金额需大于0")
    category: str

# --- 2. 核心逻辑 ---
def _stream_lines(path: str) -> Generator[str, None, None]:
    """流式读取文件，空间复杂度 O(1)"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path not found: {path}")
        
    with open(path, 'r', encoding='utf-8') as f:  # Rule ③: 资源安全
        for line in f:
            if line.strip(): yield line.strip()

def analyze_orders(file_path: str) -> Dict[str, float]:
    """
    统计各类目订单总额。
    
    :param file_path: 日志文件路径
    :return: {category: total_amount}
    :raises FileNotFoundError: 文件不存在
    
    Time: O(N), Space: O(K) K=类目数
    """
    stats = defaultdict(float)
    
    # Rule ②: 边界检查
    if not file_path:
        raise ValueError("File path cannot be empty")

    for line in _stream_lines(file_path):
        try:
            # Rule ④: Pydantic 校验
            order = OrderLog(**json.loads(line))
            stats[order.category] += order.amount
        except (json.JSONDecodeError, ValidationError) as e:
            # Rule ②: 具体异常捕获
            logger.warning(f"Skipping invalid log: {str(e)[:50]}...")
            continue
            
    return dict(stats)

# --- 3. 测试用例 ---
if __name__ == '__main__':
    import tempfile
    
    # Mock 数据
    data = '{"id":"1", "amount":100, "category":"A"}\n{"id":"2", "amount":-5, "category":"B"}'
    
    with tempfile.NamedTemporaryFile('w', suffix='.jsonl', delete=False) as tmp:
        tmp.write(data)
        path = tmp.name
        
    try:
        result = analyze_orders(path)
        print(f"Result: {result}")
        assert result['A'] == 100
        assert 'B' not in result # 负数金额应被过滤
        print("✅ Test Passed")
    finally:
        os.remove(path)
```

---

## 六、提交前自检 (Checklist)

*   [ ] **范式对吗？** (没用 List 存 1GB 数据吧？没在 for 循环里调 DB 吧？)
*   [ ] **类型全吗？** (函数参数都有 Type Hint 吗？)
*   [ ] **异常准吗？** (没写 `except Exception` 吧？)
*   [ ] **文档有吗？** (复杂度 `O(N)` 写了吗？)
*   [ ] **能跑通吗？** (`__main__` 里有测试吗？)