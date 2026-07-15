/**
 * API请求封装模块
 * Bug1修复：Axios拦截器401去重防抖锁，杜绝重复弹窗
 * Bug2修复：Token过期统一清缓存+3秒内只弹1次提示
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 全局401去重锁：3秒内只弹出1次过期提示
let _authRedirecting = false

function clearAuthCache() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  localStorage.removeItem('llm_key_mode')
  localStorage.removeItem('llm_api_key')
  localStorage.removeItem('llm_base_url')
  localStorage.removeItem('llm_model')
  localStorage.removeItem('llm_provider')
}

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 600000,  // 10分钟，论文生成等LLM调用耗时长
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动添加JWT令牌 + LLM浏览器密钥模式支持
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 🔧 FormData文件上传：删除默认的Content-Type，让axios自动设置正确的multipart/form-data+boundary
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    // 浏览器密钥模式：从localStorage读取LLM配置注入到请求头
    const llmKeyMode = localStorage.getItem('llm_key_mode')
    if (llmKeyMode === 'browser') {
      const llmApiKey = localStorage.getItem('llm_api_key')
      const llmBaseUrl = localStorage.getItem('llm_base_url')
      const llmModel = localStorage.getItem('llm_model')
      const llmProvider = localStorage.getItem('llm_provider')

      if (llmApiKey) {
        config.headers['X-LLM-Api-Key'] = llmApiKey
        if (llmBaseUrl) config.headers['X-LLM-Base-Url'] = llmBaseUrl
        if (llmModel) config.headers['X-LLM-Model'] = llmModel
        if (llmProvider) config.headers['X-LLM-Provider'] = llmProvider
      }
    }

    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器：统一错误处理（含401去重锁）
request.interceptors.response.use(
  response => response.data,
  error => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || error.message
    const url = error.config?.url || ''

    // 判断是否为登录/注册相关请求 — 这些401由页面自行处理
    const isAuthRequest = url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/verify-token')

    if (status === 401) {
      // 登录/注册接口的401由页面自行处理，不触发全局拦截
      if (isAuthRequest) {
        return Promise.reject(error)
      }

      // 判断当前是否已在登录/注册页面，避免重复跳转
      let isOnAuthPage = false
      try {
        const currentPath = window.location.hash?.replace('#', '') || window.location.pathname
        isOnAuthPage = currentPath === '/login' || currentPath === '/register'
      } catch (_) { /* ignore */ }

      if (isOnAuthPage) {
        // 已经在登录页，不弹窗不跳转，只清理旧缓存
        clearAuthCache()
        return Promise.reject(error)
      }

      // 在其他页面遇到401 → 过期处理
      if (!_authRedirecting) {
        _authRedirecting = true

        // 清除全部登录缓存
        clearAuthCache()

        // 3秒内只弹1次
        ElMessage.error({
          message: '登录已过期，请重新登录',
          duration: 3000,
          onClose: () => { _authRedirecting = false }
        })

        // 延迟跳转
        setTimeout(() => {
          import('../router').then(mod => {
            mod.default.push('/login')
          })
          setTimeout(() => { _authRedirecting = false }, 3000)
        }, 300)
      }
    } else if (status === 403) {
      ElMessage.error('权限不足')
    } else if (status === 404) {
      ElMessage.warning('请求的资源不存在')
    } else if (status !== 400) {
      // 400错误留给页面自行处理（如表单校验）
      ElMessage.error(detail || '请求失败')
    }

    return Promise.reject(error)
  }
)

// ==================== 认证接口 ====================

export const authApi = {
  login(data) { return request.post('/auth/login', data) },
  register(data) { return request.post('/auth/register', data) },
  checkUsername(username) { return request.get('/auth/check-username', { params: { username } }) },
  getMe() { return request.get('/auth/me') },
  updateProfile(data) { return request.put('/auth/profile', data) },
  changePassword(data) { return request.put('/auth/password', data) },
  verifyToken() { return request.post('/auth/verify-token') }
}

// ==================== LLM配置接口 ====================

export const llmConfigApi = {
  getProviders() { return request.get('/llm-config/providers') },
  getList() { return request.get('/llm-config/list') },
  getById(id) { return request.get(`/llm-config/${id}`) },
  create(data) { return request.post('/llm-config/create', data) },
  update(id, data) { return request.put(`/llm-config/${id}`, data) },
  delete(id) { return request.delete(`/llm-config/${id}`) },
  test(data) { return request.post('/llm-config/test', data) },
  testRaw(data) { return request.post('/llm-config/test-raw', data) }
}

// ==================== 实验题库接口 ====================

export const experimentApi = {
  getSubjects() { return request.get('/experiments/subjects') },
  getList(params) { return request.get('/experiments/list', { params }) },
  getById(id) { return request.get(`/experiments/${id}`) }
}

// ==================== 实训记录接口 ====================

export const practiceApi = {
  submit(data) { return request.post('/practice/submit', data) },
  getRecords(params) { return request.get('/practice/records', { params }) },
  getDetail(id) { return request.get(`/practice/records/${id}`) }
}

// ==================== 智能体对话接口 ====================

