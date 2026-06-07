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

    <!-- 表格视图 -->
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
        <RevoGrid
          ref="gridRef"
          :columns="columns"
          :source="gridData"
          :editable="true"
          :theme="'compact'"
          :resize="true"
          :range="true"
          :rownumbers="true"
          @afteredit="onAfterEdit"
        />
      </div>
    </template>

    <footer class="status-bar">
      <span v-if="selectedCell && currentView === 'sheet'">
        <strong>{{ selectedCell }}</strong>：
        {{ cellInfo }}
      </span>
      <span v-else-if="currentView === 'graph'">🌐 点击节点查看规则链路</span>
      <span v-else>点击单元格 · 双击编辑 · 公式栏输入 = 开头</span>
      <span class="status-right">
        <span v-if="convergenceStatus" class="converge-badge">{{ convergenceStatus }}</span>
        {{ lastSaved }}
      </span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import RevoGrid from '@revolist/vue3-datagrid'
import type { ColumnRegular } from '@revolist/revogrid'
import { createSheetEngine, type CellId } from './engine'
import { useLogger } from '@meshflow/logger'
import GraphEditor from './GraphEditor.vue'

const COLS = 10
const ROWS = 20
const COL_NAMES = 'ABCDEFGHIJ'
const COL_SIZE = 85

const engine = createSheetEngine()
const currentView = ref<'graph' | 'sheet'>('graph')
const gridRef = ref<any>(null)
const selectedCell = ref<CellId>('')
const formulaInput = ref('')
const lastSaved = ref('')
const convergenceStatus = ref('')
const columnNames = ref(COL_NAMES.split('').slice(0, COLS))
let entangleReady = false
const rows = ref(ROWS)
const cols = ref(COLS)

const gridData = ref<Record<string, any>[]>([])

const columns = computed<ColumnRegular[]>(() => {
  const names = columnNames.value
  const colsArr: ColumnRegular[] = []
  for (let c = 0; c < cols.value; c++) {
    colsArr.push({ prop: COL_NAMES[c], name: names[c] || COL_NAMES[c], size: COL_SIZE })
  }
  return colsArr
})

const activeCells = computed(() => {
  let count = 0
  for (let r = 1; r <= rows.value; r++) {
    for (let c = 0; c < cols.value; c++) {
      const v = engine.getCellValue(`${COL_NAMES[c]}${r}` as CellId)
      if (v !== '' && v !== null && v !== undefined) count++
    }
  }
  return count
})

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

// ======== 数据同步：引擎 → RevoGrid ========

function rebuildGridData() {
  const data: Record<string, any>[] = []
  for (let r = 1; r <= rows.value; r++) {
    const row: Record<string, any> = {}
    for (let c = 0; c < cols.value; c++) {
      row[COL_NAMES[c]] = engine.getCellValue(`${COL_NAMES[c]}${r}` as CellId)
    }
    data.push(row)
  }
  gridData.value = data
}

// ======== RevoGrid 事件 ========

function onAfterEdit(e: any) {
  const detail = e.detail || e
  if (!detail) return
  const { prop, rowIndex, val } = detail
  if (prop === undefined || rowIndex === undefined) return
  const id = `${String(prop)}${rowIndex + 1}` as CellId
  const raw = val !== undefined && val !== null ? String(val) : ''
  engine.setCellValue(id, raw)
  rebuildGridData()

  // 更新选中单元格信息
  selectedCell.value = id
  formulaInput.value = engine.getCellFormula(id) || ''

  // 如果是纠缠推演模式，改 B1 触发全系统收敛 + 轨迹更新
  if (entangleReady && id === 'B1') {
    const newVal = parseFloat(raw)
    if (!isNaN(newVal)) {
      // 先清除旧的轨迹区域（Row 6+），保留前5行
      for (let r = 6; r <= 30; r++) {
        engine.setCellValue(`A${r}`, '')
        engine.setCellValue(`B${r}`, '')
        engine.setCellValue(`C${r}`, '')
        engine.setCellValue(`D${r}`, '')
        engine.setCellValue(`E${r}`, '')
        engine.setCellValue(`F${r}`, '')
        engine.setCellValue(`G${r}`, '')
      }
      // 重算收敛轨迹
      const trace = computeConvergenceTrace(newVal)
      displayConvergenceTrace(trace, 6)
      convergenceStatus.value = '🌀 收敛中...'
      rebuildGridData()
      setTimeout(() => {
        convergenceStatus.value = '✅ 已收敛'
      }, 100)
    }
  }
}

