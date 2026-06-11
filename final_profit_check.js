/**
 * 最终利润验证脚本 — 精确复现 BakerySandbox.vue 中的 sk/rc/fd/nx 函数
 * 跑 36 个月 = 3 年
 */

// === 状态 ===
const c = {
  B1: 16, B2: 0, B3: 0, B4: 2, B5: 0, B6: 0, B7: 0, B8: 0,
  B9: 0, B10: 3, B11: 0, B12: 0, B13: 2000, B14: 150, B15: 7,
  B21: 0.8, B24: 8, B25: 100,
  FAT: 40, EMP: 0, BRAND: 0, TRAFFIC: 0
}

let monthLog = []
let p = 0, t = 0, m = 1

function safe(v, d = 0) { return v != null && v !== '' && Number.isFinite(v) ? v : d }

// BakerySandbox.vue 中的 sk — 最终版 (80→1, 80-90→0.30, 90-100→0.10)
function sk(c4) {
  const v = Number(c4)
  return !Number.isFinite(v) ? 1
       : v < 80 ? 1
       : v < 90 ? 0.30
       : 0.10
}

function gp(params) {
  return {
    B1: safe(params.B1, 16),
    B24: safe(params.B24, 8),
    B25: safe(params.B25, 100),
    B13: safe(params.B13, 2000),
    B10: safe(params.B10, 3),
    B14: safe(params.B14, 150),
    B15: 7  // 产品种类固定
  }
}

function rc(params) {
  const q = gp(params)
  // 工资
  c.B9 = Math.round(q.B24 * 1200 * (1 + q.B15 * 0.15 * Math.max(0, 1 - q.B24 * 0.08)))
  // 物理产能
  const ph = Math.max(1, Math.min(Math.floor(q.B14 * 25), q.B24 * 600) + Math.max(0, Math.round((2 - safe(c.B4)) * 200)))
  // 实际产能 = 物理×疲劳系数
  c.B3 = Math.max(0, Math.round(ph * sk(c.FAT)))
  // 报废率
  c.B4 = Math.max(0.1, Math.max(0.1, 2 - c.B3 * 0.0002) * (1 - safe(c.EMP) * 0.002))
  // 价格弹性
  const pb = q.B1 < 20 ? 1 + (20 - q.B1) * 0.15 : Math.max(0.6, 1 - (q.B1 - 20) * 0.03)
  // 面积杠杆
  const areaLever = 1 + q.B14 / 100
  const baseTr = Math.round(250 * q.B15) + Math.round(safe(c.BRAND) * 3)
  const mktTr = Math.round(Math.sqrt(Math.max(0, q.B13)) * 12)
  const tr = Math.round((baseTr) * pb) + Math.round(mktTr * areaLever)
  // 最高可接受价
  const ma = Math.max(1, 10 + q.B15 * 1.2 + safe(c.BRAND) * 0.3 + safe(c.B21) * 4)
  c.B2 = Math.max(0, Math.round(tr * (q.B1 <= ma ? 0.5 + (ma - q.B1) / ma * 0.4 : Math.max(0.05, 0.5 * ma / q.B1))))
  // 房租
  c.B5 = Math.max(0, Math.round(q.B14 * q.B15 * Math.max(2, 20 - q.B14 * 0.05)))
  // 满意度 (工资/人均产能+缺货惩罚)
  const pp = safe(c.B9) / Math.max(c.B3, 1)
  const bl = 3 + q.B15 * 0.4
  const ps = pp >= bl ? 0.7 + Math.min((pp - bl) / (bl * 2), 0.3) : pp / bl * 0.7
  c.B21 = Math.round(Math.min(1, Math.max(0, ps - Math.max(0, c.B3 / ph - 0.8) * 1.5)) * 1000) / 1000
  // 原料折扣上限50%
  c.B12 = Math.round(q.B10 * (1 - Math.min(0.5, c.B3 * 0.00008)) * 100) / 100
  c.B11 = safe(c.B4) + c.B3 * 0.002
  c.B6 = Math.min(c.B2, c.B3)
  c.B7 = c.B6 * q.B1
  c.B8 = Math.round(c.B7 - (c.B12 + 1 + safe(c.B4)) * c.B3 - c.B5 - c.B9 - q.B13 - q.B25 * q.B24 - Math.round(0.05 * q.B24 * 1500))
  c.TRAFFIC = tr
}

function fd(params) {
  const q = gp(params)
  const ph = Math.max(1, Math.min(Math.floor(q.B14 * 25), q.B24 * 600) + Math.max(0, Math.round((2 - safe(c.B4)) * 200)))
  let d = 3  // 基线熵增
  if (q.B25 == 0 && (c.B3 / ph) > 0.7) d += 5
  else if (q.B25 == 0) d += 2
  if ((c.B3 / ph) > 0.8) d += ((c.B3 / ph) - 0.8) * 40
  d -= q.B25 * 0.03
  const ff = c.FAT < 40 ? c.FAT / 40 : 1
  if (safe(c.B21) < 0.5) d -= (safe(c.B21) - 0.5) * 15 * ff
  if (safe(c.B9) / q.B24 > 1500) d -= (safe(c.B9) / q.B24 - 1500) * 0.005 * ff
  return Math.max(0, Math.min(100, Math.round(c.FAT + d)))
}

