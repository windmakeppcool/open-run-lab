<!--
  图标组件：引用 App.vue 中的 SVG symbol 精灵图
  用法：<AppIcon name="grid" />
-->
<script setup lang="ts">
defineProps<{ name: string }>();
</script>

<template>
  <svg class="icon" aria-hidden="true"><use :href="`#i-${name}`" /></svg>
</template>
