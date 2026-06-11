"""
debug_precision.py — 追踪Python与JS的浮点精度差异来源
"""
import math

def py_round(x):
    return round(x)

def simulate_month_community_trace():
    """社区老店 month 1，每一步拆开打印"""
    price, labor, material, other = 16, 6000, 3, 1
    marketing, area, grade = 0, 60, 5
    
    # ---- B5 房租 ----
    rent = max(0, round(area * grade * max(2, 20 - area * 0.05)))
    print(f"B5 房租 = round({area}×{grade}×max(2, 20-{area}×0.05))")
    print(f"       = round(300×max(2, {20-area*0.05})) = round(300×17) = {rent}")
    print()
    
    # ---- B3/B4 收敛循环 ----
    cap = compute_capacity(area, labor, 2.0)
    print(f"初始B3（B4=2.0时）= {cap}")
    for i in range(5):
        cost = max(0.1, 2 - cap * 0.0002)
        new_cap = compute_capacity(area, labor, cost)
        print(f"  轮{i+1}: B4=max(0.1, 2-{cap}×0.0002) = {cost:.6f}")
        print(f"         B3=min({int(area*25)}, {int(labor/2.5)})+max(0, round((2-{cost:.6f})×200)) = {new_cap}")
        cap = new_cap
    
    # ---- 注意这里 round 的差异 ----
    # Python round(62.4) = 62, round(62.5) = 62 (banker's rounding!)
    # JS Math.round(62.4) = 62, Math.round(62.5) = 63
    print()
    print("⚠️ Python round() 是 bankers' rounding (向偶取整)")
    print("   JS Math.round() 是 half-up (向远离零取整)")
    print(f"   测试: Python round(62.5) = {round(62.5)}")
    print(f"   测试: JS Math.round(62.5) = 63")
    print()
    
    # ---- B21 满意度 ----
    sat = compute_satisfaction(labor, cap, area, grade)
    print(f"B21 满意度: pay/输出={labor}/{cap}={labor/cap:.4f}")
    print(f"   baseline = 3.0+{grade}×0.4 = {3.0+grade*0.4}")
    print(f"   paySat = {sat:.4f}")
    
    # ---- B2 需求 ----
    demand = compute_demand(price, grade, marketing, 0, 0)
    print(f"\nB2 需求:")
    traffic = round(150 * grade ** 1.7)
    print(f"   traffic = round(150×{grade}^1.7) = round({150*grade**1.7}) = {traffic}")
    max_acceptable = 10 + grade * 1.5 + 0 * 0.5
    print(f"   max_acceptable = 10+{grade}×1.5+0 = {max_acceptable}")
    retention = 0.5 + (max_acceptable - price) / max_acceptable * 0.4
    print(f"   retention = 0.5+({max_acceptable}-{price})/{max_acceptable}×0.4 = {retention:.6f}")
    base = round(traffic * retention)
    print(f"   base = round({traffic}×{retention:.6f}) = round({traffic*retention}) = {base}")
    print(f"   最终B2 = {demand}")
    print()
    
    # ---- B6/B7/B8 ----
    rev = price * min(demand, cap)
    prod_cost = (material + other + cost) * cap
    total = prod_cost + rent + labor + marketing
    profit = rev - total
    print(f"B8 利润 = {rev} - {total} = {profit:.2f}")


def compare_py_vs_js_carefully():
    """在关键 round() 处对比 Python vs JS 行为"""
    print(f"{'='*60}")
    print(f"  round() 行为差异对比")
    print(f"{'='*60}")
    
    # Python 的 round 是 bankers' rounding (Gaussian rounding)
    # JS 的 Math.round 是 half away from zero
    test_vals = [62.4, 62.5, 62.6, -62.5, 3.5, 4.5, 0.5, 1.5, 2.5]
    
    print(f"\n  {'值':>8} | {'Python round':>12} | {'JS Math.round':>12}")
    print(f"  {'-'*8}-+-{'-'*12}-+-{'-'*12}")
    for v in test_vals:
        py = round(v)
        js = math.floor(v + 0.5)  # half-up
        print(f"  {v:>8.1f} | {py:>12} | {js:>12}")
    
    print(f"\n  → Python round(1.5)={round(1.5)} vs JS Math.round(1.5)=2")
    print(f"  → Python round(2.5)={round(2.5)} vs JS Math.round(2.5)=3")


# Replicate the key functions from ref_model
def compute_capacity(area, labor, processing_cost):
    if area <= 0 or labor <= 0:
        return 0
    area_cap = int(area * 25)
    labor_cap = int(labor / 2.5)
    hardware_cap = min(area_cap, labor_cap)
    efficiency_bonus = max(0, round((2 - processing_cost) * 200))
    return max(0, hardware_cap + efficiency_bonus)

def compute_satisfaction(labor, capacity, area, grade):
    pay_per_output = labor / max(capacity, 1)
    utilization = capacity / max(area * 25, 1)
    pay_baseline = 3.0 + grade * 0.4
    if pay_per_output >= pay_baseline:
        pay_sat = 0.7 + min((pay_per_output - pay_baseline) / (pay_baseline * 2), 0.3)
    else:
        pay_sat = pay_per_output / pay_baseline * 0.7
    overwork_penalty = max(0, utilization - 0.8) * 1.5
    return round(min(1, max(0, pay_sat - overwork_penalty)) * 1000) / 1000

def compute_demand(price, grade, marketing, shortage_rate, brand):
    price_discount_boost = 1.0 + (15 - price) * 0.2 if price < 15 else 1.0
    traffic = round(150 * grade ** 1.7) + round(math.sqrt(max(0, marketing)) * 15 * price_discount_boost)
    brand_premium = brand * 0.5
    location_premium = grade * 1.5
    max_acceptable = 10 + location_premium + brand_premium
    if price <= max_acceptable:
        retention = 0.5 + (max_acceptable - price) / max_acceptable * 0.4
    else:
        retention = max(0.05, 0.5 * (max_acceptable / price))
    base = round(traffic * retention)
    penalty = round(base * shortage_rate * 0.5)
    return max(0, base - penalty)

if __name__ == '__main__':
    compare_py_vs_js_carefully()
    print("\n")
    simulate_month_community_trace()
