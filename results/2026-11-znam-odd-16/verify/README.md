# verify/

Checks of the note that do not rely on the session code, plus reruns of the session searches.
All commands run from this folder with Python 3 and nothing else installed, except where noted.
Times of the four twelve-term searches are those in the `reruns/` logs (an 8-core machine).

| File | What it is |
|---|---|
| `oddsearch.py` | Exhaustive search of the equation with K terms that shares no code with the sessions. Fixes the first K−2 terms with exact bounds and gets the last two by factoring P² + N. Needs `python-flint` (`pip install python-flint`). |
| `check.py` | Exact-arithmetic checks of the smaller claims: the solution lists for k ≤ 8 from OEIS, the mod-4 argument that an all-odd solution needs 4 \| k, and the lemma over every solution containing 2. |
| `reruns/` | Output of rerunning each session's own twelve-term odd search, and of `oddsearch.py 12 --odd`. All four report 0 solutions. |
| `compare/compare.py` | Imports the four implementations (the three sessions' and `oddsearch.py`) without modifying them. Lists the ten-term prefixes each one leaves for the last-two-terms step and compares the four lists. |
| `compare/output.txt` | Output of `compare.py`. |
| `compare/details.py`, `compare/details.txt` | What `compare.py` does not print: differences for all six pairs, the two checker leaves missing from session-2's set, and session-3's candidates against those it solves. Needs `python-flint`. |

## Running

```sh
python3 oddsearch.py 12 --odd               # 353 s, 8 processes (reruns/checker.log); needs python-flint
python3 check.py b075461.txt                # under 1 s
cd compare && python3 compare.py            # about 4 s
python3 details.py > details.txt            # 7 s, needs python-flint
```

`check.py` reads the b-file of OEIS A075461, which is not included. Download it from
<https://oeis.org/A075461/b075461.txt>.

`compare.py` prints the table in `output.txt`. Without `python-flint` it leaves out the checker row
and compares only the three sessions.

To repeat the session reruns in `reruns/` (with `-B`, so that no `__pycache__` appears under
`sessions/`):

```sh
python3 -B ../sessions/session-2/znam_odd.py 12              # 11.5 s, one core
python3 -B ../sessions/session-3/znam_odd.py odd 12          # 14.7 s, 8 processes
T=$(mktemp -d); cp -r ../sessions/session-1a/znam ../sessions/session-1b/odd "$T"
(cd "$T/odd" && rm -f odd12.* && python3 -B odd.py 12)        # 186 s, one core
```

Session-1b's `odd.py` writes `odd12.*` files to its working directory and looks for its helper
modules in `../znam`. That is why it runs in a copy, laid out as it was on the original machine.

## Reading compare/output.txt

`leaves` is the number of ten-term prefixes an implementation hands to its last-two-terms step.
`distinct products` is the number of distinct products of those ten terms; it is a little lower
because a product does not identify a prefix uniquely. `A minus B` is the number of products in
A's set that are not in B's.
