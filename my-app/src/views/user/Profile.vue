<template>
  <div class="profile-page">
    <n-page-header title="个人信息" @back="handleBack">
      <template #extra>
        <n-space>
          <n-button @click="showPasswordModal = true">修改密码</n-button>
          <n-button type="primary" @click="showEditModal = true">编辑资料</n-button>
          <n-button type="error" @click="handleLogout">退出登录</n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-grid :cols="3" :x-gap="24" class="profile-grid">
      <!-- 基本信息卡片 -->
      <n-gi :span="2">
        <n-card title="基本信息" class="info-card">
          <n-descriptions :column="2" label-placement="left" bordered>
            <n-descriptions-item label="账号">
              {{ userInfo?.account || '-' }}
            </n-descriptions-item>
            <n-descriptions-item label="姓名">
              {{ userInfo?.name || '-' }}
            </n-descriptions-item>
            <n-descriptions-item label="邮箱">
              {{ userInfo?.email || '-' }}
            </n-descriptions-item>
            <n-descriptions-item label="手机号">
              {{ userInfo?.phone || '-' }}
            </n-descriptions-item>
            <n-descriptions-item label="部门">
              {{ userInfo?.department?.name || '-' }}
            </n-descriptions-item>
            <n-descriptions-item label="岗位">
              {{ formatPositions(userInfo?.positions) }}
            </n-descriptions-item>
            <n-descriptions-item label="角色">
              {{ formatRoles(userInfo?.roles) }}
            </n-descriptions-item>
            <n-descriptions-item label="学号/工号">
              {{ userInfo?.profile?.identity_no || '-' }}
            </n-descriptions-item>
            <n-descriptions-item label="所属租户">
              {{ userInfo?.tenant_id || '-' }}
            </n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="userInfo?.is_active ? 'success' : 'error'" size="small">
                {{ userInfo?.is_active ? '已启用' : '已禁用' }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="创建时间">
              {{ userInfo?.created_at ? new Date(userInfo.created_at).toLocaleString('zh-CN') : '-' }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>

        <!-- 统计信息 -->
        <n-card title="数据统计" class="stats-card">
          <n-grid :cols="4" :x-gap="16">
            <n-gi>
              <div class="stat-item">
                <div class="stat-value">{{ stats?.forms_created || 0 }}</div>
                <div class="stat-label">创建的表单</div>
              </div>
            </n-gi>
            <n-gi>
              <div class="stat-item">
                <div class="stat-value">{{ stats?.forms_submitted || 0 }}</div>
                <div class="stat-label">填写的表单</div>
              </div>
            </n-gi>
            <n-gi>
              <div class="stat-item">
                <div class="stat-value">{{ stats?.tasks_pending || 0 }}</div>
                <div class="stat-label">待办审批</div>
              </div>
            </n-gi>
            <n-gi>
              <div class="stat-item">
                <div class="stat-value">{{ stats?.tasks_completed || 0 }}</div>
                <div class="stat-label">已处理审批</div>
              </div>
            </n-gi>
          </n-grid>
        </n-card>
      </n-gi>

      <!-- 头像卡片 -->
      <n-gi>
        <n-card title="头像" class="avatar-card">
          <div class="avatar-wrapper">
            <input
              ref="avatarInputRef"
              type="file"
              accept="image/*"
              style="display: none"
              @change="handleAvatarFileChange"
            />
            <n-avatar 
              :size="120" 
              round 
              :src="userAvatarUrl" 
              object-fit="cover" 
              class="avatar-hover"
              @click="handleAvatarClick"
            >
              <template v-if="!userAvatarUrl">
                {{ userInitials }}
              </template>
            </n-avatar>
            <n-button size="small" type="primary" ghost style="margin-top: 12px" @click="triggerAvatarUpload">
              更换头像
            </n-button>
          </div>
          <div class="avatar-info">
            <p class="avatar-name">{{ userInfo?.name || '用户' }}</p>
            <p class="avatar-account">@{{ userInfo?.account || '' }}</p>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 编辑资料弹窗 -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="编辑资料" positive-text="保存" negative-text="取消" @positive-click="handleSaveProfile">
      <n-form ref="formRef" :model="editForm" :rules="formRules" label-placement="left" label-width="80">
        <n-form-item label="姓名" path="name">
          <n-input v-model:value="editForm.name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="editForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="手机号" path="phone">
          <n-input v-model:value="editForm.phone" placeholder="请输入手机号" />
        </n-form-item>
        <n-form-item label="身份角色" path="identity_type">
          <n-select v-model:value="editForm.identity_type" placeholder="请选择身份角色" :options="identityTypeOptions" />
        </n-form-item>
        <n-form-item label="学号/工号" path="identity_no">
          <n-input v-model:value="editForm.identity_no" placeholder="请输入学号或工号" />
        </n-form-item>
      </n-form>
    </n-modal>

    <!-- 修改密码弹窗 -->
    <n-modal v-model:show="showPasswordModal" preset="dialog" title="修改密码" positive-text="确认" negative-text="取消" @positive-click="handleChangePassword">
      <n-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-placement="left" label-width="80">
        <n-form-item label="原密码" path="old_password">
          <n-input v-model:value="passwordForm.old_password" type="password" placeholder="请输入原密码" show-password-on="click" />
        </n-form-item>
        <n-form-item label="新密码" path="new_password">
          <n-input v-model:value="passwordForm.new_password" type="password" placeholder="请输入新密码" show-password-on="click" />
        </n-form-item>
        <n-form-item label="确认密码" path="confirm_password">
          <n-input v-model:value="passwordForm.confirm_password" type="password" placeholder="请确认新密码" show-password-on="click" />
        </n-form-item>
      </n-form>
    </n-modal>

    <!-- 头像预览弹窗 -->
    <n-modal v-model:show="showAvatarPreview" preset="card" title="头像预览" style="width: 400px">
      <div style="display: flex; justify-content: center; padding: 20px;">
        <n-image
          :src="userAvatarUrl || ''"
          :preview-disabled="true"
          style="max-width: 100%; max-height: 400px; border-radius: 8px;"
          object-fit="contain"
        />
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { getCurrentUser, updateUser, changePassword, updateUserProfile } from '@/api/auth'
import { uploadAttachment } from '@/api/attachment'
import type { UserInfo } from '@/types/user'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const userInfo = ref<UserInfo | null>(null)
const stats = ref<{
  forms_created: number
  forms_submitted: number
  tasks_pending: number
  tasks_completed: number
} | null>(null)

const showEditModal = ref(false)
const showPasswordModal = ref(false)

const editForm = reactive({
  name: '',
  email: '',
  phone: '',
  identity_type: null as 'student' | 'teacher' | 'admin' | null,
  identity_no: ''
})

const identityTypeOptions = [
  { label: '学生', value: 'student' },
  { label: '教师', value: 'teacher' },
  { label: '管理员', value: 'admin' }
]

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const formRules = {
  name: { required: true, message: '请输入姓名', trigger: 'blur' },
  email: { type: 'email' as const, message: '邮箱格式不正确', trigger: 'blur' }
}

const passwordRules = {
  old_password: { required: true, message: '请输入原密码', trigger: 'blur' },
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string) => value === passwordForm.new_password,
      message: '两次输入的密码不一致',
      trigger: 'blur'
    }
  ]
}

