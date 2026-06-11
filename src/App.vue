<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <div class="app">
      <button class="guide-btn" @click="guideOpen = true">📖</button>
      <n-modal v-model:show="guideOpen" preset="card" :title="'🥖 面包店沙盘 · V8 推演指南'" style="max-width: 800px; width: 90vw" :segmented="false">
        <SimulationGuide />
      </n-modal>

      <div class="main-layout">
        <!-- 左侧: 指挥台 (200px) -->
        <aside class="left-panel">
          <BakerySandbox ref="sandboxRef" :engine="engine" :selected-node="selectedNodeId" @clear-node="selectedNodeId = ''" @select-node="selectedNodeId = $event" />
        </aside>

        <!-- 中间: 推演主舞台 -->
        <main class="middle-panel">
          <!-- 右上: 利润走势图 (fixed 230px) -->
          <div class="chart-area">
            <TrendChart
              :history="sandboxRef?.monthLog ?? []"
              :current-profit="sandboxRef?.p ?? 0"
            />
          </div>
          <!-- 右下: DAG 拓扑图 -->
          <div class="graph-area">
            <GraphEditor :engine="engine" :simple="true" @node-selected="selectedNodeId = $event" />
          </div>
        </main>

        <!-- 右侧: 日志面板 -->
        <aside class="log-panel-wrap">
          <LogPanel :logs="sandboxRef?.logEntries ?? []" />
        </aside>
      </div>
    </div>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NConfigProvider, NModal, darkTheme, zhCN, dateZhCN } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { createSheetEngine } from './engine'
import { useLogger } from '@meshflow/logger'
import GraphEditor from './GraphEditor.vue'
import BakerySandbox from './components/BakerySandbox.vue'
import TrendChart from './components/TrendChart.vue'
import SimulationGuide from './components/SimulationGuide.vue'
import LogPanel from './components/LogPanel.vue'

const engine = createSheetEngine()
const guideOpen = ref(false)
const sandboxRef = ref<InstanceType<typeof BakerySandbox>>()
const selectedNodeId = ref('')
let entangleReady = false

onMounted(() => {
  ;(window as any).__engine = engine as any
})

// 暗黑主题覆盖 — 纯黑底 + 绿金点缀
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#4CAF50',
    primaryColorHover: '#66BB6A',
    primaryColorPressed: '#388E3C',
    successColor: '#4CAF50',
    bodyColor: '#0a0a0a',
    cardColor: '#141414',
    modalColor: '#141414',
    tableColor: '#0a0a0a',
    inputColor: '#141414',
    inputColorDisabled: '#0a0a0a',
    actionColor: '#0a0a0a',
    popoverColor: '#141414',
    hoverColor: '#222222',
    borderColor: '#2a2a2a',
    textColor1: '#e0e0e0',
    textColor2: '#9a9a9a',
    textColor3: '#5a5a5a',
    borderRadius: '6px',
    fontSizeSmall: '11px',
    fontSize: '12px',
    fontSizeMedium: '12px',
    fontSizeLarge: '14px',
  },
  Button: {
    color: '#141414',
    colorHover: '#222222',
    colorPrimary: '#1a3a1a',
    colorHoverPrimary: '#2a5a2a',
    borderPrimary: '#2a5a2a',
    textColorPrimary: '#4CAF50',
    textColorHoverPrimary: '#66BB6A',
    textColorSuccess: '#4CAF50',
    colorSuccess: '#1a3a1a',
    colorHoverSuccess: '#2a5a2a',
    borderSuccess: '#2a5a2a',
    fontWeight: 'bold',
    fontSizeSmall: '12px',
    fontSizeMedium: '13px',
    fontSizeLarge: '15px',
  },
  Slider: {
    fillColor: '#4CAF50',
    fillColorHover: '#66BB6A',
    railColor: '#1a1a1a',
    railColorHover: '#2a2a2a',
    handleColor: '#4CAF50',
    handleColorHover: '#66BB6A',
    dotColor: '#1a1a1a',
    dotColorModal: '#1a1a1a',
    dotColorPopover: '#1a1a1a',
    handleSize: '20px',
    railHeight: '8px',
    fontSize: '10px',
    tooltipColor: '#141414',
    tooltipTextColor: '#e0e0e0',
    tooltipBoxShadow: '0 2px 8px rgba(0,0,0,0.4)',
  },
  Progress: {
    railColor: '#1a1a1a',
    fontSize: '9px',
    textColor: '#e0e0e0',
  },
  Tag: {
    color: '#222222',
    textColor: '#e0e0e0',
    border: '#2a2a2a',
    fontSizeSmall: '10px',
    padding: '0 6px',
  },
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: #0a0a0a;
  color: #e0e0e0;
  overflow: hidden;
  height: 100vh;
}
.app { width: 100%; height: 100vh; }

.guide-btn {
  position: fixed; top: 12px; right: 12px; z-index: 999;
  width: 36px; height: 36px; border-radius: 50%;
  border: 1px solid #2a2a2a; background: #141414;
  color: #ffd700; font-size: 16px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.4);
}
.guide-btn:hover { background: #222222; border-color: #4CAF50; }

/* 移除旧的 guide-overlay 样式 — 改用 n-modal */
.guide-overlay, .guide-panel, .guide-header, .guide-body, .close-btn { display: none; }

/* ===== 三栏布局 ===== */
.main-layout {
  display: grid;
  grid-template-columns: minmax(300px, 25%) 1fr 260px;
  height: 100vh;
}
.left-panel {
  background: #0a0a0a;
  border-right: 1px solid #2a2a2a;
  overflow: hidden;
}
.middle-panel {
  display: grid;
  grid-template-rows: 230px 1fr;
  overflow: hidden;
}
.log-panel-wrap {
  overflow: hidden;
  border-left: 1px solid #2a2a2a;
}
.chart-area {
  border-bottom: 1px solid #2a2a2a;
  overflow: hidden;
  min-height: 0;
}
.graph-area {
  overflow: hidden;
  min-height: 0;
}
</style>
