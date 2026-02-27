<template>
  <el-card>
    <template #header>知识图谱</template>
    <div v-loading="loading" class="graph-wrap">
      <div v-if="!loading && (nodes.length === 0)" class="empty">暂无数据，请先添加论文。</div>
      <div v-else class="graph-simple">
        <div v-for="n in nodes.slice(0, 50)" :key="n.id" class="node">{{ n.data?.label || n.id }}</div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as api from '../api'

const nodes = ref([])
const edges = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await api.getKnowledgeGraph()
    nodes.value = res.nodes || []
    edges.value = res.edges || []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.graph-wrap { min-height: 300px; }
.empty { color: #999; padding: 40px; text-align: center; }
.graph-simple {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.node {
  padding: 6px 12px;
  background: var(--el-color-primary-light-9);
  border-radius: 4px;
  font-size: 12px;
}
</style>
