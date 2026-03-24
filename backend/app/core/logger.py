# app/core/logger.py
"""
日志系统配置
结构化日志，支持文件和控制台输出
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict
import json
from datetime import datetime
from app.config import settings


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
        }

        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'tenant_id'):
            log_data['tenant_id'] = record.tenant_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'ip'):
            log_data['ip'] = record.ip

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器（用于控制台）"""

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录，添加颜色"""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        record.msg = f"{log_color}{record.msg}{self.RESET}"
        return super().format(record)


def setup_logger() -> logging.Logger:
    """
    设置日志系统

    Returns:
        配置好的根日志记录器
    """
    # 创建日志目录
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(exist_ok=True)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # 清除已有的处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # 开发环境使用彩色格式，生产环境使用结构化格式
    if settings.LOG_LEVEL == "DEBUG":
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        console_formatter = StructuredFormatter()

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器 - 按日期轮转
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "formflow.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)

    # 错误日志单独记录
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "error.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)

    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)

    return root_logger


# 创建全局日志记录器
logger = setup_logger()


class LoggerAdapter:
    """
    日志适配器，添加上下文信息
    """

    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        self.logger = logger
        self.extra = extra

    def _log(self, level: str, msg: str, *args, **kwargs):
        """内部日志方法"""
        kwargs.setdefault('extra', {}).update(self.extra)
        getattr(self.logger, level)(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        self._log('debug', msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self._log('info', msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._log('warning', msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self._log('error', msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self._log('critical', msg, *args, **kwargs)


def get_logger(
        name: str,
        **context
) -> LoggerAdapter:
    """
    获取带上下文的日志记录器

    Args:
        name: 日志记录器名称
        **context: 上下文信息

    Returns:
        日志适配器
    """
    return LoggerAdapter(
        logging.getLogger(name),
        context
    )