<template>
  <!--
  ============================================================
  数据工作台 — 全面优化版
  WRK-004: 数据处理工作区（上传/清洗/预览）
  WRK-005: 交互式可视化（ECharts）
  WRK-006: 论文草稿编辑器（Markdown + KaTeX 实时预览）
  WRK-007: 建模画布（拖拽式模型流程图）
  ============================================================
  -->
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <div class="page-container">
        <!-- 面包屑 -->
        <div class="app-breadcrumb">
          <el-icon><HomeFilled /></el-icon><span>首页</span>
          <span class="sep">/</span><span class="current">数据工作台</span>
        </div>

        <!-- 页面标题 -->
        <div class="page-header-area">
          <div class="page-title-row">
            <div>
              <h1 class="page-title">数据工作台</h1>
              <p class="page-subtitle">数据处理、可视化分析、论文草稿、建模画布 — 一站式建模工具箱</p>
            </div>
            <div class="header-actions">
              <el-tag size="small" effect="plain" round type="info">{{ dataFiles.length }} 个数据文件</el-tag>
            </div>
          </div>
        </div>

        <!-- ====== 自定义 Tab 导航 ====== -->
        <div class="ws-tabs">
          <button
            v-for="tab in tabs" :key="tab.name"
            class="ws-tab-btn"
            :class="{ active: activeTab === tab.name }"
            @click="activeTab = tab.name"
          >
            <span class="tab-icon">{{ tab.icon }}</span>
            <span class="tab-label">{{ tab.label }}</span>
            <span v-if="tab.name === 'data' && dataFiles.length" class="tab-badge">{{ dataFiles.length }}</span>
          </button>
        </div>

        <!-- ==================== Tab 1: 数据处理 ==================== -->
        <div v-show="activeTab === 'data'" class="ws-tab-content">
          <!-- 拖拽上传区 -->
          <div
            class="drop-zone"
            :class="{ dragover: isDragover }"
            @dragover.prevent="isDragover = true"
            @dragleave.prevent="isDragover = false"
            @drop.prevent="onDrop"
            @click="triggerUpload"
          >
            <div class="drop-icon">
              <el-icon :size="36"><UploadFilled /></el-icon>
            </div>
            <div class="drop-text">
              <strong>拖拽文件到此处</strong> 或点击上传
            </div>
            <div class="drop-hint">支持 CSV、Excel (.xlsx/.xls)、JSON 格式</div>
            <input ref="fileInput" type="file" accept=".csv,.xlsx,.xls,.json" multiple
              style="display:none" @change="onFileChange" />
          </div>

          <!-- 示例数据集 -->
          <div class="demo-section" v-if="demoDatasets.length">
            <div class="demo-header">
              <span class="demo-title">📦 示例数据集</span>
              <span class="demo-hint">一键导入，体验数据工作台功能</span>
            </div>
            <div class="demo-grid">
              <div
                v-for="ds in demoDatasets" :key="ds.key"
                class="demo-card"
                @click="loadDemo(ds.key)"
              >
                <div class="demo-card-header">
                  <span class="demo-card-icon">📊</span>
                  <span class="demo-card-name">{{ ds.label }}</span>
                  <el-button size="small" type="primary" plain round :loading="ds._loading" @click.stop="loadDemo(ds.key)">
                    {{ ds._loading ? '导入中' : '导入' }}
                  </el-button>
                </div>
                <div class="demo-card-desc">{{ ds.description }}</div>
                <div class="demo-card-meta">
                  <span>{{ ds.rows }} 行</span>
                  <span>{{ ds.columns.length }} 列</span>
                  <span v-if="ds.size">{{ formatSize(ds.size) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 数据工作区（有文件时显示） -->
          <div class="ws-grid" v-if="dataFiles.length > 0">
            <!-- 左栏：文件列表 -->
            <div class="ws-left">
              <div class="app-card">
                <div class="app-card-header">
                  <span class="app-card-title">数据文件</span>
                  <el-button size="small" @click="triggerUpload" round>上传文件</el-button>
                </div>
                <div class="app-card-body" style="padding-top:0;">
                  <div v-for="f in dataFiles" :key="f.name" class="file-row"
                    :class="{ active: previewFile === f.name }"
                    @click="loadPreview(f.name)">
                    <span class="file-icon">📄</span>
                    <span class="file-name">{{ f.name }}</span>
                    <span class="file-size">{{ formatSize(f.size) }}</span>
                    <el-button text type="danger" size="small" :icon="Delete"
                      @click.stop="removeFile(f.name)" />
                  </div>
                </div>
              </div>
            </div>

            <!-- 右栏：数据预览 -->
            <div class="ws-right">
              <!-- 统计卡片 -->
              <div class="stat-grid" v-if="previewData">
                <div class="stat-item learning">
                  <div class="stat-icon-wrap"><el-icon :size="18"><Grid /></el-icon></div>
                  <div class="stat-value">{{ previewData.total_rows || 0 }}</div>
                  <div class="stat-label">总行数</div>
                </div>
                <div class="stat-item projects">
                  <div class="stat-icon-wrap"><el-icon :size="18"><Menu /></el-icon></div>
                  <div class="stat-value">{{ (previewData.columns || []).length }}</div>
                  <div class="stat-label">总列数</div>
                </div>
                <div class="stat-item messages">
                  <div class="stat-icon-wrap"><el-icon :size="18"><WarningFilled /></el-icon></div>
                  <div class="stat-value">{{ missingRate }}%</div>
                  <div class="stat-label">缺失率</div>
                </div>
                <div class="stat-item practices">
                  <div class="stat-icon-wrap"><el-icon :size="18"><CircleCheckFilled /></el-icon></div>
                  <div class="stat-value">{{ dataQuality }}</div>
                  <div class="stat-label">数据质量</div>
                </div>
              </div>

              <!-- 数据预览 -->
              <div class="app-card" v-if="previewFile">
                <div class="app-card-header">
                  <span class="app-card-title">数据预览: {{ previewFile }}</span>
                  <span class="preview-info">
                    {{ previewData?.total_rows || 0 }}行 × {{ (previewData?.columns || []).length }}列
                  </span>
                </div>
                <div class="app-card-body">
                  <!-- 列统计 -->
                  <div v-if="previewData?.stats && Object.keys(previewData.stats).length" class="col-stats">
                    <h4 class="section-label">列统计</h4>
                    <div class="stat-chips">
                      <div v-for="(stat, col) in previewData.stats" :key="col" class="stat-chip">
                        <strong>{{ col }}</strong>
                        <span class="chip-vals">
                          min:{{ stat.min }} max:{{ stat.max }} avg:{{ stat.mean }} 缺失:{{ stat.missing }}
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- 数据表格 -->
                  <div class="data-table-wrap">
                    <table class="data-table" v-if="previewData?.columns?.length">
                      <thead>
                        <tr>
                          <th>#</th>
                          <th v-for="(c, ci) in previewData.columns" :key="ci"
                            :class="'type-' + (previewData.col_types?.[ci] || 'string')">
                            {{ c }}
                            <span class="col-type-badge">{{ previewData.col_types?.[ci] === 'number' ? '123' : 'Aa' }}</span>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(row, ri) in (previewData.rows || []).slice(0, 20)" :key="ri">
                          <td class="row-num">{{ ri + 1 }}</td>
                          <td v-for="(cell, ci) in row" :key="ci"
                            :class="'type-' + (previewData.col_types?.[ci] || 'string')">
                            {{ cell || '(空)' }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <!-- 清洗操作 -->
                  <div class="clean-section">
                    <h4 class="section-label">数据清洗</h4>
                    <div class="clean-controls">
                      <el-select v-model="cleanOp" placeholder="填充缺失值" size="small" style="width:140px;" clearable>
                        <el-option label="均值填充" value="mean" />
                        <el-option label="中位数填充" value="median" />
                        <el-option label="众数填充" value="mode" />
                        <el-option label="固定值填充" value="value" />
                        <el-option label="删除含缺失行" value="drop" />
                      </el-select>
                      <el-input v-if="cleanOp === 'value'" v-model="fillValue" placeholder="填充值"
                        size="small" style="width:100px;" />
                      <el-checkbox v-model="dropDup" size="small">去重</el-checkbox>
                      <el-button type="primary" size="small" :loading="cleaning" @click="doClean" round>
                        执行清洗
                      </el-button>
                    </div>
                    <div v-if="cleanResult" class="clean-result">
                      ✅ 清洗完成: {{ cleanResult.cleaned }} ({{ cleanResult.rows_before }}行)
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== Tab 2: 可视化分析 ==================== -->
        <div v-show="activeTab === 'viz'" class="ws-tab-content">
          <div class="ws-grid">
            <div class="ws-left">
              <div class="app-card">
                <div class="app-card-header">
                  <span class="app-card-title">图表配置</span>
                </div>
                <div class="app-card-body">
                  <el-form label-width="80px" size="small">
                    <el-form-item label="数据文件">
                      <el-select v-model="chartFile" placeholder="选择数据文件" style="width:100%;"
                        @change="loadChartData">
                        <el-option v-for="f in dataFiles" :key="f.name" :label="f.name" :value="f.name" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="图表类型">
                      <div class="chart-type-grid">
                        <button
                          v-for="ct in chartTypes" :key="ct.value"
                          class="chart-type-btn"
                          :class="{ active: chartType === ct.value }"
                          @click="chartType = ct.value"
                          :title="ct.label"
                        >{{ ct.icon }}</button>
                      </div>
                    </el-form-item>
                    <el-form-item label="X轴">
                      <el-select v-model="chartXCol" placeholder="选择列" style="width:100%;"
                        :disabled="!chartColumns.length">
                        <el-option v-for="c in chartColumns" :key="c" :label="c" :value="c" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="Y轴">
                      <el-select v-model="chartYCol" placeholder="选择列" style="width:100%;"
                        :disabled="!chartColumns.length">
                        <el-option v-for="c in chartColumns" :key="c" :label="c" :value="c" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="配色">
                      <div class="color-scheme-row">
                        <button
                          v-for="cs in colorSchemes" :key="cs.value"
                          class="color-scheme-btn"
                          :class="{ active: colorScheme === cs.value }"
                          @click="colorScheme = cs.value"
                          :title="cs.label"
                        >
                          <span class="color-dots">
                            <span v-for="c in cs.colors" :key="c" class="color-dot" :style="{ background: c }"></span>
                          </span>
                        </button>
                      </div>
                    </el-form-item>
                    <el-form-item label="标题">
                      <el-input v-model="chartTitle" placeholder="图表标题" />
                    </el-form-item>
                    <el-button type="primary" :disabled="!chartXCol" @click="renderChart" round
                      style="width:100%;">
                      生成图表
                    </el-button>
                  </el-form>
                </div>
              </div>
            </div>
            <div class="ws-right">
              <div class="app-card">
                <div class="app-card-header">
                  <span class="app-card-title">图表预览</span>
                  <el-button v-if="chartInstance" size="small" type="success" @click="exportChartPng" round>
                    📥 导出PNG
                  </el-button>
                </div>
                <div class="app-card-body">
                  <div ref="chartContainer" class="chart-container"></div>
                  <div v-if="!chartInstance" class="chart-empty">
                    <el-icon :size="48"><TrendCharts /></el-icon>
                    <p>配置左侧参数并点击"生成图表"</p>
                    <span class="chart-empty-hint">支持柱状图、折线图、散点图、饼图、面积图</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== Tab 3: 建模画布 ==================== -->
        <div v-show="activeTab === 'canvas'" class="ws-tab-content">
          <div class="canvas-toolbar">
            <el-button size="small" @click="addCanvasNode" round>添加节点</el-button>
            <el-button size="small" type="warning" @click="canvasMode = 'connect'" :disabled="canvasNodes.length < 2" round>
              {{ canvasMode === 'connect' ? '连接模式 (点击取消)' : '连接节点' }}
            </el-button>
            <el-button size="small" @click="autoLayoutNodes" round :disabled="canvasNodes.length < 2">
              自动布局
            </el-button>
            <el-button size="small" type="danger" @click="clearCanvasNodes" round>清空画布</el-button>
            <span class="canvas-hint">
              拖拽节点移动 | {{ canvasMode === 'connect' ? '点击两个节点建立连线' : '点击节点选中' }}
            </span>
          </div>
          <div class="canvas-area" ref="canvasArea"
            @mousedown="onCanvasMouseDown"
            @mousemove="onCanvasMouseMove"
            @mouseup="onCanvasMouseUp"
            @mouseleave="onCanvasMouseUp">
            <svg class="canvas-svg" v-if="canvasNodes.length > 0">
              <line v-for="(edge, ei) in canvasEdges" :key="'e'+ei"
                :x1="edge.x1" :y1="edge.y1" :x2="edge.x2" :y2="edge.y2"
                stroke="#165DFF" stroke-width="2" marker-end="url(#arrowhead)" />
              <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                  <polygon points="0 0, 10 3.5, 0 7" fill="#165DFF" />
                </marker>
              </defs>
            </svg>
            <div v-for="(node, ni) in canvasNodes" :key="'n'+ni"
              class="canvas-node"
              :class="{ selected: selectedNode === ni, connecting: connectingNode === ni }"
              :style="{ left: node.x + 'px', top: node.y + 'px', borderColor: nodeColors[ni % nodeColors.length] }"
              @mousedown.stop="onNodeMouseDown($event, ni)"
              @click.stop="onNodeClick(ni)">
              <div class="cn-header" :style="{ background: nodeColors[ni % nodeColors.length] + '15' }">
                {{ node.label || '模型节点' }}
              </div>
              <div class="cn-body">
                <input v-model="node.label" class="cn-input" placeholder="节点名称" @click.stop />
                <input v-model="node.detail" class="cn-input cn-detail" placeholder="描述（如：线性回归模型）" @click.stop />
              </div>
              <button class="cn-delete" @click.stop="deleteCanvasNode(ni)">×</button>
            </div>
          </div>
          <div class="canvas-legend" v-if="canvasNodes.length > 0">
            <span>节点: {{ canvasNodes.length }}</span>
            <span>连线: {{ canvasEdges.length }}</span>
          </div>
        </div>

        <!-- ==================== Tab 4: 论文编辑器 ==================== -->
        <div v-show="activeTab === 'paper'" class="ws-tab-content">
          <div class="paper-layout">
            <!-- 编辑区 -->
            <div class="app-card paper-editor-card">
              <div class="app-card-header">
                <span class="app-card-title">Markdown 编辑</span>
                <div class="paper-toolbar">
                  <span class="paper-stats">
                    {{ (mdContent || '').length }} 字 · 约 {{ readingTime }} 分钟阅读
                  </span>
                  <el-button size="small" @click="insertTemplate" round>插入模板</el-button>
                  <el-button size="small" type="success" @click="downloadMd" round :disabled="!mdContent">
                    下载MD
                  </el-button>
                  <el-button size="small" @click="downloadHtml" round :disabled="!mdContent">
                    导出HTML
                  </el-button>
                </div>
              </div>
              <div class="app-card-body editor-body">
                <textarea
                  v-model="mdContent"
                  class="md-editor"
                  placeholder="# 论文标题&#10;&#10;## 摘要&#10;&#10;在此编写您的数学建模论文..."
                  spellcheck="false"
                ></textarea>
              </div>
            </div>

            <!-- 预览区 -->
            <div class="app-card paper-preview-card">
              <div class="app-card-header">
                <span class="app-card-title">实时预览</span>
              </div>
              <div class="app-card-body preview-body">
                <div v-if="!mdContent" class="preview-empty">
                  <el-icon :size="48"><Document /></el-icon>
                  <p>在左侧编辑器中开始写作，此处将实时预览</p>
                  <span>支持 Markdown 语法 + LaTeX 数学公式（$...$ / $$...$$）</span>
                </div>
                <div v-else class="markdown-body md-preview" v-html="renderedMd"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { workspaceApi } from '../api'
import { ElMessage } from 'element-plus'
import Sidebar from '../components/Sidebar.vue'
import {
  HomeFilled, UploadFilled, Delete, DataAnalysis, TrendCharts, Document,
  Grid, Menu, WarningFilled, CircleCheckFilled
} from '@element-plus/icons-vue'
import katex from 'katex'
import { marked } from 'marked'

// ==================== Tab 导航 ====================
const activeTab = ref('data')
const tabs = [
  { name: 'data', label: '数据处理', icon: '📊' },
  { name: 'viz', label: '可视化分析', icon: '📈' },
  { name: 'canvas', label: '建模画布', icon: '🎨' },
  { name: 'paper', label: '论文编辑器', icon: '📝' },
]

// ==================== 数据处理 ====================
const fileInput = ref(null)
const dataFiles = ref([])
const isDragover = ref(false)
const previewFile = ref('')
const previewData = ref(null)
const cleanOp = ref('')
const fillValue = ref('0')
const dropDup = ref(false)
const cleaning = ref(false)
const cleanResult = ref(null)
const demoDatasets = ref([])

const missingRate = computed(() => {
  if (!previewData.value?.stats) return '0'
  const stats = previewData.value.stats
  const totalCells = Object.keys(stats).length * (previewData.value.total_rows || 1)
  const totalMissing = Object.values(stats).reduce((s, v) => s + (v.missing || 0), 0)
  return ((totalMissing / Math.max(totalCells, 1)) * 100).toFixed(1)
})

const dataQuality = computed(() => {
  const mr = parseFloat(missingRate.value)
  if (mr === 0) return '优秀'
  if (mr < 5) return '良好'
  if (mr < 15) return '一般'
  return '需清洗'
})

function triggerUpload() { fileInput.value?.click() }

async function onDrop(e) {
  isDragover.value = false
  const files = e.dataTransfer?.files
  if (!files?.length) return
  for (const f of files) {
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    if (!['.csv', '.xlsx', '.xls', '.json', '.tsv'].includes(ext)) {
      ElMessage.warning(`${f.name}: 不支持的文件格式`)
      continue
    }
    const formData = new FormData()
    formData.append('file', f)
    try {
      await workspaceApi.uploadData(formData)
      ElMessage.success(`已上传: ${f.name}`)
    } catch (err) {
      ElMessage.error(`上传失败: ${f.name}`)
    }
  }
  await loadFiles()
}

async function onFileChange(e) {
  const files = e.target.files
  if (!files?.length) return
  for (const f of files) {
    const formData = new FormData()
    formData.append('file', f)
    try {
      await workspaceApi.uploadData(formData)
      ElMessage.success(`已上传: ${f.name}`)
    } catch (err) {
      ElMessage.error(`上传失败: ${f.name}`)
    }
  }
  fileInput.value.value = ''
  await loadFiles()
}

async function loadFiles() {
  try {
    const res = await workspaceApi.listFiles()
    dataFiles.value = res.files || []
  } catch (e) { /* ignore */ }
}

async function loadPreview(filename) {
  previewFile.value = filename
  previewData.value = null
  try {
    previewData.value = await workspaceApi.previewData(filename)
  } catch (e) {
    ElMessage.error('预览失败')
  }
}

async function removeFile(filename) {
  try {
    await workspaceApi.deleteFile(filename)
    if (previewFile.value === filename) {
      previewFile.value = ''
      previewData.value = null
    }
    await loadFiles()
    ElMessage.success('已删除')
  } catch (e) { ElMessage.error('删除失败') }
}

async function doClean() {
  if (!previewFile.value) return
  cleaning.value = true
  cleanResult.value = null
  try {
    const ops = {}
    if (cleanOp.value) ops.fill_na = cleanOp.value
    if (cleanOp.value === 'value') ops.fill_value = fillValue.value
    if (dropDup.value) ops.drop_duplicates = true
    const res = await workspaceApi.cleanData(previewFile.value, ops)
    cleanResult.value = res
    ElMessage.success('清洗完成')
    await loadFiles()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '清洗失败')
  } finally {
    cleaning.value = false
  }
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

// ==================== 示例数据集 ====================
async function loadDemoDatasets() {
  try {
    const res = await workspaceApi.getDemoDatasets()
    demoDatasets.value = (res.datasets || []).map(d => ({ ...d, _loading: false }))
  } catch (e) { /* ignore if backend not available */ }
}

async function loadDemo(key) {
  const ds = demoDatasets.value.find(d => d.key === key)
  if (!ds) return
  ds._loading = true
  try {
    await workspaceApi.loadDemoDataset(key)
    ElMessage.success(`已导入示例数据: ${ds.label}`)
    await loadFiles()
  } catch (e) {
    ElMessage.error('导入失败')
  } finally {
    ds._loading = false
  }
}

// ==================== 可视化 ====================
const chartFile = ref('')
const chartType = ref('bar')
const chartXCol = ref('')
const chartYCol = ref('')
const chartTitle = ref('')
const chartColumns = ref([])
const chartData = ref(null)
const chartContainer = ref(null)
const chartInstance = ref(null)
const colorScheme = ref('blue')
let echartsInstance = null

const chartTypes = [
  { value: 'bar', label: '柱状图', icon: '📊' },
  { value: 'line', label: '折线图', icon: '📈' },
  { value: 'scatter', label: '散点图', icon: '🔵' },
  { value: 'pie', label: '饼图', icon: '🥧' },
  { value: 'area', label: '面积图', icon: '🏔️' },
]

const colorSchemes = [
  { value: 'blue', label: '品牌蓝', colors: ['#165DFF', '#3C7EFF', '#4080FF', '#6AA1FF', '#94BFFF'] },
  { value: 'warm', label: '暖色', colors: ['#F53F3F', '#FF7D00', '#FFC53D', '#FAAD14', '#FF9C6E'] },
  { value: 'cool', label: '冷色', colors: ['#00B42A', '#0FC6C2', '#08979C', '#36CFC9', '#87E8DE'] },
]

async function loadChartData() {
  if (!chartFile.value) return
  try {
    chartData.value = await workspaceApi.previewData(chartFile.value)
    chartColumns.value = chartData.value?.columns || []
    // 智能推荐：数值列优先作为Y轴
    const numCols = chartColumns.value.filter((c, i) =>
      chartData.value?.col_types?.[i] === 'number')
    chartXCol.value = chartColumns.value[0] || ''
    chartYCol.value = numCols[0] || chartColumns.value[1] || chartColumns.value[0] || ''
  } catch (e) { /* ignore */ }
}

function getSchemeColors() {
  return colorSchemes.find(s => s.value === colorScheme.value)?.colors || colorSchemes[0].colors
}

async function renderChart() {
  if (!chartContainer.value || !chartData.value) return

  if (!echartsInstance) {
    try {
      const echarts = await import('echarts')
      echartsInstance = echarts
    } catch {
      ElMessage.warning('ECharts 未安装，请运行 npm install echarts')
      return
    }
  }

  if (chartInstance.value) chartInstance.value.dispose()

  const data = chartData.value
  const xi = data.columns.indexOf(chartXCol.value)
  const yi = data.columns.indexOf(chartYCol.value)
  const rows = data.rows || []

  const xData = rows.map(r => r[xi] || '').slice(0, 50)
  const yData = rows.map(r => {
    const v = parseFloat((r[yi] || '0').replace(/,/g, ''))
    return isNaN(v) ? 0 : v
  }).slice(0, 50)

  const colors = getSchemeColors()

  const option = {
    title: { text: chartTitle.value || `${chartYCol.value} vs ${chartXCol.value}`, left: 'center',
      textStyle: { fontSize: 16, fontWeight: 600, color: '#1D2129' } },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: xData, axisLabel: { rotate: 45, fontSize: 11 },
      axisLine: { lineStyle: { color: '#E5E6EB' } } },
    yAxis: { type: 'value', axisLine: { lineStyle: { color: '#E5E6EB' } },
      splitLine: { lineStyle: { color: '#F2F3F5' } } },
    series: [{
      name: chartYCol.value,
      type: chartType.value === 'area' ? 'line' : chartType.value,
      data: yData,
      smooth: chartType.value === 'line' || chartType.value === 'area',
      areaStyle: chartType.value === 'area' ? { opacity: 0.3 } : undefined,
      itemStyle: { color: colors[0] },
      color: colors,
    }],
    grid: { left: 60, right: 20, top: 50, bottom: 60 },
    color: colors,
  }

  if (chartType.value === 'pie') {
    option.xAxis = undefined
    option.yAxis = undefined
    option.series = [{
      name: chartYCol.value,
      type: 'pie',
      radius: ['40%', '65%'],
      data: xData.map((name, i) => ({ name, value: yData[i] })),
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {d}%' },
      emphasis: { label: { fontSize: 16, fontWeight: 'bold' } },
    }]
  }

  if (chartType.value === 'scatter') {
    option.tooltip = { trigger: 'item' }
  }

  nextTick(() => {
    const inst = echartsInstance.init(chartContainer.value)
    inst.setOption(option)
    chartInstance.value = inst
    window.addEventListener('resize', () => inst.resize())
  })
}

function exportChartPng() {
  if (!chartInstance.value) return
  try {
    const url = chartInstance.value.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff'
    })
    const a = document.createElement('a')
    a.href = url
    a.download = `${chartTitle.value || 'chart'}.png`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    ElMessage.success('图表已导出为 PNG')
  } catch (e) {
    ElMessage.error('导出失败：' + e.message)
  }
}

