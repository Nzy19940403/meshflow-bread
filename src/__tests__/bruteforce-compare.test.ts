/**
 * MeshFlow 引擎 vs Python 穷举结果对比验证
 *
 * 直接用 createSheetEngine 建立完整面包店模型，
 * 用 Python 穷举找到的最优策略参数喂给引擎，对比逐月输出。
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { createSheetEngine } from '../engine'

// ===== 常量 =====
const B10 = 3
const B11 = 1

/** 注册全部 SetRules + 纠缠边 —— 完全对齐 App.vue onMounted */
function setupModel(engine: ReturnType<typeof createSheetEngine>) {
  const eng = engine.raw

  // S1: 房租 B5
  eng.config.SetRules(['B14', 'B15'], 'B5', 'value', {
    logic: ({ slot }: any) => {
      const area = slot.triggerTargets[0]?.value ?? 80
      const grade = slot.triggerTargets[1]?.value ?? 5
      const a = Number(area)
      const g = Number(grade)
      return Math.max(0, Math.round(a * g * Math.max(2, 20 - a * 0.05)))
    },
    triggerKeys: ['value', 'value'],
  })

  // S2: 需求 B2
  eng.config.SetRules(['B1', 'B15', 'B13', 'B17'], 'B2', 'value', {
    logic: ({ slot }: any) => {
      const price = slot.triggerTargets[0]?.value ?? 12
      const grade = slot.triggerTargets[1]?.value ?? 5
      const marketing = slot.triggerTargets[2]?.value ?? 0
      const shortage = slot.triggerTargets[3]?.value ?? 0
      const p = Number(price)
      const g = Number(grade)
      const m = Number(marketing)
      const s = Number(shortage)
      const priceEffect = Math.max(300, 5000 - p * 200)
      const locationEffect = g * 200
      const marketingEffect = Math.sqrt(Math.max(0, m)) * 15
      const base = priceEffect + locationEffect + marketingEffect
      const penalty = Math.round(base * s * 0.5)
      return Math.round(base - penalty)
    },
    triggerKeys: ['value', 'value', 'value', 'value'],
  })

  // E1: B16→B3 权10
  eng.config.useEntangle({
    cause: 'B16', impact: 'B3', via: ['value'],
    emit: (_src: any, _tgt: any, propose: any) => {
      const rawArea = eng.data.GetValue('B14', 'value')
      const rawLabor = eng.data.GetValue('B9', 'value')
      const area = (rawArea !== null && rawArea !== undefined) ? Number(rawArea) : 80
      const labor = (rawLabor !== null && rawLabor !== undefined) ? Number(rawLabor) : 15000
      if (area <= 0 || labor <= 0) { propose.set('value', 0, 10); return }
      const baseFromArea = Math.floor(area * 25)
      const baseFromLabor = Math.floor(labor / 5.0)
      const resourceCap = Math.min(baseFromArea, baseFromLabor)
      const lastDemand = _src.state.value || 1000
      propose.set('value', Math.min(resourceCap, Math.round(Number(lastDemand) * 1.2)), 10)
    },
  })

  // E2: B4→B3 权7
  eng.config.useEntangle({
    cause: 'B4', impact: 'B3', via: ['value'],
    emit: (src: any, _tgt: any, propose: any) => {
      const rawArea = eng.data.GetValue('B14', 'value')
      const rawLabor = eng.data.GetValue('B9', 'value')
      const area = (rawArea !== null && rawArea !== undefined) ? Number(rawArea) : 80
      const labor = (rawLabor !== null && rawLabor !== undefined) ? Number(rawLabor) : 15000
      const rawLastDemand = eng.data.GetValue('B16', 'value')
      const lastDemand = (rawLastDemand !== null && rawLastDemand !== undefined) ? Number(rawLastDemand) : 1000
      const fromDemand = Math.round(lastDemand * 1.2)
      if (area <= 0 || labor <= 0) { propose.set('value', 0, 7); return }
      const baseFromArea = Math.floor(area * 25)
      const baseFromLabor = Math.floor(labor / 5.0)
      const costBoost = Math.max(0, (2 - (src.state.value || 2)) * 200)
      const effectiveCap = Math.floor(Math.min(baseFromArea, baseFromLabor) + costBoost)
      propose.set('value', Math.min(effectiveCap, fromDemand), 7)
    },
  })

  // E3: B9→B3 权8
  eng.config.useEntangle({
    cause: 'B9', impact: 'B3', via: ['value'],
    emit: (_src: any, _tgt: any, propose: any) => {
      const rawArea = eng.data.GetValue('B14', 'value')
      const rawLabor = eng.data.GetValue('B9', 'value')
      const area = (rawArea !== null && rawArea !== undefined) ? Number(rawArea) : 80
      const labor = (rawLabor !== null && rawLabor !== undefined) ? Number(rawLabor) : 15000
      if (area <= 0 || labor <= 0) { propose.set('value', 0, 8); return }
      const resourceCap = Math.min(Math.floor(area * 25), Math.floor(labor / 5.0))
      const rawDemand = eng.data.GetValue('B16', 'value')
      const d = (rawDemand !== null && rawDemand !== undefined) ? Number(rawDemand) : 1000
      propose.set('value', Math.min(resourceCap, Math.round(d * 1.2)), 8)
    },
  })

  // E4: B14→B3 权8
  eng.config.useEntangle({
    cause: 'B14', impact: 'B3', via: ['value'],
    emit: (_src: any, _tgt: any, propose: any) => {
      const rawArea = eng.data.GetValue('B14', 'value')
      const rawLabor = eng.data.GetValue('B9', 'value')
      const area = (rawArea !== null && rawArea !== undefined) ? Number(rawArea) : 80
      const labor = (rawLabor !== null && rawLabor !== undefined) ? Number(rawLabor) : 15000
      if (area <= 0 || labor <= 0) { propose.set('value', 0, 8); return }
      const resourceCap = Math.min(Math.floor(area * 25), Math.floor(labor / 5.0))
      const rawDemand = eng.data.GetValue('B16', 'value')
      const d = (rawDemand !== null && rawDemand !== undefined) ? Number(rawDemand) : 1000
      propose.set('value', Math.min(resourceCap, Math.round(d * 1.2)), 8)
    },
  })

  // S3: B3→B4
  eng.config.SetRule('B3', 'B4', 'value', {
    logic: ({ slot }: any) => Math.max(0.1, 2 - (slot.triggerTargets[0].value || 0) * 0.0002),
    triggerKeys: ['value'],
  })
}

