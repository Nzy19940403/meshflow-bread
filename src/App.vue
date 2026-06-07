<template>
  <div class="app">
    <header class="toolbar">
      <div class="toolbar-left">
        <h1>⚡ MeshFlow 引擎演示</h1>
        <div class="view-switcher">
          <button
            class="btn btn-sm"
            :class="{ active: currentView === 'graph' }"
            @click="switchView('graph')"
          >🌐 关系图</button>
          <button
            class="btn btn-sm"
            :class="{ active: currentView === 'sheet' }"
            @click="switchView('sheet')"
          >📊 表格</button>
        </div>
        <button class="btn btn-sm" @click="loadBakeryDemo">🥖 面包店</button>
        <button v-if="currentView === 'sheet'" class="btn btn-sm" @click="exportCSV">📥 CSV</button>
      </div>
    </header>

    <!-- 关系图视图 -->
    <div v-if="currentView === 'graph'" class="graph-view">
      <GraphEditor :engine="engine" />
    </div>

    <!-- 表格视图 (纯 HTML table, 无重量级组件) -->
    <template v-if="currentView === 'sheet'">
      <div class="formula-bar">
        <span class="cell-ref">{{ selectedCell || '—' }}</span>
        <input
          v-model="formulaInput"
          class="formula-input"
          placeholder="输入公式 如 =A1+B1 或 =SUM(A1:A5)"
          @keydown.enter.prevent="applyFormula"
          @keydown.escape="formulaInput = ''"
        />
        <span v-if="showFormulaPreview" class="formula-preview">{{ showFormulaPreview }}</span>
      </div>

      <div class="grid-wrap">
        <div class="grid-scroll">
          <table class="mesh-table">
            <thead>
              <tr>
                <th class="rn"></th>
                <th v-for="(col, ci) in visibleCols" :key="'h'+ci" class="col-head">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in tableRows" :key="'r'+ri">
                <td class="rn">{{ ri + 1 }}</td>
                <td
                  v-for="(val, ci) in row"
                  :key="'c'+ci"
                  class="cell"
                  :class="{ 'cell-selected': selectedCell === colName(ci) + (ri + 1) }"
                  @click="selectCell(colName(ci) + (ri + 1))"
                >{{ formatVal(val) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <footer class="status-bar">
      <span v-if="selectedCell && currentView === 'sheet'">
        <strong>{{ selectedCell }}</strong>：
        {{ cellInfo }}
      </span>
      <span v-else-if="currentView === 'graph'">🌐 点击节点查看规则链路</span>
      <span v-else>点击单元格 · 公式栏输入 = 开头</span>
      <span class="status-right">
        <span v-if="convergenceStatus" class="converge-badge">{{ convergenceStatus }}</span>
        {{ lastSaved }}
      </span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { createSheetEngine, type CellId } from './engine'
import { useLogger } from '@meshflow/logger'
import GraphEditor from './GraphEditor.vue'

const COLS = 10
const ROWS = 20
const COL_NAMES = 'ABCDEFGHIJ'

const engine = createSheetEngine()
const currentView = ref<'graph' | 'sheet'>('graph')
const selectedCell = ref<CellId>('')
const formulaInput = ref('')
const lastSaved = ref('')
const convergenceStatus = ref('')
const visibleCols = ref(COL_NAMES.split('').slice(0, COLS))
let entangleReady = false

function colName(i: number): string { return COL_NAMES[i] }

// ======== 纯表格数据 ========

const tableRows = computed(() => {
  const rows: any[][] = []
  for (let r = 1; r <= ROWS; r++) {
    const row: any[] = []
    for (let c = 0; c < COLS; c++) {
      row.push(engine.getCellValue(`${colName(c)}${r}` as CellId))
    }
    rows.push(row)
  }
  return rows
})

function formatVal(v: any): string {
  if (v === null || v === undefined || v === '') return ''
  const n = Number(v)
  if (!isNaN(n)) {
    if (Number.isInteger(n)) return n.toLocaleString()
    if (Math.abs(n) < 0.01) return n.toFixed(4)
    return n.toFixed(2)
  }
  return String(v)
}

const cellInfo = computed(() => {
  if (!selectedCell.value) return ''
  const f = engine.getCellFormula(selectedCell.value)
  if (f) return f
  const v = engine.getCellValue(selectedCell.value)
  return v !== '' && v !== null ? String(v) : '(空)'
})

const showFormulaPreview = computed(() => {
  if (!selectedCell.value) return ''
  return engine.getCellFormula(selectedCell.value) || ''
})

// ======== 单元格选择 ========

function selectCell(id: string) {
  selectedCell.value = id as CellId
  formulaInput.value = engine.getCellFormula(id as CellId) || ''
}

// ======== 公式栏 ========

function applyFormula() {
  if (!selectedCell.value) return
  engine.setCellFormula(selectedCell.value, formulaInput.value)
  if (!formulaInput.value.startsWith('=')) {
    engine.setCellValue(selectedCell.value, formulaInput.value)
  }

  // 纠缠推演: 改 B1 触发收敛
  if (entangleReady && selectedCell.value === 'B1') {
    const newVal = parseFloat(formulaInput.value)
    if (!isNaN(newVal)) {
      for (let r = 6; r <= 30; r++) {
        engine.setCellValue(`A${r}`, '')
        engine.setCellValue(`B${r}`, '')
        engine.setCellValue(`C${r}`, '')
        engine.setCellValue(`D${r}`, '')
        engine.setCellValue(`E${r}`, '')
        engine.setCellValue(`F${r}`, '')
        engine.setCellValue(`G${r}`, '')
      }
      const trace = computeConvergenceTrace(newVal)
      displayConvergenceTrace(trace, 6)
      convergenceStatus.value = '🌀 收敛中...'
      setTimeout(() => { convergenceStatus.value = '✅ 已收敛' }, 100)
    }
  }
}

// ======== CSV 导出 ========

function exportCSV() {
  const lines: string[] = []
  const headers: string[] = ['']
  for (let c = 0; c < COLS; c++) headers.push(COL_NAMES[c])
  lines.push(headers.join(','))

  for (let r = 1; r <= ROWS; r++) {
    const cells: string[] = [String(r)]
    for (let c = 0; c < COLS; c++) {
      const id = `${COL_NAMES[c]}${r}` as CellId
      let val = engine.getCellValue(id)
      if (val === null || val === undefined) val = ''
      const s = String(val).replace(/"/g, '""')
      cells.push(s.includes(',') || s.includes('"') ? `"${s}"` : s)
    }
    lines.push(cells.join(','))
  }

  const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `meshflow-sheet-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// ======== 面包店演示数据 ========

function loadBakeryDemo() {
  engine.clearAll()

  engine.setCellValue('A1', '📝 面包售价(元)')
  engine.setCellValue('B1', '15')
  engine.setCellValue('A2', '📝 日均销量')
  engine.setCellValue('B2', '200')
  engine.setCellValue('A3', '📝 月营业天数')
  engine.setCellValue('B3', '26')
  engine.setCellValue('A5', '📝 面粉成本(元/个)')
  engine.setCellValue('B5', '5')
  engine.setCellValue('A6', '📝 其他成本(元/个)')
  engine.setCellValue('B6', '2')
  engine.setCellValue('A8', '📝 月房租')
  engine.setCellValue('B8', '8000')
  engine.setCellValue('A9', '📝 月人工费')
  engine.setCellValue('B9', '12000')
  engine.setCellValue('A10', '📝 月水电杂费')
  engine.setCellValue('B10', '3000')

  engine.setCellValue('A12', '✅ 单位成本')
  engine.setCellFormula('B12', '=B5+B6')
  engine.setCellValue('A13', '✅ 月收入')
  engine.setCellFormula('B13', '=B1*B2*B3')
  engine.setCellValue('A14', '✅ 月固定成本')
  engine.setCellFormula('B14', '=B8+B9+B10')
  engine.setCellValue('A15', '✅ 月利润')
  engine.setCellFormula('B15', '=B13-(B12*B2*B3+B14)')

  formulaInput.value = ''
  selectedCell.value = ''
  lastSaved.value = '💡 修改B1~B3试试，结果自动更新！'
  convergenceStatus.value = ''
  visibleCols.value = COL_NAMES.split('').slice(0, COLS)
}

// ======== 收敛轨迹 ========

function computeConvergenceTrace(initialPrice: number) {
  let p = initialPrice, d = 0, cap = 0, co = 0
  const trace: { epoch: number; price: number; demand: number; capacity: number; cost: number; note: string }[] = []
  trace.push({ epoch: 0, price: p, demand: NaN, capacity: NaN, cost: NaN, note: `用户设定价格=${p}` })

  for (let epoch = 1; epoch <= 25; epoch++) {
    d = Math.max(0, 100 - p * 4)
    cap = Math.max(0, d * 0.7)
    co = Math.max(1, 2 + cap * 0.1)
    const pFromCost = Math.max(1, co * 2 + 1)

    trace.push({
      epoch, price: Math.round(p * 100) / 100,
      demand: Math.round(d * 100) / 100,
      capacity: Math.round(cap * 100) / 100,
      cost: Math.round(co * 100) / 100,
      note: epoch === 1
        ? `用户价${initialPrice}→需求${Math.round(d)}→产能${Math.round(cap)}→成本${Math.round(co)}→新价格${Math.round(pFromCost)}`
        : `B4→B1反馈: 成本${Math.round(co)}→价格${Math.round(pFromCost)}`,
    })

    if (Math.abs(pFromCost - p) < 0.05 && epoch > 3) {
      trace[trace.length - 1].note = `✅ 已收敛! 价格=${Math.round(p * 100) / 100}`
      break
    }
    p = pFromCost
  }
  return trace
}

function displayConvergenceTrace(trace: any[], offsetRow: number) {
  engine.setCellValue(`A${offsetRow}`, '📜 收敛轨迹')
  engine.setCellValue(`B${offsetRow}`, '轮次')
  engine.setCellValue(`C${offsetRow}`, '价格')
  engine.setCellValue(`D${offsetRow}`, '需求')
  engine.setCellValue(`E${offsetRow}`, '产能')
  engine.setCellValue(`F${offsetRow}`, '成本')
  engine.setCellValue(`G${offsetRow}`, '变化量')

  for (let i = 0; i < trace.length && i < 25; i++) {
    const r = offsetRow + 1 + i
    const t = trace[i]
    engine.setCellValue(`A${r}`, i === 0 ? '⚡触发' : `第${t.epoch}轮`)
    engine.setCellValue(`B${r}`, t.epoch)
    engine.setCellValue(`C${r}`, isNaN(t.price) ? '—' : t.price)
    engine.setCellValue(`D${r}`, isNaN(t.demand) ? '—' : t.demand)
    engine.setCellValue(`E${r}`, isNaN(t.capacity) ? '—' : t.capacity)
    engine.setCellValue(`F${r}`, isNaN(t.cost) ? '—' : t.cost)
    if (i === 0) {
      engine.setCellValue(`G${r}`, '—')
    } else {
      let delta = 0
      if (!isNaN(t.price) && !isNaN(trace[i - 1].price)) delta += Math.abs(t.price - trace[i - 1].price)
      if (!isNaN(t.demand) && !isNaN(trace[i - 1].demand)) delta += Math.abs(t.demand - trace[i - 1].demand)
      if (!isNaN(t.capacity) && !isNaN(trace[i - 1].capacity)) delta += Math.abs(t.capacity - trace[i - 1].capacity)
      if (!isNaN(t.cost) && !isNaN(trace[i - 1].cost)) delta += Math.abs(t.cost - trace[i - 1].cost)
      engine.setCellValue(`G${r}`, delta < 0.001 ? '✅ 收敛' : delta.toFixed(2))
    }
  }
}

// ======== 纠缠推演演示 ========

function loadEntangleDemo() {
  engine.clearAll()
  formulaInput.value = ''
  selectedCell.value = ''
  convergenceStatus.value = '🌀 收敛中...'
  visibleCols.value = ['', '值', '', '', '', '', '', '']

  if (!entangleReady) {
    engine.raw.config.useEntangle({
      cause: 'B1', impact: 'B2', via: ['value'],
      emit: (src: any, tgt: any, propose: any) => {
        propose.set('value', Math.max(0, 150 - (src.state.value || 0) * 8), 5)
      },
    })
    engine.raw.config.useEntangle({
      cause: 'B2', impact: 'B3', via: ['value'],
      emit: (src: any, tgt: any, propose: any) => {
        propose.set('value', Math.max(0, (src.state.value || 0) * 0.6), 5)
      },
    })
    engine.raw.config.useEntangle({
      cause: 'B3', impact: 'B1', via: ['value'],
      emit: (src: any, tgt: any, propose: any) => {
        propose.set('value', Math.max(1, 5 + (src.state.value || 0) * 0.15), 5)
      },
    })
    engine.raw.config.useEntangle({
      cause: 'B3', impact: 'B4', via: ['value'],
      emit: (src: any, tgt: any, propose: any) => {
        propose.set('value', Math.max(1, 3 + (src.state.value || 0) * 0.08), 5)
      },
    })
    engine.raw.config.useEntangle({
      cause: 'B4', impact: 'B1', via: ['value'],
      emit: (src: any, tgt: any, propose: any) => {
        propose.set('value', Math.max(1, (src.state.value || 0) * 2 + 1), 2)
      },
    })
    entangleReady = true
  }

  engine.setCellValue('A1', '💰 价格')
  engine.setCellValue('C1', '←产能(权5)+成本(权2)')
  engine.setCellValue('D1', '→需求')
  engine.setCellValue('E1', '↺')
  engine.setCellValue('A2', '📊 需求')
  engine.setCellValue('C2', '←价格')
  engine.setCellValue('D2', '→产能')
  engine.setCellValue('E2', '↺')
  engine.setCellValue('A3', '🏭 产能')
  engine.setCellValue('C3', '←需求')
  engine.setCellValue('D3', '→成本,→价格')
  engine.setCellValue('E3', '↺')
  engine.setCellValue('A4', '💸 成本')
  engine.setCellValue('C4', '←产能')
  engine.setCellValue('E4', '↺')

  const initialPrice = 10
  const trace = computeConvergenceTrace(initialPrice)
  displayConvergenceTrace(trace, 6)
  const lastRow = 6 + trace.length + 1
  engine.setCellValue(`A${lastRow}`, '⚡ 改 B1(价格) → 全系统震荡收敛')
  lastSaved.value = '🌀 改B1 → 震荡收敛！'

  engine.raw.data.SetValue('B1', 'value', initialPrice)
  setTimeout(() => {
    convergenceStatus.value = '✅ 已收敛'
  }, 100)
}

// ======== 视图切换 ========

function switchView(view: 'graph' | 'sheet') {
  currentView.value = view
  if (view === 'sheet') {
    loadBakeryDemo()
  }
}

// ======== 初始化 ========

onMounted(() => {
  try {
    const engine2 = engine as any
    if (!entangleReady) {
      // 房租: B14面积 × B15等级 × 20
      engine2.raw.config.SetRules(
        ['B14', 'B15'], 'B5', 'value', {
        logic: ({ slot }: any) => {
          const area = slot.triggerTargets[0]?.value
          const grade = slot.triggerTargets[1]?.value
          const a = (area !== null && area !== undefined) ? Number(area) : 80
          const g = (grade !== null && grade !== undefined) ? Number(grade) : 5
          return Math.max(0, Math.round(a * g * Math.max(2, 20 - a * 0.05)))
        },
        triggerKeys: ['value', 'value'],
      } as any)

      // —— 需求 B2 = 流量 × 留存率 (品牌知名度决定价格容忍度) ——
      engine2.raw.config.SetRules(
        ['B1', 'B15', 'B13', 'B17', 'B19'], 'B2', 'value', {
        logic: ({ slot }: any) => {
          const price = slot.triggerTargets[0]?.value
          const grade = slot.triggerTargets[1]?.value
          const marketing = slot.triggerTargets[2]?.value
          const shortage = slot.triggerTargets[3]?.value
          const brand = slot.triggerTargets[4]?.value
          const p = (price !== null && price !== undefined) ? Number(price) : 12
          const g = (grade !== null && grade !== undefined) ? Number(grade) : 5
          const m = (marketing !== null && marketing !== undefined) ? Number(marketing) : 0
          const s = (shortage !== null && shortage !== undefined) ? Number(shortage) : 0
          const b = (brand !== null && brand !== undefined) ? Number(brand) : 0

          // 流量 = 地段 + 营销
          const traffic = g * 200 + Math.sqrt(Math.max(0, m)) * 15

          // 品牌溢价: 每点知名度 +¥0.5 价格容忍度
          const brandPremium = b * 0.5
          const maxAcceptable = 10 + brandPremium

          // 留存率: 价格 vs 品牌溢价能力
          let retention: number
          if (p <= maxAcceptable) {
            retention = 0.5 + (maxAcceptable - p) / maxAcceptable * 0.4
          } else {
            retention = Math.max(0.05, 0.5 * (maxAcceptable / p))
          }

          const base = Math.round(traffic * retention)
          const penalty = Math.round(base * s * 0.5)
          return Math.max(0, base - penalty)
        },
        triggerKeys: ['value', 'value', 'value', 'value', 'value'],
      } as any)

      // —— B3 产能: 多因素综合 SetRule（替代原来的4条纠缠仲裁） ——
      // 输入: B14面积, B9人工, B16上期需求, B4加工成本, B17缺货率, B18报废率
      engine2.raw.config.SetRules(
        ['B14', 'B9', 'B16', 'B4', 'B17', 'B18'], 'B3', 'value', {
        logic: ({ slot }: any) => {
          const area = Number(slot.triggerTargets[0]?.value) || 80
          const labor = Number(slot.triggerTargets[1]?.value) || 15000
          const lastDemand = Number(slot.triggerTargets[2]?.value) || 1000
          const cost = Number(slot.triggerTargets[3]?.value) || 2
          const shortage = Number(slot.triggerTargets[4]?.value) || 0
          const waste = Number(slot.triggerTargets[5]?.value) || 0

          // ① 硬约束：面积×25  vs  人工÷5 → 短板效应
          const areaCap = Math.floor(area * 25)
          const laborCap = Math.floor(labor / 5.0)
          const hardwareCap = Math.min(areaCap, laborCap)
          if (hardwareCap <= 0) return 0

          // ② 需求计划：上期销量 × 动态信心系数
          const confidence = Math.max(0.6, Math.min(1.4, 1.0 + shortage * 0.5 - waste * 0.5))
          const demandPlan = Math.round(lastDemand * confidence)

          // ③ 效率红利：加工成本低 → 同资源下多产出
          const costBonus = Math.max(0, Math.round((2 - cost) * 200))

          // ④ 组合：最终产能 = min(硬件天花板, 需求计划 + 效率红利)
          //    硬件天花板设下限：至少 30% 产能用来做试制/培训/展示
          const baseProduction = Math.min(hardwareCap, demandPlan + costBonus)
          const minOperation = Math.round(hardwareCap * 0.3)
          return Math.max(minOperation, Math.max(0, baseProduction))
        },
        triggerKeys: ['value', 'value', 'value', 'value', 'value', 'value'],
      } as any)

      // B3→B4: 规模效应
      engine2.raw.config.SetRule('B3', 'B4', 'value', {
        logic: ({ slot }: any) => Math.max(0.1, 2 - (slot.triggerTargets[0].value || 0) * 0.0002),
        triggerKeys: ['value'],
      } as any)

      // —— B21 员工满意度: 薪酬 vs 工作负荷 ——
      engine2.raw.config.SetRules(
        ['B9', 'B3', 'B14'], 'B21', 'value', {
        logic: ({ slot }: any) => {
          const rawLabor = slot.triggerTargets[0]?.value
          const rawCap = slot.triggerTargets[1]?.value
          const rawArea = slot.triggerTargets[2]?.value
          const labor = (rawLabor !== null && rawLabor !== undefined) ? Number(rawLabor) : 15000
          const cap = (rawCap !== null && rawCap !== undefined) ? Number(rawCap) : 1000
          const area = (rawArea !== null && rawArea !== undefined) ? Number(rawArea) : 80

          const payPerOutput = labor / Math.max(cap, 1)
          const utilization = cap / Math.max(area * 25, 1)

          // 薪酬满意度: 每单位产能人工成本 >= 5 → 满意
          let paySat: number
          if (payPerOutput >= 5) {
            paySat = 0.7 + Math.min((payPerOutput - 5) / 10, 0.3)
          } else {
            paySat = payPerOutput / 5 * 0.7
          }

          // 过劳惩罚: 利用率超80%开始扣
          const overworkPenalty = Math.max(0, utilization - 0.8) * 1.5

          return Math.round(Math.min(1, Math.max(0, paySat - overworkPenalty)) * 1000) / 1000
        },
        triggerKeys: ['value', 'value', 'value'],
      } as any)

      // —— B20 口味/品质: 满意度高→好面包, 满意度低→糟蹋原料 ——
      engine2.raw.config.SetRules(
        ['B21', 'B3', 'B14'], 'B20', 'value', {
        logic: ({ slot }: any) => {
          const rawSat = slot.triggerTargets[0]?.value
          const rawCap = slot.triggerTargets[1]?.value
          const rawArea = slot.triggerTargets[2]?.value
          const sat = (rawSat !== null && rawSat !== undefined) ? Number(rawSat) : 0.8
          const cap = (rawCap !== null && rawCap !== undefined) ? Number(rawCap) : 1000
          const area = (rawArea !== null && rawArea !== undefined) ? Number(rawArea) : 80

          const utilization = cap / Math.max(area * 25, 1)

          let taste: number
          if (sat >= 0.6) {
            // 满意员工→好面包, 超负荷略降
            const overload = Math.max(0, utilization - 0.9) * 0.5
            taste = Math.min(1, Math.max(0.3, 1.0 - overload))
          } else {
            // 不满意→糟蹋原料
            taste = sat * 0.6
          }

          return Math.round(taste * 1000) / 1000
        },
        triggerKeys: ['value', 'value', 'value'],
      } as any)

      entangleReady = true
    }
    engine2.raw.data.SilentSet('B1', 'value', 12)
    engine2.raw.data.SilentSet('B1', 'formula', '')
    engine2.raw.data.SilentSet('B9', 'value', 15000)
    engine2.raw.data.SilentSet('B9', 'formula', '')
    engine2.raw.data.SilentSet('B10', 'value', 3)
    engine2.raw.data.SilentSet('B10', 'formula', '')
    engine2.raw.data.SilentSet('B11', 'value', 1)
    engine2.raw.data.SilentSet('B11', 'formula', '')
    engine2.raw.data.SilentSet('B13', 'value', 0)
    engine2.raw.data.SilentSet('B13', 'formula', '')
    engine2.raw.data.SilentSet('B14', 'value', 80)
    engine2.raw.data.SilentSet('B14', 'formula', '')
    engine2.raw.data.SilentSet('B15', 'value', 5)
    engine2.raw.data.SilentSet('B15', 'formula', '')
    engine2.raw.data.SilentSet('B17', 'value', 0)
    engine2.raw.data.SilentSet('B17', 'formula', '')
    engine2.raw.data.SilentSet('B18', 'value', 0)
    engine2.raw.data.SilentSet('B18', 'formula', '')
    engine2.raw.data.SilentSet('B19', 'value', 0)
    engine2.raw.data.SilentSet('B19', 'formula', '')
    engine2.raw.data.SilentSet('B20', 'value', 0.8)
    engine2.raw.data.SilentSet('B20', 'formula', '')
    engine2.raw.data.SilentSet('B21', 'value', 0.8)
    engine2.raw.data.SilentSet('B21', 'formula', '')

    engine.setCellValue('A1', '💰 售价(元)')
    engine.setCellValue('A2', '📊 月需求(个)')
    engine.setCellValue('A3', '🏭 月产能(个)')
    engine.setCellValue('A4', '🔧 加工成本(元/个)')
    engine.setCellValue('A5', '🏢 房租(元/月)🏗️')
    engine.setCellValue('A9', '👷 人工成本(元/月)')
    engine.setCellValue('A10', '🥖 原料成本(元/个)')
    engine.setCellValue('A11', '📦 其他变动成本(元/个)')
    engine.setCellValue('A13', '📢 营销投入(元/月)')
    engine.setCellValue('A14', '📐 店面面积(m²)')
    engine.setCellValue('A15', '⭐ 场地等级(1-10)')
    engine.setCellValue('A16', '📜 上期需求(自洽)')
    engine.setCellValue('A17', '⚠️ 上期缺货率')
    engine.setCellValue('A18', '📦 上期报废率')
    engine.setCellValue('A19', '🌟 知名度(品牌)')
    engine.setCellValue('A20', '😋 口味/品质')
    engine.setCellValue('A21', '😊 员工满意度')

    engine.setCellFormula('B6', '=B1*MIN(B2,B3)')
    engine.setCellFormula('B12', '=(B10+B11+B4)*B3')
    engine.setCellFormula('B7', '=B12+B5+B9+B13')
    engine.setCellFormula('B8', '=B6-B7')

    engine2.raw.config.notifyAll()

    // 自洽初始化: B16(上期需求) = B2(本期需求)
    // 避免 B16=3600(拍脑袋) 导致首月产能虚高
    const initialDemand = engine.getCellValue('B2')
    const b2Val = (initialDemand !== null && initialDemand !== undefined) ? Number(initialDemand) : 400
    engine2.raw.data.SilentSet('B16', 'value', Math.max(100, Math.round(b2Val)))
    engine2.raw.data.SilentSet('B16', 'formula', '')
    engine2.raw.config.notifyAll()  // 引擎重算 B3(使用自洽的 B16)

    ;(window as any).__engine = engine2

    const logger = useLogger({ focusPaths: ['B9', 'B3'] })
    engine2.raw.config.usePlugin(logger)
  } catch (e: any) {
    console.error('onMounted error:', e.message, e.stack)
  }
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: #f5f5f7;
  color: #1d1d1f;
  overflow: hidden;
  height: 100vh;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
.app { max-width: 1200px; margin: 0 auto; padding: 8px 12px; height: 100vh; display: flex; flex-direction: column; }
@media (max-width: 480px) { .app { padding: 4px 6px; } }

.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; flex-shrink: 0; }
.toolbar-left { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.toolbar h1 { font-size: 14px; font-weight: 600; color: #0071e3; letter-spacing: -0.2px; }
.badge { font-size: 11px; padding: 2px 7px; border-radius: 8px; background: #e8e8ed; color: #6e6e73; white-space: nowrap; }
.badge-engine { background: #e3f2fd; color: #0071e3; }
.grid-size { font-family: 'SF Mono', 'Menlo', monospace; }

.btn {
  font-size: 12px; padding: 4px 9px; border-radius: 5px;
  border: 1px solid #d2d2d7;
  background: #ffffff; color: #1d1d1f;
  cursor: pointer; transition: all 0.1s; white-space: nowrap;
}
.btn:hover { background: #f5f5f7; border-color: #a1a1a6; }
.btn-sm { font-size: 11px; padding: 2px 7px; }
.btn-danger:hover { background: #fef2f2; border-color: #f87171; color: #dc2626; }

.formula-bar {
  display: flex; align-items: center; gap: 6px; margin-bottom: 4px;
  background: #ffffff; border: 1px solid #d2d2d7; border-radius: 5px;
  padding: 4px 8px; flex-shrink: 0;
}
.cell-ref {
  font-family: 'SF Mono', 'Menlo', monospace; font-size: 12px;
  color: #86868b; min-width: 32px; font-weight: 600; user-select: none;
}
.formula-input {
  flex: 1; background: transparent; border: none;
  color: #1d1d1f; font-size: 12px;
  font-family: 'SF Mono', 'Menlo', monospace; outline: none;
}
.formula-input::placeholder { color: #aeaeb2; }
.formula-preview {
  font-size: 11px; color: #86868b;
  padding: 1px 5px; background: #f5f5f7; border-radius: 3px;
  max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* 纯 HTML 表格 (替代 RevoGrid) */
.grid-wrap { flex: 1; overflow: hidden; border: 1px solid #d2d2d7; border-radius: 5px; }
.grid-scroll {
  width: 100%; height: 100%; overflow: auto;
}
.mesh-table {
  border-collapse: collapse; font-size: 11px; font-family: 'SF Mono', 'Menlo', monospace;
  min-width: 100%; table-layout: fixed;
}
.mesh-table th, .mesh-table td {
  border: 1px solid #e5e5ea; padding: 2px 6px; text-align: right;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  min-width: 72px; height: 24px;
}
.mesh-table thead th {
  background: #f5f5f7; color: #1d1d1f; font-weight: 600;
  font-size: 10px; text-align: center; position: sticky; top: 0; z-index: 2;
}
.mesh-table .rn {
  min-width: 36px; width: 36px;
  background: #f5f5f7; color: #86868b; font-size: 9px;
  text-align: center; position: sticky; left: 0; z-index: 1;
  user-select: none;
}
.mesh-table thead .rn { z-index: 3; }
.mesh-table tbody tr:hover td:not(.rn):not(.cell-selected) {
  background: #f5f5f7;
}
.mesh-table .cell-selected {
  background: rgba(0,113,227,0.12) !important;
  outline: 2px solid #0071e3; outline-offset: -1px;
}
.mesh-table .col-head {
  user-select: none; cursor: default;
}

.graph-view {
  flex: 1;
  overflow: hidden;
  border: 1px solid #d2d2d7;
  border-radius: 5px;
  background: #fafafa;
}

.view-switcher {
  display: flex;
  gap: 2px;
  background: #e8e8ed;
  border-radius: 5px;
  padding: 2px;
}

.view-switcher .btn {
  border: none;
  background: transparent;
  transition: all 0.15s;
}

.view-switcher .btn.active {
  background: white;
  border-color: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.status-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 3px 6px; margin-top: 3px;
  font-size: 11px; color: #86868b;
  background: #f5f5f7; border-top: 1px solid #d2d2d7; flex-shrink: 0; min-height: 22px;
}
.status-right { display: flex; align-items: center; gap: 6px; }
.save-indicator { animation: fadeIn 0.2s; color: #34c759; }
.converge-badge { font-size: 11px; padding: 1px 6px; border-radius: 8px; background: #e8f5e9; color: #2e7d32; font-weight: 500; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
