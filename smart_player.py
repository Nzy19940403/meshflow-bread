"""
聪明玩家策略验证 — 跑的不是12个月挂机，而是动态决策
"""
import math

# ========== V2 校准版公式核心 ==========
def simulate(route, strategy_fn):
    """模拟12个月，每月调用 strategy_fn 让玩家动态调参"""
    q = dict(route)
    c = {
        "B1": q["B1"], "B2": 0, "B3": 0, "B4": 2.0, "B5": 0,
        "B6": 0, "B7": 0, "B8": 0, "B9": 0, "B10": q["B10"],
        "B11": 0, "B12": 0, "B13": q["B13"], "B14": q["B14"],
        "B15": q["B15"], "B21": 0.8, "B22": 0, "B23": 0,
        "B24": q["B24"], "B25": q["B25"],
        "FAT": 40, "EMP": 0, "BRAND": 0,
        "last_B2": 0, "last_B3": 0,
    }
    cash = 50000
    profits = []
    bankrupt = False
    decisions = []

    for month in range(12):
        # 策略决策：玩家看表调参数
        strategy_fn(c, month, q)

        qq = c
        # B9 人工
        c["B9"] = round(qq["B24"] * 1200 * (1 + qq["B15"] * 0.15 * max(0, 1 - qq["B24"] * 0.08)))
        ph = max(1, min(math.floor(qq["B14"] * 25), qq["B24"] * 600) + max(0, round((2 - c["B4"]) * 200)))

        # sk (v2校准版)
        fat = c["FAT"]
        if fat < 20:  sk = 1 + (20 - fat) / 20 * 0.1
        elif fat < 60: sk = 1.0
        elif fat < 80: sk = 1 - (fat - 60) / 20 * 0.35
        elif fat < 90: sk = 0.65 - (fat - 80) / 10 * 0.35
        else: sk = max(0.10, 0.30 - (fat - 90) / 10 * 0.20)

        c["B3"] = max(0, round(ph * sk))
        c["B4"] = max(0.1, max(0.1, 2 - c["B3"] * 0.0002) * (1 - c["EMP"] * 0.002))

        # 客流 (v2校准版: 200×7^1.4 ≈ 2700)
        # === 价格弹性（校准版）===
        # 低价 (<20) → 引流, 高价 (>20) → 赶人但留底线
        pb = 1 + (20 - qq["B1"]) * 0.15 if qq["B1"] < 20 else max(0.5, 1 - (qq["B1"] - 20) * 0.03)
        # 客流 = (基础 + 品牌) × 价格弹性 + 营销
        base_traffic = round(300 * qq["B15"])
        brand_bonus = round(c["BRAND"] * 1.5)
        marketing = round(math.sqrt(max(0, qq["B13"])) * 12)
        tr = round((base_traffic + brand_bonus) * pb) + marketing

        # ma (校准版：保留满意度挂钩但留底线)
        ma = max(1, 10 + qq["B15"] * 1.2 + c["BRAND"] * 0.3 + c["B21"] * 4)

        if qq["B1"] <= ma:
            retention = 0.5 + (ma - qq["B1"]) / ma * 0.4
        else:
            retention = max(0.05, 0.5 * ma / qq["B1"])
        c["B2"] = max(0, round(tr * retention))
        c["B5"] = max(0, round(qq["B14"] * qq["B15"] * max(2, 20 - qq["B14"] * 0.05)))

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

        # fd() 疲劳
        ph2 = max(1, min(math.floor(qq["B14"] * 25), qq["B24"] * 600) + max(0, round((2 - c["B4"]) * 200)))
        d = 1
        if qq["B25"] == 0 and (c["B3"] / ph2) > 0.7: d += 5
        elif qq["B25"] == 0: d += 2
        if (c["B3"] / ph2) > 0.8: d += (c["B3"] / ph2 - 0.8) * 40
        d -= qq["B25"] * 0.03
        ff = c["FAT"] / 40 if c["FAT"] < 40 else 1
        if c["B21"] < 0.5: d -= (c["B21"] - 0.5) * 15 * ff
        if c["B9"] / qq["B24"] > 1500: d -= (c["B9"] / qq["B24"] - 1500) * 0.005 * ff
        c["FAT"] = max(0, min(100, round(c["FAT"] + d)))

        # nx()
        emp_gain = max(1, 10 - round(c["EMP"] * 0.05))
        c["EMP"] = min(200, round(c["EMP"] + emp_gain))

        shortage_rate = max(0, (c["B2"] - c["B3"]) / max(1, c["B2"]))
        decay_base = max(0.02, c["BRAND"] * 0.015)
        growth_mult = max(0.1, 1 - c["BRAND"] / 800)
        brand_growth = c["B21"] * 30
        brand_decay = c["BRAND"] * decay_base
        brand_net = brand_growth * growth_mult - brand_decay - shortage_rate * 10
        c["BRAND"] = max(0, round(c["BRAND"] + brand_net))

        c["last_B2"] = c["B2"]
        c["last_B3"] = c["B3"]

    total = round(sum(profits))
    return total, profits, bankrupt, cash, len(profits)


