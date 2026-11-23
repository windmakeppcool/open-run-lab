<!--
  实验状态徽章：running 绿 / finished 灰 / crashed 红 / aborted 米色
-->
<script setup lang="ts">
import { computed } from 'vue';
import type { RunState } from '../api/types';

const props = defineProps<{ state: RunState | string }>();

const stateNames: Record<string, string> = {
  running: '运行中',
  finished: '已完成',
  crashed: '异常',
  aborted: '中止',
};

const label = computed(() => stateNames[props.state] || props.state || '—');
</script>

<template>
  <span class="badge" :class="state">{{ label }}</span>
</template>
