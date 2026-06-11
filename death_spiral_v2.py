"""
死亡螺旋验证 v2 — 高天花板 + 脆地板 + 反复利
目标：好路线能赚100K+，坏路线速死，但不能挂机
"""
import math
from copy import deepcopy

ROUTES = [
    {"name": "✨ 高奢·精兵", "B1": 28, "B24": 3, "B25": 500, "B13": 6000, "B10": 3, "B14": 120, "B15": 7},
    {"name": "🏭 大厂·标准", "B1": 16, "B24": 8, "B25": 100, "B13": 2000, "B10": 3, "B14": 150, "B15": 7},
    {"name": "🏠 社区·基本", "B1": 16, "B24": 3, "B25": 0,   "B13": 0,    "B10": 3, "B14": 60,  "B15": 7},
    {"name": "💀 自杀: 高售价0营销", "B1": 35, "B24": 20, "B25": 0, "B13": 0, "B10": 6, "B14": 300, "B15": 7},
    {"name": "💀 自杀: 低售价超大", "B1": 5, "B24": 20, "B25": 0, "B13": 20000, "B10": 1, "B14": 300, "B15": 7},
]

def sk(fat):
    """V4 原版 sk — 只改尾部斜率不改底数"""
    if not math.isfinite(fat): return 1.0
    if fat < 20:  return 1 + (20 - fat) / 20 * 0.1
    if fat < 60:  return 1.0
    if fat < 80:  return 1 - (fat - 60) / 20 * 0.35
    if fat < 90:  return 0.65 - (fat - 80) / 10 * 0.35  # 90→0.30
    return max(0.10, 0.30 - (fat - 90) / 10 * 0.20)      # 100→0.10

def simulate(route, harsh_traffic=True, shortage_penalty=True, brand_cap=True):
    """模拟12个月"""
    q = route
    c = {
        "B1": q["B1"], "B2": 0, "B3": 0, "B4": 2.0, "B5": 0,
        "B6": 0, "B7": 0, "B8": 0, "B9": 0, "B10": q["B10"],
        "B11": 0, "B12": 0, "B13": q["B13"], "B14": q["B14"],
        "B15": q["B15"], "B21": 0.8, "B22": 0, "B23": 0,
        "B24": q["B24"], "B25": q["B25"],
        "FAT": 40, "EMP": 0, "BRAND": 0,
    }
    cash = 50000
    profits = []
    bankrupt = False

    for month in range(12):
        qq = c
        # B9 人工
        c["B9"] = round(qq["B24"] * 1200 * (1 + qq["B15"] * 0.15 * max(0, 1 - qq["B24"] * 0.08)))

        # ph 物理产能
        ph = max(1, min(math.floor(qq["B14"] * 25), qq["B24"] * 600) + max(0, round((2 - c["B4"]) * 200)))

        # B3 实际产能
        c["B3"] = max(0, round(ph * sk(c["FAT"])))

        # B4 加工成本
        c["B4"] = max(0.1, max(0.1, 2 - c["B3"] * 0.0002) * (1 - c["EMP"] * 0.002))

        # ===== 客流量 (harder but scalable with brand) =====
        pb = 1 + (15 - qq["B1"]) * 0.2 if qq["B1"] < 15 else 1
        if harsh_traffic:
            # 基础 ~1500 + 品牌效应
            base_traffic = round(200 * (qq["B15"] ** 1.4))  # 200*7^1.4 ≈ 2700
            brand_bonus = round(c["BRAND"] * 0.8)           # 品牌每点+0.8客流
            marketing = round(math.sqrt(max(0, qq["B13"])) * 15 * pb)
            tr = base_traffic + brand_bonus + marketing
        else:
            tr = round(150 * (qq["B15"] ** 1.7)) + round(math.sqrt(max(0, qq["B13"])) * 15 * pb)

        # 需求
        ma = max(1, 10 + qq["B15"] * 1.5 + c["BRAND"] * 0.5)
        if qq["B1"] <= ma:
            retention = 0.5 + (ma - qq["B1"]) / ma * 0.4
        else:
            retention = max(0.05, 0.5 * ma / qq["B1"])
        c["B2"] = max(0, round(tr * retention))

        # 房租
        c["B5"] = max(0, round(qq["B14"] * qq["B15"] * max(2, 20 - qq["B14"] * 0.05)))

        # 满意度
        pp = c["B9"] / max(c["B3"], 1)
        bl = 3 + qq["B15"] * 0.4
        if pp >= bl:
            ps = 0.7 + min((pp - bl) / (bl * 2), 0.3)
        else:
            ps = pp / bl * 0.7
        c["B21"] = round(min(1, max(0, ps - max(0, c["B3"] / ph - 0.8) * 1.5)) * 1000) / 1000

        # 原料
        c["B12"] = round(qq["B10"] * (1 - min(0.3, c["B3"] * 0.00005)) * 100) / 100
        c["B11"] = c["B4"] + c["B3"] * 0.002

        # 收支
        c["B6"] = min(c["B2"], c["B3"])
        c["B7"] = c["B6"] * qq["B1"]
        c["B8"] = round(c["B7"] - (c["B12"] + 1 + c["B4"]) * c["B3"] - c["B5"] - c["B9"] - qq["B13"] - qq["B25"] * qq["B24"] - round(0.05 * qq["B24"] * 1500))

        profit = c["B8"]
        cash += profit
        profits.append(profit)

        if cash < 0 and month < 11:  # 最后一个月破不破产都算完成
            bankrupt = True
            break

        # ===== fd() 疲劳累积 =====
        ph2 = max(1, min(math.floor(qq["B14"] * 25), qq["B24"] * 600) + max(0, round((2 - c["B4"]) * 200)))
        d = 0
        # 基线疲劳：不管怎样每月+1（反复利——即使完美经营也会缓慢累积）
        d += 1
        # 无培训惩罚：不培训的员工在高压下更容易累
        if qq["B25"] == 0 and (c["B3"] / ph2) > 0.7:
            d += 5  # 不培训还高强度? 每月+5疲劳
        elif qq["B25"] == 0:
            d += 2  # 不培训即使不高压也+2
        if (c["B3"] / ph2) > 0.8:
            d += (c["B3"] / ph2 - 0.8) * 40  # 超负荷时加快累积
        d -= qq["B25"] * 0.03  # 培训缓解（效果增强）
        ff = c["FAT"] / 40 if c["FAT"] < 40 else 1
        if c["B21"] < 0.5:
            d -= (c["B21"] - 0.5) * 15 * ff
        if c["B9"] / qq["B24"] > 1500:
            d -= (c["B9"] / qq["B24"] - 1500) * 0.005 * ff
        c["FAT"] = max(0, min(100, round(c["FAT"] + d)))

        # ===== nx() 跨月推进 =====
        # 经验（带天花板效应）
        emp_gain = max(1, 10 - round(c["EMP"] * 0.05))  # EMP越高，增速越慢
        c["EMP"] = min(200, round(c["EMP"] + emp_gain))

        # 品牌（带天花板）
        shortage_rate = max(0, (c["B2"] - c["B3"]) / c["B2"]) if c["B2"] > 0 else 0
        brand_growth = c["B21"] * 30  # 满意度驱动品牌增长
        
        if brand_cap:
            # 品牌天花板：BRAND越高，自然衰减越快，增长越慢
            decay_base = max(0.02, c["BRAND"] * 0.015)  # 高品牌时衰减加速
            growth_mult = max(0.1, 1 - c["BRAND"] / 800)  # BRAND 800时增长效率只剩10%
            brand_decay = c["BRAND"] * decay_base
            brand_net = brand_growth * growth_mult - brand_decay
            if shortage_penalty:
                brand_net -= shortage_rate * 20
            c["BRAND"] = max(0, round(c["BRAND"] + brand_net))
        else:
            brand_decay = c["BRAND"] * max(0.05, c["BRAND"] * 0.01)
            brand_net = brand_growth - brand_decay
            if shortage_penalty:
                brand_net -= shortage_rate * 50
            c["BRAND"] = max(0, round(c["BRAND"] + brand_net))

    total = round(sum(profits))
    monthly_avg = round(total / len(profits))
    return total, monthly_avg, profits, bankrupt, cash, len(profits)


