"""Plain search (no sieve, no scan) for solutions of sum 1/x_i + 1/prod x_i = 1 in ODD integers,
k terms, x_1 < ... < x_k.  Same recursion as ../znam.py with an oddness filter; the last two
terms come from factoring N = P^2 + r completely.  Fine for k = 10; hopeless for k = 12."""
import sys, math
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "znam"))
from znam import divisors

def solve_odd(k):
    sols = []; leaves = 0
    def rec(xs, P, r, m):
        nonlocal leaves
        if m == 2:
            leaves += 1
            N = P * P + r
            for d in divisors(N):
                e = N // d
                if d > e or (d + P) % r or (e + P) % r: continue
                y, z = (d + P) // r, (e + P) // r
                if y > xs[-1] and z > y and y % 2 and z % 2:
                    sols.append(xs + [y, z])
            return
        lo = max(xs[-1] + 1 if xs else 2, P // r + 1)
        hi = ((m + 1) * P) // r
        for x in range(lo, hi + 1):
            if x % 2 == 0 or math.gcd(x, P) != 1: continue
            rec(xs + [x], P * x, r * x - P, m - 1)
    rec([], 1, 1, k)
    return sols, leaves

if __name__ == "__main__":
    k = int(sys.argv[1])
    sols, leaves = solve_odd(k)
    print("k", k, "leaves", leaves, "odd solutions", len(sols))
    for s in sols: print(s)