// ==================== 论文编辑器 ====================
const mdContent = ref('')

const readingTime = computed(() => {
  const chars = (mdContent.value || '').length
  const words = chars / 2 // 中文约2字符=1词
  return Math.max(1, Math.ceil(words / 200))
})

const PAPER_TEMPLATE = `# 数学建模竞赛论文

## 摘要
本文针对[赛题名称]，建立了[模型类型]模型，解决了[核心问题]。
主要方法包括：[关键方法]。结果表明：[主要结论]。

## 一、问题重述
### 1.1 问题背景
[描述赛题背景]

### 1.2 问题分析
- **问题一**：[分析]
- **问题二**：[分析]
- **问题三**：[分析]

## 二、模型假设与符号说明
### 2.1 模型假设
1. [假设1]
2. [假设2]

### 2.2 符号说明
| 符号 | 含义 | 单位 |
|------|------|------|
| $x$ | [变量名] | [单位] |

## 三、模型建立与求解
### 3.1 问题一的模型
#### 3.1.1 模型建立
[数学模型描述，使用LaTeX公式]

#### 3.1.2 模型求解
[求解过程]

#### 3.1.3 结果分析
[结果展示与分析]

### 3.2 问题二的模型
...

## 四、模型检验与敏感性分析
### 4.1 模型检验
[检验方法]

### 4.2 敏感性分析
[参数敏感性]

## 五、模型评价与推广
### 5.1 模型优点
...

### 5.2 模型不足
...

### 5.3 模型推广
...

## 六、结论
[总结全文]

## 参考文献
[1] ...
`

