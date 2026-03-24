# 提交管理页面修复验证清单

## 修改概览

### 问题 1：表单名称和提交人名称显示不出来
**根本原因**：后端 API 返回的数据缺少这两个字段

**解决方案**：
- 在后端 `list_submissions` 方法中添加关联查询
- 从 `Form` 表查询表单名称
- 从 `User` 表查询提交人名称

**修改文件**：`backend/app/api/v1/submissions.py`

### 问题 2：点击详情跳转新页面，需要改为弹窗
**根本原因**：原来使用 `router.push()` 跳转到详情页面

**解决方案**：
- 创建新的弹窗组件 `SubmissionDetailModal.vue`
- 修改列表页面的 `viewDetail` 方法，改为打开弹窗
- 弹窗中显示基本信息和表单数据，不显示快照和流程轨迹

**修改文件**：
- `my-app/src/components/submission/SubmissionDetailModal.vue`（新建）
- `my-app/src/views/submissions/SubmissionListView.vue`（修改）

## 代码修改详情

### 后端修改

#### 文件：`backend/app/api/v1/submissions.py`

**修改 1**：添加 datetime 导入
```python
from datetime import datetime
```

**修改 2**：修改 `list_submissions` 方法
- 在循环中为每个提交记录查询表单和用户信息
- 添加 `form_name` 和 `submitter_name` 字段到响应数据

```python
items = []
for s in submissions:
    item_dict = SubmissionResponse.from_orm(s).dict()
    
    # 获取表单名称
    form = db.query(Form).filter(Form.id == s.form_id).first()
    item_dict["form_name"] = form.name if form else "未知表单"
    
    # 获取提交人名称
    if s.submitter_user_id:
        user = db.query(User).filter(User.id == s.submitter_user_id).first()
        item_dict["submitter_name"] = user.name if user else "未知用户"
    else:
        item_dict["submitter_name"] = "匿名用户"
    
    items.append(item_dict)
```

### 前端修改

#### 文件 1：`my-app/src/components/submission/SubmissionDetailModal.vue`（新建）

**功能**：
- 弹窗组件，显示提交详情
- Props：`show`（显示/隐藏）、`submissionId`（提交 ID）
- Emits：`update:show`（更新显示状态）

**显示内容**：
- ✅ 基本信息：ID、表单名称、提交人、状态、提交时间、耗时
- ✅ 表单数据：详细的字段数据，支持查看原始 JSON
- ✅ 附件列表：如果有附件则显示
- ❌ 快照信息：不显示
- ❌ 流程轨迹：不显示

#### 文件 2：`my-app/src/views/submissions/SubmissionListView.vue`（修改）

**修改 1**：导入弹窗组件
```typescript
import SubmissionDetailModal from '@/components/submission/SubmissionDetailModal.vue'
```

**修改 2**：添加状态变量
```typescript
const detailModalVisible = ref(false)
const selectedSubmissionId = ref<number | undefined>()
```

**修改 3**：修改 `viewDetail` 方法
```typescript
const viewDetail = (id: number) => {
  selectedSubmissionId.value = id
  detailModalVisible.value = true
}
```

**修改 4**：在模板中添加弹窗组件
```vue
<SubmissionDetailModal
  :show="detailModalVisible"
  :submission-id="selectedSubmissionId"
  @update:show="detailModalVisible = $event"
/>
```

## 验证清单

### 后端验证

- [ ] 代码无语法错误
- [ ] 导入正确（`datetime`、`Form`、`User`）
- [ ] 逻辑正确（查询表单和用户信息）
- [ ] 错误处理完善（表单/用户不存在时返回默认值）
- [ ] API 返回数据包含 `form_name` 和 `submitter_name`

### 前端验证

- [ ] 弹窗组件创建成功
- [ ] 列表页面导入组件成功
- [ ] 代码无语法错误
- [ ] 类型检查通过
- [ ] 点击"详情"按钮打开弹窗
- [ ] 弹窗显示正确的提交信息
- [ ] 弹窗显示表单数据
- [ ] 弹窗显示附件列表（如有）
- [ ] 弹窗不显示快照信息
- [ ] 弹窗不显示流程轨迹
- [ ] 点击"关闭"按钮关闭弹窗

### 集成测试

- [ ] 后端服务启动正常
- [ ] 前端服务启动正常
- [ ] 提交列表页面加载正常
- [ ] 表单名称显示正确
- [ ] 提交人名称显示正确
- [ ] 弹窗打开/关闭正常
- [ ] 弹窗数据加载正确
- [ ] 没有控制台错误

## 性能考虑

### 当前实现
- 使用循环 + 单条查询的方式获取表单和用户信息
- 可能存在 N+1 查询问题

### 优化建议（后续）
- 使用 SQLAlchemy 的 `joinedload` 或 `selectinload` 进行关联加载
- 或者在 `SubmissionService.list_submissions` 中直接返回关联数据

## 相关文件

### 后端
- `backend/app/api/v1/submissions.py` - API 端点
- `backend/app/models/form.py` - Form 和 Submission 模型
- `backend/app/models/user.py` - User 模型
- `backend/app/schemas/submission_schemas.py` - Schema 定义

### 前端
- `my-app/src/components/submission/SubmissionDetailModal.vue` - 新建弹窗组件
- `my-app/src/views/submissions/SubmissionListView.vue` - 列表页面
- `my-app/src/api/submission.ts` - API 调用
- `my-app/src/types/submission.ts` - 类型定义

## 测试命令

### 后端
```bash
# 启动开发服务器
cd backend
uvicorn app.main:app --reload --port 8000

# 访问 API 文档
# http://localhost:8000/api/v1/docs
```

### 前端
```bash
# 启动开发服务器
cd my-app
npm run dev

# 访问提交管理页面
# http://localhost:5173/submissions
```

## 完成状态

✅ 后端代码修改完成
✅ 前端弹窗组件创建完成
✅ 前端列表页面修改完成
✅ 代码检查通过（无语法错误）
✅ 类型检查通过

## 下一步

1. 启动后端和前端服务
2. 进行集成测试
3. 验证所有功能正常
4. 根据需要进行性能优化
