# AGENTS.md

## 项目概览
- 名称：FormFlow Backend —— 高校多租户表单与审批中台
- 目标用户/场景：高校信息化团队及审批业务部门，支撑多租户自助建表与流程管理
- 当前状态：Alpha（欠测、欠文档）
- 核心功能：多租户认证｜表单建模发布｜提交流程审批｜附件对象存储｜AI表单生成｜定时清理任务
- 技术栈：Python 3.10 / FastAPI / SQLAlchemy / Alembic / PostgreSQL / Redis / MinIO / APScheduler / JWT / JSON Logger / Uvicorn

## 目录树
```
backend/【项目根目录】[XL]
├─ .env【示例环境变量】[S]
├─ .idea/【IDE配置目录】[S]
│  ├─ .gitignore【IDE忽略规则】[S]
│  ├─ backend.iml【JetBrains模块】[S]
│  ├─ deployment.xml【部署设置】[S]
│  ├─ inspectionProfiles/【检查配置】[S]
│  │  ├─ Project_Default.xml【检查预设】[S]
│  │  └─ profiles_settings.xml【检查开关】[S]
│  ├─ misc.xml【工程设置】[S]
│  ├─ modules.xml【模块索引】[S]
│  └─ workspace.xml【个人工作区】[S]
├─ Dockerfile【TBD】[S]
├─ alembic/【迁移脚本目录】[S]
│  ├─ __init__.py【迁移包标识】[S]
│  └─ ⭐ env.py【Alembic环境】[S]
├─ alembic.ini【迁移主配置】[S]
├─ app/【主应用代码】[XL]
│  ├─ __init__.py【包标识】[S]
│  ├─ ⭐📦 main.py【FastAPI入口】[S]
│  ├─ ⭐ config.py【配置中心】[S]
│  ├─ api/【接口层】[L]
│  │  ├─ __init__.py【包标识】[S]
│  │  ├─ ⭐ deps.py【通用依赖】[S]
│  │  ├─ router.py【TBD】[S]
│  │  └─ v1/【v1路由集】[L]
│  │     ├─ ⭐ __init__.py【路由聚合】[S]
│  │     ├─ admin.py【系统管理API】[M]
│  │     ├─ ai.py【AI生成API】[S]
│  │     ├─ attachments.py【附件API】[S]
│  │     ├─ auth.py【认证API】[M]
│  │     ├─ forms.py【表单API】[M]
│  │     ├─ submissions.py【提交API】[M]
│  │     ├─ 📦 upload.py【上传控制器】[M]
│  │     └─ users.py【用户API】[M]
│  ├─ core/【基础设施】[M]
│  │  ├─ __init__.py【包标识】[S]
│  │  ├─ ⭐ database.py【会话工厂】[S]
│  │  ├─ ⭐📦 exception_handlers.py【异常注册】[S]
│  │  ├─ exceptions.py【业务异常】[S]
│  │  ├─ logger.py【结构化日志】[S]
│  │  ├─ ⭐ redis_client.py【Redis封装】[M]
│  │  ├─ response.py【统一响应】[S]
│  │  └─ ⭐ security.py【JWT工具】[S]
│  ├─ data/【内置数据】[M]
│  │  ├─ ai_prompts.py【AI提示语】[S]
│  │  └─ form_templates.py【表单模板】[M]
│  ├─ db/【数据库包】[S]
│  │  └─ __init__.py【占位】[S]
│  ├─ middleware/【中间件】[M]
│  │  ├─ __init__.py【包标识】[S]
│  │  ├─ auth.py【认证中间件】[M]
│  │  ├─ cors.py【TBD】[S]
│  │  ├─ logging.py【请求日志】[S]
│  │  └─ tenant.py【租户解析】[S]
│  ├─ models/【ORM模型】[M]
│  │  ├─ __init__.py【模型导出】[S]
│  │  ├─ activity.py【活动模型】[S]
│  │  ├─ base.py【基类与混入】[S]
│  │  ├─ form.py【表单模型】[S]
│  │  ├─ notification.py【通知模型】[S]
│  │  ├─ resource.py【资源模型】[S]
│  │  ├─ user.py【用户模型】[S]
│  │  └─ workflow.py【流程模型】[S]
│  ├─ schemas/【Pydantic模型】[M]
│  │  ├─ __init__.py【包标识】[S]
│  │  ├─ ai_schemas.py【AI枚举】[S]
│  │  ├─ auth.py【认证Schema】[S]
│  │  ├─ base.py【通用分页】[S]
│  │  ├─ form_schemas.py【表单Schema】[S]
│  │  ├─ submission_schemas.py【提交Schema】[S]
│  │  └─ user.py【用户Schema】[S]
│  ├─ services/【业务服务】[L]
│  │  ├─ __init__.py【包标识】[S]
│  │  ├─ ai_service.py【AI生成逻辑】[M]
│  │  ├─ ai_task_service.py【AI任务队列】[S]
│  │  ├─ attachment_service.py【附件服务】[S]
│  │  ├─ auth.py【认证服务】[M]
│  │  ├─ cache_service.py【通用缓存】[S]
│  │  ├─ draft_service.py【草稿服务】[S]
│  │  ├─ export_service.py【导出服务】[M]
│  │  ├─ form_service.py【表单服务】[M]
│  │  ├─ form_version_service.py【版本服务】[S]
│  │  ├─ formula_service.py【公式计算】[S]
│  │  ├─ qrcode_service.py【二维码服务】[S]
│  │  ├─ storage_service.py【对象存储】[S]
│  │  ├─ submission_service.py【提交服务】[M]
│  │  ├─ token_cache_service.py【令牌缓存】[S]
│  │  ├─ ⭐ token_service.py【JWT轮转】[M]
│  │  ├─ user_service.py【用户查询】[S]
│  │  └─ validation_service.py【校验工具】[S]
│  ├─ tasks/【调度任务】[S]
│  │  ├─ __init__.py【包标识】[S]
│  │  └─ scheduler.py【APScheduler任务】[S]
│  └─ utils/【通用工具】[M]
│     ├─ __init__.py【包标识】[S]
│     └─ audit.py【审计装饰器】[M]
├─ logs/【日志占位】[S]
│  └─ .gitkeep【保持目录】[S]
├─ requirements.txt【依赖声明】[S]
├─ tests/【测试与样例】[XL]
│  ├─ __init__.py【Nuxt适配脚手架】[M]
│  ├─ document_tree.py【结构脚本】[S]
│  ├─ nuxt-modules-organized.json【Nuxt模块整理】[L]
│  ├─ nuxt-modules-raw.json【Nuxt模块原始】[XL]
│  ├─ nuxt-modules-report.md【Nuxt报告】[L]
│  └─ nuxtjs.py【Nuxt数据分析】[M]
├─ uploads/【上传占位】[S]
│  └─ .gitkeep【保持目录】[S]
└─ 后端文档.md【TBD】[S]
```