export const chatApi = {
  send(data) { return request.post('/chat/send', data) },
  /** 流式对话：返回 fetch Response 对象，调用方通过 ReadableStream 读取 SSE */
  async sendStream(data, signal) {
    const token = localStorage.getItem('token')
    const headers = { 'Content-Type': 'application/json' }
    if (token) headers.Authorization = `Bearer ${token}`

    // 浏览器密钥模式
    const llmKeyMode = localStorage.getItem('llm_key_mode')
    if (llmKeyMode === 'browser') {
      const apiKey = localStorage.getItem('llm_api_key')
      const baseUrl = localStorage.getItem('llm_base_url')
      const model = localStorage.getItem('llm_model')
      const provider = localStorage.getItem('llm_provider')
      if (apiKey) headers['X-LLM-Api-Key'] = apiKey
      if (baseUrl) headers['X-LLM-Base-Url'] = baseUrl
      if (model) headers['X-LLM-Model'] = model
      if (provider) headers['X-LLM-Provider'] = provider
    }

    return fetch('/api/chat/stream', {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal,
    })
  },
  getHistory(params) { return request.get('/chat/history', { params }) },
  deleteSession(sessionId) { return request.delete(`/chat/session/${sessionId}`) },
  rate(chatId, rating) { return request.post(`/chat/${chatId}/rate`, { rating }) },
  uploadFile(sessionId, formData) {
    return request.post('/chat/upload-file', formData)
  },
  clearFile(sessionId) { return request.delete(`/chat/session/${sessionId}/file`) },
}

// ==================== 教师统计接口 ====================

export const teacherApi = {
  getStats() { return request.get('/teacher/stats') }
}

// ==================== 竞赛训练接口 ====================

export const competitionApi = {
  createTask(data) { return request.post('/competition/tasks', data) },
  listTasks() { return request.get('/competition/tasks') },
  getTask(id) { return request.get(`/competition/tasks/${id}`) },
  deleteTask(id) { return request.delete(`/competition/tasks/${id}`) },
  uploadFiles(taskId, formData) {
    // axios 会自动为 FormData 设置正确的 Content-Type (含 boundary)
    return request.post(`/competition/tasks/${taskId}/upload`, formData)
  },
  listFiles(taskId) { return request.get(`/competition/tasks/${taskId}/files`) },
  runPreflight(taskId) { return request.post(`/competition/tasks/${taskId}/preflight`) },
  getPreflight(taskId) { return request.get(`/competition/tasks/${taskId}/preflight`) },
  runAnalysis(taskId) { return request.post(`/competition/tasks/${taskId}/analyze`) },
  getAnalysis(taskId) { return request.get(`/competition/tasks/${taskId}/analyze`) },
  runModelRoute(taskId) { return request.post(`/competition/tasks/${taskId}/model-route`) },
  getModelRoute(taskId) { return request.get(`/competition/tasks/${taskId}/model-route`) },
  runDataPipeline(taskId) { return request.post(`/competition/tasks/${taskId}/data-pipeline`) },
  getDataPipeline(taskId) { return request.get(`/competition/tasks/${taskId}/data-pipeline`) },
  runModelContract(taskId) { return request.post(`/competition/tasks/${taskId}/model-contract`) },
  getModelContract(taskId) { return request.get(`/competition/tasks/${taskId}/model-contract`) },

  // 图表
  getFigures(taskId) { return request.get(`/competition/tasks/${taskId}/figures`) },
  getFigureUrl(taskId, path) { return `/api/competition/tasks/${taskId}/figures/${path.split('/').pop()}` },

  // S6 证据门禁
  runEvidenceGate(taskId) { return request.post(`/competition/tasks/${taskId}/evidence-gate`) },
  getEvidenceGate(taskId) { return request.get(`/competition/tasks/${taskId}/evidence-gate`) },

  // S7 论文生成
  runPaperWriting(taskId) { return request.post(`/competition/tasks/${taskId}/paper-writing`) },
  getPaper(taskId) { return request.get(`/competition/tasks/${taskId}/paper-writing`) },

  // S7 格式检查
  runFormatCheck(taskId) { return request.post(`/competition/tasks/${taskId}/format-check`) },
  getFormatCheck(taskId) { return request.get(`/competition/tasks/${taskId}/format-check`) },
  fixPaper(taskId) { return request.post(`/competition/tasks/${taskId}/fix-paper`) },

  // 🆕 流式论文生成（SSE）
  async streamPaperWriting(taskId, signal) {
    const token = localStorage.getItem('token')
    return fetch(`/api/competition/tasks/${taskId}/paper-writing/stream?token=${token}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal,
    })
  },
}

// ==================== 代码执行接口 ====================

export const codeApi = {
  execute(data) { return request.post('/code/execute', data) },
}

// ==================== 个人中心接口 ====================

export const profileApi = {
  getRecords(params) { return request.get('/profile/records', { params }) },
  getPapers(params) { return request.get('/profile/papers', { params }) },
  getStats() { return request.get('/profile/stats') },
}

// ==================== 工作台接口 ====================

export const workspaceApi = {
  uploadData(formData) {
    return request.post('/workspace/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  listFiles() { return request.get('/workspace/files') },
  previewData(filename) { return request.get(`/workspace/preview/${filename}`) },
  cleanData(filename, operations) { return request.post(`/workspace/clean/${filename}`, operations || {}) },
  deleteFile(filename) { return request.delete(`/workspace/files/${filename}`) },
  getDemoDatasets() { return request.get('/workspace/demo-datasets') },
  loadDemoDataset(key) { return request.post(`/workspace/demo-datasets/${key}/load`) },
}

// ==================== 知识库接口 ====================

export const knowledgeApi = {
  getCategories() { return request.get('/knowledge/categories') },
  getCategory(id) { return request.get(`/knowledge/categories/${id}`) },
  search(q) { return request.get('/knowledge/search', { params: { q } }) },
  getLearningPaths() { return request.get('/knowledge/learning-paths') },
  getCases() { return request.get('/knowledge/cases') },
  getCaseDetail(id) { return request.get(`/knowledge/cases/${id}`) },
  getExams() { return request.get('/knowledge/exams') },
  getExamDetail(id) { return request.get(`/knowledge/exams/${id}`) },
}

export default request
