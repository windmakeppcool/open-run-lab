<!--
  项目空间：项目卡片（实验数 / 状态分布 / 最近活动 / tags），点击进入带 project 过滤的实验列表
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import EmptyState from '../components/EmptyState.vue';
import AppIcon from '../components/AppIcon.vue';
import { getProjects } from '../api';
import type { ProjectInfo } from '../api/types';
import { formatDateTime } from '../utils/format';

const router = useRouter();

const projects = ref<ProjectInfo[]>([]);
const loading = ref(true);

/** 项目图标色调：有异常偏琥珀色，运行中偏绿色，其余蓝色 */
function projectTone(p: ProjectInfo): string {
  if ((p.stateCounts?.crashed ?? 0) > 0) return 'amber';
  if ((p.stateCounts?.running ?? 0) > 0) return '';
  return 'blue';
}

/** 跳转实验列表并带上 project 过滤 */
function openProject(name: string): void {
  router.push({ path: '/experiments', query: { project: name } });
}

onMounted(async () => {
  try {
    const res = await getProjects();
    projects.value = res.projects;
  } catch {
    // 接口失败时保留空态
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">PROJECT SPACE</div>
        <h1>项目空间</h1>
        <p>按研究方向组织实验，让每个想法都有迹可循。</p>
      </div>
      <button class="btn" @click="router.push('/experiments')">
        浏览全部实验 <AppIcon name="arrow" />
      </button>
    </div>

    <div v-if="projects.length" class="cards">
      <article v-for="p in projects" :key="p.name" class="panel project-card">
        <div class="card-top">
          <div class="project-icon" :class="projectTone(p)">{{ (p.name || '?').charAt(0).toUpperCase() }}</div>
          <div>
            <span v-for="tag in p.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
        <h3>{{ p.name }}</h3>
        <p>
          {{ p.workspace || '本地工作空间' }}<br />
          <!-- 状态分布 -->
          <span v-if="p.stateCounts?.running" class="badge running" style="margin: 6px 4px 0 0">运行 {{ p.stateCounts.running }}</span>
          <span v-if="p.stateCounts?.finished" class="badge finished" style="margin: 6px 4px 0 0">完成 {{ p.stateCounts.finished }}</span>
          <span v-if="p.stateCounts?.crashed" class="badge crashed" style="margin: 6px 4px 0 0">异常 {{ p.stateCounts.crashed }}</span>
          <span v-if="p.stateCounts?.aborted" class="badge aborted" style="margin: 6px 4px 0 0">中止 {{ p.stateCounts.aborted }}</span>
        </p>
        <div class="card-bottom">
          <span><b>{{ p.runCount }}</b> 个实验 · 更新于 {{ formatDateTime(p.lastActivityAt) }}</span>
          <button class="subtle-button" @click="openProject(p.name)">
            查看实验 <AppIcon name="arrow" />
          </button>
        </div>
      </article>
    </div>
    <div v-else-if="loading" class="panel loading">正在加载项目…</div>
    <div v-else class="panel">
      <EmptyState text="暂无项目" hint="接入 orlab-log 数据后，这里会按项目聚合实验。" />
    </div>

    <div class="bottom-note">
      <span>项目与实验数量由本地 orlab-log 数据实时聚合。</span>
    </div>
  </div>
</template>
