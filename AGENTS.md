# AGENTS.md

## 项目概览
FormFlow 是一个高校多租户表单与审批中台，包含 Python FastAPI 后端和 Vue3 前端。

**后端技术栈**: Python 3.10 / FastAPI / SQLAlchemy / Alembic / PostgreSQL / Redis / MinIO / APScheduler / JWT
**前端技术栈**: Vue 3 / Vite / TypeScript / Naive UI / Pinia / Vue Router / Axios

## 构建与测试命令

### 后端 (Python)
```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8000

# 数据库迁移
alembic revision --autogenerate -m "描述"
alembic upgrade head

# 运行测试 (当前主要是样例，需补充用例)
pytest

# 静态检查 (可选，需安装对应工具)
ruff check .          # 代码检查
black .               # 代码格式化
mypy .                # 类型检查
```

### 前端 (Vue3)
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview

# 类型检查
npm run type-check

# 代码检查和修复
npm run lint
```

## 代码风格指南

### Python 后端规范

#### 命名约定
- **文件/变量/函数**: `snake_case`
- **类名**: `PascalCase`
- **常量**: `UPPER_SNAKE_CASE`
- **路由前缀**: kebab-case，资源名使用复数

#### 代码风格
- **接口控制器**: 使用 `async def` 并标注类型
- **数据库依赖**: 统一来自 `get_db`，确保单请求单事务域
- **结构化日志**: 通过 `LoggingMiddleware` 注入 `request_id`

#### 统一响应与错误处理
```python
# 成功响应
from app.core.response import success_response
return success_response(data={"status": "ok"})

# 错误处理
from app.core.exceptions import AuthenticationError
if user_id is None:
    raise AuthenticationError("未登录")
```

#### 核心约定
1. **路由职责**: 仅做输入输出与权限校验，业务逻辑下沉至 `services`
2. **配置管理**: 所有密钥、连接串从 `settings`/`.env` 读取
3. **服务封装**: 外部依赖（Redis、MinIO、AI 接口）必须封装于可替换服务层
4. **提交前检查**: 跑通依赖安装、测试、开发服务器启动

#### 文档规范
每个模块应包含标准文件头：
```python
"""
模块用途: [核心功能简述]
依赖配置: [外部依赖/环境变量]
数据流向: [源] -> [处理逻辑] -> [宿]
函数清单:
    - func_name(): 功能描述
"""
```

### Vue3 前端规范

#### 命名约定
- **页面/组件**: `PascalCase.vue`
- **组合式函数**: `useXxx.ts`
- **Pinia 仓库**: `useXxxStore`
- **路由路径**: kebab-case

#### 代码风格
- **组件模板**: 统一使用 `<script setup lang="ts">`
- **副作用控制**: 组件避免副作用，跨组件通信优先使用 Pinia
- **UI 组件**: Naive 组件采用插件全量注册，必要时显式引入图标

#### 路由管理
- **懒加载**: 路由新增保持懒加载 `import`
- **集中管理**: 在 `src/router/index.ts` 中集中管理
- **元信息**: 根据守卫需要补充 `meta` 信息

#### API 请求示例
```typescript
import { listForms } from '@/api/form'

const loadForms = async () => {
  const { data } = await listForms({ page: 1, size: 10 })
  console.log(data.items)
}
```

## 项目结构

### 后端关键目录
- `app/api/v1/`: API 路由层
- `app/services/`: 业务服务层
- `app/models/`: ORM 模型
- `app/schemas/`: Pydantic 数据模型
- `app/core/`: 基础设施（数据库、Redis、安全等）
- `app/middleware/`: 中间件
- `alembic/`: 数据库迁移脚本

### 前端关键目录
- `src/api/`: API 接口定义
- `src/components/`: 可复用组件
- `src/views/`: 页面组件
- `src/stores/`: Pinia 状态管理
- `src/types/`: TypeScript 类型定义
- `src/utils/`: 工具函数
- `src/router/`: 路由配置

## 环境配置

### 后端环境变量
- `PROJECT_NAME` / `VERSION` / `API_V1_STR`: 基础信息
- `SECRET_KEY` / `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT 配置
- `DB_HOST` / `DB_USER` / `DB_PASSWORD`: PostgreSQL 配置
- `REDIS_HOST` / `REDIS_PORT`: Redis 配置
- `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY`: MinIO 配置
- `GLM_API_KEY` / `GLM_MODEL`: AI 服务配置

### 前端环境变量
- `VITE_APP_TITLE`: 应用标题
- `VITE_API_BASE_URL`: 后端 API 地址
- `VITE_APP_ENV`: 环境标记

## API 约定

### 后端 API
- **前缀**: `/api/v1`
- **认证**: Bearer Token (JWT)
- **多租户**: 请求头 `X-Tenant-ID`
- **响应格式**: 统一使用 `success_response` / `error_response`

### 前端 API
- **代理**: 开发环境通过 Vite 代理 `/api` 到后端
- **错误处理**: 统一在 HTTP 客户端中处理
- **类型安全**: 所有 API 调用都有对应的 TypeScript 接口

## 开发工作流

### 新功能开发
1. **后端先行**: 编写 API 和 Pydantic 模型
2. **契约同步**: 在前端创建对应的 TypeScript 接口
3. **组件开发**: 实现前端页面和组件
4. **测试验证**: 确保前后端功能正常

### 代码质量
- **类型安全**: 后端使用 Pydantic，前端使用 TypeScript
- **错误处理**: 统一的异常处理机制
- **日志记录**: 结构化日志，便于调试
- **代码审查**: 提交前运行静态检查和测试

## 核心功能模块

### 认证与租户
- JWT 令牌管理（访问令牌 + 刷新令牌）
- 多租户支持
- 权限控制

### 表单系统
- 表单设计器（拖拽式）
- 表单模板
- 字段类型与验证
- 公式计算

### 提交与审批
- 表单提交
- 草稿保存
- 审批流程
- 数据导出

### AI 助手
- 自然语言生成表单
- 智能字段推荐
- 表单优化建议

### 文件管理
- 附件上传
- 对象存储（MinIO）
- 文件类型检测
- 下载控制

## 常见问题

### 测试单个功能
- **后端**: 使用 `pytest tests/test_specific.py::test_function`
- **前端**: 在浏览器中直接访问对应路由

### 调试 API
- **后端**: 访问 `/api/v1/docs` 查看 Swagger 文档
- **前端**: 使用浏览器开发者工具查看网络请求

### 数据库问题
- **迁移**: 使用 `alembic upgrade head`
- **重置**: 删除数据库后重新运行迁移

### 依赖问题
- **后端**: 确保使用正确的 Python 版本 (3.10+)
- **前端**: 删除 `node_modules` 和 `package-lock.json` 后重新安装