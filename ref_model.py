"""
ref_model.py — 面包店经营模拟 数学参考模型
===========================================
定位：完全镜像 MeshFlow 引擎的公式，作为数学验证的参照系。
      Python 负责：设计公式、推演验证、暴力搜索。
      MeshFlow 负责：GraphEditor 交互、实时传播、纠缠收敛。

公式来源：src/App.vue (onMounted SetRules) + src/GraphEditor.vue (advanceMonth)
"""

import math

# ============================================================
# 第〇章：常量
# ============================================================

SEASONAL_FACTORS = [1.2, 1.0, 0.9, 1.1, 1.3, 1.2, 1.0, 0.8, 0.9, 1.1, 1.1, 1.3]
"""月份季节性系数（1月=1.2元旦春节, 4月=0.9淡, 8月=0.8最淡, 12月=1.3圣诞跨年）"""


# ============================================================
# 第一章：核心公式（完全镜像 App.vue / GraphEditor.vue）
# ============================================================

def compute_rent(area: float, grade: float) -> int:
    """B5 房租 = round(面积×等级×max(2, 20−面积×0.05))"""
    return max(0, round(area * grade * max(2, 20 - area * 0.05)))


def compute_demand(
    price: float, grade: float, marketing: float,
    shortage_rate: float, brand: float
) -> int:
    """B2 需求 = 流量 × 留存率 − 缺货惩罚
    
    来源: App.vue onMounted SetRules B2
    """
    # 低价营销加成: 售价<¥15时广告效果倍增
    price_discount_boost = 1.0 + (15 - price) * 0.2 if price < 15 else 1.0
    
    traffic = round(150 * grade ** 1.7) + round(
        math.sqrt(max(0, marketing)) * 15 * price_discount_boost
    )
    
    # 品牌溢价 + 地段溢价 → 顾客可接受最高价
    brand_premium = brand * 0.5
    location_premium = grade * 1.5
    max_acceptable = 10 + location_premium + brand_premium
    
    # 留存率：价格 vs 溢价能力
    if price <= max_acceptable:
        retention = 0.5 + (max_acceptable - price) / max_acceptable * 0.4
    else:
        retention = max(0.05, 0.5 * (max_acceptable / price))
    
    base = round(traffic * retention)
    penalty = round(base * shortage_rate * 0.5)
    return max(0, base - penalty)


def compute_capacity(
    area: float, labor: float,
    processing_cost: float
) -> int:
    """B3 产能 = 物理上限（非需求约束）
    
    来源: App.vue onMounted computeB3Capacity()
    
    三条同权重共同预言:
      B14面积→B3: areaCap = floor(area×25)
      B9人工→B3:   laborCap = floor(labor/2.5)
      B4加工成本→B3: efficiencyBonus = max(0, round((2-cost)×200))
    
    B3 = min(areaCap, laborCap) + efficiencyBonus
    """
    if area <= 0 or labor <= 0:
        return 0
    area_cap = int(area * 25)
    labor_cap = int(labor / 2.5)
    hardware_cap = min(area_cap, labor_cap)
    efficiency_bonus = max(0, round((2 - processing_cost) * 200))
    return max(0, hardware_cap + efficiency_bonus)


def compute_processing_cost(capacity: float) -> float:
    """B4 加工成本 = max(0.1, 2 − B3×0.0002) 规模效应"""
    return max(0.1, 2 - capacity * 0.0002)


def compute_satisfaction(
    labor: float, capacity: int, area: float, grade: float
) -> float:
    """B21 员工满意度 = paySat − overworkPenalty
    
    来源: App.vue onMounted SetRules B21
    """
    pay_per_output = labor / max(capacity, 1)
    utilization = capacity / max(area * 25, 1)
    
    # 薪酬满意度基线 = 3.0 + 等级×0.4
    pay_baseline = 3.0 + grade * 0.4
    
    if pay_per_output >= pay_baseline:
        pay_sat = 0.7 + min((pay_per_output - pay_baseline) / (pay_baseline * 2), 0.3)
    else:
        pay_sat = pay_per_output / pay_baseline * 0.7
    
    # 过劳惩罚: 利用率超过80%开始扣
    overwork_penalty = max(0, utilization - 0.8) * 1.5
    
    return round(min(1, max(0, pay_sat - overwork_penalty)) * 1000) / 1000


