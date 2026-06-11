"""
5M目标 — 哪种策略最快？
支持跨期策略切换（比如先大厂养品牌，再提价收割）

策略矩阵:
  A. 大厂到底   300㎡ ¥18 
  B. 高奢到底   80㎡  ¥30
  C. 社区到底   60㎡  ¥22
  D. 先大厂后提价  3年¥14→3年¥18→3年¥22
  E. 先小后大  社区2年→扩产大厂
  F. 精益求精  渐近提价（每月提¥1到上限）
"""
import math

class State:
    def reset(self, params):
        self.params = params
        self.B1=params.B1; self.B2=0; self.B3=0; self.B4=2; self.B5=0
        self.B6=0; self.B7=0; self.B8=0; self.B9=0; self.B10=params.B10
        self.B11=0; self.B12=0; self.B13=params.B13; self.B14=params.B14
        self.B15=7; self.B21=0.8; self.B24=params.B24; self.B25=params.B25
        self.FAT=40; self.EMP=0; self.BRAND=0; self.TRAFFIC=0
        self.t=0; self.m=0; self.monthly_profits=[]

def sk(v):
    if v < 20: return 1.0 + (20-v)/20*0.1
    if v < 60: return 1.0
    if v < 80: return 1.0 - (v-60)/20*0.2
    if v < 90: return 0.80 - (v-80)/10*0.5
    return max(0.10, 0.30 - (v-90)/10*0.2)

def one_month(s):
    p = s.params
    s.B9 = round(p.B24 * 1200 * (1 + s.B15 * 0.15 * max(0, 1 - p.B24 * 0.08)))
    ph = max(1, min(p.B14 * 25, p.B24 * 600) + max(0, round((2 - s.B4) * 200)))
    s.B3 = max(0, round(ph * sk(s.FAT)))
    s.B4 = max(0.1, max(0.1, 2 - s.B3 * 0.0002) * (1 - s.EMP * 0.002))
    
    pb = (1 + (20 - s.B1) * 0.15) if s.B1 < 20 else max(0.6, 1 - (s.B1 - 20) * 0.03)
    area_lever = 1 + p.B14 / 100
    base_tr = round(250 * s.B15) + round(s.BRAND * 3)
    mkt_tr = round(math.sqrt(max(0, p.B13)) * 12)
    tr = round(base_tr * pb) + round(mkt_tr * area_lever)
    ma = max(1, 10 + s.B15 * 1.2 + s.BRAND * 0.3 + s.B21 * 4)
    conv = (0.5 + (ma - s.B1) / ma * 0.4) if s.B1 <= ma else max(0.05, 0.5 * ma / s.B1)
    s.B2 = max(0, round(tr * conv))
    s.B5 = max(0, round(p.B14 * s.B15 * max(2, 20 - p.B14 * 0.05)))
    
    pp = s.B9 / max(s.B3, 1)
    bl = 3 + s.B15 * 0.4
    ps = (0.7 + min((pp - bl) / (bl * 2), 0.3)) if pp >= bl else (pp / bl * 0.7)
    util = s.B3 / ph
    over_penalty = max(0, util - 0.8) * 0.8
    s.B21 = round(min(1, max(0, ps - over_penalty)) * 1000) / 1000
    
    s.B12 = round(p.B10 * (1 - min(0.5, s.B3 * 0.00008)) * 100) / 100
    s.B6 = min(s.B2, s.B3)
    s.B7 = s.B6 * s.B1
    profit = round(s.B7 - (s.B12 + 1 + s.B4) * s.B3 - s.B5 - s.B9 - p.B13 - p.B25 * p.B24 - round(0.05 * p.B24 * 1500))
    s.TRAFFIC = tr
    s.B8 = profit
    
    # fd
    d = 3
    if p.B25 == 0 and (s.B3 / ph) > 0.7: d += 5
    elif p.B25 == 0: d += 2
    if (s.B3 / ph) > 0.8: d += ((s.B3 / ph) - 0.8) * 40
    d -= p.B25 * 0.03
    ff = s.FAT / 40 if s.FAT < 40 else 1
    if s.B21 < 0.5: d -= (s.B21 - 0.5) * 15 * ff
    if s.B9 / p.B24 > 1500: d -= (s.B9 / p.B24 - 1500) * 0.005 * ff
    nf = max(0, min(100, round(s.FAT + d)))
    
    # nx
    shortage_rate = max(0, (s.B2 - s.B3) / max(1, s.B2))
    brand_growth = s.B21 * 30
    brand_decay = s.BRAND * max(0.02, s.BRAND * 0.015)
    growth_mult = max(0.1, 1 - s.BRAND / 800)
    s.BRAND = max(0, round(s.BRAND + brand_growth * growth_mult - brand_decay - shortage_rate * 10))
    s.EMP = min(200, round(s.EMP + max(1, 10 - round(s.EMP * 0.05))))
    s.FAT = nf
    s.t += profit
    s.m += 1
    s.monthly_profits.append(profit)
    return profit

