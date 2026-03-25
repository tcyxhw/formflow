# AGENTS.md

## AI 执行协议

在修改任何代码之前，必须遵守以下流程：

### 一、始终先读取
1. `standards/00_ai_digest.md`
2. `standards/01_principles.md`
3. `standards/02_decision_matrix.md`
4. `standards/review_evidence.md` 的「状态看板」区，用于了解近期活跃盲区与历史候选

### 二、按任务懒加载（不要预先全部读取）
1. 如果是 Python 后端任务，再读取：
   - `standards/03_python_rules_stable.md`
   - 如涉及候选规则、规则边界、规则演进，再读 `standards/04_python_rules_experimental.md`
2. 如果是 Vue3 前端任务，再读取：
   - `standards/05_vue3_rules_stable.md`
   - 如涉及候选规则、规则边界、规则演进，再读 `standards/06_vue3_rules_experimental.md`
3. 如果当前任务涉及结构性设计问题（如建模、总线、注册、分发、抽象、组合式管线），按需读取对应样本库：
   - `standards/golden_samples/python/`
   - `standards/anti_patterns/python/`
   - `standards/golden_samples/vue3/`
   - `standards/anti_patterns/vue3/`
4. 只有在执行规范审查或规则提案时，才读取：
   - `standards/08_review_checklist.md`
   - `standards/09_review_prompt.md`
   - `standards/10_rule_proposal_template.md`
   - `standards/11_changelog.md`

### 三、修改前必须先输出
1. 对现有实现的理解
2. 受影响的文件
3. 最小改动方案
4. 明确哪些行为不会改变
5. 潜在风险点与不确定点

### 四、修改时必须遵守
1. 优先最小化改动：优先改现有函数、现有模块、现有文件。
2. 禁止功能漂移：不得擅自改变行为、输入输出、异常语义、副作用或时序。
3. 严格遵守项目已有命名、目录结构、状态管理方式、API 调用模式和错误处理风格。
4. 遇到不确定设计，不要自行“顺手修复”，必须先指出风险并等待确认。
5. 一次只做当前任务所需的最小修改，不顺带重构无关代码。

### 五、修改后必须输出

#### 5.1 改动报告
- 改动清单：本次修改了哪些文件、哪些关键位置
- 影响范围：哪些功能/模块可能受到影响
- 风险点：当前改动中不确定或需要重点注意的地方

#### 5.2 规则合规自检

快速判定：本次改动是否属于以下低风险类型？
- 纯格式 / 拼写 / 注释修改
- 单行配置项修改
- 依赖版本更新
- 完全复用现有模式的机械性改动

如果是，输出：
本次为低风险变更，自检结果：完全在现有规则范围内，无盲区发现。

然后直接进入 5.4。

如果不是，必须逐条回答以下问题：

Q1 — 涉及哪些规则？
列出本次改动涉及的所有规则（编号或名称）。若不涉及任何规则，说明原因。

Q2 — 是否完全遵守？
对 Q1 中每条规则逐一确认：遵守 / 偏离，并说明原因。

Q3 — 是否做了规则未覆盖的决策？
本次改动中，是否有你做出了选择但找不到规则指导的场景？
- 有：描述 场景 / 你的选择 / 为什么规则没覆盖到
- 无：写“所有决策在现有规则覆盖范围内”

Q4 — 是否有规则描述不清导致你猜测的地方？
- 有：指出规则名 / 哪里不清晰 / 你如何猜测
- 无：写“规则描述清晰，无需猜测”

Q5 — 是否有规则在实际执行中感觉不合理？
- 有：指出规则名 / 哪里不合理 / 你做了什么妥协
- 无：写“现有规则执行合理”

#### 5.3 证据持久化

仅当 Q3、Q4 或 Q5 发现问题时，才考虑写入 `standards/review_evidence.md`。

写入前必须先判断：这个问题是否真的值得进入 evidence。

只有满足以下任一条件时，才允许写入：
- 会影响跨文件或跨层一致性
- 会影响真实功能、接口契约、类型安全、权限、安全、性能、事务或状态流转
- 在多个位置重复出现，明显具备复用性
- 现有规则无法指导当前决策，导致必须猜测或临时约定
- 未来极可能再次出现，并值得形成规则

默认不要写入 evidence 的情况：
- 纯视觉偏好差异
- 一次性命名细节
- 单次格式风格差异
- 不影响行为的轻微 UI 风格不一致
- 纯个人审美判断，且没有演化为规则价值

