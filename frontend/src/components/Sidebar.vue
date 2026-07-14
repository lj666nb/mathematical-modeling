<template>
  <!--
  数学建模智能教学平台 — 侧边栏
  设计方向：「石板与粉笔金」— 暗色学术工坊
  遵循 frontend-design skill 原则：扎根数学主题、排版承载个性、一处大胆其余克制
  -->
  <div class="sidebar" :class="{ collapsed: isCollapsed }">

    <!-- ====== 品牌区：数学符号标识 ====== -->
    <div class="sidebar-brand">
      <div class="brand-mark">
        <!-- Σ (求和符号) — 数学建模的核心：从数据中提取结构 -->
        <svg viewBox="0 0 32 32" class="brand-svg" fill="none">
          <path d="M24 6H10L8 16L10 26H24"
                stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M10 16H22" stroke="currentColor" stroke-width="0.8" opacity="0.4"/>
          <line x1="12" y1="6" x2="20" y2="6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="12" y1="26" x2="20" y2="26" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <transition name="fade-text">
        <div class="brand-info" v-show="!isCollapsed">
          <div class="brand-name">MathModel</div>
          <div class="brand-desc">AI · 数学建模教学平台</div>
        </div>
      </transition>
    </div>

    <div class="sidebar-divider"></div>

    <!-- ====== 主导航 ====== -->
    <nav class="sidebar-nav">
      <div class="nav-section-label" v-show="!isCollapsed">学习</div>

      <router-link to="/dashboard" class="nav-item" :class="{ active: isActive('/dashboard') }">
        <span class="nav-indicator"></span>
        <el-icon class="nav-icon"><Monitor /></el-icon>
        <span class="nav-text">个人看板</span>
      </router-link>

      <router-link to="/knowledge-base" class="nav-item" :class="{ active: isActive('/knowledge-base') }">
        <span class="nav-indicator"></span>
        <el-icon class="nav-icon"><Reading /></el-icon>
        <span class="nav-text">学习中心</span>
        <span class="nav-hint">知识库</span>
      </router-link>

      <router-link to="/experiments" class="nav-item" :class="{ active: isActive('/experiments') }">
        <span class="nav-indicator"></span>
        <el-icon class="nav-icon"><Notebook /></el-icon>
        <span class="nav-text">建模题库</span>
        <span class="nav-hint">8类模型</span>
      </router-link>

      <div class="nav-section-label" v-show="!isCollapsed">工具</div>

      <router-link to="/agent-chat" class="nav-item" :class="{ active: isActive('/agent-chat') }">
        <span class="nav-indicator"></span>
        <el-icon class="nav-icon"><ChatDotSquare /></el-icon>
        <span class="nav-text">AI 辅导</span>
        <span class="nav-hint">4 Agent</span>
      </router-link>

      <router-link to="/code-editor" class="nav-item" :class="{ active: isActive('/code-editor') }">
        <span class="nav-indicator"></span>
        <el-icon class="nav-icon"><Edit /></el-icon>
        <span class="nav-text">编程工作台</span>
      </router-link>

      <router-link to="/workspace" class="nav-item" :class="{ active: isActive('/workspace') }">
        <span class="nav-indicator"></span>
        <el-icon class="nav-icon"><DataAnalysis /></el-icon>
        <span class="nav-text">数据工作台</span>
        <span class="nav-hint">数据+图表+论文</span>
      </router-link>

      <router-link to="/llm-config" class="nav-item" :class="{ active: isActive('/llm-config') }">
        <span class="nav-indicator"></span>
        <el-icon class="nav-icon"><Key /></el-icon>
        <span class="nav-text">API 配置</span>
      </router-link>

      <div class="nav-section-label" v-show="!isCollapsed">竞赛</div>

      <router-link to="/competition" class="nav-item" :class="{ active: isActive('/competition') }">
        <span class="nav-indicator"></span>
        <el-icon class="nav-icon"><Trophy /></el-icon>
        <span class="nav-text">竞赛训练</span>
        <span class="nav-hint accent">S0-S8</span>
      </router-link>

      <!-- 教师专属 -->
      <router-link
        v-if="userStore.user?.role === 'teacher' || userStore.user?.role === 'admin'"
        to="/teacher-stats"
        class="nav-item"
        :class="{ active: isActive('/teacher-stats') }"
      >
        <span class="nav-indicator"></span>
        <el-icon class="nav-icon"><DataAnalysis /></el-icon>
        <span class="nav-text">教学统计</span>
      </router-link>
    </nav>

    <!-- ====== 底部用户区 ====== -->
    <div class="sidebar-footer">
      <router-link to="/profile" class="user-strip">
        <div class="user-avatar">{{ avatarChar }}</div>
        <transition name="fade-text">
          <div class="user-info" v-show="!isCollapsed">
            <span class="user-name">{{ displayName }}</span>
            <span class="user-role">{{ roleLabel }}</span>
          </div>
        </transition>
      </router-link>
      <button class="logout-btn" @click="handleLogout" :title="'退出登录'">
        <el-icon :size="15"><SwitchButton /></el-icon>
        <span v-show="!isCollapsed">退出</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import {
  Monitor, Notebook, ChatDotSquare, Edit, Key,
  DataAnalysis, SwitchButton, Trophy, Reading
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapsed = ref(false)

function isActive(path) {
  return route.path.startsWith(path)
}

const displayName = computed(() =>
  userStore.user?.display_name || userStore.user?.username || '用户'
)
const avatarChar = computed(() => displayName.value.charAt(0).toUpperCase())
const roleLabel = computed(() => {
  const map = { student: '学生', teacher: '教师', admin: '管理员' }
  return map[userStore.user?.role] || '用户'
})

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped lang="scss">
/* ============================================================
   侧边栏 — 暗色石板 + 金色强调
   ============================================================ */

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--color-slate-800);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  transition: width 0.3s var(--ease-in-out);
  overflow: hidden;
  user-select: none;
  border-right: var(--border-subtle);
}

