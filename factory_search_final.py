# -*- coding: utf-8 -*-
import math
S=[0.85,1.10,0.95,1.00,1.00,0.90,0.85,0.85,1.25,1.10,1.00,1.30]
def sk(f):
    if f<80:return 1.0
    if f>=100:return 0.1
    t=(f-80)/20;return 1.0-t*t*(3-2*t)*0.9
def pbF(b1):
    return(1+(20-b1)*0.15)if b1<20 else max(0.6,1-(b1-20)*0.03)

def sim(p):
    B1,B24,B25,B13,B14,B15,B10,B26=p;F,E,BR=40,0,0;B21=0.8;R=[]
    for m in range(12):
        sz=S[m];B9=round(B24*B26*(1+B15*0.15*max(0,1-B24*0.08)))
        B5=max(0,round(B14*B15*max(8,45-B14*0.10)))
        wf=0.2+1.6*min(B26,10000)/10000;pc=max(1,min(B14*35,B24*1500)*wf)
        B3=max(0,round(pc*sk(F)))
        wF=max(0.5,1.5-B26/5000);eb=(1-E*0.003)if E>50 else(1-E*0.002)
        B4=round(max(0.1,max(0.1,2-B3*0.0002)*eb*wF),2)
        b28b=max(0.2,min(1.0,B10/5.0));b28s=min(0.25,(B3-3000)*0.00008)if B3>3000 else 0
        B28=round(min(1.0,b28b+b28s)*1000)/1000
        ppb=pbF(B1);qp=max(0,(B26-4000)/500)
        # retail
        bC=round(BR*3);bP=0 if BR>300 else(1-(BR-100)/200)if BR>100 else 1
        bd=round((500+500*B15)*ppb)+round(bC*bP)
        mt=round(math.sqrt(max(0,B13))*10)*(1+B14/100);rt=round(bd+mt)
        ma_r=max(1,15+B15*2+BR*0.5+B21*3+qp)
        rcv=min(0.9,0.5+(ma_r-B1)/ma_r*0.4)if B1<=ma_r else max(0.05,0.5*ma_r/B1)
        rd=max(0,round(rt*rcv*sz))
        # tourist
        td=0
        if B15>=5:
            tb=(B15-4)*500*ppb
            tm=round(math.sqrt(max(0,B13))*5)if B15>=7 else 0
            tt=round(tb+tm)
            ma_t=max(1,8+B15*2.5+B13/2500+qp)
            tcv=min(0.80,0.35+(ma_t-B1)/ma_t*0.35)if B1<=ma_t else max(0.03,0.35*ma_t/B1)
            td=max(0,round(tt*tcv*sz))
        B2=rd+td;rs=min(rd,B3);ts_=min(td,B3-rs);B6=rs+ts_
        # wholesale
        ws=0;wr=0
        if B14>130:
            wCap=round((B14-130)*50);wSz=1+(sz-1)*0.25
            wDemand=max(0,round(wCap*wSz))
            ws=min(wDemand,max(0,B3-B6));wr=round(ws*B1*0.60)
        B7=B6*B1+round(B6*B1*0.20)+wr
        B12=round(B10*(1-min(0.5,B3*0.00008))*100)/100
        pkg=round(B1*0.15);uc=round(B14*25+B24*200);eq=2000
        trn=B25*B24;ms=round(0.05*B24*1500)
        rcogs=round((B12+pkg+B4)*min(B6,B3))
        wcogs=round(ws*B10*0.50+ws*0.5)if ws>0 else 0
        B8=round(B7-rcogs-wcogs-B5-B9-B13-trn-ms-uc-eq)
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
        sr=max(0,(rd-rs)/max(1,rd));gr=B21*20;dc=BR*0.02;gm=max(0.05,1-BR/400)
        nb=round(BR+gr*gm-dc-sr*10);ceiling=999
        if B28<0.40:gap=0.40-B28;nb-=round(gap*25);ceiling=50 if B28>=0.30 else 25
        if nb>ceiling:nb=ceiling
        BR=max(0,nb);E=min(200,round(E+max(1,10-round(E*0.05))))
        R.append(B8)
    return sum(R)

best_f=[-1e9,None];nf=0
for B1 in range(12,22,2):
 for B24 in range(10,20,2):
  for B25 in[0,100,200]:
   for B13 in range(2000,16000,2000):
    for B14 in range(180,300,20):
     for B15 in range(1,5):
      for B10 in range(2,5):
       for B26 in range(2500,4500,250):
        nf+=1;t=sim((B1,B24,B25,B13,B14,B15,B10,B26))
        if t>best_f[0]:best_f=[t,(B1,B24,B25,B13,B14,B15,B10,B26)]
p=best_f[1];mo=sim(p)/12
print("Factory(%d): %d/yr B1=%d B24=%d B25=%d B13=%d B14=%d B15=%d B10=%d B26=%d | %.0f/mo"%(nf,best_f[0],p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],mo))

best_c=[-1e9,None];nc=0
for B1 in range(18,30,2):
 for B24 in range(2,6):
  for B25 in[0,100,200]:
   for B13 in range(0,6000,2000):
    for B14 in range(50,100,10):
     for B15 in range(2,6):
      for B10 in range(3,6):
       for B26 in range(3500,5500,500):
        nc+=1;t=sim((B1,B24,B25,B13,B14,B15,B10,B26))
        if t>best_c[0]:best_c=[t,(B1,B24,B25,B13,B14,B15,B10,B26)]
p2=best_c[1];mo2=sim(p2)/12
print("Community(%d): %d/yr B1=%d B24=%d B25=%d B13=%d B14=%d B15=%d B10=%d B26=%d | %.0f/mo"%(nc,best_c[0],p2[0],p2[1],p2[2],p2[3],p2[4],p2[5],p2[6],p2[7],mo2))

best_l=[-1e9,None];nl=0
for B1 in range(26,40,2):
 for B24 in range(2,6):
  for B25 in[200,400,600]:
   for B13 in range(3000,15000,3000):
    for B14 in range(70,130,15):
     for B15 in range(7,11):
      for B10 in range(4,7):
       for B26 in range(4500,7000,500):
        nl+=1;t=sim((B1,B24,B25,B13,B14,B15,B10,B26))
        if t>best_l[0]:best_l=[t,(B1,B24,B25,B13,B14,B15,B10,B26)]
p3=best_l[1];mo3=sim(p3)/12
print("Luxury(%d): %d/yr B1=%d B24=%d B25=%d B13=%d B14=%d B15=%d B10=%d B26=%d | %.0f/mo"%(nl,best_l[0],p3[0],p3[1],p3[2],p3[3],p3[4],p3[5],p3[6],p3[7],mo3))

pfs=[best_c[0],best_f[0],best_l[0]]
print("\n=== BALANCE %.1f:1 ==="%(max(pfs)/min(pfs)))
for n,v in[("Community",best_c[0]),("Factory",best_f[0]),("Luxury",best_l[0])]:
    print("  %s: %d/yr (%.0f/mo)"%(n,v,v/1