"""
面包店经营模型 V9 — Python 穷举验证脚本

与 BakerySandbox.vue 引擎逻辑完全对齐，包含：
- dynParams 连续路由参数
- SetRules: B9/B5/B12/B28/B20/B2/B6/B7/B8
- Entangle 收敛: B3↔B4↔B21↔FAT
- 状态演进: FAT/BRAND/EMP
- SK sigmoid 疲劳曲线
- 季节系统
"""

import math, json, time

SEASON = [0.85, 1.10, 0.95, 1.00, 1.00, 0.90, 0.85, 0.85, 1.25, 1.10, 1.00, 1.30]

# ── SK sigmoid: FAT < 80 → 1.0, FAT >= 100 → 0.1 ──
def sk(fat: float) -> float:
    if fat < 80: return 1.0
    if fat >= 100: return 0.1
    t = (fat - 80) / 20
    return 1.0 - t * t * (3 - 2 * t) * 0.9

# ── dynParams: 连续路由函数 ──
def dynParams(g: float, a: float) -> dict:
    gf = max(0, min(1, (g - 2) / 7))
    lf = max(0, min(1, (g - 6) / 4)) * max(0, min(1, (120 - a) / 40))
    ff = max(0, min(1, (a - 100) / 50)) * max(0, min(1, (5 - g) / 3))
    cf = max(0, min(1, 1 - ff - lf))
    return {
        'cv_b': 0.75*cf + 0.70*ff + 0.60*lf,
        'pb_mi': 22*cf + 20*ff + 30*lf,
        'pb_s': 0.03*cf + 0.02*ff + 0.01*lf,
        'pb_fl': 0.40*cf + 0.40*ff + 0.60*lf,
        'cv_s': 0.80*cf + 0.80*ff + 0.60*lf,
        'pr': 0.04*cf + 0.06*ff + 0.12*lf,
        'eq': 1200*cf + 1200*ff + 3000*lf,
        'rb': round(22*cf + 10*ff + 18*lf),
        'rd': round(2000*cf + 800*ff + 1500*lf),
        'ua': round(18*cf + 18*ff + 22*lf),
        'us': round(120*cf + 120*ff + 180*lf),
        'bp_c': round(12*cf + 12*ff + 22*lf),
        'bp_cap': round(45*cf + 45*ff + 60*lf),
        'bg1': round(8*cf + 8*ff + 14*lf),
        'bg2': round(10*cf + 10*ff + 18*lf),
        'apm': round(40*cf + 45*ff + 40*lf),
        'spm': round(1800*cf + 2000*ff + 1800*lf),
        'frh': round(30*cf + 45*ff + 35*lf),
        'ftr': round(8*cf + 15*ff + 12*lf),
        'ful': 0.80*cf + 0.70*ff + 0.75*lf,
    }

# ── physCap: pure headcount*area ──
def physCap(b14: float, b24: float, g: float) -> float:
    dp = dynParams(g, b14)
    return max(1, min(b14 * dp['apm'], b24 * dp['spm']))

# ── brand premium ──
def brandP(brand: float, g: float, a: float) -> float:
    dp = dynParams(g, a)
    raw = dp['bp_c'] * math.log(1 + brand / 25)
    gradeF = min(1, (g - 1) / 8)
    return round(min(dp['bp_cap'], raw * gradeF))

# ── price soft conversion factor ──
def pbF(price: float, pb_mi: float, pb_s: float, pb_fl: float) -> float:
    if price < 15: return 1 + (15 - price) * 0.10
    if price <= pb_mi: return 1.0
    return max(pb_fl, 1 - (price - pb_mi) * pb_s)


