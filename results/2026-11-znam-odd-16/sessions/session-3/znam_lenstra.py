# H. W. Lenstra, "Divisors in residue classes" (1984): all divisors d of n with d = r (mod s),
# when gcd(r,s) = gcd(n,s) = 1 and s^3 > n, in O(log n) steps.  Reconstructed from memory and
# re-derived; the test at the bottom compares it with brute force.
#
# Write d = r + s x, n/d = r' + s y (x, y >= 0).  Then  r' x + r y + s x y = (n - r r')/s, so
#   a_1 x + b_1 y = c_1 (mod s),  a_1 = r'/r, b_1 = 1, c_1 = (n - r r')/(s r)   (all mod s)
# and trivially a_0 x + b_0 y = c_0 with (a_0,b_0,c_0) = (s,0,0).  Run Euclid on (a_0,a_1) and carry
# b, c along: a_i x + b_i y = c_i (mod s) for every i, with a_i b_{i+1} - a_{i+1} b_i = (-1)^i s.
# Because x y < n/s^2 < s, for some i the integer a_i x + b_i y is pinned down to <= 2 candidates c:
#   i even:  |c| < s          i odd:  2 a_i b_i <= c <= n/s^2 + a_i b_i
# and then a_i X + b_i Y = c s + a_i r + b_i r' together with X Y = n is a quadratic.
from math import isqrt, gcd

def divisors_in_class(n, r, s):
    r %= s
    if s == 1: raise ValueError
    rinv = pow(r, -1, s)
    r1 = n * rinv % s
    found = set()
    a0, b0, c0 = s, 0, 0
    a1, b1, c1 = r1 * rinv % s, 1, ((n - r*r1)//s) * rinv % s
    ns2 = n // (s*s)

    def process(i, a, b, c):
        if i % 2 == 0:
            cands = (c, c - s) if c else (0,)
        else:
            lo = 2*a*b
            c += ((lo - c + s - 1)//s) * s          # smallest value = c (mod s) that is >= lo
            cands = []
            while c <= ns2 + a*b + 1:
                cands.append(c); c += s
        for cc in cands:
            e = cc*s + a*r + b*r1
            if a == 0:
                if b and e % b == 0:
                    Y = e // b
                    if Y > 0 and n % Y == 0 and (n//Y) % s == r: found.add(n//Y)
                continue
            disc = e*e - 4*a*b*n
            if disc < 0: continue
            sq = isqrt(disc)
            if sq*sq != disc: continue
            for T in (e + sq, e - sq):
                if T > 0 and T % (2*a) == 0:
                    X = T // (2*a)
                    if n % X == 0 and X % s == r: found.add(X)

    process(0, a0, b0, c0)
    process(1, a1, b1, c1)
    i = 1
    while a1:
        i += 1
        q, rem = divmod(a0, a1)
        if i % 2 == 1 and rem == 0:
            q -= 1; rem = a1
        a0, a1 = a1, rem
        b0, b1 = b1, b0 - q*b1
        c0, c1 = c1, (c0 - q*c1) % s
        process(i, a1, b1, c1)
    return found

def divisors_in_class_any(n, r, s):
    """Same, without the restriction s^3 > n: split the class mod s into classes mod s*m."""
    if s*s*s > n: return divisors_in_class(n, r, s)
    m = 2
    while (s*m)**3 <= n or gcd(m, n) != 1: m += 1
    out = set()
    sm = s*m
    for i in range(m):
        ri = r + s*i
        if gcd(ri, m) == 1:
            out |= divisors_in_class(n, ri, sm)
    return out

if __name__ == '__main__':
    import random
    random.seed(1)
    bad = 0; tot = 0; hits = 0
    for trial in range(200000):
        n = random.randrange(2, 200000)
        if trial % 3 == 0:   # make sure some have many divisors
            n = random.choice([2,3,4,5,6,7,9,11,12,30])*random.randrange(1,300)*random.randrange(1,300)+0
        s = random.randrange(2, 400)
        if gcd(n, s) != 1: continue
        r = random.randrange(1, s)
        if gcd(r, s) != 1: continue
        want = {d for d in range(1, n+1) if n % d == 0 and d % s == r} if n < 5000 else \
               {d for d in range(r, n+1, s) if d and n % d == 0}
        if s**3 > n:
            got = divisors_in_class(n, r, s)
        else:
            got = divisors_in_class_any(n, r, s)
        tot += 1; hits += len(want)
        if got != want:
            bad += 1
            if bad < 10: print("MISMATCH", n, r, s, sorted(got), sorted(want))
    print(f"{tot} cases, {hits} divisors expected in total, {bad} mismatches")
