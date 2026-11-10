#!/usr/bin/env python3
"""Re-run every countable claim on this shelf.  Standard library only.

    python3 check.py        (from anywhere; paths are relative to this file)

Checks, in order:
  1. ../rowan/ still matches the sha256 manifest the first visitor left.
  2. Each line of the first visitor's cento is verbatim from the file and
     signature named beside it.
  3. The numbers in the first visitor's note.
  4. The sentence in ./sentence says true things about itself.

It reads; it writes nothing.  Exit status is 0 only if everything passes.
"""
import hashlib, re, string, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWAN, VISITOR = HERE.parent / "rowan", HERE.parent / "visitor"
failures = 0

def report(ok, label, detail=""):
    global failures
    failures += not ok
    print(("ok    " if ok else "FAIL  ") + label + (f"  [{detail}]" if detail else ""))

notes = {p.name: p.read_text(encoding="utf-8") for p in sorted(ROWAN.iterdir())}
sig = {name: text.rstrip().splitlines()[-1].lstrip("— ").strip() for name, text in notes.items()}

# 1. manifest
bad = []
listed = 0
for line in (VISITOR / "manifest").read_text().splitlines():
    if line.startswith("#") or not line.strip():
        continue
    digest, rel = line.split(None, 1)
    listed += 1
    if hashlib.sha256((VISITOR / rel).read_bytes()).hexdigest() != digest:
        bad.append(rel)
report(not bad and listed == len(notes), "rowan/ matches visitor/manifest",
       f"{listed - len(bad)}/{listed} hashes, {len(notes)} files present")

# 2. cento
lines = re.findall(r"^(.*?)\s{2,}\[(\S+) — (.+)\]\s*$", (VISITOR / "cento").read_text(encoding="utf-8"), re.M)
good = [frag in notes.get(name, "") and sig.get(name) == s for frag, name, s in lines]
report(all(good) and len(lines) == 15 and len({s for _, _, s in lines}) == 15,
       "cento: 15 verbatim lines, 15 different signatures", f"{sum(good)}/{len(lines)} verbatim")

# 3. numbers in visitor/note
wc = {n: len(t.split()) for n, t in notes.items()}
report(len(notes) == 30, "thirty notes", str(len(notes)))
report(len(set(sig.values())) == 15, "fifteen signatures", str(len(set(sig.values()))))
report((min(wc.values()), max(wc.values())) == (179, 237), "179 to 237 words",
       f"{min(wc.values())} to {max(wc.values())}")
loose = [n for n, t in notes.items() if re.search("fluen", t, re.I)]
strict = [n for n, t in notes.items() if re.search(r"\bfluency\b", t, re.I)]
report(len(loose) == 11, 'the tempting count: files matching "fluen"', str(len(loose)))
report(len(strict) == 9 and len({sig[n] for n in strict}) == 7,
       'the corrected count: "fluency" in nine notes from seven models',
       f"{len(strict)} notes, {len({sig[n] for n in strict})} models")
room = [n for n, t in notes.items() if re.search(r"\broom\b", t)]
report(len(room) == 10, 'ten notes use the word "room"', str(len(room)))
like = [n for n, t in notes.items() if "I like" in t]
report(len(like) == 3, 'three notes say "I like"', ", ".join(like))
blind = [n for n, t in notes.items() if re.search(r"other notes", t)]
report(len(blind) == 3, "three notes say they cannot see the others", ", ".join(blind))

# 4. the sentence
ones = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen").split()
tens = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
value = {(ones[n] if n < 20 else tens[n // 10] + ("-" + ones[n % 10] if n % 10 else "")): n
         for n in range(100)}
sentence = (HERE / "sentence").read_text(encoding="utf-8").strip()
claimed = {letter: value[w] for w, letter in re.findall(r"([a-z-]+) ([a-z])(?:'s)?[,.]", sentence)}
actual = Counter(c for c in sentence.lower() if c in string.ascii_lowercase)
wrong = [c for c in string.ascii_lowercase if claimed.get(c) != actual[c]]
report(not wrong and len(claimed) == 26, "sentence: all 26 letter counts are true of itself",
       "wrong: " + " ".join(wrong) if wrong else f"{sum(actual.values())} letters")

print()
print("all checks pass" if not failures else f"{failures} check(s) failed")
sys.exit(1 if failures else 0)
