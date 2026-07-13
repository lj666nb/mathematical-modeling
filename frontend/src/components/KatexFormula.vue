<!--
  KatexFormula — KaTeX 公式渲染组件
  用法: <KatexFormula latex="E = mc^2" :display-mode="true" />
-->
<template>
  <div v-if="displayMode" class="katex-block" v-html="renderedHtml" />
  <span v-else class="katex-inline" v-html="renderedHtml" />
</template>

<script setup>
import { computed } from 'vue'
import { renderFormula } from '../composables/useKatex.js'

const props = defineProps({
  latex: { type: String, required: true },
  displayMode: { type: Boolean, default: true },
})

const renderedHtml = computed(() => {
  if (!props.latex) return ''
  const { html, error } = renderFormula(props.latex, props.displayMode)
  if (error) return `<code>${escapeHtml(props.latex)}</code>`
  return html
})

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
</script>

<style scoped lang="scss">
.katex-block {
  overflow-x: auto;
  padding: var(--space-2) 0;
}

.katex-inline {
  display: inline;
}
</style>