/** 设置初始参数并注册衍生公式 */
function initParams(engine: ReturnType<typeof createSheetEngine>, params: {
  B1: number; B9: number; B13: number; B14: number; B15: number
}) {
  const eng = engine.raw
  eng.data.SilentSet('B1', 'value', params.B1)
  eng.data.SilentSet('B1', 'formula', '')
  eng.data.SilentSet('B9', 'value', params.B9)
  eng.data.SilentSet('B9', 'formula', '')
  eng.data.SilentSet('B10', 'value', B10)
  eng.data.SilentSet('B10', 'formula', '')
  eng.data.SilentSet('B11', 'value', B11)
  eng.data.SilentSet('B11', 'formula', '')
  eng.data.SilentSet('B13', 'value', params.B13)
  eng.data.SilentSet('B13', 'formula', '')
  eng.data.SilentSet('B14', 'value', params.B14)
  eng.data.SilentSet('B14', 'formula', '')
  eng.data.SilentSet('B15', 'value', params.B15)
  eng.data.SilentSet('B15', 'formula', '')
  eng.data.SilentSet('B16', 'value', 3600)
  eng.data.SilentSet('B16', 'formula', '')
  eng.data.SilentSet('B17', 'value', 0)
  eng.data.SilentSet('B17', 'formula', '')

  // 衍生公式
  engine.setCellFormula('B6', '=B1*MIN(B2,B3)')
  engine.setCellFormula('B12', '=(B10+B11+B4)*B3')
  engine.setCellFormula('B7', '=B12+B5+B9+B13')
  engine.setCellFormula('B8', '=B6-B7')

  eng.config.notifyAll()

  // 手动触发一次 SetValue 来激活传播链
  // (SilentSet 不记录变更, notifyAll 可能无节点可推)
  const curB1 = eng.data.GetValue('B1', 'value')
  eng.data.SetValue('B1', 'value', curB1)
  eng.data.SetValue('B14', 'value', params.B14)
  eng.data.SetValue('B15', 'value', params.B15)
  eng.data.SetValue('B9', 'value', params.B9)
  eng.data.SetValue('B13', 'value', params.B13)

  // DEBUG: 检查 notifyAll 后各节点值
  const debugIds = ['B1','B2','B3','B4','B5','B14','B15','B16','B17']
  const debug = debugIds.map(id => {
    const v = eng.data.GetValue(id, 'value')
    return `${id}=${v}`
  }).join(', ')
  console.log('  [DEBUG after init]', debug)
}

