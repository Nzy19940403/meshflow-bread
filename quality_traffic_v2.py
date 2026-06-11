# -*- coding: utf-8 -*-
import math, random
random.seed(42)
S=[0.85,1.10,0.95,1.00,1.00,0.90,0.85,0.85,1.25,1.10,1.00,1.30]
def sk(f):
    if f<80:return 1.0
    if f>=100:return 0.1
    t=(f-80)/20;return 1.0-t*t*(3-2*t)*0.9
def pb(b1):
    return(1+(20-b1)*0.15)if b1<20 else max(0.6,1-(b1-20)*0.03)
def sim(seq,f=40,e=0,b=0,wb=False):
    FT,EM,BR,WB=f,e,b,wb;R=[]
    for m,p in enumerate(seq):
        B1,B24,B25,B13,B14,B15,B10,B26=p;sz=S[m%12];pp=pb(B1)
        B9=round(B24*B26*(1+B15*0.12*max(0,1-B24*0.06)))
        if B24>8:B9+=round(B24*B26*0.10)
        ur=max(6,50-B14*0.12)
        if B15<=4:ur*=0.88
        if B15>=8:ur*=1.25
        B5=max(0,round(B14*B15*ur))
        wf=0.2+1.6*min(B26,10000)/10000;le=1800 if B14>=150 else 1500
        pc=max(1,min(B14*35,B24*le)*wf);B3=max(0,round(pc*sk(FT)))
        wF=max(0.3,1.5-B26/5000);eb=(1-EM*0.003)if EM>50 else(1-EM*0.002)
        B4=round(max(0.1,max(0.1,2-B3*0.0002)*eb*wF),2)
        b28b=max(0.2,min(1.0,B10/5.0));b28s=min(0.25,(B3-3000)*0.00008)if B3>3000 else 0
        B28=round(min(1.0,b28b+b28s)*1000)/1000;bad=B28<0.40;qp=max(0,(B26-4000)/500)
        rb=(350+400*min(B15,6))*pp;rbr=round(BR*4.0)*pp
        rm=round(math.sqrt(max(0,B13))*9)*(1+min(B14,150)/120);rt=round(rb+rbr+rm)
        ma_r=max(1,12+B15*1.8+BR*0.4+B28*6+qp)
        rcv=min(0.90,0.50+(ma_r-B1)/ma_r*0.40)if B1<=ma_r else max(0.05,0.50*ma_r/B1)
        rd=max(0,round(rt*rcv*sz));td=0
        if B15>=5:
            tb=(B15-4)*500*pp;tm=round(math.sqrt(max(0,B13))*5)if B15>=7 else 0;tt=round(tb+tm)
            ma_t=max(1,8+B15*2.5+B13/2500+qp)
            tcv=min(0.80,0.35+(ma_t-B1)/ma_t*0.35)if B1<=ma_t else max(0.03,0.35*ma_t/B1)
            td=max(0,round(tt*tcv*sz))
        B2=rd+td;rs=min(rd,B3);ts=min(td,B3-rs);B6=rs+ts
        B7=B6*B1+round(B6*B1*0.20);B12=round(B10*(1-min(0.45,B3*0.00007)),2)
        if B3>2500:B12=round(B12*(1-min(0.20,(B3-2500)*0.00008)),2)
        pkg=round(B1*0.12);cr=round((B12+pkg+B4)*B6*(1.15 if B15>=7 else 1.0))
        uc=round(B14*25+B24*180);eqc=round(B14*15+B24*80);ms=round(0.04*B24*1500)
        B8=round(B7-cr-B5-B9-B13-B25*B24-ms-uc-eqc)
        ppv=B9/max(B3,1);bl=3+B15*0.35
        ps=round(0.7+min((ppv-bl)/(bl*2),0.3)if ppv>=bl else ppv/bl*0.7,3)
        ov=round(max(0,B6/max(pc,1)-(0.8+0.2*ps))*1.5,3);B21=round(min(1,max(0,ps-ov)),3)
        ur_v=B6/max(pc,1);d=3
        if B25==0 and ur_v>0.7:d+=5
        elif B25==0:d+=2
        if ur_v>0.8:d+=(ur_v-0.8)*40;d-=B25*0.025
        ff=FT/40 if FT<40 else 1
        if B21<0.5:d-=(B21-0.5)*12*ff
        if B9/max(B24,1)>1500:d-=(B9/B24-1500)*0.004*ff
        FT=max(10,min(100,round(FT+d)))
        sr=max(0,(rd-rs)/max(1,rd));gr=B21*20;gm=max(0.05,1-BR/400)
        qd=0;qc=999
        if bad:gap=0.40-B28;qd=gap*25;qc=50 if B28>=0.30 else 25
        nd=BR*0.018;nb=max(0,round(BR+gr*gm-nd-qd-sr*8))
        if not bad and WB:nb=max(0,round(BR+gr*gm*0.4-nd-sr*8))
        if nb>qc:nb=qc
        WB=bad;BR=nb;EM=min(200,round(EM+max(1,10-round(EM*0.05))))
        R.append({'B8':B8,'BR':BR,'B28':B28,'tp':round(td/max(B2,1)*100),'reg':rd,'tour':td})
    return R,sum(r['B8']for r in R)