// 身份类型映射
const getIdentityTypeText = (type: string | undefined): string => {
  const map: Record<string, string> = {
    'student': '学生',
    'teacher': '教师',
    'admin': '管理员'
  }
  return type ? map[type] || type : ''
}

const getIdentityTypeTag = (type: string | undefined): 'success' | 'warning' | 'info' => {
  const map: Record<string, 'success' | 'warning' | 'info'> = {
    'student': 'success',
    'teacher': 'warning',
    'admin': 'info'
  }
  return map[type || ''] || 'info'
}

const formatRoles = (roles?: string[]): string => {
  if (!roles || roles.length === 0) return '无'
  return roles.join('、')
}

const formatPositions = (positions?: string[]): string => {
  if (!positions || positions.length === 0) return '-'
  return positions.join('、')
}

const userInitials = computed(() => {
  if (!userInfo.value?.name) return '?'
  const clean = userInfo.value.name.replace(/\s+/g, '')
  return clean.slice(0, 2).toUpperCase()
})

const userAvatarUrl = computed(() => {
  const token = authStore.accessToken || localStorage.getItem('access_token')
  return `/api/v1/users/me/avatar?token=${encodeURIComponent(token || '')}`
})

const avatarInputRef = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const showAvatarPreview = ref(false)

const triggerAvatarUpload = () => {
  avatarInputRef.value?.click()
}

