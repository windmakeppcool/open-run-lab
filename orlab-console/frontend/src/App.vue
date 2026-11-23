<!--
  应用根组件：SVG 图标精灵 + 侧边栏 + 顶栏 + 路由视图 + 全局实验抽屉
-->
<script setup lang="ts">
import AppSidebar from './components/AppSidebar.vue';
import AppTopbar from './components/AppTopbar.vue';
import ExperimentDrawer from './components/ExperimentDrawer.vue';
</script>

<template>
  <!-- SVG 图标精灵（沿用原型 symbol 定义） -->
  <svg xmlns="http://www.w3.org/2000/svg" style="display: none">
    <symbol id="i-grid" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></symbol>
    <symbol id="i-folder" viewBox="0 0 24 24"><path d="M3 6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /></symbol>
    <symbol id="i-flask" viewBox="0 0 24 24"><path d="M9 3h6M10 3v6l-5.4 8.5A2.2 2.2 0 0 0 6.5 21h11a2.2 2.2 0 0 0 1.9-3.5L14 9V3M7.5 15h9" /></symbol>
    <symbol id="i-chart" viewBox="0 0 24 24"><path d="M4 4v16h16M7 15l4-4 3 2 5-6" /></symbol>
    <symbol id="i-users" viewBox="0 0 24 24"><circle cx="9" cy="8" r="3" /><path d="M3 20v-2a6 6 0 0 1 12 0v2M16 5a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 4.6V20" /></symbol>
    <symbol id="i-database" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7" /></symbol>
    <symbol id="i-search" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 4 4" /></symbol>
    <symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14M14 7l5 5-5 5" /></symbol>
    <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></symbol>
    <symbol id="i-check" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="m8 12 3 3 5-6" /></symbol>
    <symbol id="i-sliders" viewBox="0 0 24 24"><path d="M4 7h16M4 17h16M8 4v6M16 14v6" /></symbol>
  </svg>

  <div class="app">
    <AppSidebar />
    <main class="main">
      <AppTopbar />
      <div class="content">
        <router-view />
      </div>
    </main>
  </div>

  <!-- 全局实验详情抽屉 -->
  <ExperimentDrawer />
</template>
