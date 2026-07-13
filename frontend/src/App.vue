<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from './stores/user'

const userStore = useUserStore()

onMounted(() => {
  userStore.initFromToken()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.el-menu {
  border-right: none !important;
}

.card-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
  padding: 24px;
}

/* Markdown 内容排版 — 参考 VitePress 可读性 */
.markdown-content {
  line-height: 1.8;
  font-size: var(--text-base);
  color: var(--color-chalk, #1D2129);
}

.markdown-content h1 { font-size: 2em; margin: 1.2em 0 0.6em; }
.markdown-content h2 { font-size: 1.5em; margin: 1.4em 0 0.5em; padding-bottom: 0.3em; border-bottom: 1px solid #e5e6eb; }
.markdown-content h3 { font-size: 1.25em; margin: 1.2em 0 0.4em; }
.markdown-content p { margin: 0.8em 0; }
.markdown-content ul, .markdown-content ol { padding-left: 1.5em; margin: 0.6em 0; }
.markdown-content li { margin: 0.3em 0; }
.markdown-content blockquote {
  margin: 1em 0;
  padding: 0.6em 1em;
  border-left: 4px solid var(--color-gold, #165DFF);
  background: var(--color-gold-subtle, rgba(22,93,255,0.04));
  border-radius: 0 4px 4px 0;
}
.markdown-content blockquote p { margin: 0.3em 0; }

.markdown-content pre {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  overflow-x: auto;
  margin: 16px 0;
  font-size: var(--text-sm);
  line-height: 1.6;
}

.markdown-content code {
  background: rgba(22,93,255,0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  color: var(--color-gold, #165DFF);
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 0.95em;
}
.markdown-content th, .markdown-content td {
  padding: 10px 14px;
  border: 1px solid #e5e6eb;
  text-align: left;
}
.markdown-content th {
  background: #f7f8fa;
  font-weight: 600;
}
</style>
