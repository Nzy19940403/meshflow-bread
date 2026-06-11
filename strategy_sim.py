"""
面包店三策略推演 — 修改前 vs 修改后对比
"""
import math

def sk(fat):
    """疲劳→产出 sigmoid"""
    if fat < 80: return 1.0
    if fat >= 100: return 0.1
    t = (fat - 80) / 20
    return 1.0 - t * t * (3 - 2 * t) * 0.9

def pbF_old(b1):
    """旧版价格弹性"""
    return b1 < 20 and (1 + (20 - b1) * 0.15) or max(0.6, 1 - (b1 - 20) * 0.03)

def pbF_new(b1):
    """新版价格弹性 — B1≥20 后衰减加速"""
    return b1 < 20 and (1 + (20 - b1) * 0.15) or max(0.3, 1 - (b1 - 20) * 0.05)

def simulate(params, version='old', months=12):
    """
    version: 'old' = 当前代码, 'new' = 修改后
    """
    B1, B24, B25, B13, B14, B15, B10, B26 = params
    FAT, EMP, BRAND = 40, 0, 0
    B21, B4 = 0.8, 2.0
    monthly, detail = [], []

    for m in range(months):
        # --- 人工成本 ---
        B9 = round(B24 * B26 * (1 + B15 * 0.15 * max(0, 1 - B24 * 0.08)))
        # [NEW] 管理层成本
        if version == 'new' and B24 > 8:
            B9 += round(B24 * B26 * 0.12)

        # --- 房租 ---
        ur_unit = max(8, 45 - B14 * 0.10)
        # [NEW] 社区店租金折扣
        if version == 'new' and B15 <= 4:
            ur_unit *= 0.85
        B5 = max(0, round(B14 * B15 * ur_unit))

        # --- 物理产能上限 ---
        wf = 0.2 + 1.6 * min(B26, 10000) / 10000
        bpc = max(1, min(B14 * 35, B24 * 1500) * wf)
        # [NEW] 大厂自动化（面积大时设备效率加成）
        if version == 'new' and B14 >= 150:
            bpc = max(1, min(B14 * 35, B24 * 1800) * wf)

        B3 = max(0, round(bpc * sk(FAT)))

        # --- 加工成本 ---
        wF = max(0.3, 1.5 - B26 / 5000)
        # [NEW] 手艺溢价：经验丰富时加工成本更低
        emp_bonus = (1 - EMP * 0.002)
        if version == 'new' and EMP > 50:
            emp_bonus = (1 - EMP * 0.0035)
        B4 = round(max(0.1, max(0.1, 2 - B3 * 0.0002) * emp_bonus * wF), 2)

        # --- 需求 ---
        pbF_fn = pbF_new if version == 'new' else pbF_old
        pb = pbF_fn(B1)

        # 基础客流
        base_traffic = (500 + 500 * B15) * pb
        brand_traffic = round(BRAND * 3) * pb

        # [NEW] 大厂批发渠道
        wholesale = 0
        if version == 'new' and B14 > 150:
            wholesale = round((B14 - 150) * 3 * pb)

        # [NEW] 社区口碑加成
        community = 0
        if version == 'new' and B15 <= 4 and B14 <= 100:
            community = round(BRAND * 2)

        mkt_traffic = round(math.sqrt(max(0, B13)) * 12 * (1 + B14 / 100))
        total_traffic = round(base_traffic + brand_traffic + mkt_traffic + wholesale + community)

        # 转化率
        quality_bonus = max(0, (B26 - 4000) / 500)
        ma = max(1, 15 + B15 * 2 + BRAND * 0.5 + B21 * 3 + quality_bonus)

        # [NEW] 高奢溢价转化（高端客户对品牌敏感度更高）
        if version == 'new' and B15 >= 7:
            ma += 2  # 高净值客户容忍价更高

        cv = B1 <= ma and round(0.5 + (ma - B1) / ma * 0.4, 3) or round(max(0.05, 0.5 * ma / B1), 3)
        B2 = max(0, round(total_traffic * cv))

        # [NEW] 高奢天花板：过度扩张稀释品牌
        if version == 'new' and B15 >= 8 and B14 > 120:
            B2 = round(B2 * 0.88)

        # --- 销售与收入 ---
        B6 = min(B2, B3)
        rev = B6 * B1 + round(B6 * B1 * 0.20)

        # --- 成本 ---
        B12 = round(B10 * (1 - min(0.5, B3 * 0.00008)), 2)
        # [NEW] 原料二级批量折扣
        if version == 'new' and B3 > 3000:
            B12 = round(B12 * (1 - min(0.25, (B3 - 3000) * 0.0001)), 2)

        pkg = round(B1 * 0.15)
        cogs = round((B12 + pkg + B4) * B3)
        uc = round(B14 * 25 + B24 * 200)
        eq = 2000
        ms = round(0.05 * B24 * 1500)
        B8 = round(rev - cogs - B5 - B9 - B13 - B25 * B24 - ms - uc - eq)
        monthly.append(B8)

        # --- 月度演进 ---
        ur = B3 / max(bpc, 1)
        d = 3
        if B25 == 0 and ur > 0.7: d += 5
        elif B25 == 0: d += 2
        if ur > 0.8: d += (ur - 0.8) * 40
        d -= B25 * 0.03
        ff = FAT < 40 and FAT / 40 or 1
        if B21 < 0.5: d -= (B21 - 0.5) * 15 * ff
        if B9 / max(B24, 1) > 1500: d -= (B9 / B24 - 1500) * 0.005 * ff
        FAT = max(10, min(100, round(FAT + d)))

        pp = B9 / max(B3, 1)
        bl = 3 + B15 * 0.4
        ps = pp >= bl and round(0.7 + min((pp - bl) / (bl * 2), 0.3), 3) or round(pp / bl * 0.7, 3)
        ov = round(max(0, B3 / max(bpc, 1) - (0.8 + 0.2 * ps)) * 1.5, 3)
        B21 = round(min(1, max(0, ps - ov)), 3)

        sr = max(0, (B2 - B3) / max(1, B2))
        gr = B21 * 30
        dc = BRAND * max(0.02, BRAND * 0.015)
        gm = max(0.1, 1 - BRAND / 800)
        BRAND = max(0, round(BRAND + gr * gm - dc - sr * 10))
        EMP = min(200, round(EMP + max(1, 10 - round(EMP * 0.05))))

        if m < 3 or m >= 9:
            detail.append({
                'm': m+1, 'B2': B2, 'B3': B3, 'B5': B5, 'B8': B8,
                'B9': B9, 'FAT': FAT, 'BRAND': BRAND, 'EMP': EMP,
                'rev': rev, 'cogs': cogs, 'traf': total_traffic, 'cv': cv
            })

    return sum(monthly), monthly, detail

