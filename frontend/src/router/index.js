/**
 * 路由配置 + 全局路由守卫
 * Bug2修复：Token过期路由守卫逻辑重构，去重弹窗，记住访问路径
 */
import { createRouter, createWebHistory } from 'vue-router'

// 白名单路由（无需登录即可访问）
const WHITE_LIST = ['Login', 'Register']

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', noAuth: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { title: '注册', noAuth: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '学习看板' }
  },
  {
    path: '/llm-config',
    name: 'LlmConfig',
    component: () => import('../views/LlmConfig.vue'),
    meta: { title: 'API配置' }
  },
  {
    path: '/experiments',
    name: 'Experiments',
    component: () => import('../views/Experiments.vue'),
    meta: { title: '建模题库' }
  },
  {
    path: '/code-editor',
    name: 'CodeEditor',
    component: () => import('../views/CodeEditor.vue'),
    meta: { title: '建模工作台' }
  },
  {
    path: '/code-editor/:experimentId',
    name: 'CodeEditorWithExperiment',
    component: () => import('../views/CodeEditor.vue'),
    meta: { title: '建模工作台' }
  },
  {
    path: '/agent-chat',
    name: 'AgentChat',
    component: () => import('../views/AgentChat.vue'),
    meta: { title: 'AI辅导' }
  },
  {
    path: '/teacher-stats',
    name: 'TeacherStats',
    component: () => import('../views/TeacherStats.vue'),
    meta: { title: '教学统计', role: ['teacher', 'admin'] }
  },
  {
    path: '/competition',
    name: 'Competition',
    component: () => import('../views/Competition.vue'),
    meta: { title: '竞赛训练' }
  },
  {
    path: '/knowledge-base',
    name: 'KnowledgeBase',
    component: () => import('../views/KnowledgeBase.vue'),
    meta: { title: '学习中心' }
  },
  {
    path: '/knowledge/:categoryId',
    name: 'KnowledgeDetail',
    component: () => import('../views/KnowledgeDetail.vue'),
    meta: { title: '模型详情' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { title: '个人中心' }
  },
  {
    path: '/workspace',
    name: 'Workspace',
    component: () => import('../views/Workspace.vue'),
    meta: { title: '建模工作台' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局路由守卫 - 修复Token过期逻辑
router.beforeEach((to, from, next) => {
  // 白名单放行（登录页/注册页），无需token
  if (WHITE_LIST.includes(to.name)) {
    next()
    return
  }

  // 非白名单页面：检查本地是否存有token
  const token = localStorage.getItem('token')

  if (!token) {
    // 无token → 直接跳转登录页，携带目标路径以便登录后回跳
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 有token：验证用户信息完整性（user store可能因刷新页面尚未初始化）
  const userStr = localStorage.getItem('user')
  if (!userStr) {
    // 有token但无用户信息 → token异常，清空后跳转登录
    localStorage.removeItem('token')
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // token存在且用户信息完整：尝试解析用户信息做角色校验
  try {
    const user = JSON.parse(userStr)
    // 角色权限检查
    if (to.meta.role && !to.meta.role.includes(user.role)) {
      next({ name: 'Dashboard' })
      return
    }
  } catch (e) {
    // 用户信息解析失败 → 清空缓存跳转登录
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    next({ name: 'Login' })
    return
  }

  next()
})

export default router
