<!--
  实验记录：筛选条 + 实验表格（勾选对比 / 打开详情抽屉）+ 分页
-->
<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import RunTable from '../components/RunTable.vue';
import AppIcon from '../components/AppIcon.vue';
import { getExperiments, getProjects } from '../api';
import type { ExperimentListItem, ProjectInfo, RunState } from '../api/types';
import { openExperimentDrawer } from '../composables/useDrawer';

const route = useRoute();
const router = useRouter();

const items = ref<ExperimentListItem[]>([]);
const projects = ref<ProjectInfo[]>([]);
const total = ref(0);
const loading = ref(true);

const PAGE_SIZE = 20;

/** 筛选与分页状态 */
const filters = reactive({
  search: '',
  status: '' as '' | RunState,
  project: '',
  page: 1,
});

/** 已勾选的实验 id */
const selected = ref<string[]>([]);

/** 状态下拉选项 */
const statusOptions: Array<{ value: '' | RunState; label: string }> = [
  { value: '', label: '全部状态' },
  { value: 'running', label: '运行中' },
  { value: 'finished', label: '已完成' },
  { value: 'crashed', label: '异常' },
  { value: 'aborted', label: '中止' },
];

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)));

/** 拉取实验列表 */
async function load(): Promise<void> {
  loading.value = true;
  try {
    const res = await getExperiments({
      search: filters.search || undefined,
      status: filters.status || undefined,
      project: filters.project || undefined,
      page: filters.page,
      pageSize: PAGE_SIZE,
    });
    items.value = res.items;
    total.value = res.total;
  } catch {
    items.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

/** 搜索防抖 */
let searchTimer: ReturnType<typeof setTimeout> | undefined;
function onSearchInput(): void {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    filters.page = 1;
    load();
  }, 250);
}

/** 筛选变化时回到第一页 */
function onFilterChange(): void {
  filters.page = 1;
  load();
}

/** 勾选 / 取消勾选实验 */
function toggle(id: string, checked: boolean): void {
  if (checked) {
    if (!selected.value.includes(id)) {
      selected.value = [...selected.value, id];
    }
  } else {
    selected.value = selected.value.filter((item) => item !== id);
  }
}

/** ≥2 个勾选时跳转对比页并带上所选 id */
function goCompare(): void {
  if (selected.value.length < 2) {
    return;
  }
  // 同步到本地状态，便于刷新后仍可恢复
  sessionStorage.setItem('compareIds', selected.value.join(','));
  router.push({ path: '/compare', query: { ids: selected.value.join(',') } });
}

onMounted(async () => {
  // 从查询参数恢复筛选（支持项目卡片跳转带 project 过滤）
  const q = route.query;
  if (typeof q.project === 'string') filters.project = q.project;
  if (typeof q.status === 'string' && statusOptions.some((o) => o.value === q.status)) {
    filters.status = q.status as RunState;
  }
  if (typeof q.search === 'string') filters.search = q.search;
  await load();
  try {
    const res = await getProjects();
    projects.value = res.projects;
  } catch {
    // 项目下拉获取失败时仅保留「全部项目」
  }
});

// 外部路由参数变化（如再次从项目卡片跳转）时同步筛选
watch(
  () => route.query.project,
  (value) => {
    if (route.name !== 'experiments') {
      return;
    }
    const next = typeof value === 'string' ? value : '';
    if (next !== filters.project) {
      filters.project = next;
      filters.page = 1;
      load();
    }
  },
);
</script>

<template>
  <div>
    <div class="page-heading">
      <div>
        <div class="eyebrow">EXPERIMENT TRACKING</div>
        <h1>实验记录</h1>
        <p>筛选、查看与比较训练实验，发现影响结果的关键变化。</p>
      </div>
      <button class="btn primary" :disabled="selected.length < 2" @click="goCompare">
        <AppIcon name="chart" />对比所选 <span>{{ selected.length }}</span>
      </button>
    </div>

    <div class="panel">
      <div class="table-head">
        <div>
          <h2 class="panel-title">全部实验</h2>
          <p class="panel-sub">选择实验名称查看详情，勾选实验进行对比</p>
        </div>
        <div class="filters">
          <label class="search">
            <AppIcon name="search" />
            <input v-model="filters.search" type="search" placeholder="搜索实验或项目" aria-label="搜索实验或项目" @input="onSearchInput" />
          </label>
          <select v-model="filters.status" aria-label="按状态筛选" @change="onFilterChange">
            <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
          <select v-model="filters.project" aria-label="按项目筛选" @change="onFilterChange">
            <option value="">全部项目</option>
            <option v-for="p in projects" :key="p.name" :value="p.name">{{ p.name }}</option>
          </select>
        </div>
      </div>

      <RunTable
        :items="items"
        selectable
        :selected="selected"
        :empty-text="loading ? '正在加载实验…' : '没有匹配的实验，试试调整筛选条件。'"
        @open="openExperimentDrawer"
        @toggle="toggle"
      />

      <div class="table-foot">
        <span>共 {{ total }} 条实验 · 第 {{ filters.page }} / {{ pageCount }} 页</span>
        <div class="pager">
          <span>已选择 {{ selected.length }} 个实验</span>
          <button :disabled="filters.page <= 1 || loading" @click="filters.page--; load()">上一页</button>
          <button :disabled="filters.page >= pageCount || loading" @click="filters.page++; load()">下一页</button>
        </div>
      </div>
    </div>
  </div>
</template>
