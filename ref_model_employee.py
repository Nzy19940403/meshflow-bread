"""
ref_model_employee.py — 员工管理模型 V3
=========================================
Gemini 防死循环方案：
  1. B3 物理产能 = B24×600 + efficiencyBonus
  2. 怠工系数 = f(B21): 满意≥0.6→100%, 极不满→50%
  3. 有效产能 = 物理产能 × 怠工系数
  4. B21 过劳惩罚用物理产能算，不用有效产能（防死循环）
"""

import math
import sys
sys.path.insert(0, '.')
from ref_model import *


# ============================================================
# 参数
# ============================================================

# 薪酬
BASE_WAGE = 1200
GRADE_WAGE_MULT = 0.15
SIZE_DILUTION_RATE = 0.08

# 产能
PERSONAL_CAPACITY_RATE = 600   # 每人每月最多烤600个面包（物理极限）

# 培训与经验
EXPERIENCE_COST_REDUCTION = 0.002    # 每点经验降B4 0.2%
EXPERIENCE_TASTE_BOOST = 0.004       # 每点经验升B20 0.4%

# 离职
TURNOVER_MIN = 0.01
TURNOVER_SAT_FACTOR = 0.15
TURNOVER_TRAINING_REDUCE = 0.0001

# 人事成本
HIRING_COST = 1500
SEVERANCE_COST = 1000
REPLACEMENT_COST = 1500

# 经验增益（渐进函数用）
EXPERIENCE_SAT_DECAY_MOD = 0.6


# ============================================================
# 核心公式
# ============================================================

def compute_labor_cost_v3(headcount: int, grade: float) -> float:
    """B9 V3: 规模稀释"""
    premium = grade * GRADE_WAGE_MULT
    dilution = max(0, 1 - headcount * SIZE_DILUTION_RATE)
    return headcount * BASE_WAGE * (1 + premium * dilution)


def compute_physical_capacity(
    headcount: int, area: float, processing_cost: float
) -> int:
    """B3 物理产能 = 人数×600 + 效率加成
    
    跟工资完全解耦，只跟人头数和加工技术有关。
    """
    if headcount <= 0 or area <= 0:
        return 0
    area_cap = int(area * 25)           # 面积上限
    labor_cap = headcount * PERSONAL_CAPACITY_RATE  # 人工上限（用人数，不用工资）
    efficiency_bonus = max(0, round((2 - processing_cost) * 200))
    hardware_cap = min(area_cap, labor_cap)
    return max(0, hardware_cap + efficiency_bonus)


def compute_slacking_coefficient(satisfaction: float) -> float:
    """怠工系数: 满意度B21决定员工出几分力
    
    B21 >= 0.6: 正常干活, 系数=1.0
    B21 < 0.6:  摸鱼, 线性下降到最低50%
    """
    if satisfaction >= 0.6:
        return 1.0
    return 0.5 + (satisfaction / 0.6) * 0.5


def compute_effective_capacity(
    physical_capacity: int, slacking_coeff: float
) -> int:
    """有效产能 = 物理产能 × 怠工系数"""
    return max(0, round(physical_capacity * slacking_coeff))


def compute_satisfaction_v3(
    labor: float, effective_capacity: int, physical_capacity: int,
    area: float, grade: float
) -> float:
    """B21 V3: 满意度 — 过劳惩罚用物理产能（防死循环）"""
    pay_per_output = labor / max(effective_capacity, 1)
    # 过劳用物理产能算，不是有效产能！
    utilization = effective_capacity / max(area * 25, 1)
    
    pay_baseline = 3.0 + grade * 0.4
    if pay_per_output >= pay_baseline:
        pay_sat = 0.7 + min((pay_per_output - pay_baseline) / (pay_baseline * 2), 0.3)
    else:
        pay_sat = pay_per_output / pay_baseline * 0.7
    
    # 过劳惩罚——用物理产能做分母
    physical_utilization = effective_capacity / max(physical_capacity, 1)
    overwork_penalty = max(0, physical_utilization - 0.8) * 1.5
    
    return round(min(1, max(0, pay_sat - overwork_penalty)) * 1000) / 1000


def compute_experience_v3(
    prev_exp: float, turnover_rate: float,
    training_per_head: float, satisfaction: float
) -> float:
    """B26 V3: 渐进函数"""
    loss_rate = turnover_rate * (1 + (1 - satisfaction) * EXPERIENCE_SAT_DECAY_MOD)
    training_effect = training_per_head / (10 + prev_exp * 2)
    new_exp = prev_exp * (1 - loss_rate) + training_effect
    return round(min(200, max(0, new_exp)), 1)


def compute_turnover_rate_v3(satisfaction: float, training_per_head: float) -> float:
    """B27 离职率"""
    sat_driven = (1 - satisfaction) * TURNOVER_SAT_FACTOR
    training_reduction = training_per_head * TURNOVER_TRAINING_REDUCE
    return max(TURNOVER_MIN, min(0.20, sat_driven - training_reduction))