print("="*100)
print(" 品质惩罚+客流分化 v2")
print("="*100)
print("\nC:作死->救回 前6月B10=1后6月B10=5")
s=[(22,3,100,1000,60,3,1 if m<6 else 5,4000)for m in range(12)]
r,t=sim(s)
print(" 利润:"+str([d['B8']for d in r]))
print(" 品牌:"+" -> ".join(str(d['BR'])for d in r));print(" 年:%d"%t)
sg=[(22,3,100,1000,60,3,4,4000)for _ in range(24)]
rg,tg=sim(sg);print(" 对照一直B10=4:24月终品牌%d"%rg[-1]['BR'])
print("\nD:割韭菜 B15=9 B10=1")
s=[(28,2,200,8000,80,9,1,5000)for _ in range(12)];r,t=sim(s)
print(" 利润:"+str([d['B8']for d in r]))
print(" 品牌:"+" -> ".join(str(d['BR'])for d in r))
print(" 旅游M1=%d%% M12=%d%% 年:%d 品牌天花板:%d"%(r[0]['tp'],r[-1]['tp'],t,r[-1]['BR']))
print("\nE:高奢正常 B15=9 B10=5")
s=[(32,2,300,8000,80,9,5,5500)for _ in range(12)];r,t=sim(s)
print(" 利润:"+str([d['B8']for d in r]))
print(" 品牌:"+" -> ".join(str(d['BR'])for d in r))
print(" 旅游M1=%d%% M12=%d%% 年:%d"%(r[0]['tp'],r[-1]['tp'],t))
print("\nF:社区24月 B10=4 vs B10=1")
for lb,bb in[("好",4),("坏",1)]:
    s=[(22,3,100,1000,60,3,bb,4000)for _ in range(24)];r,t=sim(s)
    y1=sum(d['B8']for d in r[:12]);y2=sum(d['B8']for d in r[12:])
    print(" %s:Y1=%d Y2=%d 终品牌%d 稳态%d"%(lb,y1,y2,r[-1]['BR'],r[-1]['B8']))
print("\nG:大厂 B15=1 B14=255")
s=[(16,10,100,4000,255,1,2,3500)for _ in range(12)];r,t=sim(s)
print(" 利润:"+str([d['B8']for d in r]));print(" 年:%d"%t)
print("\n"+"="*100)
rr={'社区':[(18,28,2),(2,5,1),(0,200,100),(0,4000,2000),(50,90,10),(2,5,1),(3,5,1),(3500,5000,500)],'大厂':[(12,18,2),(10,18,2),(0,200,100),(4000,12000,4000),(180,280,25),(1,4,1),(2,4,1),(2500,4000,500)],'高奢':[(26,36,2),(2,5,1),(200,600,200),(3000,12000,3000),(70,120,25),(7,10,1),(4,6,1),(4500,6500,500)]}
for nm,rg in rr.items():
    best=[-1e9,None];n=0
    for B1 in range(*rg[0]):
     for B24 in range(*rg[1]):
      for B25 in range(*rg[2]):
       for B13 in range(*rg[3]):
        for B14 in range(*rg[4]):
         for B15 in range(*rg[5]):
          for B10 in range(*rg[6]):
           for B26 in range(*rg[7]):
            n+=1;s=[(B1,B24,B25,B13,B14,B15,B10,B26)for _ in range(12)];_,tv=sim(s)
            if tv>best[0]:best=[tv,(B1,B24,B25,B13,B14,B15,B10,B26)]
    p=best[1]
    print(" %s %d组:年%d|B1=%d B24=%d B14=%d B15=%d B10=%d B26=%d"%(nm,n,best[0],p[0],p[1],p[4],p[5],p[6],p[7]))
print("\nv2完成")
