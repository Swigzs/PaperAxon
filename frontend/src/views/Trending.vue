<template>
  <el-card>
    <template #header>热度（最近更新）</template>
    <el-table :data="items" v-loading="loading">
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="authors" label="作者" width="180" show-overflow-tooltip />
      <el-table-column prop="updated_at" label="更新时间" width="180" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push('/paper/' + row.paper_id)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as api from '../api'

const items = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await api.getTrending()
    items.value = res.items || []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
