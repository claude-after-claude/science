"""Every one of the 122 solutions must be re-found by leaf() under several configurations
(with/without sieve hits, scan allowed / rho forced, direct scan disabled)."""
import math
import drive
from drive import compute_roots, primes_upto, leaf
drive.PRIMES = primes_upto(1_000_000)
sols = [tuple(map(int, l.split())) for l in open('k8.sols')]
roots = {}
res = {}
for name, use_sieve, KF, T1 in [("default", True, 2500, 50_000), ("no-sieve", False, 2500, 50_000), ("rho-only", True, 0, 0), ("scan-heavy", True, 1e5, 0), ("no-direct", True, 2500, 0)]:
    drive.KF = KF; drive.T1 = T1
    paths = [0, 0, 0, 0]; found = 0
    for s in sols:
        xs = list(s[:5]); x = s[5]; P0 = math.prod(xs); r0 = P0 - sum(P0 // v for v in xs)
        hits = None; B = 1
        if use_sieve:
            B = 1_000_000
            if (P0, r0) not in roots: roots[P0, r0] = compute_roots(P0, r0, B)
            ps, rs = roots[P0, r0]
            hits = [p for p, rt in zip(ps, rs) if (x - rt) % p == 0]
        drive.STAT = [0, 0, 0, 0, 0, 0.0, 0.0, 0.0]
        got = set(leaf(P0, r0, x, hits, B))
        for i in range(4): paths[i] += drive.STAT[i]
        want = {(t[6], t[7]) for t in sols if t[:6] == s[:6]}
        found += want <= got and all(not (y > x and z > y) or (y, z) in want for (y, z) in got)
    print(f"{name:10s} re-found {found}/{len(sols)}   leaves by path [direct scan, full factor, sieve+scan, rho] = {paths}", flush=True)
