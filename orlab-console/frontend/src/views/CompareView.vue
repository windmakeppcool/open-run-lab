<!--
  实验对比：多实验同一指标的 ECharts 多系列折线叠加（x=step）
  所选实验 id 来自查询参数 ?ids=a,b，或本地状态（sessionStorage）回退。
-->
<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import LineChart, { type ChartSeries } from '../components/LineChart.vue';
import EmptyState from '../components/EmptyState.vue';
import AppIcon from '../components/AppIcon.vue';
import { getExperiment, getExperimentMetrics } from '../api';
import type { ExperimentDetail } from '../api/types';

const route = useRoute();
const router = useRouter();

/** 所选实验 id：优先查询参数，回退本地状态 */
const ids = computed<string[]>(() => {
  const q = route.query.ids;
  const fromQuery = typeof q === 'string' ? q.split(',').map((s) => s.trim()).filter(Boolean) : [];
  if (fromQuery.length) {
    return fromQuery;
  }
  const stored = sessionStorage.getItem('compareIds');
  return stored ? stored.split(',').map((s) => s.trim()).filter(Boolean) : [];
});

/** 所选实验详情 */
const details = ref<ExperimentDetail[]>([]);
const loading = ref(false);
const error = ref('');

/** 指标 key 下拉：所选实验 scalar 指标 key 的并集（详情接口 metrics 字段的键） */
const metricKeys = computed<string[]>(() => {
  const set = new Set<string>();
  for (const d of details.value) {
    for (const key of Object.keys(d.metrics || {})) {
      set.add(key);
    }
  }
  return [...set];
});

/** 当前指标 key */
const currentKey = ref('');

/** 对比曲线 */
const chartSeries = ref<ChartSeries[]>([]);
const seriesLoading = ref(false);

/** 为当前指标拉取各实验曲线 */
async function loadSeries(): Promise<void> {
  if (!currentKey.value || !details.value.length) {
    chartSeries.value = [];
    return;
  }
  seriesLoading.value = true;
  try {
    const result: ChartSeries[] = [];
    for (const d of details.value) {
      try {
        const res = await getExperimentMetrics(d.id, [currentKey.value], 500);
        const points = res.series?.[currentKey.value] ?? [];
        if (points.length) {
          result.push({
            name: d.name,
            color: d.color || undefined,
            data: points.map((p) => [p.step, p.value] as [number, number]),
          });
        }
      } catch {
        // 单个实验数据缺失时跳过该曲线
      }
    }
    chartSeries.value = result;
  } finally {
    seriesLoading.value = false;
  }
}

/** 拉取实验详情并确定默认指标 key */
async function loadDetails(): Promise<void> {
  if (!ids.value.length) {
    details.value = [];
    chartSeries.value = [];
    return;
  }
  loading.value = true;
  error.value = '';
  try {
    const list = await Promise.all(
      ids.value.map(async (id) => {
        try {
          return await getExperiment(id);
        } catch {
          return null;
        }
      }),
    );
    details.value = list.filter((d): d is ExperimentDetail => d !== null);
    // 默认取并集中第一个 key（优先 train/loss）
    const keys = metricKeys.value;
    currentKey.value = keys.includes('train/loss') ? 'train/loss' : keys[0] || '';
    await loadSeries();
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载实验详情失败';
  } finally {
    loading.value = false;
  }
}

watch(currentKey, () => {
  loadSeries();
});

onMounted(loadDetails);
</script>

<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">COMPARE & DISCOVER</div>
        <h1>实验对比</h1>
        <p>把不同实验放在同一坐标系，直观观察训练过程。</p>
      </div>
      <button class="btn" @click="router.push('/experiments')">
        <AppIcon name="sliders" />选择实验
      </button>
    </div>

    <!-- 未选择实验时的引导空态 -->
    <div v-if="!ids.length" class="panel">
      <div class="compare-empty">
        还没有选择实验。<br />
        请前往「实验记录」勾选至少两个实验，再点击「对比所选」。
        <div style="margin-top: 18px">
          <button class="btn primary" @click="router.push('/experiments')">
            <AppIcon name="flask" />前往实验记录
          </button>
        </div>
      </div>
    </div>

    <template v-else>
      <div class="compare-banner">
        已选择 {{ ids.length }} 个实验 · 指标按 Step 对齐，每条曲线对应一个实验，可切换指标 key 观察不同指标。
      </div>
      <div v-if="error" class="error-box">{{ error }}</div>
      <div class="panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">{{ currentKey || '指标对比' }}</h2>
            <p class="panel-sub">按 Step 对齐 · 共 {{ chartSeries.length }} 条曲线</p>
          </div>
          <div class="filters">
            <select v-model="currentKey" aria-label="选择指标">
              <option v-for="key in metricKeys" :key="key" :value="key">{{ key }}</option>
            </select>
          </div>
        </div>
        <div v-if="loading || seriesLoading" class="loading">正在加载对比曲线…</div>
        <div v-else-if="chartSeries.length" class="compare-chart">
          <LineChart :series="chartSeries" height="280px" />
        </div>
        <EmptyState
          v-else
          text="所选实验暂无可对比的指标数据"
          hint="确认实验已上报所选指标后，这里会显示多系列对比曲线。"
        />
      </div>
    </template>
  </div>
</template>