function insertTemplate() {
  if (mdContent.value && mdContent.value.length > 10) {
    mdContent.value += '\n' + PAPER_TEMPLATE
  } else {
    mdContent.value = PAPER_TEMPLATE
  }
}

function downloadMd() {
  if (!mdContent.value) return
  const blob = new Blob([mdContent.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'draft_paper.md'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function downloadHtml() {
  if (!mdContent.value) return
  const htmlContent = renderedMd.value
  const fullHtml = `<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>论文草稿</title>
<style>body{max-width:800px;margin:40px auto;padding:0 20px;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;font-size:16px;line-height:1.8;color:#1D2129;}h1{font-size:28px;border-bottom:2px solid #E5E6EB;padding-bottom:8px;}h2{font-size:22px;border-bottom:1px solid #E5E6EB;padding-bottom:6px;}code{background:#F2F3F5;padding:2px 6px;border-radius:3px;font-size:14px;}table{border-collapse:collapse;width:100%;margin:16px 0;}td,th{border:1px solid #E5E6EB;padding:8px 12px;text-align:left;}.katex{font-size:1.1em;}</style>
</head><body>${htmlContent}</body></html>`
  const blob = new Blob([fullHtml], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'draft_paper.html'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('HTML 已导出')
}

// Markdown + LaTeX 渲染（使用 marked 库）
const renderedMd = computed(() => {
  if (!mdContent.value) return ''
  let text = mdContent.value

  // 1. 提取 $$...$$ 块级公式 → 占位符
  const blockFormulas = []
  text = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, formula) => {
    const idx = blockFormulas.length
    try {
      blockFormulas.push(katex.renderToString(formula.trim(), {
        displayMode: true, throwOnError: false, trust: true
      }))
    } catch {
      blockFormulas.push(`<pre>$${formula}$$</pre>`)
    }
    return `__KTXBLOCK_${idx}__`
  })

  // 2. 提取 $...$ 行内公式 → 占位符
  const inlineFormulas = []
  text = text.replace(/\$([^$]+?)\$/g, (_, formula) => {
    const idx = inlineFormulas.length
    try {
      inlineFormulas.push(katex.renderToString(formula.trim(), {
        displayMode: false, throwOnError: false, trust: true
      }))
    } catch {
      inlineFormulas.push(`<code>$${formula}$</code>`)
    }
    return `__KTXINLINE_${idx}__`
  })

  // 3. 使用 marked 渲染 Markdown
  let html
  try {
    html = marked.parse(text, {
      breaks: true,
      gfm: true,
    })
  } catch {
    html = text
  }

  // 4. 替换占位符 → KaTeX HTML
  blockFormulas.forEach((formula, i) => {
    html = html.replace(`__KTXBLOCK_${i}__`, formula)
  })
  inlineFormulas.forEach((formula, i) => {
    html = html.replace(`__KTXINLINE_${i}__`, formula)
  })

  return html
})

// ==================== 建模画布 ====================
const canvasNodes = ref([])
const canvasEdges = ref([])
const canvasMode = ref('move')
const selectedNode = ref(null)
const connectingNode = ref(null)
const canvasArea = ref(null)
const draggingNode = ref(null)
const dragOffset = ref({ x: 0, y: 0 })
const nodeColors = ['#165DFF', '#00B42A', '#FF7D00', '#9B59B6', '#F53F3F', '#0FC6C2', '#FFC53D', '#722ED1']

let nodeCounter = 0

function addCanvasNode() {
  nodeCounter++
  const area = canvasArea.value
  const w = area?.clientWidth || 800
  const h = area?.clientHeight || 500
  canvasNodes.value.push({
    label: `模型${nodeCounter}`,
    detail: '',
    x: Math.random() * (w - 200) + 20,
    y: Math.random() * (h - 120) + 20,
  })
}

function autoLayoutNodes() {
  const nodes = canvasNodes.value
  if (nodes.length < 2) return
  const cols = Math.ceil(Math.sqrt(nodes.length))
  const area = canvasArea.value
  const w = area?.clientWidth || 800
  const cellW = (w - 40) / cols
  nodes.forEach((node, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    node.x = col * cellW + 20
    node.y = row * 140 + 30
  })
  updateEdgePositions()
}

function deleteCanvasNode(index) {
  canvasEdges.value = canvasEdges.value.filter(e => e.from !== index && e.to !== index)
  canvasEdges.value.forEach(e => {
    if (e.from > index) e.from--
    if (e.to > index) e.to--
  })
  canvasNodes.value.splice(index, 1)
  if (selectedNode.value === index) selectedNode.value = null
  if (connectingNode.value === index) connectingNode.value = null
}

function clearCanvasNodes() {
  canvasNodes.value = []
  canvasEdges.value = []
  selectedNode.value = null
  connectingNode.value = null
  nodeCounter = 0
}

function onNodeClick(index) {
  if (canvasMode.value === 'connect') {
    if (connectingNode.value === null) {
      connectingNode.value = index
    } else if (connectingNode.value !== index) {
      canvasEdges.value.push({ from: connectingNode.value, to: index, x1: 0, y1: 0, x2: 0, y2: 0 })
      connectingNode.value = null
      canvasMode.value = 'move'
      updateEdgePositions()
    }
  } else {
    selectedNode.value = selectedNode.value === index ? null : index
  }
}

function onNodeMouseDown(event, index) {
  if (canvasMode.value === 'connect') return
  draggingNode.value = index
  const node = canvasNodes.value[index]
  dragOffset.value = { x: event.clientX - node.x, y: event.clientY - node.y }
}

function onCanvasMouseDown() {
  selectedNode.value = null
  connectingNode.value = null
  if (canvasMode.value === 'connect') canvasMode.value = 'move'
}

function onCanvasMouseMove(event) {
  if (draggingNode.value === null) return
  const area = canvasArea.value
  if (!area) return
  const rect = area.getBoundingClientRect()
  const x = event.clientX - rect.left - dragOffset.value.x
  const y = event.clientY - rect.top - dragOffset.value.y
  canvasNodes.value[draggingNode.value].x = Math.max(0, Math.min(x, rect.width - 180))
  canvasNodes.value[draggingNode.value].y = Math.max(0, Math.min(y, rect.height - 100))
  updateEdgePositions()
}

function onCanvasMouseUp() {
  draggingNode.value = null
}

function updateEdgePositions() {
  canvasEdges.value.forEach(e => {
    const from = canvasNodes.value[e.from]
    const to = canvasNodes.value[e.to]
    if (from && to) {
      e.x1 = from.x + 90; e.y1 = from.y + 50
      e.x2 = to.x + 90; e.y2 = to.y + 50
    }
  })
}

onMounted(() => {
  loadFiles()
  loadDemoDatasets()
})
</script>

<style scoped lang="scss">
// ============================================================
// 数据工作台样式 — 匹配 Dashboard 质量标准
// ============================================================

// —— 页面头部操作 ——
.header-actions {
  display: flex;
  gap: var(--space-3);
  align-items: center;
}

// ====== 自定义 Tab 导航 ======
.ws-tabs {
  display: flex;
  gap: 4px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 4px;
  margin-bottom: var(--space-6);
}

.ws-tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 10px 16px;
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--text-secondary);
  transition: all var(--duration-fast) var(--ease-out);
  position: relative;
  font-family: var(--font-body);

  &:hover {
    color: var(--text-primary);
    background: var(--bg-hover);
  }

  &.active {
    color: var(--primary);
    background: var(--bg-card);
    box-shadow: var(--glow-card);
  }
}

