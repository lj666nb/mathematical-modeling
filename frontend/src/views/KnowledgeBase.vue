<!--
============================================================
学习中心 - 树状导航式布局 (LRN-001/002/005)
改造要点：
  ① 左侧树状结构：分类→算法的层级导航
  ② 点击算法节点 → 直接查看该知识点的笔记
  ③ 点击分类节点 → 展开/折叠 + 查看分类概览
  ④ KaTeX 公式渲染 + highlight.js 语法高亮
  ⑤ 移动端 overlay sidebar
============================================================
-->
<template>
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <div class="page-container">
        <!-- 骨架屏 -->
        <template v-if="pageLoading">
          <div style="display:flex;gap:32px;">
            <div style="width:240px;flex-shrink:0;">
              <div v-for="i in 8" :key="i" class="skeleton" style="height:36px;margin-bottom:4px;border-radius:6px;"></div>
            </div>
            <div style="flex:1;">
              <div class="skeleton" style="height:60px;margin-bottom:20px;"></div>
              <div class="skeleton" style="height:200px;margin-bottom:16px;"></div>
              <div class="skeleton" style="height:160px;margin-bottom:16px;"></div>
            </div>
          </div>
        </template>

        <!-- ===== 文档式双栏布局 ===== -->
        <DocLayout v-else ref="docLayoutRef" :sidebar-title="'知识树'">
          <template #sidebar>
            <!-- 搜索 -->
            <div style="margin-bottom:var(--space-4);">
              <el-input
                v-model="searchQuery"
                placeholder="搜索…"
                clearable
                size="small"
                @keyup.enter="doSearch"
                @clear="clearSearch"
              >
                <template #prefix>
                  <el-icon :size="14"><Search /></el-icon>
                </template>
              </el-input>
              <!-- 搜索结果 -->
              <div v-if="searchResults.length > 0" style="margin-top:8px;">
                <div style="font-size:11px;color:var(--text-secondary);margin-bottom:6px;">
                  找到 {{ searchResults.length }} 个分类
                </div>
                <div style="display:flex;flex-wrap:wrap;gap:4px;">
                  <el-tag
                    v-for="r in searchResults" :key="r.category_id"
                    size="small" round
                    :color="r.color" effect="dark"
                    style="cursor:pointer;"
                    @click="selectSearchResult(r.category_id)"
                  >
                    {{ r.category_name }}
                  </el-tag>
                </div>
              </div>
              <div v-else-if="searchQuery && searched" style="margin-top:6px;color:var(--text-tertiary);font-size:11px;">
                未找到结果
              </div>
            </div>

            <!-- 分类树 -->
            <nav class="kb-tree">
              <div v-for="cat in categoryDetails" :key="cat.id">
                <!-- Level 0: 分类节点（可展开/折叠，可点击查看概览） -->
                <div
                  class="doc-tree-node level-0"
                  :class="{ active: selectedNode?.type === 'category' && selectedNode?.categoryId === cat.id }"
                  @click="selectCategory(cat)"
                >
                  <span class="tree-arrow" :class="{ expanded: expandedCats.has(cat.id) }" @click.stop="toggleCat(cat.id)">
                    ▶
                  </span>
                  <span class="tree-dot" :style="{ background: cat.color }"></span>
                  <span>{{ cat.name }}</span>
                  <span class="doc-tree-count">{{ cat.algorithms?.length || 0 }}</span>
                </div>

                <!-- Level 1: 算法子节点（transition 动画） -->
                <transition name="doc-slide-down">
                  <div v-show="expandedCats.has(cat.id)">
                    <div
                      v-for="(algo, ai) in cat.algorithms" :key="ai"
                      class="doc-tree-node level-1"
                      :class="{ active: selectedNode?.type === 'algorithm' && selectedNode?.categoryId === cat.id && selectedNode?.algorithmIndex === ai }"
                      @click="selectAlgorithm(cat, ai)"
                      :title="algo + (cat.scenarios?.[ai] ? ' — ' + cat.scenarios[ai] : '')"
                    >
                      <span class="tree-dot" style="opacity:0.3;"></span>
                      <span class="tree-icon">📄</span>
                      <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ algo }}</span>
                    </div>
                  </div>
                </transition>
              </div>
            </nav>

            <div class="doc-nav-divider"></div>

            <!-- 快捷跳转 -->
            <div class="doc-nav-label">快捷导航</div>
            <a class="doc-tree-node level-0" :class="{ active: selectedNode?.type === 'cases' }" @click.prevent="selectSection('cases')">
              <el-icon :size="16"><Trophy /></el-icon><span>竞赛案例库</span>
            </a>
            <a class="doc-tree-node level-0" :class="{ active: selectedNode?.type === 'exams' }" @click.prevent="selectSection('exams')">
              <el-icon :size="16"><Document /></el-icon><span>历年真题库</span>
            </a>
            <a class="doc-tree-node level-0" :class="{ active: selectedNode?.type === 'paths' }" @click.prevent="selectSection('paths')">
              <el-icon :size="16"><Guide /></el-icon><span>学习路径推荐</span>
            </a>
          </template>

          <template #default>
            <!-- ============================================================
                 算法知识点详情（选中算法节点时显示）
                 ============================================================ -->
            <template v-if="selectedNode?.type === 'algorithm' && currentAlgoCat">
              <!-- 面包屑导航 -->
              <div style="margin-bottom:16px;font-size:var(--text-xs);color:var(--text-tertiary);display:flex;align-items:center;gap:6px;">
                <span style="cursor:pointer;color:var(--color-gold);" @click="selectCategory(currentAlgoCat)">学习中心</span>
                <span>/</span>
                <span style="cursor:pointer;color:var(--color-gold);" @click="selectCategory(currentAlgoCat)">{{ currentAlgoCat.name }}</span>
                <span>/</span>
                <span style="color:var(--text-primary);">{{ currentAlgoName }}</span>
              </div>

              <!-- 算法标题 -->
              <div class="kb-section-header">
                <div class="kb-section-icon" :style="{ background: (currentAlgoCat.color || '#165DFF') + '15', color: currentAlgoCat.color }">
                  <el-icon :size="24"><component :is="catIcon(currentAlgoCat.id)" /></el-icon>
                </div>
                <div>
                  <h2 class="kb-section-name">{{ currentAlgoName }}</h2>
                  <p class="kb-section-meta">
                    {{ currentAlgoCat.name }} · {{ currentAlgoNote?.brief || '' }}
                  </p>
                </div>
              </div>

              <!-- 算法详细描述 (本地笔记) -->
              <div v-if="currentAlgoNote" class="doc-blockquote" style="margin-top:12px;">
                <p><strong>📖 算法原理</strong></p>
                <p style="line-height:1.8;">{{ currentAlgoNote.description }}</p>
              </div>

              <!-- 核心公式 (来自本地笔记) -->
              <template v-if="currentAlgoNote?.formulas?.length">
                <h3 class="doc-section-subtitle">📐 核心公式</h3>
                <div v-for="(f, fi) in currentAlgoNote.formulas" :key="fi" class="doc-formula-card">
                  <div class="formula-name">{{ f.name }}</div>
                  <div class="formula-latex">
                    <KatexFormula :latex="f.latex" :display-mode="true" />
                  </div>
                  <div class="formula-desc">{{ f.explanation }}</div>
                </div>
              </template>

              <!-- 实现步骤 -->
              <template v-if="currentAlgoNote?.steps?.length">
                <h3 class="doc-section-subtitle">📋 实现步骤</h3>
                <ol style="padding-left:20px;">
                  <li v-for="(s, si) in currentAlgoNote.steps" :key="si"
                      style="font-size:var(--text-sm);color:var(--text-secondary);line-height:2;">{{ s }}</li>
                </ol>
              </template>

              <!-- 应用场景 -->
              <template v-if="currentAlgoNote?.useCases?.length">
                <h3 class="doc-section-subtitle">🎯 适用场景</h3>
                <div class="doc-tag-group">
                  <el-tag v-for="(u, ui) in currentAlgoNote.useCases" :key="ui" size="small" effect="plain" round type="success">{{ u }}</el-tag>
                </div>
              </template>

              <!-- 代码模板 (来自本地笔记) -->
              <template v-if="currentAlgoNote?.code">
                <h3 class="doc-section-subtitle">💻 Python 代码示例</h3>
                <div style="display:flex;gap:8px;margin-bottom:8px;">
                  <el-button size="small" text @click="copyCode(currentAlgoNote.code)">
                    <el-icon><CopyDocument /></el-icon>复制代码
                  </el-button>
                  <el-button size="small" type="primary" round @click="openInEditor(currentAlgoNote.code)">
                    <el-icon><Edit /></el-icon>在编辑器中打开
                  </el-button>
                </div>
                <pre class="doc-code-block"><code>{{ currentAlgoNote.code }}</code></pre>
              </template>

              <!-- 实用技巧 -->
              <template v-if="currentAlgoNote?.tips">
                <h3 class="doc-section-subtitle">💡 实用技巧</h3>
                <div class="doc-blockquote">
                  <p>{{ currentAlgoNote.tips }}</p>
                </div>
              </template>

              <!-- 同类算法 -->
              <template v-if="currentAlgoCat.algorithms?.length > 1">
                <h3 class="doc-section-subtitle">🔗 同类算法</h3>
                <div class="doc-tag-group">
                  <el-tag
                    v-for="(a, ai) in currentAlgoCat.algorithms" :key="ai"
                    size="small"
                    :type="ai === selectedNode.algorithmIndex ? '' : 'info'"
                    :effect="ai === selectedNode.algorithmIndex ? 'dark' : 'plain'"
                    round
                    style="cursor:pointer;"
                    @click="selectAlgorithm(currentAlgoCat, ai)"
                  >
                    {{ a }}
                  </el-tag>
                </div>
              </template>

              <!-- 无本地笔记时的回退显示（使用后端数据） -->
              <template v-if="!currentAlgoNote">
                <div v-if="currentAlgoScenario" class="doc-blockquote" style="margin-top:12px;">
                  <p><strong>📋 适用场景</strong></p>
                  <p>{{ currentAlgoScenario }}</p>
                </div>
                <template v-if="currentAlgoCat.core_formulas?.length">
                  <h3 class="doc-section-subtitle">📐 核心公式</h3>
                  <div v-for="(f, fi) in currentAlgoCat.core_formulas" :key="fi" class="doc-formula-card">
                    <div class="formula-name">{{ f.name }}</div>
                    <div class="formula-latex">
                      <KatexFormula :latex="f.latex" :display-mode="true" />
                    </div>
                    <div class="formula-desc">{{ f.explanation }}</div>
                  </div>
                </template>
                <template v-if="currentAlgoCat.code_template">
                  <h3 class="doc-section-subtitle">💻 Python 代码模板</h3>
                  <div style="display:flex;gap:8px;margin-bottom:8px;">
                    <el-button size="small" text @click="copyCode(currentAlgoCat.code_template)">
                      <el-icon><CopyDocument /></el-icon>复制代码
                    </el-button>
                    <el-button size="small" type="primary" round @click="openInEditor(currentAlgoCat.code_template)">
                      <el-icon><Edit /></el-icon>在编辑器中打开
                    </el-button>
                  </div>
                  <pre class="doc-code-block"><code>{{ currentAlgoCat.code_template }}</code></pre>
                </template>
              </template>
            </template>

            <!-- ============================================================
                 分类概览（选中分类节点时显示）
                 ============================================================ -->
            <template v-else-if="selectedNode?.type === 'category' && currentAlgoCat">
              <div class="kb-section-header">
                <div class="kb-section-icon" :style="{ background: (currentAlgoCat.color || '#165DFF') + '15', color: currentAlgoCat.color }">
                  <el-icon :size="24"><component :is="catIcon(currentAlgoCat.id)" /></el-icon>
                </div>
                <div>
                  <h2 class="kb-section-name">{{ currentAlgoCat.name }}</h2>
                  <p class="kb-section-meta">
                    {{ currentAlgoCat.algorithms?.length || 0 }} 种算法 · {{ currentAlgoCat.scenarios?.length || 0 }} 个应用场景
                  </p>
                </div>
              </div>

              <div class="doc-prose">
                <p>{{ currentAlgoCat.definition || currentAlgoCat.description }}</p>
              </div>

              <!-- 核心公式 -->
              <template v-if="currentAlgoCat.core_formulas?.length">
                <h3 class="doc-section-subtitle">📐 核心公式</h3>
                <div v-for="(f, fi) in currentAlgoCat.core_formulas" :key="fi" class="doc-formula-card">
                  <div class="formula-name">{{ f.name }}</div>
                  <div class="formula-latex">
                    <KatexFormula :latex="f.latex" :display-mode="true" />
                  </div>
                  <div class="formula-desc">{{ f.explanation }}</div>
                </div>
              </template>

              <!-- 算法列表（可点击跳转） -->
              <template v-if="currentAlgoCat.algorithms?.length">
                <h3 class="doc-section-subtitle">📊 求解方法</h3>
                <table class="doc-table">
                  <thead>
                    <tr><th>算法</th><th>适用场景</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(a, ai) in currentAlgoCat.algorithms" :key="ai"
                        style="cursor:pointer;" @click="selectAlgorithm(currentAlgoCat, ai)"
                        :class="{ 'kb-algo-row-active': false }">
                      <td>
                        <span style="color:var(--color-gold);font-weight:500;">{{ a }}</span>
                      </td>
                      <td>{{ currentAlgoCat.scenarios?.[ai] || '—' }}</td>
                    </tr>
                  </tbody>
                </table>
              </template>

              <!-- 代码模板 -->
              <template v-if="currentAlgoCat.code_template">
                <h3 class="doc-section-subtitle">💻 Python 代码模板</h3>
                <pre class="doc-code-block"><code>{{ currentAlgoCat.code_template }}</code></pre>
              </template>
            </template>

            <!-- ============================================================
                 默认欢迎状态（未选择任何节点时）
                 ============================================================ -->
            <template v-else-if="!selectedNode">
              <div style="text-align:center;padding:60px 20px;">
                <div style="font-size:48px;margin-bottom:16px;">📚</div>
                <h2 style="font-size:var(--text-xl);color:var(--color-chalk);margin-bottom:8px;">欢迎来到学习中心</h2>
                <p style="color:var(--text-secondary);font-size:var(--text-sm);line-height:1.8;">
                  请从左侧 <strong style="color:var(--color-gold);">知识树</strong> 中选择一个算法知识点<br>
                  即可查看该知识点的核心公式、经典例题和代码模板
                </p>
              </div>
            </template>

            <!-- ===== ② 竞赛案例库 ===== -->
            <section v-if="selectedNode?.type === 'cases'" id="cases" class="doc-section">
              <h2 class="doc-section-title">🏆 竞赛案例库</h2>
              <p class="doc-prose" style="margin-bottom:16px;">历年竞赛优秀论文深度解析，覆盖国赛、MCM/ICM 等顶级赛事</p>

              <div v-if="caseList.length > 0">
                <div
                  v-for="cs in caseList" :key="cs.id"
                  class="kb-expand-item"
                  :class="{ expanded: expandedCase === cs.id }"
                >
                  <div class="kb-expand-header" @click="toggleCase(cs.id)">
                    <div style="flex:1;min-width:0;">
                      <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-weight:600;font-size:var(--text-sm);">{{ cs.title }}</span>
                        <el-tag size="small" :type="cs.award.includes('一等') || cs.award.includes('F') ? 'danger' : 'warning'" effect="dark" round>
                          {{ cs.award }}
                        </el-tag>
                      </div>
                      <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:4px;">
                        {{ cs.competition }} · {{ cs.year }}
                      </div>
                    </div>
                    <el-icon class="kb-expand-arrow" :class="{ rotated: expandedCase === cs.id }">
                      <ArrowDown />
                    </el-icon>
                  </div>
                  <transition name="doc-slide-down">
                    <div v-if="expandedCase === cs.id" class="kb-expand-body">
                      <div v-if="caseDetailLoading" style="text-align:center;padding:16px;">
                        <el-icon class="is-loading" :size="20"><Loading /></el-icon>
                      </div>
                      <template v-else-if="currentCase">
                        <p style="font-size:var(--text-sm);color:var(--text-secondary);margin-bottom:12px;">{{ cs.summary }}</p>
                        <h4 style="font-size:var(--text-sm);font-weight:600;margin-bottom:6px;">📋 赛题简介</h4>
                        <p style="font-size:var(--text-sm);color:var(--text-secondary);line-height:1.7;margin-bottom:12px;">{{ currentCase.problem_brief }}</p>
                        <h4 style="font-size:var(--text-sm);font-weight:600;margin-bottom:6px;">🔬 建模思路</h4>
                        <ol style="padding-left:18px;margin-bottom:12px;">
                          <li v-for="(step, si) in currentCase.modeling_approach" :key="si"
                              style="font-size:var(--text-sm);color:var(--text-secondary);line-height:1.7;">{{ step }}</li>
                        </ol>
                        <div class="doc-blockquote" style="margin-top:8px;">
                          <p><strong>✨ 论文亮点：</strong>{{ currentCase.highlights }}</p>
                        </div>
                        <div style="margin-top:8px;">
                          <span style="font-size:var(--text-xs);color:var(--text-tertiary);">要点：</span>
                          <el-tag v-for="(tk, ti) in (currentCase.takeaways || [])" :key="ti" size="small" effect="plain" round style="margin:2px;">{{ tk }}</el-tag>
                        </div>
                      </template>
                    </div>
                  </transition>
                </div>
              </div>
              <div v-else class="app-empty" style="padding:32px 0;">
                <p class="app-empty-text">暂无竞赛案例</p>
              </div>
            </section>

            <!-- ===== ③ 历年真题库 ===== -->
            <section v-if="selectedNode?.type === 'exams'" id="exams" class="doc-section">
              <h2 class="doc-section-title">📝 历年真题库</h2>
              <p class="doc-prose" style="margin-bottom:16px;">10道经典国赛/MCM赛题，按难度分级，从入门到竞赛全覆盖</p>

              <div v-if="examList.length > 0">
                <div
                  v-for="ex in examList" :key="ex.id"
                  class="kb-expand-item"
                  :class="{ expanded: expandedExam === ex.id }"
                >
                  <div class="kb-expand-header" @click="toggleExam(ex.id)">
                    <div style="flex:1;min-width:0;">
                      <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-weight:600;font-size:var(--text-sm);">{{ ex.title }}</span>
                        <el-tag size="small" effect="dark" round
                          :type="ex.difficulty >= 4 ? 'danger' : ex.difficulty >= 3 ? 'warning' : 'success'">
                          {{ '⭐'.repeat(ex.difficulty) }}
                        </el-tag>
                      </div>
                      <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:4px;">
                        {{ ex.competition }} · {{ ex.year }} · <span style="color:var(--primary);">{{ ex.topic }}</span>
                      </div>
                    </div>
                    <el-icon class="kb-expand-arrow" :class="{ rotated: expandedExam === ex.id }">
                      <ArrowDown />
                    </el-icon>
                  </div>
                  <transition name="doc-slide-down">
                    <div v-if="expandedExam === ex.id" class="kb-expand-body">
                      <div v-if="examDetailLoading" style="text-align:center;padding:16px;">
                        <el-icon class="is-loading" :size="20"><Loading /></el-icon>
                      </div>
                      <template v-else-if="currentExam">
                        <p style="font-size:var(--text-sm);color:var(--text-secondary);white-space:pre-wrap;line-height:1.7;margin-bottom:12px;">{{ currentExam.problem_text }}</p>
                        <h4 style="font-size:var(--text-sm);font-weight:600;margin-bottom:6px;">🔑 核心知识点</h4>
                        <div class="doc-tag-group">
                          <el-tag v-for="kc in currentExam.key_concepts" :key="kc" size="small" effect="plain" type="primary" round>{{ kc }}</el-tag>
                        </div>
                        <h4 style="font-size:var(--text-sm);font-weight:600;margin:12px 0 6px;">💡 解题要点</h4>
                        <ol style="padding-left:18px;">
                          <li v-for="(hint, hi) in currentExam.solution_hints" :key="hi"
                              style="font-size:var(--text-sm);color:var(--text-secondary);line-height:1.7;">{{ hint }}</li>
                        </ol>
                      </template>
                    </div>
                  </transition>
                </div>
              </div>
              <div v-else class="app-empty" style="padding:32px 0;">
                <p class="app-empty-text">暂无真题数据</p>
              </div>
            </section>

            <!-- ===== ④ 学习路径推荐 ===== -->
            <section v-if="selectedNode?.type === 'paths'" id="paths" class="doc-section">
              <h2 class="doc-section-title">🗺️ 学习路径推荐</h2>
              <p class="doc-prose" style="margin-bottom:16px;">新手入门 → 进阶提升 → 竞赛强化，循序渐进掌握数学建模</p>

              <div v-if="learningPaths.length > 0" class="kb-path-grid">
                <div v-for="(path, pi) in learningPaths" :key="pi" class="kb-path-card" :class="'level-' + path.level">
                  <div class="kb-path-header">
                    <div class="kb-path-badge" :class="'lvl-' + path.level">L{{ path.level }}</div>
                    <div>
                      <div style="font-weight:600;font-size:var(--text-sm);">{{ path.stage }}</div>
                      <div style="font-size:var(--text-xs);color:var(--text-tertiary);">预计 {{ path.estimated_hours }} 学时</div>
                    </div>
                  </div>
                  <p style="font-size:var(--text-xs);color:var(--text-secondary);line-height:1.6;margin:10px 0;">{{ path.description }}</p>
                  <div class="doc-tag-group">
                    <el-tag v-for="m in path.models" :key="m" size="small" effect="plain" round>{{ m }}</el-tag>
                  </div>
                  <div style="margin-top:8px;display:flex;flex-direction:column;gap:4px;">
                    <div v-for="(topic, ti) in path.topics" :key="ti" style="display:flex;align-items:center;gap:6px;font-size:var(--text-xs);color:var(--text-secondary);">
                      <el-icon :size="12" style="color:var(--success);"><Check /></el-icon>
                      <span>{{ topic }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <!-- 底部信息 -->
            <div style="text-align:center;padding:24px 0;color:var(--text-tertiary);font-size:var(--text-xs);border-top:var(--border-subtle);margin-top:32px;">
              Last Updated: 2026-07-09
            </div>
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
import { knowledgeApi } from '../api'
import { getAlgorithmNote } from '../data/knowledgeBase.js'
import Sidebar from '../components/Sidebar.vue'
import DocLayout from '../components/DocLayout.vue'
import KatexFormula from '../components/KatexFormula.vue'
import {
  Search, ArrowDown, Loading, Check, CopyDocument, Edit,
  Trophy, Document, Guide,
  TrendCharts, DataAnalysis, Tickets, Grid, Connection, PieChart, Share
} from '@element-plus/icons-vue'

const router = useRouter()

// —— 状态 ——
const pageLoading = ref(true)
const docLayoutRef = ref(null)

const categoryDetails = ref([])
const expandedCats = ref(new Set())     // 展开的分类 ID 集合
const selectedNode = ref(null)           // { type, categoryId, algorithmIndex }

const searchQuery = ref('')
const searchResults = ref([])
const lastQuery = ref('')
const searched = ref(false)

const caseList = ref([])
const examList = ref([])
const learningPaths = ref([])
const expandedCase = ref(null)
const expandedExam = ref(null)
const currentCase = ref(null)
const currentExam = ref(null)
const caseDetailLoading = ref(false)
const examDetailLoading = ref(false)

// —— 计算属性 ——
const totalAlgorithmCount = computed(() =>
  categoryDetails.value.reduce((sum, c) => sum + (c.algorithms?.length || 0), 0)
)

const currentAlgoCat = computed(() => {
  if (!selectedNode.value) return null
  if (selectedNode.value.type === 'cases' || selectedNode.value.type === 'exams' || selectedNode.value.type === 'paths') return null
  return categoryDetails.value.find(c => c.id === selectedNode.value.categoryId) || null
})

const currentAlgoName = computed(() => {
  if (!currentAlgoCat.value || selectedNode.value?.type !== 'algorithm') return ''
  return currentAlgoCat.value.algorithms?.[selectedNode.value.algorithmIndex] || ''
})

const currentAlgoScenario = computed(() => {
  if (!currentAlgoCat.value || selectedNode.value?.type !== 'algorithm') return ''
  return currentAlgoCat.value.scenarios?.[selectedNode.value.algorithmIndex] || ''
})

// 从本地硬编码知识库获取算法独立笔记
const currentAlgoNote = computed(() => {
  if (!currentAlgoCat.value || selectedNode.value?.type !== 'algorithm') return null
  return getAlgorithmNote(
    currentAlgoCat.value.id,
    selectedNode.value.algorithmIndex,
    currentAlgoName.value  // 优先按名称匹配
  )
})

// —— 分类图标映射 ——
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

function truncateStr(str, len) {
  return str?.length > len ? str.slice(0, len) + '…' : str
}

// —— 树操作 ——
function toggleCat(catId) {
  const next = new Set(expandedCats.value)
  if (next.has(catId)) next.delete(catId)
  else next.add(catId)
  expandedCats.value = next
}

function selectCategory(cat) {
  toggleCat(cat.id)  // 点击分类时也展开
  selectedNode.value = { type: 'category', categoryId: cat.id }
  if (docLayoutRef.value) docLayoutRef.value.closeSidebar()
}

function selectAlgorithm(cat, algoIndex) {
  // 确保所属分类已展开
  const next = new Set(expandedCats.value)
  next.add(cat.id)
  expandedCats.value = next

  selectedNode.value = { type: 'algorithm', categoryId: cat.id, algorithmIndex: algoIndex }
  if (docLayoutRef.value) docLayoutRef.value.closeSidebar()
}

function selectSection(type) {
  selectedNode.value = { type }
  if (docLayoutRef.value) docLayoutRef.value.closeSidebar()
}

// —— 搜索 ——
function selectSearchResult(categoryId) {
  const cat = categoryDetails.value.find(c => c.id === categoryId)
  if (cat) {
    selectCategory(cat)
    searchQuery.value = ''
    searchResults.value = []
    searched.value = false
  }
}

async function doSearch() {
  if (!searchQuery.value.trim()) return
  lastQuery.value = searchQuery.value.trim()
  try {
    const res = await knowledgeApi.search(searchQuery.value.trim())
    searchResults.value = res.results || []
  } catch (e) { console.error(e) }
  searched.value = true
}

function clearSearch() {
  searchResults.value = []
  searched.value = false
}

// —— 案例库展开 ——
async function toggleCase(id) {
  if (expandedCase.value === id) { expandedCase.value = null; return }
  expandedCase.value = id
  caseDetailLoading.value = true
  currentCase.value = null
  try {
    const res = await knowledgeApi.getCaseDetail(id)
    currentCase.value = res
  } catch (e) { console.error(e) }
  finally { caseDetailLoading.value = false }
}

// —— 真题库展开 ——
async function toggleExam(id) {
  if (expandedExam.value === id) { expandedExam.value = null; return }
  expandedExam.value = id
  examDetailLoading.value = true
  currentExam.value = null
  try {
    const res = await knowledgeApi.getExamDetail(id)
    currentExam.value = res
  } catch (e) { console.error(e) }
  finally { examDetailLoading.value = false }
}

// —— 代码操作 ——
function copyCode(code) {
  if (code) {
    navigator.clipboard.writeText(code).then(() => {
      ElMessage.success('代码已复制到剪贴板')
    }).catch(() => { ElMessage.warning('复制失败') })
  }
}

function openInEditor(code) {
  if (code) {
    localStorage.setItem('code_editor_template', code)
    router.push('/code-editor')
  }
}

// —— 数据加载 ——
onMounted(async () => {
  try {
    const [catRes, caseRes, examRes, pathRes] = await Promise.all([
      knowledgeApi.getCategories(),
      knowledgeApi.getCases(),
      knowledgeApi.getExams(),
      knowledgeApi.getLearningPaths(),
    ])

    const categories = catRes.categories || []
    caseList.value = caseRes.cases || []
    examList.value = examRes.exams || []
    learningPaths.value = pathRes.paths || []

    // 加载所有分类详情
    if (categories.length > 0) {
      const details = await Promise.all(
        categories.map(c => knowledgeApi.getCategory(c.id).catch(() => null))
      )
      categoryDetails.value = details.filter(Boolean)

      // 默认：展开第一个分类，选中第一个算法
      if (categoryDetails.value.length > 0) {
        const first = categoryDetails.value[0]
        expandedCats.value = new Set([first.id])
        if (first.algorithms?.length > 0) {
          selectedNode.value = { type: 'algorithm', categoryId: first.id, algorithmIndex: 0 }
        } else {
          selectedNode.value = { type: 'category', categoryId: first.id }
        }
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    pageLoading.value = false
  }
})
</script>

<style scoped lang="scss">
/* ============================================================
   分类区块样式
   ============================================================ */

.kb-tree {
  display: flex;
  flex-direction: column;
}

.kb-section-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}

.kb-section-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kb-section-name {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-chalk);
  letter-spacing: -0.01em;
  line-height: 1.2;
  margin: 0;
}

.kb-section-meta {
  font-size: var(--text-xs);
  color: var(--color-chalk-dim);
  margin-top: 4px;
}

/* —— 可展开条目 (案例/真题) —— */
.kb-expand-item {
  border: var(--border-subtle);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-3);
  transition: border-color var(--duration-fast) var(--ease-out);

  &.expanded {
    border-color: var(--color-gold);
  }
}

.kb-expand-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out);

  &:hover {
    background: var(--color-slate-800);
  }
}

.kb-expand-arrow {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  transition: transform 0.25s var(--ease-out);
  flex-shrink: 0;

  &.rotated {
    transform: rotate(180deg);
  }
}

.kb-expand-body {
  padding: 0 16px 16px;
}

/* —— 学习路径卡片 —— */
.kb-path-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;

  @media (max-width: 1000px) {
    grid-template-columns: 1fr;
  }
}

.kb-path-card {
  background: var(--color-slate-800);
  border: var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 18px;

  &.level-1 { border-top: 3px solid var(--color-success); }
  &.level-2 { border-top: 3px solid var(--color-gold); }
  &.level-3 { border-top: 3px solid var(--color-warning); }
}

.kb-path-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.kb-path-badge {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: 700;
  flex-shrink: 0;

  &.lvl-1 { background: var(--color-success); color: #fff; }
  &.lvl-2 { background: var(--color-gold); color: #fff; }
  &.lvl-3 { background: var(--color-warning); color: #fff; }
}

@media (max-width: 768px) {
  .kb-path-grid {
    grid-template-columns: 1fr;
  }
}
</style>
