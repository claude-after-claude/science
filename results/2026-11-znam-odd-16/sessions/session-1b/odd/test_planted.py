"""A search that finds nothing cannot be checked against what it found.  So: build leaf
instances (P, r) that DO have a solution in odd y < z, at about the sizes of the k = 12
search, and push each one through every route of odd.leaf_core.  The planted pair must come
back every time.

Construction: take odd r = 3 (mod 4) and odd y, factor M = r y^2 + 1, and for an even
divisor d of M put P = r y - d.  Then d | P^2 + r, and z = (1 + P y)/d completes the pair
whenever it is an odd integer > y.

    python3 test_planted.py [seed] [instances] [big]

With a third argument "big", r is taken around 10^9..10^11 and y around 10^5..10^7, so that
N reaches 10^33 and beyond, as in the real k = 12 leaves; the routes that would then take
too long (a scan from d = 1, rho on an arbitrary 30-digit cofactor) are left out.
"""
import sys, random
from math import gcd, isqrt
import odd, znam, drive

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
want_n = int(sys.argv[2]) if len(sys.argv) > 2 else 300
BIGMODE = len(sys.argv) > 3 and sys.argv[3] == "big"
rng = random.Random(seed)
SMALL = drive.primes_upto(200_000)

def plant():
    while True:
        if BIGMODE:
            r = rng.randrange(10 ** 9, 10 ** 11) * 4 + 3
            y = rng.randrange(10 ** 5, 10 ** 7) * 2 + 1
        else:
            r = rng.randrange(10 ** rng.randrange(2, 8)) * 4 + 3
            y = rng.randrange(10 ** rng.randrange(4, 9)) * 2 + 1
        M = r * y * y + 1
        ds = [d for d in znam.divisors(M) if d % 2 == 0 and d < r * y]
        rng.shuffle(ds)
        for d in ds[:4]:
            P = r * y - d
            if P < 3 or gcd(P, r) != 1 or (1 + P * y) % d: continue
            z = (1 + P * y) // d
            if z % 2 == 0 or z <= y: continue
            assert r * y * z - P * (y + z) == 1
            return P, r, y, z, d

routes = [("direct scan", dict(T1=10**40)),
          ("sieve, then prime cofactor or scan", dict(T1=0, KF=1e40)),
          ("sieve, then prime cofactor or rho", dict(T1=0, KF=0)),
          ("no sieve, scan", dict(T1=0, KF=1e40, nosieve=True)),
          ("default thresholds", dict())]
if BIGMODE:
    routes = [routes[1], routes[4]]
count = {name: [0] * 4 for name, _ in routes}
n = 0; sizes = []
while n < want_n:
    P, r, y, z, d = plant()
    N = P * P + r
    if not BIGMODE and N // (r * r) > 3 * 10 ** 9: continue          # keep each scan under a second or so
    n += 1; sizes.append((N, d))
    B = 200_000 if BIGMODE else rng.choice([1000, 20_000, 200_000])
    hits = [int(p) for p in SMALL if p < B and N % p == 0]
    for name, opt in routes:
        saved = (odd.T1, odd.KF)
        odd.T1 = opt.get("T1", saved[0]); odd.KF = opt.get("KF", saved[1])
        for i in range(9): odd.STAT[i] = 0
        if opt.get("nosieve"): got = odd.leaf_core(P, r, 1, None, 1)
        else: got = odd.leaf_core(P, r, 1, hits, B)
        odd.T1, odd.KF = saved
        assert (y, z) in got, (name, P, r, y, z, d)
        for (a, b) in got: assert r * a * b - P * (a + b) == 1
        for i in range(4): count[name][i] += odd.STAT[i]
print(f"{n} planted leaves, N from {min(s[0] for s in sizes):.1e} to {max(s[0] for s in sizes):.1e}, "
      f"planted divisor d from {min(s[1] for s in sizes)} to {max(s[1] for s in sizes):.1e}")
print("every route returned the planted pair.  leaves by exit [direct, prime cofactor, scan, rho]:")
for name, _ in routes: print(f"   {name:38s} {count[name]}")