.tab-icon {
  font-size: 1.1em;
}

.tab-badge {
  font-size: var(--text-xs);
  background: var(--primary-light);
  color: var(--primary);
  padding: 1px 8px;
  border-radius: var(--radius-full);
  font-weight: var(--weight-semibold);
  min-width: 20px;
  text-align: center;
}

.ws-tab-content {
  animation: tabFadeIn 0.25s var(--ease-out);
}

@keyframes tabFadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

// ====== 拖拽上传区 ======
.drop-zone {
  border: 2px dashed var(--border-light);
  border-radius: var(--radius-xl);
  padding: var(--space-7) var(--space-5);
  text-align: center;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out);
  background: var(--bg-primary);
  margin-bottom: var(--space-5);

  &:hover, &.dragover {
    border-color: var(--primary);
    background: var(--primary-light);
  }

  &.dragover {
    border-style: solid;
    box-shadow: 0 0 0 4px var(--primary-light);
    transform: scale(1.01);
  }
}

.drop-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--bg-card);
  border: var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--space-4);
  color: var(--primary);
}

.drop-text {
  font-size: var(--text-base);
  color: var(--text-primary);
  margin-bottom: var(--space-2);

  strong {
    color: var(--primary);
  }
}

.drop-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

// ====== 示例数据集 ======
.demo-section {
  margin-bottom: var(--space-5);
}