## 模块分组
- **基础设施**  
  - 文件：`app/main.py`, `app/config.py`, `app/core/*`, `app/middleware/logging.py`, `alembic/env.py`, `alembic.ini`。  
  - 依赖：加载 `settings` 配置，构建 SQLAlchemy 引擎与 Redis 客户端，注册 APScheduler 与中间件栈。  
  - 核心流程：应用启动执行 `lifespan` → 初始化数据库与 Redis → 启动调度器 → 接入全局异常与路由聚合。

- **认证与租户**  
  - 文件：`app/api/v1/auth.py`, `app/services/auth.py`, `app/services/token_service.py`, `app/services/token_cache_service.py`, `app/core/security.py`, `app/middleware/auth.py`, `app/api/deps.py`, `app/middleware/tenant.py`, `app/models/user.py`.  
  - 依赖：使用 SQLAlchemy 会话、Redis 缓存、`AuthMiddleware` 注入 `request.state`，复用 `TokenService` 的轮转逻辑。  
  - 核心流程：登录请求经 `AuthService.login` 校验 → 生成访问/刷新令牌并写入 Redis → 中间件校验并预刷新 → `get_current_user` 读取 `request.state` 返回用户。

- **用户与组织**  
  - 文件：`app/api/v1/users.py`, `app/services/user_service.py`, `app/models/user.py`, `app/models/activity.py` 中角色映射。  
  - 依赖：复用认证模块的租户过滤，与 `app/api/deps.RequireAdmin` 权限检查协作。  
  - 核心流程：路由解析筛选条件 → `UserService` 走 SQLAlchemy 查询/分页 → 使用 Pydantic Schema 响应，必要时写入审计。

