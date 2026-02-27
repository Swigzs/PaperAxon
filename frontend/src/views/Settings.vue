<template>
  <el-card>
    <template #header>采集设置</template>
    <el-form label-width="140px" style="max-width: 400px">
      <el-form-item label="每日自动采集">
        <el-switch v-model="form.auto_collect_enabled" />
      </el-form-item>
      <el-form-item label="采集时间">
        <el-time-picker
          v-model="timeValue"
          format="HH:mm"
          value-format="HH:mm"
          placeholder="00:00"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../api'

const form = ref({ auto_collect_enabled: false, collect_time: '00:00' })
const timeValue = ref('00:00')
const saving = ref(false)

async function load() {
  const res = await api.getCollectSettings()
  form.value = res
  timeValue.value = res.collect_time || '00:00'
}

async function save() {
  saving.value = true
  try {
    const time = typeof timeValue.value === 'string' ? timeValue.value : (timeValue.value && timeValue.value.toString().slice(0, 5)) || '00:00'
    await api.updateCollectSettings({
      auto_collect_enabled: form.value.auto_collect_enabled,
      collect_time: time,
    })
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
