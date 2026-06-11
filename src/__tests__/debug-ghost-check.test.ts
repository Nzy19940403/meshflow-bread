/**
 * 直接注入引擎内部，看 ghost buffer 和 resolveGhosts
 */
import { describe, it } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT = 'FAT'

describe('Ghost buffer 终极确认', () => {
  it('检查 ghostBuffer 在 propose.set 后的状态', async () => {
    const engine = createSheetEngine()
    const eg = engine.raw as any
    
    // 直接拿到 Turnstile — 从 scheduler 的 _entangleSystem 拿
    // @ts-ignore
    const scheduler = eg.scheduler
    const entangleSystem = scheduler?._entangleSystem
    const turnstile = entangleSystem?.Turnstile
    
    console.log('scheduler:', !!scheduler)
    console.log('entangleSystem:', !!entangleSystem)
    console.log('turnstile:', !!turnstile)
    
    if (turnstile) {
      // 注册
      eg.config.SetRule('M1', 'B3', 'value', {
        triggerKeys: ['value'],
        logic: () => 1000
      })
      
      eg.config.useEntangle({
        cause: 'M1', impact: FAT, via: ['value'],
        emit: (_c: any, _i: any, propose: any) => {
          const cur = Number(eg.data.GetValue(FAT, 'value')) || 40
          console.log(`\n[EMIT] M1→FAT: ${cur}→45`)
          propose.set('value', 45)
          // 这里发射后立刻检查 ghost buffer
          const uid = eg.data.GetNodeByPath?.(FAT)?.uid
          // 运气好的话能从上下文找到
        }
      })
      
      // 创建 watcher — 定期检查 ghostBuffer 和 currentEntangleArray
      const origInit = turnstile._resolveGhosts.bind(turnstile)
      let resolveCount = 0
      turnstile._resolveGhosts = (node: any) => {
        resolveCount++
        const uid = node?.uid ?? -1
        const path = node?.path ?? '?'
        const buf = turnstile._ghostBuffer?.[uid]
        console.log(`\n[RESOLVE #${resolveCount}] path=${path} uid=${uid}`)
        console.log(`  _ghostBuffer[uid]=`, buf ? JSON.stringify(buf) : 'undefined/empty')
        console.log(`  node.state.value=${node?.state?.value}`)
        const r = origInit(node)
        console.log(`  → changedKeys:`, r)
        console.log(`  → node.state.value now=${node?.state?.value}`)
        return r
      }
      
      // 初始
      eg.data.SilentSet('M1', 'value', 0)
      eg.data.SetValues([
        {path: FAT, key: 'value', value: 40},
        {path: 'B3', key: 'value', value: 0},
      ])
      for (let r = 0; r < 3; r++) {
        await eg.config.notifyAll()
        await new Promise(r2 => setTimeout(r2, 50))
      }
      
      console.log('\n=== 推 M1=1 ===')
      eg.data.SetValues([{path: 'M1', key: 'value', value: 1}])
      
      await eg.config.notifyAll()
      await new Promise(r2 => setTimeout(r2, 100))
      
      const rd = (id: string) => Number(eg.data.GetValue(id, 'value')) || 0
      console.log(`\n最终: FAT=${rd(FAT)} (应45) B3=${rd('B3')} (应1000)`)
      console.log(`resolveGhosts 被调了 ${resolveCount} 次`)
    }
  }, 30000)
})