class BakeryEngine:
    """Full V9 bakery simulation engine, matching TS BakerySandbox.vue."""

    def __init__(self, b1=18.0, b10=3.0, b13=2000.0, b14=150.0, b15=7.0,
                 b24=8.0, b25=100.0, b26=4000.0):
        # Sliders
        self.B1 = b1
        self.B10 = b10
        self.B13 = b13
        self.B14 = b14
        self.B15 = b15
        self.B24 = b24
        self.B25 = b25
        self.B26 = b26
        # Computed
        self.B9 = 0
        self.B5 = 0
        self.B12 = 0.0
        self.B28 = 0.6
        self.B20 = 0.0
        self.B2 = 0
        self.B3 = 0
        self.B4 = 2.0
        self.B6 = 0
        self.B7 = 0
        self.B8 = 0
        self.B21 = 0.8
        # State
        self.FAT = 40.0
        self.BRAND = 0.0
        self.EMP = 0.0
        self.month_idx = 0  # 0-11 for current season

    # ── SetRules (single-pass, no entangle) ──

    def calc_B9(self):
        h, w, g = self.B24, self.B26, self.B15
        self.B9 = round(h * w * (1 + g * 0.10 * max(0, 1 - h * 0.05)))

    def calc_B5(self):
        a, g = self.B14, self.B15
        dp = dynParams(g, a)
        rate = dp['rb'] + dp['rd'] / (a + 15)
        self.B5 = max(0, round(a * g * rate))

    def calc_B12(self):
        self.B12 = round(self.B10 * (1 - min(0.4, self.B3 * 0.00006)) * 100) / 100

    def calc_B28(self):
        qBase = max(0.15, min(0.95, self.B10 / 5.5))
        qSalary = min(0.18, (self.B26 - 3000) / 28000) if self.B26 > 3000 else 0
        self.B28 = round(min(1.0, qBase + qSalary) * 1000) / 1000

    def calc_B20(self):
        self.B20 = round((self.B21 * 0.45 + self.B28 * 0.55) * 100) / 100

    def calc_B2(self):
        b1, g, mkt = self.B1, self.B15, self.B13
        brand, b21, b26 = self.BRAND, self.B21, self.B26
        b14, b28 = self.B14, self.B28
        sz = SEASON[self.month_idx]

        # Foot traffic
        ft = 500 + 400 * min(g, 6)
        ft += round(math.sqrt(b14) * 15)
        ft += round(pow(max(0, mkt), 0.45) * 0.8)
        ft += round(brand * 0.8)
        if 3 <= g <= 5 and b14 <= 90:
            ft = round(ft * 1.15)  # community density bonus
        localBase = max(0, round(ft))

        # Brand premium
        dpB = brandP(brand, g, b14)
        ma = max(12 + g * 2.5, 12 + g * 2.5 + dpB + b21 * 2 + b28 * 3 + b26 / 2500)

        dp = dynParams(g, b14)
        gap = max(0, b1 - ma)
        conv = dp['cv_b'] * pbF(b1, dp['pb_mi'], dp['pb_s'], dp['pb_fl']) * (ma / (ma + gap * dp['cv_s']))
        conv = min(0.85, max(0.04, conv))

        # Season + brand loyalty
        loyalSz = min(sz, 1.08) if brand >= 200 else (min(sz, 1.12) if brand >= 100 else sz)
        finalSz = max(loyalSz, 0.95 if brand >= 200 else (0.90 if brand >= 100 else sz))
        localDemand = max(0, round(localBase * conv * finalSz))

        # Tourist demand
        tourDemand = 0
        if g >= 5:
            tourBase = (g - 4) * 500 * pbF(b1, dp['pb_mi'], dp['pb_s'], dp['pb_fl'])
            tourMkt = round(math.sqrt(max(0, mkt)) * 5) * (0.5 + brand / 400)
            tourTotal = round(tourBase + tourMkt)
            tourMa = max(8, 8 + g * 2 + mkt / 4000 + brand * 0.25)
            tourConv = min(0.75, 0.30 + (tourMa - b1) / tourMa * 0.35) if b1 <= tourMa else max(0.02, 0.25 * tourMa / b1)
            tourDemand = max(0, round(tourTotal * tourConv * sz))

        self.B2 = max(0, localDemand + tourDemand)

    def calc_B6(self):
        self.B6 = min(self.B2, self.B3)

    def calc_B7(self):
        retail = self.B6 * self.B1
        ws = 0
        if self.B14 >= 150:
            remaining = max(0, self.B3 - self.B6)
            b2bCap = self.B24 * 1200
            spotCap = round((self.B14 - 150) * 500)
            wSold = min(b2bCap + spotCap, remaining)
            qualityMult = 1.0 if self.B28 >= 0.6 else (1.0 - (0.6 - self.B28) * 0.5 if self.B28 >= 0.4 else 0.9 - (0.4 - self.B28) * 1.0)
            b2bPriceMult = min(self.B1, 22) * 0.25 * max(0.5, qualityMult)
            ws = round(wSold * b2bPriceMult)
        self.B7 = retail + ws

    def calc_B8(self):
        dp2 = dynParams(self.B15, self.B14)
        pkg = round(self.B1 * dp2['pr'])
        util = round(self.B14 * dp2['ua'] + self.B24 * dp2['us'])
        eq = dp2['eq']
        trn = self.B25 * self.B24
        misc = round(0.02 * self.B24 * 1000)

        retailCogs = round((self.B12 + pkg + self.B4) * min(self.B6, self.B3))
        wsCogs = 0
        if self.B14 >= 150:
            remaining = max(0, self.B3 - self.B6)
            b2bCap = self.B24 * 1200
            spotCap = round((self.B14 - 150) * 500)
            wSold = min(b2bCap + spotCap, remaining)
            wsCogs = round(wSold * self.B10 * 0.50 + wSold * 0.3)
        cogs = retailCogs + wsCogs
        self.B8 = round(self.B7 - cogs - self.B5 - self.B9 - self.B13 - trn - misc - util - eq)

    # ── Entangle convergence (B3↔B4 cycle) ──

    def converge_B3_B4(self):
        """Iterate B3↔B4 entangle until convergence."""
        physMax = physCap(self.B14, self.B24, self.B15)

        for _ in range(30):
            prev_b3 = self.B3
            # B3 → B4 (entangle 1)
            wfB4 = 1.20 - 0.45 * min(self.B26, 10000) / 10000
            self.B4 = max(0.03, (1.5 - self.B3 * 0.00015) * wfB4 * (1 - self.EMP * 0.002))
            self.B4 = round(self.B4 * 100) / 100

            # B4 → B3 (entangle 2) + FAT → B3 (entangle 4)
            cap = max(0, round(physMax * sk(self.FAT)))
            if abs(cap - self.B3) < 0.5:
                self.B3 = cap
                break
            self.B3 = cap

        # Final pass: M1 → B3 (SetRule style, run AFTER entangle)
        cap = max(0, round(physMax * sk(self.FAT)))
        self.B3 = cap

    def converge_B21(self):
        """B3 → B21 entangle."""
        pc = physCap(self.B14, self.B24, self.B15)
        pp = self.B9 / max(self.B3, 1)
        wageScore = min(1, self.B26 / 5000)
        bl = 2.5 + self.B15 * 0.3
        efficiencyScore = (0.7 + min((pp - bl) / (bl * 2), 0.25)) if pp >= bl else (pp / bl * 0.7)
        b21 = min(1, max(0, wageScore * 0.4 + efficiencyScore * 0.6))
        util = self.B3 / max(pc, 1)
        ov = max(0, util - 0.85) * 1.0
        b21 = max(0.15, b21 - ov)
        if self.FAT > 60: b21 = max(0.25, b21 - (self.FAT - 60) * 0.004)
        if self.FAT > 85: b21 = max(0.10, b21 - (self.FAT - 85) * 0.01)
        self.B21 = round(b21 * 1000) / 1000

    # ── State evolution (monthly tick) ──

    def evolve_FAT(self):
        dp7 = dynParams(self.B15, self.B14)
        physMax = physCap(self.B14, self.B24, self.B15)
        retailUR = min(1, self.B2 / max(physMax, 1))
        bbpScaled = 1200
        b2bSold = min(self.B24 * bbpScaled + (round((self.B14 - 150) * 500) if self.B14 >= 150 else 0),
                      max(0, self.B3 - self.B2))
        totalUR = min(1, (self.B2 + b2bSold) / max(physMax, 1))
        d = 0
        if retailUR > 0.88: d = round((retailUR - 0.88) * dp7['frh'])
        if retailUR > 0.95: d += 2
        if totalUR >= 0.90:
            d += 3
        elif totalUR < dp7['ful']:
            d = -round((dp7['ful'] - totalUR) * 15)
        elif retailUR < 0.75:
            d = -round((0.75 - retailUR) * 5)
        if totalUR > 0.65:
            d += round((totalUR - 0.65) * dp7['ftr'])
        if self.B14 > 150 and self.B24 < math.ceil(self.B14 / 35):
            d += 3
        self.FAT = max(10, min(100, round(self.FAT + d)))

    def evolve_BRAND(self):
        dp4 = dynParams(self.B15, self.B14)
        sr = max(0, (self.B2 - self.B3) / max(1, self.B2))
        growth = (self.B21 * dp4['bg1'] + self.B28 * dp4['bg2'] +
                  max(0, (100 - self.FAT) / 100) * 5 +
                  math.sqrt(max(0, self.B13)) * 0.12)
        decay = self.BRAND * 0.015
        gm = max(0.03, 1 - self.BRAND / 500)
        nb = max(0, round(self.BRAND + growth * gm - decay - sr * 8))
        if self.B28 < 0.40:
            gap = 0.40 - self.B28
            nb = max(0, nb - round(gap * 20))
            ceiling = 50 if self.B28 >= 0.30 else 25
            if nb > ceiling: nb = ceiling
        self.BRAND = nb

    def evolve_EMP(self):
        self.EMP = min(200, round(self.EMP + max(1, 10 - round(self.EMP * 0.05))))

    # ── Full month step ──

    def step_month(self):
        """Execute one full month of simulation."""
        self.calc_B9()
        self.calc_B5()
        self.calc_B28()
        self.calc_B20()
        self.calc_B2()
        self.converge_B3_B4()
        self.calc_B12()
        self.calc_B6()
        self.calc_B7()
        self.calc_B8()
        self.converge_B21()
        self.evolve_FAT()
        self.evolve_BRAND()
        self.evolve_EMP()
        self.month_idx = (self.month_idx + 1) % 12


