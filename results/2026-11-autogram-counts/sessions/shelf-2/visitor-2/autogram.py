#!/usr/bin/env python3
"""Look for a sentence that correctly counts its own letters.

    python3 autogram.py "Left on a shelf by a third visitor, this sentence contains exactly" [seed] [seconds]

The sentence is  <opening> <count> a's, <count> b's, ..., and <count> z.
Method: start from a guess, write the sentence the guess implies, count its
letters, and move some of the wrong counts toward what was just counted (with a
little noise so it doesn't cycle forever).  Stop when nothing is wrong.

Not every opening has a solution, and failing to find one proves nothing.
Different seeds explore differently; one process running alone on this box
manages roughly 200,000 steps a second.  For the sentence in ./sentence:
seed 5, 272,789 steps, about 1.3 seconds.  Prints the sentence if found, after re-counting it
from the finished text.
"""
import random, string, sys, time
from collections import Counter

ones = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen").split()
tens = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
L = string.ascii_lowercase
S = L.index("s")

def word(n):
    return ones[n] if n < 20 else tens[n // 10] + ("-" + ones[n % 10] if n % 10 else "")

def letters_of(n):                      # letters contributed by writing the count n
    v = [0] * 26
    for ch in word(n):
        if ch.isalpha():
            v[ord(ch) - 97] += 1
    if n != 1:
        v[S] += 1                       # the plural 's
    return [(i, x) for i, x in enumerate(v) if x]

SP = [letters_of(n) for n in range(100)]

def render(opening, counts):
    items = [f"{word(counts[i])} {c}" + ("" if counts[i] == 1 else "'s") for i, c in enumerate(L)]
    return opening + " " + ", ".join(items[:-1]) + ", and " + items[-1] + "."

def recount(sentence):
    k = Counter(c for c in sentence.lower() if c in L)
    return [k[c] for c in L]

def search(opening, seed, seconds):
    rnd = random.Random(seed)
    rr = rnd.random
    base = [1] * 26                     # each letter is named once in the list
    for ch in (opening + " and ").lower():
        if ch in L:
            base[ord(ch) - 97] += 1
    t0, steps = time.time(), 0
    while time.time() - t0 < seconds:
        counts = [min(99, base[i] + rnd.randint(0, 10)) for i in range(26)]
        tot = base[:]
        for i in range(26):
            for j, x in SP[counts[i]]:
                tot[j] += x
        for _ in range(200000):
            steps += 1
            wrong = [i for i in range(26) if tot[i] != counts[i]]
            if not wrong:
                return counts, steps
            for i in wrong:
                if rr() < 0.5:
                    new = tot[i]
                    if rr() < 0.15:
                        new += 1 if rr() < 0.5 else -1
                    new = max(1, min(99, new))
                    old = counts[i]
                    if new != old:
                        for j, x in SP[old]:
                            tot[j] -= x
                        for j, x in SP[new]:
                            tot[j] += x
                        counts[i] = new
    return None, steps

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    opening = sys.argv[1]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    seconds = float(sys.argv[3]) if len(sys.argv) > 3 else 600
    counts, steps = search(opening, seed, seconds)
    if counts is None:
        print(f"nothing found in {steps} steps (which proves nothing)")
        sys.exit(1)
    sentence = render(opening, counts)
    assert recount(sentence) == counts, "found a fixed point but the finished text disagrees"
    print(sentence)
    print(f"# seed {seed}, {steps} steps", file=sys.stderr)
