<!--
  实验详情抽屉（全局组件）：
  tabs = 概览 / 指标 / 日志 / 媒体 / 配置
  打开时调用 /api/experiments/:id；Esc 或点击遮罩关闭。
-->
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import StatusBadge from './StatusBadge.vue';
import EmptyState from './EmptyState.vue';
import LineChart, { type ChartSeries } from './LineChart.vue';
import { getExperiment, getExperimentLogs, getExperimentMedia, getExperimentMetrics } from '../api';
import type { ExperimentDetail, LogItem, MediaItem, MetricStat } from '../api/types';
import { closeExperimentDrawer, drawerState } from '../composables/useDrawer';
import { formatDateTime, formatDuration, formatNumber, formatSize } from '../utils/format';

type TabKey = 'overview' | 'metrics' | 'logs' | 'media' | 'config';

/** tab 定义 */
const tabs: Array<{ key: TabKey; label: string }> = [
  { key: 'overview', label: '概览' },
  { key: 'metrics', label: '指标' },
  { key: 'logs', label: '日志' },
  { key: 'media', label: '媒体' },
  { key: 'config', label: '配置' },
];

const activeTab = ref<TabKey>('overview');
const detail = ref<ExperimentDetail | null>(null);
const loading = ref(false);
const error = ref('');

/** 抽屉是否打开 */
const visible = computed(() => drawerState.open);

/** ---------- 概览 / 配置：键值展示辅助 ---------- */

/** 单个配置值的展示文本（兼容 OpenRunLab config.yaml 的 {value, desc, sort} 结构） */
function displayValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '—';
  }
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    if ('value' in record && Object.keys(record).every((k) => ['value', 'desc', 'sort'].includes(k))) {
      return displayValue(record.value);
    }
    return JSON.stringify(value);
  }
  return String(value);
}

/** 对象转键值对列表 */
function toEntries(obj: Record<string, unknown> | null | undefined): Array<[string, string]> {
  if (!obj) {
    return [];
  }
  return Object.entries(obj).map(([key, value]) => [key, displayValue(value)]);
}

/** metadata 原始 JSON 文本 */
const metadataJson = computed(() =>
  detail.value?.metadata ? JSON.stringify(detail.value.metadata, null, 2) : '',
);

/** ---------- 指标 tab ---------- */
interface MetricChart {
  key: string;
  stat: MetricStat | null;
  series: ChartSeries[];
}

const metricCharts = ref<MetricChart[]>([]);
const metricsLoading = ref(false);
const metricsLoaded = ref(false);

/** 是否为 __orlab__. 系统监控指标（真实数据里常有几十个） */
const isSystemKey = (key: string): boolean => key.startsWith('__orlab__.');
const customCharts = computed(() => metricCharts.value.filter((c) => !isSystemKey(c.key)));
const systemCharts = computed(() => metricCharts.value.filter((c) => isSystemKey(c.key)));
/** 系统监控指标默认折叠，展开后才渲染图表，避免一次性创建几十个 ECharts 实例 */
const showSystemCharts = ref(false);

/** 拉取全部 scalar 指标序列 */
async function loadMetrics(): Promise<void> {
  if (!detail.value || metricsLoaded.value || metricsLoading.value) {
    return;
  }
  metricsLoading.value = true;
  try {
    const keys = Object.keys(detail.value.metrics || {});
    if (!keys.length) {
      metricCharts.value = [];
      metricsLoaded.value = true;
      return;
    }
    const res = await getExperimentMetrics(detail.value.id, keys, 500);
    metricCharts.value = keys.map((key) => {
      const points = res.series?.[key] ?? [];
      return {
        key,
        stat: detail.value?.metrics?.[key] ?? null,
        series: points.length
          ? [
              {
                name: key,
                color: detail.value?.color || undefined,
                data: points.map((p) => [p.step, p.value] as [number, number]),
              },
            ]
          : [],
      };
    });
    metricsLoaded.value = true;
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载指标失败';
  } finally {
    metricsLoading.value = false;
  }
}

/** ---------- 日志 tab ---------- */
const logItems = ref<LogItem[]>([]);
const logTotal = ref(0);
const logOffset = ref(0);
const logLimit = 50;
const logLevel = ref<'' | 'info' | 'error'>('');
const logsLoading = ref(false);
const logsLoaded = ref(false);

const logPageInfo = computed(() => {
  const start = logTotal.value ? logOffset.value + 1 : 0;
  const end = Math.min(logOffset.value + logLimit, logTotal.value);
  return `第 ${start} – ${end} 条 / 共 ${logTotal.value} 条`;
});