def sim_year(b1, b10, b13, b14, b15, b24, b25, b26) -> dict:
    """Simulate 12 months, return annual results."""
    eng = BakeryEngine(b1=b1, b10=b10, b13=b13, b14=b14, b15=b15,
                       b24=b24, b25=b25, b26=b26)
    history = []
    for m in range(12):
        eng.step_month()
        history.append({
            'm': m + 1, 'profit': eng.B8, 'revenue': eng.B7, 'cost': eng.B7 - eng.B8,
            'demand': eng.B2, 'capacity': eng.B3, 'sold': eng.B6,
            'FAT': eng.FAT, 'BRAND': eng.BRAND, 'B21': eng.B21,
        })
    total = sum(h['profit'] for h in history)
    return {
        'profit': total,
        'params': {'B1': b1, 'B10': b10, 'B13': b13, 'B14': b14, 'B15': b15,
                    'B24': b24, 'B25': b25, 'B26': b26},
        'history': history,
    }


# ══════════════════════════════════════════════════════════════════
#  GRID SEARCH
# ══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    t0 = time.time()
    results = []

    print("=== V9 Community Route Survival Search ===\n")

    for area in [50, 60, 70, 80, 90]:
        for grade in [2, 3, 4, 5]:
            for price in [18, 20, 22, 24, 26]:
                for staff in [2, 3, 4]:
                    # B9 = staff * B26; B26 sweep around 4k
                    for b26 in [3000, 4000, 5000]:
                        b9 = staff * b26
                        for mkt in [0, 500, 1000, 2000]:
                            for b25 in [0, 100, 300]:
                                r = sim_year(price, 3.0, mkt, area, grade, staff, b25, b26)
                                results.append(r)

    results.sort(key=lambda x: x['profit'], reverse=True)

    # Group by route fingerprint
    print("Top 30 overall:\n")
    for i, r in enumerate(results[:30]):
        p = r['params']
        months_in_red = len([h for h in r['history'] if h['profit'] < 0])
        avg_fat = sum(h['FAT'] for h in r['history']) / 12
        print(f"{i+1:2d}. ¥{r['profit']:>10,}  "
              f"area={p['B14']:>3} g={p['B15']} price=¥{p['B1']} "
              f"staff={p['B24']} w=¥{p['B26']:,} mkt=¥{p['B13']} b25=¥{p['B25']} "
              f"| {months_in_red}R avgFAT={avg_fat:.0f}")

    # ── Community-only (area 50-90, grade 2-5) top results ──
    community = [r for r in results if r['params']['B14'] <= 90 and r['params']['B15'] <= 5]
    community.sort(key=lambda x: x['profit'], reverse=True)

    print(f"\n=== Top 20 Community Route ===\n")
    for i, r in enumerate(community[:20]):
        p = r['params']
        months_in_red = len([h for h in r['history'] if h['profit'] < 0])
        avg_fat = sum(h['FAT'] for h in r['history']) / 12
        # Strategy fingerprint
        fp = '社区' if p['B14'] <= 90 and p['B15'] <= 5 else ''
        print(f"{i+1:2d}. ¥{r['profit']:>10,}  "
              f"area={p['B14']:>3} g={p['B15']} price=¥{p['B1']} "
              f"staff={p['B24']} w=¥{p['B26']:,} mkt=¥{p['B13']} b25=¥{p['B25']} "
              f"| {months_in_red}R FAT={avg_fat:.0f}")

    # ── Show monthly details for best community route ──
    if community:
        best = community[0]
        print(f"\n=== Best Community Route Monthly Detail ===\n")
        print(f"Params: area={best['params']['B14']} g={best['params']['B15']} "
              f"price=¥{best['params']['B1']} staff={best['params']['B24']} "
              f"wage=¥{best['params']['B26']:,} mkt=¥{best['params']['B13']} b25=¥{best['params']['B25']}")
        print(f"{'M':>3} {'Profit':>8} {'Revenue':>8} {'Cost':>8} {'Demand':>6} {'Cap':>6} {'Sold':>6} {'FAT':>5} {'BRAND':>6} {'B21':>5}")
        for h in best['history']:
            print(f"{h['m']:>3} {h['profit']:>8,} {h['revenue']:>8,} {h['cost']:>8,} "
                  f"{h['demand']:>6} {h['capacity']:>6} {h['sold']:>6} "
                  f"{h['FAT']:>5.0f} {h['BRAND']:>6.0f} {h['B21']:>5.2f}")

    print(f"\nSearched {len(results)} combos in {time.time()-t0:.1f}s")
