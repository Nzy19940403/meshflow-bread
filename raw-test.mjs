import { useMeshFlow, useEngine } from '@meshflow/core'

const { engineRef, scheduler } = useMeshFlow()

// Create engine
const engine = useEngine(engineRef, 'test')

// Register 200 cells
const nodes = []
for (let r = 1; r <= 20; r++) {
  for (let c = 0; c < 10; c++) {
    const id = 'ABCDEFGHIJ'[c] + r
    nodes.push({ path: id, type: 'cell', state: { value: '', formula: '' }, notifyKeys: new Set(['value', 'formula']), meta: {} })
  }
}
for (const n of nodes) scheduler.registerNode(n).createView()

// Set a value
engine.data.SilentSet('A1', 'value', 42)

// Register a simple rule: B1 = A1 * 2
engine.config.SetRule('A1', 'B1', 'value', {
  logic: ({ slot }) => {
    const v = slot.triggerTargets[0]?.value
    console.log('  [rule fired] A1=', v)
    return v !== null && v !== undefined ? Number(v) * 2 : 0
  },
  triggerKeys: ['value'],
})

// Read B1 before notify
const before = engine.data.GetValue('B1', 'value')
console.log('B1 before notifyAll:', before)

// Try notifyAll
engine.config.notifyAll()

const after = engine.data.GetValue('B1', 'value')
console.log('B1 after notifyAll:', after)

// Also try SetValue (should trigger notification)
engine.data.SetValue('A1', 'value', 99)
const afterSet = engine.data.GetValue('B1', 'value')
console.log('B1 after SetValue A1=99:', afterSet)
