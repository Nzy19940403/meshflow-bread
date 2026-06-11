"""诊断: 追踪单月引擎传播"""
import sys, math, json
sys.path.insert(0,'.')
exec(open('v5_7_verify.py').read().split("print('V5.7")[0])

# 手动跟踪一个月的计算
s = State()
params = {'B1':28,'B24':3,'B25':500,'B13':6000,'B14':120,'B10':8,'B26':5000,'B15':9}

print('Python V5.7 逐月明细 (高奢精兵):')
for month in range(3):
    p = one_month(s, params['B1'],params['B24'],params['B25'],params['B13'],
                   params['B14'],params['B10'],params['B26'],params['B15'])
    print(f'月{month+1}:')
    print(f'  B2={s.B2} B3={s.B3} B4={s.B4:.3f} B5={s.B5} B9={s.B9}')
    print(f'  B12={s.B12:.2f} B21={s.B21:.3f} FAT={s.FAT} BRAND={s.BRAND}')
    print(f'  营收={s.B7} 利润={p}')
