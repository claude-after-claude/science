"""Primality certificates for integers above the range where the twelve-base Miller-Rabin
test is known to be a proof.  See NOTES for the statements being used.

    python3 prove.py infile outfile      # one integer per line in, one certificate per line out

Certificate line:   n a F1 P Q F2
  F1 = q:e,q:e,...   prime powers dividing n-1      (always contains 2)
  F2 = q:e,...       prime powers dividing n+1, or "-" (then P = Q = 0)
"""
import sys, math, random, time, lzma
from math import gcd, isqrt

PSI12 = 318665857834031151167461      # Sorenson & Webster: below this, MR to bases 2..37 is a proof
BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)

def mr12(n):
    if n < 2: return False
    for p in BASES:
        if n % p == 0: return n == p
    d, s = n - 1, 0
    while d % 2 == 0: d //= 2; s += 1
    for a in BASES:
        x = pow(a, d, n)
        if x in (1, n - 1): continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1: break
        else: return False
    return True

def jacobi(a, n):
    a %= n; t = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5): t = -t
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3: t = -t
        a %= n
    return t if n == 1 else 0

def alpha_pow(k, P, Q, n, base=(0, 1)):
    """base^k in (Z/n)[x]/(x^2 - P x + Q), as (u, v) meaning u + v x"""
    bu, bv = base
    u, v = 1, 0
    for bit in bin(k)[2:]:
        vv = v * v
        u, v = (u * u - Q * vv) % n, (2 * u * v + P * vv) % n
        if bit == '1':
            w = v * bv
            u, v = (u * bu - Q * w) % n, (u * bv + v * bu + P * w) % n
    return u, v

# ---------- finding factors of n-1 and n+1 ----------
Y = 1_000_000
def _primorial(y):
    s = bytearray([1]) * (y + 1); s[0:2] = b"\0\0"
    for i in range(2, isqrt(y) + 1):
        if s[i]: s[i*i::i] = bytearray(len(range(i*i, y + 1, i)))
    ps = [i for i in range(y + 1) if s[i]]
    while len(ps) > 1:
        ps = [ps[i] * ps[i + 1] if i + 1 < len(ps) else ps[i] for i in range(0, len(ps), 2)]
    return ps[0]
PRIMORIAL = None

def brent(n, limit):
    """a nontrivial factor of composite odd n, or None after about `limit` iterations"""
    y = random.randrange(1, n); c = random.randrange(1, n); m = 128
    g = r = q = 1; it = 0
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
        it += 2 * r
        r *= 2
        if it > limit and g == 1: return None
    if g == n:
        g = 1
        while g == 1:
            ys = (ys * ys + c) % n
            g = gcd(abs(x - ys), n)
    return g if g != n else None

