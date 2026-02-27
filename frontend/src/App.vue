<template>
  <el-container class="layout">
    <el-header class="header">
      <router-link to="/" class="logo">PaperAxon</router-link>
      <el-menu mode="horizontal" :router="true" :default-active="activeMenu" class="nav">
        <el-menu-item index="/">论文</el-menu-item>
        <el-menu-item index="/settings">设置</el-menu-item>
        <el-menu-item index="/knowledge">知识图谱</el-menu-item>
        <el-menu-item index="/trending">热度</el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="main">
      <router-view v-slot="{ Component }">
        <component :is="Component" />
      </router-view>
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path === '/' ? '/' : route.path)
</script>

<style scoped>
.layout { min-height: 100vh; }
.header {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--el-border-color);
  padding: 0 16px;
}
.logo {
  font-size: 1.25rem;
  font-weight: 600;
  margin-right: 24px;
  color: var(--el-color-primary);
  text-decoration: none;
}
.nav { flex: 1; border-bottom: none; }
.main { padding: 20px; }
</style>
