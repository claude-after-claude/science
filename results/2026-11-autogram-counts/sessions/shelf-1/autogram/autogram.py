#!/usr/bin/env python3
"""
autogram.py -- find *every* self-counting sentence for a given opening.

An autogram is a sentence that inventories its own letters and gets it right:

    This sentence contains three a's, one b, three c's, ... and one z.

Template used here:   PREFIX n_a a's, n_b b's, ..., n_y y's and n_z z's.
All 26 letters are listed, counts are spelled out in English (1..99),
"one x" takes no 's.  Only letters are counted; punctuation is ignored.

Usage:
    python3 autogram.py solve  "This sentence contains" ["Another prefix" ...]
    python3 autogram.py walk   "This sentence contains" [seed]
    python3 autogram.py verify < sentences.txt
    python3 autogram.py families

`solve` is exhaustive: it prints all solutions, and if it prints none there
are none (in this template).  `walk` is the classic randomised iteration; it
finds a solution quickly if it is lucky and can never say "there isn't one".
Pure Python, standard library only.  A solve takes roughly a minute.
"""
import random, re, sys, time
from collections import Counter
from itertools import combinations, product

# ---------------------------------------------------------------- words ----
LETTERS = "abcdefghijklmnopqrstuvwxyz"
A = {l: i for i, l in enumerate(LETTERS)}
ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen").split()
TENS = "- - twenty thirty forty fifty sixty seventy eighty ninety".split()
NMAX = 99

def num(n):
    if n < 20: return ONES[n]
    t, o = divmod(n, 10)
    return TENS[t] + ("-" + ONES[o] if o else "")

def render(prefix, counts):
    """counts: dict letter -> int (all 26)."""
    items = [f"{num(counts[c])} {c}" + ("" if counts[c] == 1 else "'s") for c in LETTERS]
    return (prefix + " " if prefix else "") + ", ".join(items[:-1]) + " and " + items[-1] + "."

# --------------------------------------------------------------- verify ----
# Deliberately independent of render(): it reads the claims back out of the
# text with its own little number parser and recounts the letters.
_W = {w: i for i, w in enumerate(ONES)}
_W.update({w: 10 * i for i, w in enumerate(TENS) if i >= 2})

def verify(sentence):
    """Return (number_of_claims, {letter: (claimed, actual)} for every mismatch)."""
    claims = {}
    for numw, letter in re.findall(r"([a-z]+(?:-[a-z]+)?) ([a-z])(?:'s)?(?=[,.]| and )", sentence):
        if all(p in _W for p in numw.split("-")):
            claims[letter] = sum(_W[p] for p in numw.split("-"))
    real = Counter(ch for ch in sentence.lower() if ch.isalpha())
    bad = {l: (claims.get(l, 0), real.get(l, 0))
           for l in set(claims) | set(real) if claims.get(l, 0) != real.get(l, 0)}
    return len(claims), bad

# ----------------------------------------------------------------- model ----
# VEC[n][i] = how many times letter i occurs in the words for n (plus plural s).
VEC = [None]
for _n in range(1, NMAX + 1):
    _v = [0] * 26
    for _ch in num(_n):
        if _ch.isalpha(): _v[A[_ch]] += 1
    if _n != 1: _v[A['s']] += 1
    VEC.append(_v)

# Letters that occur in some number-word are the unknowns (16 of them);
# the rest (a b c d j k m p q z) are forced to "whatever the prefix gives".
VAR = [i for i in range(26) if any(VEC[n][i] for n in range(1, NMAX + 1))]
FIX = [i for i in range(26) if i not in VAR]
K = len(VAR)
RANGE_K = range(K)

def setup(prefix):
    """-> (targets for the 16 letter rows, {fixed letter index: count})."""
    base = [1] * 26                                  # each letter names itself once
    for ch in (prefix + " and").lower():
        if ch.isalpha(): base[A[ch]] += 1
    fixed = {i: base[i] for i in FIX}
    for i, n in fixed.items():
        if n > NMAX: raise ValueError("prefix too long for counts below 100")
        for k in range(26): base[k] += VEC[n][k]
    return [-base[i] for i in VAR], fixed

# Row a says:   sum_b G[a][b][c_b] == target[a]
# i.e.  (letters of kind a contributed by all the number-words) - c_a == -base_a.
G = [[[0] + [VEC[n][VAR[a]] - (n if a == b else 0) for n in range(1, NMAX + 1)]
      for b in RANGE_K] for a in RANGE_K]

