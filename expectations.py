import sys, math
sys.path.insert(0,'.')
exec(open('calibrate_v5.py').read().split("print('V5.6")[0])

# 重新定义sk(平滑) - calibrate_v5.py里已经有了
# 直接跑

def time_to_goal(label, B1, B24, B25, B13, B14, B10, B26, B15, goal=1_000_000, max_years=30):
    r = sim(label, B1, B24, B25, B13, B14, B10, B26, B15, max_years * 12)
    cum = 0
    for i in range(max_years):
        cum += sum(r['profits'][i*12:(i+1)*12])
        if cum >= goal:
            last12 = sum(r['profits'][-12:]) // 12
            stage = '初期' if i <= 2 else '成长期' if i <= 5 else '稳定期'
            print(f'  {label:28s}  第{i+1:2d}年  {stage}  ¥{cum:>9,}  月均¥{last12:,}')
            return
    last12 = sum(r['profits'][-12:]) // 12
    print(f'  {label:28s}  {max_years}年未达标  (¥{cum:>9,})  月均¥{last12:,}')

print('='*65)
print('  V5.6 成功期望 — 到¥100万')
print('='*65)

print('\n--- 三条标准路线 (¥5K工资) ---')
time_to_goal('社区精酿 B15=3', 22,3,200,1500,60,5,5000,3)
time_to_goal('高奢溢价 B15=9', 30,3,500,5000,80,8,5000,9)
time_to_goal('大厂走量 B15=7', 16,8,100,8000,250,5,5000,7)

print('\n--- 高奢变体 ---')
time_to_goal('高奢扩100㎡ B15=9', 30,4,300,8000,100,8,5000,9)
time_to_goal('高奢扩100㎡ B15=10', 30,4,300,8000,100,8,5000,10)
time_to_goal('高奢加薪¥8K B15=9', 30,3,500,5000,80,8,8000,9)

print('\n--- 大厂变体 ---')
time_to_goal('大厂走量 B15=9', 16,8,100,8000,250,5,5000,9)
time_to_goal('大厂300㎡ B15=9', 18,8,100,8000,300,5,5000,9)
time_to_goal('大厂走量 ¥16→¥18', 18,8,100,8000,250,5,5000,7)

print('\n--- 社区变体 ---')
time_to_goal('社区 B15=5', 22,3,200,2000,80,5,5000,5)
time_to_goal('社区B15=5扩100㎡', 22,3,200,2000,100,5,5000,5)
time_to_goal('社区B15=7提价¥26', 26,3,200,2000,80,5,5000,7)

print('\n--- 全局最优 ---')
time_to_goal('极限扩张 B15=10', 16,10,300,15000,300,4,5000,10)
time_to_goal('极限+高薪¥7K', 16,10,300,15000,300,4,7000,10)
time_to_goal('高奢极限 B15=10', 32,5,500,12000,150,8,6000,10)
