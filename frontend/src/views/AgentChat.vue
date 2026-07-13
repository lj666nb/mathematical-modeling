<template>
  <!--
  ============================================================
  AI智能体对话页 — 国赛视觉优化版
  v2 新增：代码块一键复制/运行 + Agent回复满意度评分
  ============================================================
  -->
  <div class="app-layout">
    <Sidebar />
    <div class="main-area" style="overflow:hidden;">
      <div class="chat-layout">
        <!-- ===== 左侧面板 ===== -->
        <div class="chat-sidebar">
          <div class="chat-sidebar-inner">
            <div class="cs-section" style="flex:1;overflow-y:auto;">
              <div class="cs-title" style="display:flex;justify-content:space-between;align-items:center;">
                <span>历史会话</span>
                <div style="display:flex;gap:4px;">
                  <el-button text size="small" @click="newSession">新建</el-button>
                </div>
              </div>
              <div v-if="sessions.length > 0" class="session-list">
                <div v-for="s in sessions" :key="s.session_id"
                  class="session-item" :class="{ active: currentSession === s.session_id }"
                  @click="loadSession(s.session_id)">
                  <span class="session-tag" :class="s.agent_type">{{ agentLabel(s.agent_type) }}</span>
                  <span class="session-time">{{ formatShort(s.last_time) }}</span>
                </div>
              </div>
              <div v-else class="cs-empty">
                <el-icon><Message /></el-icon><span>暂无会话记录</span>
              </div>
            </div>

            <div class="cs-divider"></div>
            <div class="cs-section" style="padding:12px 16px;">
              <div style="display:flex;align-items:center;gap:8px;font-size: var(--text-xs);color:var(--text-tertiary);">
                <el-icon :size="14"><Key /></el-icon>
                <span style="flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">API: {{ apiStatus }}</span>
                <el-button text size="small" @click="$router.push('/llm-config')" style="font-size: var(--text-xs);">切换</el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 中间对话主区域 ===== -->
        <div class="chat-main">
          <div class="chat-header">
            <div style="display:flex;align-items:center;gap:10px;">
              <div class="ch-agent-icon" :style="{ background: currentAgentData?.color + '15', color: currentAgentData?.color }">
                <el-icon :size="18"><component :is="currentAgentData?.icon" /></el-icon>
              </div>
              <div>
                <div class="ch-agent-name">{{ currentAgentData?.name }}</div>
                <div class="ch-agent-status" :style="{ color: currentAgentData?.color }">在线 · 随时为你解答数学建模问题</div>
              </div>
            </div>
            <el-tag size="small" effect="plain" round>
              <el-icon style="margin-right:4px;vertical-align:-2px;"><Connection /></el-icon>
              {{ apiStatusLabel }}
            </el-tag>
          </div>

          <!-- 对话消息 -->
          <div class="chat-messages" ref="msgContainer" @click="onMsgClick">
            <div v-if="messages.length === 0" class="chat-welcome">
              <div class="welcome-avatar" :style="{ background: currentAgentData?.color + '12', color: currentAgentData?.color }">
                <el-icon :size="28"><component :is="currentAgentData?.icon" /></el-icon>
              </div>
              <h3>{{ currentAgentData?.name }}</h3>
              <p class="welcome-desc">我是你的数学建模专属AI助手，可以帮你审核建模代码、生成建模练习任务、解答数学建模理论与方法疑惑</p>
              <div class="welcome-divider"></div>
              <div class="suggestions">
                <div v-for="(s, i) in (currentAgentData?.suggestions || [])" :key="s" class="sug-chip" @click="sendQuickMessage(s)">
                  <span class="sug-emoji">{{ ['💡','📊','🔍','📝'][i] || '💡' }}</span>
                  <span>{{ s }}</span>
                </div>
              </div>
            </div>

            <div v-for="(msg, idx) in messages" :key="idx" class="msg-row" :class="msg.role">
              <div v-if="msg.role === 'assistant'" class="msg-av" :style="{ background: currentAgentData?.color + '12', color: currentAgentData?.color }">
                <el-icon :size="16"><component :is="currentAgentData?.icon" /></el-icon>
              </div>
              <div class="msg-content">
                <div class="msg-sender">{{ msg.role === 'user' ? '我' : currentAgentData?.name }}</div>
                <div class="msg-bubble" :class="[msg.role, { streaming: msg._streaming }]">
                  <div class="markdown-body" v-html="renderMarkdown(msg.content, idx)"></div>
                </div>
                <!-- 操作按钮：复制 + 评分（流式输出中隐藏评分） -->
                <div class="msg-actions" v-if="msg.role === 'assistant' && !msg._streaming">
                  <el-tooltip content="复制回复"><el-button text size="small" :icon="CopyDocument" @click="copyText(msg.content)" /></el-tooltip>
                  <el-divider direction="vertical" style="height:14px;margin:0 2px;" />
                  <el-tooltip content="有用">
                    <el-button text size="small"
                      :type="msg.rating === 1 ? 'primary' : ''"
                      @click="rateMessage(msg, 1)">
                      <el-icon><Opportunity /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="没用">
                    <el-button text size="small"
                      :type="msg.rating === -1 ? 'danger' : ''"
                      @click="rateMessage(msg, -1)">
                      <el-icon><CircleClose /></el-icon>
                    </el-button>
                  </el-tooltip>
                </div>
              </div>
              <div v-if="msg.role === 'user'" class="msg-av user-av">{{ userInitial }}</div>
            </div>

            <div v-if="waiting && !abortController" class="msg-row assistant">
              <div class="msg-av" :style="{ background: currentAgentData?.color + '12', color: currentAgentData?.color }">
                <el-icon :size="16"><component :is="currentAgentData?.icon" /></el-icon>
              </div>
              <div class="msg-content">
                <div class="msg-sender">{{ currentAgentData?.name }}</div>
                <div class="msg-bubble thinking"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
              </div>
            </div>
          </div>

          <!-- 输入区 -->
          <div class="chat-input-area">
            <div v-if="pendingCode" class="code-context">
              <el-icon :size="14"><Document /></el-icon>
              <span>已附加代码 ({{ pendingCode.length }}字符)</span>
              <button class="text-link-btn" @click="pendingCode = ''">移除</button>
            </div>
            <div v-if="attachedFile" class="code-context" style="background:rgba(34,197,94,0.1);color:#16a34a;">
              <span>📄 {{ attachedFile.filename }} ({{ attachedFile.char_count }} 字符)</span>
              <button class="text-link-btn" style="color:#16a34a;" @click="clearFile">移除</button>
            </div>
            <div class="input-row">
              <el-select v-model="currentAgent" class="agent-selector" popper-class="agent-popper" @change="switchAgent(currentAgent)">
                <el-option v-for="agent in agents" :key="agent.type" :value="agent.type" :label="agent.name">
                  <div class="agent-option">
                    <span class="agent-option-dot" :style="{ background: agent.color }"></span>
                    <span>{{ agent.name }}</span>
                  </div>
                </el-option>
              </el-select>
              <input ref="fileInput" type="file" accept=".pdf" style="display:none" @change="onFileSelected" />
              <el-button class="attach-btn" :loading="uploading" @click="fileInput.click()" title="上传 PDF 文件">
                <el-icon :size="18"><Paperclip /></el-icon>
              </el-button>
              <el-input v-model="inputMessage" type="textarea" :rows="2" placeholder="输入你的数学建模问题... (Enter发送, Shift+Enter换行)" @keydown.enter.exact="sendMessage" resize="none" />
              <el-button v-if="waiting" type="danger" @click="stopStreaming" class="send-btn stop-btn" round title="停止生成">
                <span class="stop-icon">■</span>
              </el-button>
              <el-button v-else type="primary" @click="sendMessage" class="send-btn" round>
                <el-icon :size="20"><Promotion /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 代码运行结果弹窗 -->
    <el-dialog v-model="runDialogVisible" title="代码运行结果" width="600px" center :close-on-click-modal="false">
      <div v-if="runDialogLoading" style="text-align:center;padding:20px;">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <p style="margin-top:8px;color:var(--text-secondary);">代码执行中...</p>
      </div>
      <template v-else-if="runDialogResult">
        <div class="run-dialog-meta">
          <el-tag :type="runDialogResult.success ? 'success' : 'danger'" size="small" effect="dark" round>
            {{ runDialogResult.success ? '执行成功' : '执行失败 (code=' + runDialogResult.return_code + ')' }}
          </el-tag>
          <span style="font-size: var(--text-xs);color:var(--text-tertiary);">{{ runDialogResult.execution_time_ms }}ms</span>
        </div>
        <div v-if="runDialogResult.stdout" style="margin-top:10px;">
          <div style="font-size: var(--text-xs);font-weight:600;color:var(--text-secondary);margin-bottom:4px;">STDOUT</div>
          <pre class="run-dialog-stdout">{{ runDialogResult.stdout }}</pre>
        </div>
        <div v-if="runDialogResult.stderr" style="margin-top:10px;">
          <div style="font-size: var(--text-xs);font-weight:600;color:var(--danger);margin-bottom:4px;">STDERR</div>
          <pre class="run-dialog-stderr">{{ runDialogResult.stderr }}</pre>
        </div>
      </template>
      <template #footer>
        <el-button @click="runDialogVisible = false" round>关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { chatApi, codeApi } from '../api'
