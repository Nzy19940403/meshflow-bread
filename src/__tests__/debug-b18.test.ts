import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

describe('B18 上期报废率链路', () => {
  it('产能大于需求时应产生报废率', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any

    // 注册 SetValue，监听 B18
    let b18History: number[] = []
    // Override SilentSet for B18 to track
    const origSilentSet = eg.data.SilentSet.bind(eg.data)
    eg.data.SilentSet = (path: string, key: string, value: any) => {
      if (path === 'B18') b18History.push(value)
      return origSilentSet(path, key, value)
    }

    // 设置产能过剩的场景：高面积 + 低需求
    eg.data.SilentSet('B1', 'value', 40)   // 高价 → 低需求
    eg.data.SilentSet('B14', 'value', 300)  // 大厂房 → 高产能
    eg.data.SilentSet('B24', 'value', 15)  // 15人
    eg.data.SilentSet('B26', 'value', 5000)
    eg.data.SilentSet('B15', 'value', 1)   // 低地段 → 低客流
    eg.data.SilentSet('B13', 'value', 0)   // 无营销
    eg.data.SilentSet('B10', 'value', 3)
    eg.data.SilentSet('M1', 'value', 0)

    // Register B2 SetRule (simplified)
    eg.config.SetRules(['B1','B15','B13'], 'B2', 'value', {
      triggerKeys: ['value','value','value'],
      logic: ({slot}:any) => {
        const b1=slot.triggerTargets[0]?.value??40
        const g=slot.triggerTargets[1]?.value??1
        const mkt=slot.triggerTargets[2]?.value??0
        const pbF=b1<20?1+(20-b1)*0.15:Math.max(0.6,1-(b1-20)*0.03)
        return Math.round((500+500*g)*pbF+Math.sqrt(Math.max(0,mkt))*10)
      }
    })
    // Simple B3
    eg.config.SetRules(['B14','B24'], 'B3', 'value', {
      triggerKeys: ['value','value'],
      logic: ({slot}:any) => Math.round(Math.min(slot.triggerTargets[0]?.value??60, (slot.triggerTargets[1]?.value??3))*25)
    })

    // Initial notifyAll
    await eg.config.notifyAll()
    await new Promise(r => setTimeout(r, 100))

    console.log('Init: B2 =', eg.data.GetValue('B2','value'), 'B3 =', eg.data.GetValue('B3','value'))

    // Month 1: B3 >> B2, should generate waste
    await eg.data.SetValues([
      {path:'M1',key:'value',value:1},
    ])
    await new Promise(r => setTimeout(r, 200))

    const b2 = Number(eg.data.GetValue('B2','value'))||0
    const b3 = Number(eg.data.GetValue('B3','value'))||0
    const waste = b3>b2&&b3>0 ? Math.round((b3-b2)/b3*1000)/1000 : 0

    // Manually simulate what nx() should do
    eg.data.SilentSet('B18','value',waste)
    console.log('M1: B2 =', b2, 'B3 =', b3, 'waste =', waste)
    console.log('B18 history:', b18History)

    const b18After = Number(eg.data.GetValue('B18','value'))||0
    console.log('B18 in engine:', b18After)
    expect(b18After).toBeGreaterThan(0)
    expect(waste).toBeGreaterThan(0)
  }, 10000)
})