def compute_hr_costs_v3(
    prev_headcount: int, current_headcount: int, turnover_rate: float
) -> float:
    """B28 人事成本"""
    net = current_headcount - prev_headcount
    return (max(0, net) * HIRING_COST
            + abs(min(0, net)) * SEVERANCE_COST
            + turnover_rate * current_headcount * REPLACEMENT_COST)


def processing_cost_with_exp(base_cost: float, experience: float) -> float:
    """B4 经验降成本"""
    return max(0.1, base_cost * (1 - experience * EXPERIENCE_COST_REDUCTION))


def taste_with_experience_v3(base_taste: float, experience: float) -> float:
    """B20 经验提品质"""
    return round(min(1, base_taste * (1 + experience * EXPERIENCE_TASTE_BOOST)) * 1000) / 1000


# ============================================================
# V3 月度推演
# ============================================================

def simulate_month_v3(
    price, material_cost, other_cost, marketing, area, grade,
    target_headcount, training_per_head,
    prev_experience=0, prev_headcount=0,
    brand=0, shortage_rate=0,
    use_seasonal=False, month=1,
):
    """单月推演 V3"""
    
    # B9 工资（规模稀释）
    labor_cost = compute_labor_cost_v3(target_headcount, grade)
    
    # B5 房租
    rent = compute_rent(area, grade)
    
    # B3↔B4 收敛（物理产能）
    processing_cost = 2.0
    physical_cap = compute_physical_capacity(target_headcount, area, processing_cost)
    for _ in range(10):
        processing_cost = compute_processing_cost(physical_cap)
        processing_cost = processing_cost_with_exp(processing_cost, prev_experience)
        new_cap = compute_physical_capacity(target_headcount, area, processing_cost)
        if new_cap == physical_cap:
            break
        physical_cap = new_cap
    
    # B21 满意度（首次算时需要有效产能，先假设无怠工）
    slack = 1.0
    effective_cap = physical_cap  # 初值
    
    # 迭代：满意度↔怠工↔有效产能
    for _ in range(5):
        satisfaction = compute_satisfaction_v3(
            labor_cost, effective_cap, physical_cap, area, grade
        )
        slack = compute_slacking_coefficient(satisfaction)
        effective_cap = compute_effective_capacity(physical_cap, slack)
        if slack >= 0.99 or slack <= 0.51:
            break  # 收敛了
    
    # B20 口味
    taste = compute_taste(satisfaction, effective_cap, area)
    taste = taste_with_experience_v3(taste, prev_experience)
    
    # B2 需求
    demand = compute_demand(price, grade, marketing, shortage_rate, brand)
    if use_seasonal:
        demand = max(0, round(demand * SEASONAL_FACTORS[month - 1]))
    
    # B27 离职率
    turnover = compute_turnover_rate_v3(satisfaction, training_per_head)
    
    # B26 经验
    experience = compute_experience_v3(prev_experience, turnover, training_per_head, satisfaction)
    
    # B28 人事成本
    hr_cost = compute_hr_costs_v3(prev_headcount, target_headcount, turnover)
    
    # 财务
    actual_sales = min(demand, effective_cap)
    revenue = price * actual_sales
    actual_material = compute_actual_material_cost(material_cost, effective_cap)
    prod_cost = (actual_material + other_cost + processing_cost) * effective_cap
    maintenance = max(0, (effective_cap - 500) * 0.5)
    total_cost = (prod_cost + rent + labor_cost + marketing + maintenance
                  + training_per_head * target_headcount + hr_cost)
    profit = revenue - total_cost
    
    new_shortage = compute_shortage_rate(demand, effective_cap)
    new_waste = compute_waste_rate(demand, effective_cap)
    new_brand = compute_brand(brand, taste, grade, marketing)
    
    return {
        'B2_demand': demand,
        'B3_physical': physical_cap,
        'B3_effective': effective_cap,
        'B4_processing_cost': round(processing_cost, 4),
        'B5_rent': rent,
        'B6_revenue': revenue,
        'B7_total_cost': total_cost,
        'B8_profit': profit,
        'B9_labor': labor_cost,
        'B20_taste': taste,
        'B21_satisfaction': satisfaction,
        'B21_slack': slack,
        'B22_maintenance': maintenance,
        'B23_actual_material': actual_material,
        'B24_headcount': target_headcount,
        'B25_training': training_per_head,
        'B26_experience': experience,
        'B27_turnover': turnover,
        'B28_hr_cost': hr_cost,
        'B17_shortage_rate': new_shortage,
        'B18_waste_rate': new_waste,
        'B19_brand': new_brand,
    }