import Sidebar from '../components/Sidebar.vue'
import { EditPen, TrendCharts, QuestionFilled, Promotion, Connection, Document, Message, Key, CopyDocument, Opportunity, CircleClose, Loading, DataAnalysis, Paperclip, ChatDotRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import r from 'highlight.js/lib/languages/r'
import julia from 'highlight.js/lib/languages/julia'
import 'highlight.js/styles/github-dark.min.css'
import { renderAllMath } from '../composables/useKatex'

// 注册代码高亮语言
hljs.registerLanguage('python', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('r', r)
hljs.registerLanguage('julia', julia)

const route = useRoute(); const router = useRouter(); const userStore = useUserStore()
const currentAgent = ref('general'); const currentSession = ref(null)
const messages = ref([]); const inputMessage = ref(''); const waiting = ref(false)
const sessions = ref([]); const pendingCode = ref(''); const msgContainer = ref(null)

// PDF 文件上传
const attachedFile = ref(null)  // { filename, char_count }
const uploading = ref(false)
const fileInput = ref(null)

// 代码运行弹窗
const runDialogVisible = ref(false)
const runDialogLoading = ref(false)
const runDialogResult = ref(null)

// 流式输出控制
const abortController = ref(null)

const agents = [
  { type:'general', name:'通用问答', desc:'解答数学建模各类问题', icon:ChatDotRound, color:'#165DFF',
    suggestions:['什么是线性规划的标准形式？','如何选择评价模型？','介绍常用预测模型的优缺点','ARIMA模型的建模步骤是什么？'] },
  { type:'code-review', name:'建模辅导Agent', desc:'审核Python建模代码的正确性与科学性', icon:EditPen, color:'#165DFF',
    suggestions:['检查这段建模代码的问题','线性规划求解是否正确？','如何改进这个模型的灵敏度？','请分析代码的数值稳定性'] },
  { type:'training-guide', name:'实训引导Agent', desc:'生成阶梯式数学建模练习任务', icon:TrendCharts, color:'#00B42A',
    suggestions:['练习优化模型相关实验','推荐预测模型学习路径','评价模型入门练习','微分方程建模实践'] },
  { type:'qa', name:'建模答疑Agent', desc:'解答数学建模理论与方法疑惑', icon:QuestionFilled, color:'#FF7D00',
    suggestions:['AHP和TOPSIS的区别？','ARIMA模型如何选择参数？','什么是Pareto最优解？','解释SIR传染病模型的原理'] },
  { type:'paper-review', name:'论文评审Agent', desc:'评审建模论文结构与内容，给出专业改进建议', icon:DataAnalysis, color:'#9B59B6',
    suggestions:['帮我评审这篇建模论文','论文的模型假设是否合理？','结果分析部分需要如何改进？','如何提升论文的创新性？'] },
]

const currentAgentData = computed(() => agents.find(a => a.type === currentAgent.value))
const userInitial = computed(() => (userStore.user?.display_name || userStore.user?.username || 'U').charAt(0).toUpperCase())
const apiStatus = computed(() => {
  if (localStorage.getItem('llm_key_mode') === 'browser' && localStorage.getItem('llm_api_key')) return '浏览器密钥'
  return '服务端配置'
})
const apiStatusLabel = computed(() => `当前API: ${apiStatus.value}`)

function agentLabel(t) { const m={'general':'通用问答','code-review':'建模辅导','training-guide':'实训引导','qa':'建模答疑','paper-review':'论文评审'}; return m[t]||t }
function formatShort(t) {
  if(!t) return ''; const d=new Date(t); const n=new Date()
  if(d.toDateString()===n.toDateString()) return d.toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})
  return d.toLocaleDateString('zh-CN',{month:'short',day:'numeric'})
}

