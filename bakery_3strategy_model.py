"""
面包店三策略数学模型 v1
目标：社区店、大厂、高奢三种路线在合理参数下都能实现正利润
基于真实面包店经济学校准
"""
import math, json, itertools

# ============================================================
# 真实世界对标
# ============================================================
# 社区店（好利来社区店）：40-80m², 3-5人, 客单¥15-25, 月租¥8k-15k, 利润率 8-15%
# 大厂（桃李/中央工厂）：150-300m², 15-25人, 客单¥8-15, 月租¥15k-35k, 利润率 3-8%, 走批发+零售
# 高奢（B&C/黄油与面包）：60-120m², 2-5人, 客单¥30-60, 月租¥20k-50k, 利润率 15-30%

def simulate(params, months=12):
    """
    params: (B1:售价, B24:员工数, B25:培训/人, B13:营销, B14:面积, B15:地段, B10:原料, B26:工资/人)
    """
    B1, B24, B25, B13, B14, B15, B10, B26 = params

    FAT, EMP, BRAND = 40, 0, 0
    B21 = 0.8
    B4 = 2.0  # 初始加工成本

    monthly = []
    total_profit = 0.0

    def sk(fat):
        if fat < 80: return 1.0
        if fat >= 100: return 0.1
        t = (fat - 80) / 20
        return 1.0 - t * t * (3 - 2 * t) * 0.9

    for m in range(months):
        # ============ SetRules ============

        # S0: 人工成本
        B9 = round(B24 * B26 * (1 + B15 * 0.15 * max(0, 1 - B24 * 0.08)))

        # S1: 房租
        unit_rent = max(8, 45 - B14 * 0.10)
        B5 = max(0, round(B14 * B15 * unit_rent))

        # 物理产能上限
        wf = 0.2 + 1.6 * min(B26, 10000) / 10000
        base_phys_cap = max(1, min(B14 * 35, B24 * 1500) * wf)

        # B3 产能 (含疲劳)
        B3 = max(0, round(base_phys_cap * sk(FAT)))

        # B4 加工成本
        wF = max(0.3, 1.5 - B26 / 5000)
        B4 = round(max(0.1, max(0.1, 2 - B3 * 0.0002) * (1 - EMP * 0.002) * wF), 2)

        # 需求 B2
        price_boost = B1 < 20 and (1 + (20 - B1) * 0.15) or max(0.6, 1 - (B1 - 20) * 0.03)
        base_traffic = (500 + 500 * B15) * price_boost
        brand_traffic = round(BRAND * 3) * price_boost
        mkt_traffic = round(math.sqrt(max(0, B13)) * 12 * (1 + B14 / 100))
        total_traffic = round(base_traffic + brand_traffic + mkt_traffic)

        quality_bonus = max(0, (B26 - 4000) / 500)
        max_acceptable = max(1, 15 + B15 * 2 + BRAND * 0.5 + B21 * 3 + quality_bonus)
        if B1 <= max_acceptable:
            conversion = round(0.5 + (max_acceptable - B1) / max_acceptable * 0.4, 3)
        else:
            conversion = round(max(0.05, 0.5 * max_acceptable / B1), 3)

        B2 = max(0, round(total_traffic * conversion))

        # 实际销售
        B6 = min(B2, B3)
        B7 = B6 * B1
        B7_total = B7 + round(B7 * 0.20)

        # 成本
        B12 = round(B10 * (1 - min(0.5, B3 * 0.00008)), 2)
        pkg = round(B1 * 0.15)
        cogs = round((B12 + pkg + B4) * B3)

        util_cost = round(B14 * 25 + B24 * 200)
        eq = 2000
        misc = round(0.05 * B24 * 1500)
        training_total = B25 * B24

        B8 = round(B7_total - cogs - B5 - B9 - B13 - training_total - misc - util_cost - eq)
        total_profit += B8
        monthly.append(B8)

        # ============ 月度演进 ============

        ur = B3 / max(base_phys_cap, 1)
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
        ov = round(max(0, B3 / max(base_phys_cap, 1) - (0.8 + 0.2 * ps)) * 1.5, 3)
        B21 = round(min(1, max(0, ps - ov)), 3)

        shortage = max(0, (B2 - B3) / max(1, B2))
        growth = B21 * 30
        decay = BRAND * max(0.02, BRAND * 0.015)
        gm = max(0.1, 1 - BRAND / 800)
        BRAND = max(0, round(BRAND + growth * gm - decay - shortage * 10))

        EMP = min(200, round(EMP + max(1, 10 - round(EMP * 0.05))))

    return monthly, total_profit, {
        'final_FAT': FAT, 'final_EMP': EMP, 'final_BRAND': BRAND,
        'final_B21': B21, 'final_B2': B2, 'final_B3': B3,
        'final_B4': B4, 'final_B5': B5, 'final_B9': B9,
    }


