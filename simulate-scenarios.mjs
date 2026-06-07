/**
 * 面包店模型 12 个月推演 — 纯数学模拟
 * 复刻 App.vue + GraphEditor.vue 中的所有公式
 */

function simulate(b1_price, b9_labor, b13_marketing, b14_area, b15_grade, label) {
  const B10 = 3, B11 = 1;
  let b16 = 0, b17 = 0, b18 = 0, b19 = 0;
  let b20 = 0.8, b21 = 0.8, b4 = 2;

  // 首月估值: 先算 B2, 然后 B16 = B2
  const firstB2 = computeB2(b1_price, b15_grade, b13_marketing, b17=0, b19=0);
  b16 = Math.max(100, Math.round(firstB2));

  console.log(`\n${'='.repeat(60)}`);
  console.log(`  ${label}`);
  console.log(`  B1=${b1_price}  B9=${b9_labor}  B13=${b13_marketing}  B14=${b14_area}  B15=${b15_grade}`);
  console.log(`  B10=${B10}  B11=${B11}`);
  console.log(`  ${'='.repeat(60)}`);
  console.log(`  月 | 需求  | 产能   |  收入   |  成本    |  利润    | 知名度 | 报废率`);
  console.log(`  ${'-'.repeat(62)}`);

  let cumProfit = 0, yearRevenue = 0, yearCost = 0, profitMonths = 0;

  for (let month = 1; month <= 12; month++) {
    // 1. 需求 B2
    const b2 = computeB2(b1_price, b15_grade, b13_marketing, b17, b19);

    // 2. 产能 B3 (物理上限)
    const b3 = computeB3(b14_area, b9_labor, b4);

    // 3. 加工成本 B4 (规模效应)
    b4 = Math.max(0.1, 2 - b3 * 0.0002);

    // 4. 房租 B5
    const b5 = computeB5(b14_area, b15_grade);

    // 5. 收入 B6
    const sold = Math.min(b2, b3);
    const b6 = b1_price * sold;

    // 6. 总生产成本 B12
    const b12 = (B10 + B11 + b4) * b3;

    // 7. 总成本 B7
    const b7 = b12 + b5 + b9_labor + b13_marketing;

    // 8. 利润 B8
    const b8 = b6 - b7;

    // 9. 员工满意度 B21
    b21 = computeB21(b9_labor, b3, b14_area, b15_grade);

    // 10. 口味 B20
    b20 = computeB20(b21, b3, b14_area);

    // 11. 记录月度
    cumProfit += b8;
    yearRevenue += b6;
    yearCost += b7;
    if (b8 > 0) profitMonths++;

    const shortage = (b3 < b2 && b2 > 0) ? (b2 - b3) / b2 : 0;
    const waste = (b3 > b2 && b3 > 0) ? (b3 - b2) / b3 : 0;

    console.log(
      `  ${String(month).padStart(2)} | ${String(b2).padStart(5)} | ${String(b3).padStart(5)} | ` +
      `${String(b6.toFixed(0)).padStart(7)} | ${String(b7.toFixed(0)).padStart(7)} | ` +
      `${String(b8.toFixed(0)).padStart(7)} | ${String(b19).padStart(4)} | ${(waste*100).toFixed(0)}%`
    );

    // 12. 写入下月缓存
    b16 = b2;
    b17 = shortage;
    b18 = waste;

    // 13. 品牌增长 B19
    const traffic = Math.round(150 * Math.pow(b15_grade, 1.7)) + Math.sqrt(Math.max(0, b13_marketing)) * 15;
    const mouthGrowth = 10;
    const growth = Math.round(b20 * (traffic / 100 + mouthGrowth));
    const decayRate = Math.max(0.05, b19 * 0.01);
    const decay = Math.round(b19 * decayRate);
    b19 = Math.max(0, b19 + growth - decay);
  }

  const margin = yearRevenue > 0 ? (cumProfit / yearRevenue * 100).toFixed(1) : '—';
  console.log(`  ${'-'.repeat(62)}`);
  console.log(`  年利润: ¥${cumProfit.toLocaleString()}  | 利润率: ${margin}%  | 盈利月: ${profitMonths}/12`);
}

