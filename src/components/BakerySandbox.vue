<template>
  <!-- uiSignal 驱动 UI 刷新：引擎每次 propagate 完成时自增 -->
  <span style="display:none">{{ engine?.uiSignal?.value }}</span>
  <div class="command-center">
    <n-scrollbar class="cc-scroll" style="flex:1">
      <div class="cc-body-inner">
        <div class="cc-header">
          <span class="title">🥖 面包店沙盘</span>
          <span class="month">📅 {{ m }}月 <span class="season-tag" :style="{ color: seasonColor, background: seasonBg }">{{ seasonLabel }}</span></span>
        </div>

        <!-- 年度利润折线图 -->
        <div class="year-chart-wrap" v-if="annualProfits.length > 0">
          <div class="yc-header">📊 年度利润</div>
          <div class="yc-chart">
            <div
              v-for="(val, idx) in annualProfits"
              :key="idx"
              class="yc-bar"
              :style="{
                height: Math.max(2, Math.abs(val) / maxAnnual * 80) + '%',
                background: val >= 0 ? 'linear-gradient(180deg, #4CAF50, #2E7D32)' : 'linear-gradient(180deg, #f44336, #B71C1C)',
                opacity: idx === annualProfits.length - 1 ? 1 : 0.6,
              }"
              :title="'第' + (idx + 1) + '年: ' + (val >= 0 ? '+' : '') + '¥' + Math.abs(val).toLocaleString()"
            ></div>
          </div>
          <div class="yc-labels">
            <span v-for="(_, idx) in annualProfits" :key="idx" class="yc-label">
              {{ idx + 1 }}年
            </span>
          </div>
        </div>

        <!-- 目标进度条 -->
        <div class="goal-track" v-if="!isVictory">
          <div class="gt-header">
            <span>🏆 目标</span>
            <span class="gt-pct">{{ goalPct }}%</span>
          </div>
          <div class="gt-track">
            <div class="gt-fill" :style="{ width: Math.min(100, goalPct) + '%' }"></div>
            <div class="gt-label">{{ short(t) }} / ¥100万</div>
          </div>
        </div>
        <div v-else class="victory-banner">
          <div class="vb-icon">👑</div>
          <div class="vb-text">🏆 面包店大亨</div>
          <div class="vb-sub">累计盈利 ¥100万 达成！</div>
        </div>

        <!-- 北极星指标 -->
        <div class="hero-metrics">
          <div class="hm-card" :class="p >= 0 ? 'profit' : 'loss'">
            <div class="hm-top">
              <span class="hm-label">📈 本月利润</span>
              <!-- @vue-ignore -->
              <n-tag v-if="monthLog.length > 0" size="tiny" :bordered="false" :color="{ text: p - tailP >= 0 ? '#4CAF50' : '#f44336', border: 'transparent' }">
                {{ p - tailP >= 0 ? '▲' : '▼' }}{{ tailP ? Math.round(Math.abs((p - tailP) / tailP) * 100) : 0 }}%
              </n-tag>
            </div>
            <span class="hm-value" :class="p >= 0 ? 'clr-profit' : 'clr-loss'">{{ fm(p) }}</span>
          </div>
          <div class="hm-card" :class="t >= 0 ? 'profit' : 'loss'">
            <span class="hm-label">💰 累计现金流</span>
            <span class="hm-value" :class="t >= 0 ? 'clr-profit' : 'clr-loss'">{{ fm(t) }}</span>
            <n-progress
              type="line"
              :percentage="cashPct"
              :height="3"
              :border-radius="2"
              :color="t >= 0 ? '#4CAF50' : '#f44336'"
              :rail-color="'#1a2a4a'"
              :indicator-placement="'inside'"
              :show-indicator="false"
            />
          </div>
        </div>

        <!-- 士气/疲劳 -->
        <div class="fatigue-section">
          <div class="fs-header">
            <span>⚡ 士气 / 疲劳</span>
            <!-- @vue-ignore -->
            <n-tag size="tiny" :bordered="false" :color="{ text: fatText, border: 'transparent', color: fatBg }">
              {{ c.FAT }}%
            </n-tag>
            <span class="fs-eff">×{{ fsk(c.FAT) }}</span>
          </div>
          <div class="fatigue-track">
            <div class="ft-bg">
              <div class="ft-zone" style="left:0;width:20%;background:#4CAF50" title="爆种"></div>
              <div class="ft-zone" style="left:20%;width:40%;background:#8BC34A" title="正常"></div>
              <div class="ft-zone" style="left:60%;width:20%;background:#FFC107" title="摸鱼"></div>
              <div class="ft-zone" style="left:80%;width:20%;background:#f44336" title="过劳"></div>
            </div>
            <div class="ft-pointer" :style="{ left: Math.min(100, Math.max(0, c.FAT)) + '%' }" :class="fatClass"></div>
          </div>
          <div class="ft-labels">
            <span>爆种</span><span>正常</span><span>摸鱼</span><span>过劳</span>
          </div>
        </div>

        <!-- 环境指标 -->
        <div class="env-grid">
          <div class="env-card">
            <span class="env-label">😊 满意度</span>
            <span class="env-value" :style="{ color: satColor }">{{ satPct }}%</span>
          </div>
          <div class="env-card">
            <span class="env-label">⭐ 知名度</span>
            <span class="env-value" style="color:#FFD700">{{ Math.round(c.BRAND) }}</span>
          </div>
          <div class="env-card">
            <span class="env-label">📦 总出货</span>
            <span class="env-value" style="color:#4CAF50">{{ short(c.TRAFFIC) }}</span>
          </div>
          <div class="env-card">
            <span class="env-label">📊 需求/产能</span>
            <span class="env-value" style="color:#8BC34A">{{ demandDisplay }}</span>
          </div>
        </div>

        <!-- 季节条 -->
        <div class="season-card">
          <div class="sc-label">📅 季节历 <span class="sc-hint" :style="{ color: nextSeasonFactor >= 1.20 ? '#FFD700' : nextSeasonFactor <= 0.85 ? '#87CEEB' : '#9a9a9a' }">→下月{{ nextSeasonLabel }}×{{ nextSeasonFactor.toFixed(2) }}</span></div>
          <div class="season-bar">
            <div
              v-for="(sf, i) in [0.85,1.10,0.95,1.00,1.00,0.90,0.85,0.85,1.25,1.10,1.00,1.30]"
              :key="i"
              class="sb-marker"
              :class="{
                'sb-current': ((m-1)%12) === i,
                'sb-next': ((m)%12) === i,
                'sb-peak': sf >= 1.20,
                'sb-low': sf <= 0.85,
              }"
              :title="(i+1)+'月 ×'+sf.toFixed(2)"
            >{{ i+1 }}</div>
            
          </div>
        </div>

        <!-- 策略指纹 -->
        <div class="fingerprint-card">
          <div class="fp-header">
            <span>🧬 策略指纹</span>
            <span class="fp-subtitle">{{ fingerprintLabel }}</span>
          </div>
          <div class="fp-bars">
            <div class="fp-bar-row">
              <span class="fp-icon">🏠</span>
              <span class="fp-name">社区</span>
              <div class="fp-track">
                <div class="fp-fill" :style="{ width: fpCommunity + '%', background: '#4CAF50' }"></div>
              </div>
              <span class="fp-pct" :style="{ color: fpCommunity > 50 ? '#4CAF50' : '#5a5a5a' }">{{ fpCommunity }}%</span>
            </div>
            <div class="fp-bar-row">
              <span class="fp-icon">🏭</span>
              <span class="fp-name">大厂</span>
              <div class="fp-track">
                <div class="fp-fill" :style="{ width: fpFactory + '%', background: '#FF9800' }"></div>
              </div>
              <span class="fp-pct" :style="{ color: fpFactory > 50 ? '#FF9800' : '#5a5a5a' }">{{ fpFactory }}%</span>
            </div>
            <div class="fp-bar-row">
              <span class="fp-icon">✨</span>
              <span class="fp-name">高奢</span>
              <div class="fp-track">
                <div class="fp-fill" :style="{ width: fpLuxury + '%', background: '#e040fb' }"></div>
              </div>
              <span class="fp-pct" :style="{ color: fpLuxury > 50 ? '#e040fb' : '#5a5a5a' }">{{ fpLuxury }}%</span>
            </div>
          </div>
          <div class="fp-insight">{{ fingerprintInsight }}</div>
        </div>

        <!-- 产能利用率 + 成本结构 -->
        <div class="ops-card">
          <div class="ops-row">
            <span class="ops-label">🏭 产能利用率</span>
            <span class="ops-value" :class="capacityUtil >= 80 ? 'clr-profit' : capacityUtil >= 50 ? '' : 'clr-loss'">
              {{ capacityUtil }}%
            </span>
          </div>
          <div class="ops-bar-track">
            <div class="ops-bar-fill" :style="{
              width: Math.min(100, capacityUtil) + '%',
              background: capacityUtil >= 80 ? '#4CAF50' : capacityUtil >= 50 ? '#FFC107' : '#f44336'
            }"></div>
          </div>
          <div class="ops-cost">
            <span class="ops-label">💸 成本结构</span>
            <div class="cost-strip">
              <div
                v-for="(item, idx) in costItems"
                :key="idx"
                class="cs-seg"
                :style="{ flex: item.pct, background: item.color }"
                :title="item.label + ': ¥' + item.value.toLocaleString() + ' (' + item.pct + '%)'"
              ></div>
            </div>
            <div class="cost-labels">
              <span v-for="(item, idx) in costItems.filter(x => x.pct > 0)" :key="idx" :style="{ color: item.color }">
                {{ item.label }}
              </span>
            </div>
          </div>
        </div>

        <!-- 决策面板 -->
        <div class="decision-panels">
          <!-- 人事 -->
          <div class="dp-group">
            <div class="dp-title">👥 人事</div>
            <div class="dp-row">
              <span class="dp-label">人数</span>
              <n-slider :min="1" :max="20" :step="1" v-model:value="sl[1].v" @update:value="onSliderChange('B24')" style="flex:1" />
              <span class="dp-val">{{ sl[1].v }}人</span>
            </div>
            <div class="dp-row">
              <span class="dp-label">工资</span>
              <n-slider :min="800" :max="10000" :step="200" v-model:value="sl[6].v" @update:value="onSliderChange('B26')" style="flex:1" />
              <span class="dp-val">¥{{ sl[6].v }}<span class="dp-sub">/人</span></span>
            </div>
            <div class="dp-row">
              <span class="dp-label">培训</span>
              <n-slider :min="0" :max="1000" :step="50" v-model:value="sl[2].v" @update:value="onSliderChange('B25')" style="flex:1" />
              <span class="dp-val">¥{{ sl[2].v }}</span>
            </div>
          </div>
          <!-- 市场 -->
          <div class="dp-group">
            <div class="dp-title">📢 市场</div>
            <div class="dp-row">
              <span class="dp-label">售价</span>
              <n-slider :min="5" :max="40" :step="1" v-model:value="sl[0].v" @update:value="onSliderChange('B1')" style="flex:1" />
              <span class="dp-val">¥{{ sl[0].v }}</span>
            </div>
            <div class="dp-row">
              <span class="dp-label">营销</span>
              <n-slider :min="0" :max="20000" :step="500" v-model:value="sl[3].v" @update:value="onSliderChange('B13')" style="flex:1" />
              <span class="dp-val">¥{{ short(sl[3].v) }}</span>
            </div>
          </div>
          <!-- 供应链 -->
          <div class="dp-group">
            <div class="dp-title">🥖 供应链</div>
            <div class="dp-row">
              <span class="dp-label">原料</span>
              <n-slider :min="1" :max="6" :step="0.1" v-model:value="sl[4].v" @update:value="onSliderChange('B10')" style="flex:1" />
              <span class="dp-val">¥{{ sl[4].v }}</span>
            </div>
            <div class="dp-row">
              <span class="dp-label">面积</span>
              <n-slider :min="30" :max="300" :step="10" v-model:value="sl[5].v" @update:value="onSliderChange('B14')" style="flex:1" />
              <span class="dp-val">{{ sl[5].v }}m²</span>
            </div>
            <div class="dp-row">
              <span class="dp-label">地段 ⭐</span>
              <n-slider :min="1" :max="10" :step="1" v-model:value="sl[7].v" @update:value="onSliderChange('B15')" style="flex:1" />
              <span class="dp-val">{{ sl[7].v }}级</span>
            </div>
          </div>
        </div>
      </div>
    </n-scrollbar>

    <!-- 节点情报 Bottom Sheet -->
    <Transition name="sheet">
      <div v-if="selectedNode && nodeInfo" key="inspector" class="inspector-sheet">
        <!-- 顶部标题栏 -->
        <div class="is-handle"><div class="is-handle-bar"></div></div>
        <div class="is-header">
          <span class="is-icon">{{ nodeInfo.icon }}</span>
          <span class="is-name">{{ nodeInfo.name }}</span>
          <span class="is-value">{{ fm(getLiveValue(selectedNode)) }}</span>
          <button class="is-close" @click="$emit('clearNode')">✕</button>
        </div>

        <!-- 业务解释 -->
        <div class="is-desc">{{ nodeInfo.desc }}</div>

        <!-- 详细数据 -->
        <div class="is-detail-row">
          <span class="is-dl">代码</span><span class="is-dd">{{ selectedNode }}</span>
          <span class="is-dl">当前值</span><span class="is-dd" style="color:#4CAF50">{{ fm(getLiveValue(selectedNode)) }}</span>
        </div>

        <!-- 上下游 -->
        <div class="is-section-title">⬆ 上游影响因素</div>
        <div class="is-links" v-if="nodeInfo.inputs.length > 0">
          <div v-for="src in nodeInfo.inputs" :key="'in-' + src" class="is-link-item" @click="switchNode(src)">
            <span class="is-li-icon">{{ getNodeInfo(src)?.icon || '📦' }}</span>
            <span class="is-li-name">{{ getNodeInfo(src)?.name || src }}</span>
            <span class="is-li-code">{{ src }}</span>
            <span class="is-li-val">{{ short(getLiveValue(src)) }}</span>
            <span class="is-li-arrow">→</span>
          </div>
        </div>
        <div v-else class="is-empty">无上游依赖（根节点，可直接编辑）</div>

        <div class="is-section-title">⬇ 下游波及节点</div>
        <div class="is-links" v-if="nodeInfo.outputs.length > 0">
          <div v-for="tgt in nodeInfo.outputs" :key="'out-' + tgt" class="is-link-item" @click="switchNode(tgt)">
            <span class="is-li-arrow" style="color:#4CAF50">→</span>
            <span class="is-li-icon">{{ getNodeInfo(tgt)?.icon || '📦' }}</span>
            <span class="is-li-name">{{ getNodeInfo(tgt)?.name || tgt }}</span>
            <span class="is-li-code">{{ tgt }}</span>
            <span class="is-li-val">{{ short(getLiveValue(tgt)) }}</span>
          </div>
        </div>
        <div v-else class="is-empty">无下游影响（终点节点）</div>
      </div>
    </Transition>

    <!-- 底部控制栏 -->
    <div class="bottom-bar">
      <div class="bb-row">
        <n-button size="tiny" tertiary round @click="undo" :disabled="snapshotStack.length === 0" title="回退">◀</n-button>
        <n-button size="tiny" tertiary round @click="redo" :disabled="redoStack.length === 0" title="重做">▶</n-button>
        <n-button v-if="!isVictory" type="success" size="large" round @click="nx" :disabled="t <= -200000" class="bb-main">
          ▶ 推进下月
        </n-button>
        <n-button v-else type="warning" size="large" round @click="reset" class="bb-main" style="background:#3a2a00!important;border-color:#5a4a00!important">
          👑 再玩一次
        </n-button>
        <n-button size="tiny" tertiary round @click="reset" title="重置">🔄</n-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { NScrollbar, NSlider, NButton, NProgress, NTag } from 'naive-ui'
