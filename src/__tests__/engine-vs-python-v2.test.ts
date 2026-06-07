/**
 * meshflow 引擎 vs Python — 12个月推演对比验证
 *
 * 直接使用 createSheetEngine + 完整面包店公式，
 * 逐月推演并对比 Python 结果。
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

// ====== 策略参数 ======
const SCENARIOS = [
  { label: '✨ 高奢网红店', B1: 22, B9: 5000, B13: 300, B14: 60, B15: 5 },
  { label: '🏭 薄利大厂',   B1: 10, B9: 25000, B13: 8000, B14: 200, B15: 3 },
  { label: '🏠 社区老店',   B1: 14, B9: 12000, B13: 0, B14: 100, B15: 5 },
]

// Python 参考结果 (已迭代收敛 B3↔B4): 12个月利润 (元)
const PYTHON_PROFITS: Record<string, number[]> = {
  '✨ 高奢网红店': [3244, 4520, 5818, 7094, 8392, 9030, 9536, 10020, 10482, 10922, 10922, 10922],
  '🏭 薄利大厂':   [-42013, -39833, -38583, -37783, -37353, -37153, -37063, -37063, -37063, -37063, -37063, -37063],
  '🏠 社区老店':   [-14980, -13468, -12334, -11592, -11214, -10976, -10864, -10766, -10766, -10766, -10766, -10766],
}

function setupBakeryModel(engine: ReturnType<typeof createSheetEngine>) {
  const eng = engine.raw as any

  // B5 房租
  eng.config.SetRules(['B14', 'B15'], 'B5', 'value', {
    logic: ({ slot }: any) => {
      const area = slot.triggerTargets[0]?.value
      const grade = slot.triggerTargets[1]?.value
      const a = (area !== null && area !== undefined) ? Number(area) : 80
      const g = (grade !== null && grade !== undefined) ? Number(grade) : 5
      return Math.max(0, Math.round(a * g * Math.max(2, 20 - a * 0.05)))
    },
    triggerKeys: ['value', 'value'],
  } as any)

  // B2 需求
  eng.config.SetRules(['B1', 'B15', 'B13', 'B17', 'B19'], 'B2', 'value', {
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

      const priceDiscountBoost = p < 15 ? 1.0 + (15 - p) * 0.2 : 1.0
      const traffic = Math.round(150 * Math.pow(g, 1.7)) + Math.round(Math.sqrt(Math.max(0, m)) * 15 * priceDiscountBoost)

      const brandPremium = b * 0.5
      const locationPremium = g * 1.5
      const maxAcceptable = 10 + locationPremium + brandPremium

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

  // B3 产能 — 物理上限 (3条同权重共同预言)
  const computeB3Capacity = () => {
    const area = Number(eng.data.GetValue('B14', 'value') ?? 80)
    const labor = Number(eng.data.GetValue('B9', 'value') ?? 15000)
    const cost = Number(eng.data.GetValue('B4', 'value') ?? 2)
    if (area <= 0 || labor <= 0) return 0
    const areaCap = Math.floor(area * 25)
    const laborCap = Math.floor(labor / 2.5)
    const hardwareCap = Math.min(areaCap, laborCap)
    const efficiencyBonus = Math.max(0, Math.round((2 - cost) * 200))
    return Math.max(0, hardwareCap + efficiencyBonus)
  }

  eng.config.useEntangle({
    cause: 'B14', impact: 'B3', via: ['value'],
    emit: (_src: any, _tgt: any, propose: any) => { propose.set('value', computeB3Capacity(), 1) },
  })
  eng.config.useEntangle({
    cause: 'B9', impact: 'B3', via: ['value'],
    emit: (_src: any, _tgt: any, propose: any) => { propose.set('value', computeB3Capacity(), 1) },
  })
  eng.config.useEntangle({
    cause: 'B4', impact: 'B3', via: ['value'],
    emit: (_src: any, _tgt: any, propose: any) => { propose.set('value', computeB3Capacity(), 1) },
  })

  // B3→B4 规模效应
  eng.config.SetRule('B3', 'B4', 'value', {
    logic: ({ slot }: any) => Math.max(0.1, 2 - (slot.triggerTargets[0]?.value ?? 0) * 0.0002),
    triggerKeys: ['value'],
  } as any)

  // B21 员工满意度
  eng.config.SetRules(['B9', 'B3', 'B14'], 'B21', 'value', {
    logic: ({ slot }: any) => {
      const labor = Number(slot.triggerTargets[0]?.value ?? 15000)
      const cap = Number(slot.triggerTargets[1]?.value ?? 1000)
      const area = Number(slot.triggerTargets[2]?.value ?? 80)
      const grade = Number(eng.data.GetValue('B15', 'value') ?? 5)
      const payPerOutput = labor / Math.max(cap, 1)
      const utilization = cap / Math.max(area * 25, 1)
      const payBaseline = 3.0 + grade * 0.4
      let paySat: number
      if (payPerOutput >= payBaseline) {
        paySat = 0.7 + Math.min((payPerOutput - payBaseline) / (payBaseline * 2), 0.3)
      } else {
        paySat = payPerOutput / payBaseline * 0.7
      }
      const overworkPenalty = Math.max(0, utilization - 0.8) * 1.5
      return Math.round(Math.min(1, Math.max(0, paySat - overworkPenalty)) * 1000) / 1000
    },
    triggerKeys: ['value', 'value', 'value'],
  } as any)

  // B20 口味/品质
  eng.config.SetRules(['B21', 'B3', 'B14'], 'B20', 'value', {
    logic: ({ slot }: any) => {
      const sat = Number(slot.triggerTargets[0]?.value ?? 0.8)
      const cap = Number(slot.triggerTargets[1]?.value ?? 1000)
      const area = Number(slot.triggerTargets[2]?.value ?? 80)
      const utilization = cap / Math.max(area * 25, 1)
      let taste: number
      if (sat >= 0.6) {
        const overload = Math.max(0, utilization - 0.9) * 0.5
        taste = Math.min(1, Math.max(0.3, 1.0 - overload))
      } else {
        taste = sat * 0.6
      }
      return Math.round(taste * 1000) / 1000
    },
    triggerKeys: ['value', 'value', 'value'],
  } as any)

  // 公式: B6, B12, B7, B8
  engine.setCellFormula('B6', '=B1*MIN(B2,B3)')
  engine.setCellFormula('B12', '=(B10+B11+B4)*B3')
  engine.setCellFormula('B7', '=B12+B5+B9+B13')
  engine.setCellFormula('B8', '=B6-B7')
}

function initEngine(engine: ReturnType<typeof createSheetEngine>, params: { B1: number, B9: number, B13: number, B14: number, B15: number }) {
  const eng = engine.raw as any
  eng.data.SilentSet('B1', 'value', params.B1)
  eng.data.SilentSet('B1', 'formula', '')
  eng.data.SilentSet('B9', 'value', params.B9)
  eng.data.SilentSet('B9', 'formula', '')
  eng.data.SilentSet('B10', 'value', 3)
  eng.data.SilentSet('B10', 'formula', '')
  eng.data.SilentSet('B11', 'value', 1)
  eng.data.SilentSet('B11', 'formula', '')
  eng.data.SilentSet('B13', 'value', params.B13)
  eng.data.SilentSet('B13', 'formula', '')
  eng.data.SilentSet('B14', 'value', params.B14)
  eng.data.SilentSet('B14', 'formula', '')
  eng.data.SilentSet('B15', 'value', params.B15)
  eng.data.SilentSet('B15', 'formula', '')
  eng.data.SilentSet('B17', 'value', 0)
  eng.data.SilentSet('B17', 'formula', '')
  eng.data.SilentSet('B18', 'value', 0)
  eng.data.SilentSet('B18', 'formula', '')
  eng.data.SilentSet('B19', 'value', 0)
  eng.data.SilentSet('B19', 'formula', '')
  eng.data.SilentSet('B20', 'value', 0.8)
  eng.data.SilentSet('B20', 'formula', '')
  eng.data.SilentSet('B21', 'value', 0.8)
  eng.data.SilentSet('B21', 'formula', '')
}

async function runEngine(engine: ReturnType<typeof createSheetEngine>): Promise<number[]> {
  const eng = engine.raw as any
  const profits: number[] = []
  let b19 = 0

  for (let month = 1; month <= 12; month++) {
    await eng.config.notifyAll()
    await new Promise(r => setTimeout(r, 10))

    const b2 = Number(eng.data.GetValue('B2', 'value')) || 0
    const b3 = Number(eng.data.GetValue('B3', 'value')) || 0
    const b8 = Number(eng.data.GetValue('B8', 'value')) || 0
    const b20 = Number(eng.data.GetValue('B20', 'value')) || 0.8
    const b15 = Number(eng.data.GetValue('B15', 'value')) || 5
    const b13 = Number(eng.data.GetValue('B13', 'value')) || 0

    profits.push(Math.round(b8))

    // 计算缺货/报废
    const shortage = (b3 < b2 && b2 > 0) ? Math.round((b2 - b3) / b2 * 1000) / 1000 : 0
    const waste = (b3 > b2 && b3 > 0) ? Math.round((b3 - b2) / b3 * 1000) / 1000 : 0

    // 品牌增长 B19
    const traffic = Math.round(150 * Math.pow(b15, 1.7)) + Math.sqrt(Math.max(0, b13)) * 15
    const mouthGrowth = 10
    const growth = Math.round(b20 * (traffic / 100 + mouthGrowth))
    const decayRate = Math.max(0.05, b19 * 0.01)
    const decay = Math.round(b19 * decayRate)
    b19 = Math.max(0, b19 + growth - decay)

    // 写入下月缓存
    eng.data.SilentSet('B16', 'value', Math.round(b2))
    eng.data.SilentSet('B16', 'formula', '')
    eng.data.SilentSet('B17', 'value', shortage)
    eng.data.SilentSet('B17', 'formula', '')
    eng.data.SilentSet('B18', 'value', waste)
    eng.data.SilentSet('B18', 'formula', '')
    eng.data.SilentSet('B19', 'value', b19)
    eng.data.SilentSet('B19', 'formula', '')
  }

  return profits
}

describe('MeshFlow 引擎 vs Python 推演验证', () => {
  for (const scenario of SCENARIOS) {
    it(`${scenario.label}: 12个月利润与Python一致`, async () => {
      const engine = createSheetEngine()
      setupBakeryModel(engine)
      initEngine(engine, scenario)

      // 首月自洽: B16 = B2
      await engine.raw.config.notifyAll()
      await new Promise(r => setTimeout(r, 10))
      const initialB2 = Number(engine.raw.data.GetValue('B2', 'value')) || 0
      engine.raw.data.SilentSet('B16', 'value', Math.max(100, Math.round(initialB2)))
      engine.raw.data.SilentSet('B16', 'formula', '')

      const profits = await runEngine(engine)
      const expected = PYTHON_PROFITS[scenario.label]

      console.log(`\n  ${scenario.label} — 引擎月利润 vs Python:`)
      for (let m = 0; m < 12; m++) {
        const diff = Math.abs(profits[m] - expected[m])
        const ok = diff <= 1 ? '✅' : '❌'
        console.log(`    月${m+1}: 引擎=${profits[m]}  Python=${expected[m]}  差=${diff}  ${ok}`)
      }

      // 允许 ±10 元（hot-formula-parser 浮点精度差异）
      for (let m = 0; m < 12; m++) {
        expect(Math.abs(profits[m] - expected[m])).toBeLessThanOrEqual(10)
      }
    })
  }
})
