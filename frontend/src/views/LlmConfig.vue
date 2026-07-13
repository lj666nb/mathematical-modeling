<template>
  <!--
  ============================================================
  API配置页 - 国赛视觉优化版
  项目核心创新功能，重点美化：
    ① 顶部双Tab切换（服务端/浏览器）样式升级
    ② 配置列表卡片化（厂商标识+参数预览+操作按钮）
    ③ 表单分区设计（基础信息+模型参数区块）
    ④ 连通测试结果日志展示
    ⑤ 底部安全说明卡片
  ============================================================
  -->
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <div class="page-container">
        <div class="app-breadcrumb">
          <el-icon><HomeFilled /></el-icon><span>首页</span><span class="sep">/</span><span class="current">API配置</span>
        </div>
        <div class="page-header-area">
          <div class="page-title-row">
            <div>
              <h1 class="page-title">自定义大模型API配置</h1>
              <p class="page-subtitle">支持两种密钥管理模式：服务端加密存储持久化 或 浏览器本地存储（密钥不落盘）</p>
            </div>
          </div>
        </div>

        <!-- Tab切换 -->
        <el-tabs v-model="activeTab" class="config-tabs">
          <!-- ===== Tab1: 服务端存储 ===== -->
          <el-tab-pane label="💾 服务端存储" name="server">
            <el-alert title="密钥加密存储在服务端数据库，关闭浏览器不丢失，支持多设备同步" type="info" show-icon :closable="false" class="config-alert" />

            <el-row :gutter="24">
              <!-- 左：配置列表 -->
              <el-col :span="10">
                <div class="app-card" style="height:100%;">
                  <div class="app-card-header">
                    <span class="app-card-title">我的API配置</span>
                    <el-button type="primary" size="small" :icon="Plus" round @click="showCreateDialog">新建</el-button>
                  </div>
                  <div class="app-card-body">
                    <div v-if="configs.length===0" class="app-empty" style="padding:40px 0;">
                      <div class="app-empty-icon"><el-icon :size="26"><Key /></el-icon></div>
                      <p class="app-empty-text">暂无API配置</p>
                      <p class="app-empty-hint">点击「新建」添加您的第一个LLM密钥</p>
                    </div>
                    <div v-for="cfg in configs" :key="cfg.id" class="cfg-card" :class="{ active: cfg.is_active }">
                      <div class="cfg-card-row">
                        <div class="cfg-provider-icon" :class="cfg.provider"><el-icon><Aim v-if="cfg.provider==='openai'"/><Connection v-else/></el-icon></div>
                        <div class="cfg-info">
                          <div class="cfg-name">{{ cfg.config_name }}<el-tag v-if="cfg.is_active" size="small" type="success" effect="light" round style="margin-left:6px;">当前</el-tag></div>
                          <div class="cfg-meta"><span>{{ providerLabel(cfg.provider) }}</span><span class="dot">·</span><span>{{ cfg.model_name||'默认模型' }}</span></div>
                          <div class="cfg-key">{{ cfg.api_key }}</div>
                        </div>
                        <div class="cfg-actions">
                          <el-tooltip content="设为当前"><el-button text size="small" :icon="Check" @click.stop="setActive(cfg.id)" :disabled="cfg.is_active" /></el-tooltip>
                          <el-tooltip content="编辑"><el-button text size="small" :icon="Edit" @click.stop="showEditDialog(cfg)" /></el-tooltip>
                          <el-tooltip content="删除"><el-button text size="small" type="danger" :icon="Delete" @click.stop="handleDelete(cfg.id)" /></el-tooltip>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </el-col>

              <!-- 右：表单+测试 -->
              <el-col :span="14">
                <!-- DeepSeek 快速配置 -->
                <div class="app-card deepseek-quick-card" style="margin-bottom:20px;">
                  <div class="app-card-header">
                    <span class="app-card-title">🚀 快速配置 DeepSeek</span>
                    <el-tag type="danger" size="small" effect="dark" round>推荐</el-tag>
                  </div>
                  <div class="app-card-body">
                    <p style="color:var(--text-secondary);font-size: var(--text-sm);margin-bottom:12px;">DeepSeek V4 模型性价比极高，适合教学场景。只需输入API密钥即可使用。</p>
                    <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
                      <el-button type="primary" @click="quickSetupDeepSeek" round>
                        <el-icon><Connection /></el-icon> 一键填入 DeepSeek 配置
                      </el-button>
                      <span style="font-size: var(--text-xs);color:var(--text-tertiary);">自动填充：厂商/API地址/模型</span>
                    </div>
                  </div>
                </div>

                <div class="app-card" style="margin-bottom:20px;">
                  <div class="app-card-header"><span class="app-card-title">{{ isEditing ? '编辑配置' : '新建API配置' }}</span></div>
                  <div class="app-card-body" style="padding-top:20px;">
                    <el-form :model="form" :rules="formRules" ref="formRef" label-width="90px" v-if="formVisible">
                      <div class="form-section-title">基础信息</div>
                      <el-row :gutter="16">
                        <el-col :span="12"><el-form-item label="配置名称" prop="config_name"><el-input v-model="form.config_name" placeholder="如：我的OpenAI" /></el-form-item></el-col>
                        <el-col :span="12"><el-form-item label="厂商" prop="provider"><el-select v-model="form.provider" style="width:100%" @change="onProviderChange"><el-option v-for="p in providers" :key="p.key" :label="p.name" :value="p.key" /></el-select></el-form-item></el-col>
                      </el-row>
                      <el-form-item label="API地址"><el-input v-model="form.base_url" placeholder="默认使用厂商地址" /></el-form-item>
                      <el-row :gutter="16">
                        <el-col :span="12">
                          <el-form-item label="模型名称">
                            <el-select v-if="currentProviderModels.length > 0" v-model="form.model_name" style="width:100%" filterable allow-create placeholder="选择或输入模型">
                              <el-option v-for="m in currentProviderModels" :key="m" :label="m" :value="m" />
                            </el-select>
                            <el-input v-else v-model="form.model_name" placeholder="如：gpt-4o-mini" />
                          </el-form-item>
                        </el-col>
                        <el-col :span="12"><el-form-item label="API密钥" prop="api_key"><el-input v-model="form.api_key" type="password" show-password placeholder="输入API密钥" /></el-form-item></el-col>
                      </el-row>
                      <div class="form-section-title">模型参数</div>
                      <el-row :gutter="16">
                        <el-col :span="12"><el-form-item label="温度"><el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input /></el-form-item></el-col>
                        <el-col :span="12"><el-form-item label="最大Token"><el-input-number v-model="form.max_tokens" :min="1" :max="128000" :step="1024" style="width:100%;" /></el-form-item></el-col>
                      </el-row>
                      <el-form-item><el-button type="primary" :loading="saving" @click="handleSave" round>{{ isEditing ? '更新配置' : '保存配置' }}</el-button><el-button @click="formVisible=false" round>取消</el-button></el-form-item>
                    </el-form>
                    <div v-else class="app-empty" style="padding:30px 0;">
                      <div class="app-empty-icon" style="width:48px;height:48px;"><el-icon :size="20"><Plus /></el-icon></div>
                      <p class="app-empty-text">点击左侧「新建」按钮添加API配置</p>
                    </div>
                  </div>
                </div>

                <!-- 连通测试 -->
                <div class="app-card" style="margin-bottom:20px;">
                  <div class="app-card-header"><span class="app-card-title">🔌 连通性测试</span></div>
                  <div class="app-card-body">
                    <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
                      <el-select v-model="testConfigId" placeholder="选择要测试的配置" style="width:260px;" clearable>
                        <el-option v-for="cfg in configs" :key="cfg.id" :label="`${cfg.config_name} (${providerLabel(cfg.provider)})`" :value="cfg.id" />
                      </el-select>
                      <el-button type="success" :loading="testing" @click="handleTest" :disabled="!testConfigId" round><el-icon><Connection /></el-icon> 测试连通性</el-button>
                    </div>
                    <div v-if="testResult" class="test-result-box" :class="testResult.success?'success':'error'">
                      <el-icon v-if="testResult.success" color="#00B42A" size="20"><CircleCheckFilled /></el-icon>
                      <el-icon v-else color="#F53F3F" size="20"><CircleCloseFilled /></el-icon>
                      <div><div class="test-msg">{{ testResult.message }}</div><div v-if="testResult.response_time_ms" class="test-time">响应: {{ testResult.response_time_ms }}ms</div></div>
                    </div>
                  </div>
                </div>

                <!-- 安全说明 -->
                <div class="app-card">
                  <div class="app-card-header"><span class="app-card-title">🛡️ 安全说明</span></div>
                  <div class="app-card-body" style="padding-top:12px;">
                    <div class="security-grid">
                      <div class="sec-item"><el-icon color="var(--primary)" size="18"><Lock /></el-icon><div><strong>服务端存储</strong><span>密钥加密存储在数据库，登录后可在任意设备同步使用</span></div></div>
                      <div class="sec-item"><el-icon color="var(--success)" size="18"><Key /></el-icon><div><strong>浏览器存储</strong><span>密钥仅保存在浏览器localStorage，通过HTTP头传输，服务端不落盘</span></div></div>
                      <div class="sec-item"><el-icon color="var(--warning)" size="18"><InfoFilled /></el-icon><div><strong>隐私保障</strong><span>平台不收集任何API密钥，所有调用直接发往你指定的LLM厂商地址</span></div></div>
                    </div>
                  </div>
                </div>
              </el-col>
            </el-row>
          </el-tab-pane>

          <!-- ===== Tab2: 浏览器密钥 ===== -->
          <el-tab-pane label="🔑 浏览器密钥模式" name="browser">
            <el-alert title="隐私安全模式：API密钥仅保存在浏览器localStorage，通过HTTP头临时传递，服务端不存储任何密钥信息" type="success" show-icon :closable="false" class="config-alert" />
            <el-row :gutter="24">
              <el-col :span="12">
                <div class="app-card">
                  <div class="app-card-header"><span class="app-card-title">浏览器密钥配置</span></div>
                  <div class="app-card-body">
                    <el-form :model="browserForm" label-width="90px">
                      <el-form-item label="厂商"><el-select v-model="browserForm.provider" style="width:100%" @change="onBrowserProviderChange"><el-option v-for="p in providers" :key="p.key" :label="p.name" :value="p.key" /></el-select></el-form-item>
                      <el-form-item label="API地址"><el-input v-model="browserForm.base_url" placeholder="默认使用厂商地址" /></el-form-item>
                      <el-form-item label="模型名称">
                        <el-select v-if="currentBrowserProviderModels.length > 0" v-model="browserForm.model_name" style="width:100%" filterable allow-create placeholder="选择或输入模型">
                          <el-option v-for="m in currentBrowserProviderModels" :key="m" :label="m" :value="m" />
                        </el-select>
                        <el-input v-else v-model="browserForm.model_name" placeholder="如 gpt-4o-mini" />
                      </el-form-item>
                      <el-form-item label="API密钥"><el-input v-model="browserForm.api_key" type="password" show-password placeholder="输入API密钥（仅浏览器保存）" /></el-form-item>
                      <el-form-item>
                        <el-button type="primary" :disabled="!browserForm.api_key" @click="saveBrowserConfig" round><el-icon><Lock /></el-icon> 保存到浏览器</el-button>
                        <el-button @click="clearBrowserConfig" plain type="danger" round>清除</el-button>
                      </el-form-item>
                    </el-form>
                  </div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="app-card" style="margin-bottom:20px;">
                  <div class="app-card-header"><span class="app-card-title">连通性测试</span></div>
                  <div class="app-card-body">
                    <p style="color:var(--text-secondary);font-size: var(--text-sm);margin-bottom:16px;">密钥仅通过本次请求传输，不存储到服务端</p>
                    <el-button type="success" :loading="browserTesting" :disabled="!browserForm.api_key" @click="handleBrowserTest" round style="width:100%;height:46px;"><el-icon><Connection /></el-icon> 测试浏览器密钥连通性</el-button>
                    <div v-if="browserTestResult" class="test-result-box" style="margin-top:14px;" :class="browserTestResult.success?'success':'error'">
                      <el-icon v-if="browserTestResult.success" color="#00B42A" size="18"><CircleCheckFilled /></el-icon>
                      <el-icon v-else color="#F53F3F" size="18"><CircleCloseFilled /></el-icon>
                      <span>{{ browserTestResult.message }}</span>
                    </div>
                  </div>
                </div>
                <div class="app-card">
                  <div class="app-card-header"><span class="app-card-title">当前配置状态</span></div>
                  <div class="app-card-body">
                    <div v-if="browserSaved" style="background:var(--success-bg);border-radius:8px;padding:16px;">
                      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><el-icon color="#00B42A" size="16"><CircleCheckFilled /></el-icon><span style="font-weight:600;color:var(--success);font-size: var(--text-sm);">浏览器密钥已配置</span></div>
                      <p style="font-size: var(--text-sm);color:var(--text-secondary);line-height:1.8;">厂商: {{ browserSaved.providerName }}<br>模型: {{ browserSaved.model_name||'默认' }}<br>地址: {{ browserSaved.base_url||'默认地址' }}</p>
                    </div>
                    <div v-else style="background:var(--info-bg);border-radius:8px;padding:16px;">
                      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><el-icon color="var(--info)" size="16"><InfoFilled /></el-icon><span style="font-weight:600;color:var(--info);font-size: var(--text-sm);">未配置</span></div>
                      <p style="font-size: var(--text-sm);color:var(--text-secondary);">在左侧输入密钥后点击「保存到浏览器」</p>
                    </div>
                  </div>
                </div>
              </el-col>
            </el-row>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '../stores/user'