import { useLogger } from '@meshflow/logger'
import { NODE_INFO } from '../data/node-info'
import type { NodeInfo } from '../data/node-info'

// 安全取数 — 防 NaN/undefined/null
function safe(n: any, fallback = 0): number {
  if (n === null || n === undefined) return fallback
  const v = Number(n)
  return Number.isFinite(v) ? v : fallback
}

let _rulesLoaded = false

// ===== V7 SetRules + Entangle (Gemini review fixes) =====
function setupBakeryRules(eng: any) {
  if (!eng?.raw || _rulesLoaded) return
  _rulesLoaded = true
  const eg = eng.raw
  
// ============ SetRules（单向无环） ============
  
// B9 = B24×B26×(1+B15×0.10×max(0,1-B24×0.05))  // V7: reduced grade multiplier
  eg.config.SetRules(['B24','B26','B15'], 'B9', 'value', {
    triggerKeys: ['value','value','value'],
    logic: ({slot}:any) => {
      const h=slot.triggerTargets[0]?.value??8,w=slot.triggerTargets[1]?.value??5000
      const g=slot.triggerTargets[2]?.value??7
      return Math.round(h*w*(1+g*0.10*Math.max(0,1-h*0.05)))
    }
  })
  
// B5 = round(面积×地段×(20+800/(面积+15)))  // V7: smooth rent decay
  eg.config.SetRules(['B14','B15'], 'B5', 'value', {
    triggerKeys: ['value','value'],
    logic: ({slot}:any) => {
      const a=slot.triggerTargets[0]?.value??150,g=slot.triggerTargets[1]?.value??7
      const dp = dynParams(g, a)
      const rate = dp.rb + dp.rd / (a + 15)
      return Math.max(0,Math.round(a*g*rate))
    }
  })
  
// B12 = round(B10×(1-min(0.4,B3×0.00006))×100)/100  // V7: softer scale discount
  eg.config.SetRules(['B10','B3'], 'B12', 'value', {
    triggerKeys: ['value','value'],
    logic: ({slot}:any) => {
      const b10=slot.triggerTargets[0]?.value??3,b3=slot.triggerTargets[1]?.value??1000
      return Math.round(b10*(1-Math.min(0.4,b3*0.00006))*100)/100
    }
  })

  // B28 = ingredient quality: B10 tier + B26 salary bonus (no B3 scale)  // V7
  eg.config.SetRules(['B10','B26'], 'B28', 'value', {
    triggerKeys: ['value','value'],
    logic: ({slot}:any) => {
      const b10=slot.triggerTargets[0]?.value??3, b26=slot.triggerTargets[1]?.value??4000
      const qBase = Math.max(0.15, Math.min(0.95, b10 / 5.5))
      const qSalary = b26 > 3000 ? Math.min(0.18, (b26 - 3000) / 28000) : 0
      return Math.round(Math.min(1.0, qBase + qSalary) * 1000) / 1000
    }
  })


  // B20 = 口味/品质 = B21满意度(45%) + B28原料品质(55%)
  eg.config.SetRules(['B21','B28'], 'B20', 'value', {
    triggerKeys: ['value','value'],
    logic: ({slot}:any) => {
      const b21 = slot.triggerTargets[0]?.value ?? 0.8
      const b28 = slot.triggerTargets[1]?.value ?? 0.6
      return Math.round((b21 * 0.45 + b28 * 0.55) * 100) / 100
    }
  })

  // B2 = 客流×转化×季节 — V7: foot traffic independent of price, soft conversion
  const SEASON = [0.85, 1.10, 0.95, 1.00, 1.00, 0.90, 0.85, 0.85, 1.25, 1.10, 1.00, 1.30]
  // V8: 所有路线特化参数改为连续函数（无if/else硬编码）
  const dynParams = (g: number, a: number) => {
    const gf = Math.max(0, Math.min(1, (g - 2) / 7))   // grade2→0  grade9→1
    const lf = Math.max(0, Math.min(1, (g - 6) / 4)) * Math.max(0, Math.min(1, (120 - a) / 40))  // luxury
    const ff = Math.max(0, Math.min(1, (a - 100) / 50)) * Math.max(0, Math.min(1, (5 - g) / 3))  // factory
    const cf = Math.max(0, Math.min(1, 1 - ff - lf))
    return {
      cv_b: 0.75 * cf + 0.70 * ff + 0.60 * lf,
      pb_mi: 22 * cf + 20 * ff + 30 * lf,
      pb_s: 0.03 * cf + 0.02 * ff + 0.01 * lf,
      pb_fl: 0.40 * cf + 0.40 * ff + 0.60 * lf,
      cv_s: 0.80 * cf + 0.80 * ff + 0.60 * lf,
      pr: 0.04 * cf + 0.06 * ff + 0.12 * lf,
      eq: 1200 * cf + 1200 * ff + 3000 * lf,
      rb: Math.round(22 * cf + 10 * ff + 18 * lf),
      rd: Math.round(2000 * cf + 800 * ff + 1500 * lf),
      ua: Math.round(18 * cf + 18 * ff + 22 * lf),
      us: Math.round(120 * cf + 120 * ff + 180 * lf),
      bp_c: Math.round(12 * cf + 12 * ff + 22 * lf),
      bp_cap: Math.round(45 * cf + 45 * ff + 60 * lf),
      bg1: Math.round(8 * cf + 8 * ff + 14 * lf),
      bg2: Math.round(10 * cf + 10 * ff + 18 * lf),
      apm: Math.round(40 * cf + 45 * ff + 40 * lf),
      spm: Math.round(1800 * cf + 2000 * ff + 1800 * lf),
      bbp: 1200, bbpr: 0.25,
      // 疲劳参数 — 社区容易恢复, 工厂高压累积快
      frh: Math.round(30 * cf + 45 * ff + 35 * lf),   // FAT累积速率
      ftr: Math.round(8 * cf + 15 * ff + 12 * lf),    // B2B总UR疲劳速率
      ful: 0.80 * cf + 0.70 * ff + 0.75 * lf,          // 恢复触发阈值
    }
  }
  const brandP = (brand: number, grade: number, area?: number) => {
    const dp = area ? dynParams(grade, area) : { bp_c: 12, bp_cap: 45 }
    const raw = dp.bp_c * Math.log(1 + brand / 25)
    const gradeF = Math.min(1, (grade - 1) / 8)
    return Math.round(Math.min(dp.bp_cap, raw * gradeF))
  }
  const pbF = (price: number, pb_mi: number, pb_s: number, pb_fl: number) => {
    if (price < 15) return 1 + (15 - price) * 0.10
    if (price <= pb_mi) return 1.0
    return Math.max(pb_fl, 1 - (price - pb_mi) * pb_s)
  }
  eg.config.SetRules(['B1','B15','B13','BRAND','B21','B26','B14','M1','B28'], 'B2', 'value', {
    triggerKeys: ['value','value','value','value','value','value','value','value','value'],
    logic: ({slot}:any) => {
      const b1=slot.triggerTargets[0]?.value??18,g=slot.triggerTargets[1]?.value??3
      const mkt=slot.triggerTargets[2]?.value??1000,brand=slot.triggerTargets[3]?.value??0
      const b21=slot.triggerTargets[4]?.value??0.8,b26=slot.triggerTargets[5]?.value??4000
      const b14=slot.triggerTargets[6]?.value??60
      const mIdx=((slot.triggerTargets[7]?.value??1)-1)%12
      const sz=SEASON[Math.max(0,Math.min(11,Math.floor(mIdx)))]||1.0
      const b28=slot.triggerTargets[8]?.value??0.6
      // Foot traffic: location + visibility + marketing + word-of-mouth (price NOT here)
      let ft=(500+400*Math.min(g,6))
      ft+=Math.round(Math.sqrt(b14)*15)
      ft+=Math.round(Math.pow(Math.max(0,mkt),0.45)*0.8)
      ft+=Math.round(brand*0.8)
      if(g>=3&&g<=5&&b14<=90) ft=Math.round(ft*1.15)  // community density bonus
      const localBase=Math.max(0,Math.round(ft))
      // Brand premium (log scale, grade-gated)
      const dpB=brandP(brand,g,b14)
      const ma=Math.max(12+g*2.5, 12+g*2.5+dpB+b21*2+b28*3+b26/2500)
      // V8 dynamic params (no hardcoded route)
      const dp=dynParams(g,b14)
      // Soft conversion: no cliff, smooth decay when price > ma
      const gap=Math.max(0,b1-ma)
      let conv=dp.cv_b*pbF(b1,dp.pb_mi,dp.pb_s,dp.pb_fl)*(ma/(ma+gap*dp.cv_s))
      conv=Math.min(0.85,Math.max(0.04,conv))
      // Season + brand loyalty
      const loyalSz=brand>=200?Math.min(sz,1.08):(brand>=100?Math.min(sz,1.12):sz)
      const finalSz=Math.max(loyalSz,brand>=200?0.95:(brand>=100?0.90:sz))
      let localDemand=Math.max(0,Math.round(localBase*conv*finalSz))
      // Tourist demand
      let tourDemand=0
      if(g>=5){
        const tourBase=(g-4)*500*pbF(b1,dp.pb_mi,dp.pb_s,dp.pb_fl)
        const tourMkt=Math.round(Math.sqrt(Math.max(0,mkt))*5)*(0.5+brand/400)
        const tourTotal=Math.round(tourBase+tourMkt)
        const tourMa=Math.max(8,8+g*2+mkt/4000+brand*0.25)
        const tourConv=b1<=tourMa?Math.min(0.75,0.30+(tourMa-b1)/tourMa*0.35):Math.max(0.02,0.25*tourMa/b1)
        tourDemand=Math.max(0,Math.round(tourTotal*tourConv*sz))
      }
      return Math.max(0, localDemand + tourDemand)
    }
  })
  
// B6 = 实际销量 min(B2,B3)
  eg.config.SetRules(['B2','B3'], 'B6', 'value', {
    triggerKeys: ['value','value'],
    logic: ({slot}:any) => Math.min(slot.triggerTargets[0]?.value??0,slot.triggerTargets[1]?.value??0)
  })
  
// B7 = 总收入 — B2B产出×B21满意度系数 — 零售B6×B1 + B2B(1000/人, 25%零售×品质系数)
  eg.config.SetRules(['B6','B1','B14','B3','B24','B28','B21'], 'B7', 'value', {
    triggerKeys: ['value','value','value','value','value','value'],
    logic: ({slot}:any) => {
      const b6=slot.triggerTargets[0]?.value??0,b1=slot.triggerTargets[1]?.value??16
      const b14=slot.triggerTargets[2]?.value??60,b3=slot.triggerTargets[3]?.value??0
      const b24=slot.triggerTargets[4]?.value??3
      const b28=slot.triggerTargets[5]?.value??0.6
      const retail=b6*b1
      let ws=0
      if(b14>=150){
        const remaining=Math.max(0,b3-b6)
        const bbpEff=1200  // V9: 固定1200/人, 满意度不砍产量只影响售价
	        const b2bCap=b24*bbpEff
        const spotCap=Math.round((b14-150)*500)
        const wSold=Math.min(b2bCap+spotCap,remaining)
        // 品质系数: B28<0.4→B2B价打7折, B28<0.6→9折, B28≥0.6→全额
        const qualityMult = b28 >= 0.6 ? 1.0 : b28 >= 0.4 ? 1.0 - (0.6 - b28) * 0.5 : 0.9 - (0.4 - b28) * 1.0
        // V8: 满意度也影响B2B售价 — 低满意=差品控=客户压价
        const b2bPriceMult = Math.min(b1, 22) * 0.25 * Math.max(0.5, qualityMult)
        ws=Math.round(wSold*b2bPriceMult)
      }
      return retail+ws
    }
  })
  
// B8 = 月利润
  eg.config.SetRules(['B7','B12','B1','B4','B3','B5','B9','B24','B25','B13','B14','B6','B10'], 'B8', 'value', {
    triggerKeys: ['value','value','value','value','value','value','value','value','value','value','value','value','value'],
    logic: ({slot}:any) => {
            const b7=slot.triggerTargets[0]?.value??0,b12=slot.triggerTargets[1]?.value??0
        const b1=slot.triggerTargets[2]?.value??16,b4=slot.triggerTargets[3]?.value??0
        const b3=slot.triggerTargets[4]?.value??0,b5=slot.triggerTargets[5]?.value??0
        const b9=slot.triggerTargets[6]?.value??0,b24=slot.triggerTargets[7]?.value??8
        const b25=slot.triggerTargets[8]?.value??100,b13=slot.triggerTargets[9]?.value??0
        const b14=slot.triggerTargets[10]?.value??150,b6=slot.triggerTargets[11]?.value??0
        const b10=slot.triggerTargets[12]?.value??3
      const dp2=dynParams(slot.triggerTargets[5]?.value??3, slot.triggerTargets[10]?.value??60)
      const pkg=Math.round(b1*dp2.pr),util=Math.round(b14*dp2.ua+b24*dp2.us),eq=dp2.eq
      const trn=b25*b24,misc=Math.round(0.02*b24*1000)
      const retailCogs=Math.round((b12+pkg+b4)*Math.min(b6,b3))
      let wsCogs=0
      if(b14>=150){
        const remaining=Math.max(0,b3-b6)
        const bbpEff=1200  // V9: 固定1200/人, 满意度不砍产量只影响售价
	        const b2bCap=b24*bbpEff
        const spotCap=Math.round((b14-150)*500)
        const wSold=Math.min(b2bCap+spotCap,remaining)
        wsCogs=Math.round(wSold*b10*0.50+wSold*0.3)  // 原料 简包装
      }
      const cogs=retailCogs+wsCogs
      return Math.round(b7-cogs-b5-b9-b13-trn-misc-util-eq)
    }
  })
  
// ============ Entangle（循环组 B3↔B4↔B21） ============
  
const gv = (path: string, fallback = 0) => {
    try { return eg.data.GetValue(path, 'value') ?? fallback } catch { return fallback }
  }
  // V7: physCapFn — pure headcount*area, no salary multiplier

  const physCapFn = (b14: number, b24: number, grade?: number) => {
    const dp = grade != null ? dynParams(grade, b14) : { apm: 40, spm: 1800 }
    return Math.max(1, Math.min(b14 * dp.apm, b24 * dp.spm))
  }
  
// 1. B3 → B4: salary→waste reduction (wfB4 = 1.20-0.45*wage/10000)
  eg.config.useEntangle({
    cause: 'B3', impact: 'B4', via: ['value'],
    emit: (cause: any, _impact: any, propose: any) => {
      const b3 = cause.state?.value ?? 0
      const emp = gv('EMP', 0)
      const b26 = gv('B26', 4000)
      const wfB4 = 1.20 - 0.45 * Math.min(b26, 10000) / 10000
      const b4 = Math.max(0.03, (1.5 - b3 * 0.00015) * wfB4 * (1 - emp * 0.002))
      const val = Math.round(b4 * 100) / 100
      propose.set('value', val)
    }
  })
  
// 2. B4 → B3: B4变化时提出B3预言 (V7: physCapFn without salary)
  eg.config.useEntangle({
    cause: 'B4', impact: 'B3', via: ['value'],
    emit: (cause: any, _impact: any, propose: any) => {
      const b14 = gv('B14', 150), b24 = gv('B24', 8)
      const fat = gv('FAT', 40)
      const pc = physCapFn(b14, b24)
      const b3 = Math.max(0, Math.round(pc * sk(fat)))
      propose.set('value', b3)
    }
  })
  
// 3. B3 → B21: 满意度=薪酬水平(f工资/5k) + 产出匹配 - 过劳 - FAT侵蚀
  eg.config.useEntangle({
    cause: 'B3', impact: 'B21', via: ['value'],
    emit: (cause: any, _impact: any, propose: any) => {
      const b3 = cause.state?.value ?? 0
      const b9 = gv('B9', 0), b15 = gv('B15', 3)
      const b14 = gv('B14', 60), b24 = gv('B24', 3)
      const b26 = gv('B26', 4000)
      const fat = gv('FAT', 40)
      const pc = physCapFn(b14, b24, b15)
      const pp = b9 / Math.max(b3, 1)
      // 满意度 = 绝对工资水平(40%) + 产出匹配度(60%)
      const wageScore = Math.min(1, b26 / 5000)  // ¥5k=满分, ¥2.5k=50%, ¥800=16%
      const bl = 2.5 + b15 * 0.3
      const efficiencyScore = pp >= bl ? 0.7 + Math.min((pp - bl) / (bl * 2), 0.25) : pp / bl * 0.7
      let b21 = Math.round(Math.min(1, Math.max(0, wageScore * 0.4 + efficiencyScore * 0.6)) * 1000) / 1000
      // 过劳惩罚
      const util = b3 / Math.max(pc, 1)
      const ov = Math.max(0, util - 0.85) * 1.0
      b21 = Math.max(0.15, b21 - ov)
      // FAT侵蚀: >60开始缓慢, >85加速
      if (fat > 60) b21 = Math.max(0.25, b21 - (fat - 60) * 0.004)
      if (fat > 85) b21 = Math.max(0.10, b21 - (fat - 85) * 0.01)
      propose.set('value', Math.round(b21 * 1000) / 1000)
    }
  })
  
// 4. FAT → B3: FAT变化时触发B3收敛 (V7: physCapFn without salary)
  eg.config.useEntangle({
    cause: 'FAT', impact: 'B3', via: ['value'],
    emit: (cause: any, _impact: any, propose: any) => {
      const fat = cause.state?.value ?? 40
      const b14 = gv('B14', 150), b24 = gv('B24', 8)
      const cap = Math.max(0, Math.round(physCapFn(b14, b24) * sk(fat)))
      propose.set('value', cap)
    }
  })
  
// 5. M1 → B3: V7 — physCap = min(area×30, staff×1800), no salary wf
  eg.config.SetRule('M1', 'B3', 'value', {
    triggerKeys: ['value'],
    logic: () => {
      const fat = Number(eg.data.GetValue('FAT', 'value')) || 40
      const b14 = Number(eg.data.GetValue('B14', 'value')) || 60
      const b24 = Number(eg.data.GetValue('B24', 'value')) || 3
      const b15 = Number(eg.data.GetValue('B15', 'value')) || 3
      const dp5 = dynParams(b15, b14)
      const physMax = Math.max(1, Math.min(b14 * dp5.apm, b24 * dp5.spm))
      return Math.max(0, Math.round(physMax * sk(fat)))
    }
  })
  
// ===== 状态演进 entangle（M1 月变触发） =====
  
// 6. M1 → FAT: V7 — 零售UR+f(ur>.88)+ B2B产量也产生轻度疲劳
  eg.config.useEntangle({
    cause: 'M1', impact: 'FAT', via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const curFAT = gv('FAT', 40), b14 = gv('B14', 60), b24 = gv('B24', 3), b15 = gv('B15', 3)
      const b2 = gv('B2', 1000), b3 = gv('B3', 1000), b1 = gv('B1', 18), b21s = gv('B21', 0.7)
      const dp7 = dynParams(b15, b14)
      const physMax = physCapFn(b14, b24, b15)
      const retailUR = Math.min(1, b2 / Math.max(physMax, 1))
      // 总负荷（零售+B2B全部产线运转, B2B量随满意度缩放）
      const bbpScaled = 1200  // V9: 固定1200, 满意度不砍B2B产能
      const b2bSold = Math.min(b24*bbpScaled + (b14>=150?Math.round((b14-150)*500):0), Math.max(0, b3-b2))
      const totalUR = Math.min(1, (b2 + b2bSold) / Math.max(physMax, 1))
      let d = 0
      // 零售超负荷→剧烈疲劳
      if (retailUR > 0.88) d = Math.round((retailUR - 0.88) * dp7.frh)  // 社区30/工厂45/高奢35
      if (retailUR > 0.95) d += 2
      // 恢复：满负荷→禁止恢复。低于路线阈值→恢复(社区高/工厂低)
      if (totalUR >= 0.90) {
        d += 3
      } else if (totalUR < dp7.ful) {
        d = -Math.round((dp7.ful - totalUR) * 15)
      } else if (retailUR < 0.75) {
        d = -Math.round((0.75 - retailUR) * 5)
      }
      // B2B累积疲劳（路线感知: 社区8, 工厂15, 高奢12）
      if (totalUR > 0.65) d += Math.round((totalUR - 0.65) * dp7.ftr)
      if (b14 > 150 && b24 < Math.ceil(b14 / 35)) d += 3
      propose.set('value', Math.max(10, Math.min(100, Math.round(curFAT + d))))
    }
  })

  // 7. M1 → BRAND: V7 — growth 8/10/5/mkt*0.12, decay 0.015, gm 1-BR/500, sr*8
  eg.config.useEntangle({
    cause: 'M1', impact: 'BRAND', via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const cur = gv('BRAND', 0), b2 = gv('B2', 0), b3 = gv('B3', 0)
      const b21 = gv('B21', 0.8), b28 = gv('B28', 0.6)
      const fat = gv('FAT', 40), b13 = gv('B13', 1000)
      const sr = Math.max(0, (b2 - b3) / Math.max(1, b2))
      const dp4 = dynParams(gv('B15',3), gv('B14',60))
      const growth = b21 * dp4.bg1 + b28 * dp4.bg2 + Math.max(0, (100 - fat) / 100) * 5
        + Math.sqrt(Math.max(0, b13)) * 0.12
      const decay = cur * 0.015
      const gm = Math.max(0.03, 1 - cur / 500)
      let nb = Math.max(0, Math.round(cur + growth * gm - decay - sr * 8))
      if (b28 < 0.40) {
        const gap = 0.40 - b28
        nb = Math.max(0, nb - Math.round(gap * 20))
        const ceiling = b28 >= 0.30 ? 50 : 25
        if (nb > ceiling) nb = ceiling
      }
      propose.set('value', nb)
    }
  })

  // 8. M1 → EMP: 每月推经验
  eg.config.useEntangle({
    cause: 'M1', impact: 'EMP', via: ['value'],
    emit: (_cause: any, _impact: any, propose: any) => {
      const cur = gv('EMP', 0)
      propose.set('value', Math.min(200, Math.round(cur + Math.max(1, 10 - Math.round(cur * 0.05)))))
    }
  })
}

