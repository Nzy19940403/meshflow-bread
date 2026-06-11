<template>
  <div class="guide-content">
    <details class="g-section" open>
      <summary>🎯 三条路线</summary>
      <div class="g-cards">
        <div class="g-card">
          <div class="gc-icon">🏠</div>
          <div class="gc-name">社区面包房</div>
          <div class="gc-desc">面积60-90m² 地段3-5 售价¥22-28</div>
          <div class="gc-tip">靠地段客流+口碑复购+品牌溢价。薄利但有稳定回头客, 淡季品牌护城河防止暴跌。</div>
        </div>
        <div class="g-card">
          <div class="gc-icon">🏭</div>
          <div class="gc-name">中央工厂</div>
          <div class="gc-desc">面积150-250m² 地段1-2 售价¥18-22</div>
          <div class="gc-tip">B2B企业订单是核心: 每人月产1200件, 批发价=min(零售价,¥22)×25%×品质系数。低地段工业区租金极便宜。薄利走量, 跑满产能是王道。</div>
        </div>
        <div class="g-card">
          <div class="gc-icon">✨</div>
          <div class="gc-name">精品烘焙</div>
          <div class="gc-desc">面积80-100m² 地段7-10 售价¥32-40</div>
          <div class="gc-tip">核心商圈+高品牌溢价+旅游客流。高固定成本(折旧包装贵), 但每件毛利厚, 品牌积累后爆发。</div>
        </div>
      </div>
    </details>

    <details class="g-section" open>
      <summary>🎮 操作</summary>
      <ul>
        <li>调整左侧 <strong>8个滑块</strong>（售价/人数/培训/营销/面积/地段/原料/工资）</li>
        <li>点击 <strong>▶ 推进下月</strong> → 引擎自动推演所有 28+节点</li>
        <li>右侧 <strong>DAG拓扑图</strong>展示节点依赖关系，<strong>点击节点</strong>查看上下游详情</li>
        <li>左侧面板实时显示 <strong>策略指纹</strong>（百分比+诊断）和 <strong>季节历</strong></li>
        <li><strong>◀ 回退</strong>可回溯，<strong>🔄 重置</strong>重新开始</li>
      </ul>
    </details>

    <details class="g-section" open>
      <summary>📅 季节系统</summary>
      <p>12个月的季节系数决定客流波动。左下角 <strong>季节历</strong> 显示全年:</p>
      <div style="display:flex;gap:4px;font-size:10px;font-family:monospace;flex-wrap:wrap;line-height:2">
        <span style="color:#87CEEB">1月×0.85</span> <span>2月×1.10</span> <span>3-5月×0.95~1.00</span>
        <span style="color:#87CEEB">6-8月×0.85~0.90</span> <span style="color:#FFD700">9月中秋×1.25</span>
        <span>10-11月×1.00~1.10</span> <span style="color:#FFD700">12月圣诞×1.30</span>
      </div>
      <p style="margin-top:6px">品牌≥100后拥有护城河(淡季最低0.90)。<strong>旺季前</strong>提价或加人备产，<strong>淡季前</strong>降产能省成本。推进后日志会显示季节预警。</p>
    </details>

    <details class="g-section" open>
      <summary>⚙️ 核心机制</summary>
      <p><strong>动态路线参数</strong>: 引擎根据面积和地段自动调节转化率、租金、包装费等17个参数——参数平滑过渡，不需要"切换路线"。</p>
      <p><strong>B2B企业订单</strong>(面积≥150): 每人月产1200件，批发价=min(零售价,¥22)×25%×品质系数。品质B28过低→买方压价打7折。</p>
      <p><strong>FAT疲劳</strong>: 零售UR>88%→+35/月。总UR>65%→B2B累积疲劳+15/月。满负荷工厂均衡在85-90。总UR≥90%时禁止恢复。</p>
      <p><strong>品牌溢价</strong>: 12×ln(1+BRAND/25)×地段因子。低地段(≤5)品牌溢价受限。高奢品牌系数自动提升到22。</p>
      <p><strong>B21满意度</strong>: 工资水平占40%权重+产出效率占60%。降薪确实会降满意度，但工厂B2B不靠满意度定价。</p>
    </details>

    <details class="g-section" open>
      <summary>💡 策略提示</summary>
      <ul>
        <li><strong>🏠 社区</strong>: 好地段+合理售价是关键。建议售价≥¥24，原料≥¥3。品牌过100后淡季有底。</li>
        <li><strong>🏭 工厂</strong>: 低地段+大面积+7人以上。工资≥¥3k保持运转，原料≥¥2避免B2B品质惩罚。可砍营销砍地段。</li>
        <li><strong>✨ 高奢</strong>: 地段≥7，售价≥¥34，原料≥¥4。扛过品牌积累期就能爆发。旅游客流是区位红利。</li>
        <li><strong>📅 季节应对</strong>: 查看左侧季节提示。旺季前加人或提价。淡季前降薪降营销省成本。</li>
      </ul>
    </details>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.guide-content {
  color: #e0e0e0;
  font-size: 13px;
  line-height: 1.7;
  padding: 4px 0;
}
.g-section {
  margin-bottom: 10px;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 8px 14px;
  background: #0d0d0d;
}
.g-section[open] {
  background: #111;
}
.g-section summary {
  font-size: 14px;
  font-weight: bold;
  color: #FFD700;
  cursor: pointer;
  padding: 4px 0;
  font-family: monospace;
}
.g-section p {
  margin: 6px 0;
  color: #aaa;
}
.g-section ul {
  padding-left: 18px;
  margin: 4px 0;
}
.g-section li {
  margin-bottom: 4px;
  color: #999;
}
.g-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}
.g-card {
  background: #141414;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 10px 14px;
}
.gc-icon { font-size: 20px; margin-bottom: 2px; }
.gc-name { font-size: 14px; font-weight: bold; color: #e0e0e0; margin-bottom: 2px; }
.gc-desc { font-size: 12px; color: #888; font-family: monospace; margin-bottom: 4px; }
.gc-tip { font-size: 11px; color: #666; font-family: monospace; line-height: 1.5; }
</style>
