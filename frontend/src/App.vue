<script setup>
import { ref, onMounted } from 'vue'
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
const scriptText = ref('')
const evalResult = ref(null)
const report = ref(null)
const msg = ref('')

const loadProjects = async () => {
  const { data } = await api.get('/projects')
  projects.value = data.data
  if (!selectedProjectId.value && projects.value.length) {
    selectedProjectId.value = projects.value[0].id
  }
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

onMounted(loadProjects)
</script>

<template>
  <div style="max-width: 1100px; margin: 24px auto; font-family: Arial">
    <h1>演析 Pro（前后端分离 MVP）</h1>
    <p style="color:#555">流程：创建项目 → 上传文件 → 解析 → 生成问答 → 表达评估 → 复盘报告</p>
    <p style="color: green">{{ msg }}</p>

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
      <h3>4) 解析结果</h3>
      <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>页码</th><th>标题</th><th>文本量</th><th>风险标签</th></tr>
        <tr v-for="r in analysisRows" :key="r.page_no">
          <td>{{ r.page_no }}</td><td>{{ r.title_guess }}</td><td>{{ r.text_count }}</td><td>{{ r.risk_tags.join('、') }}</td>
        </tr>
      </table>
    </section>

    <section>
      <h3>5) 问答预测</h3>
      <button @click="generateQa">生成问答</button>
      <ul>
        <li v-for="(q, idx) in qaRows.slice(0, 10)" :key="idx">{{ q.question }}</li>
      </ul>
    </section>

    <section>
      <h3>6) 表达评估</h3>
      <textarea v-model="scriptText" rows="5" style="width:100%" placeholder="粘贴讲稿"></textarea>
      <button @click="evaluate">评估</button>
      <div v-if="evalResult">
        表达分：{{ evalResult.expression_score.toFixed(2) }}，语速：{{ evalResult.estimated_wpm.toFixed(1) }} 字/分钟
      </div>
    </section>

    <section>
      <h3>7) 复盘报告</h3>
      <button @click="genReport">生成报告</button>
      <pre v-if="report" style="background:#f5f5f5;padding:12px;white-space:pre-wrap">{{ report.report_markdown }}</pre>
    </section>
  </div>
</template>
