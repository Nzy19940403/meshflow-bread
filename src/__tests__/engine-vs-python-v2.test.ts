/**
 * MeshFlow SetRules vs Python V5.8 — 全部中间量保留2位小数
 */
import { describe, it, expect } from 'vitest'
import { createSheetEngine } from '../engine'

const FAT='FAT',EXP='EMP',BRAND='BRAND'

const SCENARIOS=[
  {label:'✨ 高奢·精兵',B1:28,B24:3,B25:500,B13:6000,B14:120,B15:9,B10:8,B26:5000},
  {label:'🏭 大厂·标准',B1:16,B24:8,B25:100,B13:2000,B14:150,B15:7,B10:5,B26:5000},
  {label:'🏠 社区·基本',B1:16,B24:3,B25:0,B13:0,B14:60,B15:5,B10:5,B26:4000},
]

// Python V5.8 参考数据 (全部2位小数)
const PY:Record<string,number[]>={
  '✨ 高奢·精兵':[12456,27936,32553,32453,32553,32520,32621,32544,32655,32621,32766,32689],
  '🏭 大厂·标准':[-6440,-3854,-3757,-3690,-3622,-3607,-3553,-3485,-3471,-3417,-3349,-3336],
  '🏠 社区·基本':[-7520,-6410,-6338,-6258,-6186,-6124,-6082,-6033,-5953,-5911,-5861,-5818],
}

const r2=(x:number)=>Math.round(x*100)/100

const sk=(c:number)=>c<80?1:c>=100?0.1:1-(t=>t*t*(3-2*t)*0.9)((c-80)/20)
const wf=(b:number)=>r2(0.2+1.6*b/10000)
const wF=(b:number)=>r2(Math.max(0.3,1.5-b/5000))
const qp=(b:number)=>Math.max(0,(b-4000)/500)
const pbF=(b:number)=>r2(b<20?1+(20-b)*0.15:Math.max(0.6,1-(b-20)*0.03))

function setup(e:ReturnType<typeof createSheetEngine>){
  const eg=e.raw as any
  eg.config.SetRules(['B24','B15','B26'],'B9','value',{
    logic:({slot}:any)=>{const h=slot.triggerTargets[0]?.value??5,g=slot.triggerTargets[1]?.value??7,w=slot.triggerTargets[2]?.value??5000
      return Math.round(h*w*(1+g*0.15*Math.max(0,1-h*0.08)))},triggerKeys:['value','value','value']})
  eg.config.SetRules(['B14','B15'],'B5','value',{
    logic:({slot}:any)=>{const a=slot.triggerTargets[0]?.value??80,g=slot.triggerTargets[1]?.value??5
      return Math.max(0,Math.round(a*g*Math.max(2,20-a*0.05)))},triggerKeys:['value','value']})
  eg.config.SetRules(['B3',EXP,'B26'],'B4','value',{
    logic:({slot}:any)=>{const cap=slot.triggerTargets[0]?.value??0,exp=slot.triggerTargets[1]?.value??0,b26=slot.triggerTargets[2]?.value??5000
      return r2(Math.max(0.1,Math.max(0.1,2-cap*0.0002)*(1-exp*0.002)*wF(b26)))},triggerKeys:['value','value','value']})
  eg.config.SetRules(['B9','B24','B3','B4','B14','B15','B26'],'B21','value',{
    logic:({slot}:any)=>{const labor=slot.triggerTargets[0]?.value??0,hc=slot.triggerTargets[1]?.value??5
      const eff=slot.triggerTargets[2]?.value??1000,cost=slot.triggerTargets[3]?.value??2
      const area=slot.triggerTargets[4]?.value??80,grade=slot.triggerTargets[5]?.value??7,b26=slot.triggerTargets[6]?.value??5000
      const p=Math.max(1,Math.min(area*35,hc*1500)*wf(b26)+Math.max(0,Math.round((2-cost)*100)))
      const pp=r2(labor/Math.max(hc,1)),bl=3+grade*0.4
      const ps=r2(pp>=bl?0.7+Math.min((pp-bl)/(bl*2),0.3):pp/bl*0.7)
      const ov=r2(Math.max(0,eff/Math.max(p,1)-(0.8+0.2*ps))*1.5)
      return r2(Math.min(1,Math.max(0,ps-ov)))
    },triggerKeys:['value','value','value','value','value','value','value']})
  eg.config.SetRules(['B1','B15','B13',BRAND,'B21','B26'],'B2','value',{
    logic:({slot}:any)=>{const p=slot.triggerTargets[0]?.value??16,g=slot.triggerTargets[1]?.value??7
      const m=slot.triggerTargets[2]?.value??0,brand=slot.triggerTargets[3]?.value??0,b21=slot.triggerTargets[4]?.value??0.8,b26=slot.triggerTargets[5]?.value??5000
      const area=Number(eg.data.GetValue('B14','value')??80)
      const tr=Math.round((500+500*g+Math.round(brand*3))*pbF(p))+Math.round(Math.sqrt(Math.max(0,m))*10)*(1+area/100)
      const ma=Math.max(1,15+g*2+brand*0.5+b21*3+qp(b26))
      const conv=r2(p<=ma?0.5+(ma-p)/ma*0.4:Math.max(0.05,0.5*ma/p))
      return Math.max(0,Math.round(tr*conv))
    },triggerKeys:['value','value','value','value','value','value']})
  e.setCellFormula('B12','=ROUND(B10*(1-MIN(0.5,B3*0.00008)),2)')
  e.setCellFormula('B20','=B21')
}

