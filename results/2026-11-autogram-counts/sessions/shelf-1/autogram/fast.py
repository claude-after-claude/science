#!/usr/bin/env python3
"""
fast.py -- the same exhaustive autogram search as autogram.py, about 60x faster.

Same template, same model, same bounds propagation, same answers.  Two changes:

1. Every row (the 16 letter equations, the total, and 64 redundant
   combinations) is one 16-bit field of a single Python int, so "check every
   row" and "filter this value against every row" are a handful of big-int
   operations instead of a Python loop over rows.  Field arithmetic uses the
   top bit of each field as a guard: after (a | GUARD) - b the guard bit is
   still set exactly where a >= b.

2. Since rows became nearly free, the 64 redundant rows were chosen by
   measurement, not by eye: 2000 candidate combinations were all switched on
   for three openings, each was scored by how often it was (one of) the rows
   that removed a value or killed a node, and the best 64 were kept.

Usage:
    python3 fast.py solve  "This sentence contains" ["Another opening" ...]
    python3 fast.py check  < results.txt       # re-derive a results file, compare
    python3 fast.py census english 1000 1      # ensemble, how many, seed -> stdout
    python3 fast.py tally  < census-file       # recount every solution, then statistics
    python3 fast.py planted 200                # openings with a known solution built in
    python3 fast.py rows                       # re-derive the 64 redundant rows (minutes)

Needs autogram.py next to it (words, renderer, verifier, model).
"""
import random, re, sys, time
from collections import Counter
import autogram as ag
from autogram import VAR, K, RANGE_K, NMAX, LETTERS, A

FB = 16                     # bits per field; the top one is the guard bit
OFF = 128                   # bias so that every stored term is in 0..255

# Redundant rows, best first (see docstring).  +g+u+v+x means: add up the
# equations for g, u, v and x.  Any integer combination is implied by the
# sixteen originals, so none of these can remove a solution.
ROWS = """
+g+u+v+x +e-g-h+i-n-v -l+v +o-u +t+u-y +e-h+i-l-n-v -l-s+v+x -g+h +l+t-y
+g-h+r-u -g+i+l+u +g+o+v +l+y +f+g+l+x +e-h+i-n-v-x +g-h+l+r-u -h+t-w-y +t-y
+e-g-h+i-n +g+v+x +h+v+x +h-l+o+v +g+l+s+u +f-u +l+o-u-w+y +s-x +h+l+u+x
-h+t-w +g-h+t-y +g+r+v +g+h+n-t+w+y +o-u+y +h+u+v +e-g-h+i-n-x +g+y
-g+h+u+v+x -g+i-x +g+l+r+x +h+l+o -g+i+l -g+t-w +o+v+x +g+l+o+x -g+i
+i+l+u-x -h+t-w+y -g+h+y +r+v+x -g+h+o+v +g-l+u+v+x +s-x+y -l+v+y -g+h+l
+g+l+u+x -g-r+t+u +f-l+s+u+v+x +g+l+y +g-h+r-u+y -g+i+o-u +g-h+l+t-w-y
+g-h+l+t-y +g-h+t+x-y -g+h-r+u+y -g+i+u
""".split()

class Packed:
    """Prefix-independent tables: P[b][n] = all rows' terms for 'letter b has count n'."""
    def __init__(self, combos=ROWS):
        rows, self.ys = ag.build_rows(combos)
        R = self.R = len(rows)
        self.GD = sum(1 << (FB * a + FB - 1) for a in range(R))
        self.P = []
        for b in RANGE_K:
            pb = [0]
            for n in range(1, NMAX + 1):
                x = 0
                for a in range(R):
                    v = rows[a][b][n] + OFF
                    assert 0 <= v < 256, (a, b, n, v)
                    x |= v << (FB * a)
                pb.append(x)
            self.P.append(pb)
        self.memo = {}

    def bounds(self, b, d):
        """Field-wise min and max of P[b][n] over n in d."""
        r = self.memo.get((b, d))
        if r is None:
            GD = self.GD; Pb = self.P[b]
            mn = mx = Pb[d[0]]
            for n in d[1:]:
                x = Pb[n]
                m = ((mn | GD) - x) & GD; m -= m >> (FB - 1)      # all-ones where mn >= x
                mn ^= (mn ^ x) & m
                m = ((x | GD) - mx) & GD; m -= m >> (FB - 1)      # all-ones where x >= mx
                mx ^= (mx ^ x) & m
            r = self.memo[(b, d)] = (mn, mx)
        return r

