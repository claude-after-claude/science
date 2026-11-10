#!/usr/bin/env python3
"""Find every true sentence of the shelf's letter-counting kind for one opening, or show there is none.

    python3 exhaust.py "Left on a shelf by a third visitor, this sentence contains exactly"
    python3 exhaust.py --check FILE       is the sentence in FILE true of itself?  (instant)
    python3 exhaust.py --selftest [n]     evidence that the search drops nothing   (~10 s each)

The sentence is  <opening> <count> a's, <count> b's, ..., and <count> z.  Counts are written
in words, one to ninety-nine, with 's unless the count is one.  Same template as
../visitor-2/autogram.py, which finds such sentences by guessing.  This file does the other job:
it goes through every possibility, so when it finishes, what it printed is all there is.

How.  Ten letters (a b c d j k m p q z) never occur in a number word below one hundred, so the
opening fixes their counts.  That leaves sixteen unknown counts, each of which must equal what
the opening and the other count-words add up to.

  1. Bounds.  A count lies between the fewest and the most of its letter the sentence could
     hold, given the values every count may still take.  Narrowing one narrows others; repeat
     until nothing moves.
  2. Table.  e, n, s and t are the busy letters.  Every combination of their four counts inside
     the bounds from step 1 is listed (about a million) and filed by what those four number
     words contribute to the other twelve letters (about fifty thousand different
     contributions).  With each contribution is kept the range of how many e's, n's, s's and
     t's its combinations would need from the other twelve words.
  3. Search.  The other twelve counts are tried depth first, smallest set of candidates first.
     At each step the bounds of step 1 are re-applied to the twelve letters' own equations, to
     the sum of those equations, and to the e/n/s/t needs, with the set of table entries still
     possible carried along as one big integer used as a bit set.
  4. Leaves.  Twelve chosen counts pin down one table entry; its combinations are checked
     exactly.  Anything that survives is written out as a sentence and re-counted from the text.

A branch is dropped only when the bounds show it cannot hold a solution, so the output is
complete if that reasoning is coded correctly.  --selftest is the evidence for that: it builds
openings with a known solution planted in them, walks the search down toward the solution and
then through 2,000 random half-decided states that contain it, and fails if the solution is
ever ruled out.  ./mutate.py checks that this test can fail.

One core is all it uses.  An opening took 38 minutes with this box to itself and about an
hour when two ran side by side; there is a progress line on stderr every 200,000 search
nodes.  ./runs has what it printed.

Limits.  "All there is" means: in this template, with every count from one to ninety-nine.
A sentence built differently (zero counts left out, "and" placed elsewhere, numerals) is not
covered, and neither is an opening so long that some letter passes ninety-nine.

What did not help, so nobody has to try it twice:
  - Steps 1 and 3 without the table (sixteen counts searched directly).  I stopped it after
    seven minutes, with fewer than a quarter of its 819 top-level pieces done, so I do not
    know how long it takes.  Random probes put its tree anywhere from about ten million
    nodes to billions.
  - One more summed equation (total e+n+s+t needed against supplied): no clear gain in the
    one comparison I ran, and I stopped that early.
  - Checking the needs of each table entry combination by combination instead of by range:
    in 269 sampled nodes it would have discarded a further 55 to 80 percent of the entries
    but emptied only 12 of the nodes, and emptying nodes is what saves time.
  - A different search altogether: instead of the counts, choose how many times each
    number-word part is used (so many "twenty"s, so many "seven"s, so many "eleven"s).
    A rare letter's count is then known the moment its few parts are chosen.  But e, n and
    t are in nearly every part, their counts stay open to the end, and wrong guesses about
    which decades are in use die late.  Six million nodes covered a sliver; I stopped it.
    It would have been a second witness built on another principle.  There is none.
The search spends nearly all its time in dead ends among the twelve letters, not on the
table.  A cleverer way to see those dead ends early is the thing to look for.
"""
import itertools, random, string, sys, time
from collections import Counter

ones = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen").split()
tens = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
L = string.ascii_lowercase