# Redundant rows.  Any integer combination of the sixteen rows is implied by
# them, so adding one never loses a solution -- but bounds propagation on the
# combination can see things the separate rows cannot.  The useful ones
# isolate a single family of number-words.  (`families` searches for these.)
FAMILIES = [
    ("g-h+r-u",    "forty"),
    ("-g+h+o-r",   "one, two"),
    ("f-g+h-r",    "five, fifteen (x2), fifty (x2)"),
    ("-g+h",       "three, thirteen, thirty"),
    ("s-x",        "seven, seventeen, seventy, and every plural s"),
    ("-l+v",       "five, seven, seventeen, seventy"),
    ("v-l-s+x",    "five, minus every plural s"),
    ("g-h+t-w-y",  "eight, ten, thirteen .. nineteen"),
    ("t-h-w-y",    "ten, thirteen .. seventeen, nineteen, minus eighty"),
    ("-g+i-x",     "five, nine, thirteen, fifteen, nineteen, thirty, fifty, ninety"),
    ("-g+h-r+u+y", "every tens-word except forty"),
    ("h+n-t+w+y",  "an n-heavy family"),
    ("e-g-h+i-n",  "an e-heavy family"),
]

def _parse_combo(c):
    y = {}
    for sign, l in re.findall(r"([+-]?)([a-z])", c):
        a = VAR.index(A[l]); y[a] = y.get(a, 0) + (-1 if sign == '-' else 1)
    return y

def build_rows(combos):
    ys = [{a: 1 for a in RANGE_K}] + [_parse_combo(c) for c in combos]   # first extra row: total letter count
    rows = list(G)
    for y in ys:
        rows.append([[sum(k * G[a][b][n] for a, k in y.items()) for n in range(NMAX + 1)] for b in RANGE_K])
    return rows, ys

# ---------------------------------------------------------------- solver ----
class Solver:
    """Complete search: branch on the smallest domain, propagate bounds on every row.

    State of a node: (dom, mn, mx, LO, HI)
      dom[b]        tuple of values still possible for variable b
      mn[b][a]      min over dom[b] of row a's term for b   (mx likewise)
      LO[a], HI[a]  sum over b of mn / mx  -- bounds on row a's left-hand side
    A value n of b is impossible in row a if even the most helpful choices of
    all other variables cannot bring the sum to the target.
    """
    def __init__(self, prefix, combos=None, progress=0):
        self.prefix = prefix
        t, self.fixed = setup(prefix)
        self.rows, ys = build_rows([c for c, _ in FAMILIES] if combos is None else combos)
        self.R = range(len(self.rows))
        self.target = list(t) + [sum(k * t[a] for a, k in y.items()) for y in ys]
        self.memo = {}
        self.nodes = 0; self.solutions = []; self.progress = progress

    def bounds(self, b, d):
        r = self.memo.get((b, d))
        if r is None:
            mn = []; mx = []
            for a in self.R:
                g = self.rows[a][b]; vals = [g[n] for n in d]
                mn.append(min(vals)); mx.append(max(vals))
            r = self.memo[(b, d)] = (mn, mx)
        return r

    def initial(self):
        dom = [tuple(range(1, NMAX + 1))] * K
        mn = []; mx = []
        for b in RANGE_K:
            m, M = self.bounds(b, dom[b]); mn.append(m); mx.append(M)
        LO = [sum(mn[b][a] for b in RANGE_K) for a in self.R]
        HI = [sum(mx[b][a] for b in RANGE_K) for a in self.R]
        st = (dom, mn, mx, LO, HI)
        return st if self._fix(st, list(self.R)) else None

    def _fix(self, st, queue):
        """Propagate to a fixed point, in place.  False if some domain empties."""
        dom, mn, mx, LO, HI = st
        target = self.target; rows = self.rows; R = self.R
        inq = [False] * len(rows)
        for a in queue: inq[a] = True
        while queue:
            a = queue.pop(); inq[a] = False
            t = target[a]; lo = LO[a]; hi = HI[a]
            if lo > t or hi < t: return False
            up = t - lo; down = hi - t
            for b in RANGE_K:
                m = mn[b][a]; M = mx[b][a]
                w = M - m
                if w > up or w > down:
                    g = rows[a][b]
                    lo_ok = M - down; hi_ok = m + up
                    d2 = tuple([n for n in dom[b] if lo_ok <= g[n] <= hi_ok])
                    if not d2: return False
                    dom[b] = d2
                    nm, nM = self.bounds(b, d2); om = mn[b]; oM = mx[b]
                    for r in R:
                        x = nm[r] - om[r]; y = nM[r] - oM[r]
                        if x or y:
                            LO[r] += x; HI[r] += y
                            if not inq[r]: inq[r] = True; queue.append(r)
                    mn[b] = nm; mx[b] = nM
                    lo = LO[a]; hi = HI[a]
                    if lo > t or hi < t: return False
                    up = t - lo; down = hi - t
        return True

    def assign(self, st, b, d2):
        dom, mn, mx, LO, HI = st
        dom = dom[:]; mn = mn[:]; mx = mx[:]; LO = LO[:]; HI = HI[:]
        dom[b] = d2
        nm, nM = self.bounds(b, d2); om = mn[b]; oM = mx[b]
        queue = []
        for r in self.R:
            x = nm[r] - om[r]; y = nM[r] - oM[r]
            if x or y:
                LO[r] += x; HI[r] += y; queue.append(r)
        mn[b] = nm; mx[b] = nM
        st = (dom, mn, mx, LO, HI)
        return st if self._fix(st, queue) else None

    def dfs(self, st):
        self.nodes += 1
        if self.progress and self.nodes % self.progress == 0:
            print(f"  ... {self.nodes} nodes, {len(self.solutions)} found", file=sys.stderr, flush=True)
        if st is None: return
        dom = st[0]
        best = -1; bl = NMAX + 1
        for b in RANGE_K:
            l = len(dom[b])
            if 1 < l < bl: best, bl = b, l
        if best < 0:
            sol = dict(self.fixed); sol.update({VAR[b]: dom[b][0] for b in RANGE_K})
            self.solutions.append(sol); return
        for n in dom[best]:
            self.dfs(self.assign(st, best, (n,)))

    def text(self, sol):
        return render(self.prefix, {l: sol[A[l]] for l in LETTERS})

    def solve(self):
        """All autograms for the prefix, each re-checked by verify()."""
        self.dfs(self.initial())
        out = []
        for sol in self.solutions:
            text = self.text(sol); n, bad = verify(text)
            assert n == 26 and not bad, (text, bad)
            out.append(text)
        return sorted(out)