_PK = None
def packed():
    global _PK
    if _PK is None: _PK = Packed()
    return _PK

class FastSolver:
    def __init__(self, prefix, pk=None):
        self.prefix = prefix; self.pk = pk or packed()
        t, self.fixed = ag.setup(prefix)
        tt = list(t) + [sum(k * t[a] for a, k in y.items()) for y in self.pk.ys]
        self.dead = False           # a target no assignment can reach: no solutions
        T = 0
        for a, v in enumerate(tt):
            v += K * OFF
            if not (0 <= v < (1 << (FB - 2))): self.dead = True; v = 0
            T |= v << (FB * a)
        self.T = T; self.TG = T | self.pk.GD
        self.nodes = 0; self.solutions = []

    def propagate(self, dom, MN, MX, LO, HI):
        """Bounds propagation to a fixed point, in place.  -> (LO, HI) or None."""
        pk = self.pk; GD = pk.GD; P = pk.P; T = self.T; TG = self.TG; bounds = pk.bounds
        x = TG - LO; y = (HI | GD) - T
        if x & y & GD != GD: return None                 # some row has LO > T or HI < T
        UP = x ^ GD; DOWN = y ^ GD                       # slack per row: T - LO, HI - T
        todo = [b for b in RANGE_K if len(dom[b]) > 1]
        changed = True
        while changed:
            changed = False
            for b in todo:
                d = dom[b]
                if len(d) == 1: continue
                mn = MN[b]; mx = MX[b]
                w = mx - mn
                if ((UP | GD) - w) & ((DOWN | GD) - w) & GD == GD: continue   # nothing to remove
                Ub = mn + UP + GD; Lb = DOWN - mx + GD
                Pb = P[b]
                # keep n iff in every row   mx - DOWN <= term(n) <= mn + UP
                d2 = tuple([n for n in d if (Ub - Pb[n]) & (Pb[n] + Lb) & GD == GD])
                if len(d2) != len(d):
                    if not d2: return None
                    dom[b] = d2
                    nm, nM = bounds(b, d2)
                    LO += nm - mn; HI += nM - mx
                    MN[b] = nm; MX[b] = nM
                    x = TG - LO; y = (HI | GD) - T
                    if x & y & GD != GD: return None
                    UP = x ^ GD; DOWN = y ^ GD
                    changed = True
        return LO, HI

    def dfs(self, dom, MN, MX, LO, HI):
        self.nodes += 1
        best = -1; bl = NMAX + 1
        for b in RANGE_K:
            l = len(dom[b])
            if 1 < l < bl: best, bl = b, l
        if best < 0:
            sol = dict(self.fixed); sol.update({VAR[b]: dom[b][0] for b in RANGE_K})
            self.solutions.append(sol); return
        Pb = self.pk.P[best]; mn = MN[best]; mx = MX[best]
        for n in dom[best]:
            d2 = dom[:]; m2 = MN[:]; M2 = MX[:]
            p = Pb[n]
            d2[best] = (n,); m2[best] = p; M2[best] = p
            r = self.propagate(d2, m2, M2, LO - mn + p, HI - mx + p)
            if r is None: self.nodes += 1                # counted like autogram.py counts them
            else: self.dfs(d2, m2, M2, r[0], r[1])

    def solve(self):
        """All autograms for the prefix (sorted), each re-checked by autogram.verify()."""
        if not self.dead:
            pk = self.pk
            dom = [tuple(range(1, NMAX + 1))] * K
            MN = []; MX = []
            for b in RANGE_K:
                m, M = pk.bounds(b, dom[b]); MN.append(m); MX.append(M)
            r = self.propagate(dom, MN, MX, sum(MN), sum(MX))
            if r is not None: self.dfs(dom, MN, MX, r[0], r[1])
        out = []
        for sol in self.solutions:
            text = ag.render(self.prefix, {l: sol[A[l]] for l in LETTERS})
            n, bad = ag.verify(text)
            assert n == 26 and not bad, (text, bad)
            out.append(text)
        return sorted(out)