def run_fixed(params, max_months=600):
    """固定参数跑到目标或上限"""
    s = State()
    s.reset(params)
    profits = []
    for m in range(max_months):
        profit = one_month(s)
        profits.append(profit)
        if s.t >= 5_000_000:
            break
    return s.m, s.t, s.BRAND, s.FAT, s.EMP, s.B21, profits

def run_ramp(params_start, params_end, ramp_start_month, max_months=600):
    """
    前 ramp_start_month 个月用 params_start，之后切换到 params_end
    """
    s = State()
    s.reset(params_start)
    
    for m in range(max_months):
        # 策略切换
        if m == ramp_start_month:
            p_new = params_end
            s.params = p_new
            s.B1 = p_new.B1
            s.B10 = p_new.B10
            s.B13 = p_new.B13
            s.B14 = p_new.B14
            s.B24 = p_new.B24
            s.B25 = p_new.B25
        
        profit = one_month(s)
        if s.t >= 5_000_000:
            break
    
    return s.m, s.t, s.BRAND, s.FAT, s.EMP, s.B21, s.monthly_profits

def run_gradual(params_base, schedule):
    """
    schedule: [(price, month), ...] — 在第 month 个月提价到 price
    """
    s = State()
    sp = params_base._replace(B1=schedule[0][0]) if hasattr(params_base, '_replace') else Params(**{k:getattr(params_base,k) for k in ['B1','B24','B25','B13','B14','B10']})
    # Actually let me just use a simpler approach
    return None

class Params:
    def __init__(self, B1, B24, B25, B13, B14, B10=3, label=""):
        self.B1=B1; self.B24=B24; self.B25=B25; self.B13=B13; self.B14=B14; self.B10=B10
        self.label=label

def fmt_months(m):
    years = m // 12
    months = m % 12
    return f"{years}年{months}月" if months else f"{years}年整"

strategies = [
    Params(18, 8, 100, 8000, 300, 3, "大厂到底 300㎡ ¥18"),
    Params(16, 8, 100, 8000, 300, 3, "大厂到底 300㎡ ¥16"),
    Params(18, 8, 100, 8000, 250, 3, "大厂到底 250㎡ ¥18"),
    Params(30, 3, 500, 5000, 80, 3, "高奢到底 80㎡ ¥30"),
    Params(22, 3, 200, 1500, 60, 3, "社区到底 60㎡ ¥22"),
]

print("=" * 75)
print("  5M 目标 — 各路线稳态速度")
print("=" * 75)
print(f"  {'策略':<28s} {'到达月':>7s} {'总利润':>10s} {'最终品牌':>8s} {'稳态月利润':>10s}")
print(f"  {'-'*28} {'-'*7} {'-'*10} {'-'*8} {'-'*10}")

for sp in strategies:
    months, total, brand, fat, emp, sat, profits = run_fixed(sp)
    steady = sum(profits[-12:]) // 12 if len(profits) >= 12 else profits[-1]
    years_to_5m = (5_000_000 - total) / max(steady, 1) / 12
    print(f"  {sp.label:<28s} {fmt_months(months):>7s} ¥{total:>8,}  {brand:>4d}     ¥{steady:>7,}/月  (还需{years_to_5m:.0f}年)")
    if len(profits) >= 12:
        print(f"  {'':28s}  [首年¥{sum(profits[:12]):>8,} → 末年均¥{sum(profits[-12:]):>8,}]")

