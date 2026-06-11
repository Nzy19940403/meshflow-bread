"""
ref_model_v4.py — 面包店 V4 疲劳模型
=====================================
核心改动: 用「疲劳值 C4」取代 B21→slack 的实时反馈

疲劳机制:
  C4 ∈ [0, 100], 初始=40
  C4 < 20 → 士气爆发, slack=1.1(超物理上限)
  C4 20-60 → 正常, slack=1.0
  C4 60-80 → 开始摸鱼, slack=0.7~1.0(线性)
  C4 > 80 → 严重摸鱼, slack=0.5~0.7(线性)

  疲劳变化(每月):
    +过劳: (utilization - 0.8) × 50  当利用率>80%
    -培训: B25 × 0.02
    -满意度: (B21 - 0.5) × 20
    -工资: (B9/人均 - 1500) × 0.005
"""
import math


# ===== 疲劳相关 =====

def slack_from_fatigue(c4):
    """C4 → slack系数: 低疲劳爆发, 高疲劳摸鱼"""
    if c4 < 20:
        # 士气爆发: 越接近0越猛
        return 1.0 + (20 - c4) / 20 * 0.1  # 1.0 ~ 1.1
    elif c4 < 60:
        return 1.0
    elif c4 < 80:
        # 60→1.0, 80→0.7
        return 1.0 - (c4 - 60) / 20 * 0.3
    else:
        # 80→0.7, 100→0.5
        return 0.7 - (c4 - 80) / 20 * 0.2


def fatigue_delta(utilization, b25, b21, pay_per_person, c4=40):
    """计算每月疲劳变化量"""
    delta = 0.0
    # 过劳增疲劳
    if utilization > 0.8:
        delta += (utilization - 0.8) * 50
    # 培训减疲劳
    delta -= b25 * 0.02
    # 满意度减疲劳 — 疲劳越低效果越差
    sat_recovery = max(0, b21 - 0.5) * 20
    # 疲劳越低, 恢复效果越弱 (C4=40时100%, C4=0时0%)
    fatigue_factor = c4 / 40.0 if c4 < 40 else 1.0
    delta -= sat_recovery * fatigue_factor
    # 高工资减疲劳 — 同样受 fatigue_factor 影响
    if pay_per_person > 1500:
        delta -= (pay_per_person - 1500) * 0.005 * fatigue_factor
    return delta


# ===== 核心公式（同 V3） =====

def compute_physical_capacity(area, headcount, processing_cost):
    area_cap = int(area * 25)
    labor_cap = headcount * 600
    hw_cap = min(area_cap, labor_cap)
    eff_bonus = max(0, round((2 - processing_cost) * 200))
    return max(0, hw_cap + eff_bonus)


def compute_effective_capacity(physical_cap, c4):
    """B3 = 物理产能 × slack(C4) — 不再依赖B21"""
    return max(0, round(physical_cap * slack_from_fatigue(c4)))


def compute_rent(area, grade):
    return max(0, round(area * grade * max(2, 20 - area * 0.05)))


def compute_demand(price, grade, marketing, shortage, brand):
    price_boost = 1.0 + (15 - price) * 0.2 if price < 15 else 1.0
    traffic = round(150 * grade ** 1.7) + round(
        math.sqrt(max(0, marketing)) * 15 * price_boost
    )
    max_acc = 10 + grade * 1.5 + brand * 0.5
    if price <= max_acc:
        retention = 0.5 + (max_acc - price) / max_acc * 0.4
    else:
        retention = max(0.05, 0.5 * (max_acc / price))
    base = round(traffic * retention)
    penalty = round(base * shortage * 0.5)
    return max(0, base - penalty)


def compute_wage(headcount, grade):
    premium = grade * 0.15
    dilution = max(0, 1 - headcount * 0.08)
    return round(headcount * 1200 * (1 + premium * dilution))


def compute_satisfaction(wage, effective_cap, area, headcount, grade, processing_cost):
    """B21 — 仅用于计算疲劳恢复, 不再影响产能"""
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
    base = max(0.1, 2 - capacity * 0.0002)
    return max(0.1, round(base * (1 - exp * 0.002) * 10) / 10)


def compute_taste(satisfaction, effective_cap, area, exp):
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


# ===== V4 月度推演（迭代直到收敛） =====