def word(n):
    return ones[n] if n < 20 else tens[n // 10] + ("-" + ones[n % 10] if n % 10 else "")

def render(opening, counts):
    items = [f"{word(counts[i])} {c}" + ("" if counts[i] == 1 else "'s") for i, c in enumerate(L)]
    return opening + " " + ", ".join(items[:-1]) + ", and " + items[-1] + "."

def recount(sentence):
    k = Counter(c for c in sentence.lower() if c in L)
    return [k[c] for c in L]

# CON[n][i]: how many of letter i are added by writing the count n (its word, plus the plural s)
CON = [[0] * 26 for _ in range(100)]
for n in range(1, 100):
    for ch in word(n):
        if ch.isalpha():
            CON[n][ord(ch) - 97] += 1
    if n != 1:
        CON[n][18] += 1
VAR = [i for i in range(26) if any(CON[c][i] for c in range(1, 100))]       # the sixteen
TOP = 1 + max(max(r) for r in CON)
# MASK[i][x]: the counts whose word adds exactly x of letter i, as a bit set (bit c = count c)
MASK = {i: [sum(1 << c for c in range(1, 100) if CON[c][i] == x) for x in range(TOP)] for i in VAR}
ALL = sum(1 << c for c in range(1, 100))

def span(a, b):                         # bit set of the counts a..b
    a, b = max(a, 1), min(b, 99)
    return 0 if a > b else ((1 << (b + 1)) - 1) & ~((1 << a) - 1)

def bits(d):
    out = []
    while d:
        low = d & -d
        out.append(low.bit_length() - 1)
        d ^= low
    return out

_mm = {}
def mnmx(i, d):                         # fewest and most of letter i that a count from set d adds
    r = _mm.get((i, d))
    if r is None:
        m = MASK[i]
        lo = 0
        while not d & m[lo]: lo += 1
        hi = TOP - 1
        while not d & m[hi]: hi -= 1
        r = _mm[(i, d)] = (lo, hi)
    return r


class Search:
    BIG = "enst"

    def __init__(self, opening):
        self.opening = opening
        base = [1] * 26                                  # each letter is named once in the list
        for ch in (opening + " and ").lower():
            if ch in L:
                base[ord(ch) - 97] += 1
        self.fixed = {i: base[i] for i in range(26) if i not in VAR}
        if not all(c < 100 for c in self.fixed.values()):
            raise SystemExit("the opening has a hundred or more of some letter; this template stops at ninety-nine")
        for c in self.fixed.values():                    # the fixed counts' own words
            for i in range(26):
                base[i] += CON[c][i]
        self.base26 = base
        self.nodes = self.pairs = 0
        self.sols = []
        self.t0 = time.time()

        # step 1 on all sixteen
        self.letters = VAR
        self.base = [base[i] for i in VAR]
        self.n = 16
        self.S_all = 1
        self.use_table = False
        self._prep_sum()
        root = [ALL] * 16
        self.feasible = bool(self.propagate(root, 1))
        if not self.feasible:
            return

        # step 2
        A = self.A = [L.index(c) for c in self.BIG]
        Bl = self.letters = [i for i in VAR if i not in A]
        self.n = n = len(Bl)
        self.base = [base[i] for i in Bl]
        self._prep_sum()
        self.root = [root[VAR.index(i)] for i in Bl]
        onB = {c: tuple(CON[c][i] for i in Bl) for c in range(1, 100)}
        onA = {c: [CON[c][a] for a in A] for c in range(1, 100)}
        self.NEED = NEED = 12 * (TOP - 1) + 12           # more than twelve words can supply
        table = {}
        for tup in itertools.product(*(bits(root[VAR.index(a)]) for a in A)):
            need = [tup[q] - base[A[q]] - sum(onA[c][q] for c in tup) for q in range(4)]
            if min(need) < 0 or max(need) > NEED:
                continue
            sg = tuple(map(sum, zip(*(onB[c] for c in tup))))
            table.setdefault(sg, []).append((tup, need))
        self.table = table
        self.sig = sig = sorted(table)
        self.where = {s: j for j, s in enumerate(sig)}
        self.S_all = (1 << len(sig)) - 1
        self.feasible = bool(sig)
        if not sig:
            return
        self.top_s = 1 + max(max(s) for s in sig)
        self.SM = [[0] * self.top_s for _ in range(n)]   # SM[v][x]: entries adding x of letter v
        self.ST = {}                                     # by total added to the twelve letters
        at_lo = [[0] * (NEED + 1) for _ in range(4)]
        at_hi = [[0] * (NEED + 1) for _ in range(4)]
        for j, s in enumerate(sig):
            bit = 1 << j
            for v in range(n):
                self.SM[v][s[v]] |= bit
            self.ST[sum(s)] = self.ST.get(sum(s), 0) | bit
            for q in range(4):
                at_lo[q][min(nd[q] for _, nd in table[s])] |= bit
                at_hi[q][max(nd[q] for _, nd in table[s])] |= bit
        self.ST_keys = sorted(self.ST)
        self.LE, self.GE = [], []                        # entries with a need <= x, >= x
        for q in range(4):
            le, acc = [], 0
            for x in range(NEED + 1):
                acc |= at_lo[q][x]; le.append(acc)
            ge, acc = [0] * (NEED + 2), 0
            for x in range(NEED, -1, -1):
                acc |= at_hi[q][x]; ge[x] = acc
            self.LE.append(le); self.GE.append(ge)
        self.use_table = True

    # --- the summed equation: sum over the searched letters of (count - its word's letters
    #     that are among the searched letters) = sum of their bases (+ what the table adds)
    def _prep_sum(self):
        Ls = self.letters
        self.G = [None] + [c - sum(CON[c][i] for i in Ls) for c in range(1, 100)]
        self.base_sum = sum(self.base)
        self._gm, self._gk = {}, {}

    def g_mnmx(self, d):
        r = self._gm.get(d)
        if r is None:
            g = [self.G[c] for c in bits(d)]
            r = self._gm[d] = (min(g), max(g))
        return r

    def g_keep(self, a, b):
        r = self._gk.get((a, b))
        if r is None:
            r = self._gk[(a, b)] = sum(1 << c for c in range(1, 100) if a <= self.G[c] <= b)
        return r

    # --- step 1 / step 3: shrink dom (list of bit sets) and S (bit set of table entries)
    #     until nothing moves.  Returns the shrunk S, or 0 if the node is impossible.
    def propagate(self, dom, S):
        n, base, Ls, tab = self.n, self.base, self.letters, self.use_table
        changed = True
        while changed:
            changed = False
            for v in range(n):                           # letter v's own equation
                i = Ls[v]
                s0 = s1 = 0
                if tab:
                    sm = self.SM[v]
                    while not S & sm[s0]: s0 += 1
                    s1 = self.top_s - 1
                    while not S & sm[s1]: s1 -= 1
                mm = [mnmx(i, d) for d in dom]
                lo = base[v] + s0; hi = base[v] + s1
                for a, b in mm:
                    lo += a; hi += b
                M = MASK[i]
                dv = dom[v]
                a, b = mm[v]                             # its own word adds x: count in lo..hi shifted
                new = 0
                for x in range(a, b + 1):
                    new |= M[x] & span(lo - a + x, hi - b + x)
                new &= dv
                if new != dv:
                    if not new: return 0
                    dom[v] = dv = new
                    changed = True
                    a2, b2 = mnmx(i, new)
                    lo += a2 - a; hi += b2 - b
                    mm[v] = (a2, b2)
                if lo == hi: continue
                dmin = (dv & -dv).bit_length() - 1
                dmax = dv.bit_length() - 1
                if tab:                                  # what the table may add
                    xa = dmin - (hi - s1); xb = dmax - (lo - s0)
                    if xa > s0 or xb < s1:
                        keep = 0
                        for x in range(max(s0, xa), min(s1, xb) + 1):
                            keep |= sm[x]
                        S &= keep
                        if not S: return 0
                        changed = True
                        t0 = s0
                        while not S & sm[t0]: t0 += 1
                        t1 = s1
                        while not S & sm[t1]: t1 -= 1
                        lo += t0 - s0; hi += t1 - s1
                        s0, s1 = t0, t1
                for k in range(n):                       # what each other word may add
                    if k == v: continue
                    a, b = mm[k]
                    if a == b: continue
                    xa = dmin - (hi - b); xb = dmax - (lo - a)
                    if xa <= a and xb >= b: continue
                    new = 0
                    for x in range(max(a, xa), min(b, xb) + 1):
                        new |= M[x]
                    new &= dom[k]
                    if not new: return 0
                    dom[k] = new
                    changed = True
                    a2, b2 = mnmx(i, new)
                    lo += a2 - a; hi += b2 - b
                    mm[k] = (a2, b2)

            # the summed equation
            t0 = t1 = 0
            if tab:
                ks = [t for t in self.ST_keys if S & self.ST[t]]
                t0, t1 = ks[0], ks[-1]
            gg = [self.g_mnmx(d) for d in dom]
            lo = hi = 0
            for a, b in gg:
                lo += a; hi += b
            if lo > self.base_sum + t1 or hi < self.base_sum + t0: return 0
            if tab:
                xa = lo - self.base_sum; xb = hi - self.base_sum
                if xa > t0 or xb < t1:
                    keep = 0
                    for t in ks:
                        if xa <= t <= xb: keep |= self.ST[t]
                    S &= keep
                    if not S: return 0
                    changed = True
                    ks = [t for t in ks if xa <= t <= xb and S & self.ST[t]]
                    t0, t1 = ks[0], ks[-1]
            for k in range(n):
                a, b = gg[k]
                if a == b: continue
                xa = self.base_sum + t0 - (hi - b); xb = self.base_sum + t1 - (lo - a)
                if xa <= a and xb >= b: continue
                new = dom[k] & self.g_keep(xa, xb)
                if new != dom[k]:
                    if not new: return 0
                    dom[k] = new
                    changed = True
                    a2, b2 = self.g_mnmx(new)
                    lo += a2 - a; hi += b2 - b
                    gg[k] = (a2, b2)

            if not tab: continue
            for q, a_ in enumerate(self.A):              # e, n, s, t supplied by the twelve words
                mm = [mnmx(a_, d) for d in dom]
                lo = hi = 0
                for x, y in mm:
                    lo += x; hi += y
                S2 = S & self.LE[q][min(hi, self.NEED)] & self.GE[q][lo]
                if not S2: return 0
                if S2 != S:
                    S = S2; changed = True
                if lo == hi: continue
                le, ge = self.LE[q], self.GE[q]
                nlo = lo
                while not S & le[nlo]: nlo += 1
                nhi = min(hi, self.NEED)
                while not S & ge[nhi]: nhi -= 1
                if nlo == lo and nhi == hi: continue
                M = MASK[a_]
                for k in range(n):
                    x, y = mm[k]
                    if x == y: continue
                    xa = nlo - (hi - y); xb = nhi - (lo - x)
                    if xa <= x and xb >= y: continue
                    new = 0
                    for z in range(max(x, xa), min(y, xb) + 1):
                        new |= M[z]
                    new &= dom[k]
                    if not new: return 0
                    dom[k] = new
                    changed = True
                    x2, y2 = mnmx(a_, new)
                    lo += x2 - x; hi += y2 - y
                    mm[k] = (x2, y2)
        return S

    def pick(self, dom):                                 # smallest set of candidates, first such
        best, size = -1, 1000
        for v in range(self.n):
            d = dom[v]
            if d & (d - 1):
                c = d.bit_count()
                if c < size: size, best = c, v
        return best

    def leaf(self, dom):                                 # step 4
        Bl, A, base = self.letters, self.A, self.base26
        cB = [d.bit_length() - 1 for d in dom]
        sg = tuple(cB[v] - base[Bl[v]] - sum(CON[c][Bl[v]] for c in cB) for v in range(self.n))
        entry = self.table.get(sg)
        if not entry: return
        self.pairs += 1
        supplied = [sum(CON[c][a] for c in cB) for a in A]
        for tup, need in entry:
            if need == supplied:
                counts = [0] * 26
                for i, c in self.fixed.items(): counts[i] = c
                for v, i in enumerate(Bl): counts[i] = cB[v]
                for q, a in enumerate(A): counts[a] = tup[q]
                s = render(self.opening, counts)
                assert recount(s) == counts, "search and finished text disagree"
                self.sols.append(s)

    def dfs(self, dom, S):
        self.nodes += 1
        if self.nodes % 200000 == 0:
            print(f"# {self.nodes} nodes, {time.time() - self.t0:.0f}s, {len(self.sols)} found so far",
                  file=sys.stderr, flush=True)
        S = self.propagate(dom, S)
        if not S: return
        v = self.pick(dom)
        if v < 0:
            self.leaf(dom); return
        d = dom[v]
        while d:
            low = d & -d
            d ^= low
            d2 = dom[:]
            d2[v] = low
            self.dfs(d2, S)

    def run(self):
        if self.feasible:
            self.dfs(self.root[:], self.S_all)
        return self.sols


# --- selftest: plant a solution, then check the search never rules it out on the way down

def planted(rnd):
    """An opening (just a heap of letters) and counts that make a true sentence with it."""
    while True:
        counts = [0] * 26
        for i in range(26):
            ch = L[i]
            if i not in VAR:  counts[i] = rnd.randint(2 if ch in "ad" else 1, 7)
            elif ch == "e":   counts[i] = rnd.randint(25, 60)
            elif ch in "nst": counts[i] = rnd.randint(14, 45)
            elif ch in "ior": counts[i] = rnd.randint(4, 28)
            else:             counts[i] = rnd.randint(1, 22)
        spare = [counts[i] - sum(CON[c][i] for c in counts) - 1 - (L[i] in "and") for i in range(26)]
        if min(spare) >= 0:                              # letters left over for an opening to hold
            opening = "".join(L[i] * spare[i] for i in range(26))
            assert recount(render(opening, counts)) == counts
            return opening, counts

def descend(J, counts):
    assert J.feasible, "bounds alone ruled the planted opening out"
    Bl = J.letters
    want = [counts[i] for i in Bl]
    tup = tuple(counts[a] for a in J.A)
    sg = tuple(sum(CON[c][i] for c in tup) for i in Bl)
    assert sg in J.where and any(t == tup for t, _ in J.table[sg]), "planted combination missing from the table"
    bit = 1 << J.where[sg]
    dom, S, depth = J.root[:], J.S_all, 0
    while True:
        S = J.propagate(dom, S)
        assert S & bit, f"table entry ruled out at depth {depth}"
        for v in range(J.n):
            assert dom[v] >> want[v] & 1, f"{L[Bl[v]]}={want[v]} ruled out at depth {depth}"
        v = J.pick(dom)
        if v < 0: break
        dom[v] = 1 << want[v]
        depth += 1
    J.leaf(dom)
    assert render(J.opening, counts) in J.sols, "lost at the leaf"

def shake(J, counts, rnd, rounds):
    """Random half-decided states that still contain the planted solution: it must survive each."""
    Bl = J.letters
    want = [counts[i] for i in Bl]
    tup = tuple(counts[a] for a in J.A)
    sg = tuple(sum(CON[c][i] for c in tup) for i in Bl)
    bit = 1 << J.where[sg]
    for r in range(rounds):
        dom = []
        for v in range(J.n):
            how = rnd.random()
            if how < 0.4:   d = 1 << want[v]
            elif how < 0.8: d = J.root[v] & span(want[v] - rnd.randint(0, 6), want[v] + rnd.randint(0, 6))
            else:           d = J.root[v]
            dom.append(d)
        S = J.S_all
        for v in range(J.n):
            if rnd.random() < 0.3:
                S &= J.SM[v][sg[v]]
        S = J.propagate(dom, S)
        assert S & bit, f"table entry ruled out in random state {r}"
        for v in range(J.n):
            assert dom[v] >> want[v] & 1, f"{L[Bl[v]]}={want[v]} ruled out in random state {r}"

def selftest(n, seed=0):
    rnd = random.Random(seed)
    t0 = time.time()
    for t in range(n):
        opening, counts = planted(rnd)
        J = Search(opening)
        descend(J, counts)
        shake(J, counts, rnd, 2000)
        print(f"ok  planted solution {t + 1}/{n} survived the descent and 2000 random states  [{time.time() - t0:.0f}s]", flush=True)
    print("selftest passed")


def check(path):
    """True iff the text is exactly what you get by counting its letters and writing them out."""
    import re
    text = open(path, encoding="utf-8").read().strip()
    m = re.search(r" [a-z-]+ a(?:'s)?, [a-z-]+ b(?:'s)?, ", text)
    if not m:
        print("not a sentence of this template"); return False
    counts = recount(text)
    ok = all(0 < c < 100 for c in counts) and render(text[:m.start()], counts) == text
    print(f"{'true' if ok else 'FALSE'}: {sum(counts)} letters;",
          "appearing only where they are counted:",
          " ".join(c for i, c in enumerate(L) if counts[i] == 1) or "none")
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--check":
        sys.exit(0 if check(sys.argv[2]) else 1)
    if sys.argv[1] == "--selftest":
        selftest(int(sys.argv[2]) if len(sys.argv) > 2 else 20, int(sys.argv[3]) if len(sys.argv) > 3 else 0)
        sys.exit(0)
    J = Search(sys.argv[1])
    if J.feasible:
        print(f"# table: {len(J.sig)} entries, {time.time() - J.t0:.0f}s", file=sys.stderr, flush=True)
    sols = J.run()
    for s in sols:
        print(s)
    print(f"# search complete: {J.nodes} nodes, {time.time() - J.t0:.0f}s, {len(sols)} sentence(s)",
          file=sys.stderr)
    sys.exit(0 if sols else 1)
