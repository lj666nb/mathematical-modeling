<!--
============================================================
模型详情页 — LRN-002 独立页面
6 个内容区域：定义区 / 公式区(LaTeX) / 方法区 / 例题区 / 代码区 / 相关模型推荐
============================================================
-->
<template>
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <div class="page-container">
        <!-- 面包屑 -->
        <div class="app-breadcrumb">
          <el-icon><HomeFilled /></el-icon>
          <router-link to="/knowledge-base" class="breadcrumb-link">学习中心</router-link>
          <span class="sep">/</span>
          <span class="current">{{ detail?.name || '模型详情' }}</span>
        </div>

        <!-- 加载骨架 -->
        <template v-if="loading">
          <div class="skeleton" style="height:80px;border-radius:12px;margin-bottom:20px;"></div>
          <div class="skeleton" style="height:200px;border-radius:12px;margin-bottom:16px;"></div>
          <div class="skeleton" style="height:160px;border-radius:12px;margin-bottom:16px;"></div>
        </template>

        <!-- 404 -->
        <template v-else-if="notFound">
          <div class="app-card" style="text-align:center;padding:80px 20px;">
            <el-icon :size="48" style="color:var(--text-tertiary);margin-bottom:16px;"><WarningFilled /></el-icon>
            <h3 style="margin-bottom:8px;">模型未找到</h3>
            <p style="color:var(--text-secondary);margin-bottom:20px;">分类 "{{ categoryId }}" 不存在，请确认路径是否正确</p>
            <el-button type="primary" @click="$router.push('/knowledge-base')" round>返回学习中心</el-button>
          </div>
        </template>

        <template v-else-if="detail">
          <!-- ===== 头部：模型名称 + 分类标签 ===== -->
          <div class="detail-hero" :style="{ '--hero-color': detail.color || '#165DFF', '--hero-bg': (detail.color || '#165DFF') + '0D' }">
            <div class="hero-left">
              <div class="hero-icon" :style="{ background: (detail.color || '#165DFF') + '15', color: detail.color }">
                <el-icon :size="32"><component :is="catIcon(detail.id)" /></el-icon>
              </div>
              <div class="hero-info">
                <div class="hero-tags">
                  <el-tag :color="detail.color" effect="dark" size="small" round>{{ detail.name }}</el-tag>
                  <el-tag type="info" size="small" effect="plain" round>
                    {{ detail.algorithms?.length || 0 }} 种算法
                  </el-tag>
                  <el-tag type="warning" size="small" effect="plain" round>
                    {{ detail.scenarios?.length || 0 }} 个应用场景
                  </el-tag>
                </div>
                <h1 class="hero-title">{{ detail.name }}</h1>
                <p class="hero-desc">{{ detail.description }}</p>
              </div>
            </div>
            <div class="hero-actions">
              <el-button round @click="$router.push('/agent-chat')">
                <el-icon><ChatDotSquare /></el-icon>向AI提问此模型
              </el-button>
            </div>
          </div>

          <!-- 双栏布局 -->
          <div class="detail-grid">
            <!-- 左栏 -->
            <div class="detail-left">
              <!-- ① 定义区 -->
              <div class="app-card detail-section" id="definition">
                <div class="app-card-header">
                  <span class="app-card-title">📖 模型定义</span>
                </div>
                <div class="app-card-body">
                  <div class="md-content" v-html="renderMarkdown(detail.definition || '')"></div>
                </div>
              </div>

              <!-- ② 核心公式区 (LaTeX) -->
              <div class="app-card detail-section" id="formulas">
                <div class="app-card-header">
                  <span class="app-card-title">📐 核心公式</span>
                </div>
                <div class="app-card-body">
                  <div v-if="detail.core_formulas?.length" class="formula-list">
                    <div v-for="(f, fi) in detail.core_formulas" :key="fi" class="formula-card">
                      <div class="formula-name">{{ f.name }}</div>
                      <div class="formula-latex" ref="formulaRefs"></div>
                      <div class="formula-desc">{{ f.explanation }}</div>
                    </div>
                  </div>
                  <div v-else style="text-align:center;padding:20px;color:var(--text-tertiary);">
                    暂无公式数据
                  </div>
                </div>
              </div>

              <!-- ③ 方法区：典型求解方法 -->
              <div class="app-card detail-section" id="methods">
                <div class="app-card-header">
                  <span class="app-card-title">⚙️ 求解方法</span>
                </div>
                <div class="app-card-body">
                  <div v-if="detail.algorithms?.length" class="methods-grid">
                    <div v-for="(a, ai) in detail.algorithms" :key="ai" class="method-item">
                      <span class="method-num">{{ ai + 1 }}</span>
                      <span class="method-name">{{ a }}</span>
                    </div>
                  </div>
                  <div v-if="detail.tools?.length" style="margin-top:14px;">
                    <span style="font-size: var(--text-xs);color:var(--text-tertiary);margin-right:8px;">常用工具：</span>
                    <el-tag v-for="(t, ti) in detail.tools" :key="ti" size="small" effect="plain" type="warning" round style="margin:2px;">
                      {{ t }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>

            <!-- 右栏 -->
            <div class="detail-right">
              <!-- ④ 例题区 -->
              <div class="app-card detail-section" id="example">
                <div class="app-card-header">
                  <span class="app-card-title">💡 经典例题</span>
                </div>
                <div class="app-card-body">
                  <template v-if="detail.example">
                    <div class="example-block">
                      <div class="example-label">📋 题目：{{ detail.example.title }}</div>
                      <p class="example-text">{{ detail.example.problem }}</p>
                    </div>
                    <div class="example-block">
                      <div class="example-label">🔬 解题思路</div>
                      <p class="example-text">{{ detail.example.solution }}</p>
                    </div>
                  </template>
                  <div v-else style="text-align:center;padding:20px;color:var(--text-tertiary);">
                    暂无例题数据
                  </div>
                </div>
              </div>

              <!-- ⑤ 代码区：Python 代码模板 + "在编辑器中打开"-->
              <div class="app-card detail-section" id="code">
                <div class="app-card-header">
                  <span class="app-card-title">💻 Python 代码模板</span>
                  <div style="display:flex;gap:6px;">
                    <el-button size="small" text @click="copyCode">
                      <el-icon><CopyDocument /></el-icon>复制
                    </el-button>
                    <el-button size="small" type="primary" round @click="openInEditor">
                      <el-icon><Edit /></el-icon>在编辑器中打开
                    </el-button>
                  </div>
                </div>
                <div class="app-card-body">
                  <div v-if="detail.code_template" class="code-wrapper">
                    <div class="code-lang-badge">Python</div>
                    <pre class="code-block"><code>{{ detail.code_template }}</code></pre>
                  </div>
                  <div v-else style="text-align:center;padding:30px;color:var(--text-tertiary);">
                    <el-icon :size="32"><Document /></el-icon>
                    <p style="margin-top:8px;">暂无代码模板</p>
                  </div>
                </div>
              </div>

              <!-- ⑥ 适用场景 -->
              <div class="app-card detail-section" id="scenarios">
                <div class="app-card-header">
                  <span class="app-card-title">🎯 适用场景</span>
                </div>
                <div class="app-card-body">
                  <div v-if="detail.scenarios?.length" class="scenario-list">
                    <div v-for="(s, si) in detail.scenarios" :key="si" class="scenario-item">
                      <el-icon :size="16" style="color:var(--success);flex-shrink:0;margin-top:2px;"><Check /></el-icon>
                      <span>{{ s }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ⑦ 相关模型推荐 -->
          <div class="app-card" style="margin-top:20px;" id="related">
            <div class="app-card-header">
              <span class="app-card-title">🔗 相关模型推荐</span>
              <span style="font-size: var(--text-xs);color:var(--text-tertiary);">探索其他 7 个模型分类</span>
            </div>
            <div class="app-card-body">
              <div class="related-grid">
                <div
                  v-for="r in relatedModels" :key="r.id"
                  class="related-card"
                  :style="{ '--rel-color': r.color, '--rel-bg': r.color + '08' }"
                  @click="$router.push(`/knowledge/${r.id}`)"
                >
                  <div class="related-icon" :style="{ background: r.color + '12', color: r.color }">
                    <el-icon :size="20"><component :is="catIcon(r.id)" /></el-icon>
                  </div>
                  <div class="related-info">
                    <div class="related-name">{{ r.name }}</div>
                    <div class="related-desc">{{ r.description?.substring(0, 40) }}…</div>
                  </div>
                  <el-icon :size="14" style="color:var(--text-tertiary);"><ArrowRight /></el-icon>
                </div>
              </div>
            </div>
          </div>

          <!-- 底部操作 -->
          <div style="text-align:center;margin-top:24px;">
            <el-button @click="$router.push('/knowledge-base')" round>
              <el-icon><ArrowLeft /></el-icon>返回学习中心
            </el-button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { knowledgeApi } from '../api'
import Sidebar from '../components/Sidebar.vue'
import {
  HomeFilled, WarningFilled, ChatDotSquare, ArrowLeft, ArrowRight,
  CopyDocument, Edit, Check, Document,
  TrendCharts, DataAnalysis, Tickets, Grid, Connection, PieChart, Share, Loading
} from '@element-plus/icons-vue'
import katex from 'katex'

const route = useRoute()
const router = useRouter()

const categoryId = ref(route.params.categoryId)
const loading = ref(true)
const notFound = ref(false)
const detail = ref(null)
const relatedModels = ref([])
const formulaRefs = ref([])

// 分类图标映射
function catIcon(id) {
  const map = {
    'optimization': TrendCharts,
    'prediction': DataAnalysis,
    'evaluation': Tickets,
    'classification-clustering': Grid,
    'differential-equations': Connection,
    'statistics': PieChart,
    'graph-theory': Share,
    'stochastic': Loading,
  }
  return map[id] || TrendCharts
}

// 简单 Markdown 渲染
function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code style="background:#f0f0f0;padding:1px 5px;border-radius:3px;font-size:0.9em;">$1</code>')
    .replace(/\n/g, '<br>')
}

// 渲染 LaTeX 公式
async function renderFormulas() {
  await nextTick()
  const container = document.querySelector('.formula-list')
  if (!container || !detail.value?.core_formulas) return

  const formulaCards = container.querySelectorAll('.formula-latex')
  detail.value.core_formulas.forEach((formula, idx) => {
    const el = formulaCards[idx]
    if (el && formula.latex) {
      try {
        katex.render(formula.latex, el, {
          displayMode: true,
          throwOnError: false,
          trust: true,
        })
      } catch (e) {
        el.textContent = formula.latex
      }
    }
  })
}

// 加载数据
async function loadDetail() {
  loading.value = true
  notFound.value = false
  try {
    const res = await knowledgeApi.getCategory(categoryId.value)
    detail.value = res
    await nextTick()
    await renderFormulas()
    // 加载相关模型（排除当前）
    loadRelatedModels()
  } catch (e) {
    if (e.response?.status === 404) {
      notFound.value = true
    }
  } finally {
    loading.value = false
  }
}

// 相关模型
async function loadRelatedModels() {
  try {
    const res = await knowledgeApi.getCategories()
    const cats = res.categories || []
    relatedModels.value = cats.filter(c => c.id !== categoryId.value)
  } catch (e) { /* ignore */ }
}

// 复制代码
function copyCode() {
  if (detail.value?.code_template) {
    navigator.clipboard.writeText(detail.value.code_template).then(() => {
      ElMessage.success('代码已复制到剪贴板')
    }).catch(() => {
      ElMessage.warning('复制失败，请手动复制')
    })
  }
}

// 在编辑器中打开
function openInEditor() {
  if (detail.value?.code_template) {
    localStorage.setItem('code_editor_template', detail.value.code_template)
    router.push('/code-editor')
  }
}

watch(() => route.params.categoryId, (newId) => {
  if (newId) {
    categoryId.value = newId
    loadDetail()
  }
})

onMounted(() => {
  loadDetail()
})
</script>

<style scoped lang="scss">
/* ============================================================
   Hero 头部 — 模型名称 + 标签
   ============================================================ */
.detail-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 32px;
  margin-bottom: 24px;
  background: var(--hero-bg);
  border: 1px solid var(--border-light);
  border-radius: 16px;
}

