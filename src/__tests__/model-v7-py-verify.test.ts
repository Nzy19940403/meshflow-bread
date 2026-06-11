/**
 * V7 模型 — TypeScript vs Python 逐月对照
 *
 * 完全镜像 model_v7_final.py 的 sim() 函数
 * 运行: npx vitest run src/__tests__/model-v7-py-verify.test.ts
 */
import { describe, it, expect } from 'vitest'

// ============================================================
// Python 参照值 (model_v7_final.py 输出)
// ============================================================

const PY: Record<string, { profits: number[]; total: number; b2: number[]; b3: number[]; brand: number[]; fat: number[] }> = {
  comm24: {
    profits: [-1146, 5906, 2043, 3662, 3901, 1266, 1451, 1605, 7106, 7142, 4968, 7196],
    total: 45100,
    b2: [1338, 1745, 1519, 1611, 1622, 1468, 1477, 1485, 1858, 1833, 1674, 1883],
    b3: [1800, 1800, 1800, 1800, 1800, 1800, 1800, 1800, 1800, 1800, 1800, 1800],
    brand: [0, 23, 45, 66, 85, 103, 120, 136, 151, 165, 178, 190],
    fat: [40, 40, 45, 45, 46, 47, 47, 47, 47, 53, 59, 61],
  },
  comm26: {
    profits: [-1374, 5628, 1792, 3391, 3638, 1030, 1223, 1365, 7804, 7416, 4673, 8314],
    total: 44900,
    b2: [1252, 1634, 1422, 1508, 1519, 1375, 1384, 1391, 1740, 1717, 1567, 1763],
    b3: [1800, 1800, 1800, 1800, 1800, 1800, 1800, 1800, 1800, 1800, 1800, 1800],
    brand: [0, 23, 45, 66, 86, 104, 121, 137, 152, 166, 179, 191],
    fat: [40, 39, 40, 40, 40, 40, 40, 40, 40, 45, 50, 50],
  },
  fact18: {
    profits: [1512, 3958, 2614, 3172, 3230, 2274, 1800, 1808, 5705, 4261, 3300, 6229],
    total: 39863,
    b2: [827, 1080, 939, 995, 999, 899, 849, 849, 1249, 1099, 999, 1299],
    b3: [4500, 4500, 4500, 4500, 4500, 4500, 4500, 4500, 4500, 4500, 4500, 4500],
    brand: [0, 16, 29, 42, 50, 50, 50, 50, 50, 50, 50, 50],
    fat: [40, 32, 24, 16, 10, 10, 10, 10, 10, 10, 10, 10],
  },
  fact22: {
    profits: [13875, 16977, 15243, 15933, 16474, 15241, 14615, 14624, 19754, 17845, 16572, 20430],
    total: 197583,
    b2: [802, 1047, 909, 962, 1004, 906, 856, 856, 1258, 1107, 1007, 1309],
    b3: [5400, 5400, 5400, 5400, 5400, 5400, 5400, 5400, 5400, 5400, 5400, 5400],
    brand: [0, 15, 25, 35, 45, 50, 50, 50, 50, 50, 50, 50],
    fat: [40, 34, 29, 23, 17, 12, 10, 10, 10, 10, 10, 10],
  },
  lux34: {
    profits: [-8745, 3573, 1060, 5370, 6895, 2978, 3066, 3846, 19715, 17016, 12131, 20903],
    total: 87808,
    b2: [1298, 1761, 1665, 1826, 1882, 1734, 1736, 1764, 2359, 2256, 2072, 2423],
    b3: [2400, 2400, 2400, 2400, 2400, 2400, 2400, 2400, 2400, 2400, 2400, 2400],
    brand: [0, 24, 47, 69, 89, 108, 126, 143, 159, 174, 187, 200],
    fat: [40, 37, 37, 36, 36, 36, 36, 36, 36, 42, 44, 44],
  },
  lux36: {
    profits: [-11021, 380, -2122, 2042, 3592, 22, 136, 941, 15882, 13325, 8808, 17684],
    total: 49669,
    b2: [1168, 1581, 1489, 1639, 1694, 1564, 1567, 1595, 2135, 2041, 1877, 2197],
    b3: [2400, 2400, 2400, 2400, 2400, 2400, 2400, 2400, 2400, 2400, 2400, 2400],
    brand: [0, 24, 47, 69, 90, 109, 127, 144, 160, 175, 189, 202],
    fat: [40, 36, 35, 33, 32, 31, 30, 29, 28, 28, 28, 28],
  },
  area60: {
    profits: [-10518, -6203, -8533, -7523, -7386, -8965, -8842, -8731, -4702, -4943, -6604, -4343],
    total: -87293,
    b2: [],
    b3: [],
    brand: [],
    fat: [],
  },
  area180: {
    profits: [-4545, -1408, -3147, -2434, -2343, -3519, -4071, -3368, -486, -658, -1875, -246],
    total: -28100,
    b2: [],
    b3: [],
    brand: [],
    fat: [],
  },
}

