import sys, math, random
from fractions import Fraction

def is_prime(n):
    if n < 2: return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n % p == 0: return n == p
    d, s = n-1, 0
    while d % 2 == 0: d//=2; s+=1
    for a in (2,3,5,7,11,13,17,19,23,29,31,37):
        x = pow(a,d,n)
        if x in (1,n-1): continue
        for _ in range(s-1):
            x = x*x % n
            if x == n-1: break
        else: return False
    return True

def rho(n):
    if n % 2 == 0: return 2
    while True:
        c = random.randrange(1,n); y = x = random.randrange(n); d = 1
        f = lambda v: (v*v+c) % n
        while d == 1:
            # brent-ish batching
            q = 1
            for _ in range(64):
                x = f(x); y = f(f(y)); q = q*abs(x-y) % n
            d = math.gcd(q,n)
        if d != n: return d
        # fallback slow
        x = y = random.randrange(n); d = 1
        while d == 1:
            x = f(x); y = f(f(y)); d = math.gcd(abs(x-y), n)
        if d != n: return d

def brent(n):
    if n % 2 == 0: return 2
    gcd = math.gcd
    while True:
        y = random.randrange(1, n); c = random.randrange(1, n); m = 256
        g = r = q = 1
        while g == 1:
            x = y
            for _ in range(r): y = (y * y + c) % n
            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(m, r - k)):
                    y = (y * y + c) % n
                    q = q * abs(x - y) % n
                g = gcd(q, n); k += m
            r *= 2
        if g == n:
            g = 1
            while g == 1:
                ys = (ys * ys + c) % n
                g = gcd(abs(x - ys), n)
        if g != n: return g

def factor(n, out=None):
    if out is None: out = {}
    for p in (2,3,5,7,11,13,17,19,23,29,31,37,41,43,47):
        while n % p == 0:
            out[p] = out.get(p,0)+1; n//=p
    stack = [n] if n > 1 else []
    while stack:
        m = stack.pop()
        if m == 1: continue
        if is_prime(m): out[m] = out.get(m,0)+1; continue
        d = brent(m); stack += [d, m//d]
    return out

def divisors(n):
    ds = [1]
    for p,e in factor(n).items():
        ds = [d*p**i for d in ds for i in range(e+1)]
    return ds

def solve(k):
    """all increasing solutions of sum 1/x_i + 1/prod x_i = 1 with k terms"""
    sols = []
    def rec(xs, P, r, m):
        # r/P = 1 - sum 1/x ; m terms remaining
        if m == 2:
            N = P*P + r
            for d in divisors(N):
                e = N // d
                if d > e: continue
                if (d + P) % r or (e + P) % r: continue
                x, y = (d+P)//r, (e+P)//r
                if x > xs[-1] and y > x:
                    sols.append(xs + [x, y])
            return
        lo = max(xs[-1] + 1 if xs else 2, P // r + 1)
        hi = ((m+1) * P) // r
        for x in range(lo, hi+1):
            if math.gcd(x, P) != 1: continue
            # new remainder: r/P - 1/x = (r x - P)/(P x)
            rec(xs + [x], P*x, r*x - P, m-1)
    rec([], 1, 1, k)
    return sols

if __name__ == "__main__":
    k = int(sys.argv[1])
    sols = solve(k)
    proper = [s for s in sols if s[-1] != math.prod(s[:-1]) + 1]
    print(k, len(sols), len(proper))
    for s in sols:
        tag = "" if s in proper else "  (improper)"
        odd = "  ALL ODD" if all(v % 2 for v in s) else ""
        print(s, tag, odd)
