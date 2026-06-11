"""
ref_model_v3.py — 面包店 V3 员工管理 Python 参考模型
====================================================
完全镜像引擎 V3 公式和传播顺序 (engine-vs-python-v2.test.ts)

引擎传播架构:
  ┌─ notifyAll(月1) / SetValues(月2~12) ───┐
  │   SetRules 批处理 → 纠缠批处理 →        │
  │   触发 SetRules 重算 → 纠缠重算...      │
  │   (依赖图传播直到稳定 ≈5轮)              │
  └─────────────────────────────────────────┘

关键: 模拟引擎的异步传播收敛，B21→B3纠缠阻尼平滑
"""
import math


def compute_physical_capacity(area, headcount, processing_cost):
    """B3 物理产能 = min(areaCap=area×25, laborCap=hc×600) + effBonus(2-cost)×200"""
    if area <= 0 or headcount <= 0:
        return 0
    area_cap = int(area * 25)
    labor_cap = headcount * 600
    hw_cap = min(area_cap, labor_cap)
    eff_bonus = max(0, round((2 - processing_cost) * 200))
    return max(0, hw_cap + eff_bonus)


def compute_b3_effective(physical_cap, satisfaction, old_effective):
    """引擎纠缠中的 computeB3Effective(): 阻尼平滑"""
    if satisfaction >= 0.6:
        slack = 1.0
    else:
        slack = 0.5 + (satisfaction / 0.6) * 0.5
    raw = round(physical_cap * slack)
    old = old_effective if old_effective > 0 else physical_cap
    return max(0, round((old + raw) / 2))


def compute_rent(area, grade):
    return max(0, round(area * grade * max(2, 20 - area * 0.05)))


def compute_demand(price, grade, marketing, shortage, brand):
    price_boost = 1.0 + (15 - price) * 0.2 if price < 15 else 1.0
    traffic = round(150 * grade ** 1.7) + round(
        math.sqrt(max(0, marketing)) * 15 * price_boost
    )
    loc_prem = grade * 1.5
    brand_prem = brand * 0.5
    max_acc = 10 + loc_prem + brand_prem
    if price <= max_acc:
        retention = 0.5 + (max_acc - price) / max_acc * 0.4
    else:
        retention = max(0.05, 0.5 * (max_acc / price))
    base = round(traffic * retention)
    penalty = round(base * shortage * 0.5)
    return max(0, base - penalty)


def compute_wage(headcount, grade):
    """B9 规模稀释: B24×1200×(1+等级溢价×稀释系数)"""
    premium = grade * 0.15
    dilution = max(0, 1 - headcount * 0.08)
    return round(headcount * 1200 * (1 + premium * dilution))


def compute_satisfaction(wage, effective_cap, area, headcount, grade, processing_cost):
    """B21 过劳用物理产能分母"""
    area_cap = int(area * 25)
    labor_cap = headcount * 600
    physical_cap = max(0, min(area_cap, labor_cap) +
                       max(0, round((2 - processing_cost) * 200)))
    pay_per_output = wage / max(effective_cap, 1)
    pay_baseline = 3.0 + grade * 0.4
    if pay_per_output >= pay_baseline:
        pay_sat = 0.7 + min((pay_per_output - pay_baseline) / (pay_baseline * 2), 0.3)
    else:
        pay_sat = pay_per_output / pay_baseline * 0.7
    utilization = effective_cap / max(physical_cap, 1)
    overwork = max(0, utilization - 0.8) * 1.5
    return round(min(1, max(0, pay_sat - overwork)) * 1000) / 1000


def compute_processing_cost(capacity, exp):
    """B4 = max(0.1, 2−cap×0.0002)×(1−exp×0.002)"""
    base = max(0.1, 2 - capacity * 0.0002)
    return max(0.1, round(base * (1 - exp * 0.002) * 10) / 10)


