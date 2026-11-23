<!--
  空态占位
-->
<script setup lang="ts">
withDefaults(
  defineProps<{
    text?: string;
    hint?: string;
  }>(),
  {
    text: '暂无数据',
    hint: '',
  },
);
</script>

<template>
  <div class="empty">
    <div>{{ text }}</div>
    <div v-if="hint" class="panel-sub" style="margin-top: 8px">{{ hint }}</div>
    <slot />
  </div>
</template>
