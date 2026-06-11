<template>
  <div class="graph-panel">
    <div class="gp-header">
      <span class="gp-title">DAG 节点图</span>
      <span class="gp-legend">
        <span class="gl-item"><span class="gl-line" style="background:#3b82f6"></span> SetRule</span>
        <span class="gl-item"><span class="gl-line" style="background:none;border-top:2px dashed #f59e0b"></span> 纠缠</span>
        <span class="gl-item"><span class="gl-line" style="background:none;border-top:1.5px dashed #f44336"></span> 惩罚</span>
        <span class="gl-item"><span class="gl-line" style="background:none;border-top:2px dashed #8b5cf6"></span> B2B</span>
      </span>
    </div>
    <div class="gp-body">
      <VueFlow v-model="edges" :nodes="nodes" :default-zoom="0.85" :min-zoom="0.3" :max-zoom="2" fit-view-on-init>
        <template #node-custom="np">
          <div class="flow-node" :class="{ 'flow-changed': cascadingNodes.has(np.id), 'flow-end': np.id === 'B8' }" @click="$emit('node-selected', np.id)">
            <Handle type="target" :position="Position.Left" />
            <div class="fn-label">{{ np.data.label }}</div>
            <div class="fn-value">{{ formatVal(np.data.value) }}</div>
            <div class="fn-role">{{ np.data.role }}</div>
            <Handle type="source" :position="Position.Right" />
          </div>
        </template>
        <Background :gap="16" />
      </VueFlow>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { VueFlow, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
const props = defineProps<{ engine: any; simple?: boolean; selectedNode?: string }>()
const emit = defineEmits<{ 'node-selected': [id: string] }>()
const cascadingNodes = ref(new Set<string>())
const refreshTick = ref(0)
watch(() => props.engine?.changedNodes?.value, (ns: Set<string>) => { cascadingNodes.value = new Set(ns || []); refreshTick.value++ }, { deep: true })
watch(() => props.engine?.uiSignal?.value, () => { refreshTick.value++ })
watch(() => props.selectedNode, () => { refreshTick.value++ })
function readValue(id: string): any { try { const v = props.engine.getCellValue(id); if (v === null || v === undefined) return '-'; const n = Number(v); return Number.isFinite(n) ? n : '-' } catch { return '-' } }
function formatVal(v: any): string { if (v === undefined || v === null || v === '') return '-'; const n = Number(v); if (!Number.isFinite(n)) return '-'; if (Math.abs(n) >= 1000) return Math.round(n).toLocaleString(); return n.toFixed(2) }
const srC = '#3b82f6'; const enC = '#f59e0b'; const pC = '#f44336'; const b2C = '#8b5cf6'

const nodes = computed((): any[] => { void refreshTick.value; return [
  { id: 'B10', type: 'custom', position: { x: 60,  y: 40  }, data: { label: '原料成本', value: readValue('B10'), role: '可编辑' } },
  { id: 'B14', type: 'custom', position: { x: 60,  y: 160 }, data: { label: '店面面积', value: readValue('B14'), role: '可编辑' } },
  { id: 'B24', type: 'custom', position: { x: 60,  y: 280 }, data: { label: '员工数',   value: readValue('B24'), role: '可编辑' } },
  { id: 'B26', type: 'custom', position: { x: 60,  y: 400 }, data: { label: '基础工资', value: readValue('B26'), role: '可编辑' } },
  { id: 'B15', type: 'custom', position: { x: 60,  y: 520 }, data: { label: '场地等级', value: readValue('B15'), role: '可编辑' } },
  { id: 'B13', type: 'custom', position: { x: 60,  y: 640 }, data: { label: '营销投入', value: readValue('B13'), role: '可编辑' } },
  { id: 'B25', type: 'custom', position: { x: 60,  y: 760 }, data: { label: '培训投入', value: readValue('B25'), role: '可编辑' } },
  { id: 'B9',  type: 'custom', position: { x: 320, y: 40  }, data: { label: '人工成本', value: readValue('B9'),  role: '员工×工资×地段' } },
  { id: 'B3',  type: 'custom', position: { x: 320, y: 180 }, data: { label: '月产能',   value: readValue('B3'),  role: 'min(面积,人工)×FAT' } },
  { id: 'B4',  type: 'custom', position: { x: 320, y: 320 }, data: { label: '加工成本', value: readValue('B4'),  role: '规模效应+工资' } },
  { id: 'B28', type: 'custom', position: { x: 320, y: 460 }, data: { label: '原料品质', value: readValue('B28'), role: 'B10档次+高薪引师傅' } },
  { id: 'FAT', type: 'custom', position: { x: 320, y: 590 }, data: { label: '员工疲劳', value: readValue('FAT'), role: '零售UR+B2B累积' } },
  { id: 'B21', type: 'custom', position: { x: 600, y: 40  }, data: { label: '满意度',   value: readValue('B21'), role: '工资×0.4+效率×0.6' } },
  { id: 'B20', type: 'custom', position: { x: 600, y: 200 }, data: { label: '口味品质', value: readValue('B20'), role: 'B21×0.45+B28×0.55' } },
  { id: 'B1',  type: 'custom', position: { x: 600, y: 360 }, data: { label: '售价',     value: readValue('B1'),  role: '可编辑' } },
  { id: 'B2',  type: 'custom', position: { x: 600, y: 500 }, data: { label: '零售需求', value: readValue('B2'),  role: '客流×转化×季节' } },
  { id: 'BRAND', type: 'custom', position: { x: 600, y: 660 }, data: { label: '品牌知名度', value: readValue('BRAND'), role: '口碑积累+衰减' } },
  { id: 'B5',  type: 'custom', position: { x: 900, y: 40  }, data: { label: '房租',     value: readValue('B5'),  role: '面积×地段×单价' } },
  { id: 'B12', type: 'custom', position: { x: 900, y: 180 }, data: { label: '实际原料成本', value: readValue('B12'), role: 'B10×批量折扣' } },
  { id: 'B6',  type: 'custom', position: { x: 900, y: 320 }, data: { label: '月收入',   value: readValue('B6'),  role: '零售+B2B' } },
  { id: 'B7',  type: 'custom', position: { x: 900, y: 460 }, data: { label: '总成本',   value: readValue('B7'),  role: '生产+房租+人工+营销' } },
  { id: 'B8',  type: 'custom', position: { x: 900, y: 600 }, data: { label: '月利润',   value: readValue('B8'),  role: '终点' } },
]})

const edges = ref([
  // B9 人工
  { id:'e1', source:'B24',target:'B9',label:'人头',style:{stroke:srC,strokeWidth:2}},
  { id:'e2', source:'B26',target:'B9',label:'薪基准',style:{stroke:srC,strokeWidth:2}},
  { id:'e3', source:'B15',target:'B9',label:'地段×',style:{stroke:srC,strokeWidth:2}},
  // B5 租金
  { id:'e4', source:'B14',target:'B5',label:'面积',style:{stroke:srC,strokeWidth:2}},
  { id:'e5', source:'B15',target:'B5',label:'地段',style:{stroke:srC,strokeWidth:2}},
  // B3 产能
  { id:'e6', source:'B14',target:'B3',label:'面积上限',style:{stroke:srC,strokeWidth:2}},
  { id:'e7', source:'B24',target:'B3',label:'人工上限',style:{stroke:srC,strokeWidth:2}},
  { id:'e8', source:'FAT',target:'B3',label:'sk(FAT)',style:{stroke:enC,strokeWidth:2.5,strokeDasharray:'6 3'},animated:true},
  // B3↔B4 纠缠
  { id:'e9', source:'B3',target:'B4',label:'规模→降加工',style:{stroke:srC,strokeWidth:2}},
  { id:'ea', source:'B26',target:'B4',label:'高薪→低废品',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  // B28 品质
  { id:'eb', source:'B10',target:'B28',label:'原料档次',style:{stroke:srC,strokeWidth:2}},
  { id:'ec', source:'B26',target:'B28',label:'高薪→好师傅',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  // B2 需求
  { id:'ed', source:'B15',target:'B2',label:'地段→客流',style:{stroke:srC,strokeWidth:2}},
  { id:'ee', source:'B13',target:'B2',label:'营销→客流',style:{stroke:srC,strokeWidth:2}},
  { id:'ef', source:'B14',target:'B2',label:'可见度',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  { id:'eg', source:'B1',target:'B2',label:'价格→转化',style:{stroke:srC,strokeWidth:2}},
  { id:'eh', source:'BRAND',target:'B2',label:'品牌→复购',style:{stroke:srC,strokeWidth:2},animated:true},
  { id:'ei', source:'B28',target:'B2',label:'品质→复购',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  { id:'ej', source:'B21',target:'B2',label:'满意→ma',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  { id:'ek', source:'B26',target:'B2',label:'工资→ma',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  // B21 满意度
  { id:'el', source:'B26',target:'B21',label:'工资水平',style:{stroke:srC,strokeWidth:2}},
  { id:'em', source:'B9',target:'B21',label:'件均人工',style:{stroke:srC,strokeWidth:2}},
  { id:'en', source:'B3',target:'B21',label:'产出负荷',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  { id:'eo', source:'B15',target:'B21',label:'地段基准',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  { id:'ep', source:'FAT',target:'B21',label:'过劳-满意',style:{stroke:pC,strokeWidth:1.5,strokeDasharray:'5 3'}},
  // B20 口味
  { id:'eq', source:'B21',target:'B20',label:'满意×45%',style:{stroke:srC,strokeWidth:2}},
  { id:'er', source:'B28',target:'B20',label:'品质×55%',style:{stroke:srC,strokeWidth:2}},
  // BRAND
  { id:'es', source:'B20',target:'BRAND',label:'口味→口碑',style:{stroke:srC,strokeWidth:2},animated:true},
  { id:'et', source:'B21',target:'BRAND',label:'满意度',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  { id:'eu', source:'B28',target:'BRAND',label:'品质',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  { id:'ev', source:'B13',target:'BRAND',label:'营销',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  { id:'ew', source:'FAT',target:'BRAND',label:'过劳伤口碑',style:{stroke:pC,strokeWidth:1.5,strokeDasharray:'5 3'}},
  { id:'ex', source:'B2',target:'BRAND',label:'缺货扣分',style:{stroke:pC,strokeWidth:1.5,strokeDasharray:'5 3'}},
  // FAT
  { id:'ey', source:'B2',target:'FAT',label:'零售负荷',style:{stroke:pC,strokeWidth:1.5,strokeDasharray:'4 2'}},
  { id:'ez', source:'B3',target:'FAT',label:'产能→总UR',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
  // B12
  { id:'f0', source:'B10',target:'B12',label:'原料价',style:{stroke:srC,strokeWidth:2}},
  { id:'f1', source:'B3',target:'B12',label:'批量折扣',style:{stroke:srC,strokeWidth:2}},
  // B6
  { id:'f2', source:'B2',target:'B6',label:'需求',style:{stroke:srC,strokeWidth:2}},
  { id:'f3', source:'B3',target:'B6',label:'产能',style:{stroke:srC,strokeWidth:2}},
  // B7 收入
  { id:'f4', source:'B6',target:'B7',label:'零售+B2B',style:{stroke:srC,strokeWidth:2}},
  { id:'f5', source:'B28',target:'B7',label:'品质→B2B价',style:{stroke:b2C,strokeWidth:2,strokeDasharray:'6 3'},animated:true},
  // B7 支出
  { id:'f6', source:'B12',target:'B7',label:'生产',style:{stroke:srC,strokeWidth:2}},
  { id:'f7', source:'B5',target:'B7',label:'房租',style:{stroke:srC,strokeWidth:2}},
  { id:'f8', source:'B9',target:'B7',label:'人工',style:{stroke:srC,strokeWidth:2}},
  { id:'f9', source:'B13',target:'B7',label:'营销',style:{stroke:srC,strokeWidth:2}},
  // B8
  { id:'fa', source:'B6',target:'B8',label:'收入',style:{stroke:srC,strokeWidth:2}},
  { id:'fb', source:'B7',target:'B8',label:'成本',style:{stroke:srC,strokeWidth:2}},
  { id:'fc', source:'B25',target:'B8',label:'培训',style:{stroke:srC,strokeWidth:2,strokeDasharray:'4 2'}},
])
</script>
<style scoped>
.graph-panel{background:#0a0a0a;height:100%;display:flex;flex-direction:column}
.gp-header{padding:8px 12px;border-bottom:1px solid #2a2a2a;display:flex;align-items:center;gap:10px}
.gp-title{font-size:13px;color:#e0e0e0;font-family:monospace}
.gp-legend{display:flex;gap:10px;margin-left:auto}
.gl-item{display:flex;align-items:center;gap:4px;font-size:9px;color:#5a5a5a;font-family:monospace}
.gl-line{display:inline-block;width:16px;height:2px;border-radius:1px}
.gp-body{flex:1}
.flow-node{background:#141414;border:1px solid #2a2a2a;border-radius:8px;padding:6px 10px;min-width:120px;cursor:pointer}
.flow-node:hover{border-color:#4CAF50}
.flow-changed{border-color:#FFD700!important;animation:flash-node 1.5s ease-out}
@keyframes flash-node{0%{background:#2a2a00}100%{background:#141414}}
.flow-end{border-color:#4CAF50!important;background:#0a1a0a}
.fn-label{font-size:11px;color:#e0e0e0;font-family:monospace;font-weight:bold}
.fn-value{font-size:14px;color:#4CAF50;font-family:monospace;margin:2px 0}
.fn-role{font-size:9px;color:#555;font-family:monospace}
</style>