def run(label, routes, **kwargs):
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")
    details = []
    for r in routes:
        total, avg, monthly, bankrupt, cash, months = simulate(r, **kwargs)
        status = "💀破产" if bankrupt else "✅存活"
        detail = f"  {r['name']:22s} 月均={avg:>+7,}  全年={total:>+8,}  期末现金={cash:>+8,}  {status}"
        print(detail)
        details.append((r['name'], total, bankrupt, monthly))
    return details

print("🔥"*28)
print("  V4 死亡螺旋 v2 — 校准版")
print("🔥"*28)

run("【原版 V4】", ROUTES[:3], harsh_traffic=False, shortage_penalty=False, brand_cap=False)
run("【v2 校准版】客流砍+疲劳加重+品牌天花板", ROUTES[:3], harsh_traffic=True, shortage_penalty=True, brand_cap=True)
run("【v2 自杀路线】", ROUTES[3:], harsh_traffic=True, shortage_penalty=True, brand_cap=True)

# 打印高奢精兵的逐月明细
print(f"\n{'='*55}")
print(f"  高奢精兵逐月明细 (v2)")
print(f"{'='*55}")
total, avg, monthly, bankrupt, cash, _ = simulate(ROUTES[0], True, True, True)
print(f"  月 | 利润     | 累计    | FAT | EMP | BRAND | B2(需求) | B3(产能)")
for i, p in enumerate(monthly):
    # Need to re-simulate to get per-month state... let me just print profits
    print(f"  {i+1:2d} | {p:>+8,}", end="")
    if (i+1) % 3 == 0:
        print()
print(f"\n  全年: {total:>+8,}  |  {'💀破产' if bankrupt else '✅存活'}")