# ------------------------------------------------------------ random walk ----
def walk(prefix, seed=0, max_iter=5_000_000):
    """Randomised fixed-point iteration.  -> (sentence or None, iterations)."""
    rng = random.Random(seed)
    base = [1] * 26
    for ch in (prefix + " and").lower():
        if ch.isalpha(): base[A[ch]] += 1
    counts = [min(base[i] + rng.randint(0, 5), NMAX) for i in range(26)]
    tot = base[:]
    for i in range(26):
        for j, x in enumerate(VEC[counts[i]]): tot[j] += x
    rnd = rng.random; ri = rng.randint
    for it in range(max_iter):
        wrong = [i for i in range(26) if tot[i] != counts[i]]
        if not wrong:
            return render(prefix, {l: counts[A[l]] for l in LETTERS}), it
        for i in wrong:                      # move a random half of the wrong counts
            if rnd() < 0.5:                  # toward the truth (all at once just cycles)
                t = tot[i]
                new = ri(min(counts[i], t), max(counts[i], t)) if rnd() < 0.3 else t
                new = max(1, min(new, NMAX)); old = counts[i]
                if new != old:
                    vo, vn = VEC[old], VEC[new]
                    for j in range(26): tot[j] += vn[j] - vo[j]
                    counts[i] = new
    return None, max_iter

# ------------------------------------------------------- family search ----
def families(max_letters=5, show=40):
    """List +-1 combinations of letter rows that count a sparse family of number-word parts."""
    tokens = ONES[1:] + TENS[2:]
    L = [LETTERS[i] for i in VAR]
    M = {l: [t.count(l) for t in tokens] + [1 if l == 's' else 0] for l in L}
    cols = tokens + ["(plural s)"]
    found = {}
    for k in range(1, max_letters + 1):
        for ls in combinations(L, k):
            for signs in product([1, -1], repeat=k - 1):
                sg = (1,) + signs
                v = [sum(s * M[l][c] for s, l in zip(sg, ls)) for c in range(len(cols))]
                if min(v) < 0: v = [-x for x in v]; sg = tuple(-s for s in sg)
                if min(v) < 0 or max(v) > 2: continue
                name = "".join(("+" if s > 0 else "-") + l for s, l in zip(sg, ls))
                if tuple(v) not in found or len(name) < len(found[tuple(v)]): found[tuple(v)] = name
    res = sorted(found.items(), key=lambda kv: (sum(1 for x in kv[0] if x), len(kv[1]), kv[1]))
    for v, name in res[:show]:
        print(f"{name:12s}", ", ".join(cols[c] + (" x2" if x > 1 else "") for c, x in enumerate(v) if x))

# ------------------------------------------------------------------ CLI ----
def main(argv):
    if len(argv) < 2 or argv[1] not in ("solve", "walk", "verify", "families"):
        print(__doc__); return
    cmd = argv[1]
    if cmd == "solve":
        for prefix in argv[2:]:
            t0 = time.time()
            s = Solver(prefix, progress=100000)
            texts = s.solve()
            print(f"## {prefix!r}: {len(texts)} autogram(s)   [{s.nodes} nodes, {time.time() - t0:.0f}s]", flush=True)
            for x in texts: print(x, flush=True)
    elif cmd == "walk":
        s, it = walk(argv[2], int(argv[3]) if len(argv) > 3 else 0)
        print(s if s else f"no luck in {it} steps (which proves nothing)")
    elif cmd == "verify":
        for line in sys.stdin:
            line = line.strip()
            if not line or line.startswith("#"): continue
            n, bad = verify(line)
            print(("TRUE " if not bad else "FALSE") + f" ({n} claims)  {line[:70]}..." + (f"  {bad}" if bad else ""))
    else:
        families()

if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    main(sys.argv)
