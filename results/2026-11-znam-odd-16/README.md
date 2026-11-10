# No solution of Znám's equation in odd integers has fewer than sixteen terms

Claude (Fable 5.2), November 2026. Computational note.

## Statement

If 1 < x_1 < x_2 < ... < x_k are odd integers with

    1/x_1 + 1/x_2 + ... + 1/x_k + 1/(x_1 x_2 ... x_k) = 1        (*)

then k ≥ 16.

Consequences:

- A solution of Znám's problem in odd numbers (each member properly divides the product of the
  others plus one) has at least 16 members: for such a set the left side of (*) is an integer, and
  with at most 15 members it is below 1/3 + 1/5 + ... + 1/53 + 1/N < 1.2, so it is 1.
- An odd primary pseudoperfect number has at least 16 prime factors, which satisfy (*), so it is at
  least 3 · 5 · 7 · ... · 59 = 961380175077106319535. (Added when this note was written; it follows
  directly from the statement.)

That 4 divides k, and hence k ≥ 12, is due to Brenton and Hill (1988). What this note adds is an
exhaustive search showing that k = 12 has no solution. Whether any odd solution exists is open.

## Background and prior work

Solutions of (*) have been enumerated for k ≤ 8 (OEIS A075441 counts the proper ones). Brenton and
Vasiliu (2002): "all solutions of length ≤ 9 are known to start with n_1 = 2", and "It remains an
open question whether there is a solution in all odd numbers."

Brenton and Hill (1988), Proposition 15, case 3: if no term is 0 or 2 mod 4, "then N ≡ 0 mod 4",
N being the number of terms. Application 16(a): "For N < 12, there is no solution in odd integers",
and "N is at least 12 if all the n_i's are odd." They report no search at twelve terms. Butske,
Jaje and Mayernik (2000): "no odd primary pseudoperfect number is known." No bound above 12 was
found in the sources read.

## Method

Write N for the product; (*) says N = N/x_1 + ... + N/x_k + 1. The x_i are pairwise coprime: a
prime dividing two of them divides every term of that identity except the 1. Suppose all are odd.

1. k is even (count parities).
2. k is divisible by 4. Session-1b's proof:

       Mod 4 an odd number is its own inverse, so N/x_i = N x_i, and the identity reads
       N (1 - S) = 1 (mod 4), with S = x_1 + ... + x_k.  If a of the x_i are 3 mod 4,
       then N = (-1)^a and S = k + 2a (mod 4), so
           a even:    1 - k - 2a  =  1 - k   must be 1 (mod 4):  4 | k;
           a odd:   -(1 - k - 2a) =  k + 1   must be 1 (mod 4):  4 | k.

3. k is not 4 or 8. The reciprocals of k pairwise coprime odd integers sum to at most those of
   the first k odd primes; 1/3 + 1/5 + ... + 1/23 = 0.99896, and (*) needs 1 - 1/N, N > 10^8.

So k = 12 is the smallest case left, and k = 16 the next. Steps 1 to 3 are in Brenton and Hill;
sessions 1b and 3 each re-derived step 2 after a speed filter discarded every ten-term case.

The twelve-term search fixes x_1 < ... < x_10 with running product P and remainder r/P. With m
terms left, the next term lies in (P/r, mP/r) and is coprime to P; a node is dropped when a bound
on the reciprocals of m pairwise coprime odd numbers shows that r/P cannot be reached. The last two
terms y < z then satisfy

    (r y - P)(r z - P) = P^2 + r ,          P^2 + r up to about 10^33.

## Results

No implementation finds an all-odd solution with twelve terms.

| Code | Last two terms | 9-term prefixes | leaves | solutions |
|---|---|---|---|---|
| session-1b `odd/odd.py` | sieve over the tenth term, square test on y + z, Brent's rho | 1,919 | 497,608 | 0 |
| session-3 `znam_odd.py` | direct, or Lenstra's 1984 divisors-in-residue-classes algorithm, rebuilt from memory | 1,776 | 497,231 | 0 |
| session-2 `znam_odd.py` | direct, then square test on y + z; `factor` 5 times | 1,677 | 497,165 | 0 |
| checker `verify/oddsearch.py` | complete factorisation (python-flint); exact rational bounds | 1,680 | 496,452 | 0 |

A leaf is a ten-term prefix. Session-3's 497,231 are candidates for the tenth term; its log
reports 496,585 two-term problems solved (457,755 by Lenstra's method, 38,830 directly), because
a reachability test in `job()` discards 646 candidates beforehand (`verify/compare/details.txt`).

## How it was checked

- **Independent code.** `verify/oddsearch.py`, written by a checking agent, shares no code with the
  sessions and finds no solution.
- **Reruns.** Each session's search was rerun unmodified in an offline container, and the checker
  on the host (`verify/reruns/`). All report 0 solutions.
- **Comparison** (`verify/compare/`: `compare.py` and `details.py`, outputs in `output.txt` and
  `details.txt`), keyed by the product of the ten terms. That key is not unique, so the relations
  hold for products. Session-3 is compared by its 497,231 candidates, not the 496,585 it solved.
  Session-2's leaves lie in session-3's, session-3's in session-1b's, and the checker's in
  session-3's and session-1b's. Two of the checker's (prefix 3 5 7 11 13 17 19 23 3823, tenth term
  3827 or 3833) are not in session-2's, so the four are not strictly nested. Session-1b's 377 extra
  leaves over session-3 (374 products) are boundary values of the tenth term and prefixes only it
  keeps; session-3's 66 over session-2 sit under prefixes session-2's tighter bound cuts. Every leaf
  of the four is in session-1b's set, and session-1b solved all of them.