// ===== V4 疲劳模型引擎 =====
const c = reactive({
  B1: 18, B2: 0, B3: 0, B4: 2, B5: 0, B6: 0, B7: 0, B8: 0,
  B9: 0, B10: 3, B11: 0, B12: 0, B13: 2000, B14: 150, B15: 7,
  B21: 0.8, B28: 0.6, B24: 8, B25: 100,
  FAT: 40, EMP: 0, BRAND: 0, TRAFFIC: 0,
})
const m = ref(1), p = ref(0), t = ref(0)

// 季节系统
const SEASON_LABELS = ['❄️ 淡季', '🧧 春节', '🌸 平稳', '🌸 平稳', '☀️ 平稳', '☀️ 淡季', '☀️ 淡季', '☀️ 淡季', '🎑 中秋', '🍂 旺季', '🍂 平稳', '🎄 圣诞']
const SEASON_FACTORS = [0.85, 1.10, 0.95, 1.00, 1.00, 0.90, 0.85, 0.85, 1.25, 1.10, 1.00, 1.30]
const seasonLabel = computed(() => SEASON_LABELS[((m.value - 1) % 12)] || '')
const seasonFactor = computed(() => SEASON_FACTORS[((m.value - 1) % 12)] || 1.0)
const nextSeasonLabel = computed(() => SEASON_LABELS[(m.value % 12)] || '')
const nextSeasonFactor = computed(() => SEASON_FACTORS[(m.value % 12)] || 1.0)
const seasonColor = computed(() => {
  const f = seasonFactor.value
  if (f >= 1.20) return '#FFD700'
  if (f >= 1.05) return '#4CAF50'
  if (f <= 0.85) return '#87CEEB'
  return '#9a9a9a'
})
const seasonBg = computed(() => {
  const f = seasonFactor.value
  if (f >= 1.20) return '#2a2000'
  if (f >= 1.05) return '#0a1a0a'
  if (f <= 0.85) return '#0a1a2a'
  return '#141414'
})
const monthLog = ref<{m:number;p:number;t:number}[]>([])
const revision = ref(0)
const logEntries = ref<{m:number;p:number;t:number;detail?:Record<string,any>;text?:string}[]>([])
// 记录上一次 nx() 时的滑块值，用于日志 diff（初始化时填充默认值）
const defaultSl = [18, 3, 100, 1000, 3, 60, 4000, 3]
const lastSl: number[] = [...defaultSl]
// @meshflow/logger 捕获引擎传播指令
const logBuffer = ref<string[]>([])
let _logFlushing = false
function setupLogger(engineRaw: any) {
  const logger = useLogger({
    locale: 'zh',
    ignorePaths: [],  // 监听所有节点
    onLog: (msg: string) => {
      if (!_logFlushing) logBuffer.value.push(msg)
    },
  })
  try { logger.apply(engineRaw) } catch {}
}
const sl = reactive([
  { k:'B1', l:'售价 ¥', mn:5, mx:50, v:18 }, { k:'B24', l:'员工', mn:1, mx:20, v:3 },
  { k:'B25', l:'培训 ¥', mn:0, mx:1000, st:50, v:100 }, { k:'B13', l:'营销 ¥', mn:0, mx:20000, st:500, v:1000 },
  { k:'B10', l:'原料', mn:1, mx:6, st:0.1, v:3 }, { k:'B14', l:'面积 m²', mn:30, mx:300, st:10, v:60 },
  { k:'B26', l:'工资/人 ¥', mn:800, mx:10000, st:200, v:4000 },
  { k:'B15', l:'地段 ⭐', mn:1, mx:10, v:3 },
])

