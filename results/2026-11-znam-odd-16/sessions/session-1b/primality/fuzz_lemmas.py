"""Empirical test of the two lemmas as verify.conditions implements them.
For every odd composite n below a bound, every base a, and every (P, Q) in a box, whenever
the conditions hold for some set of prime powers, every prime factor p of n must satisfy
p = 1 (mod F1), resp. p = +-1 (mod F2).  Reports how often the conditions held, so that
one can see the test had something to bite on."""
import sys
from math import isqrt
from verify import conditions

def factorize(m):
    f = {}; d = 2
    while d * d <= m:
        while m % d == 0: f[d] = f.get(d, 0) + 1; m //= d
        d += 1
    if m > 1: f[m] = f.get(m, 0) + 1
    return f

def subsets(f):
    items = sorted(f.items())
    out = [[x] for x in items]
    if len(items) > 1: out.append(items)
    # also weaker exponents
    out += [[(q, 1)] for q, e in items if e > 1]
    return out

bound = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
held1 = held2 = viol = 0
for n in range(9, bound, 2):
    pf = factorize(n)
    if len(pf) == 1 and list(pf.values()) == [1]: continue     # prime
    ps = list(pf)
    S1 = subsets(factorize(n - 1)); S2 = subsets(factorize(n + 1))
    for a in range(1, n):
        if pow(a, n - 1, n) != 1: continue
        for f1 in S1:
            r = conditions(n, a, f1, 0, 0, [], set())
            if r:
                held1 += 1
                if any((p - 1) % r[0] for p in ps): viol += 1; print("VIOLATION n-1", n, a, f1)
    for P in range(1, 10):
        for Q in range(-7, 10):
            for f2 in S2:
                r = conditions(n, 1, [], P, Q, f2, set())
                if r:
                    held2 += 1
                    if any((p - 1) % r[1] and (p + 1) % r[1] for p in ps): viol += 1; print("VIOLATION n+1", n, P, Q, f2)
print(f"composites below {bound}: n-1 conditions held {held1} times, n+1 conditions held {held2} times, violations {viol}")