strategies = {
    '🏠 社区小本经营': {
        'desc': '街角小店，靠口碑和熟客，薄利但稳定',
        'params': (22, 3, 200, 2000, 60, 3, 4, 4000),
        'range': {
            'B1': (16, 28), 'B24': (2, 5), 'B25': (0, 300),
            'B13': (0, 5000), 'B14': (40, 100), 'B15': (1, 5),
            'B10': (3, 5), 'B26': (3000, 5000),
        }
    },
    '🏭 大厂走量': {
        'desc': '中央厨房+批发+零售，规模效应压低单位成本',
        'params': (15, 15, 100, 8000, 250, 3, 3, 3500),
        'range': {
            'B1': (10, 20), 'B24': (10, 25), 'B25': (0, 200),
            'B13': (2000, 15000), 'B14': (150, 300), 'B15': (1, 5),
            'B10': (2, 5), 'B26': (2500, 5000),
        }
    },
    '✨ 高奢精品': {
        'desc': '黄金地段，手工精制，高客单高毛利',
        'params': (32, 3, 500, 6000, 100, 9, 6, 5000),
        'range': {
            'B1': (24, 40), 'B24': (2, 6), 'B25': (200, 1000),
            'B13': (2000, 15000), 'B14': (60, 150), 'B15': (7, 10),
            'B10': (4, 8), 'B26': (4000, 8000),
        }
    },
}

print("=" * 100)
print("  三策略基准参数 — 12 个月推演")
print("=" * 100)

for name, cfg in strategies.items():
    monthly, total, final = simulate(cfg['params'])
    p = cfg['params']
    print(f"\n{name} — {cfg['desc']}")
    print(f"  参数: B1=¥{p[0]}, B24={p[1]}人, B25=¥{p[2]}, B13=¥{p[3]}, B14={p[4]}m², B15={p[5]}⭐, B10=¥{p[6]}, B26=¥{p[7]}/人")
    print(f"  逐月利润: {[f'¥{v:,}' for v in monthly[:6]]} ... {[f'¥{v:,}' for v in monthly[-3:]]}")
    print(f"  年均月利: ¥{total/12:,.0f}  年利润: ¥{total:,}")
    print(f"  终态: FAT={final['final_FAT']}, BRAND={final['final_BRAND']}, EMP={final['final_EMP']}, B21={final['final_B21']}")
    print(f"  终态: B2={final['final_B2']}, B3={final['final_B3']}, B4=¥{final['final_B4']}, 租金=¥{final['final_B5']:,}, 人工=¥{final['final_B9']:,}")

print("\n" + "=" * 100)
print("  策略空间搜索")
print("=" * 100)

for name, cfg in strategies.items():
    r = cfg['range']
    best = {'profit': -float('inf'), 'params': None}
    tested = 0

    for B1 in range(r['B1'][0], r['B1'][1] + 1, 2):
        for B24 in range(r['B24'][0], r['B24'][1] + 1, max(1, (r['B24'][1] - r['B24'][0]) // 4)):
            for B25 in [0, 100, 200, 500]:
                for B13 in [0, 2000, 5000, 8000, 12000]:
                    for B14 in range(r['B14'][0], r['B14'][1] + 1, max(1, (r['B14'][1] - r['B14'][0]) // 5)):
                        for B15 in range(r['B15'][0], r['B15'][1] + 1, 1):
                            for B10 in range(r['B10'][0], r['B10'][1] + 1):
                                for B26 in range(r['B26'][0], r['B26'][1] + 1, 500):
                                    tested += 1
                                    params = (B1, B24, B25, B13, B14, B15, B10, B26)
                                    monthly, total, final = simulate(params)
                                    if total > best['profit']:
                                        best = {'profit': total, 'params': params, 'monthly': monthly}

    print(f"\n{name} (搜索 {tested:,} 组)")
    if best['params']:
        p = best['params']
        print(f"  最优: 年利润=¥{best['profit']:,}")
        print(f"  参数: B1=¥{p[0]}, B24={p[1]}人, B25=¥{p[2]}, B13=¥{p[3]}, B14={p[4]}m², B15={p[5]}⭐, B10=¥{p[6]}, B26=¥{p[7]}/人")
        print(f"  前3月: {[f'¥{v:,}' for v in best['monthly'][:3]]}")
        print(f"  后3月: {[f'¥{v:,}' for v in best['monthly'][-3:]]}")

print("\n" + "=" * 100)
print("  模型缺陷诊断")
print("=" * 100)

factory_baseline = (16, 8, 100, 8000, 250, 7, 3, 3500)
monthly, total, final = simulate(factory_baseline)
print(f"\n❌ 大厂基准 (B1=16, B24=8, B14=250, B15=7): 年利润=¥{total:,}")
print(f"  B4=¥{final['final_B4']}, B3={final['final_B3']} >> B2={final['final_B2']}")
print(f"  产能利用率: {final['final_B3']/max(final['final_B2'],1)*100:.0f}% (严重过剩)")
unit_cost = final['final_B9']/max(final['final_B3'],1) + 3*(1-min(0.5,final['final_B3']*0.00008)) + final['final_B4']
print(f"  单位成本: ¥{unit_cost:.1f} vs 售价¥16")

print("\n  根因总结:")
print("  1. 大店不直接带客流 — B14 只影响营销转化(a/100)，不贡献基本客流")
print("  2. 价格天花板太低 — B1≥20 后 pbF 砍到 0.6，薄利多销走不通")
print("  3. 品牌上限 800，大厂做品牌到顶就失效")
print("  4. 人力效率 1500×wf 过于慷慨，大团队过度产能")
