/**
 * 终极排查: 绕过 notifyAll，模拟引擎内部的传播路径
 */
import { describe, it } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT = 'FAT'

describe('逐步排查: 究竟是哪步吃掉 ghost', () => {
  
  // 测试: SilentSet + notifyAll 触发 B3 公式传播后, ghost还在不在？
  it('Step 1: SilentSet M1 + notify + entangle', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    // 只有 entangle (没有 SetRule)
    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => {
        console.log('[emit] M1→FAT propose=45')
        p.set('value', 45)
      }
    })

    // 初始化
    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([
      {path: FAT, key: 'value', value: 40},
    ])
    await eg.config.notifyAll()
    await new Promise(r2 => setTimeout(r2, 50))

    // 用 SilentSet 写 M1 (不触发propagation)
    eg.data.SilentSet('M1', 'value', 1)
    console.log(`SilentSet后 M1=${rd('M1')} FAT=${rd('FAT')}`)

    // 手动 notify M1 — 这会触发 entangle
    eg.notify?.('M1', 'value')
    await new Promise(r2 => setTimeout(r2, 100))
    console.log(`notify后 FAT=${rd('FAT')} (应45)`)
  })

  // 测试: 先 notify, 再执行 setCellFormula 的公式
  it('Step 2: notify + 公式传播分开触发', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    // 注册 B3 公式 (M1→B3)
    e.setCellFormula('B3', '=M1*1000')

    // 注册 entangle M1→FAT
    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => {
        console.log('[emit] M1→FAT propose=45')
        p.set('value', 45)
      }
    })

    // 初始化
    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([
      {path: FAT, key: 'value', value: 40},
      {path: 'B3', key: 'value', value: 0},
    ])
    await eg.config.notifyAll()
    await new Promise(r2 => setTimeout(r2, 50))

    // Set M1=1
    eg.data.SilentSet('M1', 'value', 1)
    console.log(`SilentSet后 M1=${rd('M1')} FAT=${rd('FAT')} B3=${rd('B3')}`)

    // Step A: notify M1 → 触发 entangle
    eg.notify?.('M1', 'value')
    await new Promise(r2 => setTimeout(r2, 100))
    console.log(`Step A (notify M1)后: FAT=${rd('FAT')} B3=${rd('B3')}`)

    // Step B: 手动通知 B3 计算公式
    const B3_node = eg.data.GetNodeByPath?.('B3')
    if (B3_node?.dependOn) {
      B3_node.dependOn(() => {
        const m1 = rd('M1')
        console.log(`[B3 dependOn] M1=${m1} → B3=${m1 * 1000}`)
        return m1 * 1000
      }, 'value')
    }
    await new Promise(r2 => setTimeout(r2, 100))
    console.log(`Step B (B3 formula)后: FAT=${rd('FAT')} B3=${rd('B3')}`)
  })

  // 测试: 先 Set B3 再 push M1
  it('Step 3: 先SilentSet B3, 再SetValues M1 (entangle)', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    // B3 用 SetRule
    eg.config.SetRule('M1', 'B3', 'value', {
      triggerKeys: ['value'],
      logic: () => 1000
    })

    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => {
        console.log('[emit] M1→FAT propose=45')
        p.set('value', 45)
      }
    })

    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([
      {path: FAT, key: 'value', value: 40},
      {path: 'B3', key: 'value', value: 0},
    ])
    await eg.config.notifyAll()
    await new Promise(r2 => setTimeout(r2, 50))

    // 先 SilentSet B3=500
    eg.data.SilentSet('B3', 'value', 500)
    
    // 再 SetValues M1=1 (触发 entangle + B3 SetRule)
    eg.data.SetValues([{path:'M1', key:'value', value:1}])
    for(let r=0;r<3;r++){
      await eg.config.notifyAll()
      await new Promise(r2 => setTimeout(r2, 50))
    }
    
    console.log(`FAT=${rd('FAT')} B3=${rd('B3')}`)
    // SilentSet B3 是先手值, SetRule 应该覆盖为1000
    // FAT 应该变成45
  })
})
