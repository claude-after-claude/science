"""Search for solutions of   1/x_1 + ... + 1/x_k + 1/(x_1...x_k) = 1   in ODD integers.

    python3 odd.py k        # k even.  Writes odd{k}.log, .tasks (resumable), .rho, .bigprimes, .sols

Same method as ../znam/drive.py (prefix search; last three terms by sieve / square scan /
factoring), restricted to odd pairwise-coprime terms.  What is different:

  * y and z both odd  <=>  y + z even, so the square scan runs over one residue class
    mod 2r instead of mod r (scan_odd below).
  * With all terms odd, d = r y - P and e = r z - P are both even, so N = P^2 + r must be
    divisible by 4: only r = 3 (mod 4) can work.  (This holds at every leaf when 4 | k and
    at none otherwise; see NOTES.)
  * One process; each finished task is appended to odd{k}.tasks and skipped on a rerun.
  * Every integer >= PSI12 that the Miller-Rabin test calls prime is written to
    odd{k}.bigprimes, so that ../primality/prove.py can certify it afterwards.
  * The complete factorisation of N at each leaf that needed one is written to odd{k}.rho.

Environment:  ODD=0 lifts every oddness restriction (files are then called any{k}.*), for
testing against ../znam.  DEFER=1 skips the leaves that need a full factorisation and lists
them in odd{k}.hard instead - a way to count them first; such a run is NOT a complete search
and says so in its last line.  T1, KF, BMIN, BMAX, SIEVE_MIN, CHUNK as in drive.py.
"""
import sys, os, time, json
from math import gcd, isqrt
from time import perf_counter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "znam"))
import znam, drive
from fermat import squares, scan as scan_any

ODD = int(os.environ.get("ODD", 1))     # ODD=0 turns every oddness restriction off (for testing against ../znam)

