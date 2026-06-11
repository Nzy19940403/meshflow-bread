import math
S=[0.85,1.10,0.95,1.00,1.00,0.90,0.85,0.85,1.25,1.10,1.00,1.30]
def sk(f):
    if f<80: return 1.0
    if f>=100: return 0.1
    t=(f-80)/20;return 1.0-t*t*(3-2*t)*0.9
def pbf(b1):return(1+(20-b1)*0.15)if b1<20 else max(0.6,1-(b1-20)*0.03)

def run_factory(ws_price, ws_ing, ws_pack):
    best=[-1e9,None,[]]
    for B1 in[16,18,20]:
     for B24 in[10,12,14]:
      for B25 in[0,100]:
       for B13 in[4000,8000,12000]:
        for B14 in[200,225,250,275,300]:
         for B15 in[1,2,3]:
          for B10 in[2,3]:
           for B26 in[2500,3000,3500,4000]:
            F,E,BR,B21=40,0,0,0.8;tot=0;mons=[]
            for m in range(12):
                sz=S[m];B9=round(B24*B26*(1+B15*0.15*max(0,1-B24*0.08)))
                B5=max(0,round(B14*B15*max(8,45-B14*0.10)))
                pc=max(1,min(B14*35,B24*1500)*(0.2+1.6*min(B26,10000)/10000))
                B3=max(0,round(pc*sk(F)))
                wF=max(0.5,1.5-B26/5000);eb=(1-E*0.003)if E>50 else(1-E*0.002)
                B4=round(max(0.1,max(0.1,2-B3*0.0002)*eb*wF),2)
                b28b=max(0.2,min(1.0,B10/5.0))
                b28s=min(0.25,(B3-3000)*0.00008)if B3>3000 else 0
                B28=round(min(1.0,b28b+b28s)*1000)/1000
                ppb=pbf(B1);qp=max(0,(B26-4000)/500)
                bC=round(BR*3);bP=0 if BR>300 else(1-(BR-100)/200)if BR>100 else 1
                bd=round((500+500*B15)*ppb)+round(bC*bP)
                mt=round(math.sqrt(max(0,B13))*10)*(1+B14/100);rt=round(bd+mt)
                ma_r=max(1,15+B15*2+BR*0.5+B21*3+qp)
                rcv=min(0.9,0.5+(ma_r-B1)/ma_r*0.4)if B1<=ma_r else max(0.05,0.5*ma_r/B1)
                rd=max(0,round(rt*rcv*sz))
                td=0
                if B15>=5:
                    tb=(B15-4)*500*ppb;tm=round(math.sqrt(max(0,B13))*5)if B15>=7 else 0
                    tt=round(tb+tm);ma_t=max(1,8+B15*2.5+B13/2500+qp)
                    tcv=min(0.80,0.35+(ma_t-B1)/ma_t*0.35)if B1<=ma_t else max(0.03,0.35*ma_t/B1)
                    td=max(0,round(tt*tcv*sz))
                B2=rd+td;rs=min(rd,B3);ts_=min(td,B3-rs);B6=rs+ts_
                ws=0;wr=0
                if B14>130:
                    wd=round((B14-130)*50*(1+(sz-1)*0.25))
                    ws=min(max(0,round(wd)),max(0,B3-B6));wr=round(ws*B1*ws_price)
                B7=B6*B1+round(B6*B1*0.20)+wr
                B12=round(B10*(1-min(0.5,B3*0.00008))*100)/100
                pkg=round(B1*0.15);uc=round(B14*25+B24*200);eq=2000
                trn=B25*B24;ms=round(0.05*B24*1500)
                rcogs=round((B12+pkg+B4)*min(B6,B3))
                wcogs=round(ws*B10*ws_ing+ws*ws_pack)if ws>0 else 0
                B8=round(B7-rcogs-wcogs-B5-B9-B13-trn-ms-uc-eq);tot+=B8;mons.append(B8)
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
            if tot>best[0]:best=[tot,(B1,B24,B25,B13,B14,B15,B10,B26),mons]
    return best

# Test wholesale pricing
configs=[(0.40,0.85,1.5),(0.35,1.0,2.0),(0.42,0.80,1.2)]
for ws_p,ws_i,ws_pk in configs:
    b=run_factory(ws_p,ws_i,ws_pk)
    p=b[1];m=b[2]
    avg=sum(m)/12
    print("ws=%.2f/%.2f/%.1f: %d/yr (%.0f/mo) B1=%d B24=%d B14=%d B15=%d B10=%d B26=%d"%
          (ws_p,ws_i,ws_pk,b[0],avg,p[0],p[1],p[4],p[5],p[6],p[7]))
    print("  First 6mo: %s"%[(m[i])for i in range(6)])