import { llmConfigApi } from '../api'
import Sidebar from '../components/Sidebar.vue'
import { Plus, Key, Check, Edit, Delete, Connection, Lock, CircleCheckFilled, CircleCloseFilled, InfoFilled, Aim, HomeFilled, ArrowRight } from '@element-plus/icons-vue'

const router=useRouter();const userStore=useUserStore()
const activeTab=ref('server');const configs=ref([]);const providers=ref([])
const formVisible=ref(false);const isEditing=ref(false);const editingId=ref(null)
const saving=ref(false);const testing=ref(false);const testConfigId=ref(null);const testResult=ref(null);const formRef=ref(null)
const browserTesting=ref(false);const browserTestResult=ref(null);const browserSaved=ref(null)

const form=reactive({config_name:'',provider:'openai',base_url:'',model_name:'',api_key:'',temperature:0.7,max_tokens:4096})
const browserForm=reactive({provider:'openai',base_url:'',model_name:'',api_key:''})
const formRules={config_name:[{required:true,message:'请输入配置名称',trigger:'blur'}],provider:[{required:true,message:'请选择厂商',trigger:'change'}],api_key:[{required:true,message:'请输入API密钥',trigger:'blur'}]}

function providerLabel(k){const m={openai:'OpenAI',deepseek:'DeepSeek',qwen:'通义千问','ernie-bot':'文心一言',glm:'智谱GLM',moonshot:'Moonshot'};return m[k]||k}