def compute_taste(
    satisfaction: float, capacity: int, area: float
) -> float:
    """B20 口味/品质 = f(满意度, 超负荷)
    
    来源: App.vue onMounted SetRules B20
    """
    utilization = capacity / max(area * 25, 1)
    
    if satisfaction >= 0.6:
        overload = max(0, utilization - 0.9) * 0.5
        taste = min(1, max(0.3, 1.0 - overload))
    else:
        taste = satisfaction * 0.6
    
    return round(taste * 1000) / 1000


def compute_brand(
    old_brand: float, taste: float, grade: float, marketing: float
) -> int:
    """B19 知名度 = 上期知名度 + 增长 − 衰减
    
    来源: GraphEditor.vue advanceMonth()
    
    注意: advanceMonth 中的 traffic 不含 priceDiscountBoost
    （与 B2 SetRule 中带低价营销加成的 traffic 不同——这可能是feature也可能是bug）
    """
    traffic = round(150 * grade ** 1.7) + round(math.sqrt(max(0, marketing)) * 15)
    
    # 基础口碑发酵：即使0流量0营销，口味好也能靠街坊自发涨知名度
    mouth_growth = 10
    growth = round(taste * (traffic / 100 + mouth_growth))
    
    # 非线性衰减：知名度越高忘得越快
    decay_rate = max(0.05, old_brand * 0.01)
    decay = round(old_brand * decay_rate)
    
    return max(0, old_brand + growth - decay)


def compute_actual_material_cost(base_cost: float, capacity: int) -> float:
    """B23 实际原料单价 = B10 × (1 − min(0.3, B3 × 折扣系数))
    
    折扣系数 0.00005: 每多产 1 个降 0.005%, 上限 30%
    例: B3=1000→折扣5%, B3=3000→折扣15%, B3=6000→折扣30%(上限)
    """
    discount = min(0.3, capacity * 0.00005)
    return round(base_cost * (1 - discount), 2)


def compute_financials(
    price: float, demand: int, capacity: int,
    processing_cost: float, material_cost: float, other_cost: float,
    rent: int, labor: float, marketing: float
):
    """B6 月收入, B12 生产成本, B7 总成本, B8 月利润, B22 维护费, B23 实际原料价
    
    B23 = B10 × (1 − min(0.3, B3×0.00005))  批量折扣
    B12 = (B23 + B11 + B4) × B3              生产成本改用折扣后原料价
    B22 = max(0, (B3−500)×0.5)               设备维护费
    B7  = B12 + B5 + B9 + B13 + B22          总成本
    """
    actual_sales = min(demand, capacity)
    revenue = price * actual_sales          # B6
    actual_material = compute_actual_material_cost(material_cost, capacity)  # B23
    prod_cost = (actual_material + other_cost + processing_cost) * capacity  # B12 (用B23)
    maintenance = max(0, (capacity - 500) * 0.5)  # B22
    total_cost = prod_cost + rent + labor + marketing + maintenance  # B7
    profit = revenue - total_cost            # B8
    return revenue, prod_cost, total_cost, profit, maintenance, actual_material


def compute_shortage_rate(demand: int, capacity: int) -> float:
    """B17 缺货率"""
    if capacity >= demand or demand <= 0:
        return 0.0
    return round((demand - capacity) / demand * 1000) / 1000


def compute_waste_rate(demand: int, capacity: int) -> float:
    """B18 报废率"""
    if capacity > demand and capacity > 0:
        return round((capacity - demand) / capacity * 1000) / 1000
    return 0.0


# ============================================================
# 第二章：月度沙盘推演（完全镜像 GraphEditor.vue advanceMonth()）
# ============================================================

