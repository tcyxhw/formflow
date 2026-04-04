# app/services/ai_service.py
"""
AI 服务

负责调用智谱 AI GLM-4.5 模型生成表单配置
"""
from zai import ZhipuAiClient
from app.config import settings
from app.core.exceptions import ValidationError, BusinessError
from app.schemas.ai_schemas import ThinkingType
from typing import Dict, Any, Tuple
import json
import logging
import re

logger = logging.getLogger(__name__)


class AIService:
    """
    AI 服务类

    功能:
        - 调用智谱 AI GLM-4.5-Flash 模型
        - 生成符合规范的表单配置 JSON
        - 解析和验证 AI 返回结果
    """

    # ========== 常量定义 ==========
    REQUIRED_CONFIG_KEYS = ["name", "category", "formSchema"]
    REQUIRED_FIELD_KEYS = ["id", "type", "label"]
    ALLOWED_FIELD_TYPES = [
        "text", "textarea", "number", "phone", "email",
        "select", "radio", "checkbox", "switch",
        "date", "date-range", "time", "datetime",
        "rate", "upload", "calculated",
        "divider", "description"
    ]

    @staticmethod
    def generate_form_config(
            prompt: str,
            thinking_type: ThinkingType = ThinkingType.DISABLED
    ) -> Dict[str, Any]:
        """
        根据用户需求生成表单配置

        :param prompt: 用户需求描述文本
        :param thinking_type: AI 思考模式（enabled/disabled）
        :return: {
            "config": Dict[str, Any],  # 完整的表单配置，包含 name, category, formSchema, uiSchema, logicSchema
            "summary": str,  # 配置说明
            "field_count": int,  # 字段数量
            "rule_count": int  # 逻辑规则数量
        }
        :raises BusinessError: AI 服务调用失败
        :raises ValidationError: 配置验证失败

        时间复杂度: O(1) - API 调用时间
        空间复杂度: O(n) - n 为生成的 JSON 大小
        """
        # ========== 1. 参数校验 ==========
        logger.info(f"[AI生成] 开始生成表单配置，prompt长度={len(prompt)}, thinking_type={thinking_type}")

        if not prompt or not prompt.strip():
            logger.warning("[AI生成] 空的提示词")
            raise ValidationError("需求描述不能为空")

        if len(prompt.strip()) < 5:
            logger.warning(f"[AI生成] 提示词过短: {len(prompt.strip())} 字符")
            raise ValidationError("需求描述至少需要 5 个字符")

        # ========== 2. 检查 API 配置 ==========
        if not settings.GLM_API_KEY:
            logger.error("[AI生成] GLM_API_KEY 未配置")
            raise BusinessError("AI 服务未配置，请联系管理员")

        try:
            # ========== 3. 初始化客户端 ==========
            # ✅ 修改：使用 httpx.Timeout 明确设置所有超时参数
            import httpx
            timeout_config = httpx.Timeout(
                timeout=float(settings.GLM_TIMEOUT),
                connect=30.0,
                read=float(settings.GLM_TIMEOUT),
                write=10.0,
                pool=10.0
            )
            client = ZhipuAiClient(
                api_key=settings.GLM_API_KEY,
                timeout=timeout_config,
                max_retries=0,  # 禁用 SDK 内部重试，避免 429 时反复消耗配额
            )
            logger.info(
                f"[AI生成] 初始化客户端成功，model={settings.GLM_MODEL}, "
                f"timeout={settings.GLM_TIMEOUT}s"
            )

            # ========== 4. 构建完整提示词 ==========
            full_prompt = AIService._build_prompt(prompt.strip())
            logger.debug(f"[AI生成] 完整提示词长度={len(full_prompt)}")

            # ========== 5. 调用 API ==========
            logger.info(
                f"[AI生成] 调用 API: model={settings.GLM_MODEL}, "
                f"thinking={thinking_type}, max_tokens={settings.GLM_MAX_TOKENS}, "
                f"temperature={settings.GLM_TEMPERATURE}"
            )

            response = client.chat.completions.create(
                model=settings.GLM_MODEL,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                thinking={
                    "type": thinking_type.value
                },
                stream=False,  # 不使用流式输出
                max_tokens=settings.GLM_MAX_TOKENS,
                temperature=settings.GLM_TEMPERATURE
            )

            # ========== 6. 提取响应内容 ==========
            if not response or not response.choices:
                logger.error("[AI生成] API 返回空响应")
                raise BusinessError("AI 服务返回异常")

            content = response.choices[0].message.content
            logger.info(f"[AI生成] 收到响应，内容长度={len(content)}")
            logger.debug(f"[AI生成] 响应内容预览: {content[:200]}...")

            # ========== 7. 解析响应 ==========
            config = AIService._parse_response(content)

            # ========== 8. 验证配置 ==========
            AIService._validate_config(config)

            # ========== 9. 生成统计信息 ==========
            stats = AIService._generate_stats(config)

            logger.info(
                f"[AI生成] 生成成功: name={config.get('name')}, "
                f"fields={stats['field_count']}, rules={stats['rule_count']}"
            )

            return {
                "config": config,
                "summary": stats["summary"],
                "field_count": stats["field_count"],
                "rule_count": stats["rule_count"]
            }

        except ValidationError:
            raise
        except BusinessError:
            raise
        except Exception as e:
            error_text = str(e)
            if "429" in error_text or "rate" in error_text.lower() or "速率限制" in error_text:
                logger.warning(f"[AI生成] GLM API 速率限制: {error_text}")
                raise BusinessError("AI 服务请求过于频繁，请稍后再试")
            logger.error(f"[AI生成] 未知错误: {e}", exc_info=True)
            raise BusinessError(f"AI 生成失败: {error_text}")

    @staticmethod
    def _build_prompt(user_prompt: str) -> str:
        """
        构建完整的 AI 提示词

        :param user_prompt: 用户输入的需求描述
        :return: 完整的提示词字符串

        时间复杂度: O(1)
        空间复杂度: O(n) - n 为提示词长度
        """
        from app.data.ai_prompts import FORM_GENERATION_PROMPT

        # ✅ 方法 1: 使用字符串拼接（推荐）
        return FORM_GENERATION_PROMPT + f"""

    ================================================================================

    [用户需求]
    {user_prompt}

    请根据上述需求生成完整的表单配置 JSON。
    """

    @staticmethod
    def _parse_response(content: str) -> Dict[str, Any]:
        """
        解析 AI 返回的响应内容

        :param content: AI 返回的文本内容
        :return: 解析后的配置字典
        :raises ValidationError: 解析失败

        时间复杂度: O(n) - n 为 content 长度
        空间复杂度: O(m) - m 为 JSON 对象大小
        """
        logger.debug("[AI解析] 开始解析响应内容")

        try:
            # 策略1: 提取 ```json ... ``` 代码块
            json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                logger.debug("[AI解析] 使用策略1: 匹配 json 代码块")
                json_str = json_match.group(1).strip()
                config = json.loads(json_str)
                logger.info("[AI解析] 策略1 解析成功")
                return config

            # 策略2: 提取 ```...``` 代码块（不带 json 标记）
            code_match = re.search(r'```\s*\n(.*?)\n```', content, re.DOTALL)
            if code_match:
                logger.debug("[AI解析] 使用策略2: 匹配通用代码块")
                json_str = code_match.group(1).strip()
                config = json.loads(json_str)
                logger.info("[AI解析] 策略2 解析成功")
                return config

            # 策略3: 直接查找 JSON 对象 {…}
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                logger.error("[AI解析] 未找到有效的 JSON 结构")
                raise ValueError("响应中未找到有效的 JSON 配置")

            logger.debug(f"[AI解析] 使用策略3: 提取 JSON 对象 [{json_start}:{json_end}]")
            json_str = content[json_start:json_end]
            config = json.loads(json_str)
            logger.info("[AI解析] 策略3 解析成功")
            return config

        except json.JSONDecodeError as e:
            logger.error(f"[AI解析] JSON 解析失败: {e}")
            logger.debug(f"[AI解析] 失败内容: {content[:500]}")
            raise ValidationError("AI 返回的配置格式错误，请重试")
        except Exception as e:
            logger.error(f"[AI解析] 解析异常: {e}", exc_info=True)
            raise ValidationError(f"解析 AI 响应失败: {str(e)}")

    @staticmethod
    def _validate_config(config: Dict[str, Any]) -> None:
        """验证配置的完整性和正确性（终极增强版）"""
        logger.debug("[AI验证] 开始验证配置")

        # 检查必需的顶层字段
        for key in AIService.REQUIRED_CONFIG_KEYS:
            if key not in config:
                raise ValidationError(f"配置缺少必需字段: {key}")

        # 检查 formSchema
        form_schema = config.get("formSchema", {})
        if not isinstance(form_schema, dict):
            raise ValidationError("formSchema 必须是对象")

        fields = form_schema.get("fields", [])
        if not fields or not isinstance(fields, list):
            raise ValidationError("表单至少需要一个字段")

        # 验证并修复每个字段
        field_ids = set()
        for idx, field in enumerate(fields):
            if not isinstance(field, dict):
                raise ValidationError(f"字段 {idx} 格式错误")

            # 检查必需字段
            for key in AIService.REQUIRED_FIELD_KEYS:
                if not field.get(key):
                    raise ValidationError(f"字段 {idx} 缺少 {key}")

            field_id = field.get("id")
            field_type = field.get("type")

            # ✅ 确保 props 存在
            if "props" not in field or field["props"] is None:
                logger.warning(f"[AI验证] 字段 {field_id} 缺少 props，自动补全为空对象")
                field["props"] = {}

            field_props = field["props"]

            # 检查 ID 唯一性
            if field_id in field_ids:
                raise ValidationError(f"字段 ID 重复: {field_id}")
            field_ids.add(field_id)

            # ✅ 分类型强制检查和修复 props
            if field_type == 'description':
                if not field_props.get('content'):
                    auto_content = field.get('label', '描述文本')
                    field_props['content'] = auto_content
                    logger.warning(
                        f"[AI验证] 字段 {field_id} (description) 缺少 props.content，自动补全为: {auto_content}")

            elif field_type in ['select', 'radio', 'checkbox']:
                options = field_props.get('options')
                if not options or not isinstance(options, list) or len(options) == 0:
                    default_options = [
                        {"label": "选项1", "value": "1"},
                        {"label": "选项2", "value": "2"}
                    ]
                    field_props['options'] = default_options
                    logger.warning(f"[AI验证] 字段 {field_id} ({field_type}) 缺少 props.options，自动补全")

            elif field_type == 'upload':
                if not field_props.get('action'):
                    field_props['action'] = '/api/v1/upload'
                    logger.warning(f"[AI验证] 字段 {field_id} (upload) 缺少 props.action，自动补全")
                if not field_props.get('accept'):
                    field_props['accept'] = '.pdf,.jpg,.png'
                if not field_props.get('maxSize'):
                    field_props['maxSize'] = 5242880
                if not field_props.get('maxCount'):
                    field_props['maxCount'] = 3

            elif field_type == 'calculated':
                if not field_props.get('formula'):
                    field_props['formula'] = '0'
                    field_props['dependencies'] = []
                    field_props['readonly'] = True
                    logger.warning(f"[AI验证] 字段 {field_id} (calculated) 缺少 props.formula，自动补全")

            elif field_type == 'divider':
                # divider 只需要空对象
                if not isinstance(field_props, dict):
                    field['props'] = {}

            elif field_type == 'date-range':
                if not isinstance(field_props.get('placeholder'), list):
                    field_props['placeholder'] = ['开始日期', '结束日期']
                if not field_props.get('format'):
                    field_props['format'] = 'yyyy-MM-dd'
                if not field_props.get('valueFormat'):
                    field_props['valueFormat'] = 'yyyy-MM-dd'

            elif field_type in ['text', 'textarea', 'number', 'phone', 'email']:
                if not field_props.get('placeholder'):
                    field_props['placeholder'] = f"请输入{field.get('label', '')}"

        # 检查 fieldOrder
        field_order = form_schema.get("fieldOrder", [])
        if set(field_order) != field_ids:
            logger.warning("[AI验证] fieldOrder 与 fields 不匹配，自动修复")
            form_schema["fieldOrder"] = list(field_ids)

        logger.info(f"[AI验证] 验证通过: {len(fields)} 个字段")

    @staticmethod
    def _generate_stats(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成配置统计信息

        :param config: 表单配置字典
        :return: {
            "field_count": int,  # 字段数量
            "rule_count": int,  # 逻辑规则数量
            "summary": str  # 文本说明
        }

        时间复杂度: O(n) - n 为字段数量
        空间复杂度: O(1)
        """
        field_count = len(config.get("formSchema", {}).get("fields", []))
        rule_count = len(config.get("logicSchema", {}).get("rules", []))

        summary_parts = [
            f"已生成「{config.get('name', '未命名')}」",
            f"包含 {field_count} 个字段"
        ]

        if rule_count > 0:
            summary_parts.append(f"{rule_count} 条逻辑规则")

        summary = "，".join(summary_parts)

        return {
            "field_count": field_count,
            "rule_count": rule_count,
            "summary": summary
        }