/**
 * 最小复现: SetRule M1→B3 阻止 entangle M1→FAT 
 * 排查方向: 
 *   1. 注册顺序？  2. SetRule vs SetRules 区别？  
 *   3. B3 脏标记导致 ghost 被清？  4. NotifyAll vs _batchNotify
 */
import {describe,it} from 'vitest'
import {createSheetEngine} from '../engine'

const FAT='FAT'

// 辅助: 创建引擎+注册
function mkEngine() {
  const e=createSheetEngine();const eg=e.raw as any
  const rd=(id:string)=>Number(eg.data.GetValue(id,'value'))||0
  return {e,eg,rd}
}
function regEntangle(eg:any){
  eg.config.useEntangle({
    cause:'M1',impact:FAT,via:['value'],
    emit:(_c:any,_i:any,propose:any)=>{
      const cur=Number(eg.data.GetValue(FAT,'value'))||40
      console.log(`[emit] M1→FAT: ${cur}→${cur+5}`)
      propose.set('value',cur+5)
    }
  })
}
function init(eg:any){
  eg.data.SilentSet('M1','value',0)
  eg.data.SetValues([{path:FAT,key:'value',value:40},{path:'B3',key:'value',value:0}])
}

describe('SetRule如何阻止entangle',()=>{

  // === 方向1: 注册顺序 ===
  it('先注册SetRule后注册Entangle',async()=>{
    const{eg,rd}=mkEngine()
    eg.config.SetRule('M1','B3','value',{triggerKeys:['value'],logic:()=>1000})
    regEntangle(eg)
    init(eg);for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    eg.data.SetValues([{path:'M1',key:'value',value:1}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    console.log(`FAT=${rd(FAT)} (应45)`)
  })

  it('先注册Entangle后注册SetRule',async()=>{
    const{eg,rd}=mkEngine()
    regEntangle(eg)
    eg.config.SetRule('M1','B3','value',{triggerKeys:['value'],logic:()=>1000})
    init(eg);for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    eg.data.SetValues([{path:'M1',key:'value',value:1}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    console.log(`FAT=${rd(FAT)} (应45)`)
  })

  // === 方向2: SetRules (批量) vs SetRule (单个) ===
  it('用SetRules(批量)替代SetRule(单个)',async()=>{
    const{eg,rd}=mkEngine()
    regEntangle(eg)
    eg.config.SetRules(['M1'],'B3','value',{triggerKeys:['value'],logic:({slot}:any)=>1000})
    init(eg);for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    eg.data.SetValues([{path:'M1',key:'value',value:1}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    console.log(`FAT=${rd(FAT)} (应45)`)
  })

  // === 方向3: B3用SilentSet代替SetRule ===
  it('不用SetRule，手动SilentSet B3',async()=>{
    const{eg,rd}=mkEngine()
    regEntangle(eg)
    init(eg);for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    // 手动修改 B3
    eg.data.SilentSet('B3','value',1000);eg.data.SilentSet('B3','formula','')
    eg.data.SetValues([{path:'M1',key:'value',value:1}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    console.log(`FAT=${rd(FAT)} (应45) B3=${rd('B3')}`)
  })

  // === 方向4: SetRule M1→另一个节点(不是B3) ===
  it('SetRule M1→X (X不是B3)',async()=>{
    const{eg,rd}=mkEngine()
    eg.config.SetRule('M1','B5','value',{triggerKeys:['value'],logic:()=>9999})
    regEntangle(eg)
    eg.data.SilentSet('M1','value',0)
    eg.data.SetValues([{path:FAT,key:'value',value:40},{path:'B5',key:'value',value:0}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    eg.data.SetValues([{path:'M1',key:'value',value:1}])
    for(let r=0;r<3;r++){await eg.config.notifyAll();await new Promise(r2=>setTimeout(r2,50))}
    console.log(`FAT=${rd(FAT)} (应45) B5=${rd('B5')} (应9999)`)
  })

})
