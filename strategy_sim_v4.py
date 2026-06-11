# -*- coding: utf-8 -*-
"""
面包店三策略 v4 — 高奢杠杆解锁
核心洞察: 高奢 ≠ 高价。高奢 = 礼盒 + 社交传播 + 稀缺溢价 + 低价格弹性
社区靠口碑复购，大厂靠批发走量，高奢靠品牌杠杆——三条路完全不同
"""
import math, random
random.seed(42)

SEASON = [0.85, 1.10, 0.95, 1.00, 1.00, 0.90, 0.85, 0.85, 1.25, 1.10, 1.00, 1.30]
# 节日礼盒月: 2月(春节) 9月(中秋) 12月(圣诞) — 高奢专属爆发点
GIFT_MONTHS = {2: 2.5, 9: 3.0, 12: 3.5}  # 礼盒收入倍数（仅高奢B15>=7触发）

def sk(fat):
    if fat < 80: return 1.0
    if fat >= 100: return 0.1
    t = (fat - 80) / 20
    return 1.0 - t * t * (3 - 2 * t) * 0.9

def pbF_normal(b1):
    """大众市场价格弹性：价格敏感"""
    if b1 < 20: return 1 + (20 - b1) * 0.12
    return max(0.30, 1 - (b1 - 20) * 0.045)

def pbF_luxury(b1, brand):
    """高奢价格弹性：品牌够强时价格不敏感
    参考: LV/Hermes 涨价反而刺激需求，面包也有类似现象(B&C限购排队)
    """
    base = max(0.40, 1 - (b1 - 25) * 0.025)  # 衰减更慢
    # 品牌溢价：BRAND>200 时价格弹性再减半
    if brand > 200:
        brand_floor = min(0.85, 0.40 + brand * 0.0015)
        return max(brand_floor, base)
    return base

