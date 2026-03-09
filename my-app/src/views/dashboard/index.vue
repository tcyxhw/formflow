<!-- src/views/dashboard/index.vue -->
<template>
  <div class="dashboard">
    <el-card>
      <h2>欢迎使用 FormFlow</h2>
      <p>高校轻量级表单与审批平台</p>
      
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="6">
          <el-card>
            <el-statistic title="表单数量" :value="10" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <el-statistic title="待办任务" :value="5" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <el-statistic title="已完成" :value="20" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <el-statistic title="用户数" :value="100" />
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 20px;
}
</style>