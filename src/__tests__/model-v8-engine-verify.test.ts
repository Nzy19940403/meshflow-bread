/**
 * V8 引擎 ↔ Python 对照验证
 * 运行: npx vitest run src/__tests__/model-v8-engine-verify.test.ts
 *
 * 注意: JS Math.round(向上取半) 与 Python round(银行家舍入) 的差异
 * 会导致品牌累积链路出现 <1%/月 的微差。工厂和社区的 Δ 控制在 ¥100/月以内，
 * 高奢由于品牌对数叠加, Δ 控制在 ¥2,000/月以内。
 */
import { describe, it, expect } from 'vitest'

// ============================================================
// Python 参照值 (v8_verify.py)
// ============================================================

const PY: Record<string, number[]> = {
  comm24: [-9, 8719, 3914, 5912, 6171, 2907, 3126, 3310, 11287, 10787, 7420, 11913],
  fact18: [-3995, -453, -2466, -1687, -1611, -2964, -11699, -11690, -6218, -8253, -9612, -5512],
  lux34: [-8417, 13619, 7778, 14042, 16195, 10421, 10263, 11313, 34921, 29380, 23204, 37368],
  area60: [-9985, -4509, -7482, -6239, -6043, -8086, -7922, -7785, -2706, -3010, -5113, -2254],
}

const PARAMS: Record<string, [number,number,number,number,number,number,number,number]> = {
  comm24: [24,2,0,2000,60,4,4,4500],
  fact18: [18,7,100,0,200,2,2,3500],
  lux34: [34,2,300,2500,90,9,5,5500],
  area60: [18,3,100,1000,60,3,3,4000],
}

// 哪个路线需要宽松容差（品牌对数累积）
const LOOSE_TOLERANCE = new Set(['lux34'])

// ============================================================
// TypeScript 仿真 — 完全镜像引擎 BakerySandbox.vue setupBakeryRules
// ============================================================

function sk(fat: number): number {
  if (fat < 80) return 1.0
  if (fat >= 100) return 0.1
  const t = (fat - 80) / 20
  return 1.0 - t * t * (3.0 - 2.0 * t) * 0.9
}

const SZ = [0.85, 1.10, 0.95, 1.00, 1.00, 0.90, 0.85, 0.85, 1.25, 1.10, 1.00, 1.30]

function dynParams(g: number, a: number) {
  const gf = Math.max(0, Math.min(1, (g - 2) / 7))
  const lf = Math.max(0, Math.min(1, (g - 6) / 4)) * Math.max(0, Math.min(1, (120 - a) / 40))
  const ff = Math.max(0, Math.min(1, (a - 100) / 50)) * Math.max(0, Math.min(1, (5 - g) / 3))
  const cf = Math.max(0, Math.min(1, 1 - ff - lf))
  return {
    cv_b: 0.75 * cf + 0.70 * ff + 0.60 * lf,
    pb_mi: Math.round(22 * cf + 20 * ff + 30 * lf),
    pb_s: 0.03 * cf + 0.02 * ff + 0.01 * lf,
    pb_fl: 0.40 * cf + 0.40 * ff + 0.60 * lf,
    cv_s: 0.80 * cf + 0.80 * ff + 0.60 * lf,
    pr: 0.04 * cf + 0.06 * ff + 0.12 * lf,
    eq: Math.round(1200 * cf + 1200 * ff + 3000 * lf),
    rb: Math.round(22 * cf + 10 * ff + 18 * lf),
    rd: Math.round(2000 * cf + 800 * ff + 1500 * lf),
    ua: Math.round(18 * cf + 18 * ff + 22 * lf),
    us: Math.round(120 * cf + 120 * ff + 180 * lf),
    apm: Math.round(40 * cf + 45 * ff + 40 * lf),
    spm: Math.round(1800 * cf + 2000 * ff + 1800 * lf),
    bbp: 1200, bbpr: 0.25,
    frh: Math.round(30 * cf + 45 * ff + 35 * lf),
    ftr: Math.round(8 * cf + 15 * ff + 12 * lf),
    ful: 0.80 * cf + 0.70 * ff + 0.75 * lf,
    bp_c: Math.round(12 * cf + 12 * ff + 22 * lf),
    bp_cap: Math.round(45 * cf + 45 * ff + 60 * lf),
    bg1: Math.round(8 * cf + 8 * ff + 14 * lf),
    bg2: Math.round(10 * cf + 10 * ff + 18 * lf),
  }
}

