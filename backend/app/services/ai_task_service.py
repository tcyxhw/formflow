# app/services/ai_task_service.py
"""
AI 任务队列服务
"""
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"  # 等待中
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class AITaskService:
    """AI 任务服务"""

    # 简单的内存存储（生产环境应使用 Redis）
    _tasks: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def create_task(prompt: str, thinking_type: str) -> str:
        """
        创建任务

        :param prompt: 用户需求
        :param thinking_type: 思考模式
        :return: 任务 ID
        """
        task_id = str(uuid.uuid4())

        AITaskService._tasks[task_id] = {
            "task_id": task_id,
            "prompt": prompt,
            "thinking_type": thinking_type,
            "status": TaskStatus.PENDING,
            "result": None,
            "error": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        logger.info(f"[任务队列] 创建任务: {task_id}")
        return task_id

    @staticmethod
    def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        :param task_id: 任务 ID
        :return: 任务信息
        """
        return AITaskService._tasks.get(task_id)

    @staticmethod
    def update_task_status(task_id: str, status: TaskStatus, result: Any = None, error: str = None):
        """
        更新任务状态

        :param task_id: 任务 ID
        :param status: 新状态
        :param result: 结果（可选）
        :param error: 错误信息（可选）
        """
        task = AITaskService._tasks.get(task_id)
        if task:
            task["status"] = status
            task["updated_at"] = datetime.now()
            if result:
                task["result"] = result
            if error:
                task["error"] = error
            logger.info(f"[任务队列] 更新任务状态: {task_id} -> {status}")