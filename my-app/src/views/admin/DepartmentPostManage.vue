<template>
  <div class="department-post-management">
    <div class="page-header-section">
      <div class="header-left">
        <h1 class="page-title">部门与岗位管理</h1>
        <p class="page-subtitle">管理组织架构、部门及其对应的岗位</p>
      </div>
      <div class="header-actions">
        <n-button type="primary" @click="showAddDepartment = true">
          <template #icon>
            <n-icon><add-outline /></n-icon>
          </template>
          新增部门
        </n-button>
        <n-button type="primary" @click="showAddPosition = true">
          <template #icon>
            <n-icon><add-outline /></n-icon>
          </template>
          新增岗位
        </n-button>
      </div>
    </div>

    <n-card>
      <div v-if="loading" class="loading-wrapper">
        <n-spin size="medium" />
      </div>
      <template v-else>
        <div v-if="treeData.length === 0" class="empty-wrapper">
          <n-empty description="暂无部门数据，请先添加部门" />
        </div>
        <div v-else class="tree-wrapper">
          <n-tree
            :data="treeData"
            :expanded-keys="expandedKeys"
            :selected-keys="selectedKeys"
            block-line
            selectable
            @update:expanded-keys="expandedKeys = $event"
          />
        </div>
      </template>
    </n-card>

    <!-- 新增部门对话框 -->
    <n-modal v-model:show="showAddDepartment" preset="card" title="新增部门" style="width: 500px">
      <n-form ref="departmentFormRef" :model="departmentForm" :rules="departmentRules">
        <n-form-item label="部门名称" path="name">
          <n-input v-model:value="departmentForm.name" placeholder="请输入部门名称" />
        </n-form-item>
        <n-form-item label="部门类型" path="type">
          <n-select
            v-model:value="departmentForm.type"
            :options="departmentTypeOptions"
            placeholder="请选择部门类型"
          />
        </n-form-item>
        <n-form-item label="上级部门" path="parent_id">
          <n-tree-select
            v-model:value="departmentForm.parent_id"
            :options="departmentTreeSelectOptions"
            placeholder="请选择上级部门（可选）"
            clearable
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddDepartment = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleAddDepartment">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 新增岗位对话框 -->
    <n-modal v-model:show="showAddPosition" preset="card" title="新增岗位" style="width: 500px">
      <n-form ref="positionFormRef" :model="positionForm" :rules="positionRules">
        <n-form-item label="岗位名称" path="name">
          <n-input v-model:value="positionForm.name" placeholder="请输入岗位名称" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddPosition = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleAddPosition">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 添加岗位到部门对话框 -->
    <n-modal v-model:show="showAddPostToDeptModal" preset="card" title="添加岗位到部门" style="width: 500px">
      <n-form ref="postToDeptFormRef" :model="postToDeptForm" :rules="postToDeptRules">
        <n-form-item label="部门">
          <n-input :value="postToDeptForm.departmentName" disabled />
        </n-form-item>
        <n-form-item label="选择岗位" path="post_id">
          <n-select
            v-model:value="postToDeptForm.post_id"
            :options="positionSelectOptions"
            placeholder="请选择岗位"
          />
        </n-form-item>
        <n-form-item label="是否主负责人岗位" path="is_head">
          <n-switch v-model:value="postToDeptForm.is_head" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddPostToDeptModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleAddPostToDept">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useMessage, NIcon, NTag, NButton, NSpace } from 'naive-ui'
import type { TreeOption } from 'naive-ui'
import { AddOutline, TrashOutline } from '@vicons/ionicons5'
import { 
  departmentApi, 
  positionApi, 
  departmentPostApi,
  type Department, 
  type Position, 
  type DepartmentPost 
} from '@/api/admin'

const message = useMessage()

const departmentList = ref<Department[]>([])
const positionList = ref<Position[]>([])
const relationList = ref<DepartmentPost[]>([])

const loading = ref(false)
const submitting = ref(false)

const showAddDepartment = ref(false)
const showAddPosition = ref(false)
const showAddPostToDeptModal = ref(false)

const expandedKeys = ref<(string | number)[]>([])
const selectedKeys = ref<(string | number)[]>([])

const departmentForm = ref({
  name: '',
  type: 'department',
  parent_id: null as number | null
})
const positionForm = ref({ name: '' })
const postToDeptForm = ref({
  department_id: null as number | null,
  departmentName: '',
  post_id: null as number | null,
  is_head: false
})

const departmentRules = {
  name: { required: true, message: '请输入部门名称', trigger: 'blur' },
  type: { required: true, message: '请选择部门类型', trigger: 'change' }
}
const positionRules = {
  name: { required: true, message: '请输入岗位名称', trigger: 'blur' }
}
const postToDeptRules = {
  post_id: { required: true, message: '请选择岗位', trigger: 'change' }
}

const departmentTypeOptions = [
  { label: '学院', value: 'college' },
  { label: '办公室', value: 'office' },
  { label: '系/部门', value: 'department' },
  { label: '班级', value: 'class' }
]

const departmentTreeSelectOptions = computed(() => {
  return departmentList.value.map(dept => ({
    label: dept.name,
    value: dept.id
  }))
})

const positionSelectOptions = computed(() => {
  const usedPostIds = relationList.value
    .filter(r => r.department_id === postToDeptForm.value.department_id)
    .map(r => r.post_id)
  
  return positionList.value
    .filter(pos => !usedPostIds.includes(pos.id))
    .map(pos => ({
      label: pos.name,
      value: pos.id
    }))
})

