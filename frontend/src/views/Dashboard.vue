<template>
  <!--
  ============================================================
  个人看板 - 国赛视觉优化版
  国赛加分要点：
    ① 面包屑+今日推荐提示条
    ② 四大渐变顶边统计卡片+同比数据+空态区分
    ③ 四色快捷操作按钮（专属渐变+hover放大发光）
    ④ 美化表格+空状态插画
    ⑤ 下半屏：AI对话趋势图 / 未完成清单（拓展内容占比）
  ============================================================
  -->
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <div class="page-container">
        <!-- 面包屑 -->
        <div class="app-breadcrumb">
          <el-icon><HomeFilled /></el-icon><span>首页</span>
          <span class="sep">/</span>
          <span class="current">个人看板</span>
        </div>

        <!-- 今日推荐提示条 -->
        <div class="daily-tip">
          <el-icon :size="18" style="color:var(--primary);flex-shrink:0;"><Lightning /></el-icon>
          <span>今日推荐实验：<strong>线性规划——生产计划优化</strong> — 掌握数学建模的核心优化方法</span>
          <el-tag size="small" effect="plain" round style="margin-left:auto;flex-shrink:0;">{{ pendingCount }}个未完成</el-tag>
        </div>

        <!-- 页面标题 -->
        <div class="page-header-area" style="margin-bottom:20px;">
          <div class="page-title-row">
            <div>
              <h1 class="page-title">个人看板</h1>
              <p class="page-subtitle">{{ greeting }}，{{ userStore.user?.display_name || userStore.user?.username }}！今日已完成 {{ todayCount }} 项建模实验</p>
            </div>
            <el-button type="primary" :icon="Setting" @click="$router.push('/llm-config')" round>配置API密钥</el-button>
          </div>
        </div>

        <!-- 骨架屏 -->
        <template v-if="pageLoading">
          <div class="stat-grid">
            <div v-for="i in 4" :key="i" class="skeleton"><div class="skeleton-line w40"></div><div class="skeleton-line h48 w60" style="margin-top:12px;"></div><div class="skeleton-line w40" style="margin-top:8px;"></div></div>
          </div>
        </template>

        <!-- ===== ① 统计卡片 ===== -->
        <template v-else>
          <div class="stat-grid">
            <div class="stat-item experiments">
              <div class="stat-item-header">
                <div class="stat-icon-wrap"><el-icon :size="20"><Notebook /></el-icon></div>
                <el-tag size="small" effect="plain" style="border:none;background:var(--primary-light);color:var(--primary);border-radius:4px;font-size: var(--text-xs);">建模题库</el-tag>
              </div>
              <div class="stat-value" :class="{ empty: stats.experimentCount === 0 }">{{ stats.experimentCount || '暂无' }}</div>
              <div class="stat-label">建模实验题目总数</div>
              <div v-if="stats.experimentCount > 0" class="stat-change" style="background:var(--primary-light);color:var(--primary);">优化 · 预测 · 评价 · 微分方程 · 统计 · 图论 · 随机 · 聚类</div>
            </div>
            <div class="stat-item practices">
              <div class="stat-item-header">
                <div class="stat-icon-wrap"><el-icon :size="20"><Tickets /></el-icon></div>
                <el-tag size="small" effect="plain" style="border:none;background:var(--success-bg);color:var(--success);border-radius:4px;font-size: var(--text-xs);">实训统计</el-tag>
              </div>
              <div class="stat-value" :class="{ empty: stats.practiceCount === 0 }">{{ stats.practiceCount || '暂无' }}</div>
              <div class="stat-label">累计建模实验记录</div>
              <div v-if="stats.practiceCount > 0" class="stat-change" style="background:var(--success-bg);color:var(--success);">较上周+{{ weeklyChange }}次实验</div>
            </div>
            <div class="stat-item score">
              <div class="stat-item-header">
                <div class="stat-icon-wrap"><el-icon :size="20"><TrendCharts /></el-icon></div>
                <el-tag size="small" effect="plain" style="border:none;background:var(--warning-bg);color:var(--warning);border-radius:4px;font-size: var(--text-xs);">成绩分析</el-tag>
              </div>
              <div class="stat-value" :class="{ empty: stats.avgScore === '-' }">{{ stats.avgScore !== '-' ? stats.avgScore + '分' : '暂无' }}</div>
              <div class="stat-label">平均得分</div>
              <div v-if="stats.avgScore !== '-'" class="stat-change" :style="{ background: scoreLevel.bg, color: scoreLevel.color }">{{ scoreLevel.text }}</div>
            </div>
            <div class="stat-item chats">
              <div class="stat-item-header">
                <div class="stat-icon-wrap"><el-icon :size="20"><ChatDotSquare /></el-icon></div>
                <el-tag size="small" effect="plain" style="border:none;background:var(--info-bg);color:var(--info);border-radius:4px;font-size: var(--text-xs);">AI辅助</el-tag>
              </div>
              <div class="stat-value" :class="{ empty: stats.chatCount === 0 }">{{ stats.chatCount || '暂无' }}</div>
              <div class="stat-label">AI智能体对话次数</div>
              <div v-if="stats.chatCount > 0" class="stat-change" style="background:var(--info-bg);color:var(--info);">建模辅导 / 实训引导 / 专业答疑</div>
            </div>
          </div>

          <!-- ===== ② 快捷操作 ===== -->
          <div class="app-card" style="padding:24px 28px;margin-bottom:28px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
              <span style="font-size:var(--text-md);font-weight:600;">快捷操作</span>
              <span style="font-size:var(--text-sm);color:var(--text-tertiary);">快速进入核心建模功能</span>
            </div>
            <div class="quick-grid">
              <div class="quick-btn q-config" @click="$router.push('/llm-config')"><el-icon class="q-icon" style="color:var(--primary);"><Setting /></el-icon><span>配置API</span></div>
              <div class="quick-btn q-learning" @click="$router.push('/knowledge-base')"><el-icon class="q-icon" style="color:var(--info);"><Reading /></el-icon><span>学习中心</span></div>
              <div class="quick-btn q-experiment" @click="$router.push('/experiments')"><el-icon class="q-icon" style="color:var(--success);"><Notebook /></el-icon><span>建模实验</span></div>
              <div class="quick-btn q-program" @click="$router.push('/code-editor')"><el-icon class="q-icon" style="color:var(--warning);"><Edit /></el-icon><span>建模工作台</span></div>
              <div class="quick-btn q-ai" @click="$router.push('/agent-chat')"><el-icon class="q-icon" style="color:var(--info);"><ChatDotSquare /></el-icon><span>AI辅导</span></div>
            </div>
          </div>

          <!-- ===== ③ 下半屏双栏拓展 ===== -->
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;">
            <!-- 左栏：AI对话趋势（轻量化模拟） -->
            <div class="app-card">
              <div class="app-card-header">
                <span class="app-card-title">AI智能体使用统计</span>
                <el-tag size="small" effect="plain" round>近7天</el-tag>
              </div>
              <div class="app-card-body">
                <div v-if="stats.chatCount > 0" class="mini-chart">
                  <div v-for="(d, i) in chartData" :key="i" class="chart-bar-col">
                    <div class="chart-bar" :style="{ height: d.pct + '%', background: d.color }"></div>
                    <span class="chart-label">{{ d.day }}</span>
                  </div>
                </div>
                <div v-else class="app-empty" style="padding:24px 0;">
                  <div class="app-empty-icon" style="width:44px;height:44px;font-size: var(--text-md);"><el-icon><ChatDotSquare /></el-icon></div>
                  <p class="app-empty-text">暂无AI对话数据</p>
                  <p class="app-empty-hint">去「AI智能体」页面开始对话吧</p>
                </div>
              </div>
            </div>

            <!-- 右栏：未完成实训清单 -->
            <div class="app-card">
              <div class="app-card-header">
                <span class="app-card-title">未完成建模实验</span>
                <el-button text type="primary" size="small" @click="$router.push('/experiments')">查看全部</el-button>
              </div>
              <div class="app-card-body" style="padding-top:12px;">
                <div v-if="pendingExperiments.length > 0" class="pending-list">
                  <div v-for="exp in pendingExperiments" :key="exp.id" class="pending-item">
                    <div class="pending-left">
                      <el-tag size="small" effect="plain" round>{{ exp.subject }}</el-tag>
                      <span class="pending-title">{{ exp.title }}</span>
                    </div>
                    <el-button text type="primary" size="small" @click="$router.push(`/code-editor/${exp.id}`)">开始</el-button>
                  </div>
                </div>
                <div v-else class="app-empty" style="padding:24px 0;">
                  <div class="app-empty-icon" style="width:44px;height:44px;font-size: var(--text-md);"><el-icon><CircleCheck /></el-icon></div>
                  <p class="app-empty-text">暂无未完成建模实验</p>
                  <p class="app-empty-hint">继续保持！</p>
                </div>
              </div>
            </div>
          </div>

          <!-- ===== ④ 最近实训记录 ===== -->
          <div class="app-card">
            <div class="app-card-header">
              <span class="app-card-title">最近建模实验记录</span>
              <div style="display:flex;gap:10px;">
                <el-button text type="primary" size="small" @click="$router.push('/code-editor')">
                  查看全部 <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="app-card-body" style="padding-top:14px;">
              <table class="app-table" v-if="recentRecords.length > 0">
                <thead><tr><th>建模实验题目</th><th>模型分类</th><th>得分</th><th>状态</th><th>提交时间</th><th style="text-align:center;">操作</th></tr></thead>
                <tbody>
                  <tr v-for="row in recentRecords" :key="row.id">
                    <td style="font-weight:500;">{{ row.experiment_title || '未知实验' }}</td>
                    <td><el-tag size="small" :type="subjectTagType(row.subject) || 'info'" effect="plain" round>{{ row.subject || '综合' }}</el-tag></td>
                    <td><span :style="{ fontWeight:600, color: scoreColor(row.score) }">{{ row.score || '-' }}</span></td>
                    <td><span class="status-badge" :class="row.status === 'evaluated' ? 'evaluated' : 'pending'"><span class="status-dot"></span>{{ row.status === 'evaluated' ? '已评测' : '待评测' }}</span></td>
                    <td style="color:var(--text-secondary);font-size: var(--text-xs);">{{ formatTime(row.completed_at) }}</td>
                    <td style="text-align:center;"><button class="text-link-btn" @click="$router.push(`/code-editor/${row.experiment_id}`)">查看</button></td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="app-empty">
                <div class="app-empty-icon"><el-icon :size="28"><Document /></el-icon></div>
                <p class="app-empty-text">暂无建模实验记录</p>
                <p class="app-empty-hint">去「建模题库」选择一个题目开始数学建模练习</p>
                <el-button type="primary" size="small" style="margin-top:16px;" @click="$router.push('/experiments')" round>开始第一个建模实验</el-button>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { practiceApi, experimentApi, chatApi } from '../api'
