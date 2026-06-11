"""
bakery_v4_final_sandbox.py
面包店 V4 最终公式验证沙盒 — 精确 1:1 复现 BakerySandbox.vue

用法: python bakery_v4_final_sandbox.py

两种模式:
  MODE='current' — 当前 Vue 中的公式 (sk断崖 + penalty 1.5)
  MODE='fixed'   — Gemini 修正版 (渐变sk + penalty 0.8)
"""

import math

# ============================================================
# 全局状态
# ============================================================
class State:
    def __init__(self):
        self.reset()

    def reset(self):
        self.B1 = 16; self.B2 = 0; self.B3 = 0; self.B4 = 2; self.B5 = 0
        self.B6 = 0; self.B7 = 0; self.B8 = 0; self.B9 = 0; self.B10 = 3
        self.B11 = 0; self.B12 = 0; self.B13 = 2000; self.B14 = 150
        self.B15 = 7; self.B21 = 0.8; self.B24 = 8; self.B25 = 100
        self.FAT = 40; self.EMP = 0; self.BRAND = 0; self.TRAFFIC = 0
        self.month_log = []
        self.p = 0; self.t = 0; self.m = 1

    def copy_from(self, other):
        for k, v in other.__dict__.items():
            if k != 'month_log':
                setattr(self, k, v)
        self.month_log = list(other.month_log)


def safe(v, d=0):
    return v if v is not None and isinstance(v, (int, float)) and not math.isnan(v) and math.isfinite(v) else d


# ============================================================
# sk 曲线 — 两种模式
# ============================================================
def sk_current(c4):
    """当前 Vue 中的断崖版本"""
    v = float(c4)
    if not math.isfinite(v):
        return 1.0
    if v < 80:
        return 1.0
    elif v < 90:
        return 0.30
    else:
        return 0.10


def sk_fixed(c4):
    """Gemini 平滑渐变版本"""
    v = float(c4)
    if not math.isfinite(v):
        return 1.0
    if v < 20:
        return 1.0 + (20 - v) / 20 * 0.1        # 1.10 → 1.00
    elif v < 60:
        return 1.0                                 # 1.00
    elif v < 80:
        return 1.0 - (v - 60) / 20 * 0.2          # 1.00 → 0.80
    elif v < 90:
        return 0.80 - (v - 80) / 10 * 0.5         # 0.80 → 0.30
    else:
        return max(0.10, 0.30 - (v - 90) / 10 * 0.2)  # 0.30 → 0.10


# ============================================================
# 核心公式 (完全 1:1 复现 BakerySandbox.vue)
# ============================================================
def rc(state, sk_func, params, penalty_mult=1.5):
    """
    rc() — 实时计算 (完全对齐 BakerySandbox.vue 的 rc())
    penalty_mult: 利用率惩罚乘数 (当前1.5, 建议0.8)
    """
    q = params  # gp() 参数

    # 工资 B9
    state.B9 = round(q.B24 * 1200 * (1 + q.B15 * 0.15 * max(0, 1 - q.B24 * 0.08)))

    # 物理产能 ph
    ph = max(1, min(q.B14 * 25, q.B24 * 600) + max(0, round((2 - safe(state.B4)) * 200)))
    ph = int(ph)

    # 实际产能 B3 = 物理 × 疲劳系数
    state.B3 = max(0, round(ph * sk_func(state.FAT)))

    # 报废率 B4
    state.B4 = max(0.1, max(0.1, 2 - state.B3 * 0.0002) * (1 - safe(state.EMP) * 0.002))
    state.B4 = round(state.B4 * 10000) / 10000

    # 价格弹性 pb
    pb = (1 + (20 - q.B1) * 0.15) if q.B1 < 20 else max(0.6, 1 - (q.B1 - 20) * 0.03)

    # 面积杠杆
    area_lever = 1 + q.B14 / 100

    # 客流 tr
    base_tr = round(250 * q.B15) + round(safe(state.BRAND) * 3)
    mkt_tr = round(math.sqrt(max(0, q.B13)) * 12)
    tr = round(base_tr * pb) + round(mkt_tr * area_lever)

    # 最高可接受价 ma
    ma = max(1, 10 + q.B15 * 1.2 + safe(state.BRAND) * 0.3 + safe(state.B21) * 4)

    # 需求 B2
    if q.B1 <= ma:
        conv = 0.5 + (ma - q.B1) / ma * 0.4
    else:
        conv = max(0.05, 0.5 * ma / q.B1)
    state.B2 = max(0, round(tr * conv))

    # 房租 B5
    state.B5 = max(0, round(q.B14 * q.B15 * max(2, 20 - q.B14 * 0.05)))

    # 满意度 B21
    pp = safe(state.B9) / max(state.B3, 1)
    bl = 3 + q.B15 * 0.4
    if pp >= bl:
        ps = 0.7 + min((pp - bl) / (bl * 2), 0.3)
    else:
        ps = pp / bl * 0.7
    over_penalty = max(0, state.B3 / ph - 0.8) * penalty_mult
    state.B21 = round(min(1, max(0, ps - over_penalty)) * 1000) / 1000

    # 原料折扣 B12
    state.B12 = round(q.B10 * (1 - min(0.5, state.B3 * 0.00008)) * 100) / 100

    # 单位其他成本 B11
    state.B11 = safe(state.B4) + state.B3 * 0.002

    # 实际销售 B6 = min(需求, 产能)
    state.B6 = min(state.B2, state.B3)

    # 收入 B7
    state.B7 = state.B6 * q.B1

    # 利润 B8
    state.B8 = round(state.B7 - (state.B12 + 1 + safe(state.B4)) * state.B3
                     - state.B5 - state.B9 - q.B13
                     - q.B25 * q.B24 - round(0.05 * q.B24 * 1500))

    state.TRAFFIC = tr
    return ph


