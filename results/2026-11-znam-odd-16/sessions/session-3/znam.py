# Znam's problem: x_1 < ... < x_k, each x_i divides (product of the others) + 1.
# For small k this is the same as  sum 1/x_i + 1/prod x_i = 1.
# "Proper" solutions additionally have x_k != (product of the others) + 1.
import sys, time
from math import gcd, isqrt
from fractions import Fraction
import random

SMALL = [2,3,5,7,11,13,17,19,23,29,31,37]
def is_prime(n):
    if n < 2: return False
    for p in SMALL:
        if n % p == 0: return n == p
    d = n-1; s = 0
    while d % 2 == 0: d//=2; s+=1
    for a in SMALL:            # deterministic below 3.3e24, strong probable-prime beyond
        x = pow(a, d, n)
        if x in (1, n-1): continue
        for _ in range(s-1):
            x = x*x % n
            if x == n-1: break
        else: return False
    return True

def rho(n):
    if n % 2 == 0: return 2
    while True:
        c = random.randrange(1, n); y = random.randrange(n); m = 128
        g = r = q = 1
        while g == 1:
            x = y
            for _ in range(r): y = (y*y + c) % n
            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(m, r-k)):
                    y = (y*y + c) % n
                    q = q*abs(x-y) % n
                g = gcd(q, n); k += m
            r *= 2
        if g == n:
            g = 1
            while g == 1:
                ys = (ys*ys + c) % n
                g = gcd(abs(x-ys), n)
        if g != n: return g

def factor(n, out=None):
    if out is None: out = {}
    for p in range(2, 2000):
        if p*p > n: break
        while n % p == 0:
            out[p] = out.get(p,0)+1; n //= p
    stack = [n] if n > 1 else []
    while stack:
        m = stack.pop()
        if m == 1: continue
        if is_prime(m): out[m] = out.get(m,0)+1; continue
        d = rho(m); stack += [d, m//d]
    return out

def divisors(f):
    ds = [1]
    for p, e in f.items():
        ds = [d*p**i for d in ds for i in range(e+1)]
    return ds

def tail2(P, a, lo):
    """All y<z, y>lo, with 1/y + 1/z + 1/(P y z) = a/P.   (ay-P)(az-P) = P^2 + a."""
    N = P*P + a
    res = []
    for d in divisors(factor(N)):
        if d*d < N and (d + P) % a == 0:
            y = (d+P)//a; z = (N//d + P)//a
            if y > lo: res.append((y, z))
    return res

def solve(k, first=None, stats=None):
    """All increasing x with sum 1/x_i + 1/prod = 1 (improper solutions included)."""
    sols = []
    def rec(pre, P, a, m):
        # remainder is a/P, m terms still to choose
        lo = pre[-1] if pre else 1
        if m == 2:
            if stats is not None: stats['tails'] = stats.get('tails',0)+1
            for y, z in tail2(P, a, lo):
                sols.append(tuple(pre) + (y, z))
            return
        x = max(lo, P//a) + 1            # 1/x < a/P
        while x*a < m*P:                 # a/P < m/x
            if gcd(x, P) == 1:
                rec(pre+[x], P*x, a*x - P, m-1)
            x += 1
    if k == 1: return [(2,)]            # 1/2 + 1/2 = 1
    if first: 
        P = 1; a = 1
        for x in first: a = a*x - P; P *= x
        rec(list(first), P, a, k-len(first))
    else:
        rec([], 1, 1, k)
    return sorted(sols)

def check(sol):
    P = 1
    for x in sol: P *= x
    assert all((P//x + 1) % x == 0 for x in sol)
    assert sum(Fraction(1,x) for x in sol) + Fraction(1,P) == 1
    return sol[-1] != P//sol[-1] + 1     # proper?

if __name__ == '__main__':
    K = int(sys.argv[1])
    for k in range(2, K+1):
        t = time.time(); st = {}
        sols = solve(k, stats=st)
        proper = [s for s in sols if check(s)]
        print(f"k={k}: {len(sols)} solutions of the fraction equation, {len(proper)} proper; "
              f"{st.get('tails',0)} tails factored, {time.time()-t:.1f}s")
        if '-v' in sys.argv:
            for s in sols: print('   ', '' if check(s) else '*', s)
