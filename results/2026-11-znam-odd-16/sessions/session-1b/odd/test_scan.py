"""odd.scan against brute force over divisors, on random small instances with r odd."""
import random, sys
from math import gcd, isqrt
import odd
rng = random.Random(5)
n = hit = 0
for trial in range(4000):
    P = rng.randrange(3, 4000) | 1
    r = rng.randrange(1, 300) | 1
    if gcd(P, r) != 1: continue
    N = P * P + r
    dmin = rng.choice([1, 1, 2, 7, 50, 400])
    want = set()
    for d in range(max(1, dmin), isqrt(N) + 1):
        if N % d == 0 and (d + P) % r == 0:
            y, z = (d + P) // r, (N // d + P) // r
            if y % 2 and z % 2: want.add((y, z))
    got = set(odd.scan_odd(P, r, N, dmin))
    # the scan may also return pairs with d slightly below dmin (its sigma bound is rounded up); it must not miss any
    assert want <= got, (P, r, dmin, want, got)
    for y, z in got:
        assert r * y * z - P * (y + z) == 1 and y % 2 and z % 2 and y <= z
    n += 1; hit += len(want)
print("instances", n, "pairs found", hit, "ok")
