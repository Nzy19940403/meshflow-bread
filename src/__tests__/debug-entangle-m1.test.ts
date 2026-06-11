/**
 * Debug: 检查 entangle M1 触发器是否正常工作
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT = 'FAT', EXP = 'EMP', BRAND = 'BRAND'

const sk = (c: number) => c < 80 ? 1 : c >= 100 ? 0.1 : 1 - ((t => t * t * (3 - 2 * t) * 0.9)((c - 80) / 20))
const wfFn = (b26: number) => 0.2 + 1.6 * Math.min(b26, 10000) / 10000
const physCapFn = (b14: number, b24: number, b26: number, b4: number) =>
  Math.max(1, Math.min(b14 * 35, b24 * 1500) * wfFn(b26) + Math.max(0, Math.round((2 - b4) * 100)))

function setupBakeryRules(eng: any) {
  const eg = eng.raw
  const gv = (path: string, fallback = 0) => {
    try { return eg.data.GetValue(path, 'value') ?? fallback } catch { return fallback }
  }

  // 简化：只注册 entangle，没有 SetRules
  // M1 → FAT
  eg.config.useEntangle({
    cause: 'M1', impact: FAT, via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const curFAT = gv(FAT, 40)
      const val = Math.max(10, Math.min(100, Math.round(curFAT + 5))) // 每月+5
      console.log(`[M1→FAT] curFAT=${curFAT} → propose=${val}`)
      propose.set('value', val)
    }
  })

  // M1 → BRAND
  eg.config.useEntangle({
    cause: 'M1', impact: BRAND, via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const cur = gv(BRAND, 0)
      const val = Math.round(cur + 10)
      console.log(`[M1→BRAND] cur=${cur} → propose=${val}`)
      propose.set('value', val)
    }
  })

  // M1 → EMP
  eg.config.useEntangle({
    cause: 'M1', impact: EXP, via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const cur = gv(EXP, 0)
      const val = Math.min(200, Math.round(cur + 1))
      console.log(`[M1→EMP] cur=${cur} → propose=${val}`)
      propose.set('value', val)
    }
  })
}

describe('Debug entangle M1 trigger', () => {
  it('M1变化应触发FAT/BRAND/EMP演进', async () => {
    const engine = createSheetEngine()
    setupBakeryRules(engine)
    const eg = engine.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    // 初始化
    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([
      { path: FAT, key: 'value', value: 40 },
      { path: BRAND, key: 'value', value: 0 },
      { path: EXP, key: 'value', value: 0 },
    ])

    console.log('\n=== 初始 notifyAll ===')
    for (let r = 0; r < 3; r++) {
      console.log(`\n--- Round ${r} ---`)
      await eg.config.notifyAll()
      await new Promise(r2 => setTimeout(r2, 50))
      console.log(`  FAT=${rd(FAT)} BRAND=${rd(BRAND)} EMP=${rd(EXP)}`)
    }

    console.log('\n=== 推 M1=1 ===')
    eg.data.SetValues([{ path: 'M1', key: 'value', value: 1 }])
    console.log(`  SetValues后 M1=${rd('M1')}`)
    for (let r = 0; r < 3; r++) {
      console.log(`\n--- Round ${r} ---`)
      await eg.config.notifyAll()
      await new Promise(r2 => setTimeout(r2, 50))
      console.log(`  FAT=${rd(FAT)} BRAND=${rd(BRAND)} EMP=${rd(EXP)}`)
    }

    console.log('\n=== 推 M1=2 ===')
    eg.data.SetValues([{ path: 'M1', key: 'value', value: 2 }])
    for (let r = 0; r < 3; r++) {
      console.log(`\n--- Round ${r} ---`)
      await eg.config.notifyAll()
      await new Promise(r2 => setTimeout(r2, 50))
      console.log(`  FAT=${rd(FAT)} BRAND=${rd(BRAND)} EMP=${rd(EXP)}`)
    }

    // 验证演进是否发生
    console.log(`\n最终: FAT=${rd(FAT)} (应>40), BRAND=${rd(BRAND)} (应>0), EMP=${rd(EXP)} (应>0)`)
    expect(rd(FAT)).toBeGreaterThan(40)
    expect(rd(BRAND)).toBeGreaterThan(0)
    expect(rd(EXP)).toBeGreaterThan(0)
  }, 30000)
})
