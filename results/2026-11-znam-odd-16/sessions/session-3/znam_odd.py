# Exhaustive search for solutions of   sum_{i<=k} 1/x_i + 1/prod x_i = 1,   x_1 < ... < x_k,
# either in all integers >= 2 or in odd integers only.
#
#   python3 znam_odd.py odd 12          # odd solutions with 12 terms
#   python3 znam_odd.py all 7           # all solutions with 7 terms (cross-check against znam.py)
#   python3 znam_odd.py all 7 lenstra   # same, but force every tail through the Lenstra code path
#
# State: prefix with product P and remainder a/P (gcd(a,P)=1), m terms still to choose.
#  m > 2:  the next term x satisfies
#            x > P/a      (the remainder a/P - 1/x must stay positive),
#            x < m P/a    (m distinct terms <= 1/x and the tiny product term must add up to a/P),
#            gcd(x, P) = 1 (terms of a solution are pairwise coprime),
#          and the node is dropped if reachable() shows the remainder cannot be met any more.
#  m = 2:  (a y - P)(a z - P) = P^2 + a, so we need the divisors of N = P^2 + a that are = -P (mod a).
#          Found by (i) stepping through y directly, (ii) Lenstra's divisors-in-residue-classes
#          algorithm, or (iii) full factorisation -- whichever is estimated cheapest.
#  odd case only: y, z odd forces both divisors even, so a = 3 (mod 4), and we work with N/4.
import sys, time
from math import gcd, isqrt
from fractions import Fraction
from multiprocessing import Pool
from znam import factor, divisors
from znam_lenstra import divisors_in_class

PR = [p for p in range(2, 4000) if all(p % q for q in range(2, int(p**.5)+1))]

def reachable(P, a, lo, m, odd):
    """Could a remainder a/P still be written as m unit fractions plus 1/(final product), with the
    new denominators > lo, pairwise coprime and coprime to P?  The i-th smallest new denominator is
    >= lo+i (lo+2i if odd) and >= the i-th smallest prime not dividing P (distinct smallest prime
    factors).  Returns False only when that bound, taken exactly, rules the node out."""
    step = 2 if odd else 1
    den = []; i = 0
    for q in PR:
        if P % q and not (odd and q == 2):
            i += 1
            den.append(max(q, lo + step*i))
            if i == m: break
    else: raise ValueError
    if a/P <= sum(1.0/d for d in den) * (1 - 1e-9): return True      # clearly fine (keeping is always safe)
    prod = P
    for d in den: prod *= d
    return Fraction(a, P) <= sum(Fraction(1, d) for d in den) + Fraction(1, prod)

def icbrt(n):
    x = int(round(n ** (1/3)))
    while x*x*x > n: x -= 1
    while (x+1)**3 <= n: x += 1
    return x

