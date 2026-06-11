/**
 * BRAND entangle 诊断测试
 * 检查 M1→BRAND useEntangle 是否被注册和触发
 * 运行: npx vitest run src/__tests__/debug-brand-entangle.test.ts
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

describe('BRAND entangle 诊断', () => {
  it('M1变化应触发BRAND增长', async () => {
    const engine = createSheetEngine()
    const eg = engine.raw as any

    // 注册 M1→BRAND entangle（和 BakerySandbox 里一样的逻辑）
    eg.config.useEntangle({
      cause: 'M1', impact: 'BRAND', via: ['value'],
      emit: (_cause: any, _impact: any, propose: any) => {
        const b21 = Number(eg.data.GetValue('B21', 'value')) || 0.8
        const b28 = Number(eg.data.GetValue('B28', 'value')) || 0.6
        const fat = Number(eg.data.GetValue('FAT', 'value')) || 40
        const b13 = Number(eg.data.GetValue('B13', 'value')) || 1000
        const b2 = Number(eg.data.GetValue('B2', 'value')) || 0
        const b3 = Number(eg.data.GetValue('B3', 'value')) || 0
        const cur = Number(eg.data.GetValue('BRAND', 'value')) || 0
        const sr = Math.max(0, (b2 - b3) / Math.max(1, b2))
        const growth = b21 * 10 + b28 * 12 + Math.max(0, (100 - fat) / 100) * 6
          + Math.sqrt(Math.max(0, b13)) * 0.15
        const decay = cur * 0.02
        const gm = Math.max(0.05, 1 - cur / 400)
        const nb = Math.max(0, Math.round(cur + growth * gm - decay - sr * 10))
        console.log(`[BRAND entangle] cur=${cur} b21=${b21} b28=${b28} fat=${fat} b13=${b13} growth=${growth.toFixed(1)} nb=${nb}`)
        propose.set('value', nb)
      },
    })

    // 初始化状态节点
    eg.data.SilentSet('FAT', 'value', 40)
    eg.data.SilentSet('B21', 'value', 0.8)
    eg.data.SilentSet('B28', 'value', 0.6)
    eg.data.SilentSet('B13', 'value', 1000)
    eg.data.SilentSet('B2', 'value', 0)
    eg.data.SilentSet('B3', 'value', 0)
    eg.data.SilentSet('BRAND', 'value', 0)
    eg.data.SilentSet('M1', 'value', 0)

    const brBefore = eg.data.GetValue('BRAND', 'value')
    console.log('BRAND before:', brBefore)

    // 模拟 nx(): SetValue M1 触发变化
    eg.data.SetValue('M1', 'value', 1)
    await new Promise(r => setTimeout(r, 200))

    const brAfter = eg.data.GetValue('BRAND', 'value')
    console.log('BRAND after:', brAfter)

    expect(brAfter).not.toBe(0)
    expect(brAfter).toBeGreaterThan(0)
  }, 10000)
})