def simulate(params, noise=0.0, verbose=False):
    B1, B24, B25, B13, B14, B15, B10, B26 = params
    FAT, EMP, BRAND = 40, 0, 0
    B21, B4 = 0.8, 2.0
    is_luxury = B15 >= 7
    is_factory = B14 >= 150
    is_community = B15 <= 4 and B14 <= 100

    monthly, detail = [], []

    for m in range(12):
        sz = SEASON[m] * (1 + random.uniform(-noise, noise))
        mn = m + 1  # 1-based month

        # ======== 人工 ========
        B9 = round(B24 * B26 * (1 + B15 * 0.12 * max(0, 1 - B24 * 0.06)))
        if B24 > 8:
            B9 += round(B24 * B26 * 0.10)

        # ======== 房租 ========
        ur = max(6, 50 - B14 * 0.12)
        if is_community: ur *= 0.85
        if is_luxury: ur *= 1.30  # 核心商圈溢价更高
        B5 = max(0, round(B14 * B15 * ur))

        # ======== 产能 ========
        wf = 0.2 + 1.6 * min(B26, 10000) / 10000
        labor_eff = 1800 if is_factory else 1500
        bpc = max(1, min(B14 * 35, B24 * labor_eff) * wf)
        B3 = max(0, round(bpc * sk(FAT)))

        # ======== 加工成本 ========
        wF = max(0.3, 1.5 - B26 / 5000)
        if is_luxury and EMP > 80:
            # 大师傅手艺：经验极高时加工成本大幅下降（手艺溢价）
            emp_bonus = 1 - EMP * 0.004
        else:
            emp_bonus = 1 - EMP * 0.002
        B4 = round(max(0.1, max(0.1, 2 - B3 * 0.0002) * emp_bonus * wF), 2)

        # ======== 需求 ========
        # 选择价格弹性曲线
        pb = pbF_luxury(B1, BRAND) if is_luxury else pbF_normal(B1)

        # 基础客流
        base_tr = (450 + 400 * B15) * pb
        brand_tr = round(BRAND * (6 if is_luxury else 4)) * pb  # 高奢品牌效应更强

        # 营销
        mkt_tr = round(math.sqrt(max(0, B13)) * 10 * (1 + min(B14, 200) / 120))

        # 社区口碑
        community = round(BRAND * 1.5) if is_community else 0

        # ════════════════════════════════════
        # 高奢社交传播杠杆 (v4 新增)
        # 对标: 小红书/抖音打卡, B&C排队效应
        # ════════════════════════════════════
        social_viral = 0
        if is_luxury and BRAND > 100:
            # 品牌过100→社交传播开始发力
            # 品牌越高传播越快（指数增长）
            viral_base = round((BRAND - 100) * 2.5 * pb)
            # 传播有随机性但可复现
            social_viral = viral_base

        # ════════════════════════════════════
        # 稀缺效应 (v4 新增)
        # 对标: 限购/售罄反而刺激需求(B&C可颂限购)
        # ════════════════════════════════════
        # 上个月的供需比影响本月客流
        mkt_tr += social_viral
        retail_tr = round(base_tr + brand_tr + mkt_tr + community)

        # 转化率
        qp = max(0, (B26 - 4000) / 500)
        ma = max(1, 15 + B15 * 2 + BRAND * (0.6 if is_luxury else 0.4) + B21 * 3 + qp)
        # 高奢顾客价格容忍度更高
        if is_luxury: ma += 3
        cv = B1 <= ma and round(0.5 + (ma - B1) / ma * 0.4, 3) or round(max(0.05, 0.5 * ma / B1), 3)
        B2_retail = max(0, round(retail_tr * cv * sz))

        # ════════════════════════════════════
        # 礼盒经济 (v4 新增 — 高奢专属)
        # 对标: B&C中秋月饼礼盒¥388-888, 圣诞礼盒
        # 节日月零售额外爆发，不影响常规产能
        # ════════════════════════════════════
        gift_rev = 0
        gift_cost = 0
        gift_profit = 0
        if is_luxury and mn in GIFT_MONTHS:
            gift_mult = GIFT_MONTHS[mn]
            # 礼盒销量 = 基础销量 × 倍数，但受品牌加成
            gift_units = round(B2_retail * gift_mult * (0.3 + BRAND * 0.003))
            gift_units = min(gift_units, 5000)  # 产能上限
            # 礼盒单价更高（包装溢价）
            gift_price = B1 * 1.8
            gift_rev = round(gift_units * gift_price)
            # 礼盒成本：高档包装 + 原料，但毛利极高
            gift_cost = round(gift_units * (B10 * 0.8 + 8))  # ¥8包装费
            gift_profit = gift_rev - gift_cost

        # ======== 批发（大厂专属）========
        wholesale_vol = 0
        wholesale_rev = 0
        if is_factory:
            base_ws = (B14 - 130) * 50
            ws_sz = 1 + (sz - 1) * 0.3
            wholesale_vol = round(base_ws * ws_sz)
            wholesale_rev = round(wholesale_vol * B1 * 0.65)

        # ======== 销售与收入 ========
        retail_sold = min(B2_retail, B3)
        remaining_cap = B3 - retail_sold
        wholesale_sold = min(wholesale_vol, remaining_cap) if is_factory else 0

        retail_rev = retail_sold * B1 + round(retail_sold * B1 * 0.20)
        total_rev = retail_rev + wholesale_sold * B1 * 0.65 + gift_rev

        # ======== 成本 ========
        B12 = round(B10 * (1 - min(0.45, B3 * 0.00007)), 2)
        if is_factory and B3 > 2500:
            B12 = round(B12 * (1 - min(0.20, (B3 - 2500) * 0.00008)), 2)
        pkg = round(B1 * 0.10)
        cogs_retail = round((B12 + pkg + B4) * retail_sold)
        cogs_ws = round(wholesale_sold * B10 * 0.55 + wholesale_sold * 0.5) if is_factory else 0
        # 高奢额外原料成本（进口黄油等）
        if is_luxury:
            cogs_retail = round(cogs_retail * 1.15)  # 15%溢价原料
        cogs = cogs_retail + cogs_ws + (gift_cost if is_luxury else 0)
        uc = round(B14 * 25 + B24 * 180)
        eq = round(B14 * 15 + B24 * 80)
        ms = round(0.04 * B24 * 1500)
        B8 = round(total_rev - cogs - B5 - B9 - B13 - B25 * B24 - ms - uc - eq)
        monthly.append(B8)

        if verbose:
            detail.append({
                'm': mn, 'sz': round(sz, 2), 'B2r': B2_retail, 'B2w': wholesale_vol,
                'B3': B3, 'rev': total_rev, 'cogs': cogs, 'B5': B5, 'B9': B9,
                'B8': B8, 'gift': gift_rev, 'viral': social_viral, 'BRAND': BRAND,
                'pb': round(pb, 3), 'cv': cv, 'FAT': FAT,
            })

        # ======== 月度演进 ========
        sold_for_ur = retail_sold + wholesale_sold
        ur = sold_for_ur / max(bpc, 1)
        d = 3
        if B25 == 0 and ur > 0.7: d += 5
        elif B25 == 0: d += 2
        if ur > 0.8: d += (ur - 0.8) * 40
        d -= B25 * 0.025
        # 高奢工作环境更好，疲劳累积更慢
        if is_luxury: d -= 2
        ff = FAT < 40 and FAT / 40 or 1
        if B21 < 0.5: d -= (B21 - 0.5) * 12 * ff
        if B9 / max(B24, 1) > 1500: d -= (B9 / B24 - 1500) * 0.004 * ff
        FAT = max(10, min(100, round(FAT + d)))

        pp = B9 / max(B3, 1)
        bl = 3 + B15 * 0.35
        ps = round(pp >= bl and (0.7 + min((pp - bl) / (bl * 2), 0.3)) or (pp / bl * 0.7), 3)
        ov = round(max(0, sold_for_ur / max(bpc, 1) - (0.8 + 0.2 * ps)) * 1.5, 3)
        B21 = round(min(1, max(0, ps - ov)), 3)

        # ════════════════════════════════════
        # 稀缺效应 — 售罄反哺品牌 (v4 新增)
        # 对标: 限量发售引发排队,反而提升品牌
        # ════════════════════════════════════
        sr = max(0, (B2_retail - retail_sold) / max(1, B2_retail))
        if is_luxury and sr > 0.05:
            # 适度缺货(5-30%)对高奢是好事——制造稀缺
            # 超过30%才是坏事——客人怒了
            if sr <= 0.30:
                scarcity_brand_boost = round(sr * 40)  # 缺货10%→品牌+4
                BRAND += scarcity_brand_boost
            else:
                # 严重缺货 >30%，惩罚
                BRAND = max(0, BRAND - round((sr - 0.30) * 30))

        gr = B21 * 25
        dc = BRAND * max(0.015, BRAND * 0.012)
        gm = max(0.1, 1 - BRAND / 1000)
        BRAND = max(0, round(BRAND + gr * gm - dc - (sr * 12 if not is_luxury else 0)))

        EMP = min(200, round(EMP + max(1, 10 - round(EMP * 0.05))))

    return sum(monthly), monthly, detail


