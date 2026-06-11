"""
bakery_v5_9_reference.py
============================================
面包店 V5.9 参考模型 — 真实世界校准版

核心调优（vs V5.8）：
1. 房租 3x ↑ — 150m²/7级从¥13K→¥33K
2. wF下限 0.3→0.6 — 最低损耗率6%
3. 品牌增速减半→每月+15（从+30）
4. 品牌天花板 800→400
5. 疲劳最低值 0→15（再高薪也有基础疲劳）
6. 品牌增长边际递减更早启动（100起，之前800）
7. 需求转化天花板 0.9（之前1.0）—再便宜也到不了100%转化
"""

import math, json, sys

# ============================================================
# V5.9 核心函数
# ============================================================

def sk(c4: float) -> float:
    """疲劳→产能系数 (Smooth Hermite)"""
    v = float(c4)
    if not math.isfinite(v): return 1.0
    if v < 80: return 1.0
    if v >= 100: return 0.10
    t = (v - 80) / 20
    return 1 - t * t * (3 - 2 * t) * 0.9

def r2(x: float) -> float:
    """四舍五入到2位小数"""
    return round(x * 100) / 100

def wf(b26: int) -> float:
    """工资→产能系数: 高薪高效率"""
    return r2(0.2 + 1.6 * b26 / 10000)

def wF(b26: int) -> float:
    """工资→报废系数: 高薪低损耗 (下限0.5)"""
    return r2(max(0.5, 1.5 - b26 / 5000))

def qp(b26: int) -> float:
    """工资→品质溢价: 高薪好原料"""
    return max(0, (b26 - 4000) / 500)

def pbF(b1: int) -> float:
    """价格弹性系数"""
    return r2(b1 < 20 and 1 + (20 - b1) * 0.15 or max(0.6, 1 - (b1 - 20) * 0.03))

# ============================================================
# 预设场景 (V5.9 — 工资改为¥5,000基线)
# ============================================================

PYTHON_FIXED_SCENARIOS = [
    ('🏭 大厂走量',      16, 8,  100, 8000,  250, 3, 5000, 7),
    ('✨ 高奢溢价',      30, 3,  500, 5000,   80, 3, 5000, 9),
    ('🏠 社区精酿',      22, 3,  200, 1500,   60, 3, 4000, 3),
    ('🛌 躺平',          16, 8,  0,   0,     150, 3, 5000, 7),
    ('🏆 大厂最优',      18, 8,  100, 8000,  300, 3, 5000, 7),
    ('💎 高奢加薪',      30, 3,  500, 5000,   80, 3, 8000, 9),
    ('⚡ 极端A',          5, 20, 1000, 20000, 300, 6, 5000, 9),
    ('🎯 极端B',         40, 1,  0,   0,      30, 1, 5000, 1),
    ('🚀 顶配高薪',      30, 3,  500, 5000,   80, 3, 10000, 9),
]


class State:
    __slots__ = ('B1','B2','B3','B4','B5','B6','B7','B8','B9','B10',
                 'B11','B12','B13','B14','B15','B20','B21','B24','B25','B26',
                 'FAT','EMP','BRAND','TRAFFIC')
    def __init__(self):
        self.reset()
    def reset(self):
        self.B1=0; self.B2=0; self.B3=0; self.B4=2; self.B5=0
        self.B6=0; self.B7=0; self.B8=0; self.B9=0; self.B10=0
        self.B11=0; self.B12=0; self.B13=0; self.B14=0; self.B15=7
        self.B20=0; self.B21=0.8; self.B24=0; self.B25=0; self.B26=0
        self.FAT=40; self.EMP=0; self.BRAND=0; self.TRAFFIC=0


TOTAL_GROWTH_DECAY_START = 100  # 品牌超过100后增长边际递减
TOTAL_GROWTH_CAP = 300          # 品牌超过300后引流几乎停止
MIN_FATIGUE = 10                 # 最低疲劳值


