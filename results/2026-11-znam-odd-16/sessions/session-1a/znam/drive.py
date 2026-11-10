"""Enumerate all solutions of  sum 1/x_i + 1/prod x_i = 1  with k terms, x_1 < ... < x_k.
Prefix DFS for the first k-3 terms; for the last three (x,y,z):
  for each x:  (r y - P)(r z - P) = P^2 + r  with P = P0 x, r = r0 x - P0,
  solved either by a square-discriminant scan over y+z (fermat.scan) or by factoring.
A quadratic-polynomial sieve over x strips the small primes of N(x) = P0^2 x^2 + r0 x - P0."""
import sys, math, time, os
from time import perf_counter
from array import array
from math import isqrt, gcd
from multiprocessing import Pool
from znam import is_prime, factor
from fermat import scan

T1 = int(os.environ.get('T1', 50_000))          # direct-scan threshold (candidates)
SIEVE_MIN = int(os.environ.get('SIEVE_MIN', 100))   # sieve only prefixes whose hard region has at least this many x
KF = float(os.environ.get('KF', 2500))
BMIN = int(os.environ.get('BMIN', 100_000))
BMAX = int(os.environ.get("BMAX", 30_000_000))
CHUNK = int(os.environ.get("CHUNK", 40_000))

def primes_upto(n):
    s = bytearray([1]) * (n + 1); s[0:2] = b"\0\0"
    for i in range(2, isqrt(n) + 1):
        if s[i]: s[i*i::i] = bytearray(len(range(i*i, n + 1, i)))
    from itertools import compress
    return array('I', compress(range(n + 1), s))

def sqrt_mod(a, p):
    """sqrt of a mod odd prime p, or None"""
    if a == 0: return 0
    if pow(a, (p - 1) >> 1, p) != 1: return None
    if p & 3 == 3: return pow(a, (p + 1) >> 2, p)
    q, s = p - 1, 0
    while not q & 1: q >>= 1; s += 1
    z = 2
    while pow(z, (p - 1) >> 1, p) != p - 1: z += 1
    m, c, t, R = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) >> 1, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1: t2 = t2 * t2 % p; i += 1
        b = pow(c, 1 << (m - i - 1), p)
        m, c = i, b * b % p
        t, R = t * c % p, R * b % p
    return R

PRIMES = None
ROOTS = {}   # (P0, r0) -> (B, array p, array root)

def compute_roots(P0, r0, B):
    ps = array('I'); rs = array('I')
    disc = r0 * r0 + 4 * P0 ** 3
    twoA = 2 * P0 * P0
    for p in PRIMES:
        if p >= B: break
        if P0 % p == 0: continue
        if p == 2:
            for x in (0, 1):
                if (P0 * P0 * x * x + r0 * x - P0) % 2 == 0: ps.append(2); rs.append(x)
            continue
        s = sqrt_mod(disc % p, p)
        if s is None: continue
        inv = pow(twoA, -1, p)
        r1 = (s - r0) * inv % p
        ps.append(p); rs.append(r1)
        if s:
            ps.append(p); rs.append((-s - r0) * inv % p)
    return ps, rs

