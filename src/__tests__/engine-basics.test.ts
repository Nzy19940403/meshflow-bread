/**
 * 极小测试：验证 @meshflow/core 在 Node.js/vitest 环境中的 SetRule 能否触发
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

describe('引擎基础功能验证', () => {
  it('SetRule 应能触发传播', async () => {
    const engine = createSheetEngine()
    const eng = engine.raw

    // 注册 A1→B1: B1 = A1 * 2
    eng.config.SetRule('A1', 'B1', 'value', {
      logic: ({ slot }: any) => {
        const v = slot.triggerTargets[0]?.value
        return v !== null && v !== undefined ? Number(v) * 2 : 0
      },
      triggerKeys: ['value'],
    })

    // 设置 A1 = 5
    eng.data.SetValue('A1', 'value', 5)

    // 用 notifyAll 等待传播完成
    await eng.config.notifyAll()
    await new Promise(r => setTimeout(r, 10))
    const b1 = eng.data.GetValue('B1', 'value')
    console.log(`  Set A1=5, B1=${b1} (期望 10)`)

    expect(b1).toBe(10)
  })

  it('notifyAll 后应能读到已设值', () => {
    const engine = createSheetEngine()
    const eng = engine.raw

    // SilentSet
    eng.data.SilentSet('A1', 'value', 42)
    eng.data.SilentSet('A1', 'formula', '')

    // 读值
    const v1 = eng.data.GetValue('A1', 'value')
    console.log(`  SilentSet A1=42, 直接读=${v1}`)

    // notifyAll 后读
    eng.config.notifyAll()
    const v2 = eng.data.GetValue('A1', 'value')
    console.log(`  notifyAll 后读 A1=${v2}`)

    // 再 SetValue
    eng.data.SetValue('A1', 'value', 99)
    const v3 = eng.data.GetValue('A1', 'value')
    console.log(`  SetValue A1=99, 读=${v3}`)

    expect(v1).toBe(42)
    expect(v3).toBe(99)
  })

  it('engine.getCellValue 接口测试', () => {
    const engine = createSheetEngine()
    engine.raw.data.SetValue('C3', 'value', 777)
    const v = engine.getCellValue('C3')
    console.log(`  setCellValue C3=777, getCellValue=${v}`)
    expect(v).toBe(777)
  })

  it('setCellFormula 后读值', () => {
    const engine = createSheetEngine()
    engine.setCellValue('A1', '10')
    engine.setCellValue('B1', '20')
    engine.setCellFormula('C1', '=A1+B1')
    const v = engine.getCellValue('C1')
    console.log(`  A1=10, B1=20, setCellFormula C1=A1+B1 = ${v} (期望 30)`)
    expect(v).toBe(30)
  })
})
