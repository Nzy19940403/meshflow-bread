/**
 * 引擎 vs Python 传播时序追踪
 * 
 * 给每个节点加执行日志，重建引擎的传播链，
 * 与 Python ref_model_v3.py 的迭代顺序对比。
 */
import { describe, it } from 'vitest'
import { createSheetEngine } from '../engine'

const V3 = { EXP: 'C1', TURNOVER: 'C2', HR_COST: 'C3' } as const

describe('引擎传播追踪 — 高奢·精兵 月1', () => {
  it('notifyAll 各节点执行序 vs Python', async () => {
    const engine = createSheetEngine()
    const eng = engine.raw as any

    // ===== 闭包: 执行计数 =====
    let seq = 0

    // ===== 注册所有节点 =====

    // B5 房租
    eng.config.SetRules(['B14', 'B15'], 'B5', 'value', {
      logic: ({ slot }: any) => {
        seq++; const a = slot.triggerTargets[0]?.value ?? 80; const g = slot.triggerTargets[1]?.value ?? 5
        const r = Math.max(0, Math.round(a * g * Math.max(2, 20 - a * 0.05)))
        console.log(`  [#${seq}] SetRule B5 ← B14=${a} B15=${g}  → B5=${r}`)
        return r
      }, triggerKeys: ['value', 'value'],
    } as any)

    // B9 工资 (SetRule B24)
    eng.config.SetRule('B24', 'B9', 'value', {
      logic: ({ slot }: any) => {
        seq++; const hc = Number(slot.triggerTargets[0]?.value ?? 5); const g = Number(eng.data.GetValue('B15', 'value') ?? 5)
        const p = g * 0.15; const d = Math.max(0, 1 - hc * 0.08)
        const r = Math.round(hc * 1200 * (1 + p * d))
        console.log(`  [#${seq}] SetRule B9  ← B24=${hc} B15=${g}  → B9=${r}`)
        return r
      }, triggerKeys: ['value'],
    } as any)

    // B3 纠缠发射器 ×4
    const computeB3 = () => {
      seq++; const area = Number(eng.data.GetValue('B14', 'value') ?? 80)
      const hc = Number(eng.data.GetValue('B24', 'value') ?? 5)
      const cost = Number(eng.data.GetValue('B4', 'value') ?? 2)
      const sat = Number(eng.data.GetValue('B21', 'value') ?? 0.8)
      const oldB3 = Number(eng.data.GetValue('B3', 'value') ?? 0)
      const physCap = Math.max(0, Math.min(Math.floor(area * 25), hc * 600) + Math.max(0, Math.round((2 - cost) * 200)))
      const slack = sat >= 0.6 ? 1.0 : 0.5 + (sat / 0.6) * 0.5
      const raw = Math.round(physCap * slack)
      const newB3 = Math.max(0, Math.round((oldB3 + raw) / 2))
      console.log(`  [#${seq}] Entangle  →B3 ← physCap=${physCap} B21=${sat.toFixed(3)} slack=${slack.toFixed(3)} raw=${raw} old=${oldB3} → B3=${newB3}`)
      return newB3
    }
    for (const c of ['B14', 'B24', 'B4', 'B21']) {
      eng.config.useEntangle({
        cause: c, impact: 'B3', via: ['value'],
        emit: (_src: any, _tgt: any, propose: any) => {
          const v = computeB3()
          propose.set('value', v, 1)
        },
      } as any)
    }

    // B4 加工成本 (SetRules B3, C1)
    eng.config.SetRules(['B3', 'C1'], 'B4', 'value', {
      logic: ({ slot }: any) => {
        seq++; const cap = Number(slot.triggerTargets[0]?.value ?? 0); const exp = Number(slot.triggerTargets[1]?.value ?? 0)
        const base = Math.max(0.1, 2 - cap * 0.0002); const r = Math.max(0.1, base * (1 - exp * 0.002))
        console.log(`  [#${seq}] SetRule B4  ← B3=${cap} C1=${exp}  → B4=${r.toFixed(3)}`)
        return r
      }, triggerKeys: ['value', 'value'],
    } as any)

    // B2 需求
    eng.config.SetRules(['B1','B15','B13','B17','B19'], 'B2', 'value', {
      logic: ({ slot }: any) => {
        seq++; const p = slot.triggerTargets[0]?.value ?? 12; const g = slot.triggerTargets[1]?.value ?? 5
        const m = slot.triggerTargets[2]?.value ?? 0; const s = slot.triggerTargets[3]?.value ?? 0
        const b = slot.triggerTargets[4]?.value ?? 0
        const pb = p < 15 ? 1+(15-p)*0.2 : 1
        const tr = Math.round(150*Math.pow(g,1.7)) + Math.round(Math.sqrt(Math.max(0,m))*15*pb)
        const loc = g*1.5; const bp = b*0.5; const maxAcc = 10+loc+bp
        const ret = p <= maxAcc ? 0.5+(maxAcc-p)/maxAcc*0.4 : Math.max(0.05, 0.5*(maxAcc/p))
        const r = Math.max(0, Math.round(tr*ret) - Math.round(Math.round(tr*ret)*s*0.5))
        console.log(`  [#${seq}] SetRule B2  ← B1=${p} B15=${g} B13=${m} B17=${s} B19=${b}  → B2=${r}`)
        return r
      }, triggerKeys: ['value','value','value','value','value'],
    } as any)

    // B21 满意度
    eng.config.SetRules(['B9','B3','B14','B24'], 'B21', 'value', {
      logic: ({ slot }: any) => {
        seq++; const labor = slot.triggerTargets[0]?.value ?? 15000; const eff = slot.triggerTargets[1]?.value ?? 1000
        const area = slot.triggerTargets[2]?.value ?? 80; const hc = slot.triggerTargets[3]?.value ?? 5
        const grade = Number(eng.data.GetValue('B15','value') ?? 5); const cost = Number(eng.data.GetValue('B4','value') ?? 2)
        const phys = Math.max(0, Math.min(Math.floor(area*25), hc*600) + Math.max(0, Math.round((2-cost)*200)))
        const ppo = labor / Math.max(eff,1); const baseLine = 3+grade*0.4
        const ps = ppo >= baseLine ? 0.7+Math.min((ppo-baseLine)/(baseLine*2),0.3) : ppo/baseLine*0.7
        const util = eff / Math.max(phys,1); const ov = Math.max(0, util-0.8)*1.5
        const r = Math.round(Math.min(1, Math.max(0, ps-ov))*1000)/1000
        console.log(`  [#${seq}] SetRule B21 ← B9=${labor} B3=${eff} B14=${area} B24=${hc} B15=${grade} B4=${cost}  phys=${phys} ppo=${ppo.toFixed(2)} ps=${ps.toFixed(3)} util=${util.toFixed(3)} ov=${ov.toFixed(3)} → B21=${r}`)
        return r
      }, triggerKeys: ['value','value','value','value'],
    } as any)

    // B20 口味
    eng.config.SetRules(['B21','B3','B14','C1'], 'B20', 'value', {
      logic: ({ slot }: any) => {
        seq++; const sat = slot.triggerTargets[0]?.value ?? 0.8; const cap = slot.triggerTargets[1]?.value ?? 1000
        const area = slot.triggerTargets[2]?.value ?? 80; const exp = slot.triggerTargets[3]?.value ?? 0
        const util = cap/Math.max(area*25,1)
        const t = sat >= 0.6 ? Math.min(1, Math.max(0.3, 1-Math.max(0,util-0.9)*0.5)) : sat*0.6
        const r = Math.round(Math.min(1, t*(1+exp*0.004))*1000)/1000
        console.log(`  [#${seq}] SetRule B20 ← B21=${sat.toFixed(3)} B3=${cap} B14=${area} C1=${exp}  util=${util.toFixed(3)} → B20=${r}`)
        return r
      }, triggerKeys: ['value','value','value','value'],
    } as any)

    // B22 维护
    eng.config.SetRule('B3', 'B22', 'value', {
      logic: ({ slot }: any) => {
        seq++; const cap = slot.triggerTargets[0]?.value ?? 0; const r = Math.max(0, (cap-500)*0.5)
        console.log(`  [#${seq}] SetRule B22 ← B3=${cap} → B22=${r}`)
        return r
      }, triggerKeys: ['value'],
    } as any)

    // B27 离职率
    eng.config.SetRules(['B21','B25'], V3.TURNOVER, 'value', {
      logic: ({ slot }: any) => {
        seq++; const sat = slot.triggerTargets[0]?.value ?? 0.8; const tr = slot.triggerTargets[1]?.value ?? 0
        const sd = (1-sat)*0.15; const trr = tr*0.0001
        const r = Math.max(0.01, Math.min(0.20, sd-trr))
        console.log(`  [#${seq}] SetRule C2(B27) ← B21=${sat.toFixed(3)} B25=${tr}  satDriven=${sd.toFixed(4)} → C2=${r.toFixed(3)}`)
        return r
      }, triggerKeys: ['value','value'],
    } as any)

    // setCellFormula 节点
    engine.setCellFormula('B23', '=B10*(1-MIN(0.3,B3*0.00005))')
    engine.setCellFormula('B6', '=B1*MIN(B2,B3)')
    engine.setCellFormula('B12', '=(B23+B11+B4)*B3')
    engine.setCellFormula('B7', '=B12+B5+B9+B13+B22')
    engine.setCellFormula('B8', '=B6-B7')

    // ===== 初始化 =====
    eng.data.SilentSet('B1', 'value', 28); eng.data.SilentSet('B1', 'formula', '')
    eng.data.SilentSet('B4', 'value', 2); eng.data.SilentSet('B4', 'formula', '')
    eng.data.SilentSet('B10', 'value', 3); eng.data.SilentSet('B10', 'formula', '')
    eng.data.SilentSet('B11', 'value', 1); eng.data.SilentSet('B11', 'formula', '')
    eng.data.SilentSet('B13', 'value', 6000); eng.data.SilentSet('B13', 'formula', '')
    eng.data.SilentSet('B14', 'value', 120); eng.data.SilentSet('B14', 'formula', '')
    eng.data.SilentSet('B15', 'value', 9); eng.data.SilentSet('B15', 'formula', '')
    eng.data.SilentSet('B17', 'value', 0); eng.data.SilentSet('B17', 'formula', '')
    eng.data.SilentSet('B18', 'value', 0); eng.data.SilentSet('B18', 'formula', '')
    eng.data.SilentSet('B19', 'value', 0); eng.data.SilentSet('B19', 'formula', '')
    eng.data.SilentSet('B20', 'value', 0.8); eng.data.SilentSet('B20', 'formula', '')
    eng.data.SilentSet('B21', 'value', 0.8); eng.data.SilentSet('B21', 'formula', '')
    const cap_init = Math.max(0, Math.min(Math.floor(120*25), 3*600))
    eng.data.SilentSet('B3', 'value', cap_init); eng.data.SilentSet('B3', 'formula', '')
    eng.data.SilentSet('B22', 'value', Math.max(0, (cap_init-500)*0.5)); eng.data.SilentSet('B22', 'formula', '')
    eng.data.SilentSet('B24', 'value', 3); eng.data.SilentSet('B24', 'formula', '')
    eng.data.SilentSet('B25', 'value', 500); eng.data.SilentSet('B25', 'formula', '')
    eng.data.SilentSet(V3.EXP, 'value', 0); eng.data.SilentSet(V3.EXP, 'formula', '')
    eng.data.SilentSet(V3.TURNOVER, 'value', 0.01); eng.data.SilentSet(V3.TURNOVER, 'formula', '')
    eng.data.SilentSet(V3.HR_COST, 'value', 0); eng.data.SilentSet(V3.HR_COST, 'formula', '')

    // 预先写 B16 以防 B2/B6 读不到
    const b2_init = 3125
    eng.data.SilentSet('B16', 'value', b2_init)
    eng.data.SilentSet('B16', 'formula', '')

    console.log(`\n  📋 初始化完成: B1=28 B3=${cap_init} B4=2.0 B14=120 B15=9 B21=0.8 B24=3 B25=500 C1=0`)
    console.log(`\n  ═══ notifyAll 传播链 ═══\n`)

    seq++ // 标记 notifyAll
    await eng.config.notifyAll()
    await new Promise(r => setTimeout(r, 20))

    console.log(`\n  ═══ 传播结束 ═══\n`)
    
    // 最终值
    for (const n of ['B2','B3','B4','B5','B6','B7','B8','B9','B12','B20','B21','B22','B23','C2']) {
      console.log(`  ${n} = ${eng.data.GetValue(n, 'value')}`)
    }
  })
})