// 当前选中厂商的模型列表
const currentProviderModels = computed(() => {
  const p = providers.value.find(x => x.key === form.provider)
  return p?.models || []
})
const currentBrowserProviderModels = computed(() => {
  const p = providers.value.find(x => x.key === browserForm.provider)
  return p?.models || []
})

function onProviderChange(v){
  const p=providers.value.find(x=>x.key===v)
  if(p && !isEditing.value) {
    form.base_url = p.default_url || ''
    // 自动选择第一个模型
    if (p.models && p.models.length > 0) form.model_name = p.models[0]
    else form.model_name = ''
  }
}
function onBrowserProviderChange(v){
  const p=providers.value.find(x=>x.key===v)
  if(p) {
    browserForm.base_url = p.default_url || ''
    if (p.models && p.models.length > 0) browserForm.model_name = p.models[0]
    else browserForm.model_name = ''
  }
}

// DeepSeek 快速配置
function quickSetupDeepSeek() {
  isEditing.value = false; editingId.value = null
  Object.assign(form, {
    config_name: '我的 DeepSeek V4',
    provider: 'deepseek',
    base_url: 'https://api.deepseek.com/v1',
    model_name: 'deepseek-v4-pro',
    api_key: 'sk-5b7fc02c278a4f13b8c3cc542001405c',
    temperature: 0.7,
    max_tokens: 4096
  })
  formVisible.value = true
  ElMessage.success('🚀 已自动填充 DeepSeek 配置，点击「保存配置」即可使用')
}