// === 公式实现 ===

function computeB2(price, grade, marketing, shortage, brand) {
  const p = Number(price) || 12;
  const g = Number(grade) || 5;
  const m = Number(marketing) || 0;
  const s = Number(shortage) || 0;
  const b = Number(brand) || 0;

  const priceDiscountBoost = p < 15 ? 1.0 + (15 - p) * 0.2 : 1.0;
  const traffic = Math.round(150 * Math.pow(g, 1.7)) + Math.round(Math.sqrt(Math.max(0, m)) * 15 * priceDiscountBoost);

  const brandPremium = b * 0.5;
  const locationPremium = g * 1.5;
  const maxAcceptable = 10 + locationPremium + brandPremium;

  let retention;
  if (p <= maxAcceptable) {
    retention = 0.5 + (maxAcceptable - p) / maxAcceptable * 0.4;
  } else {
    retention = Math.max(0.05, 0.5 * maxAcceptable / p);
  }

  const base = Math.round(traffic * retention);
  const penalty = Math.round(base * s * 0.5);
  return Math.max(0, base - penalty);
}

function computeB3(area, labor, cost) {
  const a = Number(area) || 80;
  const l = Number(labor) || 15000;
  const c = Number(cost) || 2;
  if (a <= 0 || l <= 0) return 0;
  const areaCap = Math.floor(a * 25);
  const laborCap = Math.floor(l / 2.5);
  const hardwareCap = Math.min(areaCap, laborCap);
  const efficiencyBonus = Math.max(0, Math.round((2 - c) * 200));
  return Math.max(0, hardwareCap + efficiencyBonus);
}

function computeB5(area, grade) {
  const a = Number(area) || 80;
  const g = Number(grade) || 5;
  return Math.max(0, Math.round(a * g * Math.max(2, 20 - a * 0.05)));
}

function computeB21(labor, cap, area, grade) {
  const l = Number(labor) || 15000;
  const c = Number(cap) || 1000;
  const a = Number(area) || 80;
  const g = Number(grade) || 5;
  const payPerOutput = l / Math.max(c, 1);
  const utilization = c / Math.max(a * 25, 1);
  const payBaseline = 3.0 + g * 0.4;
  let paySat;
  if (payPerOutput >= payBaseline) {
    paySat = 0.7 + Math.min((payPerOutput - payBaseline) / (payBaseline * 2), 0.3);
  } else {
    paySat = payPerOutput / payBaseline * 0.7;
  }
  const overworkPenalty = Math.max(0, utilization - 0.8) * 1.5;
  return Math.round(Math.min(1, Math.max(0, paySat - overworkPenalty)) * 1000) / 1000;
}

function computeB20(satisfaction, cap, area) {
  const s = Number(satisfaction) || 0.8;
  const c = Number(cap) || 1000;
  const a = Number(area) || 80;
  const utilization = c / Math.max(a * 25, 1);
  let taste;
  if (s >= 0.6) {
    const overload = Math.max(0, utilization - 0.9) * 0.5;
    taste = Math.min(1, Math.max(0.3, 1.0 - overload));
  } else {
    taste = s * 0.6;
  }
  return Math.round(taste * 1000) / 1000;
}

// === 三种策略 ===
simulate(22, 5000, 300, 60, 5, '✨ 高奢网红店 (售价22 面积60 人工5k 营销300)');
simulate(10, 25000, 8000, 200, 3, '🏭 薄利大厂 (售价10 面积200 人工25k 营销8k)');
simulate(14, 12000, 0, 100, 5, '🏠 社区老店 (售价14 面积100 人工12k 营销0)');
