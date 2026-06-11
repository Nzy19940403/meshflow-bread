"""
V5.3 完整验证
"""
import sys, math
sys.path.insert(0,'.')
exec(open('calibrate_v5.py').read().split("print('V5.3")[0])

# 验证1: 原版三条路线 (含地段差异化)
print('=== 原版三条路线 (B15差异化) ===')
print('-'*60)
scenarios = [
    ('大厂走量  B15=7', 16, 8, 100, 8000, 250, 5, 4000, 7),
    ('高奢溢价  B15=9', 30, 3, 500, 5000, 80, 8, 5000, 9),
    ('社区精酿  B15=3', 22, 3, 200, 1500, 60, 5, 4000, 3),
]
for label, B1, B24, B25, B13, B14, B10, B26, B15 in scenarios:
    r = sim(label, B1, B24, B25, B13, B14, B10, B26, B15, 36)
    f = r['final']
    ann = [sum(r['profits'][i*12:(i+1)*12]) for i in range(3)]
    t = f['TRAFFIC']
    last12 = sum(r['profits'][-12:])
    print(f'{label}')
    print(f'  ￥{B1} {B24}人 {B14}㎡ 工资￥{B26} 进价￥{B10}')
    print(f'  日营收￥{f["B7"]//30:,}  日销{f["B6"]//30}份')
    print(f'  年利润: {ann[0]:+} | {ann[1]:+} | {ann[2]:+}  3年:￥{r["total"]:+}')
    print(f'  稳态月净￥{last12//12:,}  净利{last12//12/max(f["B7"],1)*100:.0f}%')
    print()

# 验证2: 加薪测试 — 工资翻倍能否扛住
print('=== 压力测试: 工资翻倍 / 营销减半 ===')
print('-'*60)
for label, B1, B24, B25, B13, B14, B10, B26, B15, stress in [
    ('社区加薪50%', 18, 2, 100, 1000, 60, 5, 5250, 3, ''),
    ('商场降营销', 30, 4, 300, 4000, 100, 8, 5000, 9, ''),
    ('大厂涨价', 20, 8, 100, 8000, 250, 5, 4000, 7, ''),
]:
    r = sim(label, B1, B24, B25, B13, B14, B10, B26, B15, 36)
    ann = [sum(r['profits'][i*12:(i+1)*12]) for i in range(3)]
    print(f'{label}:  3年￥{r["total"]:+}  ({ann[0]:+} | {ann[1]:+} | {ann[2]:+})')

# 验证3: 不同地段的影响
print()
print('=== 地段等级影响 (大厂8人250㎡) ===')
print('-'*60)
for B15 in [3,5,7,9]:
    r = sim(f'B15={B15}', 16, 8, 100, 8000, 250, 5, 4000, B15, 36)
    f = r['final']
    print(f'  B15={B15}: 月营收￥{f["B7"]:,}  房租￥{f["B5"]:,}  客流{f["TRAFFIC"]}  3年￥{r["total"]:+}  ' +
          (f'月净￥{sum(r["profits"][-12:])//12:+}' if r['total'] > 0 else '亏损'))

# 验证4: 低工资Vs高工资对比
print()
print('=== 工资灵敏度 (社区夫妻店60㎡) ===')
print('-'*60)
for wage in [2500, 3500, 5000, 8000]:
    r = sim(f'工资￥{wage}', 18, 2, 100, 1000, 60, 5, wage, 3, 36)
    ann = [sum(r['profits'][i*12:(i+1)*12]) for i in range(3)]
    print(f'  工资￥{wage}:  3年￥{r["total"]:+}  (最后一年{ann[2]:+})')

# 验证5: 社区店到100万需要多久
print()
print('=== 100万目标时间 (最优方案) ===')
best_configs = [
    ('大厂B15=9', 18, 8, 100, 8000, 300, 5, 4000, 9),
    ('大厂B15=10', 18, 8, 100, 8000, 300, 5, 4000, 10),
    ('高奢B15=10', 30, 4, 300, 8000, 100, 8, 5000, 10),
]
for label, B1, B24, B25, B13, B14, B10, B26, B15 in best_configs:
    r = sim(label, B1, B24, B25, B13, B14, B10, B26, B15, 240)
    cum = 0
    for i in range(20):
        cum += sum(r['profits'][i*12:(i+1)*12])
        if cum >= 1000000:
            print(f'  {label}: 第{i+1}年达100万  月均￥{sum(r["profits"][-12:])//12:,}')
            break
