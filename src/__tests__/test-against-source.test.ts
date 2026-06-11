/**
 * 直接 import 引擎源码测试 — 跳过 npm 包
 * 
 * 在 bakery 项目环境里直接引用 vue-app-webpack 的源码
 */
import { describe, it, expect } from 'vitest'
// @ts-ignore
import { useMeshFlow, deleteEngine } from '../../microapp/vue-app-webpack/utils/core/engine/useEngineManager'

const FAT = 'FAT'

describe('直接 import 引擎源码 — SetRule + Entangle', () => {

  function makeEngine() {
    const testData = {
      nodes: [
        { path: 'M1', initValue: 0 },
        { path: 'FAT', initValue: 40 },
        { path: 'B3', initValue: 0 },
      ],
    }
    const engine = useMeshFlow('test-src', testData, {
      config: { useGreedy: true, useEntangleStep: 100 },
      modules: {
        useTestModule: (scheduler: any, _config: any) => {
          const views: Record<string, any> = {}
          testData.nodes.forEach((config) => {
            const node = scheduler.registerNode({
              path: config.path,
              type: 'test-node',
              state: { value: config.initValue, count: 0 },
              notifyKeys: new Set(),
              meta: {},
            })
            views[config.path] = node.createView()
          })
          const statsPath = 'sys.stats'
          const statsNode = scheduler.registerNode({
            path: statsPath,
            type: 'stats',
            state: { version: 0 },
            notifyKeys: new Set(),
            meta: {},
          })
          views['stats'] = statsNode.createView({ path: statsPath })
          return views
        },
      },
    })
    const rd = (id: string) => engine.data.GetValue(id, 'state')?.value
    return { engine, raw: engine as any, rd }
  }

  afterEach(() => {
    try { deleteEngine('test-src') } catch {}
  })

  it('只有 Entangle M1→FAT', async () => {
    const { engine, raw, rd } = makeEngine()
    raw.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (src: any, _tgt: any, propose: any) => {
        propose.set('value', (src?.state?.value ?? 0) + 5)
      },
    })
    engine.data.SetValue('M1', 'value', 1)
    await raw.config.notifyAll()
    await new Promise(r => setTimeout(r, 50))
    console.log(`FAT=${rd(FAT)}`)
    expect(rd(FAT)).toBe(6)
  })

  it('SetRule M1→B3 + Entangle M1→FAT', async () => {
    const { engine, raw, rd } = makeEngine()
    raw.config.SetRule('M1', 'B3', 'value', {
      triggerKeys: ['value'],
      logic: ({ slot }: any) => (slot.triggerTargets?.[0]?.value ?? 0) * 1000,
    })
    raw.config.useEntangle({
      cause: 'M1', impact: FAT, via: ['value'],
      emit: (src: any, _tgt: any, propose: any) => {
        propose.set('value', (src?.state?.value ?? 0) + 5)
      },
    })
    engine.data.SetValue('M1', 'value', 1)
    await raw.config.notifyAll()
    await new Promise(r => setTimeout(r, 50))
    console.log(`FAT=${rd(FAT)} B3=${rd('B3')}`)
    expect(rd(FAT)).toBe(6)
    expect(rd('B3')).toBe(1000)
  })
})
