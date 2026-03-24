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
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'avg': lambda *args: sum(args) / len(args) if args else 0,
        'floor': lambda x: int(x),
        'ceil': lambda x: int(x) + (1 if x % 1 > 0 else 0),

        'diffDays': lambda end, start: FormulaService._diff_days(end, start),
        'diffHours': lambda end, start: FormulaService._diff_hours(end, start),
        'today': lambda: datetime.now().strftime('%Y-%m-%d'),
        'now': lambda: datetime.now().isoformat(),

        'concat': lambda *args: ''.join(str(x) for x in args),
        'length': len,
        'upper': str.upper,
        'lower': str.lower,
        'trim': str.strip,

        'if': lambda cond, true_val, false_val: true_val if cond else false_val,
    }

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, (int, float)):
            if value > 1e12:
                return datetime.fromtimestamp(value / 1000)
            else:
                return datetime.fromtimestamp(value)
        elif isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.strptime(value, '%Y-%m-%d')
        elif isinstance(value, datetime):
            return value
        else:
            raise ValidationError(f"无法解析日期值: {value}")

    @staticmethod
    def _diff_days(end: Any, start: Any) -> int:
        end_dt = FormulaService._parse_datetime(end)
        start_dt = FormulaService._parse_datetime(start)
        return (end_dt - start_dt).days

    @staticmethod
    def _diff_hours(end: Any, start: Any) -> float:
        end_dt = FormulaService._parse_datetime(end)
        start_dt = FormulaService._parse_datetime(start)
        return (end_dt - start_dt).total_seconds() / 3600

    @staticmethod
    def extract_dependencies(formula: str) -> List[str]:
        """
        提取公式中的依赖字段

        Example:
            "${price} * ${quantity}" -> ["price", "quantity"]
            "${date_range}.start" -> ["date_range"]
        """
        pattern = r'\$\{(\w+)'
        return re.findall(pattern, formula)

    @staticmethod
    def replace_variables(formula: str, context: Dict[str, Any]) -> str:
        """
        替换公式中的变量引用

        支持以下格式：
        - ${field_name}: 直接引用字段值
        - ${field_name}.start: 引用日期范围字段的开始时间
        - ${field_name}.end: 引用日期范围字段的结束时间
        - ${field_name}[0], ${field_name}[1]: 引用数组字段的元素

        Example:
            formula: "${price} * ${quantity}"
            context: {"price": 100, "quantity": 5}
            返回: "100 * 5"

            formula: "diffDays(${date_range}.end, ${date_range}.start) + 1"
            context: {"date_range": [1774108800000, 1774540800000]}
            返回: "diffDays(1774540800000, 1774108800000) + 1"
        """

        def full_replace(match):
            field_name = match.group(1)
            prop_access = match.group(2)

            if field_name not in context:
                raise ValidationError(f"公式引用了不存在的字段: {field_name}")

            value = context[field_name]

            if prop_access:
                if prop_access == 'start':
                    if isinstance(value, list) and len(value) >= 1:
                        val = value[0]
                    elif isinstance(value, dict) and 'start' in value:
                        val = value['start']
                    else:
                        raise ValidationError(f"字段 {field_name} 不支持 .start 访问")
                elif prop_access == 'end':
                    if isinstance(value, list) and len(value) >= 2:
                        val = value[1]
                    elif isinstance(value, dict) and 'end' in value:
                        val = value['end']
                    else:
                        raise ValidationError(f"字段 {field_name} 不支持 .end 访问")
                else:
                    raise ValidationError(f"不支持的属性访问: .{prop_access}")
            else:
                val = value

            if isinstance(val, str):
                return f'"{val}"'
            return str(val)

        pattern = r'\$\{(\w+)\}(?:\.(start|end))?'
        return re.sub(pattern, full_replace, formula)

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