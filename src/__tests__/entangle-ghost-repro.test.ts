/**
 * 最小复现：entangle 的 ghost 提案是否被正确 resolve
 * 
 * 场景：A 变化时，entangle 提议 B = A + 1
 * 期望：notifyAll 后 B = A + 1
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

describe('Entangle ghost resolve 时序', () => {
  it('SetValue + notifyAll 后 ghost 提案应写入引擎', async () => {
    const engine = createSheetEngine()
    const raw = engine.raw as any
    const rd = (id: string) => Number(raw.data.GetValue(id, 'value')) || 0

    raw.config.useEntangle({
      cause: 'A6', impact: 'B6', via: ['value'],
      emit: (_src: any, _tgt: any, propose: any) => {
        const aVal = Number(raw.data.GetValue('A6', 'value')) || 0
        console.log('[ENTANGLE] A6→B6 fired, A=', aVal)
        propose.set('value', aVal + 1)
      }
    })

    raw.data.SilentSet('A6', 'value', 0)
    raw.data.SilentSet('B6', 'value', 999)

    raw.data.SetValue('A6', 'value', 5)

    await raw.config.notifyAll()
    await new Promise(r => setTimeout(r, 100))

    console.log('Test1: B6=', rd('B6'))
    expect(rd('B6')).toBe(6)
  })

  it('SilentSet + notifyAll 后 ghost 提案应写入引擎', async () => {
    const engine = createSheetEngine()
    const raw = engine.raw as any
    const rd = (id: string) => Number(raw.data.GetValue(id, 'value')) || 0

    raw.config.useEntangle({
      cause: 'A7', impact: 'B7', via: ['value'],
      emit: (_src: any, _tgt: any, propose: any) => {
        const aVal = Number(raw.data.GetValue('A7', 'value')) || 0
        console.log('[ENTANGLE] A7→B7 fired, A=', aVal)
        propose.set('value', aVal + 10)
      }
    })

    raw.data.SilentSet('A7', 'value', 3)
    raw.data.SilentSet('B7', 'value', 999)

    await raw.config.notifyAll()
    await new Promise(r => setTimeout(r, 100))

    console.log('Test2: B7=', rd('B7'))
    expect(rd('B7')).toBe(13)
  })

  it('SetValues 批量后 ghost 提案应写入引擎', async () => {
    const engine = createSheetEngine()
    const raw = engine.raw as any
    const rd = (id: string) => Number(raw.data.GetValue(id, 'value')) || 0

    raw.config.useEntangle({
      cause: 'A8', impact: 'B8', via: ['value'],
      emit: (_src: any, _tgt: any, propose: any) => {
        const aVal = Number(raw.data.GetValue('A8', 'value')) || 0
        console.log('[ENTANGLE] A8→B8 fired, A=', aVal)
        propose.set('value', aVal + 100)
      }
    })

    raw.data.SilentSet('A8', 'value', 0)
    raw.data.SilentSet('B8', 'value', 999)

    raw.data.SetValues([
      { path: 'A8', key: 'value', value: 7 },
      { path: 'C8', key: 'value', value: 42 },
    ])

    await raw.config.notifyAll()
    await new Promise(r => setTimeout(r, 100))

    console.log('Test3: B8=', rd('B8'))
    expect(rd('B8')).toBe(107)
  })

  it('面包店场景复现——同微任务: entangle注册后立即SetValues', async () => {
    const engine = createSheetEngine()
    const raw = engine.raw as any
    const rd = (id: string) => Number(raw.data.GetValue(id, 'value')) || 0

    // 注册 entangle — 同 setupBakeryRules
    raw.config.useEntangle({
      cause: 'M1', impact: 'B3', via: ['value'],
      emit: (_src: any, _tgt: any, propose: any) => {
        console.log('[ENTANGLE] M1→B3 fired')
        propose.set('value', 5250)
      }
    })

    // SilentSet 初值 — 同 writeSlider
    raw.data.SilentSet('M1', 'value', 0)
    raw.data.SilentSet('B3', 'value', 0)

    // 立即 SetValues — 同 reset (不包含 M1)
    // ⚠️ _updateEntangleLevel 的微任务还没跑！
    raw.data.SetValues([
      { path: 'FAT', key: 'value', value: 40 },
      { path: 'B3', key: 'value', value: 0 },
    ])

    // 模拟用户点击 — SetValues(M1) 触发 entangle
    // ⚠️ 没有 await，模拟在同一次事件循环里
    raw.data.SetValues([
      { path: 'M1', key: 'value', value: 1 },
    ])

    for (let r = 0; r < 3; r++) { await raw.config.notifyAll(); await new Promise(r2 => setTimeout(r2, 50)) }

    console.log('同微任务: B3=', rd('B3'))
    // 如果 B3=0 → _updateEntangleLevel 没跑, IS_ENTANGLEMENT_ENABLED=false, entangle 被 No-op
    expect(rd('B3')).toBe(5250)
  })
})
