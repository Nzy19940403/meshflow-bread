"""
最终验证 vFinal — 覆盖所有未验证的数学建模盲区
"""
import math, itertools

def sk(fat):
    if not math.isfinite(fat): return 1.0
    if fat<20: return 1+(20-fat)/20*0.1
    if fat<60: return 1.0
    if fat<80: return 1-(fat-60)/20*0.35
    if fat<90: return 0.65-(fat-80)/10*0.35
    return max(0.10,0.30-(fat-90)/10*0.20)

def simulate_3y(params, do_strategy=None, init_cash=50000, max_months=36):
    p=dict(params)
    for k,v in {"B1":16,"B24":5,"B25":50,"B13":1000,"B10":3,"B14":60,"B15":7}.items(): p.setdefault(k,v)
    B1,B24,B25,B13,B10,B14,B15=p["B1"],p["B24"],p["B25"],p["B13"],p["B10"],p["B14"],p["B15"]
    c={"B1":B1,"B2":0,"B3":0,"B4":2,"B5":0,"B6":0,"B7":0,"B8":0,"B9":0,"B10":B10,"B11":0,"B12":0,
       "B13":B13,"B14":B14,"B15":B15,"B21":0.8,"B24":B24,"B25":B25,"FAT":40,"EMP":0,"BRAND":0}
    cash=init_cash; profits=[]; fat_trace=[]; brand_trace=[]; emp_trace=[]
    for month in range(max_months):
        if do_strategy: do_strategy(c,month,p)
        pp=c
        c["B9"]=round(pp["B24"]*1200*(1+pp["B15"]*0.15*max(0,1-pp["B24"]*0.08)))
        ph=max(1,min(math.floor(pp["B14"]*25),pp["B24"]*600)+max(0,round((2-c["B4"])*200)))
        c["B3"]=max(0,round(ph*sk(c["FAT"])))
        c["B4"]=max(0.1,max(0.1,2-c["B3"]*0.0002)*(1-c["EMP"]*0.002))
        pb=1+(20-pp["B1"])*0.15 if pp["B1"]<20 else max(0.6,1-(pp["B1"]-20)*0.03)
        area_leverage=1+pp["B14"]/100
        base_traffic=round(250*pp["B15"]); brand_bonus=round(c["BRAND"]*1.5)
        marketing=round(math.sqrt(max(0,pp["B13"]))*12)
        tr=round((base_traffic+brand_bonus)*pb)+round(marketing*area_leverage)
        ma=max(1,10+pp["B15"]*1.2+c["BRAND"]*0.3+c["B21"]*4)
        retention=0.5+(ma-pp["B1"])/ma*0.4 if pp["B1"]<=ma else max(0.05,0.5*ma/pp["B1"])
        c["B2"]=max(0,round(tr*retention))
        c["B5"]=max(0,round(pp["B14"]*pp["B15"]*max(2,20-pp["B14"]*0.05)))
        pp2=c["B9"]/max(c["B3"],1); bl=3+pp["B15"]*0.4
        ps=0.7+min((pp2-bl)/(bl*2),0.3) if pp2>=bl else pp2/bl*0.7
        c["B21"]=round(min(1,max(0,ps-max(0,c["B3"]/ph-0.8)*1.5))*1000)/1000
        c["B12"]=round(pp["B10"]*(1-min(0.5,c["B3"]*0.00008))*100)/100
        c["B11"]=c["B4"]+c["B3"]*0.002
        c["B6"]=min(c["B2"],c["B3"]); c["B7"]=c["B6"]*pp["B1"]
        training_cost=pp["B25"]*pp["B24"]+round(0.05*pp["B24"]*1500)
        c["B8"]=round(c["B7"]-(c["B12"]+1+c["B4"])*c["B3"]-c["B5"]-c["B9"]-pp["B13"]-training_cost)
        profit=c["B8"]; cash+=profit; profits.append(profit)
        fat_trace.append(c["FAT"]); brand_trace.append(c["BRAND"]); emp_trace.append(c["EMP"])
        if cash<0: return round(sum(profits)),profits,True,cash,month+1,fat_trace,brand_trace,emp_trace
        ph2=max(1,min(math.floor(pp["B14"]*25),pp["B24"]*600)+max(0,round((2-c["B4"])*200)))
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
        decay_base=max(0.02,c["BRAND"]*0.015); growth_mult=max(0.1,1-c["BRAND"]/800)
        brand_growth=c["B21"]*30; brand_decay=c["BRAND"]*decay_base
        brand_net=brand_growth*growth_mult-brand_decay-shortage_rate*10
        c["BRAND"]=max(0,round(c["BRAND"]+brand_net))
    return round(sum(profits)),profits,False,cash,max_months,fat_trace,brand_trace,emp_trace