const handleAvatarClick = () => {
  if (userAvatarUrl.value) {
    showAvatarPreview.value = true
  } else {
    triggerAvatarUpload()
  }
}

const handleAvatarFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  
  uploading.value = true
  try {
    const uploadRes = await uploadAttachment(file)
    console.log('Upload response:', uploadRes)
    
    if (uploadRes.code === 200 && uploadRes.data?.download_url) {
      const avatarUrl = uploadRes.data.download_url
      await updateUser(userInfo.value!.id, { avatar_url: avatarUrl })
      userInfo.value!.avatar_url = avatarUrl
      message.success('头像更新成功')
    } else {
      message.error('头像上传失败')
    }
  } catch (error) {
    console.error('Avatar upload error:', error)
    message.error('头像上传失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

const loadUserInfo = async () => {
  try {
    const res = await getCurrentUser()
    userInfo.value = res.data
    editForm.name = res.data.name || ''
    editForm.email = res.data.email || ''
    editForm.phone = res.data.phone || ''
    // 加载扩展信息
    if (res.data.profile) {
      editForm.identity_type = res.data.profile.identity_type || null
      editForm.identity_no = res.data.profile.identity_no || ''
    }
    // 确保 avatar_url 被正确加载
    if (res.data.avatar_url) {
      userInfo.value.avatar_url = res.data.avatar_url
    }
  } catch (error) {
    message.error('获取用户信息失败')
  }
}

const loadStats = async () => {
  try {
    const res = await authStore.fetchUserStats()
    stats.value = res
  } catch (error) {
    console.error('获取统计信息失败', error)
  }
}

const handleBack = () => {
  router.push('/')
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const handleSaveProfile = async () => {
  if (!userInfo.value) return
  try {
    await updateUser(userInfo.value.id, {
      name: editForm.name,
      email: editForm.email || undefined,
      phone: editForm.phone || undefined
    })
    // 保存扩展信息
    await updateUserProfile(userInfo.value.id, {
      identity_type: editForm.identity_type || undefined,
      identity_no: editForm.identity_no || undefined
    })
    message.success('保存成功')
    showEditModal.value = false
    loadUserInfo()
  } catch (error) {
    message.error('保存失败')
    return false
  }
}

const handleChangePassword = async () => {
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    message.error('两次输入的密码不一致')
    return false
  }
  if (!userInfo.value) return
  try {
    await changePassword(userInfo.value.id, {
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    message.success('密码修改成功，请重新登录')
    showPasswordModal.value = false
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    setTimeout(() => {
      authStore.logout()
      router.push('/login')
    }, 1500)
  } catch (error) {
    message.error('密码修改失败')
    return false
  }
}

onMounted(() => {
  loadUserInfo()
  loadStats()
})
</script>

<style scoped lang="scss">
.profile-page {
  padding: 24px;
}

.profile-grid {
  margin-top: 24px;
}

.info-card,
.stats-card,
.avatar-card {
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fb;
  border-radius: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #0b0d12;
}

.stat-label {
  font-size: 13px;
  color: #6b7282;
  margin-top: 4px;
}

.avatar-card {
  text-align: center;
}

.avatar-wrapper {
  padding: 24px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.avatar-hover {
  cursor: pointer;
  transition: opacity 0.2s;
  object-fit: cover;
}

.avatar-hover:hover {
  opacity: 0.8;
}

.avatar-name {
  font-size: 18px;
  font-weight: 600;
  color: #0b0d12;
  margin: 8px 0 4px;
}

.avatar-account {
  font-size: 14px;
  color: #6b7282;
}

.no-identity {
  color: #999;
  font-size: 12px;
}
</style>