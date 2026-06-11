"""
最优策略搜素 — 哪些参数组合能最快到 5M？
"""
import math, sys
sys.path.insert(0, '.')
from bakery_v4_reference import one_month, State, PYTHON_FIXED_SCENARIOS

# 快速单月推演（不打印）
def quick_sim(B1, B24, B25, B13, B14, B10, B26, months=120):
    """跑最多120个月，返回 (月数, 总利润, 稳态月利润, 品牌, 疲劳, 满意度, 品质)"""
    s = State()
    profits = []
    for _ in range(months):
        p = one_month(s, B1, B24, B25, B13, B14, B10, B26)
        profits.append(p)
        if sum(profits) >= 5_000_000:
            break
    
    total = sum(profits)
    n_months = len(profits)
    steady = sum(profits[-12:]) // 12 if len(profits) >= 12 else (total // max(n_months, 1))
    
    return n_months, total, steady, s.BRAND, s.FAT, s.B21, s.B20


# ============================================================
# 1. 高奢路线 — 不同工资测试
# ============================================================
print("=" * 70)
print("  高奢路线 80㎡ ¥30 — 不同工资水平")
print("=" * 70)
for wage in [1200, 2000, 3000, 4000, 5000, 6000, 8000]:
    m, total, steady, brand, fat, sat, qua = quick_sim(30, 3, 500, 5000, 80, 3, wage)
    yrs = m / 12
    if total > 0:
        remain = (5_000_000 - total) / max(steady, 1) / 12
        print(f"  ¥{wage:>5}/人 → {yrs:.1f}年 ¥{total:+,}  稳态¥{steady:,}/月  品质{qua}  到5M还需{remain:.0f}年")
    else:
        print(f"  ¥{wage:>5}/人 → {yrs:.1f}年 ¥{total:+,}  亏损，到不了")

# ============================================================
# 2. 大厂路线 — 不同售价+面积
# ============================================================
print(f"\n{'=' * 70}")
print("  大厂路线 8人/¥100培训/¥8K营销 — 面积×售价")
print("=" * 70)
best = (0, 0, 0, 0)
for area in [200, 250, 300]:
    for price in [14, 16, 18, 20]:
        m, total, steady, brand, fat, sat, qua = quick_sim(price, 8, 100, 8000, area, 3, 1200)
        yrs = m / 12
        label = f"  {area}㎡ ¥{price:>2}"
        if total > 0:
            remain = (5_000_000 - total) / max(steady, 1) / 12
            yrs_total = yrs + remain
            print(f"  {label} → {yrs:.0f}年¥{total:+,}  稳态¥{steady:,}/月  到5M需{yrs_total:.0f}年")
            if yrs_total < best[0] or best[0] == 0:
                best = (yrs_total, area, price, steady)
        else:
            print(f"  {label} → {yrs:.0f}年¥{total:+,}  亏损")

if best[0] > 0:
    print(f"\n  🏆 大厂最快: {best[1]}㎡ ¥{best[2]} → {best[0]:.0f}年到5M")

# ============================================================
# 3. 大厂+加薪路线
# ============================================================
print(f"\n{'=' * 70}")
print("  大厂 300㎡ 加薪 — 不同工资水平")
print("=" * 70)
for wage in [1200, 2000, 3000, 4000]:
    for price in [18, 20, 22, 25]:
        m, total, steady, brand, fat, sat, qua = quick_sim(price, 8, 100, 8000, 300, 3, wage)
        if total > 0:
            remain = (5_000_000 - total) / max(steady, 1) / 12
            yrs_total = m/12 + remain
            print(f"  ¥{wage:>4}/人 ¥{price:>2} → {m//12}年{m%12}月¥{total:+,} 稳态¥{steady:,}/月  品牌{brand}  品质{qua}  总{yrs_total:.0f}年")
        else:
            print(f"  ¥{wage:>4}/人 ¥{price:>2} → {m//12}年{m%12}月¥{total:+,}  亏损")

# ============================================================
# 4. 策略切换：先小厂养品牌 → 提价收割
# ============================================================
print(f"\n{'=' * 70}")
print("  策略切换 — 大厂养品牌3年 → 提价到¥25")
print("=" * 70)

from bakery_v4_reference import one_month, State

for base_wage in [1200, 1500, 2000]:
    for area in [250, 300]:
        # 前3年 ¥18 养品牌
        s = State()
        y1_profits = []
        for _ in range(36):
            p = one_month(s, 18, 8, 100, 8000, area, 3, base_wage)
            y1_profits.append(p)
        
        brand_after_3y = s.BRAND
        fat_after_3y = s.FAT
        
        # 第4年起 ¥25 收割
        total_before = sum(y1_profits)
        profits = list(y1_profits)
        for _ in range(12*10):  # 再跑10年
            p = one_month(s, 25, 8, 100, 8000, area, 3, base_wage)
            profits.append(p)
            if sum(profits) >= 5_000_000:
                break
        
        total = sum(profits)
        months = len(profits)
        steady = sum(profits[-12:]) // 12 if len(profits) >= 12 else 0
        
        if total >= 5_000_000:
            print(f"  ¥{base_wage:>4}/人 {area}㎡: 前3年养品牌{total_before:+,} → 第4年提价¥25 ")
            print(f"    {months//12}年{months%12}月到5M, 最终品牌={s.BRAND}, 品质={s.B20}, 稳态¥{steady:,}/月")
        else:
            yrs = months/12
            print(f"  ¥{base_wage:>4}/人 {area}㎡: {yrs:.0f}年仅¥{total:+,}, 不到5M")
