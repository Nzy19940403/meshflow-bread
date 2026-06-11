"""
生成 V3 Python 参考值，供测试用
"""
import sys
sys.path.insert(0, '.')
from ref_model_employee import simulate_year_v3

scenarios = [
    ("✨ 高奢网红店", dict(price=28, marketing=6000, area=120, grade=9,
        target_headcount=4, training_per_head=300)),
    ("🏭 薄利大厂", dict(price=16, marketing=2000, area=150, grade=7,
        target_headcount=6, training_per_head=50)),
    ("🏠 社区老店", dict(price=16, marketing=0, area=60, grade=5,
        target_headcount=3, training_per_head=0)),
]

for name, params in scenarios:
    r = simulate_year_v3(**params)
    profits = [round(m['B8_profit']) for m in r['months']]
    print(f"{name}: P={profits}")
    print(f"  年利润={r['annual_profit']:.0f}  "
          f"终期经验={r['final_experience']}  "
          f"品牌={r['final_brand']}")
