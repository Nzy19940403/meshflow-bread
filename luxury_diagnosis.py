"""
高奢路线 — 深度满意度诊断
"""
import math

class State:
    def __init__(self):
        self.B1=30; self.B2=0; self.B3=0; self.B4=2; self.B5=0
        self.B6=0; self.B7=0; self.B8=0; self.B9=0; self.B10=3
        self.B11=0; self.B12=0; self.B13=5000; self.B14=80
        self.B15=7; self.B21=0.8; self.B24=3; self.B25=500
        self.FAT=0; self.EMP=0; self.BRAND=0; self.TRAFFIC=0

def sk(v):
    if v < 20: return 1.0 + (20-v)/20*0.1
    if v < 60: return 1.0
    if v < 80: return 1.0 - (v-60)/20*0.2
    if v < 90: return 0.80 - (v-80)/10*0.5
    return max(0.10, 0.30 - (v-90)/10*0.2)

s = State()

# 逐月打印前12个月
for month in range(1, 13):
    # rc()
    s.B9 = round(s.B24 * 1200 * (1 + s.B15 * 0.15 * max(0, 1 - s.B24 * 0.08)))
    ph = max(1, min(s.B14 * 25, s.B24 * 600) + max(0, round((2 - s.B4) * 200)))
    s.B3 = max(0, round(ph * sk(s.FAT)))
    s.B4 = max(0.1, max(0.1, 2 - s.B3 * 0.0002) * (1 - s.EMP * 0.002))
    
    pb = (1 + (20 - s.B1) * 0.15) if s.B1 < 20 else max(0.6, 1 - (s.B1 - 20) * 0.03)
    area_lever = 1 + s.B14 / 100
    base_tr = round(250 * s.B15) + round(s.BRAND * 3)
    mkt_tr = round(math.sqrt(max(0, s.B13)) * 12)
    tr = round(base_tr * pb) + round(mkt_tr * area_lever)
    ma = max(1, 10 + s.B15 * 1.2 + s.BRAND * 0.3 + s.B21 * 4)
    conv = (0.5 + (ma - s.B1) / ma * 0.4) if s.B1 <= ma else max(0.05, 0.5 * ma / s.B1)
    s.B2 = max(0, round(tr * conv))
    s.B5 = max(0, round(s.B14 * s.B15 * max(2, 20 - s.B14 * 0.05)))
    
    pp = s.B9 / max(s.B3, 1)
    bl = 3 + s.B15 * 0.4
    ps = (0.7 + min((pp - bl) / (bl * 2), 0.3)) if pp >= bl else (pp / bl * 0.7)
    util = s.B3 / ph
    over_penalty = max(0, util - 0.8) * 0.8
    s.B21 = round(min(1, max(0, ps - over_penalty)) * 1000) / 1000
    
    s.B12 = round(s.B10 * (1 - min(0.5, s.B3 * 0.00008)) * 100) / 100
    s.B6 = min(s.B2, s.B3)
    s.B7 = s.B6 * s.B1
    s.B8 = round(s.B7 - (s.B12 + 1 + s.B4) * s.B3 - s.B5 - s.B9 - s.B13 - s.B25 * s.B24 - round(0.05 * s.B24 * 1500))
    s.TRAFFIC = tr

    # fd()
    d = 3
    if s.B25 == 0 and (s.B3 / ph) > 0.7: d += 5
    elif s.B25 == 0: d += 2
    if (s.B3 / ph) > 0.8: d += ((s.B3 / ph) - 0.8) * 40
    d -= s.B25 * 0.03
    ff = s.FAT / 40 if s.FAT < 40 else 1
    if s.B21 < 0.5: d -= (s.B21 - 0.5) * 15 * ff
    if s.B9 / s.B24 > 1500: d -= (s.B9 / s.B24 - 1500) * 0.005 * ff
    nf = max(0, min(100, round(s.FAT + d)))

    profit = s.B8

    print(f"月{month:2d} | FAT={s.FAT:3d}→{nf:3d} | sk={sk(s.FAT):.2f} | B3={s.B3:4d} | 需求={s.B2:4d} | "
          f"实售={s.B6:4d} | util={util:.2f} | pp={pp:.2f} bl={bl:.1f} | ps={ps:.3f} "
          f"overPen={over_penalty:.3f} | B21={s.B21:.3f} | "
          f"品牌={s.BRAND:3d} | 利润={'+' if profit>=0 else ''}¥{profit:+,}")

    # nx()部分: 推进
    shortage_rate = max(0, (s.B2 - s.B3) / max(1, s.B2))
    brand_growth = s.B21 * 30
    brand_decay = s.BRAND * max(0.02, s.BRAND * 0.015)
    growth_mult = max(0.1, 1 - s.BRAND / 800)
    s.BRAND = max(0, round(s.BRAND + brand_growth * growth_mult - brand_decay - shortage_rate * 10))
    s.EMP = min(200, round(s.EMP + max(1, 10 - round(s.EMP * 0.05))))
    s.FAT = nf
