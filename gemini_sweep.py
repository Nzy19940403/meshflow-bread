"""
GEMINI v3 — 全参数穷举验证
找出每条路线的理论上限 + 最优参数组合
"""
import math
import itertools

def sk(fat):
    if not math.isfinite(fat): return 1.0
    if fat < 20:  return 1 + (20 - fat) / 20 * 0.1
    if fat < 60:  return 1.0
    if fat < 80:  return 1 - (fat - 60) / 20 * 0.35
    if fat < 90:  return 0.65 - (fat - 80) / 10 * 0.35
    return max(0.10, 0.30 - (fat - 90) / 10 * 0.20)

def simulate(params, do_strategy=None):
    """模拟12个月，params包含所有初始参数"""
    p = dict(params)
    # 安全缺省值
    defaults = {"B1":16,"B24":5,"B25":50,"B13":1000,"B10":3,"B14":60,"B15":7}
    for k,v in defaults.items():
        p.setdefault(k, v)
    B1, B24, B25, B13, B10, B14, B15 = p["B1"], p["B24"], p["B25"], p["B13"], p["B10"], p["B14"], p["B15"]
    c = {"B1":B1,"B2":0,"B3":0,"B4":2.0,"B5":0,"B6":0,"B7":0,"B8":0,"B9":0,
         "B10":B10,"B11":0,"B12":0,"B13":B13,"B14":B14,"B15":B15,"B21":0.8,"B24":B24,"B25":B25,
         "FAT":40,"EMP":0,"BRAND":0,"last_B2":0,"last_B3":0}
    cash = 50000
    profits, dec = [], []

    for month in range(12):
        if do_strategy:
            do_strategy(c, month, params)
        pp = c
        c["B9"] = round(pp["B24"]*1200*(1+pp["B15"]*0.15*max(0,1-pp["B24"]*0.08)))
        ph = max(1, min(math.floor(pp["B14"]*25),pp["B24"]*600)+max(0,round((2-c["B4"])*200)))
        c["B3"] = max(0, round(ph*sk(c["FAT"])))
        c["B4"] = max(0.1, max(0.1,2-c["B3"]*0.0002)*(1-c["EMP"]*0.002))
        
        # === Gemini v3 客流 ===
        pb = 1+(20-pp["B1"])*0.15 if pp["B1"]<20 else max(0.5,1-(pp["B1"]-20)*0.03)
        base_traffic = round(250*pp["B15"])
        brand_bonus = round(c["BRAND"]*1.5)
        marketing = round(math.sqrt(max(0,pp["B13"]))*12)
        tr = round((base_traffic+brand_bonus)*pb)+marketing
        
        # === Gemini v3 ma ===
        ma = max(1, 10+pp["B15"]*1.2+c["BRAND"]*0.3+c["B21"]*4)
        if pp["B1"]<=ma: retention = 0.5+(ma-pp["B1"])/ma*0.4
        else: retention = max(0.05,0.5*ma/pp["B1"])
        c["B2"] = max(0, round(tr*retention))
        c["B5"] = max(0, round(pp["B14"]*pp["B15"]*max(2,20-pp["B14"]*0.05)))
        
        pp2 = c["B9"]/max(c["B3"],1); bl=3+pp["B15"]*0.4
        ps = 0.7+min((pp2-bl)/(bl*2),0.3) if pp2>=bl else pp2/bl*0.7
        c["B21"] = round(min(1,max(0,ps-max(0,c["B3"]/ph-0.8)*1.5))*1000)/1000
        c["B12"] = round(pp["B10"]*(1-min(0.3,c["B3"]*0.00005))*100)/100
        c["B11"] = c["B4"]+c["B3"]*0.002
        c["B6"] = min(c["B2"],c["B3"])
        c["B7"] = c["B6"]*pp["B1"]
        c["B8"] = round(c["B7"]-(c["B12"]+1+c["B4"])*c["B3"]-c["B5"]-c["B9"]-pp["B13"]-pp["B25"]*pp["B24"]-round(0.05*pp["B24"]*1500))
        
        profit=c["B8"]; cash+=profit; profits.append(profit)
        if cash<0 and month<11: return round(sum(profits)), profits, True, cash, len(profits)
        
        # fd()
        ph2 = max(1, min(math.floor(pp["B14"]*25),pp["B24"]*600)+max(0,round((2-c["B4"])*200)))
        d=3
        if pp["B25"]==0 and (c["B3"]/ph2)>0.7: d+=5
        elif pp["B25"]==0: d+=2
        if (c["B3"]/ph2)>0.8: d+=(c["B3"]/ph2-0.8)*40
        d-=pp["B25"]*0.03; ff=c["FAT"]/40 if c["FAT"]<40 else 1
        if c["B21"]<0.5: d-=(c["B21"]-0.5)*15*ff
        if c["B9"]/pp["B24"]>1500: d-=(c["B9"]/pp["B24"]-1500)*0.005*ff
        c["FAT"]=max(0,min(100,round(c["FAT"]+d)))
        emp_gain=max(1,10-round(c["EMP"]*0.05))
        c["EMP"]=min(200,round(c["EMP"]+emp_gain))
        shortage_rate=max(0,(c["B2"]-c["B3"])/max(1,c["B2"]))
        decay_base=max(0.02,c["BRAND"]*0.015)
        growth_mult=max(0.1,1-c["BRAND"]/800)
        brand_growth=c["B21"]*30
        brand_decay=c["BRAND"]*decay_base
        brand_net=brand_growth*growth_mult-brand_decay-shortage_rate*10
        c["BRAND"]=max(0,round(c["BRAND"]+brand_net))
        c["last_B2"]=c["B2"]; c["last_B3"]=c["B3"]
    
    return round(sum(profits)), profits, False, cash, 12


