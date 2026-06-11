/**
 * 逐步 debug: 在有 SetRules 的情况下，entangle ghost 提案为什么被拒绝
 * 
 * 观察: SetRule M1→B3 成功更新 B3，但 M1→FAT entangle 提案 (propose=45) 被忽略
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT='FAT', EXP='EMP', BRAND='BRAND'

// 最小复现: 一个 SetRule + 一个 entangle
describe('最小复现 — SetRule 阻塞 entangle ？', () => {

  it('测试: 1个SetRule(M1→B3) + 1个Entangle(M1→FAT)', async () => {
    const engine = createSheetEngine()
    const eg = engine.raw as any
    const rd = (id:string) => Number(eg.data.GetValue(id,'value'))||0

    // 只注册 1 个 SetRule
    eg.config.SetRule('M1','B3','value',{
      triggerKeys:['value'],
      logic:()=>1000 // 固定 B3=1000
    })

    // 只注册 1 个 entangle
    eg.config.useEntangle({
      cause:'M1', impact:FAT, via:['value'],
      emit:(_cause:any,_impact:any,propose:any)=>{
        const cur = rd(FAT)||40
        console.log(`[emit] M1→FAT: cur=${cur} propose=${cur+5}`)
        propose.set('value', cur+5)
      }
    })

    // 初始化
    eg.data.SilentSet('M1','value',0)
    eg.data.SetValues([
      {path:FAT,key:'value',value:40},
      {path:'B3',key:'value',value:0},
    ])

    // 初始收敛
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    console.log(`初始后: FAT=${rd(FAT)} B3=${rd('B3')}`)

    // 推M1
    eg.data.SetValues([{path:'M1',key:'value',value:1}])
    console.log(`SetValues(M1=1)后立即读: FAT=${rd(FAT)} B3=${rd('B3')}`)

    // 逐round打印
    console.log('\n--- Round 0 ---')
    await eg.config.notifyAll()
    await new Promise(r2=>setTimeout(r2,50))
    console.log(`  FAT=${rd(FAT)} B3=${rd('B3')}`)

    console.log('--- Round 1 ---')
    await eg.config.notifyAll()
    await new Promise(r2=>setTimeout(r2,50))
    console.log(`  FAT=${rd(FAT)} B3=${rd('B3')}`)

    console.log('--- Round 2 ---')
    await eg.config.notifyAll()
    await new Promise(r2=>setTimeout(r2,50))
    console.log(`  FAT=${rd(FAT)} B3=${rd('B3')}`)

    // 再多几轮
    for(let r=3;r<10;r++){
      await eg.config.notifyAll()
      await new Promise(r2=>setTimeout(r2,50))
    }
    console.log(`\n10轮后: FAT=${rd(FAT)} B3=${rd('B3')}`)

    expect(rd(FAT)).toBeGreaterThan(40)
  },30000)

  it('测试: 只有 Entangle(M1→FAT)，没有 SetRule', async () => {
    const engine = createSheetEngine()
    const eg = engine.raw as any
    const rd = (id:string) => Number(eg.data.GetValue(id,'value'))||0

    eg.config.useEntangle({
      cause:'M1', impact:FAT, via:['value'],
      emit:(_cause:any,_impact:any,propose:any)=>{
        const cur = rd(FAT)||40
        console.log(`[emit] M1→FAT: cur=${cur} propose=${cur+5}`)
        propose.set('value', cur+5)
      }
    })

    eg.data.SilentSet('M1','value',0)
    eg.data.SetValues([{path:FAT,key:'value',value:40}])

    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    console.log(`初始后: FAT=${rd(FAT)}`)

    eg.data.SetValues([{path:'M1',key:'value',value:1}])

    await eg.config.notifyAll()
    await new Promise(r2=>setTimeout(r2,50))
    console.log(`Round 0: FAT=${rd(FAT)}`)

    expect(rd(FAT)).toBeGreaterThan(40)
  },30000)
})
