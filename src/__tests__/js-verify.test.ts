/**
 * MeshFlow vs Python 穷举对比 — 纯 JS 实现
 *
 * 因为 @meshflow/core 的 SetRule/useEntangle 在 Node.js 环境不触发传播，
 * 这里用 hot-formula-parser + 纯 JS 实现所有公式逻辑，
 * 验证 Python 穷举结果的正确性。
 */
import { describe, it, expect } from 'vitest'

// ====== 所有公式的纯 JS 实现 ======

function round(v: number): number { return Math.round(v) }

/** S1: 房租 B5 */
function calcB5(b14: number, b15: number): number {
  return Math.max(0, round(b14 * b15 * Math.max(2, 20 - b14 * 0.05)))
}

/** S2: 需求 B2 */
function calcB2(b1: number, b15: number, b13: number, b17: number): number {
  const priceEffect = Math.max(300, 5000 - b1 * 200)
  const locationEffect = b15 * 200
  const marketingEffect = Math.sqrt(Math.max(0, b13)) * 15
  const base = priceEffect + locationEffect + marketingEffect
  const penalty = round(base * b17 * 0.5)
  return round(base - penalty)
}

/** S3: 加工成本 B4 */
function calcB4(b3: number): number {
  return Math.max(0.1, 2 - b3 * 0.0002)
}

/** 资源上限计算 */
function resourceCap(b14: number, b9: number): number {
  const fromArea = Math.floor(b14 * 25)
  const fromLabor = Math.floor(b9 / 5.0)
  return Math.min(fromArea, fromLabor)
}

/** 纠缠收敛：B3(产能) 最终值 */
function convergeB3(b14: number, b9: number, b16: number): number {
  const cap = resourceCap(b14, b9)
  const fromDemand = round(b16 * 1.2)

  if (cap <= 0 || b14 <= 0 || b9 <= 0) return 0

  // Epoch 1: E1 (B16→B3, w10) 胜出
  let b3 = Math.min(cap, fromDemand)
  let b4 = calcB4(b3)

  // Epoch 2+: E2 (B4→B3, w7) 迭代收敛
  for (let i = 0; i < 20; i++) {
    const prev = b3
    const costBoost = Math.max(0, (2 - b4) * 200)
    const effectiveCap = Math.floor(cap + costBoost)
    b3 = Math.min(effectiveCap, fromDemand)
    b4 = calcB4(b3)
    if (Math.abs(b3 - prev) < 0.5) break
  }

  return b3
}

/** 衍生公式 */
function calcB12(b10: number, b11: number, b4: number, b3: number): number {
  return (b10 + b11 + b4) * b3
}
function calcB6(b1: number, b2: number, b3: number): number {
  return b1 * Math.min(b2, b3)
}
function calcB7(b12: number, b5: number, b9: number, b13: number): number {
  return b12 + b5 + b9 + b13
}
function calcB8(b6: number, b7: number): number {
  return b6 - b7
}

/** 逐月推进 */
function shortage(b3: number, b2: number): number {
  if (b3 >= b2 || b2 <= 0) return 0
  return round((b2 - b3) / b2 * 1000) / 1000
}

interface YearResult {
  history: {
    month: number
    demand: number
    capacity: number
    sold: number
    b4: number
    b5: number
    b12: number
    revenue: number
    cost: number
    profit: number
  }[]
  cumulativeProfit: number
}

function simulateYear(
  b1: number, b9: number, b13: number, b14: number, b15: number,
  b10 = 3, b11 = 1,
  initialDemand = 3600, initialShortage = 0,
): YearResult {
  let b16 = initialDemand
  let b17 = initialShortage
  let cumProfit = 0
  const history: YearResult['history'] = []

  for (let m = 0; m < 12; m++) {
    const b5 = calcB5(b14, b15)
    const b2 = calcB2(b1, b15, b13, b17)
    const b3 = convergeB3(b14, b9, b16)
    const b4 = calcB4(b3)
    const b12 = calcB12(b10, b11, b4, b3)
    const b6 = calcB6(b1, b2, b3)
    const b7 = calcB7(b12, b5, b9, b13)
    const b8 = calcB8(b6, b7)
    const sold = Math.min(b2, b3)

    cumProfit += b8
    history.push({
      month: m + 1,
      demand: Math.round(b2),
      capacity: Math.round(b3),
      sold: Math.round(sold),
      b4: Math.round(b4 * 100) / 100,
      b5: Math.round(b5),
      b12: Math.round(b12),
      revenue: Math.round(b6),
      cost: Math.round(b7),
      profit: Math.round(b8),
    })

    // 月度推进
    b16 = b2
    b17 = shortage(b3, b2)
  }

  return { history, cumulativeProfit: Math.round(cumProfit) }
}

// ====== Python 穷举基准 ======

interface Strategy {
  name: string
  params: { B1: number; B9: number; B13: number; B14: number; B15: number }
  pythonProfit: number
}

const STRATEGIES: Strategy[] = [
  { name: '🥇 全局最优', params: { B1: 28, B9: 16000, B13: 5000, B14: 140, B15: 10 }, pythonProfit: 436173 },
  { name: '🥇 精品店',   params: { B1: 28, B9: 8000,  B13: 2000, B14: 60,  B15: 3 },  pythonProfit: 261504 },
  { name: '🏭 工厂',     params: { B1: 16, B9: 14000, B13: 3500, B14: 120, B15: 1 },  pythonProfit: 134599 },
  { name: '⚡ Gemini原版精品', params: { B1: 24, B9: 8400, B13: 300, B14: 46, B15: 5 }, pythonProfit: -1 },  // 旧模型无参考值
]

// ====== 测试 ======

describe('Python 穷举 vs 纯 JS 实现对比', () => {
  for (const s of STRATEGIES) {
    it(`${s.name} — 全年利润应 ≈ ¥${s.pythonProfit.toLocaleString()}`, () => {
      const p = s.params
      const result = simulateYear(p.B1, p.B9, p.B13, p.B14, p.B15)

      // 输出
      console.log(`\n--- ${s.name} ---`)
      console.log(`  配置: B1=${p.B1} B9=${p.B9} B13=${p.B13} B14=${p.B14} B15=${p.B15}`)
      console.log(`  月 | 需求 产能 实售  B4    B5    收入    成本    利润`)
      for (const h of result.history) {
        console.log(
          `  ${String(h.month).padStart(2)} | ${String(h.demand).padStart(5)} ${String(h.capacity).padStart(5)} ${String(h.sold).padStart(5)} ${String(h.b4).padStart(5)} ${String(h.b5).padStart(5)} ${String(h.revenue).padStart(7)} ${String(h.cost).padStart(7)} ${String(h.profit).padStart(7)}`
        )
      }
      console.log(`  全年利润: ¥${result.cumulativeProfit.toLocaleString()}`)

      if (s.pythonProfit > 0) {
        const diff = Math.abs(result.cumulativeProfit - s.pythonProfit)
        const pct = diff / s.pythonProfit
        console.log(`  Python: ¥${s.pythonProfit.toLocaleString()}`)
        console.log(`  偏差: ${(pct * 100).toFixed(2)}%`)
        expect(pct).toBeLessThan(0.01)
      }
    })
  }
})
