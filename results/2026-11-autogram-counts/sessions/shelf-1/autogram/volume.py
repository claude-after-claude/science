#!/usr/bin/env python3
"""
volume.py -- how many autograms to expect, measured without searching for any.

Every vector c of sixteen counts is the solution of exactly one bag of opening
letters: the difference between c and the letters of c's own number-words
(when no entry of that difference is negative).  Take an opening and the "box" of 10^16 openings obtained by
appending 0..9 extra copies of each of the sixteen number-word letters.  Then

    average number of autograms per opening in the box
        =  (number of vectors c whose opening lies in the box) / 10^16 .

The right-hand side is estimated here by importance sampling: draw c, work
out which opening it solves, see whether that opening is in the box.  There is
no solver in this file -- no propagation, no rows, no tree.

So this is two things at once.  It is a map of where autograms are common
and where they are rare.  And it is an audit: `fast.py census box:OPENING N`
measures the left-hand side by exhaustive search, and if the search were
losing solutions its average would fall below this one.

    python3 volume.py 1000000 "" [seed] [width]
    python3 volume.py selftest            # the estimator on a case with a known answer
"""
import random, sys
import autogram as ag
from autogram import VAR, VEC, K, NMAX, LETTERS

FB = 16; BIAS = 8
ORDER = [VAR.index(ag.A[l]) for l in "gluxywvfhroistne"]     # rare letters first, e last
MASK = (1 << FB) - 1
GD = sum(1 << (FB * k + FB - 1) for k in range(K))
# VP[n]: field k = number of letters VAR[k] in the words for n
VP = [0] + [sum(VEC[n][VAR[k]] << (FB * k) for k in range(K)) for n in range(1, NMAX + 1)]
# D[i][n]: field k = [k == i] * n - VP[n] field k + BIAS     (so the sum over i is  c - S(c) + 16 * BIAS)
D = [[0] + [(n << (FB * i)) + sum(BIAS << (FB * k) for k in range(K)) - VP[n] for n in range(1, NMAX + 1)] for i in range(K)]

def S(c):
    return [sum(VEC[n][VAR[k]] for n in c) for k in range(K)]

