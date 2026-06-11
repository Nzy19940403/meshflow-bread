"""
对比引擎 vs Python 传播时序 — 高奢·精兵 月1

跟踪每个 SetRule/纠缠的执行顺序、输入值、输出值，
找到引擎异步 cascade 与 Python 固定迭代的分叉点。
"""
import math


# ============ 引擎传播追踪工具 ============
seq = [0]  # mutable counter for closures

def e(msg):
    seq[0] += 1
    print(f"  [#{seq[0]:>3}] {msg}")


# ============ 引擎公式（完全镜像） ============

def engine_compute_b3_effective(b21_val, b3_old, area, hc, cost):
    area_cap = int(area * 25)
    labor_cap = hc * 600
    phys = max(0, min(area_cap, labor_cap) + max(0, round((2 - cost) * 200)))
    slack = 1.0 if b21_val >= 0.6 else 0.5 + (b21_val / 0.6) * 0.5
    raw = round(phys * slack)
    new_b3 = max(0, round(b3_old * 0.6 + raw * 0.4))
    e(f"Entangle→B3: phys={phys} B21={b21_val:.3f} slack={slack:.3f} "
      f"raw={raw} old={b3_old} → B3={new_b3}")
    return new_b3


def engine_compute_b4(b3_val, c1_val):
    base = max(0.1, 2 - b3_val * 0.0002)
    r = max(0.1, base * (1 - c1_val * 0.002))
    e(f"SetRule B4: ← B3={b3_val} C1={c1_val} → B4={r:.3f}")
    return r


def engine_compute_b21(labor, eff_cap, area, hc, grade, cost):
    phys = max(0, min(int(area * 25), hc * 600) + max(0, round((2 - cost) * 200)))
    ppo = labor / max(eff_cap, 1)
    bl = 3 + grade * 0.4
    ps = 0.7 + min((ppo - bl) / (bl * 2), 0.3) if ppo >= bl else ppo / bl * 0.7
    ov = max(0, eff_cap / max(phys, 1) - 0.8) * 1.5
    r = round(min(1, max(0, ps - ov)) * 1000) / 1000
    e(f"SetRule B21: ← B9={labor} B3={eff_cap} B14={area} B24={hc} "
      f"B15={grade} B4={cost} phys={phys} ppo={ppo:.2f} ps={ps:.3f} "
      f"util={eff_cap/max(phys,1):.3f} ov={ov:.3f} → B21={r}")
    return r


# ============ 引擎初始值 ============
B1 = 28; B14 = 120; B15 = 9; B13 = 6000
B24 = 3; B25 = 500
B4 = 2.0; B3 = 1800; B21 = 0.8; B17 = 0; B19 = 0; C1 = 0
B10 = 3; B11 = 1

print("\n══════════ 引擎 notifyAll 模拟 ══════════\n")
print(f"  初始: B3={B3} B4={B4:.1f} B21={B21:.1f}")

# --- Phase 1: notifyAll triggers all SetRules + entanglement ---
e(f"SetRule B5: area={B14} grade={B15} → B5={round(B14*B15*max(2,20-B14*0.05))}")

# B2
pb = 1 + (15 - B1) * 0.2 if B1 < 15 else 1
traffic = round(150 * B15 ** 1.7) + round(math.sqrt(max(0, B13)) * 15 * pb)
max_acc = 10 + B15 * 1.5 + B19 * 0.5
ret = 0.5 + (max_acc - B1) / max_acc * 0.4 if B1 <= max_acc else max(0.05, 0.5 * (max_acc / B1))
B2 = max(0, round(traffic * ret) - round(round(traffic * ret) * B17 * 0.5))
e(f"SetRule B2: ← B1={B1} B15={B15} B13={B13} B17={B17} B19={B19} → B2={B2}")

# B9
dil = max(0, 1 - B24 * 0.08)
B9 = round(B24 * 1200 * (1 + B15 * 0.15 * dil))
e(f"SetRule B9: ← B24={B24} B15={B15} → B9={B9}")

# B4 first
B4 = engine_compute_b4(B3, C1)

# B3 entanglement x4 (all fire with initial values)
seq[0] += 1  # skip the function's seq increment for each entangle
for cause in ['B14', 'B24', 'B4', 'B21']:
    b3_new = engine_compute_b3_effective(B21, B3, B14, B24, B4)
    if b3_new != B3:
        B3 = b3_new

# B22
B22 = max(0, (B3 - 500) * 0.5)
e(f"SetRule B22: ← B3={B3} → B22={B22}")

# B21 first computation
B21 = engine_compute_b21(B9, B3, B14, B24, B15, B4)

# --- Phase 2: propagate (B21 changed → B3 entangle → B4 → B21 → ...) ---
print("\n  --- 传播收敛 (循环到稳定) ---\n")

for iteration in range(20):
    changed = False
    
    # B21→B3 entanglement
    b3_old = B3
    B3 = engine_compute_b3_effective(B21, B3, B14, B24, B4)
    if B3 != b3_old:
        changed = True
    
    # B22
    B22 = max(0, (B3 - 500) * 0.5)
    
    # B4
    b4_old = B4
    B4 = engine_compute_b4(B3, C1)
    if abs(B4 - b4_old) > 0.001:
        changed = True
    
    # B21
    b21_old = B21
    B21 = engine_compute_b21(B9, B3, B14, B24, B15, B4)
    if B21 != b21_old:
        changed = True
    
    if not changed and iteration > 0:
        e(f"--- 收敛 (迭代{iteration+1}) ---")
        break
    if iteration >= 5 and abs(B3 - b3_old) < 0.5 and abs(B21 - b21_old) < 0.001:
        e(f"--- 稳定 (迭代{iteration+1}) ---")
        break

print(f"\n  收敛结果: B3={B3} B4={B4:.3f} B21={B21:.3f}")