def split_small(g, out):
    """g is a product of primes < Y (each < PSI12, so mr12 decides); put them in out"""
    stack = [g]
    while stack:
        m = stack.pop()
        if m == 1: continue
        if mr12(m): out.append(m); continue
        d = None
        for p in BASES:
            if m % p == 0: d = p; break
        while d is None: d = brent(m, 10**9)
        stack += [d, m // d]

def smooth_part(m):
    """({q: e}, R): m = prod q^e * R, R free of primes < Y"""
    global PRIMORIAL
    if PRIMORIAL is None: PRIMORIAL = _primorial(Y)
    fac = {}; R = m
    g = gcd(m, PRIMORIAL)
    if g > 1:
        qs = []; split_small(g, qs)
        for q in qs:
            e = 0
            while R % q == 0: R //= q; e += 1
            fac[q] = e
    return fac, R

class Side:
    def __init__(self, m):
        self.m = m
        self.fac, R = smooth_part(m)
        self.F = m // R
        self.comp = []          # composite cofactors, no known factor
        self.big = []           # probable primes >= PSI12 awaiting proof
        self.add(R)
    def add(self, R):
        if R == 1: return
        if mr12(R):
            if R < PSI12: self.take(R)
            else: self.big.append(R)
        else: self.comp.append(R)
    def take(self, q):
        e = 0; m = self.m // self.F     # count multiplicity in the unfactored part
        while m % q == 0: m //= q; e += 1
        self.fac[q] = self.fac.get(q, 0) + e
        self.F *= q ** e
    def rho_step(self, limit):
        """spend ~limit iterations on the smallest composite cofactor; True if it split"""
        self.comp.sort()
        c = self.comp[0]
        d = brent(c, limit)
        if d is None: return False
        self.comp.pop(0)
        self.add(d); self.add(c // d)
        return True

def residues(F1, F2):
    L = F1 * F2 // gcd(F1, F2)
    S = {1 % L}
    g = gcd(F1, F2)
    if 2 % g == 0:
        t = (-2 // g) * pow(F1 // g, -1, F2 // g) % (F2 // g) if F2 // g > 1 else 0
        S.add((1 + F1 * t) % L)
    return L, sorted(S)

STATS = {'direct': 0, 'recurse': 0, 'rho': 0, 'trials': 0, 'rho_its': 0}
KMAX = 100_000

def prove(n, certs):
    """append certificate lines for n (and for any large primes it leans on) to certs: {n: line}"""
    if n in certs: return
    assert n >= PSI12 and n % 2 == 1
    s1 = Side(n - 1); s2 = Side(n + 1)
    rt = isqrt(n)
    def K():
        L, S = residues(s1.F, s2.F)
        return len(S) * (rt // L + 1)
    used = 'direct'
    budget = 2000
    while K() > KMAX:
        # cheapest first: a probable-prime cofactor only needs its own certificate
        bigs = [(q, s) for s in (s1, s2) for q in s.big]
        if bigs:
            q, s = min(bigs)
            prove(q, certs); s.big.remove(q); s.take(q)
            used = 'recurse'; continue
        sides = [s for s in (s1, s2) if s.comp]
        assert sides, "nothing left to factor yet K is large"
        used = 'rho'
        s = min(sides, key=lambda s: min(s.comp))
        STATS['rho_its'] += budget
        if not s.rho_step(budget):
            # try the other side at the same budget before raising it
            others = [t for t in sides if t is not s]
            if not (others and others[0].rho_step(budget)):
                budget *= 2
    STATS[used] += 1
    # --- n-1 side ---
    m = n - 1
    for a in range(2, 2000):
        if pow(a, m, n) != 1: raise ValueError(f"{n} is composite (Fermat base {a})")
        if all(gcd(pow(a, m // q, n) - 1, n) == 1 for q in s1.fac): break
    else: raise RuntimeError("no witness a")
    f1 = ",".join(f"{q}:{e}" for q, e in sorted(s1.fac.items()))
    # can we do without the n+1 side?
    if rt // s1.F + 1 <= KMAX and rt // s1.F <= 4 * K():
        P = Q = 0; f2 = "-"; F2 = 1
    else:
        F2 = s2.F; R2 = (n + 1) // F2
        # U_((n+1)/2) is nonzero only if Q is a non-residue, so look at Q first (negative Q allowed)
        Qs = [Q for i in range(1, 400) for Q in (i + 1, -i) if jacobi(Q, n) == -1]
        for P, Q in ((P, Q) for Q in Qs for P in range(1, 60)):
            D = P * P - 4 * Q
            if jacobi(D, n) != -1 or gcd(n, 2 * Q * D) != 1: continue
            base = alpha_pow(R2, P, Q, n)
            if alpha_pow(F2, P, Q, n, base)[1] != 0: raise ValueError(f"{n} is composite (Lucas)")
            if all(gcd(alpha_pow(F2 // q, P, Q, n, base)[1], n) == 1 for q in s2.fac): break
        else: raise RuntimeError("no Lucas parameters")
        f2 = ",".join(f"{q}:{e}" for q, e in sorted(s2.fac.items()))
    L, S = residues(s1.F, F2)
    for r in S:
        start = r if r > 1 else r + L
        STATS['trials'] += len(range(start, rt + 1, L))
        if 0 in map(n.__mod__, range(start, rt + 1, L)):
            raise ValueError(f"{n} is composite (trial division)")
    certs[n] = f"{n} {a} {f1} {P} {Q} {f2}"

if __name__ == "__main__":
    import os
    inf, outf = sys.argv[1], sys.argv[2]
    t0 = time.time()
    todo = sorted({int(l) for l in (lzma.open(inf, 'rt') if inf.endswith('.xz') else open(inf)) if l.strip()})
    have = set()                      # resume: lines already in outf are kept (verify.py judges them, not us)
    if os.path.exists(outf):
        have = {int(l.split()[0]) for l in open(outf) if l.strip()}
    with open(outf, "a") as out:
        for i, n in enumerate(todo):
            if n not in have:
                new = {}
                prove(n, new)
                for q, line in sorted(new.items()):
                    if q not in have:
                        have.add(q); out.write(line + "\n")
            if (i + 1) % 20000 == 0:
                print(i + 1, "/", len(todo), round(time.time() - t0, 1), STATS, file=sys.stderr, flush=True)
    print(len(todo), "inputs,", len(have), "certificates on file,", round(time.time() - t0, 1), "s", STATS, file=sys.stderr)
