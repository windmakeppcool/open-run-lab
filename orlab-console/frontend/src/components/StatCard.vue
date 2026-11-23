<!--
  统计卡片（工作台 4 宫格）
-->
<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  note?: string;
  /** 图标名（对应 SVG symbol） */
  icon: string;
  /** 图标色调：green / amber / blue / violet */
  tone?: 'green' | 'amber' | 'blue' | 'violet';
}>();
</script>

<template>
  <div class="stat">
    <div class="stat-top">
      {{ label }}
      <span class="stat-icon" :class="tone && tone !== 'green' ? tone : ''">
        <svg class="icon"><use :href="`#i-${icon}`" /></svg>
      </span>
    </div>
    <div class="stat-value">{{ value }}</div>
    <div v-if="note" class="stat-note">{{ note }}</div>
  </div>
</template>
