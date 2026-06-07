"""
面包店经营模型 V6 — Python 穷举验证脚本

穷举搜索最优策略，然后与 MeshFlow 引擎的输出进行比对。
输出：
  1. Top 10 最优策略（全年利润）
  2. 精品店路线最优解
  3. 工厂路线最优解
  4. 指定策略的逐月明细（供对比 MeshFlow）
"""

import math
import itertools
import time
import json

# ============================================================
# 常量
# ============================================================
B10 = 3   # 原料成本 (元/个)
B11 = 1   # 其他变动成本 (元/个)

# ============================================================
# 核心推演函数
# ============================================================

def compute_cell_b3(area: float, labor: float, last_demand: float) -> tuple:
    """
    计算 B3(产能) 核心逻辑，含纠缠收敛。
    返回 (B3, B4) 收敛后的值。
    """
    if area <= 0 or labor <= 0:
        return 0, 2.0

    base_from_area = math.floor(area * 25)
    base_from_labor = math.floor(labor / 5.0)
    resource_cap = min(base_from_area, base_from_labor)
    from_demand = round(last_demand * 1.2)

    # Epoch 1: E1 (B16→B3, w10) 胜出
    b3 = min(resource_cap, from_demand)
    b4 = max(0.1, 2 - b3 * 0.0002)

    # Epoch 2-N: E2 (B4→B3, w7) 在B16不变时胜出
    for _ in range(20):
        prev_b3 = b3
        cost_boost = max(0, (2 - b4) * 200)
        effective_cap = math.floor(min(base_from_area, base_from_labor) + cost_boost)
        b3_new = min(effective_cap, from_demand)
        b4_new = max(0.1, 2 - b3_new * 0.0002)

        if abs(b3_new - b3) < 0.5:
            b3, b4 = b3_new, b4_new
            break
        b3, b4 = b3_new, b4_new

    return b3, b4


def simulate_year(b1: float, b9: float, b13: float, b14: float, b15: float,
                  initial_demand: float = 3600, initial_shortage: float = 0) -> dict:
    """
    模拟 12 个月经营，返回全年结果。
    
    参数:
      b1: 售价 (元)
      b9: 人工成本 (元/月)
      b13: 营销投入 (元/月)
      b14: 店面面积 (m²)
      b15: 场地等级 (1-10)
    
    返回:
      { 'profit': 全年利润, 'history': 逐月明细, ... }
    """
    state = {
        'B1': b1, 'B9': b9, 'B10': B10, 'B11': B11,
        'B13': b13, 'B14': b14, 'B15': b15,
        'B16': initial_demand, 'B17': initial_shortage,
    }

    history = []
    cumulative_profit = 0
    year_revenue = 0
    year_cost = 0

    for month in range(12):
        area = state['B14']
        labor = state['B9']
        grade = state['B15']
        price = state['B1']
        marketing = state['B13']

        # --- S1: 房租 (SetRule: B14+B15→B5) ---
        b5 = max(0, round(area * grade * max(2, 20 - area * 0.05)))

        # --- S2: 需求 (SetRule: B1+B15+B13-B17→B2) ---
        price_effect = max(300, 5000 - price * 200)
        location_effect = grade * 200
        marketing_effect = math.sqrt(max(0, marketing)) * 15
        base_demand = price_effect + location_effect + marketing_effect
        penalty = round(base_demand * state['B17'] * 0.5)
        b2 = round(base_demand - penalty)

        # --- 纠缠收敛: B3 + B4 ---
        b3, b4 = compute_cell_b3(area, labor, state['B16'])

        # --- S3: 加工成本 (SetRule: B3→B4, 但已在纠缠中同步) ---

        # --- 衍生公式 ---
        b12 = (B10 + B11 + b4) * b3   # 总生产成本
        b6 = price * min(b2, b3)       # 月收入
        b7 = b12 + b5 + labor + marketing  # 总成本
        b8 = b6 - b7                   # 月利润

        # --- 记录本月 ---
        profit = b8
        sold = min(b2, b3)
        cumulative_profit += profit
        year_revenue += b6
        year_cost += b7

        history.append({
            'month': month + 1,
            'profit': round(profit),
            'revenue': round(b6),
            'cost': round(b7),
            'demand': b2,
            'capacity': b3,
            'sold': sold,
            'b4': round(b4, 2),
            'b5': b5,
            'b12': round(b12),
        })

        # --- 月度推进: 快照到 B16/B17 ---
        shortage = 0
        if b3 < b2 and b2 > 0:
            shortage = round((b2 - b3) / b2 * 1000) / 1000
        state['B16'] = b2
        state['B17'] = shortage

    return {
        'profit': round(cumulative_profit),
        'revenue': round(year_revenue),
        'cost': round(year_cost),
        'margin_percent': round(cumulative_profit / year_revenue * 100, 1) if year_revenue > 0 else 0,
        'params': {'B1': b1, 'B9': b9, 'B13': b13, 'B14': b14, 'B15': b15},
        'history': history,
    }


