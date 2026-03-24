<template>
  <div class="form-card-skeleton">
    <div class="status-indicator skeleton-shimmer"></div>
    <div class="card-content">
      <div class="card-header">
        <div class="skeleton-title skeleton-shimmer"></div>
        <div class="skeleton-tag skeleton-shimmer"></div>
      </div>
      <div class="skeleton-description skeleton-shimmer"></div>
      <div class="form-meta">
        <div class="skeleton-meta skeleton-shimmer"></div>
        <div class="skeleton-meta skeleton-shimmer"></div>
        <div class="skeleton-meta skeleton-shimmer"></div>
      </div>
      <div class="card-actions">
        <div class="skeleton-button skeleton-shimmer"></div>
        <div class="skeleton-button skeleton-shimmer"></div>
        <div class="skeleton-button skeleton-shimmer"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 骨架屏组件，用于加载状态展示
</script>

<style scoped>
.form-card-skeleton {
  position: relative;
  padding: 20px;
  background-color: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  overflow: hidden;
}

.status-indicator {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background-color: #e0e0e0;
}

.card-content {
  padding-left: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.skeleton-title {
  height: 20px;
  width: 60%;
  border-radius: 4px;
}

.skeleton-tag {
  height: 24px;
  width: 60px;
  border-radius: 4px;
}

.skeleton-description {
  height: 40px;
  width: 100%;
  margin-bottom: 12px;
  border-radius: 4px;
}

.form-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.skeleton-meta {
  height: 16px;
  width: 80px;
  border-radius: 4px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.skeleton-button {
  height: 28px;
  width: 60px;
  border-radius: 4px;
}

/* 骨架屏动画 */
.skeleton-shimmer {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
