"""
cashflow_design.py — 现金流死亡螺旋 功能设计验证
================================================
在 ref_model.py 基础上扩展，设计并验证新机制。
"""

import sys
sys.path.insert(0, '.')
from ref_model import (
    simulate_one_year, simulate_one_month,
    compute_demand, compute_capacity, compute_processing_cost,
    compute_rent, compute_satisfaction, compute_taste, compute_brand,
    SEASONAL_FACTORS
)


# ============================================================
# 设计一：三条路线在零初始现金下的月度现金流曲线
# ============================================================

def cash_curve_analysis():
    """分析每条路线在全年中的现金流累积趋势"""
    scenarios = [
        ("✨ 高奢网红店", dict(price=28, labor=8000, material_cost=3,
                               other_cost=1, marketing=6000, area=120, grade=9)),
        ("🏭 薄利大厂", dict(price=16, labor=8000, material_cost=3,
                             other_cost=1, marketing=2000, area=150, grade=7)),
        ("🏠 社区老店", dict(price=16, labor=6000, material_cost=3,
                             other_cost=1, marketing=0, area=60, grade=5)),
        # 额外：一条有风险的"激进扩张"路线
        ("🔥 激进扩张", dict(price=18, labor=12000, material_cost=3,
                             other_cost=1, marketing=4000, area=200, grade=6)),
    ]
    
    print(f"\n{'='*75}")
    print(f"  现金流曲线分析（零初始现金，逐月累积）")
    print(f"{'='*75}")
    
    results = []
    for name, params in scenarios:
        r = simulate_one_year(
            price=params['price'], labor=params['labor'],
            material_cost=params['material_cost'], other_cost=params['other_cost'],
            marketing=params['marketing'], area=params['area'],
            grade=params['grade'],
            track_cash=True, initial_cash=0
        )
        monthly_profits = [m['B8_profit'] for m in r['months'] if not m.get('bankrupt')]
        cash_vals = [m.get('cash', 0) for m in r['months']]
        
        # 找出最大累计亏损（现金流最低点）
        min_cash = min(cash_vals) if cash_vals else 0
        
        print(f"\n  {name}")
        print(f"  月利润: {', '.join(f'{p:+,.0f}' for p in monthly_profits)}")
        
        # 画个简单的现金流条
        bar_width = 40
        max_abs = max(abs(c) for c in cash_vals) if cash_vals else 1
        print(f"  现金流轨迹:")
        for i, c in enumerate(cash_vals):
            bar_len = int(abs(c) / max_abs * bar_width)
            bar = '█' * bar_len if c >= 0 else '█' * bar_len
            if bar:
                print(f"    月{i+1:>2}: {bar} {c:+,.0f}")
            else:
                print(f"    月{i+1:>2}: (0) {c:+,.0f}")
        
        # 存活分析
        if r['bankrupt']:
            bankrupt_month = r['months_completed']
            print(f"  💀 破产！第{bankrupt_month}个月现金耗尽")
        else:
            print(f"  ✅ 存活12个月")
        
        # 需要的最低初始现金
        required = abs(min_cash)
        if required == 0:
            print(f"  💰 自造血，无需初始现金")
        else:
            print(f"  💰 最低初始现金需求: ¥{required:,}")
        
        results.append({
            'name': name,
            'params': params,
            'annual_profit': r['annual']['profit'],
            'min_cash': min_cash,
            'required_capital': required,
            'bankrupt': r['bankrupt'],
            'bankrupt_month': r['months_completed'] if r['bankrupt'] else None,
        })
    
    return results


# ============================================================
# 设计二：不同初始现金下的存活率扫描
# ============================================================

def capital_sweep():
    """扫描不同初始现金对存活率的影响"""
    print(f"\n{'='*75}")
    print(f"  初始现金存活率扫描")
    print(f"{'='*75}")
    
    test_strategies = [
        ("保守小本", dict(price=16, labor=6000, material_cost=3,
                         other_cost=1, marketing=0, area=60, grade=5)),
        ("均衡中型", dict(price=18, labor=10000, material_cost=3,
                         other_cost=1, marketing=3000, area=100, grade=6)),
        ("激进扩张", dict(price=18, labor=12000, material_cost=3,
                         other_cost=1, marketing=4000, area=200, grade=6)),
        ("高奢冒险", dict(price=28, labor=12000, material_cost=3,
                         other_cost=1, marketing=6000, area=120, grade=9)),
    ]
    
    capital_levels = [0, 10000, 30000, 50000, 80000, 100000, 150000, 200000]
    
    header = f"  {'策略':<16} | {'初始现金':>10} → {'结果':<12} | {'年利润':>10}"
    print(f"\n  {header}")
    print(f"  {'-'*16}-+-{'-'*10}-+-{'-'*12}-+-{'-'*10}")
    
    for name, params in test_strategies:
        for cap in capital_levels:
            r = simulate_one_year(
                price=params['price'], labor=params['labor'],
                material_cost=params['material_cost'], other_cost=params['other_cost'],
                marketing=params['marketing'], area=params['area'],
                grade=params['grade'],
                track_cash=True, initial_cash=cap
            )
            if r['bankrupt']:
                status = f"💀 月{r['months_completed']}"
            else:
                status = "✅ 存活"
            profit = r['annual']['profit']
            print(f"  {name:<16} | ¥{cap:>8,} → {status:<12} | ¥{profit:>+8,.0f}")
        print()  # 空行分隔策略组