def strategy_name(b1: float, b14: float) -> str:
    """对策略分类"""
    if b1 >= 20 and b14 <= 60:
        return '精品店'
    elif b1 <= 16 and b14 >= 120:
        return '大工厂'
    elif b1 >= 20:
        return '高定价'
    elif b14 >= 120:
        return '大面积'
    else:
        return '中庸'


# ============================================================
# 穷举搜索
# ============================================================

def brute_force():
    """穷举所有参数组合，找最优策略。"""
    
    # 参数范围
    b1_range = range(8, 29)                # 8-28, 21种
    b9_range = range(2000, 41000, 2000)    # 2000-40000, 20种
    b13_range = range(0, 5200, 500)        # 0-5000, 11种
    b14_range = range(20, 260, 20)         # 20-240, 12种
    b15_range = range(1, 11)               # 1-10, 10种
    
    total = len(list(b1_range)) * len(list(b9_range)) * len(list(b13_range)) \
            * len(list(b14_range)) * len(list(b15_range))
    
    print(f"📊 总计组合: {total:,}")
    print(f"   参数范围:")
    print(f"     B1(售价):     {min(b1_range)}-{max(b1_range)}  步长1  ({len(list(b1_range))}种)")
    print(f"     B9(人工):     {min(b9_range)}-{max(b9_range)}  步长1000 ({len(list(b9_range))}种)")
    print(f"     B13(营销):    {min(b13_range)}-{max(b13_range)} 步长200 ({len(list(b13_range))}种)")
    print(f"     B14(面积):    {min(b14_range)}-{max(b14_range)} 步长10  ({len(list(b14_range))}种)")
    print(f"     B15(等级):    {min(b15_range)}-{max(b15_range)} 步长1   ({len(list(b15_range))}种)")
    print()
    
    results = []
    start = time.time()
    count = 0
    report_interval = max(1, total // 100)  # 每1%报一次
    
    for b1 in b1_range:
        for b9 in b9_range:
            for b13 in b13_range:
                for b14 in b14_range:
                    for b15 in b15_range:
                        result = simulate_year(b1, b9, b13, b14, b15)
                        results.append(result)
                        count += 1
                        
                        if count % report_interval == 0:
                            elapsed = time.time() - start
                            pct = count / total * 100
                            rate = count / elapsed if elapsed > 0 else 0
                            eta = (total - count) / rate if rate > 0 else 0
                            print(f"  [{pct:.0f}%] {count:,}/{total:,}  "
                                  f"耗时{elapsed:.0f}s  速率{rate:.0f}组合/s  "
                                  f"预计剩余{eta:.0f}s", end='\r')
    
    elapsed = time.time() - start
    print(f"\n✅ 完成! 耗时 {elapsed:.1f}s, 速率 {total/elapsed:.0f} 组合/s")
    print()
    
    return results


# ============================================================
# 结果分析
# ============================================================

def analyze_results(results):
    """分析穷举结果，输出 Top 策略。"""
    
    # 按利润排序
    results.sort(key=lambda r: r['profit'], reverse=True)
    
    print("=" * 80)
    print("🥇  TOP 10 最优策略（全年利润）")
    print("=" * 80)
    print(f"{'排名':>4} {'类型':<6} {'利润':>8} {'利润率':>7} {'B1售价':>6} {'B9人工':>7} {'B13营销':>7} {'B14面积':>6} {'B15等级':>5}")
    print("-" * 80)
    for i, r in enumerate(results[:10]):
        p = r['params']
        print(f"{i+1:>4} {strategy_name(p['B1'], p['B14']):<6} "
              f"{r['profit']:>8,} {r['margin_percent']:>6}% "
              f"{p['B1']:>6} {p['B9']:>7,} {p['B13']:>7,} {p['B14']:>6} {p['B15']:>5}")
    print()
    
    # 按路线分类分析
    boutique_results = [r for r in results 
                        if r['params']['B1'] >= 18 and r['params']['B14'] <= 60]
    factory_results = [r for r in results 
                      if r['params']['B1'] <= 16 and r['params']['B14'] >= 120]
    
    if boutique_results:
        boutique_results.sort(key=lambda r: r['profit'], reverse=True)
        print("=" * 80)
        print("🥇 精品店路线 Top 5 (售价≥18, 面积≤60)")
        print("=" * 80)
        print(f"{'排名':>4} {'利润':>8} {'利润率':>7} {'B1':>6} {'B9':>7} {'B13':>7} {'B14':>6} {'B15':>5}")
        print("-" * 80)
        for i, r in enumerate(boutique_results[:5]):
            p = r['params']
            print(f"{i+1:>4} {r['profit']:>8,} {r['margin_percent']:>6}% "
                  f"{p['B1']:>6} {p['B9']:>7,} {p['B13']:>7,} {p['B14']:>6} {p['B15']:>5}")
        print()
    
    if factory_results:
        factory_results.sort(key=lambda r: r['profit'], reverse=True)
        print("=" * 80)
        print("🏭 工厂路线 Top 5 (售价≤16, 面积≥120)")
        print("=" * 80)
        print(f"{'排名':>4} {'利润':>8} {'利润率':>7} {'B1':>6} {'B9':>7} {'B13':>7} {'B14':>6} {'B15':>5}")
        print("-" * 80)
        for i, r in enumerate(factory_results[:5]):
            p = r['params']
            print(f"{i+1:>4} {r['profit']:>8,} {r['margin_percent']:>6}% "
                  f"{p['B1']:>6} {p['B9']:>7,} {p['B13']:>7,} {p['B14']:>6} {p['B15']:>5}")
        print()
    
    # 亏损策略统计
    loss_count = sum(1 for r in results if r['profit'] <= 0)
    positive_count = sum(1 for r in results if r['profit'] > 0)
    print(f"📊 统计: 盈利策略 {positive_count:,}/{len(results):,} "
          f"({positive_count/len(results)*100:.1f}%)  "
          f"亏损策略 {loss_count:,}/{len(results):,}")
    print()
    
    return results[:10]


def print_monthly_detail(result, label=""):
    """打印逐月明细，用于对比 MeshFlow 输出"""
    p = result['params']
    print(f"\n{'='*80}")
    print(f"  📋 {label}")
    print(f"  B1={p['B1']}  B9={p['B9']:,}  B13={p['B13']:,}  "
          f"B14={p['B14']}  B15={p['B15']}")
    print(f"  全年: 利润={result['profit']:,}  收入={result['revenue']:,}  "
          f"成本={result['cost']:,}  利润率={result['margin_percent']}%")
    print(f"{'='*80}")
    print(f"{'月':>3} {'需求':>6} {'产能':>6} {'实售':>6} {'加工成本':>8} "
          f"{'房租':>6} {'收入':>8} {'成本':>8} {'利润':>8}")
    print("-" * 80)
    for h in result['history']:
        print(f"{h['month']:>3} {h['demand']:>6} {h['capacity']:>6} {h['sold']:>6} "
              f"{h['b4']:>8} {h['b5']:>6} {h['revenue']:>8,} {h['cost']:>8,} {h['profit']:>8,}")


# ============================================================
# 单策略详细推演（供手动对比 MeshFlow）
# ============================================================

def single_strategy_detail(b1, b9, b13, b14, b15):
    """对单一策略做精细推演，输出每步状态"""
    
    print(f"\n{'='*80}")
    print(f"  单策略精细推演: B1={b1} B9={b9:,} B13={b13:,} B14={b14} B15={b15}")
    print(f"{'='*80}")
    
    area, labor, grade, price, marketing = b14, b9, b15, b1, b13
    
    # 计算资源上限
    base_from_area = math.floor(area * 25)
    base_from_labor = math.floor(labor / 5.0)
    resource_cap = min(base_from_area, base_from_labor)
    print(f"\n📐 资源上限: 面积→{base_from_area}  人工→{base_from_labor}  短板→{resource_cap}")
    
    initial_demand = 3600
    initial_shortage = 0
    b16 = initial_demand
    b17 = initial_shortage
    
    cumulative_profit = 0
    
    for month in range(12):
        print(f"\n{'─'*80}")
        print(f"  第 {month+1} 月")
        print(f"{'─'*80}")
        
        # S1: 房租
        b5 = max(0, round(area * grade * max(2, 20 - area * 0.05)))
        print(f"  S1 房租:      {area}×{grade}×max(2, 20-{area}×0.05) = {b5}")
        
        # S2: 需求
        price_effect = max(300, 5000 - price * 200)
        location_effect = grade * 200
        marketing_effect = math.sqrt(max(0, marketing)) * 15
        base_demand = price_effect + location_effect + marketing_effect
        penalty = round(base_demand * b17 * 0.5)
        b2 = round(base_demand - penalty)
        print(f"  S2 需求:      价效={price_effect} + 地段={location_effect} + "
              f"营销={marketing_effect:.0f} - 罚={penalty} = {b2}")
        print(f"                  (上期缺货率={b17})")
        
        # 纠缠收敛 B3
        from_demand = round(b16 * 1.2)
        b3 = min(resource_cap, from_demand)
        b4 = max(0.1, 2 - b3 * 0.0002)
        print(f"  E1 B16→B3:    min({resource_cap}, {from_demand}) = {b3}  (权10)")
        print(f"  S3 B3→B4:     max(0.1, 2-{b3}×0.0002) = {b4:.2f}")
        
        # E2 迭代
        for ep in range(5):
            prev_b3 = b3
            cost_boost = max(0, (2 - b4) * 200)
            effective_cap = math.floor(min(base_from_area, base_from_labor) + cost_boost)
            b3_new = min(effective_cap, from_demand)
            b4_new = max(0.1, 2 - b3_new * 0.0002)
            delta = abs(b3_new - b3)
            print(f"  E2 收敛ep{ep+1}: B4={b4:.2f}→红利={cost_boost}→有效上限={effective_cap} "
                  f"→B3={b3_new} (Δ={delta:.1f})")
            if delta < 0.5:
                b3, b4 = b3_new, b4_new
                break
            b3, b4 = b3_new, b4_new
        
        # 衍生公式
        b12 = (B10 + B11 + b4) * b3
        b6 = price * min(b2, b3)
        b7 = b12 + b5 + labor + marketing
        b8 = b6 - b7
        
        print(f"  B12 生产成本: ({B10}+{B11}+{b4:.2f})×{b3} = {b12:.0f}")
        print(f"  B6  月收入:   {price}×min({b2},{b3}) = {b6:.0f}")
        print(f"  B7  总成本:   {b12:.0f}+{b5}+{labor}+{marketing} = {b7:.0f}")
        print(f"  B8  月利润:   {b6:.0f} - {b7:.0f} = {b8:.0f}")
        
        sold = min(b2, b3)
        cumulative_profit += b8
        print(f"  → 实售 {sold}, 累计利润 {cumulative_profit:.0f}")
        
        # 推进
        shortage = 0
        if b3 < b2 and b2 > 0:
            shortage = round((b2 - b3) / b2 * 1000) / 1000
        b16 = b2
        b17 = shortage
    
    print(f"\n{'='*80}")
    print(f"  全年利润: {cumulative_profit:.0f}")
    print(f"{'='*80}\n")


# ============================================================
# 主入口
# ============================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'single':
        # 单策略精细推演模式
        b1 = float(sys.argv[2]) if len(sys.argv) > 2 else 24
        b9 = float(sys.argv[3]) if len(sys.argv) > 3 else 6325
        b13 = float(sys.argv[4]) if len(sys.argv) > 4 else 300
        b14 = float(sys.argv[5]) if len(sys.argv) > 5 else 46
        b15 = float(sys.argv[6]) if len(sys.argv) > 6 else 5
        single_strategy_detail(b1, b9, b13, b14, b15)
    else:
        # 穷举模式
        results = brute_force()
        top = analyze_results(results)
        
        # 输出 Top1 逐月明细
        print_monthly_detail(top[0], f"🥇 全局最优 (利润={top[0]['profit']:,})")
        
        # 按路线分类
        boutique_top = [r for r in results 
                       if r['params']['B1'] >= 18 and r['params']['B14'] <= 60]
        factory_top = [r for r in results 
                     if r['params']['B1'] <= 16 and r['params']['B14'] >= 120]
        
        if boutique_top:
            boutique_top.sort(key=lambda r: r['profit'], reverse=True)
            print_monthly_detail(boutique_top[0], "🥇 精品路线最优")
        
        if factory_top:
            factory_top.sort(key=lambda r: r['profit'], reverse=True)
            print_monthly_detail(factory_top[0], "🏭 工厂路线最优")
        
        # 保存 JSON 供后续对比
        output = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_combinations': len(results),
            'top10': [{
                'profit': r['profit'],
                'revenue': r['revenue'],
                'cost': r['cost'],
                'margin_pct': r['margin_percent'],
                'params': r['params'],
                'strategy': strategy_name(r['params']['B1'], r['params']['B14']),
                'history': r['history'],
            } for r in top],
        }
        with open('bruteforce_results.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n📁 结果已保存到 bruteforce_results.json")