class Box:
    def __init__(self, opening="", width=10):
        t0, _ = ag.setup(opening)
        self.W = width
        self.base0 = [-t for t in t0]      # letters from everything except the 16 unknown number-words
        self.ZLO = sum((K * BIAS + self.base0[k]) << (FB * k) for k in range(K))
        self.ZHI = sum((K * BIAS + self.base0[k] + width - 1) << (FB * k) for k in range(K))
        self.KN0 = sum(self.base0[k] << (FB * k) for k in range(K))

    def contains(self, c):
        """Is the opening that c solves inside the box?"""
        z = 0
        for i in range(K): z += D[i][c[i]]
        return ((z | GD) - self.ZLO) & ((self.ZHI | GD) - z) & GD == GD

    def central(self, rng, rounds=6, m=3000):
        """Intervals holding most of the c we want.  Only efficiency depends on them, not correctness."""
        lo = [1] * K; hi = [40] * K
        for _ in range(rounds):
            ss = [S([rng.randint(lo[i], hi[i]) for i in range(K)]) for _ in range(m)]
            for k in range(K):
                col = sorted(s[k] for s in ss)
                lo[k] = max(1, min(NMAX - 1, self.base0[k] + col[m // 200]))
                hi[k] = max(lo[k], min(NMAX, self.base0[k] + self.W - 1 + col[-1 - m // 200]))
        return lo, hi

    def estimate(self, M, seed=1, p_near=0.13, p_far=0.02, margin=4):
        """-> (mean autograms per opening, standard error, hits, hits that needed a tail).

        The counts are drawn one letter at a time.  When a letter's turn comes, the
        words already drawn have fixed part of its total, so its count can be aimed
        at a narrow window.  The window is a guess (it trusts the intervals from
        central()), so with probability p_near the count is drawn from the window
        widened by `margin` on both sides, and with probability p_far from all of
        1..99.  Every c stays possible, each sample is weighted by 1 / (its
        probability), and the estimate is unbiased whatever the windows are.
        """
        rng = random.Random(f"volume/{seed}"); rnd = rng.random
        lo, hi = self.central(rng); W = self.W
        vmin = [[min(VEC[n][VAR[k]] for n in range(lo[j], hi[j] + 1)) for k in range(K)] for j in range(K)]
        vmax = [[max(VEC[n][VAR[k]] for n in range(lo[j], hi[j] + 1)) for k in range(K)] for j in range(K)]
        steps = []
        for t, i in enumerate(ORDER):
            later = ORDER[t:]                                   # letter i's own word and the words still to come
            steps.append((i, FB * i, sum(vmin[j][i] for j in later), sum(vmax[j][i] for j in later) + W - 1, lo[i], hi[i], D[i]))
        p_win = 1 - p_near - p_far; far = p_far / NMAX; KN0 = self.KN0; ZLO = self.ZLO; ZHI = self.ZHI
        tot = tot2 = 0.0; hits = tails = 0
        for _ in range(M):
            kn = KN0; z = 0; q = 1.0; tail = False
            for i, sh, a, b, l, h, Di in steps:
                known = (kn >> sh) & MASK
                a += known; b += known
                if a < l: a = l
                if b > h: b = h
                if a > b: a, b = b, a                           # the guess was empty; aim at the gap instead
                a2 = a - margin if a > margin else 1
                b2 = b + margin if b + margin < NMAX else NMAX
                r = rnd()
                if r < p_win: n = a + int(rnd() * (b - a + 1))
                elif r < p_win + p_near: n = a2 + int(rnd() * (b2 - a2 + 1))
                else: n = 1 + int(rnd() * NMAX)
                if a <= n <= b: q *= far + p_near / (b2 - a2 + 1) + p_win / (b - a + 1)
                elif a2 <= n <= b2: q *= far + p_near / (b2 - a2 + 1); tail = True
                else: q *= far; tail = True
                kn += VP[n]; z += Di[n]
            if ((z | GD) - ZLO) & ((ZHI | GD) - z) & GD == GD:
                hits += 1; tails += tail; tot += 1 / q; tot2 += 1 / (q * q)
        scale = float(W) ** K
        mean = tot / M
        return mean / scale, ((tot2 / M - mean * mean) / M) ** 0.5 / scale, hits, tails

def det(M):
    n = len(M); M = [r[:] for r in M]; d = 1.0
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(M[r][i]))
        if abs(M[p][i]) < 1e-12: return 0.0
        if p != i: M[i], M[p] = M[p], M[i]; d = -d
        d *= M[i][i]
        for r in range(i + 1, n):
            f = M[r][i] / M[i][i]
            for c in range(i, n): M[r][c] -= f * M[i][c]
    return d

def trend(opening="", width=10, seed=1):
    """A back-of-envelope prediction of the same average, 1 / det(I - J).

    J[k][j] is the straight-line slope of "how many letters k are in the words
    for n" against n, over the plausible range of count j.  If the letters in
    the number-words drifted exactly linearly with the counts, c -> opening
    would be a linear map and this would be its density.  They do not, and the
    answer moves when the ranges move; treat it as a rough guide (README).
    """
    lo, hi = Box(opening, width).central(random.Random(f"trend/{seed}"))
    J = [[0.0] * K for _ in range(K)]
    for j in range(K):
        ns = range(lo[j], hi[j] + 1); mn = sum(ns) / len(ns); vn = sum((n - mn) ** 2 for n in ns)
        for k in range(K):
            ys = [VEC[n][VAR[k]] for n in ns]; my = sum(ys) / len(ys)
            J[k][j] = sum((n - mn) * (y - my) for n, y in zip(ns, ys)) / vn if vn else 0.0
    return 1 / det([[(i == j) - J[i][j] for j in range(K)] for i in range(K)])

def selftest():
    """Give every number the same name.  Then c -> opening is a pure shift, every opening
    has exactly one autogram, and both estimates below must come out as 1 -- the second
    one with deliberately wrong windows, so that almost every hit has to come from a tail."""
    for n in range(1, NMAX + 1): VEC[n] = VEC[23]
    VP[:] = [0] + [sum(VEC[n][VAR[k]] << (FB * k) for k in range(K)) for n in range(1, NMAX + 1)]
    for i in range(K):
        D[i][:] = [0] + [(n << (FB * i)) + sum(BIAS << (FB * k) for k in range(K)) - VP[n] for n in range(1, NMAX + 1)]
    box = Box("", 10)
    mean, se, hits, tails = box.estimate(200000)
    print(f"good windows: {mean:.3f} +- {se:.3f}   ({hits} hits, {tails} from tails)")
    good = box.central
    box.central = lambda rng: (lambda lo, hi: (lo, [h - 2 for h in hi]))(*good(rng))
    mean, se, hits, tails = box.estimate(600000)
    print(f"bad windows:  {mean:.3f} +- {se:.3f}   ({hits} hits, {tails} from tails)")

if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]: selftest(); sys.exit()
    M = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
    opening = sys.argv[2] if len(sys.argv) > 2 else ""
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    W = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    mean, se, hits, tails = Box(opening, W).estimate(M, seed)
    print(f"box around {opening!r}, width {W}: {M} samples, {hits} hits ({tails} of them outside the guessed windows)")
    print(f"average number of autograms per opening in the box: {mean:.3f} +- {se:.3f}")
    print(f"(linear-trend guess for the same number: {trend(opening, W):.2f})")
