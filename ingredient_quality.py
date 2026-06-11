# -*- coding: utf-8 -*-
"""Verify: ingredient price -> quality, factory scale -> supplier bonus"""
import math, random
random.seed(42)

def ingredient_quality(b10, b3):
    base = min(1.0, max(0.2, b10 / 5.0))
    scale_bonus = min(0.25, max(0, (b3 - 3000) * 0.00008)) if b3 > 3000 else 0
    return round(min(1.0, base + scale_bonus), 3)

print("Ingredient Quality Matrix (B10 x B3 -> quality)")
hdr = "B3\\B10"
print("%8s %8s %8s %8s %8s %8s" % (hdr, "1(worst)", "2", "3", "4", "5(best)"))
for b3 in [500, 1500, 2500, 4000, 6000, 8000]:
    row = "%8d" % b3
    for b10 in range(1, 6):
        q = ingredient_quality(b10, b3)
        row += " %8.3f" % q
    print(row)

print()
print("Three strategy comparison:")
cases = [
    ("Community", 22, 3, 1500),
    ("Factory", 16, 2, 5000),
    ("Luxury", 32, 5, 2000),
    ("Trash", 12, 1, 800),
]
for name, b1, b10, b3 in cases:
    q = ingredient_quality(b10, b3)
    cost = round(b10 * (1 - min(0.5, b3 * 0.00008)), 2)
    print("  %s: B1=Y%d B10=Y%d B3=%d -> quality=%.3f actualCost=Y%.2f" % (name, b1, b10, b3, q, cost))
    if q >= 0.9: print("    Premium ingredients -> great taste -> brand premium")
    elif q >= 0.65: print("    Mid ingredients + supplier -> stable quality -> volume ok")
    elif q >= 0.4: print("    Basic ingredients -> mediocre taste -> price-dependent")
    else: print("    Bad ingredients -> taste falls -> brand tanks -> death spiral")