// 增强版 Markdown 渲染：marked + KaTeX + highlight.js
function renderMarkdown(text, msgIdx) {
  if (!text) return ''

  // Step 1: 提取代码块 → 语法高亮 → 替换为占位符
  const codeBlocks = []
  let processed = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const idx = codeBlocks.length
    const blockId = `cb-${msgIdx}-${idx}`
    const cleanCode = code.trimEnd()
    let highlighted
    try {
      if (lang && hljs.getLanguage(lang)) {
        highlighted = hljs.highlight(cleanCode, { language: lang }).value
      } else {
        highlighted = hljs.highlightAuto(cleanCode).value
      }
    } catch {
      highlighted = cleanCode.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    }

    const codeHtml = `<div class="cb-wrapper" data-block-id="${blockId}">
      <div class="cb-toolbar">
        <span class="cb-lang">${lang || 'code'}</span>
        <span class="cb-btns">
          <button class="cb-btn cb-copy" data-action="copy" data-block="${blockId}" title="复制代码"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg> 复制</button>
          <button class="cb-btn cb-run" data-action="run" data-block="${blockId}" title="运行代码"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg> 运行</button>
        </span>
      </div>
      <pre><code>${highlighted}</code></pre>
      <div class="cb-result" data-result="${blockId}" style="display:none;"></div>
    </div>`
    codeBlocks.push(codeHtml)
    return `\n%%CB_${idx}%%\n`
  })

  // Step 2: 渲染 LaTeX 公式 ($...$ 和 $$...$$)
  processed = renderAllMath(processed)

  // Step 3: 渲染 Markdown（marked：表格/列表/引用/加粗/斜体等）
  let html = marked.parse(processed, { breaks: false, gfm: true })

  // Step 4: 替换占位符为高亮代码块
  codeBlocks.forEach((codeHtml, idx) => {
    // marked 会把单独一行的占位符包在 <p> 里
    html = html.replace(`<p>%%CB_${idx}%%</p>`, codeHtml)
    html = html.replace(`%%CB_${idx}%%`, codeHtml)
  })

  return html
}