// 年度利润跟踪
const annualProfits = ref<number[]>([])
const maxAnnual = computed(() => Math.max(1, ...annualProfits.value.map(Math.abs)))
const GOAL = 1_000_000
const isVictory = computed(() => t.value >= GOAL)
const goalPct = computed(() => Math.min(100, Math.round(t.value / GOAL * 100)))

// 从 monthLog 重建年度利润
function rebuildAnnualProfits() {
  annualProfits.value = []
  const totalMonths = m.value
  for (let year = 0; year < Math.ceil(totalMonths / 12); year++) {
    const start = year * 12 + 1
    const end = Math.min(start + 11, totalMonths)
    const yearMonths = monthLog.value.filter(x => x.m >= start && x.m <= end)
    const sum = yearMonths.reduce((s, x) => s + (x.p || 0), 0)
    annualProfits.value.push(sum)
  }
}

// 滑块变化跟踪 — 高亮对应DAG节点
let flashTimer: ReturnType<typeof setTimeout> | null = null

// 下游依赖图 (同 GraphEditor.vue)
const SR_EDGES: [string, string][] = [
  ['B1','B2'],['B1','B6'],['B14','B5'],['B15','B5'],['B14','B3'],['B9','B3'],
  ['B15','B2'],['B13','B2'],['B10','B12'],['B11','B12'],['B4','B12'],
  ['B3','B12'],['B3','B4'],['B1','B6'],['B2','B6'],['B3','B6'],
  ['B12','B7'],['B5','B7'],['B9','B7'],['B13','B7'],['B22','B7'],
  ['B6','B8'],['B7','B8'],
  ['B3','B22'],['B3','B23'],['B23','B12'],
  ['B9','B21'],['B3','B21'],['B14','B21'],
  ['B21','B20'],['B28','B20'],
  ['B28','B2'],  // 原料品质 → 本地客流
  ['B24','B9'],['B24','B3'],
  ['B25','B21'],
  ['B26','B9'],
  // v3 新增: 原料品质 + 批发 + 季节 + 月度缓存反馈
  ['B10','B28'],['B3','B28'],['B28','B20'],
  ['B14','B7'],['B3','B7'],['B10','B7'],  // 批发
  ['B17','B2'],  // 缺货惩罚 → 需求
  ['B16','B3'],['B18','B3'],['B25','B18'],  // 月度缓存+培训→报废→产能自适应备货
]
const DEP_MAP: Record<string, string[]> = {}
for (const [src, tgt] of SR_EDGES) {
  if (!DEP_MAP[src]) DEP_MAP[src] = []
  if (!DEP_MAP[src].includes(tgt)) DEP_MAP[src].push(tgt)
}

// 从 c 对象写入引擎的指定节点集合
function writeToEngine(ids: string[]) {
  if (!eng.value) return
  for (const id of ids) {
    switch (id) {
      case 'B1': eng.value.SilentSet('B1', sl[0].v); break
      case 'B2': eng.value.SilentSet('B2', c.B2); break
      case 'B3': eng.value.SilentSet('B3', c.B3); break
      case 'B4': eng.value.SilentSet('B4', Math.round(c.B4 * 100) / 100); break
      case 'B5': eng.value.SilentSet('B5', c.B5); break
      case 'B6': eng.value.SilentSet('B6', c.B6); break
      case 'B7': eng.value.SilentSet('B7', c.B7); break
      case 'B8': eng.value.SilentSet('B8', c.B8); break
      case 'B9': eng.value.SilentSet('B9', c.B9); break
      case 'B10': eng.value.SilentSet('B10', sl[4].v); break
      case 'B11': eng.value.SilentSet('B11', Math.round(c.B11 * 100) / 100); break
      case 'B12': eng.value.SilentSet('B12', Math.round(c.B12 * 100) / 100); break
      case 'B13': eng.value.SilentSet('B13', sl[3].v); break
      case 'B14': eng.value.SilentSet('B14', sl[5].v); break
      case 'B15': eng.value.SilentSet('B15', sl[7].v); break
      case 'B21': eng.value.SilentSet('B21', Math.round(c.B21 * 1000) / 1000); break
      case 'B20': eng.value.SilentSet('B20', Math.round(c.B21 * 100) / 100); break
      case 'B22': eng.value.SilentSet('B22', Math.max(0, (c.B3 - 500) * 0.5)); break
      case 'B23': eng.value.SilentSet('B28', Math.round((c.B28||0.6) * 1000) / 1000)
  eng.value.SilentSet('B23', Math.round(sl[4].v * (1 - Math.min(0.3, c.B3 * 0.00005)) * 100) / 100); break
      case 'B24': eng.value.SilentSet('B24', sl[1].v); break
      case 'B25': eng.value.SilentSet('B25', sl[2].v); break
      case 'B28': eng.value.SilentSet('B28', Math.round((c.B28||0.6) * 1000) / 1000); break
      case 'B26': eng.value.SilentSet('B26', sl[6].v); break
    }
  }
}

async function onSliderChange(nodeId: string) {
  writeSlider(nodeId)  // SilentSet 改值，不触发传播
  // 传播只在 nx() 推月份时通过 notifyAll 统一执行
}

// 节点情报面板
const props = defineProps<{ engine?: any; selectedNode?: string }>()
const emit = defineEmits<{ clearNode: []; 'select-node': [id: string] }>()
const eng = computed(() => props.engine)

// ===== 快照型 undo/redo（只记 nx 不记滑块）=====
interface StateSnapshot {
  sl: number[]  // 8 个滑块值 [B1,B24,B25,B13,B10,B14,B26,B15]
  m: number; p: number; t: number
  fat: number; emp: number; b19: number
  log: {m:number;p:number;t:number}[]
}
const snapshotStack = ref<StateSnapshot[]>([])
const redoStack = ref<StateSnapshot[]>([])
const undoCan = computed(() => snapshotStack.value.length > 0)
const redoCan = computed(() => redoStack.value.length > 0)

function snap(): StateSnapshot {
  return {
    sl: sl.map(s => s.v),
    m: m.value, p: p.value, t: t.value,
    fat: c.FAT, emp: c.EMP, b19: c.BRAND,
    log: JSON.parse(JSON.stringify(monthLog.value)),
  }
}

async function restoreSnap(s: StateSnapshot) {
  // 1. 恢复滑块 Vue 值
  sl.forEach((item, i) => { item.v = s.sl[i] })
  // 2. 恢复状态变量
  m.value = s.m; p.value = s.p; t.value = s.t
  c.FAT = s.fat; c.EMP = s.emp; c.BRAND = s.b19
  monthLog.value = s.log
  // 3. 写回引擎
  const e = eng.value
  if (!e) return
  e.SetValue('B1', s.sl[0]); e.SetValue('B24', s.sl[1]); e.SetValue('B25', s.sl[2])
  e.SetValue('B13', s.sl[3]); e.SetValue('B10', s.sl[4]); e.SetValue('B14', s.sl[5])
  e.SetValue('B26', s.sl[6]); e.SetValue('B15', s.sl[7])
  e.raw.data.SetValues([
    {path:'M1',key:'value',value:s.m},
    {path:'P1',key:'value',value:s.p},{path:'T1',key:'value',value:s.t},
    {path:'FAT',key:'value',value:s.fat},{path:'EMP',key:'value',value:s.emp},
    {path:'BRAND',key:'value',value:s.b19},
  ])
  await e.notifyAll()
  readEngine()
  rebuildAnnualProfits()
  revision.value++
  // 通知 GraphEditor 高亮
  if (e.changedNodes) e.changedNodes.value = new Set([
    'B2','B3','B4','B5','B6','B7','B8','B9','B12',
'B16','B17','B18','B20','B21','B22','B23','B28','FAT','BRAND','EMP','B19',
  ])
}