# ===== 策略工厂 =====

# 策略 1: 挂机 (不动任何参数)
def idle(c, m, p): pass

# 策略 2: 聪明大厂 — 逐步扩张
def smart_factory(c, m, p):
    if m==0: c["B1"]=16; c["B24"]=5; c["B25"]=50; c["B13"]=1000; c["B10"]=3; c["B14"]=60
    if m==3: c["B14"]=100; c["B24"]=8; c["B25"]=100; c["B13"]+=500
    if m==6: c["B14"]=150; c["B24"]=12
    if m==9 and c["BRAND"]>80: c["B1"]=18

# 策略 3: 聪明大厂 v2 — 温和扩张
def smart_factory2(c, m, p):
    if m==0: c["B1"]=16; c["B24"]=4; c["B25"]=50; c["B13"]=800; c["B10"]=3; c["B14"]=60
    if m==4: c["B24"]=6; c["B14"]=80; c["B13"]+=500
    if m==8: c["B24"]=8; c["B14"]=120

# 策略 4: 高奢 — 先养品牌后提价
def smart_luxury(c, m, p):
    if m==0: c["B1"]=25; c["B24"]=3; c["B25"]=500; c["B13"]=6000; c["B10"]=3; c["B14"]=100
    if m==4 and c["BRAND"]>30: c["B1"]=30
    if m==7 and c["BRAND"]>80: c["B1"]=35
    if m==10 and c["BRAND"]>150: c["B1"]=40

# 策略 5: 高奢保守 — 稳扎稳打
def smart_luxury2(c, m, p):
    if m==0: c["B1"]=22; c["B24"]=3; c["B25"]=400; c["B13"]=5000; c["B10"]=3; c["B14"]=80
    if m==5 and c["BRAND"]>50: c["B1"]=28
    if m==9: c["B1"]=32

# 策略 6: 高奢激进 — 满配拉满
def smart_luxury3(c, m, p):
    if m==0: c["B1"]=28; c["B24"]=2; c["B25"]=800; c["B13"]=8000; c["B10"]=3; c["B14"]=80
    if m==3: c["B13"]+=2000
    if m==6 and c["BRAND"]>60: c["B1"]=35
    if m==9: c["B1"]=42

# 策略 7: 社区精酿
def smart_community(c, m, p):
    if m==0: c["B1"]=20; c["B24"]=2; c["B25"]=0; c["B13"]=0; c["B10"]=3; c["B14"]=50
    if m==3: c["B25"]=100; c["B13"]=500
    if m==6: c["B1"]=24
    if m==9: c["B1"]=28

# 策略 8: 大厂精细化管理
def smart_factory3(c, m, p):
    if m==0: c["B1"]=16; c["B24"]=3; c["B25"]=80; c["B13"]=1500; c["B10"]=3; c["B14"]=50
    if m==2 and c["BRAND"]>10: c["B24"]=5; c["B14"]=80
    if m==4: c["B24"]=7; c["B14"]=100; c["B13"]+=1000
    if m==6: c["B24"]=10; c["B14"]=130
    if m==8 and c["BRAND"]>100: c["B1"]=19
    if m==10: c["B1"]=21

# 策略 9: 大厂 v4 — 极简起步
def smart_factory4(c, m, p):
    if m==0: c["B1"]=15; c["B24"]=3; c["B25"]=0; c["B13"]=500; c["B10"]=3; c["B14"]=50
    if m==3: c["B24"]=5; c["B14"]=70; c["B13"]=1000
    if m==6: c["B24"]=7; c["B14"]=100; c["B13"]=2000
    if m==9 and c["BRAND"]>60: c["B1"]=18