.demo-header {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.demo-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--text-primary);
}

.demo-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.demo-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
}

.demo-card {
  background: var(--bg-card);
  border: var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);

  &:hover {
    border-color: var(--primary);
    box-shadow: var(--glow-elevated);
  }
}

.demo-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.demo-card-icon {
  font-size: 1.2em;
}

.demo-card-name {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--text-primary);
  flex: 1;
}

.demo-card-desc {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: var(--space-2);
}

.demo-card-meta {
  display: flex;
  gap: var(--space-3);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

// ====== 布局网格 ======
.ws-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--space-5);
  min-height: 400px;
}

.ws-left, .ws-right {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

// ====== 文件列表 ======
.file-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 8px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  border: 1px solid transparent;
  transition: all 0.15s;
  margin-bottom: 2px;

  &:hover { background: var(--bg-primary); }
  &.active {
    border-color: var(--primary);
    background: var(--primary-light);
    .file-name { color: var(--primary); }
  }
}

.file-icon { font-size: 1.1em; flex-shrink: 0; }
.file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-primary); }
.file-size { font-size: var(--text-xs); color: var(--text-tertiary); white-space: nowrap; }

// ====== 统计卡片覆盖 ======
.stat-item {
  padding: var(--space-4) var(--space-5);

  .stat-icon-wrap {
    width: 32px;
    height: 32px;
    margin-bottom: var(--space-2);
  }

  .stat-value {
    font-size: var(--text-xl);
  }
}

