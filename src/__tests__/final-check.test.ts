/**
 * 面包店项目直接import引擎源码 — 对比 0.8.9 vs 0.9.0 vs 源码
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT = 'FAT'

describe('三步确认', () => {

  // Step 1: 当前 0.9.0 npm 包
  it('npm 0.9.0 — SetRule + Entangle', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    eg.config.SetRule('M1', 'B3', 'value', {
      triggerKeys: ['value'],
      logic: () => { console.log('[SetRule fired]'); return 1000 }
    })

    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => {
        console.log('[emit fired]')
        p.set('value', 999)
      }
    })

    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([{path:FAT,key:'value',value:40},{path:'B3',key:'value',value:0}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    eg.data.SetValues([{path:'M1',key:'value',value:1}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    console.log(`FAT=${rd(FAT)} (应999) B3=${rd('B3')} (应1000)`)
  })

  // Step 2: 只用 Entangle（无SetRule）确认 0.9.0 entangle 本身是否正常
  it('npm 0.9.0 — 只有 Entangle', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => {
        console.log('[emit fired]')
        p.set('value', 999)
      }
    })

    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([{path:FAT,key:'value',value:40}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    eg.data.SetValues([{path:'M1',key:'value',value:1}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    console.log(`FAT=${rd(FAT)} (应999)`)
  })
})