如果满足写入条件，则追加到 `standards/review_evidence.md` 的活跃证据区，条目结构为：

- 标题行：`### [YYYY-MM-DD HH:MM] <类型> | <标题>`
- 字段：
  - 文件
  - 场景
  - 当前做法
  - 规则缺口
  - 建议方向
  - 级别：observation
  - 严重性：高 / 中 / 低
  - 标签：从预定义列表选取，可多选
  - 出现次数：1
  - 最后触发：YYYY-MM-DD

类型取值：
- 盲区
- 模糊
- 冲突
- 过严
- 过松
- 过时

标签预定义列表：
`error-handling` / `naming` / `state-management` / `api-contract` / `type-safety` / `file-structure` / `dependency` / `testing` / `security` / `performance` / `concurrency` / `data-model` / `auth` / `config` / `logging`

如果 Q3、Q4、Q5 均无发现，或者发现的问题不满足 evidence 写入条件，输出：
本次无值得沉淀的盲区，不写入 review_evidence。

#### 5.4 历史盲区复查

完成 5.3 后，快速检查 `review_evidence.md` 的状态看板中是否有与本次改动相关的历史条目：

- 如果本次改动解决了某个历史问题：建议将该条目标记为 `✅ 已解决`
- 如果本次改动再次触发了某个历史问题：建议该条目出现次数 +1，并视情况建议升级
- 如果无关：明确说明“与当前历史活跃条目无直接关联”

#### 5.5 阈值提醒

在完成 5.4 后，检查当前任务累计改动情况：

如果满足任一条件，应输出提醒：
- 累计修改文件数 ≥ 6
- 累计改动行数 ≥ 400
- 涉及跨层联动（如 schema + service + api + router / 前端 api + types + views）

提醒格式：
⚠️ 当前累计改动较大，建议在合适时机运行 `/review-commit` 进行阶段性审查。

如果 `review_evidence.md` 活跃证据条目数 ≥ 15，再追加提醒：
⚠️ review_evidence 活跃证据较多，建议人工审核并归档。

### 六、提案与规则升级约束

1. 证据状态必须严格区分：
   - observation
   - confirmed
   - candidate
   - validated
2. 未达到 validated 的条目，不得直接生成正式规则提案。
3. `/propose-rule` 只能写入 `standards/rule_proposals/`，不得自动写入 stable 或 experimental。
4. 最终是否纳入规则文件，必须人工决定。
5. 所有最终结论以源码 / diff 为准，不以历史摘要文本为准。

### 七、审查命令使用时机

1. commit 前：
   - `git add -A`
   - `/review-commit`
2. push / PR 前：
   - `git fetch origin`
   - `/review-commit origin/main`
3. 当已有 validated 证据，且确实值得规则化时：
   - `/propose-rule`

## 项目概览

FormFlow 是一个高校多租户表单与审批中台，包含 Python FastAPI 后端和 Vue3 前端。

后端技术栈：Python 3.10 / FastAPI / SQLAlchemy / Alembic / PostgreSQL / Redis / MinIO / APScheduler / JWT  
前端技术栈：Vue 3 / Vite / TypeScript / Naive UI / Pinia / Vue Router / Axios

---

## 构建与测试命令

### 后端 (Python)
- 安装依赖：`pip install -r requirements.txt`
- 启动开发服务器：`uvicorn app.main:app --reload --port 8000`
- 数据库迁移：
  - `alembic revision --autogenerate -m "描述"`
  - `alembic upgrade head`
- 运行测试：`pytest`
- 静态检查：
  - `ruff check .`
  - `black .`
  - `mypy .`

### 前端 (Vue3)
- 安装依赖：`npm install`
- 启动开发服务器：`npm run dev`
- 构建生产版本：`npm run build`
- 预览构建结果：`npm run preview`
- 类型检查：`npm run type-check`
- 代码检查和修复：`npm run lint`

---

## 项目结构

### 后端关键目录
- `app/api/v1/`：API 路由层
- `app/services/`：业务服务层
- `app/models/`：ORM 模型
- `app/schemas/`：Pydantic 数据模型
- `app/core/`：基础设施（数据库、Redis、安全等）
- `app/middleware/`：中间件
- `alembic/`：数据库迁移脚本

