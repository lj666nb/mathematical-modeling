<template>
  <!--
  ============================================================
  在线编程页 - 国赛视觉优化版
  优化要点：
    ① 顶部操作栏扩容（模板库+保存草稿）
    ② 实验题目卡片美化（难度星级+知识点分段）
    ③ 深色代码编辑区+行数显示
    ④ 结果面板分栏+得分三色状态
    ⑤ 底部快捷工具条（跳转AI纠错/复制/清空）
  ============================================================
  -->
  <div class="app-layout">
    <Sidebar />
    <div class="main-area" style="overflow:hidden;">
      <div class="code-layout">
        <!-- 顶部工具栏 -->
        <div class="code-toolbar">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <el-select v-model="selectedExperimentId" placeholder="选择建模实验" style="width:280px;" @change="onExperimentChange" clearable>
              <el-option v-for="exp in allExperiments" :key="exp.id" :label="`${exp.subject} - ${exp.title}`" :value="exp.id" />
            </el-select>
            <el-select v-model="language" style="width:100px;">
              <el-option label="Python" value="python" /><el-option label="MATLAB" value="matlab" />
            </el-select>
            <el-button text type="primary" size="small" :icon="Document">模板库</el-button>
          </div>
          <div style="display:flex;gap:8px;">
            <el-button size="small" :icon="FolderOpened" @click="saveDraft" :disabled="!code">保存草稿</el-button>
            <el-button type="primary" :loading="running" :disabled="!code" @click="runCode" round>
              <el-icon><VideoPlay /></el-icon> 运行
            </el-button>
            <el-button type="success" :loading="submitting" :disabled="!selectedExperimentId||!code" @click="handleSubmit" round>
              <el-icon><Upload /></el-icon> 提交评估
            </el-button>
            <el-button :disabled="!code" @click="askCodeReview" round>AI辅导</el-button>
          </div>
        </div>

        <div class="code-body">
          <!-- 左侧：实验信息+编辑器 -->
          <div class="code-left">
            <!-- 实验信息卡片 -->
            <div v-if="currentExperiment" class="exp-info-card">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <el-tag :type="subjectTagType(currentExperiment.subject)||'info'" effect="plain" size="small" round>{{ currentExperiment.subject }}</el-tag>
                <span style="display:flex;gap:2px;">
                  <el-icon v-for="i in 5" :key="i" :size="12" :color="i<=currentExperiment.difficulty?'#FF7D00':'#E5E6EB'">
                    <StarFilled v-if="i<=currentExperiment.difficulty" /><Star v-else />
                  </el-icon>
                </span>
                <span style="font-size: var(--text-xs);color:var(--text-tertiary);margin-left:4px;">难度 {{ currentExperiment.difficulty }}/5</span>
              </div>
              <h3 class="exp-info-title">{{ currentExperiment.title }}</h3>
              <p class="exp-info-desc">{{ currentExperiment.description }}</p>
            </div>
            <div v-else class="exp-info-card" style="text-align:center;padding:40px;">
              <div class="app-empty" style="padding:0;"><el-icon :size="24" style="color:var(--text-tertiary);"><Edit /></el-icon><p class="app-empty-text" style="margin-top:8px;">请从上方选择一个建模实验</p></div>
            </div>

            <!-- 代码编辑器 -->
            <div class="editor-container">
              <div class="editor-header">
                <span><el-icon :size="14"><Document /></el-icon> {{ language === 'python' ? 'model.py' : 'model.m' }}</span>
                <div style="display:flex;gap:6px;">
                  <el-tooltip content="格式化代码"><el-button text size="small" :icon="MagicStick" @click="formatCode" :disabled="!code" /></el-tooltip>
                  <el-tooltip content="清空"><el-button text size="small" :icon="Delete" @click="code=''" :disabled="!code" /></el-tooltip>
                </div>
              </div>
              <textarea v-model="code" class="code-textarea" :placeholder="codePlaceholder" spellcheck="false"></textarea>
              <div class="editor-footer">
                <span style="font-size: var(--text-xs);color:var(--text-tertiary,#C9CDD4);">行数: {{ code.split('\n').length }} | 字符: {{ code.length }}</span>
                <div style="display:flex;gap:8px;">
                  <button class="toolbar-btn" @click="askCodeReview"><el-icon :size="13"><ChatDotSquare /></el-icon> AI辅导</button>
                  <button class="toolbar-btn" @click="copyCode"><el-icon :size="13"><CopyDocument /></el-icon> 复制</button>
                  <button class="toolbar-btn" @click="code=''" style="color:var(--text-tertiary,#C9CDD4);"><el-icon :size="13"><Delete /></el-icon> 清空</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧：结果面板 -->
          <div class="code-right">
            <el-tabs v-model="activeTab" class="result-tabs">
              <el-tab-pane label="建模结果" name="result">
                <div v-if="!lastResult" class="app-empty" style="padding:50px 0;">
                  <div class="app-empty-icon" style="width:56px;height:56px;"><el-icon :size="22"><Tickets /></el-icon></div>
                  <p class="app-empty-text">提交建模代码后将显示AI评估结果</p>
                  <p class="app-empty-hint">包括建模质量评分、错误分析和改进建议</p>
                </div>
                <div v-else class="result-body">
                  <div class="result-hero" :class="scoreClass(lastResult.score)">
                    <div class="result-hero-score">{{ lastResult.score || '-' }}</div>
                    <div class="result-hero-label">综合评分</div>
                    <el-tag size="small" :type="lastResult.status==='evaluated'?'success':'info'" effect="dark" round>
                      {{ lastResult.status==='evaluated'?'已评测':'待评测' }}
                    </el-tag>
                  </div>
                  <div v-if="lastResult.feedback" class="result-feedback">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin-bottom:10px;color:var(--text-primary);">AI详细反馈</h4>
                    <div class="markdown-body" v-html="renderMarkdown(lastResult.feedback)"></div>
                  </div>
                </div>
              </el-tab-pane>
              <el-tab-pane label="运行结果" name="output">
                <div v-if="!runResult && !runResultError" class="app-empty" style="padding:50px 0;">
                  <div class="app-empty-icon" style="width:56px;height:56px;"><el-icon :size="22"><VideoPlay /></el-icon></div>
                  <p class="app-empty-text">点击「运行」按钮执行代码</p>
                  <p class="app-empty-hint">代码将在安全沙箱中执行，超时限制 30 秒</p>
                </div>
                <div v-else class="run-output">
                  <div v-if="runResultError" class="run-error">{{ runResultError }}</div>
                  <template v-else-if="runResult">
                    <div class="run-meta">
                      <el-tag :type="runResult.success ? 'success' : 'danger'" size="small" effect="dark" round>
                        {{ runResult.success ? '执行成功' : '执行失败 (code=' + runResult.return_code + ')' }}
                      </el-tag>
                      <span class="run-time">{{ runResult.execution_time_ms }}ms</span>
                    </div>
                    <div v-if="runResult.stdout" class="run-section">
                      <div class="run-section-title">STDOUT</div>
                      <pre class="run-stdout">{{ runResult.stdout }}</pre>
                    </div>
                    <div v-if="runResult.stderr" class="run-section">
                      <div class="run-section-title" style="color:var(--danger);">STDERR</div>
                      <pre class="run-stderr">{{ runResult.stderr }}</pre>
                    </div>
                    <div v-if="runResult.truncated" style="margin-top:8px;font-size: var(--text-xs);color:var(--text-tertiary);">
                      ⚠️ 输出已截断（超出 50000 字符限制）
                    </div>
                  </template>
                </div>
              </el-tab-pane>
              <el-tab-pane label="提交记录" name="history">
                <div v-if="records.length===0" class="app-empty" style="padding:50px 0;">
                  <div class="app-empty-icon" style="width:56px;height:56px;"><el-icon :size="22"><Clock /></el-icon></div>
                  <p class="app-empty-text">暂无提交记录</p>
                </div>
                <div v-else class="history-list">
                  <div v-for="r in records" :key="r.id" class="history-item">
                    <div class="hi-top"><span class="hi-title">{{ r.experiment_title }}</span><span class="status-badge" :class="r.score>=80?'evaluated':r.score>=60?'pending':'submitted'">{{ r.score||'-' }}</span></div>
                    <div class="hi-meta"><span>{{ r.subject||'' }}</span><span>{{ formatTime(r.completed_at) }}</span></div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
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
import { experimentApi, practiceApi, codeApi } from '../api'
import Sidebar from '../components/Sidebar.vue'
import { Upload, Edit, Document, Tickets, Clock, StarFilled, Star, FolderOpened, MagicStick, Delete, ChatDotSquare, CopyDocument, VideoPlay } from '@element-plus/icons-vue'

