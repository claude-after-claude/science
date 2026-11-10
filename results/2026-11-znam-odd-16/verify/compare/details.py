"""Details behind the comparison that compare.py does not print.

    python3 details.py > details.txt        # needs python-flint; about 10 s

1. Set differences between all six pairs of enumerations (compare.py prints adjacent pairs only).
2. The checker's leaves that are not in session-2's set, with their ten-term prefixes.
3. Session-3: how many tenth-term candidates it enumerates, and how many pass the reachability test
   that its job() applies before solving the last two terms.

Leaves are keyed by the product of their ten terms, as in compare.py, whose --dump mode is reused.
"""
import json
import subprocess
import sys
from itertools import combinations
from math import gcd, prod
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SESSIONS = HERE.parents[1] / "sessions"
ORDER = ["checker", "session-2", "session-3", "session-1b"]


def session_3_candidates():
    sys.path.insert(0, str(SESSIONS / "session-3"))
    import znam_odd
    cand = passed = 0
    for pre, P, a, x0, x1, *_ in znam_odd.jobs(12, True, None):
        for x in range(x0, x1, 2):
            if gcd(x, P) == 1:
                cand += 1
                passed += znam_odd.reachable(P * x, a * x - P, x, 2, True)
    print(json.dumps([cand, passed]))


def main():
    procs = {n: subprocess.Popen([sys.executable, "-B", str(HERE / "compare.py"), "--dump", n],
                                 stdout=subprocess.PIPE, text=True) for n in ORDER}
    s3 = subprocess.Popen([sys.executable, "-B", __file__, "--s3"], stdout=subprocess.PIPE, text=True)
    S = {}
    for n, p in procs.items():
        out, _ = p.communicate()
        assert p.returncode == 0, n
        S[n] = set(json.loads(out))

    print("1. products in A's set and not in B's, all pairs")
    for a, b in combinations(ORDER, 2):
        print(f"   {a} minus {b}: {len(S[a] - S[b])}   |   {b} minus {a}: {len(S[b] - S[a])}")

    print("2. checker leaves not in session-2's set")
    sys.path.insert(0, str(HERE.parent))
    import oddsearch
    tasks, _ = oddsearch.enumerate_prefixes(12, True)
    missing = S["checker"] - S["session-2"]
    for pre, P, _ in tasks:
        if str(P) in missing:
            print("   ", *pre, "| in session-3:", str(P) in S["session-3"], "| in session-1b:", str(P) in S["session-1b"])

    out, _ = s3.communicate()
    cand, passed = json.loads(out)
    print(f"3. session-3: {cand} tenth-term candidates, {passed} pass reachable(.., 2, ..) in job(), "
          f"{cand - passed} discarded before the last two terms are solved")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--s3"]:
        session_3_candidates()
    else:
        main()