.hero-left {
  display: flex;
  align-items: flex-start;
  gap: 18px;
}

.hero-icon {
  width: 64px;
  height: 64px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hero-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hero-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.hero-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.2;
}

.hero-desc {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
  max-width: 600px;
}

.hero-actions {
  flex-shrink: 0;
  padding-top: 12px;
}

/* ============================================================
   双栏布局
   ============================================================ */
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

.detail-left, .detail-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ============================================================
   内容区通用样式
   ============================================================ */
.md-content {
  font-size: var(--text-sm);
  line-height: 1.8;
  color: var(--text-secondary);
}

/* —— ② 公式区 —— */
.formula-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.formula-card {
  padding: 16px;
  background: var(--bg-primary);
  border-radius: 10px;
  border: 1px solid var(--border-light);
}

.formula-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 10px;
}

.formula-latex {
  overflow-x: auto;
  padding: 8px 0;
  margin-bottom: 8px;
}

.formula-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  line-height: 1.6;
  padding-top: 8px;
  border-top: 1px dashed var(--border-light);
}

/* —— ③ 方法区 —— */
.methods-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.method-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--bg-primary);
  border-radius: 8px;
  transition: background 0.2s;

  &:hover {
    background: var(--primary-light);
  }
}

.method-num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--primary-light);
  color: var(--primary);
  font-size: var(--text-xs);
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.method-name {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-primary);
}

