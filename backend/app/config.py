# app/config.py
"""
系统配置管理模块
使用Pydantic Settings统一管理环境变量
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import secrets


class Settings(BaseSettings):
    """系统配置类"""

    # 基础配置
    PROJECT_NAME: str = "FormFlow"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # 安全配置
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15分钟
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7天

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "13579qwe"

    # 构建数据库URL
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_EXPIRE_SECONDS: int = 3600  # 默认缓存1小时

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx", ".xls", ".xlsx"]

    # 管理员CRUD白名单
    ADMIN_CRUD_WHITELIST: List[str] = [
        "user", "department", "position", "role", "form", "submission",
        "activity", "resource", "notification_log", "dict_item"
    ]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    # ========== 文件存储配置 ==========
    STORAGE_TYPE: str = "minio"  # local / minio
    UPLOAD_BASE_DIR: str = "uploads"  # 本地存储时的路径

    # MinIO配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_SECURE: bool = False  # 生产环境改为True
    MINIO_BUCKET: str = "formflow"
    MINIO_PUBLIC_BUCKET: str = "formflow-public"  # 公开访问的bucket

    # 文件限制
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_MAX_TOTAL_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {
        '.pdf', '.jpg', '.jpeg', '.png',
        '.doc', '.docx', '.xls', '.xlsx', '.zip'
    }

    # ========== AI配置 ==========
    GLM_API_KEY: str = "d00b73355718453897b8ac77aea684e7.08pMGeEK0F16Xwu4"  # 智谱 AI API Key
    GLM_MODEL: str = "glm-4.5-flash"  # 模型名称
    GLM_THINKING_TYPE: str = "disabled"  # 思考模式：enabled/disabled
    GLM_MAX_TOKENS: int = 4096  # 最大输出 tokens
    GLM_TEMPERATURE: float = 0.7  # 温度参数（0-1）
    GLM_STREAM: bool = False  # 是否启用流式输出（AI表单生成不需要流式）
    GLM_TIMEOUT: int = 120  # ✅ 新增：超时时间（秒），默认 120 秒
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"

    # ========== 导出配置 ==========
    EXPORT_ASYNC_THRESHOLD: int = 1000  # 超过1000条异步导出
    EXPORT_TEMP_DIR: str = "temp/exports"
    EXPORT_EXPIRE_HOURS: int = 24  # 导出文件保留24小时

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()