# ============================================================
# 三条路线核心参数
# ============================================================

strategies = {
    '🏠 社区小店': (24, 2, 100, 2000, 65, 3, 3, 4200),
    '🏭 大厂走量': (16, 12, 100, 8000, 230, 3, 2, 3200),
    '✨ 高奢精品': (36, 2, 300, 9000, 90, 9, 5, 6000),
}

print("=" * 110)
print("  面包店三策略推演 — 修改前 vs 修改后 对比")
print("=" * 110)

for name, params in strategies.items():
    t_old, m_old, d_old = simulate(params, 'old', 12)
    t_new, m_new, d_new = simulate(params, 'new', 12)

    print(f"\n{'─' * 110}")
    print(f"  {name}")
    print(f"  参数: B1=¥{params[0]} | {params[1]}人 | 培训¥{params[2]} | 营销¥{params[3]} | {params[4]}m² | {params[5]}⭐ | 原料¥{params[6]} | 工资¥{params[7]}/人")
    print(f"{'─' * 110}")

    # 表格头
    print(f"  {'月':>3} │ {'修改前月利':>10} │ {'修改后月利':>10} │ {'差值':>10} │")
    print(f"  {'───':>3}─┼─{'──────────':>10}─┼─{'──────────':>10}─┼─{'──────────':>10}─┤")

    for i in range(12):
        diff = m_new[i] - m_old[i]
        sign = '+' if diff > 0 else ''
        print(f"  {i+1:>3} │ ¥{m_old[i]:>9,} │ ¥{m_new[i]:>9,} │ {sign}¥{diff:>9,} │")

    print(f"  {'───':>3}─┼─{'──────────':>10}─┼─{'──────────':>10}─┼─{'──────────':>10}─┤")
    diff_t = t_new - t_old
    sign_t = '+' if diff_t > 0 else ''
    print(f"  {'∑':>3} │ ¥{t_old:>9,} │ ¥{t_new:>9,} │ {sign_t}¥{diff_t:>9,} │")

    # 前3月关键指标对比
    print(f"\n  前3月关键指标对比:")
    print(f"  {'指标':<16} │ {'修改前 M1':>8} {'M2':>8} {'M3':>8} │ {'修改后 M1':>8} {'M2':>8} {'M3':>8} │")
    print(f"  {'─'*16}─┼─{'─'*27}─┼─{'─'*27}─┤")
    for key, label in [('B2','需求'),('B3','产能'),('B5','房租'),('B9','人工'),('FAT','疲劳'),('BRAND','品牌'),('traf','客流'),('cv','转化率')]:
        old_vals = [d_old[i][key] for i in range(3)]
        new_vals = [d_new[i][key] for i in range(3)]
        print(f"  {label:<16} │ {old_vals[0]:>8} {old_vals[1]:>8} {old_vals[2]:>8} │ {new_vals[0]:>8} {new_vals[1]:>8} {new_vals[2]:>8} │")

    # 稳态月利
    print(f"\n  修改前稳态月利: ¥{m_old[-3]:,} → 修改后: ¥{m_new[-3]:,}")
    print(f"  利润率: {m_old[-1]/d_old[-1]['rev']*100:.1f}% → {m_new[-1]/d_new[-1]['rev']*100:.1f}%" if d_new[-1]['rev'] > 0 else "")

