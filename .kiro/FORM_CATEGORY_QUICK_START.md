# 表单分类系统 - 快速开始指南

## 🚀 快速启动

### 1. 数据库迁移

```bash
cd backend
alembic upgrade head
```

这将：
- 创建 `category` 表
- 为 `form` 表添加 `category_id` 列
- 为每个现有租户创建默认分类 "Uncategorized"
- 为所有现有表单分配默认分类

### 2. 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/api/v1/docs 查看API文档

### 3. 启动前端开发服务器

```bash
cd my-app
npm run dev
```

## 📋 API快速参考

### 获取分类列表
```bash
curl -X GET "http://localhost:8000/api/v1/categories?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 1"
```

### 创建分类
```bash
curl -X POST "http://localhost:8000/api/v1/categories" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"name": "HR Forms"}'
```

### 更新分类
```bash
curl -X PUT "http://localhost:8000/api/v1/categories/2" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Human Resources"}'
```

### 删除分类
```bash
curl -X DELETE "http://localhost:8000/api/v1/categories/2" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 1"
```

### 按分类过滤表单
```bash
curl -X GET "http://localhost:8000/api/v1/forms?category_id=2&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 1"
```

## 🧪 运行测试

### 后端单元测试
```bash
cd backend
pytest tests/test_category_service.py -v
```

### 后端属性测试
```bash
cd backend
pytest tests/test_category_properties.py -v
```

### 后端集成测试
```bash
cd backend
pytest tests/test_category_integration.py -v
```

### 运行所有分类测试
```bash
cd backend
pytest tests/test_category*.py -v
```

## 🎨 前端集成示例

### 在表单搭建页面使用CategoryDropdown

```vue
<template>
  <div class="form-builder">
    <n-form-item label="表单名称">
      <n-input v-model:value="formData.name" />
    </n-form-item>
    
    <n-form-item label="分类">
      <CategoryDropdown 
        v-model="formData.category_id"
        :disabled="isLoading"
      />
    </n-form-item>
    
    <n-button type="primary" @click="saveForm">
      保存表单
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NForm, NFormItem, NInput, NButton } from 'naive-ui'
import CategoryDropdown from '@/components/form/CategoryDropdown.vue'
import { createForm } from '@/api/form'

const formData = ref({
  name: '',
  category_id: null
})

const isLoading = ref(false)

const saveForm = async () => {
  isLoading.value = true
  try {
    await createForm({
      name: formData.value.name,
      category_id: formData.value.category_id
    })
    // 显示成功提示
  } finally {
    isLoading.value = false
  }
}
</script>
```

### 在表单搜索页面使用CategoryFilter

```vue
<template>
  <div class="form-search">
    <n-space>
      <n-input 
        v-model:value="searchKeyword"
        placeholder="搜索表单..."
      />
      
      <CategoryFilter 
        v-model="selectedCategory"
        @update:modelValue="handleFilterChange"
      />
      
      <n-button type="primary" @click="searchForms">
        搜索
      </n-button>
    </n-space>
    
    <n-data-table
      :columns="columns"
      :data="forms"
      :loading="isLoading"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NSpace, NInput, NButton, NDataTable } from 'naive-ui'
import CategoryFilter from '@/components/form/CategoryFilter.vue'
import { listForms } from '@/api/form'

const searchKeyword = ref('')
const selectedCategory = ref<number | null>(null)
const forms = ref([])
const isLoading = ref(false)

const columns = computed(() => [
  {
    title: '表单名称',
    key: 'name'
  },
  {
    title: '分类',
    key: 'category_name'
  },
  {
    title: '状态',
    key: 'status'
  },
  {
    title: '创建时间',
    key: 'created_at'
  }
])

const handleFilterChange = (categoryId: number | null) => {
  searchForms()
}

const searchForms = async () => {
  isLoading.value = true
  try {
    const response = await listForms({
      keyword: searchKeyword.value,
      category_id: selectedCategory.value,
      page: 1,
      page_size: 20
    })
    forms.value = response.data.items
  } finally {
    isLoading.value = false
  }
}
</script>
```

## 📊 数据库查询示例

### 查看所有分类
```sql
SELECT * FROM category WHERE tenant_id = 1;
```

### 查看某个分类下的表单
```sql
SELECT f.* FROM form f
WHERE f.tenant_id = 1 AND f.category_id = 2;
```

### 查看默认分类
```sql
SELECT * FROM category 
WHERE tenant_id = 1 AND is_default = true;
```

### 统计每个分类的表单数
```sql
SELECT c.name, COUNT(f.id) as form_count
FROM category c
LEFT JOIN form f ON c.id = f.category_id
WHERE c.tenant_id = 1
GROUP BY c.id, c.name;
```

## 🔍 常见问题

### Q: 如何创建新的分类？
A: 使用 `POST /api/v1/categories` 端点，提供分类名称。

### Q: 删除分类会发生什么？
A: 该分类下的所有表单会被自动重新分配到默认分类 "Uncategorized"。

### Q: 能否删除默认分类？
A: 不能。系统会防止删除默认分类以确保数据完整性。

### Q: 分类名称有什么限制？
A: 分类名称必须是1-50个字符，且在同一租户内唯一。

### Q: 如何过滤所有分类的表单？
A: 不指定 `category_id` 参数或将其设为 `null`。

### Q: 分类过滤状态会保存吗？
A: 是的，CategoryFilter组件会将选择的分类保存到 `sessionStorage`，页面刷新后会自动恢复。

## 📚 相关文件

- 实施总结: `.kiro/FORM_CATEGORY_SYSTEM_IMPLEMENTATION.md`
- 需求文档: `.kiro/specs/form-category-system/requirements.md`
- 设计文档: `.kiro/specs/form-category-system/design.md`
- 任务清单: `.kiro/specs/form-category-system/tasks.md`

## 🎯 下一步

1. 在表单搭建页面集成 CategoryDropdown
2. 在表单搜索页面集成 CategoryFilter
3. 在表单列表中显示分类信息
4. 运行完整的测试套件验证功能
5. 部署到生产环境

## 💡 提示

- 使用 Swagger UI (`/api/v1/docs`) 测试API
- 查看浏览器控制台了解前端错误
- 检查后端日志了解服务器错误
- 使用 `pytest -v` 运行详细的测试输出
