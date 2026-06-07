<template>
  <div class="graph-editor">
    <div class="graph-toolbar">
      <span class="graph-title">🌐 面包店经营模型</span>
      <div class="graph-legend">
        <span class="legend-item"><span class="legend-line solid"></span> SetRule</span>
        <span class="legend-item"><span class="legend-line dashed"></span> 纠缠</span>
        <span class="legend-item"><span class="legend-line conflict"></span> 冲突点</span>
        <span class="legend-item"><span class="legend-dot live"></span> 传播</span>
      </div>
      <button class="btn btn-sm btn-month" @click="advanceMonth" :disabled="yearDone">
        {{ yearDone ? '✅ 年终' : '📅 下个月' }}
      </button>
    </div>

    <div class="sim-bar">
      <span class="sim-month">📊 第 <strong>{{ currentMonth }}</strong> / 12 月</span>
      <span class="sim-profit" :class="monthProfitClass">📈 本月: {{ formatMoney(monthlyProfit) }}</span>
      <span class="sim-cumulative" :class="cumProfitClass">💰 累计: {{ formatMoney(cumulativeProfit) }}</span>
      <span class="sim-actions" v-if="yearDone">
        <button class="btn btn-sm btn-reset" @click="newYear">🔄 新一年</button>
      </span>
    </div>

    <div class="graph-canvas">
      <!-- 大节点组标签 -->
      <div class="group-labels">
        <div class="group-label sc">🏭 供应链</div>
        <div class="group-label prod">🍞 生产</div>
        <div class="group-label market">🏪 市场</div>
        <div class="group-label fin">💰 财务</div>
      </div>
      <VueFlow
        :nodes="nodes"
        :edges="edges"
        :fit-view-on-init="true"
        @node-click="onNodeClick"
        class="meshflow-graph"
      >
        <Background :gap="20" />
        <template #node-custom="nodeProps">
          <div
            class="vue-flow__node-custom"
            :class="{
              selected: selectedNode === nodeProps.id,
              conflicted: nodeProps.id === 'B2' || nodeProps.id === 'B3',
              affected: isAffected(nodeProps.id),
              changed: wasChanged(nodeProps.id),
            }"
            @dblclick="startEdit(nodeProps.id)"
          >
            <div class="node-icon">{{ nodeIcons[nodeProps.id as keyof typeof nodeIcons] || '📦' }}</div>
            <div class="node-label">{{ nodeProps.data.label }}</div>
            <div class="node-values">
              <!-- 编辑模式 -->
              <div v-if="editingNode === nodeProps.id" class="node-edit-row">
                <input
                  ref="editInput"
                  v-model="editValue"
                  class="node-edit-input"
                  @keydown.enter="commitEdit(nodeProps.id)"
                  @keydown.escape="cancelEdit"
                  @blur="commitEdit(nodeProps.id)"
                  autofocus
                />
              </div>
              <!-- 展示模式 -->
              <div v-else class="node-value-row" @click="startEdit(nodeProps.id)">
                <span class="node-value-num" :class="{ 'value-changed': wasChanged(nodeProps.id) }">
                  {{ formatVal(nodeProps.data.value) }}
                </span>
                <span class="edit-hint">✎</span>
              </div>
              <div v-if="nodeProps.data.role" class="node-role-badge">{{ nodeProps.data.role }}</div>
            </div>
          </div>
        </template>
      </VueFlow>
    </div>

    <!-- 年终总结 -->
    <div v-if="yearDone" class="year-summary">
      <div class="year-summary-header">🏆 年度经营总结</div>
      <div class="year-summary-grid">
        <div class="summary-item">
          <span class="summary-label">全年收入</span>
          <span class="summary-value">{{ formatMoney(yearRevenue) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">全年成本</span>
          <span class="summary-value">{{ formatMoney(yearCost) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">全年利润</span>
          <span class="summary-value" :class="cumProfitClass">{{ formatMoney(cumulativeProfit) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">利润率</span>
          <span class="summary-value">{{ profitMargin }}%</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">月均利润</span>
          <span class="summary-value">{{ formatMoney(Math.round(cumulativeProfit / 12)) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">盈利月数</span>
          <span class="summary-value">{{ profitableMonths }}/12</span>
        </div>
      </div>
    </div>

    <!-- 传播状态 -->
    <div class="propagation-bar" v-if="propagating">
      <span class="prop-spinner">⟳</span>
      <span>{{ propMessage }}</span>
    </div>

    <!-- 节点详情 -->
    <div v-if="selectedNode && !propagating" class="node-detail-panel">
      <div class="detail-header">
        <strong>{{ getNodeLabel(selectedNode) }}</strong>
        <span class="node-value-big">{{ formatVal(getNodeValue(selectedNode)) }}</span>
        <button class="close-btn" @click="selectedNode = ''">✕</button>
      </div>
      <div class="detail-body">
        <div class="detail-section">
          <h4>📤 出边 · 影响这些节点</h4>
          <div v-for="e in outgoingEdges" :key="e.id" class="edge-info">
            <span class="edge-arrow">→</span>
            <strong>{{ getNodeLabel(e.target) }}</strong>
            <span class="edge-desc">{{ e.label }}</span>
          </div>
          <div v-if="outgoingEdges.length === 0" class="no-edges">无</div>
        </div>
        <div class="detail-section">
          <h4>📥 入边 · 受这些节点影响</h4>
          <div v-for="e in incomingEdges" :key="e.id" class="edge-info">
            <span class="edge-arrow">←</span>
            <strong>{{ getNodeLabel(e.source) }}</strong>
            <span class="edge-desc">{{ e.label }}</span>
          </div>
          <div v-if="incomingEdges.length === 0" class="no-edges">无</div>
        </div>
        <div v-if="selectedNode === 'B2'" class="detail-warning">
          ⚡ B2(需求) SetRule: 价格+等级+营销 减去 B17缺货惩罚
        </div>
        <div v-if="selectedNode === 'B3'" class="detail-warning">
          ⚡ B3(产能) 上期需求(权10)← VS 成本红利(权7)→
        </div>
      </div>
    </div>

    <!-- 提示 -->
    <div v-else-if="!propagating" class="node-hint">
      👆 点击节点详请 · 双击或点数值编辑 · 改 B1 看传播路径！
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

// === Props ===
const props = defineProps<{ engine: any }>()

function readValue(id: string): any {
  try { return props.engine.getCellValue(id) } catch { return '' }
}

const nodeIcons: Record<string, string> = {
  B1: '💰', B2: '📊', B3: '🏭', B4: '🔧', B5: '🏢',
  B6: '📈', B7: '📉', B8: '✅', B9: '👷',
  B10: '🥖', B11: '📦', B12: '🏗️', B13: '📢', B14: '📐', B15: '⭐',
  B16: '📜', B17: '⚠️',
}

function formatVal(v: any): string {
  if (v === undefined || v === null || v === '') return '—'
  const n = Number(v)
  if (Math.abs(n) >= 1000) return Math.round(n).toLocaleString()
  return isNaN(n) ? String(v) : n.toFixed(2)
}

// === 节点数据 ===
const nodes = ref([
  // 🏭 供应链
  { id: 'B10', type: 'custom', position: { x: 50, y: 80 }, data: { label: '原料成本', value: readValue('B10'), role: '可编辑' } },
  { id: 'B11', type: 'custom', position: { x: 50, y: 200 }, data: { label: '其他变动成本', value: readValue('B11'), role: '可编辑' } },
  { id: 'B14', type: 'custom', position: { x: 50, y: 320 }, data: { label: '店面面积', value: readValue('B14'), role: '可编辑(m²)' } },
  // 🍞 生产
  { id: 'B3', type: 'custom', position: { x: 400, y: 80 }, data: { label: '产能 ⚡', value: readValue('B3'), role: '冲突点' } },
  { id: 'B4', type: 'custom', position: { x: 400, y: 200 }, data: { label: '加工成本', value: readValue('B4'), role: '规模效应' } },
  { id: 'B9', type: 'custom', position: { x: 400, y: 320 }, data: { label: '人工成本', value: readValue('B9'), role: '可编辑' } },
  { id: 'B12', type: 'custom', position: { x: 400, y: 440 }, data: { label: '总生产成本', value: readValue('B12'), role: '=(B10+B11+B4)×B3' } },
  // 🏪 市场
  { id: 'B1', type: 'custom', position: { x: 750, y: 80 }, data: { label: '售价', value: readValue('B1'), role: '可编辑' } },
  { id: 'B2', type: 'custom', position: { x: 750, y: 200 }, data: { label: '需求 ⚡', value: readValue('B2'), role: '冲突点' } },
  { id: 'B13', type: 'custom', position: { x: 750, y: 320 }, data: { label: '营销投入', value: readValue('B13'), role: '可编辑' } },
  { id: 'B15', type: 'custom', position: { x: 750, y: 440 }, data: { label: '场地等级', value: readValue('B15'), role: '可编辑(1-10)' } },
  { id: 'B16', type: 'custom', position: { x: 930, y: 80 }, data: { label: '上期需求📜', value: readValue('B16'), role: '缓存' } },
  { id: 'B17', type: 'custom', position: { x: 930, y: 200 }, data: { label: '上期缺货率⚠️', value: readValue('B17'), role: '缓存' } },
  // 💰 财务
  { id: 'B5', type: 'custom', position: { x: 280, y: 540 }, data: { label: '房租🏗️', value: readValue('B5'), role: '=面积×等级×20' } },
  { id: 'B6', type: 'custom', position: { x: 460, y: 540 }, data: { label: '月收入', value: readValue('B6'), role: '=B1×MIN(B2,B3)' } },
  { id: 'B7', type: 'custom', position: { x: 640, y: 540 }, data: { label: '总成本', value: readValue('B7'), role: '=B12+B5+B9+B13' } },
  { id: 'B8', type: 'custom', position: { x: 820, y: 540 }, data: { label: '月利润', value: readValue('B8'), role: '=B6-B7' } },
])

// === 边 ===
const srColor = '#3b82f6'
const entColor = '#f59e0b'
const cflColor = '#ef4444'

const edges = ref([
  // — SetRule 实线 —
  { id: 'sr-b3-b4', source: 'B3', target: 'B4', label: '规模效应',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  // 需求基线: B1价格+B15等级+B13营销
  { id: 'sr-b1-b2', source: 'B1', target: 'B2', label: '价格',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  // 房租: B14面积+B15等级 → B5
  { id: 'sr-b14-b5', source: 'B14', target: 'B5', label: '面积·非线性折扣房租',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b15-b5', source: 'B15', target: 'B5', label: '等级·房租',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  // 现场资源限制产能 (人工效率5.0, 面积×25)
  { id: 'sr-b14-b3', source: 'B14', target: 'B3', label: '空间限产能',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b9-b3', source: 'B9', target: 'B3', label: '人工限产能',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
  // 地段流量影响需求
  { id: 'sr-b15-b2', source: 'B15', target: 'B2', label: '地段流量',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b13-b2', source: 'B13', target: 'B2', label: '营销',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b10-b12', source: 'B10', target: 'B12', label: '原料', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b11-b12', source: 'B11', target: 'B12', label: '其他', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b4-b12', source: 'B4', target: 'B12', label: '加工', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b3-b12', source: 'B3', target: 'B12', label: '产能', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b1-b6', source: 'B1', target: 'B6', label: '售价', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b2-b6', source: 'B2', target: 'B6', label: '销量', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b12-b7', source: 'B12', target: 'B7', label: '生产成本', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b5-b7', source: 'B5', target: 'B7', label: '房租', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b9-b7', source: 'B9', target: 'B7', label: '人工', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b13-b7', source: 'B13', target: 'B7', label: '营销', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b6-b8', source: 'B6', target: 'B8', label: '收入', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b7-b8', source: 'B7', target: 'B8', label: '成本', style: { stroke: srColor, strokeWidth: 2 } },

  // — 滞后纠缠: 上期需求→产能计划 + 成本红利 + 缺货惩罚 —
  { id: 'ent-b16-b3', source: 'B16', target: 'B3', label: '📜上期→产 权10',
    style: { stroke: entColor, strokeWidth: 2, strokeDasharray: '6 3' }, labelStyle: { fill: entColor, fontSize: 9 }, animated: true },
  { id: 'ent-b4-b3', source: 'B4', target: 'B3', label: '本低→扩产 权7',
    style: { stroke: entColor, strokeWidth: 2, strokeDasharray: '6 3' }, labelStyle: { fill: entColor, fontSize: 9 }, animated: true },
  { id: 'sr-b17-b2', source: 'B17', target: 'B2', label: '缺货惩罚',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
])

// === 选中节点 ===
const selectedNode = ref('')

function getNodeLabel(id: string): string {
  return nodes.value.find(n => n.id === id)?.data.label || id
}
function getNodeValue(id: string): any {
  return nodes.value.find(n => n.id === id)?.data.value
}

const outgoingEdges = computed(() =>
  (selectedNode.value
    ? edges.value.filter(e => e.source === selectedNode.value).map(e => ({
        id: e.id,
        target: e.target,
        label: e.label || '',
        className: 'setrule',
      }))
    : [])
)
const incomingEdges = computed(() =>
  (selectedNode.value
    ? edges.value.filter(e => e.target === selectedNode.value).map(e => ({
        id: e.id,
        source: e.source,
        label: e.label || '',
        className: 'setrule',
      }))
    : [])
)

// === 编辑功能 ===
const editingNode = ref('')
const editValue = ref('')
const editInput = ref<HTMLInputElement | null>(null)

function startEdit(id: string) {
  // B1,B9,B10,B11,B13,B14,B15 可编辑 (B5/B16/B17由引擎或"下月"按钮计算)
  if (id !== 'B1' && id !== 'B9' && id !== 'B10' && id !== 'B11' && id !== 'B13' && id !== 'B14' && id !== 'B15') return
  editingNode.value = id
  const v = getNodeValue(id)
  editValue.value = v !== undefined && v !== null && v !== '' ? String(v) : ''
  nextTick(() => {
    const el = document.querySelector('.node-edit-input') as HTMLInputElement
    if (el) { el.focus(); el.select() }
  })
}

function cancelEdit() {
  editingNode.value = ''
}

function commitEdit(id: string) {
  if (editingNode.value !== id) return
  editingNode.value = ''
  const raw = editValue.value.trim()
  if (raw === '' || isNaN(Number(raw))) return

  props.engine.setCellValue(id, raw)

  if (id === 'B1') {
    triggerPropagation()
    setTimeout(() => refreshAllValues(), 300)
  } else {
    // B9/B10/B11/B13/B14/B15 → 也触发全系统传播
    triggerPropagation()
    setTimeout(() => refreshAllValues(), 300)
  }
}

// === 传播高亮系统 ===
const propagationGen = ref(0)
const propagating = ref(false)
const propMessage = ref('')

const affectedNodes = ref<Set<string>>(new Set())
const changedNodes = ref<Set<string>>(new Set())

// === 商业模拟沙盘 ===
const currentMonth = ref(1)
const cumulativeProfit = ref(0)
const yearRevenue = ref(0)
const yearCost = ref(0)
const profitableMonths = ref(0)
const yearDone = ref(false)
const monthHistory = ref<{ month: number; profit: number; revenue: number; cost: number; demand: number; sold: number }[]>([])

const monthlyProfit = computed(() => {
  const profit = Number(readValue('B8'))
  return isNaN(profit) ? 0 : profit
})

const monthProfitClass = computed(() => monthlyProfit.value >= 0 ? 'sim-positive' : 'sim-negative')
const cumProfitClass = computed(() => cumulativeProfit.value >= 0 ? 'sim-positive' : 'sim-negative')
const profitMargin = computed(() => {
  if (yearRevenue.value <= 0) return '—'
  return (cumulativeProfit.value / yearRevenue.value * 100).toFixed(1)
})

function formatMoney(v: number): string {
  const sign = v >= 0 ? '+' : ''
  return `${sign}¥${Math.round(v).toLocaleString()}`
}

// === 月度经营推进 ===
function advanceMonth() {
  const demand = Number(readValue('B2'))
  const cap = Number(readValue('B3'))
  const revenue = Number(readValue('B6')) || 0
  const cost = Number(readValue('B7')) || 0
  const profit = Number(readValue('B8')) || 0

  // 记录本月
  monthHistory.value.push({
    month: currentMonth.value,
    profit,
    revenue,
    cost,
    demand,
    sold: Math.min(demand, cap),
  })

  cumulativeProfit.value += profit
  yearRevenue.value += revenue
  yearCost.value += cost
  if (profit > 0) profitableMonths.value++

  // 计算缺货率
  const shortage = (cap >= demand || demand <= 0) ? 0 : Math.round((demand - cap) / demand * 1000) / 1000
  // 快照上期需求 → B16
  props.engine.setCellValue('B16', String(demand))
  // 写缺货率 → B17 (触发需求重算)
  props.engine.setCellValue('B17', String(shortage))
  triggerPropagation()
  setTimeout(() => refreshAllValues(), 300)

  // 推进月份
  if (currentMonth.value >= 12) {
    yearDone.value = true
  } else {
    currentMonth.value++
  }
}

function newYear() {
  currentMonth.value = 1
  cumulativeProfit.value = 0
  yearRevenue.value = 0
  yearCost.value = 0
  profitableMonths.value = 0
  yearDone.value = false
  monthHistory.value = []
  // 清空缓存
  props.engine.setCellValue('B16', '0')
  props.engine.setCellValue('B17', '0')
  refreshAllValues()
}

// 传播顺序：资源→房租→需求(含缺货惩罚)→产能计划→成本→财务
const PROPAGATION_STEPS: { nodes: string[]; edges: string[]; msg: string }[] = [
  { nodes: ['B1', 'B14', 'B15', 'B9', 'B13'], edges: [], msg: '⚡ 改售价/面积/等级/人工/营销' },
  { nodes: ['B5'], edges: ['sr-b14-b5', 'sr-b15-b5'], msg: '① SetRules: 房租=面积×等级×(20−面积×0.05) 非线性折扣' },
  { nodes: ['B16', 'B17'], edges: [], msg: '② 下月: 快照需求→B16, 缺货率→B17' },
  { nodes: ['B2'], edges: ['sr-b1-b2', 'sr-b15-b2', 'sr-b13-b2', 'sr-b17-b2'], msg: '③ SetRules: 需求=价格+等级+营销−缺货惩罚' },
  { nodes: ['B3'], edges: ['ent-b16-b3', 'sr-b14-b3', 'sr-b9-b3'], msg: '④ 滞后纠缠: 上期需求+资源→产能计划' },
  { nodes: ['B4'], edges: ['sr-b3-b4'], msg: '⑤ SetRule: 规模效应 产高→加工成本低(下限0.1,斜率×2)' },
  { nodes: ['B3'], edges: ['ent-b4-b3'], msg: '⑥ 纠缠 B4→B3(权7): 低成本→效率提升' },
  { nodes: ['B12'], edges: ['sr-b10-b12', 'sr-b11-b12', 'sr-b4-b12', 'sr-b3-b12'], msg: '⑦ 供应链→生产成本' },
  { nodes: ['B6'], edges: ['sr-b1-b6', 'sr-b2-b6'], msg: '⑧ 收入=售价×实际销售(产能限制)' },
  { nodes: ['B7'], edges: ['sr-b12-b7', 'sr-b5-b7', 'sr-b9-b7', 'sr-b13-b7'], msg: '⑨ 总成本=生产+房租+人工+营销' },
  { nodes: ['B8'], edges: ['sr-b6-b8', 'sr-b7-b8'], msg: '⑩ 利润=收入-总成本' },
]

function triggerPropagation() {
  propagationGen.value++
  propagating.value = true
  const gen = propagationGen.value

  // 清空旧状态
  affectedNodes.value = new Set()
  changedNodes.value = new Set()
  clearEdgeHighlights()
  changedNodes.value.add('B1')

  // 逐步高亮传播路径
  let delay = 0
  for (const step of PROPAGATION_STEPS) {
    const stepDelay = delay
    setTimeout(() => {
      if (propagationGen.value !== gen) return // 旧的传播被新的取代
      propMessage.value = step.msg

      // 高亮节点
      for (const nid of step.nodes) {
        affectedNodes.value = new Set([...affectedNodes.value, nid])
      }
      // 高亮边
      for (const eid of step.edges) {
        const edge = edges.value.find(e => e.id === eid)
        if (edge) {
          edge.style = { ...edge.style, stroke: '#22c55e', strokeWidth: 4 }
        }
      }
    }, stepDelay)
    delay += 350 // 每步间隔 350ms
  }

  // 最后一步：恢复
  setTimeout(() => {
    if (propagationGen.value !== gen) return
    // 标记最后收敛的节点为"变化"
    const finalIds = ['B1','B2','B3','B4','B5','B6','B7','B8','B16','B17']
    changedNodes.value = new Set(finalIds)
    // 1.5秒后清除高亮
    setTimeout(() => {
      if (propagationGen.value !== gen) return
      affectedNodes.value = new Set()
      changedNodes.value = new Set()
      clearEdgeHighlights()
      propagating.value = false
      // 刷新所有值
      refreshAllValues()
    }, 1500)
  }, delay + 500)
}

function clearEdgeHighlights() {
  for (const edge of edges.value) {
    const isEnt = edge.id.startsWith('ent')
    edge.style = {
      stroke: isEnt ? entColor : srColor,
      strokeWidth: 2,
      ...(isEnt
        ? { strokeDasharray: '6 3' }
        : edge.id.startsWith('sr-b14-') || edge.id.startsWith('sr-b9-') || edge.id.startsWith('sr-b13-') || edge.id.startsWith('sr-b17-')
          ? { strokeDasharray: '4 2' }
          : {}
      ),
    }
  }
}

function isConflictedNode(id: string): boolean {
  return id === 'B3'  // 只有B3有多纠缠竞争
}
function isAffected(id: string): boolean {
  return affectedNodes.value.has(id)
}
function wasChanged(id: string): boolean {
  return changedNodes.value.has(id)
}

// 刷新所有节点的值
function refreshAllValues() {
  const ids = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15', 'B16', 'B17']
  for (const id of ids) {
    const node = nodes.value.find(n => n.id === id)
    if (node) node.data.value = readValue(id)
  }
}

// === 节点点击：选中/取消 ===
function onNodeClick({ node }: any) {
  if (selectedNode.value === node.id) {
    selectedNode.value = ''
  } else {
    selectedNode.value = node.id
  }
}

// === 定时刷新 ===
let timer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  refreshAllValues()
  timer = setInterval(refreshAllValues, 1000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.graph-editor {
  display: flex; flex-direction: column; height: 100%;
  font-size: 12px;
}

.graph-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 10px; background: #f5f5f7;
  border-bottom: 1px solid #d2d2d7; flex-shrink: 0; gap: 6px;
}
.graph-title { font-weight: 600; font-size: 13px; color: #1d1d1f; white-space: nowrap; }
.graph-legend { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #6e6e73; }
.legend-line { width: 18px; height: 2px; border-radius: 1px; }
.legend-line.solid { background: #3b82f6; }
.legend-line.dashed { background: transparent; border-top: 2px dashed #f59e0b; }
.legend-line.conflict { background: #ef4444; height: 3px; }
.legend-line.dashed { background: transparent; border-top: 2px dashed #f59e0b; }
.legend-line.conflict { background: #ef4444; height: 3px; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; }
.legend-dot.live { background: #22c55e; animation: pulse-dot 1s infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:.4} }

.graph-canvas { flex: 1; min-height: 300px; position: relative; }

/* 模拟沙盘状态栏 */
.sim-bar {
  display: flex; align-items: center; gap: 14px;
  padding: 4px 12px; background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px; flex-shrink: 0;
}
.sim-month { color: #475569; font-variant-numeric: tabular-nums; }
.sim-month strong { color: #1e293b; font-size: 14px; }
.sim-profit, .sim-cumulative {
  font-weight: 600; font-variant-numeric: tabular-nums;
  font-family: 'SF Mono','Menlo',monospace; font-size: 12px;
}
.sim-positive { color: #059669; }
.sim-negative { color: #dc2626; }
.sim-actions { margin-left: auto; }
.btn-reset {
  background: #0891b2 !important; color: white !important; border-color: #0891b2 !important;
  font-weight: 600 !important;
}
.btn-reset:hover { background: #0e7490 !important; }

.btn-month {
  background: #7c3aed !important; color: white !important; border-color: #7c3aed !important;
  font-weight: 600 !important;
}
.btn-month:hover { background: #6d28d9 !important; }
.btn-month:disabled { opacity: 0.5; cursor: default; }

/* 年终总结 */
.year-summary {
  border-top: 2px solid #10b981; background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
  padding: 10px 16px; flex-shrink: 0;
}
.year-summary-header {
  font-size: 13px; font-weight: 700; color: #065f46; margin-bottom: 8px;
}
.year-summary-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
}
.summary-item {
  display: flex; flex-direction: column; gap: 2px;
  padding: 6px 10px; background: rgba(255,255,255,.7);
  border-radius: 6px; border: 1px solid #d1fae5;
}
.summary-label { font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.3px; }
.summary-value {
  font-size: 14px; font-weight: 700; font-family: 'SF Mono','Menlo',monospace;
  color: #1e293b; font-variant-numeric: tabular-nums;
}

/* 大节点组标签 */
.group-labels { position: absolute; top: 0; left: 0; right: 0; pointer-events: none; z-index: 5; }
.group-label {
  position: absolute; font-size: 11px; font-weight: 700; padding: 2px 8px;
  border-radius: 4px; letter-spacing: 0.5px; opacity: 0.7;
}
.group-label.sc { left: 30px; top: 10px; color: #8b5cf6; background: #f5f3ff; }
.group-label.prod { left: 350px; top: 10px; color: #0891b2; background: #ecfeff; }
.group-label.market { left: 700px; top: 10px; color: #d97706; background: #fffbeb; }
.group-label.fin { left: 530px; top: 10px; color: #059669; background: #ecfdf5; }

/* === 节点样式 === */
:deep(.vue-flow__node-custom) {
  background: white; border: 2px solid #d2d2d7; border-radius: 8px;
  padding: 8px 12px; min-width: 110px; cursor: pointer;
  transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
:deep(.vue-flow__node-custom:hover) {
  border-color: #0071e3; box-shadow: 0 2px 8px rgba(0,113,227,.15);
}
:deep(.vue-flow__node-custom.selected) {
  border-color: #0071e3; background: #f0f7ff; box-shadow: 0 2px 12px rgba(0,113,227,.2);
}
:deep(.vue-flow__node-custom.conflicted) {
  border-color: #ef4444; background: #fef2f2;
}
:deep(.vue-flow__node-custom.affected) {
  border-color: #22c55e; background: #f0fdf4;
  box-shadow: 0 0 16px rgba(34,197,94,.35);
  animation: pulse-border 0.6s ease-in-out 3;
}
@keyframes pulse-border {
  0%,100%{ box-shadow: 0 0 8px rgba(34,197,94,.25); }
  50%{ box-shadow: 0 0 20px rgba(34,197,94,.5); }
}
:deep(.vue-flow__node-custom.changed) .node-value-num {
  color: #22c55e; font-weight: 800;
}
:deep(.vue-flow__node-custom.changed) .node-value-num.value-changed {
  animation: value-flash 0.3s ease-in-out 4;
}
@keyframes value-flash {
  0%,100%{ color: #22c55e; }
  50%{ color: #16a34a; transform: scale(1.15); }
}

.node-icon { font-size: 18px; text-align: center; margin-bottom: 2px; }
.node-label { font-weight: 600; font-size: 11px; color: #1d1d1f; text-align: center; }
.node-values { margin-top: 4px; text-align: center; position: relative; }

.node-value-row {
  display: flex; align-items: center; justify-content: center;
  gap: 3px; cursor: pointer; padding: 2px 6px; border-radius: 4px;
  transition: background 0.15s;
}
.node-value-row:hover { background: #e8e8ed; }
.node-value-num {
  font-size: 13px; font-weight: 700; color: #0071e3;
  font-family: 'SF Mono','Menlo',monospace; transition: all 0.2s;
}
.edit-hint { font-size: 10px; color: #aeaeb2; opacity: 0; transition: opacity 0.15s; }
.node-value-row:hover .edit-hint { opacity: 1; }

.node-edit-row { padding: 1px 0; }
.node-edit-input {
  width: 70px; text-align: center;
  font-size: 13px; font-family: 'SF Mono','Menlo',monospace;
  font-weight: 700; color: #0071e3; background: white;
  border: 2px solid #0071e3; border-radius: 4px;
  padding: 2px 4px; outline: none;
}

.node-role-badge {
  display: inline-block; margin-top: 2px;
  font-size: 9px; padding: 1px 5px; border-radius: 3px;
  background: #e8e8ed; color: #6e6e73;
}

/* === 传播状态 === */
.propagation-bar {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 12px; background: #f0fdf4;
  border-top: 1px solid #bbf7d0; color: #166534;
  font-size: 11px; font-weight: 500; flex-shrink: 0;
}
.prop-spinner { font-size: 16px; animation: spin 1s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

/* === 详情面板 === */
.node-detail-panel {
  border-top: 1px solid #d2d2d7; background: #fafafa;
  padding: 8px 12px; max-height: 180px; overflow-y: auto; flex-shrink: 0;
}
.detail-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
}
.detail-header strong { font-size: 13px; }
.node-value-big {
  font-size: 15px; font-weight: 700; color: #0071e3;
  font-family: 'SF Mono','Menlo',monospace;
}
.close-btn { margin-left: auto; background: none; border: none; cursor: pointer; color: #86868b; font-size: 14px; }
.detail-body { display: flex; gap: 20px; flex-wrap: wrap; }
.detail-section { flex: 1; min-width: 140px; }
.detail-section h4 { font-size: 10px; text-transform: uppercase; color: #86868b; margin-bottom: 4px; }
.edge-info {
  display: flex; align-items: center; gap: 4px; padding: 2px 0; font-size: 11px;
}
.edge-info.setrule { color: #3b82f6; }
.edge-info.entangle { color: #d97706; }
.edge-arrow { font-size: 13px; }
.edge-desc { font-size: 10px; opacity: 0.7; }
.weight-badge {
  font-size: 9px; padding: 0 4px; border-radius: 3px;
  background: #e8e8ed; color: #6e6e73;
}
.no-edges { font-size: 10px; color: #aeaeb2; font-style: italic; }
.detail-warning {
  margin-top: 6px; padding: 4px 8px; background: #fef2f2;
  border: 1px solid #fecaca; border-radius: 4px; font-size: 11px; color: #dc2626; width: 100%;
}
.node-hint {
  border-top: 1px solid #d2d2d7; padding: 10px;
  text-align: center; font-size: 12px; color: #86868b; flex-shrink: 0;
}
</style>