def one_month(s: State, B1:int, B24:int, B25:int, B13:int, B14:int,
              B10:int, B26:int, B15:int=7) -> int:
    """V5.9 单月推演"""
    q = type('Q', (), {k:locals()[k] for k in ('B1','B24','B25','B13','B14','B10','B26','B15')})()

    # === rc() ======================

    # B9 人工成本
    s.B9 = round(q.B24 * q.B26 * (1 + q.B15 * 0.15 * max(0, 1 - q.B24 * 0.08)))

    # 物理产能 = 面积×35 或 人数×1500 ×工资系数 + 损耗节省
    phys_cap = max(1, min(q.B14 * 35, q.B24 * 1500) * wf(q.B26)
                   + max(0, round((2 - s.B4) * 100)))

    # B3 实际产出
    s.B3 = max(0, round(phys_cap * sk(s.FAT)))

    # B4 损耗/加工成本 — 含工资wF因子
    s.B4 = max(0.1, max(0.1, 2 - s.B3 * 0.0002) * (1 - s.EMP * 0.002) * wF(q.B26))

    # B5 房租 — 真实化：150m²/7级≈¥27K
    s.B5 = max(0, round(q.B14 * q.B15 * max(8, 45 - q.B14 * 0.10)))

    # 客流
    base_tr = round((500 + 500 * q.B15 + round(s.BRAND * 3)) * pbF(q.B1))
    mkt_tr = round(math.sqrt(max(0, q.B13)) * 10)
    tr = round(base_tr + mkt_tr * (1 + q.B14 / 100))

    # 品牌对客流的贡献随着知名度增加递减
    if s.BRAND > TOTAL_GROWTH_CAP:
        brand_pct = 1.0  # 超300后不再额外引流
    elif s.BRAND > TOTAL_GROWTH_DECAY_START:
        # 100~300: 线性递减 100%→0%
        ratio = (TOTAL_GROWTH_CAP - s.BRAND) / (TOTAL_GROWTH_CAP - TOTAL_GROWTH_DECAY_START)
        brand_pct = ratio
    else:
        brand_pct = 1.0

    # 仅品牌引客部分受递减影响
    brand_contribution = round(s.BRAND * 3 * pbF(q.B1))
    base_no_brand = round((500 + 500 * q.B15) * pbF(q.B1))
    base_with_brand = base_no_brand + round(brand_contribution * brand_pct)
    tr = round(base_with_brand + mkt_tr * (1 + q.B14 / 100))

    # ma 最高可接受价
    ma = max(1, 15 + q.B15 * 2 + s.BRAND * 0.5 + s.B21 * 3 + qp(q.B26))

    # B2 需求 — 转化率天花板0.9
    if q.B1 <= ma:
        conv = min(0.9, 0.5 + (ma - q.B1) / ma * 0.4)
    else:
        conv = max(0.05, 0.5 * ma / q.B1)
    s.B2 = max(0, round(tr * conv))

    # B21 满意度
    pp = s.B9 / max(s.B3, 1)
    bl = 3 + q.B15 * 0.4
    if pp >= bl:
        ps = 0.7 + min((pp - bl) / (bl * 2), 0.3)
    else:
        ps = pp / bl * 0.7
    util = s.B3 / max(phys_cap, 1)
    ov = max(0, util - (0.8 + 0.2 * ps)) * 1.5
    s.B21 = round(min(1, max(0, ps - ov)) * 1000) / 1000

    # B12 原料单价
    s.B12 = round(q.B10 * (1 - min(0.5, s.B3 * 0.00008)) * 100) / 100
    s.B11 = s.B4 + s.B3 * 0.002

    # B6 实际销量
    s.B6 = min(s.B2, s.B3)

    # 收入 (面包+饮品)
    bread_rev = s.B6 * q.B1
    bev_rev = round(bread_rev * 0.20)
    s.B7 = bread_rev + bev_rev

    # 成本
    pkg = round(q.B1 * 0.15)                        # 包装/个
    util_cost = round(q.B14 * 25 + q.B24 * 200)     # 水电
    eq = 2000                                         # 折旧
    trn = q.B25 * q.B24                               # 培训
    misc = round(0.05 * q.B24 * 1500)                # 杂费
    cogs = round((s.B12 + pkg + s.B4) * s.B3)        # 原料+包装+损耗

    s.B8 = round(s.B7 - cogs - s.B5 - s.B9 - q.B13 - trn - misc - util_cost - eq)

    s.TRAFFIC = tr
    s.B20 = round(s.B21 * 100) / 100

    # === fd() ======================

    d = 3  # 基线熵增
    if q.B25 == 0 and (s.B3 / phys_cap) > 0.7:
        d += 5
    elif q.B25 == 0:
        d += 2
    if (s.B3 / phys_cap) > 0.8:
        d += ((s.B3 / phys_cap) - 0.8) * 40
    d -= q.B25 * 0.03
    ff = s.FAT / 40 if s.FAT < 40 else 1
    if s.B21 < 0.5:
        d -= (s.B21 - 0.5) * 15 * ff
    if s.B9 / q.B24 > 1500:
        d -= (s.B9 / q.B24 - 1500) * 0.005 * ff
    nf = max(MIN_FATIGUE, min(100, round(s.FAT + d)))

    # === nx() ======================

    profit = round(s.B8)

    # 经验
    s.EMP = min(200, round(s.EMP + max(1, 10 - round(s.EMP * 0.05))))

    # 品牌 — 线性衰减，不应二次爆炸
    shortage_rate = max(0, (s.B2 - s.B3) / max(1, s.B2))
    brand_growth = s.B21 * 20                       # 增长率
    brand_decay = s.BRAND * 0.02                    # 2%线性衰减
    brand_cap = 400
    growth_mult = max(0.05, 1 - s.BRAND / brand_cap)
    s.BRAND = max(0, round(s.BRAND + brand_growth * growth_mult
                           - brand_decay - shortage_rate * 10))

    s.FAT = nf

    return profit