# ===== 跑全部 =====
STRATEGIES = [
    ("😴 挂机", idle),
    ("🏭 聪明大厂 v1", smart_factory),
    ("🏭 聪明大厂 v2", smart_factory2),
    ("🏭 聪明大厂 v3 精细管理", smart_factory3),
    ("🏭 聪明大厂 v4 极简起步", smart_factory4),
    ("✨ 高奢 v1 先养后涨", smart_luxury),
    ("✨ 高奢 v2 保守", smart_luxury2),
    ("✨ 高奢 v3 激进", smart_luxury3),
    ("🏠 社区精酿", smart_community),
]

# 也跑纯参数穷举
def brute_force_opt():
    """粗搜最佳参数组合"""
    best = {"profit": -999999, "params": None}
    # 三个方向的不同搜索空间
    searches = [
        # 大厂空间
        {"B1":[15,16,18,20], "B24":[3,4,5,6,7,8], "B25":[0,50,100,200],
         "B13":[500,1000,1500,2000], "B10":[3], "B14":[50,60,80,100,120], "B15":[7]},
        # 高奢空间
        {"B1":[22,25,28,30,35], "B24":[2,3,4,5], "B25":[200,400,600,800,1000],
         "B13":[3000,4000,5000,6000,8000], "B10":[3], "B14":[60,80,100,120], "B15":[7]},
        # 社区空间
        {"B1":[16,18,20,22,25], "B24":[2,3,4], "B25":[0,50,100],
         "B13":[0,500,1000], "B10":[3], "B14":[40,50,60,80], "B15":[7]},
    ]
    results = []
    for space in searches:
        keys = list(space.keys())
        for vals in itertools.product(*[space[k] for k in keys]):
            params = dict(zip(keys, vals))
            total, _, bankrupt, cash, _ = simulate(params, idle)
            results.append((total, params, bankrupt))
            if total > best["profit"]:
                best = {"profit": total, "params": dict(params), "bankrupt": bankrupt}
    return best, results

print("🔥"*30)
print("  GEMINI v3 — 全策略+穷举验证")
print("🔥"*30)

# 第一部分：策略测试
print(f"\n{'='*65}")
print(f"  策略测试 (聪明玩家动态调参)")
print(f"{'='*65}")
print(f"  {'策略':30s} {'全年利润':>12s} {'月均':>10s} {'状态':>8s} {'期末现金':>10s}")
print(f"  {'-'*65}")
strategy_results = []
for name, fn in STRATEGIES:
    total, monthly, bankrupt, cash, n = simulate({}, fn)
    avg = total // n
    status = "💀破产" if bankrupt else "✅存活"
    print(f"  {name:30s} {total:>+10,}  {avg:>+8,}  {status:>8s} {cash:>+10,}")
    strategy_results.append((name, total, bankrupt, cash))

# 第二部分：纯参数穷举
print(f"\n{'='*65}")
print(f"  参数穷举 (挂机12个月不动)")
print(f"{'='*65}")
print(f"  搜索空间: 大厂3^6+高奢3^6+社区3^6 ≈ 20K组合")
print(f"  (每个方向取关键参数子集)")
print(f"{'='*65}")

best_overall, all_results = brute_force_opt()
print(f"\n🏆 全局最佳 (挂机不动):")
print(f"   利润: {best_overall['profit']:>+8,}")
print(f"   参数: {best_overall['params']}")
print(f"   状态: {'破产' if best_overall.get('bankrupt') else '存活'}")

# 按路线分组最佳
print(f"\n{'='*65}")
print(f"  各路线最佳参数 (挂机)")
print(f"{'='*65}")
print(f"  {'路线':30s} {'利润':>10s} {'售价':>5s} {'员工':>5s} {'培训':>6s} {'营销':>6s} {'面积':>5s}")
print(f"  {'-'*65}")

# 大厂路线 (B1<=20, B24≥4)
factory_best = max([r for r in all_results if r[1].get("B1",99)<=20 and r[1].get("B24",0)>=4], key=lambda x: x[0])
luxury_best = max([r for r in all_results if r[1].get("B1",0)>=22 and r[1].get("B13",0)>=3000], key=lambda x: x[0])
community_best = max([r for r in all_results if r[1].get("B14",0)<=80 and r[1].get("B13",0)<=2000], key=lambda x: x[0])

for name, best in [("🏭 大厂走量", factory_best), ("✨ 高奢溢价", luxury_best), ("🏠 社区精酿", community_best)]:
    p = best[1]
    print(f"  {name:30s} {best[0]:>+8,}  {p['B1']:>4}  {p['B24']:>4}  {p['B25']:>5}  {p['B13']:>5}  {p['B14']:>4}")

# 最终总结
print(f"\n{'='*65}")
print(f"  📊 最终结论")
print(f"{'='*65}")

for name, total, bankrupt, cash in strategy_results:
    if not bankrupt:
        print(f"  ✅ {name:30s} → 年利润 {total:>+8,}")
    else:
        print(f"  ❌ {name:30s} → 破产")
