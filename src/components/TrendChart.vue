<template>
  <div class="trend-chart">
    <Line v-if="loaded" :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Filler,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler)

const props = defineProps<{
  history: { m: number; p: number }[]
  currentProfit: number
}>()

const loaded = ref(true)

const chartData = computed(() => {
  const vals = [...props.history.map(x => x.p), props.currentProfit]
  const labels = vals.map((_, i) => String(i + 1))
  return {
    labels,
    datasets: [
      {
        label: '月利润',
        data: vals,
        borderColor: '#4CAF50',
        backgroundColor: (ctx: any) => {
          if (!ctx.chart.chartArea) return 'transparent'
          const g = ctx.chart.ctx.createLinearGradient(0, ctx.chart.chartArea.top, 0, ctx.chart.chartArea.bottom)
          g.addColorStop(0, 'rgba(76, 175, 80, 0.25)')
          g.addColorStop(1, 'rgba(76, 175, 80, 0.01)')
          return g
        },
        fill: true,
        tension: 0.3,
        pointRadius: vals.map((v: number) => v === props.currentProfit ? 4 : 2.5),
        pointBackgroundColor: vals.map((v: number) => v >= 0 ? '#4CAF50' : '#f44336'),
        pointBorderColor: vals.map((v: number) => v >= 0 ? '#4CAF50' : '#f44336'),
        pointHoverRadius: 6,
        borderWidth: 2,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 500,
    easing: 'easeOutQuart' as const,
  },
  plugins: {
    legend: { display: false },
    title: {
      display: true,
      text: '📈 月度利润走势',
      color: '#4a7aaa',
      font: { size: 12, family: 'monospace' },
      padding: { top: 6, bottom: 2 },
      align: 'start' as const,
    },
    tooltip: {
      backgroundColor: '#0d1f3c',
      titleColor: '#8a9aaa',
      bodyColor: '#4CAF50',
      borderColor: '#1a3a5a',
      borderWidth: 1,
      padding: 8,
      callbacks: {
        label: (ctx: any) => {
          const v = ctx.parsed.y
          return (v >= 0 ? '+' : '') + '¥' + Math.abs(v).toLocaleString()
        },
      },
    },
  },
  scales: {
    x: {
      display: true,
      grid: { display: false },
      ticks: {
        color: '#3a5a7a',
        font: { size: 9, family: 'monospace' },
        maxTicksLimit: 6,
        callback: (val: any, i: number) => i + 1,
      },
    },
    y: {
      display: true,
      grid: {
        color: '#1a2a4a',
        drawBorder: false,
      },
      ticks: {
        color: '#3a5a7a',
        font: { size: 9, family: 'monospace' },
        maxTicksLimit: 5,
        callback: (val: any) => {
          if (Math.abs(val) >= 10000) return (val / 10000).toFixed(1) + '万'
          if (Math.abs(val) >= 1000) return (val / 1000).toFixed(1) + 'k'
          return val
        },
      },
    },
  },
}))
</script>

<style scoped>
.trend-chart {
  width: 100%;
  height: 100%;
  background: #0a0a0a;
  padding: 2px 8px 4px;
}
</style>