- **表单建模**  
  - 文件：`app/api/v1/forms.py`, `app/services/form_service.py`, `app/services/form_version_service.py`, `app/services/formula_service.py`, `app/data/form_templates.py`, `app/models/form.py`, `app/schemas/form_schemas.py`.  
  - 依赖：读取 `Form` 与 `FormVersion` 模型，调用 `FormulaService` 计算字段，允许从内置模板复制。  
  - 核心流程：路由校验租户权限 → 读取或复制模板 → 落库 `Form`/`FormVersion` → 返回统一响应。

- **提交流程**  
  - 文件：`app/api/v1/submissions.py`, `app/services/submission_service.py`, `app/services.draft_service.py`, `app/models/workflow.py`, `app/schemas/submission_schemas.py`.  
  - 依赖：调用表单模块获取版本，结合附件服务、公式服务处理数据，写入提交与快照模型。  
  - 核心流程：校验表单状态 → `SubmissionService.create_submission` 验证与计算 → 绑定附件/删除草稿 → 返回结果或触发统计。

- **附件与存储**  
  - 文件：`app/api/v1/attachments.py`, `app/api/v1/upload.py`, `app/services/attachment_service.py`, `app/services/storage_service.py`, `app/models.form.Attachment`, `uploads/.gitkeep`.  
  - 依赖：使用 FastAPI `UploadFile`、MinIO 客户端、Redis 缓存清理策略，并挂钩审计日志。  
  - 核心流程：上传控制器验证文件 → `StorageService` 选择本地或 MinIO → `AttachmentService` 记录元数据 → 审计装饰器记录操作。

- **AI 表单助手**  
  - 文件：`app/api/v1/ai.py`, `app/services/ai_service.py`, `app/services/ai_task_service.py`, `app/data/ai_prompts.py`, `app/schemas/ai_schemas.py`.  
  - 依赖：调用 `zai` SDK 使用智谱 GLM API，结合本地提示词与状态枚举；暂存任务于内存映射。  
  - 核心流程：创建任务写入内存队列 → `AIService.generate_form_config` 请求远端 → 校验字段并返回 JSON → 提供轮询接口查询状态。

- **调度与运维**  
  - 文件：`app/tasks/scheduler.py`, `app/services/attachment_service.py`, `app/services/draft_service.py`, `app/services/export_service.py`.  
  - 依赖：APScheduler 定时任务获取 SQLAlchemy 会话，调用各服务做过期清理或导出压缩。  
  - 核心流程：定时作业触发 → 打开短生命周期会话 → 执行清理逻辑 → 写入日志。

- **统一响应与审计**  
  - 文件：`app/core/response.py`, `app/utils/audit.py`, `app/core/exceptions.py`, `app/core/exception_handlers.py`, `app/core/logger.py`.  
  - 依赖：所有路由直接返回 `success_response`/`error_response`，审计装饰器需要数据库会话及请求上下文。  
  - 核心流程：路由执行业务 → 使用响应封装输出 → 若有装饰器则写入 `AuditLog` → 异常统一由处理器转换。

