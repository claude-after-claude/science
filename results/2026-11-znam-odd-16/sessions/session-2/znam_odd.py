#!/usr/bin/env python3
"""
Is there a solution of Znam's problem using only odd numbers?   (Open; see ../linden/znam.)

    python3 znam_odd.py K          search for all-odd solutions with K terms
    python3 znam_odd.py test       self-checks, a few seconds (see the bottom of this file)
    python3 znam_odd.py test8      the same plus one slow check (the full K=8 search, about an hour)

Searched, as in znam.py, in the "improper" form  1/x_1 + ... + 1/x_K + 1/(x_1...x_K) = 1,
which includes every proper solution.

Two facts do most of the work:

 * Parity.  Multiply through by Q = x_1...x_K:  sum of Q/x_i, plus 1, equals Q.  With everything odd
   that is K odd numbers plus 1 making an odd number, so K is even.

 * Crowding.  The terms are pairwise coprime, so at most one of them is divisible by 3, at most one
   by 5, and so on.  That caps how fast odd reciprocals can add up, and the cap is tight:
   1/3 + 1/5 + 1/7 + 1/11 + 1/13 + 1/17 + 1/19 + 1/23 = 0.99896 < 1, so eight terms can never do it,
   and with ten or twelve terms nearly every choice is forced.  `bound` below is that cap.

Once three terms remain the first is looped over and the last two, y < z, are found without factoring:
with remainder u/P to fill, d = u*y - P must divide P^2 + u.  The first T candidates for y are tested
directly; beyond them S = y + z is confined to a short window and known mod 2u, and S^2 - 4yz must be
a square.  (If no affordable T exists the number goes to coreutils `factor` instead; that is rare.)
"""
import sys, time, random
from math import gcd, isqrt
import znam

ODD = True                      # False = allow even terms too; only used to test this code against znam.py
SMALL = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
SMALLPROD = 1
for q in SMALL: SMALLPROD *= q
TMAX = 1 << 21