# ============================================================
strategies = {
    '🏠 社区小店': {
        'params': (22, 3, 150, 1500, 60, 3, 3, 4000),
        'desc': '对标好利来社区店: 熟客复购, 稳定薄利',
    },
    '🏭 大厂走量': {
        'params': (14, 12, 80, 6000, 230, 3, 2, 3000),
        'desc': '对标桃李中央工厂: 批发+零售, 规模效应',
    },
    '✨ 高奢精品': {
        'params': (30, 3, 300, 6000, 80, 8, 5, 5500),
        'desc': '对标B&C精品店: 礼盒+社交传播+稀缺, 高杠杆',
    },
}

print("=" * 130)
print("  面包店三策略推演 v4 — 高奢杠杆解锁")
print("  高奢专属: 礼盒经济(春节×2.5 中秋×3.0 圣诞×3.5) + 社交传播 + 品牌价格护城河 + 稀缺效应")
print("=" * 130)

for name, cfg in strategies.items():
    random.seed(42)
    total, monthly, detail = simulate(cfg['params'], verbose=True)
    p = cfg['params']
    avg = total / 12

    print(f"\n{'─' * 130}")
    print(f"  {name} — {cfg['desc']}")
    print(f"  参数: B1=¥{p[0]} | {p[1]}人 | 培训¥{p[2]}/人 | 营销¥{p[3]} | {p[4]}m² | {p[5]}⭐ | 原料¥{p[6]} | 工资¥{p[7]}/人")
    print(f"  年利润: ¥{total:,} | 月均: ¥{avg:,.0f}/月 | 旺季: ¥{max(monthly):,} | 淡季: ¥{min(monthly):,}")

    # 完整12月
    print(f"  逐月: {[f'{v:,}' for v in monthly]}")

    if detail:
        print(f"  {'月':>3} {'季节':>5} {'需求':>6} {'产能':>6} {'营收':>9} {'成本':>9} {'利润':>9} {'礼盒':>8} {'品牌':>5} {'pbF':>5}")
        print(f"  {'─'*3} {'─'*5} {'─'*6} {'─'*6} {'─'*9} {'─'*9} {'─'*9} {'─'*8} {'─'*5} {'─'*5}")
        for d in detail[:6]:
            print(f"  {d['m']:>3} ×{d['sz']:.2f} {d['B2r']:>5,} {d['B3']:>5,} ¥{d['rev']:>8,} ¥{d['cogs']:>8,} ¥{d['B8']:>8,} ¥{d['gift']:>7,} {d['BRAND']:>5} {d['pb']:.3f}")