// 代码块按钮存储
const codeBlockStore = {}

// 消息区域点击事件委托
function onMsgClick(e) {
  const btn = e.target.closest('.cb-btn')
  if (!btn) return
  const action = btn.dataset.action
  const blockId = btn.dataset.block
  if (!blockId) return

  // 找到父级 code-block-wrapper
  const wrapper = btn.closest('.cb-wrapper')
  if (!wrapper) return
  const codeEl = wrapper.querySelector('code')
  const code = codeEl ? (codeEl.textContent || '') : ''

  if (action === 'copy') {
    copyCodeBlock(code, btn)
  } else if (action === 'run') {
    runCodeBlock(code, blockId, wrapper)
  }
}

function copyText(text) { try { navigator.clipboard.writeText(text); ElMessage.success('已复制') } catch(e){} }

function copyCodeBlock(code, btn) {
  try {
    navigator.clipboard.writeText(code)
    const orig = btn.innerHTML
    btn.innerHTML = '✅ 已复制'
    btn.classList.add('cb-copied')
    setTimeout(() => {
      btn.innerHTML = orig
      btn.classList.remove('cb-copied')
    }, 1500)
  } catch(e) {}
}

async function runCodeBlock(code, blockId, wrapper) {
  const resultEl = wrapper.querySelector('.cb-result')
  const runBtn = wrapper.querySelector('.cb-run')

  // 显示加载态
  if (resultEl) { resultEl.style.display = 'block'; resultEl.innerHTML = '<span style="color:var(--text-secondary);">⏳ 执行中...</span>' }
  if (runBtn) runBtn.disabled = true

  try {
    const res = await codeApi.execute({ code, timeout: 30 })
    if (resultEl) {
      const success = res.success
      resultEl.style.display = 'block'
      resultEl.innerHTML = `
        <div class="cb-result-meta">
          <span class="cb-result-status ${success ? 'success' : 'fail'}">${success ? '✅ 执行成功' : '❌ 执行失败 (code=' + res.return_code + ')'}</span>
          <span class="cb-result-time">${res.execution_time_ms}ms</span>
        </div>
        ${res.stdout ? `<div class="cb-result-label">STDOUT</div><pre class="cb-result-stdout">${escapeHtml(res.stdout)}</pre>` : ''}
        ${res.stderr ? `<div class="cb-result-label" style="color:var(--danger);">STDERR</div><pre class="cb-result-stderr">${escapeHtml(res.stderr)}</pre>` : ''}
        ${res.truncated ? '<div style="font-size: var(--text-xs);color:var(--text-tertiary);margin-top:4px;">⚠️ 输出已截断</div>' : ''}
      `
    }
  } catch(e) {
    if (resultEl) {
      resultEl.style.display = 'block'
      resultEl.innerHTML = `<span style="color:var(--danger);">❌ 执行异常: ${escapeHtml(e?.response?.data?.detail || e.message || '未知错误')}</span>`
    }
  } finally {
    if (runBtn) runBtn.disabled = false
  }
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')
}

// 评分
async function rateMessage(msg, rating) {
  if (!msg.chat_id) {
    ElMessage.warning('该消息暂不支持评分')
    return
  }
  // 如果点击同一个评分，则取消
  const newRating = msg.rating === rating ? 0 : rating
  try {
    await chatApi.rate(msg.chat_id, newRating)
    msg.rating = newRating
    ElMessage.success(newRating === 1 ? '感谢反馈 👍' : newRating === -1 ? '感谢反馈，我们会改进 🙏' : '已取消评分')
  } catch(e) {
    ElMessage.error('评分失败')
  }
}

// Agent / Session 切换
function switchAgent(t) { stopStreaming(); currentAgent.value=t; currentSession.value=null; messages.value=[]; attachedFile.value=null; resetScroll(); loadSessions() }
function newSession() { stopStreaming(); currentSession.value=null; messages.value=[]; attachedFile.value=null; resetScroll() }

function resetScroll() {
  if (msgContainer.value) msgContainer.value.scrollTop = 0
}

