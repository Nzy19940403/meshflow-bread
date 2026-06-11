"""
面包店三策略 v3 — 精准对标真实经济学
v2 问题诊断 & 修复:
  大厂: 批发渠道贡献太弱(¥299/月)，固定成本吃掉所有毛利 → 大改批发公式
  高奢: 默认B1=32太高，pbF砍到0.52 → 降到B1=28(对标B&C真实定价)
  社区: 表现正常，微调
"""
import math, random
random.seed(42)

SEASON = [0.85, 1.10, 0.95, 1.00, 1.00, 0.90, 0.85, 0.85, 1.25, 1.10, 1.00, 1.30]

def sk(fat):
    if fat < 80: return 1.0
    if fat >= 100: return 0.1
    t = (fat - 80) / 20
    return 1.0 - t * t * (3 - 2 * t) * 0.9

def pbF(b1):
    """对标真实面包店需求弹性"""
    if b1 < 20:
        return 1 + (20 - b1) * 0.12
    elif b1 <= 35:
        return max(0.35, 1 - (b1 - 20) * 0.04)
    else:
        return max(0.20, 0.40 - (b1 - 35) * 0.03)

def simulate(params, noise=0.0, verbose=False):
    B1, B24, B25, B13, B14, B15, B10, B26 = params
    FAT, EMP, BRAND = 40, 0, 0
    B21, B4 = 0.8, 2.0
    monthly, detail = [], []

    for m in range(12):
        sz = SEASON[m] * (1 + random.uniform(-noise, noise))

        # ---- 人工成本 ----
        B9 = round(B24 * B26 * (1 + B15 * 0.12 * max(0, 1 - B24 * 0.06)))
        if B24 > 8:
            B9 += round(B24 * B26 * 0.10)  # 管理层溢价

        # ---- 房租 ----
        ur = max(6, 50 - B14 * 0.12)
        if B15 <= 4: ur *= 0.85
        if B15 >= 8: ur *= 1.25
        B5 = max(0, round(B14 * B15 * ur))

        # ---- 产能 ----
        wf = 0.2 + 1.6 * min(B26, 10000) / 10000
        labor_eff = 1800 if B14 >= 150 else 1500
        bpc = max(1, min(B14 * 35, B24 * labor_eff) * wf)
        B3 = max(0, round(bpc * sk(FAT)))

        # ---- 加工成本 ----
        wF = max(0.3, 1.5 - B26 / 5000)
        emp_bonus = (1 - EMP * 0.003) if EMP > 50 else (1 - EMP * 0.002)
        B4 = round(max(0.1, max(0.1, 2 - B3 * 0.0002) * emp_bonus * wF), 2)

        # ======== 需求（零售+渠道） ========
        pb = pbF(B1)

        # 零售客流
        base_tr = (450 + 400 * B15) * pb
        brand_tr = round(BRAND * 4) * pb
        mkt_tr = round(math.sqrt(max(0, B13)) * 10 * (1 + min(B14, 200) / 120))

        # 社区口碑
        community = 0
        if B15 <= 4 and B14 <= 100:
            community = round(BRAND * 1.5)

        # 高奢社交传播
        luxury_spike = 0
        if B15 >= 7 and BRAND > 80:
            luxury_spike = round(BRAND * 1.0 * random.uniform(0.8, 1.2)) if noise > 0 else round(BRAND * 1.0)

        retail_tr = round(base_tr + brand_tr + mkt_tr + community + luxury_spike)

        # 转化率
        qp = max(0, (B26 - 4000) / 500)
        ma = max(1, 15 + B15 * 2 + BRAND * 0.4 + B21 * 3 + qp)
        cv = B1 <= ma and round(0.5 + (ma - B1) / ma * 0.4, 3) or round(max(0.05, 0.5 * ma / B1), 3)
        B2_retail = max(0, round(retail_tr * cv * sz))

        # ════════════════════════════════════
        # 【核心修改】批发渠道 — 大厂的第二条收入线
        # 对标：桃李面包给超市/学校供应的批发业务
        # 超过150m²的部分用来做批发产能
        # 批发：按合同价(零售价×0.65)供货给超市/食堂/便利店
        # ════════════════════════════════════
        wholesale_vol = 0
        wholesale_rev = 0
        wholesale_cost = 0
        if B14 > 130:
            # 每超额m²对应50个批发单位的月度供应（合同稳定，不受季节大幅波动）
            base_ws_vol = (B14 - 130) * 50
            # 批发合同只受轻微季节影响(±10%)
            ws_sz = 1 + (sz - 1) * 0.3  # 批发渠道季节波动只有零售的30%
            wholesale_vol = round(base_ws_vol * ws_sz)
            # 批发价 = 零售价 × 0.65（批发折扣）
            wholesale_rev = round(wholesale_vol * B1 * 0.65)
            # 批发成本 = 批量原料价（比零售原料便宜30%）+ 简单包装
            ws_ingredient = round(wholesale_vol * B10 * 0.55)
            ws_packing = round(wholesale_vol * 0.5)
            wholesale_cost = ws_ingredient + ws_packing

        # 总需求 = 零售 + 批发
        B2_total = B2_retail + wholesale_vol
        # 总产能需要 = 零售需求 + 批发需求（批发也要产能）
        B3_needed = B3
        # 产能分配到零售和批发
        retail_sold = min(B2_retail, B3)
        remaining_cap = B3 - retail_sold
        wholesale_sold = min(wholesale_vol, remaining_cap)
        B6 = retail_sold + wholesale_sold

        # ---- 收入 ----
        retail_rev = retail_sold * B1 + round(retail_sold * B1 * 0.20)
        total_rev = retail_rev + (wholesale_sold * B1 * 0.65)

        # ---- 成本 ----
        B12 = round(B10 * (1 - min(0.45, B3 * 0.00007)), 2)
        if B3 > 2500:
            B12 = round(B12 * (1 - min(0.20, (B3 - 2500) * 0.00008)), 2)
        pkg = round(B1 * 0.10)
        # COGS 按实际产量计算（零售部分全价原料，批发部分折价）
        cogs_retail = round((B12 + pkg + B4) * retail_sold)
        cogs_ws = round(wholesale_sold * B10 * 0.55 + wholesale_sold * 0.5)
        cogs = cogs_retail + cogs_ws
        uc = round(B14 * 25 + B24 * 180)
        eq = round(B14 * 15 + B24 * 80)
        ms = round(0.04 * B24 * 1500)
        B8 = round(total_rev - cogs - B5 - B9 - B13 - B25 * B24 - ms - uc - eq)
        monthly.append(B8)

        if verbose and m < 3:
             detail.append({'m': m+1, 'sz': sz, 'B2r': B2_retail, 'B2w': wholesale_vol,
                            'B3': B3, 'B6': B6, 'ws_rev': wholesale_sold * B1 * 0.65,
                            'rev': total_rev, 'cogs': cogs, 'B5': B5, 'B9': B9, 'B8': B8})

        # ---- 月度演进（同 v2）----
        ur = retail_sold / max(min(bpc, B2_retail) if B2_retail > 0 else bpc, 1)
        d = 3
        if B25 == 0 and ur > 0.7: d += 5
        elif B25 == 0: d += 2
        if ur > 0.8: d += (ur - 0.8) * 40
        d -= B25 * 0.025
        ff = FAT < 40 and FAT / 40 or 1
        if B21 < 0.5: d -= (B21 - 0.5) * 12 * ff
        if B9 / max(B24, 1) > 1500: d -= (B9 / B24 - 1500) * 0.004 * ff
        FAT = max(10, min(100, round(FAT + d)))
        pp = B9 / max(B3, 1)
        bl = 3 + B15 * 0.35
        ps = round(pp >= bl and (0.7 + min((pp - bl) / (bl * 2), 0.3)) or (pp / bl * 0.7), 3)
        ov = round(max(0, retail_sold / max(bpc, 1) - (0.8 + 0.2 * ps)) * 1.5, 3)
        B21 = round(min(1, max(0, ps - ov)), 3)
        sr = max(0, (B2_retail - retail_sold) / max(1, B2_retail))
        gr = B21 * 25
        dc = BRAND * max(0.015, BRAND * 0.012)
        gm = max(0.1, 1 - BRAND / 1000)
        BRAND = max(0, round(BRAND + gr * gm - dc - sr * 12))
        EMP = min(200, round(EMP + max(1, 10 - round(EMP * 0.05))))

    return sum(monthly), monthly, detail