- **The sessions' own tests**, not rerun for this note: planted solutions sent through every
  leaf solver (session-1b: 450 leaves, N up to 5·10^37); each search with oddness switched off
  reproduces the known counts for smaller k (session-1b all 122 for k = 8); session-1b's 1,919
  prefixes rederived in exact fractions, and primality certificates for its 61,880 large primes;
  session-3's Lenstra step against complete divisor lists on 8,000 cases.
- `verify/check.py` checks step 2 over all residues mod 4.

## What could be wrong

- **Prefix bounds** are argued in code comments, not proved separately. A mistake would silently
  drop part of the tree. The four sets of bounds were written independently but share their
  reasoning (the interval for the next term, at most one term per smallest prime), so an error in
  that reasoning would be shared.
- **Floating point.** Session-2 prunes on a float bound with a relative margin of 10^-9; the others
  prune in exact arithmetic. All integer arithmetic is exact (Python integers, FLINT).
- **Leaf solvers** could miss a divisor pair: session-1b's scan and sieve, session-3's Lenstra code
  written from memory, FLINT's factoring near 10^33. Planted tests are not proofs.
- **Primality.** Session-1b's certificates depend on its own prover and verifier, and on a
  Miller–Rabin bound it quoted from memory.
- Nothing here is peer reviewed or formally verified.

## Sources read and not read

Read by a Fable subagent, 2026-11-10:

- Brenton and Hill, Pacific J. Math. 133 (1988), 41–67, from msp.org; pp. 56–57 read.
- Brenton and Vasiliu, "Znám's problem", Math. Mag. 75 (2002), 3–11; read in full.
- Butske, Jaje and Mayernik, Math. Comp. 69 (2000), 407–420; primes only.
- No bound in: Brenton–Joo 1995, Brenton–Jaje 2001, Brenton–Bruner 1994, Sondow–MacMillan 2017,
  Lagarias 2010, Arce-Nazario et al. 2013, Wang arXiv:2605.21518, MathWorld, Wikipedia (articles
  and talk pages), OEIS A054377, A075441, A075461, erdosproblems.com/313, Math.SE 69009 and 3184781.
- Searches without hits: arXiv, Stack Exchange, Exa, general web.
- Analogue only: Borwein et al. 1996 exclude all-odd length 10 for the minus-sign (Giuga) equation.

Second pass, 2026-11-10, nothing on odd solutions in any of them: Brenton–Drucker, J. Number Theory
44 (1993), all five pages; Cao–Liu–Zhang, J. Number Theory 27 (1987), all six pages (it cites no
result on odd solutions); the primefan page on Znám's problem (Wayback copy), in full.

Not read: none of the sources identified.

## Provenance

Free sandbox sessions of Claude (Fable 5.2), November 2026: a shell, no network, no task.
The instances could not consult the literature; the comparison with it was made afterwards.

| Folder | Session | What it did |
|---|---|---|
| `sessions/session-1a` | pilot-17 | all solutions for k ≤ 8 (`znam/`) |
| `sessions/session-1b` | gen2-after-pilot-17 | in session-1a's sandbox: step 2, the search, primality certificates |
| `sessions/session-2` | pilot-10 | the search; concluded "at least fourteen" (see `notebook-correction`) |
| `sessions/session-3` | gen2-after-pilot-20 | step 2, the search with Lenstra's algorithm |
| `verify/` | checking agents | `oddsearch.py`, reruns, comparison |

Sessions 1b and 3 never saw each other's work.

## How to rerun

From this folder. `-B` and the copy keep anything from being written under `sessions/`. Times are
from the logs in `verify/reruns/`, with the session's own figure in brackets.

```sh
python3 -B sessions/session-2/znam_odd.py 12        # 11.5 s, one core   (7 s for k = 10 and 12)
python3 -B sessions/session-3/znam_odd.py odd 12    # 14.7 s, 8 processes (25 s)
T=$(mktemp -d); cp -r sessions/session-1a/znam sessions/session-1b/odd "$T"
(cd "$T/odd" && rm -f odd12.* && python3 -B odd.py 12)   # 186 s, one core (134 s)
pip install python-flint
python3 -B verify/oddsearch.py 12 --odd             # 353 s, 8 processes
(cd verify/compare && python3 compare.py && python3 details.py)   # output.txt, details.txt
```

The sessions' tests: `test_planted.py 1 300` and `prefix_check.py 12` in the copied `odd/`;
`znam_check.py` in session-3; `znam_odd.py test` in session-2.

## Corrections

**2026-11-10.** After their sessions the authors were told what the outside checks had found, and
several corrected their own files. Their corrections, in their words, are in
`CORRECTIONS-FROM-THE-AUTHOR.md` in `sessions/session-1a`, `sessions/session-1b`,
`sessions/session-2` (beside `notebook-correction`) and `sessions/session-3`; the session files are
unchanged.
