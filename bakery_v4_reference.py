"""
bakery_v4_reference.py
============================================
面包店 V4 参考模型 — 权威验证工具

用途:
  这个文件是「唯一权威参考」。
  - MeshFlow 引擎 (engine.ts) 的计算结果必须与此一致
  - Vue 前端 (BakerySandbox.vue) 的 rc()/fd()/nx() 必须与此一致

用法:
  python bakery_v4_reference.py                          # 跑全部预设场景
  python bakery_v4_reference.py --scenario 大厂 16 8 100 8000 250 3 1200  # 自定义
  python bakery_v4_reference.py --json                    # 输出 JSON (供测试用)
  python bakery_v4_reference.py --compare                 # 与引擎现有的测试对比

容差标准:
  - 逐月利润: ≤ ¥300/月
  - 36个月总计: ≤ ¥600
  - 排除 sk 断崖导致的震荡相位偏移场景 (社区路线)

公式版本: V4 (sk断崖 + penalty 1.5 + B26工资预算 + B20=B21品质)
"""

import math, json, sys

# ============================================================
# sk 断崖 (当前 Vue/引擎版本)
# ============================================================
def sk(c4: float) -> float:
    """疲劳→产能系数 (Step Function)"""
    v = float(c4)
    if not math.isfinite(v): return 1.0
    if v < 80: return 1.0
    if v < 90: return 0.30
    return 0.10


# ============================================================
# 参数集
# ============================================================
# 每个参数: (B1售价, B24员工数, B25培训费, B13营销, B14面积, B10原料价, B26基础工资)
# B15(产品种类)固定为7

PYTHON_FIXED_SCENARIOS = [
    # (label, B1, B24, B25, B13, B14, B10, B26, B15)
    ('🏭 大厂走量',      16, 8,  100, 8000,  250, 3, 1200, 7),
    ('✨ 高奢溢价',      30, 3,  500, 5000,   80, 3, 1200, 9),
    ('🏠 社区精酿',      22, 3,  200, 1500,   60, 3, 1200, 3),
    ('🛌 躺平',          16, 8,  0,   0,     150, 3, 1200, 7),
    ('🏆 大厂最优',      18, 8,  100, 8000,  300, 3, 1200, 7),
    ('💎 高奢加薪',      30, 3,  500, 5000,   80, 3, 3000, 9),
    ('⚡ 极端A(低价多人)', 5, 20, 1000, 20000, 300, 6, 4000, 9),
    ('🎯 极端B(高价单人)',40, 1,  0,   0,      30, 1, 800, 1),
    ('🚀 顶配高薪',       30, 3,  500, 5000,   80, 3, 8000, 9),
]


# ============================================================
# 单月计算 — 精确 1:1 对齐 BakerySandbox.vue 的 rc/fd/nx
# ============================================================

class State:
    """月度快照状态"""
    __slots__ = ('B1','B2','B3','B4','B5','B6','B7','B8','B9','B10',
                 'B11','B12','B13','B14','B15','B20','B21','B24','B25','B26',
                 'FAT','EMP','BRAND','TRAFFIC')
    def __init__(self):
        self.reset()
    def reset(self):
        self.B1=0; self.B2=0; self.B3=0; self.B4=2; self.B5=0
        self.B6=0; self.B7=0; self.B8=0; self.B9=0; self.B10=0
        self.B11=0; self.B12=0; self.B13=0; self.B14=0; self.B15=7
        self.B20=0; self.B21=0.8; self.B24=0; self.B25=0; self.B26=0
        self.FAT=40; self.EMP=0; self.BRAND=0; self.TRAFFIC=0