/* —— ④ 例题区 —— */
.example-block {
  margin-bottom: 14px;

  &:last-child {
    margin-bottom: 0;
  }
}

.example-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.example-text {
  font-size: var(--text-sm);
  line-height: 1.8;
  color: var(--text-secondary);
  margin: 0;
}

/* —— ⑤ 代码区 —— */
.code-wrapper {
  position: relative;
  background: #1e1e2e;
  border-radius: 10px;
  overflow: hidden;
}

.code-lang-badge {
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: var(--text-xs);
  font-weight: 600;
  color: #a6adc8;
  background: rgba(255, 255, 255, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
  z-index: 1;
}

.code-block {
  padding: 16px;
  margin: 0;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
  font-size: var(--text-xs);
  line-height: 1.7;
  color: #cdd6f4;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  white-space: pre;
  tab-size: 4;
}

/* —— ⑥ 适用场景 —— */
.scenario-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scenario-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 12px;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  background: var(--bg-primary);
  border-radius: 8px;
}

/* ============================================================
   ⑦ 相关模型推荐
   ============================================================ */
.related-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.related-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--rel-bg);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: var(--rel-color);
    background: var(--rel-color) + '12';
    transform: translateY(-2px);
  }
}

.related-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.related-info {
  flex: 1;
  min-width: 0;
}

.related-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.related-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ============================================================
   面包屑
   ============================================================ */
.breadcrumb-link {
  color: var(--primary);
  text-decoration: none;
  &:hover { text-decoration: underline; }
}

/* ============================================================
   响应式
   ============================================================ */
@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-hero {
    flex-direction: column;
  }

  .hero-actions {
    padding-top: 0;
  }
}
</style>
