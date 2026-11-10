"""Independent check of the leaf solver: for random (prefix, x) leaves of the k=8 search,
compare drive.leaf (sieve + scan / rho) against plain full factorisation of N."""
import random, sys, math
import drive
from drive import prefixes, hard_end, compute_roots, primes_upto, leaf
from znam import factor
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
n_pref = int(sys.argv[2]) if len(sys.argv) > 2 else 25
drive.PRIMES = primes_upto(2_000_000)
pre = [p for p in prefixes(8)]
weights = [p[4] - p[3] + 1 for p in pre]
checked = 0; bad = 0; nsol = 0; paths = [0, 0, 0, 0]
for xs, P0, r0, lo, hi in random.choices(pre, weights=weights, k=n_pref):
    he = hard_end(P0, r0, lo, hi)
    R = he - lo
    B = 1; ps = rs = ()
    if R >= 100:
        B = min(2_000_000, max(100_000, 10 * R))
        ps, rs = compute_roots(P0, r0, B)
    for _ in range(12):
        # bias towards the hard region and its low end
        u = random.random()
        x = lo + int((he - lo) * u * u) if (random.random() < .7 and he > lo) else random.randrange(lo, hi + 1)
        if math.gcd(x, P0) != 1 or x <= xs[-1]: continue
        hits = [p for p, rt in zip(ps, rs) if (x - rt) % p == 0] if R >= 100 and x < he else None
        drive.STAT = [0, 0, 0, 0, 0, 0.0, 0.0, 0.0]
        got = {(y, z) for (y, z) in leaf(P0, r0, x, hits, B if hits is not None else 1) if y > x and z > y}
        for i in range(4): paths[i] += drive.STAT[i]
        P = P0 * x; r = r0 * x - P0; N = P * P + r
        ds = [1]
        for p, e in factor(N).items():
            ds = [d * p ** i for d in ds for i in range(e + 1)]
        want = set()
        for d in ds:
            e = N // d
            if d <= e and (d + P) % r == 0:
                y, z = (d + P) // r, (e + P) // r
                if y > x and z > y: want.add((y, z))
        checked += 1; nsol += len(want)
        if got != want:
            bad += 1; print("MISMATCH", xs, x, got, want)
print("leaves checked", checked, "by path [direct scan, full factor, sieve+scan, rho]", paths, "solutions among them", nsol, "mismatches", bad)