def simulate_year_v3(
    price, material_cost=3, other_cost=1, marketing=0,
    area=60, grade=5,
    target_headcount=5, training_per_head=0,
    use_seasonal=False
):
    """一年推演 V3"""
    brand, shortage_rate = 0, 0
    prev_exp, prev_headcount = 0, target_headcount
    months = []
    
    for m in range(1, 13):
        r = simulate_month_v3(
            price, material_cost, other_cost, marketing, area, grade,
            target_headcount, training_per_head,
            prev_experience=prev_exp, prev_headcount=prev_headcount,
            brand=brand, shortage_rate=shortage_rate,
            use_seasonal=use_seasonal, month=m,
        )
        r['month'] = m
        months.append(r)
        brand = r['B19_brand']
        shortage_rate = r['B17_shortage_rate']
        prev_exp = r['B26_experience']
        prev_headcount = target_headcount
    
    return {
        'months': months,
        'annual_profit': sum(m['B8_profit'] for m in months),
        'final_experience': prev_exp,
        'final_brand': brand,
    }


# ============================================================
# 验证
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("  员工管理模型 V3 — Gemini 防死循环方案")
    print("=" * 60)
    
    scenarios = [
        # ✨ 高奢
        ("✨ 高奢·精兵(3人¥500培训)",
         dict(price=28, marketing=6000, area=120, grade=9,
              target_headcount=3, training_per_head=500)),
        ("✨ 高奢·稳健(4人¥300培训)",
         dict(price=28, marketing=6000, area=120, grade=9,
              target_headcount=4, training_per_head=300)),
        ("✨ 高奢·压工资(3人不培训)",
         dict(price=28, marketing=6000, area=120, grade=9,
              target_headcount=3, training_per_head=0)),
        
        # 🏭 大厂
        ("🏭 大厂·标准(8人¥100培训)",
         dict(price=16, marketing=2000, area=150, grade=7,
              target_headcount=8, training_per_head=100)),
        ("🏭 大厂·精简(6人¥50培训)",
         dict(price=16, marketing=2000, area=150, grade=7,
              target_headcount=6, training_per_head=50)),
        ("🏭 大厂·抠门(8人0培训)",
         dict(price=16, marketing=2000, area=150, grade=7,
              target_headcount=8, training_per_head=0)),
        
        # 🏠 社区
        ("🏠 社区·基本(3人无培训)",
         dict(price=16, marketing=0, area=60, grade=5,
              target_headcount=3, training_per_head=0)),
        ("🏠 社区·稳住(4人¥50培训)",
         dict(price=16, marketing=0, area=60, grade=5,
              target_headcount=4, training_per_head=50)),
        ("🏠 社区·压力(3人¥100培训)",
         dict(price=16, marketing=0, area=60, grade=5,
              target_headcount=3, training_per_head=100)),
    ]
    
    print(f"\n{'='*60}")
    print(f"  九条策略对比")
    print(f"{'='*60}")
    print(f"  {'名称':<28} {'年利润':>9} {'有效/物理':>12} {'满意度':>6} {'离职率':>6} {'品牌':>5}")
    print(f"  {'-'*65}")
    
    for name, params in scenarios:
        r = simulate_year_v3(**params)
        m1 = r['months'][0]
        avg_sat = sum(x['B21_satisfaction'] for x in r['months']) / len(r['months'])
        avg_turn = sum(x['B27_turnover'] for x in r['months']) / len(r['months'])
        eff = m1['B3_effective']
        phy = m1['B3_physical']
        profit_ok = "✅" if r['annual_profit'] > 0 else "❌"
        print(f"  {name:<28} ¥{r['annual_profit']:>+8,.0f} "
              f"{eff:>4}/{phy:<4} "
              f"{avg_sat:>5.2f}  {avg_turn:>4.1%}  "
              f"{r['final_brand']:>5}  {profit_ok}")
    
    # 精选路线逐月明细
    for name, params in [
        ("✨ 高奢·精兵", dict(price=28, marketing=6000, area=120, grade=9,
                            target_headcount=3, training_per_head=500)),
        ("🏭 大厂·标准", dict(price=16, marketing=2000, area=150, grade=7,
                            target_headcount=8, training_per_head=100)),
        ("🏭 大厂·抠门", dict(price=16, marketing=2000, area=150, grade=7,
                            target_headcount=8, training_per_head=0)),
        ("🏠 社区·基本", dict(price=16, marketing=0, area=60, grade=5,
                            target_headcount=3, training_per_head=0)),
    ]:
        r = simulate_year_v3(**params)
        print(f"\n{'='*60}")
        print(f"  {name}  [年利润 ¥{r['annual_profit']:+,.0f}]")
        print(f"  B9={r['months'][0]['B9_labor']:.0f}/月  "
              f"经验终期={r['final_experience']}")
        cols = "月 需求 有效 物理  B4    收入    成本    利润  满意 怠工 离职"
        print(f"  {cols}")
        print(f"  {'-'*60}")
        for m in r['months']:
            print(f"  {m['month']:>2} {m['B2_demand']:>4} {m['B3_effective']:>4} "
                  f"{m['B3_physical']:>4} {m['B4_processing_cost']:>5.2f} "
                  f"¥{m['B6_revenue']:>6,.0f} ¥{m['B7_total_cost']:>6,.0f} "
                  f"¥{m['B8_profit']:>+6,.0f} "
                  f"{m['B21_satisfaction']:>4.2f} {m['B21_slack']:>4.2f} "
                  f"{m['B27_turnover']:>4.1%}")
