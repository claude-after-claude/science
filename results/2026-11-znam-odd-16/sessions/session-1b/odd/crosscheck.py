"""Random leaves of the real odd search, solved twice: by odd.leaf (sieve / scan / rho as the
thresholds dictate) and by factoring N completely and listing every divisor.  The two
answers must agree on all pairs with y > x, y and z odd.

    python3 crosscheck.py k [seed] [leaves]
"""
import sys, random, time
from math import gcd
import odd, znam, drive

k = int(sys.argv[1]); seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
want = int(sys.argv[3]) if len(sys.argv) > 3 else 100
rng = random.Random(seed)
pre = odd.prefixes(k)
weights = [p[4] - p[3] + 1 for p in pre]
drive.PRIMES = drive.primes_upto(300_000)
n = found = 0; routes = [0] * 4; t0 = time.time()
while n < want:
    xs, P0, r0, lo, hi = rng.choices(pre, weights)[0]
    # half of the samples from the low end of the range, where the leaves are hardest
    x = rng.randrange(lo, hi + 1) if rng.random() < 0.5 else rng.randrange(lo, lo + max(1, (hi - lo) // 50))
    x |= 1
    if x <= xs[-1] or x > hi or gcd(x, P0) != 1: continue
    P = P0 * x; r = r0 * x - P0; N = P * P + r
    B = 300_000
    ps, rs = drive.compute_roots(P0, r0, B)
    hits = [p for p, rt in zip(ps, rs) if (x - rt) % p == 0]
    assert all(N % p == 0 for p in hits)
    for i in range(9): odd.STAT[i] = 0
    got = {(y, z) for y, z in odd.leaf(P0, r0, x, hits, B) if y > x and z > y and y % 2 and z % 2}
    for i in range(4): routes[i] += odd.STAT[i]
    ref = set()
    for d in znam.divisors(N):
        e = N // d
        if d <= e and (d + P) % r == 0:
            y, z = (d + P) // r, (e + P) // r
            if y > x and z > y and y % 2 and z % 2: ref.add((y, z))
    assert got == ref, (xs, x, got, ref)
    n += 1; found += len(ref)
print(f"k={k} seed={seed}: {n} leaves agree ({found} of them had a solution); "
      f"routes [direct, prime cofactor, scan, rho] = {routes}; {time.time() - t0:.0f} s")