async function loadSessions() {
  try { const res=await chatApi.getHistory({agent_type:currentAgent.value,page:1,page_size:50}); sessions.value=res.sessions||[] }
  catch(e) {}
}
async function loadSession(sid) {
  currentSession.value=sid
  try {
    const res=await chatApi.getHistory({session_id:sid,page:1,page_size:100})
    const items=[]
    for(const m of (res.history||[])) {
      items.push({role:'user',content:m.user_message})
      // 解析 metadata 中的 rating
      let rating = 0
      try {
        const meta = typeof m.extra_metadata === 'string' ? JSON.parse(m.extra_metadata || '{}') : (m.extra_metadata || {})
        rating = meta.rating || 0
      } catch(e) {}
      items.push({role:'assistant',content:m.agent_message, chat_id: m.id, rating})
    }
    const merged=[]; for(const item of items) { if(merged.length>0&&merged[merged.length-1].role===item.role) merged[merged.length-1].content=item.content; else merged.push(item) }
    messages.value=merged; await nextTick(); scrollToBottom()
  } catch(e) {}
}
async function sendMessage() {
  const msg = inputMessage.value.trim()
  if (!msg || waiting.value) return
  if (route.query.code && !pendingCode.value) pendingCode.value = route.query.code

  // 停止之前的流式输出
  if (abortController.value) abortController.value.abort()

  messages.value.push({ role: 'user', content: msg })
  inputMessage.value = ''
  waiting.value = true

  const ctrl = new AbortController()
  abortController.value = ctrl

  // 插入占位消息
  const assistIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', rating: 0, _streaming: true })

  // 立即滚动到底部，确保用户消息可见
  await nextTick()
  scrollToBottom()

  try {
    const response = await chatApi.sendStream(
      {
        agent_type: currentAgent.value,
        message: msg,
        session_id: currentSession.value || undefined,
        code_context: pendingCode.value || undefined,
      },
      ctrl.signal
    )

    if (!response.ok) {
      const errText = await response.text()
      throw new Error(errText || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          const am = messages.value[assistIdx]
          if (!am) continue

          if (data.type === 'chunk') {
            am.content += data.content
          } else if (data.type === 'done') {
            am.content = data.content
            am.chat_id = data.chat_id
            am._streaming = false
            if (data.session_id) currentSession.value = data.session_id
          } else if (data.type === 'error') {
            am.content = data.content
            am._streaming = false
          }
        } catch { /* skip malformed JSON */ }
      }

      await nextTick()
      scrollToBottomIfNear()
    }
  } catch (e) {
    const am = messages.value[assistIdx]
    if (e.name === 'AbortError') {
      if (am) {
        am._streaming = false
        if (!am.content) am.content = '（已停止生成）'
      }
    } else {
      if (am && !am.content) {
        am.content = '抱歉，AI服务暂不可用，请检查您的API配置。'
        am._streaming = false
      }
    }
  } finally {
    waiting.value = false
    abortController.value = null
    pendingCode.value = ''
    await nextTick()
    scrollToBottom()
    loadSessions()
  }
}

function stopStreaming() {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  waiting.value = false
}

