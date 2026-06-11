#!/usr/bin/env python3
"""Fix default slider values to neutral starting point"""
with open('src/components/BakerySandbox.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for tabs
has_tab = '\t' in content
print(f"File has tabs: {has_tab}")

# Fix sl defaults - need to match exactly
old = "mn:5, mx:40, v:16 }, { k:'B24', l:'员工', mn:1, mx:20, v:8 }"
new = "mn:5, mx:40, v:18 }, { k:'B24', l:'员工', mn:1, mx:20, v:3 }"
if old in content:
    content = content.replace(old, new)
    print("Fixed B1(16->18) and B24(8->3)")
else:
    print("sl B1/B24 not found")

old2 = "st:50, v:100 }, { k:'B13', l:'营销 ¥', mn:0, mx:20000, st:500, v:2000 }"
new2 = "st:50, v:100 }, { k:'B13', l:'营销 ¥', mn:0, mx:20000, st:500, v:1000 }"
if old2 in content:
    content = content.replace(old2, new2)
    print("Fixed B13(2000->1000)")
else:
    print("B13 not found")

old3 = "st:0.1, v:3 }, { k:'B14', l:'面积 m²', mn:30, mx:300, st:10, v:150 }"
new3 = "st:0.1, v:3 }, { k:'B14', l:'面积 m²', mn:30, mx:300, st:10, v:60 }"
if old3 in content:
    content = content.replace(old3, new3)
    print("Fixed B14(150->60)")
else:
    print("B14 not found")

old4 = "st:200, v:5000 },\n  { k:'B15', l:'地段 ⭐', mn:1, mx:10, v:7 },"
new4 = "st:200, v:4000 },\n  { k:'B15', l:'地段 ⭐', mn:1, mx:10, v:3 },"
if old4 in content:
    content = content.replace(old4, new4)
    print("Fixed B26(5000->4000) and B15(7->3)")
else:
    print("B26/B15 not found")

# Fix defaultSl array
old5 = "const defaultSl = [16, 8, 100, 2000, 3, 150, 5000, 7]"
new5 = "const defaultSl = [18, 3, 100, 1000, 3, 60, 4000, 3]"
if old5 in content:
    content = content.replace(old5, new5)
    print("Fixed defaultSl")
else:
    print("defaultSl not found")

# Fix c (reactive initial state) - B1
old6 = "B1: 16, B2: 0, B3: 0, B4: 2, B5: 0, B6: 0, B7: 0, B8: 0,"
new6 = "B1: 18, B2: 0, B3: 0, B4: 2, B5: 0, B6: 0, B7: 0, B8: 0,"
if old6 in content:
    content = content.replace(old6, new6)
    print("Fixed c.B1(16->18)")
else:
    print("c.B1 not found")

# Fix reset() function
old7 = "sl[0].v=16;sl[1].v=8;sl[2].v=100;sl[3].v=2000;sl[4].v=3;sl[5].v=150;sl[6].v=5000;sl[7].v=7"
new7 = "sl[0].v=18;sl[1].v=3;sl[2].v=100;sl[3].v=1000;sl[4].v=3;sl[5].v=60;sl[6].v=4000;sl[7].v=3"
if old7 in content:
    content = content.replace(old7, new7)
    print("Fixed reset() slider defaults")
else:
    print("reset() defaults not found")

# Fix fingerprint thresholds - factory requires B14>=150 or score>65 to claim "factory"
old8 = "if (fpFactory.value === best) return '大厂 · 规模驱动'"
new8 = "if (fpFactory.value === best && fpFactory.value >= 50) return '大厂 · 规模驱动'\n  if (fpFactory.value === best) return '成长中 · 偏向走量'"
if old8 in content:
    content = content.replace(old8, new8)
    print("Fixed factory label threshold")
else:
    print("factory label not found")

# Fix "未成形" threshold to include mixed states
old9 = "if (best < 30) return '未成形'"
new9 = "if (best < 25) return '探索中'\n  if (best < 40) return '萌芽期'"
if old9 in content:
    content = content.replace(old9, new9)
    print("Fixed fingerprint labels")
else:
    print("fingerprint labels not found")

with open('src/components/BakerySandbox.vue', 'w', encoding='utf-8') as f:
    f.write(content)
print("\nAll done!")
