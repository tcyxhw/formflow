<!-- src/views/forms/FormNewView.vue -->
<template>
    <div class="form-new-page">
      <n-page-header title="创建表单" @back="$router.back()" />
      <n-card style="margin-top: 16px;">
        <n-empty description="表单设计器功能开发中">
          <template #extra>
            <n-space>
              <n-button @click="$router.back()">返回</n-button>
              <n-button type="primary" @click="handleSave">
                保存表单（演示）
              </n-button>
            </n-space>
          </template>
        </n-empty>
      </n-card>
    </div>
  </template>
  
  <script setup lang="ts">
  import { useMessage } from 'naive-ui'
  
  const message = useMessage()
  
  const handleSave = () => {
    message.success('表单保存成功（演示）')
  }
  </script>
  
  <style scoped>
  .form-new-page {
    padding: 20px;
  }
  </style>