def v4_month(m, params, state):
    B1 = params['B1']; B24 = params['B24']; B25 = params['B25']
    B13 = params['B13']; B14 = params['B14']; B15 = params['B15']
    B10 = 3; B11 = 1

    B4 = state.get('B4', 2.0)
    C1 = state.get('C1', 0)
    B21 = state.get('B21', 0.8)
    B19 = state.get('B19', 0)
    B17 = state.get('B17', 0)
    prev_hc = state.get('prev_headcount', B24)
    C4 = state.get('C4', 40)  # 疲劳, 初始40

    # 物理产能
    physical_cap = compute_physical_capacity(B14, B24, B4)

    # B3 = 物理产能 × slack(C4) — 迭代直到B3和C4互洽
    B3 = state.get('B3', physical_cap)
    B5 = compute_rent(B14, B15)
    B9 = compute_wage(B24, B15)

    # 迭代: B3 ↔ B4 ↔ B21(仅影响疲劳变化) ↔ C4 → 下次B3
    for iteration in range(20):
        changed = False

        # B3 = 物理 × slack(C4)
        new_b3 = compute_effective_capacity(physical_cap, C4)
        if new_b3 != B3:
            changed = True
            B3 = new_b3

        # B4 = f(B3, C1)
        new_b4 = compute_processing_cost(B3, C1)
        if abs(new_b4 - B4) > 0.001:
            changed = True
            B4 = new_b4

        # B21 = f(B9, B3, B14, B24, B15, B4) — 只是输出,不反馈到B3
        new_b21 = compute_satisfaction(B9, B3, B14, B24, B15, B4)
        if new_b21 != B21:
            changed = True
            B21 = new_b21

        # 物理产能可能随B4变化而变化
        new_phys = compute_physical_capacity(B14, B24, B4)
        if new_phys != physical_cap:
            changed = True
            physical_cap = new_phys

        if not changed:
            break

    # 用收敛后的值计算疲劳变化和所有终端节点
    utilization = B3 / max(physical_cap, 1)
    pay_per_person = B9 / max(B24, 1)
    c4_delta = fatigue_delta(utilization, B25, B21, pay_per_person, C4)
    C4_new = max(0, min(100, round(C4 + c4_delta)))

    B20 = compute_taste(B21, B3, B14, C1)
    B2 = compute_demand(B1, B15, B13, B17, B19)
    B23 = compute_actual_material(B10, B3)
    B6 = B1 * min(B2, B3)
    B22 = compute_maintenance(B3)
    B12 = (B23 + B11 + B4) * B3
    B7 = B12 + B5 + B9 + B13 + B22
    B8 = B6 - B7

    B17_new = 0.0 if B3 >= B2 or B2 <= 0 else round((B2 - B3) / B2 * 1000) / 1000
    B18_new = 0.0 if B3 <= B2 or B3 <= 0 else round((B3 - B2) / B3 * 1000) / 1000
    B19_new = compute_brand(B19, B20, B15, B13)

    # 经验
    turnover_rate = compute_turnover_rate(B21, B25)
    loss_rate = turnover_rate * (1 + (1 - B21) * 0.6)
    training_effect = B25 / (10 + C1 * 2)
    C1_new = max(0, min(200, round((C1 * (1 - loss_rate) + training_effect) * 10) / 10))

    # 人事成本
    net_change = B24 - prev_hc
    hiring = max(0, net_change) * 1500
    severance = abs(min(0, net_change)) * 1000
    replacement = turnover_rate * B24 * 1500
    C3 = round(hiring + severance + replacement)

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
        'C4': C4_new,
        'profit': profit, 'training_cost': training_cost,
        'slack': slack_from_fatigue(C4), 'c4_delta': c4_delta,
        'physical_cap': physical_cap, 'utilization': utilization,
        'pay_per_person': pay_per_person,
        'prev_headcount': B24,
    }


def v4_year(params):
    months = []
    state = {
        'B4': 2.0, 'B21': 0.8, 'B20': 0.8,
        'C1': 0, 'C4': 40,  # 初始疲劳=40
        'B19': 0, 'B17': 0,
        'prev_headcount': params['B24'],
    }
    physical_cap = compute_physical_capacity(params['B14'], params['B24'], 2.0)
    state['B3'] = physical_cap

    for m in range(1, 13):
        result = v4_month(m, params, state)
        months.append(result)
        state['C1'] = result['C1']
        state['C4'] = result['C4']
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
        months = v4_year(s)
        for m, r in enumerate(months):
            label = f'月{m+1}'
            print(f'  {label:>3} | B3={r["B3"]:>5} B4={r["B4"]:.2f} C4={r["C4"]:>3} '
                  f'slack={r["slack"]:.3f} B21={r["B21"]:.3f} '
                  f'B6={r["B6"]:>8} B8={r["B8"]:>+8} '
                  f'C1={r["C1"]:>5} C3={r["C3"]:>4} profit={r["profit"]:>+6}')
        profits = [r['profit'] for r in months]
        print(f'  年利润: {sum(profits):>+8,}')
        print(f'  逐月: {", ".join(str(p) for p in profits)}')