# ============================================================
# 空间搜索
# ============================================================
print("\n" + "=" * 130)
print("  策略空间搜索 — 最优参数 (搜索数万组)")
print("=" * 130)

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
        'B1': (26, 38, 2), 'B24': (2, 5, 1), 'B25': (200, 600, 200),
        'B13': (3000, 12000, 3000), 'B14': (70, 120, 25), 'B15': (7, 10, 1),
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
    print(f"  月利润: {[f'{v:,}' for v in best[2]]}")

# ============================================================
# 高奢专属：如果做对了所有事能赚多少？
# ============================================================
print("\n" + "=" * 130)
print("  ✨ 高奢极限推演 — '做对一切'的最优解")
print("=" * 130)

# 搜索高奢大范围
best_lux = (-1e9, None, None)
for B1 in range(28, 40, 2):
 for B24 in range(2, 5):
  for B25 in range(200, 800, 200):
   for B13 in range(4000, 16000, 2000):
    for B14 in range(70, 130, 10):
     for B15 in range(8, 11):
      for B10 in range(5, 8):
       for B26 in range(5000, 7500, 500):
        random.seed(42)
        t, m, d = simulate((B1,B24,B25,B13,B14,B15,B10,B26), verbose=True)
        if t > best_lux[0]: best_lux = (t, (B1,B24,B25,B13,B14,B15,B10,B26), m, d)

p = best_lux[1]
print(f"  极限年利润: ¥{best_lux[0]:,} (月均 ¥{best_lux[0]/12:,.0f})")
print(f"  参数: B1=¥{p[0]} B24={p[1]}人 B25=¥{p[2]} B13=¥{p[3]} B14={p[4]}m² B15={p[5]}⭐ B10=¥{p[6]} B26=¥{p[7]}/人")
print(f"  逐月: {[f'{v:,}' for v in best_lux[2]]}")

if best_lux[3]:
    print(f"\n  月度明细:")
    print(f"  {'月':>3} {'需求':>6} {'产能':>6} {'营收':>10} {'利润':>10} {'礼盒':>8} {'品牌':>5} {'pbF':>5} {'FAT':>4}")
    print(f"  {'─'*3} {'─'*6} {'─'*6} {'─'*10} {'─'*10} {'─'*8} {'─'*5} {'─'*5} {'─'*4}")
    for d in best_lux[3]:
        print(f"  {d['m']:>3} {d['B2r']:>5,} {d['B3']:>5,} ¥{d['rev']:>9,} ¥{d['B8']:>9,} ¥{d['gift']:>7,} {d['BRAND']:>5} {d['pb']:.3f} {d['FAT']:>4}")

# ============================================================
# 均衡性总结
# ============================================================
print("\n" + "=" * 130)
print("  三路线最终均衡性")
print("=" * 130)

for name, profit, params, _ in results:
    print(f"  {name:<16} ¥{profit:>10,}/年 | B1=¥{params[0]} {params[1]}人 {params[4]}m² {params[5]}⭐ | ¥{profit/12:,.0f}/月")

pvals = [r[1] for r in results]
print(f"\n  策略间差距: {max(pvals)/max(min(pvals),1):.1f}:1")

lux_ratio = best_lux[0] / max(min(pvals), 1)
print(f"  高奢极限/社区最优: {lux_ratio:.1f}:1")
print(f"  高奢极限年利润: ¥{best_lux[0]:,}")
print(f"\n  社区 = 稳, 大厂 = 量, 高奢 = 杠杆 — 三条路各有天花板, 高奢上限最高但需要品牌积累")
print(f"  ✅ 不做扼杀可能性的沙盘")
