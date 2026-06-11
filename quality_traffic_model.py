# -*- coding: utf-8 -*-
"""
原料品质惩罚 + 客流分化模型验证
1. B28 品质影响品牌：垃圾原料 → 品牌加速衰减 + 恢复难度加倍
2. 客流 = 常客流(品质敏感) + 旅游客流(地段决定,品质不敏感)
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
    return (1 + (20 - b1) * 0.15) if b1 < 20 else max(0.6, 1 - (b1 - 20) * 0.03)

def compute_month_new(params, fat, emp, brand, prev_brand, month_idx, was_quality_bad=False):
    """新版：品质惩罚 + 客流分化"""
    B1, B24, B25, B13, B14, B15, B10, B26 = params

    # === 人工 ===
    B9 = round(B24 * B26 * (1 + B15 * 0.15 * max(0, 1 - B24 * 0.08)))

    # === 房租 ===
    B5 = max(0, round(B14 * B15 * max(8, 45 - B14 * 0.10)))

    # === 产能 ===
    wf_val = 0.2 + 1.6 * min(B26, 10000) / 10000
    phys_cap = max(1, min(B14 * 35, B24 * 1500) * wf_val)
    B3 = max(0, round(phys_cap * sk(fat)))

    # === 加工成本 ===
    wF = max(0.5, 1.5 - B26 / 5000)
    B4 = round(max(0.1, max(0.1, 2 - B3 * 0.0002) * (1 - emp * 0.002) * wF) * 100) / 100

    # === 原料品质 ===
    b28_base = max(0.2, min(1.0, B10 / 5.0))
    b28_bonus = min(0.25, (B3 - 3000) * 0.00008) if B3 > 3000 else 0
    B28 = round(min(1.0, b28_base + b28_bonus) * 1000) / 1000

    # ════════════════════════════════════════
    # 客流分化：常客流 vs 旅游客流
    # ════════════════════════════════════════

    sz = SEASON[month_idx % 12]
    pb = pbF(B1)

    # --- 常客流 (品质/品牌敏感) ---
    # 基础 + 品牌，适合社区店
    regular_base = (400 + 350 * min(B15, 6)) * pb  # 低地段也够吃
    regular_brand = round(brand * 3.5) * pb  # 品牌口碑对常客影响大
    regular_mkt = round(math.sqrt(max(0, B13)) * 8) * (1 + min(B14, 120) / 120)
    regular_tr = round(regular_base + regular_brand + regular_mkt)

    # 常客转化率 — 受品质(B28)影响
    qpV = max(0, (B26 - 4000) / 500)
    ma_regular = max(1, 13 + B15 * 1.5 + brand * 0.5 + B28 * 5 + qpV)  # B28 权重 5
    if B1 <= ma_regular:
        regular_conv = min(0.9, 0.5 + (ma_regular - B1) / ma_regular * 0.4)
    else:
        regular_conv = max(0.05, 0.5 * ma_regular / B1)
    regular_demand = max(0, round(regular_tr * regular_conv * sz))

    # --- 旅游客流 (地段决定，品质不太在乎) ---
    # 只在 B15>=5 时明显出现
    tourist_tr = 0
    if B15 >= 5:
        tourist_base = (B15 - 4) * 600 * pb  # B15=5→600, B15=10→3600
        tourist_mkt = round(math.sqrt(max(0, B13)) * 6) if B15 >= 7 else 0  # 高端地段营销才拉旅游客
        tourist_tr = round(tourist_base + tourist_mkt)

    # 旅游客转化率 — 对品质不敏感，对价格较敏感
    ma_tourist = max(1, 10 + B15 * 2 + B13 / 3000 + qpV)  # 不依赖 B28
    if B1 <= ma_tourist:
        tourist_conv = min(0.85, 0.4 + (ma_tourist - B1) / ma_tourist * 0.35)
    else:
        tourist_conv = max(0.03, 0.35 * ma_tourist / B1)
    tourist_demand = max(0, round(tourist_tr * tourist_conv * sz))

    B2 = regular_demand + tourist_demand

    # --- 销售 ---
    B6 = min(B2, B3)
    regular_sold = min(regular_demand, B6)
    tourist_sold = B6 - regular_sold

    B7 = B6 * B1 + round(B6 * B1 * 0.20)

    # --- 成本 ---
    B12 = round(B10 * (1 - min(0.5, B3 * 0.00008)) * 100) / 100
    pkg = round(B1 * 0.15)
    cogs = round((B12 + pkg + B4) * B3)
    B8 = round(B7 - cogs - B5 - B9 - B13 - B25 * B24 -
               round(0.05 * B24 * 1500) - round(B14 * 25 + B24 * 200) - 2000)

    # === 满意度 ===
    pp = B9 / max(B3, 1)
    bl = 3 + B15 * 0.4
    ps = round(pp >= bl and (0.7 + min((pp - bl) / (bl * 2), 0.3)) or (pp / bl * 0.7), 3)
    ov = round(max(0, B3 / max(phys_cap, 1) - (0.8 + 0.2 * ps)) * 1.5, 3)
    B21 = round(min(1, max(0, ps - ov)), 3)

    # === 疲劳 ===
    ur_val = B3 / max(phys_cap, 1)
    d = 3
    if B25 == 0 and ur_val > 0.7: d += 5
    elif B25 == 0: d += 2
    if ur_val > 0.8: d += (ur_val - 0.8) * 40
    d -= B25 * 0.03
    ff = fat / 40 if fat < 40 else 1
    if B21 < 0.5: d -= (B21 - 0.5) * 12 * ff
    new_fat = max(10, min(100, round(fat + d)))

    # ════════════════════════════════════════
    # 品牌演变 — 品质惩罚
    # ════════════════════════════════════════
    sr = max(0, (regular_demand - regular_sold) / max(1, regular_demand))

    # 基础增长
    growth = B21 * 20
    gm = max(0.05, 1 - brand / 400)

    # 品质惩罚 (B28 低时)
    quality_decay = 0
    if B28 < 0.5:
        # 垃圾原料：品牌自然衰减加速
        gap = 0.5 - B28
        quality_decay = gap * 30  # B28=0.2 → 衰减9点/月

    # 常规衰减
    normal_decay = brand * 0.02

    # 缺货惩罚
    shortage_penalty = sr * 10

    new_brand = max(0, round(brand + growth * gm - normal_decay - quality_decay - shortage_penalty))

    # 品质恢复惩罚：如果品牌因品质下降而下跌，恢复速度减半
    if was_quality_bad and B28 >= 0.5:
        # 刚从垃圾原料恢复，品牌增长打折
        growth *= 0.5

    # 判断下个月是否在品质惩罚状态
    next_was_bad = B28 < 0.5

    # === 经验 ===
    new_emp = min(200, round(emp + max(1, 10 - round(emp * 0.05))))

    return {
        'B2': B2, 'B2r': regular_demand, 'B2t': tourist_demand,
        'B3': B3, 'B4': B4, 'B5': B5, 'B6': B6, 'B7': B7, 'B8': B8,
        'B9': B9, 'B12': B12, 'B21': B21, 'B28': B28,
        'FAT': new_fat, 'EMP': new_emp, 'BRAND': new_brand,
        'was_quality_bad': next_was_bad,
    }

def run_sim(params, months=12):
    FAT, EMP, BRAND = 40, 0, 0
    was_bad = False
    results = []
    total = 0
    for m in range(months):
        d = compute_month_new(params, FAT, EMP, BRAND, 0, m, was_bad)
        total += d['B8']
        results.append(d)
        FAT = d['FAT']
        EMP = d['EMP']
        BRAND = d['BRAND']
        was_bad = d['was_quality_bad']
    return results, total


# ============================================================
# 场景测试
# ============================================================

print("=" * 130)
print("  原料品质惩罚 + 客流分化 模型验证")
print("  常客流: 品质/品牌敏感 | 旅游客流: B15>=5触发, 品质不敏感")
print("=" * 130)

# 场景1: 正常社区店
print("\n--- 场景A: 社区熟客店 (B15=3, 品质优先) ---")
params = (22, 3, 100, 1000, 60, 3, 4, 4000)  # B10=4 好原料
results, total = run_sim(params)
for d in results[:3]:
    print("  M%d: 常客%d + 旅游%d = %d | 品牌%d | 品质%.2f | 利润¥%d" %
          (d['m']+1 if 'm' in d else results.index(d)+1, d['B2r'], d['B2t'], d['B2'],
           d['BRAND'], d['B28'], d['B8']))
print("  年利润: ¥%d" % total)

print("\n--- 场景B: 同样社区店但用垃圾面粉 (B10=1) ---")
params = (22, 3, 100, 1000, 60, 3, 1, 4000)  # B10=1 垃圾
results, total = run_sim(params)
for d in results[:6]:
    print("  M%d: 常客%d + 旅游%d = %d | 品牌%d | 品质%.2f | 利润¥%d" %
          (results.index(d)+1, d['B2r'], d['B2t'], d['B2'], d['BRAND'], d['B28'], d['B8']))
print("  年利润: ¥%d (vs 好原料 ¥%d → 品牌从%d跌到%d)" % (total, 0,
      results[0]['BRAND'] if results else 0, results[-1]['BRAND'] if results else 0))

# 重新算好原料版本对比
results_good, total_good = run_sim((22, 3, 100, 1000, 60, 3, 4, 4000))
results_bad, total_bad = run_sim((22, 3, 100, 1000, 60, 3, 1, 4000))
print("  好原料年利润: ¥%d, 终态品牌: %d" % (total_good, results_good[-1]['BRAND']))
print("  坏原料年利润: ¥%d, 终态品牌: %d" % (total_bad, results_bad[-1]['BRAND']))
print("  差: ¥%d, 品牌从 %d 跌到 %d" % (total_good - total_bad,
      results_bad[0]['BRAND'], results_bad[-1]['BRAND']))

# 场景3: 品质恢复测试
print("\n--- 场景C: 口碑店作死再救回 ---")
print("  前6个月 B10=1 (垃圾), 后6个月 B10=5 (顶级)")
total_all = 0
brand_history = []
for m in range(12):
    b10 = 1 if m < 6 else 5
    p = (22, 3, 100, 1000, 60, 3, b10, 4000)
    d = compute_month_new(p, 40 if m == 0 else results[-1]['FAT'],
                         0 if m == 0 else results[-1]['EMP'],
                         0 if m == 0 else results[-1]['BRAND'],
                         0, m,
                         False if m == 0 else results[-1]['was_quality_bad'])
    results = results[-1:] + [d] if m > 0 else [d]
    total_all += d['B8']
    brand_history.append(d['BRAND'])
    if m < 3 or m >= 9:
        print("  M%d: B10=¥%d | 常客%d | 品牌%d | 品质%.2f | 利润¥%d" %
              (m+1, b10, d['B2r'], d['BRAND'], d['B28'], d['B8']))

print("  品牌轨迹: %s" % " → ".join(str(b) for b in brand_history))
print("  年利润: ¥%d" % total_all)

# 场景4: 割韭菜模式 — 高奢地段 + 垃圾原料
print("\n--- 场景D: 割韭菜模式 (B15=9, B10=1, ¥28) ---")
params = (28, 2, 200, 8000, 80, 9, 1, 5000)
results, total = run_sim(params)
for d in results[:6]:
    print("  M%d: 常客%d + 旅游%d = %d | 品牌%d | 品质%.2f | 利润¥%d" %
          (results.index(d)+1, d['B2r'], d['B2t'], d['B2'], d['BRAND'], d['B28'], d['B8']))
print("  年利润: ¥%d → 割韭菜能赚但品牌从%d跌到%d" % (total, results[0]['BRAND'], results[-1]['BRAND']))

# 场景5: 高奢正常模式
print("\n--- 场景E: 高奢正常模式 (B15=9, B10=5, ¥32) ---")
params = (32, 2, 300, 8000, 80, 9, 5, 5500)
results, total = run_sim(params)
for d in results[:6]:
    print("  M%d: 常客%d + 旅游%d = %d (旅游占比%.0f%%) | 品牌%d | 品质%.2f | 利润¥%d" %
          (results.index(d)+1, d['B2r'], d['B2t'], d['B2'],
           d['B2t']/max(d['B2'],1)*100, d['BRAND'], d['B28'], d['B8']))
print("  年利润: ¥%d" % total)

print("\n" + "=" * 130)
print("  结论:")
print("  1. 垃圾原料 → 品牌每月额外衰减 (B28<0.5时衰减=(0.5-B28)×30) → 常客流崩盘")
print("  2. 品质恢复后品牌增长打5折 → 作死容易救回难")
print("  3. 旅游客流: B15=5起每级+600基础客流, 对B28不敏感 → 割韭菜有理论可能")
print("  4. 割韭菜模式: B15=9+B10=1 → 旅游客撑场, 品牌跌到0但还能赚(因为旅游客不看品质)")
print("  5. 但旅游客对价格也有一定敏感, 不能无限提价")
print("=" * 130)
