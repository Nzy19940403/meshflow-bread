print("FAT   step   smooth   diff")
for fat in range(70, 101):
    s = 1.0 if fat < 80 else (0.30 if fat < 90 else 0.10)
    if fat < 80:
        m = 1.0
    elif fat >= 100:
        m = 0.10
    else:
        t = (fat - 80) / 20
        sm = t * t * (3 - 2 * t)
        m = 1.0 - sm * 0.9
    print(f" {fat}%   {s:.2f}    {m:.2f}    {abs(s-m):.2f}")
