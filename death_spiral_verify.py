"""
死亡螺旋验证器 — V4 原版 vs 硬核版 对比
对比三条基准路线的年利润 + 破产情况
"""
import math

# ========== 三条基准路线 ==========
ROUTES = [
    {"name": "✨ 高奢·精兵", "B1": 28, "B24": 3, "B25": 500, "B13": 6000, "B10": 3, "B14": 120, "B15": 7},
    {"name": "🏭 大厂·标准", "B1": 16, "B24": 8, "B25": 100, "B13": 2000, "B10": 3, "B14": 150, "B15": 7},
    {"name": "🏠 社区·基本", "B1": 16, "B24": 3, "B25": 0,   "B13": 0,    "B10": 3, "B14": 60,  "B15": 7},
]

# 破产场景
ROUTES_STRESS = ROUTES + [
    {"name": "💀 自杀路线(高售价0营销0培训)", "B1": 35, "B24": 20, "B25": 0, "B13": 0, "B10": 6, "B14": 300, "B15": 7},
    {"name": "💀 自杀路线(低售价超大面积)", "B1": 5, "B24": 20, "B25": 0, "B13": 20000, "B10": 1, "B14": 300, "B15": 7},
]

def sk_original(fat):
    """V4 原版 — 太温柔"""
    if not math.isfinite(fat): return 1.0
    if fat < 20:  return 1 + (20 - fat) / 20 * 0.1
    if fat < 60:  return 1.0
    if fat < 80:  return 1 - (fat - 60) / 20 * 0.3
    return 0.7 - (fat - 80) / 20 * 0.2  # FAT=100 → 0.50

def sk_hardcore(fat):
    """硬核版 — 断崖崩溃"""
    if not math.isfinite(fat): return 1.0
    if fat < 20:  return 1 + (20 - fat) / 20 * 0.05  # 爆种减弱
    if fat < 60:  return 1.0
    if fat < 80:  return 1 - (fat - 60) / 20 * 0.5   # 摸鱼更狠 (max 50% loss)
    if fat < 90:  return 0.3 - (fat - 80) / 10 * 0.1 # 崩溃前奏 (90→0.2)
    return max(0.02, 0.2 - (fat - 90) / 10 * 0.15)   # 崩溃区 (100→0.05)