def simulate_one_month(
    price: float, labor: float, material_cost: float, other_cost: float,
    marketing: float, area: float, grade: float,
    brand: float = 0, prev_demand: float = 0,
    shortage_rate: float = 0, waste_rate: float = 0,
    use_seasonal: bool = False, month: int = 1
):
    """单月推演：按传播顺序执行所有节点计算。
    
    返回 dict 包含所有节点值和中间变量。
    传播顺序（与 GraphEditor.vue PROPAGATION_STEPS 一致）:
      ① B5 房租
      ② B2 需求 (依赖 B17缺货率, B19品牌)
      ③ B3 产能 (依赖 B4加工成本)
      ④ B4 加工成本 (依赖 B3)
      ⑤ B12 生产成本
      ⑥ B6 月收入
      ⑦ B7 总成本
      ⑧ B8 月利润
    """
    # 第一步：B5 房租
    rent = compute_rent(area, grade)                       # B5

    # 第二步：迭代求解 B3↔B4 循环依赖
    # B3 物理产能上限, B4 规模效应, 两者相互依赖需要收敛
    # 数学上正确的初始值: B4=2.0（首轮 B3=B4 未计算时，加工成本=¥2/个）
    processing_cost = 2.0                                   # B4 初始值

    # 初始 B3
    capacity = compute_capacity(area, labor, processing_cost)  # B3

    # B4 收敛：B3↔B4 是双依赖，迭代直到稳定
    for _ in range(10):
        processing_cost = compute_processing_cost(capacity)    # B4
        new_cap = compute_capacity(area, labor, processing_cost)  # B3
        if new_cap == capacity and abs(processing_cost - compute_processing_cost(new_cap)) < 0.0001:
            break
        capacity = new_cap

    # 第二步：B21 员工满意度
    satisfaction = compute_satisfaction(labor, capacity, area, grade)  # B21

    # B20 口味/品质
    taste = compute_taste(satisfaction, capacity, area)          # B20

    # B2 需求（使用上期缓存值）
    demand = compute_demand(price, grade, marketing,
                            shortage_rate, brand)                # B2

    # 应用季节性（只在用了 seasonal 标志时）
    if use_seasonal:
        seasonal = SEASONAL_FACTORS[month - 1]
        demand = max(0, round(demand * seasonal))

    # B6 月收入 / B12 生产成本 / B7 总成本 / B8 月利润
    revenue, prod_cost, total_cost, profit, maintenance, actual_material = compute_financials(
        price, demand, capacity,
        processing_cost, material_cost, other_cost,
        rent, labor, marketing
    )

    # B17 缺货率 / B18 报废率
    new_shortage = compute_shortage_rate(demand, capacity)
    new_waste = compute_waste_rate(demand, capacity)

    # B19 品牌知名度
    new_brand = compute_brand(brand, taste, grade, marketing)

    return {
        # 可编辑输入
        'price': price,
        'labor': labor,
        'material_cost': material_cost,
        'other_cost': other_cost,
        'marketing': marketing,
        'area': area,
        'grade': grade,
        # 引擎计算节点
        'B5_rent': rent,
        'B2_demand': demand,
        'B3_capacity': capacity,
        'B4_processing_cost': processing_cost,
        'B21_satisfaction': satisfaction,
        'B20_taste': taste,
        'B6_revenue': revenue,
        'B12_prod_cost': prod_cost,
        'B7_total_cost': total_cost,
        'B8_profit': profit,
        'B22_maintenance': maintenance,
        'B23_actual_material': actual_material,
        'B17_shortage_rate': new_shortage,
        'B18_waste_rate': new_waste,
        'B19_brand': new_brand,
        # 实际销量（可用于外部引用）
        'actual_sales': min(demand, capacity),
    }


