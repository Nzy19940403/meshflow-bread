/**
 * 社区面包店生存验证
 * 目标：B1≥24, B24≤3, B14≤80, B15≤4 时年利润>¥8万, FAT<75
 */
import { describe, it, expect } from 'vitest'

// Python 模型 1:1 复现 (利用率 FAT, 培训 B25 减缓)
function simulate(p: number[], months = 12) {
  const [B1,B24,B25,B13,B14,B15,B10,B26] = p
  const S=[0.85,1.10,0.95,1.00,1.00,0.90,0.85,0.85,1.25,1.10,1.00,1.30]
  function sk(f: number): number {
    if (f < 80) return 1.0
    if (f >= 100) return 0.1
    const t = (f - 80) / 20
    return 1.0 - t*t*(3-2*t)*0.9
  }
  function pbf(b1: number): number {
    return b1 < 20 ? (1+(20-b1)*0.15) : Math.max(0.6,1-(b1-20)*0.03)
  }
  const R = Math.round
  let FAT = 40, EMP = 0, BRAND = 0, B21 = 0.8, prevB2 = 1000
  const results: any[] = []

  for (let m = 0; m < months; m++) {
    const sz = S[m % 12]

    const B9 = R(B24 * B26 * (1 + B15 * 0.15 * Math.max(0, 1 - B24 * 0.08)))
    const B5 = Math.max(0, R(B14 * B15 * Math.max(8, 45 - B14 * 0.10)))
    const wf = 0.2 + 1.6 * Math.min(B26, 10000) / 10000
    const eff = 1 + B25 / 600
    const le = B14 >= 150 ? 1800 : 1500
    const phys = Math.max(1, Math.min(B14 * 35, B24 * le) * wf * eff)
    const planned = R(prevB2 * 1.2)
    const B3 = Math.max(0, R(Math.min(phys, planned) * sk(FAT)))

    const wF = Math.max(0.5, 1.5 - B26 / 5000)
    const eb = EMP > 50 ? (1 - EMP * 0.003) : (1 - EMP * 0.002)
    const B4 = R(Math.max(0.1, Math.max(0.1, 2 - B3 * 0.0002) * eb * wF) * 100) / 100
    const b28b = Math.max(0.2, Math.min(1.0, B10 / 5.0))
    const b28s = B3 > 3000 ? Math.min(0.25, (B3 - 3000) * 0.00008) : 0
    const B28 = R(Math.min(1.0, b28b + b28s) * 1000) / 1000

    const ppb = pbf(B1)
    const qp = Math.max(0, (B26 - 4000) / 500)
    const bC = R(BRAND * 3)
    const bP = BRAND > 300 ? 0 : BRAND > 100 ? 1 - (BRAND - 100) / 200 : 1
    const bd = R((500 + 500 * B15) * ppb) + R(bC * bP)
    const mkt = R(Math.sqrt(Math.max(0, B13)) * 10) * (1 + B14 / 100)
    const rt = R(bd + mkt)
    const ma_r = Math.max(1, 15 + B15 * 2 + BRAND * 0.5 + B21 * 3 + qp)
    const rcv = B1 <= ma_r ? Math.min(0.9, 0.5 + (ma_r - B1) / ma_r * 0.4) : Math.max(0.05, 0.5 * ma_r / B1)
    let localD = Math.max(0, R(rt * rcv * sz))
    let tourD = 0
    if (B15 >= 5) {
      const tb = (B15 - 4) * 500 * ppb
      const tm = B15 >= 7 ? R(Math.sqrt(Math.max(0, B13)) * 5) : 0
      const tt = R(tb + tm)
      const ma_t = Math.max(1, 8 + B15 * 2.5 + B13 / 2500 + qp)
      const tcv = B1 <= ma_t ? Math.min(0.80, 0.35 + (ma_t - B1) / ma_t * 0.35) : Math.max(0.03, 0.35 * ma_t / B1)
      tourD = Math.max(0, R(tt * tcv * sz))
    }
    const B2 = localD + tourD
    const B6 = Math.min(B2, B3)

    const B7 = B6 * B1 + R(B6 * B1 * 0.20)
    const B12 = R(B10 * (1 - Math.min(0.5, B3 * 0.00008)) * 100) / 100
    const pkg = R(B1 * 0.15)
    const uc = R(B14 * 25 + B24 * 200)
    const trn = B25 * B24
    const ms = R(0.05 * B24 * 1500)
    const rcogs = R((B12 + pkg + B4) * Math.min(B6, B3))
    const B8 = R(B7 - rcogs - B5 - B9 - B13 - trn - ms - uc - 2000)

    const pp = B9 / Math.max(B3, 1)
    const bl = 3 + B15 * 0.4
    const ps = pp >= bl ? 0.7 + Math.min((pp - bl) / (bl * 2), 0.3) : pp / bl * 0.7
    const ut = B3 / Math.max(phys, 1)
    const ov = Math.max(0, ut - (0.8 + 0.2 * ps)) * 1.5
    B21 = R(Math.min(1, Math.max(0, ps - ov)) * 1000) / 1000

    // FAT: capacity utilization
    const ur = B3 / Math.max(phys, 1)
    let d = 0
    if (ur > 0.90) d = R((ur - 0.90) * 60) + 3
    else if (ur > 0.75) d = R((ur - 0.75) * 20)
    else if (ur < 0.60) d = -R((0.60 - ur) * 10)
    d = R(d * Math.max(0.1, 1 - B25 / 500))
    FAT = Math.max(10, Math.min(100, FAT + d))

    // BRAND
    const sr = Math.max(0, (B2 - B3) / Math.max(1, B2))
    const growth = B21 * 10 + B28 * 12 + Math.max(0, (100 - FAT) / 100) * 6 + Math.sqrt(Math.max(0, B13)) * 0.15
    const dc = BRAND * 0.02
    const gm = Math.max(0.05, 1 - BRAND / 400)
    let nb = R(BRAND + growth * gm - dc - sr * 10)
    if (B28 < 0.40) {
      nb -= R((0.40 - B28) * 25)
      nb = Math.min(nb, B28 >= 0.30 ? 50 : 25)
    }
    BRAND = Math.max(0, nb)
    EMP = Math.min(200, R(EMP + Math.max(1, 10 - R(EMP * 0.05))))
    prevB2 = B2

    results.push({ B8, FAT, B2, B3, BRAND, ur })
  }
  return { results, total: results.reduce((s, r) => s + r.B8, 0) }
}