function getDepartmentName(deptId: number): string {
  const dept = departmentList.value.find(d => d.id === deptId)
  return dept?.name || ''
}

const treeData = computed<TreeOption[]>(() => {
  const childrenMap = new Map<number | null, Department[]>()
  departmentList.value.forEach(d => {
    const parentId = d.parent_id
    if (!childrenMap.has(parentId)) {
      childrenMap.set(parentId, [])
    }
    childrenMap.get(parentId)!.push(d)
  })

  const deptPostMap = new Map<number, DepartmentPost[]>()
  relationList.value.forEach(rp => {
    if (!deptPostMap.has(rp.department_id)) {
      deptPostMap.set(rp.department_id, [])
    }
    deptPostMap.get(rp.department_id)!.push(rp)
  })

  function buildTree(parentId: number | null): TreeOption[] {
    const children = childrenMap.get(parentId) || []
    return children.map(dept => {
      const deptPosts = deptPostMap.get(dept.id) || []
      
      const postChildren: TreeOption[] = deptPosts.map(rp => ({
        key: `post_${rp.id}`,
        label: rp.post_name,
        prefix: () => h(NTag, { size: 'small', type: 'info' }, { default: () => '岗位' })
      }))

      const deptChildren: TreeOption[] = buildTree(dept.id)
      
      return {
        key: dept.id,
        label: dept.name,
        prefix: () => h(NTag, { size: 'small', type: 'warning' }, { default: () => '部门' }),
        suffix: () => h(NSpace, { size: 'small' }, {
          default: () => [
            h(NButton, 
              { size: 'tiny', quaternary: true, onClick: () => openAddPostToDept(dept.id, dept.name) },
              { icon: () => h(NIcon, null, { default: () => h(AddOutline) }), default: () => '添加岗位' }
            ),
            h(NButton,
              { size: 'tiny', quaternary: true, type: 'error', onClick: () => handleDeleteDepartment(dept.id) },
              { icon: () => h(NIcon, null, { default: () => h(TrashOutline) }) }
            )
          ]
        }),
        children: [...postChildren, ...deptChildren]
      }
    })
  }

  return buildTree(null)
})

function openAddPostToDept(deptId: number, deptName: string) {
  postToDeptForm.value = {
    department_id: deptId,
    departmentName: deptName,
    post_id: null,
    is_head: false
  }
  showAddPostToDeptModal.value = true
}

async function loadData() {
  loading.value = true
  try {
    const [deptRes, posRes, relRes] = await Promise.all([
      departmentApi.list({ page: 1, size: 1000 }),
      positionApi.list({ page: 1, size: 1000 }),
      departmentPostApi.list()
    ])
    
    const deptData = (deptRes as any).data
    const posData = (posRes as any).data
    const relData = (relRes as any).data
    
    departmentList.value = deptData?.items || []
    positionList.value = posData?.items || []
    relationList.value = relData?.items || []
    
    const rootDepts = departmentList.value.filter(d => !d.parent_id)
    expandedKeys.value = rootDepts.map(d => d.id)
  } catch (e: any) {
    message.error('加载数据失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

async function handleAddDepartment() {
  if (!departmentForm.value.name) {
    message.warning('请输入部门名称')
    return
  }
  submitting.value = true
  try {
    await departmentApi.create(departmentForm.value)
    message.success('部门创建成功')
    showAddDepartment.value = false
    departmentForm.value = { name: '', type: 'department', parent_id: null }
    loadData()
  } catch (e: any) {
    message.error(e.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

async function handleDeleteDepartment(id: number | string) {
  try {
    await departmentApi.delete(id as number)
    message.success('部门删除成功')
    loadData()
  } catch (e: any) {
    message.error(e.message || '删除失败')
  }
}

async function handleAddPosition() {
  if (!positionForm.value.name) {
    message.warning('请输入岗位名称')
    return
  }
  submitting.value = true
  try {
    await positionApi.create(positionForm.value)
    message.success('岗位创建成功')
    showAddPosition.value = false
    positionForm.value = { name: '' }
    loadData()
  } catch (e: any) {
    message.error(e.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

async function handleDeletePosition(id: number | string) {
  const postId = parseInt(id.toString().replace('post_', ''))
  try {
    await departmentPostApi.delete(postId)
    message.success('岗位关联删除成功')
    loadData()
  } catch (e: any) {
    message.error(e.message || '删除失败')
  }
}

async function handleAddPostToDept() {
  if (!postToDeptForm.value.post_id) {
    message.warning('请选择岗位')
    return
  }
  submitting.value = true
  try {
    await departmentPostApi.create({
      department_id: postToDeptForm.value.department_id!,
      post_id: postToDeptForm.value.post_id,
      is_head: postToDeptForm.value.is_head
    })
    message.success('岗位添加成功')
    showAddPostToDeptModal.value = false
    postToDeptForm.value = { department_id: null, departmentName: '', post_id: null, is_head: false }
    loadData()
  } catch (e: any) {
    message.error(e.message || '添加失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.department-post-management {
  padding: 20px;
}

.page-header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.page-subtitle {
  margin: 4px 0 0;
  color: #666;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.loading-wrapper {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.empty-wrapper {
  display: flex;
  justify-content: center;
  padding: 60px;
}

.tree-wrapper {
  min-height: 300px;
}
</style>