/** 读值 */
function read(engine: ReturnType<typeof createSheetEngine>, id: string): number {
  const v = engine.getCellValue(id)
  return (v !== '' && v !== null && v !== undefined) ? Number(v) : 0
}

/** 跑 12 个月模拟 */
function runYear(engine: ReturnType<typeof createSheetEngine>) {
  const history: any[] = []
  let cumulativeProfit = 0

  for (let month = 0; month < 12; month++) {
    const b2 = read(engine, 'B2')
    const b3 = read(engine, 'B3')
    const b4 = read(engine, 'B4')
    const b5 = read(engine, 'B5')
    const b6 = read(engine, 'B6')
    const b7 = read(engine, 'B7')
    const b8 = read(engine, 'B8')
    const b12 = read(engine, 'B12')

    cumulativeProfit += b8
    history.push({
      month: month + 1,
      demand: Math.round(b2),
      capacity: Math.round(b3),
      sold: Math.min(Math.round(b2), Math.round(b3)),
      b4: Math.round(b4 * 100) / 100,
      b5: Math.round(b5),
      b12: Math.round(b12),
      revenue: Math.round(b6),
      cost: Math.round(b7),
      profit: Math.round(b8),
    })

    // 月度推进
    const shortage = (b3 < b2 && b2 > 0)
      ? Math.round((b2 - b3) / b2 * 1000) / 1000
      : 0
    engine.raw.data.SetValue('B16', 'value', b2)
    engine.raw.data.SetValue('B17', 'value', shortage)
  }

  return { history, cumulativeProfit }
}

// ============================================================
// Python 穷举结果（对照基准）
// ============================================================
const PYTHON_RESULTS = {
  global: {
    name: '🥇 全局最优',
    params: { B1: 28, B9: 16000, B13: 5000, B14: 140, B15: 10 },
    profit: 436173,
  },
  boutique: {
    name: '🥇 精品店',
    params: { B1: 28, B9: 8000, B13: 2000, B14: 60, B15: 3 },
    profit: 261504,
  },
  factory: {
    name: '🏭 工厂',
    params: { B1: 16, B9: 14000, B13: 3500, B14: 120, B15: 1 },
    profit: 134599,
  },
}

// ============================================================
// 测试
// ============================================================

describe('Python 穷举 vs MeshFlow 引擎对比', () => {

  for (const [key, strategy] of Object.entries(PYTHON_RESULTS)) {
    it(`${strategy.name} — 年利润应 ≈ ¥${strategy.profit.toLocaleString()}`, () => {
      const engine = createSheetEngine()
      setupModel(engine)
      initParams(engine, strategy.params)

      const { cumulativeProfit, history } = runYear(engine)

      // 输出逐月明细（测试日志可见）
      console.log(`\n--- ${strategy.name} ---`)
      console.log('  月 | 需求 产能 实售  B4    B5    收入    成本    利润')
      for (const h of history) {
        console.log(
          `  ${String(h.month).padStart(2)} | ${String(h.demand).padStart(5)} ${String(h.capacity).padStart(5)} ${String(h.sold).padStart(5)} ${String(h.b4).padStart(5)} ${String(h.b5).padStart(5)} ${String(h.revenue).padStart(7)} ${String(h.cost).padStart(7)} ${String(h.profit).padStart(7)}`
        )
      }
      console.log(`  全年利润: ¥${cumulativeProfit.toLocaleString()}  (Python: ¥${strategy.profit.toLocaleString()})`)
      console.log(`  偏差: ${((cumulativeProfit - strategy.profit) / strategy.profit * 100).toFixed(2)}%`)

      // 允许 1% 偏差（浮点/收敛差异）
      const diff = Math.abs(cumulativeProfit - strategy.profit)
      const pct = diff / strategy.profit
      expect(pct).toBeLessThan(0.01)
    })
  }
})
