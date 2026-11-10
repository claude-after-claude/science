"""Independent checks for claims 1 and 3 (exact integers). Usage: check.py b075461.txt [session_list ...]"""
import re
import sys
from fractions import Fraction
from itertools import combinations, permutations, product
from math import gcd, prod


def is_solution(t):
    return sum(Fraction(1, x) for x in t) + Fraction(1, prod(t)) == 1


def is_proper_znam(t):
    for i, x in enumerate(t):
        v = prod(t[:i] + t[i + 1:]) + 1
        if v % x or v == x:
            return False
    return True


def jacobi(a, n):
    assert n > 0 and n % 2 == 1
    a %= n
    r = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                r = -r
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            r = -r
        a %= n
    return r if n == 1 else 0


# ---- claim 1: lists from OEIS A075461 b-file
vals = [int(l.split()[1]) for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
proper = {}
pos = 0
for k, cnt in ((5, 2), (6, 5), (7, 18), (8, 96)):
    proper[k] = [tuple(vals[pos + i * k: pos + (i + 1) * k]) for i in range(cnt)]
    pos += k * cnt
assert pos == len(vals) == 934
for k, lst in proper.items():
    assert len(set(lst)) == len(lst)
    for t in lst:
        assert list(t) == sorted(t) and is_solution(t) and is_proper_znam(t), t
print("OEIS b-file: proper counts", {k: len(v) for k, v in proper.items()}, "all verified exactly")

improper = {4: [(2, 3, 7, 43)]}
assert is_solution(improper[4][0])
for k in (5, 6, 7, 8):
    ext = [t + (prod(t) + 1,) for t in improper[k - 1]]
    improper[k] = sorted(set(proper[k]) | set(ext))
    assert len(improper[k]) == len(proper[k]) + len(ext)
    assert all(is_solution(t) for t in improper[k])
print("improper counts (proper(k) + improper(k-1)):", {k: len(v) for k, v in improper.items()})

no3 = [t for t in improper[8] if 3 not in t]
print("8-term solutions without a 3:", no3)
tup = (2, 5, 7, 11, 17, 157, 961, 4398619)
print("tuple", tup, "satisfies equation:", is_solution(tup), "| proper Znam:", is_proper_znam(tup),
      "| pairwise coprime:", all(gcd(a, b) == 1 for a, b in combinations(tup, 2)))

for path in sys.argv[2:]:
    got = set()
    for l in open(path):
        l = l.split('#')[0]
        nums = tuple(int(x) for x in re.findall(r'\d+', l))
        if len(nums) == 8:
            got.add(tuple(sorted(nums)))
    print(f"session list {path.split('scratchpad/')[-1]}: {len(got)} 8-tuples; equal to OEIS-derived 122: {got == set(improper[8])}")

# ---- claim 2 side check: all-odd forces N = 0 mod 4 (residues mod 4 only)
ok_N = set()
for N in range(1, 15):
    for a3 in range(N + 1):  # number of terms = 3 mod 4; the rest = 1 mod 4
        res = [3] * a3 + [1] * (N - a3)
        P = prod(res)
        lhs = sum(prod(res[:i] + res[i + 1:]) for i in range(N)) + 1
        if (lhs - P) % 4 == 0:
            ok_N.add(N)
print("N for which sum_i prod_{j!=i} x_j + 1 = prod x_j is solvable mod 4 in odd residues:", sorted(ok_N))

# ---- claim 3: the lemma, every solution containing 2, every ordered choice (x; y, z)
stats = dict(cases=0, t3=0, t1=0, viol=0, a1=0, cor_viol=0, ident_viol=0)
for k in (4, 5, 6, 7, 8):
    for sol in improper[k]:
        if 2 not in sol:
            continue
        others = [v for v in sol if v != 2]
        for trio in combinations(others, 3):
            rest = [v for v in sol if v not in trio]
            P = prod(rest)
            aF = P * (1 - sum(Fraction(1, v) for v in rest))
            assert aF.denominator == 1
            a = int(aF)
            for x, y, z in permutations(trio):
                t = a * x - P
                d = t * y - P * x
                okid = (a > 0 and gcd(a, P) == 1 and a * x * y * z == P * (x * y + y * z + z * x) + 1
                        and P % 2 == 0 and a % 2 and x % 2 and t % 2 and t > 0 and gcd(t, P * x) == 1
                        and (t * y - P * x) * (t * z - P * x) == P * P * x * x + t
                        and d > 0 and d % 2 and gcd(d, t) == 1 and d * z == P * x * y + 1)
                stats['ident_viol'] += not okid
                stats['cases'] += 1
                j = jacobi(a, t)
                if t % 4 == 3:
                    stats['t3'] += 1
                    stats['viol'] += (j != -1)
                else:
                    stats['t1'] += 1
                    stats['viol'] += ((d - j) % 4 != 0)
            if a == 1:
                stats['a1'] += 1
                assert is_solution(tuple(rest))
                stats['cor_viol'] += any(v % 4 != 3 for v in trio) or P % 4 != 2
print("lemma test over k=4..8, ordered (x,y,z):", stats)

# Brenton-Hill remainders: a, t, d are R_{N-3}, R_{N-2}, R_{N-1} for the ordering (rest..., x, y, z)
sol = improper[7][5]
x, y, z = sol[-3:]
rest = sol[:-3]
R = [1]
Pk = 1
for n in list(rest) + [x, y, z]:
    R.append(n * R[-1] - Pk)
    Pk *= n
P = prod(rest)
a = R[len(rest)]
print("example", sol, "remainders", R, "-> a,t,d =", a, a * x - P, (a * x - P) * y - P * x, "| R_N =", R[-1])