def simulate(route, sk_fn, harsh_traffic=False, shortage_penalty=False):
    """模拟12个月"""
    q = route.copy()
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
        # ---- rc() 实时计算 ----
        q = c  # alias
        # B9 人工
        c["B9"] = round(q["B24"] * 1200 * (1 + q["B15"] * 0.15 * max(0, 1 - q["B24"] * 0.08)))

        # ph 物理产能
        ph = max(1, min(math.floor(q["B14"] * 25), q["B24"] * 600) + max(0, round((2 - c["B4"]) * 200)))

        # B3 实际产能
        c["B3"] = max(0, round(ph * sk_fn(c["FAT"])))

        # B4 加工成本
        c["B4"] = max(0.1, max(0.1, 2 - c["B3"] * 0.0002) * (1 - c["EMP"] * 0.002))

        # 客流量
        pb = 1 + (15 - q["B1"]) * 0.2 if q["B1"] < 15 else 1
        if harsh_traffic:
            # 硬核版：品牌参与基础客流乘法
            tr = round((50 + c["BRAND"] * 0.5) * (q["B15"] ** 1.2)) + round(math.sqrt(max(0, q["B13"])) * 15 * pb)
        else:
            tr = round(150 * (q["B15"] ** 1.7)) + round(math.sqrt(max(0, q["B13"])) * 15 * pb)

        # 需求
        ma = max(1, 10 + q["B15"] * 1.5 + c["BRAND"] * 0.5)
        if q["B1"] <= ma:
            retention = 0.5 + (ma - q["B1"]) / ma * 0.4
        else:
            retention = max(0.05, 0.5 * ma / q["B1"])
        c["B2"] = max(0, round(tr * retention))

        # 房租
        c["B5"] = max(0, round(q["B14"] * q["B15"] * max(2, 20 - q["B14"] * 0.05)))

        # 满意度
        pp = c["B9"] / max(c["B3"], 1)
        bl = 3 + q["B15"] * 0.4
        if pp >= bl:
            ps = 0.7 + min((pp - bl) / (bl * 2), 0.3)
        else:
            ps = pp / bl * 0.7
        c["B21"] = round(min(1, max(0, ps - max(0, c["B3"] / ph - 0.8) * 1.5)) * 1000) / 1000

        # 原料
        c["B12"] = round(q["B10"] * (1 - min(0.3, c["B3"] * 0.00005)) * 100) / 100
        c["B11"] = c["B4"] + c["B3"] * 0.002

        # 收支
        c["B6"] = min(c["B2"], c["B3"])
        c["B7"] = c["B6"] * q["B1"]
        c["B8"] = round(c["B7"] - (c["B12"] + 1 + c["B4"]) * c["B3"] - c["B5"] - c["B9"] - q["B13"] - q["B25"] * q["B24"] - round(0.05 * q["B24"] * 1500))

        profit = c["B8"]
        cash += profit
        profits.append(profit)

        if cash < 0:
            bankrupt = True
            break

        # ---- fd() 疲劳累积 ----
        ph2 = max(1, min(math.floor(q["B14"] * 25), q["B24"] * 600) + max(0, round((2 - c["B4"]) * 200)))
        d = 0
        if (c["B3"] / ph2) > 0.8:
            d += (c["B3"] / ph2 - 0.8) * 50
        d -= q["B25"] * 0.02
        ff = c["FAT"] / 40 if c["FAT"] < 40 else 1
        if c["B21"] < 0.5:
            d -= (c["B21"] - 0.5) * 20 * ff
        if c["B9"] / q["B24"] > 1500:
            d -= (c["B9"] / q["B24"] - 1500) * 0.005 * ff
        c["FAT"] = max(0, min(100, round(c["FAT"] + d)))

        # ---- nx() 跨月推进 ----
        c["EMP"] = min(200, round(c["EMP"] + 10))

        # 品牌更新
        shortage_rate = max(0, (c["B2"] - c["B3"]) / c["B2"]) if c["B2"] > 0 else 0
        if shortage_penalty:
            brand_growth = c["B21"] * (round(150 * 7 ** 1.7) / 100 + 10)
            brand_decay = c["BRAND"] * max(0.05, c["BRAND"] * 0.01)
            brand_shortage = shortage_rate * 50
            c["BRAND"] = max(0, round(c["BRAND"] + brand_growth - brand_decay - brand_shortage))
        else:
            c["BRAND"] = max(0, round(c["BRAND"] + c["B21"] * (round(150 * 7 ** 1.7) / 100 + 10) - c["BRAND"] * max(0.05, c["BRAND"] * 0.01)))

    total = round(sum(profits))
    return total, profits, bankrupt, cash, len(profits)


def print_results(label, routes, sk_fn, harsh_traffic=False, shortage_penalty=False):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    total_profit = 0
    for r in routes:
        total, monthly, bankrupt, cash, months = simulate(r, sk_fn, harsh_traffic, shortage_penalty)
        status = "💀 破产" if bankrupt else "✅"
        print(f"  {r['name']:20s} 全年={total:>+8,}  期末现金={cash:>+8,}  {status}")
        total_profit += total
    print(f"  {'合计':20s}  {total_profit:>+8,}")
    return total_profit


# ========== 运行 ==========
print("\n" + "🔥" * 30)
print("  死亡螺旋验证器")
print("🔥" * 30)

# 原版 V4（全三项保护伞）
p1 = print_results("【原版 V4】三项保护伞全在", ROUTES, sk_original, False, False)

# 硬核版：断崖疲劳 + 硬核客流 + 缺货惩罚
p2 = print_results("【硬核版】三项全砍", ROUTES, sk_hardcore, True, True)

# 自杀路线测试
print_results("【自杀路线 — 原版】", ROUTES_STRESS[3:], sk_original, False, False)
print_results("【自杀路线 — 硬核版】", ROUTES_STRESS[3:], sk_hardcore, True, True)

print(f"\n{'='*60}")
print(f"  利润变化: 原版 ¥{p1:,} → 硬核 ¥{p2:,}  ({'↓' if p2 < p1 else '↑'} {abs(p1-p2):,})")
print(f"{'='*60}")