### 前端关键目录
- `src/api/`：API 接口定义
- `src/components/`：可复用组件
- `src/views/`：页面组件
- `src/stores/`：Pinia 状态管理
- `src/types/`：TypeScript 类型定义
- `src/utils/`：工具函数
- `src/router/`：路由配置

---

## 后端关键约定

### 命名约定
- 文件/变量/函数：`snake_case`
- 类名：`PascalCase`
- 常量：`UPPER_SNAKE_CASE`
- 路由前缀：kebab-case，资源名使用复数

### 编码约定
1. 接口控制器使用 `async def` 并标注类型。
2. 数据库依赖统一来自 `get_db`，确保单请求单事务域。
3. 路由层仅做输入输出、权限校验和调用编排，核心业务逻辑下沉到 `services`。
4. 结构化日志通过 `LoggingMiddleware` 注入 `request_id`。
5. 所有密钥、连接串、功能开关从 `settings`/`.env` 读取。
6. 外部依赖（Redis、MinIO、AI 接口）必须封装在可替换服务层中。
7. 提交前至少跑通依赖安装、开发服务器启动、关键路径验证。

### 统一响应与错误处理
成功响应统一使用项目中的 `success_response`。  
错误处理统一使用项目异常体系，例如 `AuthenticationError` 等业务异常，不要直接散落返回非结构化错误。

### 文档规范
每个非临时模块应包含标准文件头，至少包括：
- 模块用途
- 依赖配置
- 数据流向
- 函数清单

---

## 前端关键约定

### 命名约定
- 页面/组件：`PascalCase.vue`
- 组合式函数：`useXxx.ts`
- Pinia 仓库：`useXxxStore`
- 路由路径：kebab-case

### 编码约定
1. 组件统一使用 `<script setup lang="ts">`。
2. 跨组件状态管理优先使用 Pinia，不使用临时全局事件漂移状态。
3. 路由新增保持懒加载 `import`。
4. 路由集中在 `src/router/index.ts` 中管理，并按需要补充 `meta`。
5. API 调用统一放在 `src/api/` 层，不把接口逻辑直接写入模板。
6. 错误处理统一在 HTTP 客户端或既有封装层处理。
7. 所有 API 调用都有对应 TypeScript 接口或类型定义。

### API 请求约定
优先复用 `src/api/` 中已有接口封装，页面和组件只消费封装后的函数与类型，不直接拼接 URL 或重复书写请求细节。

---

## 环境配置

### 后端环境变量
- `PROJECT_NAME`
- `VERSION`
- `API_V1_STR`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DB_HOST`
- `DB_USER`
- `DB_PASSWORD`
- `REDIS_HOST`
- `REDIS_PORT`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `GLM_API_KEY`
- `GLM_MODEL`

### 前端环境变量
- `VITE_APP_TITLE`
- `VITE_API_BASE_URL`
- `VITE_APP_ENV`

---

## API 约定

### 后端 API
- 前缀：`/api/v1`
- 认证：Bearer Token (JWT)
- 多租户：请求头 `X-Tenant-ID`
- 响应格式：统一使用项目响应封装

### 前端 API
- 开发环境通过 Vite 代理 `/api` 到后端
- 错误处理统一在 HTTP 客户端中处理
- 所有接口消费都要求类型安全

---

## 开发工作流

### 新功能开发
1. 后端先行：编写 API 和 Pydantic 模型
2. 契约同步：前端创建对应 TypeScript 接口
3. 组件开发：实现页面和组件
4. 联调验证：确保前后端功能正常

### 代码质量
- 后端使用 Pydantic 进行边界模型约束
- 前端使用 TypeScript 保持类型安全
- 使用统一异常处理机制
- 使用结构化日志便于排查
- 提交前运行静态检查和测试

---

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

---

## 常见问题

### 测试单个功能
- 后端：`pytest tests/test_specific.py::test_function`
- 前端：浏览器直接访问对应路由并结合网络面板检查

### 调试 API
- 后端：访问 `/api/v1/docs`
- 前端：使用浏览器开发者工具查看网络请求

### 数据库问题
- 迁移：`alembic upgrade head`
- 重置：删除数据库后重新运行迁移

### 依赖问题
- 后端：确保使用正确 Python 版本
- 前端：删除 `node_modules` 和 lock 文件后重新安装

---

## 优先级约定

当以下内容冲突时，优先级从高到低为：
1. 用户当前明确指令
2. 仓库中的 `standards/` 规范文件
3. 本文件中的项目说明与执行协议
4. 工具默认行为