/** 拉取当前页日志 */
async function loadLogs(): Promise<void> {
  if (!detail.value || logsLoading.value) {
    return;
  }
  logsLoading.value = true;
  try {
    const res = await getExperimentLogs(detail.value.id, {
      level: logLevel.value || undefined,
      limit: logLimit,
      offset: logOffset.value,
    });
    logItems.value = res.items;
    logTotal.value = res.total;
    logsLoaded.value = true;
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载日志失败';
  } finally {
    logsLoading.value = false;
  }
}

/** 日志级别过滤切换 */
function onLogLevelChange(): void {
  logOffset.value = 0;
  logsLoaded.value = false;
  loadLogs();
}

/** 日志翻页 */
function turnLogPage(delta: number): void {
  logOffset.value = Math.max(0, logOffset.value + delta * logLimit);
  logsLoaded.value = false;
  loadLogs();
}

/** 单行日志文本：[时间] [级别] 内容 */
function logLineText(item: LogItem): string {
  const parts: string[] = [];
  if (item.timestamp) {
    parts.push(`[${item.timestamp}]`);
  }
  if (item.level) {
    parts.push(`[${String(item.level).toUpperCase()}]`);
  }
  parts.push(String(item.line ?? ''));
  return parts.join(' ');
}

/** ---------- 媒体 tab ---------- */
const mediaItems = ref<MediaItem[]>([]);
const mediaLoading = ref(false);
const mediaLoaded = ref(false);

/** 判断媒体条目是否为图片 */
function isImage(item: MediaItem): boolean {
  const type = (item.type || '').toLowerCase();
  if (type.startsWith('image')) {
    return true;
  }
  const name = (item.filename || item.url || '').toLowerCase();
  return /\.(png|jpe?g|gif|webp|bmp|svg)(\?|$)/.test(name);
}

/** 拉取媒体列表 */
async function loadMedia(): Promise<void> {
  if (!detail.value || mediaLoaded.value || mediaLoading.value) {
    return;
  }
  mediaLoading.value = true;
  try {
    const res = await getExperimentMedia(detail.value.id);
    mediaItems.value = res.items;
    mediaLoaded.value = true;
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载媒体失败';
  } finally {
    mediaLoading.value = false;
  }
}

/** ---------- 抽屉开关与数据加载 ---------- */

/** 重置各 tab 的懒加载状态 */
function resetTabData(): void {
  activeTab.value = 'overview';
  metricCharts.value = [];
  metricsLoaded.value = false;
  logItems.value = [];
  logTotal.value = 0;
  logOffset.value = 0;
  logLevel.value = '';
  logsLoaded.value = false;
  mediaItems.value = [];
  mediaLoaded.value = false;
}

/** 打开时拉取实验详情 */
async function loadDetail(id: string): Promise<void> {
  loading.value = true;
  error.value = '';
  detail.value = null;
  resetTabData();
  try {
    detail.value = await getExperiment(id);
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载实验详情失败';
  } finally {
    loading.value = false;
  }
}

watch(
  () => (drawerState.open ? drawerState.experimentId : ''),
  (id) => {
    if (id) {
      loadDetail(id);
    }
  },
);

/** tab 切换时懒加载对应数据 */
watch(activeTab, (tab) => {
  if (tab === 'metrics') {
    loadMetrics();
  } else if (tab === 'logs') {
    if (!logsLoaded.value) {
      loadLogs();
    }
  } else if (tab === 'media') {
    loadMedia();
  }
});

/** Esc 关闭 */
function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && drawerState.open) {
    closeExperimentDrawer();
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown);
});

/** 打开抽屉时锁定页面滚动 */
watch(visible, (open) => {
  document.body.style.overflow = open ? 'hidden' : '';
});

/** 抽屉副标题 */
const subtitle = computed(() => {
  const d = detail.value;
  if (!d) {
    return '';
  }
  const stateName: Record<string, string> = {
    running: '运行中',
    finished: '已完成',
    crashed: '异常',
    aborted: '中止',
  };
  return `${d.project || '—'}  /  #${d.id}  /  ${stateName[d.state] || d.state}`;
});
</script>

