"""Clean-room exhaustive search for solutions of 1/x1+...+1/xK+1/(x1...xK)=1, x1<...<xK.

    oddsearch.py K [--odd] [--procs 8]

Enumerates the first K-2 terms with rigorous bounds, then finds the last two by factoring
P^2 + N (python-flint):  (N*y - P)(N*z - P) = P^2 + N.
"""
import argparse
import itertools
import time
from fractions import Fraction
from math import gcd, prod
from multiprocessing import Pool

from flint import fmpz

PRIMES = [p for p in range(3, 6000, 2) if all(p % q for q in range(3, int(p ** 0.5) + 1, 2))]
BOUND_MAX_X = 3000


def upper_bound(P, x, m, odd):
    """Rigorous upper bound on the reciprocal sum of m pairwise coprime integers >= x coprime to P.
    Distinct terms have distinct smallest prime factors p (not dividing P); such a term is a multiple
    of p that is >= x (odd multiple if odd)."""
    cands = []
    above = 0
    for p in ([] if odd else [2]) + PRIMES:
        if P % p == 0:
            continue
        if p >= x:
            cands.append(p)
            above += 1
            if above >= m:
                break
        else:
            c = -(-x // p) * p
            if odd and c % 2 == 0:
                c += p
            cands.append(c)
    assert above >= m
    cands.sort()
    return sum(Fraction(1, c) for c in cands[:m])


def enumerate_prefixes(K, odd):
    """All (prefix, P, N) with K-2 terms such that N/P = 1 - sum(1/x) > 0 can still be completed."""
    out = []
    nodes = [0] * K
    step = 2 if odd else 1

    def rec(prefix, P, N, m):
        nodes[len(prefix)] += 1
        if m == 2:
            out.append((tuple(prefix), P, N))
            return
        lo = prefix[-1] if prefix else 1
        x = max(lo + 1, P // N + 1)
        if odd and x % 2 == 0:
            x += 1
        hi = (m * P - 1) // N  # x < m*P/N
        while x <= hi:
            if gcd(x, P) == 1:
                if x < BOUND_MAX_X and upper_bound(P, x, m, odd) + Fraction(1, P * x) < Fraction(N, P):
                    break
                N2 = N * x - P
                assert N2 > 0
                rec(prefix + [x], P * x, N2, m - 1)
            x += step

    rec([], 1, 1, K)
    return out, nodes


def divisors(fac):
    ds = [1]
    for p, e in fac:
        p = int(p)
        ds = [d * p ** i for d in ds for i in range(e + 1)]
    return ds


def last_two(task):
    prefix, P, N = task
    n = P * P + N
    sols = []
    for d in divisors(fmpz(n).factor()):
        if d * d < n and (d + P) % N == 0:
            y = (d + P) // N
            z = (n // d + P) // N
            assert (n // d + P) % N == 0
            if y > prefix[-1] and y < z:
                sols.append(prefix + (y, z))
    return sols


def is_solution(t):
    return sum(Fraction(1, x) for x in t) + Fraction(1, prod(t)) == 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("K", type=int)
    ap.add_argument("--odd", action="store_true")
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    t0 = time.time()
    tasks, nodes = enumerate_prefixes(a.K, a.odd)
    print(f"K={a.K} odd={a.odd}: nodes by prefix length {nodes[:a.K - 1]}; {len(tasks)} two-term problems; "
          f"max P^2+N ~ 10^{max(len(str(t[1] ** 2)) for t in tasks) - 1}; {time.time() - t0:.0f}s", flush=True)
    sols = []
    with Pool(a.procs) as pool:
        for i, r in enumerate(pool.imap_unordered(last_two, tasks, chunksize=200)):
            sols.extend(r)
            if i % 50000 == 0 and i:
                print(f"  {i}/{len(tasks)} factored, {time.time() - t0:.0f}s", flush=True)
    assert all(is_solution(s) for s in sols) and len(set(sols)) == len(sols)
    if a.odd:
        sols = [s for s in sols if all(v % 2 for v in s)]
    print(f"K={a.K} odd={a.odd}: {len(sols)} solutions; {time.time() - t0:.0f}s")
    for s in sorted(sols)[:30]:
        print("  ", *s)