def solve(prefix):
    s = FastSolver(prefix); return s.solve(), s.nodes

# ---------------------------------------------------------------- census ----
# English letter frequencies, per 10,000 letters (the usual textbook table).
FREQ = dict(e=1270, t=906, a=817, o=751, i=697, n=675, s=633, h=609, r=599, d=425, l=403, c=278,
            u=276, m=241, w=236, f=223, g=202, y=197, p=193, b=149, v=98, k=77, j=15, x=15, q=10, z=7)

def ensemble(name, count, seed):
    """Yield `count` openings.  Only an opening's letter counts matter to the search.

    english   a bag of L letters, L uniform on 0..60, letters drawn from FREQ
    flat      each of the 26 letters appears 0..4 times, uniformly and independently
    text      the first 2..8 words of sentences in Python's own language reference
    box:XYZ   the opening XYZ followed by 0..9 extra copies of each of the sixteen
              letters that occur in number-words (the ensemble volume.py can audit)
    """
    rng = random.Random(f"{name}/{seed}")
    if name == "english":
        ls = list(FREQ); ws = list(FREQ.values())
        for _ in range(count):
            yield "".join(sorted(rng.choices(ls, ws, k=rng.randint(0, 60))))
    elif name == "flat":
        for _ in range(count):
            yield "".join(l * rng.randint(0, 4) for l in LETTERS)
    elif name == "text":
        import pydoc_data.topics as t
        body = " ".join(t.topics[k] for k in sorted(t.topics))
        sents = [s.split() for s in re.findall(r"(?<=[.!?] )[A-Z][a-z]+(?: [A-Za-z][a-z]*,?){7,}", re.sub(r"\s+", " ", body))]
        seen = set()
        while len(seen) < count:
            s = rng.choice(sents); p = " ".join(s[:rng.randint(2, 8)]).rstrip(",")
            if p not in seen: seen.add(p); yield p
    elif name.startswith("box:"):
        for _ in range(count):
            yield (name[4:] + " " + "".join(LETTERS[i] * rng.randint(0, 9) for i in VAR)).strip()
    else:
        raise SystemExit("ensembles: english, flat, text, box:OPENING")

def census(name, count, seed):
    """One line per opening:  opening <tab> number of autograms <tab> nodes <tab> count vectors."""
    for prefix in ensemble(name, count, seed):
        s = FastSolver(prefix); s.solve()
        vecs = ["".join(f"{sol[i]:02d}" for i in range(26)) for sol in s.solutions]
        print(prefix, len(vecs), s.nodes, " ".join(sorted(vecs)), sep="\t", flush=True)

def read_census(lines):
    for line in lines:
        if line.startswith("#") or not line.strip(): continue
        prefix, n, nodes, vecs = line.rstrip("\n").split("\t")
        yield prefix, int(n), int(nodes), vecs.split()

def tally(lines):
    """Read a census file back, recounting every stored solution with autogram.verify()."""
    rows = list(read_census(lines))
    for prefix, n, nodes, vecs in rows:
        assert n == len(vecs)
        for v in vecs:
            text = ag.render(prefix, {l: int(v[2 * i:2 * i + 2]) for i, l in enumerate(LETTERS)})
            k, bad = ag.verify(text); assert k == 26 and not bad, text
    return rows

