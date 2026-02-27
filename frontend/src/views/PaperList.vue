<template>
  <div>
    <el-card class="toolbar">
      <el-upload
        :show-file-list="false"
        accept=".pdf"
        :http-request="handleUpload"
      >
        <el-button type="primary" :loading="uploading">上传 PDF</el-button>
      </el-upload>
      <el-form inline class="arxiv-form">
        <el-form-item label="arXiv">
          <el-input v-model="arxivInput" placeholder="链接或 ID" style="width: 280px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" plain :loading="arxivLoading" @click="fetchArxiv">拉取</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="paper_id" label="ID" width="120" />
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="authors" label="作者" width="180" show-overflow-tooltip />
      <el-table-column prop="source_type" label="来源" width="90" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push('/paper/' + row.paper_id)">详情</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../api'

const items = ref([])
const loading = ref(false)
const uploading = ref(false)
const arxivLoading = ref(false)
const arxivInput = ref('')

async function load() {
  loading.value = true
  try {
    const res = await api.listPapers()
    items.value = res.items || []
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleUpload({ file }) {
  uploading.value = true
  try {
    await api.uploadPdf(file)
    ElMessage.success('上传成功')
    load()
  } catch (e) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function fetchArxiv() {
  if (!arxivInput.value.trim()) {
    ElMessage.warning('请输入 arXiv 链接或 ID')
    return
  }
  arxivLoading.value = true
  try {
    await api.fromArxiv({ url: arxivInput.value.trim() })
    ElMessage.success('拉取成功')
    arxivInput.value = ''
    load()
  } catch (e) {
    ElMessage.error(e.message || '拉取失败')
  } finally {
    arxivLoading.value = false
  }
}

async function onDelete(row) {
  try {
    await api.deletePaper(row.paper_id)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    ElMessage.error(e.message || '删除失败')
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar { margin-bottom: 16px; }
.toolbar .el-upload { margin-right: 16px; }
.arxiv-form { margin: 0; }
</style>
