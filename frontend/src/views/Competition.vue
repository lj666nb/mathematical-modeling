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

        <!-- ===== 任务选择区 ===== -->
        <div v-if="!activeTaskId && !loading" class="app-card" style="text-align:center;padding:60px 20px;">
          <el-icon :size="48" style="color:var(--text-tertiary);margin-bottom:16px;"><Trophy /></el-icon>
          <h3 style="margin-bottom:8px;">选择一个竞赛任务</h3>
          <p style="color:var(--text-secondary);margin-bottom:20px;">从下方已有任务中选择，或创建新的竞赛任务开始训练</p>
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true" round>新建任务</el-button>
        </div>

        <!-- ===== 已有任务列表 ===== -->
        <div v-if="tasks.length > 0" class="app-card" style="margin-bottom:20px;">
          <div class="app-card-header">
            <span class="app-card-title">我的竞赛任务</span>
            <span style="font-size: var(--text-xs);color:var(--text-tertiary);">共 {{ tasks.length }} 个</span>
          </div>
          <div class="app-card-body" style="padding-top:12px;">
            <div class="task-list">
              <div
                v-for="t in tasks" :key="t.id"
                class="task-item"
                :class="{ active: activeTaskId === t.id }"
                @click="selectTask(t)"
              >
                <div class="task-item-main">
                  <span class="task-title">{{ t.title }}</span>
                  <div class="task-meta">
                    <el-tag :type="stepTagType(t.current_step)" size="small" effect="plain" round>{{ t.current_step }}</el-tag>
                    <span style="font-size: var(--text-xs);color:var(--text-tertiary);">{{ t.file_count }}个文件</span>
                    <span v-if="t.preflight_status === 'pass'" style="color:var(--success);font-size: var(--text-xs);">✓ 预检通过</span>
                    <span v-else-if="t.preflight_status === 'fail'" style="color:var(--danger);font-size: var(--text-xs);">✗ 预检失败</span>
                    <span v-if="t.status !== 's7_check_passed'" style="font-size: var(--text-xs);color:var(--primary);background:var(--primary-light);padding:1px 6px;border-radius:3px;" title="点击继续任务">🔄 {{ resumeHintForTask(t) }}</span>
                  </div>
                </div>
                <el-button text type="danger" size="small" :icon="Delete" @click.stop="deleteTask(t.id)" />
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 活跃任务工作区 ===== -->
        <template v-if="activeTaskId">
          <!-- 工作流步骤指示器 -->
          <div class="step-indicator">
            <div class="step-dot" :class="{ done: activeTask.preflight_status === 'pass', active: activeTask.current_step === 'S0' }">
              <span class="step-num">S0</span>
              <span class="step-label">预检</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S0') }"></div>
            <div class="step-dot" :class="{ done: isStepDone('S1'), active: activeTask.current_step === 'S1' }">
              <span class="step-num">S1</span>
              <span class="step-label">分析</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S1') }"></div>
            <div class="step-dot" :class="{ done: isStepDone('S2'), active: activeTask.current_step === 'S2' }">
              <span class="step-num">S2</span><span class="step-label">路线</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S3') }"></div>
            <div class="step-dot" :class="{ done: isStepDone('S3'), active: activeTask.current_step === 'S3' || activeTask.current_step === 'S4' }">
              <span class="step-num">S3</span><span class="step-label">数据</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S4') }"></div>
            <div class="step-dot" :class="{ done: isStepDone('S4'), active: false }">
              <span class="step-num">S4</span><span class="step-label">图表</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S5') }"></div>
            <div class="step-dot" :class="{ done: isStepDone('S5'), active: activeTask.current_step === 'S5' }">
              <span class="step-num">S5</span><span class="step-label">代码</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S6') }"></div>
            <div class="step-dot" :class="{ done: isStepDone('S6'), active: activeTask.current_step === 'S6' }">
              <span class="step-num">S6</span>
              <span class="step-label">门禁</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S7') }"></div>
            <div class="step-dot" :class="{ done: isStepDone('S7'), active: activeTask.current_step === 'S7' }">
              <span class="step-num">S7</span>
              <span class="step-label">论文</span>
            </div>
            <div class="step-line" :class="{ done: isStepDone('S8') }"></div>
            <div class="step-dot" :class="{ done: isStepDone('S8'), active: activeTask.current_step === 'S7_check' }">
              <span class="step-num">S8</span>
              <span class="step-label">提交</span>
            </div>
          </div>
          <!-- 进度条 -->
          <div style="margin-bottom:16px;padding:0 10px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
              <span style="font-size: var(--text-xs);color:var(--text-secondary);">整体进度</span>
              <span style="font-size: var(--text-xs);font-weight:600;color:var(--primary);">{{ completedSteps }}/8 步骤完成</span>
            </div>
            <div style="height:6px;background:var(--bg-primary);border-radius:3px;overflow:hidden;">
              <div :style="{ width: (completedSteps/8*100)+'%', height:'100%', background:'var(--primary)', borderRadius:'3px', transition:'width 0.5s' }"></div>
            </div>
          </div>

          <!-- 双栏布局 -->
          <div class="work-area">
            <!-- 左栏：文件上传 + S0 预检 -->
            <div class="work-left">
              <!-- 文件上传区 -->
              <div class="app-card">
                <div class="app-card-header">
                  <span class="app-card-title">📁 赛题文件</span>
                  <span style="font-size: var(--text-xs);color:var(--text-tertiary);">{{ uploadedFiles.length }} 个文件</span>
                </div>
                <div class="app-card-body">
                  <!-- 拖拽上传区 -->
                  <el-upload
                    class="upload-zone"
                    drag
                    multiple
                    name="files"
                    :action="`/api/competition/tasks/${activeTaskId}/upload`"
                    :headers="uploadHeaders"
                    :on-success="onUploadSuccess"
                    :on-error="onUploadError"
                    :show-file-list="false"
                  >
                    <el-icon :size="36" style="color:var(--primary);"><UploadFilled /></el-icon>
                    <div class="upload-text">
                      <p><strong>点击或拖拽上传赛题文件</strong></p>
                      <p class="upload-hint">支持 PDF / DOCX / MD / TXT / CSV / XLSX / JSON</p>
                    </div>
                  </el-upload>

                  <!-- 已上传文件列表 -->
                  <div v-if="uploadedFiles.length > 0" class="file-list">
                    <div v-for="f in uploadedFiles" :key="f.name" class="file-item">
                      <el-icon :size="16" :style="{ color: fileIconColor(f.ext) }"><Document /></el-icon>
                      <span class="file-name">{{ f.name }}</span>
                      <span class="file-size">{{ formatSize(f.size) }}</span>
                    </div>
                  </div>
                  <div v-else style="text-align:center;padding:20px;color:var(--text-tertiary);font-size: var(--text-sm);">
                    尚未上传文件 — 请上传赛题 PDF/Word 与数据附件
                  </div>
                </div>
              </div>

              <!-- S0 预检 -->
              <div class="app-card">
                <div class="app-card-header">
                  <span class="app-card-title">🔍 S0 预检</span>
                  <el-tag v-if="activeTask.preflight_status === 'pass'" type="success" size="small" effect="dark" round>PASS</el-tag>
                  <el-tag v-else-if="activeTask.preflight_status === 'fail'" type="danger" size="small" effect="dark" round>FAIL</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>未运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p style="font-size: var(--text-sm);color:var(--text-secondary);margin-bottom:12px;">
                    检查赛题文件完整性：识别题面/数据/结果模板，验证文件可读性和依赖项。
                  </p>
                  <el-button
                    type="primary"
                    :loading="preflightLoading"
                    :disabled="uploadedFiles.length === 0"
                    @click="runPreflight"
                    round
                  >
                    {{ preflightLoading ? '预检中...' : '运行 S0 预检' }}
                  </el-button>
                </div>

                <!-- 预检结果 -->
                <div v-if="preflightData" class="preflight-result">
                  <div class="result-status" :class="preflightData.status === 'PASS' ? 'pass' : 'fail'">
                    <el-icon :size="18"><CircleCheck v-if="preflightData.status === 'PASS'" /><CircleClose v-else /></el-icon>
                    <span>{{ preflightData.status === 'PASS' ? '预检通过！可以进入 S1 赛题分析' : '预检未通过，请修复以下问题' }}</span>
                  </div>

                  <!-- 附件清单 -->
                  <div v-if="manifestEntries.length > 0" style="margin-top:12px;">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin-bottom:8px;">附件清单</h4>
                    <div class="manifest-table">
                      <div v-for="entry in manifestEntries" :key="entry.path" class="manifest-row">
                        <span class="manifest-file">{{ entry.path }}</span>
                        <el-tag :type="roleTagType(entry.role)" size="small" effect="plain" round>
                          {{ roleLabel(entry.role) }}
                        </el-tag>
                        <span v-if="entry.char_count" style="font-size: var(--text-xs);color:var(--text-tertiary);">{{ entry.char_count }}字符</span>
                        <span v-if="entry.warnings?.length" style="color:var(--warning);font-size: var(--text-xs);">⚠{{ entry.warnings.length }}</span>
                        <span v-if="entry.errors?.length" style="color:var(--danger);font-size: var(--text-xs);">✗{{ entry.errors.length }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- 错误列表 -->
                  <div v-if="preflightData.errors?.length" style="margin-top:12px;">
                    <h4 style="font-size: var(--text-sm);font-weight:600;color:var(--danger);margin-bottom:6px;">错误 ({{ preflightData.errors.length }})</h4>
                    <div v-for="(e, i) in preflightData.errors" :key="'e'+i" class="err-item err">
                      {{ e }}
                    </div>
                  </div>

                  <!-- 警告列表 -->
                  <div v-if="preflightData.warnings?.length" style="margin-top:8px;">
                    <h4 style="font-size: var(--text-sm);font-weight:600;color:var(--warning);margin-bottom:6px;">警告 ({{ preflightData.warnings.length }})</h4>
                    <div v-for="(w, i) in preflightData.warnings" :key="'w'+i" class="err-item warn">
                      {{ w }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 右栏：S1 赛题分析 -->
            <div class="work-right">
              <div class="app-card">
                <div class="app-card-header">
                  <span class="app-card-title">📊 S1 赛题分析</span>
                  <el-tag v-if="analysisData" type="success" size="small" effect="dark" round>已完成</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p style="font-size: var(--text-sm);color:var(--text-secondary);margin-bottom:12px;">
                    自动拆分赛题为子问题，识别任务类型，推荐基线模型与改进方案。
                  </p>
                  <el-button
                    type="success"
                    :loading="analysisLoading"
                    :disabled="activeTask.preflight_status !== 'pass'"
                    @click="runAnalysis"
                    round
                  >
                    {{ analysisLoading ? '分析中...' : '运行 S1 赛题分析' }}
                  </el-button>
                  <div v-if="activeTask.preflight_status !== 'pass'" style="margin-top:8px;font-size: var(--text-xs);color:var(--text-tertiary);">
                    ⚠ 请先通过 S0 预检再运行赛题分析
                  </div>
                </div>

                <!-- S1 分析结果 -->
                <div v-if="analysisData" class="analysis-result">
                  <!-- 文档/数据概览 -->
                  <div v-if="analysisData.documents?.length || analysisData.data_files?.length" style="margin-bottom:16px;">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin-bottom:6px;">读取文件</h4>
                    <div style="display:flex;flex-wrap:wrap;gap:6px;">
                      <el-tag v-for="d in analysisData.documents" :key="d.path" size="small" effect="plain">
                        📄 {{ d.path }} ({{ d.chars }}字)
                      </el-tag>
                      <el-tag v-for="d in analysisData.data_files" :key="d.path" size="small" effect="plain" type="warning">
                        📊 {{ d.path }}
                      </el-tag>
                    </div>
                  </div>

                  <!-- 子问题卡片 -->
                  <h4 style="font-size: var(--text-sm);font-weight:600;margin-bottom:10px;">
                    子问题分析 ({{ analysisData.questions?.length || 0 }} 个问题)
                  </h4>
                  <div v-if="analysisData.questions?.length" class="question-cards">
                    <div v-for="q in analysisData.questions" :key="q.id" class="q-card">
                      <div class="q-card-header">
                        <span class="q-id">{{ q.id }}</span>
                        <span class="q-title">{{ q.title }}</span>
                        <el-tag :type="taskTypeColor(q.task_type)" size="small" effect="dark" round>{{ q.task_type }}</el-tag>
                      </div>
                      <p class="q-summary">{{ q.summary }}</p>
                      <div class="q-detail-grid">
                        <div class="q-detail-item">
                          <span class="q-detail-label">基线模型</span>
                          <span class="q-detail-value">{{ q.recommended_models?.baseline }}</span>
                        </div>
                        <div class="q-detail-item">
                          <span class="q-detail-label">改进方案</span>
                          <span class="q-detail-value">{{ q.recommended_models?.improved }}</span>
                        </div>
                        <div class="q-detail-item">
                          <span class="q-detail-label">验证计划</span>
                          <span class="q-detail-value">{{ (q.validation_plan || []).join('；') }}</span>
                        </div>
                        <div class="q-detail-item">
                          <span class="q-detail-label">建议图表</span>
                          <span class="q-detail-value">{{ (q.figure_suggestions || []).join('；') }}</span>
                        </div>
                      </div>
                      <div v-if="q.constraints?.length" style="margin-top:8px;">
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">约束条件：</span>
                        <el-tag v-for="(c, ci) in q.constraints.slice(0,3)" :key="ci" size="small" effect="plain" style="margin:2px;">{{ c }}</el-tag>
                      </div>
                    </div>
                  </div>
                  <div v-else style="text-align:center;padding:20px;color:var(--text-tertiary);">
                    未能自动拆分出子问题 — 请确认赛题文件包含明确的问题编号
                  </div>
                </div>

                <!-- 空状态 -->
                <div v-if="!analysisData && !analysisLoading" style="text-align:center;padding:30px 0;color:var(--text-tertiary);">
                  <el-icon :size="32"><DataAnalysis /></el-icon>
                  <p style="margin-top:8px;font-size: var(--text-sm);">运行 S1 后在此查看赛题结构化分析结果</p>
                </div>
              </div>

              <!-- S2 模型路线 -->
              <div class="app-card" style="margin-top:16px;">
                <div class="app-card-header">
                  <span class="app-card-title">🗺️ S2 模型路线</span>
                  <el-tag v-if="modelRouteData" type="success" size="small" effect="dark" round>已完成</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p style="font-size: var(--text-sm);color:var(--text-secondary);margin-bottom:12px;">
                    为每个子问题推荐基线模型、主模型与备选模型，映射评分点到论文落位，规划图表与公式要求。
                  </p>
                  <el-button
                    type="primary"
                    :loading="modelRouteLoading"
                    :disabled="activeTask.status !== 's1_completed' && activeTask.status !== 's2_completed' && activeTask.status !== 's4_completed'"
                    @click="runModelRoute"
                    round
                  >
                    {{ modelRouteLoading ? '生成中...' : '运行 S2 模型路线' }}
                  </el-button>
                  <div v-if="activeTask.status !== 's1_completed' && activeTask.status !== 's2_completed' && activeTask.status !== 's4_completed'" style="margin-top:8px;font-size: var(--text-xs);color:var(--text-tertiary);">
                    ⚠ 请先完成 S1 赛题分析再运行 S2 模型路线
                  </div>
                  <div v-if="['s2_completed','s4_completed','s5_completed'].includes(activeTask.status)" style="margin-top:8px;font-size: var(--text-xs);color:var(--success);">
                    ✅ S2 模型路线已完成，可重新运行
                  </div>
                </div>

                <!-- S2 结果 -->
                <div v-if="modelRouteData" class="analysis-result">
                  <h4 style="font-size: var(--text-sm);font-weight:600;margin-bottom:10px;">
                    模型路线 ({{ modelRouteData.questions?.length || 0 }} 个问题)
                  </h4>
                  <div v-if="modelRouteData.questions?.length" class="question-cards">
                    <div v-for="q in modelRouteData.questions" :key="q.question_id" class="q-card" style="border-left-color:var(--warning);">
                      <div class="q-card-header">
                        <span class="q-id">{{ q.question_id }}</span>
                        <span class="q-title">{{ q.title }}</span>
                        <el-tag :type="taskTypeColor(q.task_type)" size="small" effect="dark" round>{{ q.task_type }}</el-tag>
                      </div>
                      <p style="font-size: var(--text-xs);color:var(--text-secondary);margin:4px 0 8px;">{{ q.core_goal }}</p>
                      <div class="q-detail-grid">
                        <div class="q-detail-item">
                          <span class="q-detail-label">🏁 基线</span>
                          <span class="q-detail-value">{{ q.baseline_model }}</span>
                        </div>
                        <div class="q-detail-item">
                          <span class="q-detail-label">🚀 主模型</span>
                          <span class="q-detail-value" style="font-weight:600;color:var(--primary);">{{ q.main_model }}</span>
                        </div>
                        <div class="q-detail-item">
                          <span class="q-detail-label">🔄 备选</span>
                          <span class="q-detail-value">{{ (q.backup_models || []).join('、') }}</span>
                        </div>
                      </div>
                      <div style="margin-top:6px;font-size: var(--text-xs);color:var(--text-secondary);">
                        <strong>理由：</strong>{{ q.model_reason }}
                      </div>
                      <div class="q-detail-grid" style="margin-top:8px;">
                        <div class="q-detail-item">
                          <span class="q-detail-label">📐 公式要求</span>
                          <span class="q-detail-value">{{ (q.formula_requirements || []).join('；') }}</span>
                        </div>
                        <div class="q-detail-item">
                          <span class="q-detail-label">✅ 验证</span>
                          <span class="q-detail-value">{{ (q.validation || []).join('；') }}</span>
                        </div>
                      </div>
                      <div v-if="q.figures?.length" style="margin-top:8px;">
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">📈 图表：</span>
                        <el-tag v-for="fig in q.figures" :key="fig.figure_id" size="small" effect="plain" type="warning" style="margin:2px;">
                          {{ fig.title }}
                        </el-tag>
                      </div>
                      <div v-if="q.paper_sections?.length" style="margin-top:4px;">
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">📄 论文落位：{{ q.paper_sections.join(' → ') }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- 评分点对齐 -->
                  <template v-if="rubricAlignmentData?.items?.length">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin:16px 0 10px;">评分点对齐</h4>
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

                <!-- 空状态 -->
                <div v-if="!modelRouteData && !modelRouteLoading" style="text-align:center;padding:30px 0;color:var(--text-tertiary);">
                  <el-icon :size="32"><Guide /></el-icon>
                  <p style="margin-top:8px;font-size: var(--text-sm);">运行 S2 后在此查看模型路线与评分点对齐结果</p>
                </div>
              </div>

              <!-- S3-S4 数据处理 + 可视化计划 -->
              <div class="app-card" style="margin-top:16px;">
                <div class="app-card-header">
                  <span class="app-card-title">📊 S3-S4 数据处理 + 可视化</span>
                  <el-tag v-if="dataPlanData" type="success" size="small" effect="dark" round>已完成</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p style="font-size: var(--text-sm);color:var(--text-secondary);margin-bottom:12px;">
                    扫描数据文件生成画像，为每问规划清洗任务与图表类型，输出数据计划与可视化计划交接单。
                  </p>
                  <el-button
                    type="primary"
                    :loading="dataPipelineLoading"
                    :disabled="activeTask.status !== 's2_completed' && activeTask.status !== 's4_completed'"
                    @click="runDataPipeline"
                    round
                  >
                    {{ dataPipelineLoading ? '生成中...' : '运行 S3-S4 数据处理' }}
                  </el-button>
                  <div v-if="activeTask.status !== 's2_completed' && activeTask.status !== 's4_completed'" style="margin-top:8px;font-size: var(--text-xs);color:var(--text-tertiary);">
                    ⚠ 请先完成 S2 模型路线再运行 S3-S4 数据处理
                  </div>
                  <div v-if="['s4_completed','s5_completed'].includes(activeTask.status)" style="margin-top:8px;font-size: var(--text-xs);color:var(--success);">
                    ✅ S3-S4 数据处理已完成，可重新运行
                  </div>
                </div>

                <!-- S3-S4 结果 -->
                <div v-if="dataPlanData" class="analysis-result">
                  <!-- S3 数据计划 -->
                  <h4 style="font-size: var(--text-sm);font-weight:600;margin-bottom:10px;">
                    📋 数据计划 ({{ dataPlanData.data_files?.length || 0 }} 个数据文件)
                  </h4>
                  <div v-if="dataPlanData.data_files?.length" class="question-cards">
                    <div v-for="(df, i) in dataPlanData.data_files" :key="i" class="q-card" style="border-left-color:var(--success);">
                      <div class="q-card-header">
                        <span style="font-weight:600;font-size: var(--text-sm);">{{ df.path?.split('/').pop() || '数据文件' }}</span>
                        <el-tag :type="df.readable ? 'success' : 'danger'" size="small" effect="dark" round>{{ df.readable ? '可读' : '不可读' }}</el-tag>
                        <el-tag type="info" size="small" effect="plain">{{ df.role }}</el-tag>
                      </div>
                      <div class="q-detail-grid">
                        <div class="q-detail-item">
                          <span class="q-detail-label">📄 格式</span>
                          <span class="q-detail-value">{{ df.type }}</span>
                        </div>
                        <div class="q-detail-item">
                          <span class="q-detail-label">📐 列数</span>
                          <span class="q-detail-value">{{ (df.columns || []).length }}</span>
                        </div>
                        <div class="q-detail-item">
                          <span class="q-detail-label">💾 清洗输出</span>
                          <span class="q-detail-value" style="font-size: var(--text-xs);">{{ df.cleaned_output?.split('/').pop() }}</span>
                        </div>
                      </div>
                      <div style="margin-top:6px;font-size: var(--text-xs);color:var(--text-secondary);">
                        <strong>列名：</strong>{{ (df.columns || []).join('、') || '无' }}
                      </div>
                      <div v-if="df.numeric_columns?.length" style="margin-top:4px;font-size: var(--text-xs);color:var(--text-secondary);">
                        <strong>数值列：</strong>
                        <el-tag v-for="c in df.numeric_columns" :key="c" size="small" effect="plain" type="primary" style="margin:1px;">{{ c }}</el-tag>
                      </div>
                      <div v-if="df.categorical_columns?.length" style="margin-top:4px;font-size: var(--text-xs);color:var(--text-secondary);">
                        <strong>分类列：</strong>
                        <el-tag v-for="c in df.categorical_columns" :key="c" size="small" effect="plain" type="warning" style="margin:1px;">{{ c }}</el-tag>
                      </div>
                      <div style="margin-top:6px;">
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">清洗任务：</span>
                        <el-tag v-for="t in (df.cleaning_tasks || [])" :key="t" size="small" effect="plain" type="info" style="margin:2px;">{{ t }}</el-tag>
                      </div>
                    </div>
                  </div>
                  <div v-else style="text-align:center;padding:16px;color:var(--text-tertiary);font-size: var(--text-sm);">
                    未检测到数据文件（CSV/Excel）。赛题可能为纯数学推导题。
                  </div>

                  <!-- 问题-字段链接 -->
                  <template v-if="dataPlanData.question_links?.length">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin:16px 0 6px;">🔗 问题-字段映射</h4>
                    <div style="display:flex;flex-wrap:wrap;gap:8px;">
                      <div v-for="(ql, qi) in dataPlanData.question_links" :key="qi" style="background:var(--bg-tertiary);border-radius:8px;padding:8px 12px;font-size: var(--text-xs);">
                        <strong>{{ ql.question_id }}</strong>
                        <span style="color:var(--text-tertiary);margin-left:6px;">
                          需要：{{ (ql.required_fields || []).join('、') || '无需字段' }}
                        </span>
                        <br />
                        <span style="color:var(--text-tertiary);">
                          输出：{{ (ql.expected_outputs || []).join('、') }}
                        </span>
                      </div>
                    </div>
                  </template>

                  <!-- S4 可视化计划 -->
                  <template v-if="vizPlanData?.figures?.length">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin:16px 0 6px;">📈 可视化计划 ({{ vizPlanData.figures.length }} 个图表)</h4>
                    <div class="rubric-table">
                      <div style="display:grid;grid-template-columns:1fr 1.5fr 1fr 1fr 0.8fr 1.2fr;gap:6px;padding:6px 10px;font-size: var(--text-xs);color:var(--text-tertiary);font-weight:600;background:var(--bg-secondary);border-radius:6px 6px 0 0;">
                        <span>图表ID</span><span>标题</span><span>类型</span><span>X轴</span><span>Y轴</span><span>论文落位</span>
                      </div>
                      <div v-for="(fig, fi) in vizPlanData.figures" :key="fi" style="display:grid;grid-template-columns:1fr 1.5fr 1fr 1fr 0.8fr 1.2fr;gap:6px;padding:6px 10px;font-size: var(--text-xs);border-bottom:1px solid var(--border-light);align-items:center;">
                        <span style="font-family:monospace;color:var(--primary);font-size: var(--text-xs);">{{ fig.figure_id }}</span>
                        <span>{{ fig.title }}</span>
                        <el-tag size="small" effect="plain" :type="fig.chart_type === 'bar' ? 'primary' : fig.chart_type === 'line' ? 'success' : 'warning'">{{ fig.chart_type }}</el-tag>
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">{{ fig.candidate_x || '-' }}</span>
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">{{ (fig.candidate_y || []).slice(0,2).join('、') || '-' }}</span>
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">{{ fig.paper_usage }}</span>
                      </div>
                    </div>
                    <div style="margin-top:4px;font-size: var(--text-xs);color:var(--text-tertiary);">
                      提示：{{ vizPlanData.note }}
                    </div>
                  </template>
                </div>

                <!-- 空状态 -->
                <div v-if="!dataPlanData && !dataPipelineLoading" style="text-align:center;padding:30px 0;color:var(--text-tertiary);">
                  <el-icon :size="32"><DataAnalysis /></el-icon>
                  <p style="margin-top:8px;font-size: var(--text-sm);">运行 S3-S4 后在此查看数据画像与图表规划</p>
                </div>
              </div>

              <!-- S5 建模代码生成 + 结果契约 -->
              <div class="app-card" style="margin-top:16px;">
                <div class="app-card-header">
                  <span class="app-card-title">🤖 S5 建模代码 + 结果契约</span>
                  <el-tag v-if="modelContractData" type="success" size="small" effect="dark" round>已完成</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p style="font-size: var(--text-sm);color:var(--text-secondary);margin-bottom:12px;">
                    为每问生成建模代码脚手架，建立结果-指标-结论-表格四维证据契约，尝试运行脚手架产出数据。
                  </p>
                  <el-button
                    type="primary"
                    :loading="modelContractLoading"
                    :disabled="activeTask.status !== 's4_completed' && activeTask.status !== 's5_completed'"
                    @click="runModelContract"
                    round
                  >
                    {{ modelContractLoading ? '生成中...' : '运行 S5 建模代码' }}
                  </el-button>
                  <div v-if="activeTask.status !== 's4_completed' && activeTask.status !== 's5_completed'" style="margin-top:8px;font-size: var(--text-xs);color:var(--text-tertiary);">
                    ⚠ 请先完成 S3-S4 数据处理再运行 S5 建模代码
                  </div>
                  <div v-if="activeTask.status === 's5_completed'" style="margin-top:8px;font-size: var(--text-xs);color:var(--success);">
                    ✅ S5 建模代码已完成，可重新运行
                  </div>
                </div>

                <!-- S5 结果 -->
                <div v-if="modelContractData" class="analysis-result">
                  <!-- 结果契约概览 -->
                  <div class="q-detail-grid" style="margin-bottom:16px;">
                    <div class="q-detail-item">
                      <span class="q-detail-label">📋 问题数</span>
                      <span class="q-detail-value">{{ (modelContractData.model_results || []).length }}</span>
                    </div>
                    <div class="q-detail-item">
                      <span class="q-detail-label">📊 表格数</span>
                      <span class="q-detail-value">{{ (modelContractData.tables || []).length }}</span>
                    </div>
                    <div class="q-detail-item">
                      <span class="q-detail-label">📏 指标数</span>
                      <span class="q-detail-value">{{ (modelContractData.metrics || []).length }}</span>
                    </div>
                    <div class="q-detail-item">
                      <span class="q-detail-label">✅ 结论数</span>
                      <span class="q-detail-value">{{ (modelContractData.conclusions || []).length }}</span>
                    </div>
                  </div>

                  <!-- 每问结果 -->
                  <h4 style="font-size: var(--text-sm);font-weight:600;margin-bottom:10px;">
                    结果契约 ({{ (modelContractData.model_results || []).length }} 个问题)
                  </h4>
                  <div v-if="(modelContractData.model_results || []).length" class="question-cards">
                    <div v-for="r in modelContractData.model_results" :key="r.question_id" class="q-card" style="border-left-color:var(--primary);">
                      <div class="q-card-header">
                        <span class="q-id">{{ r.question_id }}</span>
                        <span class="q-title">{{ r.title }}</span>
                        <el-tag :type="taskTypeColor(r.task_type)" size="small" effect="dark" round>{{ r.task_type }}</el-tag>
                        <el-tag :type="r.evidence_status === 'needs_real_modeling' ? 'warning' : 'success'" size="small" effect="plain" round style="margin-left:4px;">{{ r.evidence_status }}</el-tag>
                      </div>
                      <p style="font-size: var(--text-xs);color:var(--text-secondary);margin:4px 0 8px;">{{ r.result_summary }}</p>
                      <div class="q-detail-grid">
                        <div class="q-detail-item">
                          <span class="q-detail-label">🏁 基线</span>
                          <span class="q-detail-value">{{ r.baseline_model || '-' }}</span>
                        </div>
                        <div class="q-detail-item">
                          <span class="q-detail-label">🚀 主模型</span>
                          <span class="q-detail-value" style="font-weight:600;color:var(--primary);">{{ r.main_model }}</span>
                        </div>
                        <div class="q-detail-item">
                          <span class="q-detail-label">📂 产出</span>
                          <span class="q-detail-value">{{ (r.outputs || []).map(o => o.name).join('、') || '无' }}</span>
                        </div>
                      </div>
                      <!-- 参数 -->
                      <div v-if="(r.parameters || []).length" style="margin-top:6px;">
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">参数：</span>
                        <el-tag v-for="p in r.parameters" :key="p.name" size="small" effect="plain" type="info" style="margin:2px;">{{ p.name }}={{ p.value }}</el-tag>
                      </div>
                    </div>
                  </div>

                  <!-- 指标契约 -->
                  <template v-if="(modelContractData.metrics || []).length">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin:16px 0 6px;">📏 指标契约</h4>
                    <div class="rubric-table">
                      <div style="display:grid;grid-template-columns:0.8fr 1fr 1fr 0.6fr 0.8fr;gap:6px;padding:6px 10px;font-size: var(--text-xs);color:var(--text-tertiary);font-weight:600;background:var(--bg-secondary);border-radius:6px 6px 0 0;">
                        <span>问题</span><span>指标名</span><span>角色</span><span>值</span><span>状态</span>
                      </div>
                      <div v-for="(m, mi) in modelContractData.metrics.slice(0, 20)" :key="mi" style="display:grid;grid-template-columns:0.8fr 1fr 1fr 0.6fr 0.8fr;gap:6px;padding:6px 10px;font-size: var(--text-xs);border-bottom:1px solid var(--border-light);align-items:center;">
                        <span style="font-family:monospace;color:var(--primary);font-size: var(--text-xs);">{{ m.question_id }}</span>
                        <span>{{ m.metric_name }}</span>
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">{{ m.metric_role }}</span>
                        <span style="font-size: var(--text-xs);">{{ m.value !== null && m.value !== undefined ? m.value + (m.unit || '') : '待填' }}</span>
                        <el-tag size="small" effect="plain" :type="m.status === 'to_be_filled' ? 'warning' : 'info'">{{ m.status }}</el-tag>
                      </div>
                    </div>
                    <div v-if="modelContractData.metrics.length > 20" style="font-size: var(--text-xs);color:var(--text-tertiary);text-align:center;padding:4px;">
                      ... 还有 {{ modelContractData.metrics.length - 20 }} 项
                    </div>
                  </template>

                  <!-- 表格索引 -->
                  <template v-if="(modelContractData.tables || []).length">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin:16px 0 6px;">📊 表格索引</h4>
                    <div class="rubric-table">
                      <div style="display:grid;grid-template-columns:1.2fr 0.7fr 1.2fr 1.5fr 0.8fr 0.8fr;gap:6px;padding:6px 10px;font-size: var(--text-xs);color:var(--text-tertiary);font-weight:600;background:var(--bg-secondary);border-radius:6px 6px 0 0;">
                        <span>表格ID</span><span>问题</span><span>标题</span><span>用途</span><span>路径</span><span>状态</span>
                      </div>
                      <div v-for="(t, ti) in modelContractData.tables" :key="ti" style="display:grid;grid-template-columns:1.2fr 0.7fr 1.2fr 1.5fr 0.8fr 0.8fr;gap:6px;padding:6px 10px;font-size: var(--text-xs);border-bottom:1px solid var(--border-light);align-items:center;">
                        <span style="font-family:monospace;color:var(--primary);font-size: var(--text-xs);">{{ t.table_id }}</span>
                        <span style="font-family:monospace;font-size: var(--text-xs);">{{ t.question_id }}</span>
                        <span style="font-size: var(--text-xs);">{{ t.title }}</span>
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">{{ t.purpose }}</span>
                        <span style="font-size: var(--text-xs);color:var(--text-tertiary);">{{ (t.path || '').split('/').pop() }}</span>
                        <el-tag size="small" effect="plain" :type="t.status === 'draft_contract' ? 'warning' : 'info'">{{ t.status }}</el-tag>
                      </div>
                    </div>
                  </template>

                  <!-- 结论 -->
                  <template v-if="(modelContractData.conclusions || []).length">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin:16px 0 6px;">📝 结论契约</h4>
                    <div v-for="(c, ci) in modelContractData.conclusions" :key="ci" style="display:flex;gap:8px;align-items:flex-start;padding:6px 0;border-bottom:1px solid var(--border-light);font-size: var(--text-xs);">
                      <el-tag size="small" effect="dark" round style="flex-shrink:0;">{{ c.question_id }}</el-tag>
                      <span style="color:var(--text-secondary);">{{ c.conclusion_text }}</span>
                      <el-tag size="small" effect="plain" :type="c.evidence_status === 'needs_real_modeling' ? 'warning' : 'success'" style="flex-shrink:0;">{{ c.evidence_status }}</el-tag>
                    </div>
                  </template>
                </div>

                <!-- 空状态 -->
                <div v-if="!modelContractData && !modelContractLoading" style="text-align:center;padding:30px 0;color:var(--text-tertiary);">
                  <el-icon :size="32"><Guide /></el-icon>
                  <p style="margin-top:8px;font-size: var(--text-sm);">运行 S5 后在此查看建模代码与结果契约</p>
                </div>
              </div>

              <!-- S6 证据门禁 -->
              <div class="app-card" style="margin-top:16px;">
                <div class="app-card-header">
                  <span class="app-card-title">🔒 S6 证据门禁</span>
                  <el-tag v-if="evidenceGateData?.status === 'PASS'" type="success" size="small" effect="dark" round>PASS</el-tag>
                  <el-tag v-else-if="evidenceGateData?.status === 'FAIL'" type="danger" size="small" effect="dark" round>FAIL</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p style="font-size: var(--text-sm);color:var(--text-secondary);margin-bottom:12px;">
                    验证 S0-S5 产出证据完整性：模型结果、指标、结论、表格 + 评分点对齐。
                  </p>
                  <el-button
                    type="primary"
                    :loading="evidenceGateLoading"
                    :disabled="activeTask.status !== 's5_completed' && activeTask.status !== 's6_completed' && activeTask.status !== 's6_failed'"
                    @click="runEvidenceGate"
                    round
                  >
                    {{ evidenceGateLoading ? '检查中...' : '运行 S6 证据门禁' }}
                  </el-button>
                  <div v-if="activeTask.status !== 's5_completed' && activeTask.status !== 's6_completed' && activeTask.status !== 's6_failed'" style="margin-top:8px;font-size: var(--text-xs);color:var(--text-tertiary);">
                    ⚠ 请先完成 S5 建模代码再运行 S6
                  </div>
                  <div v-if="activeTask.status === 's6_completed'" style="margin-top:8px;font-size: var(--text-xs);color:var(--success);">
                    ✅ S6 证据门禁通过，可以进入 S7
                  </div>
                </div>

                <div v-if="evidenceGateData" class="analysis-result">
                  <div class="result-status" :class="evidenceGateData.status === 'PASS' ? 'pass' : 'fail'">
                    <el-icon :size="18"><CircleCheck v-if="evidenceGateData.status === 'PASS'" /><CircleClose v-else /></el-icon>
                    <span>{{ evidenceGateData.status === 'PASS' ? '证据门禁通过！' : '存在证据缺口，需修复' }}</span>
                  </div>
                  <div v-if="evidenceGateData.summary" style="margin-top:12px;display:flex;gap:16px;flex-wrap:wrap;">
                    <div style="text-align:center;"><div style="font-size: var(--text-lg);font-weight:700;color:var(--primary);">{{ evidenceGateData.summary.total_checks }}</div><div style="font-size: var(--text-xs);color:var(--text-tertiary);">总检查</div></div>
                    <div style="text-align:center;"><div style="font-size: var(--text-lg);font-weight:700;color:var(--success);">{{ evidenceGateData.summary.passed }}</div><div style="font-size: var(--text-xs);color:var(--text-tertiary);">通过</div></div>
                    <div style="text-align:center;"><div style="font-size: var(--text-lg);font-weight:700;color:var(--danger);">{{ evidenceGateData.summary.failed }}</div><div style="font-size: var(--text-xs);color:var(--text-tertiary);">失败</div></div>
                    <div style="text-align:center;"><div style="font-size: var(--text-lg);font-weight:700;color:var(--warning);">{{ evidenceGateData.summary.warnings }}</div><div style="font-size: var(--text-xs);color:var(--text-tertiary);">警告</div></div>
                  </div>
                  <div v-if="(evidenceGateData.failures || []).length" style="margin-top:8px;">
                    <h4 style="font-size: var(--text-sm);font-weight:600;color:var(--danger);margin-bottom:4px;">失败项</h4>
                    <div v-for="(f, fi) in evidenceGateData.failures" :key="fi" class="err-item err">{{ f }}</div>
                  </div>
                  <div v-if="(evidenceGateData.questions || []).length" style="margin-top:12px;">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin-bottom:6px;">逐问检查</h4>
                    <div v-for="q in evidenceGateData.questions" :key="q.question_id" style="padding:8px;border-bottom:1px solid var(--border-light);">
                      <span style="font-weight:600;font-size: var(--text-sm);">{{ q.question_id }}</span>
                      <span v-for="item in q.items" :key="item.check" style="margin-left:8px;">
                        <el-tag :type="item.status === 'PASS' ? 'success' : item.status === 'WARN' ? 'warning' : 'danger'" size="small" effect="plain" round>{{ item.check }}</el-tag>
                      </span>
                    </div>
                  </div>
                </div>
                <div v-if="!evidenceGateData && !evidenceGateLoading" style="text-align:center;padding:30px 0;color:var(--text-tertiary);">
                  <el-icon :size="32"><Lock /></el-icon>
                  <p style="margin-top:8px;font-size: var(--text-sm);">运行 S6 后在此查验证据门禁结果</p>
                </div>
              </div>

              <!-- S7 论文生成 + 格式检查 -->
              <div class="app-card" style="margin-top:16px;">
                <div class="app-card-header">
                  <span class="app-card-title">📝 S7 论文生成 + 格式检查</span>
                  <el-tag v-if="formatCheckData?.status === 'PASS'" type="success" size="small" effect="dark" round>已通过</el-tag>
                  <el-tag v-else-if="paperData" type="warning" size="small" effect="dark" round>已生成</el-tag>
                  <el-tag v-else type="info" size="small" effect="plain" round>待运行</el-tag>
                </div>
                <div class="app-card-body">
                  <p style="font-size: var(--text-sm);color:var(--text-secondary);margin-bottom:12px;">
                    基于 S0-S6 全部合约生成完整学术论文，检查格式合规性。
                  </p>
                  <div style="display:flex;gap:8px;flex-wrap:wrap;">
                    <el-button type="primary" :loading="paperWritingLoading"
                      :disabled="activeTask.status !== 's6_completed' && activeTask.status !== 's7_completed' && activeTask.status !== 's7_check_passed'"
                      @click="runPaperWriting" round>
                      {{ paperWritingLoading ? '生成中...' : '生成论文' }}
                    </el-button>
                    <el-button type="warning" :loading="formatCheckLoading"
                      :disabled="activeTask.status !== 's7_completed' && activeTask.status !== 's7_check_passed'"
                      @click="runFormatCheck" round>
                      {{ formatCheckLoading ? '检查中...' : '格式检查' }}
                    </el-button>
                    <el-button type="success" :disabled="!paperData" @click="downloadPaper" round>
                      📥 下载论文(MD)
                    </el-button>
                  </div>
                  <div v-if="activeTask.status !== 's6_completed' && activeTask.status !== 's7_completed' && activeTask.status !== 's7_check_passed'" style="margin-top:8px;font-size: var(--text-xs);color:var(--text-tertiary);">
                    ⚠ 请先通过 S6 证据门禁
                  </div>
                </div>

                <!-- 论文预览 -->
                <div v-if="paperData" class="analysis-result">
                  <div class="q-detail-grid" style="margin-bottom:12px;">
                    <div class="q-detail-item"><span class="q-detail-label">📏 字数</span><span class="q-detail-value">{{ paperData.word_count || '-' }}</span></div>
                    <div class="q-detail-item"><span class="q-detail-label">📑 章节</span><span class="q-detail-value">{{ paperData.sections_count || '-' }}</span></div>
                  </div>

                  <!-- 格式检查 -->
                  <div v-if="formatCheckData" style="margin-top:12px;">
                    <div class="result-status" :class="formatCheckData.status === 'PASS' ? 'pass' : 'fail'">
                      <el-icon :size="18"><CircleCheck v-if="formatCheckData.status === 'PASS'" /><CircleClose v-else /></el-icon>
                      <span>{{ formatCheckData.status === 'PASS' ? '格式检查通过' : '格式问题待修复' }}</span>
                    </div>
                    <div v-if="(formatCheckData.checks || []).length" style="margin-top:8px;">
                      <div v-for="(c, ci) in formatCheckData.checks" :key="ci" class="err-item" :class="c.status === 'FAIL' ? 'err' : c.status === 'WARN' ? 'warn' : ''">
                        <el-tag :type="c.status === 'PASS' ? 'success' : c.status === 'WARN' ? 'warning' : 'danger'" size="small" effect="dark" round style="margin-right:8px;">{{ c.status }}</el-tag>
                        <span style="font-size: var(--text-xs);">{{ c.detail }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Markdown 预览 -->
                  <div style="margin-top:12px;" v-if="paperData.draft_paper">
                    <h4 style="font-size: var(--text-sm);font-weight:600;margin-bottom:6px;">论文预览（前 1500 字）</h4>
                    <pre style="background:var(--bg-primary);border:1px solid var(--border-light);border-radius:8px;padding:12px;font-size: var(--text-xs);line-height:1.6;white-space:pre-wrap;word-break:break-word;max-height:300px;overflow-y:auto;font-family:inherit;">{{ paperData.draft_paper?.substring(0, 1500) || '(空)' }}{{ (paperData.draft_paper || '').length > 1500 ? '\n\n... (内容过长，已截断)' : '' }}</pre>
                  </div>
                </div>

                <div v-if="!paperData && !paperWritingLoading" style="text-align:center;padding:30px 0;color:var(--text-tertiary);">
                  <el-icon :size="32"><Document /></el-icon>
                  <p style="margin-top:8px;font-size: var(--text-sm);">通过 S6 门禁后在此生成论文</p>
                </div>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { competitionApi } from '../api'
import Sidebar from '../components/Sidebar.vue'
import {
  HomeFilled, Trophy, Plus, UploadFilled, Document, Delete,
  CircleCheck, CircleClose, DataAnalysis, Guide, Lock
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
const modelContractLoading = ref(false)
const modelContractData = ref(null)
const evidenceGateLoading = ref(false)
const evidenceGateData = ref(null)
const paperWritingLoading = ref(false)
const paperData = ref(null)
const formatCheckLoading = ref(false)
const formatCheckData = ref(null)
const showCreateDialog = ref(false)
const newTaskTitle = ref('')
const creatingTask = ref(false)

// 上传请求头
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

// 步骤完成判断 (CMP-010: 进度可视化)
const stepStatusMap = {
  'S0': ['s0_passed'],
  'S1': ['s1_completed', 's2_completed', 's4_completed', 's5_completed', 's6_completed', 's7_completed', 's7_check_passed'],
  'S2': ['s2_completed', 's4_completed', 's5_completed', 's6_completed', 's7_completed', 's7_check_passed'],
  'S3': ['s4_completed', 's5_completed', 's6_completed', 's7_completed', 's7_check_passed'],
  'S4': ['s4_completed', 's5_completed', 's6_completed', 's7_completed', 's7_check_passed'],
  'S5': ['s5_completed', 's6_completed', 's7_completed', 's7_check_passed'],
  'S6': ['s6_completed', 's7_completed', 's7_check_passed'],
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

function onUploadSuccess() {
  loadFiles()
  // 刷新任务计数
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
    const res = await competitionApi.runPaperWriting(activeTaskId.value)
    paperData.value = { draft_paper: res.draft_paper, paper: res.paper, word_count: res.word_count, sections_count: res.sections_count }
    await refreshTask()
  } catch (e) {
    console.error(e)
    paperData.value = { draft_paper: e.response?.data?.detail || '论文生成失败', word_count: 0, sections_count: 0 }
  }
  finally { paperWritingLoading.value = false }
}

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

// ===== 论文下载 =====

function downloadPaper() {
  if (!activeTaskId.value) return
  const a = document.createElement('a')
  a.href = `/api/competition/tasks/${activeTaskId.value}/paper/download`
  a.download = `paper_task${activeTaskId.value}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
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
// 任务列表
.task-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid var(--border-light);
  transition: all 0.2s;
  &:hover {
    border-color: var(--primary);
    background: var(--primary-light);
  }
  &.active {
    border-color: var(--primary);
    background: var(--primary-light);
  }
}
.task-item-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.task-title {
  font-size: var(--text-sm);
  font-weight: 600;
}
.task-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

// 步骤指示器
.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 20px 0;
  margin-bottom: 16px;
}
.step-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  border-radius: 12px;
  background: var(--bg-primary);
  border: 2px solid var(--border-light);
  min-width: 60px;
  transition: all 0.3s;
  &.active {
    border-color: var(--primary);
    background: var(--primary-light);
    .step-num { color: var(--primary); font-weight: 700; }
  }
  &.done {
    border-color: var(--success);
    background: var(--success-bg);
    .step-num { color: var(--success); }
  }
  &.future {
    opacity: 0.4;
  }
}
.step-num {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  font-family: monospace;
}
.step-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}
.step-line {
  width: 32px;
  height: 2px;
  background: var(--border-light);
  &.done { background: var(--success); }
}

// 工作区
.work-area {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.work-left, .work-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

// 上传区
.upload-zone {
  width: 100%;
  margin-bottom: 12px;
}
.upload-text {
  p { margin: 4px 0; font-size: var(--text-sm); }
  .upload-hint { font-size: var(--text-xs); color: var(--text-tertiary); }
}

// 文件列表
.file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  background: var(--bg-primary);
  font-size: var(--text-sm);
}
.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-size {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

// 预检结果
.preflight-result {
  padding: 16px 20px 20px;
  border-top: 1px solid var(--border-light);
}
.result-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: var(--text-sm);
  font-weight: 500;
  &.pass { background: var(--success-bg); color: var(--success); }
  &.fail { background: var(--danger-bg); color: var(--danger); }
}

// 附件清单
.manifest-table {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.manifest-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: var(--bg-primary);
  border-radius: 6px;
  font-size: var(--text-xs);
}
.manifest-file {
  flex: 1;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// 错误/警告
.err-item {
  font-size: var(--text-xs);
  padding: 4px 10px;
  border-radius: 4px;
  margin-bottom: 2px;
  line-height: 1.5;
  &.err { background: #FFF1F0; color: var(--danger); }
  &.warn { background: #FFF7E6; color: var(--warning); }
}

// S1 分析结果
.analysis-result {
  padding: 16px 20px 20px;
  border-top: 1px solid var(--border-light);
}
.question-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.q-card {
  padding: 14px 16px;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  background: var(--bg-card);
}
.q-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.q-id {
  font-weight: 700;
  font-size: var(--text-sm);
  font-family: monospace;
  color: var(--primary);
  background: var(--primary-light);
  padding: 2px 8px;
  border-radius: 4px;
}
.q-title {
  font-size: var(--text-sm);
  font-weight: 600;
  flex: 1;
}
.q-summary {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 10px;
}
.q-detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
}
.q-detail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.q-detail-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}
.q-detail-value {
  font-size: var(--text-xs);
  color: var(--text-primary);
  line-height: 1.4;
}

// S2 评分点对齐表格
.rubric-table {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: var(--border-light);
  border-radius: 8px;
  overflow: hidden;
}
.rubric-row {
  display: grid;
  grid-template-columns: 80px 50px 1fr 1fr;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-primary);
  font-size: var(--text-xs);
  align-items: center;
}
.rubric-point {
  font-weight: 600;
  color: var(--primary);
}
.rubric-q {
  color: var(--text-tertiary);
  font-family: monospace;
}
.rubric-evidence {
  color: var(--text-secondary);
}
.rubric-location {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}
</style>
