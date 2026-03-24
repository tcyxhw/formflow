<template>
  <div class="certificate-verify-shell">
    <div class="verify-container">
      <div class="verify-card">
        <div class="verify-header">
          <div class="logo">
            <span class="logo-mark">FF</span>
            <span class="logo-text">FormFlow</span>
          </div>
          <h1>证书验证</h1>
          <p class="subtitle">输入验证码验证证书真伪</p>
        </div>

        <div class="verify-form">
          <n-input
            v-model:value="verifyCode"
            placeholder="请输入8位验证码"
            size="large"
            maxlength="8"
            class="verify-input"
          >
            <template #prefix>
              <Icon icon="carbon:certificate" />
            </template>
          </n-input>
          <n-button
            type="primary"
            size="large"
            block
            :loading="verifying"
            @click="handleVerify"
          >
            验证
          </n-button>
        </div>

        <!-- 验证结果 -->
        <div v-if="verifyResult" class="verify-result" :class="{ valid: verifyResult.valid }">
          <template v-if="verifyResult.valid">
            <div class="result-icon valid">
              <Icon icon="carbon:checkmark-filled" />
            </div>
            <h2>证书真实有效</h2>
            <div class="certificate-info">
              <div class="info-item">
                <span class="info-label">证书编号</span>
                <span class="info-value">{{ verifyResult.certificate?.certificate_no }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">持证人</span>
                <span class="info-value">{{ verifyResult.student?.name }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">活动名称</span>
                <span class="info-value">{{ verifyResult.activity?.name }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">颁发时间</span>
                <span class="info-value">{{ formatDate(verifyResult.certificate?.issued_at) }}</span>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="result-icon invalid">
              <Icon icon="carbon:close-filled" />
            </div>
            <h2>验证失败</h2>
            <p class="error-message">{{ verifyResult.message }}</p>
          </template>
        </div>

        <div class="verify-footer">
          <p>FormFlow 高校表单与审批平台</p>
          <p class="copyright">© 2024 FormFlow. All rights reserved.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { verifyCertificate } from '@/api/activity'

const message = useMessage()
const verifyCode = ref('')
const verifying = ref(false)
const verifyResult = ref<any>(null)

const handleVerify = async () => {
  if (!verifyCode.value || verifyCode.value.length < 6) {
    message.warning('请输入有效的验证码')
    return
  }
  
  verifying.value = true
  try {
    const { data } = await verifyCertificate(verifyCode.value.toUpperCase())
    verifyResult.value = data
  } catch (error) {
    message.error('验证失败')
  } finally {
    verifying.value = false
  }
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.certificate-verify-shell {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.verify-container {
  width: 100%;
  max-width: 480px;
}

.verify-card {
  background: white;
  border-radius: 32px;
  padding: 48px;
  box-shadow: 0 40px 80px rgba(0, 0, 0, 0.12);
}

.verify-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
}

.logo-mark {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: #0b0d12;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  color: #0b0d12;
}

.verify-header h1 {
  font-size: 28px;
  color: #0b0d12;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #6b7282;
  font-size: 15px;
}

.verify-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}

.verify-input :deep(.n-input__input) {
  font-size: 18px;
  letter-spacing: 4px;
  text-align: center;
}

.verify-result {
  background: #fef2f2;
  border-radius: 20px;
  padding: 32px;
  text-align: center;
  margin-bottom: 32px;
}

.verify-result.valid {
  background: #f0fdf4;
}

.result-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  margin: 0 auto 16px;
}

.result-icon.valid {
  background: #dcfce7;
  color: #16a34a;
}

.result-icon.invalid {
  background: #fee2e2;
  color: #dc2626;
}

.verify-result h2 {
  font-size: 20px;
  margin: 0 0 16px 0;
  color: #0b0d12;
}

.error-message {
  color: #dc2626;
}

.certificate-info {
  text-align: left;
  background: white;
  border-radius: 16px;
  padding: 20px;
  margin-top: 20px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f6;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: #6b7282;
  font-size: 14px;
}

.info-value {
  color: #0b0d12;
  font-weight: 500;
  font-size: 14px;
}

.verify-footer {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}

.verify-footer p {
  margin: 4px 0;
}

.copyright {
  font-size: 12px;
}

@media (max-width: 480px) {
  .verify-card {
    padding: 32px 24px;
  }
}
</style>