const route=useRoute();const router=useRouter();const userStore=useUserStore()
const allExperiments=ref([]);const currentExperiment=ref(null);const selectedExperimentId=ref(null)
const language=ref('python');const code=ref('');const submitting=ref(false)
const activeTab=ref('result');const lastResult=ref(null);const records=ref([])
const running=ref(false);const runResult=ref(null);const runResultError=ref('')
const codePlaceholder='# 请在此输入你的数学建模代码\nimport numpy as np\nfrom scipy.optimize import linprog\n\n# 定义目标函数和约束条件\n# 求解并输出结果\nprint("数学建模求解结果:")'

function subjectTagType(s){const m={'优化模型':'','预测模型':'success','评价模型':'warning','分类与聚类':'info','微分方程':'danger','统计模型':'','图论与网络':'success','随机模型':'warning'};return m[s]||''}
function formatTime(t){if(!t)return'-';const d=new Date(t);return d.toLocaleString('zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}
function scoreClass(s){if(!s||s<=0)return'';if(s>=80)return'high';if(s>=60)return'mid';return'low'}
function renderMarkdown(text){if(!text)return'';return text.replace(/```(\w*)\n?([\s\S]*?)```/g,'<pre><code>$2</code></pre>').replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\n/g,'<br>').replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/^###\s+(.*)/gm,'<h4>$1</h4>').replace(/^##\s+(.*)/gm,'<h3>$1</h3>')}
function formatCode(){} // 占位
function copyCode(){if(code.value)try{navigator.clipboard.writeText(code.value)}catch(e){}}
function saveDraft(){if(code.value)localStorage.setItem('code_draft_'+selectedExperimentId.value,code.value)}

async function onExperimentChange(id){if(!id)return;try{currentExperiment.value=await experimentApi.getById(id);const draft=localStorage.getItem('code_draft_'+id);code.value=draft||currentExperiment.value.template_code||''}catch(e){}}
async function handleSubmit(){if(!selectedExperimentId.value||!code.value)return;submitting.value=true;try{const res=await practiceApi.submit({experiment_id:selectedExperimentId.value,code:code.value,language:language.value});lastResult.value=res;activeTab.value='result';await getAiFeedback(res.id);await loadRecords()}catch(e){}finally{submitting.value=false}}
async function getAiFeedback(rid){try{const{chatApi}=await import('../api');const r=await chatApi.send({agent_type:'code-review',message:'请评测这段代码的正确性、代码质量和改进建议。给出评分（0-100）和详细反馈。',code_context:code.value});if(r)lastResult.value.feedback=r.agent_message}catch(e){}}
function askCodeReview(){if(!code.value)return;router.push({path:'/agent-chat',query:{agent:'code-review',code:code.value}})}
async function runCode(){if(!code.value)return;running.value=true;runResult.value=null;runResultError.value='';activeTab.value='output';try{const res=await codeApi.execute({code:code.value,timeout:30});runResult.value=res}catch(e){runResultError.value=e?.response?.data?.detail||e.message||'执行失败'}finally{running.value=false}}
async function loadExperiments(){try{const res=await experimentApi.getList({page:1,page_size:100});allExperiments.value=res.experiments||[]}catch(e){}}
async function loadRecords(){try{const res=await practiceApi.getRecords({page:1,page_size:20});records.value=res.records||[]}catch(e){}}

onMounted(async()=>{await loadExperiments();await loadRecords();if(route.params.experimentId){selectedExperimentId.value=Number(route.params.experimentId);await onExperimentChange(selectedExperimentId.value)}})
</script>

<style scoped lang="scss">
.code-layout{display:flex;flex-direction:column;height:100vh;}
.code-toolbar{display:flex;align-items:center;justify-content:space-between;padding:12px 24px;background:var(--bg-card);border-bottom:1px solid var(--border-light);flex-wrap:wrap;gap:8px;}
.code-body{display:flex;flex:1;overflow:hidden;}
.code-left{flex:1;display:flex;flex-direction:column;padding:12px 8px 12px 24px;overflow-y:auto;}
.exp-info-card{background:var(--bg-card);border-radius:var(--radius-card);padding:16px 20px;margin-bottom:10px;border:1px solid var(--border-light);}
.exp-info-title{font-size: var(--text-base);font-weight:600;margin-bottom:4px;}
.exp-info-desc{font-size: var(--text-sm);color:var(--text-secondary);line-height:1.6;}
.editor-container{flex:1;background:#F2F3F5;border-radius:var(--radius-card);overflow:hidden;display:flex;flex-direction:column;border:1px solid var(--border-light);}
.editor-header{display:flex;justify-content:space-between;align-items:center;padding:8px 16px;background:#E5E6EB;color:var(--text-secondary);font-size: var(--text-xs);}
.code-textarea{flex:1;background:#F2F3F5;color:var(--text-primary,#1D2129);border:none;padding:16px;font-family:var(--font-mono);font-size: var(--text-sm);line-height:1.7;resize:none;outline:none;tab-size:4;}
.code-textarea::placeholder{color:var(--text-tertiary,#C9CDD4);}
.editor-footer{display:flex;justify-content:space-between;align-items:center;padding:6px 16px;background:#E5E6EB;}
.toolbar-btn{background:none;border:none;color:var(--text-secondary,#86909C);font-size: var(--text-xs);cursor:pointer;display:flex;align-items:center;gap:4px;padding:4px 8px;border-radius:4px;transition:all 0.2s;}
.toolbar-btn:hover{background:rgba(0,0,0,0.06);color:var(--text-primary,#1D2129);}
.code-right{width:380px;background:var(--bg-card);border-left:1px solid var(--border-light);display:flex;flex-direction:column;overflow-y:auto;}
.result-tabs{padding:12px 16px;flex:1;}
.result-body{}
.result-hero{padding:20px;border-radius:10px;text-align:center;margin-bottom:16px;}
.result-hero.high{background:var(--success-bg);}.result-hero.mid{background:var(--warning-bg);}.result-hero.low{background:var(--danger-bg);}
.result-hero-score{font-size: var(--text-2xl);font-weight:700;line-height:1;}
.result-hero.high .result-hero-score{color:var(--success);}.result-hero.mid .result-hero-score{color:var(--warning);}.result-hero.low .result-hero-score{color:var(--danger);}
.result-hero-label{font-size: var(--text-xs);color:var(--text-secondary);margin:4px 0 8px;}
.history-list{display:flex;flex-direction:column;gap:8px;}
.history-item{padding:10px 12px;border:1px solid var(--border-light);border-radius:8px;}
.hi-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;}
.hi-title{font-size: var(--text-sm);font-weight:500;}
.hi-meta{font-size: var(--text-xs);color:var(--text-tertiary);display:flex;gap:8px;}
.markdown-body{font-size: var(--text-sm);line-height:1.8;color:var(--text-secondary);}
.markdown-body pre{background:#F2F3F8;padding:12px;border-radius:8px;overflow-x:auto;margin:8px 0;}
.markdown-body code{background:rgba(0,0,0,0.04);padding:2px 6px;border-radius:3px;font-size: var(--text-sm);}
// 运行输出面板
.run-output{padding:4px 0;}
.run-error{padding:12px;background:var(--danger-bg);border-radius:8px;color:var(--danger);font-size: var(--text-sm);line-height:1.6;}
.run-meta{display:flex;align-items:center;gap:8px;margin-bottom:12px;}
.run-time{font-size: var(--text-xs);color:var(--text-tertiary);}
.run-section{margin-bottom:12px;}
.run-section-title{font-size: var(--text-xs);font-weight:600;color:var(--text-secondary);text-transform:uppercase;margin-bottom:4px;}
.run-stdout{background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:8px;font-size: var(--text-xs);line-height:1.5;overflow-x:auto;white-space:pre-wrap;max-height:400px;overflow-y:auto;font-family:var(--font-mono);}
.run-stderr{background:var(--danger-bg);color:var(--danger);padding:12px;border-radius:8px;font-size: var(--text-xs);line-height:1.5;overflow-x:auto;white-space:pre-wrap;max-height:200px;overflow-y:auto;font-family:var(--font-mono);}
</style>
