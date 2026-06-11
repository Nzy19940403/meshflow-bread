# -*- coding: utf-8 -*-
"""
MeshFlow 引擎公式 vs Python 精确对照
逐月对比验证：引擎 SetRule/Entangle 计算结果是否与数学预期一致

用户操作：在 MeshFlow 沙盘输入对应参数 → 点12次下个月 → 逐月利润 vs 本脚本输出
偏差目标：每月 ≤ ¥500（浮点舍入误差）
"""
import math

S = [0.85, 1.10, 0.95, 1.00, 1.00, 0.90, 0.85, 0.85, 1.25, 1.10, 1.00, 1.30]

def sk(fat):
    if fat < 80: return 1.0
    if fat >= 100: return 0.1
    t = (fat - 80) / 20
    return 1.0 - t * t * (3 - 2 * t) * 0.9

def pbF(b1):
    return (1 + (20 - b1) * 0.15) if b1 < 20 else max(0.6, 1 - (b1 - 20) * 0.03)

def sim(params, months=12):
    """精确复现 BakerySandbox.vue 第328-556行公式"""
    B1, B24, B25, B13, B14, B15, B10, B26 = params
    FAT, EMP, BRAND = 40, 0, 0
    B21 = 0.8
    results = []

    for m in range(months):
        sz = S[m % 12]

        # === SetRule: B9 人工 ===
        B9 = round(B24 * B26 * (1 + B15 * 0.15 * max(0, 1 - B24 * 0.08)))

        # === SetRule: B5 房租 ===
        B5 = max(0, round(B14 * B15 * max(8, 45 - B14 * 0.10)))

        # === physCapFn ===
        wf_val = 0.2 + 1.6 * min(B26, 10000) / 10000
        phys_cap = max(1, min(B14 * 35, B24 * 1500) * wf_val + max(0, round((2 - 2.0) * 100)))

        # === B3 产能 (M1→B3 SetRule) ===
        B3 = max(0, round(phys_cap * sk(FAT)))

        # === B4 加工成本 (B3→B4 entangle) ===
        wF = max(0.5, 1.5 - B26 / 5000)
        B4 = max(0.1, max(0.1, 2 - B3 * 0.0002) * (1 - EMP * 0.002) * wF)
        B4 = round(B4 * 100) / 100

        # === B28 原料品质 ===
        b28_base = max(0.2, min(1.0, B10 / 5.0))
        b28_bonus = min(0.25, (B3 - 3000) * 0.00008) if B3 > 3000 else 0
        B28 = round(min(1.0, b28_base + b28_bonus) * 1000) / 1000

        # === B2 需求 ===
        bC = round(BRAND * 3)
        bP = 0 if BRAND > 300 else (1 - (BRAND - 100) / 200) if BRAND > 100 else 1
        base_d = round((500 + 500 * B15) * pbF(B1)) + round(bC * bP)
        mktTr = round(math.sqrt(max(0, B13)) * 10) * (1 + B14 / 100)
        tr = round(base_d + mktTr)
        qpV = max(0, (B26 - 4000) / 500)
        ma = max(1, 15 + B15 * 2 + BRAND * 0.5 + B21 * 3 + qpV)
        if B1 <= ma:
            conv = min(0.9, 0.5 + (ma - B1) / ma * 0.4)
        else:
            conv = max(0.05, 0.5 * ma / B1)
        B2 = max(0, round(tr * conv * sz))

        # === B6 实际销量 ===
        B6 = min(B2, B3)

        # === B7 营收 ===
        B7 = B6 * B1 + round(B6 * B1 * 0.20)

        # === B12 原料实际成本 ===
        B12 = round(B10 * (1 - min(0.5, B3 * 0.00008)) * 100) / 100

        # === B8 月利润 ===
        pkg = round(B1 * 0.15)
        utilCost = round(B14 * 25 + B24 * 200)
        eq_cost = 2000
        trn = B25 * B24
        misc = round(0.05 * B24 * 1500)
        cogs = round((B12 + pkg + B4) * B3)
        B8 = round(B7 - cogs - B5 - B9 - B13 - trn - misc - utilCost - eq_cost)

        # === B21 满意度 ===
        pp = B9 / max(B3, 1)
        bl = 3 + B15 * 0.4
        if pp >= bl:
            ps = 0.7 + min((pp - bl) / (bl * 2), 0.3)
        else:
            ps = pp / bl * 0.7
        util = B3 / max(phys_cap, 1)
        ov = max(0, util - (0.8 + 0.2 * ps)) * 1.5
        B21 = round(min(1, max(0, ps - ov)) * 1000) / 1000

        # === 月度演进 ===
        # FAT
        ph = max(1, min(B14 * 35, B24 * 1500) * wf_val + max(0, (2 - B4) * 100))
        ur_val = B3 / max(ph, 1)
        d = 3
        if B25 == 0 and ur_val > 0.7: d += 5
        elif B25 == 0: d += 2
        if ur_val > 0.8: d += (ur_val - 0.8) * 40
        d -= B25 * 0.03
        ff = FAT / 40 if FAT < 40 else 1
        if B21 < 0.5: d -= (B21 - 0.5) * 15 * ff
        if B9 / max(B24, 1) > 1500: d -= (B9 / B24 - 1500) * 0.005 * ff
        FAT = max(10, min(100, round(FAT + d)))

        # BRAND
        sr = max(0, (B2 - B3) / max(1, B2))
        growth = B21 * 20
        decay = BRAND * 0.02
        gm = max(0.05, 1 - BRAND / 400)
        BRAND = max(0, round(BRAND + growth * gm - decay - sr * 10))

        # EMP
        EMP = min(200, round(EMP + max(1, 10 - round(EMP * 0.05))))

        results.append({
            'm': m+1, 'B2': B2, 'B3': B3, 'B4': B4, 'B5': B5, 'B6': B6,
            'B7': B7, 'B8': B8, 'B9': B9, 'B12': B12, 'B21': B21, 'B28': B28,
            'FAT': FAT, 'BRAND': BRAND, 'EMP': EMP,
        })

    return results, sum(r['B8'] for r in results)


