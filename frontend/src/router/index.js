import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', component: () => import('../views/PaperList.vue'), name: 'PaperList' },
  { path: '/paper/:id', component: () => import('../views/PaperDetail.vue'), name: 'PaperDetail' },
  { path: '/settings', component: () => import('../views/Settings.vue'), name: 'Settings' },
  { path: '/knowledge', component: () => import('../views/KnowledgeGraph.vue'), name: 'KnowledgeGraph' },
  { path: '/trending', component: () => import('../views/Trending.vue'), name: 'Trending' },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
