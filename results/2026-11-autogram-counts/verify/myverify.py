"""Independent autogram check: own number-word table, own parser, own letter count. Imports nothing from the code under test."""
import string

AZ = string.ascii_lowercase
_UNITS = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
_TEENS = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
WORD2N = {}
for i, u in enumerate(_UNITS): WORD2N[u] = i + 1
for i, t in enumerate(_TEENS): WORD2N[t] = 10 + i
for i, t in enumerate(_TENS):
    WORD2N[t] = 20 + 10 * i
    for j, u in enumerate(_UNITS): WORD2N[t + "-" + u] = 20 + 10 * i + j + 1
N2WORD = {n: w for w, n in WORD2N.items()}
assert sorted(N2WORD) == list(range(1, 100))


def letter_counts(text):
    low = text.lower()
    return [low.count(c) for c in AZ]


def vec52(counts):
    assert len(counts) == 26 and all(0 <= c <= 99 for c in counts)
    return "".join("%02d" % c for c in counts)


def my_render(opening, counts):
    items = ["%s %s%s" % (N2WORD[c], l, "" if c == 1 else "'s") for l, c in zip(AZ, counts)]
    return (opening + " " if opening else "") + ", ".join(items[:-1]) + " and " + items[-1] + "."


def check(sentence, opening):
    """-> dict(ok, claims, actual, vec, oxford, problems). ok means: 26 well-formed claims in a..z order, each equal
    to the real letter count of the whole sentence."""
    problems = []
    if opening:
        if not sentence.startswith(opening + " "): problems.append("does not start with the opening")
        rest = sentence[len(opening) + 1:]
    else:
        rest = sentence
    if not rest.endswith("."): problems.append("no final period")
    rest = rest[:-1]
    oxford = ", and " in rest
    head, sep, last = rest.rpartition(", and " if oxford else " and ")
    items = head.split(", ") + [last]
    claims = []
    if len(items) != 26: problems.append("%d items, not 26" % len(items))
    for k, item in enumerate(items):
        parts = item.split(" ")
        if len(parts) != 2 or parts[0] not in WORD2N:
            problems.append("bad item %r" % item); continue
        n = WORD2N[parts[0]]
        want = AZ[k] if k < 26 else "?"
        if parts[1] != (want if n == 1 else want + "'s"): problems.append("bad label in %r" % item)
        claims.append(n)
    actual = letter_counts(sentence)
    if claims != actual: problems.append("claims differ from letter count")
    return dict(ok=not problems, claims=claims, actual=actual, vec=vec52(actual) if max(actual) <= 99 else None,
                oxford=oxford, problems=problems)