def fd(state, sk_func, params):
    """fd() — 疲劳累计 (完全对齐 BakerySandbox.vue)"""
    q = params
    ph = max(1, min(q.B14 * 25, q.B24 * 600) + max(0, round((2 - safe(state.B4)) * 200)))
    ph = int(ph)

    d = 3  # 基线熵增

    if q.B25 == 0 and (state.B3 / ph) > 0.7:
        d += 5
    elif q.B25 == 0:
        d += 2

    if (state.B3 / ph) > 0.8:
        d += ((state.B3 / ph) - 0.8) * 40

    d -= q.B25 * 0.03

    ff = state.FAT / 40 if state.FAT < 40 else 1

    if safe(state.B21) < 0.5:
        d -= (safe(state.B21) - 0.5) * 15 * ff

    if safe(state.B9) / q.B24 > 1500:
        d -= (safe(state.B9) / q.B24 - 1500) * 0.005 * ff

    return max(0, min(100, round(state.FAT + d)))


def nx(state, sk_func, params, penalty_mult=1.5):
    """nx() — 下月推进"""
    if state.m >= 36:
        return False

    ph = rc(state, sk_func, params, penalty_mult)
    nf = fd(state, sk_func, params)
    pf = round(state.B8)

    state.month_log.append({'m': state.m, 'p': state.p, 't': state.t})

    # 经验边际递减
    state.EMP = min(200, round(safe(state.EMP) + max(1, 10 - round(safe(state.EMP) * 0.05))))

    # 品牌含缺货惩罚 + 天花板
    shortage_rate = max(0, (state.B2 - state.B3) / max(1, state.B2))
    brand_growth = safe(state.B21) * 30
    brand_decay = safe(state.BRAND) * max(0.02, safe(state.BRAND) * 0.015)
    growth_mult = max(0.1, 1 - safe(state.BRAND) / 800)
    state.BRAND = max(0, round(safe(state.BRAND) + brand_growth * growth_mult - brand_decay - shortage_rate * 10))

    state.FAT = nf
    state.p = pf
    state.t += pf
    state.m += 1
    return True


