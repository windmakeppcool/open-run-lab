<!--
  左侧品牌导航栏（复刻原型侧边栏视觉）
-->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import AppIcon from './AppIcon.vue';
import { getProjects } from '../api';
import { healthState, loadHealth } from '../composables/useHealth';

const route = useRoute();

/** 项目数量（侧边栏角标） */
const projectCount = ref<number | null>(null);

/** 工作空间卡片副文本 */
const workspaceNote = computed(() => {
  if (healthState.data) {
    return `本地数据 · ${healthState.data.runCount} 个实验`;
  }
  return healthState.error ? '数据源未连接' : '等待数据源连接';
});

onMounted(async () => {
  loadHealth();
  try {
    const res = await getProjects();
    projectCount.value = res.projects.length;
  } catch {
    // 获取失败时不展示角标
  }
});
</script>

<template>
  <aside class="sidebar" aria-label="主导航">
    <div class="brand">
      <div class="brand-mark">
        <svg class="icon" viewBox="0 0 24 24"><path d="M4 17c5-1 7-5 9-12 1 6 3 10 7 12M7 15c3 1 7 1 10 0M5 20h14" /></svg>
      </div>
      <div>
        <strong>OpenRunLab</strong>
        <small>EXPERIMENT SPACE</small>
      </div>
    </div>

    <div class="side-label">WORKSPACE</div>
    <nav class="nav">
      <router-link to="/" :class="{ active: route.name === 'overview' }" aria-label="工作台">
        <AppIcon name="grid" /><span>工作台</span>
      </router-link>
      <router-link to="/projects" :class="{ active: route.name === 'projects' }" aria-label="项目空间">
        <AppIcon name="folder" /><span>项目空间</span>
        <span v-if="projectCount !== null" class="count">{{ projectCount }}</span>
      </router-link>
      <router-link to="/experiments" :class="{ active: route.name === 'experiments' }" aria-label="实验记录">
        <AppIcon name="flask" /><span>实验记录</span>
      </router-link>
      <router-link to="/compare" :class="{ active: route.name === 'compare' }" aria-label="实验对比">
        <AppIcon name="chart" /><span>实验对比</span>
      </router-link>
    </nav>

    <div class="side-label">MANAGEMENT</div>
    <nav class="nav">
      <router-link to="/users" :class="{ active: route.name === 'users' }" aria-label="用户与权限">
        <AppIcon name="users" /><span>用户与权限</span>
      </router-link>
    </nav>

    <div class="side-bottom">
      <div class="workspace">
        <div class="workspace-icon"><AppIcon name="database" /></div>
        <div>
          <strong>本地工作空间</strong>
          <small>{{ workspaceNote }}</small>
        </div>
      </div>
    </div>
  </aside>
</template>
