
/**
 * 对比: setCellFormula vs SetRule 
 * setCellFormula 不建立 DAG 边 — 应该不阻塞 entangle
 */
import { describe, it } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT='FAT', BRAND='BRAND', EXP='EMP'

describe('setCellFormula vs SetRule', () => {
  it('setCellFormula + entangle', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    // 用 setCellFormula 替代 SetRule
    e.setCellFormula('B3', '=M1*1000')

    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => {
        p.set('value', 45)
        console.log('[emit] M1→FAT propose=45')
      }
    })

    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([
      {path: FAT, key: 'value', value: 40},
      {path: 'B3', key: 'value', value: 0},
    ])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    
    eg.data.SetValues([{path:'M1',key:'value',value:1}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    
    console.log(`FAT=${rd(FAT)} B3=${rd('B3')}`)
  })

  it('纯 SetRule + entangle (复现问题)', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    eg.config.SetRule('M1', 'B3', 'value', {
      triggerKeys: ['value'],
      logic: () => 1000
    })

    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => {
        p.set('value', 45)
        console.log('[emit] M1→FAT propose=45')
      }
    })

    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([
      {path: FAT, key: 'value', value: 40},
      {path: 'B3', key: 'value', value: 0},
    ])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    
    eg.data.SetValues([{path:'M1',key:'value',value:1}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    
    console.log(`FAT=${rd(FAT)} B3=${rd('B3')}`)
  })

  it('SetRule + entangle 但用 SetValue 不是 SetValues', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    eg.config.SetRule('M1', 'B3', 'value', {
      triggerKeys: ['value'],
      logic: () => 1000
    })

    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => {
        p.set('value', 45)
        console.log('[emit] M1→FAT propose=45')
      }
    })

    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([
      {path: FAT, key: 'value', value: 40},
      {path: 'B3', key: 'value', value: 0},
    ])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    
    // 用 SetValue 不是 SetValues
    eg.data.SetValue('M1', 'value', 1)
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    
    console.log(`FAT=${rd(FAT)} B3=${rd('B3')}`)
  })
})