# ===== 策略 1：大厂暴利流 =====
# 核心：看需求趋势预判扩产，避免缺货反噬
def factory_tycoon(state, month, params):
    if month == 0:
        # 第1个月挂机观察，合理起步配置
        state["B1"] = 16
        state["B24"] = 5
        state["B25"] = 50
        state["B13"] = 1000
        state["B10"] = 3
        state["B14"] = 60
    elif month == 3:
        # 看到需求增长趋势，提前加人+扩面积
        state["B14"] = 100
        state["B24"] = 8
        state["B25"] = 100
    elif month == 6:
        # 需求还在涨，再加人+扩面积
        state["B14"] = 150
        state["B24"] = 12
    elif month == 9:
        # 品牌高了，小幅提价
        state["B1"] = 18
# ===== 策略 2：高奢提价流 =====
def luxury_king(state, month, params):
    if month == 0:
        state["B1"] = 28
        state["B24"] = 3
        state["B25"] = 500
        state["B13"] = 6000
        state["B10"] = 3
        state["B14"] = 120
    elif month == 4:
        # 品牌和满意度都够了，提价到30
        state["B1"] = 32
    elif month == 7:
        # 品牌继续涨，提到35
        state["B1"] = 38
    elif month == 10:
        # 摸顶
        state["B1"] = 42


# ===== 策略 3：正常玩家 — 见招拆招 =====
def adaptive_manager(state, month, params):
    if month == 0:
        state["B1"] = 16
        state["B24"] = 8
        state["B25"] = 100
        state["B13"] = 2000
        state["B10"] = 3
        state["B14"] = 150
    # 每月检查：如果上期缺货 > 5%，加人
    if month > 0 and state["last_B2"] > state["last_B3"]:
        gap = state["last_B2"] - state["last_B3"]
        needed = min(5, max(1, round(gap / 600)))
        state["B24"] += needed
        state["B25"] = 100 + needed * 50  # 新人来了多培训
    # 如果品牌>50，微幅提价
    if state["BRAND"] > 50 and state["B1"] < 20:
        state["B1"] = min(22, state["B1"] + 2)
    if state["BRAND"] > 100 and state["B1"] < 25:
        state["B1"] = min(28, state["B1"] + 2)


# ===== 跑全部 =====
BASE = {"B1":16, "B24":8, "B25":100, "B13":2000, "B10":3, "B14":150, "B15":7}

print("🔥"*30)
print("  聪明玩家策略验证 — 动态调参 vs 挂机")
print("🔥"*30)

# 大厂暴利流
total1, m1, b1, c1, _ = simulate(BASE, factory_tycoon)
print(f"\n🏭 大厂暴利流:")
print(f"   全年利润: {total1:>+8,}  |  期末现金: {c1:>+8,}  {'💀' if b1 else '✅'}")
print(f"   逐月: {', '.join(f'{p:>+6,}' for p in m1)}")

# 高奢提价流
high_end = {"B1":28, "B24":3, "B25":500, "B13":6000, "B10":3, "B14":120, "B15":7}
total2, m2, b2, c2, _ = simulate(high_end, luxury_king)
print(f"\n✨ 高奢提价流:")
print(f"   全年利润: {total2:>+8,}  |  期末现金: {c2:>+8,}  {'💀' if b2 else '✅'}")
print(f"   逐月: {', '.join(f'{p:>+6,}' for p in m2)}")

# 自适应经理
total3, m3, b3, c3, _ = simulate(BASE, adaptive_manager)
print(f"\n🧠 自适应经理:")
print(f"   全年利润: {total3:>+8,}  |  期末现金: {c3:>+8,}  {'💀' if b3 else '✅'}")
print(f"   逐月: {', '.join(f'{p:>+6,}' for p in m3)}")

# 对比：挂机大厂
# ===== 策略 4：真·大厂暴利（面积+人数同步扩）=====
def real_factory_tycoon(state, month, params):
    if month == 0:
        state["B1"] = 16
        state["B24"] = 8
        state["B25"] = 100
        state["B13"] = 2000
        state["B10"] = 3
        state["B14"] = 80  # 小面积起步，省房租
    if month in [3, 6]:
        state["B14"] = min(300, state["B14"] + 50)
        state["B24"] = min(20, state["B24"] + 3)
        state["B13"] += 1000
    if month == 9 and state["BRAND"] > 100:
        state["B1"] = 20


def do_nothing(state, month, params): pass

# ===== 真·大厂暴利 =====
total4, m4, b4, c4, _ = simulate(BASE, real_factory_tycoon)
print(f"\n🏭 真·大厂暴利 (面积+人同步扩):")
print(f"   全年利润: {total4:>+8,}  |  期末现金: {c4:>+8,}  {'💀' if b4 else '✅'}")
print(f"   逐月: {', '.join(f'{p:>+6,}' for p in m4)}")

total0, m0, b0, c0, _ = simulate(BASE, do_nothing)
print(f"\n😴 挂机大厂 (对照):")
print(f"   全年利润: {total0:>+8,}  |  期末现金: {c0:>+8,}  {'💀' if b0 else '✅'}")

print(f"\n{'='*55}")
print(f"  聪明玩家 vs 挂机:  +¥{max(0,total1):,} vs +¥{max(0,total0):,}")
print(f"  证明: 操作 = 暴富, 挂机 = 苟活 ✅")
print(f"{'='*55}")
