<!--
============================================================
建模题库 - 树状导航式布局 (EXP-001/002)
改造要点：
  ① 左侧树状结构：学科分类 → 实验列表
  ② 点击实验节点 → 直接查看该实验的完整详情
  ③ 点击分类 → 展开/折叠子节点
  ④ 代码模板使用 highlight.js 语法高亮
  ⑤ 移动端 overlay sidebar
============================================================
-->
<template>
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <div class="page-container">
        <!-- 骨架屏 -->
        <template v-if="loading">
          <div style="display:flex;gap:32px;">
            <div style="width:240px;flex-shrink:0;">
              <div v-for="i in 9" :key="i" class="skeleton" style="height:36px;margin-bottom:4px;border-radius:6px;"></div>
            </div>
            <div style="flex:1;">
              <div class="skeleton" style="height:200px;margin-bottom:16px;"></div>
            </div>
          </div>
        </template>

        <!-- ===== 文档式双栏布局 ===== -->
        <DocLayout v-else ref="docLayoutRef" :sidebar-title="'题库导航'">
          <template #sidebar>
            <!-- 学科树 -->
            <nav class="exp-tree">
              <div v-for="sub in subjects" :key="sub.key">
                <!-- Level 0: 分类节点 -->
                <div
                  class="doc-tree-node level-0"
                  :class="{ active: selectedSubject === sub.key && !selectedExperiment }"
                  @click="toggleSubject(sub.key)"
                >
                  <span class="tree-arrow" :class="{ expanded: expandedSubjects.has(sub.key) }">
                    ▶
                  </span>
                  <span class="tree-icon">📁</span>
                  <span>{{ sub.label }}</span>
                  <span class="doc-tree-count">{{ sub.count }}</span>
                </div>

                <!-- Level 1: 实验子节点 -->
                <transition name="doc-slide-down">
                  <div v-show="expandedSubjects.has(sub.key)">
                    <div
                      v-for="exp in getExperimentsBySubject(sub.key)" :key="exp.id"
                      class="doc-tree-node level-1"
                      :class="{ active: selectedExperiment?.id === exp.id }"
                      @click="selectExperiment(exp, sub.key)"
                    >
                      <span class="tree-icon" style="font-size:12px;">📄</span>
                      <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ exp.title }}</span>
                      <span v-if="completedIds.has(exp.id)" style="color:var(--color-success);font-size:12px;flex-shrink:0;">✓</span>
                    </div>
                    <div v-if="getExperimentsBySubject(sub.key).length === 0" style="padding:6px 12px 6px 36px;font-size:12px;color:var(--text-tertiary);">
                      暂无实验
                    </div>
                  </div>
                </transition>
              </div>
            </nav>

            <div class="doc-nav-divider"></div>

            <!-- 学习进度 -->
            <div class="doc-nav-label">学习进度</div>
            <div style="padding:0 var(--space-3);">
              <div style="display:flex;justify-content:space-between;font-size:var(--text-xs);color:var(--text-secondary);margin-bottom:8px;">
                <span>完成进度</span>
                <span>{{ completedCount }}/{{ totalCount }}</span>
              </div>
              <div style="height:6px;background:var(--color-slate-600);border-radius:3px;overflow:hidden;">
                <div
                  style="height:100%;background:var(--color-gold);border-radius:3px;transition:width 0.6s ease;"
                  :style="{ width: progressPct + '%' }"
                ></div>
              </div>
              <div v-if="progressPct > 0" style="text-align:center;font-size:var(--text-xs);color:var(--color-gold);margin-top:6px;font-weight:600;">
                {{ progressPct }}%
              </div>
            </div>
          </template>

          <template #default>
            <!-- ============================================================
                 实验详情（选中实验节点时显示）
                 ============================================================ -->
            <template v-if="selectedExperiment">
              <!-- 面包屑 -->
              <div style="margin-bottom:16px;font-size:var(--text-xs);color:var(--text-tertiary);display:flex;align-items:center;gap:6px;">
                <span style="cursor:pointer;color:var(--color-gold);" @click="clearSelection">建模题库</span>
                <span>/</span>
                <span style="cursor:pointer;color:var(--color-gold);" @click="clearSelection">{{ selectedExperiment.subject }}</span>
                <span>/</span>
                <span style="color:var(--text-primary);">{{ selectedExperiment.title }}</span>
              </div>

              <!-- 实验标题区 -->
              <div style="margin-bottom:20px;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                  <el-tag
                    :type="subjectTagType(selectedExperiment.subject) || 'info'"
                    effect="plain" size="small" round
                  >
                    {{ selectedExperiment.subject }}
                  </el-tag>
                  <div class="exp-stars">
                    <el-icon v-for="i in 5" :key="i" :size="13"
                      :color="i <= selectedExperiment.difficulty ? '#FF7D00' : '#E5E6EB'">
                      <StarFilled v-if="i <= selectedExperiment.difficulty" />
                      <Star v-else />
                    </el-icon>
                  </div>
                  <span v-if="completedIds.has(selectedExperiment.id)" class="exp-completed-badge">
                    <el-icon :size="14"><Check /></el-icon>已完成
                  </span>
                </div>
                <h2 style="font-size:var(--text-xl);font-weight:600;color:var(--color-chalk);margin:0;">{{ selectedExperiment.title }}</h2>
              </div>

              <!-- 建模要求 -->
              <div style="margin-bottom:20px;">
                <h4 class="exp-detail-title">📋 建模要求</h4>
                <p class="exp-detail-text">{{ selectedExperiment.description }}</p>
              </div>

              <!-- 涉及知识点 -->
              <div v-if="parsePoints(selectedExperiment.reference_points).length > 0" style="margin-bottom:20px;">
                <h4 class="exp-detail-title">🎯 涉及知识点</h4>
                <div class="doc-tag-group">
                  <el-tag
                    v-for="pt in parsePoints(selectedExperiment.reference_points)" :key="pt"
                    effect="plain" round
                  >
                    {{ pt }}
                  </el-tag>
                </div>
              </div>

              <!-- 代码模板 (highlight.js) -->
              <div v-if="selectedExperiment.template_code" style="margin-bottom:20px;">
                <h4 class="exp-detail-title">💻 代码模板</h4>
                <div style="display:flex;gap:8px;margin-bottom:8px;">
                  <el-button size="small" text @click="copyCodeStr(selectedExperiment.template_code)">
                    <el-icon><CopyDocument /></el-icon>复制代码
                  </el-button>
                </div>
                <pre class="doc-code-block"><code v-html="highlightedCode(selectedExperiment.template_code)"></code></pre>
              </div>

              <!-- 操作按钮 -->
              <div style="display:flex;gap:10px;justify-content:flex-end;padding-top:12px;border-top:var(--border-subtle);">
                <el-button @click="clearSelection" round>返回列表</el-button>
                <el-button type="primary" @click="startExperiment(selectedExperiment.id)" round>
                  <el-icon><Edit /></el-icon>
                  {{ completedIds.has(selectedExperiment.id) ? '再次练习' : '开始建模' }}
                </el-button>
              </div>
            </template>

            <!-- ============================================================
                 分类筛选视图（点击分类节点时显示该分类下所有实验列表）
                 ============================================================ -->
            <template v-else-if="selectedSubject && selectedSubject !== 'all'">
              <div style="margin-bottom:16px;display:flex;align-items:center;gap:10px;">
                <h2 style="font-size:var(--text-lg);font-weight:600;color:var(--color-chalk);margin:0;">
                  {{ selectedSubject }}
                </h2>
                <span style="font-size:var(--text-xs);color:var(--text-tertiary);">
                  {{ filteredExperiments.length }} 个实验
                </span>
              </div>

              <div v-if="filteredExperiments.length === 0" class="app-empty">
                <div class="app-empty-icon"><el-icon :size="28"><Notebook /></el-icon></div>
                <p class="app-empty-text">该分类暂无建模实验</p>
              </div>

              <!-- 实验列表（简化卡片） -->
              <div v-else>
                <div
                  v-for="exp in filteredExperiments" :key="exp.id"
                  class="exp-card"
                  :class="{ completed: completedIds.has(exp.id) }"
                  @click="selectExperiment(exp, selectedSubject)"
                >
                  <div class="exp-card-top">
                    <div style="display:flex;align-items:center;gap:8px;">
                      <el-tag
                        :type="subjectTagType(exp.subject) || 'info'"
                        effect="plain" size="small" round
                      >
                        {{ exp.subject }}
                      </el-tag>
                      <div class="exp-stars">
                        <el-icon v-for="i in 5" :key="i" :size="12"
                          :color="i <= exp.difficulty ? '#FF7D00' : '#E5E6EB'">
                          <StarFilled v-if="i <= exp.difficulty" />
                          <Star v-else />
                        </el-icon>
                      </div>
                    </div>
                    <span v-if="completedIds.has(exp.id)" class="exp-completed-badge">
                      <el-icon :size="12"><Check /></el-icon>已完成
                    </span>
                  </div>
                  <h3 class="exp-card-title">{{ exp.title }}</h3>
                  <p class="exp-card-desc">{{ truncate(exp.description, 100) }}</p>
                  <div v-if="exp.reference_points" class="exp-card-tags">
                    <el-tag
                      v-for="pt in parsePoints(exp.reference_points).slice(0, 4)" :key="pt"
                      size="small" effect="plain" round
                    >
                      {{ pt }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </template>

            <!-- ============================================================
                 "全部"视图（默认：全部实验列表）
                 ============================================================ -->
            <template v-else>
              <div style="margin-bottom:16px;display:flex;align-items:center;gap:10px;">
                <h2 style="font-size:var(--text-lg);font-weight:600;color:var(--color-chalk);margin:0;">全部实验</h2>
                <span style="font-size:var(--text-xs);color:var(--text-tertiary);">{{ totalCount }} 个建模实验</span>
              </div>

              <div v-if="allExperiments.length === 0" class="app-empty">
                <div class="app-empty-icon"><el-icon :size="28"><Notebook /></el-icon></div>
                <p class="app-empty-text">暂无建模实验数据</p>
              </div>

              <div v-else>
                <div
                  v-for="exp in paginatedExperiments" :key="exp.id"
                  class="exp-card"
                  :class="{ completed: completedIds.has(exp.id) }"
                  @click="selectExperiment(exp, 'all')"
                >
                  <div class="exp-card-top">
                    <div style="display:flex;align-items:center;gap:8px;">
                      <el-tag
                        :type="subjectTagType(exp.subject) || 'info'"
                        effect="plain" size="small" round
                      >
                        {{ exp.subject }}
                      </el-tag>
                      <div class="exp-stars">
                        <el-icon v-for="i in 5" :key="i" :size="12"
                          :color="i <= exp.difficulty ? '#FF7D00' : '#E5E6EB'">
                          <StarFilled v-if="i <= exp.difficulty" />
                          <Star v-else />
                        </el-icon>
                      </div>
                    </div>
                    <span v-if="completedIds.has(exp.id)" class="exp-completed-badge">
                      <el-icon :size="12"><Check /></el-icon>已完成
                    </span>
                  </div>
                  <h3 class="exp-card-title">{{ exp.title }}</h3>
                  <p class="exp-card-desc">{{ truncate(exp.description, 100) }}</p>
                  <div v-if="exp.reference_points" class="exp-card-tags">
                    <el-tag
                      v-for="pt in parsePoints(exp.reference_points).slice(0, 4)" :key="pt"
                      size="small" effect="plain" round
                    >
                      {{ pt }}
                    </el-tag>
                  </div>
                </div>
              </div>

              <!-- 分页 -->
              <div v-if="totalCount > pageSize" class="exp-pagination">
                <span style="font-size:var(--text-xs);color:var(--text-tertiary);">共 {{ totalCount }} 个实验</span>
                <el-pagination
                  background layout="prev,pager,next"
                  :total="totalCount" :page-size="pageSize"
                  :current-page="currentPage"
                  @current-change="p => currentPage = p"
                  small
                />
              </div>
            </template>
          </template>
        </DocLayout>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { experimentApi, practiceApi } from '../api'
import Sidebar from '../components/Sidebar.vue'
import DocLayout from '../components/DocLayout.vue'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import {
  Notebook, StarFilled, Star, Check, CopyDocument, Edit
} from '@element-plus/icons-vue'

// 注册 Python 语法高亮
hljs.registerLanguage('python', python)

const router = useRouter()
const docLayoutRef = ref(null)

// —— 状态 ——
const loading = ref(false)
const allExperiments = ref([])
const totalCount = ref(0)
const completedIds = ref(new Set())
const completedCount = ref(0)
const currentPage = ref(1)
const pageSize = 50

// 树状态
const expandedSubjects = ref(new Set(['all'])) // 默认展开"全部"
const selectedSubject = ref('all')             // 当前筛选的学科
const selectedExperiment = ref(null)           // 当前选中的实验对象

// 学科分类
const subjects = ref([
  { key: 'all', label: '全部', count: 0 },
  { key: '优化模型', label: '优化模型', count: 0 },
  { key: '预测模型', label: '预测模型', count: 0 },
  { key: '评价模型', label: '评价模型', count: 0 },
  { key: '分类与聚类', label: '分类与聚类', count: 0 },
  { key: '微分方程', label: '微分方程', count: 0 },
  { key: '统计模型', label: '统计模型', count: 0 },
  { key: '图论与网络', label: '图论与网络', count: 0 },
  { key: '随机模型', label: '随机模型', count: 0 },
])

const progressPct = computed(() =>
  totalCount.value > 0 ? Math.round((completedCount.value / totalCount.value) * 100) : 0
)

// 按分类筛选的实验
const filteredExperiments = computed(() => {
  if (selectedSubject.value === 'all') return allExperiments.value
  return allExperiments.value.filter(e => e.subject === selectedSubject.value)
})

const paginatedExperiments = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return allExperiments.value.slice(start, start + pageSize)
})