def one_month(s: State, B1:int, B24:int, B25:int, B13:int, B14:int, B10:int, B26:int, B15:int=7) -> int:
    """
    执行一个月的 rc()+fd()+nx()，返回当月利润。
    所有计算精确复现 BakerySandbox.vue。
    """
    q = type('Q', (), {'B1':B1,'B24':B24,'B25':B25,'B13':B13,'B14':B14,'B10':B10,'B26':B26,'B15':B15})()

    # === rc() — 实时计算 ======================
    
    # B9 人工成本 = 人数×基础工资×复杂度系数
    s.B9 = round(q.B24 * q.B26 * (1 + q.B15 * 0.15 * max(0, 1 - q.B24 * 0.08)))
    
    # 物理产能上限
    ph = max(1, min(q.B14 * 25, q.B24 * 600) + max(0, round((2 - s.B4) * 200)))
    
    # B3 实际产能 = 物理 × 疲劳系数
    s.B3 = max(0, round(ph * sk(s.FAT)))
    
    # B4 报废/加工成本 = 规模效应(产能越大越低) × 经验熟练度
    s.B4 = max(0.1, max(0.1, 2 - s.B3 * 0.0002) * (1 - s.EMP * 0.002))
    
    # pb 价格弹性系数 — 低于¥20有引流加成，高于¥20驱客
    pb = (1 + (20 - q.B1) * 0.15) if q.B1 < 20 else max(0.6, 1 - (q.B1 - 20) * 0.03)
    
    # 面积杠杆 — 大面积店铺=批发渠道
    area_lever = 1 + q.B14 / 100
    
    # tr 客流 = 基础客流 + 品牌客流 + 营销客流
    base_tr = round(250 * q.B15) + round(s.BRAND * 3)
    mkt_tr = round(math.sqrt(max(0, q.B13)) * 12)
    tr = round(base_tr * pb) + round(mkt_tr * area_lever)
    
    # ma 最高可接受价 — 受品牌和满意度影响
    ma = max(1, 10 + q.B15 * 1.2 + s.BRAND * 0.3 + s.B21 * 4)
    
    # B2 需求 = 客流 × 转化率 (价格合适→高转化)
    if q.B1 <= ma:
        conv = 0.5 + (ma - q.B1) / ma * 0.4
    else:
        conv = max(0.05, 0.5 * ma / q.B1)
    s.B2 = max(0, round(tr * conv))
    
    # B5 房租
    s.B5 = max(0, round(q.B14 * q.B15 * max(2, 20 - q.B14 * 0.05)))
    
    # B21 员工满意度
    #   ps (薪资满意度): 工资/产能 与 基准生活水平 对比
    #   over_penalty (超负荷惩罚): 利用率>80% 扣减满意度
    pp = s.B9 / max(s.B3, 1)
    bl = 3 + q.B15 * 0.4  # 5.8 (基准生活线)
    if pp >= bl:
        ps = 0.7 + min((pp - bl) / (bl * 2), 0.3)
    else:
        ps = pp / bl * 0.7
    s.B21 = round(min(1, max(0, ps - max(0, s.B3 / ph - (0.8 + 0.2 * ps)) * 1.5)) * 1000) / 1000
    
    # B12 原料成本 (含批量折扣 cap 50%)
    s.B12 = round(q.B10 * (1 - min(0.5, s.B3 * 0.00008)) * 100) / 100
    
    # B11 其他变动成本
    s.B11 = s.B4 + s.B3 * 0.002
    
    # B6 实际销量 = min(需求, 产能)
    s.B6 = min(s.B2, s.B3)
    
    # B7 月收入
    s.B7 = s.B6 * q.B1
    
    # B8 月利润
    s.B8 = round(s.B7 - (s.B12 + 1 + s.B4) * s.B3
                 - s.B5 - s.B9 - q.B13
                 - q.B25 * q.B24 - round(0.05 * q.B24 * 1500))
    
    s.TRAFFIC = tr
    s.B20 = round(s.B21 * 100) / 100  # 品质 = 满意度
    
    # === fd() — 疲劳累计 ======================
    
    d = 3  # 基线熵增
    if q.B25 == 0 and (s.B3 / ph) > 0.7:
        d += 5  # 不培训+高强度→爆炸
    elif q.B25 == 0:
        d += 2  # 不培训→小幅积累
    if (s.B3 / ph) > 0.8:
        d += ((s.B3 / ph) - 0.8) * 40  # 超负荷严重惩罚
    d -= q.B25 * 0.03  # 培训减免
    ff = s.FAT / 40 if s.FAT < 40 else 1  # 低疲劳时容易恢复
    if s.B21 < 0.5:
        d -= (s.B21 - 0.5) * 15 * ff  # 满意度低→疲劳加速
    if s.B9 / q.B24 > 1500:
        d -= (s.B9 / q.B24 - 1500) * 0.005 * ff  # 高薪缓解疲劳
    nf = max(0, min(100, round(s.FAT + d)))
    
    # === nx() — 下月推进 ======================
    
    profit = round(s.B8)
    
    # 经验: 边际递减 (每月+1~+10, 越老越慢)
    s.EMP = min(200, round(s.EMP + max(1, 10 - round(s.EMP * 0.05))))
    
    # 品牌: 满意度驱动增长, 缺货反噬, 天花板800
    shortage_rate = max(0, (s.B2 - s.B3) / max(1, s.B2))
    brand_growth = s.B21 * 30
    brand_decay = s.BRAND * max(0.02, s.BRAND * 0.015)
    growth_mult = max(0.1, 1 - s.BRAND / 800)
    s.BRAND = max(0, round(s.BRAND + brand_growth * growth_mult - brand_decay - shortage_rate * 10))
    
    s.FAT = nf
    
    return profit


