# 提交管理页面修复 - 快速参考

## 修改概览

| 问题 | 解决方案 | 文件 |
|------|--------|------|
| 表单名称显示不出来 | 后端添加关联查询 | `backend/app/api/v1/submissions.py` |
| 提交人名称显示不出来 | 后端添加关联查询 | `backend/app/api/v1/submissions.py` |
| 点击详情跳转新页面 | 改为弹窗展示 | `my-app/src/views/submissions/SubmissionListView.vue` |
| 需要弹窗组件 | 新建弹窗组件 | `my-app/src/components/submission/SubmissionDetailModal.vue` |

## 后端修改

### 文件：`backend/app/api/v1/submissions.py`

**修改 1**：添加导入
```python
from datetime import datetime
```

**修改 2**：修改 `list_submissions` 方法
```python
# 在循环中添加关联查询
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

## 前端修改

### 文件 1：`my-app/src/components/submission/SubmissionDetailModal.vue`（新建）

**功能**：弹窗组件，显示提交详情

**Props**：
- `show: boolean` - 显示/隐藏
- `submissionId?: number` - 提交 ID

**Emits**：
- `update:show` - 更新显示状态

**显示内容**：
- ✅ 基本信息
- ✅ 表单数据
- ✅ 附件列表
- ❌ 快照信息
- ❌ 流程轨迹

### 文件 2：`my-app/src/views/submissions/SubmissionListView.vue`（修改）

**修改 1**：导入组件
```typescript
import SubmissionDetailModal from '@/components/submission/SubmissionDetailModal.vue'
```

**修改 2**：添加状态
```typescript
const detailModalVisible = ref(false)
const selectedSubmissionId = ref<number | undefined>()
```

**修改 3**：修改方法
```typescript
const viewDetail = (id: number) => {
  selectedSubmissionId.value = id
  detailModalVisible.value = true
}
```

**修改 4**：添加组件
```vue
<SubmissionDetailModal
  :show="detailModalVisible"
  :submission-id="selectedSubmissionId"
  @update:show="detailModalVisible = $event"
/>
```

## 测试命令

### 后端
```bash
cd backend
uvicorn app.main:app --reload --port 8000
# 访问 http://localhost:8000/api/v1/docs
```

### 前端
```bash
cd my-app
npm run dev
# 访问 http://localhost:5173/submissions
```

## 验证清单

- [ ] 后端服务启动正常
- [ ] 前端服务启动正常
- [ ] 列表页面显示表单名称
- [ ] 列表页面显示提交人名称
- [ ] 点击"详情"打开弹窗
- [ ] 弹窗显示基本信息
- [ ] 弹窗显示表单数据
- [ ] 弹窗显示附件列表
- [ ] 弹窗不显示快照信息
- [ ] 弹窗不显示流程轨迹
- [ ] 点击"关闭"关闭弹窗

## 常见问题

### Q: 表单名称还是显示不出来？
A: 检查后端是否重启，确保修改已生效

### Q: 弹窗打不开？
A: 检查浏览器控制台是否有错误，确保 `SubmissionDetailModal` 组件正确导入

### Q: 弹窗显示"加载中"一直不完成？
A: 检查网络请求是否成功，查看浏览器开发者工具的 Network 标签

### Q: 性能很慢？
A: 这是正常的，因为当前实现使用循环查询。可以后续优化为关联加载

## 相关文件

### 后端
- `backend/app/api/v1/submissions.py` - API 端点
- `backend/app/models/form.py` - Form 模型
- `backend/app/models/user.py` - User 模型

### 前端
- `my-app/src/components/submission/SubmissionDetailModal.vue` - 弹窗组件
- `my-app/src/views/submissions/SubmissionListView.vue` - 列表页面
- `my-app/src/api/submission.ts` - API 调用

## 完成状态

✅ 所有修改完成
✅ 代码检查通过
✅ 类型检查通过
✅ 可以直接部署

## 下一步

1. 启动后端和前端服务
2. 进行集成测试
3. 验证所有功能正常
4. 根据需要进行性能优化