def scan_odd(P, r, N, dmin):
    """All (y, z), y <= z, BOTH ODD, with r y z - P (y + z) = 1 and r y - P >= dmin.
    As fermat.scan, but y + z must be even, so the stride in sigma = y + z is 2r (r is odd)."""
    sig0 = (-pow(P, -1, r)) % r if r > 1 else 0
    if sig0 & 1: sig0 += r                     # the even representative mod 2r
    R = 2 * r
    s_lo = (2 * (P + isqrt(N))) // r
    s_hi = (dmin + N // dmin + 2 * P) // r + 1
    s_s = s_lo + ((sig0 - s_lo) % R)
    if s_s > s_hi: return []
    K = (s_hi - s_s) // R + 1
    res = []
    for j, w in squares(R * R, 2 * s_s * R - 8 * P, s_s * s_s - 4 * ((P * s_s + 1) // r), K):
        s = s_s + j * R
        res.append(((s - w) // 2, (s + w) // 2))
    return res

PSI12 = 318665857834031151167461
T1 = int(os.environ.get('T1', 50_000))
SIEVE_MIN = int(os.environ.get('SIEVE_MIN', 100))
KF = float(os.environ.get('KF', 2500))
BMIN = int(os.environ.get('BMIN', 100_000))
BMAX = int(os.environ.get("BMAX", 30_000_000))
CHUNK = int(os.environ.get("CHUNK", 20_000))
DEFER = int(os.environ.get("DEFER", 0))
scan = scan_odd if ODD else scan_any

BIG = None; HARD = None; RHO = None
def is_prime(n):
    ok = znam._is_prime(n)
    if ok and n >= PSI12 and BIG is not None: BIG.write(f"{n}\n")
    return ok
znam._is_prime = znam.is_prime
znam.is_prime = is_prime          # znam.factor looks this up at call time

def prefixes(k):
    out = []
    def rec(xs, P, r, m):
        lo = max(xs[-1] + 1 if xs else 2, P // r + 1)
        if m == 3:
            hi = (3 * P) // r + 1
            if lo <= hi: out.append((xs, P, r, lo, hi))
            return
        hi = ((m + 1) * P) // r
        for x in (range(lo | 1, hi + 1, 2) if ODD else range(lo, hi + 1)):
            if gcd(x, P) != 1: continue
            rec(xs + [x], P * x, r * x - P, m - 1)
    rec([], 1, 1, k)
    return out

STAT = [0] * 9     # direct, sieve+prime, sieve+scan, factored, scan candidates, scan s, rho s, sieve s, parity-dropped
def leaf(P0, r0, x, hits, B):
    """all (y, z) with x < y < z completing the prefix, x included (plus possibly some with y <= x)"""
    P = P0 * x; r = r0 * x - P0
    dlow = (x + 1) * r - P
    return leaf_core(P, r, dlow if dlow > 1 else 1, hits, B, (P0, r0, x))

def leaf_core(P, r, dlow, hits, B, tag=None):
    """All (y, z), y <= z, with r y z - P (y + z) = 1 and d = r y - P >= dlow.
    hits: the primes below B dividing N = P^2 + r (all of them), or None with B = 1.
    When ODD, pairs with an even member may be dropped (the scan drops them, the divisor
    listings do not); the caller filters."""
    if ODD and r & 3 != 3:
        STAT[8] += 1
        return []
    N = P * P + r
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
        return drive.divisor_pairs(fac, N, P, r, dlow)
    dmin = max(dlow, B)
    K = N // (dmin * rr)
    if K < KF * C ** 0.25:
        STAT[2] += 1; STAT[4] += K
        t = perf_counter()
        out = scan(P, r, N, dmin)
        STAT[5] += perf_counter() - t
        # the scan covers divisor pairs with both members >= B; the rest have one member
        # built from the sieved primes alone (times, possibly, the whole cofactor C)
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
    if DEFER:
        P0, r0, x = tag
        HARD.write(json.dumps({"P0": P0, "r0": r0, "x": x, "C": C, "K": K, "B": B, "fac": sorted(fac.items())}) + "\n")
        HARD.flush()
        return []
    t = perf_counter()
    znam.factor(C, fac)
    STAT[6] += perf_counter() - t
    if RHO is not None:
        RHO.write(json.dumps({"tag": tag, "N": str(N), "fac": sorted(fac.items())}) + "\n"); RHO.flush()
    return drive.divisor_pairs(fac, N, P, r, dlow)

def run_task(task):
    xs, P0, r0, xa, xb, key = task
    L = xb - xa + 1
    hits = None; B = 1
    if key is not None:
        t0 = perf_counter()
        B, ps, rs = drive.ROOTS[key]
        hits = [None] * L
        for p, rt in zip(ps, rs):
            i = (rt - xa) % p
            while i < L:
                h = hits[i]
                if h is None: hits[i] = [p]
                else: h.append(p)
                i += p
        STAT[7] += perf_counter() - t0
    sols = []
    x0 = max(xa, xs[-1] + 1)
    for x in (range(x0 | 1, xb + 1, 2) if ODD else range(x0, xb + 1)):
        if gcd(x, P0) != 1: continue
        for (y, z) in set(leaf(P0, r0, x, hits[x - xa] if hits else None, B)):
            if y > x and z > y:
                sols.append(xs + [x, y, z])        # y, z are filtered for oddness at the end
    return sols

def main():
    global BIG, HARD, RHO
    k = int(sys.argv[1]); assert k % 2 == 0 or not ODD
    stem = f"odd{k}" if ODD else f"any{k}"
    logf = open(f"{stem}.log", "a")
    def log(*a): print(*a, file=logf, flush=True)
    BIG = open(f"{stem}.bigprimes", "a", buffering=1)
    if DEFER: HARD = open(f"{stem}.hard", "a")
    else: RHO = open(f"{stem}.rho", "a")
    t0 = time.time()
    pre = prefixes(k)
    log("prefixes", len(pre), "total x", sum(p[4] - p[3] + 1 for p in pre), "t", round(time.time() - t0, 1))
    drive.PRIMES = drive.primes_upto(BMAX)
    drive.T1 = T1
    done = {}
    if os.path.exists(f"{stem}.tasks"):
        for line in open(f"{stem}.tasks"):
            rec = json.loads(line); done[tuple(rec["id"])] = rec
    out = open(f"{stem}.tasks", "a")
    allsols = []; tot = [0] * 9; ntask = 0
    for xs, P0, r0, lo, hi in sorted(pre, key=lambda p: p[4] - p[3]):      # small prefixes first
        he = drive.hard_end(P0, r0, lo, hi)
        R = he - lo
        key = None
        tasks = []
        a = lo
        while a < he:
            b = min(he - 1, a + CHUNK - 1); tasks.append((a, b, True)); a = b + 1
        a = he
        while a <= hi:
            b = min(hi, a + 10 * CHUNK - 1); tasks.append((a, b, False)); a = b + 1
        for a, b, hard in tasks:
            tid = (P0, r0, a, b)
            ntask += 1
            if tid in done:
                rec = done[tid]
            else:
                if hard and R >= SIEVE_MIN and key is None:
                    B = min(BMAX, max(BMIN, 10 * R))
                    ts = time.time()
                    ps, rs = drive.compute_roots(P0, r0, B)
                    key = (P0, r0); drive.ROOTS[key] = (B, ps, rs)
                    log("sieve", xs, "R", R, "B", B, "roots", len(ps), "setup", round(time.time() - ts, 1))
                for i in range(9): STAT[i] = 0
                ts = time.time()
                sols = run_task((xs, P0, r0, a, b, key if hard else None))
                rec = {"id": tid, "xs": xs, "sols": sols, "stat": [round(v, 2) if isinstance(v, float) else v for v in STAT], "dt": round(time.time() - ts, 2)}
                out.write(json.dumps(rec) + "\n"); out.flush()
                if rec["dt"] > 20 or sols:
                    log("task", xs, a, b, "stat", rec["stat"], "dt", rec["dt"], "sols", sols, "elapsed", round(time.time() - t0, 1))
            allsols += rec["sols"]
            for i in range(9): tot[i] += rec["stat"][i]
        drive.ROOTS.pop(key, None)
    from fractions import Fraction
    import math
    allsols = sorted(set(map(tuple, allsols)))
    for s in allsols:
        assert sum(Fraction(1, v) for v in s) + Fraction(1, math.prod(s)) == 1, s
    odd = [s for s in allsols if all(v % 2 for v in s)]
    log("TOTAL k", k, "tasks", ntask, ("solutions with x_1..x_{k-2} odd:" if ODD else "solutions:"), len(allsols), "all odd:", len(odd),
        "stats", [round(v) for v in tot], "time", round(time.time() - t0, 1))
    if DEFER and tot[3]:
        log("INCOMPLETE:", tot[3], f"leaves were deferred to {stem}.hard and not searched")
        print("INCOMPLETE:", tot[3], "leaves deferred")
    with open(f"{stem}.sols", "w") as f:
        for s in allsols: print(*s, file=f)
    if ODD: print("k", k, "all-odd solutions:", len(odd), " (solutions with only the first k-2 odd:", len(allsols), ")")
    else: print("k", k, "solutions:", len(allsols))

if __name__ == "__main__":
    main()
