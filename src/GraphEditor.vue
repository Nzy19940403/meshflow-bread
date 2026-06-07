<template>
  <div class="graph-editor">
    <div class="graph-toolbar">
      <span class="graph-title">🌐 面包店经营模型</span>
      <div class="graph-legend">
        <span class="legend-item"><span class="legend-line solid"></span> SetRule</span>
        <span class="legend-item"><span class="legend-line dashed"></span> 纠缠</span>
        <span class="legend-item"><span class="legend-line conflict"></span> 冲突点</span>
        <span class="legend-item"><span class="legend-dot live"></span> 传播</span>
      </div>
      <button class="btn btn-sm btn-month" @click="advanceMonth" :disabled="yearDone">
        {{ yearDone ? '✅ 年终' : '📅 下个月' }}
      </button>
      <button class="btn btn-sm btn-guide" @click="toggleGuide">
        {{ guideOpen ? '✕ 关闭指南' : '📖 推演指南' }}
      </button>
    </div>

    <div class="sim-bar">
      <span class="sim-month">📊 第 <strong>{{ currentMonth }}</strong> / 12 月</span>
      <span class="sim-profit" :class="monthProfitClass">📈 本月: {{ formatMoney(monthlyProfit) }}</span>
      <span class="sim-cumulative" :class="cumProfitClass">💰 累计: {{ formatMoney(cumulativeProfit) }}</span>
      <span class="sim-actions" v-if="yearDone">
        <button class="btn btn-sm btn-reset" @click="newYear">🔄 新一年</button>
      </span>
    </div>

    <div class="graph-canvas">
      <!-- 大节点组标签 -->
      <div class="group-labels">
        <div class="group-label sc">🏭 供应链</div>
        <div class="group-label prod">🍞 生产</div>
        <div class="group-label market">🏪 市场</div>
        <div class="group-label fin">💰 财务</div>
      </div>
      <VueFlow
        :nodes="nodes"
        :edges="edges"
        :fit-view-on-init="true"
        :min-zoom="0.15"
        :max-zoom="2.5"
        :pan-on-drag="true"
        :zoom-on-scroll="true"
        :zoom-on-pinch="true"
        fit-view-on-init-params="default"
        @node-click="onNodeClick"
        class="meshflow-graph"
      >
        <Background :gap="20" />
        <template #node-custom="nodeProps">
          <!-- 上端口：输入 (target) — 被别人影响 -->
          <Handle type="target" :position="Position.Top" :style="{ background: '#0071e3', width: 8, height: 8, border: '2px solid #fff' }" />
          <div
            class="vue-flow__node-custom"
            :class="{
              selected: selectedNode === nodeProps.id,
              conflicted: nodeProps.id === 'B2' || nodeProps.id === 'B3',
              affected: isAffected(nodeProps.id),
              changed: wasChanged(nodeProps.id),
            }"
            @dblclick="startEdit(nodeProps.id)"
          >
            <div class="node-icon">{{ nodeIcons[nodeProps.id as keyof typeof nodeIcons] || '📦' }}</div>
            <div class="node-label">{{ nodeProps.data.label }}</div>
            <div class="node-values">
              <!-- 编辑模式 -->
              <div v-if="editingNode === nodeProps.id" class="node-edit-row">
                <input
                  ref="editInput"
                  v-model="editValue"
                  class="node-edit-input"
                  @keydown.enter="commitEdit(nodeProps.id)"
                  @keydown.escape="cancelEdit"
                  @blur="commitEdit(nodeProps.id)"
                  autofocus
                />
              </div>
              <!-- 展示模式 -->
              <div v-else class="node-value-row" @click="startEdit(nodeProps.id)">
                <span class="node-value-num" :class="{ 'value-changed': wasChanged(nodeProps.id) }">
                  {{ formatVal(nodeProps.data.value) }}
                </span>
                <span class="edit-hint">✎</span>
              </div>
              <div v-if="nodeProps.data.role" class="node-role-badge">{{ nodeProps.data.role }}</div>
            </div>
          </div>
          <!-- 下端口：输出 (source) — 影响别人 -->
          <Handle type="source" :position="Position.Bottom" :style="{ background: '#059669', width: 8, height: 8, border: '2px solid #fff' }" />
        </template>
      </VueFlow>
    </div>

    <!-- 📖 推演指南 — 原生 <details> headless disclosure 模式 -->
    <details ref="guideEl" class="guide-panel" open>
      <summary class="guide-header">📖 推演指南 <span class="guide-arrow">▾</span></summary>
      <div class="guide-body">

        <details class="g-section" open>
          <summary>🎯 目标</summary>
          <p>经营一家虚拟面包店，在 <strong>12 个月</strong> 的推演中找到盈利策略。调整售价、面积、人工、营销等参数，点击「📅 下个月」推进，看年终能不能赚钱。</p>
        </details>

        <details class="g-section" open>
          <summary>🎮 操作说明</summary>
          <ul>
            <li><strong>双击</strong> 任意可编辑节点（蓝色数值）→ 输入数字 → <kbd>Enter</kbd></li>
            <li>修改后系统自动 <strong>传播推演</strong>，绿色高亮显示数据流路径</li>
            <li><strong>📅 下个月</strong> → 推进一个月，记录本月盈亏，更新上期缓存</li>
            <li>第 12 个月后弹出 <strong>🏆 年度总结</strong>，可「🔄 新一年」重置</li>
            <li><strong>点击节点</strong> → 查看详情（出边/入边/公式说明）</li>
          </ul>
        </details>

        <details class="g-section" open>
          <summary>🧩 节点速查</summary>
          <div class="g-table">
            <div class="g-tr g-th"><span>组</span><span>节点</span><span>含义</span><span>可编辑</span></div>
            <div class="g-tr"><span>🏪市场</span><span>B1 售价</span><span>面包单价(元)</span><span class="g-yes">✅</span></div>
            <div class="g-tr"><span>🏪市场</span><span>B2 需求⚡</span><span>= f(价格+等级+营销−缺货惩罚)</span><span class="g-no">引擎</span></div>
            <div class="g-tr"><span>🍞生产</span><span>B3 产能⚡</span><span>= f(面积,人工,上期需求×动态系数)</span><span class="g-no">引擎</span></div>
            <div class="g-tr"><span>🍞生产</span><span>B4 加工成本</span><span>规模效应: 产高→成本低(下限¥0.1)</span><span class="g-no">引擎</span></div>
            <div class="g-tr"><span>💰财务</span><span>B5 房租🏗️</span><span>= 面积×等级×(20−面积×0.05)</span><span class="g-no">引擎</span></div>
            <div class="g-tr"><span>💰财务</span><span>B6 月收入</span><span>= 售价 × 实际销量</span><span class="g-no">引擎</span></div>
            <div class="g-tr"><span>💰财务</span><span>B7 总成本</span><span>= 生产+房租+人工+营销</span><span class="g-no">引擎</span></div>
            <div class="g-tr"><span>💰财务</span><span>B8 利润✅</span><span>= 收入 − 成本</span><span class="g-no">引擎</span></div>
            <div class="g-tr"><span>🍞生产</span><span>B9 人工</span><span>月人工成本，每¥5出1个产能</span><span class="g-yes">✅</span></div>
            <div class="g-tr"><span>🏭供应链</span><span>B10 原料</span><span>每单位原料成本(元/个)</span><span class="g-yes">✅</span></div>
            <div class="g-tr"><span>🏭供应链</span><span>B11 其他</span><span>水电包装等(元/个)</span><span class="g-yes">✅</span></div>
            <div class="g-tr"><span>🏭供应链</span><span>B12 生产成本</span><span>=(原料+其他+加工)×产能</span><span class="g-no">引擎</span></div>
            <div class="g-tr"><span>🏪市场</span><span>B13 营销</span><span>月营销投入(元)，√效应递减</span><span class="g-yes">✅</span></div>
            <div class="g-tr"><span>🏭供应链</span><span>B14 面积</span><span>店面面积(m²)，每m²出25个产能</span><span class="g-yes">✅</span></div>
            <div class="g-tr"><span>🏭供应链</span><span>B15 等级</span><span>地段等级(1-10)，影响需求+房租</span><span class="g-yes">✅</span></div>
            <div class="g-tr"><span>🏪市场</span><span>B16 上期需求📜</span><span>上月真实需求，影响下月备货</span><span class="g-no">缓存</span></div>
            <div class="g-tr"><span>🏪市场</span><span>B17 缺货率⚠️</span><span>缺货比例→降低当月需求</span><span class="g-no">缓存</span></div>
            <div class="g-tr"><span>🏪市场</span><span>B18 报废率📦</span><span>报废比例→降低备货信心</span><span class="g-no">缓存</span></div>
          </div>
        </details>

        <details class="g-section" open>
          <summary>⚙️ 核心公式</summary>
          <div class="g-formula">
            <div class="gf-title">📊 需求 (B2) — 流量×留存率</div>
            <code>流量 = round(150×等级^1.7) + max(0, √营销×15)  // 幂律分布</code>
            <code>地段溢价 = 等级×1.5  // 高级地段顾客接受更高价</code>
            <code>品牌溢价 = 知名度×0.5  // 每点知名度+¥0.5价格容忍</code>
            <code>可接受最高价 = 10 + 地段溢价 + 品牌溢价</code>
            <code>留存率 = if(售价≤可接受价) 0.5+(差价÷可接受价)×0.4 else 0.5×可接受价÷售价</code>
            <code>B2 = 流量 × 留存率 − 流量×缺货率×0.5</code>
            <p class="gf-note">顶级地段(10级)流量是偏远(1级)的50倍，且自然支持¥25高客单价。</p>
          </div>
          <div class="g-formula">
            <div class="gf-title">🏭 产能 (B3) — 物理上限（非需求约束）</div>
            <code>硬约束 = min(面积×25, 人工÷2.5)  // 每¥2.5出1产能</code>
            <code>效率红利 = max(0, (2−加工成本)×200)  // 成本低→同资源多产</code>
            <code>B3 = 硬约束 + 效率红利  // 纯物理产能，不含需求约束</code>
            <p class="gf-note">B3 只反映你能产多少，不反映你能卖多少。供需差通过 报废率(B18) 和 月收入(B6) 体现。</p>
          </div>
          <div class="g-formula">
            <div class="gf-title">🏢 房租 (B5) — 非线性折扣</div>
            <code>B5 = max(0, round(面积 × 等级 × max(2, 20−面积×0.05)))</code>
            <p class="gf-note">面积越大每平米越便宜。200m²时单价5折。</p>
          </div>
          <div class="g-formula">
            <div class="gf-title">💰 利润 (B8)</div>
            <code>收入 = 售价 × min(需求, 产能)  // 卖不掉不算</code>
            <code>成本 = (原料+其他+加工)×产能 + 房租 + 人工 + 营销</code>
            <code>利润 = 收入 − 成本</code>
            <p class="gf-note">核心是 <strong>供需匹配</strong>：做多了报废白花钱，做少了缺货损失机会。</p>
          </div>
        </details>

        <details class="g-section" open>
          <summary>💡 推演策略</summary>
          <div class="g-cards">
            <div class="g-card">
              <div class="gc-icon">✨</div>
              <div class="gc-name">精品路线</div>
              <div class="gc-desc">高售价(¥24~28) + 小店面(40~60m²) + 好地段 + 精人工</div>
              <div class="gc-tip">高价降低需求，须用等级和营销补偿；小面积房租低但产能受限。</div>
            </div>
            <div class="g-card">
              <div class="gc-icon">🏭</div>
              <div class="gc-name">工厂模式</div>
              <div class="gc-desc">低售价(¥14~16) + 大面积(100~200m²) + 低等级</div>
              <div class="gc-tip">大面积房租有非线性折扣，但人工和原料线性增长；单位利润薄。</div>
            </div>
            <div class="g-card">
              <div class="gc-icon">⚖️</div>
              <div class="gc-name">均衡路线</div>
              <div class="gc-desc">尝试中档参数(售价¥18~22)，探索未发现的盈利空间</div>
              <div class="gc-tip">每个参数微调都可能产生连锁反应，通过月度推演找到最优组合。</div>
            </div>
          </div>
        </details>

        <details class="g-section" open>
          <summary>⚠️ 陷阱</summary>
          <ul>
            <li><strong>盲目扩张</strong>：卖得好就加面积/人工 → 需求没增长 → 报废飙升</li>
            <li><strong>价格太低</strong>：检查 B4+B9+B10+B11 是否大于 B1，卖越多亏越多</li>
            <li><strong>忽视营销</strong>：仅调价格不调营销，B2 需求公式中营销有√效应</li>
            <li><strong>年底才看总结</strong>：每月查看本月利润，及时调整策略</li>
          </ul>
        </details>

        <details class="g-section" open>
          <summary>🔬 参考数据</summary>
          <p>模型经 <strong>500,000+ 组合穷举验证</strong>，引擎推演与 Python 偏差 &lt;0.01%。三条参考路线（固定1.2倍率版）：</p>
          <ul>
            <li>🥇 全局最优：售价28 / 人工16k / 营销5k / 面积140 / 等级10 → <strong>¥436,173/年</strong></li>
            <li>✨ 精品店：售价28 / 人工8k / 营销2k / 面积60 / 等级3 → <strong>¥261,504/年</strong></li>
            <li>🏭 工厂：售价16 / 人工14k / 营销3.5k / 面积120 / 等级1 → <strong>¥134,599/年</strong></li>
          </ul>
          <p class="gf-note">* 现版本已改用动态备货系数，参考值仅供对比。</p>
        </details>

      </div>
    </details>

    <!-- 年终总结 -->
    <div v-if="yearDone" class="year-summary">
      <div class="year-summary-header">🏆 年度经营总结</div>
      <div class="year-summary-grid">
        <div class="summary-item">
          <span class="summary-label">全年收入</span>
          <span class="summary-value">{{ formatMoney(yearRevenue) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">全年成本</span>
          <span class="summary-value">{{ formatMoney(yearCost) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">全年利润</span>
          <span class="summary-value" :class="cumProfitClass">{{ formatMoney(cumulativeProfit) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">利润率</span>
          <span class="summary-value">{{ profitMargin }}%</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">月均利润</span>
          <span class="summary-value">{{ formatMoney(Math.round(cumulativeProfit / 12)) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">盈利月数</span>
          <span class="summary-value">{{ profitableMonths }}/12</span>
        </div>
      </div>
    </div>

    <!-- 传播状态 -->
    <div class="propagation-bar" v-if="propagating">
      <span class="prop-spinner">⟳</span>
      <span>{{ propMessage }}</span>
    </div>

    <!-- 节点详情 -->
    <div v-if="selectedNode && !propagating" class="node-detail-panel">
      <div class="detail-header">
        <strong>{{ getNodeLabel(selectedNode) }}</strong>
        <span class="node-value-big">{{ formatVal(getNodeValue(selectedNode)) }}</span>
        <button class="close-btn" @click="selectedNode = ''">✕</button>
      </div>
      <div class="detail-body">
        <div class="detail-section">
          <h4>📤 出边 · 影响这些节点</h4>
          <div v-for="e in outgoingEdges" :key="e.id" class="edge-info">
            <span class="edge-arrow">→</span>
            <strong>{{ getNodeLabel(e.target) }}</strong>
            <span class="edge-desc">{{ e.label }}</span>
          </div>
          <div v-if="outgoingEdges.length === 0" class="no-edges">无</div>
        </div>
        <div class="detail-section">
          <h4>📥 入边 · 受这些节点影响</h4>
          <div v-for="e in incomingEdges" :key="e.id" class="edge-info">
            <span class="edge-arrow">←</span>
            <strong>{{ getNodeLabel(e.source) }}</strong>
            <span class="edge-desc">{{ e.label }}</span>
          </div>
          <div v-if="incomingEdges.length === 0" class="no-edges">无</div>
        </div>
        <div v-if="selectedNode === 'B2'" class="detail-warning">
          ⚡ B2(需求) SetRule: 价格+等级+营销 减去 B17缺货惩罚
        </div>
        <div v-if="selectedNode === 'B3'" class="detail-warning">
          ⚡ B3(产能) 物理上限: 面积×25 ∩ 人工÷2.5 + 效率红利(2-B4)×200
        </div>
      </div>
    </div>

    <!-- 提示 -->
    <div v-else-if="!propagating" class="node-hint">
      👆 点击节点详请 · 双击或点数值编辑 · 改 B1 看传播路径！
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { VueFlow, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

// === Props ===
const props = defineProps<{ engine: any }>()

function readValue(id: string): any {
  try { return props.engine.getCellValue(id) } catch { return '' }
}

const nodeIcons: Record<string, string> = {
  B1: '💰', B2: '📊', B3: '🏭', B4: '🔧', B5: '🏢',
  B6: '📈', B7: '📉', B8: '✅', B9: '👷',
  B10: '🥖', B11: '📦', B12: '🏗️', B13: '📢', B14: '📐', B15: '⭐',
  B16: '📜', B17: '⚠️', B18: '📦',
  B19: '🌟', B20: '😋', B21: '😊',
}

function formatVal(v: any): string {
  if (v === undefined || v === null || v === '') return '—'
  const n = Number(v)
  if (Math.abs(n) >= 1000) return Math.round(n).toLocaleString()
  return isNaN(n) ? String(v) : n.toFixed(2)
}

// === 节点数据 ===
const nodes = ref([
  // ============ 🏭 供应链 (x=50) — 输入决策 ============
  { id: 'B10', type: 'custom', position: { x: 50, y: 60 }, data: { label: '原料成本', value: readValue('B10'), role: '可编辑' } },
  { id: 'B11', type: 'custom', position: { x: 50, y: 180 }, data: { label: '其他变动成本', value: readValue('B11'), role: '可编辑' } },
  { id: 'B14', type: 'custom', position: { x: 50, y: 300 }, data: { label: '店面面积', value: readValue('B14'), role: '可编辑(m²)' } },
  { id: 'B15', type: 'custom', position: { x: 50, y: 420 }, data: { label: '场地等级', value: readValue('B15'), role: '可编辑(1-10)' } },
  { id: 'B9', type: 'custom', position: { x: 50, y: 540 }, data: { label: '人工成本', value: readValue('B9'), role: '可编辑' } },
  { id: 'B13', type: 'custom', position: { x: 50, y: 660 }, data: { label: '营销投入', value: readValue('B13'), role: '可编辑' } },

  // ============ 🍞 运营 (x=330) — 业务逻辑 ============
  { id: 'B5', type: 'custom', position: { x: 330, y: 60 }, data: { label: '房租🏗️', value: readValue('B5'), role: '=面积×等级×折扣' } },
  { id: 'B21', type: 'custom', position: { x: 330, y: 180 }, data: { label: '员工满意度😊', value: readValue('B21'), role: '薪酬vs负荷' } },
  { id: 'B4', type: 'custom', position: { x: 330, y: 300 }, data: { label: '加工成本', value: readValue('B4'), role: '规模效应' } },
  { id: 'B20', type: 'custom', position: { x: 330, y: 420 }, data: { label: '口味/品质😋', value: readValue('B20'), role: '满意度→品质' } },
  { id: 'B3', type: 'custom', position: { x: 330, y: 540 }, data: { label: '产能 ⚡', value: readValue('B3'), role: '冲突点' } },
  { id: 'B1', type: 'custom', position: { x: 330, y: 660 }, data: { label: '售价', value: readValue('B1'), role: '可编辑' } },

  // ============ 📊 市场 (x=610) — 需求+品牌+缓存 ============
  { id: 'B2', type: 'custom', position: { x: 610, y: 60 }, data: { label: '需求 ⚡', value: readValue('B2'), role: '流量×留存率' } },
  { id: 'B19', type: 'custom', position: { x: 610, y: 200 }, data: { label: '知名度🌟', value: readValue('B19'), role: '积累中' } },
  { id: 'B16', type: 'custom', position: { x: 610, y: 340 }, data: { label: '上期需求📜', value: readValue('B16'), role: '缓存' } },
  { id: 'B17', type: 'custom', position: { x: 610, y: 470 }, data: { label: '上期缺货率⚠️', value: readValue('B17'), role: '缓存' } },
  { id: 'B18', type: 'custom', position: { x: 610, y: 600 }, data: { label: '上期报废率📦', value: readValue('B18'), role: '缓存' } },

  // ============ 💰 财务 (x=850) — 结果 ============
  { id: 'B12', type: 'custom', position: { x: 850, y: 80 }, data: { label: '总生产成本', value: readValue('B12'), role: '=(B10+B11+B4)×B3' } },
  { id: 'B6', type: 'custom', position: { x: 850, y: 220 }, data: { label: '月收入', value: readValue('B6'), role: '=B1×MIN(B2,B3)' } },
  { id: 'B7', type: 'custom', position: { x: 850, y: 360 }, data: { label: '总成本', value: readValue('B7'), role: '=B12+B5+B9+B13' } },
  { id: 'B8', type: 'custom', position: { x: 850, y: 500 }, data: { label: '月利润', value: readValue('B8'), role: '=B6-B7' } },
])

// === 边 ===
const srColor = '#3b82f6'
const entColor = '#f59e0b'
const cflColor = '#ef4444'

const edges = ref([
  // — SetRule 实线 —
  { id: 'sr-b3-b4', source: 'B3', target: 'B4', label: '规模效应',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  // 需求基线: B1价格+B15等级+B13营销
  { id: 'sr-b1-b2', source: 'B1', target: 'B2', label: '价格',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  // 房租: B14面积+B15等级 → B5
  { id: 'sr-b14-b5', source: 'B14', target: 'B5', label: '面积·非线性折扣房租',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b15-b5', source: 'B15', target: 'B5', label: '等级·房租',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  // 现场资源限制产能 (人工效率5.0, 面积×25)
  { id: 'sr-b14-b3', source: 'B14', target: 'B3', label: '空间限产能',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b9-b3', source: 'B9', target: 'B3', label: '人工限产能',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
  // 地段流量影响需求
  { id: 'sr-b15-b2', source: 'B15', target: 'B2', label: '地段流量',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b13-b2', source: 'B13', target: 'B2', label: '营销',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b10-b12', source: 'B10', target: 'B12', label: '原料', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b11-b12', source: 'B11', target: 'B12', label: '其他', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b4-b12', source: 'B4', target: 'B12', label: '加工', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b3-b12', source: 'B3', target: 'B12', label: '产能', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b1-b6', source: 'B1', target: 'B6', label: '售价', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b2-b6', source: 'B2', target: 'B6', label: '销量', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b3-b6', source: 'B3', target: 'B6', label: '产能', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b12-b7', source: 'B12', target: 'B7', label: '生产成本', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b5-b7', source: 'B5', target: 'B7', label: '房租', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b9-b7', source: 'B9', target: 'B7', label: '人工', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b13-b7', source: 'B13', target: 'B7', label: '营销', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b6-b8', source: 'B6', target: 'B8', label: '收入', style: { stroke: srColor, strokeWidth: 2 } },
  { id: 'sr-b7-b8', source: 'B7', target: 'B8', label: '成本', style: { stroke: srColor, strokeWidth: 2 } },

  // — 品质&品牌链路: 人工→满意度→口味→知名度→需求 —
  { id: 'sr-b9-b21', source: 'B9', target: 'B21', label: '薪酬',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b3-b21', source: 'B3', target: 'B21', label: '负荷',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b14-b21', source: 'B14', target: 'B21', label: '空间上限',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b21-b20', source: 'B21', target: 'B20', label: '满意度→品质',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b3-b20', source: 'B3', target: 'B20', label: '超负荷',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b14-b20', source: 'B14', target: 'B20', label: '产能上限',
    style: { stroke: srColor, strokeWidth: 2, strokeDasharray: '4 2' }, labelStyle: { fill: srColor, fontSize: 9 } },
  { id: 'sr-b20-b19', source: 'B20', target: 'B19', label: '口碑积累',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 }, animated: true },
  { id: 'sr-b19-b2', source: 'B19', target: 'B2', label: '品牌溢价',
    style: { stroke: srColor, strokeWidth: 2 }, labelStyle: { fill: srColor, fontSize: 9 }, animated: true },

  // — B3 产能: 物理上限 (面积天花板 + 人工天花板 + 效率红利) —
  { id: 'ent-b14-b3', source: 'B14', target: 'B3', label: '面积×25',
    style: { stroke: entColor, strokeWidth: 2, strokeDasharray: '6 3' }, labelStyle: { fill: entColor, fontSize: 9 }, animated: true },
  { id: 'ent-b9-b3', source: 'B9', target: 'B3', label: '人工÷2.5',
    style: { stroke: entColor, strokeWidth: 2, strokeDasharray: '6 3' }, labelStyle: { fill: entColor, fontSize: 9 }, animated: true },
  { id: 'ent-b4-b3', source: 'B4', target: 'B3', label: '效率红利(2-B4)×200',
    style: { stroke: entColor, strokeWidth: 2, strokeDasharray: '6 3' }, labelStyle: { fill: entColor, fontSize: 9 }, animated: true },
])

// === 选中节点 ===
const selectedNode = ref('')

function getNodeLabel(id: string): string {
  return nodes.value.find(n => n.id === id)?.data.label || id
}
function getNodeValue(id: string): any {
  return nodes.value.find(n => n.id === id)?.data.value
}

const outgoingEdges = computed(() =>
  (selectedNode.value
    ? edges.value.filter(e => e.source === selectedNode.value).map(e => ({
        id: e.id,
        target: e.target,
        label: e.label || '',
        className: 'setrule',
      }))
    : [])
)
const incomingEdges = computed(() =>
  (selectedNode.value
    ? edges.value.filter(e => e.target === selectedNode.value).map(e => ({
        id: e.id,
        source: e.source,
        label: e.label || '',
        className: 'setrule',
      }))
    : [])
)

// === 编辑功能 ===
const editingNode = ref('')
const editValue = ref('')
const editInput = ref<HTMLInputElement | null>(null)

function startEdit(id: string) {
  // B1,B9,B10,B11,B13,B14,B15 可编辑 (B5/B16/B17由引擎或"下月"按钮计算)
  if (id !== 'B1' && id !== 'B9' && id !== 'B10' && id !== 'B11' && id !== 'B13' && id !== 'B14' && id !== 'B15') return
  editingNode.value = id
  const v = getNodeValue(id)
  editValue.value = v !== undefined && v !== null && v !== '' ? String(v) : ''
  nextTick(() => {
    const el = document.querySelector('.node-edit-input') as HTMLInputElement
    if (el) { el.focus(); el.select() }
  })
}

function cancelEdit() {
  editingNode.value = ''
}

function commitEdit(id: string) {
  if (editingNode.value !== id) return
  editingNode.value = ''
  const raw = editValue.value.trim()
  if (raw === '' || isNaN(Number(raw))) return

  props.engine.setCellValue(id, raw)

  if (id === 'B1') {
    triggerPropagation()
    setTimeout(() => refreshAllValues(), 300)
  } else {
    // B9/B10/B11/B13/B14/B15 → 也触发全系统传播
    triggerPropagation()
    setTimeout(() => refreshAllValues(), 300)
  }
}

// === 传播高亮系统 ===
const propagationGen = ref(0)
const propagating = ref(false)
const propMessage = ref('')

const affectedNodes = ref<Set<string>>(new Set())
const changedNodes = ref<Set<string>>(new Set())
const guideEl = ref<HTMLDetailsElement | null>(null)
const guideOpen = ref(true)

function toggleGuide() {
  guideOpen.value = !guideOpen.value
  if (guideEl.value) guideEl.value.open = guideOpen.value
}

// === 商业模拟沙盘 ===
const currentMonth = ref(1)
const cumulativeProfit = ref(0)
const yearRevenue = ref(0)
const yearCost = ref(0)
const profitableMonths = ref(0)
const yearDone = ref(false)
const monthHistory = ref<{ month: number; profit: number; revenue: number; cost: number; demand: number; sold: number }[]>([])

const monthlyProfit = computed(() => {
  const profit = Number(readValue('B8'))
  return isNaN(profit) ? 0 : profit
})

const monthProfitClass = computed(() => monthlyProfit.value >= 0 ? 'sim-positive' : 'sim-negative')
const cumProfitClass = computed(() => cumulativeProfit.value >= 0 ? 'sim-positive' : 'sim-negative')
const profitMargin = computed(() => {
  if (yearRevenue.value <= 0) return '—'
  return (cumulativeProfit.value / yearRevenue.value * 100).toFixed(1)
})

function formatMoney(v: number): string {
  const sign = v >= 0 ? '+' : ''
  return `${sign}¥${Math.round(v).toLocaleString()}`
}

// === 月度经营推进 ===
function advanceMonth() {
  const demand = Number(readValue('B2'))
  const cap = Number(readValue('B3'))
  const revenue = Number(readValue('B6')) || 0
  const cost = Number(readValue('B7')) || 0
  const profit = Number(readValue('B8')) || 0

  // 记录本月
  monthHistory.value.push({
    month: currentMonth.value,
    profit,
    revenue,
    cost,
    demand,
    sold: Math.min(demand, cap),
  })

  cumulativeProfit.value += profit
  yearRevenue.value += revenue
  yearCost.value += cost
  if (profit > 0) profitableMonths.value++

  // 计算缺货率
  const shortage = (cap >= demand || demand <= 0) ? 0 : Math.round((demand - cap) / demand * 1000) / 1000
  // 快照上期需求 → B16
  props.engine.setCellValue('B16', String(demand))
  // 写缺货率 → B17 (触发需求重算)
  props.engine.setCellValue('B17', String(shortage))
  // 计算报废率（产能过剩比例）
  const waste = (cap > demand && cap > 0) ? Math.round((cap - demand) / cap * 1000) / 1000 : 0
  props.engine.setCellValue('B18', String(waste))
  // 品牌积累: 口味×流量→知名度增长, 每月非线性衰减
  const taste = Number(readValue('B20')) || 0
  const grade = Number(readValue('B15')) || 5
  const mkt = Number(readValue('B13')) || 0
  const oldBrand = Number(readValue('B19')) || 0
  const traffic = Math.round(150 * Math.pow(grade, 1.7)) + Math.sqrt(Math.max(0, mkt)) * 15
  // 基础口碑增长: 即使0流量/0营销, 口味好也能靠街坊自发涨知名度
  const mouthGrowth = 10  // 保底值, 口味越好涨越快
  const growth = Math.round(taste * (traffic / 100 + mouthGrowth))
  // 非线性衰减: 知名度越高忘得越快(高处不胜寒)
  const decayRate = Math.max(0.05, oldBrand * 0.01)  // 知名度20时衰减率=20%
  const decay = Math.round(oldBrand * decayRate)
  const newBrand = Math.max(0, oldBrand + growth - decay)
  props.engine.setCellValue('B19', String(newBrand))
  triggerPropagation()
  setTimeout(() => refreshAllValues(), 300)

  // 推进月份
  if (currentMonth.value >= 12) {
    yearDone.value = true
  } else {
    currentMonth.value++
  }
}

function newYear() {
  currentMonth.value = 1
  cumulativeProfit.value = 0
  yearRevenue.value = 0
  yearCost.value = 0
  profitableMonths.value = 0
  yearDone.value = false
  monthHistory.value = []
  // 清空缓存
  props.engine.setCellValue('B16', '0')
  props.engine.setCellValue('B17', '0')
  refreshAllValues()
}

// 传播顺序：资源→房租→需求(含缺货惩罚)→产能计划→成本→财务
const PROPAGATION_STEPS: { nodes: string[]; edges: string[]; msg: string }[] = [
  { nodes: ['B1', 'B14', 'B15', 'B9', 'B13'], edges: [], msg: '⚡ 改售价/面积/等级/人工/营销' },
  { nodes: ['B5'], edges: ['sr-b14-b5', 'sr-b15-b5'], msg: '① SetRules: 房租=面积×等级×(20−面积×0.05) 非线性折扣' },
  { nodes: ['B16', 'B17'], edges: [], msg: '② 下月: 快照需求→B16, 缺货率→B17' },
  { nodes: ['B2'], edges: ['sr-b1-b2', 'sr-b15-b2', 'sr-b13-b2', 'sr-b17-b2', 'sr-b19-b2'], msg: '③ SetRules: 需求=交通流量×品牌留存率−缺货惩罚' },
  { nodes: ['B3'], edges: ['ent-b14-b3', 'ent-b9-b3', 'ent-b4-b3'], msg: '④ 同权共预: 产能=min(面积×25, 人工÷2.5)+效率红利' },
  { nodes: ['B4'], edges: ['sr-b3-b4'], msg: '⑤ SetRule: 规模效应 产能越高→加工成本越低(下限¥0.1)' },
  { nodes: ['B12'], edges: ['sr-b10-b12', 'sr-b11-b12', 'sr-b4-b12', 'sr-b3-b12'], msg: '⑥ 供应链→生产成本' },
  { nodes: ['B6'], edges: ['sr-b1-b6', 'sr-b2-b6', 'sr-b3-b6'], msg: '⑦ 收入=售价×实际销售(产能限制)' },
  { nodes: ['B7'], edges: ['sr-b12-b7', 'sr-b5-b7', 'sr-b9-b7', 'sr-b13-b7'], msg: '⑧ 总成本=生产+房租+人工+营销' },
  { nodes: ['B8'], edges: ['sr-b6-b8', 'sr-b7-b8'], msg: '⑨ 利润=收入-总成本' },
]

function triggerPropagation() {
  propagationGen.value++
  propagating.value = true
  const gen = propagationGen.value

  // 清空旧状态
  affectedNodes.value = new Set()
  changedNodes.value = new Set()
  clearEdgeHighlights()
  changedNodes.value.add('B1')

  // 逐步高亮传播路径
  let delay = 0
  for (const step of PROPAGATION_STEPS) {
    const stepDelay = delay
    setTimeout(() => {
      if (propagationGen.value !== gen) return // 旧的传播被新的取代
      propMessage.value = step.msg

      // 高亮节点
      for (const nid of step.nodes) {
        affectedNodes.value = new Set([...affectedNodes.value, nid])
      }
      // 高亮边
      for (const eid of step.edges) {
        const edge = edges.value.find(e => e.id === eid)
        if (edge) {
          edge.style = { ...edge.style, stroke: '#22c55e', strokeWidth: 4 }
        }
      }
    }, stepDelay)
    delay += 350 // 每步间隔 350ms
  }

  // 最后一步：恢复
  setTimeout(() => {
    if (propagationGen.value !== gen) return
    // 标记最后收敛的节点为"变化"
    const finalIds = ['B1','B2','B3','B4','B5','B6','B7','B8','B16','B17','B18','B19','B20','B21']
    changedNodes.value = new Set(finalIds)
    // 1.5秒后清除高亮
    setTimeout(() => {
      if (propagationGen.value !== gen) return
      affectedNodes.value = new Set()
      changedNodes.value = new Set()
      clearEdgeHighlights()
      propagating.value = false
      // 刷新所有值
      refreshAllValues()
    }, 1500)
  }, delay + 500)
}

function clearEdgeHighlights() {
  for (const edge of edges.value) {
    const isEnt = edge.id.startsWith('ent')
    edge.style = {
      stroke: isEnt ? entColor : srColor,
      strokeWidth: 2,
      ...(isEnt ? { strokeDasharray: '6 3' } : {}),
    }
  }
}

function isConflictedNode(id: string): boolean {
  return id === 'B3'  // 只有B3有多纠缠竞争
}
function isAffected(id: string): boolean {
  return affectedNodes.value.has(id)
}
function wasChanged(id: string): boolean {
  return changedNodes.value.has(id)
}

// 刷新所有节点的值
function refreshAllValues() {
  const ids = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15', 'B16', 'B17', 'B18', 'B19', 'B20', 'B21']
  for (const id of ids) {
    const node = nodes.value.find(n => n.id === id)
    if (node) node.data.value = readValue(id)
  }
}

// === 节点点击：选中/取消 ===
function onNodeClick({ node }: any) {
  if (selectedNode.value === node.id) {
    selectedNode.value = ''
  } else {
    selectedNode.value = node.id
  }
}

// === 定时刷新 ===
let timer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  refreshAllValues()
  timer = setInterval(refreshAllValues, 1000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.graph-editor {
  display: flex; flex-direction: column; height: 100%;
  font-size: 12px; touch-action: manipulation;
}

.graph-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 10px; background: #f5f5f7;
  border-bottom: 1px solid #d2d2d7; flex-shrink: 0; gap: 6px;
}
.graph-title { font-weight: 600; font-size: 13px; color: #1d1d1f; white-space: nowrap; }
.graph-legend { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #6e6e73; }
.legend-line { width: 18px; height: 2px; border-radius: 1px; }
.legend-line.solid { background: #3b82f6; }
.legend-line.dashed { background: transparent; border-top: 2px dashed #f59e0b; }
.legend-line.conflict { background: #ef4444; height: 3px; }
.legend-line.dashed { background: transparent; border-top: 2px dashed #f59e0b; }
.legend-line.conflict { background: #ef4444; height: 3px; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; }
.legend-dot.live { background: #22c55e; animation: pulse-dot 1s infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:.4} }

.graph-canvas { flex: 1; min-height: 300px; position: relative; }

/* 模拟沙盘状态栏 */
.sim-bar {
  display: flex; align-items: center; gap: 14px;
  padding: 4px 12px; background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px; flex-shrink: 0;
}
.sim-month { color: #475569; font-variant-numeric: tabular-nums; }
.sim-month strong { color: #1e293b; font-size: 14px; }
.sim-profit, .sim-cumulative {
  font-weight: 600; font-variant-numeric: tabular-nums;
  font-family: 'SF Mono','Menlo',monospace; font-size: 12px;
}
.sim-positive { color: #059669; }
.sim-negative { color: #dc2626; }
.sim-actions { margin-left: auto; }
.btn-reset {
  background: #0891b2 !important; color: white !important; border-color: #0891b2 !important;
  font-weight: 600 !important;
}
.btn-reset:hover { background: #0e7490 !important; }

.btn-month {
  background: #7c3aed !important; color: white !important; border-color: #7c3aed !important;
  font-weight: 600 !important;
}
.btn-month:hover { background: #6d28d9 !important; }
.btn-month:disabled { opacity: 0.5; cursor: default; }

/* 年终总结 */
.year-summary {
  border-top: 2px solid #10b981; background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
  padding: 10px 16px; flex-shrink: 0;
}
.year-summary-header {
  font-size: 13px; font-weight: 700; color: #065f46; margin-bottom: 8px;
}
.year-summary-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
}
.summary-item {
  display: flex; flex-direction: column; gap: 2px;
  padding: 6px 10px; background: rgba(255,255,255,.7);
  border-radius: 6px; border: 1px solid #d1fae5;
}
.summary-label { font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.3px; }
.summary-value {
  font-size: 14px; font-weight: 700; font-family: 'SF Mono','Menlo',monospace;
  color: #1e293b; font-variant-numeric: tabular-nums;
}

/* 大节点组标签 */
.group-labels { position: absolute; top: 0; left: 0; right: 0; pointer-events: none; z-index: 5; }
.group-label {
  position: absolute; font-size: 11px; font-weight: 700; padding: 2px 8px;
  border-radius: 4px; letter-spacing: 0.5px; opacity: 0.7;
}
.group-label.sc { left: 20px; top: 10px; color: #8b5cf6; background: #f5f3ff; }
.group-label.prod { left: 280px; top: 10px; color: #0891b2; background: #ecfeff; }
.group-label.market { left: 560px; top: 10px; color: #d97706; background: #fffbeb; }
.group-label.fin { left: 800px; top: 10px; color: #059669; background: #ecfdf5; }

/* === 节点样式 === */
:deep(.vue-flow__node-custom) {
  background: white; border: 2px solid #d2d2d7; border-radius: 8px;
  padding: 8px 12px; min-width: 110px; cursor: pointer;
  transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
:deep(.vue-flow__node-custom:hover) {
  border-color: #0071e3; box-shadow: 0 2px 8px rgba(0,113,227,.15);
}
:deep(.vue-flow__node-custom.selected) {
  border-color: #0071e3; background: #f0f7ff; box-shadow: 0 2px 12px rgba(0,113,227,.2);
}
:deep(.vue-flow__node-custom.conflicted) {
  border-color: #ef4444; background: #fef2f2;
}
:deep(.vue-flow__node-custom.affected) {
  border-color: #22c55e; background: #f0fdf4;
  box-shadow: 0 0 16px rgba(34,197,94,.35);
  animation: pulse-border 0.6s ease-in-out 3;
}
@keyframes pulse-border {
  0%,100%{ box-shadow: 0 0 8px rgba(34,197,94,.25); }
  50%{ box-shadow: 0 0 20px rgba(34,197,94,.5); }
}
:deep(.vue-flow__node-custom.changed) .node-value-num {
  color: #22c55e; font-weight: 800;
}
:deep(.vue-flow__node-custom.changed) .node-value-num.value-changed {
  animation: value-flash 0.3s ease-in-out 4;
}
@keyframes value-flash {
  0%,100%{ color: #22c55e; }
  50%{ color: #16a34a; transform: scale(1.15); }
}

.node-icon { font-size: 18px; text-align: center; margin-bottom: 2px; }
.node-label { font-weight: 600; font-size: 11px; color: #1d1d1f; text-align: center; }
.node-values { margin-top: 4px; text-align: center; position: relative; }

.node-value-row {
  display: flex; align-items: center; justify-content: center;
  gap: 3px; cursor: pointer; padding: 2px 6px; border-radius: 4px;
  transition: background 0.15s; touch-action: manipulation;
}
.node-value-row:hover { background: #e8e8ed; }
.node-value-num {
  font-size: 13px; font-weight: 700; color: #0071e3;
  font-family: 'SF Mono','Menlo',monospace; transition: all 0.2s;
}
.edit-hint { font-size: 10px; color: #aeaeb2; opacity: 0; transition: opacity 0.15s; }
.node-value-row:hover .edit-hint { opacity: 1; }
/* 触摸设备编辑提示常显 */
@media (hover: none) and (pointer: coarse) {
  .edit-hint { opacity: 0.5; }
  .node-value-row { min-height: 28px; }
}

.node-edit-row { padding: 1px 0; }
.node-edit-input {
  width: 70px; text-align: center;
  font-size: 13px; font-family: 'SF Mono','Menlo',monospace;
  font-weight: 700; color: #0071e3; background: white;
  border: 2px solid #0071e3; border-radius: 4px;
  padding: 2px 4px; outline: none;
}

.node-role-badge {
  display: inline-block; margin-top: 2px;
  font-size: 9px; padding: 1px 5px; border-radius: 3px;
  background: #e8e8ed; color: #6e6e73;
}

/* === 传播状态 === */
.propagation-bar {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 12px; background: #f0fdf4;
  border-top: 1px solid #bbf7d0; color: #166534;
  font-size: 11px; font-weight: 500; flex-shrink: 0;
}
.prop-spinner { font-size: 16px; animation: spin 1s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

/* === 详情面板 === */
.node-detail-panel {
  border-top: 1px solid #d2d2d7; background: #fafafa;
  padding: 8px 12px; max-height: 180px; overflow-y: auto; flex-shrink: 0;
}
.detail-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
}
.detail-header strong { font-size: 13px; }
.node-value-big {
  font-size: 15px; font-weight: 700; color: #0071e3;
  font-family: 'SF Mono','Menlo',monospace;
}
.close-btn { margin-left: auto; background: none; border: none; cursor: pointer; color: #86868b; font-size: 14px; }
.detail-body { display: flex; gap: 20px; flex-wrap: wrap; }
.detail-section { flex: 1; min-width: 140px; }
.detail-section h4 { font-size: 10px; text-transform: uppercase; color: #86868b; margin-bottom: 4px; }
.edge-info {
  display: flex; align-items: center; gap: 4px; padding: 2px 0; font-size: 11px;
}
.edge-info.setrule { color: #3b82f6; }
.edge-info.entangle { color: #d97706; }
.edge-arrow { font-size: 13px; }
.edge-desc { font-size: 10px; opacity: 0.7; }
.weight-badge {
  font-size: 9px; padding: 0 4px; border-radius: 3px;
  background: #e8e8ed; color: #6e6e73;
}
.no-edges { font-size: 10px; color: #aeaeb2; font-style: italic; }
.detail-warning {
  margin-top: 6px; padding: 4px 8px; background: #fef2f2;
  border: 1px solid #fecaca; border-radius: 4px; font-size: 11px; color: #dc2626; width: 100%;
}
.node-hint {
  border-top: 1px solid #d2d2d7; padding: 10px;
  text-align: center; font-size: 12px; color: #86868b; flex-shrink: 0;
}

/* 📖 推演指南 — headless <details> 模式 */
.guide-panel {
  border-top: 2px solid #059669;
  background: linear-gradient(135deg, #f0fdf4, #f8fafc);
  flex-shrink: 0;
  max-height: 45vh;
  overflow-y: auto;
}
.guide-panel[open] { padding-bottom: 4px; }

.guide-header {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; cursor: pointer; user-select: none;
  font-size: 12px; font-weight: 700; color: #065f46;
  list-style: none; /* 隐藏默认三角 */
}
.guide-header::-webkit-details-marker { display: none; }
.guide-header:hover { background: rgba(5,150,105,.06); }
.guide-arrow { font-size: 10px; transition: transform .2s; color: #6b7280; }
.guide-panel[open] .guide-arrow { transform: rotate(180deg); }

.guide-body {
  padding: 0 14px 6px;
  display: flex; flex-direction: column; gap: 4px;
}

/* 内层 disclosure 子项 */
.g-section {
  border: 1px solid #d1fae5; border-radius: 5px;
  background: rgba(255,255,255,.6);
}
.g-section summary {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 10px; cursor: pointer; user-select: none;
  font-size: 11px; font-weight: 600; color: #065f46;
  list-style: none; border-radius: 5px;
}
.g-section summary::-webkit-details-marker { display: none; }
.g-section summary::before {
  content: '▸'; font-size: 10px; color: #6b7280;
  transition: transform .15s; flex-shrink: 0;
}
.g-section[open] summary::before { transform: rotate(90deg); }
.g-section summary:hover { background: rgba(5,150,105,.05); }
.g-section[open] summary { border-bottom: 1px solid #d1fae5; }
.g-section > div, .g-section > p, .g-section > ul {
  padding: 4px 10px 8px; font-size: 11px; color: #374151; line-height: 1.5;
}
.g-section ul { margin: 2px 0; padding-left: 24px; }
.g-section li { line-height: 1.6; }
.g-section kbd {
  font-size: 10px; padding: 1px 4px; background: #e8e8ed;
  border-radius: 3px; border: 1px solid #d2d2d7; font-family: monospace;
}

/* 节点速查表 */
.g-table { display: flex; flex-direction: column; gap: 1px; font-size: 10px; }
.g-tr { display: grid; grid-template-columns: 48px 72px 1fr 32px; gap: 3px; padding: 2px 4px; align-items: center; }
.g-tr:nth-child(even) { background: rgba(255,255,255,.5); }
.g-th { font-weight: 600; color: #6b7280; font-size: 9px; text-transform: uppercase; letter-spacing: .3px; }
.g-yes { color: #059669; font-weight: 600; font-size: 9px; text-align: center; }
.g-no { color: #6b7280; font-size: 9px; text-align: center; }

/* 公式卡片 */
.g-formula { margin: 4px 0; padding: 5px 8px; background: rgba(255,255,255,.5); border-radius: 4px; border: 1px solid #d1fae5; }
.gf-title { font-size: 11px; font-weight: 600; color: #065f46; margin-bottom: 2px; }
.g-formula code {
  display: block; font-size: 10px; color: #1e293b;
  background: #f1f5f9; padding: 2px 6px; border-radius: 3px;
  margin: 2px 0; font-family: 'SF Mono','Menlo',monospace; line-height: 1.5;
}
.gf-note { font-size: 10px !important; color: #6b7280 !important; margin-top: 2px !important; }

/* 策略卡片 */
.g-cards { display: flex; gap: 6px; flex-wrap: wrap; }
.g-card { flex: 1; min-width: 120px; padding: 5px 8px; background: rgba(255,255,255,.5); border-radius: 4px; border: 1px solid #d1fae5; }
.gc-icon { font-size: 16px; text-align: center; }
.gc-name { font-size: 11px; font-weight: 600; color: #065f46; text-align: center; margin: 2px 0; }
.gc-desc { font-size: 10px; color: #374151; line-height: 1.4; }
.gc-tip { font-size: 10px; color: #d97706; line-height: 1.4; margin-top: 2px; }

/* 📱 移动端响应式 */
@media (max-width: 640px) {
  .graph-toolbar {
    flex-wrap: wrap; gap: 3px; padding: 4px 6px;
  }
  .graph-title { font-size: 11px; }
  .graph-legend { gap: 4px; }
  .legend-item { font-size: 9px; }
  .legend-line { width: 12px; }

  .sim-bar {
    flex-wrap: wrap; gap: 4px 8px; padding: 3px 6px;
    font-size: 11px;
  }
  .sim-month { font-size: 11px; }
  .sim-month strong { font-size: 12px; }
  .sim-profit, .sim-cumulative { font-size: 11px; }

  .btn-sm { font-size: 10px !important; padding: 1px 5px !important; }

  .graph-canvas { min-height: 200px; }

  .g-tr { grid-template-columns: 32px 60px 1fr 26px; font-size: 9px; }

  .g-cards { flex-direction: column; }
  .g-card { min-width: auto; }

  .guide-panel { max-height: 35vh; }

  .node-detail-panel { font-size: 10px; padding: 6px 8px; max-height: 140px; }
}

@media (max-width: 400px) {
  .graph-legend { display: none; }
  .graph-title { font-size: 10px; }
}
</style>
