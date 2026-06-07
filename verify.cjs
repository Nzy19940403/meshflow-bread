/**
 * MeshFlow 引擎直接验证脚本
 * 用 @meshflow/core 创建引擎，设置相同规则，验证 Python 穷举结果
 * 
 * 用法: node verify.js
 */

const { createEngine } = require('@meshflow/core')

// ===== 常量 =====
const B10 = 3  // 原料成本
const B11 = 1  // 其他变动成本

// ===== 创建引擎 =====
const engine = createEngine({
  config: { logLevel: 'error' /* 安静模式 */ }
})

const eng = engine

// ===== 注册 SetRules =====

// S1: 房租 B5 = f(B14, B15)  非线性折扣
eng.config.SetRules(['B14', 'B15'], 'B5', 'value', {
  logic: ({ slot }) => {
    const area = slot.triggerTargets[0]?.value ?? 80
    const grade = slot.triggerTargets[1]?.value ?? 5
    const a = Number(area)
    const g = Number(grade)
    return Math.max(0, Math.round(a * g * Math.max(2, 20 - a * 0.05)))
  },
  triggerKeys: ['value', 'value'],
})

// S2: 需求 B2 = f(B1, B15, B13, B17)
eng.config.SetRules(['B1', 'B15', 'B13', 'B17'], 'B2', 'value', {
  logic: ({ slot }) => {
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

// S3: 加工成本 B4 = f(B3)
eng.config.SetRule('B3', 'B4', 'value', {
  logic: ({ slot }) => Math.max(0.1, 2 - (slot.triggerTargets[0].value || 0) * 0.0002),
  triggerKeys: ['value'],
})

// ===== 注册纠缠边 =====

// E1: B16→B3 (权10) 上期需求驱动产能
eng.config.useEntangle({
  cause: 'B16', impact: 'B3', via: ['value'],
  emit: (src, tgt, propose) => {
    const rawArea = eng.data.GetValue('B14', 'value')
    const rawLabor = eng.data.GetValue('B9', 'value')
    const area = rawArea ?? 80
    const labor = rawLabor ?? 15000
    if (area <= 0 || labor <= 0) { propose.set('value', 0, 10); return }
    const baseFromArea = Math.floor(Number(area) * 25)
    const baseFromLabor = Math.floor(Number(labor) / 5.0)
    const resourceCap = Math.min(baseFromArea, baseFromLabor)
    const lastDemand = src.state.value || 1000
    propose.set('value', Math.min(resourceCap, Math.round(Number(lastDemand) * 1.2)), 10)
  },
})

// E2: B4→B3 (权7) 成本效率红利
eng.config.useEntangle({
  cause: 'B4', impact: 'B3', via: ['value'],
  emit: (src, tgt, propose) => {
    const rawArea = eng.data.GetValue('B14', 'value')
    const rawLabor = eng.data.GetValue('B9', 'value')
    const area = rawArea ?? 80
    const labor = rawLabor ?? 15000
    const rawLastDemand = eng.data.GetValue('B16', 'value')
    const lastDemand = rawLastDemand ?? 1000
    const fromDemand = Math.round(Number(lastDemand) * 1.2)
    if (area <= 0 || labor <= 0) { propose.set('value', 0, 7); return }
    const baseFromArea = Math.floor(Number(area) * 25)
    const baseFromLabor = Math.floor(Number(labor) / 5.0)
    const costBoost = Math.max(0, (2 - (src.state.value || 2)) * 200)
    const effectiveCap = Math.floor(Math.min(baseFromArea, baseFromLabor) + costBoost)
    propose.set('value', Math.min(effectiveCap, fromDemand), 7)
  },
})

// E3: B9→B3 (权8) 人工变化
eng.config.useEntangle({
  cause: 'B9', impact: 'B3', via: ['value'],
  emit: (src, tgt, propose) => {
    const rawArea = eng.data.GetValue('B14', 'value')
    const rawLabor = eng.data.GetValue('B9', 'value')
    const area = rawArea ?? 80
    const labor = rawLabor ?? 15000
    if (area <= 0 || labor <= 0) { propose.set('value', 0, 8); return }
    const resourceCap = Math.min(Math.floor(Number(area) * 25), Math.floor(Number(labor) / 5.0))
    const rawDemand = eng.data.GetValue('B16', 'value')
    const d = rawDemand ?? 1000
    propose.set('value', Math.min(resourceCap, Math.round(Number(d) * 1.2)), 8)
  },
})

// E4: B14→B3 (权8) 面积变化
eng.config.useEntangle({
  cause: 'B14', impact: 'B3', via: ['value'],
  emit: (src, tgt, propose) => {
    const rawArea = eng.data.GetValue('B14', 'value')
    const rawLabor = eng.data.GetValue('B9', 'value')
    const area = rawArea ?? 80
    const labor = rawLabor ?? 15000
    if (area <= 0 || labor <= 0) { propose.set('value', 0, 8); return }
    const resourceCap = Math.min(Math.floor(Number(area) * 25), Math.floor(Number(labor) / 5.0))
    const rawDemand = eng.data.GetValue('B16', 'value')
    const d = rawDemand ?? 1000
    propose.set('value', Math.min(resourceCap, Math.round(Number(d) * 1.2)), 8)
  },
})

// ===== 读取辅助函数 =====
function read(id) {
  const v = eng.getCellValue(id)
  return v !== null && v !== undefined ? Number(v) : 0
}

// ===== 模拟 12 个月 =====
function runSimulation(params) {
  // 设置参数
  eng.data.SilentSet('B1', 'value', params.B1)
  eng.data.SilentSet('B9', 'value', params.B9)
  eng.data.SilentSet('B13', 'value', params.B13)
  eng.data.SilentSet('B14', 'value', params.B14)
  eng.data.SilentSet('B15', 'value', params.B15)
  eng.data.SilentSet('B16', 'value', 3600)  // 初始上期需求
  eng.data.SilentSet('B17', 'value', 0)      // 初始缺货率
  eng.data.SilentSet('B10', 'value', B10)
  eng.data.SilentSet('B11', 'value', B11)

  // 注册衍生公式（在 SilentSet 之后）
  eng.setCellFormula('B6', '=B1*MIN(B2,B3)')
  eng.setCellFormula('B12', '=(B10+B11+B4)*B3')
  eng.setCellFormula('B7', '=B12+B5+B9+B13')
  eng.setCellFormula('B8', '=B6-B7')

  const history = []
  let cumulativeProfit = 0

  for (let month = 0; month < 12; month++) {
    // NotifyAll: 触发全套 SetRules + 纠缠收敛
    eng.config.notifyAll()

    // 收集当月数据
    const b2 = read('B2')
    const b3 = read('B3')
    const b4 = read('B4')
    const b5 = read('B5')
    const b6 = read('B6')
    const b7 = read('B7')
    const b8 = read('B8')
    const b12 = read('B12')

    cumulativeProfit += b8
    history.push({
      month: month + 1,
      demand: b2,
      capacity: b3,
      sold: Math.min(b2, b3),
      b4: b4,
      b5: b5,
      b12: b12,
      revenue: b6,
      cost: b7,
      profit: b8,
    })

    // 月度推进
    const shortage = (b3 < b2 && b2 > 0) ? Math.round((b2 - b3) / b2 * 1000) / 1000 : 0
    eng.data.SetValue('B16', 'value', b2)
    eng.data.SetValue('B17', 'value', shortage)
  }

  return { history, cumulativeProfit }
}

// ===== 测试参数 =====
const strategies = [
  { name: '🥇 全局最优', B1: 28, B9: 16000, B13: 5000, B14: 140, B15: 10 },
  { name: '🥇 精品店',   B1: 28, B9: 8000,  B13: 2000, B14: 60,  B15: 3 },
  { name: '🏭 工厂',     B1: 16, B9: 14000, B13: 3500, B14: 120, B15: 1 },
]

for (const s of strategies) {
  const { history, cumulativeProfit } = runSimulation(s)

  console.log(`\n${'='.repeat(80)}`)
  console.log(`  ${s.name}   B1=${s.B1}  B9=${s.B9}  B13=${s.B13}  B14=${s.B14}  B15=${s.B15}`)
  console.log(`  全年利润: ¥${cumulativeProfit.toLocaleString()}`)
  console.log(`${'='.repeat(80)}`)
  console.log(`  月 | 需求  产能  实售  B4    B5    收入    成本    利润`)
  console.log(`  ${'-'.repeat(67)}`)
  for (const h of history) {
    console.log(
      `  ${String(h.month).padStart(2)} | ${String(Math.round(h.demand)).padStart(5)} ${String(Math.round(h.capacity)).padStart(5)} ${String(Math.round(h.sold)).padStart(5)} ${h.b4.toFixed(2).padStart(5)} ${String(Math.round(h.b5)).padStart(5)} ${String(Math.round(h.revenue)).padStart(7)} ${String(Math.round(h.cost)).padStart(7)} ${String(Math.round(h.profit)).padStart(7)}`
    )
  }
}

console.log(`\n${'='.repeat(80)}`)
console.log('  🎯 与 Python 穷举结果对比:')
console.log('  Python 全局最优: 436,173')
console.log('  Python 精品店:   261,504')
console.log('  Python 工厂:     134,599')
console.log('  差异 = |MeshFlow - Python|')