const nodeInfo = computed(() => props.selectedNode ? NODE_INFO[props.selectedNode] : null)
function getNodeInfo(id: string): NodeInfo | null { return NODE_INFO[id] || null }
function getLiveValue(id: string): number {
  const mapping: Record<string, () => number> = {
    B1: () => sl[0].v, B24: () => sl[1].v, B25: () => sl[2].v, B13: () => sl[3].v,
    B10: () => sl[4].v, B14: () => sl[5].v,
    B2: () => c.B2, B3: () => c.B3, B4: () => c.B4, B5: () => c.B5,
    B6: () => c.B6, B7: () => c.B7, B8: () => c.B8, B9: () => c.B9,
    B11: () => c.B11, B12: () => c.B12, B21: () => c.B21,
    B22: () => Math.max(0, (c.B3 - 500) * 0.5),
    B23: () => Math.round(sl[4].v * (1 - Math.min(0.3, c.B3 * 0.00005)) * 100) / 100,
 B20: () => { try { let v = eng.value?.getCellValue('B20'); let n = Number(v); return Number.isFinite(n) ? Math.round(n*100)/100 : 0 } catch { return 0 } }, B15: () => sl[7].v,
    B16: () => { try { return Number(eng.value?.getCellValue('B16'))||0 } catch { return 0 } }, B17: () => { try { return Number(eng.value?.getCellValue('B17'))||0 } catch { return 0 } }, B18: () => { try { return Number(eng.value?.getCellValue('B18'))||0 } catch { return 0 } },
    B26: () => sl[6].v, B28: () => { try { let v = eng.value?.getCellValue('B28'); let n = Number(v); return Number.isFinite(n) ? Math.round(n*1000)/1000 : 0 } catch { return 0 } },
  }
  return mapping[id]?.() ?? 0
}
function switchNode(id: string) {
  emit('select-node', id)
}

// 对外暴露
defineExpose({ c, m, p, t, sl, monthLog, revision, readEngine, nx, undo, redo, reset, undoCan, redoCan, logEntries, fm, short, sk })

// 现金流百分比
const cashPct = computed(() =>
  Math.min(100, Math.max(0, (t.value + 200000) / 400000 * 100))
)

// 士气颜色
const fatText = computed(() => {
  if (c.FAT < 20) return '#4CAF50'
  if (c.FAT < 60) return '#8BC34A'
  if (c.FAT < 80) return '#FFC107'
  return '#f44336'
})
const fatBg = computed(() => {
  if (c.FAT < 20) return '#0a2a1a'
  if (c.FAT < 60) return '#1a2a0a'
  if (c.FAT < 80) return '#2a1a00'
  return '#2a0a0a'
})

// 同步 V4 计算结果到共享引擎 (供 GraphEditor 读取)
function syncToEngine() {
  if (!eng.value) return
  eng.value.SilentSet('B1', sl[0].v)
  eng.value.SilentSet('B2', c.B2)
  eng.value.SilentSet('B3', c.B3)
  eng.value.SilentSet('B4', Math.round(c.B4 * 100) / 100)
  eng.value.SilentSet('B5', c.B5)
  eng.value.SilentSet('B6', c.B6)
  eng.value.SilentSet('B7', c.B7)
  eng.value.SilentSet('B8', c.B8)
  eng.value.SilentSet('B9', c.B9)
  eng.value.SilentSet('B10', sl[4].v)
  eng.value.SilentSet('B11', Math.round(c.B11 * 100) / 100)
  eng.value.SilentSet('B12', Math.round(c.B12 * 100) / 100)
  eng.value.SilentSet('B13', sl[3].v)
  eng.value.SilentSet('B14', sl[5].v)
  eng.value.SilentSet('B15', sl[7].v)
  eng.value.SilentSet('B21', Math.round(c.B21 * 1000) / 1000)
  // B20 由 SetRule B21+B28→B20 自动计算
  eng.value.SilentSet('B22', Math.max(0, (c.B3 - 500) * 0.5))
  eng.value.SilentSet('B28', Math.round((c.B28||0.6) * 1000) / 1000)
  eng.value.SilentSet('B23', Math.round(sl[4].v * (1 - Math.min(0.3, c.B3 * 0.00005)) * 100) / 100)
  eng.value.SilentSet('B24', sl[1].v)
  eng.value.SilentSet('B25', sl[2].v)
  eng.value.SilentSet('B26', sl[6].v)
  eng.value.SilentSet('FAT', c.FAT)
  eng.value.SilentSet('EMP', c.EMP)
  eng.value.SilentSet('BRAND', c.BRAND)
  eng.value.SilentSet('TRAFFIC', c.TRAFFIC)
  eng.value.SilentSet('M1', m.value)
  eng.value.SilentSet('P1', p.value)
  eng.value.SilentSet('T1', t.value)
}

const tailP = computed(() => monthLog.value.length > 0 ? safe(monthLog.value[monthLog.value.length - 1]?.p) : 0)

// 最近5个月 (用于迷你回顾)
const recentMonths = computed(() => [...monthLog.value].slice(-5).reverse())

const monthProfits = computed(() => {
  const arr = new Array(12).fill(0)
  monthLog.value.forEach(x => { if (x.m >= 1 && x.m <= 12) arr[x.m - 1] = safe(x.p) })
  return arr
})
const maxMonthProfit = computed(() => Math.max(1, ...monthProfits.value.map(Math.abs)))
function getMonthProfit(i: number) { return monthProfits.value[i - 1] || 0 }
function getMonthClass(i: number) {
  const v = monthProfits.value[i - 1]
  if (v === undefined) return ''
  if (v > 0) return 'ms-profit'
  if (v < 0) return 'ms-loss'
  return 'ms-zero'
}

function gp() { return {
  B1: safe(sl[0].v, 16),
  B24: safe(sl[1].v, 8),
  B25: safe(sl[2].v, 100),
  B13: safe(sl[3].v, 2000),
  B10: safe(sl[4].v, 3),
  B14: safe(sl[5].v, 150),
  B15: safe(sl[7].v, 7)
} }
// 从引擎读取计算值到 Vue 响应式对象
function readEngine() {
  const e = eng.value
  if (!e) return
  c.B2 = e.GetValue('B2') ?? c.B2
  c.B4 = e.GetValue('B4') ?? c.B4
  c.B5 = e.GetValue('B5') ?? c.B5
  c.B9 = e.GetValue('B9') ?? c.B9
  c.B12 = e.GetValue('B12') ?? c.B12
  c.B3 = e.GetValue('B3') ?? c.B3
  c.B21 = e.GetValue('B21') ?? c.B21
  c.FAT = e.GetValue('FAT') ?? c.FAT
  c.EMP = e.GetValue('EMP') ?? c.EMP
  c.BRAND = e.GetValue('BRAND') ?? c.BRAND
  c.B28 = e.GetValue('B28') ?? c.B28
  c.B6 = e.GetValue('B6') ?? c.B6
  c.B7 = e.GetValue('B7') ?? c.B7
  c.B8 = e.GetValue('B8') ?? c.B8
  // 总人流量 = 零售需求B2 + B2B销量(剩余产能)
  const b3 = c.B3 || 0, b2 = c.B2 || 0
  const b2bSold = b3 > b2 ? b3 - b2 : 0
  c.TRAFFIC = b2 + b2bSold
}

// 滑块值 → SilentSet 到引擎（只存值，不触发传播）
function writeSlider(id: string) {
  const e = eng.value
  if (!e) return
  const m: Record<string, number> = { 'B1':0,'B24':1,'B25':2,'B13':3,'B10':4,'B14':5,'B26':6,'B15':7 }
  const idx = m[id]
  if (idx === undefined) return
  e.SilentSet(id, sl[idx].v)
}
function sk(c4:number){const v=Number(c4);return!Number.isFinite(v)?1:v<80?1:v>=100?0.1:1-((t=>t*t*(3-2*t)*0.9)((v-80)/20))}
function fsk(c4:number){return sk(c4).toFixed(2)}
async function nx(){if(t.value<=-200000)return;readEngine()
  const e=eng.value
  if(!e)return
  // 记录上月 B2/B8 用于 B16 展示和利润 diff
  const lastB2 = c.B2, lastB8 = c.B8

  // 0. 拍快照
  snapshotStack.value.push(snap()); redoStack.value.length = 0
  monthLog.value.push({m:m.value,p:p.value,t:t.value})
  // 1. SetValues 批量写入+统一触发传播（引擎原生 API，不调 notifyAll）
  e.raw.data.SetValues([
    {path:'B1',key:'value',value:sl[0].v},{path:'B24',key:'value',value:sl[1].v},
    {path:'B25',key:'value',value:sl[2].v},{path:'B13',key:'value',value:sl[3].v},
    {path:'B10',key:'value',value:sl[4].v},{path:'B14',key:'value',value:sl[5].v},
    {path:'B26',key:'value',value:sl[6].v},{path:'B15',key:'value',value:sl[7].v},
    {path:'M1',key:'value',value:m.value},
  ])
  // SetValues 内部异步传播，等微任务完成
  await new Promise(r => setTimeout(r, 50))
  readEngine()
  // B17 缺货率: 需求超出产能的比例
  const shortage = c.B3 < c.B2 && c.B2 > 0 ? Math.round((c.B2 - c.B3) / c.B2 * 1000) / 1000 : 0
  // B18 报废率: 培训不足→废品多(上限15%), EMP经验越高越少
  const trainGap = Math.max(0, 0.15 - sl[2].v / 3000)  // B25=0→15%, B25=100→12%, B25=300→5%, B25=450→0
  const empEff = Math.max(0.15, 1 - c.EMP / 150)        // EMP=0→1.0, EMP=75→0.5, EMP=150→0.15
  const waste = Math.round(trainGap * empEff * 1000) / 1000
  e.raw.data.SilentSet('B16','value',lastB2);e.raw.data.SilentSet('B17','value',shortage);e.raw.data.SilentSet('B18','value',waste)
  const pf=Math.round(safe(c.B8))
  p.value=pf;t.value+=pf;m.value++
  if(m.value%12===1)rebuildAnnualProfits()
  revision.value++

  // ===== 日志：变更追踪 =====
  const lines: string[] = []
  // 滑块变化（对比上一次 nx() 时的值）
  const dd: string[] = []
  if (lastSl[1] !== sl[1].v) dd.push(`员工 ${lastSl[1]}→${sl[1].v}人`)
  if (lastSl[6] !== sl[6].v) dd.push(`工资 ¥${lastSl[6]}→¥${sl[6].v}`)
  if (lastSl[2] !== sl[2].v) dd.push(`培训 ¥${lastSl[2]}→¥${sl[2].v}`)
  if (lastSl[0] !== sl[0].v) dd.push(`售价 ¥${lastSl[0]}→¥${sl[0].v}`)
  if (lastSl[3] !== sl[3].v) dd.push(`营销 ${lastSl[3].toLocaleString()}→${sl[3].v.toLocaleString()}`)
  if (lastSl[4] !== sl[4].v) dd.push(`原料 ¥${lastSl[4]}→¥${sl[4].v}`)
  if (lastSl[5] !== sl[5].v) dd.push(`面积 ${lastSl[5]}→${sl[5].v}m²`)
  if (lastSl[7] !== sl[7].v) dd.push(`地段 ${lastSl[7]}→${sl[7].v}⭐`)
  if (dd.length) lines.push(`📋 调整: ${dd.join('、')}`)
  // 更新 lastSl 为当前值，供下月 diff
  lastSl.length = 0; lastSl.push(...sl.map(s => s.v))

  // 关键指标（始终显示当前值）
  const kv: string[] = []
  kv.push(`B9人工=${c.B9.toLocaleString()}`)
  kv.push(`B5房租=${c.B5.toLocaleString()}`)
  kv.push(`B2需求=${c.B2}`)
  kv.push(`B3产能=${c.B3}`)
  kv.push(`B4加工=${c.B4}`)
  kv.push(`B6实售=${c.B6}`)
  kv.push(`B12原料=${c.B12}`)
  kv.push(`B21满意度=${typeof c.B21==='number'?c.B21.toFixed(3):c.B21}`)
  kv.push(`FAT=${c.FAT}`)
  kv.push(`BRAND=${c.BRAND}`)
  kv.push(`EMP=${c.EMP}`)
  lines.push(`⚡ 指标: ${kv.join('、')}`)

  // 利润趋势
  const pt = pf - lastB8
  lines.push(`📊 利润 ¥${(pf>=0?'+':'')+pf.toLocaleString()} (${pt>=0?'▲+':'▼'}${Math.abs(pt).toLocaleString()})`)

  // 季节预警 — 推进下月后进入的季节
  const curMonth = m.value % 12 || 12   // 当前月 1-12
  const curSF = SEASON_FACTORS[(curMonth - 1) % 12]
  const nextMonth = (curMonth % 12) + 1  // 下个月 1-12
  const nextSF = SEASON_FACTORS[(nextMonth - 1) % 12]
  const nextLabel = SEASON_LABELS[(nextMonth - 1) % 12]
  if (nextSF >= 1.20 && curSF < 1.20) {
    lines.push(`🔥 下月${nextLabel}(×${nextSF.toFixed(2)})旺季来袭 | 建议提前加人或提价备产`)
  } else if (nextSF <= 0.85 && curSF > 0.85) {
    lines.push(`❄️ 下月${nextLabel}(×${nextSF.toFixed(2)})淡季将至 | 可提前降产能/砍营销省成本`)
  } else if (nextSF >= 1.20 && curSF >= 1.20) {
    lines.push(`🔥 下月${nextLabel}仍是旺季 ×${nextSF.toFixed(2)} | 保持产能`)
  }

  logEntries.value.push({
    m: m.value-1, p: pf, t: t.value,
    detail: { B3:c.B3, B6:c.B6, FAT:c.FAT, BRAND:c.BRAND, EMP:c.EMP, B21:c.B21?.toFixed(3) },
    text: lines.join(String.fromCharCode(10)),
  })
  // 追加 logger 捕获的传播指令
  if (logBuffer.value.length > 0) {
    const last = logEntries.value[logEntries.value.length - 1]
    if (last) last.text = (last.text || '') + String.fromCharCode(10) + '--- 传播链 ---' + String.fromCharCode(10) + logBuffer.value.join(String.fromCharCode(10))
    logBuffer.value.length = 0
  }
  // 告知 GraphEditor：全部联动节点高亮
  if (e.changedNodes) e.changedNodes.value = new Set([
    'B2','B3','B4','B5','B6','B7','B8','B9','B12',
    'B16','B17','B18','B20','B21','B22','B23','B28',
    'FAT','BRAND','EMP',
  ])}