# ============================================================
# 设计三：破产临界点分析 + 预警线
# ============================================================

def bankruptcy_threshold_analysis():
    """分析哪些策略在什么条件下容易破产，设计预警机制"""
    print(f"\n{'='*75}")
    print(f"  破产阈值与预警设计")
    print(f"{'='*75}")
    
    # 1) 找出"危险区间"——那些月利润有正有负的策略
    print(f"\n  📊 哪些策略有正有负（最需要现金流保护）：")
    
    test_grid = [
        # (售价, 面积, 人工, 等级, 描述)
        (16, 60, 6000, 5, "保守小本"),
        (18, 80, 8000, 5, "中型均衡"),
        (20, 120, 10000, 7, "中高档"),
        (16, 150, 8000, 7, "薄利大厂"),
        (28, 120, 8000, 9, "高奢"),
        (28, 120, 12000, 9, "高奢+高人力"),
    ]
    
    for price, area, labor, grade, desc in test_grid:
        m1 = simulate_one_month(price, labor, 3, 1, 0, area, grade)
        m1_profit = m1['B8_profit']
        
        # 跑一年看最差月
        r = simulate_one_year(price, labor, 3, 1, 0, area, grade)
        monthly = [m['B8_profit'] for m in r['months'] if not m.get('bankrupt')]
        worst = min(monthly) if monthly else 0
        best = max(monthly) if monthly else 0
        
        # 计算"喘息月数"：¥50,000初始现金能撑几个月亏损
        loss_per_month = abs(worst) if worst < 0 else 0
        survival = int(50000 / loss_per_month) if loss_per_month > 0 else "∞"
        
        print(f"  {desc:<14} 首月利润:{m1_profit:>+8,.0f}  | "
              f"最差月:{worst:>+8,.0f} 最好月:{best:>+8,.0f}  | "
              f"¥50k可撑:{survival}月")

    # 2) 预警机制设计
    print(f"\n")
    print(f"  🚨 预警设计：")
    print(f"  ┌─────────────────────────────────────────────────────┐")
    print(f"  │  现金 >= 月支出×3  →  🟢 安全                         │")
    print(f"  │  现金 >= 月支出×1  →  🟡 警告（现金不够下月开支）       │")
    print(f"  │  现金 > 0          →  🟠 危险（随时可能破产）           │")
    print(f"  │  现金 <= 0         →  🔴 破产！💀                     │")
    print(f"  └─────────────────────────────────────────────────────┘")


# ============================================================
# 设计四：功能实现方案
# ============================================================

def implementation_plan():
    """完整的 Vue 前端修改方案"""
    print("\n" + "=" * 75)
    print("  [T] Vue 前端实现方案")
    print("=" * 75)
    
    plan = """
  [?] 修改文件: src/GraphEditor.vue

  [NEW STATE]
    initialCash = ref(50000)      -- 初始现金（可配置）
    cashBalance = ref(50000)      -- 当前现金余额
    bankrupt    = ref(false)      -- 是否破产

  [GraphEditor.vue 改动点]

  1. sim-bar 加一行现金显示：
     --- 月进度 + 本月利润 + 累计 + 现金余额

  2. advanceMonth() 末尾加：
     cashBalance.value += profit
     if cashBalance.value < 0:
         bankrupt.value = true
         // 弹出 !!! 破产 模态框
         // 锁定"下个月"按钮

  3. newYear() 重置现金：
     cashBalance.value = initialCash.value

  4. 新增[初始现金]滑块：
     范围 10,000~500,000 STEP=5000

  5. 破产状态：
     -- 全图半透明遮罩 + "!!! 经营不善，破产了！"
     -- 按钮变[ 重新开始 ]
     -- 保留年终总结（虽然没满12月）

  [FORMULA CHANGES]
    无公式改动！现金是纯外部状态，不影响 B1~B21 任何节点。
    """
    print(plan)
    
    print(f"  {'='*75}")
    print(f"  三条路线在 50,000 初始现金下的存活验证")
    print(f"  {'='*75}")
    
    for name, params in [
        ("✨ 高奢网红店", dict(price=28, labor=8000, material_cost=3,
                               other_cost=1, marketing=6000, area=120, grade=9)),
        ("🏭 薄利大厂", dict(price=16, labor=8000, material_cost=3,
                             other_cost=1, marketing=2000, area=150, grade=7)),
        ("🏠 社区老店", dict(price=16, labor=6000, material_cost=3,
                             other_cost=1, marketing=0, area=60, grade=5)),
    ]:
        r = simulate_one_year(**params, track_cash=True, initial_cash=50000)
        if r['bankrupt']:
            print(f"  ❌ {name} → 第{r['months_completed']}个月破产")
        else:
            end_cash = r['months'][-1].get('cash', 0)
            final_cash = r['annual']['profit'] + 50000
            tightest = min(m.get('cash', 0) for m in r['months'])
            print(f"  ✅ {name} → 年末现金 ¥{final_cash:,.0f}  (最低: ¥{tightest:,.0f})")


if __name__ == '__main__':
    results = cash_curve_analysis()
    capital_sweep()
    bankruptcy_threshold_analysis()
    implementation_plan()
