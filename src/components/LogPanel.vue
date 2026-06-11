<template>
  <div class="log-panel">
    <div class="lp-header">📋 运行日志</div>
    <div class="lp-empty" v-if="logs.length === 0">暂无记录，点击 ▶ 推进下月</div>
    <div class="lp-scroll" v-else ref="scrollRef">
      <div v-for="(entry, idx) in logs" :key="idx" class="lp-entry">
        <div class="lp-meta">
          <span class="lp-month">📅 {{ entry.m }}月</span>
          <span class="lp-profit" :class="entry.p >= 0 ? 'clr-green' : 'clr-red'">
            {{ entry.p >= 0 ? '+' : '' }}¥{{ Math.abs(entry.p).toLocaleString() }}
          </span>
        </div>
        <pre class="lp-text">{{ entry.text || '(无详情)' }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

export interface LogEntry {
  m: number        // 月份
  p: number        // 当月利润
  t: number        // 累计现金流
  detail?: Record<string, any>  // 关键指标速览
  text?: string     // 变更追踪全文
}

const props = defineProps<{ logs: LogEntry[] }>()
const scrollRef = ref<HTMLElement>()

watch(() => props.logs.length, async () => {
  await nextTick()
  if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
})
</script>

<style scoped>
.log-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
  font-size: 11px;
  overflow: hidden;
}
.lp-header {
  padding: 10px 12px;
  font-size: 13px;
  font-weight: bold;
  color: #4CAF50;
  border-bottom: 1px solid #1a2a1a;
  flex-shrink: 0;
  font-family: monospace;
}
.lp-empty {
  padding: 24px 12px;
  text-align: center;
  color: #3a3a3a;
  font-size: 11px;
}
.lp-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0;
}
.lp-scroll::-webkit-scrollbar { width: 4px; }
.lp-scroll::-webkit-scrollbar-track { background: transparent; }
.lp-scroll::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 2px; }

.lp-entry {
  padding: 6px 12px;
  border-bottom: 1px solid #141414;
  transition: background 0.15s;
}
.lp-entry:hover { background: #111; }

.lp-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.lp-month { color: #FFD700; font-weight: 600; }
.lp-profit { font-weight: bold; font-family: monospace; font-size: 12px; }
.clr-green { color: #4CAF50; }
.clr-red { color: #f44336; }

.lp-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 3px 6px;
  margin-top: 3px;
}
.lp-stat {
  font-size: 10px;
  color: #5a5a5a;
  font-family: monospace;
}
.lp-text {
  font-size: 10px;
  color: #9a9a9a;
  font-family: monospace;
  line-height: 1.5;
  margin: 3px 0 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