# ===== 1. 疲劳振荡验证 =====
def idle(c,m,p): pass

print("🔥"*32)
print("  VFinal — 数学模型最终验证")
print("🔥"*32)

print(f"\n{'='*65}")
print(f"  1. 疲劳振荡分析 (FAT 36个月走势)")
print(f"{'='*65}")

strategies = [
    ("🏭 真·大厂 (8人/150m²)", [("B1",15),("B24",8),("B25",200),("B13",3000),("B14",150)]),
    ("🏠 社区精酿 (2人/50m²)", [("B1",20),("B24",2),("B25",100),("B13",500),("B14",50)]),
    ("✨ 高奢 (3人/80m²)", [("B1",25),("B24",3),("B25",500),("B13",5000),("B14",80)]),
    ("💀 自杀 (20人/300m²/0培训)", [("B1",35),("B24",20),("B25",0),("B13",0),("B14",300)]),
]

for name, params_list in strategies:
    params = dict(params_list)
    total, profits, bankrupt, cash, n, fats, brands, emps = simulate_3y(params, idle)
    y1_fat = round(sum(fats[0:12])/12) if len(fats)>=12 else 0
    y3_fat = round(sum(fats[-12:])/12) if len(fats)>=12 else 0
    fat_range = max(fats)-min(fats) if len(fats)>0 else 0
    fat_end = fats[-1] if len(fats)>0 else 0
    
    # 疲劳振荡特征
    changes = sum(1 for i in range(1,len(fats)) if abs(fats[i]-fats[i-1])>=5)
    print(f"\n  {name}:")
    print(f"    FAT走势: {fats[0]:>2d}→{fats[5] if len(fats)>5 else '-'}>...→{fat_end:>2d}  (范围 {min(fats)}-{max(fats)}, 大幅波动{changes}次)")
    print(f"    年均FAT: Y1={y1_fat}  Y3={y3_fat}")
    print(f"    破产: {'是 (第'+str(n)+'月)' if bankrupt else '否'}")
    if not bankrupt:
        print(f"    BRAND终值: {brands[-1] if len(brands)>0 else 0}")


# ===== 2. 破产速度测试 =====
print(f"\n{'='*65}")
print(f"  2. 破产速度 — 错误决策多久死？")
print(f"{'='*65}")

death_scenarios = [
    ("💀 20人/300m²/0培训/0营销/¥35", {"B1":35,"B24":20,"B25":0,"B13":0,"B14":300}),
    ("💀 8人/150m²/0培训/0营销/¥5", {"B1":5,"B24":8,"B25":0,"B13":0,"B14":150}),
    ("💀 3人/50m²/¥1000培训/¥10000营销/¥5", {"B1":5,"B24":3,"B25":1000,"B13":10000,"B14":50}),
    ("💀 3人/50m²/¥1000培训/¥10000营销/¥40", {"B1":40,"B24":3,"B25":1000,"B13":10000,"B14":50}),
]

for name, params in death_scenarios:
    total, profits, bankrupt, cash, n, fats, brands, emps = simulate_3y(params, idle, init_cash=50000)
    months_survived = n if bankrupt else 36
    print(f"  {name:50s} → 存活 {months_survived:2d} 个月  {'💀'+str(months_survived)+'月破产' if bankrupt else '✅存活3年'}  期末现金={cash:>+8,}")


# ===== 3. 半聪明玩家测试 =====
print(f"\n{'='*65}")
print(f"  3. 半聪明玩家 — 不全对也不全错")
print(f"{'='*65}")

def half_smart_factory(c,m,p):
    """只做一半正确决策"""
    if m==0: c["B1"]=15;c["B24"]=6;c["B25"]=100;c["B13"]=1500;c["B14"]=100
    if m==6:c["B13"]=3000  # 第6个月加营销但忘了加人
    if m==12:c["B24"]=8;c["B14"]=120  # 第12个月才想起来扩产
    if m==18:c["B13"]=5000  # 再加营销

def half_smart_luxury(c,m,p):
    """高奢忘做培训"""
    if m==0: c["B1"]=25;c["B24"]=3;c["B25"]=0;c["B13"]=5000;c["B14"]=80
    if m==6:c["B1"]=28  # 过早提价
    if m==12:c["B13"]=3000  # 反而减营销了

def lazy_community(c,m,p):
    """社区店躺平不扩张"""
    if m==0: c["B1"]=20;c["B24"]=2;c["B25"]=0;c["B13"]=0;c["B14"]=50
    # 什么都不做，躺3年