function simulate(params: number[]) {
  const [B1, B24, B25, B13, B14, B15, B10, B26] = params
  let FAT = 40, EMP = 0, BR = 0, B21 = 0.8
  const profits: number[] = []
  const dp = dynParams(B15, B14)

  for (let m = 0; m < 12; m++) {
    const sz = SZ[m % 12]
    const physCap = Math.max(1, Math.min(B14 * dp.apm, B24 * dp.spm))
    const B3 = Math.max(0, Math.round(physCap * sk(FAT)))
    const wfB4 = 1.20 - 0.45 * Math.min(B26, 10000) / 10000
    const B4 = Math.round(Math.max(0.03, (1.5 - B3 * 0.00015) * wfB4 * (1 - EMP * 0.002)) * 100) / 100
    const qBase = Math.max(0.15, Math.min(0.95, B10 / 5.5))
    const qS = B26 > 3000 ? Math.min(0.18, (B26 - 3000) / 28000) : 0
    const B28 = Math.min(1.0, qBase + qS)
    let ft = (500 + 400 * Math.min(B15, 6))
    ft += Math.round(Math.sqrt(B14) * 15) + Math.round(Math.pow(B13, 0.45) * 0.8) + Math.round(BR * 0.8)
    if (B15 >= 3 && B15 <= 5 && B14 <= 90) ft = Math.round(ft * 1.15)
    const lb = Math.max(0, Math.round(ft))
    const bpVal = Math.round(Math.min(dp.bp_cap, Math.round(dp.bp_c * Math.log(1 + BR / 25) * Math.min(1, (B15 - 1) / 8))))
    const ma = Math.max(12 + B15 * 2.5, 12 + B15 * 2.5 + bpVal + B21 * 2 + B28 * 3 + B26 / 2500)
    const pf = (pr: number) => pr < 15 ? 1 + (15 - pr) * 0.10 : pr <= dp.pb_mi ? 1.0 : Math.max(dp.pb_fl, 1 - (pr - dp.pb_mi) * dp.pb_s)
    const pv = pf(B1), gap = Math.max(0, B1 - ma)
    let cv = dp.cv_b * pv * (ma / (ma + gap * dp.cv_s))
    cv = Math.min(0.85, Math.max(0.04, cv))
    const ls = BR >= 200 ? Math.min(sz, 1.08) : (BR >= 100 ? Math.min(sz, 1.12) : sz)
    const fs2 = Math.max(ls, BR >= 200 ? 0.95 : (BR >= 100 ? 0.90 : sz))
    const ld = Math.max(0, Math.round(lb * cv * fs2))
    let td = 0
    if (B15 >= 5) {
      const tb = (B15 - 4) * 500 * pv
      const tm = Math.round(Math.sqrt(Math.max(0, B13)) * 5) * (0.5 + BR / 400)
      const tt = Math.round(tb + tm)
      const tma = Math.max(8, 8 + B15 * 2 + B13 / 4000 + BR * 0.25)
      const tc = B1 <= tma ? Math.min(0.75, 0.30 + (tma - B1) / tma * 0.35) : Math.max(0.02, 0.25 * tma / B1)
      td = Math.max(0, Math.round(tt * tc * sz))
    }
    const B2 = ld + td, B6 = Math.min(B2, B3)
    let ws = 0, wr = 0
    if (B14 >= 150) {
      const rem = Math.max(0, B3 - B6)
      ws = Math.min(B24 * 1200 + Math.round((B14 - 150) * 500), rem)
      const qMult = B28 >= 0.6 ? 1.0 : B28 >= 0.4 ? 1.0 - (0.6 - B28) * 0.5 : 0.9 - (0.4 - B28) * 1.0
      wr = Math.round(ws * Math.min(B1, 22) * 0.25 * Math.max(0.5, qMult))
    }
    const B7 = B6 * B1 + wr
    const rate = dp.rb + dp.rd / (B14 + 15)
    const B5 = Math.max(0, Math.round(B14 * B15 * rate))
    const B9 = Math.round(B24 * B26 * (1 + B15 * 0.10 * Math.max(0, 1 - B24 * 0.05)))
    const B12 = Math.round(B10 * (1 - Math.min(0.4, B3 * 0.00006)) * 100) / 100
    const pkg = Math.round(B1 * dp.pr), util = Math.round(B14 * dp.ua + B24 * dp.us)
    const trn = B25 * B24, misc = Math.round(0.02 * B24 * 1000)
    const rc = Math.round((B12 + pkg + B4) * B6)
    const wc = ws > 0 ? Math.round(ws * B10 * 0.50 + ws * 0.3) : 0
    const B8 = Math.round(B7 - rc - wc - B5 - B9 - B13 - trn - misc - util - dp.eq)

    const ru = Math.min(1, B2 / Math.max(physCap, 1))
    const tu = Math.min(1, (B2 + ws) / Math.max(physCap, 1))
    let d = 0
    if (ru > 0.88) d = Math.round((ru - 0.88) * dp.frh)
    if (ru > 0.95) d += 2
    if (tu >= 0.90) d += 3
    else if (tu < dp.ful) d = -Math.round((dp.ful - tu) * 15)
    else if (ru < 0.75) d = -Math.round((0.75 - ru) * 5)
    if (tu > 0.65) d += Math.round((tu - 0.65) * dp.ftr)
    if (B14 > 150 && B24 < Math.ceil(B14 / 35)) d += 3
    const nF = Math.max(10, Math.min(100, Math.round(FAT + d)))
    const wageScore = Math.min(1, B26 / 5000)
    const pp = B9 / Math.max(B3, 1), bl = 2.5 + B15 * 0.3
    const effScore = pp >= bl ? 0.7 + Math.min((pp - bl) / (bl * 2), 0.25) : pp / bl * 0.7
    let nB = Math.min(1, Math.max(0, wageScore * 0.4 + effScore * 0.6))
    const ut = B3 / Math.max(physCap, 1)
    nB = Math.max(0.15, nB - Math.max(0, ut - 0.85) * 1)
    if (nF > 60) nB = Math.max(0.25, nB - (nF - 60) * 0.004)
    if (nF > 85) nB = Math.max(0.10, nB - (nF - 85) * 0.01)
    profits.push(B8)

    const sr2 = Math.max(0, (B2 - B3) / Math.max(1, B2))
    const gr = B21 * dp.bg1 + B28 * dp.bg2 + Math.max(0, (100 - FAT) / 100) * 5 + Math.sqrt(Math.max(0, B13)) * 0.12
    const dc = BR * 0.015
    const gm = Math.max(0.03, 1 - BR / 500)
    BR = Math.round(BR + gr * gm - dc - sr2 * 8)
    if (B28 < 0.4) {
      const g2 = 0.4 - B28
      BR = Math.max(0, BR - Math.round(g2 * 20))
      if (BR > (B28 >= 0.3 ? 50 : 25)) BR = B28 >= 0.3 ? 50 : 25
    }
    FAT = nF
    EMP = Math.min(200, Math.round(EMP + Math.max(1, 10 - Math.round(EMP * 0.05))))
    B21 = nB
  }
  return profits
}

