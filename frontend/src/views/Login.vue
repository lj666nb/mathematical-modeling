<template>
  <!--
  登录页面 — 「石板与粉笔金」设计
  签名元素：极淡的数学网格背景 + 金色Σ符号
  遵循 frontend-design skill：扎根数学主题、一处大胆其余克制
  -->
  <div class="login-page">
    <!-- 签名背景：极淡的数学网格纹理 -->
    <div class="login-bg"></div>

    <!-- 中央面板 -->
    <div class="login-panel">
      <!-- 品牌标识 — 唯一的"大胆"元素 -->
      <div class="login-brand">
        <div class="brand-symbol">
          <!-- Σ — 求和符号，数学建模的核心动作 -->
          <svg viewBox="0 0 40 40" class="brand-icon" fill="none">
            <path d="M30 8H12L10 20L12 32H30"
                  stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 20H26" stroke="currentColor" stroke-width="0.7" opacity="0.3"/>
            <line x1="15" y1="8" x2="26" y2="8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            <line x1="15" y1="32" x2="26" y2="32" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          </svg>
        </div>
        <h1 class="brand-title">MathModel</h1>
        <p class="brand-tagline">AI · 数学建模智能教学平台</p>
      </div>

      <!-- 表单 — 克制、精准 -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="field-group">
          <label class="field-label" for="username">用户名</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            class="app-input"
            placeholder="输入用户名"
            autocomplete="username"
            :disabled="loading"
          />
        </div>

        <div class="field-group">
          <label class="field-label" for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            class="app-input"
            placeholder="输入密码"
            autocomplete="current-password"
            :disabled="loading"
          />
        </div>

        <button
          type="submit"
          class="btn-primary login-submit"
          :disabled="loading"
        >
          {{ loading ? '验证中...' : '进入平台' }}
        </button>
      </form>

      <!-- 底部链接 -->
      <div class="login-footer">
        <span class="text-dim">还没有账号？</span>
        <router-link to="/register" class="text-gold">注册</router-link>
      </div>
    </div>

    <!-- 大赛标识 -->
    <div class="competition-tag">
      全球校园人工智能算法精英大赛 · AI+学科交叉赛道
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
let _lock = false

onMounted(async () => {
  // 有旧token时先验证有效性，避免直接跳转导致401循环
  const savedToken = localStorage.getItem('token')
  if (savedToken) {
    try {
      await authApi.verifyToken()
      // token有效，直接跳转
      router.push('/dashboard')
    } catch (_) {
      // token失效，静默清理（不弹错误提示）
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})

const form = reactive({
  username: '',
  password: ''
})

async function handleLogin() {
  // 前端非空校验
  if (!form.username.trim() || !form.password.trim()) {
    ElMessage.warning('请填写用户名和密码')
    return
  }

  if (_lock) return
  _lock = true
  loading.value = true

  try {
    const res = await authApi.login({
      username: form.username.trim(),
      password: form.password
    })

    userStore.setAuth(res.access_token, res.user)

    ElMessage.success(`欢迎回来，${res.user.display_name || res.user.username}`)

    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  } catch (err) {
    const status = err?.response?.status
    const detail = err?.response?.data?.detail || ''

    if (status === 401 || detail.includes('用户名或密码错误')) {
      ElMessage.error('用户名或密码错误')
    } else if (detail) {
      ElMessage.error(detail)
    }
  } finally {
    loading.value = false
    setTimeout(() => { _lock = false }, 2000)
  }
}
</script>

<style scoped lang="scss">
/* ============================================================
   登录页 — 暗色石板 + 金色品牌
   签名元素：极淡数学网格纹理
   ============================================================ */

.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: var(--color-slate-900);
}

/* —— 签名背景：数学网格 —— */
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.03;
  background-image:
    radial-gradient(circle at 70% 20%, var(--color-gold) 0, transparent 50%),
    radial-gradient(circle at 30% 80%, var(--color-gold) 0, transparent 40%),
    linear-gradient(var(--color-slate-500) 0.5px, transparent 0.5px),
    linear-gradient(90deg, var(--color-slate-500) 0.5px, transparent 0.5px);
  background-size:
    100% 100%,
    100% 100%,
    48px 48px,
    48px 48px;
}

/* —— 面板 —— */
.login-panel {
  width: 420px;
  padding: var(--space-10) var(--space-9) var(--space-8);
  position: relative;
  z-index: 1;
  background: var(--color-slate-800);
  border: var(--border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}

/* —— 品牌区：签名元素 —— */
.login-brand {
  text-align: center;
  margin-bottom: var(--space-8);
}

.brand-symbol {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-lg);
  background: rgba(201, 168, 76, 0.08);
  border: 1px solid rgba(201, 168, 76, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--space-5);
}

.brand-icon {
  width: 30px;
  height: 30px;
  color: var(--color-gold);
}

.brand-title {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: var(--weight-semibold);
  color: var(--color-chalk);
  letter-spacing: -0.02em;
  margin-bottom: var(--space-2);
}

.brand-tagline {
  font-size: var(--text-sm);
  color: var(--color-chalk-dim);
  font-weight: var(--weight-normal);
  letter-spacing: 0.02em;
}

/* —— 表单 —— */
.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field-label {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-chalk-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.login-submit {
  width: 100%;
  height: 48px;
  justify-content: center;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  margin-top: var(--space-3);
  letter-spacing: 0.03em;
}

/* —— 底部 —— */
.login-footer {
  text-align: center;
  margin-top: var(--space-7);
  padding-top: var(--space-5);
  border-top: var(--border-subtle);
  font-size: var(--text-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
}

/* —— 大赛标识 —— */
.competition-tag {
  position: absolute;
  bottom: var(--space-6);
  left: 0;
  right: 0;
  text-align: center;
  font-size: var(--text-xs);
  color: var(--color-chalk-faint);
  letter-spacing: 0.04em;
  z-index: 1;
}

/* —— 响应式 —— */
@media (max-width: 480px) {
  .login-panel {
    width: 92%;
    padding: var(--space-7) var(--space-5) var(--space-5);
    margin: var(--space-4);
  }
}
</style>
