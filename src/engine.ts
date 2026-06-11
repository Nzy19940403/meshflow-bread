import { useMeshFlow, deleteEngine as _deleteMeshEngine } from '@meshflow/core'
import { useLogger } from '@meshflow/logger'
import { Parser } from 'hot-formula-parser'
import { shallowRef, ref } from 'vue'

export type CellId = string

interface CellState {
  value: any
  formula: string
}

let ROWS = 25
let COLS = 10
const MAX_COLS = 26
const MAX_ROWS = 99
const COL_NAMES = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

export interface ParsedFormula {
  deps: CellId[]
  compute: (vals: Record<CellId, any>) => any
}

/**
 * 使用 hot-formula-parser 解析并求值公式
 * 安全：仅解析 Excel 公式语法，不会执行任意 JS 代码
 */
function parseFormula(expr: string): ParsedFormula | null {
  if (!expr || !expr.startsWith('=')) return null
  const body = expr.slice(1).trim()

  // 提取所有单元格引用，用于依赖追踪
  const refs = [...new Set(body.match(/[A-Za-z]+\d+/g) || [])].map(r => r.toUpperCase()) as CellId[]

  const compute = (vals: Record<CellId, any>): any => {
    try {
      const parser = new Parser()

      // 注册单元格值回调
      parser.on('callCellValue', ({ label }: { label: string }, cb: (v: any) => void) => {
        const key = label.toUpperCase() as CellId
        cb(vals[key] !== undefined ? vals[key] : 0)
      })

      // 注册范围值回调 (注意: hot-formula-parser 行号是 0-based)
      parser.on('callRangeValue', (startCell: any, endCell: any, cb: (vals: any[]) => void) => {
        const values: any[] = []
        const sCol = startCell.column.index
        const eCol = endCell.column.index
        const sRow = startCell.row.index + 1  // 转 1-based
        const eRow = endCell.row.index + 1
        for (let c = sCol; c <= eCol; c++) {
          for (let r = sRow; r <= eRow; r++) {
            const id = `${COL_NAMES[c]}${r}` as CellId
            values.push(vals[id] !== undefined ? vals[id] : 0)
          }
        }
        cb(values)
      })

      const { result, error } = parser.parse(body)

      if (error || (result as any) instanceof Error) return '#ERR'
      if (typeof result === 'boolean') return result
      if (typeof result === 'string') {
        const num = Number(result)
        return isNaN(num) ? result : num
      }
      return result
    } catch {
      return '#ERR'
    }
  }

  return { deps: refs, compute }
}

function expandRange(range: string): string[] {
  const parts = range.split(':')
  if (parts.length !== 2) return [range]
  const from = parts[0].trim()
  const to = parts[1].trim()
  const col1 = from[0]; const row1 = parseInt(from.slice(1))
  const col2 = to[0];   const row2 = parseInt(to.slice(1))
  const cells: string[] = []
  const startCol = COL_NAMES.indexOf(col1.toUpperCase())
  const endCol = COL_NAMES.indexOf(col2.toUpperCase())
  if (startCol < 0 || endCol < 0 || isNaN(row1) || isNaN(row2)) return [range]
  for (let c = startCol; c <= endCol; c++) {
    for (let r = row1; r <= row2; r++) {
      cells.push(`${COL_NAMES[c]}${r}`)
    }
  }
  return cells
}

export interface SheetEngine {
  getCellValue: (id: CellId) => any
  getCellFormula: (id: CellId) => string
  setCellValue: (id: CellId, raw: string) => void
  setCellFormula: (id: CellId, formula: string) => void
  getAffectedCells: (from: CellId) => CellId[]
  getRows: () => number
  getCols: () => number
  addRow: () => void
  addCol: () => void
  loadState: (data: Record<string, { value: any; formula: string }>) => void
  exportState: () => Record<string, { value: any; formula: string }>
  clearAll: () => void
  /** 触发引擎规则求值 */
  notifyAll: () => any
  /** 原始引擎实例（供纠缠等高级 API 使用） */
  raw: any
  /** 历史模块（Undo/Redo） */
  history?: {
    Undo: () => void
    Redo: () => void
    updateUndoSize: (cb: (n: number) => void) => void
    updateRedoSize: (cb: (n: number) => void) => void
  }
  /** 便捷 SetValue (写入引擎单元格并触发历史记录) */
  SetValue: (id: CellId, val: any) => void
  /** 便捷 GetValue (读取引擎单元格) */
  GetValue: (id: CellId) => any
  /** 便捷 SilentSet (写入引擎单元格但不触发规则求值) */
  SilentSet: (id: CellId, val: any) => void
  /** 销毁引擎实例（从全局缓存移除） */
  destroy: () => void
  /** 最近变更的节点 ID 集（供 UI 高亮用）。拖动滑块：Set([id])；推月份：Set([所有联动节点]) */
  changedNodes: { value: Set<string> }
  uiSignal: { value: number }
}