def bound(P, x, m):
    """Upper bound (float) for the reciprocal sum of m pairwise coprime numbers >= x, coprime to P
    (all odd if ODD).  At most one is a multiple of each small prime q; the others have none."""
    c = []
    for q in SMALL:
        if P % q == 0 or (ODD and q == 2): continue
        r = -(-x // q) * q
        if ODD and r % 2 == 0: r += q
        c.append(r)
    step = 2 if ODD else 1
    t = x + 1 if (ODD and x % 2 == 0) else x
    n = 0; PP = P * SMALLPROD
    while n < m:
        if gcd(t, PP) == 1: c.append(t); n += 1
        t += step
    c.sort()
    return sum(1.0 / v for v in c[:m])

def last_two(P, u, lo):
    """All y < z, y > lo, with u/P = 1/y + 1/z + 1/(P y z)   (y, z odd if ODD; then P, u must be odd).
    Returns a list, or None meaning: factor P^2 + u instead."""
    n = P * P + u
    st = 2 if ODD else 1
    ymin = max(lo + 1, P // u + 1)
    if ODD and ymin % 2 == 0: ymin += 1
    smin = 2 * P // u + 1
    T = 8
    while True:
        y1 = ymin + st * T                       # first y not covered by the direct tests
        smax = y1 + (P * y1 + 1) // (u * y1 - P)  # y + z is decreasing in y while y < z
        W = (smax - smin) // (st * u) + 1 if smax >= smin else 0
        if 6 * W <= T: break                     # a window candidate costs about six direct tests
        T *= 2
        if T > TMAX: return None
    sols = []
    d0 = u * ymin - P
    for i, d in enumerate(range(d0, d0 + st * u * T, st * u)):
        if n % d == 0:
            y = ymin + st * i; z = (n // d + P) // u
            if y < z and (z % 2 or not ODD): sols.append((y, z))
    if W:
        r = (-pow(P, -1, u)) % u if u > 1 else 0
        if ODD and r % 2: r += u                 # S = y + z is even and u is odd
        first = smin + ((r - smin) % (st * u))
        for S in range(first, smax + 1, st * u):
            D = S * S - 4 * ((1 + P * S) // u)
            if D <= 0: continue
            s = isqrt(D)
            if s * s == D and (S - s) % 2 == 0:
                y, z = (S - s) // 2, (S + s) // 2
                if y >= y1 and (not ODD or (y % 2 and z % 2)): sols.append((y, z))
    return sols

def search(K, verbose=True):
    t0 = time.time(); last = [t0]
    nodes = [0] * (K + 1); count = [0]; hard = []; sols = []
    st = 2 if ODD else 1
    def rec(prefix, P, N, m):
        nodes[len(prefix)] += 1
        if verbose and time.time() - last[0] > 30:
            last[0] = time.time()
            print(f"   {last[0]-t0:.0f}s  at {prefix}  nodes by depth {nodes[:K-2]}", flush=True)
        lo = prefix[-1] if prefix else 1
        x = max(lo + 1, P // N + 1)
        if ODD and x % 2 == 0: x += 1
        hi = (m * P + 1) // N
        while x <= hi:
            if gcd(x, P) == 1:
                if m > 3 and bound(P, x, m) * (1 + 1e-9) + 1.0 / (P * x) < N / P: break
                N2 = N * x - P
                if N2 > 0:
                    if m > 3: rec(prefix + [x], P * x, N2, m - 1)
                    else:
                        count[0] += 1
                        r = last_two(P * x, N2, x)
                        if r is None: hard.append((prefix + [x], P * x, N2))
                        else: sols.extend(prefix + [x, y, z] for y, z in r)
            x += st
    rec([], 1, 1, K)
    for i in range(0, len(hard), 500):
        batch = hard[i:i + 500]
        for (pre, P2, u), fd in zip(batch, znam.factor_many([P2 * P2 + u for _, P2, u in batch])):
            sols.extend(pre + [y, z] for y, z in znam.two_by_factoring(P2, u, pre[-1], fd)
                        if not ODD or (y % 2 and z % 2))
    assert all(znam.check(s) for s in sols)
    if verbose:
        print(f"K={K}: nodes by depth {nodes[:K-2]}; {count[0]} two-term problems, "
              f"{len(hard)} of them sent to `factor`; {time.time()-t0:.0f}s")
    return sols

def selftest(slow=False):
    global ODD
    random.seed(3)
    # 1. last_two against factoring, on two-term problems with a planted all-odd solution
    planted = 0
    for trial in range(2000):
        while True:
            y = random.randrange(3, 4000) | 1; z = y + 2 * random.randrange(1, 3000)
            if gcd(y, z) == 1: break
        P = (-pow(y + z, -1, y * z)) % (y * z) + y * z * random.randrange(0, 50)
        if P % 2 == 0: P += y * z
        u = (P * (y + z) + 1) // (y * z)
        if gcd(P, u) != 1: continue
        lo = random.choice([1, y - 2, y - 1])
        got = last_two(P, u, lo)
        ref = [(a, b) for a, b in znam.two_by_factoring(P, u, lo, znam.factor_many([P * P + u])[0]) if a % 2 and b % 2]
        assert got is not None and sorted(got) == sorted(ref) and (y, z) in got
        planted += 1
    print(f"last_two: {planted} planted odd solutions recovered, agreeing with factoring")
    # 2. the whole search with even terms allowed must reproduce znam.py's counts
    ODD = False
    for K, want in ((5, 3), (6, 8), (7, 26), (8, 122)):
        if K == 8 and not slow: continue
        got = search(K, verbose=False)
        assert len(set(map(tuple, got))) == len(got) == want, (K, len(got))
        print(f"search with ODD=False, K={K}: {len(got)} solutions, as znam.py finds", flush=True)
    ODD = True

if __name__ == '__main__':
    if sys.argv[1].startswith('test'): selftest(slow=sys.argv[1] == 'test8')
    else:
        K = int(sys.argv[1])
        sols = search(K)
        print(f"K={K}: {len(sols)} all-odd solutions")
        for s in sols: print('  ', *s)
