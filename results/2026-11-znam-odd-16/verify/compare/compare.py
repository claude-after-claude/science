"""Compare the leaves of four independent enumerations of the twelve-term odd search.

    python3 compare.py            # prints the table stored in output.txt

A leaf is a ten-term prefix whose last two terms are left to solve; it is identified by the
product of its ten terms. The product is not a unique key for a leaf, so the set sizes are a
little below the leaf counts. Each implementation is imported unmodified from the repo, in its
own Python process, because several of them ship a module named `znam`.

The checker (../oddsearch.py) needs python-flint (`pip install python-flint`). Without it, its
row is skipped and only the three session enumerations are compared.
"""
import json
import subprocess
import sys
from math import gcd, prod
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SESSIONS = HERE.parents[1] / "sessions"
ORDER = ["checker", "session-2", "session-3", "session-1b"]


def leaves_session_1b():
    sys.path[:0] = [str(SESSIONS / "session-1b" / "odd"), str(SESSIONS / "session-1a" / "znam")]
    import odd
    out = []
    for xs, P, r, lo, hi in odd.prefixes(12):
        p = prod(xs)
        out.extend(p * x for x in range(lo | 1, hi + 1, 2) if x > xs[-1] and gcd(x, P) == 1)
    return out


def leaves_session_3():
    sys.path.insert(0, str(SESSIONS / "session-3"))
    import znam_odd
    out = []
    for pre, P, a, x0, x1, *_ in znam_odd.jobs(12, True, None):
        p = prod(pre)
        out.extend(p * x for x in range(x0, x1, 2) if gcd(x, P) == 1)
    return out


def leaves_session_2():
    sys.path.insert(0, str(SESSIONS / "session-2"))
    import znam_odd
    out = []
    znam_odd.last_two = lambda P, u, lo: (out.append(P), [])[1]
    znam_odd.search(12, verbose=False)
    return out


def leaves_checker():
    sys.path.insert(0, str(HERE.parent))
    import oddsearch
    tasks, nodes = oddsearch.enumerate_prefixes(12, True)
    return [P for _, P, _ in tasks]


DUMP = {"session-1b": leaves_session_1b, "session-3": leaves_session_3,
        "session-2": leaves_session_2, "checker": leaves_checker}


def dump(name):
    stdout, sys.stdout = sys.stdout, sys.stderr
    leaves = DUMP[name]()
    sys.stdout = stdout
    json.dump([str(p) for p in leaves], sys.stdout)


def main():
    have_flint = subprocess.run([sys.executable, "-c", "import flint"], capture_output=True).returncode == 0
    names = ORDER if have_flint else ORDER[1:]
    if not have_flint:
        print("python-flint not installed: skipping the checker (../oddsearch.py)", file=sys.stderr)
    procs = {n: subprocess.Popen([sys.executable, "-B", __file__, "--dump", n], stdout=subprocess.PIPE, text=True)
             for n in names}
    L, S = {}, {}
    for n, p in procs.items():
        out, _ = p.communicate()
        if p.returncode:
            sys.exit(f"{n}: enumeration failed (exit {p.returncode})")
        leaves = json.loads(out)
        L[n], S[n] = len(leaves), set(leaves)
    for k in names:
        print(f"{k:11s} leaves {L[k]:7d}  distinct products {len(S[k]):7d}")
    for a, b in zip(names, names[1:]):
        print(f"{a} minus {b}: {len(S[a] - S[b])}   |   {b} minus {a}: {len(S[b] - S[a])}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--dump"]:
        dump(sys.argv[2])
    else:
        main()