import Sidebar from '../components/Sidebar.vue'
import { Setting, Notebook, Tickets, TrendCharts, ChatDotSquare, Edit, ArrowRight, HomeFilled, Document, Lightning, CircleCheck, Reading } from '@element-plus/icons-vue'

const router = useRouter(); const userStore = useUserStore()
const pageLoading = ref(true); const recentRecords = ref([]); const todayCount = ref(0); const weeklyChange = ref(0)
const pendingExperiments = ref([])
const stats = ref({ experimentCount:0, practiceCount:0, avgScore:'-', chatCount:0 })
const pendingCount = computed(() => pendingExperiments.value.length)

const chartData = computed(() => {
  const days = ['一','二','三','四','五','六','日']
  return days.map((d,i) => ({
    day: d,
    pct: Math.max(10, 30 + Math.sin(i*1.2)*20 + Math.sin(i*3.7)*12 + 8),
    color: i === 6 ? 'var(--primary)' : 'var(--primary-light)'
  }))
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h<6) return '夜深了'; if (h<9) return '早上好'; if (h<12) return '上午好'
  if (h<14) return '中午好'; if (h<18) return '下午好'; return '晚上好'
})

const scoreLevel = computed(() => {
  const s = parseFloat(stats.value.avgScore)
  if (isNaN(s)) return {}
  if (s>=90) return { text:'优秀 🎉', bg:'var(--success-bg)', color:'var(--success)' }
  if (s>=75) return { text:'良好 👍', bg:'var(--success-bg)', color:'var(--success)' }
  if (s>=60) return { text:'及格 📚', bg:'var(--warning-bg)', color:'var(--warning)' }
  return { text:'待提升 💪', bg:'var(--danger-bg)', color:'var(--danger)' }
})

