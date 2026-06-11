"""V5.6 — sk平滑"""
import sys, math

def sk(c4):
    """平滑S曲线: 80以下0疲劳, 80-100间smoothstep渐变到0.10"""
    if c4 < 80: return 1.0
    if c4 >= 100: return 0.10
    t = (c4 - 80) / 20
    sm = t * t * (3 - 2 * t)
    return 1.0 - sm * 0.9

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

def one_month(s, B1, B24, B25, B13, B14, B10, B26, B15=7):
    q = type('Q',(),{'B1':B1,'B24':B24,'B25':B25,'B13':B13,'B14':B14,
                     'B10':B10,'B26':B26,'B15':B15})()
    s.B9 = round(q.B24 * q.B26 * (1 + q.B15 * 0.15 * max(0, 1 - q.B24 * 0.08)))
    wf = 0.2 + 1.6 * q.B26 / 10000
    waste_factor = max(0.3, 1.5 - q.B26 / 5000)
    quality_premium = max(0, (q.B26 - 4000) / 500)
    ph = max(1, min(q.B14 * 35, q.B24 * 1500) * wf + max(0, round((2 - s.B4) * 100)))
    s.B3 = max(0, round(ph * sk(s.FAT)))
    s.B4 = max(0.1, max(0.1, 2 - s.B3 * 0.0002) * (1 - s.EMP * 0.002) * waste_factor)
    pb = (1 + (20 - q.B1) * 0.15) if q.B1 < 20 else max(0.6, 1 - (q.B1 - 20) * 0.03)
    base_tr = round(500 + 500 * q.B15) + round(s.BRAND * 3)
    area_lever = 1 + q.B14 / 100
    mkt_tr = round(math.sqrt(max(0, q.B13)) * 10)
    tr = round(base_tr * pb) + round(mkt_tr * area_lever)
    ma = max(1, 15 + q.B15 * 2 + s.BRAND * 0.5 + s.B21 * 3 + quality_premium)
    conv = 0.5 + (ma - q.B1) / ma * 0.4 if q.B1 <= ma else max(0.05, 0.5 * ma / q.B1)
    s.B2 = max(0, round(tr * conv))
    s.B5 = max(0, round(q.B14 * q.B15 * max(2, 20 - q.B14 * 0.05)))
    pp = s.B9 / max(q.B24, 1); bl = 3 + q.B15 * 0.4
    ps = pp / bl * 0.7 if pp < bl else 0.7 + min((pp - bl) / (bl * 2), 0.3)
    s.B21 = round(min(1, max(0, ps - max(0, s.B3/ph - (0.8 + 0.2*ps)) * 1.5)) * 1000) / 1000
    s.B12 = round(q.B10 * (1 - min(0.5, s.B3 * 0.00008)) * 100) / 100
    s.B11 = s.B4 + s.B3 * 0.002; s.B6 = min(s.B2, s.B3)
    drink_rev = round(s.B6 * q.B1 * 0.20)
    s.B7 = s.B6 * q.B1 + drink_rev
    packaging = round(q.B1 * 0.15)
    utilities = round(q.B14 * 25 + q.B24 * 200)
    equipment = 2000
    s.B8 = round(s.B7 - (s.B12 + packaging + s.B4) * s.B3 - s.B5 - s.B9
                 - q.B13 - q.B25 * q.B24 - round(0.05 * q.B24 * 1500)
                 - utilities - equipment)
    s.TRAFFIC = tr; s.B20 = round(s.B21 * 100) / 100
    d = 3
    if q.B25 == 0 and (s.B3 / ph) > 0.7: d += 5
    elif q.B25 == 0: d += 2
    if (s.B3 / ph) > 0.8: d += ((s.B3 / ph) - 0.8) * 40
    d -= q.B25 * 0.03
    ff = s.FAT / 40 if s.FAT < 40 else 1
    if s.B21 < 0.5: d -= (s.B21 - 0.5) * 15 * ff
    if s.B9 / q.B24 > 1500: d -= (s.B9 / q.B24 - 1500) * 0.005 * ff
    nf = max(0, min(100, round(s.FAT + d)))
    profit = round(s.B8)
    s.EMP = min(200, round(s.EMP + max(1, 10 - round(s.EMP * 0.05))))
    shortage_rate = max(0, (s.B2 - s.B3) / max(1, s.B2))
    brand_growth = s.B21 * 30
    brand_decay = s.BRAND * max(0.02, s.BRAND * 0.015)
    growth_mult = max(0.1, 1 - s.BRAND / 800)
    s.BRAND = max(0, round(s.BRAND + brand_growth * growth_mult - brand_decay - shortage_rate * 10))
    s.FAT = nf
    return profit

def sim(label, B1, B24, B25, B13, B14, B10, B26, B15=7, months=36):
    s = State()
    profits = []
    for _ in range(months):
        p = one_month(s, B1, B24, B25, B13, B14, B10, B26, B15)
        profits.append(p)
    return {'label':label,'total':sum(profits),'final':{
        'B2':s.B2,'B3':s.B3,'B4':round(s.B4,4),'B5':s.B5,'B6':s.B6,'B7':s.B7,'B8':s.B8,
        'B9':s.B9,'B12':s.B12,'B20':s.B20,'B21':s.B21,
        'BRAND':s.BRAND,'FAT':s.FAT,'EMP':s.EMP,'TRAFFIC':s.TRAFFIC,
    },'profits':profits}

def pt(label, B1, B24, B25, B13, B14, B10, B26, B15, m=36):
    r = sim(label, B1, B24, B25, B13, B14, B10, B26, B15, m)
    f = r['final']
    last = sum(r['profits'][-12:])//12
    # 检查后12个月是否有剧烈波动
    last12 = r['profits'][-12:]
    max_var = max(last12) - min(last12)
    print(f'  {label:25s}  3年:{r["total"]:+>8,}  月净:{last:+>6,}  后12月波幅:{max_var:>5,}')

print('V5.6 — sk平滑  (社区精酿特别注意波幅)')
print('='*65)
pt('社区精酿 B15=3', 22,3,200,1500,60,5,5000,3)
pt('高奢溢价 B15=9', 30,3,500,5000,80,8,5000,9)
pt('大厂走量 B15=7', 16,8,100,8000,250,5,5000,7)

# 特别检查社区路线有无振荡
r = sim('社区', 22,3,200,1500,60,5,5000,3, 60)
fat_values = [None]
s = State()
for i in range(60):
    p = one_month(s, 22,3,200,1500,60,5,5000,3)
    fat_values.append(s.FAT)

print()
print('社区路线 FAT 演化 (后24个月):')
fat_str = ','.join(str(f) for f in fat_values[-24:])
print(f'  [{fat_str}]')
# 检查是否在80附近来回跳
osc = sum(1 for i in range(len(fat_values)-1) if abs(fat_values[i]-fat_values[i+1]) > 10)
print(f'  大幅波动(>10)次数: {osc}')