.sidebar.collapsed {
  width: 64px;
}

/* —— 品牌区 —— */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-4);
  cursor: pointer;
  min-height: 64px;

  .collapsed & {
    justify-content: center;
    padding: var(--space-5) var(--space-2);
  }
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: var(--color-gold-subtle);
  border: 1px solid var(--color-gold-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: border-color var(--duration-normal) var(--ease-out);

  .sidebar-brand:hover & {
    border-color: var(--color-gold);
  }
}

.brand-svg {
  width: 20px;
  height: 20px;
  color: var(--color-gold);
}

.brand-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  white-space: nowrap;
}

.brand-name {
  font-family: var(--font-display);
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-chalk);
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.brand-desc {
  font-size: var(--text-xs);
  color: var(--color-chalk-faint);
  margin-top: 2px;
  font-weight: var(--weight-normal);
}

/* —— 分隔线 —— */
.sidebar-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: 0 var(--space-4);
}

/* —— 导航 —— */
.sidebar-nav {
  flex: 1;
  padding: var(--space-2) 0;
  overflow-y: auto;
}

.nav-section-label {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-chalk-faint);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: var(--space-5) var(--space-5) var(--space-3);
  white-space: nowrap;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 38px;
  padding: 0 var(--space-4);
  margin: 1px var(--space-2);
  border-radius: var(--radius-md);
  cursor: pointer;
  text-decoration: none;
  position: relative;
  color: var(--color-chalk-dim);
  transition: color var(--duration-fast) var(--ease-out),
              background var(--duration-fast) var(--ease-out);

  .collapsed & {
    justify-content: center;
    padding: 0;
  }
}

.nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  border-radius: 0 2px 2px 0;
  background: var(--color-gold);
  transition: height var(--duration-normal) var(--ease-out);
}

.nav-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
  transition: color var(--duration-fast) var(--ease-out);
}

.nav-text {
  font-size: var(--text-sm);
  font-weight: var(--weight-normal);
  white-space: nowrap;
  flex: 1;
}

.nav-hint {
  font-size: var(--text-xs);
  padding: 1px var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--color-slate-600);
  color: var(--color-chalk-faint);
  white-space: nowrap;

  &.accent {
    background: var(--color-gold-subtle);
    color: var(--color-gold);
  }
}

.nav-item:hover {
  color: var(--color-chalk);
  background: var(--color-slate-600);

  .nav-indicator {
    height: 14px;
  }
}

.nav-item.active {
  color: var(--color-chalk);
  background: var(--color-gold-subtle);

  .nav-indicator {
    height: 22px;
  }

  .nav-icon {
    color: var(--color-gold);
  }
}

/* —— 底部用户区 —— */
.sidebar-footer {
  padding: var(--space-3) var(--space-3) var(--space-4);
  border-top: var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);

  .collapsed & {
    align-items: center;
  }
}

.user-strip {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-1);
  text-decoration: none;
  border-radius: var(--radius-md);
  transition: background var(--duration-fast) var(--ease-out);

  &:hover {
    background: var(--color-slate-600);
  }

  .collapsed & {
    justify-content: center;
  }
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-gold-subtle);
  border: 1px solid var(--color-gold-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-gold);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  white-space: nowrap;
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-chalk);
  line-height: 1.2;
}

.user-role {
  font-size: var(--text-xs);
  color: var(--color-chalk-faint);
  margin-top: 1px;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  height: 30px;
  padding: 0 var(--space-3);
  background: none;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-chalk-faint);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);

  .collapsed & {
    justify-content: center;
    width: auto;
  }

  &:hover {
    color: var(--color-error);
    background: rgba(196, 102, 90, 0.1);
  }
}

/* —— 过渡 —— */
.fade-text-enter-active,
.fade-text-leave-active {
  transition: opacity var(--duration-normal) var(--ease-out);
}

.fade-text-enter-from,
.fade-text-leave-to {
  opacity: 0;
}
</style>
