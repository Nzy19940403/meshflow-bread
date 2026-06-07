"""
面包店经营模型 — Python 纯数学推演
与 meshflow 引擎逐月对比验证
"""
import math

def simulate(b1_price, b9_labor, b13_marketing, b14_area, b15_grade, label):
    B10 = 3
    B11 = 1
    
    b16 = 0.0
    b17 = 0.0
    b18 = 0.0
    b19 = 0.0
    b20 = 0.8
    b21 = 0.8
    b4 = 2.0
    
    # 首月自洽初始化: B16 = B2
    first_b2 = compute_b2(b1_price, b15_grade, b13_marketing, 0.0, 0.0)
    b16 = max(100, round(first_b2))
    
    rows = []
    
    for month in range(1, 13):
        # 1) 需求 B2
        b2 = compute_b2(b1_price, b15_grade, b13_marketing, b17, b19)
        
        # 2) 产能 B3 + 加工成本 B4 (迭代收敛: B3↔B4 循环)
        b3 = compute_b3(b14_area, b9_labor, b4)
        for _ in range(5):  # 引擎在同T时刻收敛, Python模拟迭代
            b4_new = max(0.1, 2.0 - b3 * 0.0002)
            b3_new = compute_b3(b14_area, b9_labor, b4_new)
            if abs(b3_new - b3) < 1 and abs(b4_new - b4) < 0.001:
                b3, b4 = b3_new, b4_new
                break
            b3, b4 = b3_new, b4_new
        
        # 4) 房租 B5
        b5 = compute_b5(b14_area, b15_grade)
        
        # 5) 收入 B6
        sold = min(b2, b3)
        b6 = b1_price * sold
        
        # 6) 总生产成本 B12
        b12 = (B10 + B11 + b4) * b3
        
        # 7) 总成本 B7
        b7 = b12 + b5 + b9_labor + b13_marketing
        
        # 8) 利润 B8
        b8 = b6 - b7
        
        # 9) 员工满意度 B21
        b21 = compute_b21(b9_labor, b3, b14_area, b15_grade)
        
        # 10) 口味 B20
        b20 = compute_b20(b21, b3, b14_area)
        
        # 缓存
        shortage = (b3 < b2 and b2 > 0) and (b2 - b3) / b2 or 0.0
        waste = (b3 > b2 and b3 > 0) and (b3 - b2) / b3 or 0.0
        
        # 品牌增长 B19
        traffic = round(150 * (b15_grade ** 1.7)) + math.sqrt(max(0, b13_marketing)) * 15
        mouth_growth = 10
        growth = round(b20 * (traffic / 100 + mouth_growth))
        decay_rate = max(0.05, b19 * 0.01)
        decay = round(b19 * decay_rate)
        b19 = max(0, b19 + growth - decay)
        
        # 下月缓存
        b16 = b2
        b17 = shortage
        b18 = waste
        
        rows.append({
            'month': month,
            'b2': b2,
            'b3': b3,
            'b4': round(b4, 4),
            'b5': b5,
            'b6': round(b6, 2),
            'b7': round(b7, 2),
            'b8': round(b8, 2),
            'b19': b19,
            'b20': round(b20, 4),
            'b21': round(b21, 4),
            'waste_pct': round(waste * 100, 1),
        })
    
    return rows


def compute_b2(price, grade, marketing, shortage, brand):
    p = float(price) if price else 12.0
    g = float(grade) if grade else 5.0
    m = float(marketing) if marketing else 0.0
    s = float(shortage) if shortage else 0.0
    b = float(brand) if brand else 0.0
    
    price_discount_boost = 1.0 + (15 - p) * 0.2 if p < 15 else 1.0
    traffic = round(150 * (g ** 1.7)) + round(math.sqrt(max(0, m)) * 15 * price_discount_boost)
    
    brand_premium = b * 0.5
    location_premium = g * 1.5
    max_acceptable = 10 + location_premium + brand_premium
    
    if p <= max_acceptable:
        retention = 0.5 + (max_acceptable - p) / max_acceptable * 0.4
    else:
        retention = max(0.05, 0.5 * max_acceptable / p)
    
    base = round(traffic * retention)
    penalty = round(base * s * 0.5)
    return max(0, base - penalty)


def compute_b3(area, labor, cost):
    a = float(area) if area else 80.0
    l = float(labor) if labor else 15000.0
    c = float(cost) if cost else 2.0
    if a <= 0 or l <= 0:
        return 0
    area_cap = int(a * 25)
    labor_cap = int(l / 2.5)
    hw_cap = min(area_cap, labor_cap)
    efficiency = max(0, round((2 - c) * 200))
    return max(0, hw_cap + efficiency)


def compute_b5(area, grade):
    a = float(area) if area else 80.0
    g = float(grade) if grade else 5.0
    return max(0, round(a * g * max(2, 20 - a * 0.05)))


def compute_b21(labor, cap, area, grade):
    l = float(labor) if labor else 15000.0
    c = float(cap) if cap else 1000.0
    a = float(area) if area else 80.0
    g = float(grade) if grade else 5.0
    pay_per_output = l / max(c, 1)
    utilization = c / max(a * 25, 1)
    baseline = 3.0 + g * 0.4
    if pay_per_output >= baseline:
        pay_sat = 0.7 + min((pay_per_output - baseline) / (baseline * 2), 0.3)
    else:
        pay_sat = pay_per_output / baseline * 0.7
    overwork = max(0, utilization - 0.8) * 1.5
    return round(min(1, max(0, pay_sat - overwork)) * 1000) / 1000


def compute_b20(satisfaction, cap, area):
    s = float(satisfaction) if satisfaction else 0.8
    c = float(cap) if cap else 1000.0
    a = float(area) if area else 80.0
    utilization = c / max(a * 25, 1)
    if s >= 0.6:
        overload = max(0, utilization - 0.9) * 0.5
        taste = min(1, max(0.3, 1.0 - overload))
    else:
        taste = s * 0.6
    return round(taste * 1000) / 1000


# ====== 三种策略 ======
scenarios = [
    ("✨ 高奢网红店 (22/60/5k/300/5)", 22, 5000, 300, 60, 5),
    ("🏭 薄利大厂 (10/200/25k/8k/3)", 10, 25000, 8000, 200, 3),
    ("🏠 社区老店 (14/100/12k/0/5)", 14, 12000, 0, 100, 5),
]

for label, b1, b9, b13, b14, b15 in scenarios:
    rows = simulate(b1, b9, b13, b14, b15, label)
    cum_profit = sum(r['b8'] for r in rows)
    year_rev = sum(r['b6'] for r in rows)
    margin = (cum_profit / year_rev * 100) if year_rev > 0 else 0
    profit_months = sum(1 for r in rows if r['b8'] > 0)
    
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"  {'='*70}")
    print(f"  {'月':>3} | {'需求':>5} | {'产能':>5} | {'B4':>6} | {'收入':>8} | {'成本':>8} | {'利润':>8} | {'知名度':>4} | {'报废%':>4}")
    print(f"  {'-'*65}")
    for r in rows:
        print(f"  {r['month']:>3} | {r['b2']:>5} | {r['b3']:>5} | {r['b4']:>6} | {r['b6']:>8.0f} | {r['b7']:>8.0f} | {r['b8']:>8.0f} | {r['b19']:>4} | {r['waste_pct']:>4}%")
    
    print(f"  {'-'*65}")
    print(f"  年利润: ¥{cum_profit:,.0f}  | 利润率: {margin:.1f}%  | 盈利月: {profit_months}/12")