SCENARIOS = {
    'AO默认·中立开局': (18, 3, 100, 1000, 60, 3, 3, 4000),
    'B大厂·走量': (16, 12, 100, 8000, 230, 3, 2, 3200),
    'C高奢·精品': (28, 3, 300, 6000, 90, 8, 5, 5500),
    'D旧参数·大店': (16, 8, 100, 2000, 150, 7, 3, 5000),
    'E社区·高价好料': (24, 2, 0, 2000, 60, 4, 4, 4500),
    'F高奢·极限': (36, 2, 200, 9000, 95, 9, 5, 6000),
}

print("=" * 130)
print("  MeshFlow 引擎 vs Python — 逐月利润对照表")
print("  操作方法: 在沙盘中输入对应参数 → 点12次[推进下月] → 比对每月利润")
print("=" * 130)

for label, params in SCENARIOS.items():
    results, total = sim(params)

    print("\n" + "-" * 130)
    print("  %s" % label)
    print("  参数: B1=%d B24=%d人 B25=%d B13=%d B14=%dm B15=%d* B10=%d B26=%d" % params)
    print("  Python预期年利润: %d (月均 %.0f)" % (total, total/12))
    print("  %4s %7s %7s %7s %6s %9s %8s %9s %7s %5s" %
          ("月", "需求B2", "产能B3", "实售B6", "工本B4", "营收B7", "房租B5", "利润B8", "品牌", "疲劳"))
    print("  " + "-" * 85)

    for d in results:
        print("  %4d %7d %7d %7d %6.2f %9d %8d %9d %7d %5d" %
              (d['m'], d['B2'], d['B3'], d['B6'], d['B4'], d['B7'], d['B5'], d['B8'], d['BRAND'], d['FAT']))

    print("  " + "-" * 85)
    print("  12月利润序列: %s" % [d['B8'] for d in results])
    print("  逐月对照表: 请在MeshFlow中验证以上每行数字是否匹配")
    print("  偏差标准: 每月|B8差值| <= 500 → 通过 ✅")

print("\n" + "=" * 130)
print("  对照完成。将沙盘输出与本表逐行对比，确认引擎与数学预期一致。")
print("=" * 130)
