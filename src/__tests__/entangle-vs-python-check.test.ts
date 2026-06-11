/**
 * 对比: entangle 系统 vs Python V5.8 参考数据
 * 用来发现公式差异
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT='FAT', EXP='EMP', BRAND='BRAND'

const r2 = (x: number) => Math.round(x * 100) / 100

const sk = (c: number) => c < 80 ? 1 : c >= 100 ? 0.1 : 1 - ((t => t * t * (3 - 2 * t) * 0.9)((c - 80) / 20))
const wfFn = (b26: number) => 0.2 + 1.6 * Math.min(b26, 10000) / 10000
const physCapFn = (b14: number, b24: number, b26: number, b4: number) =>
  Math.max(1, Math.min(b14 * 35, b24 * 1500) * wfFn(b26) + Math.max(0, Math.round((2 - b4) * 100)))

// ===== 精确复制 BakerySandbox.vue 的 setupBakeryRules =====
function setupBakeryRules(eng: any) {
  const eg = eng.raw

  eg.config.SetRules(['B24', 'B26', 'B15'], 'B9', 'value', {
    triggerKeys: ['value', 'value', 'value'],
    logic: ({ slot }: any) => {
      const h = slot.triggerTargets[0]?.value ?? 8, w = slot.triggerTargets[1]?.value ?? 5000
      const g = slot.triggerTargets[2]?.value ?? 7
      return Math.round(h * w * (1 + g * 0.15 * Math.max(0, 1 - h * 0.08)))
    }
  })

  eg.config.SetRules(['B14', 'B15'], 'B5', 'value', {
    triggerKeys: ['value', 'value'],
    logic: ({ slot }: any) => {
      const a = slot.triggerTargets[0]?.value ?? 150, g = slot.triggerTargets[1]?.value ?? 7
      return Math.max(0, Math.round(a * g * Math.max(8, 45 - a * 0.10)))
    }
  })

  eg.config.SetRules(['B10', 'B3'], 'B12', 'value', {
    triggerKeys: ['value', 'value'],
    logic: ({ slot }: any) => {
      const b10 = slot.triggerTargets[0]?.value ?? 3, b3 = slot.triggerTargets[1]?.value ?? 1000
      return Math.round(b10 * (1 - Math.min(0.5, b3 * 0.00008)) * 100) / 100
    }
  })

  eg.config.SetRules(['B1', 'B15', 'B13', BRAND, 'B21', 'B26', 'B14'], 'B2', 'value', {
    triggerKeys: ['value', 'value', 'value', 'value', 'value', 'value', 'value'],
    logic: ({ slot }: any) => {
      const b1 = slot.triggerTargets[0]?.value ?? 16, g = slot.triggerTargets[1]?.value ?? 7
      const mkt = slot.triggerTargets[2]?.value ?? 0, brand = slot.triggerTargets[3]?.value ?? 0
      const b21 = slot.triggerTargets[4]?.value ?? 0.8, b26 = slot.triggerTargets[5]?.value ?? 5000
      const b14 = slot.triggerTargets[6]?.value ?? 150
      const bC = Math.round(brand * 3), bP = brand > 300 ? 0 : brand > 100 ? 1 - (brand - 100) / 200 : 1
      const pbF = b1 < 20 ? 1 + (20 - b1) * 0.15 : Math.max(0.6, 1 - (b1 - 20) * 0.03)
      const base = Math.round((500 + 500 * g) * pbF) + Math.round(bC * bP)
      const mktTr = Math.round(Math.sqrt(Math.max(0, mkt)) * 10) * (1 + b14 / 100)
      const qpV = Math.max(0, (b26 - 4000) / 500)
      const ma = Math.max(1, 15 + g * 2 + brand * 0.5 + b21 * 3 + qpV)
      const conv = b1 <= ma ? Math.min(0.9, 0.5 + (ma - b1) / ma * 0.4) : Math.max(0.05, 0.5 * ma / b1)
      return Math.max(0, Math.round((base + mktTr) * conv))
    }
  })

  eg.config.SetRules(['B2', 'B3'], 'B6', 'value', {
    triggerKeys: ['value', 'value'],
    logic: ({ slot }: any) => Math.min(slot.triggerTargets[0]?.value ?? 0, slot.triggerTargets[1]?.value ?? 0)
  })

  eg.config.SetRules(['B6', 'B1'], 'B7', 'value', {
    triggerKeys: ['value', 'value'],
    logic: ({ slot }: any) => {
      const b6 = slot.triggerTargets[0]?.value ?? 0, b1 = slot.triggerTargets[1]?.value ?? 16
      return b6 * b1 + Math.round(b6 * b1 * 0.20)
    }
  })

  eg.config.SetRules(['B7', 'B12', 'B1', 'B4', 'B3', 'B5', 'B9', 'B24', 'B25', 'B13', 'B14'], 'B8', 'value', {
    triggerKeys: ['value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value'],
    logic: ({ slot }: any) => {
      const b7 = slot.triggerTargets[0]?.value ?? 0, b12 = slot.triggerTargets[1]?.value ?? 0
      const b1 = slot.triggerTargets[2]?.value ?? 16, b4 = slot.triggerTargets[3]?.value ?? 0
      const b3 = slot.triggerTargets[4]?.value ?? 0, b5 = slot.triggerTargets[5]?.value ?? 0
      const b9 = slot.triggerTargets[6]?.value ?? 0, b24 = slot.triggerTargets[7]?.value ?? 8
      const b25 = slot.triggerTargets[8]?.value ?? 100, b13 = slot.triggerTargets[9]?.value ?? 0
      const b14 = slot.triggerTargets[10]?.value ?? 150
      const pkg = Math.round(b1 * 0.15), utilCost = Math.round(b14 * 25 + b24 * 200), eq = 2000
      const trn = b25 * b24, misc = Math.round(0.05 * b24 * 1500)
      const cogs = Math.round((b12 + pkg + b4) * b3)
      return Math.round(b7 - cogs - b5 - b9 - b13 - trn - misc - utilCost - eq)
    }
  })

  const gv = (path: string, fallback = 0) => {
    try { return eg.data.GetValue(path, 'value') ?? fallback } catch { return fallback }
  }

  // 1. B3 → B4
  eg.config.useEntangle({
    cause: 'B3', impact: 'B4', via: ['value'],
    emit: (cause: any, _impact: any, propose: any) => {
      const b3 = cause.state?.value ?? 0
      const emp = gv('EMP', 0), b26 = gv('B26', 5000)
      const wF = Math.max(0.5, 1.5 - b26 / 5000)
      const b4 = Math.max(0.1, Math.max(0.1, 2 - b3 * 0.0002) * (1 - emp * 0.002) * wF)
      propose.set('value', Math.round(b4 * 100) / 100)
    }
  })

  // 2. B4 → B3
  eg.config.useEntangle({
    cause: 'B4', impact: 'B3', via: ['value'],
    emit: (cause: any, _impact: any, propose: any) => {
      const b4 = cause.state?.value ?? 2
      const b14 = gv('B14', 150), b24 = gv('B24', 8), b26 = gv('B26', 5000), fat = gv('FAT', 40)
      const pc = physCapFn(b14, b24, b26, b4)
      propose.set('value', Math.max(0, Math.round(pc * sk(fat))))
    }
  })

  // 3. B3 → B21
  eg.config.useEntangle({
    cause: 'B3', impact: 'B21', via: ['value'],
    emit: (cause: any, _impact: any, propose: any) => {
      const b3 = cause.state?.value ?? 0
      const b4 = gv('B4', 2), b9 = gv('B9', 0), b15 = gv('B15', 7)
      const b14 = gv('B14', 150), b24 = gv('B24', 8), b26 = gv('B26', 5000)
      const pc = physCapFn(b14, b24, b26, b4)
      const pp = b9 / Math.max(b3, 1)
      const bl = 3 + b15 * 0.4
      const ps = pp >= bl ? 0.7 + Math.min((pp - bl) / (bl * 2), 0.3) : pp / bl * 0.7
      const util = b3 / Math.max(pc, 1)
      const ov = Math.max(0, util - (0.8 + 0.2 * ps)) * 1.5
      const b21 = Math.round(Math.min(1, Math.max(0, ps - ov)) * 1000) / 1000
      propose.set('value', b21)
    }
  })

  // 4. FAT → B3
  eg.config.useEntangle({
    cause: 'FAT', impact: 'B3', via: ['value'],
    emit: (cause: any, _impact: any, propose: any) => {
      const fat = cause.state?.value ?? 40
      const b4 = gv('B4', 2), b14 = gv('B14', 150), b24 = gv('B24', 8), b26 = gv('B26', 5000)
      const cap = Math.max(0, Math.round(physCapFn(b14, b24, b26, b4) * sk(fat)))
      propose.set('value', cap)
    }
  })

  // 5. M1 → B3 (SetRule seed)
  eg.config.SetRule('M1', 'B3', 'value', {
    triggerKeys: ['value'],
    logic: () => {
      const fat = Number(eg.data.GetValue('FAT', 'value')) || 40
      const b4 = Number(eg.data.GetValue('B4', 'value')) || 2
      const b14 = Number(eg.data.GetValue('B14', 'value')) || 150
      const b24 = Number(eg.data.GetValue('B24', 'value')) || 8
      const b26 = Number(eg.data.GetValue('B26', 'value')) || 5000
      return Math.max(0, Math.round(physCapFn(b14, b24, b26, b4) * sk(fat)))
    }
  })

  // 6. M1 → FAT
  eg.config.useEntangle({
    cause: 'M1', impact: 'FAT', via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const curFAT = gv('FAT', 40), b14 = gv('B14', 150), b24 = gv('B24', 8)
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
    }
  })

  // 7. M1 → BRAND — V5.9 entangle formula
  eg.config.useEntangle({
    cause: 'M1', impact: BRAND, via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const cur = gv(BRAND, 0), b2 = gv('B2', 0), b3 = gv('B3', 0), b21 = gv('B21', 0.8)
      const sr = Math.max(0, (b2 - b3) / Math.max(1, b2))
      const growth = b21 * 20
      const decay = cur * 0.02
      const gm = Math.max(0.05, 1 - cur / 400)
      propose.set('value', Math.max(0, Math.round(cur + growth * gm - decay - sr * 10)))
    }
  })

  // 8. M1 → EMP
  eg.config.useEntangle({
    cause: 'M1', impact: EXP, via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const cur = gv(EXP, 0)
      propose.set('value', Math.min(200, Math.round(cur + Math.max(1, 10 - Math.round(cur * 0.05)))))
    }
  })
}

// ===== V5.8 预期数据 (Python) =====
const PY: Record<string, number[]> = {
  '✨ 高奢·精兵': [12456, 27936, 32553, 32453, 32553, 32520, 32621, 32544, 32655, 32621, 32766, 32689],
  '🏭 大厂·标准': [-6440, -3854, -3757, -3690, -3622, -3607, -3553, -3485, -3471, -3417, -3349, -3336],
  '🏠 社区·基本': [-7520, -6410, -6338, -6258, -6186, -6124, -6082, -6033, -5953, -5911, -5861, -5818],
}

const SCENARIOS = [
  { label: '✨ 高奢·精兵', B1: 28, B24: 3, B25: 500, B13: 6000, B14: 120, B15: 9, B10: 8, B26: 5000 },
  { label: '🏭 大厂·标准', B1: 16, B24: 8, B25: 100, B13: 2000, B14: 150, B15: 7, B10: 5, B26: 5000 },
  { label: '🏠 社区·基本', B1: 16, B24: 3, B25: 0, B13: 0, B14: 60, B15: 5, B10: 5, B26: 4000 },
]

describe('Entangle vs Python V5.8 — FIND DIFFS', () => {
  for (const s of SCENARIOS) {
    it(`${s.label}: 逐月利润对比`, async () => {
      const engine = createSheetEngine()
      setupBakeryRules(engine)
      const eg = engine.raw as any, rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

      // === 初始化 (同 BakerySandbox.vue reset()) ===
      eg.data.SilentSet('M1', 'value', 0)
      eg.data.SetValues([
        { path: FAT, key: 'value', value: 40 },
        { path: EXP, key: 'value', value: 0 },
        { path: BRAND, key: 'value', value: 0 },
        { path: 'B21', key: 'value', value: 0.8 },
        { path: 'B1', key: 'value', value: s.B1 },
        { path: 'B24', key: 'value', value: s.B24 },
        { path: 'B25', key: 'value', value: s.B25 },
        { path: 'B13', key: 'value', value: s.B13 },
        { path: 'B14', key: 'value', value: s.B14 },
        { path: 'B10', key: 'value', value: s.B10 },
        { path: 'B26', key: 'value', value: s.B26 },
        { path: 'B15', key: 'value', value: s.B15 },
        { path: 'B3', key: 'value', value: 0 },
        { path: 'P1', key: 'value', value: 0 },
        { path: 'T1', key: 'value', value: 0 },
      ])

      // 初始收敛
      for (let r = 0; r < 3; r++) { await eg.config.notifyAll(); await new Promise(r2 => setTimeout(r2, 50)) }

      const profits: number[] = []
      for (let m = 1; m <= 12; m++) {
        // 推月份
        eg.data.SetValues([{ path: 'M1', key: 'value', value: m }])
        for (let r = 0; r < 3; r++) { await eg.config.notifyAll(); await new Promise(r2 => setTimeout(r2, 50)) }

        const b8 = rd('B8')
        profits.push(b8)

        // 打印中间变量
        const b2 = rd('B2'), b3 = rd('B3'), b4 = rd('B4'), b6 = rd('B6')
        const b21 = rd('B21'), fat = rd(FAT), brand = rd(BRAND), emp = rd(EXP)
        console.log(`  月${m}: B8=${b8} B3=${b3} B4=${b4.toFixed(3)} B6=${b6} B21=${b21.toFixed(3)} FAT=${fat} BRAND=${brand} EMP=${emp}`)
      }

      const exp = PY[s.label]
      console.log(`\n  [对比 Python V5.8]`)
      let maxD = 0
      for (let i = 0; i < 12; i++) {
        const d = Math.abs(profits[i] - exp[i])
        maxD = Math.max(maxD, d)
        console.log(`  月${i + 1}: 引擎=${profits[i]}  Python=${exp[i]}  差=${d}  ${d > 50 ? '⚠️' : '✅'}`)
      }
      console.log(`  最大偏差: ${maxD}`)

      // 故意不 assert，只是记录
      expect(true).toBe(true)
    }, 60000)
  }
})
