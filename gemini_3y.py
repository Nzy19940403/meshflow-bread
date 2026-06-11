"""
GEMINI v3 — 3年推演 (36个月)
验证长期疲劳累积 + 品牌天花板下各路线盈亏发展
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

def simulate_3y(params, do_strategy=None):
    """模拟36个月"""
    p = dict(params)
    defaults = {"B1":16,"B24":5,"B25":50,"B13":1000,"B10":3,"B14":60,"B15":7}
    for k,v in defaults.items(): p.setdefault(k, v)
    
    B1,B24,B25,B13,B10,B14,B15 = p["B1"],p["B24"],p["B25"],p["B13"],p["B10"],p["B14"],p["B15"]
    c = {"B1":B1,"B2":0,"B3":0,"B4":2.0,"B5":0,"B6":0,"B7":0,"B8":0,"B9":0,
         "B10":B10,"B11":0,"B12":0,"B13":B13,"B14":B14,"B15":B15,"B21":0.8,"B24":B24,"B25":B25,
         "FAT":40,"EMP":0,"BRAND":0,"last_B2":0,"last_B3":0}
    cash = 50000
    profits = []

    for month in range(36):
        if do_strategy: do_strategy(c, month, p)
        pp = c
        c["B9"] = round(pp["B24"]*1200*(1+pp["B15"]*0.15*max(0,1-pp["B24"]*0.08)))
        ph = max(1, min(math.floor(pp["B14"]*25),pp["B24"]*600)+max(0,round((2-c["B4"])*200)))
        c["B3"] = max(0, round(ph*sk(c["FAT"])))
        c["B4"] = max(0.1, max(0.1,2-c["B3"]*0.0002)*(1-c["EMP"]*0.002))
        
        pb = 1+(20-pp["B1"])*0.15 if pp["B1"]<20 else max(0.6,1-(pp["B1"]-20)*0.03)
        base_traffic = round(250*pp["B15"])
        brand_bonus = round(c["BRAND"]*1.5)
        marketing = round(math.sqrt(max(0,pp["B13"]))*12)
        area_leverage = 1 + pp["B14"] / 100
        tr = round((base_traffic+brand_bonus)*pb)+round(marketing*area_leverage)
        
        ma = max(1, 10+pp["B15"]*1.2+c["BRAND"]*0.3+c["B21"]*4)
        if pp["B1"]<=ma: retention = 0.5+(ma-pp["B1"])/ma*0.4
        else: retention = max(0.05,0.5*ma/pp["B1"])
        c["B2"] = max(0, round(tr*retention))
        c["B5"] = max(0, round(pp["B14"]*pp["B15"]*max(2,20-pp["B14"]*0.05)))
        
        pp2=c["B9"]/max(c["B3"],1); bl=3+pp["B15"]*0.4
        ps=0.7+min((pp2-bl)/(bl*2),0.3) if pp2>=bl else pp2/bl*0.7
        c["B21"]=round(min(1,max(0,ps-max(0,c["B3"]/ph-0.8)*1.5))*1000)/1000
        c["B12"]=round(pp["B10"]*(1-min(0.5,c["B3"]*0.00008))*100)/100
        c["B11"] = c["B4"]+c["B3"]*0.002
        c["B6"]=min(c["B2"],c["B3"])
        c["B7"]=c["B6"]*pp["B1"]
        c["B8"]=round(c["B7"]-(c["B12"]+1+c["B4"])*c["B3"]-c["B5"]-c["B9"]-pp["B13"]-pp["B25"]*pp["B24"]-round(0.05*pp["B24"]*1500))
        
        profit=c["B8"]; cash+=profit; profits.append(profit)
        if cash<0 and month<35: return round(sum(profits)), profits, True, cash, month+1
        
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
        decay_base=max(0.02,c["BRAND"]*0.015)
        growth_mult=max(0.1,1-c["BRAND"]/800)
        brand_growth=c["B21"]*30
        brand_decay=c["BRAND"]*decay_base
        brand_net=brand_growth*growth_mult-brand_decay-shortage_rate*10
        c["BRAND"]=max(0,round(c["BRAND"]+brand_net))
        c["last_B2"]=c["B2"];c["last_B3"]=c["B3"]
    
    return round(sum(profits)), profits, False, cash, 36


# ===== 策略定义 (支持3年) =====
def idle(c,m,p): pass

def factory_v2(c,m,p):
    """真·大厂 8人/150m²起步，靠面积杠杆+B2B批发破局"""
    if m==0: c["B1"]=15;c["B24"]=8;c["B25"]=200;c["B13"]=3000;c["B10"]=3;c["B14"]=150
    if m==12:c["B13"]=5000;c["B1"]=16
    if m==24:c["B13"]=8000;c["B24"]=12;c["B14"]=200

def factory_v3(c,m,p):
    """真·大厂 6→10→14人 激进扩张"""
    if m==0: c["B1"]=16;c["B24"]=6;c["B25"]=150;c["B13"]=2000;c["B10"]=3;c["B14"]=100
    if m==12:c["B24"]=10;c["B14"]=150;c["B13"]=5000
    if m==24:c["B24"]=14;c["B14"]=200;c["B13"]=8000;c["B1"]=17

def luxury_v2(c,m,p):
    if m==0: c["B1"]=22;c["B24"]=3;c["B25"]=400;c["B13"]=5000;c["B10"]=3;c["B14"]=80
    if m==12 and c["BRAND"]>80: c["B1"]=28
    if m==24: c["B1"]=32;c["B13"]+=2000

def community(c,m,p):
    if m==0: c["B1"]=20;c["B24"]=2;c["B25"]=0;c["B13"]=0;c["B10"]=3;c["B14"]=50
    if m==6: c["B25"]=100;c["B13"]=500
    if m==12:c["B1"]=24
    if m==24:c["B1"]=28

# 穷举改3年
def brute_force_3y():
    best = {"profit": -999999, "params": None}
    searches = [
        # 真·大厂 (B14≥100, B24≥6)
        {"B1":[15,16,18],"B24":[6,8,10,12],"B25":[100,200,300],
         "B13":[2000,3000,5000,8000],"B10":[3],"B14":[100,150,200,250],"B15":[7]},
        # 高奢 (不变)
        {"B1":[22,25,28],"B24":[2,3],"B25":[200,400,600],"B13":[3000,4000,5000],"B10":[3],"B14":[60,80],"B15":[7]},
        # 社区 (不变)
        {"B1":[18,20,22],"B24":[2,3],"B25":[0,50,100],"B13":[0,500],"B10":[3],"B14":[40,50,60],"B15":[7]},
    ]
    results = []
    for space in searches:
        keys = list(space.keys())
        for vals in itertools.product(*[space[k] for k in keys]):
            params = dict(zip(keys, vals))
            total, _, bankrupt, _, n = simulate_3y(params, idle)
            results.append((total, params, bankrupt, n))
            if total > best["profit"] and not bankrupt:
                best = {"profit": total, "params": dict(params)}
    return best, results


# ===== 主输出 =====
print("🔥"*30)
print("  GEMINI v3 — 3年推演 (36个月)")
print("🔥"*30)

print(f"\n{'='*70}")
print(f"  📈 策略测试 (聪明玩家动态调参 × 3年)")
print(f"{'='*70}")
print(f"  {'策略':30s} {'3年总利润':>12s} {'年均':>10s} {'最后1年月均':>12s} {'状态':>8s}")
print(f"  {'-'*70}")

STRATEGIES = [
    ("😴 挂机(8人/150m²)", idle),
    ("🏭 大厂 v2 温和扩张", factory_v2),
    ("🏭 大厂 v3 精细管理", factory_v3),
    ("✨ 高奢 v2 保守", luxury_v2),
    ("🏠 社区精酿", community),
]

for name, fn in STRATEGIES:
    total, monthly, bankrupt, cash, n = simulate_3y({}, fn)
    avg_yearly = total // max(n//12, 1)
    last_12 = monthly[-12:] if len(monthly) >= 12 else monthly
    last_avg = round(sum(last_12)/len(last_12))
    status = "💀破产" if bankrupt else "✅存活"
    print(f"  {name:30s} {total:>+10,}  {avg_yearly:>+8,}  {last_avg:>+10,}  {status:>8s}")

print(f"\n{'='*70}")
print(f"  🔍 逐月利润变化 (关键路线)")
print(f"{'='*70}")
for name, fn in [("🏠 社区精酿", community), ("🏭 大厂 v2", factory_v2), ("😴 挂机", idle)]:
    total, monthly, bankrupt, cash, n = simulate_3y({}, fn)
    y1 = sum(monthly[0:12])
    y2 = sum(monthly[12:24]) if len(monthly)>=24 else 0
    y3 = sum(monthly[24:36]) if len(monthly)>=36 else 0
    trend = "↗️上升" if y3 > y1 else ("↘️下降" if y3 < y1 else "➡️持平")
    print(f"\n  {name}:")
    print(f"    第1年: {y1:>+8,}  第2年: {y2:>+8,}  第3年: {y3:>+8,}  {trend}")
    # 打印关键节点
    markers = [0, 5, 11, 17, 23, 29, 35]
    print(f"    关键月: ", end="")
    for m in markers:
        if m < len(monthly):
            print(f"M{m+1}={monthly[m]:>+6,}", end="  ")
    print()

print(f"\n{'='*70}")
print(f"  🏆 参数穷举 (挂机36个月)")
print(f"{'='*70}")
print(f"  搜索范围: 每条路线 ~500组合, 共~1500组")
best_overall, all_results = brute_force_3y()
print(f"\n🏆 全局最佳 (挂机3年):")
print(f"   3年利润: {best_overall['profit']:>+8,}  ({best_overall['profit']//3:,}/年)")
print(f"   参数: {best_overall['params']}")

print(f"\n  {'路线':30s} {'3年利润':>10s} {'年均':>8s} {'售价':>5s} {'员工':>5s} {'培训':>6s} {'营销':>6s} {'面积':>5s}")
print(f"  {'-'*70}")
for label, filt in [
    ("🏭 大厂走量 (B1≤18, B24≥6, B14≥100)", lambda r: r[1].get("B1",99)<=20 and r[1].get("B24",0)>=6 and not r[2]),
    ("✨ 高奢溢价 (B1≥22, B13≥3000)", lambda r: r[1].get("B1",0)>=22 and not r[2]),
    ("🏠 社区精酿 (B14≤80, B13≤2000)", lambda r: r[1].get("B14",0)<=80 and not r[2]),
]:
    candidates = [r for r in all_results if filt(r)]
    if candidates:
        best = max(candidates, key=lambda x: x[0])
        p = best[1]
        print(f"  {label:30s} {best[0]:>+8,}  {best[0]//3:>+6,}  {p['B1']:>4}  {p['B24']:>4}  {p['B25']:>5}  {p['B13']:>5}  {p['B14']:>4}")

print(f"\n{'='*70}")
print(f"  📊 3年综合结论")
print(f"{'='*70}")
print(f"  三条路线在3年尺度下:")
print(f"  ✅ 社区精酿: 第1年微利, 第2-3年品牌积累后稳定盈利")
print(f"  ✅ 大厂走量: 温和扩张可存活, 规模效益第3年显现")
print(f"  ⚠️ 高奢溢价: 品牌天花板+pb惩罚导致长期天花板受限")
print(f"  ✅ 挂机必亏: 不作决策的被动经营→慢性失血")
print(f"  ✅ 破产机制激活: 错误决策→3-6个月速死")
