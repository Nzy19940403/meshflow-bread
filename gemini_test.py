"""
Gemini 地狱版 V4 验证
"""
import math

ROUTES = [
    {"name": "✨ 高奢·精兵", "B1": 28, "B24": 3, "B25": 500, "B13": 6000, "B10": 3, "B14": 120, "B15": 7},
    {"name": "🏭 大厂·标准", "B1": 16, "B24": 8, "B25": 100, "B13": 2000, "B10": 3, "B14": 150, "B15": 7},
    {"name": "🏠 社区·基本", "B1": 16, "B24": 3, "B25": 0,   "B13": 0,    "B10": 3, "B14": 60,  "B15": 7},
    {"name": "💀 自杀1: 高价0营销", "B1": 35, "B24": 20, "B25": 0, "B13": 0, "B10": 6, "B14": 300, "B15": 7},
    {"name": "💀 自杀2: 低价超大", "B1": 5, "B24": 20, "B25": 0, "B13": 20000, "B10": 1, "B14": 300, "B15": 7},
]

def sk_gemini(fat):
    """Gemini 断崖版"""
    if not math.isfinite(fat): return 1.0
    if fat <= 20:  return 1.10
    if fat <= 50:  return 1.00
    if fat <= 80:  return 0.80
    if fat <= 90:  return 0.40
    return 0.05

def simulate_gemini(route):
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

        c["B3"] = max(0, round(ph * sk_gemini(c["FAT"])))

        c["B4"] = max(0.1, max(0.1, 2 - c["B3"] * 0.0002) * (1 - c["EMP"] * 0.002))

        # === Gemini 客流 ===
        pb = 1 + (15 - qq["B1"]) * 0.2 if qq["B1"] < 15 else 1
        tr = round(50 * qq["B15"]) + round((c["BRAND"] ** 1.2) * 5) + round(math.sqrt(max(0, qq["B13"])) * 10 * pb)

        # === Gemini 最高接受价 ===
        ma = max(1, 8 + qq["B15"] + c["BRAND"] * 0.2 + c["B21"] * 6)

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

        c["B12"] = round(qq["B10"] * (1 - min(0.3, c["B3"] * 0.00005)) * 100) / 100
        c["B11"] = c["B4"] + c["B3"] * 0.002

        c["B6"] = min(c["B2"], c["B3"])
        c["B7"] = c["B6"] * qq["B1"]
        c["B8"] = round(c["B7"] - (c["B12"] + 1 + c["B4"]) * c["B3"] - c["B5"] - c["B9"] - qq["B13"] - qq["B25"] * qq["B24"] - round(0.05 * qq["B24"] * 1500))

        profit = c["B8"]
        cash += profit
        profits.append(profit)
        if cash < 0 and month < 11:
            bankrupt = True
            break

        # fd() 疲劳累积
        ph2 = max(1, min(math.floor(qq["B14"] * 25), qq["B24"] * 600) + max(0, round((2 - c["B4"]) * 200)))
        d = 0
        d += 1
        if qq["B25"] == 0 and (c["B3"] / ph2) > 0.7:
            d += 5
        elif qq["B25"] == 0:
            d += 2
        if (c["B3"] / ph2) > 0.8:
            d += (c["B3"] / ph2 - 0.8) * 40
        d -= qq["B25"] * 0.03
        ff = c["FAT"] / 40 if c["FAT"] < 40 else 1
        if c["B21"] < 0.5:
            d -= (c["B21"] - 0.5) * 15 * ff
        if c["B9"] / qq["B24"] > 1500:
            d -= (c["B9"] / qq["B24"] - 1500) * 0.005 * ff
        c["FAT"] = max(0, min(100, round(c["FAT"] + d)))

        # nx() 跨月
        emp_gain = max(1, 10 - round(c["EMP"] * 0.05))
        c["EMP"] = min(200, round(c["EMP"] + emp_gain))

        # === Gemini 品牌（含缺货反噬）===
        shortage_rate = max(0, (c["B2"] - c["B3"]) / max(1, c["B2"]))
        brand_growth = c["B21"] * 15
        brand_decay = c["BRAND"] * 0.05
        brand_shortage = shortage_rate * 100
        brand_net = brand_growth - brand_decay - brand_shortage
        c["BRAND"] = max(0, round(c["BRAND"] + brand_net))

    total = round(sum(profits))
    monthly_avg = round(total / len(profits))
    return total, profits, bankrupt, cash, len(profits)

print("🔥"*28)
print("  Gemini 地狱版 — 四刀全砍")
print("🔥"*28)
print(f"\n{'='*55}")
print(f"  路线{'':>20s}  全年利润      状态")
print(f"{'='*55}")
for r in ROUTES:
    total, monthly, bankrupt, cash, n = simulate_gemini(r)
    status = "💀破产" if bankrupt else "✅存活"
    print(f"  {r['name']:22s}  {total:>+8,}   {status}  期末现金={cash:>+8,}")

# 高奢逐月
print(f"\n{'='*55}")
print(f"  高奢精兵逐月")
print(f"{'='*55}")
total, monthly, bankrupt, cash, n = simulate_gemini(ROUTES[0])
for i, p in enumerate(monthly):
    print(f"  月{i+1:2d}: {p:>+8,}")
print(f"  全年: {total:>+8,}  |  {'💀破产' if bankrupt else '✅存活'}")