.stat-grid {
  margin-bottom: 0;
}

.preview-info {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

// ====== 数据预览 ======
.col-stats {
  margin-bottom: var(--space-3);
}

.section-label {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.stat-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.stat-chip {
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  padding: 6px 12px;
  font-size: var(--text-xs);

  strong {
    color: var(--text-primary);
    margin-right: 8px;
  }

  .chip-vals {
    color: var(--text-tertiary);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
  }
}

.data-table-wrap {
  max-height: 360px;
  overflow: auto;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-xs);
  th {
    position: sticky;
    top: 0;
    background: var(--bg-secondary);
    padding: 10px 12px;
    text-align: left;
    font-weight: var(--weight-semibold);
    border-bottom: 2px solid var(--border-light);
    white-space: nowrap;
    z-index: 1;
  }
  td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-light);
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  tbody tr:hover td {
    background: var(--bg-primary);
  }
  td.type-number { text-align: right; font-family: var(--font-mono); }
  td.row-num { color: var(--text-tertiary); font-size: var(--text-xs); text-align: center; width: 36px; }
}

.col-type-badge {
  font-size: 10px;
  color: var(--text-tertiary);
  margin-left: 4px;
  background: var(--bg-primary);
  padding: 1px 5px;
  border-radius: var(--radius-sm);
  font-weight: var(--weight-normal);
}

