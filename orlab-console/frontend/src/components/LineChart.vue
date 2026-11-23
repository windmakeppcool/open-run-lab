<!--
  ECharts 折线图封装：多系列 step-value 曲线叠加
-->
<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import * as echarts from 'echarts';

/** 单条曲线：data 为 [step, value] 点序列 */
export interface ChartSeries {
  name: string;
  color?: string;
  data: Array<[number, number]>;
}

const props = withDefaults(
  defineProps<{
    series: ChartSeries[];
    height?: string;
    xName?: string;
    yName?: string;
    showLegend?: boolean;
  }>(),
  {
    height: '220px',
    xName: 'Step',
    yName: '',
    showLegend: true,
  },
);

const el = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;
let observer: ResizeObserver | null = null;

// 默认配色沿用设计原型的曲线色板
const PALETTE = ['#4d9871', '#d5a075', '#7d9eb2', '#a996c2', '#c98579', '#6f8fb0', '#8fae6e'];

/** 渲染 / 更新图表 */
function render(): void {
  if (!chart) {
    return;
  }
  chart.setOption(
    {
      color: props.series.map((s, i) => s.color || PALETTE[i % PALETTE.length]),
      grid: {
        left: 52,
        right: 18,
        top: props.showLegend ? 38 : 14,
        bottom: 32,
      },
      legend: props.showLegend
        ? {
            top: 8,
            left: 0,
            icon: 'circle',
            itemWidth: 7,
            itemHeight: 7,
            textStyle: { color: '#8b9890', fontSize: 11 },
          }
        : undefined,
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#fff',
        borderColor: '#e8ede8',
        textStyle: { color: '#516158', fontSize: 11 },
        axisPointer: { type: 'line', lineStyle: { color: '#c8d6cc' } },
      },
      xAxis: {
        type: 'value',
        name: props.xName,
        nameTextStyle: { color: '#a5b0a8', fontSize: 10 },
        scale: true,
        axisLabel: { color: '#a5b0a8', fontSize: 10 },
        axisLine: { lineStyle: { color: '#edf1ed' } },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        name: props.yName,
        nameTextStyle: { color: '#a5b0a8', fontSize: 10 },
        scale: true,
        axisLabel: { color: '#a5b0a8', fontSize: 10 },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#edf1ed' } },
      },
      series: props.series.map((s) => ({
        name: s.name,
        type: 'line' as const,
        data: s.data,
        showSymbol: false,
        smooth: false,
        lineStyle: { width: 2.5 },
        emphasis: { focus: 'series' as const },
      })),
    },
    true,
  );
}

onMounted(() => {
  if (!el.value) {
    return;
  }
  chart = echarts.init(el.value);
  render();
  // 容器尺寸变化时自适应
  observer = new ResizeObserver(() => {
    chart?.resize();
  });
  observer.observe(el.value);
});

watch(
  () => props.series,
  () => render(),
  { deep: true },
);

onBeforeUnmount(() => {
  observer?.disconnect();
  observer = null;
  chart?.dispose();
  chart = null;
});
</script>

<template>
  <div ref="el" class="line-chart" :style="{ height }"></div>
</template>
