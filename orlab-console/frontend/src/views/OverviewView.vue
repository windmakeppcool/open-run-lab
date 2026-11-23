<!--
  工作台：统计卡片 + 活动图（ECharts）+ 最近实验 + 项目健康度
-->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import StatCard from '../components/StatCard.vue';
import RunTable from '../components/RunTable.vue';
import LineChart, { type ChartSeries } from '../components/LineChart.vue';
import EmptyState from '../components/EmptyState.vue';
import AppIcon from '../components/AppIcon.vue';
import { getExperimentMetrics, getExperiments, getProjects } from '../api';
import type { ExperimentListItem, ProjectInfo } from '../api/types';
import { openExperimentDrawer } from '../composables/useDrawer';
import { formatDateTime, formatNumber } from '../utils/format';

const router = useRouter();

/** 项目列表（统计汇总 + 项目健康度） */
const projects = ref<ProjectInfo[]>([]);
/** 最近实验列表 */
const recentRuns = ref<ExperimentListItem[]>([]);
/** 活动图曲线 */
const chartSeries = ref<ChartSeries[]>([]);
/** 活动图指标名（图头展示） */
const chartMetricKey = ref('');
const loading = ref(true);
const chartLoading = ref(true);

/** 由项目 stateCounts 汇总的全局计数 */
const totals = computed(() => {
  const result = { total: 0, running: 0, finished: 0, crashed: 0, aborted: 0 };
  for (const p of projects.value) {
    result.total += p.runCount;
    result.running += p.stateCounts?.running ?? 0;
    result.finished += p.stateCounts?.finished ?? 0;
    result.crashed += p.stateCounts?.crashed ?? 0;
    result.aborted += p.stateCounts?.aborted ?? 0;
  }
  return result;
});

/** 已结束卡片副文本（附带中止数量） */
const finishedNote = computed(() =>
  totals.value.aborted > 0 ? `另有 ${totals.value.aborted} 个实验中止` : '成功完成的训练实验',
);

/** 活动图图头：第一个系列的最新值 */
const latestValue = computed(() => {
  const first = chartSeries.value[0];
  if (!first || !first.data.length) {
    return '—';
  }
  return formatNumber(first.data[first.data.length - 1][1]);
});

/** 项目健康度小结：各状态数量（省略为 0 的状态） */
function projectHealth(p: ProjectInfo): string {
  const parts: string[] = [];
  const counts = p.stateCounts || { running: 0, finished: 0, crashed: 0, aborted: 0 };
  if (counts.running) parts.push(`运行 ${counts.running}`);
  if (counts.finished) parts.push(`完成 ${counts.finished}`);
  if (counts.crashed) parts.push(`异常 ${counts.crashed}`);
  if (counts.aborted) parts.push(`中止 ${counts.aborted}`);
  return parts.length ? parts.join(' · ') : '暂无实验';
}

/** 项目图标色调：有异常偏琥珀色，运行中偏绿色，其余蓝色 */
function projectTone(p: ProjectInfo): string {
  if ((p.stateCounts?.crashed ?? 0) > 0) return 'amber';
  if ((p.stateCounts?.running ?? 0) > 0) return '';
  return 'blue';
}

/** 活动图：各实验最近一次记录的主指标（metricSummary 首个 key）走势 */
async function loadChart(items: ExperimentListItem[]): Promise<void> {
  chartLoading.value = true;
  try {
    const candidates = items.filter((item) => item.metricSummary && item.metricSummary.length > 0);
    if (!candidates.length) {
      chartSeries.value = [];
      chartMetricKey.value = '';
      return;
    }
    chartMetricKey.value = candidates[0].metricSummary[0].key;
    const result: ChartSeries[] = [];
    for (const item of candidates) {
      const key = item.metricSummary[0].key;
      try {
        const res = await getExperimentMetrics(item.id, [key], 500);
        const points = res.series?.[key] ?? [];
        if (points.length) {
          result.push({
            name: item.name,
            color: item.color || undefined,
            data: points.map((p) => [p.step, p.value] as [number, number]),
          });
        }
      } catch {
        // 单个实验指标获取失败时跳过该曲线
      }
    }
    chartSeries.value = result;
  } finally {
    chartLoading.value = false;
  }
}