const COMMUNITY = [
  { label: '社区·升价+培训', params: [26, 3, 400, 1500, 60, 3, 3, 4000] },
  { label: '社区·高价精料', params: [26, 2, 400, 1500, 60, 3, 4, 4500] },
  { label: '社区·最优', params: [26, 2, 400, 3000, 70, 4, 3, 3500] },
  { label: '社区·低配', params: [22, 3, 100, 1000, 60, 3, 3, 4000] },
]

describe('社区店生存验证', () => {
  for (const c of COMMUNITY) {
    it(`${c.label} — 年利润>¥8万且FAT<75`, () => {
      const { results, total } = simulate(c.params)

      const maxFAT = Math.max(...results.map(r => r.FAT))
      const avgProfit = total / 12

      console.log(`${c.label}: yr=${total.toLocaleString()} avg=¥${avgProfit.toLocaleString()} maxFAT=${maxFAT}`)
      console.log(`  FAT: ${results.map(r => r.FAT).join(',')}`)
      console.log(`  B8:  ${results.map(r => r.B8.toLocaleString()).join(',')}`)

      expect(total).toBeGreaterThan(80000)
      expect(maxFAT).toBeLessThan(75)
    }, 10000)
  }

  it('社区路线有正期望 — 12个月不破产', () => {
    const { results } = simulate([26, 2, 400, 1500, 60, 3, 4, 4500])
    const posMonths = results.filter(r => r.B8 > 0).length
    expect(posMonths).toBeGreaterThan(6)
  })

  it('默认参数下不改任何变量FAT也会变化', () => {
    const { results } = simulate([18, 3, 100, 1000, 60, 3, 3, 4000])
    const fats = results.map(r => r.FAT)
    const allSame = fats.every(f => f === fats[0])
    expect(allSame).toBe(false)
  })

  it('增加人数降FAT — 高价控需求后差异明显', () => {
    // B1=26 控需求，这时产能差异才体现——人多的利用率更低
    const r3 = simulate([26, 3, 200, 1000, 60, 3, 3, 4000])
    const r5 = simulate([26, 5, 200, 1000, 60, 3, 3, 4000])
    const avg3 = r3.results.reduce((s, r) => s + r.FAT, 0) / 12
    const avg5 = r5.results.reduce((s, r) => s + r.FAT, 0) / 12
    const ur3 = r3.results.reduce((s, r) => s + r.ur, 0) / 12
    const ur5 = r5.results.reduce((s, r) => s + r.ur, 0) / 12
    console.log(`  3人 avgFAT=${avg3.toFixed(0)} UR=${ur3.toFixed(2)} vs 5人 avgFAT=${avg5.toFixed(0)} UR=${ur5.toFixed(2)}`)
    expect(avg5).toBeLessThanOrEqual(avg3)
  })
})