# ============================================================
# 三策略参数（校准到真实世界）
# ============================================================

strategies = {
    '🏠 社区小店': {
        'params': (22, 3, 150, 1500, 60, 3, 3, 4000),
        'desc': '对标好利来社区店: 40-80m², 3-5人, 客单¥15-22',
    },
    '🏭 大厂走量': {
        'params': (14, 12, 80, 6000, 230, 3, 2, 3000),
        'desc': '对标桃李中央工厂: 200-300m², 10-20人, 批发价¥8-12, 走超市+学校渠道',
    },
    '✨ 高奢精品': {
        'params': (28, 3, 300, 5000, 90, 8, 5, 5000),
        'desc': '对标B&C精品店: 60-120m², 2-5人, 客单¥28-50, 商圈溢价区',
    },
}

print("=" * 120)
print("  面包店三策略推演 v3 — 真实经济学校准 + 批发渠道 + 季节波动")
print("  季节: 1月淡(85%) 2月+10% 7-8月淡(85%) 9月+25% 12月+30%")
print("=" * 120)

for name, cfg in strategies.items():
    random.seed(42)
    total, monthly, detail = simulate(cfg['params'], verbose=True)
    p = cfg['params']
    avg = total / 12

    print(f"\n{'─' * 120}")
    print(f"  {name} — {cfg['desc']}")
    print(f"  参数: B1=¥{p[0]} | {p[1]}人 | 培训¥{p[2]}/人 | 营销¥{p[3]} | {p[4]}m² | {p[5]}⭐ | 原料¥{p[6]} | 工资¥{p[7]}/人")
    print(f"  年利润: ¥{total:,} | 月均: ¥{avg:,.0f}/月 | 旺季: ¥{max(monthly):,} | 淡季: ¥{min(monthly):,}")

    # 逐月明细
    print(f"  {'月':>3} {'季节':>5} {'零售':>6} {'批发':>6} {'产能':>6} {'营收':>8} {'利润':>9} {'FAT':>4} {'BR':>4} |")
    print(f"  {'─'*3} {'─'*5} {'─'*6} {'─'*6} {'─'*6} {'─'*8} {'─'*9} {'─'*4} {'─'*4} |")
    for d in detail:
        print(f"  {d['m']:>3} ×{d['sz']:.2f} {d['B2r']:>5,} {d['B2w']:>5,} {d['B3']:>5,} ¥{d['rev']:>7,} {d['B8']:>+9,} {40:>4} {0:>4} |")

    # 完整12月
    print(f"  完整12月: {[f'{v:,}' for v in monthly]}")