<template>
  <div v-if="visible" class="drawer-overlay" @click.self="closeExperimentDrawer">
    <aside class="drawer" role="dialog" aria-modal="true" aria-label="实验详情">
      <div class="drawer-head">
        <div>
          <div class="eyebrow">EXPERIMENT DETAILS</div>
          <h2>{{ detail?.name || '加载中…' }}</h2>
          <p>{{ subtitle }}</p>
        </div>
        <button class="close" aria-label="关闭详情" @click="closeExperimentDrawer">×</button>
      </div>

      <div class="drawer-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="drawer-body">
        <div v-if="loading" class="loading">正在加载实验详情…</div>
        <div v-else-if="error && !detail" class="error-box">{{ error }}</div>

        <template v-else-if="detail">
          <!-- ===== 概览 ===== -->
          <template v-if="activeTab === 'overview'">
            <div class="detail-grid">
              <div class="detail-box">
                <small>状态</small>
                <strong><StatusBadge :state="detail.state" /></strong>
              </div>
              <div class="detail-box">
                <small>时长</small>
                <strong>{{ formatDuration(detail.durationSec) }}</strong>
              </div>
              <div class="detail-box">
                <small>开始时间</small>
                <strong>{{ formatDateTime(detail.startedAt) }}</strong>
              </div>
              <div class="detail-box">
                <small>结束时间</small>
                <strong>{{ formatDateTime(detail.finishedAt) }}</strong>
              </div>
            </div>

            <div v-if="detail.error" class="error-box">{{ detail.error }}</div>

            <div class="detail-title">描述</div>
            <p class="panel-sub" style="font-size: 12px; line-height: 1.8">{{ detail.description || '—' }}</p>

            <div class="detail-title">标签</div>
            <div>
              <span v-for="tag in detail.tags" :key="tag" class="tag">{{ tag }}</span>
              <span v-if="!detail.tags || !detail.tags.length" class="panel-sub">—</span>
            </div>

            <div class="detail-title">训练配置 <span style="color: #aab5ad; font-weight: 400">· config.yaml</span></div>
            <div v-if="toEntries(detail.config).length" class="detail-list">
              <div v-for="[key, value] in toEntries(detail.config)" :key="key">
                <span>{{ key }}</span>
                <span>{{ value }}</span>
              </div>
            </div>
            <div v-else class="media-empty">暂无配置信息</div>

            <div class="detail-title">元数据 <span style="color: #aab5ad; font-weight: 400">· metadata</span></div>
            <div v-if="toEntries(detail.metadata).length" class="detail-list">
              <div v-for="[key, value] in toEntries(detail.metadata)" :key="key">
                <span>{{ key }}</span>
                <span>{{ value }}</span>
              </div>
            </div>
            <div v-else class="media-empty">暂无元数据</div>

            <div class="detail-title">保存的文件</div>
            <div v-if="detail.files && detail.files.length" class="detail-list">
              <div v-for="file in detail.files" :key="file">
                <span>文件</span>
                <span>{{ file }}</span>
              </div>
            </div>
            <div v-else class="media-empty">暂无保存文件</div>
          </template>

          <!-- ===== 指标 ===== -->
          <template v-else-if="activeTab === 'metrics'">
            <div v-if="metricsLoading" class="loading">正在加载指标…</div>
            <template v-else-if="metricCharts.length">
              <div class="detail-title" style="margin-top: 0">
                训练指标 <span style="color: #aab5ad; font-weight: 400">· 共 {{ customCharts.length }} 个指标</span>
              </div>
              <template v-if="customCharts.length">
                <div v-for="chart in customCharts" :key="chart.key" class="metric-chart-card">
                  <div class="metric-chart-head">
                    <strong>{{ chart.key }}</strong>
                    <small>
                      最新 {{ formatNumber(chart.stat?.last) }} · 最小 {{ formatNumber(chart.stat?.min) }} ·
                      最大 {{ formatNumber(chart.stat?.max) }} · 平均 {{ formatNumber(chart.stat?.avg) }}
                    </small>
                  </div>
                  <LineChart v-if="chart.series.length" :series="chart.series" height="160px" :show-legend="false" />
                  <div v-else class="media-empty">该指标暂无数据点</div>
                </div>
              </template>
              <div v-else class="media-empty">没有自定义指标，该实验仅记录了系统监控指标</div>
              <template v-if="systemCharts.length">
                <button class="btn" style="width: 100%; margin: 6px 0 12px" @click="showSystemCharts = !showSystemCharts">
                  系统监控指标 · 共 {{ systemCharts.length }} 个（{{ showSystemCharts ? '收起' : '展开' }}）
                </button>
                <template v-if="showSystemCharts">
                  <div v-for="chart in systemCharts" :key="chart.key" class="metric-chart-card">
                    <div class="metric-chart-head">
                      <strong>{{ chart.key }}</strong>
                      <small>
                        最新 {{ formatNumber(chart.stat?.last) }} · 最小 {{ formatNumber(chart.stat?.min) }} ·
                        最大 {{ formatNumber(chart.stat?.max) }} · 平均 {{ formatNumber(chart.stat?.avg) }}
                      </small>
                    </div>
                    <LineChart v-if="chart.series.length" :series="chart.series" height="160px" :show-legend="false" />
                    <div v-else class="media-empty">该指标暂无数据点</div>
                  </div>
                </template>
              </template>
            </template>
            <EmptyState v-else text="该实验没有 scalar 指标" hint="实验上报指标后，这里会展示各指标的走势曲线。" />
          </template>

          <!-- ===== 日志 ===== -->
          <template v-else-if="activeTab === 'logs'">
            <div class="detail-title" style="margin-top: 0; display: flex; justify-content: space-between; align-items: center">
              <span>终端日志 <span style="color: #aab5ad; font-weight: 400">· 共 {{ detail.logCount }} 条</span></span>
              <select v-model="logLevel" aria-label="按级别筛选日志" @change="onLogLevelChange">
                <option value="">全部级别</option>
                <option value="info">info</option>
                <option value="error">error</option>
              </select>
            </div>
            <div v-if="logsLoading" class="loading">正在加载日志…</div>
            <div v-else-if="logItems.length" class="logs">
              <div
                v-for="(item, index) in logItems"
                :key="`${item.line}-${index}`"
                class="log-line"
                :class="`level-${item.level || 'info'}`"
              >
                {{ logLineText(item) }}
              </div>
            </div>
            <EmptyState v-else text="暂无日志" />
            <div class="table-foot" style="padding-left: 0; padding-right: 0">
              <span>{{ logPageInfo }}</span>
              <div class="pager">
                <button :disabled="logOffset <= 0 || logsLoading" @click="turnLogPage(-1)">上一页</button>
                <button :disabled="logOffset + logLimit >= logTotal || logsLoading" @click="turnLogPage(1)">下一页</button>
              </div>
            </div>
          </template>

          <!-- ===== 媒体 ===== -->
          <template v-else-if="activeTab === 'media'">
            <div class="detail-title" style="margin-top: 0">
              媒体文件 <span style="color: #aab5ad; font-weight: 400">· 共 {{ detail.mediaCount }} 个</span>
            </div>
            <div v-if="mediaLoading" class="loading">正在加载媒体…</div>
            <div v-else-if="mediaItems.length" class="media-grid">
              <div v-for="(item, index) in mediaItems" :key="`${item.key}-${item.step}-${index}`" class="media-card">
                <!-- 图片直接渲染 url -->
                <img v-if="isImage(item)" :src="item.url" :alt="item.caption || item.filename || item.key" loading="lazy" />
                <!-- 其它类型显示文件名 -->
                <div v-else class="media-file">{{ item.filename || item.key }}</div>
                <div class="media-meta">
                  <div>指标：{{ item.key }}<span v-if="item.step !== null"> · step {{ item.step }}</span></div>
                  <div v-if="item.caption">说明：{{ item.caption }}</div>
                  <div v-if="item.size !== null">大小：{{ formatSize(item.size) }}</div>
                </div>
              </div>
            </div>
            <div v-else class="media-empty">
              暂无媒体文件<br />
              实验上报图片、文本等媒体后，会在这里展示。
            </div>
          </template>

          <!-- ===== 配置 ===== -->
          <template v-else-if="activeTab === 'config'">
            <div class="detail-title" style="margin-top: 0">
              训练配置 <span style="color: #aab5ad; font-weight: 400">· config.yaml 解析结果</span>
            </div>
            <div v-if="toEntries(detail.config).length" class="detail-list">
              <div v-for="[key, value] in toEntries(detail.config)" :key="key">
                <span>{{ key }}</span>
                <span>{{ value }}</span>
              </div>
            </div>
            <div v-else class="media-empty">暂无配置信息</div>

            <div class="detail-title">
              元数据 <span style="color: #aab5ad; font-weight: 400">· 原始 JSON</span>
            </div>
            <pre v-if="metadataJson" class="json-block">{{ metadataJson }}</pre>
            <div v-else class="media-empty">暂无元数据</div>
          </template>
        </template>
      </div>
    </aside>
  </div>
</template>
