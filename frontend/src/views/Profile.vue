<template>
  <!--
  ============================================================
  个人中心 — 资料 + 密码 + 学习记录 + 论文管理 + 统计
  PRF-001/002/003/004
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
          <span class="current">个人中心</span>
        </div>

        <!-- 页面标题 -->
        <div class="page-header-area" style="margin-bottom:20px;">
          <div class="page-title-row">
            <div>
              <h1 class="page-title">个人中心</h1>
              <p class="page-subtitle">管理您的个人资料与账户安全</p>
            </div>
          </div>
        </div>

        <!-- 主体双栏 -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">

          <!-- ===== 左栏：个人资料卡片 ===== -->
          <div class="app-card">
            <div class="app-card-header">
              <span class="app-card-title">
                <el-icon :size="16" style="margin-right:4px;"><User /></el-icon>个人资料
              </span>
            </div>
            <div class="app-card-body">
              <el-form
                ref="profileFormRef"
                :model="profileForm"
                :rules="profileRules"
                label-width="80px"
                label-position="left"
                @submit.prevent
              >
                <!-- 用户名（只读） -->
                <el-form-item label="用户名">
                  <el-input :model-value="userStore.user?.username" disabled>
                    <template #prefix>
                      <el-icon><Avatar /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <!-- 角色（只读） -->
                <el-form-item label="角色">
                  <el-tag
                    :type="roleTagType"
                    effect="plain"
                    round
                    size="large"
                    style="text-transform:capitalize;"
                  >
                    {{ roleLabel }}
                  </el-tag>
                </el-form-item>

                <!-- 昵称 -->
                <el-form-item label="昵称" prop="display_name">
                  <el-input
                    v-model="profileForm.display_name"
                    placeholder="设置一个昵称，方便同学识别"
                    maxlength="50"
                    show-word-limit
                  >
                    <template #prefix>
                      <el-icon><Edit /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <!-- 班级 -->
                <el-form-item label="班级" prop="class_name">
                  <el-input
                    v-model="profileForm.class_name"
                    placeholder="如：数学2024级1班"
                    maxlength="50"
                    show-word-limit
                  >
                    <template #prefix>
                      <el-icon><School /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <!-- 注册时间（只读） -->
                <el-form-item label="注册时间">
                  <el-input
                    :model-value="formatDate(userStore.user?.created_at)"
                    disabled
                  >
                    <template #prefix>
                      <el-icon><Clock /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item>
                  <el-button
                    type="primary"
                    :loading="profileSaving"
                    @click="saveProfile"
                    round
                  >
                    <el-icon><Check /></el-icon> 保存资料
                  </el-button>
                  <el-button @click="resetProfile" round :disabled="profileSaving">
                    重置
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>

          <!-- ===== 右栏：密码修改卡片 ===== -->
          <div class="app-card">
            <div class="app-card-header">
              <span class="app-card-title">
                <el-icon :size="16" style="margin-right:4px;"><Lock /></el-icon>修改密码
              </span>
            </div>
            <div class="app-card-body">
              <el-form
                ref="passwordFormRef"
                :model="passwordForm"
                :rules="passwordRules"
                label-width="80px"
                label-position="left"
                @submit.prevent
              >
                <el-form-item label="原密码" prop="old_password">
                  <el-input
                    v-model="passwordForm.old_password"
                    type="password"
                    placeholder="请输入当前密码"
                    show-password
                  >
                    <template #prefix>
                      <el-icon><Lock /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item label="新密码" prop="new_password">
                  <el-input
                    v-model="passwordForm.new_password"
                    type="password"
                    placeholder="8位以上，含数字+字母"
                    show-password
                  >
                    <template #prefix>
                      <el-icon><Key /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item label="确认密码" prop="confirm_password">
                  <el-input
                    v-model="passwordForm.confirm_password"
                    type="password"
                    placeholder="再次输入新密码"
                    show-password
                  >
                    <template #prefix>
                      <el-icon><CircleCheck /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <!-- 密码强度指示 -->
                <el-form-item label="密码强度" v-if="passwordForm.new_password">
                  <div class="pwd-strength">
                    <div class="strength-bars">
                      <span
                        v-for="i in 3"
                        :key="i"
                        class="strength-seg"
                        :class="{ active: i <= pwdStrength, [strengthClass]: i <= pwdStrength }"
                      ></span>
                    </div>
                    <span class="strength-text" :style="{ color: strengthColor }">
                      {{ strengthLabel }}
                    </span>
                  </div>
                </el-form-item>

                <el-form-item>
                  <el-button
                    type="primary"
                    :loading="passwordSaving"
                    @click="changePassword"
                    round
                  >
                    <el-icon><Check /></el-icon> 修改密码
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>

        </div>

        <!-- ===== 个人中心标签页 (PRF-001~004) ===== -->
        <el-tabs v-model="centerTab" type="border-card" style="margin-top:20px;">
          <!-- Tab 1: 学习记录 -->
          <el-tab-pane label="📋 学习记录" name="records">
            <div style="display:flex;gap:8px;margin-bottom:12px;">
              <el-radio-group v-model="recordFilter" size="small" @change="loadRecords">
                <el-radio-button value="all">全部</el-radio-button>
                <el-radio-button value="chat">AI对话</el-radio-button>
                <el-radio-button value="practice">练习记录</el-radio-button>
              </el-radio-group>
            </div>
            <div v-if="records.length > 0" class="record-list">
              <div v-for="r in records" :key="r.id" class="record-item">
                <div style="display:flex;align-items:center;gap:8px;">
                  <el-tag :type="r.type === 'chat' ? 'primary' : 'success'" size="small" effect="plain" round>
                    {{ r.type === 'chat' ? '对话' : '练习' }}
                  </el-tag>
                  <span style="font-weight:600;font-size: var(--text-sm);">{{ r.title }}</span>
                </div>
                <div style="font-size: var(--text-xs);color:var(--text-secondary);margin-top:4px;">{{ r.detail }}</div>
                <div style="font-size: var(--text-xs);color:var(--text-tertiary);margin-top:2px;">{{ r.created_at?.slice(0, 16) }}</div>
              </div>
            </div>
            <div v-else style="text-align:center;padding:40px;color:var(--text-tertiary);">暂无记录</div>
          </el-tab-pane>

          <!-- Tab 2: 论文管理 -->
          <el-tab-pane label="📝 论文管理" name="papers">
            <div v-if="papers.length > 0" style="display:flex;flex-direction:column;gap:8px;">
              <div v-for="p in papers" :key="p.id" class="paper-item">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                  <div>
                    <span style="font-weight:600;font-size: var(--text-sm);">{{ p.title }}</span>
                    <el-tag :type="p.status === 's7_check_passed' ? 'success' : 'warning'" size="small" effect="plain" round style="margin-left:8px;">
                      {{ p.current_step }}
                    </el-tag>
                  </div>
                  <div style="display:flex;gap:6px;">
                    <el-button v-if="p.has_paper" size="small" @click="downloadCompetitionPaper(p.id)" round>
                      下载论文
                    </el-button>
                    <el-button size="small" @click="$router.push('/competition')" round>
                      打开任务
                    </el-button>
                  </div>
                </div>
                <div style="font-size: var(--text-xs);color:var(--text-tertiary);margin-top:4px;">
                  更新于 {{ p.updated_at?.slice(0, 16) }}
                </div>
              </div>
            </div>
            <div v-else style="text-align:center;padding:40px;color:var(--text-tertiary);">
              暂无竞赛论文 — <el-button text type="primary" @click="$router.push('/competition')">去竞赛</el-button>
            </div>
          </el-tab-pane>

          <!-- Tab 3: 收藏书签 -->
          <el-tab-pane label="⭐ 收藏书签" name="bookmarks">
            <div v-if="bookmarks.length > 0" style="display:flex;flex-direction:column;gap:8px;">
              <div v-for="(bm, i) in bookmarks" :key="i" class="bookmark-item">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                  <div>
                    <span style="font-weight:600;font-size: var(--text-sm);">{{ bm.title }}</span>
                    <el-tag size="small" effect="plain" round style="margin-left:8px;">{{ bm.type }}</el-tag>
                  </div>
                  <el-button text type="danger" size="small" :icon="Delete" @click="removeBookmark(i)" />
                </div>
                <div style="font-size: var(--text-xs);color:var(--text-secondary);margin-top:2px;">{{ bm.desc }}</div>
              </div>
            </div>
            <div v-else style="text-align:center;padding:40px;color:var(--text-tertiary);">
              <el-icon :size="32"><Star /></el-icon>
              <p style="margin-top:8px;">暂无收藏 — 在知识库中点击 ⭐ 收藏内容</p>
            </div>
          </el-tab-pane>

          <!-- Tab 4: 学习统计 -->
          <el-tab-pane label="📊 学习统计" name="stats">
            <div v-if="stats" class="stats-dashboard">
              <!-- 概览卡片 -->
              <div class="stats-cards">
                <div class="stat-card">
                  <div class="stat-value" style="color:var(--primary);">{{ stats.total_chats }}</div>
                  <div class="stat-label">AI对话次数</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value" style="color:var(--success);">{{ stats.total_practices }}</div>
                  <div class="stat-label">练习次数</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value" style="color:var(--warning);">{{ stats.avg_practice_score }}</div>
                  <div class="stat-label">平均得分</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value" style="color:var(--danger);">{{ stats.total_competition_tasks }}</div>
                  <div class="stat-label">竞赛任务</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value" style="color:var(--primary);">{{ stats.completed_tasks }}</div>
                  <div class="stat-label">已完成论文</div>
                </div>
              </div>

              <!-- Agent 使用分布 -->
              <div style="margin-top:20px;">
                <h4 style="font-size: var(--text-sm);margin-bottom:12px;">Agent 使用分布</h4>
                <div class="agent-bars">
                  <div v-for="(count, agent) in stats.agent_breakdown" :key="agent" class="agent-bar-item">
                    <span class="agent-bar-label">{{ agentLabel2(agent) }}</span>
                    <div class="agent-bar-track">
                      <div class="agent-bar-fill" :style="{
                        width: maxAgentCount ? (count/maxAgentCount*100)+'%' : '0%',
                        background: agentColor(agent)
                      }"></div>
                    </div>
                    <span class="agent-bar-count">{{ count }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else style="text-align:center;padding:40px;color:var(--text-tertiary);">
              加载中...
            </div>
          </el-tab-pane>
        </el-tabs>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { authApi, profileApi } from '../api'
import { ElMessage } from 'element-plus'
import Sidebar from '../components/Sidebar.vue'
import {
  HomeFilled, User, Avatar, Edit, School, Clock, Lock, Key,
  CircleCheck, Check, Delete, Star
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

// ==================== 个人资料表单 ====================
const profileFormRef = ref(null)
const profileSaving = ref(false)

const profileForm = reactive({
  display_name: userStore.user?.display_name || '',
  class_name: userStore.user?.class_name || '',
})

const profileRules = {
  display_name: [
    { max: 50, message: '昵称不能超过50个字符', trigger: 'blur' },
  ],
  class_name: [
    { max: 50, message: '班级名称不能超过50个字符', trigger: 'blur' },
  ],
}

function resetProfile() {
  profileForm.display_name = userStore.user?.display_name || ''
  profileForm.class_name = userStore.user?.class_name || ''
}

async function saveProfile() {
  if (!profileFormRef.value) return
  try {
    await profileFormRef.value.validate()
  } catch { return }

  profileSaving.value = true
  try {
    const updated = await authApi.updateProfile({
      display_name: profileForm.display_name,
      class_name: profileForm.class_name,
    })
    // 更新本地 store
    userStore.user = { ...userStore.user, ...updated }
    localStorage.setItem('user', JSON.stringify(userStore.user))
    ElMessage.success('个人资料已保存')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    profileSaving.value = false
  }
}

// ==================== 密码修改表单 ====================
const passwordFormRef = ref(null)
const passwordSaving = ref(false)

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirmPassword = (_rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次密码输入不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    { pattern: /\d/, message: '密码必须包含至少一个数字', trigger: 'blur' },
    { pattern: /[a-zA-Z]/, message: '密码必须包含至少一个字母', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

// 密码强度计算
const pwdStrength = computed(() => {
  const p = passwordForm.new_password
  if (!p) return 0
  let score = 0
  if (p.length >= 8) score++
  if (p.length >= 12) score++
  if (/[a-z]/.test(p) && /[A-Z]/.test(p)) score++
  if (/\d/.test(p)) score++
  if (/[^a-zA-Z0-9]/.test(p)) score++
  return Math.min(score, 3)
})

const strengthClass = computed(() => {
  if (pwdStrength.value <= 1) return 'weak'
  if (pwdStrength.value === 2) return 'medium'
  return 'strong'
})

const strengthColor = computed(() => {
  if (pwdStrength.value <= 1) return 'var(--danger)'
  if (pwdStrength.value === 2) return 'var(--warning)'
  return 'var(--success)'
})

const strengthLabel = computed(() => {
  if (pwdStrength.value <= 1) return '弱'
  if (pwdStrength.value === 2) return '中等'
  return '强'
})

// 监听新密码变化，重新触发确认密码校验
watch(() => passwordForm.new_password, () => {
  if (passwordForm.confirm_password && passwordFormRef.value) {
    passwordFormRef.value.validateField('confirm_password')
  }
})

async function changePassword() {
  if (!passwordFormRef.value) return
  try {
    await passwordFormRef.value.validate()
  } catch { return }

  passwordSaving.value = true
  try {
    await authApi.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功，请妥善保管新密码')
    // 清空表单
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    passwordFormRef.value.resetFields()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '密码修改失败')
  } finally {
    passwordSaving.value = false
  }
}

// ==================== 辅助 ====================
const roleLabel = computed(() => {
  const map = { student: '学生', teacher: '教师', admin: '管理员' }
  return map[userStore.user?.role] || '用户'
})

const roleTagType = computed(() => {
  const map = { student: '', teacher: 'success', admin: 'danger' }
  return map[userStore.user?.role] || 'info'
})

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

// ==================== 个人中心标签页 ====================
const centerTab = ref('records')

// PRF-001: 学习记录
const recordFilter = ref('all')
const records = ref([])
async function loadRecords() {
  try {
    const res = await profileApi.getRecords({ type: recordFilter.value, page_size: 20 })
    records.value = res.records || []
  } catch (e) { /* ignore */ }
}

// PRF-002: 论文管理
const papers = ref([])
async function loadPapers() {
  try {
    const res = await profileApi.getPapers({ page_size: 20 })
    papers.value = res.papers || []
  } catch (e) { /* ignore */ }
}
function downloadCompetitionPaper(taskId) {
  const a = document.createElement('a')
  a.href = `/api/competition/tasks/${taskId}/paper/download`
  a.download = `paper_task${taskId}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

// PRF-003: 收藏书签
const bookmarks = ref(JSON.parse(localStorage.getItem('bookmarks') || '[]'))
function removeBookmark(index) {
  bookmarks.value.splice(index, 1)
  localStorage.setItem('bookmarks', JSON.stringify(bookmarks.value))
}

// PRF-004: 学习统计
const stats = ref(null)
const maxAgentCount = computed(() => {
  if (!stats.value?.agent_breakdown) return 1
  return Math.max(...Object.values(stats.value.agent_breakdown), 1)
})
function agentLabel2(type) {
  const m = { 'code-review': '建模辅导', 'training-guide': '实训引导', 'qa': '建模答疑', 'paper-review': '论文评审' }
  return m[type] || type
}
function agentColor(type) {
  const m = { 'code-review': '#165DFF', 'training-guide': '#00B42A', 'qa': '#FF7D00', 'paper-review': '#9B59B6' }
  return m[type] || '#86909C'
}
async function loadStats() {
  try {
    stats.value = await profileApi.getStats()
  } catch (e) { /* ignore */ }
}

// 监听tab切换加载数据
watch(centerTab, (tab) => {
  if (tab === 'records' && records.value.length === 0) loadRecords()
  if (tab === 'papers' && papers.value.length === 0) loadPapers()
  if (tab === 'stats' && !stats.value) loadStats()
})

onMounted(() => {
  loadRecords()
})
</script>

<style scoped lang="scss">
// 密码强度指示器
.pwd-strength {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.strength-bars {
  display: flex;
  gap: 4px;
  flex: 1;
}

.strength-seg {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: var(--border-light);
  transition: background 0.3s ease;

  &.active.weak { background: var(--danger); }
  &.active.medium { background: var(--warning); }
  &.active.strong { background: var(--success); }
}

.strength-text {
  font-size: var(--text-xs);
  font-weight: 500;
  white-space: nowrap;
}

// ===== 学习记录 =====
.record-list { display:flex; flex-direction:column; gap:6px; }
.record-item {
  padding: 12px 14px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-card);
  transition: border-color 0.2s;
  &:hover { border-color: var(--primary); }
}

// ===== 论文管理 =====
.paper-item {
  padding: 12px 14px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-card);
}

// ===== 书签 =====
.bookmark-item {
  padding: 12px 14px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-card);
}

// ===== 学习统计 =====
.stats-dashboard { padding: 0; }
.stats-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}
.stat-card {
  text-align: center;
  padding: 20px 12px;
  border-radius: 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
}
.stat-value {
  font-size: var(--text-xl);
  font-weight: 700;
  margin-bottom: 4px;
}
.stat-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

// Agent 使用分布
.agent-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.agent-bar-item {
  display: flex;
  align-items: center;
  gap: 10px;
}
.agent-bar-label {
  width: 80px;
  font-size: var(--text-xs);
  color: var(--text-secondary);
  text-align: right;
}
.agent-bar-track {
  flex: 1;
  height: 10px;
  background: var(--bg-primary);
  border-radius: 5px;
  overflow: hidden;
}
.agent-bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.5s ease;
}
.agent-bar-count {
  width: 30px;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-primary);
}
</style>