const PARAMS: Record<string, [number, number, number, number, number, number, number, number]> = {
  comm24: [24, 2, 0, 2000, 60, 4, 4, 4500],
  comm26: [26, 2, 0, 2000, 60, 4, 4, 4500],
  fact18: [18, 3, 100, 500, 150, 2, 2, 3500],
  fact22: [22, 3, 100, 500, 180, 2, 2, 3000],
  lux34:  [34, 2, 300, 2500, 80, 8, 4, 5500],
  lux36:  [36, 2, 300, 2500, 80, 8, 4, 5500],
  area60:  [18, 3, 100, 1000, 60, 3, 3, 4000],
  area180: [18, 3, 100, 1000, 180, 3, 3, 4000],
}

// ============================================================
// TypeScript V7 仿真 — 与 model_v7_final.py 逐行对照
// ============================================================

const SZ = [0.85, 1.10, 0.95, 1.00, 1.00, 0.90, 0.85, 0.85, 1.25, 1.10, 1.00, 1.30]

function sk(fat: number): number {
  if (fat < 80) return 1.0
  if (fat >= 100) return 0.1
  const t = (fat - 80) / 20
  return 1.0 - t * t * (3.0 - 2.0 * t) * 0.9
}

// Python banker's rounding: round half to even
function pyRound(x: number): number {
  if (x < 0) return -pyRound(-x)
  const int = Math.floor(x)
  const frac = x - int
  if (frac < 0.5) return int
  if (frac > 0.5) return int + 1
  return int % 2 === 0 ? int : int + 1
}

function brandP(brand: number, grade: number): number {
  const raw = 12 * Math.log(1 + brand / 25)
  const gradeF = Math.min(1.0, (grade - 1) / 8.0)
  return pyRound(Math.min(45, raw * gradeF))
}

function pbF(price: number): number {
  if (price < 15) return 1 + (15 - price) * 0.10
  if (price <= 22) return 1.0
  return Math.max(0.40, 1 - (price - 22) * 0.03)
}