def compute_taste(satisfaction, effective_cap, area, exp):
    """B20 口味 = f(满意度, 超负荷, 经验)"""
    utilization = effective_cap / max(area * 25, 1)
    if satisfaction >= 0.6:
        overload = max(0, utilization - 0.9) * 0.5
        taste = min(1, max(0.3, 1.0 - overload))
    else:
        taste = satisfaction * 0.6
    return round(min(1, taste * (1 + exp * 0.004)) * 1000) / 1000


def compute_maintenance(cap):
    return max(0, (cap - 500) * 0.5)


def compute_actual_material(base_cost, capacity):
    discount = min(0.3, capacity * 0.00005)
    return round(base_cost * (1 - discount), 2)


def compute_turnover_rate(satisfaction, training):
    sat_driven = (1 - satisfaction) * 0.15
    training_reduction = training * 0.0001
    return max(0.01, min(0.20, sat_driven - training_reduction))


def compute_brand(old_brand, taste, grade, marketing):
    traffic = round(150 * grade ** 1.7) + round(math.sqrt(max(0, marketing)) * 15)
    growth = round(taste * (traffic / 100 + 10))
    decay_rate = max(0.05, old_brand * 0.01)
    decay = round(old_brand * decay_rate)
    return max(0, old_brand + growth - decay)


def engine_v3_month(m, params, state):
    """模拟引擎V3单月: 异步传播收敛 (依赖图迭代≈5轮)"""
    B1 = params['B1']
    B24 = params['B24']
    B25 = params['B25']
    B13 = params['B13']
    B14 = params['B14']
    B15 = params['B15']
    B10 = 3
    B11 = 1

    # 初始状态
    B4 = state.get('B4', 2.0)
    B3 = state.get('B3', compute_physical_capacity(B14, B24, B4))
    B21 = state.get('B21', 0.8)
    C1 = state.get('C1', 0)
    B19 = state.get('B19', 0)
    B17 = state.get('B17', 0)
    prev_hc = state.get('prev_headcount', B24)

    # === 引擎传播迭代 ≈5轮 ===
    # 模拟 SetRules + 纠缠依赖图 fan-out
    for iteration in range(6):
        changed = False

        # B5 房租 (只会变如果B14/B15变, 这里不变)
        B5 = compute_rent(B14, B15)

        # B9 工资 (SetRule B24, 不变)
        B9 = compute_wage(B24, B15)

        # 物理产能 (B14/B24/B4 → 纠缠)
        old_phys = B3  # 用当前有效产能做 old
        physical_cap = compute_physical_capacity(B14, B24, B4)
        new_b3 = compute_b3_effective(physical_cap, B21, old_phys)
        if new_b3 != B3:
            changed = True
            B3 = new_b3

        # B4 加工成本 (SetRules B3, C1)
        new_b4 = compute_processing_cost(B3, C1)
        if abs(new_b4 - B4) > 0.001:
            changed = True
            B4 = new_b4

        # B21 满意度 (SetRules B9, B3, B14, B24)
        new_b21 = compute_satisfaction(B9, B3, B14, B24, B15, B4)
        if new_b21 != B21:
            changed = True
            B21 = new_b21

        # B20 口味 (SetRules B21, B3, B14, C1)
        B20 = compute_taste(B21, B3, B14, C1)

        if not changed:
            break

    # 收敛后计算最终节点
    # B2 需求
    B2 = compute_demand(B1, B15, B13, B17, B19)

    # B23 原料折扣
    B23 = compute_actual_material(B10, B3)

    # B6 收入 = B1 × min(B2, B3) — SetRules
    B6 = B1 * min(B2, B3)

    # B22 维护
    B22 = compute_maintenance(B3)

    # B12 生产成本 — SetRules
    B12 = (B23 + B11 + B4) * B3

    # B7 总成本 — SetRules
    B7 = B12 + B5 + B9 + B13 + B22

    # B8 月利润 — SetRules
    B8 = B6 - B7

    # B17/B18
    B17_new = 0.0 if B3 >= B2 or B2 <= 0 else round((B2 - B3) / B2 * 1000) / 1000
    B18_new = 0.0 if B3 <= B2 or B3 <= 0 else round((B3 - B2) / B3 * 1000) / 1000

    # B19 品牌 — advanceMonth
    B19_new = compute_brand(B19, B20, B15, B13)

    # C1 经验
    turnover_rate = compute_turnover_rate(B21, B25)
    loss_rate = turnover_rate * (1 + (1 - B21) * 0.6)
    training_effect = B25 / (10 + C1 * 2)
    C1_new = max(0, min(200, round((C1 * (1 - loss_rate) + training_effect) * 10) / 10))

    # C3 人事成本
    net_change = B24 - prev_hc
    hiring = max(0, net_change) * 1500
    severance = abs(min(0, net_change)) * 1000
    replacement = turnover_rate * B24 * 1500
    C3 = round(hiring + severance + replacement)

    # 最终利润
    training_cost = B25 * B24
    profit = round(B8 - training_cost - C3)

    return {
        'B1': B1, 'B2': B2, 'B3': B3, 'B4': B4,
        'B5': B5, 'B6': B6, 'B7': round(B7, 2),
        'B8': round(B8, 2), 'B9': B9,
        'B12': B12, 'B13': B13, 'B14': B14, 'B15': B15,
        'B17': B17_new, 'B18': B18_new, 'B19': B19_new,
        'B20': B20, 'B21': B21, 'B22': B22, 'B23': B23,
        'B24': B24, 'B25': B25,
        'C1': C1_new, 'C2': compute_turnover_rate(B21, B25), 'C3': C3,
        'profit': profit, 'training_cost': training_cost,
        'B6_raw': B6, 'B7_raw': B7, 'B8_raw': B8,
        'prev_headcount': B24,
    }