function scrollToBottomIfNear() {
  if (!msgContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = msgContainer.value
  if (scrollHeight - scrollTop - clientHeight < 150) {
    msgContainer.value.scrollTop = scrollHeight
  }
}

function sendQuickMessage(t) { inputMessage.value = t; sendMessage() }
function scrollToBottom() { if(msgContainer.value) msgContainer.value.scrollTop=msgContainer.value.scrollHeight }

// PDF 文件上传
async function onFileSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  uploading.value = true
  try {
    const sid = currentSession.value || crypto.randomUUID()
    const fd = new FormData()
    fd.append('session_id', sid)
    fd.append('file', file)
    const res = await chatApi.uploadFile(sid, fd)
    attachedFile.value = { filename: res.filename, char_count: res.char_count }
    if (!currentSession.value) currentSession.value = res.session_id
    ElMessage.success(`已上传: ${res.filename} (${res.char_count} 字符)`)
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '文件上传失败')
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function clearFile() {
  if (currentSession.value) {
    try { await chatApi.clearFile(currentSession.value) } catch {}
  }
  attachedFile.value = null
  ElMessage.info('文件已移除')
}

onMounted(async () => {
  if(route.query.agent) currentAgent.value=route.query.agent
  if(route.query.code) { pendingCode.value=route.query.code; if(currentAgent.value==='code-review') inputMessage.value='请检查这段代码的问题' }
  await loadSessions()
})

onUnmounted(() => {
  // 清理流式连接
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
})
</script>

<style scoped lang="scss">
.chat-layout { display:flex; height:100vh; }
.chat-sidebar { width:240px; background:var(--bg-card); border-right:1px solid var(--border-light); display:flex; flex-direction:column; }
.chat-sidebar-inner { display:flex; flex-direction:column; height:100%; }
.cs-section { padding:16px 14px 8px; }
.cs-title { font-size:var(--text-xs); font-weight:700; color:var(--text-secondary); margin-bottom:10px; text-transform:uppercase; letter-spacing:0.04em; display:flex; align-items:center; gap:6px; }
.cs-empty { display:flex; flex-direction:column; align-items:center; gap:8px; padding:30px 0; color:var(--text-tertiary); font-size:var(--text-xs); }
.cs-divider { height:1px; background:var(--border-light); margin:4px 14px; opacity:0.6; }
.agent-card { display:flex; align-items:center; gap:10px; padding:10px 12px; margin-bottom:4px; border-radius:8px; cursor:pointer; transition:all 0.2s; position:relative; }
.agent-card:hover { background:var(--bg-hover); }
.agent-card.active { background:var(--primary-light); }
.agent-avatar { width:36px; height:36px; border-radius:8px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.agent-info { flex:1; min-width:0; }
.agent-name { font-size: var(--text-sm); font-weight:600; color:var(--text-primary); }
.agent-desc { font-size: var(--text-xs); color:var(--text-tertiary); margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.online-dot { position:absolute; right:10px; top:50%; transform:translateY(-50%); width:8px; height:8px; border-radius:50%; opacity:0.7; }
.session-list { display:flex; flex-direction:column; gap:2px; }
.session-item { display:flex; justify-content:space-between; align-items:center; padding:9px 12px; border-radius:8px; cursor:pointer; transition:all 0.2s var(--ease-out); }
.session-item:hover { background:var(--bg-hover); }
.session-item.active { background:var(--color-gold-pale); }
.session-tag { font-size:var(--text-xs); font-weight:500; padding:2px 8px; border-radius:4px; }
.session-tag.general { background:rgba(22,93,255,0.08); color:#165DFF; }
.session-tag.code-review { background:rgba(22,93,255,0.10); color:#165DFF; }
.session-tag.training-guide { background:rgba(0,180,42,0.10); color:#00B42A; }
.session-tag.qa { background:rgba(255,125,0,0.10); color:#FF7D00; }
.session-tag.paper-review { background:rgba(155,89,182,0.10); color:#9B59B6; }
.session-time { font-size:11px; color:var(--text-tertiary); }

.chat-main { flex:1; display:flex; flex-direction:column; background:var(--bg-primary); }
.chat-header { display:flex; align-items:center; justify-content:space-between; padding:14px 24px; background:rgba(255,255,255,0.7); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); border-bottom:1px solid rgba(0,0,0,0.04); box-shadow:0 1px 8px rgba(0,0,0,0.03); }
.ch-agent-icon { width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.ch-agent-name { font-size:var(--text-sm); font-weight:700; color:var(--text-primary); }
.ch-agent-status { font-size:var(--text-xs); display:flex; align-items:center; gap:6px; }
.ch-agent-status::before { content:''; width:7px; height:7px; border-radius:50%; background:currentColor; animation:agent-pulse 2s ease-in-out infinite; }
@keyframes agent-pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.chat-messages { flex:1; overflow-y:auto; padding:24px;
  background:
    radial-gradient(ellipse at 50% 0%, rgba(22,93,255,0.03) 0%, transparent 60%),
    linear-gradient(180deg, #F7F8FA 0%, #F0F2F5 100%);
}
.chat-welcome { text-align:center; padding:80px 20px 60px; }
.welcome-avatar { width:80px; height:80px; border-radius:20px; display:flex; align-items:center; justify-content:center; margin:0 auto 20px; box-shadow: 0 8px 32px rgba(22,93,255,0.12); transition: transform 0.3s var(--ease-out); }
.welcome-avatar:hover { transform: translateY(-2px); }
.chat-welcome h3 { font-size:var(--text-xl); font-weight:700; margin-bottom:8px; color:var(--text-primary); }
.welcome-desc { color:var(--text-secondary); font-size:var(--text-sm); margin-bottom:16px; max-width:480px; margin-left:auto; margin-right:auto; line-height:1.7; }
.welcome-divider { width:48px; height:3px; background:var(--color-gold); border-radius:2px; margin:0 auto 24px; opacity:0.5; }
.suggestions { display:flex; flex-wrap:wrap; gap:10px; justify-content:center; max-width:600px; margin:0 auto; }
.sug-chip { display:flex; align-items:center; gap:8px; padding:10px 18px; background:var(--bg-card); border:1px solid var(--border-light); border-radius:24px; font-size:var(--text-sm); cursor:pointer; transition:all 0.25s var(--ease-out); box-shadow:0 1px 2px rgba(0,0,0,0.02); }
.sug-chip:hover { background:var(--color-gold-pale); border-color:var(--color-gold); transform:translateY(-2px); box-shadow:0 4px 16px rgba(22,93,255,0.1); }
.sug-emoji { font-size:16px; line-height:1; }
.msg-row { display:flex; gap:12px; margin-bottom:24px; align-items:flex-start; }
.msg-row.user { flex-direction:row-reverse; }
.msg-av { width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:var(--text-sm); font-weight:600; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.user-av { background:linear-gradient(135deg, #165DFF, #3C7EFF); color:#fff; box-shadow:0 2px 12px rgba(22,93,255,0.3); }
.msg-content { max-width:68%; }
.msg-sender { font-size:var(--text-xs); color:var(--text-tertiary); margin-bottom:4px; font-weight:500; }
.msg-row.user .msg-sender { text-align:right; }
.msg-bubble { padding:14px 18px; border-radius:18px; font-size:var(--text-sm); line-height:1.7; background:var(--bg-card); border:1px solid var(--border-light); box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.msg-bubble.user { background:linear-gradient(135deg, #165DFF 0%, #3C7EFF 100%); color:#fff; border-color:transparent; box-shadow:0 2px 12px rgba(22,93,255,0.25); }
.msg-actions { margin-top:4px; display:flex; gap:4px; align-items:center; opacity:0; transition:opacity 0.2s; }
.msg-row:hover .msg-actions { opacity:1; }
.msg-bubble.thinking { padding:16px 20px; }
.dot { width:7px; height:7px; border-radius:50%; background:var(--text-tertiary); animation:dot-bounce 1.4s infinite; display:inline-block; margin:0 3px; }
.dot:nth-child(2) { animation-delay:0.2s; } .dot:nth-child(3) { animation-delay:0.4s; }
@keyframes dot-bounce { 0%,80%,100%{opacity:0.2;transform:scale(0.8)} 40%{opacity:1;transform:scale(1)} }
.markdown-body { line-height:1.8; color:inherit; word-break:break-word; }
.markdown-body p { margin-bottom:var(--space-3); }
.markdown-body p:last-child { margin-bottom:0; }
.markdown-body pre { background:#F2F3F8; padding:12px 16px; border-radius:0 0 10px 10px; overflow-x:auto; margin:0; font-size:var(--text-sm); }
.markdown-body code { background:rgba(0,0,0,0.05); padding:2px 7px; border-radius:4px; font-size:0.9em; font-family:var(--font-mono); }
.msg-bubble.user code { background:rgba(255,255,255,0.15); }
.msg-bubble.user .markdown-body { color:rgba(255,255,255,0.95); }
.msg-bubble.user .markdown-body a { color:#fff; text-decoration:underline; }
.msg-bubble.user .markdown-body blockquote { background:rgba(255,255,255,0.08); border-left-color:rgba(255,255,255,0.4); color:rgba(255,255,255,0.8); }
.msg-bubble.user .markdown-body table th { background:rgba(255,255,255,0.1); }
.msg-bubble.user .markdown-body table td { border-color:rgba(255,255,255,0.15); }
.msg-bubble.user .markdown-body h2 { border-bottom-color:rgba(255,255,255,0.2); }

// —— marked 生成的 Markdown 元素样式 ——
.markdown-body {
  h1 { font-size:var(--text-lg); font-weight:700; margin:var(--space-5) 0 var(--space-3); }
  h2 { font-size:var(--text-md); font-weight:700; margin:var(--space-4) 0 var(--space-2); padding-bottom:var(--space-2); border-bottom:1px solid var(--border-light); }
  h3 { font-size:var(--text-sm); font-weight:600; margin:var(--space-3) 0 var(--space-2); }
  h4 { font-size:var(--text-sm); font-weight:600; margin:var(--space-3) 0 var(--space-1); }

  ul, ol { padding-left:var(--space-6); margin:var(--space-2) 0; }
  li { margin-bottom:var(--space-1); }
  li > ul, li > ol { margin-top:var(--space-1); }

  blockquote {
    margin:var(--space-3) 0;
    padding:var(--space-2) var(--space-4);
    border-left:3px solid var(--primary);
    background:var(--primary-light);
    border-radius:0 var(--radius-sm) var(--radius-sm) 0;
    color:var(--text-secondary);
  }

  table {
    width:100%; border-collapse:collapse; margin:var(--space-3) 0; font-size:var(--text-sm);
    th { background:var(--bg-hover); font-weight:600; text-align:left; padding:var(--space-2) var(--space-3); border:1px solid var(--border-light); }
    td { padding:var(--space-2) var(--space-3); border:1px solid var(--border-light); }
    tr:nth-child(even) td { background:rgba(0,0,0,0.015); }
  }

  hr { border:none; border-top:1px solid var(--border-light); margin:var(--space-4) 0; }

  a { color:var(--primary); text-decoration:underline; }
  img { max-width:100%; border-radius:var(--radius-md); }

  // KaTeX 公式块
  .katex-display { overflow-x:auto; overflow-y:hidden; padding:var(--space-1) 0; }
  .katex { font-size:1.05em; }
}

// highlight.js 暗色主题适配 cb-wrapper
.cb-wrapper pre {
  background: #0d1117;
  padding: 12px 16px;
  border-radius: 0 0 8px 8px;
  margin: 0;
}

.msg-bubble.user .cb-wrapper pre {
  background: rgba(0,0,0,0.2);
}
.msg-bubble.user .cb-toolbar {
  background: rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.7);
}
.msg-bubble.user .cb-lang { color: rgba(255,255,255,0.6); }
.msg-bubble.user .cb-btn { color: rgba(255,255,255,0.6); }
.msg-bubble.user .cb-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }

// —— 流式输出闪烁光标 ——
.msg-bubble.streaming .markdown-body::after {
  content: '';
  display: inline-block;
  width: 8px;
  height: 18px;
  background: currentColor;
  opacity: 0.7;
  margin-left: 2px;
  vertical-align: text-bottom;
  border-radius: 1px;
  animation: stream-blink 0.8s ease-in-out infinite;
}
@keyframes stream-blink {
  0%, 50% { opacity: 0.7; }
  51%, 100% { opacity: 0; }
}
.chat-input-area { padding:16px 24px 20px; background:rgba(255,255,255,0.75); backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px); border-top:1px solid rgba(0,0,0,0.05); box-shadow:0 -2px 16px rgba(0,0,0,0.04); }

// —— Agent 选择器（输入栏左侧） ——
.agent-selector {
  width: 150px;
  flex-shrink: 0;
  height: 46px;
}
.agent-selector :deep(.el-input__wrapper) {
  height: 46px;
  border-radius:14px;
  background:var(--bg-primary);
  border-color:var(--border-light);
  box-shadow:none;
  transition:all 0.2s;
}
.agent-selector :deep(.el-input__wrapper:hover) {
  border-color:var(--color-gold);
}
.agent-selector :deep(.el-input__wrapper.is-focus) {
  border-color:var(--color-gold);
  box-shadow:0 0 0 2px var(--color-gold-subtle);
}
.agent-option {
  display: flex;
  align-items: center;
  gap: 8px;
}
.agent-option-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.input-row { display:flex; gap:10px; align-items:flex-end;
  background:var(--bg-primary); padding:8px; border-radius:18px;
  border:1px solid var(--border-light); transition:border-color 0.2s;
}
.input-row:focus-within { border-color:var(--color-gold); box-shadow:0 0 0 3px var(--color-gold-subtle); }
.input-row .el-textarea { flex:1; }
.input-row :deep(.el-textarea__inner) {
  background:transparent; border:none; box-shadow:none; padding:6px 4px;
  font-size:var(--text-sm); line-height:1.5;
}
.input-row :deep(.el-textarea__inner:focus) { box-shadow:none; }
.attach-btn { height:40px; width:40px; flex-shrink:0; border:1px solid var(--border-light); color:var(--text-secondary); background:transparent; border-radius:12px; margin-bottom:3px; }
.attach-btn:hover { border-color:var(--primary); color:var(--primary); background:var(--color-gold-subtle); }
.send-btn { height:40px; width:40px; flex-shrink:0; border-radius:12px; margin-bottom:3px;
  background:linear-gradient(135deg, #165DFF, #3C7EFF); border:none;
  box-shadow:0 2px 8px rgba(22,93,255,0.3); transition:all 0.2s;
}
.send-btn:hover { box-shadow:0 4px 16px rgba(22,93,255,0.4); transform:translateY(-1px); }
.stop-btn { background:var(--danger) !important; box-shadow:0 2px 8px rgba(245,63,63,0.3) !important; }
.stop-btn .stop-icon { font-size:14px; line-height:1; font-weight:700; }
.code-context { display:flex; align-items:center; gap:6px; padding:6px 12px; background:var(--primary-light); border-radius:8px; margin-bottom:10px; font-size:var(--text-xs); color:var(--primary); }
.text-link-btn { color:var(--primary); font-size:var(--text-xs); cursor:pointer; background:none; border:none; padding:0; font-weight:500; }
.text-link-btn:hover { text-decoration:underline; }
.text-link-btn { color:var(--primary); font-size: var(--text-xs); cursor:pointer; background:none; border:none; padding:0; font-weight:500; }
.text-link-btn:hover { text-decoration:underline; }

// ===== 代码块增强样式 =====
.cb-wrapper {
  margin: 12px 0;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  overflow: hidden;
  box-shadow:0 1px 4px rgba(0,0,0,0.04);
}
.cb-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: #F2F3F5;
  font-size:var(--text-xs);
  border-bottom:1px solid var(--border-light);
}
.cb-lang {
  color: var(--text-secondary);
  font-weight: 500;
  text-transform: uppercase;
}
.cb-btns {
  display: flex;
  gap: 2px;
}
.cb-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 10px;
  border: none;
  border-radius: 6px;
  font-size:var(--text-xs);
  cursor: pointer;
  color: var(--text-secondary);
  background: transparent;
  transition: all 0.2s;
  font-family: inherit;
}
.cb-btn:hover {
  background: rgba(0,0,0,0.06);
  color: var(--text-primary);
}
.cb-btn.cb-run:hover {
  color: var(--success);
}
.cb-btn.cb-copied {
  color: var(--success);
}
// 运行结果内联显示
.cb-result {
  padding: 8px 12px;
  border-top: 1px solid var(--border-light);
  background: #1e1e1e;
  font-size: var(--text-xs);
  line-height: 1.5;
}
.cb-result-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.cb-result-status {
  font-size: var(--text-xs);
  font-weight: 600;
  &.success { color: #4ec9b0; }
  &.fail { color: #f14c4c; }
}
.cb-result-time {
  font-size: var(--text-xs);
  color: #888;
}
.cb-result-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  color: #888;
  margin: 4px 0 2px;
}
.cb-result-stdout {
  color: #d4d4d4;
  white-space: pre-wrap;
  margin: 0;
  max-height: 250px;
  overflow-y: auto;
  font-family: var(--font-mono);
}
.cb-result-stderr {
  color: #f14c4c;
  white-space: pre-wrap;
  margin: 0;
  max-height: 150px;
  overflow-y: auto;
  font-family: var(--font-mono);
}

// ===== 代码运行弹窗 =====
.run-dialog-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.run-dialog-stdout {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 8px;
  font-size: var(--text-xs);
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  max-height: 350px;
  overflow-y: auto;
  font-family: var(--font-mono);
}
.run-dialog-stderr {
  background: var(--danger-bg);
  color: var(--danger);
  padding: 12px;
  border-radius: 8px;
  font-size: var(--text-xs);
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
  font-family: var(--font-mono);
}
</style>