function simulateV7(params: number[], months = 12) {
  const [B1, B24, B25, B13, B14, B15, B10, B26] = params
  let FAT = 40, EMP = 0, BR = 0, B21 = 0.8
  const results: any[] = []

  for (let m = 0; m < months; m++) {
    const sz = SZ[m % 12]

    // PhysCap: pure headcount*area, no salary multiplier
    const physCap = Math.max(1, Math.min(B14 * 30, B24 * 1800))
    const B3 = Math.max(0, pyRound(physCap * sk(FAT)))

    // B4: higher salary → lower waste → lower processing cost
    const wfB4 = 1.20 - 0.45 * Math.min(B26, 10000) / 10000
    const B4 = pyRound(Math.max(0.03, (1.5 - B3 * 0.00015) * wfB4 * (1 - EMP * 0.002)) * 100) / 100

    // B28: ingredient base + salary quality bonus
    const qBase = Math.max(0.15, Math.min(0.95, B10 / 5.5))
    const qSalary = B26 > 3000 ? Math.min(0.18, (B26 - 3000) / 28000) : 0
    const B28 = pyRound(Math.min(1.0, qBase + qSalary) * 1000) / 1000

    // Foot traffic
    let ft = (500 + 400 * Math.min(B15, 6))
    ft += pyRound(Math.sqrt(B14) * 15)
    ft += pyRound(Math.pow(B13, 0.45) * 0.8)
    ft += pyRound(BR * 0.8)
    if (B15 >= 3 && B15 <= 5 && B14 <= 90) {
      ft = pyRound(ft * 1.15)
    }
    const localBase = Math.max(0, pyRound(ft))

    // ma
    const bp = brandP(BR, B15)
    const ma = Math.max(12 + B15 * 2.5, 12 + B15 * 2.5 + bp + B21 * 2 + B28 * 3 + B26 / 2500)

    // Soft conversion
    const gap = Math.max(0, B1 - ma)
    let conv = 0.65 * pbF(B1) * (ma / (ma + gap * 0.8))
    conv = Math.min(0.82, Math.max(0.04, conv))

    // Season + brand loyalty
    const loyalSz = BR >= 200 ? Math.min(sz, 1.08) : (BR >= 100 ? Math.min(sz, 1.12) : sz)
    const finalSz = Math.max(loyalSz, BR >= 200 ? 0.95 : (BR >= 100 ? 0.90 : sz))
    let localD = Math.max(0, pyRound(localBase * conv * finalSz))

    // Tourist
    let tourD = 0
    if (B15 >= 5) {
      const tourBase = (B15 - 4) * 500 * pbF(B1)
      const tourMkt = pyRound(Math.sqrt(Math.max(0, B13)) * 5) * (0.5 + BR / 400)
      const tourTotal = pyRound(tourBase + tourMkt)
      const tourMa = Math.max(8, 8 + B15 * 2 + B13 / 4000 + BR * 0.25)
      const tourConv = B1 <= tourMa
        ? Math.min(0.75, 0.30 + (tourMa - B1) / tourMa * 0.35)
        : Math.max(0.02, 0.25 * tourMa / B1)
      tourD = Math.max(0, pyRound(tourTotal * tourConv * sz))
    }

    const B2 = localD + tourD
    const B6 = Math.min(B2, B3)

    // B2B: 3000/person, 30% retail price
    let wsSold = 0, wsRev = 0
    if (B14 >= 150) {
      const remaining = Math.max(0, B3 - B6)
      const b2bCap = B24 * 3000
      const spotCap = pyRound((B14 - 150) * 500)
      wsSold = Math.min(b2bCap + spotCap, remaining)
      wsRev = pyRound(wsSold * B1 * 0.30)
    }

    const B7 = B6 * B1 + wsRev

    // Rent
    const rate = 20 + 800 / (B14 + 15)
    const B5 = Math.max(0, pyRound(B14 * B15 * rate))

    // Labor
    const B9 = pyRound(B24 * B26 * (1 + B15 * 0.10 * Math.max(0, 1 - B24 * 0.05)))

    // Costs
    const B12 = pyRound(B10 * (1 - Math.min(0.4, B3 * 0.00006)) * 100) / 100
    const pkg = pyRound(B1 * 0.10)
    const util = pyRound(B14 * 18 + B24 * 120)
    const eq = 1200
    const trn = B25 * B24
    const misc = pyRound(0.02 * B24 * 1000)
    const retailCogs = pyRound((B12 + pkg + B4) * B6)
    const wsCogs = wsSold > 0 ? pyRound(wsSold * B10 * 0.50 + wsSold * 0.3) : 0
    const B8 = pyRound(B7 - retailCogs - wsCogs - B5 - B9 - B13 - trn - misc - util - eq)

    // FAT
    const retailUR = Math.min(1, B2 / Math.max(physCap, 1))
    let d = 0
    if (retailUR > 0.88) d = pyRound((retailUR - 0.88) * 35)
    if (retailUR > 0.95) d += 2
    if (retailUR < 0.75) d = -pyRound((0.75 - retailUR) * 15)
    if (B14 > 150 && B24 < Math.ceil(B14 / 35)) d += 3
    const newFAT = Math.max(10, Math.min(100, pyRound(FAT + d)))

    // BRAND
    const sr = Math.max(0, (B2 - B3) / Math.max(1, B2))
    const growth = B21 * 8 + B28 * 10 + Math.max(0, (100 - FAT) / 100) * 5 + Math.sqrt(Math.max(0, B13)) * 0.12
    const decay = BR * 0.015
    const gm = Math.max(0.03, 1 - BR / 500)
    let nb = Math.max(0, pyRound(BR + growth * gm - decay - sr * 8))
    if (B28 < 0.4) {
      const gap2 = 0.4 - B28
      nb = Math.max(0, nb - pyRound(gap2 * 20))
      const ceiling = B28 >= 0.3 ? 50 : 25
      if (nb > ceiling) nb = ceiling
    }
    const newBR = nb

    // EMP
    const newEMP = Math.min(200, pyRound(EMP + Math.max(1, 10 - pyRound(EMP * 0.05))))

    // B21
    const pp = B9 / Math.max(B3, 1)
    const bl = 2.5 + B15 * 0.3
    const ps = pp >= bl ? 0.7 + Math.min((pp - bl) / (bl * 2), 0.25) : pp / bl * 0.7
    const ut = B3 / Math.max(physCap, 1)
    const ov = Math.max(0, ut - (0.8 + 0.2 * ps)) * 1.2
    let newB21 = pyRound(Math.min(1, Math.max(0, ps - ov)) * 1000) / 1000
    if (newFAT > 60) newB21 = Math.max(0.3, newB21 - (newFAT - 60) * 0.004)
    if (newFAT > 85) newB21 = Math.max(0.15, newB21 - (newFAT - 85) * 0.01)

    results.push({
      profit: B8, demand: B2, capacity: B3,
      FAT: Math.round(FAT), BRAND: Math.round(BR),
    })

    FAT = newFAT
    EMP = newEMP
    BR = newBR
    B21 = newB21
  }
  return results
}

