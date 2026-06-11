/**
 * 终极 debug: 直接在引擎代码里打 log
 * 检查 _ghostBuffer 是否有数据 + resolveGhosts 是否被调
 */
import { describe, it } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT = 'FAT', BRAND = 'BRAND', EXP = 'EMP'

const sk = (c: number) => c < 80 ? 1 : c >= 100 ? 0.1 : 1 - ((t => t * t * (3 - 2 * t) * 0.9)((c - 80) / 20))
const wfFn = (b26: number) => 0.2 + 1.6 * Math.min(b26, 10000) / 10000
const physCapFn = (b14: number, b24: number, b26: number, b4: number) =>
  Math.max(1, Math.min(b14 * 35, b24 * 1500) * wfFn(b26) + Math.max(0, Math.round((2 - b4) * 100)))

describe('终极debug: 引擎内部 ghost 系统', () => {
  it('Patch引擎Turnstile，拦截ghostBuffer+resolveGhosts', async () => {
    const engine = createSheetEngine()
    const eg = engine.raw as any

    // ====== Patch Turnstile 打日志 ======
    const ts = eg._meshTaskSystem?.data?.Turnstile || 
              // @ts-ignore
              eg.config?.Turnstile
    
    let ts2: any
    // 直接从 scheduler 拿 Turnstile
    if ((eg as any).scheduler) ts2 = (eg as any).scheduler?._meshTaskSystem?.data?.Turnstile
    if (!ts2) ts2 = (eg as any)._entangleSystem?.Turnstile
    
    const originalResolveGhosts = ts2?._resolveGhosts || ts?._resolveGhosts
    
    console.log('Turnstile found:', !!ts2)
    console.log('Turnstile type:', typeof ts2)
    
    if (ts2 && ts2._resolveGhosts) {
      // 注册
      eg.config.SetRule('M1', 'B3', 'value', {
        triggerKeys: ['value'],
        logic: () => {
          const b14 = Number(eg.data.GetValue('B14','value'))||150
          const b24 = Number(eg.data.GetValue('B24','value'))||8
          const b26 = Number(eg.data.GetValue('B26','value'))||5000
          const b4 = Number(eg.data.GetValue('B4','value'))||2
          const fat = Number(eg.data.GetValue(FAT,'value'))||40
          return Math.max(0, Math.round(physCapFn(b14,b24,b26,b4)*sk(fat)))
        }
      })

      eg.config.useEntangle({
        cause: 'M1', impact: FAT, via: ['value'],
        emit: (_c: any, _i: any, propose: any) => {
          const cur = Number(eg.data.GetValue(FAT,'value'))||40
          console.log(`[emit] M1→FAT: cur=${cur} propose=45, 当前epoch=${(ts2 as any).currentEpoch}`)
          propose.set('value', 45)
          // 检查 ghostBuffer 在 propose 后是否有数据
          const uid = eg.data.GetNodeByPath ? eg.data.GetNodeByPath(FAT)?.uid : -1
          // 从 local 变量找 _ghostBuffer
          console.log(`  FAT uid=${uid} ghostBuffer[uid] length=${(ts2 as any)._ghostBuffer?.[uid]?.length ?? 'N/A'}`)
        }
      })

      // 补丁 resolveGhosts
      const origResolve = ts2._resolveGhosts.bind(ts2)
      ts2._resolveGhosts = (node: any) => {
        const uid = node?.uid ?? -1
        const path = eg.data.GetPathByUid?.(uid) ?? '?'
        const bufLen = ts2._ghostBuffer?.[uid]?.length ?? 0
        const ghostData = ts2._ghostBuffer?.[uid]
        console.log(`[resolveGhosts] path=${path} uid=${uid} buffer.len=${bufLen}`, ghostData ? JSON.stringify(ghostData) : 'empty')
        const result = origResolve(node)
        console.log(`  → changed keys:`, result)
        return result
      }

      // 初始化
      eg.data.SilentSet('M1','value',0)
      eg.data.SetValues([
        {path:FAT,key:'value',value:40},
        {path:BRAND,key:'value',value:0},
        {path:EXP,key:'value',value:0},
        {path:'B3',key:'value',value:0},
        {path:'B14',key:'value',value:150},
        {path:'B24',key:'value',value:8},
        {path:'B26',key:'value',value:5000},
        {path:'B4',key:'value',value:2},
        {path:'B10',key:'value',value:5},
        {path:'B15',key:'value',value:7},
        {path:'B1',key:'value',value:16},
        {path:'B13',key:'value',value:2000},
        {path:'B25',key:'value',value:100},
        {path:'P1',key:'value',value:0},
        {path:'T1',key:'value',value:0},
      ])
      for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}

      console.log('\n=== 推 M1=1 ===')
      eg.data.SetValues([{path:'M1',key:'value',value:1}])

      for(let r=0;r<3;r++){
        console.log(`\n--- notifyAll Round ${r} ---`)
        await eg.config.notifyAll()
        await new Promise(r2=>setTimeout(r2,100))
        const rd = (id:string)=>Number(eg.data.GetValue(id,'value'))||0
        console.log(`  FAT=${rd(FAT)} BRAND=${rd(BRAND)} EMP=${rd(EXP)} B3=${rd('B3')}`)
      }
    } else {
      console.log('Could not find Turnstile')
    }
  }, 30000)
})