// ====== 数据清洗 ======
.clean-section {
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-light);
}

.clean-controls {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  align-items: center;
}

.clean-result {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--success);
  font-weight: var(--weight-medium);
}

// ====== 可视化 ======
.chart-type-grid {
  display: flex;
  gap: 6px;
  width: 100%;
}

.chart-type-btn {
  flex: 1;
  padding: 8px 4px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  cursor: pointer;
  font-size: 1.2em;
  transition: all var(--duration-fast) var(--ease-out);
  text-align: center;

  &:hover {
    border-color: var(--primary);
  }

  &.active {
    border-color: var(--primary);
    background: var(--primary-light);
    box-shadow: 0 0 0 2px var(--primary-light);
  }
}

.color-scheme-row {
  display: flex;
  gap: var(--space-2);
}

.color-scheme-btn {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);

  &:hover { border-color: var(--primary); }
  &.active { border-color: var(--primary); background: var(--primary-light); }
}

.color-dots {
  display: flex;
  gap: 3px;
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.chart-container {
  width: 100%;
  height: 420px;
}

.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
  text-align: center;

  p {
    margin-top: var(--space-3);
    font-size: var(--text-sm);
  }
}

.chart-empty-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-1);
}

// ====== 建模画布 ======
.canvas-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 10px 14px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-3);
}

