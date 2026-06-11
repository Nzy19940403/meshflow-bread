# -*- coding: utf-8 -*-
"""大厂批发渠道建模 + 三条路线验证"""
import math, random, itertools
random.seed(42)
S=[0.85,1.10,0.95,1.00,1.00,0.90,0.85,0.85,1.25,1.10,1.00,1.30]
def sk(f):
    if f<80:return 1.0
    if f>=100:return 0.1
    t=(f-80)/20;return 1.0-t*t*(3-2*t)*0.9
def pb(b1):
    return(1+(20-b1)*0.15)if b1<20 else max(0.6,1-(b1-20)*0.03)
def sim(p):
    B1,B24,B25,B13,B14,B15,B10,B26=p
    F,E,BR=40,0,0;B21=0.8;R=[]
    for m in range(12):
        sz=S[m];pp=pb(B1)
        B9=round(B24*B26*(1+B15*0.15*max(0,1-B24*0.08)))
        B5=max(0,round(B14*B15*max(8,45-B14*0.10)))
        wf=0.2+1.6*min(B26,10000)/10000
        pc=max(1,min(B14*35,B24*1500)*wf)
        B3=max(0,round(pc*sk(F)))
        wF=max(0.5,1.5-B26/5000);eb=(1-E*0.003)if E>50 else(1-E*0.002)
        B4=round(max(0.1,max(0.1,2-B3*0.0002)*eb*wF),2)
        qp=max(0,(B26-4000)/500)
        # 零售客流
        bC=round(BR*3);bP=0 if BR>300 else(1-(BR-100)/200)if BR>100 else 1
        bd=round((500+500*B15)*pp)+round(bC*bP)
        mt=round(math.sqrt(max(0,B13))*10)*(1+min(B14,200)/100)
        rt=round(bd+mt);ma_r=max(1,15+B15*2+BR*0.5+B21*3+qp)
        rcv=min(0.9,0.5+(ma_r-B1)/ma_r*0.4)if B1<=ma_r else max(0.05,0.5*ma_r/B1)
        rd=max(0,round(rt*rcv*sz))
        # === 批发渠道 (大厂专属 B14>130) ===
        wd,wr=0,0
        if B14>130:
            wvol=round((B14-130)*50)  # 每超额m²=50批发单位/月
            wsz=1+(sz-1)*0.25  # 批发合同受季节影响只有零售的25%
            wd=max(0,round(wvol*wsz))  # 批发需求
            # 批发收入 (合同价=零售×0.6, 低包装费)
            wr=round(wd*B1*0.60)
            # 批发成本单独算 (后面从B8扣)
        B2=rd+wd;rs=min(rd,B3);ts=min(wd,B3-rs);B6=rs+ts
        B7=B6*B1+round(B6*B1*0.20)
        # 零售营收(含饮品)+批发营收
        rev_retail=rs*B1+round(rs*B1*0.20)
        rev_total=rev_retail+round(ts*B1*0.60)
        B12=round(B10*(1-min(0.5,B3*0.00008))*100)/100
        # 批发成本远低于零售(B10原料×0.5折+简单包装¥0.5/个)
        pkg=round(B1*0.15)
        cogs_retail=round((B12+pkg+B4)*rs)
        cogs_ws=round(ts*B10*0.50+ts*0.5)
        cogs=cogs_retail+cogs_ws
        uc=round(B14*25+B24*200);eq=2000;trn=B25*B24;ms=round(0.05*B24*1500)
        B8=round(rev_total-cogs-B5-B9-B13-trn-ms-uc-eq)
        ppv=B9/max(B3,1);bl=3+B15*0.4
        ps=0.7+min((ppv-bl)/(bl*2),0.3)if ppv>=bl else ppv/bl*0.7
        ut=B3/max(pc,1);ov=max(0,ut-(0.8+0.2*ps))*1.5
        B21=round(min(1,max(0,ps-ov))*1000)/1000
        ph=pc+max(0,round((2-B4)*100));ur=B3/max(ph,1);d=3
        if B25==0 and ur>0.7:d+=5
        elif B25==0:d+=2
        if ur>0.8:d+=(ur-0.8)*40;d-=B25*0.03
        ff=F/40 if F<40 else 1
        if B21<0.5:d-=(B21-0.5)*15*ff
        if B9/max(B24,1)>1500:d-=(B9/B24-1500)*0.005*ff
        F=max(10,min(100,round(F+d)))
        sr=max(0,(rd+B3-rs-B3)/max(1,rd));gr=B21*20;dc=BR*0.02;gm=max(0.05,1-BR/400)
        BR=max(0,round(BR+gr*gm-dc-sr*10))
        E=min(200,round(E+max(1,10-round(E*0.05))))
        if m<3 or m>=9:
            R.append({'m':m+1,'B8':B8,'retail':rd,'ws':wd,'ws_rev':round(ts*B1*0.60),'total_rev':rev_total,'BR':BR})
        else:
            R.append({'B8':B8})
    return [r['B8']for r in R],sum(r['B8']for r in R),R