// ============================================================
// Tests
// ============================================================

describe('V8 引擎 ↔ Python 逐月对照', () => {
  for (const name of Object.keys(PY)) {
    const ref = PY[name]
    const params = PARAMS[name]
    const isLoose = LOOSE_TOLERANCE.has(name)
    const maxDelta = isLoose ? 2000 : 100

    it(`${name} (maxΔ=¥${maxDelta}/月)`, () => {
      const r = simulate(params)

      for (let i = 0; i < 12; i++) {
        const delta = Math.abs(r[i] - ref[i])
        if (delta > maxDelta) {
          // Log all mismatches for debugging
          console.log(`M${i+1}: TS=${r[i]} PY=${ref[i]} Δ=${delta}`)
        }
        expect(delta, `M${i+1}: TS=${r[i]} PY=${ref[i]}`).toBeLessThanOrEqual(maxDelta)
      }

      const tTS = r.reduce((s, x) => s + x, 0)
      const tPY = ref.reduce((s, x) => s + x, 0)
      console.log(`${name}: TS=¥${tTS.toLocaleString()} PY=¥${tPY.toLocaleString()}`)
      expect(tTS).toBeGreaterThan(tPY - 5000)
      expect(tTS).toBeLessThan(tPY + 5000)
    })
  }
})
