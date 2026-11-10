"""The prefix enumeration of odd.py, redone with exact fractions and the bounds written as
the inequalities they come from, to check the integer bookkeeping (P, r, floor divisions).

With rem = 1 - (1/x_1 + ... + 1/x_j) and m terms still to choose, the next term x satisfies
    1/x < rem                      (what is left over is positive)
    rem < (m + 1)/x                (m terms each <= 1/x, plus 1/N < 1/x)
and when m = 3 the sharper  rem < 3/x  (see below), so x < 3/rem; odd.py allows x <= 3/rem + 1.
    [x < y < z, N >= x y z:  1/y + 1/z + 1/N <= 1/(x+1) + 1/(x+2) + 1/(x(x+1)(x+2)) < 2/x,
     because 2/x - 1/(x+1) - 1/(x+2) = (3x+4)/(x(x+1)(x+2)).]

    python3 prefix_check.py 12
"""
import sys
from fractions import Fraction
from math import gcd, floor
import odd

def prefixes(k):
    out = []
    def rec(xs, rem, m):
        prod = 1
        for v in xs: prod *= v
        last = xs[-1] if xs else 1
        if m == 3:
            xs_ok = [x for x in range(last + 1, floor(3 / rem) + 2) if Fraction(1, x) < rem]
            if xs_ok: out.append((tuple(xs), xs_ok[0], floor(3 / rem) + 1))
            return
        x = last + 1
        while Fraction(m + 1, x) >= rem:          # odd.py keeps the boundary case; so do we
            if x % 2 == 1 and Fraction(1, x) < rem and gcd(x, prod) == 1:
                rec(xs + [x], rem - Fraction(1, x), m - 1)
            x += 1
    rec([], Fraction(1), k)
    return out

k = int(sys.argv[1])
mine = sorted(prefixes(k))
theirs = sorted((tuple(xs), lo, hi) for xs, P, r, lo, hi in odd.prefixes(k))
print("k", k, "prefixes:", len(mine), "vs", len(theirs), " identical:", mine == theirs,
      " total range:", sum(hi - lo + 1 for _, lo, hi in mine))
