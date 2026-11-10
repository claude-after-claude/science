"""Check primality certificates written by prove.py.  Shares no code with it.

    python3 verify.py certfile [listfile]         (either may be .xz)

Each line  "n a F1 P Q F2"  is accepted only if every step below passes; see NOTES
for why passing them means n is prime.  If listfile is given, also check that every integer
in it has an accepted certificate.  Exit status 0 only if everything passed.
"""
import sys, lzma
from math import gcd, isqrt

def read_lines(path):
    """plain text, or xz-compressed if the name ends in .xz"""
    return lzma.open(path, "rt") if path.endswith(".xz") else open(path)

LIMIT = 318665857834031151167461     # below this the 12-base test is taken as a proof (Sorenson-Webster 2015)

def small_prime(q):
    """q < LIMIT only.  Strong probable-prime test to the first twelve prime bases."""
    assert q < LIMIT
    if q < 41: return q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if q % a == 0: return False
    t = q - 1; s = 0
    while t % 2 == 0: t //= 2; s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, t, q)
        if x == 1: continue
        ok = False
        for _ in range(s):
            if x == q - 1: ok = True; break
            x = x * x % q
        if not ok: return False
    return True

def ring_mul(A, B, P, Q, n):
    # (a0 + a1 x)(b0 + b1 x)  with  x^2 = P x - Q
    a0, a1 = A; b0, b1 = B
    hi = a1 * b1
    return ((a0 * b0 - Q * hi) % n, (a0 * b1 + a1 * b0 + P * hi) % n)

def ring_pow(X, k, P, Q, n):
    R = (1, 0)
    while k:
        if k & 1: R = ring_mul(R, X, P, Q, n)
        X = ring_mul(X, X, P, Q, n)
        k >>= 1
    return R

def parse_fac(s):
    if s == "-": return []
    out = []
    for item in s.split(","):
        q, e = item.split(":")
        out.append((int(q), int(e)))
    return out

def conditions(n, a, f1, P, Q, f2, proved):
    """Check the n-1 and n+1 conditions.  Returns (F1, F2) if they hold, else None.
    When they hold, every prime factor of n is 1 mod F1 and (all with one sign each) +-1 mod F2."""
    if n < 3 or n % 2 == 0: return None
    def prime_ok(q):
        return small_prime(q) if q < LIMIT else q in proved
    # --- n - 1 ---
    F1 = 1
    if pow(a, n - 1, n) != 1: return None
    seen = set()
    for q, e in f1:
        if e < 1 or q in seen or not prime_ok(q): return None
        seen.add(q)
        if (n - 1) % q ** e: return None
        if gcd(pow(a, (n - 1) // q, n) - 1, n) != 1: return None
        F1 *= q ** e
    # --- n + 1 ---
    F2 = 1
    if f2:
        D = P * P - 4 * Q
        if gcd(n, 2 * Q * D) != 1: return None
        if ring_pow((0, 1), n + 1, P, Q, n)[1] != 0: return None
        seen = set()
        for q, e in f2:
            if e < 1 or q in seen or not prime_ok(q): return None
            seen.add(q)
            if (n + 1) % q ** e: return None
            if gcd(ring_pow((0, 1), (n + 1) // q, P, Q, n)[1], n) != 1: return None
            F2 *= q ** e
    return F1, F2

def check(n, a, f1, P, Q, f2, proved):
    """True iff the certificate proves n prime, given `proved` = set of large primes already certified"""
    FF = conditions(n, a, f1, P, Q, f2, proved)
    if FF is None: return False
    F1, F2 = FF
    # --- every prime factor p of n is 1 mod F1 and +-1 mod F2; rule out all such p <= sqrt(n) ---
    L = F1 * F2 // gcd(F1, F2)
    classes = {1 % L}
    # the class that is 1 mod F1 and -1 mod F2, if there is one
    g = gcd(F1, F2)
    if (-2) % g == 0:
        # 1 + F1 t = -1 (mod F2)
        step = F2 // g
        t = ((-2) // g) * pow(F1 // g, -1, step) % step if step > 1 else 0
        c = (1 + F1 * t) % L
        assert (c - 1) % F1 == 0 and (c + 1) % F2 == 0
        classes.add(c)
    root = isqrt(n)
    if len(classes) * (root // L + 1) > 5_000_000: return False      # refuse absurdly long checks
    for c in classes:
        d = c
        while d <= root:
            if d > 1 and n % d == 0: return False
            d += L
    return True

def main():
    certs = {}
    for line in read_lines(sys.argv[1]):
        w = line.split()
        if not w: continue
        n = int(w[0])
        certs[n] = (int(w[1]), parse_fac(w[2]), int(w[3]), int(w[4]), parse_fac(w[5]))
    proved = set(); bad = 0
    for n in sorted(certs):                 # a certificate may only lean on smaller primes
        a, f1, P, Q, f2 = certs[n]
        if check(n, a, f1, P, Q, f2, proved): proved.add(n)
        else: bad += 1; print("REJECTED", n)
    print(len(certs), "certificates,", len(proved), "accepted,", bad, "rejected")
    missing = 0
    if len(sys.argv) > 2:
        want = {int(l) for l in read_lines(sys.argv[2]) if l.strip()}
        missing = len(want - proved)
        print(len(want), "integers listed,", missing, "without an accepted certificate")
    sys.exit(1 if bad or missing else 0)

if __name__ == "__main__":
    main()