def simulate_one_year(
    price: float, labor: float, material_cost: float, other_cost: float,
    marketing: float, area: float, grade: float,
    use_seasonal: bool = False,
    initial_cash: float = 0,
    track_cash: bool = False
):
    """一年12个月推演。
    
    参数:
        track_cash: True 时追踪现金流，现金耗尽则提前终止
        initial_cash: 初始现金（仅 track_cash=True 时需要）
    
    返回:
        months: 12个月的逐月结果
        annual: 年终汇总
        bankrupt: 是否破产（track_cash 模式下）
    """
    brand = 0.0
    prev_demand = 0
    shortage_rate = 0.0
    waste_rate = 0.0
    
    months = []
    cash = initial_cash
    bankrupt = False
    
    for m in range(1, 13):
        result = simulate_one_month(
            price, labor, material_cost, other_cost,
            marketing, area, grade,
            brand=brand,
            prev_demand=prev_demand,
            shortage_rate=shortage_rate,
            waste_rate=waste_rate,
            use_seasonal=use_seasonal,
            month=m,
        )
        result['month'] = m
        months.append(result)
        
        # 缓存推到下月
        brand = result['B19_brand']
        prev_demand = result['B2_demand']
        shortage_rate = result['B17_shortage_rate']
        waste_rate = result['B18_waste_rate']
        
        # 现金流追踪
        if track_cash:
            cash += result['B8_profit']
            result['cash'] = cash
            if cash < 0:
                bankrupt = True
                # 后面月份标记为破产
                for remaining in range(m + 1, 13):
                    months.append({
                        'month': remaining,
                        'bankrupt': True,
                        'B8_profit': 0,
                        'B6_revenue': 0,
                        'B7_total_cost': 0,
                        'B2_demand': 0,
                        'B3_capacity': 0,
                        'B19_brand': 0,
                        'cash': cash,
                    })
                break
    
    annual_revenue = sum(m.get('B6_revenue', 0) for m in months)
    annual_cost = sum(m.get('B7_total_cost', 0) for m in months)
    annual_profit = sum(m.get('B8_profit', 0) for m in months)
    profitable_months = sum(1 for m in months if m.get('B8_profit', 0) > 0)
    avg_monthly_profit = annual_profit / max(len(months), 1)
    
    return {
        'months': months,
        'annual': {
            'revenue': annual_revenue,
            'cost': annual_cost,
            'profit': annual_profit,
            'profitable_months': profitable_months,
            'avg_monthly_profit': avg_monthly_profit,
            'profit_margin': (annual_profit / annual_revenue * 100) if annual_revenue > 0 else 0,
        },
        'bankrupt': bankrupt,
        'months_completed': len(months),
    }


# ============================================================
# 第三章：已知通关路线验证
# ============================================================

def print_scenario(name, params, result):
    """打印一条路线推演结果"""
    a = result['annual']
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    print(f"  参数: 售价¥{params['price']} | {params['area']}m² | "
          f"人工¥{params['labor']:,} | 营销¥{params['marketing']:,} | "
          f"等级{params['grade']}")
    print(f"  年收入: ¥{a['revenue']:,.0f}  年成本: ¥{a['cost']:,.0f}  "
          f"年利润: ¥{a['profit']:,.0f}  ({a['profit_margin']:.1f}%)")
    print(f"  盈利月数: {a['profitable_months']}/12")
    if result['bankrupt']:
        print(f"  💀 破产！第{result['months_completed']}个月现金耗尽")
    else:
        print(f"  状态: ✅ 存活")
    print()
    
    # 打印逐月明细
    print(f"  月份 | {'需求':>5} | {'产能':>5} | {'收入':>8} | {'成本':>8} | {'利润':>8} | {'品牌':>5}")
    print(f"  {'-'*54}")
    for m in result['months']:
        if m.get('bankrupt'):
            print(f"  {m['month']:>3}  | 💀 破产")
        else:
            print(f"  {m['month']:>3}  | {m['B2_demand']:>5} | {m['B3_capacity']:>5} | "
                  f"{m['B6_revenue']:>8,.0f} | {m['B7_total_cost']:>8,.0f} | "
                  f"{m['B8_profit']:>+8,.0f} | {m['B19_brand']:>5}")


def verify_known_scenarios():
    """验证三条已知通过路线"""
    
    scenarios = [
        ("✨ 高奢网红店", dict(price=28, labor=8000, material_cost=3,
                               other_cost=1, marketing=6000, area=120, grade=9)),
        ("🏭 薄利大厂", dict(price=16, labor=8000, material_cost=3,
                             other_cost=1, marketing=2000, area=150, grade=7)),
        ("🏠 社区老店", dict(price=16, labor=6000, material_cost=3,
                             other_cost=1, marketing=0, area=60, grade=5)),
    ]
    
    for name, params in scenarios:
        result = simulate_one_year(**params)
        print_scenario(name, params, result)


# ============================================================
# 第四章：现金流检测（新功能——死亡螺旋验证）
# ============================================================

def find_viable_cash_level(
    price: float, labor: float, material_cost: float, other_cost: float,
    marketing: float, area: float, grade: float,
    initial_cash: float = 50000
):
    """对于一条路线，给定初始现金，检测能否活过一年。
    
    返回:
        'SURVIVE' — 活得过去
        'BANKRUPT: month X' — 第 X 个月破产
    """
    result = simulate_one_year(
        price, labor, material_cost, other_cost,
        marketing, area, grade,
        track_cash=True,
        initial_cash=initial_cash,
    )
    if result['bankrupt']:
        # 找到第一个现金为负的月份
        for m in result['months']:
            if m.get('cash', 0) < 0:
                return f'BANKRUPT: month {m["month"]}'
    return 'SURVIVE'