def engine_v3_year(params):
    months = []
    state = {
        'B4': 2.0, 'B21': 0.8, 'B20': 0.8,
        'C1': 0, 'B19': 0, 'B17': 0,
        'prev_headcount': params['B24'],
    }
    physical_cap = compute_physical_capacity(params['B14'], params['B24'], 2.0)
    state['B3'] = physical_cap  # 引擎 SilentSet 初值

    for m in range(1, 13):
        result = engine_v3_month(m, params, state)
        months.append(result)
        # 跨月状态
        state['C1'] = result['C1']
        state['B19'] = result['B19']
        state['B17'] = result['B17']
        state['B21'] = result['B21']
        state['B3'] = result['B3']
        state['B4'] = result['B4']
        state['prev_headcount'] = result['prev_headcount']

    return months


SCENARIOS = [
    { 'label': '✨ 高奢·精兵', 'B1': 28, 'B24': 3, 'B25': 500, 'B13': 6000, 'B14': 120, 'B15': 9 },
    { 'label': '🏭 大厂·标准', 'B1': 16, 'B24': 8, 'B25': 100, 'B13': 2000, 'B14': 150, 'B15': 7 },
    { 'label': '🏠 社区·基本', 'B1': 16, 'B24': 3, 'B25': 0,   'B13': 0,    'B14': 60,  'B15': 5 },
]

if __name__ == '__main__':
    for s in SCENARIOS:
        print(f"\n{'='*60}")
        print(f'  {s["label"]}')
        print(f'  B1={s["B1"]} B24={s["B24"]} B25={s["B25"]} B13={s["B13"]:,} B14={s["B14"]} B15={s["B15"]}')
        print(f"{'='*60}")
        months = engine_v3_year(s)
        for m, r in enumerate(months):
            label = f'月{m+1}'
            print(f'  {label:>3} | B3={r["B3"]:>5} B4={r["B4"]:.2f} B9={r["B9"]:>5} B21={r["B21"]:.3f} B20={r["B20"]:.3f} B2={r["B2"]:>4} B6={r["B6"]:>8} B8={r["B8"]:>+8} C1={r["C1"]:>5} C3={r["C3"]:>4} profit={r["profit"]:>+6}')
        profits = [r['profit'] for r in months]
        print(f'  年利润: +{sum(profits):>+8,}')
        print(f'  逐月利润: {", ".join(str(p) for p in profits)}')
