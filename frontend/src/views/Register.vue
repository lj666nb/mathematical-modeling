<template>
  <!--
  ============================================================
  注册页面 - Bug修复 + 国赛级视觉重构
  Bug1修复：用户名校验文案逻辑颠倒 → 新增实时查重API，文案严格区分
  Bug2修复：注册后无法跳转 → 成功后push(/login) + 成功弹窗
  新增：密码强度检测、确认密码、完整表单校验
  视觉：蓝紫渐变背景+二进制纹理+品牌LOGO+卡片分层设计
  ============================================================
  -->
  <div class="register-page">
    <!-- 背景粒子 -->
    <div class="particles">
      <span v-for="i in 20" :key="i" class="particle"
        :style="{ left: randPct(i), top: randPct(i+5), delay: randDelay(i), size: randSize(i) }">
        {{ i % 3 === 0 ? '0' : '1' }}
      </span>
    </div>

    <div class="register-card">
      <!-- 卡片顶部品牌区 -->
      <div class="card-brand">
        <div class="brand-badge">
          <svg viewBox="0 0 24 24" class="brand-svg" fill="none">
            <path d="M5 4 C3 4 3 7 3 9 C3 11 2 12 2 12 C2 12 3 13 3 15 C3 17 3 20 5 20"
                  stroke="currentColor" stroke-width="0.9" fill="none" stroke-linecap="round"/>
            <path d="M19 4 C21 4 21 7 21 9 C21 11 22 12 22 12 C22 12 21 13 21 15 C21 17 21 20 19 20"
                  stroke="currentColor" stroke-width="0.9" fill="none" stroke-linecap="round"/>
            <path d="M12 8 L15 12 L12 16 L9 12 Z" stroke="currentColor" stroke-width="0.7" fill="none"/>
            <circle cx="12" cy="12" r="1.2" fill="currentColor"/>
            <path d="M7 6 C9 8 10 10 12 12" stroke="currentColor" stroke-width="0.7" fill="none" opacity="0.5" stroke-linecap="round"/>
            <path d="M17 6 C15 8 14 10 12 12" stroke="currentColor" stroke-width="0.7" fill="none" opacity="0.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="brand-text">
          <div class="brand-title">MathModel · AI数学建模</div>
          <div class="brand-sub">多智能体数学建模学科交叉教学系统</div>
        </div>
      </div>

      <!-- 标题 -->
      <h1 class="form-title">创建账号</h1>
      <p class="form-subtitle">加入AI多智能体数学建模教学平台，开启数学建模学习之旅</p>

      <!-- 表单 -->
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @submit.prevent="handleRegister"
        class="register-form" status-icon>

        <!-- 用户名（实时校验） -->
        <el-form-item label="用户名" prop="username" class="form-item-required">
          <el-input
            v-model="form.username"
            placeholder="3-16位字母或数字"
            :prefix-icon="User"
            maxlength="16"
            @blur="checkUsername"
            @input="onUsernameInput"
            :class="usernameStatus === 'valid' ? 'input-valid' : usernameStatus === 'invalid' ? 'input-error' : ''"
          >
            <template #suffix>
              <el-icon v-if="usernameChecking" class="is-loading"><Loading /></el-icon>
              <el-icon v-else-if="usernameStatus === 'valid'" color="#00B42A"><CircleCheck /></el-icon>
              <el-icon v-else-if="usernameStatus === 'invalid'" color="#F53F3F"><CloseBold /></el-icon>
            </template>
          </el-input>
          <div v-if="usernameStatus === 'valid'" class="input-hint hint-valid">用户名可用</div>
          <div v-else-if="usernameStatus === 'invalid'" class="input-hint hint-error">该用户名已被注册，请更换</div>
          <div v-else-if="usernameStatus === 'format-error'" class="input-hint hint-error">仅允许字母和数字</div>
        </el-form-item>

        <!-- 昵称 -->
        <el-form-item label="昵称" prop="display_name">
          <el-input v-model="form.display_name" placeholder="选填，展示用昵称" :prefix-icon="EditPen" />
        </el-form-item>

        <!-- 密码 -->
        <el-form-item label="密码" prop="password" class="form-item-required">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="至少6位密码"
            :prefix-icon="Lock"
            show-password
            @input="onPasswordInput"
          />
          <!-- 密码强度 -->
          <div v-if="form.password.length > 0" class="pwd-strength">
            <div class="strength-bar">
              <div class="strength-fill" :class="strengthClass" :style="{ width: strengthWidth + '%' }"></div>
            </div>
            <span class="strength-label" :class="strengthClass">{{ strengthText }}</span>
          </div>
        </el-form-item>

        <!-- 确认密码 -->
        <el-form-item label="确认密码" prop="confirmPassword" class="form-item-required">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <!-- 角色 + 班级（双列） -->
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="角色" prop="role" class="form-item-required">
              <el-select v-model="form.role" style="width:100%">
                <el-option label="学生" value="student" />
                <el-option label="教师" value="teacher" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="班级" prop="class_name">
              <el-input v-model="form.class_name" placeholder="如：数模实验班" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 提交按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="submit-btn"
            :loading="loading"
            :disabled="submitDisabled"
            native-type="submit"
          >
            <el-icon v-if="!loading"><UserFilled /></el-icon>
            {{ loading ? '注册中...' : '注 册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 底部登录跳转 -->
      <div class="login-link">
        <span>已有账号？</span>
        <router-link to="/login" class="login-route-link">
          立即登录
          <el-icon><ArrowRight /></el-icon>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, EditPen, Lock, Loading, CircleCheck, CloseBold, UserFilled, ArrowRight } from '@element-plus/icons-vue'
import { authApi } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

// ==================== 用户名校验状态 ====================
const usernameChecking = ref(false)
const usernameStatus = ref('')  // '' | 'valid' | 'invalid' | 'format-error' | 'checking'

const form = reactive({
  username: '',
  display_name: '',
  password: '',
  confirmPassword: '',
  role: 'student',
  class_name: ''
})

// ==================== 密码强度 ====================
const strengthWidth = ref(0)
const strengthText = ref('')
const strengthClass = ref('')

function calcPasswordStrength(pwd) {
  if (!pwd) { strengthWidth.value = 0; strengthText.value = ''; strengthClass.value = ''; return }
  let score = 0
  if (pwd.length >= 8) score += 20
  if (pwd.length >= 10) score += 10
  if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score += 20
  if (/\d/.test(pwd)) score += 15
  if (/[^a-zA-Z0-9]/.test(pwd)) score += 15
  score = Math.min(score, 100)

  strengthWidth.value = score
  if (score < 30) { strengthText.value = '弱'; strengthClass.value = 'weak' }
  else if (score < 60) { strengthText.value = '中'; strengthClass.value = 'medium' }
  else { strengthText.value = '强'; strengthClass.value = 'strong' }
}

function onPasswordInput() { calcPasswordStrength(form.password) }

// ==================== 实时查重校验 ====================
// Bug1修复：输入框失去焦点时自动请求后端，文案严格区分"已注册"/"可用"

async function checkUsername() {
  const val = form.username.trim()
  if (!val || val.length < 3) { usernameStatus.value = ''; return }

  // 格式校验
  if (!/^[a-zA-Z0-9]+$/.test(val)) { usernameStatus.value = 'format-error'; return }

  usernameChecking.value = true
  usernameStatus.value = 'checking'
  try {
    // 请求后端查重接口
    const data = await authApi.checkUsername(val)
    if (data.exists) {
      usernameStatus.value = 'invalid'   // 红色：已被注册
    } else {
      usernameStatus.value = 'valid'     // 绿色：可用
    }
  } catch (err) {
    usernameStatus.value = ''
  } finally {
    usernameChecking.value = false
  }
}

function onUsernameInput() {
  // 输入时重置校验状态
  if (usernameStatus.value !== '') usernameStatus.value = ''
}

// 提交按钮锁定：仅当用户名格式错误或已被注册时才置灰
// Bug修复：不在 usernameStatus 为空（未校验）时禁用，避免用户不触发 blur 就无法提交
const submitDisabled = computed(() => {
  if (loading.value) return true
  if (usernameStatus.value === 'invalid' || usernameStatus.value === 'format-error') return true
  return false
})

// ==================== 表单校验规则 ====================
const validateUsername = (rule, value, callback) => {
  if (!value) return callback(new Error('请输入用户名'))
  if (value.length < 3) return callback(new Error('用户名至少3个字符'))
  if (value.length > 16) return callback(new Error('用户名不超过16个字符'))
  if (!/^[a-zA-Z0-9]+$/.test(value)) return callback(new Error('仅允许字母和数字'))
  if (usernameStatus.value === 'invalid') return callback(new Error('该用户名已被注册'))
  callback()
}

const validatePassword = (rule, value, callback) => {
  if (!value) return callback(new Error('请输入密码'))
  if (value.length < 6) return callback(new Error('密码至少6位'))
  callback()
}

const validateConfirm = (rule, value, callback) => {
  if (!value) return callback(new Error('请再次输入密码'))
  if (value !== form.password) return callback(new Error('两次密码输入不一致'))
  callback()
}

const rules = {
  username: [
    { required: true, validator: validateUsername, trigger: ['blur', 'change'] }
  ],
  password: [
    { required: true, validator: validatePassword, trigger: ['blur', 'change'] }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirm, trigger: ['blur', 'change'] }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// ==================== 注册提交 ====================
// Bug2修复：注册成功后正确跳转登录页 + 成功弹窗

async function handleRegister() {
  // Bug修复：提交前先校验用户名的格式+唯一性（用户可能未触发 blur）
  if (form.username.trim().length >= 3 && /^[a-zA-Z0-9]+$/.test(form.username.trim())) {
    if (usernameStatus.value !== 'valid' && usernameStatus.value !== 'invalid') {
      await checkUsername()
    }
    // 等待校验完成后，如果用户名已被注册，阻止提交
    if (usernameStatus.value === 'invalid') {
      ElMessage.error('该用户名已被注册，请更换')
      return
    }
    if (usernameStatus.value === 'format-error') {
      ElMessage.error('用户名仅允许字母和数字')
      return
    }
  }

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    ElMessage.warning('请正确填写所有必填项')
    return
  }

  loading.value = true
  try {
    // 发送注册请求
    await authApi.register({
      username: form.username,
      password: form.password,
      role: form.role,
      class_name: form.class_name,
      display_name: form.display_name || form.username
    })

    // Bug2修复：注册成功 → 绿色弹窗 + 跳转登录页
    ElMessage.success({
      message: '🎉 账号注册成功，请前往登录！',
      duration: 3000
    })

    // 路由跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 500)

  } catch (err) {
    // 错误在拦截器中已处理，此处补充提示
    const detail = err?.response?.data?.detail || ''
    if (detail === '用户名已存在') {
      usernameStatus.value = 'invalid'
      ElMessage.error('该用户名已被注册，请更换')
    } else if (detail) {
      ElMessage.error(detail)
    } else {
      ElMessage.error('注册失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

// ==================== 粒子背景辅助 ====================
function randPct(seed) { return ((seed * 17 + 3) % 100) + '%' }
function randDelay(seed) { return ((seed * 7) % 5) + 's' }
function randSize(seed) { return (seed % 3 === 0 ? '8' : '6') + 'px' }

// ==================== 路由守卫：已登录用户不可访问注册页 ====================
onMounted(() => {
  if (userStore.isLoggedIn) {
    router.push('/dashboard')
  }
})
</script>

<style scoped lang="scss">
/* ============================================================
   注册页专属样式 - 国赛级视觉设计
   渐变背景 + 二进制纹理 + 品牌卡片 + 输入框交互动效
   ============================================================ */

/* ---------- 页面背景 ---------- */
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 30%, #F0F4FF 60%, #EDF2FF 100%);
}

/* ---------- 二进制粒子背景 ---------- */
.particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.particle {
  position: absolute;
  font-family: 'Courier New', monospace;
  color: rgba(22, 93, 255, 0.04);
  font-weight: 700;
  animation: floatParticle 8s ease-in-out infinite;
  user-select: none;
}
@keyframes floatParticle {
  0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.3; }
  25% { transform: translateY(-20px) rotate(3deg); opacity: 0.6; }
  50% { transform: translateY(-40px) rotate(-2deg); opacity: 0.4; }
  75% { transform: translateY(-15px) rotate(1deg); opacity: 0.7; }
}

/* ---------- 注册卡片 ---------- */
.register-card {
  width: 500px;
  padding: 36px 40px 32px;
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.04),
    0 16px 40px rgba(22, 93, 255, 0.06);
  position: relative;
  z-index: 1;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.register-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.06),
    0 20px 48px rgba(22, 93, 255, 0.08);
}

/* ---------- 品牌区 ---------- */
.card-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #F0F1F5;
}
.brand-badge {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #F0F4FF;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #165DFF;
  flex-shrink: 0;
}
.brand-svg { width: 24px; height: 24px; }
.brand-text { flex: 1; min-width: 0; }
.brand-title { font-size: var(--text-base); font-weight: 700; color: #1D2129; letter-spacing: 0.3px; }
.brand-sub { font-size: var(--text-xs); color: #86909C; margin-top: 2px; }

/* ---------- 标题 ---------- */
.form-title { font-size: var(--text-lg); font-weight: 700; color: #1D2129; margin-bottom: 4px; letter-spacing: -0.3px; }
.form-subtitle { font-size: var(--text-sm); color: #86909C; margin-bottom: 24px; }

/* ---------- 表单 ---------- */
.register-form { max-width: 100%; }

/* 必填项红色星标 */
:deep(.form-item-required .el-form-item__label::before) {
  content: '* ';
  color: #F53F3F;
  font-weight: 600;
}

/* 输入框统一样式 */
:deep(.el-input__wrapper) {
  border-radius: 8px !important;
  box-shadow: 0 0 0 1px #E5E6EB inset !important;
  transition: box-shadow 0.25s ease !important;
  padding: 4px 12px !important;
}
:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #165DFF inset !important;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #165DFF inset, 0 0 0 3px rgba(22, 93, 255, 0.08) !important;
}
:deep(.el-input__inner) {
  height: 36px !important;
  font-size: var(--text-sm) !important;
}
:deep(.el-form-item) {
  margin-bottom: 22px;
}
:deep(.el-form-item__label) {
  font-size: var(--text-sm);
  font-weight: 600;
  color: #4E5969;
  padding-bottom: 4px;
}

/* 输入框校验状态覆盖 */
:deep(.input-valid .el-input__wrapper) {
  box-shadow: 0 0 0 1px #00B42A inset !important;
  background: #F6FFF9;
}
:deep(.input-error .el-input__wrapper) {
  box-shadow: 0 0 0 1px #F53F3F inset !important;
  background: #FFF8F8;
}

/* 输入框下方提示 */
.input-hint {
  font-size: var(--text-xs);
  margin-top: 4px;
  padding-left: 2px;
  line-height: 1.4;
}
.hint-valid { color: #00B42A; }
.hint-error { color: #F53F3F; }

/* select 统一样式 */
:deep(.el-select .el-input__wrapper) { border-radius: 8px !important; }

/* ---------- 密码强度 ---------- */
.pwd-strength {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}
.strength-bar {
  flex: 1;
  height: 4px;
  background: #F0F1F5;
  border-radius: 2px;
  overflow: hidden;
}
.strength-fill {
  height: 100%;
  border-radius: 2px;
  transition: all 0.3s ease;
}
.strength-fill.weak { background: linear-gradient(90deg, #F53F3F, #FF7D00); }
.strength-fill.medium { background: linear-gradient(90deg, #FF7D00, #FFC800); }
.strength-fill.strong { background: linear-gradient(90deg, #00B42A, #27C24C); }
.strength-label {
  font-size: var(--text-xs);
  font-weight: 500;
  width: 20px;
  text-align: center;
}
.strength-label.weak { color: #F53F3F; }
.strength-label.medium { color: #FF7D00; }
.strength-label.strong { color: #00B42A; }

/* ---------- 提交按钮 ---------- */
.submit-btn {
  width: 100%;
  height: 44px;
  font-size: var(--text-base);
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, #165DFF 0%, #3C7EFF 100%) !important;
  border: none !important;
  letter-spacing: 2px;
  transition: all 0.25s ease !important;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.submit-btn:hover {
  background: linear-gradient(135deg, #0E42D2 0%, #165DFF 100%) !important;
  transform: scale(1.015);
  box-shadow: 0 6px 20px rgba(22, 93, 255, 0.30) !important;
}
.submit-btn:active {
  transform: scale(0.985);
}
.submit-btn.is-disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
  transform: none !important;
  box-shadow: none !important;
}

/* ---------- 底部登录链接 ---------- */
.login-link {
  text-align: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #F0F1F5;
  font-size: var(--text-sm);
  color: #86909C;
}
.login-route-link {
  color: #165DFF;
  font-weight: 500;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;
}
.login-route-link:hover {
  color: #0E42D2;
  text-decoration: underline;
  gap: 6px;
}

/* ---------- Element Plus 消息弹窗覆盖 ---------- */
:global(.el-message) {
  border-radius: 8px !important;
  min-width: 300px !important;
}
:global(.el-message--success) {
  background: #F6FFF9 !important;
  border-color: #00B42A !important;
}
:global(.el-message--error) {
  background: #FFF8F8 !important;
  border-color: #F53F3F !important;
}
:global(.el-message--warning) {
  background: #FFFCF0 !important;
  border-color: #FF7D00 !important;
}

/* ---------- Loading 旋转动画 ---------- */
.is-loading { animation: rotating 1s linear infinite; }
@keyframes rotating { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

/* ---------- 响应式 ---------- */
@media (max-width: 540px) {
  .register-card { width: 94%; padding: 28px 20px 24px; margin: 16px; }
}
</style>