async function undo(){
  if (snapshotStack.value.length === 0) return
  redoStack.value.push(snap())
  const s = snapshotStack.value.pop()!
  await restoreSnap(s)
}
async function redo(){
  if (redoStack.value.length === 0) return
  snapshotStack.value.push(snap())
  const s = redoStack.value.pop()!
  await restoreSnap(s)
}
function reset(){m.value=1;p.value=0;t.value=0;monthLog.value.length=0;annualProfits.value.length=0
snapshotStack.value.length=0;redoStack.value.length=0;logEntries.value.length=0;lastSl.length=0;logBuffer.value.length=0
Object.assign(c,{B2:0,B3:0,B4:2,B5:0,B6:0,B7:0,B8:0,B9:0,B11:0,B12:0,B21:0.8,B28:0.6,B24:8,B25:100,FAT:40,EMP:0,BRAND:0,TRAFFIC:0});sl[0].v=18;sl[1].v=3;sl[2].v=100;sl[3].v=1000;sl[4].v=3;sl[5].v=60;sl[6].v=4000;sl[7].v=3;lastSl.push(...defaultSl)
setupBakeryRules(eng.value);writeSlider('B1');writeSlider('B24');writeSlider('B25');writeSlider('B13')
writeSlider('B10');writeSlider('B14');writeSlider('B26');writeSlider('B15')
eng.value?.raw.data.SilentSet('M1','value',0)
eng.value?.raw.data.SetValues([
  {path:'FAT',key:'value',value:40},{path:'EMP',key:'value',value:0},{path:'BRAND',key:'value',value:0},{path:'B21',key:'value',value:0.8},
  {path:'B3',key:'value',value:0},{path:'P1',key:'value',value:0},{path:'T1',key:'value',value:0},
])
readEngine();revision.value++}
function fm(n: any){const v=safe(n);return (v>=0?'+':'')+'¥'+Math.abs(v).toLocaleString()}
function short(n: any){const v=safe(n);return v>=10000?(v/10000).toFixed(1)+'万':v.toLocaleString()}

const satPct = computed(() => Math.round(Math.min(1, Math.max(0, c.B21)) * 100))
const satColor = computed(() => {
  if (c.B21 >= 0.7) return '#4CAF50'
  if (c.B21 >= 0.4) return '#FFC107'
  return '#f44336'
})

// 需求/产能 展示
const demandDisplay = computed(() => {
  const b3 = safe(c.B3), b2 = safe(c.B2)
  if (sl[5].v >= 150 && b3 > b2) {
    const b2b = b3 - b2
    return '零售 ' + short(b2) + ' · B2B ' + short(b2b) + ' · 产' + short(b3)
  }
  return '零售 ' + short(b2) + ' · 产' + short(b3)
})
const totalDemand = computed(() => safe(c.B2))
const capacityUtil = computed(() => {
  const b3 = safe(c.B3)
  if (b3 <= 0) return 0
  // 工厂路线用总吞吐量(零售+B2B全部吃完产能)/B3
  if (sl[5].v >= 150) {
    const b2bEst = Math.max(0, safe(c.B3) - safe(c.B2))  // 实际B2B出货
    return Math.min(100, Math.round((safe(c.B2) + b2bEst) / b3 * 100))
  }
  return Math.round(safe(c.B2) / b3 * 100)
})

// 成本结构 (当月各项成本占比)
const costItems = computed(() => {
  const training = safe(sl[2].v) * safe(sl[1].v)
  const benefits = Math.round(0.05 * safe(sl[1].v) * 1500)
  const total = Math.abs(c.B7) || 1
  const items = [
    { label: '人工', value: safe(c.B9), color: '#4CAF50' },
    { label: '原料', value: Math.round((c.B12 + safe(c.B4)) * c.B3), color: '#8BC34A' },
    { label: '包装', value: Math.round(safe(sl[0].v) * 0.15 * c.B6), color: '#FFC107' },
    { label: '场地', value: safe(c.B5), color: '#FF9800' },
    { label: '水电', value: Math.round(safe(sl[5].v) * 25 + safe(sl[1].v) * 200), color: '#e91e63' },
    { label: '折旧', value: 2000, color: '#f44336' },
  ]
  return items.map(x => ({ ...x, pct: Math.round(x.value / total * 100) }))
})

const fatClass = computed(() => {
  if (c.FAT < 20) return 'fg-burst'
  if (c.FAT < 60) return 'fg-normal'
  if (c.FAT < 80) return 'fg-slack'
  return 'fg-burnout'
})

// ===== 策略指纹 =====
function gauss(x: number, center: number, width: number): number {
  return Math.exp(-Math.pow((x - center) / width, 2))
}

const fpCommunity = computed(() => {
  const s = [
    gauss(sl[5].v, 60, 35) * 1.2,         // area: center 60m2
    gauss(sl[7].v, 3.5, 3) * 1.0,          // grade: 3-4
    gauss(sl[0].v, 22, 8) * 1.1,           // price: mid
    Math.max(0, 1 - (sl[1].v - 1) / 5) * 1.2, // staff: 1-3max, >6 zero
    Math.max(0, 1 - sl[3].v / 5000) * 0.8, // mkt: low
    Math.max(0, 1 - sl[4].v / 5) * 0.6,    // ingredient: mid
  ]
  // crowding penalty: >1.2 person per 10m2 = not a community shop
  const crowding = sl[1].v / Math.max(1, sl[5].v / 10)
  const crowdPenalty = crowding > 1.2 ? Math.max(0.2, 1 - (crowding - 1.2) * 0.5) : 1.0
  const avg = s.reduce((a, b) => a + b, 0) / s.length * crowdPenalty
  // 大空间惩罚: >120m²自动脱离社区路线
  const areaPenalty = sl[5].v > 120 ? Math.max(0.1, 1 - (sl[5].v - 120) / 80) : 1.0
  return Math.min(100, Math.max(0, Math.round(avg * 100 * areaPenalty)))
});const fpFactory = computed(() => {
  // 工厂核心: 面积>150触发批发 + 人数>6工业化团队
  const areaScore = sl[5].v > 200 ? 1.0 : sl[5].v > 150 ? (sl[5].v - 150) / 50 : 0
  const staffScore = sl[1].v > 10 ? 1.0 : sl[1].v > 4 ? (sl[1].v - 4) / 6 : 0
  const s = [
    areaScore * 2.0,                           // 面积权重2.0
    staffScore * 2.0,                          // 人数权重2.0
    gauss(sl[7].v, 1.5, 3) * 1.0,             // 地段低
    gauss(sl[0].v, 15, 6) * 1.1,              // 售价低
    gauss(sl[3].v, 7000, 6000) * 0.5,         // 营销
    Math.max(0, 1 - sl[4].v / 4) * 0.5,       // 原料便宜
  ]
  const avg = s.reduce((a, b) => a + b, 0) / s.length
  return Math.min(100, Math.max(0, Math.round(avg * 100)))
});const fpLuxury = computed(() => {
  const s = [
    gauss(sl[7].v, 9, 2.5) * 1.5,          // 地段：越高越好，核心商圈必备
    gauss(sl[0].v, 32, 10) * 1.2,           // 售价：中心 ¥32，高溢价
    gauss(sl[5].v, 85, 35) * 1.0,           // 面积：70-100m²，精致不大
    gauss(sl[4].v, 5.5, 2.5) * 1.0,        // 原料：¥5-6，优质进口原料
    gauss(sl[6].v, 5500, 2500) * 0.8,      // 工资：高薪留住大师傅
    gauss(sl[1].v, 2.5, 2) * 0.7,           // 员工：2-3 人精兵
    Math.max(0, sl[3].v / 12000) * 0.6,     // 营销：舍得砸钱做品牌
  ]
  const avg = s.reduce((a, b) => a + b, 0) / s.length
  return Math.min(100, Math.max(0, Math.round(avg * 100)))
})

const fingerprintLabel = computed(() => {
  const best = Math.max(fpCommunity.value, fpFactory.value, fpLuxury.value)
  if (best < 25) return '探索中'
  if (best < 40) return '萌芽期'
  if (fpCommunity.value === best) return '社区 · 口碑驱动'
  if (fpFactory.value === best && fpFactory.value >= 50) {
    const minS = sl[5].v > 150 ? Math.ceil(sl[5].v / 40) : 0
    const short = sl[5].v > 150 && sl[1].v < minS ? ' ⚠缺人' : ''
    return '大厂 · 规模驱动' + short
  }
  if (fpFactory.value === best) return '成长中 · 偏向走量'
  return '高奢 · 品牌驱动'
})