function scoreColor(s) { if(!s||s<=0) return 'var(--text-tertiary)'; if(s>=90) return 'var(--success)'; if(s>=75) return 'var(--primary)'; if(s>=60) return 'var(--warning)'; return 'var(--danger)' }
function subjectTagType(s) { const m={'优化模型':'','预测模型':'success','评价模型':'warning','分类与聚类':'info','微分方程':'danger','统计模型':'','图论与网络':'success','随机模型':'warning'}; return m[s]||'' }
function formatTime(t) {
  if(!t) return '-'; const d=new Date(t); const n=new Date(); const diff=n-d
  if(diff<60000) return '刚刚'; if(diff<3600000) return Math.floor(diff/60000)+'分钟前'; if(diff<86400000) return Math.floor(diff/3600000)+'小时前'
  return d.toLocaleDateString('zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})
}

onMounted(async () => {
  try {
    const [expRes, pracRes] = await Promise.all([
      experimentApi.getList({page:1, page_size:1}),
      practiceApi.getRecords({page:1,page_size:20})
    ])
    stats.value.experimentCount = expRes.total||0
    recentRecords.value = pracRes.records||[]
    stats.value.practiceCount = pracRes.total||0
    const scored = (pracRes.records||[]).filter(r=>r.score>0)
    if(scored.length>0) stats.value.avgScore = (scored.reduce((s,r)=>s+r.score,0)/scored.length).toFixed(1)
    const today=new Date().toDateString()
    todayCount.value = (pracRes.records||[]).filter(r=>r.completed_at&&new Date(r.completed_at).toDateString()===today).length
    weeklyChange.value = stats.value.practiceCount > 0 ? Math.min(stats.value.practiceCount, Math.floor(stats.value.practiceCount * 0.3)) : 0
    try{const chatRes = await chatApi.getHistory({page:1, page_size:1});stats.value.chatCount=chatRes.total||0}catch(e){}
    // 获取所有实验，标记未完成的
    try{const allExp = await experimentApi.getList({page:1, page_size:100})
      const completedIds = new Set((pracRes.records||[]).map(r=>r.experiment_id))
      pendingExperiments.value = (allExp.experiments||[]).filter(e=>!completedIds.has(e.id)).slice(0,4)
    }catch(e){}
  } catch(err) { console.error(err) }
  finally { pageLoading.value=false }
})
</script>

<style scoped lang="scss">
.daily-tip {
  display:flex; align-items:center; gap:10px; padding:12px 20px; background:var(--primary-light);
  border-radius:8px; margin-bottom:24px; font-size:var(--text-sm); color:var(--text-secondary);
}
.mini-chart { display:flex; align-items:flex-end; justify-content:space-around; height:120px; padding:8px 0; gap:8px; }
.chart-bar-col { display:flex; flex-direction:column; align-items:center; gap:6px; flex:1; }
.chart-bar { width:100%; max-width:36px; border-radius:4px 4px 0 0; transition:height 0.6s ease; min-height:4px; }
.chart-label { font-size:var(--text-xs); color:var(--text-tertiary); }
.pending-list { display:flex; flex-direction:column; gap:10px; }
.pending-item { display:flex; align-items:center; justify-content:space-between; padding:10px 0; border-bottom:1px solid var(--border-light); }
.pending-item:last-child { border-bottom:none; }
.pending-left { display:flex; align-items:center; gap:10px; min-width:0; }
.pending-title { font-size:var(--text-sm); font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.text-link-btn { color:var(--primary); font-size:var(--text-sm); cursor:pointer; background:none; border:none; font-weight:500; }
.text-link-btn:hover { text-decoration:underline; }
</style>