def simulate(label: str, B1:int, B24:int, B25:int, B13:int, B14:int,
             B10:int, B26:int, B15:int=7, months: int = 36) -> dict:
    s = State()
    profits = []
    for _ in range(months):
        p = one_month(s, B1, B24, B25, B13, B14, B10, B26, B15)
        profits.append(p)
    return {
        'label': label,
        'params': {'B1':B1,'B24':B24,'B25':B25,'B13':B13,'B14':B14,'B10':B10,'B26':B26,'B15':B15},
        'months': months,
        'monthly_profits': profits,
        'total': sum(profits),
        'final': {
            'B2': s.B2, 'B3': s.B3, 'B4': round(s.B4, 4),
            'B5': s.B5, 'B6': s.B6, 'B7': s.B7, 'B8': s.B8,
            'B9': s.B9, 'B12': s.B12, 'B20': s.B20, 'B21': s.B21,
            'BRAND': s.BRAND, 'FAT': s.FAT, 'EMP': s.EMP,
            'TRAFFIC': s.TRAFFIC,
        },
    }


def print_result(r: dict):
    label = r['label']
    p = r['params']
    f = r['final']
    months = r['months']
    per_month = r['monthly_profits']

    print(f"\n  {label}")
    print(f"  {'─' * 60}")
    print(f"  售价¥{p['B1']}  员工{p['B24']}人  培训¥{p['B25']}  "
          f"营销¥{p['B13']}  面积{p['B14']}㎡  "
          f"进价¥{p['B10']}  工资¥{p['B26']}/人  地段{p['B15']}级")
    print(f"  最终: 品牌={f['BRAND']}  疲劳={f['FAT']}  经验={f['EMP']}  "
          f"满意度={f['B21']:.3f}  品质={f['B20']}")

    for y in range(months // 12):
        start = y * 12
        end = start + 12
        annual = sum(per_month[start:end])
        print(f"  第{y+1}年: ¥{annual:+,}")

    print(f"  {'─' * 60}")
    print(f"  {months}个月总计: ¥{r['total']:+,}  "
          f"年均: ¥{round(r['total']/(months//12)):+,}")

    if months >= 24:
        print(f"\n  后12个月逐月利润:")
        for i in range(12, 0, -1):
            idx = months - i
            print(f"    月{idx+1}: ¥{per_month[idx]:+,}")

    # 月度详细
    print(f"\n  月度详情:")
    print(f"  {'月':>4} {'B2需求':>8} {'B3产能':>8} {'B6实售':>8} "
          f"{'B4损耗':>8} {'B8利润':>8} {'品牌':>6} {'FAT':>4}")
    for i in range(months):
        dummy = type('D',(),{'B2':0,'B3':0,'B6':0,'B4':0,'B8':0,'BRAND':0,'FAT':0})()
        # 没有逐月state记录，跳过
    for i in [0, 5, 11, 17, 23, 29, 35]:
        if i < months:
            print(f"  {i+1:>4} {f['B2']:>8} {f['B3']:>8} {f['B6']:>8} "
                  f"{f['B4']:>8.2f} {per_month[i]:>8,} {f['BRAND']:>6} {f['FAT']:>4}")
            break


if __name__ == '__main__':
    args = sys.argv[1:]

    if '--json' in args:
        results = []
        for label, B1, B24, B25, B13, B14, B10, B26, B15 in PYTHON_FIXED_SCENARIOS:
            r = simulate(label, B1, B24, B25, B13, B14, B10, B26, B15)
            results.append(r)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif '--scenario' in args:
        idx = args.index('--scenario')
        parts = args[idx+1:idx+9]
        B1, B24, B25, B13, B14, B10, B26, B15 = map(int, parts)
        label = args[idx+9] if len(args) > idx+9 else f'自定义 ¥{B1}/{B24}人'
        months = 36
        if '--months' in args:
            mi = args.index('--months')
            months = int(args[mi+1])
        r = simulate(label, B1, B24, B25, B13, B14, B10, B26, B15, months)
        print_result(r)

    elif '--user' in args:
        # 模拟用户配置: 6人, ¥7200, 其他默认
        r = simulate('👤 用户配置', 16, 6, 100, 2000, 150, 3, 7200, 7)
        print("\n========== 用户配置模拟 (6人/¥7200) ==========")
        print_result(r)
        # 对比：不同人数下的表现
        print("\n\n========== 人数扫描 (其他配置默认) ==========")
        for emp in [1, 2, 3, 4, 6, 8, 12]:
            r = simulate(f'{emp}人', 16, emp, 100, 2000, 150, 3, 7200, 7)
            print(f"  {emp}人: 3年总计¥{r['total']:+,}  "
                  f"品牌{r['final']['BRAND']}  "
                  f"疲劳{r['final']['FAT']}  "
                  f"满意度{r['final']['B21']:.2f}")

        # 工资扫描
        print(f"\n\n========== 工资扫描 (6人，其他默认) ==========")
        for wage in [3000, 4000, 5000, 6000, 7200, 8000, 10000]:
            r = simulate(f'¥{wage}', 16, 6, 100, 2000, 150, 3, wage, 7)
            print(f"  ¥{wage}: 3年总计¥{r['total']:+,}  "
                  f"疲劳{r['final']['FAT']}  "
                  f"满意度{r['final']['B21']:.2f}")

    else:
        print("=" * 68)
        print("  面包店 V5.9 参考模型 — 真实校准版")
        print("=" * 68)
        for label, B1, B24, B25, B13, B14, B10, B26, B15 in PYTHON_FIXED_SCENARIOS:
            r = simulate(label, B1, B24, B25, B13, B14, B10, B26, B15)
            print_result(r)
        print()