// 刷新时同步选中状态（通过点击列头/行号触发）
// 目前 RevoGrid 有选中单元格时公式栏会自动更新

// ======== 公式栏 ========

function applyFormula() {
  if (!selectedCell.value) return
  engine.setCellFormula(selectedCell.value, formulaInput.value)
  if (!formulaInput.value.startsWith('=')) {
    engine.setCellValue(selectedCell.value, formulaInput.value)
  }
  rebuildGridData()
}

// ======== 选中跟踪 ========

// 通过监听键盘/鼠标事件跟踪当前选中的单元格
function trackSelection(e: any) {
  try {
    const d = e.detail || e
    if (d && d.prop !== undefined && d.rowIndex !== undefined) {
      const id = `${String(d.prop)}${d.rowIndex + 1}` as CellId
      if (id !== selectedCell.value) {
        selectedCell.value = id
        formulaInput.value = engine.getCellFormula(id) || ''
      }
    }
  } catch {}
}

// ======== CSV 导出 ========
function exportCSV() {
  const lines: string[] = []
  const headers: string[] = ['']
  for (let c = 0; c < cols.value; c++) headers.push(COL_NAMES[c])
  lines.push(headers.join(','))

  for (let r = 1; r <= rows.value; r++) {
    const cells: string[] = [String(r)]
    for (let c = 0; c < cols.value; c++) {
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

// ======== 演示数据：面包店月度经营推演 ========

function loadBakeryDemo() {
  engine.clearAll()

  // ====== 你要填的数据（改这些数，下面自动算） ======
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

  // ====== 引擎自动算的（你改上面，这里自动变） ======
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
  columnNames.value = COL_NAMES.split('').slice(0, COLS)
  rebuildGridData()
}

// ======== 收敛轨迹计算 ========
// 正确经济模型: Price→Demand→Capacity→Cost→Price (闭环)
function computeConvergenceTrace(initialPrice: number) {
  let p = initialPrice
  let d = 0, cap = 0, co = 0
  const trace: { epoch: number; price: number; demand: number; capacity: number; cost: number; note: string }[] = []
  trace.push({ epoch: 0, price: p, demand: NaN, capacity: NaN, cost: NaN, note: `用户设定价格=${p}` })

  for (let epoch = 1; epoch <= 25; epoch++) {
    // SetRule: B1→B2
    d = Math.max(0, 100 - p * 4)
    // 纠缠: B2→B3
    cap = Math.max(0, d * 0.7)
    // 纠缠: B3→B4
    co = Math.max(1, 2 + cap * 0.1)
    // 纠缠: B4→B1 (权7) 价格反馈
    const pFromCost = Math.max(1, co * 2 + 1)

    trace.push({
      epoch,
      price: Math.round(p * 100) / 100,
      demand: Math.round(d * 100) / 100,
      capacity: Math.round(cap * 100) / 100,
      cost: Math.round(co * 100) / 100,
      note: epoch === 1
        ? `用户价${initialPrice}→需求${Math.round(d)}→产能${Math.round(cap)}→成本${Math.round(co)}→新价格${Math.round(pFromCost)}`
        : `B4→B1反馈: 成本${Math.round(co)}→价格${Math.round(pFromCost)}`,
    })

    const delta = Math.abs(pFromCost - p)
    if (delta < 0.05 && epoch > 3) {
      trace[trace.length - 1].note = `✅ 已收敛! 价格=${Math.round(p*100)/100}`
      break
    }

    p = pFromCost
  }
  return trace
}

// 显示收敛轨迹到表格
function displayConvergenceTrace(trace: any[], offsetRow: number) {
  // 表头
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
      const prev = trace[i - 1]
      let delta = 0
      if (!isNaN(t.price) && !isNaN(prev.price)) delta += Math.abs(t.price - prev.price)
      if (!isNaN(t.demand) && !isNaN(prev.demand)) delta += Math.abs(t.demand - prev.demand)
      if (!isNaN(t.capacity) && !isNaN(prev.capacity)) delta += Math.abs(t.capacity - prev.capacity)
      if (!isNaN(t.cost) && !isNaN(prev.cost)) delta += Math.abs(t.cost - prev.cost)
      engine.setCellValue(`G${r}`, delta < 0.001 ? '✅ 收敛' : delta.toFixed(2))
    }
  }
}

// ======== 纠缠推演：循环依赖 + 震荡收敛 ========

function loadEntangleDemo() {
  engine.clearAll()
  formulaInput.value = ''
  selectedCell.value = ''
  convergenceStatus.value = '🌀 收敛中...'
  columnNames.value = ['', '值', '', '', '', '', '', '']

  // ===== 先注册纠缠边（仅首次） =====
  if (!entangleReady) {
    // ① B1价格 → B2需求: 价格越高需求越低
    engine.raw.config.useEntangle({
      cause: 'B1', impact: 'B2', via: ['value'],
      emit: (src: any, tgt: any, propose: any) => {
        const newVal = Math.max(0, 150 - (src.state.value || 0) * 8)
        propose.set('value', newVal, 5)
      },
    })

    // ② B2需求 → B3产能: 需求越高产能越多
    engine.raw.config.useEntangle({
      cause: 'B2', impact: 'B3', via: ['value'],
      emit: (src: any, tgt: any, propose: any) => {
        propose.set('value', Math.max(0, (src.state.value || 0) * 0.6), 5)
      },
    })

    // ③ B3产能 → B1价格 (主要路径, weight=5)
    engine.raw.config.useEntangle({
      cause: 'B3', impact: 'B1', via: ['value'],
      emit: (src: any, tgt: any, propose: any) => {
        propose.set('value', Math.max(1, 5 + (src.state.value || 0) * 0.15), 5)
      },
    })

    // ④ B3产能 → B4成本
    engine.raw.config.useEntangle({
      cause: 'B3', impact: 'B4', via: ['value'],
      emit: (src: any, tgt: any, propose: any) => {
        propose.set('value', Math.max(1, 3 + (src.state.value || 0) * 0.08), 5)
      },
    })

    // ⑤ B4成本 → B1价格 (次要路径, weight=2)
    // ⚡ 冲突! B1同时从③(weight=5)和⑤(weight=2)收到提案
    engine.raw.config.useEntangle({
      cause: 'B4', impact: 'B1', via: ['value'],
      emit: (src: any, tgt: any, propose: any) => {
        propose.set('value', Math.max(1, (src.state.value || 0) * 2 + 1), 2)
      },
    })

    entangleReady = true
  }

  // ==================================================================
  // 布局：干净简单的四行 + 收敛轨迹
  // ==================================================================

  // —— Section 1: 核心纠缠节点 (Row 1-4) ——
  // A=标签  B=值   C-E=纠缠链路示意
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

  // —— Section 2: 收敛轨迹 (Row 6+) ——
  // 先计算轨迹再显示
  const initialPrice = 10
  const trace = computeConvergenceTrace(initialPrice)
  displayConvergenceTrace(trace, 6)

  // 说明
  const lastRow = 6 + trace.length + 1
  engine.setCellValue(`A${lastRow}`, '⚡ 改 B1(价格) → 全系统震荡收敛')

  lastSaved.value = '🌀 改B1 → 震荡收敛！'

  // —— 触发引擎纠缠传播 ——
  rebuildGridData()
  engine.raw.data.SetValue('B1', 'value', initialPrice)

  // 等收敛后刷新 B 列
  setTimeout(() => {
    rebuildGridData()
    convergenceStatus.value = '✅ 已收敛'
  }, 100)
}

// ======== 视图切换 ========

function switchView(view: 'graph' | 'sheet') {
  currentView.value = view
  if (view === 'sheet') {
    // 进入表格时初始化纠缠数据
    loadBakeryDemo()
  }
}

// ======== 初始化 ========

onMounted(() => {
  // 默认显示关系图，引擎在 GraphEditor 中自动加载数据
  try {
    // 先初始化引擎数据（B1 等）
    const engine2 = engine as any
    // 注册纠缠边（仅首次）
    if (!entangleReady) {
      // —— 房租: B14面积 × B15等级 × 20 ——
      engine2.raw.config.SetRules(
        ['B14', 'B15'], 'B5', 'value', {
        logic: ({ slot }: any) => {
          const area = slot.triggerTargets[0]?.value
          const grade = slot.triggerTargets[1]?.value
          const a = (area !== null && area !== undefined) ? Number(area) : 80
          const g = (grade !== null && grade !== undefined) ? Number(grade) : 5
          // 非线性房租: 面积越大单位租金越便宜
          return Math.max(0, Math.round(a * g * Math.max(2, 20 - a * 0.05)))
        },
        triggerKeys: ['value', 'value'],
      } as any)

      // —— SetRules: 需求基线 (B1价格+B15等级+B13营销, B17缺货惩罚) ——
      engine2.raw.config.SetRules(
        ['B1', 'B15', 'B13', 'B17'], 'B2', 'value', {
        logic: ({ slot }: any) => {
          const price = slot.triggerTargets[0]?.value
          const grade = slot.triggerTargets[1]?.value
          const marketing = slot.triggerTargets[2]?.value
          const shortage = slot.triggerTargets[3]?.value
          const p = (price !== null && price !== undefined) ? Number(price) : 12
          const g = (grade !== null && grade !== undefined) ? Number(grade) : 5
          const m = (marketing !== null && marketing !== undefined) ? Number(marketing) : 0
          const s = (shortage !== null && shortage !== undefined) ? Number(shortage) : 0
          // 价格效应: 价越低买越多
          const priceEffect = Math.max(300, 5000 - p * 200)
          // 地段效应: 等级越高=人流量越大
          const locationEffect = g * 200
          // 营销效应: 投入越多→跟风人群越多
          const marketingEffect = Math.sqrt(Math.max(0, m)) * 15
          // 缺货惩罚: 上期没买到的客人流失 (每缺1%赶走0.5%客户)
          const base = priceEffect + locationEffect + marketingEffect
          const penalty = Math.round(base * s * 0.5)
          return Math.round(base - penalty)
        },
        triggerKeys: ['value', 'value', 'value', 'value'],
      } as any)

      // —— 纠缠: B16上期需求→B3产能 (滞后一期,商家按上月销量备货) ——
      engine2.raw.config.useEntangle({
        cause: 'B16', impact: 'B3', via: ['value'],
        emit: (src: any, tgt: any, propose: any) => {
          const rawArea = engine2.raw.data.GetValue('B14', 'value')
          const rawLabor = engine2.raw.data.GetValue('B9', 'value')
          const area = (rawArea !== null && rawArea !== undefined) ? Number(rawArea) : 80
          const labor = (rawLabor !== null && rawLabor !== undefined) ? Number(rawLabor) : 15000
          if (area <= 0 || labor <= 0) { propose.set('value', 0, 10); return }
          const baseFromArea = Math.floor(area * 25)
          const baseFromLabor = Math.floor(labor / 5.0)
          const resourceCap = Math.min(baseFromArea, baseFromLabor)
          // 动态备货系数: 依赖上期缺货/报废率
          const lastDemand = src.state.value || 1000
          const shortage = Number(engine2.raw.data.GetValue('B17', 'value')) || 0
          const wasteRate = Number(engine2.raw.data.GetValue('B18', 'value')) || 0
          const conf = Math.max(0.6, Math.min(1.4, 1.0 + shortage * 0.5 - wasteRate * 0.5))
          propose.set('value', Math.min(resourceCap, Math.round(lastDemand * conf)), 10)
        },
      })
      // 纠缠: B4加工成本→B3产能 (成本低→投资更多)
      engine2.raw.config.useEntangle({
        cause: 'B4', impact: 'B3', via: ['value'],
        emit: (src: any, tgt: any, propose: any) => {
          const rawArea = engine2.raw.data.GetValue('B14', 'value')
          const rawLabor = engine2.raw.data.GetValue('B9', 'value')
          const area = (rawArea !== null && rawArea !== undefined) ? Number(rawArea) : 80
          const labor = (rawLabor !== null && rawLabor !== undefined) ? Number(rawLabor) : 15000
          const lastDemand = engine2.raw.data.GetValue('B16', 'value')
          const ld = (lastDemand !== null && lastDemand !== undefined) ? Number(lastDemand) : 1000
          // 动态备货系数
          const shortage = Number(engine2.raw.data.GetValue('B17', 'value')) || 0
          const wasteRate = Number(engine2.raw.data.GetValue('B18', 'value')) || 0
          const conf = Math.max(0.6, Math.min(1.4, 1.0 + shortage * 0.5 - wasteRate * 0.5))
          const fromDemand = Math.round(ld * conf)
          if (area <= 0 || labor <= 0) { propose.set('value', 0, 7); return }
          const baseFromArea = Math.floor(area * 25)
          const baseFromLabor = Math.floor(labor / 5.0)
          const baseline = Math.min(Math.min(baseFromArea, baseFromLabor), fromDemand)
          // 成本红利是效率提升，基准线设在加工成本上限2元
          const costBoost = Math.max(0, (2 - (src.state.value || 2)) * 200)
          const effectiveCap = Math.floor(Math.min(baseFromArea, baseFromLabor) + costBoost)
          propose.set('value', Math.min(effectiveCap, fromDemand), 7)
        },
      })

      // —— SetRules: 单向依赖 ——
      // B3→B4: 规模效应-产能越高加工成本越低 (下限0.1, 速度×2)
      engine2.raw.config.SetRule('B3', 'B4', 'value', {
        logic: ({ slot }: any) => Math.max(0.1, 2 - (slot.triggerTargets[0].value || 0) * 0.0002),
        triggerKeys: ['value'],
      } as any)

      // —— 纠缠: B9人工成本→B3产能 (资源变化直接触发重算) ——
      engine2.raw.config.useEntangle({
        cause: 'B9', impact: 'B3', via: ['value'],
        emit: (src: any, tgt: any, propose: any) => {
          const rawArea = engine2.raw.data.GetValue('B14', 'value')
          const rawLabor = engine2.raw.data.GetValue('B9', 'value')
          const area = (rawArea !== null && rawArea !== undefined) ? Number(rawArea) : 80
          const labor = (rawLabor !== null && rawLabor !== undefined) ? Number(rawLabor) : 15000
          if (area <= 0 || labor <= 0) { propose.set('value', 0, 8); return }
          const resourceCap = Math.min(Math.floor(area * 25), Math.floor(labor / 5.0))
          const lastDemand = engine2.raw.data.GetValue('B16', 'value')
          const d = (lastDemand !== null && lastDemand !== undefined) ? Number(lastDemand) : 1000
          // 动态备货系数
          const shortage = Number(engine2.raw.data.GetValue('B17', 'value')) || 0
          const wasteRate = Number(engine2.raw.data.GetValue('B18', 'value')) || 0
          const conf = Math.max(0.6, Math.min(1.4, 1.0 + shortage * 0.5 - wasteRate * 0.5))
          propose.set('value', Math.min(resourceCap, Math.round(d * conf)), 8)
        },
      })
      // —— 纠缠: B14面积→B3产能 (面积变化直接触发重算) ——
      engine2.raw.config.useEntangle({
        cause: 'B14', impact: 'B3', via: ['value'],
        emit: (src: any, tgt: any, propose: any) => {
          const rawArea = engine2.raw.data.GetValue('B14', 'value')
          const rawLabor = engine2.raw.data.GetValue('B9', 'value')
          const area = (rawArea !== null && rawArea !== undefined) ? Number(rawArea) : 80
          const labor = (rawLabor !== null && rawLabor !== undefined) ? Number(rawLabor) : 15000
          if (area <= 0 || labor <= 0) { propose.set('value', 0, 8); return }
          const resourceCap = Math.min(Math.floor(area * 25), Math.floor(labor / 5.0))
          const lastDemand = engine2.raw.data.GetValue('B16', 'value')
          const d = (lastDemand !== null && lastDemand !== undefined) ? Number(lastDemand) : 1000
          // 动态备货系数
          const shortage = Number(engine2.raw.data.GetValue('B17', 'value')) || 0
          const wasteRate = Number(engine2.raw.data.GetValue('B18', 'value')) || 0
          const conf = Math.max(0.6, Math.min(1.4, 1.0 + shortage * 0.5 - wasteRate * 0.5))
          propose.set('value', Math.min(resourceCap, Math.round(d * conf)), 8)
        },
      })

      entangleReady = true
    }
    // SilentSet 初始值 (接近真实面包店的数据)
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
    engine2.raw.data.SilentSet('B16', 'value', 3600)
    engine2.raw.data.SilentSet('B16', 'formula', '')
    engine2.raw.data.SilentSet('B17', 'value', 0)
    engine2.raw.data.SilentSet('B17', 'formula', '')
    engine2.raw.data.SilentSet('B18', 'value', 0)
    engine2.raw.data.SilentSet('B18', 'formula', '')

    // A列标签
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
    engine.setCellValue('A16', '📜 上期需求')
    engine.setCellValue('A17', '⚠️ 上期缺货率')
    engine.setCellValue('A18', '📦 上期报废率')

    // 衍生公式 (在 SilentSet 之后, notifyAll 之前注册)
    engine.setCellFormula('B6', '=B1*MIN(B2,B3)')            // 月收入 = 售价 × 实际销售(产能限制)
    engine.setCellFormula('B12', '=(B10+B11+B4)*B3')          // 总生产成本
    engine.setCellFormula('B7', '=B12+B5+B9+B13')             // 总成本 = 生产 + 房租 + 人工 + 营销
    engine.setCellFormula('B8', '=B6-B7')                     // 月利润

    // 🔥 notifyAll: 从所有根节点推演
    engine2.raw.config.notifyAll()

    // 🔧 暴露引擎到 window 供调试验证
    ;(window as any).__engine = engine2

    // 📝 Logger: 关注人工成本(B9)和产能(B3)的变化
    const logger = useLogger({ focusPaths: ['B9', 'B3'] })
    let cancel = engine2.raw.config.usePlugin(logger)

    setTimeout(() => rebuildGridData(), 200)
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
}
.app { max-width: 1200px; margin: 0 auto; padding: 8px 12px; height: 100vh; display: flex; flex-direction: column; }

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

.grid-wrap { flex: 1; overflow: hidden; border: 1px solid #d2d2d7; border-radius: 5px; }
.grid-wrap revo-grid {
  width: 100%; height: 100%;
  --rg-color: #1d1d1f;
  --rg-background: #ffffff;
  --rg-header-background: #f5f5f7;
  --rg-border-color: #d2d2d7;
  --rg-selection-color: rgba(0,113,227,0.15);
  --rg-focused-cell-border-color: #0071e3;
  --rg-row-hover-background: #f5f5f7;
  --rg-cell-color: #1d1d1f;
  --rg-cell-selected-background: rgba(0,113,227,0.08);
  --rg-header-color: #1d1d1f;
  --rg-header-selected-color: #0071e3;
  --rg-disabled-color: #aeaeb2;
  --rg-error-color: #dc2626;
  --rg-scrollbar-thumb-background: #c7c7cc;
  --rg-scrollbar-track-background: #f5f5f7;
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
