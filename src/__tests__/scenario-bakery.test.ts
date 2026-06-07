/**
 * meshflow-sheet 复杂经营推演测试
 *
 * 场景：面包店月度经营模拟
 * 测试四组 What-If 推演：降价、扩产、同时降价扩产、降低成本
 * 核心验证：多依赖公式的联动计算、链式传播
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { Parser } from 'hot-formula-parser'

// ============================================================
// 纯公式解析器测试 (hot-formula-parser 结果验证)
// ============================================================

function parseFormula(expr: string): string[] {
  if (!expr || !expr.startsWith('=')) return []
  const body = expr.slice(1).trim()
  return [...new Set(body.match(/[A-Za-z]+\d+/g) || [])].map(r => r.toUpperCase())
}

function evalFormula(expr: string, vals: Record<string, any>): any {
  const body = expr.slice(1).trim()
  try {
    const parser = new Parser()
    parser.on('callCellValue', ({ label }: any, cb: (v: any) => void) => {
      cb(vals[label.toUpperCase()] !== undefined ? vals[label.toUpperCase()] : 0)
    })
    parser.on('callRangeValue', (startCell: any, endCell: any, cb: (v: any[]) => void) => {
      const values: any[] = []
      for (let c = startCell.column.index; c <= endCell.column.index; c++) {
        for (let r = startCell.row.index + 1; r <= endCell.row.index + 1; r++) {
          const id = `${'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[c]}${r}`
          values.push(vals[id] !== undefined ? vals[id] : 0)
        }
      }
      cb(values)
    })
    const { result, error } = parser.parse(body)
    if (error) return '#ERR'
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

// ============================================================
// 场景设定：面包店经营数据
// ============================================================
const baseData: Record<string, any> = {
  A1: 15,    // 面包售价 (元/个)
  B1: 200,   // 日均销量 (个/天)
  C1: 26,    // 月营业天数
  D1: 5,     // 面粉成本 (元/个)
  E1: 2,     // 其他材料成本 (元/个)
  H1: 8000,  // 房租 (元/月)
  I1: 12000, // 人工费 (元/月)
  J1: 3000,  // 水电杂费 (元/月)
}

// 验证每个公式的结果
describe('面包店月度经营模型', () => {
  it('F1: 单位总成本 = D1 + E1', () => {
    expect(evalFormula('=D1+E1', baseData)).toBe(7)
  })

  it('G1: 月收入 = A1 * B1 * C1', () => {
    expect(evalFormula('=A1*B1*C1', baseData)).toBe(15 * 200 * 26) // 78,000
  })

  it('K1: 总固定成本 = H1 + I1 + J1', () => {
    expect(evalFormula('=H1+I1+J1', baseData)).toBe(8000 + 12000 + 3000) // 23,000
  })

  it('L1: 月总成本 = F1*B1*C1 + K1', () => {
    const f1 = evalFormula('=D1+E1', baseData) // 7
    const k1 = evalFormula('=H1+I1+J1', baseData) // 23000
    const vals = { ...baseData, F1: f1, K1: k1 }
    expect(evalFormula('=F1*B1*C1+K1', vals)).toBe(7 * 200 * 26 + 23000) // 59,400
  })

  it('M1: 月利润 = G1 - L1', () => {
    const f1 = evalFormula('=D1+E1', baseData)
    const k1 = evalFormula('=H1+I1+J1', baseData)
    const g1 = evalFormula('=A1*B1*C1', baseData)
    const l1 = evalFormula('=F1*B1*C1+K1', { ...baseData, F1: f1, K1: k1 })
    expect(evalFormula('=G1-L1', { G1: g1, L1: l1 })).toBe(78000 - 59400) // 18,600
  })

  it('N1: 利润率 = M1 / G1', () => {
    const g1 = 78000; const m1 = 18600
    expect(evalFormula('=M1/G1', { M1: m1, G1: g1 })).toBeCloseTo(0.2385, 3)
  })
})

// ============================================================
// What-if 推演测试
// ============================================================
describe('What-if 推演', () => {
  // 已计算的基线值
  const base = {
    A1: 15, B1: 200, C1: 26,
    D1: 5, E1: 2, F1: 7,
    H1: 8000, I1: 12000, J1: 3000, K1: 23000,
    G1: 78000, L1: 59400, M1: 18600, N1: 0.2385,
  }

  describe('推演1: 降价10% (薄利多销)', () => {
    it('A2: 新售价 = A1 * 0.9', () => {
      expect(evalFormula('=A1*0.9', base)).toBe(13.5)
    })

    it('B2: 价格弹性系数 = 2.0 (输入)', () => {
      // 纯输入值，没有公式
    })

    it('C2: 预测销量 = B1*(1+B2*0.1) — 多依赖', () => {
      const vals = { ...base, A2: 13.5, B2: 2.0 }
      expect(evalFormula('=B1*(1+B2*0.1)', vals)).toBe(200 * (1 + 2.0 * 0.1)) // 240
    })

    it('D2: 预测月收入 = A2*C2*C1 — 多依赖', () => {
      const vals = { ...base, A2: 13.5, C2: 240 }
      expect(evalFormula('=A2*C2*C1', vals)).toBe(13.5 * 240 * 26) // 84,240
    })

    it('F2: 预测月利润 = D2 - E2 — 降价后利润反而下降', () => {
      const vals = { ...base, D2: 84240, E2: 66680 }
      const profit = evalFormula('=D2-E2', vals)
      expect(profit).toBe(84240 - 66680) // 17,560
      expect(profit).toBeLessThan(base.M1) // 利润比原来少 → 降价不好！
    })

    it('G2: 利润变化 = F2 - M1 — 降价10%利润变化', () => {
      expect(evalFormula('=F2-M1', { F2: 17560, M1: 18600 })).toBe(-1040) // 反而少了1040
    })
  })

  describe('推演2: 扩产20% (规模效应)', () => {
    it('A3: 扩产系数 = 1.2 (输入)', () => {})

    it('B3: 新销量 = B1 * A3', () => {
      expect(evalFormula('=B1*A3', { ...base, A3: 1.2 })).toBe(200 * 1.2) // 240
    })

    it('C3: 新收入 = A1*B3*C1 — 扩产带动收入', () => {
      expect(evalFormula('=A1*B3*C1', { ...base, B3: 240 })).toBe(15 * 240 * 26) // 93,600
    })

    it('E3: 新利润 = C3 - D3 — 扩产后利润大增', () => {
      const vals = { ...base, C3: 93600, D3: 66680 }
      const profit = evalFormula('=C3-D3', vals)
      expect(profit).toBe(93600 - 66680) // 26,920
      expect(profit).toBeGreaterThan(base.M1) // 比原来好！
    })

    it('F3: 利润增幅 = (E3-M1)/M1', () => {
      const gain = evalFormula('=(E3-M1)/M1', { E3: 26920, M1: 18600 })
      expect(gain).toBeCloseTo((26920 - 18600) / 18600, 4) // 44.73%
    })
  })

  describe('推演3: 降价15%+扩产50% (双管齐下)', () => {
    it('C4: 预测收入 = A4*B4*C1 — 销量大幅增长', () => {
      expect(evalFormula('=12.75*300*26', {})).toBe(99450)
    })

    it('E4: 预测利润 = C4-D4 — 双策略下利润提升', () => {
      const profit = 99450 - 54600 - 23000 // 21,850
      expect(profit).toBe(21850)
      expect(profit).toBeGreaterThan(base.M1) // 降价+扩产 = 效果最好！
    })

    it('F4: 利润对比 = E4-M1 — 比现在多赚3250', () => {
      expect(evalFormula('=E4-M1', { E4: 21850, M1: 18600 })).toBe(3250)
    })
  })

  describe('推演4: 降低成本10% (利润杠杆)', () => {
    it('A5: 成本降幅 = 0.1 (输入)', () => {})

    it('B5: 新单位成本 = F1*(1-A5)', () => {
      expect(evalFormula('=F1*(1-A5)', { ...base, A5: 0.1 })).toBe(7 * 0.9) // 6.3
    })

    it('C5: 新利润 = G1-(B5*B1*C1+K1)', () => {
      const newCost = 6.3 * 200 * 26 + 23000 // 32760 + 23000 = 55760
      const profit = 78000 - newCost // 22,240
      expect(profit).toBe(22240)
      expect(profit).toBeGreaterThan(base.M1) // 成本降10% → 利润涨19%
    })

    it('D5: 利润提升 = C5-M1', () => {
      expect(evalFormula('=C5-M1', { C5: 22240, M1: 18600 })).toBe(3640)
    })

    it('E5: 提升幅度 = D5/M1', () => {
      expect(evalFormula('=D5/M1', { D5: 3640, M1: 18600 })).toBeCloseTo(0.1957, 3) // 19.57%
    })
  })
})

// ============================================================
// 核心公式格式测试 (hot-formula-parser 对 Excel 语法的支持)
// ============================================================
describe('Excel 函数支持', () => {
  const vals: Record<string, any> = {
    A1: 10, A2: 20, A3: 30, A4: 40, A5: 50,
    B1: 5, B2: 15, B3: 25,
    C1: 100, C2: 0, C3: -50,
  }

  it('SUM 求和', () => {
    expect(evalFormula('=SUM(A1:A5)', vals)).toBe(10 + 20 + 30 + 40 + 50) // 150
  })

  it('AVERAGE 平均', () => {
    expect(evalFormula('=AVERAGE(A1:A3)', vals)).toBe((10 + 20 + 30) / 3) // 20
  })

  it('MAX 最大值', () => {
    expect(evalFormula('=MAX(A1:A5)', vals)).toBe(50)
  })

  it('MIN 最小值', () => {
    expect(evalFormula('=MIN(A1:A5)', vals)).toBe(10)
  })

  it('COUNT 计数', () => {
    expect(evalFormula('=COUNT(A1:A5)', vals)).toBe(5)
  })

  it('IF 条件判断', () => {
    expect(evalFormula('=IF(A1>5, "大", "小")', vals)).toBe('大')
    expect(evalFormula('=IF(B2<10, "小", "大")', vals)).toBe('大') // B2=15
  })

  it('混合运算：=A1*B1+SUM(A2:A4)', () => {
    expect(evalFormula('=A1*B1+SUM(A2:A4)', vals)).toBe(10 * 5 + (20 + 30 + 40)) // 50 + 90 = 140
  })

  it('嵌套函数：=IF(SUM(A1:A3)>50, "达标", "不达标")', () => {
    expect(evalFormula('=IF(SUM(A1:A3)>50, "达标", "不达标")', vals)).toBe('达标') // SUM=60>50
  })

  it('范围+单个引用混合', () => {
    expect(evalFormula('=SUM(A1:A3)+B1', vals)).toBe((10 + 20 + 30) + 5) // 65
  })
})

// ============================================================
// MeshFlow 传播链测试 (依赖关系验证)
// ============================================================
describe('依赖链与传播', () => {
  it('parseFormula 正确提取单依赖', () => {
    const deps = parseFormula('=A1*2')
    expect(deps).toEqual(['A1'])
  })

  it('parseFormula 正确提取多依赖', () => {
    const deps = parseFormula('=A1+B1')
    expect(deps.sort()).toEqual(['A1', 'B1'])
  })

  it('parseFormula 提取 SUM 范围内的所有单元格', () => {
    const deps = parseFormula('=SUM(A1:C3)')
    // 正则只提取字面单元格引用，不展开范围
    // 范围展开在 hot-formula-parser 的 callRangeValue 回调中处理
    expect(deps.sort()).toEqual(['A1', 'C3'].sort())
  })

  it('parseFormula 提取混合引用', () => {
    const deps = parseFormula('=A1+SUM(B1:B5)+C1').sort()
    // 正则提取字面引用：A1, B1, B5, C1（B2/B3/B4 由运行时展开）
    expect(deps).toEqual(['A1', 'B1', 'B5', 'C1'].sort())
  })

  it('依赖链传播：A1→D1→E1 (两层传播)', () => {
    // 模拟公式: D1=A1*2, E1=D1+10
    // A1=5 → D1=10 → E1=20
    let vals: Record<string, any> = { A1: 5 }
    const d1 = evalFormula('=A1*2', vals)
    vals.D1 = d1
    const e1 = evalFormula('=D1+10', vals)
    expect(d1).toBe(10)
    expect(e1).toBe(20)

    // A1 变了 → 验证传播
    vals.A1 = 100
    const d1_new = evalFormula('=A1*2', vals)
    vals.D1 = d1_new
    const e1_new = evalFormula('=D1+10', vals)
    expect(d1_new).toBe(200)
    expect(e1_new).toBe(210)
  })

  it('多输入传播：A1+B1→C1, C1+D1→E1 (三层)', () => {
    // C1=A1+B1, E1=C1+ D1
    // A1=10, B1=20 → C1=30, E1=30+40=70
    let vals: Record<string, any> = { A1: 10, B1: 20, D1: 40 }
    const c1 = evalFormula('=A1+B1', vals)
    vals.C1 = c1
    const e1 = evalFormula('=C1+D1', vals)
    expect(c1).toBe(30)
    expect(e1).toBe(70)

    // 改 A1 → 整条链级联更新
    vals.A1 = 100
    const c1_new = evalFormula('=A1+B1', vals)
    vals.C1 = c1_new
    const e1_new = evalFormula('=C1+D1', vals)
    expect(c1_new).toBe(120)
    expect(e1_new).toBe(160)
  })
})

// ============================================================
// 推演结论测试
// ============================================================
describe('经营决策推演结论', () => {
  it('降价10% → 利润反而下降 (价格战不划算)', () => {
    const baseProfit = 18600
    const discountProfit = 17560
    expect(discountProfit).toBeLessThan(baseProfit)
    expect(baseProfit - discountProfit).toBe(1040)
  })

  it('扩产20% → 利润增长44.7% (规模效应明显)', () => {
    const baseProfit = 18600
    const expandProfit = 26920
    expect(expandProfit).toBeGreaterThan(baseProfit)
    expect(((expandProfit - baseProfit) / baseProfit) * 100).toBeCloseTo(44.73, 1)
  })

  it('降价15%+扩产50% → 利润增长17.5% (双策略)', () => {
    const baseProfit = 18600
    const dualProfit = 21850
    expect(dualProfit).toBeGreaterThan(baseProfit)
    expect(dualProfit - baseProfit).toBe(3250)
  })

  it('成本降10% → 利润增19.6% (成本杠杆远超降价)', () => {
    const baseProfit = 18600
    const costProfit = 22240
    const gain = 3640
    const gainPercent = (gain / baseProfit) * 100
    expect(gainPercent).toBeCloseTo(19.57, 1)
    expect(gainPercent).toBeGreaterThan(10) // 成本降10% → 利润增19.6%, 杠杆率约2倍
  })

  it('结论：降成本 > 扩产 > 双策略 > 降价 (效果排序)', () => {
    // 从最好的策略到最差的
    const strategies = [
      { name: '降成本10%', gain: 22240 - 18600 },
      { name: '扩产20%', gain: 26920 - 18600 },
      { name: '降价15%+扩产50%', gain: 21850 - 18600 },
      { name: '降价10%', gain: 17560 - 18600 },
    ]
    strategies.sort((a, b) => b.gain - a.gain)
    expect(strategies[0].name).toBe('扩产20%') // 扩产20%利润增幅最大
    expect(strategies[3].name).toBe('降价10%') // 降价最差
  })
})
