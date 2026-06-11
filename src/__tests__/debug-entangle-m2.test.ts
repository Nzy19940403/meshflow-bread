/**
 * Debug: 检查完整 setupBakeryRules 下 M1 entangle 是否触发
 * 简化版正常工作 → 加 SetRules 后失效？
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT = 'FAT', EXP = 'EMP', BRAND = 'BRAND'

const sk = (c: number) => c < 80 ? 1 : c >= 100 ? 0.1 : 1 - ((t => t * t * (3 - 2 * t) * 0.9)((c - 80) / 20))
const wfFn = (b26: number) => 0.2 + 1.6 * Math.min(b26, 10000) / 10000
const physCapFn = (b14: number, b24: number, b26: number, b4: number) =>
  Math.max(1, Math.min(b14 * 35, b24 * 1500) * wfFn(b26) + Math.max(0, Math.round((2 - b4) * 100)))

function setupFull(eng: any) {
  const eg = eng.raw
  const gv = (path: string, fallback = 0) => {
    try { return eg.data.GetValue(path, 'value') ?? fallback } catch { return fallback }
  }

  // SetRules (单向)
  eg.config.SetRules(['B24', 'B26', 'B15'], 'B9', 'value', {
    triggerKeys: ['value', 'value', 'value'],
    logic: ({ slot }: any) => {
      const h = slot.triggerTargets[0]?.value ?? 8, w = slot.triggerTargets[1]?.value ?? 5000, g = slot.triggerTargets[2]?.value ?? 7
      return Math.round(h * w * (1 + g * 0.15 * Math.max(0, 1 - h * 0.08)))
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

  // Entangle
  eg.config.useEntangle({
    cause: 'M1', impact: FAT, via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const curFAT = gv(FAT, 40)
      const val = Math.max(10, Math.min(100, Math.round(curFAT + 5)))
      console.log(`[M1→FAT] curFAT=${curFAT} → propose=${val}`)
      propose.set('value', val)
    }
  })

  eg.config.useEntangle({
    cause: 'M1', impact: BRAND, via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const cur = gv(BRAND, 0)
      const val = Math.round(cur + 10)
      console.log(`[M1→BRAND] cur=${cur} → propose=${val}`)
      propose.set('value', val)
    }
  })

  eg.config.useEntangle({
    cause: 'M1', impact: EXP, via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const cur = gv(EXP, 0)
      const val = Math.min(200, Math.round(cur + 1))
      console.log(`[M1→EMP] cur=${cur} → propose=${val}`)
      propose.set('value', val)
    }
  })

  // SetRule M1→B3 — 看这个会不会触发
  eg.config.SetRule('M1', 'B3', 'value', {
    triggerKeys: ['value'],
    logic: () => {
      const b14 = Number(eg.data.GetValue('B14', 'value')) || 150
      const b24 = Number(eg.data.GetValue('B24', 'value')) || 8
      const b26 = Number(eg.data.GetValue('B26', 'value')) || 5000
      const b4 = Number(eg.data.GetValue('B4', 'value')) || 2
      const fat = Number(eg.data.GetValue(FAT, 'value')) || 40
      const val = Math.max(0, Math.round(physCapFn(b14, b24, b26, b4) * sk(fat)))
      console.log(`[SetRule M1→B3] → ${val}`)
      return val
    }
  })
}

// 跟 BakerySandbox.vue reset() 一致的初始化
function initEngine(eg: any, p: any) {
  eg.data.SilentSet('M1', 'value', 0)
  eg.data.SetValues([
    { path: FAT, key: 'value', value: 40 },
    { path: EXP, key: 'value', value: 0 },
    { path: BRAND, key: 'value', value: 0 },
    { path: 'B21', key: 'value', value: 0.8 },
    { path: 'B1', key: 'value', value: p.B1 },
    { path: 'B24', key: 'value', value: p.B24 },
    { path: 'B25', key: 'value', value: p.B25 },
    { path: 'B13', key: 'value', value: p.B13 },
    { path: 'B14', key: 'value', value: p.B14 },
    { path: 'B10', key: 'value', value: p.B10 },
    { path: 'B26', key: 'value', value: p.B26 },
    { path: 'B15', key: 'value', value: p.B15 },
    { path: 'B3', key: 'value', value: 0 },
    { path: 'P1', key: 'value', value: 0 },
    { path: 'T1', key: 'value', value: 0 },
  ])
}

describe('Debug: SetRules 会不会阻塞 entangle 触发？', () => {
  it('推 M1→B3 SetRule + M1→FAT/BRAND/EMP entangle 是否都触发？', async () => {
    const engine = createSheetEngine()
    setupFull(engine)
    const eg = engine.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    initEngine(eg, { B1: 16, B24: 8, B25: 100, B13: 2000, B14: 150, B15: 7, B10: 5, B26: 5000 })

    console.log('\n=== 初始收敛 ===')
    for (let r = 0; r < 3; r++) {
      console.log(`\n--- 初始 Round ${r} ---`)
      await eg.config.notifyAll()
      await new Promise(r2 => setTimeout(r2, 50))
      console.log(`  FAT=${rd(FAT)} BRAND=${rd(BRAND)} EMP=${rd(EXP)} B3=${rd('B3')} B2=${rd('B2')}`)
    }

    console.log('\n=== 推 M1=1 ===')
    eg.data.SetValues([{ path: 'M1', key: 'value', value: 1 }])
    console.log(`  SetValues后: M1=${rd('M1')}`)
    for (let r = 0; r < 3; r++) {
      console.log(`\n--- M1=1 Round ${r} ---`)
      await eg.config.notifyAll()
      await new Promise(r2 => setTimeout(r2, 50))
      console.log(`  FAT=${rd(FAT)} BRAND=${rd(BRAND)} EMP=${rd(EXP)} B3=${rd('B3')} B2=${rd('B2')}`)
    }

    console.log('\n=== 推 M1=2 ===')
    eg.data.SetValues([{ path: 'M1', key: 'value', value: 2 }])
    for (let r = 0; r < 3; r++) {
      console.log(`\n--- M1=2 Round ${r} ---`)
      await eg.config.notifyAll()
      await new Promise(r2 => setTimeout(r2, 50))
      console.log(`  FAT=${rd(FAT)} BRAND=${rd(BRAND)} EMP=${rd(EXP)} B3=${rd('B3')}`)
    }

    expect(rd(FAT)).toBeGreaterThan(40)
    expect(rd(BRAND)).toBeGreaterThan(0)
  }, 30000)
})
