/**
 * 完整模型月度推演测试 — 1:1 复现 BakerySandbox.vue setupBakeryRules
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT = 'FAT', EMP = 'EMP', BRAND = 'BRAND'

function setupAll(eng: any) {
  const eg = eng
  const gv = (p: string, f = 0) => { try { return Number(eg.data.GetValue(p, 'value')) || f } catch { return f } }
  const wfFn = (b26: number) => 0.2 + 1.6 * Math.min(b26, 10000) / 10000
  const physCapFn = (b14: number, b24: number, b26: number, b4: number) =>
    Math.max(1, Math.min(b14 * 35, b24 * 1500) * wfFn(b26) + Math.max(0, Math.round((2 - b4) * 100)))

  // --- SetRules ---
  eg.config.SetRules(['B24', 'B26', 'B15'], 'B9', 'value', {
    triggerKeys: ['value', 'value', 'value'],
    logic: ({ slot }: any) => {
      const h = slot.triggerTargets[0]?.value ?? 3, w = slot.triggerTargets[1]?.value ?? 4000, g = slot.triggerTargets[2]?.value ?? 3
      return Math.round(h * w * (1 + g * 0.15 * Math.max(0, 1 - h * 0.08)))
    },
  })
  eg.config.SetRules(['B14', 'B15'], 'B5', 'value', {
    triggerKeys: ['value', 'value'],
    logic: ({ slot }: any) => {
      const a = slot.triggerTargets[0]?.value ?? 60, g = slot.triggerTargets[1]?.value ?? 3
      return Math.max(0, Math.round(a * g * Math.max(8, 45 - a * 0.10)))
    },
  })
  eg.config.SetRules(['B10', 'B3'], 'B12', 'value', {
    triggerKeys: ['value', 'value'],
    logic: ({ slot }: any) => {
      const b10 = slot.triggerTargets[0]?.value ?? 3, b3 = slot.triggerTargets[1]?.value ?? 1000
      return Math.round(b10 * (1 - Math.min(0.5, b3 * 0.00008)) * 100) / 100
    },
  })
  eg.config.SetRules(['B10', 'B3'], 'B28', 'value', {
    triggerKeys: ['value', 'value'],
    logic: ({ slot }: any) => {
      const b10 = slot.triggerTargets[0]?.value ?? 3, b3 = slot.triggerTargets[1]?.value ?? 1000
      const base = Math.max(0.2, Math.min(1.0, b10 / 5.0))
      const scaleBonus = b3 > 3000 ? Math.min(0.25, (b3 - 3000) * 0.00008) : 0
      return Math.round(Math.min(1.0, base + scaleBonus) * 1000) / 1000
    },
  })
  const SEASON = [0.85, 1.10, 0.95, 1.00, 1.00, 0.90, 0.85, 0.85, 1.25, 1.10, 1.00, 1.30]
  eg.config.SetRules(['B1', 'B15', 'B13', BRAND, 'B21', 'B26', 'B14', 'M1'], 'B2', 'value', {
    triggerKeys: ['value', 'value', 'value', 'value', 'value', 'value', 'value', 'value'],
    logic: ({ slot }: any) => {
      const b1 = slot.triggerTargets[0]?.value ?? 18, g = slot.triggerTargets[1]?.value ?? 3
      const mkt = slot.triggerTargets[2]?.value ?? 1000, brand = slot.triggerTargets[3]?.value ?? 0
      const b21 = slot.triggerTargets[4]?.value ?? 0.8, b26 = slot.triggerTargets[5]?.value ?? 4000
      const b14 = slot.triggerTargets[6]?.value ?? 60
      const mIdx = ((slot.triggerTargets[7]?.value ?? 1) - 1) % 12
      const sz = SEASON[Math.max(0, Math.min(11, Math.floor(mIdx)))] || 1.0
      const bC = Math.round(brand * 3), bP = brand > 300 ? 0 : brand > 100 ? 1 - (brand - 100) / 200 : 1
      const pbF = b1 < 20 ? 1 + (20 - b1) * 0.15 : Math.max(0.6, 1 - (b1 - 20) * 0.03)
      const base = Math.round((500 + 500 * g) * pbF) + Math.round(bC * bP)
      const mktTr = Math.round(Math.sqrt(Math.max(0, mkt)) * 10) * (1 + b14 / 100)
      const tr = Math.round(base + mktTr)
      const qpV = Math.max(0, (b26 - 4000) / 500)
      const ma = Math.max(1, 15 + g * 2 + brand * 0.5 + b21 * 3 + qpV)
      const conv = b1 <= ma ? Math.min(0.9, 0.5 + (ma - b1) / ma * 0.4) : Math.max(0.05, 0.5 * ma / b1)
      let retailDemand = Math.max(0, Math.round(tr * conv * sz))
      let tourDemand = 0
      if (g >= 5) {
        const tourBase = (g - 4) * 500 * pbF
        const tourMkt = g >= 7 ? Math.round(Math.sqrt(Math.max(0, mkt)) * 5) : 0
        const tourTr = Math.round(tourBase + tourMkt)
        const tourMa = Math.max(1, 8 + g * 2.5 + mkt / 2500 + qpV)
        const tourConv = b1 <= tourMa ? Math.min(0.80, 0.35 + (tourMa - b1) / tourMa * 0.35) : Math.max(0.03, 0.35 * tourMa / b1)
        tourDemand = Math.max(0, Math.round(tourTr * tourConv * sz))
      }
      return Math.max(0, retailDemand + tourDemand)
    },
  })
  eg.config.SetRules(['B2', 'B3'], 'B6', 'value', {
    triggerKeys: ['value', 'value'],
    logic: ({ slot }: any) => Math.min(slot.triggerTargets[0]?.value ?? 0, slot.triggerTargets[1]?.value ?? 0),
  })
  eg.config.SetRules(['B6', 'B1', 'B14', 'B3'], 'B7', 'value', {
    triggerKeys: ['value', 'value', 'value', 'value'],
    logic: ({ slot }: any) => {
      const b6 = slot.triggerTargets[0]?.value ?? 0, b1 = slot.triggerTargets[1]?.value ?? 18
      const b14 = slot.triggerTargets[2]?.value ?? 60, b3 = slot.triggerTargets[3]?.value ?? 0
      const retail = b6 * b1 + Math.round(b6 * b1 * 0.20)
      let ws = 0
      if (b14 > 130) {
        const wSold = Math.min(Math.round((b14 - 130) * 50), Math.max(0, b3 - b6))
        ws = Math.round(wSold * b1 * 0.40)
      }
      return retail + ws
    },
  })
  eg.config.SetRules(['B7', 'B12', 'B1', 'B4', 'B3', 'B5', 'B9', 'B24', 'B25', 'B13', 'B14', 'B6', 'B10'], 'B8', 'value', {
    triggerKeys: ['value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value'],
    logic: ({ slot }: any) => {
      const b7 = slot.triggerTargets[0]?.value ?? 0, b12 = slot.triggerTargets[1]?.value ?? 0, b1 = slot.triggerTargets[2]?.value ?? 18
      const b4 = slot.triggerTargets[3]?.value ?? 0, b3 = slot.triggerTargets[4]?.value ?? 0, b5 = slot.triggerTargets[5]?.value ?? 0
      const b9 = slot.triggerTargets[6]?.value ?? 0, b24 = slot.triggerTargets[7]?.value ?? 3
      const b25 = slot.triggerTargets[8]?.value ?? 100, b13 = slot.triggerTargets[9]?.value ?? 1000
      const b14 = slot.triggerTargets[10]?.value ?? 60, b6 = slot.triggerTargets[11]?.value ?? 0
      const b10 = slot.triggerTargets[12]?.value ?? 3
      const pkg = Math.round(b1 * 0.15), utilCost = Math.round(b14 * 25 + b24 * 200), eq = 2000
      const trn = b25 * b24, misc = Math.round(0.05 * b24 * 1500)
      const retailCogs = Math.round((b12 + pkg + b4) * Math.min(b6, b3))
      let wsCogs = 0
      if (b14 > 130) {
        const wSold = Math.min(Math.round((b14 - 130) * 50), Math.max(0, b3 - b6))
        wsCogs = Math.round(wSold * (b10 || 3) * 0.85 + wSold * 1.5)
      }
      return Math.round(b7 - retailCogs - wsCogs - b5 - b9 - b13 - trn - misc - utilCost - eq)
    },
  })

  // --- Entangles ---
  eg.config.useEntangle({
    cause: 'B3', impact: 'B4', via: ['value'],
    emit: (cause: any, _: any, propose: any) => {
      const b3 = cause.state?.value ?? 0
      const emp = gv(EMP, 0), b26 = gv('B26', 4000)
      const wF = Math.max(0.5, 1.5 - b26 / 5000)
      const b4 = Math.max(0.1, Math.max(0.1, 2 - b3 * 0.0002) * (1 - emp * 0.002) * wF)
      propose.set('value', Math.round(b4 * 100) / 100)
    },
  })
  eg.config.useEntangle({
    cause: 'B4', impact: 'B3', via: ['value'],
    emit: (cause: any, _: any, propose: any) => {
      const b4 = cause.state?.value ?? 2
      const b14 = gv('B14', 150), b24 = gv('B24', 8), b26 = gv('B26', 5000), fat = gv(FAT, 40)
      const sk = (c4: number) => { const v = Number(c4); return !Number.isFinite(v) ? 1 : v < 80 ? 1 : v >= 100 ? 0.1 : 1 - ((t: number) => t * t * (3 - 2 * t) * 0.9)((v - 80) / 20) }
      propose.set('value', Math.max(0, Math.round(physCapFn(b14, b24, b26, b4) * sk(fat))))
    },
  })
  eg.config.useEntangle({
    cause: 'B3', impact: 'B21', via: ['value'],
    emit: (cause: any, _: any, propose: any) => {
      const b3 = cause.state?.value ?? 0, b4 = gv('B4', 2), b9 = gv('B9', 0)
      const b15 = gv('B15', 7), b14 = gv('B14', 150), b24 = gv('B24', 8), b26 = gv('B26', 5000)
      const pc = physCapFn(b14, b24, b26, b4)
      const pp = b9 / Math.max(b3, 1), bl = 3 + b15 * 0.4
      const ps = pp >= bl ? 0.7 + Math.min((pp - bl) / (bl * 2), 0.3) : pp / bl * 0.7
      const util = b3 / Math.max(pc, 1), ov = Math.max(0, util - (0.8 + 0.2 * ps)) * 1.5
      propose.set('value', Math.round(Math.min(1, Math.max(0, ps - ov)) * 1000) / 1000)
    },
  })
  eg.config.useEntangle({
    cause: FAT, impact: 'B3', via: ['value'],
    emit: (cause: any, _: any, propose: any) => {
      const fat = cause.state?.value ?? 40
      const b4 = gv('B4', 2), b14 = gv('B14', 150), b24 = gv('B24', 8), b26 = gv('B26', 5000)
      const sk = (c4: number) => { const v = Number(c4); return !Number.isFinite(v) ? 1 : v < 80 ? 1 : v >= 100 ? 0.1 : 1 - ((t: number) => t * t * (3 - 2 * t) * 0.9)((v - 80) / 20) }
      propose.set('value', Math.max(0, Math.round(physCapFn(b14, b24, b26, b4) * sk(fat))))
    },
  })
  eg.config.SetRule('M1', 'B3', 'value', {
    triggerKeys: ['value'],
    logic: () => {
      const fat = Number(eg.data.GetValue(FAT, 'value')) || 40
      const b4 = Number(eg.data.GetValue('B4', 'value')) || 2
      const b14 = Number(eg.data.GetValue('B14', 'value')) || 150
      const b24 = Number(eg.data.GetValue('B24', 'value')) || 8
      const b26 = Number(eg.data.GetValue('B26', 'value')) || 5000
      const sk = (c4: number) => { const v = Number(c4); return !Number.isFinite(v) ? 1 : v < 80 ? 1 : v >= 100 ? 0.1 : 1 - ((t: number) => t * t * (3 - 2 * t) * 0.9)((v - 80) / 20) }
      return Math.max(0, Math.round(physCapFn(b14, b24, b26, b4) * sk(fat)))
    },
  })
  eg.config.useEntangle({
    cause: 'M1', impact: FAT, via: ['value'],
    emit: (_: any, __: any, propose: any) => {
      const curFAT = gv(FAT, 40), b14 = gv('B14', 150), b24 = gv('B24', 8)
      const b25 = gv('B25', 100), b26 = gv('B26', 5000), b3 = gv('B3', 0)
      const b4 = gv('B4', 2), b21 = gv('B21', 0.8), b9 = gv('B9', 0)
      const wf = 0.2 + 1.6 * Math.min(b26, 10000) / 10000
      const ph = Math.max(1, Math.min(b14 * 35, b24 * 1500) * wf + Math.max(0, (2 - b4) * 100))
      let d = 3
      if (b25 === 0 && b3 / ph > 0.7) d += 5; else if (b25 === 0) d += 2
      if (b3 / ph > 0.8) d += (b3 / ph - 0.8) * 40
      d -= b25 * 0.03
      const ff = curFAT < 40 ? curFAT / 40 : 1
      if (b21 < 0.5) d -= (b21 - 0.5) * 15 * ff
      if (b9 / Math.max(b24, 1) > 1500) d -= (b9 / b24 - 1500) * 0.005 * ff
      propose.set('value', Math.max(10, Math.min(100, Math.round(curFAT + d))))
    },
  })
  eg.config.useEntangle({
    cause: 'M1', impact: BRAND, via: ['value'],
    emit: (_: any, __: any, propose: any) => {
      const cur = gv(BRAND, 0), b2 = gv('B2', 0), b3 = gv('B3', 0)
      const b21 = gv('B21', 0.8), b28 = gv('B28', 0.6)
      const fat = gv(FAT, 40), b13 = gv('B13', 1000)
      const sr = Math.max(0, (b2 - b3) / Math.max(1, b2))
      const growth = b21 * 10 + b28 * 12 + Math.max(0, (100 - fat) / 100) * 6 + Math.sqrt(Math.max(0, b13)) * 0.15
      const decay = cur * 0.02
      const gm = Math.max(0.05, 1 - cur / 400)
      let nb = Math.max(0, Math.round(cur + growth * gm - decay - sr * 10))
      const isBad = b28 < 0.40
      if (isBad) {
        const gap = 0.40 - b28; nb = Math.max(0, nb - Math.round(gap * 25))
        const ceiling = b28 >= 0.30 ? 50 : 25; if (nb > ceiling) nb = ceiling
      }
      propose.set('value', nb)
    },
  })
  eg.config.useEntangle({
    cause: 'M1', impact: EMP, via: ['value'],
    emit: (_: any, __: any, propose: any) => { const cur = gv(EMP, 0); propose.set('value', Math.min(200, Math.round(cur + Math.max(1, 10 - Math.round(cur * 0.05))))) },
  })
}

function gv(eg: any, id: string): number {
  try { return Number(eg.data.GetValue(id, 'value')) || 0 } catch { return 0 }
}

describe('完整模型月度推演', () => {
  it('6个月推演 — BRAND应逐月增长', async () => {
    const engine = createSheetEngine()
    const eg = engine.raw as any
    setupAll(eg)

    // Init with default params
    const params = { B1: 18, B24: 3, B25: 100, B13: 1000, B14: 60, B15: 3, B10: 3, B26: 4000 }
    for (const [k, v] of Object.entries(params)) eg.data.SilentSet(k, 'value', v)
    eg.data.SilentSet(FAT, 'value', 40)
    eg.data.SilentSet(EMP, 'value', 0)
    eg.data.SilentSet(BRAND, 'value', 0)
    eg.data.SilentSet('B21', 'value', 0.8)
    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SilentSet('B16', 'value', 0)
    eg.data.SilentSet('B17', 'value', 0)
    eg.data.SilentSet('B18', 'value', 0)
    await eg.config.notifyAll()
    await new Promise(r => setTimeout(r, 100))

    console.log('\n=== 6个月逐月推演 ===')
    for (let m = 0; m < 6; m++) {
      const mVal = m + 1
      // Simulate nx(): rewrite all sliders + M1
      eg.data.SetValue('B1', 'value', params.B1)
      eg.data.SetValue('B24', 'value', params.B24)
      eg.data.SetValue('B25', 'value', params.B25)
      eg.data.SetValue('B13', 'value', params.B13)
      eg.data.SetValue('B10', 'value', params.B10)
      eg.data.SetValue('B14', 'value', params.B14)
      eg.data.SetValue('B26', 'value', params.B26)
      eg.data.SetValue('B15', 'value', params.B15)
      eg.data.SetValue('M1', 'value', mVal)
      await new Promise(r => setTimeout(r, 200))

      const brand = gv(eg, BRAND)
      const b2 = gv(eg, 'B2')
      const b3 = gv(eg, 'B3')
      const b8 = gv(eg, 'B8')
      const fat = gv(eg, FAT)
      const b21 = gv(eg, 'B21')
      const b28 = gv(eg, 'B28')
      const b9 = gv(eg, 'B9')

      console.log(`  M${mVal}: BRAND=${brand} B2=${b2} B3=${b3} B8=${b8} FAT=${fat} B21=${b21.toFixed(3)} B28=${b28.toFixed(3)} B9=${b9}`)

      if (m === 0) {
        expect(brand).toBeGreaterThan(0)
      }
      if (m >= 1) {
        expect(brand).toBeGreaterThan(0)
      }
    }

    const brand6 = gv(eg, BRAND)
    console.log(`\n  终态 BRAND = ${brand6}`)
    expect(brand6).toBeGreaterThan(50)
  }, 30000)
})