# == 策略切换场景 ==
print(f"\n{'=' * 75}")
print("  策略切换 — 先养品牌再提价")
print("=" * 75)

# 大厂3年 → 提价 → 继续
switches = [
    ("大厂 ¥14 → ¥18 (3年切换)", Params(14,8,100,8000,300,3), Params(18,8,100,8000,300,3), 36),
    ("大厂 ¥14 → ¥22 (3年切换)", Params(14,8,100,8000,300,3), Params(22,8,100,8000,300,3), 36),
    ("大厂 ¥16 → ¥22 (3年切换)", Params(16,8,100,8000,300,3), Params(22,8,100,8000,300,3), 36),
    ("大厂 ¥16 → ¥25 (3年切换)", Params(16,8,100,8000,300,3), Params(25,8,100,8000,300,3), 36),
    ("大厂 ¥18 → ¥25 (3年切换)", Params(18,8,100,8000,300,3), Params(25,8,100,8000,300,3), 36),
    ("社区 → 大厂提价(2年)", Params(22,3,200,1500,60,3), Params(22,8,100,8000,250,3), 24),
    ("社区 → 精品大厂(2年)", Params(22,3,200,1500,60,3), Params(25,6,300,8000,150,3), 24),
]

print(f"  {'策略':<35s} {'到达月':>7s} {'总利润':>10s} {'最终品牌':>6s} {'稳态月利润':>10s}")
print(f"  {'-'*35} {'-'*7} {'-'*10} {'-'*6} {'-'*10}")

for label, p1, p2, switch_month in switches:
    months, total, brand, fat, emp, sat, profits = run_ramp(p1, p2, switch_month)
    steady = sum(profits[-12:]) // 12 if len(profits) >= 12 else profits[-1]
    years_to_5m = (5_000_000 - total) / max(steady, 1) / 12 if steady > 0 else float('inf')
    reachable = "可达" if steady > 0 else "永远达不到"
    y = f"还需{years_to_5m:.0f}年" if years_to_5m < 100 else reachable
    print(f"  {label:<35s} {fmt_months(months):>7s} ¥{total:>8,}  {brand:>4d}    ¥{steady:>7,}/月  ({y})")
    if len(profits) >= 60:
        y1 = sum(profits[:12])
        y2 = sum(profits[12:24])
        y3 = sum(profits[24:36])
        y4 = sum(profits[36:48])
        y5 = sum(profits[48:60])
        print(f"  {'':35s}  [逐年: ¥{y1:>7,} ¥{y2:>7,} ¥{y3:>7,} ¥{y4:>7,} ¥{y5:>7,}]")

# == 渐进提价场景 ==
print(f"\n{'=' * 75}")
print("  渐进提价 — 每24个月+¥2，从¥14起步")
print("=" * 75)

# 大厂300㎡ 每2年提¥2: ¥14→¥16→¥18→¥20→¥22
base = Params(14, 8, 100, 8000, 300, 3)
s = State()
s.reset(base)
for target_b1 in [14, 16, 18, 20, 22]:
    s.params.B1 = target_b1
    s.B1 = target_b1
    for _ in range(24):
        one_month(s)
        if s.t >= 5_000_000:
            break
    if s.t >= 5_000_000:
        break

total = s.t
steady = sum(s.monthly_profits[-12:]) // 12
print(f"  大厂300㎡ 每2年提¥2: ¥14→¥16→¥18→¥20→¥22")
print(f"  到达: {fmt_months(s.m)}, 总利润: ¥{total:,}, 最终品牌: {s.BRAND}")
print(f"  末段月均: ¥{steady:,}/月")
print(f"  {'→ 可行!' if total >= 5_000_000 else '→ 还不够'}")
if total < 5_000_000:
    remaining = 5_000_000 - total
    extra_years = remaining / max(steady, 1) / 12
    print(f"  还需{extra_years:.0f}年 (稳态¥{steady:,}/月)")