// —— 工具函数 ——
function subjectTagType(s) {
  const m = { '优化模型': '', '预测模型': 'success', '评价模型': 'warning', '分类与聚类': 'info',
    '微分方程': 'danger', '统计模型': '', '图论与网络': 'success', '随机模型': 'warning' }
  return m[s] || ''
}

function parsePoints(p) {
  if (!p) return []
  try { return JSON.parse(p) }
  catch { return p.split(',').map(s => s.trim()).filter(Boolean) }
}

function truncate(str, len) {
  return str?.length > len ? str.slice(0, len) + '…' : str
}

function highlightedCode(code) {
  try {
    return hljs.highlight(code, { language: 'python' }).value
  } catch {
    return code
  }
}

function copyCodeStr(code) {
  if (code) {
    navigator.clipboard.writeText(code).then(() => {
      ElMessage.success('代码已复制')
    }).catch(() => { ElMessage.warning('复制失败') })
  }
}

function getExperimentsBySubject(key) {
  if (key === 'all') return allExperiments.value
  return allExperiments.value.filter(e => e.subject === key)
}

// —— 树操作 ——
function toggleSubject(key) {
  const next = new Set(expandedSubjects.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
  }
  expandedSubjects.value = next
  selectedSubject.value = key
  selectedExperiment.value = null  // 切换分类时清除选中的实验
  currentPage.value = 1
  if (docLayoutRef.value) docLayoutRef.value.closeSidebar()
}

