/**
 * 核心发现: notify() 方式 entangle 不生效, _batchNotify 方式生效
 * 原因可能是 notify() 内部调用了 _requestUpdate 导致 rAF 二次点火清空 ghost buffer
 */
import { describe, it } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT = 'FAT'

describe('notify() vs _batchNotify — 关键路径对比', () => {
  
  // 这个之前测试通过: FAT=45
  it('✅ SetValues (走_batchNotify) + notifyAll', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => { p.set('value', 45); console.log('[emit]') }
    })

    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([{path: FAT, key: 'value', value: 40}])
    await eg.config.notifyAll(); await new Promise(r2=>setTimeout(r2,50))

    eg.data.SetValues([{path:'M1', key:'value', value:1}])
    await eg.config.notifyAll(); await new Promise(r2=>setTimeout(r2,50))
    
    console.log(`FAT=${rd(FAT)}`)
  })

  // 同样的 entangle 设置，但用 notify()
  it('❌ SilentSet + notify()', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => { p.set('value', 45); console.log('[emit]') }
    })

    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([{path: FAT, key: 'value', value: 40}])
    await eg.config.notifyAll(); await new Promise(r2=>setTimeout(r2,50))

    eg.data.SilentSet('M1', 'value', 1)
    // 用 notify 而不是 SetValues
    eg.notify?.('M1', 'value')
    await new Promise(r2=>setTimeout(r2,100))
    
    console.log(`FAT=${rd(FAT)}`)
  })

  // SetValues 也用 notifyAll 后续
  it('✅ SetValues + 手动_notifyAll (绕过config.notifyAll)', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => { p.set('value', 45); console.log('[emit]') }
    })

    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([{path: FAT, key: 'value', value: 40}])
    await eg.config.notifyAll(); await new Promise(r2=>setTimeout(r2,50))

    eg.data.SetValues([{path:'M1', key:'value', value:1}])
    // 用 scheduler 内部的 _notifyAll
    // @ts-ignore
    await eg.scheduler?._notifyAll()
    await new Promise(r2=>setTimeout(r2,100))
    
    console.log(`FAT=${rd(FAT)}`)
  })

  // SetValues 不是 _batchNotify 而是手动 TaskRunner
  it('✅ SetValues 后手动 TaskRunner (绕过_notifyAll)', async () => {
    const e = createSheetEngine()
    const eg = e.raw as any
    const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0

    eg.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (_c: any, _i: any, p: any) => { p.set('value', 45); console.log('[emit]') }
    })

    eg.data.SilentSet('M1', 'value', 0)
    eg.data.SetValues([{path: FAT, key: 'value', value: 40}])
    await eg.config.notifyAll(); await new Promise(r2=>setTimeout(r2,50))

    eg.data.SilentSet('M1', 'value', 1)
    
    // 手动触发 TaskRunner — 模拟 _batchNotify 的行为但不经过 _requestUpdate
    // @ts-ignore
    const scheduler = eg.scheduler
    if (scheduler) {
      const m1Uid = scheduler.GetNodeByPath?.('M1')?.uid
      if (m1Uid !== undefined) {
        // @ts-ignore
        scheduler._meshTaskSystem.TaskRunner(null, [m1Uid], [{uid: m1Uid, key: 'value'}])
        await new Promise(r2=>setTimeout(r2,100))
      }
    }
    
    console.log(`FAT=${rd(FAT)}`)
  })
})