const fingerprintInsight = computed(() => {
  const cScore = fpCommunity.value
  const fScore = fpFactory.value
  const lScore = fpLuxury.value
  const best = Math.max(cScore, fScore, lScore)

  // 核心诊断 — V7: physMax = min(area×30, staff×1800), no salary wf
  const physMax = Math.min(sl[5].v * 40, sl[1].v * 1800)
  const ur = safe(c.B3) > 0 ? Math.min(1, safe(c.B2) / physMax) : 0
  const fat = safe(c.FAT)
  const brand = Math.round(safe(c.BRAND))
  const profit = safe(c.B8)

  // V7: 人手不足检测 — ceil(area/35)
  const minStaff = sl[5].v > 150 ? Math.ceil(sl[5].v / 35) : 0
  const isUnderstaffed = sl[5].v > 150 && sl[1].v < minStaff

  // ===== 工厂路线专属诊断 =====
  if (sl[5].v >= 150 && fScore >= cScore) {
    const b21sat = safe(c.B21) || 0.7
    const bbpEff = 1200
    const b2bCap = sl[1].v * bbpEff
    const spotCap = sl[5].v >= 150 ? Math.round((sl[5].v - 150) * 500) : 0
    const wsAvail = Math.max(0, safe(c.B3) - safe(c.B2))
    const wsSoldEst = Math.min(b2bCap + spotCap, wsAvail)
    const b28q = safe(c.B28) || 0.6
    const qMult = b28q >= 0.6 ? 1.0 : b28q >= 0.4 ? 1.0 - (0.6 - b28q) * 0.5 : 0.9 - (0.4 - b28q) * 1.0
    const wsMarginPerItem = Math.min(sl[0].v, 22) * 0.25 * Math.max(0.5, qMult) - sl[4].v * 0.50 - 0.3
    const wsNet = Math.round(wsSoldEst * wsMarginPerItem)
    const rent = safe(c.B5)
    const labor = safe(c.B9)

    // Total UR (零售+B2B): 工厂真实负荷
    const totalSoldEst = safe(c.B2) + wsSoldEst
    const totalUR = physMax > 0 ? Math.min(1, totalSoldEst / physMax) : 0

    // Factory economics breakdown
    const perPersonOutput = Math.round(totalSoldEst / sl[1].v)  // 人均月产出
    const b2bPct = Math.round(wsSoldEst / Math.max(1, totalSoldEst) * 100)  // B2B占比
    const revenuePerPerson = Math.round(((safe(c.B2)*sl[0].v + wsNet) / sl[1].v) / 1000 * 10) / 10

    if (profit < -2000) {
      const kpis: string[] = []
      const acts: string[] = []

      kpis.push('零售' + safe(c.B2) + '件')
      kpis.push('B2B≈¥' + (wsNet/1000).toFixed(0) + 'k(' + b2bPct + '%)')
      kpis.push('人均' + perPersonOutput + '件/月')

      // Factory P&L analysis
      const costPerPerson = Math.round((labor + rent + sl[3].v + sl[2].v*sl[1].v + 1200 + sl[1].v*sl[6].v*0.02) / sl[1].v / 1000 * 10) / 10
      // Factory P&L: 缺口的根因是什么
      const monthlyGap = Math.abs(profit)  // 亏损缺口
      if (wsNet < labor * 0.5) {
        // B2B barely covers labor — need more margin
        kpis.push('⚠B2B薄利(件赚¥' + wsMarginPerItem.toFixed(1) + ')')
        acts.push('提价→¥' + Math.min(26, sl[0].v+4) + '(B2B+¥' + Math.round(sl[0].v*0.25*wsSoldEst/1000) + 'k/月)')
        if (sl[4].v > 1) acts.push('原料→¥' + Math.max(1, sl[4].v-1))
      }
      // Main fix path: B2B working but fixed costs too heavy
      const priceImpact = Math.round((sl[0].v + 4) * 0.25 * wsSoldEst / 1000) - Math.round(wsNet / 1000)
      if (sl[0].v < 26 && b2bPct > 50) {
        acts.push('提价→¥' + Math.min(26, sl[0].v+4) + '(B2B增¥' + Math.max(1, priceImpact) + 'k)')
      }
      if (sl[4].v > 1) acts.push('原料→¥' + Math.max(1, sl[4].v-1) + '(省成本)')
      // Labor reduction if overstaffed for retail
      if (sl[1].v > 4 && monthlyGap > labor * 0.3) {
        const target = Math.max(3, sl[1].v - 1)
        acts.push('试裁→' + target + '人(月省¥' + Math.round(sl[6].v/1000) + 'k)')
      }

      // Fallback
      if (acts.length === 0) {
        if (sl[0].v < 26) acts.push('提价→¥' + Math.min(28, sl[0].v+4))
        if (sl[4].v > 1) acts.push('原料→¥' + Math.max(1, sl[4].v-1))
        if (sl[1].v > 4) acts.push('试裁到' + Math.max(3, Math.ceil(sl[1].v*0.7)) + '人')
      }

      return '🏭 月亏 ¥' + Math.abs(Math.round(profit/1000)) + 'k | ' + kpis.join(' ') + ' | → ' + acts.slice(0, 3).join('、')
    }

    if (profit < 5000) {
      // 薄利诊断：给具体可操作建议
      const acts: string[] = []

      // 每项操作对利润的预估影响
      if (sl[0].v < 26 && b2bPct > 50) {
        const priceNow = Math.round(wsNet / 1000)
        const priceGain = Math.round(wsSoldEst * (sl[0].v + 2) * 0.25 / 1000)
        if (priceGain > priceNow) acts.push('提价→¥' + (sl[0].v + 2) + '(B2B从¥' + priceNow + 'k→¥' + priceGain + 'k)')
      }
      // Factory-specific: kill marketing (B2B doesn't need retail traffic)
      if (b2bPct > 70 && sl[3].v >= 1000) {
        acts.push('砍营销→¥0(工厂靠B2B不靠客流, 月省¥' + Math.round(sl[3].v/1000) + 'k)')
      }
      if (sl[4].v > 1) {
        const ingrSave = Math.round(wsSoldEst * (sl[4].v - 1) * 0.5 / 1000)
        if (ingrSave > 0) acts.push('原料→¥' + (sl[4].v - 1) + '(月省¥' + ingrSave + 'k)')
      }
      // Factory-specific: kill location (industrial rent already cheap, but grade still multiplies it)
      if (b2bPct > 70 && sl[7].v >= 3) {
        acts.push('地段→' + Math.max(1, sl[7].v - 2) + '(工厂不看地段, 月省租金)')
      }
      if (sl[6].v > 3000 && sl[1].v >= 4) {
        acts.push('降薪→¥' + Math.max(2500, sl[6].v - 1000) + '(月省¥' + Math.round(sl[1].v * 1000 / 1000) + 'k)')
      }
      if (acts.length === 0) {
        if (sl[0].v < 28) acts.push('提价→¥' + (sl[0].v + 4))
        if (sl[4].v > 1) acts.push('原料→¥' + Math.max(1, sl[4].v - 1))
      }

      return '🏭 薄利 ¥' + profit.toLocaleString() + ' | 人均' + perPersonOutput + '件 B2B' + b2bPct + '% | → ' + acts.slice(0, 3).join('、')
    }

    return '🏭 稳健 ¥' + (profit/1000).toFixed(1) + 'k/月 | 人均' + perPersonOutput + '件 B2B' + b2bPct + '% | UR' + Math.round(totalUR*100) + '%'
  }

  // ===== 通用诊断（非工厂 / 工厂已返回）=====

  // FAT 危机
  if (fat > 80) {
    if (isUnderstaffed) return '\uD83D\uDD34 过劳FAT' + fat + ' | 缺' + minStaff + '人\u2192+3FAT/\u6708 | \u7acb\u5373\u52a0\u4eba\u5230' + minStaff + '+'
    return '\uD83D\uDD34 过劳FAT' + fat + ' | UR' + Math.round(ur*100) + '% | \u63d0\u4ef7\u6216\u6269\u4ea7\u51cf\u8d1f'
  }

  // UR \u9884\u8b66
  if (ur > 0.88) {
    const sp = Math.min(38, Math.round(sl[0].v * 1.08))
    return '\uD83D\uDFE1 \u9ad8\u8d1f\u8377UR' + Math.round(ur*100) + '% | \u63d0\u4ef7\u2192\u00a5' + sp + '\u6216\u6269\u4ea7 | \u5426\u5219FAT\u5feb\u901f\u7d2f\u79ef'
  }

  // \u54c1\u724c\u5b9a\u4ef7\u6743
  if (brand > 80 && ur < 0.85 && sl[0].v < 34 && profit > -3000) {
    const bp2 = Math.round(12 * Math.log(1 + brand / 25))
    const suggest = Math.min(32, Math.round(sl[0].v * 1.06))
    return '\uD83D\uDC8E \u54c1\u724c' + brand + '\u6ea2\u4ef7\u2248\u00a5' + bp2 + ' | \u53ef\u63d0\u4ef7\u2192\u00a5' + suggest
  }

  // \u54c1\u8d28\u8fc7\u4f4e
  if ((safe(c.B28) || 0) < 0.5 && sl[4].v < 5 && brand < 40 && profit < 0) {
    return '\uD83E\uDDEA \u54c1\u8d28' + (safe(c.B28)||0.6).toFixed(2) + '\u8fc7\u4f4e\u2192\u54c1\u724c\u6da8\u4e0d\u52a8 | \u539f\u6599\u2192\u00a5' + Math.min(5, sl[4].v+2) + '+'
  }

  if (best < 25) return '\uD83D\uDD0D \u672a\u5f62\u6210\u6e05\u6670\u7b56\u7565 | \u9009\u65b9\u5411: \uD83C\uDFE0\u793e\u533a(\u5c0f\u9762\u79ef+\u597d\u5730\u6bb5) \uD83C\uDFED\u5de5\u5382(\u2265150m\u00b2+B2B) \u2728\u9ad8\u5962(\u9ad8\u552e\u4ef7+\u5730\u6bb57+)'

  if (cScore >= fScore && cScore >= lScore && cScore > 40) {
    if (ur > 0.85) return '\uD83C\uDFE0 \u793e\u533a\u00b7UR' + Math.round(ur*100) + '%\u4ea7\u80fd\u7d27\u5f20 | \u63d0\u4ef7\u6216\u52a0\u4eba | \u54c1\u724c' + brand + (brand>100?'\u2713':'')
    return '\uD83C\uDFE0 \u793e\u533a\u00b7UR' + Math.round(ur*100) + '% FAT' + fat + ' | \u54c1\u724c' + brand + (brand>100?'(\u62a4\u57ce\u6cb3\u6fc0\u6d3b)':'(\u79ef\u7d2f\u4e2d)')
  }
  if (fScore >= cScore && fScore >= lScore && fScore > 40) {
    const wsMsg2 = sl[5].v >= 150 ? 'B2B\u5df2\u6fc0\u6d3b' : '\u9762\u79ef\u9700\u2265150m\u00b2'
    const staffMsg2 = isUnderstaffed ? ' \u26a0\u7f3a' + minStaff + '\u4eba' : (sl[1].v > Math.ceil(safe(c.B2)/400)+2 ? ' \u26a0\u4eba\u5197\u4f59' : '')
    return '\uD83C\uDFED \u5927\u5382\u00b7UR' + Math.round(ur*100) + '% | ' + wsMsg2 + staffMsg2
  }
  if (lScore >= cScore && lScore >= fScore && lScore > 40) {
    return '\u2728 \u9ad8\u5962\u00b7UR' + Math.round(ur*100) + '% FAT' + fat + ' | ' + (sl[7].v>=7?'\u65c5\u6e38\u5ba2\u2713':'\u5730\u6bb5\u21927+')
  }
  const ns = nextSeasonFactor.value
  const cs = seasonFactor.value
  let seasonHint = ''
  if (ns >= 1.20 && cs < 1.20) {
    const bump = Math.round(safe(c.B2) * (ns / cs - 1))
    if (capacityUtil.value >= 85) {
      const sugPrice = Math.min(38, Math.round(sl[0].v * 1.1))
      seasonHint = ' 📈 下月旺季 需≈+' + bump + '件 产能已满 → 提价→¥' + sugPrice + '或临时加1人'
    } else {
      seasonHint = ' 📈 下月旺季 需≈+' + bump + '件 产能有空余 → 等着多卖就行'
    }
  } else if (ns <= 0.85 && cs > 0.85) {
    const drop = Math.round(safe(c.B2) * (1 - ns / cs))
    if (sl[1].v >= 3 && sl[6].v > 3000) {
      seasonHint = ' 📉 下月淡季 需≈-' + drop + '件 → 可临时降薪到¥3k省成本'
    } else {
      seasonHint = ' 📉 下月淡季 需≈-' + drop + '件 → 产能充裕, 挺过去即可'
    }
  }
  return 'UR' + Math.round(ur*100) + '% FAT' + fat + ' | ' + (ur>0.85?'\u63d0\u4ef7\u6216\u6269\u4ea7':'\u7a33\u5b9a\u8fd0\u884c') + seasonHint
})

