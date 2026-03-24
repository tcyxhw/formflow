"""
反例: 无替换需求也无测试隔离需求时的冗余抽象

何时算反模式:
- 只有一个实现
- 测试中也不需要替换
- 没有作为框架扩展点对外暴露
- ABC 存在的唯一效果是增加间接层和代码量

何时不算反模式:
- 需要在测试中替换为 fake/mock → 合理
- 有明确的多实现需求 → 合理
- 作为对外 SDK 的扩展接口 → 合理

问题:
- 读代码时必须在 ABC 和实现之间跳转
- 重命名方法需要改两处
- 没有带来实际灵活性收益
"""

from abc import ABC, abstractmethod


class FormQueryService(ABC):
    @abstractmethod
    def list_forms(self, tenant_id: str) -> list[dict]: ...


class SqlFormQueryService(FormQueryService):
    """永远只有这一个实现，测试也直接用它。"""

    def list_forms(self, tenant_id: str) -> list[dict]:
        return []


# 更简单的写法往往已经足够:
#
# class FormQueryService:
#     def list_forms(self, tenant_id: str) -> list[dict]:
#         return []