def divisor_pairs(fac, N, P, r, dlow):
    ds = [1]
    for p, e in fac.items():
        ds = [d * p ** i for d in ds for i in range(e + 1)]
    out = []
    for d in ds:
        e = N // d
        if d <= e and d >= dlow and (d + P) % r == 0:
            out.append(((d + P) // r, (e + P) // r))
    return out

STAT = None
def leaf(P0, r0, x, hits, B):
    """all (y,z) with x<y<z completing the solution"""
    P = P0 * x; r = r0 * x - P0; N = P * P + r
    dlow = (x + 1) * r - P
    if dlow < 1: dlow = 1
    rr = r * r
    if N // (dlow * rr) <= T1:
        STAT[0] += 1
        return scan(P, r, N, dlow)
    fac = {}; C = N
    if hits:
        for p in hits:
            while C % p == 0:
                C //= p; fac[p] = fac.get(p, 0) + 1
    if C > 1 and is_prime(C):
        fac[C] = 1; C = 1
    if C == 1:
        STAT[1] += 1
        return divisor_pairs(fac, N, P, r, dlow)
    dmin = max(dlow, B)
    K = N // (dmin * rr)
    if K < KF * C ** 0.25:
        STAT[2] += 1; STAT[4] += K
        t = perf_counter()
        out = scan(P, r, N, dmin)
        STAT[5] += perf_counter() - t
        # divisors of the form s1 or s1*C (s1 | smooth part)
        ds = [1]
        for p, e in fac.items():
            ds = [d * p ** i for d in ds for i in range(e + 1)]
        for d in ds:
            e = N // d
            if d > e: d, e = e, d
            if d >= dlow and (d + P) % r == 0:
                out.append(((d + P) // r, (e + P) // r))
        return out
    STAT[3] += 1
    t = perf_counter()
    factor(C, fac)
    STAT[6] += perf_counter() - t
    return divisor_pairs(fac, N, P, r, dlow)

def run_task(task):
    global STAT
    STAT = [0, 0, 0, 0, 0, 0.0, 0.0, 0.0]
    xs, P0, r0, xa, xb, key = task
    t0 = time.time()
    L = xb - xa + 1
    hits = None; B = 1
    if key is not None:
        B, ps, rs = ROOTS[key]
        hits = [None] * L
        for p, rt in zip(ps, rs):
            i = (rt - xa) % p
            while i < L:
                h = hits[i]
                if h is None: hits[i] = [p]
                else: h.append(p)
                i += p
        STAT[7] = time.time() - t0
    sols = []
    last = xs[-1]
    for x in range(max(xa, last + 1), xb + 1):
        if gcd(x, P0) != 1: continue
        for (y, z) in set(leaf(P0, r0, x, hits[x - xa] if hits else None, B)):
            if y > x and z > y:
                sols.append(xs + [x, y, z])
    return task[:5], sols, STAT, time.time() - t0

def hard_end(P0, r0, lo, hi):
    """smallest x in [lo,hi+1] from which the direct scan is always cheap (K <= T1)"""
    def cheap(x):
        P = P0 * x; r = r0 * x - P0; N = P * P + r
        dlow = (x + 1) * r - P
        return dlow >= 1 and N // (dlow * r * r) <= T1
    a, b = lo, hi + 1          # invariant: answer in [a,b]; cheap is monotone (False..True)
    while a < b:
        m = (a + b) // 2
        if cheap(m): b = m
        else: a = m + 1
    return a

def prefixes(k):
    out = []
    def rec(xs, P, r, m):
        lo = max(xs[-1] + 1 if xs else 2, P // r + 1)
        if m == 3:
            hi = (3 * P) // r + 1
            if lo <= hi: out.append((xs, P, r, lo, hi))
            return
        hi = ((m + 1) * P) // r
        for x in range(lo, hi + 1):
            if gcd(x, P) != 1: continue
            rec(xs + [x], P * x, r * x - P, m - 1)
    rec([], 1, 1, k)
    return out

def main():
    global PRIMES
    k = int(sys.argv[1])
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    logf = open(f"k{k}.log", "w")
    def log(*a):
        print(*a, file=logf, flush=True)
    t0 = time.time()
    pre = prefixes(k)
    log("prefixes", len(pre), "total x", sum(p[4] - p[3] + 1 for p in pre))
    PRIMES = primes_upto(BMAX)
    tasks = []
    for xs, P0, r0, lo, hi in pre:
        he = hard_end(P0, r0, lo, hi)           # hard region [lo, he)
        R = he - lo
        key = None
        if R >= SIEVE_MIN:
            B = min(BMAX, max(BMIN, 10 * R))
            ps, rs = compute_roots(P0, r0, B)
            key = (P0, r0)
            ROOTS[key] = (B, ps, rs)
            log("sieve", xs, "R", R, "B", B, "roots", len(ps), "t", round(time.time() - t0, 1))
        # hard region in chunks (smaller chunks at the low end, where factoring is needed)
        a = lo
        while a < he:
            step = CHUNK // 8 if (key and a - lo < R // 30) else CHUNK
            b = min(he - 1, a + step - 1)
            tasks.append((xs, P0, r0, a, b, key))
            a = b + 1
        a = he
        while a <= hi:
            b = min(hi, a + 10 * CHUNK - 1)
            tasks.append((xs, P0, r0, a, b, None))
            a = b + 1
    log("tasks", len(tasks), "setup time", round(time.time() - t0, 1))
    # big/slow tasks first
    tasks.sort(key=lambda t: -(t[1] * (t[4] - t[3] + 1)) * (10 if t[5] else 1))
    sols = []; done = 0; tot = [0] * 8
    with Pool(nproc) as pool:
        for t, s, st, dt in pool.imap_unordered(run_task, tasks, chunksize=1):
            done += 1
            for i in range(8): tot[i] += st[i]
            for v in s:
                log("SOL", v)
            sols += s
            if dt > 15 or done % 250 == 0 or s:
                log("done", done, "/", len(tasks), t[0], t[3], t[4], "stat", st[:5], [round(v, 1) for v in st[5:]], "dt", round(dt, 1), "elapsed", round(time.time() - t0, 1))
    # exact verification
    from fractions import Fraction
    sols = sorted(set(map(tuple, sols)))
    for s in sols:
        assert sum(Fraction(1, v) for v in s) + Fraction(1, math.prod(s)) == 1, s
        assert all(s[i] < s[i + 1] for i in range(len(s) - 1))
    proper = [s for s in sols if s[-1] != math.prod(s[:-1]) + 1]
    log("TOTAL", k, len(sols), "proper", len(proper), "stats", tot[:5], "scan/rho/sieve-pass seconds", [round(v) for v in tot[5:]], "time", round(time.time() - t0, 1))
    with open(f"k{k}.sols", "w") as f:
        for s in sols: print(*s, file=f)
    print(k, len(sols), len(proper), round(time.time() - t0, 1))

if __name__ == "__main__":
    main()
