#!/usr/bin/env python3
"""Break exhaust.py on purpose, eighteen ways, and see whether its selftest notices.

    python3 mutate.py            (a few minutes; writes only to a temporary directory)

exhaust.py claims to miss nothing.  Its selftest is the evidence, and a test that cannot fail
is no evidence.  Each entry below changes one line, nearly always so that the pruning discards
slightly too much, then runs the selftest on the broken copy.  "caught" is the good outcome.

When I left, seventeen were caught.  The one MISSED is the last: a combination of e, n, s, t
counts that needs none of one of those letters from the other twelve number words.  No planted
case reaches that corner (I tried 200,000 random draws for each of e, n and t with the twelve
words restricted to ones lacking the letter, and none made a sentence), so that line of
exhaust.py is right by reading, not by test.
"""
import os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE / "exhaust.py").read_text()
OTHERS = """                    xa = dmin - (hi - b); xb = dmax - (lo - a)
                    if xa <= a and xb >= b: continue
                    new = 0
                    for x in range(max(a, xa), min(b, xb) + 1):
                        new |= M[x]
                    new &= dom[k]"""
mutants = [
 ("a letter's equation, other words: lower bound one too high",
  OTHERS, OTHERS.replace("xa = dmin - (hi - b);", "xa = dmin - (hi - b) + 1;")),
 ("a letter's equation, other words: upper bound one too low",
  OTHERS, OTHERS.replace("xb = dmax - (lo - a)", "xb = dmax - (lo - a) - 1")),
 ("a letter's equation, own count: upper bound one too low",
  "new |= M[x] & span(lo - a + x, hi - b + x)", "new |= M[x] & span(lo - a + x, hi - b + x - 1)"),
 ("a letter's equation, own count: lower bound one too high",
  "new |= M[x] & span(lo - a + x, hi - b + x)", "new |= M[x] & span(lo - a + x + 1, hi - b + x)"),
 ("a letter's equation, table: upper bound one too low",
  "xa = dmin - (hi - s1); xb = dmax - (lo - s0)", "xa = dmin - (hi - s1); xb = dmax - (lo - s0) - 1"),
 ("a letter's equation, table: lower bound one too high",
  "xa = dmin - (hi - s1); xb = dmax - (lo - s0)", "xa = dmin - (hi - s1) + 1; xb = dmax - (lo - s0)"),
 ("summed equation: gives up one too early",
  "if lo > self.base_sum + t1 or hi < self.base_sum + t0: return 0",
  "if lo >= self.base_sum + t1 or hi < self.base_sum + t0: return 0"),
 ("summed equation, table: window one too narrow",
  "xa = lo - self.base_sum; xb = hi - self.base_sum", "xa = lo - self.base_sum + 1; xb = hi - self.base_sum"),
 ("summed equation, words: lower bound one too high",
  "xa = self.base_sum + t0 - (hi - b); xb = self.base_sum + t1 - (lo - a)",
  "xa = self.base_sum + t0 - (hi - b) + 1; xb = self.base_sum + t1 - (lo - a)"),
 ("summed equation, words: upper bound one too low",
  "xa = self.base_sum + t0 - (hi - b); xb = self.base_sum + t1 - (lo - a)",
  "xa = self.base_sum + t0 - (hi - b); xb = self.base_sum + t1 - (lo - a) - 1"),
 ("needs, table: upper end one too tight",
  "S2 = S & self.LE[q][min(hi, self.NEED)] & self.GE[q][lo]",
  "S2 = S & self.LE[q][min(hi, self.NEED) - 1] & self.GE[q][lo]"),
 ("needs, table: lower end one too tight",
  "S2 = S & self.LE[q][min(hi, self.NEED)] & self.GE[q][lo]",
  "S2 = S & self.LE[q][min(hi, self.NEED)] & self.GE[q][lo + 1]"),
 ("needs, words: upper bound one too low",
  "xa = nlo - (hi - y); xb = nhi - (lo - x)", "xa = nlo - (hi - y); xb = nhi - (lo - x) - 1"),
 ("needs, words: lower bound one too high",
  "xa = nlo - (hi - y); xb = nhi - (lo - x)", "xa = nlo - (hi - y) + 1; xb = nhi - (lo - x)"),
 ("needs: a table entry's largest need recorded as its smallest",
  "at_hi[q][max(nd[q] for _, nd in table[s])] |= bit", "at_hi[q][min(nd[q] for _, nd in table[s])] |= bit"),
 ("bit sets: a range of counts loses its top value",
  "return 0 if a > b else ((1 << (b + 1)) - 1) & ~((1 << a) - 1)",
  "return 0 if a > b else ((1 << b) - 1) & ~((1 << a) - 1)"),
 ("number words: the plural s dropped from two instead of from one",
  "    if n != 1:\n        CON[n][18] += 1", "    if n != 2:\n        CON[n][18] += 1"),
 ("table: combinations needing none of a letter thrown away",
  "if min(need) < 0 or max(need) > NEED:", "if min(need) < 1 or max(need) > NEED:"),
]

if __name__ == "__main__":
    missed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, old, new in mutants:
            assert src.count(old) == 1 and old != new, f"exhaust.py has changed; cannot apply: {name}"
            path = os.path.join(tmp, "broken.py")
            Path(path).write_text(src.replace(old, new))
            r = subprocess.run([sys.executable, path, "--selftest", "4"], capture_output=True, text=True)
            why = (r.stderr.strip().splitlines() or [""])[-1].replace("AssertionError: ", "")
            missed += r.returncode == 0
            print(("caught  " if r.returncode else "MISSED  ") + name + (f"  [{why}]" if r.returncode else ""), flush=True)
    print(f"\n{len(mutants) - missed} of {len(mutants)} caught")
