"""Try to get verify.check to accept a composite.  It must never do so.
Also confirm that it accepts honest certificates for small primes (so the test is not vacuous)."""
import random, sys, itertools
from math import gcd, isqrt
from verify import check

def factorize(m):
    f = {}; d = 2
    while d * d <= m:
        while m % d == 0: f[d] = f.get(d, 0) + 1; m //= d
        d += 1
    if m > 1: f[m] = f.get(m, 0) + 1
    return f

def is_prime_td(n):
    return n > 1 and all(n % d for d in range(2, isqrt(n) + 1))

def attempts(n, rng, tries):
    """generate plausible certificates for n"""
    f1 = sorted(factorize(n - 1).items()); f2 = sorted(factorize(n + 1).items())
    for _ in range(tries):
        a = rng.randrange(2, n)
        s1 = [x for x in f1 if rng.random() < 0.7]
        s2 = [x for x in f2 if rng.random() < 0.7]
        if rng.random() < 0.3: s2 = []
        P = rng.randrange(1, 12); Q = rng.randrange(-8, 12)
        yield a, s1, P, Q, s2

rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
acc_comp = 0; acc_prime = 0; n_comp = 0; n_prime = 0
# 1. every odd n below 3000, heavy
# 2. special composites: Carmichael numbers, p(2p-1), (p)(p+2), squares, strong pseudoprimes to base 2
special = [561, 1105, 1729, 2465, 2821, 6601, 8911, 10585, 15841, 29341, 41041, 46657, 52633, 62745, 63973, 75361,
           2047, 3277, 4033, 4681, 8321, 15841, 29341, 42799, 49141, 52633, 65281, 74665, 80581, 85489, 88357, 90751,
           323, 377, 1159, 1829, 3827, 5459, 5777, 9071, 9179, 10877, 11419, 11663, 13919, 14839, 16109, 16211, 18407]
for p in range(3, 400, 2):
    if is_prime_td(p):
        if is_prime_td(2 * p - 1): special.append(p * (2 * p - 1))
        if is_prime_td(p + 2): special.append(p * (p + 2))
        special.append(p * p)
todo = [(n, 300) for n in range(3, 3000, 2)] + [(n, 2000) for n in special] + \
       [(rng.randrange(3001, 10**7) | 1, 100) for _ in range(4000)]
for n, tries in todo:
    pr = is_prime_td(n)
    ok = any(check(n, a, s1, P, Q, s2, set()) for a, s1, P, Q, s2 in attempts(n, rng, tries))
    if pr: n_prime += 1; acc_prime += ok
    else:
        n_comp += 1
        if ok: acc_comp += 1; print("ACCEPTED COMPOSITE", n)
print(f"composites tried {n_comp}, accepted {acc_comp};  primes tried {n_prime}, some certificate accepted for {acc_prime}")