# ============================================================
# 各策略空间搜索（修改后）
# ============================================================

print("\n" + "=" * 110)
print("  修改后 — 各策略空间搜索最优解")
print("=" * 110)

paths = [
    ('🏠 社区小店', [(22,28,2),(2,4,1),(0,200,100),(0,4000,2000),(50,80,15),(2,4,1),(3,5,1),(3500,4500,500)]),
    ('🏭 大厂走量', [(12,18,2),(10,18,4),(0,200,100),(4000,12000,4000),(180,280,50),(1,4,1),(2,4,1),(2500,4000,500)]),
    ('✨ 高奢精品', [(28,38,2),(2,4,1),(200,600,200),(3000,9000,3000),(70,110,20),(8,10,1),(5,7,1),(4500,6500,500)]),
]

for name, ranges in paths:
    best_o = (-1e9, None, None)
    best_n = (-1e9, None, None)
    tested = 0

    for B1 in range(*ranges[0]):
     for B24 in range(*ranges[1]):
      for B25 in range(*ranges[2]):
       for B13 in range(*ranges[3]):
        for B14 in range(*ranges[4]):
         for B15 in range(*ranges[5]):
          for B10 in range(*ranges[6]):
           for B26 in range(*ranges[7]):
            tested += 1
            p = (B1,B24,B25,B13,B14,B15,B10,B26)
            to, mo, _ = simulate(p, 'old')
            tn, mn, _ = simulate(p, 'new')
            if to > best_o[0]: best_o = (to, p, mo)
            if tn > best_n[0]: best_n = (tn, p, mn)

    print(f"\n{name} (搜索 {tested:,} 组)")
    print(f"  修改前最优: ¥{best_o[0]:,} | 参数: B1={best_o[1][0]} B24={best_o[1][1]} B25={best_o[1][2]} B13={best_o[1][3]} B14={best_o[1][4]} B15={best_o[1][5]} B10={best_o[1][6]} B26={best_o[1][7]}")
    print(f"    前3月: {best_o[2][:3]} 后3月: {best_o[2][-3:]}")
    print(f"  修改后最优: ¥{best_n[0]:,} | 参数: B1={best_n[1][0]} B24={best_n[1][1]} B25={best_n[1][2]} B13={best_n[1][3]} B14={best_n[1][4]} B15={best_n[1][5]} B10={best_n[1][6]} B26={best_n[1][7]}")
    print(f"    前3月: {best_n[2][:3]} 后3月: {best_n[2][-3:]}")

# ============================================================
# 策略间均衡性分析
# ============================================================
print("\n" + "=" * 110)
print("  策略间均衡性分析")
print("=" * 110)

results = []
for name, ranges in paths:
    best = (-1e9, None, None)
    tested = 0
    for B1 in range(*ranges[0]):
     for B24 in range(*ranges[1]):
      for B25 in range(*ranges[2]):
       for B13 in range(*ranges[3]):
        for B14 in range(*ranges[4]):
         for B15 in range(*ranges[5]):
          for B10 in range(*ranges[6]):
           for B26 in range(*ranges[7]):
            tested += 1
            p = (B1,B24,B25,B13,B14,B15,B10,B26)
            tn, mn, _ = simulate(p, 'new')
            if tn > best[0]: best = (tn, p, mn)
    results.append((name, best[0], best[1], best[2]))

print(f"\n  {'路线':<16} {'最优年利润':>12} {'月均利润':>10} {'策略特征':}")
for name, profit, params, monthly in results:
    avg = profit / 12
    feature = f"B1=¥{params[0]} {params[1]}人 {params[4]}m² {params[5]}⭐"
    print(f"  {name:<16} ¥{profit:>11,} ¥{avg:>9,.0f} {feature}")

# 计算相对差距
profits = [r[1] for r in results]
max_p = max(profits)
min_p = min(profits)
ratio = max_p / max(min_p, 1)
print(f"\n  最高利润 / 最低利润 = {ratio:.1f}:1")
print(f"  目标: ≤ 3:1 (健康策略多样性)")
if ratio <= 3:
    print(f"  ✅ 通过 — 三条路线差距在可接受范围")
else:
    print(f"  ⚠️ 仍需调整 — 差距 > 3:1，需进一步削弱高奢或增强弱势路线")
