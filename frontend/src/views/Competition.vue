<template>
  <!--
  ============================================================
  竞赛训练页 — S0-S8 数学建模竞赛工作流
  S0 预检：文件分类 + 可读性检查 + 附件角色识别
  S1 赛题分析：文本提取 + 子问题拆分 + 模型推荐
  ============================================================
  -->
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <div class="page-container">
        <!-- 面包屑 -->
        <div class="app-breadcrumb">
          <el-icon><HomeFilled /></el-icon><span>首页</span>
          <span class="sep">/</span><span>竞赛</span>
          <span class="sep">/</span><span class="current">竞赛训练</span>
        </div>

        <div class="page-header-area">
          <div class="page-title-row">
            <div>
              <h1 class="page-title">竞赛训练</h1>
              <p class="page-subtitle">数学建模竞赛全流程 S0-S8，从赛题上传到论文成稿</p>
            </div>
            <el-button type="primary" :icon="Plus" @click="showCreateDialog = true" round>新建赛题任务</el-button>
          </div>
        </div>

        <!-- ===== 空状态（无任何任务） ===== -->
        <div v-if="tasks.length === 0 && !loading" class="app-card" style="text-align:center;padding:64px 20px;">
          <div class="empty-illustration"><el-icon :size="48"><Trophy /></el-icon></div>
          <h3 style="font-size:var(--text-lg);font-weight:600;margin-bottom:8px;color:var(--text-primary);">还没有训练记录</h3>
          <p class="card-desc" style="text-align:center;">创建竞赛任务，上传赛题文件，开始 S0-S8 全流程训练</p>
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true" round size="large">新建训练任务</el-button>
        </div>

        <!-- ===== 训练记录卡片网格 ===== -->
        <div v-if="tasks.length > 0" class="training-records-section">
          <div class="section-header-row">
            <h2 class="section-heading">📋 训练记录</h2>
            <span class="text-muted">共 {{ tasks.length }} 次训练</span>
          </div>
          <div class="training-grid">
            <div
              v-for="t in tasks" :key="t.id"
              class="training-card"
              :class="{ active: activeTaskId === t.id }"
              @click="selectTask(t)"
            >
              <!-- 卡片顶部色条 -->
              <div class="card-accent" :style="{ background: taskAccentColor(t) }"></div>
              <div class="card-body">
                <!-- 标题行 -->
                <div class="card-title-row">
                  <h3 class="card-title">{{ t.title }}</h3>
                  <el-button text type="danger" size="small" :icon="Delete" @click.stop="deleteTask(t.id)" class="card-delete-btn" />
                </div>
                <!-- 状态徽章行 -->
                <div class="card-badges">
                  <el-tag :type="taskStatusType(t)" size="small" effect="dark" round>
                    {{ taskStatusLabel(t) }}
                  </el-tag>
                  <span v-if="t.preflight_status === 'pass'" class="badge-ok">✓ 预检通过</span>
                  <span v-else-if="t.preflight_status === 'fail'" class="badge-fail">✗ 预检失败</span>
                  <span v-if="t.status !== 's7_check_passed'" class="resume-badge">🔄 {{ resumeHintForTask(t) }}</span>
                  <span v-else class="badge-done">✅ 全部完成</span>
                </div>
                <!-- 进度条 -->
                <div class="card-progress">
                  <div class="card-progress-header">
                    <span>进度</span>
                    <span>{{ getTaskCompletedSteps(t) }}/8</span>
                  </div>
                  <div class="card-progress-bar">
                    <div class="card-progress-fill" :style="{ width: (getTaskCompletedSteps(t)/8*100)+'%' }"></div>
                  </div>
                </div>
                <!-- 底部信息 -->
                <div class="card-footer">
                  <span class="card-meta"><el-icon :size="12"><Document /></el-icon> {{ t.file_count }} 文件</span>
                  <span class="card-meta"><el-icon :size="12"><Clock /></el-icon> {{ formatDate(t.updated_at) }}</span>
                  <span v-if="activeTaskId === t.id" class="card-active-tag">当前查看</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 活跃任务工作区 ===== -->
        <template v-if="activeTaskId">
          <!-- 任务上下文横幅 -->
          <div class="task-banner">
            <div class="task-banner-left">
              <el-icon :size="22" style="color:var(--primary);"><Trophy /></el-icon>
              <div>
                <div class="task-banner-title">{{ activeTask.title }}</div>
                <div class="task-banner-meta mt-2">
                  <el-tag :type="stepTagType(activeTask.current_step)" size="small" effect="dark" round>{{ activeTask.current_step }}</el-tag>
                  <span class="text-muted">{{ activeTask.file_count || uploadedFiles.length }} 个文件</span>
                  <span v-if="activeTask.status !== 's7_check_passed'" class="resume-badge">🔄 {{ resumeHint }}</span>
                  <span v-else style="color:var(--success);font-size:var(--text-xs);">✅ 全部完成</span>
                </div>
              </div>
            </div>
            <el-button type="danger" plain size="small" :icon="Delete" @click="deleteTask(activeTaskId)" round>删除任务</el-button>
          </div>
          <!-- 工作流步骤指示器（带图标 + 色彩编码） -->
          <div class="step-indicator">
            <div class="step-dot s0" :class="{ done: activeTask.preflight_status === 'pass', active: activeTask.current_step === 'S0' }">
              <span class="step-icon"><el-icon v-if="isStepDone('S0')"><CircleCheck /></el-icon><el-icon v-else><Search /></el-icon></span>
              <span class="step-num">S0</span><span class="step-label">预检</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S0') }"></div>
            <div class="step-dot s1" :class="{ done: isStepDone('S1'), active: activeTask.current_step === 'S1' }">
              <span class="step-icon"><el-icon v-if="isStepDone('S1')"><CircleCheck /></el-icon><el-icon v-else><DataAnalysis /></el-icon></span>
              <span class="step-num">S1</span><span class="step-label">分析</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S1') }"></div>
            <div class="step-dot s2" :class="{ done: isStepDone('S2'), active: activeTask.current_step === 'S2' }">
              <span class="step-icon"><el-icon v-if="isStepDone('S2')"><CircleCheck /></el-icon><el-icon v-else><Guide /></el-icon></span>
              <span class="step-num">S2</span><span class="step-label">路线</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S3') }"></div>
            <div class="step-dot s3" :class="{ done: isStepDone('S3'), active: activeTask.current_step === 'S3' || activeTask.current_step === 'S4' }">
              <span class="step-icon"><el-icon v-if="isStepDone('S3')"><CircleCheck /></el-icon><el-icon v-else><Coin /></el-icon></span>
              <span class="step-num">S3</span><span class="step-label">数据</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S4') }"></div>
            <div class="step-dot s4" :class="{ done: isStepDone('S4'), active: false }">
              <span class="step-icon"><el-icon v-if="isStepDone('S4')"><CircleCheck /></el-icon><el-icon v-else><PictureFilled /></el-icon></span>
              <span class="step-num">S4</span><span class="step-label">图表</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S5') }"></div>
            <div class="step-dot s5" :class="{ done: isStepDone('S5'), active: activeTask.current_step === 'S5' }">
              <span class="step-icon"><el-icon v-if="isStepDone('S5')"><CircleCheck /></el-icon><el-icon v-else><Monitor /></el-icon></span>
              <span class="step-num">S5</span><span class="step-label">代码</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S6') }"></div>
            <div class="step-dot s6" :class="{ done: isStepDone('S6'), active: activeTask.current_step === 'S6' }">
              <span class="step-icon"><el-icon v-if="isStepDone('S6')"><CircleCheck /></el-icon><el-icon v-else><Lock /></el-icon></span>
              <span class="step-num">S6</span><span class="step-label">门禁</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S7') }"></div>
            <div class="step-dot s7" :class="{ done: isStepDone('S7'), active: activeTask.current_step === 'S7' }">
              <span class="step-icon"><el-icon v-if="isStepDone('S7')"><CircleCheck /></el-icon><el-icon v-else><Document /></el-icon></span>
              <span class="step-num">S7</span><span class="step-label">论文</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S8') }"></div>
            <div class="step-dot s8" :class="{ done: isStepDone('S8'), active: activeTask.current_step === 'S7_check' }">
              <span class="step-icon"><el-icon v-if="isStepDone('S8')"><CircleCheck /></el-icon><el-icon v-else><Finished /></el-icon></span>
              <span class="step-num">S8</span><span class="step-label">提交</span>
            </div>
          </div>
          <!-- 进度条 -->
          <div class="progress-bar-wrap">
            <div class="progress-bar-header">
              <span class="progress-label">整体进度</span>
              <span class="progress-value">{{ completedSteps }}/8 步骤完成</span>
            </div>
            <div style="height:6px;background:var(--bg-primary);border-radius:3px;overflow:hidden;">
              <div :style="{ width: (completedSteps/8*100)+'%', height:'100%', background:'var(--primary)', borderRadius:'3px', transition:'width 0.5s' }"></div>
            </div>
          </div>

          <!-- 单栏全宽布局 -->
          <div class="work-area">
            <!-- 文件上传区 -->
            <div class="app-card">
                <div class="app-card-header">
                  <span class="app-card-title">📁 赛题文件</span>
                  <span class="text-muted">{{ uploadedFiles.length }} 个文件</span>
                </div>
                <div class="app-card-body">
                  <input
                    id="competition-file-input"
                    ref="fileInputRef"
                    type="file"
                    multiple
                    accept=".pdf,.docx,.md,.txt,.csv,.xlsx,.xls,.json,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,application/json"
                    style="display:none"
                    @change="onFileInputChange"
                  />
                  <label for="competition-file-input" class="upload-zone" @dragover.prevent @drop.prevent="onFileDrop">
                    <el-icon :size="40" style="color:var(--primary);margin-bottom:8px;"><UploadFilled /></el-icon>
                    <div class="upload-text">
                      <p><strong>点击选择文件 或 拖拽到此处</strong></p>
                      <p class="upload-hint">支持 PDF / DOCX / MD / TXT / CSV / XLSX / JSON</p>
                    </div>
                  </label>

                  <div v-if="uploadedFiles.length > 0" class="file-list">
                    <div v-for="f in uploadedFiles" :key="f.name" class="file-item">
                      <el-icon :size="16" :style="{ color: fileIconColor(f.ext) }"><Document /></el-icon>
                      <span class="file-name">{{ f.name }}</span>
                      <span class="file-size">{{ formatSize(f.size) }}</span>
                    </div>
                  </div>
                  <div v-else class="empty-state-sm">尚未上传文件 — 请上传赛题 PDF/Word 与数据附件</div>
                </div>
              </div>

              <!-- S0 预检 -->
              <div class="app-card step-card s0">
                <div class="app-card-header">
                  <span class="app-card-title">🔍 S0 预检</span>
                  <el-tag v-if="activeTask.preflight_status === 'pass'" type="success" size="small" effect="dark" round>PASS</el-tag>
                  <el-tag v-else-if="activeTask.preflight_status === 'fail'" type="danger" size="small" effect="dark" round>FAIL</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>未运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p class="card-desc">检查赛题文件完整性：识别题面/数据/结果模板，验证文件可读性和依赖项。</p>
                  <el-button type="primary" :loading="preflightLoading" :disabled="uploadedFiles.length === 0" @click="runPreflight" round>
                    {{ preflightLoading ? '预检中...' : '运行 S0 预检' }}
                  </el-button>
                </div>

                <!-- 预检结果 -->
                <div v-if="preflightData" class="analysis-result">
                  <div class="result-status" :class="preflightData.status === 'PASS' ? 'pass' : 'fail'">
                    <el-icon :size="18"><CircleCheck v-if="preflightData.status === 'PASS'" /><CircleClose v-else /></el-icon>
                    <span>{{ preflightData.status === 'PASS' ? '预检通过！可以进入 S1 赛题分析' : '预检未通过，请修复以下问题' }}</span>
                  </div>

                  <!-- 附件清单 -->
                  <div v-if="manifestEntries.length > 0" class="mt-4">
                    <h4 class="section-title">附件清单</h4>
                    <div class="manifest-table">
                      <div v-for="entry in manifestEntries" :key="entry.path" class="manifest-row">
                        <span class="manifest-file">{{ entry.path }}</span>
                        <el-tag :type="roleTagType(entry.role)" size="small" effect="plain" round>{{ roleLabel(entry.role) }}</el-tag>
                        <span v-if="entry.char_count" class="text-muted">{{ entry.char_count }}字符</span>
                        <span v-if="entry.warnings?.length" style="color:var(--warning);font-size:var(--text-xs);">⚠{{ entry.warnings.length }}</span>
                        <span v-if="entry.errors?.length" style="color:var(--danger);font-size:var(--text-xs);">✗{{ entry.errors.length }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- 错误列表 -->
                  <div v-if="preflightData.errors?.length" class="mt-4">
                    <h4 style="font-size:var(--text-sm);font-weight:600;color:var(--danger);margin-bottom:6px;">错误 ({{ preflightData.errors.length }})</h4>
                    <div v-for="(e, i) in preflightData.errors" :key="'e'+i" class="err-item err">{{ e }}</div>
                  </div>

                  <!-- 警告列表 -->
                  <div v-if="preflightData.warnings?.length" class="mt-2">
                    <h4 style="font-size:var(--text-sm);font-weight:600;color:var(--warning);margin-bottom:6px;">警告 ({{ preflightData.warnings.length }})</h4>
                    <div v-for="(w, i) in preflightData.warnings" :key="'w'+i" class="err-item warn">{{ w }}</div>
                  </div>
                </div>
              </div>
            <!-- S1 赛题分析 -->
            <div class="app-card step-card s1">
                <div class="app-card-header">
                  <span class="app-card-title">📊 S1 赛题分析</span>
                  <el-tag v-if="analysisData" type="success" size="small" effect="dark" round>已完成</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p class="card-desc">自动拆分赛题为子问题，识别任务类型，推荐基线模型与改进方案。</p>
                  <el-button type="success" :loading="analysisLoading" :disabled="!isStepDone('S0')" @click="runAnalysis" round>
                    {{ analysisLoading ? '分析中...' : '运行 S1 赛题分析' }}
                  </el-button>
                  <div v-if="activeTask.preflight_status !== 'pass'" class="step-hint">⚠ 请先通过 S0 预检再运行赛题分析</div>
                </div>

                <!-- S1 分析结果 -->
                <div v-if="analysisData" class="analysis-result">
                  <div v-if="analysisData.documents?.length || analysisData.data_files?.length" class="mb-3">
                    <h4 class="section-title">读取文件</h4>
                    <div class="tag-row">
                      <el-tag v-for="d in analysisData.documents" :key="d.path" size="small" effect="plain">📄 {{ d.path }} ({{ d.chars }}字)</el-tag>
                      <el-tag v-for="d in analysisData.data_files" :key="d.path" size="small" effect="plain" type="warning">📊 {{ d.path }}</el-tag>
                    </div>
                  </div>

                  <h4 class="section-title">子问题分析 ({{ analysisData.questions?.length || 0 }} 个问题)</h4>
                  <div v-if="analysisData.questions?.length" class="question-cards">
                    <div v-for="q in analysisData.questions" :key="q.id" class="q-card">
                      <div class="q-card-header">
                        <span class="q-id">{{ q.id }}</span>
                        <span class="q-title">{{ q.title }}</span>
                        <el-tag :type="taskTypeColor(q.task_type)" size="small" effect="dark" round>{{ q.task_type }}</el-tag>
                      </div>
                      <p class="q-summary">{{ q.summary }}</p>
                      <div class="q-detail-grid">
                        <div class="q-detail-item"><span class="q-detail-label">基线模型</span><span class="q-detail-value">{{ q.recommended_models?.baseline }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">改进方案</span><span class="q-detail-value">{{ q.recommended_models?.improved }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">验证计划</span><span class="q-detail-value">{{ (q.validation_plan || []).join('；') }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">建议图表</span><span class="q-detail-value">{{ (q.figure_suggestions || []).join('；') }}</span></div>
                      </div>
                      <div v-if="q.constraints?.length" class="mt-2">
                        <span class="text-muted">约束条件：</span>
                        <el-tag v-for="(c, ci) in q.constraints.slice(0,3)" :key="ci" size="small" effect="plain" style="margin:2px;">{{ c }}</el-tag>
                      </div>
                    </div>
                  </div>
                  <div v-else class="empty-state-sm">未能自动拆分出子问题 — 请确认赛题文件包含明确的问题编号</div>
                </div>

                <div v-if="!analysisData && !analysisLoading" class="empty-state">
                  <div class="empty-icon"><el-icon :size="32"><DataAnalysis /></el-icon></div>
                  <p style="font-size:var(--text-sm);">运行 S1 后在此查看赛题结构化分析结果</p>
                </div>
              </div>

              <!-- S2 模型路线 -->
              <div class="app-card step-card s2">
                <div class="app-card-header">
                  <span class="app-card-title">🗺️ S2 模型路线</span>
                  <el-tag v-if="modelRouteData" type="success" size="small" effect="dark" round>已完成</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p class="card-desc">为每个子问题推荐基线模型、主模型与备选模型，映射评分点到论文落位，规划图表与公式要求。</p>
                  <el-button type="primary" :loading="modelRouteLoading" :disabled="!isStepDone('S1')" @click="runModelRoute" round>
                    {{ modelRouteLoading ? '生成中...' : '运行 S2 模型路线' }}
                  </el-button>
                  <div v-if="!isStepDone('S1')" class="step-hint">⚠ 请先完成 S1 赛题分析再运行 S2 模型路线</div>
                  <div v-if="isStepDone('S2')" class="step-ok">✅ S2 模型路线已完成，可重新运行</div>
                </div>

                <div v-if="modelRouteData" class="analysis-result">
                  <h4 class="section-title">模型路线 ({{ modelRouteData.questions?.length || 0 }} 个问题)</h4>
                  <div v-if="modelRouteData.questions?.length" class="question-cards">
                    <div v-for="q in modelRouteData.questions" :key="q.question_id" class="q-card" style="border-left:3px solid var(--step-s2);">
                      <div class="q-card-header">
                        <span class="q-id">{{ q.question_id }}</span>
                        <span class="q-title">{{ q.title }}</span>
                        <el-tag :type="taskTypeColor(q.task_type)" size="small" effect="dark" round>{{ q.task_type }}</el-tag>
                      </div>
                      <p class="text-muted mb-2">{{ q.core_goal }}</p>
                      <div class="q-detail-grid">
                        <div class="q-detail-item"><span class="q-detail-label">🏁 基线</span><span class="q-detail-value">{{ q.baseline_model }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">🚀 主模型</span><span class="q-detail-value" style="font-weight:600;color:var(--primary);">{{ q.main_model }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">🔄 备选</span><span class="q-detail-value">{{ (q.backup_models || []).join('、') }}</span></div>
                      </div>
                      <div class="mt-2 text-muted"><strong>理由：</strong>{{ q.model_reason }}</div>
                      <div class="q-detail-grid mt-2">
                        <div class="q-detail-item"><span class="q-detail-label">📐 公式要求</span><span class="q-detail-value">{{ (q.formula_requirements || []).join('；') }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">✅ 验证</span><span class="q-detail-value">{{ (q.validation || []).join('；') }}</span></div>
                      </div>
                      <div v-if="q.figures?.length" class="mt-2"><span class="text-muted">📈 图表：</span><el-tag v-for="fig in q.figures" :key="fig.figure_id" size="small" effect="plain" type="warning" style="margin:2px;">{{ fig.title }}</el-tag></div>
                      <div v-if="q.paper_sections?.length" class="mt-2"><span class="text-muted">📄 论文落位：{{ q.paper_sections.join(' → ') }}</span></div>
                    </div>
                  </div>

                  <template v-if="rubricAlignmentData?.items?.length">
                    <h4 class="section-sub">评分点对齐</h4>
                    <div class="rubric-table">
                      <div v-for="(item, ri) in rubricAlignmentData.items" :key="ri" class="rubric-row">
                        <span class="rubric-point">{{ item.rubric_point }}</span>
                        <span class="rubric-q">{{ item.question_id }}</span>
                        <span class="rubric-evidence">{{ (item.evidence_required || []).join('、') }}</span>
                        <span class="rubric-location">{{ (item.paper_location || []).join(' → ') }}</span>
                      </div>
                    </div>
                  </template>
                </div>

                <div v-if="!modelRouteData && !modelRouteLoading" class="empty-state">
                  <div class="empty-icon"><el-icon :size="32"><Guide /></el-icon></div>
                  <p style="font-size:var(--text-sm);">运行 S2 后在此查看模型路线与评分点对齐结果</p>
                </div>
              </div>

              <!-- S3-S4 数据处理 + 可视化计划 -->
              <div class="app-card step-card s3">
                <div class="app-card-header">
                  <span class="app-card-title">📊 S3-S4 数据处理 + 可视化</span>
                  <el-tag v-if="dataPlanData" type="success" size="small" effect="dark" round>已完成</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p class="card-desc">扫描数据文件生成画像，为每问规划清洗任务与图表类型，输出数据计划与可视化计划交接单。</p>
                  <el-button type="primary" :loading="dataPipelineLoading" :disabled="!isStepDone('S2')" @click="runDataPipeline" round>
                    {{ dataPipelineLoading ? '生成中...' : '运行 S3-S4 数据处理' }}
                  </el-button>
                  <div v-if="!['s2_completed','s4_completed','s5_completed','s6_completed','s7_completed','s7_check_passed'].includes(activeTask.status)" class="step-hint">⚠ 请先完成 S2 模型路线再运行 S3-S4 数据处理</div>
                  <div v-if="isStepDone('S4')" class="step-ok">✅ S3-S4 数据处理已完成，可重新运行</div>
                </div>

                <div v-if="dataPlanData" class="analysis-result">
                  <h4 class="section-title">📋 数据计划 ({{ dataPlanData.data_files?.length || 0 }} 个数据文件)</h4>
                  <div v-if="dataPlanData.data_files?.length" class="question-cards">
                    <div v-for="(df, i) in dataPlanData.data_files" :key="i" class="q-card" style="border-left:3px solid var(--step-s3);">
                      <div class="q-card-header">
                        <span style="font-weight:600;font-size:var(--text-sm);">{{ df.path?.split('/').pop() || '数据文件' }}</span>
                        <el-tag :type="df.readable ? 'success' : 'danger'" size="small" effect="dark" round>{{ df.readable ? '可读' : '不可读' }}</el-tag>
                        <el-tag type="info" size="small" effect="plain">{{ df.role }}</el-tag>
                      </div>
                      <div class="q-detail-grid cols-4">
                        <div class="q-detail-item"><span class="q-detail-label">📄 格式</span><span class="q-detail-value">{{ df.type }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">📐 列数</span><span class="q-detail-value">{{ (df.columns || []).length }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">📏 行数</span><span class="q-detail-value" style="font-weight:600;color:var(--primary);">{{ df.rows || '-' }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">💾 清洗输出</span><span class="q-detail-value" style="font-size:var(--text-xs);">{{ df.cleaned_output?.split('/').pop() }}</span></div>
                      </div>
                      <div class="mt-2 text-muted"><strong>列名：</strong>{{ (df.columns || []).join('、') || '无' }}</div>
                      <div v-if="df.numeric_columns?.length" class="mt-1 text-muted"><strong>数值列：</strong><el-tag v-for="c in df.numeric_columns" :key="c" size="small" effect="plain" type="primary" style="margin:1px;">{{ c }}</el-tag></div>
                      <div v-if="df.categorical_columns?.length" class="mt-1 text-muted"><strong>分类列：</strong><el-tag v-for="c in df.categorical_columns" :key="c" size="small" effect="plain" type="warning" style="margin:1px;">{{ c }}</el-tag></div>
                      <!-- 🆕 数据预览表格 -->
                      <div v-if="df.sample_rows?.length" class="mt-3">
                        <div class="data-preview-header">
                          <span class="data-preview-title">📋 数据预览（前 {{ df.sample_rows.length }} 行）</span>
                          <span class="text-muted">共 {{ df.rows || '?' }} 行</span>
                        </div>
                        <div class="data-preview-wrap">
                          <table class="data-preview-table">
                            <thead>
                              <tr>
                                <th class="row-num-col">#</th>
                                <th v-for="(col, ci) in df.columns" :key="ci">{{ col }}</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr v-for="(row, ri) in df.sample_rows" :key="ri">
                                <td class="row-num-col">{{ ri + 1 }}</td>
                                <td v-for="(cell, ci) in row" :key="ci" :title="cell">{{ cell }}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                      <div class="mt-2"><span class="text-muted">清洗任务：</span><el-tag v-for="t in (df.cleaning_tasks || [])" :key="t" size="small" effect="plain" type="info" style="margin:2px;">{{ t }}</el-tag></div>
                    </div>
                  </div>
                  <div v-else class="empty-state-sm">未检测到数据文件（CSV/Excel）。赛题可能为纯数学推导题。</div>

                  <template v-if="dataPlanData.question_links?.length">
                    <h4 class="section-sub">🔗 问题-字段映射</h4>
                    <div class="tag-row">
                      <div v-for="(ql, qi) in dataPlanData.question_links" :key="qi" class="field-link-card">
                        <strong>{{ ql.question_id }}</strong>
                        <span class="text-muted" style="margin-left:6px;">需要：{{ (ql.required_fields || []).join('、') || '无需字段' }}</span>
                        <br /><span class="text-muted">输出：{{ (ql.expected_outputs || []).join('、') }}</span>
                      </div>
                    </div>
                  </template>

                  <template v-if="vizPlanData?.figures?.length">
                    <h4 class="section-sub">📈 可视化计划 ({{ vizPlanData.figures.length }} 个图表)</h4>
                    <div class="rubric-table">
                      <div class="data-grid-header cols-6b"><span>图表ID</span><span>标题</span><span>类型</span><span>X轴</span><span>Y轴</span><span>论文落位</span></div>
                      <div v-for="(fig, fi) in vizPlanData.figures" :key="fi" class="data-grid-row cols-6b">
                        <span style="font-family:monospace;color:var(--primary);font-size:var(--text-xs);">{{ fig.figure_id }}</span>
                        <span>{{ fig.title }}</span>
                        <el-tag size="small" effect="plain" :type="fig.chart_type === 'bar' ? 'primary' : fig.chart_type === 'line' ? 'success' : 'warning'">{{ fig.chart_type }}</el-tag>
                        <span class="text-muted">{{ fig.candidate_x || '-' }}</span>
                        <span class="text-muted">{{ (fig.candidate_y || []).slice(0,2).join('、') || '-' }}</span>
                        <span class="text-muted">{{ fig.paper_usage }}</span>
                      </div>
                    </div>
                    <div class="text-muted mt-2">提示：{{ vizPlanData.note }}</div>
                  </template>

                  <template v-if="figuresData.length">
                    <h4 class="section-sub">🖼️ 生成的图表 ({{ figuresData.filter(f=>f.exists).length }}/{{ figuresData.length }} 张)</h4>
                    <div class="figure-grid">
                      <div v-for="(fig, fi) in figuresData.filter(f=>f.exists)" :key="fi" class="figure-card">
                        <img :src="getFigureImgUrl(fig)" :alt="fig.title" @error="$event.target.style.display='none'" />
                        <div class="figure-info"><strong>{{ fig.figure_id }}</strong><span>{{ fig.title }}</span><span style="margin-left:auto;color:var(--text-tertiary);">{{ (fig.file_size/1024).toFixed(0) }}KB</span></div>
                      </div>
                    </div>
                  </template>
                </div>

                <div v-if="!dataPlanData && !dataPipelineLoading" class="empty-state">
                  <div class="empty-icon"><el-icon :size="32"><DataAnalysis /></el-icon></div>
                  <p style="font-size:var(--text-sm);">运行 S3-S4 后在此查看数据画像与图表规划</p>
                </div>
              </div>

              <!-- S5 建模代码生成 + 结果契约 -->
              <div class="app-card step-card s5">
                <div class="app-card-header">
                  <span class="app-card-title">🤖 S5 建模代码 + 结果契约</span>
                  <el-tag v-if="modelContractData" type="success" size="small" effect="dark" round>已完成</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p class="card-desc">为每问生成建模代码脚手架，建立结果-指标-结论-表格四维证据契约，尝试运行脚手架产出数据。</p>
                  <el-button type="primary" :loading="modelContractLoading" :disabled="!isStepDone('S4')" @click="runModelContract" round>
                    {{ modelContractLoading ? '生成中...' : '运行 S5 建模代码' }}
                  </el-button>
                  <div v-if="!isStepDone('S4')" class="step-hint">⚠ 请先完成 S3-S4 数据处理再运行 S5 建模代码</div>
                  <div v-if="isStepDone('S5')" class="step-ok">✅ S5 建模代码已完成，可重新运行</div>
                </div>

                <div v-if="modelContractData" class="analysis-result">
                  <div class="q-detail-grid mb-3">
                    <div class="q-detail-item"><span class="q-detail-label">📋 问题数</span><span class="q-detail-value">{{ (modelContractData.model_results || []).length }}</span></div>
                    <div class="q-detail-item"><span class="q-detail-label">📊 表格数</span><span class="q-detail-value">{{ (modelContractData.tables || []).length }}</span></div>
                    <div class="q-detail-item"><span class="q-detail-label">📏 指标数</span><span class="q-detail-value">{{ (modelContractData.metrics || []).length }}</span></div>
                    <div class="q-detail-item"><span class="q-detail-label">✅ 结论数</span><span class="q-detail-value">{{ (modelContractData.conclusions || []).length }}</span></div>
                  </div>

                  <h4 class="section-title">结果契约 ({{ (modelContractData.model_results || []).length }} 个问题)</h4>
                  <div v-if="(modelContractData.model_results || []).length" class="question-cards">
                    <div v-for="r in modelContractData.model_results" :key="r.question_id" class="q-card" style="border-left:3px solid var(--step-s5);">
                      <div class="q-card-header">
                        <span class="q-id">{{ r.question_id }}</span>
                        <span class="q-title">{{ r.title }}</span>
                        <el-tag :type="taskTypeColor(r.task_type)" size="small" effect="dark" round>{{ r.task_type }}</el-tag>
                        <el-tag :type="r.evidence_status === 'needs_real_modeling' ? 'warning' : 'success'" size="small" effect="plain" round>{{ r.evidence_status }}</el-tag>
                      </div>
                      <p class="text-muted mb-2">{{ r.result_summary }}</p>
                      <div class="q-detail-grid">
                        <div class="q-detail-item"><span class="q-detail-label">🏁 基线</span><span class="q-detail-value">{{ r.baseline_model || '-' }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">🚀 主模型</span><span class="q-detail-value" style="font-weight:600;color:var(--primary);">{{ r.main_model }}</span></div>
                        <div class="q-detail-item"><span class="q-detail-label">📂 产出</span><span class="q-detail-value">{{ (r.outputs || []).map(o => o.name).join('、') || '无' }}</span></div>
                      </div>
                      <div v-if="(r.parameters || []).length" class="mt-2"><span class="text-muted">参数：</span><el-tag v-for="p in r.parameters" :key="p.name" size="small" effect="plain" type="info" style="margin:2px;">{{ p.name }}={{ p.value }}</el-tag></div>
                    </div>
                  </div>

                  <template v-if="(modelContractData.metrics || []).length">
                    <h4 class="section-sub">📏 指标契约</h4>
                    <div class="rubric-table">
                      <div class="data-grid-header cols-5"><span>问题</span><span>指标名</span><span>角色</span><span>值</span><span>状态</span></div>
                      <div v-for="(m, mi) in modelContractData.metrics.slice(0, 20)" :key="mi" class="data-grid-row cols-5">
                        <span style="font-family:monospace;color:var(--primary);font-size:var(--text-xs);">{{ m.question_id }}</span>
                        <span>{{ m.metric_name }}</span>
                        <span class="text-muted">{{ m.metric_role }}</span>
                        <span style="font-size:var(--text-xs);">{{ m.value !== null && m.value !== undefined ? m.value + (m.unit || '') : '待填' }}</span>
                        <el-tag size="small" effect="plain" :type="m.status === 'to_be_filled' ? 'warning' : 'info'">{{ m.status }}</el-tag>
                      </div>
                    </div>
                    <div v-if="modelContractData.metrics.length > 20" class="text-muted" style="text-align:center;padding:8px;">... 还有 {{ modelContractData.metrics.length - 20 }} 项</div>
                  </template>

                  <template v-if="(modelContractData.tables || []).length">
                    <h4 class="section-sub">📊 表格索引</h4>
                    <div class="rubric-table">
                      <div class="data-grid-header cols-6"><span>表格ID</span><span>问题</span><span>标题</span><span>用途</span><span>路径</span><span>状态</span></div>
                      <div v-for="(t, ti) in modelContractData.tables" :key="ti" class="data-grid-row cols-6">
                        <span style="font-family:monospace;color:var(--primary);font-size:var(--text-xs);">{{ t.table_id }}</span>
                        <span style="font-family:monospace;font-size:var(--text-xs);">{{ t.question_id }}</span>
                        <span style="font-size:var(--text-xs);">{{ t.title }}</span>
                        <span class="text-muted">{{ t.purpose }}</span>
                        <span class="text-muted">{{ (t.path || '').split('/').pop() }}</span>
                        <el-tag size="small" effect="plain" :type="t.status === 'draft_contract' ? 'warning' : 'info'">{{ t.status }}</el-tag>
                      </div>
                    </div>
                  </template>

                  <template v-if="(modelContractData.conclusions || []).length">
                    <h4 class="section-sub">📝 结论契约</h4>
                    <div v-for="(c, ci) in modelContractData.conclusions" :key="ci" style="display:flex;gap:8px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--border-light);font-size:var(--text-xs);">
                      <el-tag size="small" effect="dark" round style="flex-shrink:0;">{{ c.question_id }}</el-tag>
                      <span style="color:var(--text-secondary);flex:1;">{{ c.conclusion_text }}</span>
                      <el-tag size="small" effect="plain" :type="c.evidence_status === 'needs_real_modeling' ? 'warning' : 'success'" style="flex-shrink:0;">{{ c.evidence_status }}</el-tag>
                    </div>
                  </template>
                </div>

                <div v-if="!modelContractData && !modelContractLoading" class="empty-state">
                  <div class="empty-icon"><el-icon :size="32"><Guide /></el-icon></div>
                  <p style="font-size:var(--text-sm);">运行 S5 后在此查看建模代码与结果契约</p>
                </div>
              </div>

              <!-- S6 证据门禁 -->
              <div class="app-card step-card s6">
                <div class="app-card-header">
                  <span class="app-card-title">🔒 S6 证据门禁</span>
                  <el-tag v-if="evidenceGateData?.status === 'PASS'" type="success" size="small" effect="dark" round>PASS</el-tag>
                  <el-tag v-else-if="evidenceGateData?.status === 'FAIL'" type="danger" size="small" effect="dark" round>FAIL</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p class="card-desc">验证 S0-S5 产出证据完整性：模型结果、指标、结论、表格 + 评分点对齐。</p>
                  <el-button type="primary" :loading="evidenceGateLoading" :disabled="!isStepDone('S5')" @click="runEvidenceGate" round>
                    {{ evidenceGateLoading ? '检查中...' : '运行 S6 证据门禁' }}
                  </el-button>
                  <div v-if="!isStepDone('S5')" class="step-hint">⚠ 请先完成 S5 建模代码再运行 S6</div>
                  <div v-if="isStepDone('S6')" class="step-ok">✅ S6 证据门禁通过，可以进入 S7</div>
                </div>

                <div v-if="evidenceGateData" class="analysis-result">
                  <div class="result-status" :class="evidenceGateData.status === 'PASS' ? 'pass' : 'fail'">
                    <el-icon :size="18"><CircleCheck v-if="evidenceGateData.status === 'PASS'" /><CircleClose v-else /></el-icon>
                    <span>{{ evidenceGateData.status === 'PASS' ? '证据门禁通过！' : '存在证据缺口，需修复' }}</span>
                  </div>
                  <div v-if="evidenceGateData.summary" class="stat-minis">
                    <div class="stat-mini"><div class="stat-mini-val" style="color:var(--primary);">{{ evidenceGateData.summary.total_checks }}</div><div class="stat-mini-lbl">总检查</div></div>
                    <div class="stat-mini"><div class="stat-mini-val" style="color:var(--success);">{{ evidenceGateData.summary.passed }}</div><div class="stat-mini-lbl">通过</div></div>
                    <div class="stat-mini"><div class="stat-mini-val" style="color:var(--danger);">{{ evidenceGateData.summary.failed }}</div><div class="stat-mini-lbl">失败</div></div>
                    <div class="stat-mini"><div class="stat-mini-val" style="color:var(--warning);">{{ evidenceGateData.summary.warnings }}</div><div class="stat-mini-lbl">警告</div></div>
                  </div>
                  <div v-if="(evidenceGateData.failures || []).length" class="mt-2">
                    <h4 style="font-size:var(--text-sm);font-weight:600;color:var(--danger);margin-bottom:4px;">失败项</h4>
                    <div v-for="(f, fi) in evidenceGateData.failures" :key="fi" class="err-item err">{{ f }}</div>
                  </div>
                  <div v-if="(evidenceGateData.questions || []).length" class="mt-4">
                    <h4 class="section-title">逐问检查</h4>
                    <div v-for="q in evidenceGateData.questions" :key="q.question_id" style="padding:10px 0;border-bottom:1px solid var(--border-light);display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                      <span style="font-weight:600;font-size:var(--text-sm);">{{ q.question_id }}</span>
                      <el-tag v-for="item in q.items" :key="item.check" :type="item.status === 'PASS' ? 'success' : item.status === 'WARN' ? 'warning' : 'danger'" size="small" effect="plain" round>{{ item.check }}</el-tag>
                    </div>
                  </div>
                </div>
                <div v-if="!evidenceGateData && !evidenceGateLoading" class="empty-state">
                  <div class="empty-icon"><el-icon :size="32"><Lock /></el-icon></div>
                  <p style="font-size:var(--text-sm);">运行 S6 后在此查验证据门禁结果</p>
                </div>
              </div>

              <!-- S7 论文生成 + 格式检查 -->
              <div class="app-card step-card s7">
                <div class="app-card-header">
                  <span class="app-card-title">📝 S7 论文生成 + 格式检查</span>
                  <el-tag v-if="formatCheckData?.status === 'PASS'" type="success" size="small" effect="dark" round>已通过</el-tag>
                  <el-tag v-else-if="paperData" type="warning" size="small" effect="dark" round>已生成</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p class="card-desc">基于 S0-S6 全部合约生成完整学术论文，检查格式合规性。</p>
                  <div class="btn-row">
                    <el-button type="primary" :loading="paperWritingLoading" :disabled="!isStepDone('S6')" @click="runPaperWriting" round>📝 {{ paperWritingLoading ? '生成中...' : '生成论文' }}</el-button>
                    <el-button type="primary" :loading="paperStreaming" :disabled="!isStepDone('S6')" @click="startStreamingGeneration" round :style="{background: paperStreaming ? '#e74c3c' : '#165DFF', borderColor: paperStreaming ? '#e74c3c' : '#165DFF'}">
                      📺 {{ paperStreaming ? '生成中...' : '分屏生成' }}
                    </el-button>
                    <el-button type="warning" :loading="formatCheckLoading" :disabled="!isStepDone('S7')" @click="runFormatCheck" round>🔍 {{ formatCheckLoading ? '检查中...' : '格式检查' }}</el-button>
                    <el-button type="success" :disabled="!paperData" @click="downloadPaper" round>📥 下载 MD</el-button>
                    <el-button type="success" :disabled="!paperData" @click="downloadPaperDocx" round>📄 下载 Word</el-button>
                  </div>
                  <div v-if="!isStepDone('S6')" class="step-hint">⚠ 请先通过 S6 证据门禁</div>
                  <div v-if="isStepDone('S7')" class="step-ok">✅ 论文已生成，可重新生成</div>

                  <!-- 🆕 分屏流式预览 -->
                  <div v-if="showSplitPreview" class="split-preview-container mt-3">
                    <div class="split-toolbar">
                      <span class="split-toolbar-title">📺 双栏实时生成预览</span>
                      <span class="text-muted" style="font-size:12px;">
                        {{ paperStreaming ? '⏳ 正在生成...' : '✅ 生成完成' }} |
                        已生成 {{ streamWordCount.toLocaleString() }} 字
                      </span>
                      <el-button v-if="paperStreaming" size="small" type="danger" @click="stopStreaming" round>⏹ 停止生成</el-button>
                      <el-button v-if="!paperStreaming && streamingPaperMd" size="small" type="success" @click="saveStreamedPaper" round>💾 保存论文</el-button>
                      <el-button size="small" @click="closeSplitPreview" round>✕ 关闭</el-button>
                    </div>
                    <div class="split-panels">
                      <!-- 左栏：AI 编辑区 -->
                      <div class="split-editor-pane">
                        <div class="split-pane-header">✏️ AI 编辑区（Markdown 原文）</div>
                        <textarea
                          class="split-editor-textarea"
                          :value="streamingPaperMd"
                          readonly
                          placeholder="等待 AI 生成论文内容..."
                          ref="streamEditorRef"
                        ></textarea>
                      </div>
                      <!-- 右栏：实时渲染预览 -->
                      <div class="split-preview-pane">
                        <div class="split-pane-header">👁 实时预览（Word 风格排版）</div>
                        <div class="paper-preview markdown-body" v-html="renderedStreamPreview"></div>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-if="paperData" class="analysis-result">
                  <div class="q-detail-grid mb-3">
                    <div class="q-detail-item"><span class="q-detail-label">📏 字数</span><span class="q-detail-value">{{ paperData.word_count || '-' }}</span></div>
                    <div class="q-detail-item"><span class="q-detail-label">📑 章节</span><span class="q-detail-value">{{ paperData.sections_count || '-' }}</span></div>
                  </div>

                  <div v-if="formatCheckData" class="mt-4">
                    <div class="result-status" :class="formatCheckData.status === 'PASS' ? 'pass' : 'fail'">
                      <el-icon :size="18"><CircleCheck v-if="formatCheckData.status === 'PASS'" /><CircleClose v-else /></el-icon>
                      <span>{{ formatCheckData.status === 'PASS' ? '格式检查通过！论文合格' : '格式问题待修复 — 请点击下方按钮自动修复' }}</span>
                    </div>
                    <div v-if="(formatCheckData.checks || []).length" class="mt-2">
                      <div v-for="(c, ci) in formatCheckData.checks" :key="ci" class="err-item" :class="c.status === 'FAIL' ? 'err' : c.status === 'WARN' ? 'warn' : ''">
                        <el-tag :type="c.status === 'PASS' ? 'success' : c.status === 'WARN' ? 'warning' : 'danger'" size="small" effect="dark" round style="margin-right:8px;">{{ c.status }}</el-tag>
                        <span style="font-size:var(--text-xs);">{{ c.detail }}</span>
                      </div>
                    </div>
                    <!-- 🆕 修复论文按钮 -->
                    <div v-if="hasFormatFailures" class="mt-3" style="text-align:center;padding:12px;background:var(--danger-bg);border-radius:10px;border:1px solid rgba(245,63,63,0.2);">
                      <p style="font-size:var(--text-sm);color:var(--danger);font-weight:600;margin-bottom:10px;">
                        ⚠️ 格式检查发现 {{ formatFailCount }} 项失败、{{ formatWarnCount }} 项警告，建议修复
                      </p>
                      <el-button type="danger" :loading="fixPaperLoading" :icon="Warning" @click="fixPaper" round>
                        {{ fixPaperLoading ? '修复中...' : '🔧 修复并重新生成论文' }}
                      </el-button>
                      <p class="text-muted mt-2" style="margin-top:8px;">将自动补充缺失章节、扩充字数、增加代码和引用</p>
                    </div>
                  </div>

                  <div class="mt-4" v-if="paperData.draft_paper">
                    <div class="paper-toolbar">
                      <span class="paper-toolbar-title">📄 论文预览</span>
                      <span class="text-muted">{{ (paperData.draft_paper || '').length }} 字符</span>
                    </div>
                    <div class="paper-render markdown-body" v-html="renderedPaper"></div>
                  </div>
                </div>

                <div v-if="!paperData && !paperWritingLoading" class="empty-state">
                  <div class="empty-icon"><el-icon :size="32"><Document /></el-icon></div>
                  <p style="font-size:var(--text-sm);">通过 S6 门禁后在此生成论文</p>
                </div>
              </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 新建任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建竞赛任务" width="440px" :close-on-click-modal="false">
      <el-form @submit.prevent="createTask">
        <el-form-item label="任务名称">
          <el-input v-model="newTaskTitle" placeholder="例如：2024国赛B题——生产过程中的决策问题" maxlength="200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false" round>取消</el-button>
        <el-button type="primary" @click="createTask" :loading="creatingTask" round>创建任务</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { competitionApi } from '../api'
import Sidebar from '../components/Sidebar.vue'
import { marked } from 'marked'
import { renderAllMath } from '../composables/useKatex'
import {
  HomeFilled, Trophy, Plus, UploadFilled, Document, Delete,
  CircleCheck, CircleClose, DataAnalysis, Guide, Lock,
  Search, Coin, PictureFilled, Monitor, Finished, Clock, Warning
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

// 状态
const loading = ref(false)
const tasks = ref([])
const activeTaskId = ref(null)
const activeTask = ref({})
const uploadedFiles = ref([])
const preflightLoading = ref(false)
const preflightData = ref(null)
const analysisLoading = ref(false)
const analysisData = ref(null)
const modelRouteLoading = ref(false)
const modelRouteData = ref(null)
const rubricAlignmentData = ref(null)
const dataPipelineLoading = ref(false)
const dataPlanData = ref(null)
const vizPlanData = ref(null)
const figuresData = ref([])
const modelContractLoading = ref(false)
const modelContractData = ref(null)
const evidenceGateLoading = ref(false)
const evidenceGateData = ref(null)
const paperWritingLoading = ref(false)
const paperData = ref(null)
const formatCheckLoading = ref(false)
const formatCheckData = ref(null)
const fixPaperLoading = ref(false)  // 🆕 论文修复

// 🆕 流式双栏生成
const paperStreaming = ref(false)
const streamingPaperMd = ref('')
const showSplitPreview = ref(false)
const abortController = ref(null)
const streamWordCount = ref(0)

const showCreateDialog = ref(false)
const newTaskTitle = ref('')
const creatingTask = ref(false)

const fileInputRef = ref(null)

// 上传请求头
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

// 步骤完成判断 (CMP-010: 进度可视化)
const stepStatusMap = {
  'S0': ['s0_passed', 's1_completed', 's2_completed', 's4_completed', 's5_completed', 's6_completed', 's6_failed', 's7_completed', 's7_check_passed'],
  'S1': ['s1_completed', 's2_completed', 's4_completed', 's5_completed', 's6_completed', 's6_failed', 's7_completed', 's7_check_passed'],
  'S2': ['s2_completed', 's4_completed', 's5_completed', 's6_completed', 's6_failed', 's7_completed', 's7_check_passed'],
  'S3': ['s4_completed', 's5_completed', 's6_completed', 's6_failed', 's7_completed', 's7_check_passed'],
  'S4': ['s4_completed', 's5_completed', 's6_completed', 's6_failed', 's7_completed', 's7_check_passed'],
  'S5': ['s5_completed', 's6_completed', 's6_failed', 's7_completed', 's7_check_passed'],
  'S6': ['s6_completed', 's6_failed', 's7_completed', 's7_check_passed'],
  'S7': ['s7_completed', 's7_check_passed'],
  'S8': ['s7_check_passed'],
}
function isStepDone(step) {
  const statuses = stepStatusMap[step] || []
  return statuses.includes(activeTask.value?.status)
}
const completedSteps = computed(() => {
  let count = 0
  for (const step of ['S0','S1','S2','S3','S4','S5','S6','S7','S8']) {
    if (isStepDone(step)) count++
  }
  return count
})

// 🆕 论文渲染（Markdown + LaTeX + 图片）
const renderedPaper = computed(() => {
  const raw = paperData.value?.draft_paper
  if (!raw) return '<p style="color:var(--text-tertiary);">(暂无内容)</p>'

  // Step 1: 修复图片路径 — 将相对路径转为 API 端点
  let processed = raw.replace(
    /!\[([^\]]*)\]\(([^)]+)\)/g,
    (match, alt, src) => {
      // 跳过外部 URL
      if (src.startsWith('http://') || src.startsWith('https://')) return match
      // 提取文件名
      const filename = src.split('/').pop()
      const token = localStorage.getItem('token')
      const apiUrl = `/api/competition/tasks/${activeTaskId.value}/figures/${filename}?token=${encodeURIComponent(token || '')}`
      return `![${alt}](${apiUrl})`
    }
  )

  // Step 2: 渲染 LaTeX 公式
  processed = renderAllMath(processed)

  // Step 3: 渲染 Markdown
  let html = ''
  try {
    html = marked.parse(processed, { breaks: false, gfm: true })
  } catch {
    html = `<pre>${processed.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</pre>`
  }

  return html
})

// 🆕 流式预览渲染（与 renderedPaper 相同的管线）
const renderedStreamPreview = computed(() => {
  if (!streamingPaperMd.value) return '<p style="color:#999;text-align:center;padding:40px;">等待 AI 生成论文内容...</p>'
  let md = streamingPaperMd.value
  // Step 1: 修复图片路径
  md = md.replace(
    /!\[(.*?)\]\((?!https?:\/\/)(.*?)\)/g,
    (_m, alt, src) => {
      const filename = src.split('/').pop()
      const token = localStorage.getItem('token')
      const apiUrl = `/api/competition/tasks/${activeTaskId.value}/figures/${filename}?token=${encodeURIComponent(token || '')}`
      return `![${alt}](${apiUrl})`
    }
  )
  // Step 2: 渲染 LaTeX
  md = renderAllMath(md)
  // Step 3: 渲染 Markdown
  let html = ''
  try {
    html = marked.parse(md, { breaks: false, gfm: true })
  } catch {
    html = `<pre>${md.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</pre>`
  }
  return html
})

// 🆕 格式检查失败统计
const hasFormatFailures = computed(() => {
  if (!formatCheckData.value?.checks) return false
  return formatCheckData.value.checks.some(c => c.status === 'FAIL' || c.status === 'WARN')
})
const formatFailCount = computed(() => {
  if (!formatCheckData.value?.checks) return 0
  return formatCheckData.value.checks.filter(c => c.status === 'FAIL').length
})
const formatWarnCount = computed(() => {
  if (!formatCheckData.value?.checks) return 0
  return formatCheckData.value.checks.filter(c => c.status === 'WARN').length
})

// 断点恢复提示 (CMP-014)
const resumeHint = computed(() => {
  return resumeHintForTask(activeTask.value)
})
function resumeHintForTask(t) {
  if (!t) return ''
  const s = t.status
  const hints = {
    'created': '请先上传赛题文件',
    'files_uploaded': '运行 S0 预检',
    's0_passed': '运行 S1 赛题分析',
    's1_completed': '运行 S2 模型路线',
    's2_completed': '运行 S3-S4 数据处理',
    's4_completed': '运行 S5 建模代码',
    's5_completed': '运行 S6 证据门禁',
    's6_completed': '运行 S7 论文生成',
    's7_completed': '运行 S7 格式检查',
    's7_check_passed': '✅ 全部完成',
    's0_failed': 'S0 预检未通过',
    's6_failed': 'S6 门禁未通过',
  }
  return hints[s] || '继续任务'
}

// 🆕 计算任意任务的完成步骤数
function getTaskCompletedSteps(t) {
  if (!t) return 0
  let count = 0
  const statuses = stepStatusMap
  for (const step of ['S0','S1','S2','S3','S4','S5','S6','S7','S8']) {
    const valid = statuses[step] || []
    if (valid.includes(t.status)) count++
  }
  return count
}

// 🆕 任务状态标签类型
function taskStatusType(t) {
  if (!t) return 'info'
  const s = t.status
  if (s === 's7_check_passed') return 'success'
  if (s === 's0_failed' || s === 's6_failed') return 'danger'
  if (s === 'created' || s === 'files_uploaded') return 'info'
  return ''
}

// 🆕 任务状态可读标签
function taskStatusLabel(t) {
  if (!t) return '未知'
  const s = t.status
  const labels = {
    'created': '新建',
    'files_uploaded': '已上传文件',
    's0_passed': 'S0 预检通过',
    's0_failed': 'S0 预检失败',
    's1_completed': 'S1 分析完成',
    's2_completed': 'S2 路线完成',
    's4_completed': 'S4 数据处理完成',
    's5_completed': 'S5 代码完成',
    's6_completed': 'S6 门禁通过',
    's6_failed': 'S6 门禁失败',
    's7_completed': 'S7 论文生成',
    's7_check_passed': '✅ 全部完成',
  }
  return labels[s] || s
}

// 🆕 卡片强调色
function taskAccentColor(t) {
  if (!t) return 'var(--border-light)'
  const s = t.status
  if (s === 's7_check_passed') return 'linear-gradient(135deg, #00B42A, #14C9C9)'
  if (s === 's0_failed' || s === 's6_failed') return 'linear-gradient(135deg, #F53F3F, #FF7D00)'
  if (s === 'created' || s === 'files_uploaded') return 'var(--border-light)'
  // 进行中 — 蓝色渐变
  return 'linear-gradient(135deg, #165DFF, #722ED1)'
}

// 🆕 日期格式化
function formatDate(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff/3600000)}小时前`
  const m = d.getMonth() + 1
  const day = d.getDate()
  return `${m}月${day}日`
}

// 附件清单
const manifestEntries = computed(() => {
  try {
    const m = preflightData.value?.input_manifest
    if (typeof m === 'object' && m.entries) return m.entries
    if (typeof m === 'string') return JSON.parse(m).entries || []
  } catch (e) { return [] }
  return []
})

// ===== 任务管理 =====

async function loadTasks() {
  loading.value = true
  try {
    const res = await competitionApi.listTasks()
    tasks.value = res.tasks || []
    // 恢复上次选中的任务
    const saved = localStorage.getItem('active_competition_task')
    if (saved && tasks.value.find(t => t.id === Number(saved))) {
      await selectTaskById(Number(saved))
    }
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

async function selectTaskById(id) {
  activeTaskId.value = id
  localStorage.setItem('active_competition_task', id)
  await refreshTask()
}

async function selectTask(task) {
  await selectTaskById(task.id)
}

async function refreshTask() {
  if (!activeTaskId.value) return
  try {
    activeTask.value = await competitionApi.getTask(activeTaskId.value)
    await loadFiles()
    await loadPreflightFromDB()
    await loadAnalysisFromDB()
    await loadModelRouteFromDB()
    await loadDataPipelineFromDB()
    await loadModelContractFromDB()
    await loadEvidenceGateFromDB()
    await loadPaperFromDB()
    await loadFormatCheckFromDB()
  } catch (e) { /* ignore */ }
}

async function createTask() {
  if (!newTaskTitle.value.trim()) return
  creatingTask.value = true
  try {
    const task = await competitionApi.createTask({ title: newTaskTitle.value.trim() })
    tasks.value.unshift(task)
    showCreateDialog.value = false
    newTaskTitle.value = ''
    await selectTaskById(task.id)
  } catch (e) { /* ignore */ }
  finally { creatingTask.value = false }
}

async function deleteTask(id) {
  try {
    await competitionApi.deleteTask(id)
    tasks.value = tasks.value.filter(t => t.id !== id)
    if (activeTaskId.value === id) {
      activeTaskId.value = null
      activeTask.value = {}
      preflightData.value = null
      analysisData.value = null
      modelRouteData.value = null
      rubricAlignmentData.value = null
      dataPlanData.value = null
      vizPlanData.value = null
      modelContractData.value = null
      evidenceGateData.value = null
      paperData.value = null
      formatCheckData.value = null
      uploadedFiles.value = []
      localStorage.removeItem('active_competition_task')
    }
  } catch (e) { /* ignore */ }
}

// ===== 文件管理 =====

async function loadFiles() {
  if (!activeTaskId.value) return
  try {
    const res = await competitionApi.listFiles(activeTaskId.value)
    uploadedFiles.value = res.files || []
  } catch (e) { /* ignore */ }
}

function triggerFileUpload() {
  fileInputRef.value?.click()
}

async function onFileInputChange(e) {
  const files = e.target.files
  if (!files || files.length === 0) return
  await uploadFiles(files)
  if (fileInputRef.value) fileInputRef.value.value = ''
}

async function onFileDrop(e) {
  const files = e.dataTransfer?.files
  if (!files || files.length === 0) return
  await uploadFiles(files)
}

async function uploadFiles(fileList) {
  if (!activeTaskId.value) return
  const formData = new FormData()
  for (const f of fileList) {
    formData.append('files', f)
  }
  try {
    await competitionApi.uploadFiles(activeTaskId.value, formData)
    await loadFiles()
    await refreshTask()
    ElMessage.success(`成功上传 ${fileList.length} 个文件`)
  } catch (err) {
    console.error('Upload failed', err)
    ElMessage.error('上传失败: ' + (err.response?.data?.detail || err.message))
  }
}

function onUploadSuccess() {
  loadFiles()
  refreshTask()
}

function onUploadError(err) {
  console.error('Upload failed', err)
}

// ===== S0 预检 =====

async function runPreflight() {
  if (!activeTaskId.value) return
  preflightLoading.value = true
  preflightData.value = null
  try {
    const res = await competitionApi.runPreflight(activeTaskId.value)
    preflightData.value = res.preflight_report || res
    await refreshTask()
  } catch (e) {
    console.error(e)
    preflightData.value = { status: 'FAIL', errors: [e.response?.data?.detail || '预检请求失败'], warnings: [], input_manifest: { entries: [] } }
  }
  finally { preflightLoading.value = false }
}

async function loadPreflightFromDB() {
  if (!activeTaskId.value) return
  try {
    const res = await competitionApi.getPreflight(activeTaskId.value)
    if (res.preflight_report && Object.keys(res.preflight_report).length > 0) {
      preflightData.value = res.preflight_report
    }
  } catch (e) { /* ignore */ }
}

// ===== S1 赛题分析 =====

async function runAnalysis() {
  if (!activeTaskId.value) return
  analysisLoading.value = true
  analysisData.value = null
  try {
    const res = await competitionApi.runAnalysis(activeTaskId.value)
    analysisData.value = res.problem_analysis || res
    await refreshTask()
  } catch (e) {
    console.error(e)
    analysisData.value = { questions: [], documents: [], data_files: [], error: e.response?.data?.detail || '分析请求失败' }
  }
  finally { analysisLoading.value = false }
}

async function loadAnalysisFromDB() {
  if (!activeTaskId.value) return
  try {
    const res = await competitionApi.getAnalysis(activeTaskId.value)
    if (res.problem_analysis && Object.keys(res.problem_analysis).length > 0) {
      analysisData.value = res.problem_analysis
    }
  } catch (e) { /* ignore */ }
}

// ===== S2 模型路线 =====

async function runModelRoute() {
  if (!activeTaskId.value) return
  modelRouteLoading.value = true
  modelRouteData.value = null
  rubricAlignmentData.value = null
  try {
    const res = await competitionApi.runModelRoute(activeTaskId.value)
    modelRouteData.value = res.model_route || res
    rubricAlignmentData.value = res.rubric_alignment || {}
    await refreshTask()
  } catch (e) {
    console.error(e)
    modelRouteData.value = { questions: [], error: e.response?.data?.detail || '模型路线生成失败' }
  }
  finally { modelRouteLoading.value = false }
}

async function loadModelRouteFromDB() {
  if (!activeTaskId.value) return
  try {
    const res = await competitionApi.getModelRoute(activeTaskId.value)
    if (res.model_route && Object.keys(res.model_route).length > 0) {
      modelRouteData.value = res.model_route
      rubricAlignmentData.value = res.rubric_alignment || {}
    }
  } catch (e) { /* ignore */ }
}

// ===== S3-S4 数据处理 + 可视化计划 =====

async function runDataPipeline() {
  if (!activeTaskId.value) return
  dataPipelineLoading.value = true
  dataPlanData.value = null
  vizPlanData.value = null
  try {
    const res = await competitionApi.runDataPipeline(activeTaskId.value)
    dataPlanData.value = res.data_plan || res
    vizPlanData.value = res.visualization_plan || {}
    await loadFigures()
    await refreshTask()
  } catch (e) {
    console.error(e)
    dataPlanData.value = { data_files: [], question_links: [], error: e.response?.data?.detail || '数据处理失败' }
  }
  finally { dataPipelineLoading.value = false }
}

async function loadDataPipelineFromDB() {
  if (!activeTaskId.value) return
  try {
    const res = await competitionApi.getDataPipeline(activeTaskId.value)
    if (res.data_plan && Object.keys(res.data_plan).length > 0) {
      dataPlanData.value = res.data_plan
    }
    if (res.visualization_plan && Object.keys(res.visualization_plan).length > 0) {
      vizPlanData.value = res.visualization_plan
    }
  } catch (e) { /* ignore */ }
  loadFigures() // also load figure images
}

// 🆕 加载已生成的图表列表
async function loadFigures() {
  if (!activeTaskId.value) return
  try {
    const res = await competitionApi.getFigures(activeTaskId.value)
    figuresData.value = res.figures || []
  } catch (e) { figuresData.value = [] }
}

// 🆕 获取图表图片URL
function getFigureImgUrl(fig) {
  if (!activeTaskId.value) return ''
  const base = competitionApi.getFigureUrl(activeTaskId.value, fig.path || '')
  // <img> 标签不经过axios，需要把token拼在URL里
  const token = localStorage.getItem('token')
  return token ? `${base}?token=${encodeURIComponent(token)}` : base
}

// ===== S5 建模代码生成 + 结果契约 =====

async function runModelContract() {
  if (!activeTaskId.value) return
  modelContractLoading.value = true
  modelContractData.value = null
  try {
    const res = await competitionApi.runModelContract(activeTaskId.value)
    modelContractData.value = res.model_contract || res
    await refreshTask()
  } catch (e) {
    console.error(e)
    modelContractData.value = { model_results: [], metrics: [], conclusions: [], tables: [], error: e.response?.data?.detail || '建模代码生成失败' }
  }
  finally { modelContractLoading.value = false }
}

async function loadModelContractFromDB() {
  if (!activeTaskId.value) return
  try {
    const res = await competitionApi.getModelContract(activeTaskId.value)
    if (res.model_contract && Object.keys(res.model_contract).length > 0) {
      modelContractData.value = res.model_contract
    }
  } catch (e) { /* ignore */ }
}

// ===== S6 证据门禁 =====

async function runEvidenceGate() {
  if (!activeTaskId.value) return
  evidenceGateLoading.value = true
  evidenceGateData.value = null
  try {
    const res = await competitionApi.runEvidenceGate(activeTaskId.value)
    evidenceGateData.value = res.gate_report || res
    await refreshTask()
  } catch (e) {
    console.error(e)
    evidenceGateData.value = { status: 'FAIL', summary: { total_checks: 0, passed: 0, failed: 1, warnings: 0 }, questions: [], failures: [e.response?.data?.detail || '证据门禁请求失败'] }
  }
  finally { evidenceGateLoading.value = false }
}

async function loadEvidenceGateFromDB() {
  if (!activeTaskId.value) return
  try {
    const res = await competitionApi.getEvidenceGate(activeTaskId.value)
    if (res.gate_report && Object.keys(res.gate_report).length > 0) {
      evidenceGateData.value = res.gate_report
    }
  } catch (e) { /* ignore */ }
}

// ===== S7 论文生成 =====

async function runPaperWriting() {
  if (!activeTaskId.value) return
  paperWritingLoading.value = true
  paperData.value = null
  try {
    await competitionApi.runPaperWriting(activeTaskId.value)
    // POST 不返回全文，通过 refreshTask → loadPaperFromDB GET 加载完整论文
    await refreshTask()
  } catch (e) {
    console.error(e)
    paperData.value = { draft_paper: e.response?.data?.detail || '论文生成失败', word_count: 0, sections_count: 0 }
  }
  finally { paperWritingLoading.value = false }
}

// ===== 🆕 流式双栏论文生成 =====

async function startStreamingGeneration() {
  if (!activeTaskId.value) return
  paperStreaming.value = true
  showSplitPreview.value = true
  streamingPaperMd.value = ''
  streamWordCount.value = 0

  const ctrl = new AbortController()
  abortController.value = ctrl

  try {
    const response = await competitionApi.streamPaperWriting(activeTaskId.value, ctrl.signal)
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const dataStr = line.slice(6)
        try {
          const data = JSON.parse(dataStr)
          if (data.type === 'chunk') {
            streamingPaperMd.value += data.content
            streamWordCount.value = streamingPaperMd.value.replace(/\s/g, '').length
          }
        } catch {}
      }
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      streamingPaperMd.value += '\n\n*[生成已停止]*'
    } else {
      streamingPaperMd.value += `\n\n*[连接错误: ${e.message}]*`
    }
  } finally {
    paperStreaming.value = false
    abortController.value = null
    // 生成完成后刷新任务
    await refreshTask()
  }
}

function stopStreaming() {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  paperStreaming.value = false
}

function closeSplitPreview() {
  stopStreaming()
  showSplitPreview.value = false
  streamingPaperMd.value = ''
}

function saveStreamedPaper() {
  // 将流式内容保存到 paperData 并退出分屏
  if (streamingPaperMd.value) {
    paperData.value = {
      draft_paper: streamingPaperMd.value,
      word_count: streamWordCount.value,
      sections_count: (streamingPaperMd.value.match(/^##\s+/gm) || []).length,
    }
  }
  showSplitPreview.value = false
}

// 🆕 自动滚动到流式编辑器底部
const streamEditorRef = ref(null)
watch(streamingPaperMd, () => {
  if (streamEditorRef.value) {
    streamEditorRef.value.scrollTop = streamEditorRef.value.scrollHeight
  }
})

// ===== S7 论文加载 =====

async function loadPaperFromDB() {
  if (!activeTaskId.value) return
  try {
    const res = await competitionApi.getPaper(activeTaskId.value)
    if (res.draft_paper || (res.paper && Object.keys(res.paper).length > 0)) {
      paperData.value = { draft_paper: res.draft_paper, paper: res.paper, word_count: res.word_count, sections_count: res.sections_count }
    }
  } catch (e) { /* ignore */ }
}

// ===== S7 格式检查 =====

async function runFormatCheck() {
  if (!activeTaskId.value) return
  formatCheckLoading.value = true
  formatCheckData.value = null
  try {
    const res = await competitionApi.runFormatCheck(activeTaskId.value)
    formatCheckData.value = res.format_report || res
    await refreshTask()
  } catch (e) {
    console.error(e)
    formatCheckData.value = { status: 'FAIL', checks: [{ check: '错误', status: 'FAIL', detail: e.response?.data?.detail || '格式检查失败' }] }
  }
  finally { formatCheckLoading.value = false }
}

async function loadFormatCheckFromDB() {
  if (!activeTaskId.value) return
  try {
    const res = await competitionApi.getFormatCheck(activeTaskId.value)
    if (res.format_report && Object.keys(res.format_report).length > 0) {
      formatCheckData.value = res.format_report
    }
  } catch (e) { /* ignore */ }
}

// 🆕 修复论文（格式检查失败后自动修复）
async function fixPaper() {
  if (!activeTaskId.value) return
  fixPaperLoading.value = true
  try {
    const res = await competitionApi.fixPaper(activeTaskId.value)
    // 更新论文数据
    paperData.value = {
      draft_paper: '',
      paper: res.paper,
      word_count: res.word_count,
      sections_count: res.sections_count,
    }
    // 🆕 直接用返回的格式检查结果更新（清除红色警告）
    if (res.format_check && Object.keys(res.format_check).length > 0) {
      formatCheckData.value = res.format_check
    }
    // 刷新任务状态和论文全文
    await refreshTask()
    ElMessage.success('论文已修复！格式检查：' + (res.format_check?.status === 'PASS' ? '✅ 通过' : '⚠️ 仍有问题'))
  } catch (e) {
    console.error(e)
    ElMessage.error('论文修复失败: ' + (e.response?.data?.detail || e.message))
  }
  finally { fixPaperLoading.value = false }
}

// ===== 论文下载 =====

function downloadPaper() {
  if (!activeTaskId.value) return
  const token = localStorage.getItem('token')
  const a = document.createElement('a')
  a.href = `/api/competition/tasks/${activeTaskId.value}/paper/download?token=${encodeURIComponent(token || '')}`
  a.download = `paper_task${activeTaskId.value}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

// 🆕 下载 Word 版本
function downloadPaperDocx() {
  if (!activeTaskId.value) return
  const token = localStorage.getItem('token')
  const a = document.createElement('a')
  // 加时间戳防缓存
  const ts = Date.now()
  a.href = `/api/competition/tasks/${activeTaskId.value}/paper/download-docx?token=${encodeURIComponent(token || '')}&t=${ts}`
  a.download = `paper_task${activeTaskId.value}.docx`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  ElMessage.success('正在下载 Word 文档...')
}

// ===== 辅助函数 =====

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function fileIconColor(ext) {
  const m = { '.pdf': '#F53F3F', '.docx': '#2B7FFF', '.md': '#0FC6C2', '.txt': '#86909C', '.csv': '#00B42A', '.xlsx': '#00B42A', '.xls': '#00B42A', '.json': '#FF7D00' }
  return m[ext] || '#86909C'
}

function stepTagType(step) {
  const m = { 'S0': 'info', 'S1': 'warning', 'S2': 'success' }
  return m[step] || ''
}

function roleTagType(role) {
  if (role?.includes('unreadable')) return 'danger'
  if (role === 'problem_statement') return 'primary'
  if (role === 'raw_data') return 'success'
  if (role === 'result_template') return 'warning'
  if (role === 'unsupported') return 'info'
  return 'info'
}

function roleLabel(role) {
  const m = {
    problem_statement: '题面',
    problem_statement_unreadable: '题面(不可读)',
    raw_data: '原始数据',
    raw_data_unreadable: '数据(不可读)',
    result_template: '结果模板',
    unsupported: '未识别',
  }
  return m[role] || role
}

function taskTypeColor(type) {
  const m = {
    '预测/回归': 'primary',
    '优化/规划': 'success',
    '评价/排序': 'warning',
    '分类/识别': 'danger',
    '聚类/分群': 'info',
    '机理/仿真': '',
    '综合建模/统计分析': '',
  }
  return m[type] || 'info'
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped lang="scss">
// ============================================================
// 竞赛训练页 — 完整重设计
// 设计语言：明亮学术工坊 · 渐变强调 · 卡片层次 · 微动效
// ============================================================

// —— 设计令牌（SCSS 变量） ——
$step-colors: (
  s0: #165DFF, s1: #722ED1, s2: #FF7D00, s3: #00B42A,
  s4: #14C9C9, s5: #4F46E5, s6: #F53F3F, s7: #D4A017,
);
$step-bgs: (
  s0: #E8F0FE, s1: #F3E8FF, s2: #FFF3E8, s3: #E8FFF0,
  s4: #E8FFFF, s5: #EDECFF, s6: #FFF0F0, s7: #FFFBE8,
);
$step-grads: (
  s0: linear-gradient(135deg, #E8F0FE, #D4E4FD),
  s1: linear-gradient(135deg, #F3E8FF, #E8D6FE),
  s2: linear-gradient(135deg, #FFF3E8, #FFE4CC),
  s3: linear-gradient(135deg, #E8FFF0, #D0F5DC),
  s4: linear-gradient(135deg, #E8FFFF, #D0F5F5),
  s5: linear-gradient(135deg, #EDECFF, #DDDBFA),
  s6: linear-gradient(135deg, #FFF0F0, #FDE0E0),
  s7: linear-gradient(135deg, #FFFBE8, #FFF3CC),
);

// ===========================================
// 1. 训练记录卡片网格
// ===========================================
.training-records-section { margin-bottom: 24px; }
.section-header-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.section-heading {
  font-size: var(--text-lg); font-weight: 700; color: var(--text-primary);
  margin: 0;
}

.training-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}

.training-card {
  background: var(--bg-card); border-radius: 14px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: all 0.3s var(--ease-out);
  overflow: hidden;
  display: flex; flex-direction: column;
  &:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg);
    border-color: var(--primary);
  }
  &.active {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(22,93,255,0.1), var(--shadow-md);
  }
}

.card-accent {
  height: 4px; width: 100%; flex-shrink: 0;
}

.card-body {
  padding: 16px 20px 18px;
  display: flex; flex-direction: column; gap: 10px;
  flex: 1;
}

.card-title-row {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 8px;
}
.card-title {
  font-size: var(--text-sm); font-weight: 700; color: var(--text-primary);
  margin: 0; line-height: 1.45; flex: 1;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-delete-btn { flex-shrink: 0; opacity: 0.5; transition: opacity 0.2s;
  .training-card:hover & { opacity: 1; }
}

.card-badges {
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}

.badge-ok {
  font-size: var(--text-xs); color: var(--success);
  background: var(--success-bg); padding: 2px 8px; border-radius: 10px;
  font-weight: 500;
}
.badge-fail {
  font-size: var(--text-xs); color: var(--danger);
  background: var(--danger-bg); padding: 2px 8px; border-radius: 10px;
  font-weight: 500;
}
.badge-done {
  font-size: var(--text-xs); color: var(--success); font-weight: 500;
}

// 迷你进度条
.card-progress {
  display: flex; flex-direction: column; gap: 4px;
}
.card-progress-header {
  display: flex; justify-content: space-between;
  font-size: 11px; color: var(--text-tertiary);
}
.card-progress-bar {
  height: 5px; background: var(--bg-primary); border-radius: 3px;
  overflow: hidden;
}
.card-progress-fill {
  height: 100%; background: var(--primary); border-radius: 3px;
  transition: width 0.5s var(--ease-out);
}

// 底部信息
.card-footer {
  display: flex; align-items: center; gap: 12px;
  margin-top: 2px;
}
.card-meta {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; color: var(--text-tertiary);
}
.card-active-tag {
  margin-left: auto;
  font-size: 10px; color: var(--primary);
  background: var(--primary-light); padding: 2px 8px; border-radius: 10px;
  font-weight: 600;
}

// ===========================================
// 2. 步骤指示器 — 浮动药丸风格
// ===========================================
.step-indicator {
  display: flex; align-items: center; justify-content: center; gap: 0;
  padding: 20px 0; margin-bottom: 20px; flex-wrap: wrap;
  background: var(--bg-card); border: 1px solid var(--border-light);
  border-radius: 16px; box-shadow: var(--shadow-sm);
}
.step-dot {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 8px 11px; border-radius: 12px;
  background: var(--bg-primary); border: 2px solid transparent;
  min-width: 58px; cursor: default;
  transition: all 0.3s var(--ease-out);
  position: relative;

  &.active {
    border-color: var(--primary); background: var(--primary-light);
    box-shadow: 0 0 16px rgba(22,93,255,0.18);
    animation: pulse-glow 2s ease-in-out infinite;
    .step-icon { color: var(--primary); transform: scale(1.15); }
    .step-num { color: var(--primary); font-weight: 700; }
    .step-label { color: var(--primary); }
  }
  &.done {
    border-color: var(--success); background: var(--success-bg);
    .step-icon { color: var(--success); }
    .step-num { color: var(--success); }
  }
}
.step-icon {
  font-size: 17px; line-height: 1; color: var(--text-tertiary);
  transition: all 0.3s var(--ease-out);
  .step-dot.done & { animation: checkBounce 0.4s var(--ease-out); }
}
.step-num {
  font-size: 11px; font-weight: 600; color: var(--text-secondary);
  font-family: var(--font-mono); transition: color 0.3s;
}
.step-label { font-size: 10px; color: var(--text-tertiary); transition: color 0.3s; }
.step-line {
  width: 24px; height: 2px; background: var(--border-light);
  border-radius: 1px; transition: all 0.4s var(--ease-out);
  &.done { background: linear-gradient(90deg, var(--success), var(--primary)); }
}

// ===========================================
// 3. 进度条
// ===========================================
.progress-bar-wrap { margin-bottom: 20px; }
.progress-bar-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;
}
.progress-label { font-size: var(--text-xs); color: var(--text-secondary); font-weight: 500; }
.progress-value { font-size: var(--text-xs); font-weight: 600; color: var(--primary); }

// ===========================================
// 4. 工作区
// ===========================================
.work-area { display: flex; flex-direction: column; gap: 18px; }

// ===========================================
// 5. 上传区
// ===========================================
.upload-zone {
  display: block; width: 100%; margin-bottom: 14px;
  border: 2px dashed var(--color-slate-400); border-radius: 12px;
  background: linear-gradient(180deg, #FAFBFC, #F7F8FA);
  padding: 32px 20px; text-align: center; cursor: pointer;
  transition: all 0.3s var(--ease-out);
  &:hover {
    border-color: var(--primary); background: var(--primary-light);
    transform: translateY(-1px); box-shadow: var(--shadow-md);
  }
  &:active { transform: scale(0.985); }
}
.upload-text {
  p { margin: 4px 0; font-size: var(--text-sm); color: var(--text-primary); }
  .upload-hint { font-size: var(--text-xs); color: var(--text-tertiary); margin-top: 6px; }
}

// 文件列表
.file-list { display: flex; flex-direction: column; gap: 4px; max-height: 200px; overflow-y: auto; }
.file-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  border-radius: 8px; background: var(--bg-primary); font-size: var(--text-sm);
  transition: background 0.2s;
  &:hover { background: var(--bg-hover); }
}
.file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.file-size { font-size: var(--text-xs); color: var(--text-tertiary); flex-shrink: 0; }

// ===========================================
// 6. 步骤卡片 (S0-S7)
// ===========================================
.step-card {
  border-left: 4px solid transparent;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s var(--ease-out);
  &:hover { box-shadow: var(--shadow-md); }

  @each $key, $color in $step-colors {
    &.#{$key} {
      border-left-color: $color;
      .app-card-header {
        background: map-get($step-bgs, $key);
        border-radius: 7px 7px 0 0;
        margin: -1px -1px 0 -1px;
        padding: 14px 24px;
        border-bottom: 1px solid rgba($color, 0.15);
      }
      .app-card-title {
        color: $color;
      }
    }
  }
}

// ===========================================
// 7. 结果面板
// ===========================================
.analysis-result {
  padding: 20px 24px 24px;
  border-top: 1px solid var(--border-light);
  animation: slideUp 0.35s var(--ease-out);
}
.result-status {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; border-radius: 10px;
  font-size: var(--text-sm); font-weight: 600;
  &.pass { background: var(--success-bg); color: var(--success); border: 1px solid rgba(0,180,42,0.15); }
  &.fail { background: var(--danger-bg); color: var(--danger); border: 1px solid rgba(245,63,63,0.15); }
}

// 附件清单
.manifest-table { display: flex; flex-direction: column; gap: 4px; }
.manifest-row {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  background: var(--bg-primary); border-radius: 8px; font-size: var(--text-xs);
}
.manifest-file { flex: 1; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

// 错误/警告
.err-item {
  font-size: var(--text-xs); padding: 6px 12px; border-radius: 6px;
  margin-bottom: 3px; line-height: 1.5; display: flex; align-items: flex-start; gap: 6px;
  &.err { background: var(--danger-bg); color: var(--danger); }
  &.warn { background: var(--warning-bg); color: var(--warning); }
}

// ===========================================
// 8. 子问题卡片
// ===========================================
.question-cards { display: flex; flex-direction: column; gap: 12px; }
.q-card {
  padding: 16px 18px; border: 1px solid var(--border-light);
  border-radius: 12px; background: var(--bg-primary);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s;
  &:hover { box-shadow: var(--shadow-md); }
}
.q-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.q-id {
  font-weight: 700; font-size: var(--text-xs); font-family: var(--font-mono);
  color: var(--primary); background: var(--primary-light);
  padding: 3px 10px; border-radius: 6px;
}
.q-title { font-size: var(--text-sm); font-weight: 600; flex: 1; color: var(--text-primary); }
.q-summary { font-size: var(--text-sm); color: var(--text-secondary); line-height: 1.65; margin-bottom: 10px; }
.q-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 14px; }
.q-detail-grid.cols-4 { grid-template-columns: 1fr 1fr 1fr 1fr; }
.q-detail-item { display: flex; flex-direction: column; gap: 2px; }
.q-detail-label { font-size: var(--text-xs); color: var(--text-tertiary); font-weight: 500; }
.q-detail-value { font-size: var(--text-xs); color: var(--text-primary); line-height: 1.45; }

// ===========================================
// 9. 表格（评分点 / 指标 / 表格索引 / 可视化计划）
// ===========================================
.rubric-table {
  display: flex; flex-direction: column; gap: 1px;
  background: var(--border-light); border-radius: 10px; overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.rubric-row {
  display: grid; grid-template-columns: 80px 50px 1fr 1fr;
  gap: 8px; padding: 8px 14px; background: var(--bg-primary);
  font-size: var(--text-xs); align-items: center;
}
.rubric-point { font-weight: 600; color: var(--primary); }
.rubric-q { color: var(--text-tertiary); font-family: var(--font-mono); }
.rubric-evidence { color: var(--text-secondary); }
.rubric-location { color: var(--text-tertiary); font-size: var(--text-xs); }

// 通用数据网格表头
.data-grid-header {
  display: grid; gap: 6px; padding: 8px 14px;
  font-size: var(--text-xs); color: var(--text-tertiary);
  font-weight: 600; background: var(--bg-tertiary);
  border-radius: 8px 8px 0 0;
}
.data-grid-row {
  display: grid; gap: 6px; padding: 7px 14px;
  font-size: var(--text-xs); border-bottom: 1px solid var(--border-light);
  align-items: center; transition: background 0.15s;
  &:hover { background: var(--bg-primary); }
  &:last-child { border-bottom: none; }
}
.cols-5 { grid-template-columns: 0.8fr 1fr 1fr 0.6fr 0.8fr; }
.cols-6 { grid-template-columns: 1.2fr 0.7fr 1.2fr 1.5fr 0.8fr 0.8fr; }
.cols-6b { grid-template-columns: 1fr 1.5fr 1fr 1fr 0.8fr 1.2fr; }

// ===========================================
// 10. 图表缩略图响应式网格
// ===========================================
.figure-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}
.figure-card {
  border: 1px solid var(--border-light); border-radius: 10px;
  overflow: hidden; background: #fff;
  box-shadow: var(--shadow-sm);
  transition: transform 0.25s var(--ease-out), box-shadow 0.25s var(--ease-out);
  &:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
  img { width: 100%; height: auto; display: block; }
  .figure-info {
    padding: 8px 12px; font-size: var(--text-xs); color: var(--text-secondary);
    background: var(--bg-secondary); display: flex; align-items: center; gap: 6px;
  }
}

// ===========================================
// 11. 论文预览
// 11. 论文预览 — Markdown + LaTeX 全文渲染
// ===========================================
.paper-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: var(--bg-tertiary);
  border-radius: 10px 10px 0 0; border: 1px solid var(--border-light);
  border-bottom: none;
}
.paper-toolbar-title { font-size: var(--text-sm); font-weight: 600; color: var(--text-primary); }

.paper-render {
  background: #fff; border: 1px solid var(--border-light);
  border-top: none; border-radius: 0 0 10px 10px;
  padding: 28px 32px;
  max-height: 70vh; overflow-y: auto;
  font-size: var(--text-sm); line-height: 1.9; color: var(--text-primary);

  h1 { font-size: var(--text-xl); font-weight: 700; margin: 1.2em 0 0.6em; color: var(--text-primary);
       padding-bottom: 0.4em; border-bottom: 2px solid var(--primary); }
  h2 { font-size: var(--text-lg); font-weight: 700; margin: 1em 0 0.5em; color: var(--text-primary);
       padding-bottom: 0.3em; border-bottom: 1px solid var(--border-light); }
  h3 { font-size: var(--text-md); font-weight: 600; margin: 0.8em 0 0.4em; color: var(--text-primary); }
  h4 { font-size: var(--text-sm); font-weight: 600; margin: 0.6em 0 0.3em; color: var(--text-secondary); }
  p { margin-bottom: 0.8em; text-align: justify; }
  strong { font-weight: 700; color: var(--text-primary); }
  em { font-style: italic; }
  ul, ol { padding-left: 1.8em; margin: 0.5em 0; }
  li { margin-bottom: 0.25em; }
  li > ul, li > ol { margin-top: 0.25em; }
  blockquote {
    margin: 0.8em 0; padding: 0.6em 1em;
    border-left: 3px solid var(--primary);
    background: var(--primary-light);
    border-radius: 0 6px 6px 0; color: var(--text-secondary);
  }
  table {
    width: 100%; border-collapse: collapse; margin: 0.8em 0; font-size: var(--text-xs);
    th { background: var(--bg-tertiary); font-weight: 600; text-align: left;
         padding: 8px 12px; border: 1px solid var(--border-light); }
    td { padding: 6px 12px; border: 1px solid var(--border-light); }
    tbody tr:nth-child(even) td { background: #FAFBFC; }
  }
  code { background: #F0F1F5; padding: 2px 6px; border-radius: 4px;
         font-size: 0.9em; font-family: var(--font-mono); color: #D63384; }
  pre { background: #F2F3F8; padding: 12px 16px; border-radius: 8px;
        overflow-x: auto; margin: 0.8em 0;
        code { background: none; padding: 0; color: inherit; } }
  hr { border: none; border-top: 1px solid var(--border-light); margin: 1.2em 0; }
  a { color: var(--primary); text-decoration: underline; }
  img { max-width: 100%; height: auto; border-radius: 8px; margin: 0.6em 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
  .katex-display { overflow-x: auto; overflow-y: hidden; padding: 0.3em 0; margin: 0.5em 0; }
  .katex { font-size: 1.05em; }
}

// ===========================================
// 12. 数据预览表格
// ===========================================
.data-preview-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px;
}
.data-preview-title {
  font-size: var(--text-xs); font-weight: 600; color: var(--text-primary);
}
.data-preview-wrap {
  overflow-x: auto; border: 1px solid var(--border-light);
  border-radius: 8px; max-height: 260px; overflow-y: auto;
  background: #fff;
}
.data-preview-table {
  width: 100%; border-collapse: collapse; font-size: 11px;
  white-space: nowrap;
  th {
    position: sticky; top: 0; z-index: 2;
    background: var(--bg-tertiary); color: var(--text-secondary);
    font-weight: 600; padding: 6px 10px; text-align: left;
    border-bottom: 1px solid var(--border-light);
  }
  td {
    padding: 5px 10px; border-bottom: 1px solid #f5f5f5;
    color: var(--text-primary); max-width: 140px;
    overflow: hidden; text-overflow: ellipsis;
  }
  tbody tr:hover { background: var(--primary-light); }
  .row-num-col {
    text-align: center; color: var(--text-tertiary);
    font-family: var(--font-mono); width: 36px; min-width: 36px;
    background: var(--bg-tertiary); font-size: 10px;
  }
}

// ===========================================
// 13. 统计小卡片（S6门禁用）
// ===========================================
.stat-minis {
  display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px;
}
.stat-mini {
  text-align: center; padding: 12px 20px; background: var(--bg-primary);
  border-radius: 10px; border: 1px solid var(--border-light);
  min-width: 80px;
  .stat-mini-val { font-size: var(--text-xl); font-weight: 700; line-height: 1.2; }
  .stat-mini-lbl { font-size: var(--text-xs); color: var(--text-tertiary); margin-top: 4px; }
}

// ===========================================
// 13. 问题-字段链接卡片
// ===========================================
.field-link-card {
  background: var(--bg-tertiary); border-radius: 8px;
  padding: 10px 14px; font-size: var(--text-xs);
  border: 1px solid var(--border-light);
}

// ===========================================
// 14. 按钮行
// ===========================================
.btn-row { display: flex; gap: 8px; flex-wrap: wrap; }

// ===========================================
// 15. 工具类（替代全部内联样式）
// ===========================================
.card-desc { font-size: var(--text-sm); color: var(--text-secondary); margin-bottom: 14px; line-height: 1.6; }
.step-hint { font-size: var(--text-xs); color: var(--text-tertiary); margin-top: 8px; }
.step-hint-warn { font-size: var(--text-xs); color: var(--text-tertiary); margin-top: 8px; }
.step-ok { font-size: var(--text-xs); color: var(--success); margin-top: 8px; font-weight: 500; }
.empty-state { text-align: center; padding: 36px 0; color: var(--text-tertiary); }
.empty-state-sm { text-align: center; padding: 20px; color: var(--text-tertiary); font-size: var(--text-sm); }
.empty-icon { font-size: 36px; color: var(--text-tertiary); margin-bottom: 8px; }
.section-title { font-size: var(--text-sm); font-weight: 600; margin-bottom: 10px; color: var(--text-primary); }
.section-sub { font-size: var(--text-sm); font-weight: 600; margin: 18px 0 8px; color: var(--text-primary); }
.section-label { font-size: var(--text-xs); color: var(--text-tertiary); margin-bottom: 4px; }
.text-muted { color: var(--text-tertiary); font-size: var(--text-xs); }
.text-muted-sm { font-size: var(--text-xs); color: var(--text-tertiary); }
.text-accent { color: var(--primary); font-size: var(--text-xs); }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.mt-4 { margin-top: 16px; }
.mb-2 { margin-bottom: 8px; }
.mb-3 { margin-bottom: 12px; }
.flex-wrap { display: flex; flex-wrap: wrap; }
.info-inline { display: flex; gap: 16px; flex-wrap: wrap; align-items: center; }
.divider-top { border-top: 1px solid var(--border-light); }

// ===========================================
// 16. 任务上下文横幅
// ===========================================
.task-banner {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 24px; border-radius: 14px;
  background: var(--grad-subtle); border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm); margin-bottom: 20px; flex-wrap: wrap; gap: 12px;
}
.task-banner-left { display: flex; align-items: center; gap: 12px; min-width: 0; }
.task-banner-title { font-size: var(--text-md); font-weight: 700; color: var(--text-primary); }
.task-banner-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

.resume-badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: var(--text-xs); color: var(--primary);
  background: var(--primary-light); padding: 3px 10px; border-radius: 20px;
  font-weight: 500;
}

/* ========== 🆕 流式双栏预览 ========== */
.split-preview-container {
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--bg);
}
.split-toolbar {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border);
}
.split-toolbar-title {
  font-weight: 700; font-size: 14px; color: var(--primary);
}
.split-panels {
  display: flex; height: 75vh; min-height: 500px;
}
.split-editor-pane, .split-preview-pane {
  flex: 1; display: flex; flex-direction: column; overflow: hidden;
}
.split-editor-pane {
  border-right: 2px solid var(--border);
  background: #1e1e1e;
}
.split-preview-pane {
  background: #f8f9fa;
}
.split-pane-header {
  padding: 8px 12px;
  font-size: 12px; font-weight: 600; color: #666;
  background: #fff;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.split-editor-pane .split-pane-header {
  background: #2d2d2d; color: #ccc;
}
.split-editor-textarea {
  flex: 1; width: 100%; border: none; outline: none; resize: none;
  background: #1e1e1e; color: #d4d4d4;
  font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
  font-size: 13px; line-height: 1.6;
  padding: 16px; overflow-y: auto;
}
.split-editor-textarea::placeholder {
  color: #666;
}
.split-preview-pane .paper-preview {
  flex: 1; padding: 24px 32px; overflow-y: auto;
  max-width: 800px; margin: 0 auto;
  background: #fff;
  box-shadow: 0 0 20px rgba(0,0,0,0.05);
  font-family: '宋体', SimSun, serif;
  font-size: 14px; line-height: 1.8;
}
.split-preview-pane .paper-preview :deep(h1) {
  font-size: 22px; font-weight: 700; text-align: center; margin-bottom: 16px; font-family: '黑体', SimHei, sans-serif;
}
.split-preview-pane .paper-preview :deep(h2) {
  font-size: 18px; font-weight: 700; margin-top: 24px; margin-bottom: 12px; font-family: '黑体', SimHei, sans-serif; border-bottom: 1px solid #eee; padding-bottom: 6px;
}
.split-preview-pane .paper-preview :deep(h3) {
  font-size: 15px; font-weight: 600; margin-top: 18px; margin-bottom: 8px;
}
.split-preview-pane .paper-preview :deep(table) {
  border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 12px;
}
.split-preview-pane .paper-preview :deep(th), .split-preview-pane .paper-preview :deep(td) {
  border: 1px solid #333; padding: 4px 8px; text-align: center;
}
.split-preview-pane .paper-preview :deep(th) {
  background: #f0f0f0; font-weight: 600;
}
.split-preview-pane .paper-preview :deep(pre) {
  background: #f5f5f5; border-left: 4px solid #4472C4; padding: 12px 16px;
  overflow-x: auto; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px;
  line-height: 1.4; margin: 10px 0;
}
.split-preview-pane .paper-preview :deep(.katex-display) {
  overflow-x: auto; overflow-y: hidden;
}
.split-preview-pane .paper-preview :deep(img) {
  max-width: 100%; height: auto; display: block; margin: 8px auto;
}
</style>