def cash_flow_analysis():
    """三条路线在不同初始现金下的存活情况"""
    scenarios = [
        ("✨ 高奢网红店", dict(price=28, labor=8000, material_cost=3,
                               other_cost=1, marketing=6000, area=120, grade=9)),
        ("🏭 薄利大厂", dict(price=16, labor=8000, material_cost=3,
                             other_cost=1, marketing=2000, area=150, grade=7)),
        ("🏠 社区老店", dict(price=16, labor=6000, material_cost=3,
                             other_cost=1, marketing=0, area=60, grade=5)),
    ]
    
    print(f"\n{'='*60}")
    print(f"  💰 现金流死亡螺旋检测")
    print(f"  ('生存最低线' = 刚好活过12个月需要的初始现金)")
    print(f"{'='*60}")
    
    for name, params in scenarios:
        # 先看没有现金追踪时的月度利润曲线
        base = simulate_one_year(**params, track_cash=True, initial_cash=0)
        monthly = [m['B8_profit'] for m in base['months'] if not m.get('bankrupt')]
        
        print(f"\n  {name}")
        print(f"  逐月利润: {', '.join(f'{p:+,.0f}' for p in monthly)}")
        
        # 检测月利润曲线，找到累积最低点 = 需要的最小初始现金
        running = 0
        min_cash = 0
        for m in base['months']:
            if m.get('bankrupt'):
                break
            running += m['B8_profit']
            min_cash = min(min_cash, running)
        
        required = abs(min_cash)
        print(f"  最大累计亏损: ¥{min_cash:,.0f}")
        
        if required == 0:
            print(f"  ✅ 无需初始现金，全年自造血")
        else:
            print(f"  💰 最低初始现金: ¥{required:,.0f}")
            # 验证 result = simulate_one_year(**params, track_cash=True, initial_cash=required)
            test = simulate_one_year(**params, track_cash=True, initial_cash=required)
            if test['bankrupt']:
                print(f"  ⚠️  ¥{required:,.0f} 仍不够，需更多")
                # 二分查找
                lo, hi = required, required * 3
                while hi - lo > 1000:
                    mid = (lo + hi) // 2
                    if simulate_one_year(**params, track_cash=True, initial_cash=mid)['bankrupt']:
                        lo = mid
                    else:
                        hi = mid
                print(f"  💰 实际最低现金: ¥{hi:,.0f}")
            else:
                print(f"  ✅ 验证通过: ¥{required:,.0f} 刚好够")


# ============================================================
# 第五章：引擎一致性验证（Python vs MeshFlow 对比）
# ============================================================

def dump_month_for_comparison(result):
    """输出标准格式，方便与 MeshFlow 引擎结果逐字段对比"""
    return {
        'B2_demand': result['B2_demand'],
        'B3_capacity': result['B3_capacity'],
        'B4_processing_cost': result['B4_processing_cost'],
        'B5_rent': result['B5_rent'],
        'B6_revenue': result['B6_revenue'],
        'B7_total_cost': result['B7_total_cost'],
        'B8_profit': result['B8_profit'],
        'B12_prod_cost': result['B12_prod_cost'],
        'B17_shortage_rate': result['B17_shortage_rate'],
        'B18_waste_rate': result['B18_waste_rate'],
        'B19_brand': result['B19_brand'],
        'B20_taste': result['B20_taste'],
        'B21_satisfaction': result['B21_satisfaction'],
        'B22_maintenance': result['B22_maintenance'],
        'B23_actual_material': result['B23_actual_material'],
    }


# ============================================================
# 主入口
# ============================================================

if __name__ == '__main__':
    # 1) 验证三条已知路线
    verify_known_scenarios()
    
    # 2) 现金流分析
    cash_flow_analysis()
    
    # 3) 打印单月详细公式分解（用于调试）
    print(f"\n{'='*60}")
    print(f"  📊 单月公式分解（高奢店, 第1个月）")
    print(f"{'='*60}")
    m = simulate_one_month(
        price=28, labor=8000, material_cost=3,
        other_cost=1, marketing=6000, area=120, grade=9
    )
    for k, v in m.items():
        if isinstance(v, float):
            print(f"  {k:>25s} = {v:>10.4f}")
        else:
            print(f"  {k:>25s} = {v:>10}")
