<template>
  <div class="activity-create-shell">
    <section class="section">
      <div class="section-shell">
        <div class="page-header">
          <n-button quaternary @click="router.back()">
            <template #icon>
              <Icon icon="carbon:arrow-left" />
            </template>
            返回
          </n-button>
          <h1>{{ isEdit ? '编辑活动' : '创建活动' }}</h1>
        </div>

        <n-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-placement="left"
          label-width="120px"
          class="activity-form"
        >
          <n-card title="基本信息" class="form-card">
            <n-grid :cols="2" :x-gap="24">
              <n-gi>
                <n-form-item label="活动名称" path="name">
                  <n-input v-model:value="form.name" placeholder="请输入活动名称" />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="活动类型" path="activity_type">
                  <n-select
                    v-model:value="form.activity_type"
                    :options="typeOptions"
                    placeholder="请选择活动类型"
                  />
                </n-form-item>
              </n-gi>
              <n-gi :span="2">
                <n-form-item label="活动地点" path="location">
                  <n-input v-model:value="form.location" placeholder="请输入活动地点" />
                </n-form-item>
              </n-gi>
              <n-gi :span="2">
                <n-form-item label="活动说明" path="description">
                  <n-input
                    v-model:value="form.description"
                    type="textarea"
                    :rows="4"
                    placeholder="请输入活动说明"
                  />
                </n-form-item>
              </n-gi>
            </n-grid>
          </n-card>

          <n-card title="时间安排" class="form-card">
            <n-grid :cols="2" :x-gap="24">
              <n-gi>
                <n-form-item label="开始时间" path="start_date">
                  <n-date-picker
                    v-model:value="form.start_date"
                    type="datetime"
                    placeholder="选择开始时间"
                    style="width: 100%"
                  />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="结束时间" path="end_date">
                  <n-date-picker
                    v-model:value="form.end_date"
                    type="datetime"
                    placeholder="选择结束时间"
                    style="width: 100%"
                  />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="报名开始" path="register_start">
                  <n-date-picker
                    v-model:value="form.register_start"
                    type="datetime"
                    placeholder="选择报名开始时间"
                    style="width: 100%"
                  />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="报名结束" path="register_end">
                  <n-date-picker
                    v-model:value="form.register_end"
                    type="datetime"
                    placeholder="选择报名结束时间"
                    style="width: 100%"
                  />
                </n-form-item>
              </n-gi>
            </n-grid>
          </n-card>

          <n-card title="报名设置" class="form-card">
            <n-grid :cols="2" :x-gap="24">
              <n-gi>
                <n-form-item label="名额限制" path="quota">
                  <n-input-number
                    v-model:value="form.quota"
                    :min="0"
                    placeholder="0表示不限名额"
                    style="width: 100%"
                  />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="报名表单" path="form_id">
                  <n-select
                    v-model:value="form.form_id"
                    :options="formOptions"
                    placeholder="选择报名表单"
                    clearable
                  />
                </n-form-item>
              </n-gi>
            </n-grid>
          </n-card>

          <div class="form-actions">
            <n-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
              {{ isEdit ? '保存修改' : '创建活动' }}
            </n-button>
            <n-button size="large" @click="router.back()">取消</n-button>
          </div>
        </n-form>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { createActivity, getActivityDetail } from '@/api/activity'
import { listForms } from '@/api/form'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const isEdit = computed(() => !!route.params.id)
const activityId = computed(() => Number(route.params.id))

const formRef = ref()
const submitting = ref(false)
const formOptions = ref<{ label: string; value: number }[]>([])

const form = reactive({
  name: '',
  activity_type: null as string | null,
  location: '',
  description: '',
  start_date: null as number | null,
  end_date: null as number | null,
  register_start: null as number | null,
  register_end: null as number | null,
  quota: 0,
  form_id: null as number | null,
})

const rules = {
  name: [{ required: true, message: '请输入活动名称', trigger: 'blur' }],
  activity_type: [{ required: true, message: '请选择活动类型', trigger: 'change' }],
}

const typeOptions = [
  { label: '学术讲座', value: 'lecture' },
  { label: '文体活动', value: 'sports' },
  { label: '志愿服务', value: 'volunteer' },
  { label: '竞赛比赛', value: 'competition' },
  { label: '社团活动', value: 'club' },
]

const loadForms = async () => {
  try {
    const { data } = await listForms({ page: 1, page_size: 100 })
    formOptions.value = (data?.items || []).map((f: any) => ({
      label: f.name,
      value: f.id,
    }))
  } catch (error) {
    console.error('加载表单列表失败', error)
  }
}

const loadActivity = async () => {
  if (!isEdit.value) return
  try {
    const { data } = await getActivityDetail(activityId.value)
    if (data) {
      form.name = data.name
      form.activity_type = data.type
      form.location = data.location || ''
      form.description = data.description || ''
      form.quota = data.quota || 0
      form.form_id = data.form_id
      // 日期转换略
    }
  } catch (error) {
    message.error('加载活动信息失败')
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    
    const payload = {
      ...form,
      start_date: form.start_date ? new Date(form.start_date).toISOString() : undefined,
      end_date: form.end_date ? new Date(form.end_date).toISOString() : undefined,
      register_start: form.register_start ? new Date(form.register_start).toISOString() : undefined,
      register_end: form.register_end ? new Date(form.register_end).toISOString() : undefined,
    }
    
    if (isEdit.value) {
      // TODO: 调用更新API
      message.success('更新成功')
    } else {
      await createActivity(payload as any)
      message.success('创建成功')
    }
    
    router.push('/activities')
  } catch (error) {
    console.error('提交失败', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadForms()
  loadActivity()
})
</script>

<style scoped>
.activity-create-shell {
  min-height: 100vh;
  background: var(--bg);
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  color: #0b0d12;
}

.activity-form {
  max-width: 900px;
}

.form-card {
  margin-bottom: 24px;
  border-radius: 18px;
}

.form-card :deep(.n-card-header) {
  font-size: 16px;
  font-weight: 600;
  color: #0b0d12;
}

.form-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 32px 0;
}
</style>