function selectExperiment(exp, subjectKey) {
  selectedExperiment.value = exp
  selectedSubject.value = subjectKey
  // 确保分类展开
  const next = new Set(expandedSubjects.value)
  next.add(subjectKey)
  expandedSubjects.value = next
  if (docLayoutRef.value) docLayoutRef.value.closeSidebar()
}

function clearSelection() {
  selectedExperiment.value = null
}

function startExperiment(id) {
  router.push(`/code-editor/${id}`)
}

// —— 数据加载 ——
async function loadExperiments() {
  loading.value = true
  try {
    const res = await experimentApi.getList({ page: 1, page_size: 100 })
    allExperiments.value = res.experiments || []
    totalCount.value = res.total || 0

    // 更新各分类数量
    subjects.value.forEach(s => {
      if (s.key === 'all') s.count = allExperiments.value.length
      else s.count = allExperiments.value.filter(e => e.subject === s.key).length
    })
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(async () => {
  await loadExperiments()
  // 加载完成记录
  try {
    const pr = await practiceApi.getRecords({ page: 1, page_size: 100 })
    completedIds.value = new Set((pr.records || []).map(r => r.experiment_id))
    completedCount.value = completedIds.value.size
  } catch (e) { console.error(e) }
})
</script>

<style scoped lang="scss">
/* ============================================================
   实验树 & 卡片
   ============================================================ */

.exp-tree {
  display: flex;
  flex-direction: column;
}

/* —— 实验卡片（点击跳转详情） —— */
.exp-card {
  border: var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 16px 18px;
  margin-bottom: var(--space-3);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);

  &:hover {
    border-color: var(--color-gold);
    background: var(--color-slate-800);
  }

  &.completed {
    border-left: 3px solid var(--color-success);
  }
}

.exp-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.exp-stars {
  display: flex;
  gap: 1px;
}

.exp-completed-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-success);
  background: rgba(0, 180, 42, 0.08);
  padding: 2px 10px;
  border-radius: var(--radius-full);
}

.exp-card-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-chalk);
  margin: 0 0 6px 0;
}

.exp-card-desc {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 8px;
}

.exp-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* —— 实验详情样式 —— */
.exp-detail-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px 0;
}

.exp-detail-text {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.8;
  margin: 0;
}

/* —— 分页 —— */
.exp-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-6);
  padding-top: var(--space-4);
  border-top: var(--border-subtle);
}
</style>