const ENGINE_ID = 'meshflow-sheet'

export function createSheetEngine(): SheetEngine {
  // 清理旧实例（支持热重载 / 重复调用）
  try { _deleteMeshEngine(ENGINE_ID) } catch {}

  let engine: any
  const uiSignal = ref(0)


  function buildNodes(_rows: number, _cols: number) {
    const nodes: { path: CellId; initValue: CellState }[] = []
    for (let r = 1; r <= _rows; r++) {
      for (let c = 0; c < _cols; c++) {
        const id = `${COL_NAMES[c]}${r}` as CellId
        nodes.push({ path: id, initValue: { value: '', formula: '' } })
      }
    }
    return nodes
  }

  function initEngine(_rows: number, _cols: number) {
    const nodes = buildNodes(_rows, _cols)
    console.log('createEngine id:', ENGINE_ID, 'nodes:', nodes.length)
    engine = useMeshFlow(ENGINE_ID, { nodes } as any, {
      config: { useGreedy: true },
      UITrigger: {
        signalCreator: () => uiSignal,
        signalTrigger: (signal: any) => signal.value++,
      },
      modules: {
        mountNodes: (scheduler: any, schema: any) => {
          for (const n of schema.nodes) {
            scheduler.registerNode({
              path: n.path,
              type: 'cell',
              state: { value: '', formula: '' },
              notifyKeys: new Set(['value', 'formula']),
              meta: {},
            }).createView()
          }
          // 额外节点（不在 A1-J25 范围内的特殊 ID。B16-B25 已在格子里，M1/P1/T1/B26/B28 不在）
          for (const path of ['FAT', 'EMP', 'BRAND', 'TRAFFIC', 'M1', 'P1', 'T1', 'B26', 'B28', 'B32']) {
            scheduler.registerNode({
              path,
              type: 'cell',
              state: { value: 0, formula: '' },
              notifyKeys: new Set(['value', 'formula']),
              meta: {},
            }).createView()
          }
        },
      },
    } as any);

    const logger = useLogger( {
    // locale:'en',
        focusPaths:['B18']
    })
    let cancel = engine.config.usePlugin(logger)
  }

  initEngine(ROWS, COLS)

  const formulaCache = new Map<CellId, ParsedFormula | null>()

  function getCellData(id: CellId): CellState {
    try {
      return engine.data.GetValue(id, 'state') || { value: '', formula: '' }
    } catch {
      return { value: '', formula: '' }
    }
  }

  function getCellValue(id: CellId): any {
    return getCellData(id).value
  }

  function getCellFormula(id: CellId): string {
    return getCellData(id).formula
  }

  function setCellValue(id: CellId, raw: string) {
    const isFormula = raw.startsWith('=')
    if (isFormula) {
      setCellFormula(id, raw)
    } else {
      const parsed = formulaCache.get(id)
      if (parsed) {
        formulaCache.delete(id)
        // 清除旧规则（简化处理）
      }
      const num = raw === '' ? '' : isNaN(Number(raw)) ? raw : Number(raw)
      engine.data.SetValue(id, 'value', num)
      engine.data.SetValue(id, 'formula', '')
    }
  }

  function setCellFormula(id: CellId, formula: string) {
    const parsed = parseFormula(formula)
    formulaCache.set(id, parsed)

    try {
      engine.data.SilentSet(id, 'formula', formula)
    } catch (e: any) {
      console.error('setCellFormula SilentSet failed', id, formula, 'engineId:', ENGINE_ID, e.message)
      return
    }

    if (!parsed || parsed.deps.length === 0) {
      engine.data.SetValue(id, 'value', formula || '')
      return
    }

    try {
      if (parsed.deps.length === 1) {
        engine.config.SetRule(
          parsed.deps[0],
          id,
          'value' as any,
          {
            triggerKeys: ['value'],
            logic: ({ slot }: any) => {
              const vals: Record<CellId, any> = {}
              parsed.deps.forEach((dep, i) => {
                vals[dep] = slot.triggerTargets[i]?.value
              })
              return parsed.compute(vals)
            },
          } as any
        )
      } else {
        engine.config.SetRules(
          parsed.deps,
          id,
          'value' as any,
          {
            triggerKeys: ['value'],
            logic: ({ slot }: any) => {
              const vals: Record<CellId, any> = {}
              parsed.deps.forEach((dep, i) => {
                vals[dep] = slot.triggerTargets[i]?.value
              })
              return parsed.compute(vals)
            },
          } as any
        )
      }
    } catch (e) {
      // 规则可能已存在
    }

    // 直接用 hot-formula-parser 即时求值（因为 npm @meshflow/core v0.8.9 的规则求值不会同步触发）
    try {
      const vals: Record<string, any> = {}
      parsed.deps.forEach(dep => {
        const v = getCellValue(dep)
        vals[dep] = v !== '' && v !== undefined && v !== null ? v : 0
      })
      const result = parsed.compute(vals)
      engine.data.SetValue(id, 'value', result !== undefined ? result : undefined)
    } catch {
      engine.data.SetValue(id, 'value', undefined)
    }
  }

  function getAffectedCells(from: CellId): CellId[] {
    const affected: CellId[] = []
    for (const [cellId, parsed] of formulaCache.entries()) {
      if (parsed && parsed.deps.includes(from)) {
        affected.push(cellId)
        affected.push(...getAffectedCells(cellId))
      }
    }
    return [...new Set(affected)]
  }

  function addRow() {
    if (ROWS >= MAX_ROWS) return
    ROWS++
  }

  function addCol() {
    if (COLS >= MAX_COLS) return
    COLS++
  }

  function loadState(data: Record<string, { value: any; formula: string }>) {
    for (const [id, state] of Object.entries(data)) {
      engine.data.SilentSet(id, 'formula', state.formula)
      if (state.formula.startsWith('=')) {
        formulaCache.set(id as CellId, parseFormula(state.formula))
      }
    }
    for (const [id] of Object.entries(data)) {
      if (getCellFormula(id as CellId).startsWith('=')) {
        try { engine.data.SetValue(id as CellId, 'value', undefined) } catch {}
      } else {
        const raw = data[id].value
        const num = raw === '' ? '' : isNaN(Number(raw)) ? raw : Number(raw)
        engine.data.SilentSet(id as CellId, 'value', num)
      }
    }
  }

  function exportState(): Record<string, { value: any; formula: string }> {
    const data: Record<string, { value: any; formula: string }> = {}
    for (let r = 1; r <= ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const id = `${COL_NAMES[c]}${r}` as CellId
        const state = getCellData(id)
        if (state.value !== '' || state.formula !== '') {
          data[id] = state
        }
      }
    }
    return data
  }

  function clearAll() {
    formulaCache.clear()
    for (let r = 1; r <= ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const id = `${COL_NAMES[c]}${r}` as CellId
        engine.data.SilentSet(id, 'value', '')
        engine.data.SilentSet(id, 'formula', '')
      }
    }
  }

  return {
    getCellValue,
    getCellFormula,
    setCellValue,
    setCellFormula,
    getAffectedCells,
    getRows: () => ROWS,
    getCols: () => COLS,
    addRow,
    addCol,
    loadState,
    exportState,
    clearAll,
    notifyAll: () => engine.config.notifyAll(),
    raw: engine,
    changedNodes: shallowRef(new Set<string>()),
    uiSignal,
    SetValue: (id: CellId, val: any) => engine.data.SetValue(id, 'value', val),
    GetValue: (id: CellId) => { try { return engine.data.GetValue(id, 'value') } catch { return 0 } },
    SilentSet: (id: CellId, val: any) => engine.data.SilentSet(id, 'value', val),
    destroy: () => { try { _deleteMeshEngine(ENGINE_ID) } catch {} },
  }
}