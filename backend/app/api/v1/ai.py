# app/api/v1/ai.py
"""
AI 相关 API 端点

路由列表:
    POST /ai/generate-form  生成表单配置

请求格式:
    {
        "prompt": str,  # 需求描述 (5-2000字符)
        "thinking_type": str  # 思考模式 (可选: enabled/disabled)
    }

响应格式:
    {
        "code": 2000,
        "message": "表单配置生成成功",
        "data": {
            "config": {...},  # 完整的表单配置 JSON
            "summary": "已生成...",  # 配置说明
            "field_count": 8,  # 字段数量
            "rule_count": 1  # 逻辑规则数量
        }
    }
"""
from fastapi import APIRouter, Body
from app.schemas.ai_schemas import (
    AIFormGenerateRequest,
    AIFormGenerateResponse,
    ThinkingType
)
from app.core.response import success_response, error_response
from app.core.exceptions import ValidationError, BusinessError
from app.services.ai_task_service import AITaskService, TaskStatus
from app.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate-form", summary="AI 生成表单配置")
async def generate_form(request: "AIFormGenerateRequest" = Body(...)):
    """
    根据用户需求描述生成表单配置

    **功能说明:**
    - 使用智谱 AI GLM-4.5-Flash 模型
    - 支持深度思考模式（适用于复杂表单）
    - 自动生成符合规范的表单 JSON 配置

    **请求参数:**
    - prompt (str, 必需): 表单需求描述，5-2000 字符
    - thinking_type (str, 可选): 思考模式，enabled（启用）或 disabled（禁用），默认 enabled

    **响应字段:**
    - config (object): 完整的表单配置，包含 formSchema、uiSchema、logicSchema
    - summary (str): 配置说明
    - field_count (int): 字段数量
    - rule_count (int): 逻辑规则数量

    **请求示例:**
    ```json
    {
        "prompt": "创建一个学生请假申请表，需要学生姓名、学号、请假类型（事假/病假/公假）、请假时间（日期范围）、自动计算请假天数、请假事由、联系电话，病假需要上传病假证明",
        "thinking_type": "enabled"
    }
    ```

    **响应示例:**
    ```json
    {
        "code": 2000,
        "message": "表单配置生成成功",
        "data": {
            "config": {
                "name": "学生请假申请表",
                "category": "请假申请",
                "accessMode": "authenticated",
                "formSchema": {
                    "version": "1.0.0",
                    "fields": [...]
                },
                "uiSchema": {...},
                "logicSchema": {...}
            },
            "summary": "已生成「学生请假申请表」，包含 8 个字段，1 条逻辑规则",
            "field_count": 8,
            "rule_count": 1
        }
    }
    ```

    **错误码:**
    - 4001: 参数验证失败（prompt 为空或过短）
    - 4002: 业务错误（AI 服务未配置或调用失败）
    - 5001: 服务器内部错误
    """
    try:
        logger.info(f"[API] 收到生成请求: prompt_length={len(request.prompt)}, thinking={request.thinking_type}")

        # 调用服务层
        result = AIService.generate_form_config(
            prompt=request.prompt
        )

        logger.info(
            f"[API] 生成成功: field_count={result['field_count']}, "
            f"rule_count={result['rule_count']}"
        )

        return success_response(
            data=AIFormGenerateResponse(**result).dict(),
            message="表单配置生成成功"
        )

    except ValidationError as e:
        logger.warning(f"[API] 验证错误: {e}")
        return error_response(str(e), 4001)

    except BusinessError as e:
        logger.warning(f"[API] 业务错误: {e}")
        return error_response(str(e), 4002)

    except Exception as e:
        logger.error(f"[API] 未知错误: {e}", exc_info=True)
        return error_response("生成失败，请稍后重试", 5001)


@router.get("/task/{task_id}", summary="查询任务状态")
async def get_task_status(task_id: str):
    """
    查询 AI 生成任务状态

    **响应示例:**
    ```json
    {
        "code": 2000,
        "data": {
            "task_id": "uuid",
            "status": "completed",
            "result": { ... },
            "error": null
        }
    }
    ```
    """
    try:
        task = AITaskService.get_task(task_id)

        if not task:
            return error_response("任务不存在", 4041)

        response_data = {
            "task_id": task["task_id"],
            "status": task["status"],
            "result": task.get("result"),
            "error": task.get("error")
        }

        return success_response(data=response_data)
    except Exception as e:
        logger.error(f"[API] 查询任务失败: {e}")
        return error_response("查询失败", 5001)


def process_ai_task(task_id: str, prompt: str, thinking_type: str):
    """
    后台处理 AI 任务

    :param task_id: 任务 ID
    :param prompt: 用户需求
    :param thinking_type: 思考模式
    """
    try:
        logger.info(f"[后台任务] 开始处理: {task_id}")

        # 更新为处理中
        AITaskService.update_task_status(task_id, TaskStatus.PROCESSING)

        # 调用 AI 服务
        from app.schemas.ai_schemas import ThinkingType
        result = AIService.generate_form_config(
            prompt=prompt,
            thinking_type=ThinkingType(thinking_type)
        )

        # 更新为完成
        AITaskService.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            result=result
        )

        logger.info(f"[后台任务] 处理完成: {task_id}")
    except Exception as e:
        logger.error(f"[后台任务] 处理失败: {task_id}, {e}", exc_info=True)
        AITaskService.update_task_status(
            task_id,
            TaskStatus.FAILED,
            error=str(e)
        )