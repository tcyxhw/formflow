// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
// ❌ 移除 Element Plus 相关导入
// import AutoImport from 'unplugin-auto-import/vite'
// import Components from 'unplugin-vue-components/vite'
// import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  
  return {
    plugins: [
      vue(),
      // ❌ 移除 Element Plus 自动导入
      // AutoImport({
      //   imports: ['vue', 'vue-router', 'pinia'],
      //   dts: 'src/types/auto-imports.d.ts',
      //   resolvers: [ElementPlusResolver()],
      // }),
      // Components({
      //   resolvers: [ElementPlusResolver()],
      //   dts: 'src/types/components.d.ts',
      // }),
    ],
    resolve: {
      alias: {
        // ✅ 使用现代化的路径解析
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
    server: {
      port: 3000,
      host: true,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
          timeout: 120000,  // 代理超时 120 秒，匹配后端 AI 服务超时
        },
      },
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false,
      chunkSizeWarningLimit: 1500,
      rollupOptions: {
        output: {
          manualChunks: {
            // ✅ 改为 Naive UI 和 ECharts
            'naive-ui': ['naive-ui'],
            'echarts': ['echarts'],
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
          },
        },
      },
    },
    // ✅ 添加依赖优化配置
    optimizeDeps: {
      include: ['naive-ui', 'echarts', '@vicons/ionicons5']
    },
    // ✅ CSS 预处理器配置（消除 Sass 警告）
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler'
        }
      }
    }
  }
})