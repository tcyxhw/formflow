<template>
  <div class="fill-center">
    <header class="page-head">
      <div>
        <p class="eyebrow">Fill Workspace</p>
        <h1>表单填写工作台</h1>
        <p class="subtitle">
          快速挑选需要提交的表单，查看草稿与历史记录，并可在同一处执行合规补填、二次编辑。
        </p>
      </div>
      <n-button type="primary" size="large" @click="handleDesigner">
        新建表单
      </n-button>
    </header>

    <section class="grid">
      <article class="panel">
        <div class="panel-head">
          <h3>我的填报队列</h3>
          <span class="meta">最近 7 天待办</span>
        </div>
        <ul class="queue" role="list">
          <li v-for="item in pendingForms" :key="item.id" role="listitem">
            <div>
              <p class="title">{{ item.title }}</p>
              <p class="desc">截止 {{ item.deadline }}</p>
            </div>
            <n-button tertiary size="small" @click="() => handleFill(item.id)">填写</n-button>
          </li>
        </ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <h3>历史提交</h3>
          <span class="meta">可直接回填并再次提交</span>
        </div>
        <div class="history">
          <p>支持根据账号自动载入最近 50 条提交，点击后将读取最新表单结构并预填旧数据。</p>
          <n-button quaternary size="small" @click="handleHistory">
            查看全部
          </n-button>
        </div>
      </article>

      <article class="panel highlight">
        <div class="panel-head">
          <h3>AI 辅助填写</h3>
          <span class="meta">Beta</span>
        </div>
        <p>描述你需要提交的事务，系统会匹配合适表单并自动填写可推断字段。</p>
        <n-input
          v-model:value="prompt"
          type="textarea"
          placeholder="例如：我要提交 2025 春季科研经费报销。"
          rows="3"
        />
        <n-button class="cta" type="primary" @click="handleAIFill">
          开始匹配
        </n-button>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const pendingForms = [
  { id: 101, title: '实习证明申请', deadline: '12-28 18:00' },
  { id: 206, title: '科研经费报销', deadline: '12-30 12:00' }
]

const prompt = ref('')

const handleDesigner = () => {
  router.push('/form/designer')
}

const handleFill = (id: number) => {
  router.push(`/form/${id}/fill`)
}

const handleHistory = () => {
  router.push('/submissions')
}

const handleAIFill = () => {
  router.push('/form/designer')
}
</script>

<style scoped>
.fill-center {
  padding: 48px clamp(24px, 5vw, 64px);
  background: linear-gradient(180deg, #fafafc 0%, #ffffff 100%);
  min-height: 100vh;
}

.page-head {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding-bottom: 32px;
  border-bottom: 1px solid rgba(15, 18, 23, 0.08);
  margin-bottom: 40px;
  align-items: center;
}

.page-head h1 {
  margin: 8px 0;
  font-size: clamp(28px, 5vw, 40px);
  color: #0b0d12;
}

.subtitle {
  margin: 0;
  color: #5a6172;
  max-width: 620px;
}

.grid {
  display: grid;
  gap: 24px;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.panel {
  background: #fff;
  border: 1px solid rgba(15, 18, 23, 0.08);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 20px 45px rgba(12, 16, 32, 0.08);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel.highlight {
  grid-column: span 2;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-head h3 {
  margin: 0;
  font-size: 20px;
}

.meta {
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #8a8f9f;
}

.queue {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.queue li {
  padding: 14px 0;
  border-bottom: 1px solid rgba(15, 18, 23, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.queue .title {
  margin: 0 0 4px;
  font-weight: 600;
}

.queue .desc {
  margin: 0;
  color: #6f7482;
  font-size: 13px;
}

.history {
  background: rgba(15, 18, 23, 0.02);
  border: 1px dashed rgba(15, 18, 23, 0.08);
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cta {
  align-self: flex-start;
}

@media (max-width: 768px) {
  .panel.highlight {
    grid-column: span 1;
  }

  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