# ============================================================
# 推演引擎
# ============================================================
def simulate(label, params, sk_func, penalty_mult=1.5, years=3):
    state = State()
    months = years * 12

    # 逐月推演
    while nx(state, sk_func, params, penalty_mult):
        pass

    # 记录逐月利润
    state2 = State()
    per_month = []
    for i in range(months):
        ph = rc(state2, sk_func, params, penalty_mult)
        nf = fd(state2, sk_func, params)
        per_month.append(state2.B8)

        # 手动推进 (不调用nx以避免重复)
        shortage_rate = max(0, (state2.B2 - state2.B3) / max(1, state2.B2))
        brand_growth = safe(state2.B21) * 30
        brand_decay = safe(state2.BRAND) * max(0.02, safe(state2.BRAND) * 0.015)
        growth_mult = max(0.1, 1 - safe(state2.BRAND) / 800)
        state2.BRAND = max(0, round(safe(state2.BRAND) + brand_growth * growth_mult - brand_decay - shortage_rate * 10))
        state2.EMP = min(200, round(safe(state2.EMP) + max(1, 10 - round(safe(state2.EMP) * 0.05))))
        state2.FAT = nf

    total = sum(per_month)
    final_brand = state2.BRAND
    final_fat = state2.FAT
    final_emp = state2.EMP
    final_sat = state2.B21
    final_b1 = params.B1
    final_b3 = state2.B3

    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"  {'─' * 60}")
    print(f"  参数: 售价¥{params.B1}  员工{params.B24}人  培训¥{params.B25}  营销¥{params.B13}  面积{params.B14}㎡  进价¥{params.B10}")
    print(f"  最终状态: 品牌={final_brand}  疲劳={final_fat}  经验={final_emp}  满意度={final_sat:.3f}")

    for y in range(years):
        start = y * 12
        end = start + 12
        annual = sum(per_month[start:end])
        print(f"  第{y+1}年: {'+' if annual >= 0 else ''}¥{annual:+,}")

    print(f"  {'─' * 60}")
    print(f"  3年总计: {'+' if total >= 0 else ''}¥{total:+,}  年均: {'+' if total >= 0 else ''}¥{round(total/years):+,}")

    # 半年逐月
    if years >= 3:
        print(f"\n  第3年逐月利润 (月25-36):")
        for i, v in enumerate(per_month[24:36]):
            print(f"    月{i+25}: {'+' if v >= 0 else ''}¥{v:+,}")

    return total


# ============================================================
# 测试路线
# ============================================================
class Params:
    def __init__(self, B1, B24, B25, B13, B14, B10=3):
        self.B1 = B1; self.B24 = B24; self.B25 = B25
        self.B13 = B13; self.B14 = B14; self.B10 = B10
        self.B15 = 7

ROUTES = [
    Params(B1=16, B24=8,  B25=100, B13=8000, B14=250, B10=3),
    Params(B1=30, B24=3,  B25=500, B13=5000, B14=80,  B10=3),
    Params(B1=22, B24=3,  B25=200, B13=1500, B14=60,  B10=3),
    Params(B1=16, B24=8,  B25=0,   B13=0,    B14=150, B10=3),
]

ROUTE_LABELS = ['🏭 大厂走量', '✨ 高奢溢价', '🏠 社区精酿', '🛌 躺平']

print("=" * 68)
print("  面包店 V4 — A/B 对比验证")
print("  A: 当前Vue公式 (sk断崖 + penalty 1.5)")
print("  B: Gemini修正版 (渐变sk + penalty 0.8)")
print("=" * 68)

for mode_name, sk_fn, penalty in [
    ('【A】当前Vue', sk_current, 1.5),
    ('【B】Gemini修正', sk_fixed, 0.8),
]:
    print(f"\n\n{'#' * 68}")
    print(f"  # {mode_name}")
    print(f"  # sk断崖={'ON' if sk_fn is sk_current else '渐变'} | 惩罚乘数={penalty}")
    print(f"{'#' * 68}")
    for r, label in zip(ROUTES, ROUTE_LABELS):
        simulate(label, r, sk_fn, penalty)

print(f"\n\n{'=' * 68}")
print("  📊 感度测试: 大厂路线 — 面积×定价矩阵 (Gemini修正版)")
print(f"{'=' * 68}")

for area in [200, 250, 300]:
    for price in [14, 16, 18]:
        simulate(f"  大厂 {area}㎡ ¥{price}", Params(B1=price, B24=8, B25=100, B13=8000, B14=area, B10=3),
                 sk_fixed, 0.8)

print(f"\n\n{'=' * 68}")
print("  场景压测: 大厂 不同培训/营销投入 (Gemini修正版)")
print(f"{'=' * 68}")

for train in [0, 100, 300]:
    for mkt in [2000, 5000, 8000]:
        s = simulate(f"  培训¥{train}/人 营销¥{mkt}",
                      Params(B1=16, B24=8, B25=train, B13=mkt, B14=250, B10=3),
                      sk_fixed, 0.8)