# ============================================================
# 完整推演
# ============================================================

def simulate(label: str, B1:int, B24:int, B25:int, B13:int, B14:int, B10:int, B26:int, B15:int=7,
             months: int = 36) -> dict:
    """跑 full 推演，返回逐月利润+最终状态"""
    s = State()
    profits = []
    
    for _ in range(months):
        p = one_month(s, B1, B24, B25, B13, B14, B10, B26, B15)
        profits.append(p)
    
    return {
        'label': label,
        'params': {'B1':B1,'B24':B24,'B25':B25,'B13':B13,'B14':B14,'B10':B10,'B26':B26,'B15':B15},
        'months': months,
        'monthly_profits': profits,
        'total': sum(profits),
        'final': {
            'B2': s.B2, 'B3': s.B3, 'B4': round(s.B4, 4),
            'B5': s.B5, 'B6': s.B6, 'B7': s.B7, 'B8': s.B8,
            'B9': s.B9, 'B12': s.B12, 'B20': s.B20, 'B21': s.B21,
            'BRAND': s.BRAND, 'FAT': s.FAT, 'EMP': s.EMP,
            'TRAFFIC': s.TRAFFIC,
        },
    }


def verify_against_python(js_monthly: list, label: str, tolerance_per_month=300, tolerance_total=600):
    """在 JS 测试里调用这个来验证"""
    pass  # 这是 Python 参考定义，实际对比在 vitest 里做


def print_result(r: dict):
    """格式化输出一次推演结果"""
    label = r['label']
    p = r['params']
    print(f"\n  {label}")
    print(f"  {'─' * 55}")
    print(f"  参数: 售价¥{p['B1']}  员工{p['B24']}人  培训¥{p['B25']}  营销¥{p['B13']}  面积{p['B14']}㎡  进价¥{p['B10']}  工资¥{p['B26']}/人  地段{p['B15']}级")
    
    f = r['final']
    print(f"  最终: 品牌={f['BRAND']}  疲劳={f['FAT']}  经验={f['EMP']}  满意度={f['B21']:.3f}  品质={f['B20']}")
    
    months = r['months']
    per_month = r['monthly_profits']
    
    for y in range(months // 12):
        start = y * 12
        end = start + 12
        annual = sum(per_month[start:end])
        print(f"  第{y+1}年: ¥{annual:+,}")
    
    print(f"  {'─' * 55}")
    print(f"  {months}个月总计: ¥{r['total']:+,}  年均: ¥{round(r['total']/(months//12)):+,}")
    
    if months >= 24:
        print(f"\n  后12个月逐月利润:")
        for i in range(12, 0, -1):
            idx = months - i
            print(f"    月{idx+1}: ¥{per_month[idx]:+,}")


# ============================================================
# CLI 入口
# ============================================================

if __name__ == '__main__':
    args = sys.argv[1:]
    
    if '--json' in args:
        # JSON 模式 — 输出所有预设场景供测试用
        results = []
        for label, B1, B24, B25, B13, B14, B10, B26, B15 in PYTHON_FIXED_SCENARIOS:
            r = simulate(label, B1, B24, B25, B13, B14, B10, B26, B15)
            results.append(r)
        print(json.dumps(results, indent=2))
    
    elif '--scenario' in args:
        # 自定义场景
        idx = args.index('--scenario')
        parts = args[idx+1:idx+9]
        B1, B24, B25, B13, B14, B10, B26, B15 = map(int, parts)
        label = args[idx+9] if len(args) > idx+9 else f'自定义 ¥{B1}/{B24}人'
        months = 36
        if '--months' in args:
            mi = args.index('--months')
            months = int(args[mi+1])
        r = simulate(label, B1, B24, B25, B13, B14, B10, B26, B15, months)
        print_result(r)
    
    else:
        # 默认: 打印全部预设场景
        print("=" * 68)
        print("  面包店 V4 参考模型 — 预设场景")
        print("=" * 68)
        for label, B1, B24, B25, B13, B14, B10, B26, B15 in PYTHON_FIXED_SCENARIOS:
            r = simulate(label, B1, B24, B25, B13, B14, B10, B26, B15)
            print_result(r)
        print()