for name, fn in [
    ("🏭 半聪明大厂 (扩产滞后)", half_smart_factory),
    ("✨ 半聪明高奢 (忘培训+过早提价)", half_smart_luxury),
    ("🏠 躺平社区 (0培训0营销)", lazy_community),
]:
    total, profits, bankrupt, cash, n, fats, brands, emps = simulate_3y({}, fn)
    y1 = sum(profits[0:12])
    y2 = sum(profits[12:24]) if len(profits)>=24 else 0
    y3 = sum(profits[24:36]) if len(profits)>=36 else 0
    status = "💀破产" if bankrupt else "✅存活"
    print(f"  {name:45s} {y1:>+8,} {y2:>+8,} {y3:>+8,}  3年={total:>+8,}  {status}")


# ===== 4. 参数敏感性分析 =====
print(f"\n{'='*65}")
print(f"  4. 参数敏感性 — 哪个参数对利润影响最大？")
print(f"{'='*65}")

# 大厂基准
base = {"B1":16,"B24":8,"B25":200,"B13":3000,"B10":3,"B14":150,"B15":7}
base_total,_,_,_,_,_,_,_ = simulate_3y(base)

print(f"  大厂基准 (8人/150m²/¥16/¥3000营销): {base_total:>+8,}")
print(f"  {'参数变化':40s} {'利润变化':>12s} {'影响':>8s}")
print(f"  {'-'*60}")

tests = [
    ("售价 ¥15→¥18", {"B1":18}),
    ("人数 8→6", {"B24":6}),
    ("培训 ¥200→¥0", {"B25":0}),
    ("培训 ¥200→¥500", {"B25":500}),
    ("营销 ¥3000→¥1000", {"B13":1000}),
    ("营销 ¥3000→¥8000", {"B13":8000}),
    ("面积 150→100", {"B14":100}),
    ("面积 150→200", {"B14":200}),
    ("面积 150→250", {"B14":250}),
]

for desc, change in tests:
    p = dict(base)
    p.update(change)
    t,_,b,_,_,_,_,_ = simulate_3y(p)
    diff = t - base_total
    pct = diff / abs(base_total) * 100 if base_total != 0 else 0
    print(f"  {desc:40s} {diff:>+10,}  ({pct:>+.0f}%)")


# ===== 5. 路线最终分离 =====
print(f"\n{'='*65}")
print(f"  5. 各路线最佳参数 (严格分离)")
print(f"{'='*65}")

# 纯大厂空间 (B14≥100, B24≥6, B1≤20)
factory_space = {"B1":[15,16,18],"B24":[6,8,10,12],"B25":[100,200,300],"B13":[2000,3000,5000,8000],"B10":[3],"B14":[100,150,200,250],"B15":[7]}
# 纯高奢 (B13≥3000, B24≤3, B1≥22)
luxury_space = {"B1":[22,25,28,30],"B24":[2,3],"B25":[200,400,600],"B13":[3000,5000,8000],"B10":[3],"B14":[60,80],"B15":[7]}
# 纯社区 (B14≤60, B13≤1000, B24≤3)
community_space = {"B1":[16,18,20,22],"B24":[2,3],"B25":[0,50,100],"B13":[0,500,1000],"B10":[3],"B14":[40,50,60],"B15":[7]}

for label, space in [
    ("🏭 大厂 (B14≥100, B24≥6, B1≤20)", factory_space),
    ("✨ 高奢 (B13≥3000, B24≤3, B1≥22)", luxury_space),
    ("🏠 社区 (B14≤60, B13≤1000, B24≤3)", community_space),
]:
    keys = list(space.keys())
    best_profit = -999999; best_params = None
    count=0
    for vals in itertools.product(*[space[k] for k in keys]):
        params = dict(zip(keys, vals))
        t,_,b,_,_,_,_,_ = simulate_3y(params)
        count+=1
        if t>best_profit and not b:
            best_profit=t; best_params=dict(params)
    alive = sum(1 for vals in itertools.product(*[space[k] for k in keys]) for params in [dict(zip(keys, vals))] for t,_,b,_,_,_,_,_ in [simulate_3y(params)] if not b)
    total = count
    p = best_params
    print(f"\n  {label}:")
    print(f"    搜索 {count} 组合, {alive}/{total} 存活")
    print(f"    最佳: ¥{p['B1']:>2d}/ {p['B24']}人/ ¥{p['B25']}培训/ ¥{p['B13']}营销/ {p['B14']}m²")
    print(f"    3年利润: {best_profit:>+8,}  (年均 {best_profit//3:,})")


print(f"\n{'='*65}")
print(f"  ✅ 数学建模验证完毕")
print(f"{'='*65}")