def tail2(P, a, lo, odd, force=None):
    """All (y, z), lo < y < z, with 1/y + 1/z + 1/(P y z) = a/P.  Returns (list, method)."""
    N = P*P + a
    res = []
    if a == 1:
        for d in divisors(factor(N)):
            if d*d < N:
                y = d + P; z = N//d + P
                if y > lo and not (odd and (y % 2 == 0 or z % 2 == 0)): res.append((y, z))
        return res, 'factor'
    if odd:
        if a % 4 != 3: return res, 'mod4'
        n = N // 4; r = (-P * pow(2, -1, a)) % a       # d/2 divides N/4, d/2 = -P/2 (mod a)
    else:
        n = N; r = (-P) % a
    step = 2 if odd else 1
    y0 = max(lo, P//a) + 1                  # a/P = 1/y + 1/z + 1/(Pyz) < 2/y, so P/a < y < 2P/a
    if odd and y0 % 2 == 0: y0 += 1
    ytop = 2*P//a + 1
    direct_cost = max(0, (ytop - y0)//step + 1)
    runs = icbrt(n)//a + 1
    if force != 'lenstra' and direct_cost <= 250*runs:
        y = y0
        while y <= ytop:
            u = a*y - P
            if u > 0 and (P*y + 1) % u == 0:
                z = (P*y + 1)//u
                if z > y and not (odd and z % 2 == 0): res.append((y, z))
            y += step
        return res, 'direct'
    # Lenstra, splitting the class mod a into classes mod a*m if a is below the cube root
    if a*a*a > n:
        ds = divisors_in_class(n, r, a)
    else:
        m = runs
        while (a*m)**3 <= n or gcd(m, n) != 1: m += 1
        ds = set(); am = a*m
        for i in range(m):
            ri = r + a*i
            if gcd(ri, m) == 1: ds |= divisors_in_class(n, ri, am)
    for d in ds:
        if odd: d *= 2
        if d*d < N:
            y = (d + P)//a; z = (N//d + P)//a
            if y > lo: res.append((y, z))
    return res, 'lenstra'

def job(args):
    """Prefix (P, a), three terms left; handle next term x in [x0, x1)."""
    pre, P, a, x0, x1, odd, force = args
    out = []; st = {}
    step = 1
    x = x0
    if odd:
        # the child numerator a x - P must be 3 (mod 4).  With x and P odd that needs a even,
        # and then a x = a (mod 4): either every child qualifies or none does.
        if (a - P) % 4 != 3: return out, {'mod4-prefix': 1}
        if x % 2 == 0: x += 1
        step = 2
    while x < x1:
        if gcd(x, P) == 1:
            P2 = P*x; a2 = a*x - P
            if reachable(P2, a2, x, 2, odd):
                res, how = tail2(P2, a2, x, odd, force)
                st[how] = st.get(how, 0) + 1
                for y, z in res: out.append(tuple(pre) + (x, y, z))
        x += step
    return out, st

def jobs(k, odd, force, chunk=4000, start=([], 1, 1)):
    step = 2 if odd else 1
    def rec(pre, P, a, m):
        lo = pre[-1] if pre else 1
        x = max(lo, P//a) + 1
        if odd and x % 2 == 0: x += 1
        if m == 3:
            top = (m*P - 1)//a + 1
            while x < top:
                yield (pre, P, a, x, min(top, x + chunk), odd, force)
                x += chunk
            return
        while x*a < m*P:
            if gcd(x, P) == 1:
                P2 = P*x; a2 = a*x - P
                if reachable(P2, a2, x, m-1, odd):
                    yield from rec(pre + [x], P2, a2, m-1)
            x += step
    yield from rec(list(start[0]), start[1], start[2], k)

def run(k, odd, force=None, procs=8, quiet=False):
    t = time.time()
    if k < 3: raise ValueError('k >= 3 only')
    js = list(jobs(k, odd, force))
    js.sort(key=lambda j: -(j[1]//j[2]))          # hardest (smallest remainder) first
    sols = []; st = {}; done = 0
    with Pool(procs) as pool:
        for out, s in pool.imap_unordered(job, js, chunksize=1):
            sols += out
            for kk, v in s.items(): st[kk] = st.get(kk, 0) + v
            done += 1
            if not quiet and done % 200 == 0:
                print(f"   {done}/{len(js)} jobs, {time.time()-t:.0f}s, {st}", file=sys.stderr, flush=True)
    sols.sort()
    for s in sols:
        Pr = 1
        for x in s: Pr *= x
        assert sum(Fraction(1, x) for x in s) + Fraction(1, Pr) == 1, s
    return sols, st, len(js), time.time() - t

if __name__ == '__main__':
    odd = sys.argv[1] == 'odd'
    k = int(sys.argv[2])
    force = sys.argv[3] if len(sys.argv) > 3 else None
    sols, st, nj, dt = run(k, odd, force)
    print(f"k={k} {'odd' if odd else 'all'}: {len(sols)} solutions; {nj} jobs; tails by method {st}; {dt:.1f}s")
    for s in sols: print("   ", s)