.canvas-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-left: auto;
}

.canvas-area {
  position: relative;
  width: 100%;
  height: 520px;
  background:
    linear-gradient(90deg, var(--border-light) 1px, transparent 1px),
    linear-gradient(0deg, var(--border-light) 1px, transparent 1px);
  background-size: 30px 30px;
  background-position: center center;
  border: 2px solid var(--border-light);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.canvas-svg {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 1;
}

.canvas-node {
  position: absolute;
  width: 180px;
  background: var(--bg-card);
  border: 2px solid #165DFF;
  border-radius: var(--radius-lg);
  cursor: move;
  z-index: 2;
  user-select: none;
  box-shadow: var(--glow-card);
  transition: box-shadow 0.15s, transform 0.15s;

  &:hover {
    box-shadow: var(--glow-elevated);
    transform: translateY(-1px);
  }

  &.selected { box-shadow: 0 0 0 3px rgba(22,93,255,0.3); }
  &.connecting { box-shadow: 0 0 0 3px rgba(255,125,0,0.4); }
}

.cn-header {
  padding: 8px 12px;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  border-radius: 6px 6px 0 0;
  border-bottom: 1px solid var(--border-light);
}

.cn-body {
  padding: 8px 12px 10px;
}

.cn-input {
  width: 100%;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 5px 8px;
  font-size: var(--text-xs);
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-family: var(--font-body);
  transition: border-color var(--duration-fast) var(--ease-out);

  &:focus { border-color: var(--primary); }

  &.cn-detail {
    margin-top: 6px;
    font-size: var(--text-xs);
    color: var(--text-secondary);
  }
}

.cn-delete {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 20px;
  height: 20px;
  border: none;
  background: var(--danger);
  color: white;
  border-radius: 50%;
  font-size: var(--text-xs);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s;

  .canvas-node:hover & { opacity: 1; }
}

.canvas-legend {
  display: flex;
  gap: var(--space-4);
  padding: 8px 12px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

// ====== 论文编辑器 ======
.paper-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-5);
  height: calc(100vh - 300px);
  min-height: 550px;
}

.paper-editor-card, .paper-preview-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.paper-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.paper-stats {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-right: auto;
}

.editor-body, .preview-body {
  flex: 1;
  overflow: hidden;
  padding: 0 !important;
  display: flex;
  flex-direction: column;
}

.md-editor {
  width: 100%;
  flex: 1;
  border: none;
  resize: none;
  padding: 16px 20px;
  font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-primary);
  background: var(--bg-primary);
  outline: none;
  tab-size: 4;

  &::placeholder { color: var(--text-tertiary); }
}

.preview-body {
  overflow-y: auto;
  padding: 16px 20px !important;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
  text-align: center;
  height: 100%;

  p {
    margin-top: var(--space-3);
    font-size: var(--text-sm);
  }

  span {
    font-size: var(--text-xs);
    color: var(--text-tertiary);
    margin-top: var(--space-1);
  }
}

.md-preview {
  font-size: var(--text-sm);
  line-height: 1.9;
  color: var(--text-primary);

  :deep(h1) { font-size: var(--text-xl); border-bottom: 2px solid var(--border-light); padding-bottom: 8px; margin: 20px 0 14px; font-weight: var(--weight-semibold); }
  :deep(h2) { font-size: var(--text-lg); border-bottom: 1px solid var(--border-light); padding-bottom: 6px; margin: 18px 0 12px; font-weight: var(--weight-semibold); }
  :deep(h3) { font-size: var(--text-md); margin: 16px 0 10px; font-weight: var(--weight-semibold); }
  :deep(p) { margin-bottom: var(--space-3); }
  :deep(ul), :deep(ol) { margin: var(--space-2) 0; padding-left: var(--space-6); }
  :deep(li) { margin-bottom: var(--space-1); }
  :deep(code) { background: var(--bg-primary); padding: 2px 6px; border-radius: var(--radius-sm); font-size: 13px; font-family: var(--font-mono); }
  :deep(pre) { background: #1e1e2e; border-radius: var(--radius-lg); padding: var(--space-4); overflow-x: auto; margin: var(--space-3) 0;
    code { background: transparent; padding: 0; color: #cdd6f4; } }
  :deep(table) { border-collapse: collapse; width: 100%; margin: var(--space-3) 0; }
  :deep(th), :deep(td) { border: 1px solid var(--border-light); padding: 6px 12px; text-align: left; font-size: var(--text-xs); }
  :deep(th) { background: var(--bg-primary); font-weight: var(--weight-semibold); }
  :deep(blockquote) { border-left: 4px solid var(--primary); padding: var(--space-2) var(--space-4); margin: var(--space-3) 0; background: var(--primary-light); border-radius: 0 var(--radius-md) var(--radius-md) 0; color: var(--text-secondary); }
  :deep(strong) { font-weight: var(--weight-semibold); color: var(--text-primary); }
  :deep(hr) { border: none; height: 1px; background: var(--border-light); margin: var(--space-5) 0; }
}

// ====== 响应式 ======
@media (max-width: 1200px) {
  .demo-grid { grid-template-columns: repeat(2, 1fr); }
  .paper-layout { grid-template-columns: 1fr; height: auto; min-height: auto; }
  .paper-editor-card, .paper-preview-card { height: 400px; }
}

@media (max-width: 768px) {
  .ws-grid { grid-template-columns: 1fr; }
  .demo-grid { grid-template-columns: 1fr; }
  .ws-tabs { flex-wrap: wrap; }
  .ws-tab-btn { flex: 0 0 auto; font-size: var(--text-xs); padding: 8px 12px;
    .tab-label { display: none; }
  }
  .canvas-hint { display: none; }
  .paper-layout { grid-template-columns: 1fr; }
}
</style>
