import random, math, sys
from fermat import scan, squares
from znam import divisors
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 11)
# 1. generic quadratic test with planted squares, all wheels
bad = 0; tot = 0
for trial in range(1500):
    K = random.choice([5, 30, 200, 3000, 70000])
    A = random.randrange(1, 10**random.randrange(1, 12)) ** 2 if random.random() < .7 else random.randrange(1, 10**6)
    j0 = random.randrange(K); w0 = random.randrange(10**random.randrange(1, 20))
    B = random.randrange(-10**15, 10**15)
    C = w0 * w0 - A * j0 * j0 - B * j0          # plants a square at j0
    want = []
    for j in range(K):
        D = A*j*j + B*j + C
        if D >= 0 and math.isqrt(D)**2 == D: want.append((j, math.isqrt(D)))
    for wh in (0, 1, 2, 3, 4):
        got = sorted(squares(A, B, C, K, wh))
        if got != want: bad += 1; print("MISMATCH quad", A, B, C, K, wh)
    tot += len(want)
print("quadratic: planted/found", tot, "bad", bad)
# 2. the divisor problem
tot = 0; bad = 0
for trial in range(6000):
    P = random.randrange(2, 10**random.randrange(1, 9))
    r = random.randrange(1, max(2, min(P, 10**random.randrange(1, 6))))
    if math.gcd(P, r) != 1: continue
    N = P*P + r
    dmin = random.choice([1, 1, 2, 5, 100, 10**4])
    if N // (dmin * r * r) > 3_000_000: continue
    want = set()
    for d in divisors(N):
        e = N // d
        if d <= e and d >= dmin and (d + P) % r == 0:
            want.add(((d + P)//r, (e + P)//r))
    for wh in (None, 0, 1, 2, 3, 4):
        got = set(scan(P, r, N, dmin, wh))
        got = {(y, z) for (y, z) in got if y*r - P >= dmin}
        if got != want:
            bad += 1
            if bad < 5: print("MISMATCH", P, r, dmin, wh, sorted(got), sorted(want))
    tot += len(want)
print("divisor problem: solutions seen", tot, "bad", bad)
