# Checks for the Znam scripts.  About a minute.   python3 znam_check.py
import random, sys
from math import gcd
from fractions import Fraction
import znam, znam_odd
from znam_lenstra import divisors_in_class
from znam_odd import tail2

random.seed(2024)

# 1. Lenstra's algorithm against a complete divisor list.
primes = [3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107]
tot = hits = bad = 0
while tot < 8000:
    n = 1
    for _ in range(random.randrange(3, 12)): n *= random.choice(primes)
    if tot % 2: n *= random.randrange(10**6, 10**9) | 1
    ds = znam.divisors(znam.factor(n))
    c = int(round(n ** (1/3)))
    s = random.randrange(c + 2, 30*c + 3)
    if gcd(s, n) != 1: continue
    r = random.choice(ds) % s if tot % 3 else random.randrange(1, s)
    if gcd(r, s) != 1: continue
    tot += 1
    want = {d for d in ds if d % s == r}; hits += len(want)
    bad += divisors_in_class(n, r, s) != want
print(f"1. divisors in residue classes: {tot} cases, {hits} divisors to find, {bad} mismatches")
assert not bad

# 2. Tails in odd mode against stepping through y.  (y, z) is planted: P = -(y+z)^(-1) mod yz.
def brute_tail(P, a, lo):
    out = []; y = max(lo, P//a) + 1
    while y <= 2*P//a + 1:
        u = a*y - P
        if u > 0 and (P*y + 1) % u == 0:
            z = (P*y + 1)//u
            if z > y and y % 2 and z % 2: out.append((y, z))
        y += 1
    return sorted(out)
tot = hits = bad = 0
while tot < 6000:
    y = random.randrange(3, 3000) | 1; z = random.randrange(y + 2, random.choice([10**4, 10**6, 10**9])) | 1
    if gcd(y, z) != 1: continue
    P = (-pow(y + z, -1, y*z)) % (y*z) + random.randrange(0, 5)*y*z
    if P % 2 == 0: P += y*z
    a = (P*(y + z) + 1)//(y*z)
    if a < 3: continue
    lo = random.choice([1, 1, y - 2, y])
    want = brute_tail(P, a, lo); tot += 1; hits += len(want)
    for force in (None, 'lenstra'):
        bad += sorted(tail2(P, a, lo, True, force)[0]) != want
print(f"2. odd tails: {tot} planted instances, {hits} tails to find, {bad} mismatches")
assert not bad

# 3. Whole odd-mode search on a generalised equation that has odd solutions:
#    1/x_1 + ... + 1/x_m + 1/(P0 x_1...x_m) = a0/P0, with P0 planted from a chosen odd tuple.
def brute(P, a, m, lo, pre, out):
    if m == 1:
        if (P + 1) % a == 0:
            w = (P + 1)//a
            if w > lo and w % 2: out.append(tuple(pre) + (w,))
        return
    x = max(lo, P//a) + 1
    while x*a < m*P:
        if x % 2 and gcd(x, P) == 1: brute(P*x, a*x - P, m - 1, x, pre + [x], out)
        x += 1
tot = hits = bad = 0
while tot < 300:
    m = random.choice([3, 3, 3, 4])
    xs = sorted(random.sample(range(3, random.choice([30, 60]), 2), m))
    if any(gcd(xs[i], xs[j]) != 1 for i in range(m) for j in range(i)): continue
    Pi = 1
    for x in xs: Pi *= x
    S = sum(Pi//x for x in xs)
    P0 = (-pow(S, -1, Pi)) % Pi
    if P0 % 2 == 0: P0 += Pi
    if any(gcd(P0, x) != 1 for x in xs): continue
    a0 = (P0*S + 1)//Pi
    want = []; brute(P0, a0, m, 1, [], want); want.sort()
    assert tuple(xs) in want
    tot += 1; hits += len(want)
    for force in (None, 'lenstra'):
        got = []
        for j in znam_odd.jobs(m, True, force, start=([], P0, a0)): got += znam_odd.job(j)[0]
        bad += sorted(got) != want
print(f"3. odd search end to end: {tot} planted instances, {hits} solutions to find, {bad} mismatches")
assert not bad

# 4. All-integer mode, every tail forced through Lenstra, against the factoring enumerator.
if __name__ == '__main__':
    for k in (5, 6, 7):
        a = znam.solve(k); b = znam_odd.run(k, False, 'lenstra', quiet=True)[0]
        assert a == b, k
        print(f"4. k={k}: {len(a)} solutions both ways")
    print("all checks passed")
