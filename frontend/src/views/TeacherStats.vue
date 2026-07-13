<template>
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <div class="page-container">
        <div class="app-breadcrumb">
          <el-icon><HomeFilled /></el-icon><span>首页</span>
          <el-icon><ArrowRight /></el-icon><span>教学管理</span>
          <el-icon><ArrowRight /></el-icon><span class="current">教学数据统计</span>
        </div>

        <div class="page-header-area">
          <div class="page-title-row">
            <div>
              <h1 class="page-title">教学数据统计</h1>
              <p class="page-subtitle">数学建模实验数据总览，仅教师和管理员可见</p>
            </div>
          </div>
        </div>

        <!-- 统计卡片 -->
        <div class="stat-card-grid" v-if="!loading">
          <div class="stat-card experiments">
            <div class="stat-card-top">
              <div class="stat-card-icon"><el-icon :size="22"><User /></el-icon></div>
            </div>
            <div class="stat-card-value">{{ stats.total_students }}</div>
            <div class="stat-card-label">学生总数</div>
          </div>
          <div class="stat-card practices">
            <div class="stat-card-top">
              <div class="stat-card-icon"><el-icon :size="22"><Tickets /></el-icon></div>
            </div>
            <div class="stat-card-value">{{ stats.total_records }}</div>
            <div class="stat-card-label">实训记录</div>
          </div>
          <div class="stat-card score">
            <div class="stat-card-top">
              <div class="stat-card-icon"><el-icon :size="22"><TrendCharts /></el-icon></div>
            </div>
            <div class="stat-card-value">{{ stats.average_score }}</div>
            <div class="stat-card-label">平均分</div>
          </div>
          <div class="stat-card chats">
            <div class="stat-card-top">
              <div class="stat-card-icon"><el-icon :size="22"><Medal /></el-icon></div>
            </div>
            <div class="stat-card-value">{{ topCount }}</div>
            <div class="stat-card-label">优秀学生</div>
          </div>
        </div>

        <div v-else class="stat-card-grid">
          <div v-for="i in 4" :key="i" class="skeleton-card"><div class="skeleton-line w40"></div><div class="skeleton-line h48 w60" style="margin-top:12px;"></div></div>
        </div>

        <el-row :gutter="20" style="margin-bottom:20px;">
          <el-col :span="12">
            <div class="app-card">
              <div class="app-card-header"><span class="app-card-title">各模型分类实验分布</span></div>
              <div class="app-card-body">
                <div v-if="stats.subject_distribution?.length" class="chart-list">
                  <div v-for="item in stats.subject_distribution" :key="item.subject" class="bar-row">
                    <span class="bar-label">{{ item.subject }}</span>
                    <div class="bar-track"><div class="bar-fill" :style="{ width: barWidth(item.count), background: barColor(item.subject) }"></div></div>
                    <span class="bar-value">{{ item.count }}</span>
                  </div>
                </div>
                <div v-else class="app-empty" style="padding:30px;"><p class="app-empty-text">暂无数据</p></div>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="app-card">
              <div class="app-card-header"><span class="app-card-title">分数段分布</span></div>
              <div class="app-card-body">
                <div v-if="stats.score_distribution?.length" class="chart-list">
                  <div v-for="item in stats.score_distribution" :key="item.range" class="bar-row">
                    <span class="bar-label">{{ item.range }}</span>
                    <div class="bar-track"><div class="bar-fill" :style="{ width: scoreBarWidth(item.count), background: scoreBarColor(item.range) }"></div></div>
                    <span class="bar-value">{{ item.count }}</span>
                  </div>
                </div>
                <div v-else class="app-empty" style="padding:30px;"><p class="app-empty-text">暂无数据</p></div>
              </div>
            </div>
          </el-col>
        </el-row>

        <div class="app-card">
          <div class="app-card-header"><span class="app-card-title">优秀学生排行</span></div>
          <div class="app-card-body" style="padding-top:16px;">
            <table class="app-table" v-if="stats.top_students?.length">
              <thead><tr><th>排名</th><th>姓名</th><th>班级</th><th>平均分</th><th>完成次数</th></tr></thead>
              <tbody>
                <tr v-for="(row, idx) in stats.top_students" :key="idx">
                  <td style="font-weight:600;">{{ idx + 1 }}</td>
                  <td>{{ row.name }}</td>
                  <td>{{ row.class_name || '-' }}</td>
                  <td><span style="font-weight:600;color:scoreColor(row.avg_score);">{{ row.avg_score }}</span></td>
                  <td>{{ row.total_practices }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="app-empty" style="padding:30px;"><p class="app-empty-text">暂无排行数据</p></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { teacherApi } from '../api'
import Sidebar from '../components/Sidebar.vue'
import { User, Tickets, TrendCharts, Medal, HomeFilled, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter(); const userStore = useUserStore()
const loading = ref(true)
const stats = ref({ total_students:0, total_records:0, average_score:0, subject_distribution:[], score_distribution:[], top_students:[] })
const topCount = computed(() => stats.value.top_students?.length || 0)

function scoreColor(s) { if (s >= 90) return 'var(--success)'; if (s >= 75) return 'var(--primary)'; if (s >= 60) return 'var(--warning)'; return 'var(--danger)' }
function barColor(s) { const m={'优化模型':'var(--primary)','预测模型':'var(--success)','评价模型':'var(--warning)','分类与聚类':'var(--info)','微分方程':'var(--danger)','统计模型':'var(--primary)','图论与网络':'var(--success)','随机模型':'var(--warning)'}; return m[s] || 'var(--info)' }
function barWidth(c) { const max = Math.max(...(stats.value.subject_distribution?.map(i => i.count) || [1])); return Math.max((c/max)*100,5)+'%' }
function scoreBarWidth(c) { const max = Math.max(...(stats.value.score_distribution?.map(i => i.count) || [1])); return Math.max((c/max)*100,5)+'%' }
function scoreBarColor(r) { if (r.startsWith('90')) return 'var(--success)'; if (r.startsWith('80')) return 'var(--primary)'; if (r.startsWith('70')) return 'var(--warning)'; if (r.startsWith('60')) return '#FF9500'; return 'var(--danger)' }

onMounted(async () => {
  try { stats.value = await teacherApi.getStats() } catch (err) { /* ignore */ }
  finally { loading.value = false }
})
</script>

<style scoped>
.chart-list { padding:4px 0; }
.bar-row { display:flex; align-items:center; margin-bottom:12px; gap:10px; }
.bar-label { width:80px; font-size: var(--text-sm); color:var(--text-secondary); text-align:right; flex-shrink:0; }
.bar-track { flex:1; height:22px; background:var(--bg-primary); border-radius:11px; overflow:hidden; }
.bar-fill { height:100%; border-radius:11px; transition:width 0.8s ease; min-width:4px; }
.bar-value { width:36px; font-size: var(--text-sm); color:var(--text-primary); font-weight:600; }
</style>