## 编码规范
- 命名：文件/变量/函数保持 `snake_case`，类名用 `PascalCase`，常量（如 `ACCESS_TOKEN_EXPIRE_MINUTES`）使用 `UPPER_SNAKE`；路由前缀遵循 kebab-case 且资源名复数（见 `app/api/v1/__init__.py`）。  
- 风格：接口控制器（如 `app/api/v1/auth.py:login`）使用 `async def` 并标注类型；数据库依赖统一来自 `get_db`，确保单请求单事务域；结构化日志通过 `LoggingMiddleware` 注入 `request_id`。  
- 统一响应与错误：`app/core/response.py` 提供 `success_response` 与 `error_response`，异常通过 `app/core/exceptions.py` 的自定义错误抛出，由 `exception_handlers` 转换为 JSON。示例：
  ```python
  from fastapi import APIRouter
  from app.core.response import success_response

  router = APIRouter()

  @router.get("/ping")
  async def ping():
      return success_response(data={"status": "ok"})
  ```
  ```python
  from app.core.exceptions import AuthenticationError

  def ensure_login(user_id: int | None) -> None:
      if user_id is None:
          raise AuthenticationError("未登录")
  ```
- 必守约定：  
  1. 路由仅做输入输出与权限校验，业务逻辑下沉至 `services`。  
  2. 所有密钥、连接串从 `settings`/`.env` 读取，不可写死在业务代码。  
  3. 外部依赖（Redis、MinIO、AI 接口）必须封装于可替换服务层，便于 Mock 与容错。  
  4. 提交合并前至少跑通 `pip install -r requirements.txt`、单元/集成测试（`pytest`）及运行自检（`uvicorn app.main:app --reload` smoke）。

## 快速参考
- **常用命令**  
  - 安装依赖：`pip install -r requirements.txt`  
  - 启动开发：`uvicorn app.main:app --reload --port 8000`  
  - 数据迁移：`alembic revision --autogenerate -m "describe"`；`alembic upgrade head`  
  - 执行测试：`pytest`（测试目录当前主要存放样例，需先补充用例）  
  - 静态检查（若启用）：`ruff check .` / `black .` / `mypy .`

- **核心配置文件**  
  - `app/config.py`：Pydantic Settings，含默认值与派生 URL。  
  - `.env`：本地环境变量覆盖（需替换示例凭据）。  
  - `alembic.ini` & `alembic/env.py`：数据库迁移设置。  
  - `app/tasks/scheduler.py`：定时任务注册。

- **环境变量（键名→用途）**  
  - `PROJECT_NAME` / `VERSION` / `API_V1_STR`：基础信息与路由前缀。  
  - `SECRET_KEY` / `ALGORITHM` / `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS`：JWT 签发参数。  
  - `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD`：PostgreSQL 连接配置。  
  - `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` / `REDIS_PASSWORD`：Redis 连接。  
  - `BACKEND_CORS_ORIGINS`：允许的前端域名列表。  
  - `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` / `MINIO_BUCKET` / `MINIO_SECURE`：对象存储访问。  
  - `GLM_API_KEY` / `GLM_MODEL` / `GLM_BASE_URL`：智谱 AI 调用参数。  
  - `UPLOAD_MAX_SIZE` / `UPLOAD_MAX_TOTAL_SIZE`：上传限制。  
  - `LOG_LEVEL` / `LOG_DIR`：日志级别与目录。  
  - 其他：`ADMIN_CRUD_WHITELIST`、`REDIS_EXPIRE_SECONDS`、`EXPORT_TEMP_DIR` 等用于权限与清理策略。

- **路由前缀与约定**  
  - 公共 API：`/api/v1`（统一在 `app/main.py` 设置 `openapi_url/docs`）。  
  - 健康检查：`/health`；根路径 `/` 返回欢迎信息。  
  - 认证白名单：`/api/v1/auth/login|register|refresh|tenants|validate-tenant`、`/api/health`、`/docs`、`/redoc`、`/openapi.json`。  
  - 多租户请求需附带 `X-Tenant-ID` 请求头，上传请求需支持 `X-Refresh-Token`。
