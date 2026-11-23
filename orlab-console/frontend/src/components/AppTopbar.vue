<!--
  顶部栏：面包屑 + 数据来源状态（来自 /api/health）+ 用户头像
-->
<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { healthState, loadHealth } from '../composables/useHealth';

const route = useRoute();

/** 当前页面标题（面包屑末级） */
const pageTitle = computed(() => (route.meta.title as string) || '工作台');

/** 数据来源标签文本 */
const sourceText = computed(() => {
  if (healthState.error) {
    return '数据源未连接';
  }
  const data = healthState.data;
  if (!data) {
    return '正在连接数据源…';
  }
  // 取 orlab-log 目录名作为来源标识
  const dirLabel = data.orlabLogDir.split(/[\\/]/).filter(Boolean).pop() || 'orlab-log';
  return `本地 ${dirLabel} · ${data.runCount} 个实验`;
});

/** 标签样式：连接成功为绿色调，失败为红色调 */
const sourceClass = computed(() => ({
  ok: !!healthState.data,
  error: !!healthState.error,
}));

onMounted(() => {
  loadHealth();
});
</script>

<template>
  <header class="topbar">
    <div class="crumb">工作空间 <span style="padding: 0 9px">/</span> <b>{{ pageTitle }}</b></div>
    <div class="top-actions">
      <span class="source-tag" :class="sourceClass">{{ sourceText }}</span>
      <div class="avatar" aria-label="当前用户">YL</div>
    </div>
  </header>
</template>