// 初始化计算
onMounted(async () => {
  setupBakeryRules(eng.value)
  if (eng.value?.raw) setupLogger(eng.value.raw)
  // SilentSet 写入所有节点初始值，notifyAll 根据 DAG 统一求值
  writeSlider('B1');writeSlider('B24');writeSlider('B25');writeSlider('B13')
  writeSlider('B10');writeSlider('B14');writeSlider('B26');writeSlider('B15')
  eng.value?.raw.data.SilentSet('B11','value',0)
  eng.value?.raw.data.SilentSet('B16','value',0)
  eng.value?.raw.data.SilentSet('B17','value',0)
  eng.value?.raw.data.SilentSet('B18','value',0)
  eng.value?.raw.data.SilentSet('B32','value',0)
    eng.value?.raw.data.SilentSet('B20','value',0.8)
  eng.value?.raw.data.SilentSet('B22','value',0)
  eng.value?.raw.data.SilentSet('B23','value',3)
  eng.value?.raw.data.SilentSet('B28','value',0.6)
  eng.value?.raw.data.SilentSet('FAT','value',40)
  eng.value?.raw.data.SilentSet('EMP','value',0)
  eng.value?.raw.data.SilentSet('BRAND','value',0)
  eng.value?.raw.data.SilentSet('B21','value',0.8)
  eng.value?.raw.data.SilentSet('M1','value',0)
  await eng.value?.notifyAll()
  readEngine()
  revision.value++
  if (eng.value?.changedNodes) eng.value.changedNodes.value = new Set([
    'B1','B2','B3','B4','B5','B6','B7','B8','B9','B10','B11','B12','B13','B14','B15',
'B20','B21','B22','B23','B24','B25','B26','B28','FAT','BRAND','EMP',
  ])
})
</script>
  <style scoped>
.command-center{background:#0a0a0a;height:100%;display:flex;flex-direction:column;position:relative}
.cc-scroll{height:100%}
.cc-body-inner{min-height:100%;display:flex;flex-direction:column;gap:10px;padding:10px 12px}
.cc-header{display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.title{color:#4CAF50;font-size:16px;font-weight:bold;font-family:monospace}
.month{color:#FFD700;font-size:14px;font-weight:bold;display:flex;align-items:center;gap:6px}
.season-tag{font-size:10px;padding:1px 6px;border-radius:3px;font-weight:normal}
.season-card{background:#141414;border:1px solid #2a2a2a;border-radius:10px;padding:6px 10px 4px;flex-shrink:0}
.sc-label{font-size:10px;color:#5a5a5a;font-family:monospace;margin-bottom:3px;display:flex;justify-content:space-between}
.sc-hint{font-size:9px;font-weight:bold}
.season-bar{position:relative;height:20px;background:#0a0a0a;border:1px solid #1a1a1a;border-radius:6px;display:flex;align-items:center;padding:0 1px}
.sb-marker{flex:1;text-align:center;font-size:8px;color:#4a4a4a;font-family:monospace;position:relative;z-index:1;cursor:help}
.sb-current{color:#FFD700!important;font-weight:bold;font-size:10px!important;background:#2a2000;border-radius:3px}
.sb-next{border-bottom:2px dashed #FFD700}
.sb-peak{color:#FF9800!important}
.sb-low{color:#87CEEB!important}
.hero-metrics{display:flex;gap:8px;flex-shrink:0}
.hm-card{flex:1;background:#141414;border:1px solid #2a2a2a;border-radius:10px;padding:8px 12px;display:flex;flex-direction:column;gap:3px}
.hm-card.profit{border-color:#1a3a1a}
.hm-card.loss{border-color:#2a1a1a}
.hm-top{display:flex;justify-content:space-between;align-items:center}
.hm-label{font-size:11px;color:#5a5a5a;font-family:monospace}
.hm-value{font-size:20px;font-weight:bold;font-family:monospace}
.clr-profit{color:#4CAF50}
.clr-loss{color:#f44336}
.fatigue-section{flex-shrink:0;background:#141414;border:1px solid #2a2a2a;border-radius:12px;padding:10px 14px}
.fs-header{display:flex;align-items:center;gap:10px;font-size:13px;color:#9a9a9a;font-family:monospace;margin-bottom:4px}
.fs-eff{color:#5a5a5a;font-size:12px}
.fatigue-track{position:relative;height:22px}
.ft-bg{position:absolute;inset:5px 0;border-radius:8px;overflow:hidden}
.ft-zone{position:absolute;top:0;bottom:0}
.ft-pointer{position:absolute;top:0;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:11px solid #4CAF50;transform:translateX(-6px);transition:left 0.3s;z-index:1}
.ft-labels{display:flex;justify-content:space-between;font-size:10px;color:#5a5a5a;font-family:monospace;margin-top:2px}
.env-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;flex-shrink:0}
.env-card{background:#141414;border:1px solid #2a2a2a;border-radius:10px;padding:8px 12px;display:flex;flex-direction:column;align-items:center;gap:3px}
.env-label{font-size:11px;color:#5a5a5a;font-family:monospace}
.env-value{font-size:17px;font-weight:bold;font-family:monospace}
.fingerprint-card{flex-shrink:0;background:#141414;border:1px solid #2a2a2a;border-radius:12px;padding:12px 14px}
.fp-header{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.fp-header>span:first-child{font-size:13px;color:#9a9a9a;font-family:monospace}
.fp-subtitle{font-size:11px;color:#FFD700;font-family:monospace;font-weight:bold;margin-left:auto}
.fp-bars{display:flex;flex-direction:column;gap:5px;margin-bottom:8px}
.fp-bar-row{display:flex;align-items:center;gap:8px}
.fp-icon{font-size:14px;width:22px;text-align:center}
.fp-name{font-size:11px;color:#6a6a6a;font-family:monospace;width:28px}
.fp-track{flex:1;height:8px;background:#1a1a1a;border-radius:4px;overflow:hidden}
.fp-fill{height:100%;border-radius:4px;transition:width 0.5s cubic-bezier(0.4,0,0.2,1);min-width:0}
.fp-pct{font-size:11px;font-weight:bold;font-family:monospace;width:32px;text-align:right}
.fp-insight{font-size:11px;color:#5a5a5a;font-family:monospace;line-height:1.5;border-top:1px solid #1a1a1a;padding-top:8px}
.ops-card{background:#141414;border:1px solid #2a2a2a;border-radius:12px;padding:12px 14px;flex-shrink:0;display:flex;flex-direction:column;gap:6px}
.ops-row{display:flex;justify-content:space-between;align-items:center}
.ops-label{font-size:12px;color:#5a5a5a;font-family:monospace}
.ops-value{font-size:16px;font-weight:bold;font-family:monospace;color:#9a9a9a}
.ops-bar-track{height:6px;background:#1a1a1a;border-radius:3px;overflow:hidden}
.ops-bar-fill{height:100%;border-radius:3px;transition:width 0.3s}
.ops-cost{display:flex;flex-direction:column;gap:3px}
.cost-strip{display:flex;gap:2px;height:14px;border-radius:4px;overflow:hidden}
.cost-labels{display:flex;flex-wrap:wrap;gap:3px 12px}
.cost-labels span{font-size:11px;font-family:monospace}
.cs-seg:last-child{border-radius:0 4px 4px 0}
.cs-seg:only-child{border-radius:4px}
.decision-panels{flex-shrink:0;display:flex;flex-direction:column;gap:8px}
.dp-group{background:#141414;border:1px solid #2a2a2a;border-radius:10px;padding:8px 12px}
.dp-title{font-size:12px;color:#9a9a9a;font-family:monospace;margin-bottom:6px}
.dp-row{display:flex;align-items:center;gap:8px;margin-bottom:5px}
.dp-row:last-child{margin-bottom:0}
.dp-label{font-size:11px;color:#6a6a6a;font-family:monospace;width:36px;text-align:right}
.dp-val{font-size:12px;font-weight:bold;font-family:monospace;color:#9a9a9a;min-width:60px;text-align:right}
.dp-sub{font-size:10px;color:#5a5a5a}
.goal-track{flex-shrink:0;background:#141414;border:1px solid #2a2a2a;border-radius:12px;padding:6px 14px}
.gt-header{display:flex;justify-content:space-between;font-size:12px;color:#9a9a9a;font-family:monospace}
.gt-pct{color:#4CAF50;font-weight:bold}
.gt-track{height:8px;background:#1a1a1a;border-radius:4px;overflow:hidden;margin:4px 0;position:relative}
.gt-fill{height:100%;background:linear-gradient(90deg,#4CAF50,#8BC34A);border-radius:4px;transition:width 0.5s}
.gt-label{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:9px;color:#FFD700;font-family:monospace}
.victory-banner{flex-shrink:0;background:linear-gradient(135deg,#1a2a0a,#2a1a0a);border:1px solid #FFD700;border-radius:12px;padding:10px 14px;text-align:center}
.vb-icon{font-size:28px}
.vb-text{font-size:14px;color:#FFD700;font-weight:bold;font-family:monospace}
.vb-sub{font-size:11px;color:#9a9a9a}
.year-chart-wrap{flex-shrink:0;background:#141414;border:1px solid #2a2a2a;border-radius:12px;padding:10px 14px;margin-top:6px}
.yc-header{font-size:12px;color:#9a9a9a;font-family:monospace;margin-bottom:6px}
.yc-chart{display:flex;align-items:flex-end;gap:4px;height:60px}
.yc-bar{flex:1;border-radius:3px 3px 0 0;transition:height 0.3s,opacity 0.3s;min-width:12px;cursor:help}
.yc-labels{display:flex;gap:4px;margin-top:2px}
.yc-label{flex:1;text-align:center;font-size:9px;color:#5a5a5a}
.inspector-sheet{position:absolute;bottom:54px;left:0;right:0;height:74%;z-index:20;background:#0a0a0a;border-top:1px solid #2a2a2a;border-radius:16px 16px 0 0;box-shadow:0 -8px 30px rgba(0,0,0,0.5);display:flex;flex-direction:column;padding:4px 14px 14px;overflow-y:auto}
.is-handle{display:flex;justify-content:center;padding:6px 0 8px;flex-shrink:0}
.is-handle-bar{width:40px;height:4px;border-radius:2px;background:#2a2a2a}
.is-header{display:flex;align-items:center;gap:10px;flex-shrink:0;margin-bottom:2px}
.is-icon{font-size:26px}
.is-name{font-size:18px;font-weight:bold;color:#e0e0e0;font-family:monospace}
.is-value{margin-left:auto;font-size:20px;font-weight:bold;font-family:monospace;color:#4CAF50}
.is-close{background:none;border:none;cursor:pointer;color:#3a3a3a;font-size:16px;padding:4px 8px;border-radius:6px}
.is-desc{font-size:13px;color:#6a6a6a;font-family:monospace;line-height:1.6;margin:8px 0 10px;flex-shrink:0}
.is-detail-row{display:flex;gap:8px;align-items:center;background:#141414;border:1px solid #2a2a2a;border-radius:8px;padding:8px 12px;margin-bottom:10px;flex-shrink:0}
.is-dl{font-size:12px;color:#5a5a5a;font-family:monospace}
.is-dd{font-size:14px;color:#9a9a9a;font-weight:bold;font-family:monospace}
.is-section-title{font-size:13px;color:#5a5a5a;font-family:monospace;margin-bottom:4px;flex-shrink:0}
.is-links{display:flex;flex-direction:column;gap:3px;margin-bottom:10px}
.is-link-item{display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:8px;cursor:pointer;transition:background 0.15s}
.is-link-item:hover{background:#141414}
.is-li-icon{font-size:16px}
.is-li-name{font-size:13px;color:#9a9a9a;font-family:monospace;flex:1}
.is-li-code{font-size:10px;color:#3a3a3a;font-family:monospace}
.is-li-val{font-size:13px;color:#4CAF50;font-weight:bold;font-family:monospace}
.is-li-arrow{font-size:13px;color:#3a3a3a}
.is-empty{font-size:12px;color:#2a2a2a;font-style:italic;font-family:monospace;margin-bottom:10px}
.sheet-enter-active{transition:transform 0.35s cubic-bezier(0.4,0,0.2,1)}
.sheet-leave-active{transition:transform 0.25s cubic-bezier(0.4,0,0.2,1)}
.sheet-enter-from{transform:translateY(100%)}
.sheet-leave-to{transform:translateY(100%)}
.sheet-enter-to{transform:translateY(0)}
.sheet-leave-from{transform:translateY(0)}
.bottom-bar{flex-shrink:0;margin-top:auto;background:linear-gradient(180deg,transparent 0%,#0a0a0a 60%);padding:10px 12px;border-top:1px solid #2a2a2a;position:sticky;bottom:0}
.bb-row{display:flex;align-items:center;gap:10px}
.bb-main{flex:1!important;letter-spacing:1px;font-weight:bold;padding:14px 0!important;font-size:16px!important}
</style>
                              