function showCreateDialog(){isEditing.value=false;editingId.value=null;Object.assign(form,{config_name:'',provider:'openai',base_url:'',model_name:'',api_key:'',temperature:0.7,max_tokens:4096});formVisible.value=true}
function showEditDialog(cfg){isEditing.value=true;editingId.value=cfg.id;Object.assign(form,{config_name:cfg.config_name,provider:cfg.provider,base_url:cfg.base_url,model_name:cfg.model_name,api_key:'',temperature:cfg.temperature,max_tokens:cfg.max_tokens});formVisible.value=true}

async function handleSave(){const valid=await formRef.value.validate().catch(()=>false);if(!valid)return;saving.value=true;try{if(isEditing.value){const upd={};if(form.api_key)upd.api_key=form.api_key;Object.keys(form).forEach(k=>{if(k!=='api_key')upd[k]=form[k]});await llmConfigApi.update(editingId.value,upd);ElMessage.success('已更新')}else{await llmConfigApi.create(form);ElMessage.success('已创建')}formVisible.value=false;await loadConfigs()}catch(e){}finally{saving.value=false}}
async function handleDelete(id){try{await ElMessageBox.confirm('确定删除此配置？','确认删除');await llmConfigApi.delete(id);ElMessage.success('已删除');await loadConfigs()}catch(e){if(e!=='cancel')throw e}}
async function setActive(id){await llmConfigApi.update(id,{is_active:1});ElMessage.success('已切换');await loadConfigs()}
async function handleTest(){if(!testConfigId.value)return;testing.value=true;testResult.value=null;try{testResult.value=await llmConfigApi.test({config_id:testConfigId.value})}catch(e){testResult.value={success:false,message:'测试请求失败'}}finally{testing.value=false}}