function nx(params) {
  if (m >= 36) return false
  rc(params)
  const pf = Math.round(c.B8)
  monthLog.push({ m: m, p: p, t: t })
  // 经验边际递减
  c.EMP = Math.min(200, Math.round(safe(c.EMP) + Math.max(1, 10 - Math.round(safe(c.EMP) * 0.05))))
  // 品牌含缺货惩罚+天花板
  const shortageRate = Math.max(0, (c.B2 - c.B3) / Math.max(1, c.B2))
  const brandGrowth = safe(c.B21) * 30
  const brandDecay = safe(c.BRAND) * Math.max(0.02, safe(c.BRAND) * 0.015)
  const growthMult = Math.max(0.1, 1 - safe(c.BRAND) / 800)
  c.BRAND = Math.max(0, Math.round(safe(c.BRAND) + brandGrowth * growthMult - brandDecay - shortageRate * 10))
  c.FAT = fd(params)
  p = pf
  t += pf
  m++
  return true
}

function reset(params) {
  m = 1; p = 0; t = 0; monthLog = []
  Object.assign(c, {
    B1: 16, B2: 0, B3: 0, B4: 2, B5: 0, B6: 0, B7: 0, B8: 0,
    B9: 0, B10: 3, B11: 0, B12: 0, B13: 2000, B14: 150, B15: 7,
    B21: 0.8, B24: 8, B25: 100,
    FAT: 40, EMP: 0, BRAND: 0, TRAFFIC: 0
  })
}

function simulate(label, params, years = 3) {
  reset(params)
  const months = years * 12
  while (nx(params)) {}
  const total = t
  const monthly = monthLog.map((_, i) => {
    // Re-run to get per-month profit
    return null
  })
  // Re-run for monthly breakdown
  reset(params)
  const perMonth = []
  for (let i = 0; i < months; i++) {
    rc(params)
    perMonth.push(c.B8)
    const nf = fd(params)
    // Update state
    const shortageRate = Math.max(0, (c.B2 - c.B3) / Math.max(1, c.B2))
    const brandGrowth = safe(c.B21) * 30
    const brandDecay = safe(c.BRAND) * Math.max(0.02, safe(c.BRAND) * 0.015)
    const growthMult = Math.max(0.1, 1 - safe(c.BRAND) / 800)
    c.BRAND = Math.max(0, Math.round(safe(c.BRAND) + brandGrowth * growthMult - brandDecay - shortageRate * 10))
    c.EMP = Math.min(200, Math.round(safe(c.EMP) + Math.max(1, 10 - Math.round(safe(c.EMP) * 0.05))))
    c.FAT = nf
  }
  const finalBrand = c.BRAND
  const finalFat = c.FAT
  const finalEmp = c.EMP
  const finalSat = c.B21

  console.log(`\n${label}`)
  console.log(`  ${'─'.repeat(55)}`)
  console.log(`  参数: 售价¥${params.B1}  员工${params.B24}人  培训¥${params.B25}  营销¥${params.B13}  面积${params.B14}㎡  进价¥${params.B10}`)
  console.log(`  最终状态: 品牌=${finalBrand}  疲劳=${finalFat}  经验=${finalEmp}  满意度=${finalSat.toFixed(3)}`)

  // Annual breakdown
  for (let y = 0; y < years; y++) {
    const start = y * 12
    const end = start + 12
    const annual = perMonth.slice(start, end).reduce((a, b) => a + b, 0)
    console.log(`  第${y + 1}年: ${annual >= 0 ? '+' : ''}¥${annual.toLocaleString()}`)
  }
  console.log(`  ${'─'.repeat(55)}`)
  console.log(`  3年总计: ${total >= 0 ? '+' : ''}¥${total.toLocaleString()}  年均: ${total >= 0 ? '+' : ''}¥${Math.round(total / years).toLocaleString()}`)

  // Show final 12 months detail
  if (years >= 3) {
    console.log(`\n  第3年逐月利润:`)
    const y3 = perMonth.slice(24, 36)
    y3.forEach((v, i) => {
      console.log(`    月${i + 25}: ${v >= 0 ? '+' : ''}¥${v.toLocaleString()}`)
    })
  }
  return total
}

// === 三大路线 ===
console.log('='.repeat(65))
console.log('  面包店沙盘 — 最终利润验证 (sk断崖 + BRAND×3)')
console.log('='.repeat(65))

const routes = [
  { label: '🏭 大厂走量', B1: 16, B24: 8, B25: 100, B13: 8000, B14: 250, B10: 3 },
  { label: '✨ 高奢溢价', B1: 30, B24: 3, B25: 500, B13: 5000, B14: 80,  B10: 3 },
  { label: '🏠 社区精酿', B1: 22, B24: 3, B25: 200, B13: 1500, B14: 60,  B10: 3 },
  { label: '🛌 躺平',    B1: 16, B24: 8, B25: 0,   B13: 0,    B14: 150, B10: 3 },
]

routes.forEach(r => simulate(r.label, r, 3))

// === 敏感性测试: 大厂不同面积/定价 ===
console.log(`\n\n${'='.repeat(65)}`)
console.log('  敏感性测试: 大厂路线 — 面积×定价矩阵')
console.log('='.repeat(65))

for (const area of [200, 250, 300]) {
  for (const price of [14, 16, 18]) {
    simulate(`  大厂 ${area}㎡ ¥${price}`, { B1: price, B24: 8, B25: 100, B13: 8000, B14: area, B10: 3 }, 3)
  }
}
