"""
公式计算服务
"""
from simpleeval import simple_eval, InvalidExpression
from datetime import datetime, timedelta
import re
from typing import Any, List, Dict
from app.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class FormulaService:
    """公式计算服务"""

    # 支持的函数
    FUNCTIONS = {
        # 数学函数
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'avg': lambda *args: sum(args) / len(args) if args else 0,
        'floor': lambda x: int(x),
        'ceil': lambda x: int(x) + (1 if x % 1 > 0 else 0),

        # 日期函数
        'diffDays': lambda end, start: (
                datetime.fromisoformat(str(end)) - datetime.fromisoformat(str(start))
        ).days,
        'diffHours': lambda end, start: (
                                                datetime.fromisoformat(str(end)) - datetime.fromisoformat(str(start))
                                        ).total_seconds() / 3600,
        'today': lambda: datetime.now().strftime('%Y-%m-%d'),
        'now': lambda: datetime.now().isoformat(),

        # 文本函数
        'concat': lambda *args: ''.join(str(x) for x in args),
        'length': len,
        'upper': str.upper,
        'lower': str.lower,
        'trim': str.strip,

        # 条件函数
        'if': lambda cond, true_val, false_val: true_val if cond else false_val,
    }

    @staticmethod
    def extract_dependencies(formula: str) -> List[str]:
        """
        提取公式中的依赖字段

        Example:
            "${price} * ${quantity}" -> ["price", "quantity"]
        """
        pattern = r'\$\{(\w+)\}'
        return re.findall(pattern, formula)

    @staticmethod
    def replace_variables(formula: str, context: Dict[str, Any]) -> str:
        """
        替换公式中的变量引用

        Example:
            formula: "${price} * ${quantity}"
            context: {"price": 100, "quantity": 5}
            返回: "100 * 5"
        """

        def replace_func(match):
            field_name = match.group(1)
            if field_name not in context:
                raise ValidationError(f"公式引用了不存在的字段: {field_name}")
            value = context[field_name]
            # 字符串需要加引号
            if isinstance(value, str):
                return f'"{value}"'
            return str(value)

        return re.sub(r'\$\{(\w+)\}', replace_func, formula)

    @classmethod
    def evaluate(cls, formula: str, context: Dict[str, Any]) -> Any:
        """
        计算公式

        Args:
            formula: 公式字符串，如 "${price} * ${quantity}"
            context: 字段值字典，如 {"price": 100, "quantity": 5}

        Returns:
            计算结果

        Raises:
            ValidationError: 公式错误或计算失败
        """
        try:
            # 替换变量
            expression = cls.replace_variables(formula, context)

            # 计算表达式
            result = simple_eval(
                expression,
                functions=cls.FUNCTIONS
            )

            logger.debug(f"Formula: {formula} => {expression} = {result}")
            return result

        except InvalidExpression as e:
            raise ValidationError(f"公式语法错误: {str(e)}")
        except ZeroDivisionError:
            raise ValidationError("公式计算错误: 除数不能为零")
        except Exception as e:
            logger.error(f"Formula evaluation error: {formula}, {e}")
            raise ValidationError(f"公式计算失败: {str(e)}")

    @staticmethod
    def check_circular_dependency(fields: List[Dict]) -> bool:
        """
        检测循环依赖（拓扑排序）

        Args:
            fields: 字段列表，每个字段包含 id 和 type、props

        Returns:
            True if 有循环依赖, False otherwise
        """
        # 构建依赖图
        graph = {}
        for field in fields:
            if field.get('type') == 'calculated':
                formula = field.get('props', {}).get('formula', '')
                deps = FormulaService.extract_dependencies(formula)
                graph[field['id']] = deps

        # DFS检测环
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True

        return False

    @staticmethod
    def get_calculation_order(fields: List[Dict]) -> List[str]:
        """
        获取计算字段的拓扑排序顺序

        Returns:
            字段ID列表，按依赖顺序排列
        """
        # 构建依赖图
        graph = {}
        in_degree = {}

        for field in fields:
            field_id = field['id']
            in_degree[field_id] = 0

            if field.get('type') == 'calculated':
                formula = field.get('props', {}).get('formula', '')
                deps = FormulaService.extract_dependencies(formula)
                graph[field_id] = deps
            else:
                graph[field_id] = []

        # 计算入度
        for deps in graph.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        # Kahn算法拓扑排序
        queue = [k for k, v in in_degree.items() if v == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph.get(node, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return result