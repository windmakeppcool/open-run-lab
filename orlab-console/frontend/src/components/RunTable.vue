<!--
  实验表格：实验名（点击打开详情抽屉）/ 项目 / 状态 / 标签 / 开始时间 / 时长 / 关键指标
-->
<script setup lang="ts">
import StatusBadge from './StatusBadge.vue';
import EmptyState from './EmptyState.vue';
import type { ExperimentListItem } from '../api/types';
import { formatDateTime, formatDuration, formatNumber } from '../utils/format';

withDefaults(
  defineProps<{
    items: ExperimentListItem[];
    /** 是否显示勾选列 */
    selectable?: boolean;
    /** 已勾选的实验 id */
    selected?: string[];
    emptyText?: string;
    emptyHint?: string;
  }>(),
  {
    selectable: false,
    selected: () => [],
    emptyText: '没有匹配的实验，试试调整筛选条件。',
    emptyHint: '',
  },
);

const emit = defineEmits<{
  open: [id: string];
  toggle: [id: string, checked: boolean];
}>();
</script>

<template>
  <EmptyState v-if="!items.length" :text="emptyText" :hint="emptyHint" />
  <div v-else class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>{{ selectable ? '选择' : '' }}</th>
          <th>实验名称</th>
          <th>所属项目</th>
          <th>状态</th>
          <th>标签</th>
          <th>开始时间</th>
          <th>时长</th>
          <th>关键指标</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>
            <input
              v-if="selectable"
              type="checkbox"
              :aria-label="`选择 ${item.name}`"
              :checked="selected.includes(item.id)"
              @change="emit('toggle', item.id, ($event.target as HTMLInputElement).checked)"
            />
          </td>
          <td>
            <button class="run-link" @click="emit('open', item.id)">
              {{ item.name }}
              <span class="run-id">#{{ item.id }}</span>
            </button>
          </td>
          <td>{{ item.project || '—' }}</td>
          <td><StatusBadge :state="item.state" /></td>
          <td>
            <template v-if="item.tags && item.tags.length">
              <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
            </template>
            <template v-else>—</template>
          </td>
          <td>{{ formatDateTime(item.startedAt) }}</td>
          <td>{{ formatDuration(item.durationSec) }}</td>
          <td>
            <!-- metricSummary 最多展示 2 个关键指标 -->
            <div v-if="item.metricSummary && item.metricSummary.length">
              <div v-for="metric in item.metricSummary.slice(0, 2)" :key="metric.key" class="metric-cell">
                <span class="metric-key">{{ metric.key }}</span>
                <span class="metric-val">{{ formatNumber(metric.last) }}</span>
              </div>
            </div>
            <template v-else>—</template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