onMounted(async () => {
  loading.value = true;
  try {
    const [projectRes, runRes] = await Promise.all([getProjects(), getExperiments({ pageSize: 5 })]);
    projects.value = projectRes.projects;
    recentRuns.value = runRes.items;
    await loadChart(runRes.items);
  } catch {
    // 接口失败时页面保留空态
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">YOUR RESEARCH, IN FOCUS</div>
        <h1>实验工作台</h1>
        <p>把每一次探索留下的轨迹，变成下一次突破的起点。</p>
      </div>
      <div class="heading-actions">
        <button class="btn" @click="router.push('/projects')">
          <AppIcon name="folder" />查看项目
        </button>
        <button class="btn primary" @click="router.push('/experiments')">
          <AppIcon name="flask" />浏览实验
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="summary">
      <StatCard label="实验总数" :value="totals.total" icon="flask" tone="blue" :note="`覆盖 ${projects.length} 个项目`" />
      <StatCard label="运行中" :value="totals.running" icon="chart" :note="'正在进行的训练实验'" />
      <StatCard label="已结束" :value="totals.finished" icon="check" tone="amber" :note="finishedNote" />
      <StatCard label="异常" :value="totals.crashed" icon="clock" tone="violet" :note="'异常退出的训练实验'" />
    </div>

    <div class="section-grid">
      <!-- 活动图 -->
      <div class="panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">训练指标概览</h2>
            <p class="panel-sub">各实验最近一次记录的主指标走势 · 横轴为 Step</p>
          </div>
          <button class="subtle-button" @click="router.push('/compare')">
            对比实验 <AppIcon name="arrow" style="width: 13px" />
          </button>
        </div>
        <template v-if="chartSeries.length">
          <div class="chart-top">
            <div class="chart-number">{{ latestValue }}</div>
            <div class="chart-meta">
              最新 {{ chartMetricKey }}<br />
              <span class="up">{{ chartSeries.length }} 个实验同轴对比</span>
            </div>
          </div>
          <div class="chart-wrap">
            <LineChart :series="chartSeries" height="220px" />
          </div>
        </template>
        <div v-else-if="chartLoading || loading" class="loading">正在加载训练指标…</div>
        <EmptyState v-else text="暂无可展示的训练指标" hint="实验上报 scalar 指标后，这里会显示各实验的主指标走势。" />
      </div>

      <!-- 项目健康度 -->
      <div class="panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">项目空间</h2>
            <p class="panel-sub">最近活跃的项目与健康度</p>
          </div>
          <button class="subtle-button" @click="router.push('/projects')">
            全部 <AppIcon name="arrow" style="width: 13px" />
          </button>
        </div>
        <div v-if="projects.length" class="project-list">
          <div v-for="p in projects" :key="p.name" class="project-row">
            <div class="project-icon" :class="projectTone(p)">{{ (p.name || '?').charAt(0).toUpperCase() }}</div>
            <div class="project-info">
              <strong>{{ p.name }}</strong>
              <small>{{ projectHealth(p) }} · 更新于 {{ formatDateTime(p.lastActivityAt) }}</small>
            </div>
            <div class="project-count">{{ p.runCount }}<small>实验</small></div>
          </div>
        </div>
        <EmptyState v-else-if="!loading" text="暂无项目" hint="接入 orlab-log 数据后自动聚合项目。" />
        <div v-else class="loading">正在加载项目…</div>
      </div>
    </div>

    <!-- 最近实验 -->
    <div class="panel">
      <div class="table-head">
        <div>
          <h2 class="panel-title">最近实验</h2>
          <p class="panel-sub">追踪每一次训练进展</p>
        </div>
        <button class="subtle-button" @click="router.push('/experiments')">
          查看全部实验 <AppIcon name="arrow" style="width: 13px" />
        </button>
      </div>
      <RunTable :items="recentRuns" empty-text="暂无实验记录" @open="openExperimentDrawer" />
      <div v-if="recentRuns.length" class="table-foot">
        <span>显示最近 {{ recentRuns.length }} 条实验</span>
        <button @click="router.push('/experiments')">进入实验列表 →</button>
      </div>
    </div>

    <div class="bottom-note">
      <span><i class="dot"></i>本地优先 · 面向 OpenRunLab 离线实验数据</span>
      <span>数据来源 · 本地 orlab-log 目录</span>
    </div>
  </div>
</template>