function saveBrowserConfig(){localStorage.setItem('llm_key_mode','browser');localStorage.setItem('llm_api_key',browserForm.api_key);localStorage.setItem('llm_base_url',browserForm.base_url);localStorage.setItem('llm_model',browserForm.model_name);localStorage.setItem('llm_provider',browserForm.provider);readBrowserConfig();ElMessage.success('✅ 密钥已保存到浏览器，服务端不会存储')}
function clearBrowserConfig(){['llm_key_mode','llm_api_key','llm_base_url','llm_model','llm_provider'].forEach(k=>localStorage.removeItem(k));browserSaved.value=null;browserForm.api_key='';ElMessage.success('已清除')}
function readBrowserConfig(){if(localStorage.getItem('llm_key_mode')==='browser'){const p=localStorage.getItem('llm_provider')||'openai';browserSaved.value={provider:p,providerName:providerLabel(p),model_name:localStorage.getItem('llm_model')||'',base_url:localStorage.getItem('llm_base_url')||''};Object.assign(browserForm,{provider:p,base_url:browserSaved.value.base_url,model_name:browserSaved.value.model_name})}else{browserSaved.value=null}}
async function handleBrowserTest(){if(!browserForm.api_key)return;browserTesting.value=true;browserTestResult.value=null;try{browserTestResult.value=await llmConfigApi.testRaw({api_key:browserForm.api_key,base_url:browserForm.base_url,model_name:browserForm.model_name,provider:browserForm.provider})}catch(e){browserTestResult.value={success:false,message:'请求失败'}}finally{browserTesting.value=false}}
async function loadConfigs(){try{configs.value=await llmConfigApi.getList()}catch(e){}}

onMounted(async()=>{try{providers.value=(await llmConfigApi.getProviders()).providers||[]}catch(e){};await loadConfigs();readBrowserConfig()})
</script>

<style scoped lang="scss">
.config-tabs{background:#fff;border-radius:12px;padding:8px;}
.config-alert{margin-bottom:20px;border-radius:8px;}
.cfg-card{padding:12px;border:1px solid var(--border-light);border-radius:10px;margin-bottom:8px;transition:all 0.25s;}
.cfg-card:hover{border-color:var(--primary);background:var(--primary-light);}
.cfg-card.active{border-color:var(--success);background:var(--success-bg);}
.cfg-card-row{display:flex;gap:12px;align-items:center;}
.cfg-provider-icon{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size: var(--text-md);background:var(--info-bg);color:var(--info);flex-shrink:0;}
.cfg-provider-icon.openai{background:var(--primary-light);color:var(--primary);}
.cfg-info{flex:1;min-width:0;}
.cfg-name{font-weight:600;font-size: var(--text-sm);display:flex;align-items:center;margin-bottom:1px;}
.cfg-meta{font-size: var(--text-xs);color:var(--text-tertiary);display:flex;align-items:center;gap:4px;}
.cfg-key{font-size: var(--text-xs);color:var(--text-tertiary);font-family:var(--font-mono);margin-top:1px;}
.cfg-actions{display:flex;flex-direction:column;gap:2px;opacity:0;transition:opacity 0.2s;}
.cfg-card:hover .cfg-actions{opacity:1;}

.form-section-title{font-size: var(--text-sm);font-weight:600;color:var(--text-primary);margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid var(--border-light);}

.test-result-box{display:flex;align-items:flex-start;gap:10px;margin-top:14px;padding:14px;border-radius:8px;}
.test-result-box.success{background:var(--success-bg);}
.test-result-box.error{background:var(--danger-bg);}
.test-msg{font-size: var(--text-sm);font-weight:500;}.test-result-box.success .test-msg{color:var(--success);}.test-result-box.error .test-msg{color:var(--danger);}
.test-time{font-size: var(--text-xs);color:var(--text-tertiary);margin-top:2px;}

.security-grid{display:flex;flex-direction:column;gap:12px;}
.sec-item{display:flex;align-items:flex-start;gap:10px;font-size: var(--text-sm);line-height:1.5;}
.sec-item strong{display:block;font-weight:600;color:var(--text-primary);margin-bottom:1px;}
.sec-item span{color:var(--text-secondary);}
</style>
