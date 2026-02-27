<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push('/')" title="返回" />
    <template v-if="paper">
      <el-card class="meta">
        <h2>{{ paper.title }}</h2>
        <p><strong>作者</strong> {{ paper.authors }}</p>
        <p v-if="paper.abstract" class="abstract">{{ paper.abstract }}</p>
      </el-card>

      <el-card class="actions">
        <el-button type="primary" :loading="interpretLoading" @click="doInterpret" :disabled="!!interpretTaskId">
          {{ interpretTaskId ? '解读中…' : '生成解读' }}
        </el-button>
        <el-button type="success" :loading="podcastLoading" @click="doPodcast" :disabled="!!podcastTaskId || !hasInterpretation">
          {{ podcastTaskId ? '生成播客中…' : (hasInterpretation ? '生成播客' : '请先生成解读') }}
        </el-button>
      </el-card>

      <el-card v-if="interpretation" class="interpretation">
        <template #header>解读</template>
        <div class="markdown-body" v-html="renderedInterpretation" />
      </el-card>

      <el-card v-if="hasInterpretation" class="podcast">
        <template #header>播客</template>
        <audio v-if="podcastExists" :src="audioSrc" controls style="width:100%; max-width:600px" />
        <p v-else>点击「生成播客」后在此播放。</p>
      </el-card>

      <el-card class="related">
        <template #header>相关论文</template>
        <el-button size="small" @click="loadRelated" :loading="relatedLoading">刷新</el-button>
        <ul v-if="related.length">
          <li v-for="r in related" :key="r.arxiv_id">
            {{ r.title }} — {{ r.authors }}
          </li>
        </ul>
        <p v-else>暂无或请先刷新。</p>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import * as api from '../api'

const route = useRoute()
const paper = ref(null)
const interpretation = ref('')
const related = ref([])
const loading = ref(true)
const interpretLoading = ref(false)
const interpretTaskId = ref(null)
const podcastLoading = ref(false)
const podcastTaskId = ref(null)
const relatedLoading = ref(false)
const podcastExists = ref(false)

const id = computed(() => route.params.id)

const hasInterpretation = computed(() => !!interpretation.value)

const renderedInterpretation = computed(() => {
  if (!interpretation.value) return ''
  return marked(interpretation.value)
})

const audioSrc = computed(() => api.podcastUrl(id.value))

const POLL_INTERVAL = 2000
const POLL_MAX = (15 * 60 * 1000) / POLL_INTERVAL

function pollTask(taskId, onSuccess) {
  let count = 0
  const t = setInterval(async () => {
    count++
    try {
      const res = await api.getTask(taskId)
      if (res.status === 'success') {
        clearInterval(t)
        onSuccess(res)
      } else if (res.status === 'failed') {
        clearInterval(t)
        ElMessage.error(res.error || '任务失败')
      }
    } catch (_) {}
    if (count >= POLL_MAX) clearInterval(t)
  }, POLL_INTERVAL)
}

async function loadPaper() {
  loading.value = true
  try {
    paper.value = await api.getPaper(id.value)
    try {
      interpretation.value = await api.getInterpretation(id.value)
    } catch {
      interpretation.value = ''
    }
    podcastExists.value = false
    try {
      const r = await fetch(api.podcastUrl(id.value), { method: 'HEAD' })
      if (r.ok) podcastExists.value = true
      else if (r.status === 503) ElMessage.warning('当前为文稿占位，配置 TTS 后请重新点击「生成播客」')
    } catch {
      podcastExists.value = false
    }
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function doInterpret() {
  interpretLoading.value = true
  interpretTaskId.value = null
  try {
    const res = await api.triggerInterpret(id.value)
    interpretTaskId.value = res.task_id
    pollTask(res.task_id, async () => {
      interpretTaskId.value = null
      interpretLoading.value = false
      ElMessage.success('解读完成')
      loadPaper()
    })
  } catch (e) {
    ElMessage.error(e.message || '触发失败')
    interpretLoading.value = false
  }
}

async function doPodcast() {
  podcastLoading.value = true
  podcastTaskId.value = null
  try {
    const res = await api.triggerPodcast(id.value)
    if (res.task_id) {
      podcastTaskId.value = res.task_id
      pollTask(res.task_id, (taskRes) => {
        podcastTaskId.value = null
        podcastLoading.value = false
        const placehold = taskRes.result && taskRes.result.is_placeholder
        if (placehold) {
          ElMessage.warning('生成完成，但仅为文稿占位（TTS 未配置或调用失败）。请检查 TTS 配置后重新点击「生成播客」。')
          podcastExists.value = false
        } else {
          ElMessage.success('播客生成完成')
          podcastExists.value = true
        }
      })
    } else {
      podcastLoading.value = false
      podcastExists.value = true
      ElMessage.success('播客已存在')
    }
  } catch (e) {
    ElMessage.error(e.message || '触发失败')
    podcastLoading.value = false
  }
}

async function loadRelated() {
  relatedLoading.value = true
  try {
    const res = await api.getRelated(id.value)
    related.value = res.items || []
  } catch {
    related.value = []
  } finally {
    relatedLoading.value = false
  }
}

onMounted(() => {
  loadPaper()
  loadRelated()
})
watch(id, loadPaper)
</script>

<style scoped>
.meta { margin: 16px 0; }
.abstract { color: #666; font-size: 0.9rem; }
.actions { margin-bottom: 16px; }
.actions .el-button { margin-right: 8px; }
.interpretation, .podcast, .related { margin-bottom: 16px; }
.markdown-body { line-height: 1.6; }
.markdown-body :deep(h1) { font-size: 1.25rem; }
.markdown-body :deep(h2) { font-size: 1.1rem; }
.markdown-body :deep(ul) { padding-left: 1.5rem; }
ul { list-style: none; padding-left: 0; }
li { margin: 8px 0; }
</style>