def report(rows, bins=6):
    """Histogram against Poisson, a chi-square, and the mean by length of opening."""
    from math import exp, factorial
    total = len(rows); ks = [r[1] for r in rows]; hist = Counter(ks)
    mean = sum(ks) / total
    var = sum((k - mean) ** 2 for k in ks) / (total - 1)
    print(f"openings {total}   mean {mean:.3f} (s.e. {(var / total) ** 0.5:.3f})   variance {var:.3f}")
    print("  k   seen   Poisson(1)   Poisson(mean)")
    for k in range(max(hist) + 1):
        print(f"{k:3d} {hist[k]:6d} {total * exp(-1) / factorial(k):12.1f} {total * exp(-mean) * mean ** k / factorial(k):15.1f}")
    def chi2(lam):                                   # cells 0, 1, 2, 3, 4+
        ex = [total * exp(-lam) * lam ** k / factorial(k) for k in range(4)]; ex.append(total - sum(ex))
        ob = [hist[k] for k in range(4)]; ob.append(total - sum(ob))
        return sum((o - e) ** 2 / e for o, e in zip(ob, ex))
    print(f"chi-square on cells 0,1,2,3,4+:  {chi2(1):.1f} against Poisson(1) (5% point 9.49),  "
          f"{chi2(mean):.1f} against Poisson(mean) (5% point 7.81)")
    size = lambda p: sum(ch.isalpha() for ch in p)
    rows = sorted(rows, key=lambda r: size(r[0]))
    print("by length of opening (equal-sized groups):")
    for i in range(bins):
        part = rows[i * total // bins:(i + 1) * total // bins]
        ks = [r[1] for r in part]; m = sum(ks) / len(ks); v = sum((k - m) ** 2 for k in ks) / (len(ks) - 1)
        print(f"  {size(part[0][0]):3d}..{size(part[-1][0]):3d} letters   n={len(ks):4d}   mean {m:.3f} +- {(v / len(ks)) ** .5:.3f}   variance/mean {v / m:.2f}")

# --------------------------------------------------------- planted test ----
def planted(count, seed):
    """Openings built so that a known count vector is a solution; the search must find it.

    A vector is made by a few rounds of "count the letters, add some slack"; the
    opening is then whatever letters are missing.  Reports how many OTHER solutions
    each such opening has (their openings are junk, around 70 letters long).
    """
    def totals(c):
        tot = [1] * 26
        for ch in "and": tot[A[ch]] += 1
        for n in c:
            for k in range(26): tot[k] += ag.VEC[n][k]
        return tot
    rng = random.Random(f"planted/{seed}"); others = Counter(); made = 0
    while made < count:
        slack = [rng.randint(0, 6 if i in VAR else 3) for i in range(26)]
        c = [rng.randint(1, 12) for _ in range(26)]
        for _ in range(rng.randint(3, 8)):
            c = [min(t + e, NMAX) for t, e in zip(totals(c), slack)]
        need = [ci - ti for ci, ti in zip(c, totals(c))]
        if min(need) < 0: continue
        prefix = "".join(l * k for l, k in zip(LETTERS, need))
        texts, _ = solve(prefix)
        assert ag.render(prefix, dict(zip(LETTERS, c))) in texts, (prefix, c)
        others[len(texts) - 1] += 1; made += 1
    print(f"planted solution recovered in all {made} cases")
    print("other solutions per opening:", sorted(others.items()),
          f"  mean {sum(k * v for k, v in others.items()) / made:.2f}")

# ------------------------------------------------------- choosing ROWS ----
def choose_rows(openings, pool=2000, keep=64):
    """Re-derive ROWS: switch on a large pool of combinations and see which ones do the work.

    Each time a value is removed or a node dies, the rows responsible share one
    point between them.  Takes a few minutes.
    """
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): ag.families(max_letters=6, show=pool)
    names = [c for c, _ in ag.FAMILIES]
    names += [c for c in (l.split()[0] for l in buf.getvalue().splitlines()) if c not in names]
    pk = Packed(names); GD = pk.GD; blame = Counter()
    class Scored(FastSolver):
        def propagate(self, dom, MN, MX, LO, HI):
            P = pk.P; T = self.T; TG = self.TG
            x = TG - LO; y = (HI | GD) - T
            if x & y & GD != GD: blame[GD & ~(x & y)] += 1; return None
            UP = x ^ GD; DOWN = y ^ GD
            changed = True
            while changed:
                changed = False
                for b in RANGE_K:
                    d = dom[b]
                    if len(d) == 1: continue
                    mn = MN[b]; mx = MX[b]; w = mx - mn
                    if ((UP | GD) - w) & ((DOWN | GD) - w) & GD == GD: continue
                    Ub = mn + UP + GD; Lb = DOWN - mx + GD; Pb = P[b]; d2 = []
                    for n in d:
                        z = (Ub - Pb[n]) & (Pb[n] + Lb) & GD
                        if z == GD: d2.append(n)
                        else: blame[GD ^ z] += 1
                    if len(d2) != len(d):
                        if not d2: return None
                        d2 = tuple(d2); dom[b] = d2
                        nm, nM = pk.bounds(b, d2)
                        LO += nm - mn; HI += nM - mx; MN[b] = nm; MX[b] = nM
                        x = TG - LO; y = (HI | GD) - T
                        if x & y & GD != GD: blame[GD & ~(x & y)] += 1; return None
                        UP = x ^ GD; DOWN = y ^ GD
                        changed = True
            return LO, HI
    for prefix in openings: Scored(prefix, pk).solve()
    score = [0.0] * pk.R
    for bad, cnt in blame.items():
        bits = []
        while bad:
            low = bad & -bad; bits.append((low.bit_length() - 1) // FB); bad ^= low
        for a in bits: score[a] += cnt / len(bits)
    L = [LETTERS[i] for i in VAR]; seen = set(); out = []
    for a in sorted(range(K + 1, pk.R), key=lambda a: -score[a]):          # skip the 16 letter rows and the total
        y = ag._parse_combo(names[a - K - 1]); key = tuple(sorted(y.items()))
        if len(y) > 1 and key not in seen:
            seen.add(key); out.append("".join(("+" if k > 0 else "-") + L[b] for b, k in key))
    return out[:keep]

# ------------------------------------------------------------------- CLI ----
def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "solve":
        for prefix in argv[2:]:
            t0 = time.time(); texts, nodes = solve(prefix)
            print(f"## {prefix!r}: {len(texts)} autogram(s)   [{nodes} nodes, {time.time() - t0:.1f}s]", flush=True)
            for x in texts: print(x)
    elif cmd == "check":
        # results.txt format: "## 'prefix': n autogram(s) ..." followed by the sentences
        cur = None; want = {}
        for line in sys.stdin:
            m = re.match(r"## (['\"])(.*)\1: (\d+) autogram", line)
            if m: cur = m.group(2); want[cur] = []
            elif cur is not None and line.strip() and not line.startswith("#"): want[cur].append(line.strip())
        ok = True; t0 = time.time()
        for prefix, texts in want.items():
            got, nodes = solve(prefix)
            same = got == sorted(texts); ok &= same
            print(("same     " if same else "DIFFERENT"), f"{len(got)} solution(s), {nodes:6d} nodes  {prefix!r}", flush=True)
        print(("all lists reproduced" if ok else "MISMATCH") + f" ({len(want)} openings, {time.time() - t0:.0f}s)")
    elif cmd == "census":
        census(argv[2], int(argv[3]), int(argv[4]) if len(argv) > 4 else 1)
    elif cmd == "planted":
        planted(int(argv[2]), int(argv[3]) if len(argv) > 3 else 1)
    elif cmd == "rows":
        rows = choose_rows(argv[2:] or ["Claude counted", "This sentence contains", "Here are"])
        print(" ".join(rows)); print("same as the built-in list" if rows == ROWS else "DIFFERENT from the built-in list")
    elif cmd == "tally":
        report(tally(sys.stdin))
    else:
        print(__doc__)

if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    main(sys.argv)
