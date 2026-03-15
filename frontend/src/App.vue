<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from './api/client'

const projects = ref([])
const selectedProjectId = ref(null)
const name = ref('我的参赛项目')
const sceneType = ref('competition')
const targetMinutes = ref(10)
const fileRef = ref(null)
const uploadedFileId = ref(null)
const analysisRows = ref([])
const qaRows = ref([])
const sceneSuggestions = ref([])
const scriptText = ref('')
const evalResult = ref(null)
const report = ref(null)
const msg = ref('')

const maxTextCount = computed(() => Math.max(...analysisRows.value.map((r) => r.text_count), 1))
const riskPageCount = computed(() => analysisRows.value.filter((r) => r.risk_tags.length > 0).length)

const loadProjects = async () => {
  const { data } = await api.get('/projects')
  projects.value = data.data
  if (!selectedProjectId.value && projects.value.length) {
    selectedProjectId.value = projects.value[0].id
  }
}

const bootstrapDemo = async () => {
  const { data } = await api.post('/projects/bootstrap_demo')
  selectedProjectId.value = data.data.project_id
  uploadedFileId.value = data.data.file_id
  await api.post(`/analysis/parse/${uploadedFileId.value}`)
  await loadAnalysis()
  msg.value = '示例项目已导入并完成解析'
  await loadProjects()
}

const createProject = async () => {
  const { data } = await api.post('/projects', {
    name: name.value,
    scene_type: sceneType.value,
    target_minutes: targetMinutes.value
  })
  selectedProjectId.value = data.data.id
  msg.value = '项目创建成功'
  await loadProjects()
}

const upload = async () => {
  if (!fileRef.value?.files?.length || !selectedProjectId.value) return
  const form = new FormData()
  form.append('project_id', selectedProjectId.value)
  form.append('file', fileRef.value.files[0])
  const { data } = await api.post('/files/upload', form)
  uploadedFileId.value = data.data.file_id
  msg.value = '文件上传成功'
}

const parseFile = async () => {
  if (!uploadedFileId.value) return
  await api.post(`/analysis/parse/${uploadedFileId.value}`)
  msg.value = '解析完成'
  await loadAnalysis()
}

const loadAnalysis = async () => {
  if (!selectedProjectId.value) return
  const { data } = await api.get(`/analysis/project/${selectedProjectId.value}`)
  analysisRows.value = data.data
}

const generateScene = async () => {
  if (!selectedProjectId.value) return
  await api.post(`/scene/rewrite/${selectedProjectId.value}`, { scene_type: sceneType.value })
  const { data } = await api.get(`/scene/project/${selectedProjectId.value}`)
  sceneSuggestions.value = data.data
}

const generateQa = async () => {
  if (!selectedProjectId.value) return
  await api.post(`/qa/generate/${selectedProjectId.value}`)
  const { data } = await api.get(`/qa/project/${selectedProjectId.value}`)
  qaRows.value = data.data
}

const evaluate = async () => {
  if (!selectedProjectId.value) return
  const { data } = await api.post(`/evaluation/run/${selectedProjectId.value}`, {
    script_text: scriptText.value,
    target_minutes: targetMinutes.value
  })
  evalResult.value = data.data
}

const genReport = async () => {
  if (!evalResult.value?.evaluation_id) return
  const { data } = await api.post(`/reports/generate/${evalResult.value.evaluation_id}`)
  report.value = data.data
}

const downloadReport = () => {
  if (!report.value?.report_id) return
  window.open(`/api/reports/download/${report.value.report_id}`, '_blank')
}

onMounted(loadProjects)
</script>

<template>
  <div style="max-width: 1100px; margin: 24px auto; font-family: Arial">
    <h1>演析 Pro（前后端分离 MVP）</h1>
    <p style="color:#555">流程：创建项目 → 上传文件 → 解析 → 场景重构 → 问答预测 → 表达评估 → 复盘报告</p>
    <p style="color: green">{{ msg }}</p>

    <section>
      <h3>0) 快速导入示例</h3>
      <button @click="bootstrapDemo">一键导入示例项目</button>
    </section>

    <section>
      <h3>1) 创建项目</h3>
      <input v-model="name" placeholder="项目名" />
      <select v-model="sceneType">
        <option value="competition">竞赛答辩</option>
        <option value="thesis">论文答辩</option>
        <option value="course">课程汇报</option>
      </select>
      <input v-model.number="targetMinutes" type="number" min="3" max="60" />
      <button @click="createProject">创建</button>
    </section>

    <section>
      <h3>2) 选择项目</h3>
      <select v-model.number="selectedProjectId" @change="loadAnalysis">
        <option v-for="p in projects" :key="p.id" :value="p.id">#{{ p.id }} {{ p.name }}</option>
      </select>
    </section>

    <section>
      <h3>3) 上传并解析</h3>
      <input ref="fileRef" type="file" />
      <button @click="upload">上传</button>
      <button @click="parseFile">开始解析</button>
    </section>

    <section>
      <h3>4) 解析结果（图表化）</h3>
      <p>总页数：{{ analysisRows.length }}，风险页：{{ riskPageCount }}</p>
      <div v-for="row in analysisRows" :key="row.page_no" style="display:flex; align-items:center; margin:6px 0; gap:8px;">
        <span style="width:120px">第{{ row.page_no }}页</span>
        <div style="background:#e9ecef; height:14px; width:380px;">
          <div :style="{width: `${(row.text_count / maxTextCount) * 100}%`, height:'14px', background:'#0d6efd'}"></div>
        </div>
        <span>{{ row.text_count }} 字</span>
        <span style="color:#d63384">{{ row.risk_tags.join('、') }}</span>
      </div>
    </section>

    <section>
      <h3>5) 场景化重构</h3>
      <button @click="generateScene">生成场景建议</button>
      <ul>
        <li v-for="(s, idx) in sceneSuggestions" :key="idx">[{{ s.suggestion_type }}] {{ s.content }}</li>
      </ul>
    </section>

    <section>
      <h3>6) 问答预测</h3>
      <button @click="generateQa">生成问答</button>
      <ul>
        <li v-for="(q, idx) in qaRows.slice(0, 10)" :key="idx">{{ q.question }}</li>
      </ul>
    </section>

    <section>
      <h3>7) 表达评估</h3>
      <textarea v-model="scriptText" rows="5" style="width:100%" placeholder="粘贴讲稿"></textarea>
      <button @click="evaluate">评估</button>
      <div v-if="evalResult">
        表达分：{{ evalResult.expression_score.toFixed(2) }}，语速：{{ evalResult.estimated_wpm.toFixed(1) }} 字/分钟
      </div>
    </section>

    <section>
      <h3>8) 复盘报告</h3>
      <button @click="genReport">生成报告</button>
      <button @click="downloadReport" :disabled="!report">下载Markdown</button>
      <pre v-if="report" style="background:#f5f5f5;padding:12px;white-space:pre-wrap">{{ report.report_markdown }}</pre>
    </section>
  </div>
</template>
