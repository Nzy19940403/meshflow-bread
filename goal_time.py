import sys, math, json
sys.path.insert(0,'.')
exec(open('calibrate_v5.py').read().split("print('V5.3")[0])

def time_to_goal(label, B1, B24, B25, B13, B14, B10, B26, B15, goal=1_000_000, max_years=30):
    r = sim(label, B1, B24, B25, B13, B14, B10, B26, B15, max_years*12)
    cum = 0
    for i in range(max_years):
        cum += sum(r['profits'][i*12:(i+1)*12])
        if cum >= goal:
            final_monthly = sum(r['profits'][-12:]) // 12
            print(f'  {label:30s}  第{i+1:2d}年  ¥{cum:>9,}  稳态月净¥{final_monthly:,}')
            return i+1
    print(f'  {label:30s}  {max_years}年未达标  ¥{cum:>9,}')
    return None

print('='*65)
print('  V5.3 成功期望 — 到¥100万')
print('='*65)

print('\n--- 标准路线 ---')
time_to_goal('社区精酿 B15=3', 22,3,200,1500,60,5,4000,3)
time_to_goal('高奢溢价 B15=9', 30,3,500,5000,80,8,5000,9)
time_to_goal('大厂走量 B15=7', 16,8,100,8000,250,5,4000,7)

print('\n--- 优化路线 ---')
time_to_goal('大厂300㎡ B15=7', 18,8,100,8000,300,5,4000,7)
time_to_goal('大厂300㎡ B15=8', 18,8,100,8000,300,5,4000,8)
time_to_goal('大厂300㎡ B15=9', 18,8,100,8000,300,5,4000,9)
time_to_goal('大厂B15=9+高薪', 18,8,200,10000,300,5,5000,9)
time_to_goal('高奢4人扩100㎡', 30,4,300,8000,100,8,5000,9)
time_to_goal('高奢4人扩100㎡B15=10', 30,4,300,8000,100,8,5000,10)

print('\n--- 社区极限 ---')
time_to_goal('社区拓100㎡', 22,3,200,2000,100,5,4000,3)
time_to_goal('社区提价¥28', 28,3,200,2000,100,5,4000,3)
time_to_goal('社区B15=5', 22,3,200,2000,100,5,4000,5)

print('\n--- 极端测试 ---')
time_to_goal('极限扩张B15=10', 15,10,300,15000,300,4,4500,10)
time_to_goal('精品B15=10+扩', 35,5,500,12000,150,8,6000,10)