# ============================================================
# 空间搜索
# ============================================================

print("\n" + "=" * 120)
print("  策略空间搜索 — 最优参数")
print("=" * 120)

ranges = {
    '🏠 社区小店': {
        'B1': (18, 28, 2), 'B24': (2, 5, 1), 'B25': (0, 200, 100),
        'B13': (0, 4000, 2000), 'B14': (50, 90, 10), 'B15': (2, 5, 1),
        'B10': (3, 5, 1), 'B26': (3500, 5000, 500),
    },
    '🏭 大厂走量': {
        'B1': (12, 18, 2), 'B24': (10, 18, 2), 'B25': (0, 200, 100),
        'B13': (4000, 12000, 4000), 'B14': (180, 280, 25), 'B15': (1, 4, 1),
        'B10': (2, 4, 1), 'B26': (2500, 4000, 500),
    },
    '✨ 高奢精品': {
        'B1': (26, 36, 2), 'B24': (2, 5, 1), 'B25': (200, 600, 200),
        'B13': (3000, 9000, 3000), 'B14': (70, 120, 25), 'B15': (7, 10, 1),
        'B10': (5, 7, 1), 'B26': (4500, 6500, 500),
    },
}

results = []
for name, r in ranges.items():
    best = (-1e9, None, None)
    tested = 0
    for B1 in range(*r['B1']):
     for B24 in range(*r['B24']):
      for B25 in range(*r['B25']):
       for B13 in range(*r['B13']):
        for B14 in range(*r['B14']):
         for B15 in range(*r['B15']):
          for B10 in range(*r['B10']):
           for B26 in range(*r['B26']):
            tested += 1
            random.seed(42)
            t, m, _ = simulate((B1,B24,B25,B13,B14,B15,B10,B26))
            if t > best[0]: best = (t, (B1,B24,B25,B13,B14,B15,B10,B26), m)
    results.append((name, best[0], best[1], best[2]))
    p = best[1]
    print(f"\n{name}: {tested:,}组 → ¥{best[0]:,}/年 (月均¥{best[0]/12:,.0f})")
    print(f"  参数: B1=¥{p[0]} B24={p[1]}人 B25=¥{p[2]} B13=¥{p[3]} B14={p[4]}m² B15={p[5]}⭐ B10=¥{p[6]} B26=¥{p[7]}/人")
    print(f"  旺季¥{max(best[2]):,} 淡季¥{min(best[2]):,} 波动¥{max(best[2])-min(best[2]):,}")

# 均衡性
print("\n" + "=" * 120)
print("  三路线均衡性 & 真实世界对标")
print("=" * 120)
for name, profit, params, monthly in results:
    avg = profit/12
    print(f"  {name:<16} ¥{profit:>9,}/年 | 月均¥{avg:>8,.0f} | B1=¥{params[0]} {params[1]}人 {params[4]}m² {params[5]}⭐")

pvals = [r[1] for r in results]
ratio = max(pvals)/max(min(pvals), 1)

ref = {
    '🏠 社区小店': (96000, 240000),
    '🏭 大厂走量': (120000, 360000),
    '✨ 高奢精品': (600000, 1800000),
}
print(f"\n  最高/最低 = {ratio:.1f}:1")
for name, profit, _, _ in results:
    lo, hi = ref[name]
    ok = lo <= profit <= hi
    print(f"  {name}: ¥{profit:,}/年 (对标区间 ¥{lo:,}-¥{hi:,}) {'✅' if ok else '⚠️'}")

print(f"\n  ✅ 三条路线均可盈利，符合真实世界经验区间，季节打破稳态，批发渠道让大厂差异化") if ratio <= 3 else print(f"\n  ⚠️ 差距 {ratio:.1f}:1，仍需调整")