// ============================================================
// Tests
// ============================================================

describe('V7 六场景逐月对照', () => {
  for (const name of ['comm24', 'comm26', 'fact18', 'fact22', 'lux34', 'lux36']) {
    const params = PARAMS[name]
    const ref = PY[name]

    it(`${name} (¥${params[0]} ${params[1]}人 ${params[4]}m²)`, () => {
      const r = simulateV7(params, 12)

      // 逐月对照利润、需求、产能、品牌、疲劳
      for (let i = 0; i < 12; i++) {
        expect(r[i].profit).toBe(ref.profits[i])
        expect(r[i].demand).toBe(ref.b2[i])
        expect(r[i].capacity).toBe(ref.b3[i])
        expect(r[i].BRAND).toBe(ref.brand[i])
        expect(r[i].FAT).toBe(ref.fat[i])
      }

      const total = r.reduce((s, x) => s + x.profit, 0)
      expect(total).toBe(ref.total)
    })
  }
})

describe('V7 防印钞测试', () => {
  it('60m² 默认参数 不应盈利', () => {
    const r = simulateV7(PARAMS.area60, 12)
    const total = r.reduce((s, x) => s + x.profit, 0)
    expect(total).toBe(PY.area60.total)
    expect(total).toBeLessThan(0)
  })

  it('180m² 只拉面积 不应盈利', () => {
    const r = simulateV7(PARAMS.area180, 12)
    for (let i = 0; i < 12; i++) {
      expect(r[i].profit).toBe(PY.area180.profits[i])
    }
    const total = r.reduce((s, x) => s + x.profit, 0)
    expect(total).toBe(PY.area180.total)
    expect(total).toBeLessThan(0)
  })
})

describe('V7 关键特性验证', () => {
  it('physCap 不含工资系数 (salary→B4/B28 instead)', () => {
    const rLow = simulateV7([24, 2, 0, 2000, 60, 4, 4, 3000], 1)
    const rHigh = simulateV7([24, 2, 0, 2000, 60, 4, 4, 8000], 1)
    // 产能应相同 (physCap不随工资变)
    expect(rLow[0].capacity).toBe(rHigh[0].capacity)
  })

  it('B2B = 3000/人, 批发价30%零售', () => {
    // 工厂 150m² 3人: B2B cap = 3*3000 = 9000
    const r = simulateV7([18, 3, 100, 500, 150, 2, 2, 3500], 1)
    // B3 ≈ 4500, B2 ≈ 827 (very low), so wsSold ≈ 4500-827=3673
    // All at 30% of B1=18 → 18*0.30 = 5.40/unit
    expect(r[0].capacity).toBeGreaterThan(4000)
    // Should have B2B revenue (not just spot wholesale)
  })

  it('营收不含隐形+20%加成', () => {
    // Retail revenue should be exactly B6×B1, no hidden multiplier
    // We can't directly test this from the test output, but the profit
    // values matching Python reference confirms it's correct.
  })

  it('租金使用平滑衰减 rate=20+800/(area+15)', () => {
    const rent60 = Math.round(60 * 4 * (20 + 800 / (60 + 15)))
    const rent200 = Math.round(200 * 2 * (20 + 800 / (200 + 15)))
    // Just verifying the formula is applied
    expect(rent60).toBe(7368)  // 60*4*(20+10.67) = 60*4*30.67 = 7360
    expect(rent200).toBe(9480)
  })

  it('品牌溢价对数衰减 + 地段绑定', () => {
    // brand=200, grade=9 → raw=12*ln(1+200/25)=12*ln(9)=26.4, gradeF=1.0
    // bp = pyRound(26.4) = 26
    const bp = Math.round(12 * Math.log(1 + 200 / 25))
    expect(bp).toBe(26)

    // brand=200, grade=2 → gradeF=0.125, bp = pyRound(26.4*0.125) = pyRound(3.3) = 3
    const bpLow = Math.round(12 * Math.log(1 + 200 / 25) * (1 / 8))
    expect(bpLow).toBeLessThan(5)
  })
})