function init(e:ReturnType<typeof createSheetEngine>,p:any){
  const eg=e.raw as any
  for(const[k,v]of Object.entries({B1:p.B1,B4:2,B10:p.B10,B13:p.B13,B14:p.B14,B15:p.B15,
    B24:p.B24,B25:p.B25,B26:p.B26,B21:0.8,[EXP]:0,[BRAND]:0,[FAT]:40,
  })){eg.data.SilentSet(k,'value',v);eg.data.SilentSet(k,'formula','')}
  const ib3=Math.max(0,Math.round(Math.min(p.B14*35,p.B24*1500)*wf(p.B26)))
  eg.data.SilentSet('B3','value',ib3);eg.data.SilentSet('B3','formula','')
}

describe('MeshFlow vs Python V5.8 (2位小数)',()=>{
  const engine=createSheetEngine()
  setup(engine)

  for(const s of SCENARIOS){it(`${s.label}: 12个月`,async()=>{
    init(engine,s)
    const eg=engine.raw as any,rd=(id:string)=>Number(eg.data.GetValue(id,'value'))||0
    const profits:number[]=[]
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    for(let m=0;m<12;m++){
      const b1=rd('B1'),b2=rd('B2'),b3=rd('B3'),b4=rd('B4'),b5=rd('B5'),b9=rd('B9')
      const b12=rd('B12'),b13=rd('B13'),b14=rd('B14'),b15=rd('B15')
      const b21=rd('B21'),b24=rd('B24'),b25=rd('B25'),b26=rd('B26')
      const brand=rd(BRAND),c4=rd(FAT),emp=rd(EXP)
      const b6=Math.min(b2,b3)
      const rev=b6*b1+Math.round(b6*b1*0.20)
      const pkg=Math.round(b1*0.15),util=Math.round(b14*25+b24*200),eq=2000
      const trn=b25*b24,misc=Math.round(0.05*b24*1500)
      const cost=Math.round((b12+pkg+b4)*b3)
      const b8=Math.round(rev-cost-b5-b9-b13-trn-misc-util-eq)
      profits.push(b8)
      const ph=Math.max(1,Math.min(b14*35,b24*1500)*wf(b26)+Math.max(0,Math.round((2-b4)*100)))
      const ur=b3/Math.max(ph,1)
      let d=3
      if(b25===0&&ur>0.7)d+=5;else if(b25===0)d+=2
      if(ur>0.8)d+=(ur-0.8)*40
      d-=b25*0.03;d=Math.round(d)
      const ff=c4<40?c4/40:1
      if(b21<0.5)d-=(b21-0.5)*15*ff
      if(b9/b24>1500)d-=(b9/b24-1500)*0.005*ff
      const nF=Math.max(0,Math.min(100,Math.round(c4+d)))
      const sr=Math.max(0,(b2-b3)/Math.max(1,b2))
      const nE=Math.min(200,Math.round(emp+Math.max(1,10-Math.round(emp*0.05))))
      const nB=Math.max(0,Math.round(brand+b21*30*Math.max(0.1,1-brand/800)-brand*Math.max(0.02,brand*0.015)-sr*10))
      const nB3=Math.max(0,Math.round(ph*sk(nF)))
      eg.data.SetValues([
        {path:FAT,key:'value',value:nF},{path:EXP,key:'value',value:nE},
        {path:BRAND,key:'value',value:nB},{path:'B3',key:'value',value:nB3},
      ])
      await new Promise(r2=>setTimeout(r2,50))
    }
    const exp=PY[s.label];let maxD=0
    for(let m=0;m<12;m++){const d=Math.abs(profits[m]-exp[m]);maxD=Math.max(maxD,d)
      console.log(`  月${m+1}: 引擎=${profits[m]}  Python=${exp[m]}  差=${d}`)}
    console.log(`  最大偏差: ${maxD}`)
    expect(maxD).toBeLessThanOrEqual(100)
  },30000)}
})