print("="*120)
print("  === 大厂批发渠道验证 + 三路线 === ")
print("="*120)

# 大厂最优搜索
print("\n  --- 大厂路线空间搜索 (B14>130带批发) ---")
best=[-1e9,None,None];n=0
for B1 in range(12,20,2):
 for B24 in range(10,20,2):
  for B25 in[0,100,200]:
   for B13 in range(4000,14000,4000):
    for B14 in range(180,300,25):
     for B15 in range(1,5,1):
      for B10 in range(2,5,1):
       for B26 in range(2500,4500,500):
        n+=1;m,ts,R=sim((B1,B24,B25,B13,B14,B15,B10,B26))
        if ts>best[0]:best=[ts,(B1,B24,B25,B13,B14,B15,B10,B26),R]
p=best[1]
print("  搜索%d组:"%n)
print("  最优年利润: %d (月均 %.0f)"%(best[0],best[0]/12))
print("  参数: B1=%d B24=%d人 B25=%d B13=%d B14=%dm2 B15=%d* B10=%d B26=%d"%(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7]))
print("  逐月: %s"%[d['B8']for d in best[2]])

# 看几个月的批发占比
print("  关键月份:")
for d in best[2]:
    if isinstance(d,dict)and'ws'in d and d['ws']>0:
        print("    M%d: 零售%d+批发%d=%d 批发收入%d 总营收%d 利润%d"%
              (d['m'],d['retail'],d['ws'],d['retail']+d['ws'],d['ws_rev'],d['total_rev'],d['B8']))

# 典型大厂参数详细
print("\n  --- 典型大厂逐月详情 (B1=16,B14=255,B15=1) ---")
m,ts,R=sim((16,10,100,8000,255,1,2,3000))
print("  年:%d 逐月:%s"%(ts,[d['B8']for d in R]))
for d in R[:3]:
    if isinstance(d,dict)and'ws'in d:
        print("    M%d:零售%d批%d 批收入%d 利润%d"%(d['m'],d['retail'],d['ws'],d['ws_rev'],d['B8']))

# 三条线同时搜索
print("\n"+"="*120)
print("  三条路线最优搜索 (社区+大厂带批发+高奢)")
print("="*120)
# 降低搜索精度提速
routes={
    '社区':[(18,28,2),(2,5,1),(0,200,100),(0,4000,2000),(50,90,10),(2,5,1),(3,5,1),(3500,5000,500)],
    '大厂带批发':[(12,18,2),(10,18,2),(0,200,100),(4000,12000,4000),(180,280,25),(1,4,1),(2,4,1),(2500,4000,500)],
    '高奢':[(26,36,2),(2,5,1),(200,600,200),(3000,12000,3000),(70,120,25),(7,10,1),(4,6,1),(4500,6500,500)],
}
results=[]
for nm,rg in routes.items():
    best=[-1e9,None];n=0
    for B1 in range(*rg[0]):
     for B24 in range(*rg[1]):
      for B25 in range(*rg[2]):
       for B13 in range(*rg[3]):
        for B14 in range(*rg[4]):
         for B15 in range(*rg[5]):
          for B10 in range(*rg[6]):
           for B26 in range(*rg[7]):
            n+=1;_,tv,_=sim((B1,B24,B25,B13,B14,B15,B10,B26))
            if tv>best[0]:best=[tv,(B1,B24,B25,B13,B14,B15,B10,B26)]
    results.append((nm,best[0],best[1],n))
    p=best[1]
    print("  %s %d组:年%d(月%.0f) | B1=%d B24=%d B14=%d B15=%d B10=%d B26=%d"%(nm,n,best[0],best[0]/12,p[0],p[1],p[4],p[5],p[6],p[7]))

print("\n  均衡性:")
profs=[r[1]for r in results]
ratio=max(profs)/max(min(profs),1)
for nm,pf,_,_ in results:print("    %s: %d"%(nm,pf))
print("  最高/最低: %.1f:1 %s"%(ratio,"OK" if ratio<3 else "还要调"))

