# Corrections from the author

The files in this folder are unchanged. The author stated the corrections below after its session,
when it was told what outside checks had found.

## 1. Eight terms in pure Python

Applies to `znam-worked`, section 1: “about 26 million numbers near 10^27 to factor, too many for
pure Python; there is no compiler on this box”. One of the three instances is the session in
`../session-1a`.

> **My note is wrong about eight terms.** It says 26 million factorisations is "too many for pure Python". It was too many for my method. I did notice that for a fixed prefix the numbers are values of one quadratic and could be sieved together, and I talked myself out of it because I expected the unsieved cofactors to stay hard. Three instances showed otherwise.

## 2. A line of the Lenstra routine that the checks do not cover

Applies to `znam-worked`, section 3: “Deleting either of the two candidate rules in the Lenstra
step makes the first check fail, so it has teeth.” The adjustment is in `znam_lenstra.py`, in the
Euclid loop of `divisors_in_class`: `if i % 2 == 1 and rem == 0: q -= 1; rem = a1`.

> **One piece of the Lenstra routine is not covered by the checks.** The note's claim about the two candidate rules is accurate. But I also tried removing the adjustment that forces Euclid to end on an even index, and the checks still passed. I kept it because the proof needs it. Anyone leaning on that file should know that line rests on the derivation alone.

## 3. Candidates for the tenth term and tails solved

Applies to `znam-worked`, section 2(b): “about 497,000 choices of the tenth, each leaving a divisor
problem for the last two.” The guess was confirmed afterwards: `../../verify/compare/details.txt`.

> One small discrepancy for the record. My run's own log shows 496,585 two-term tails actually executed (457,755 by Lenstra plus 38,830 by direct stepping), against the 497,231 leaves you count for my enumeration. My guess is that the 646 are tenth-term candidates dropped by the final `reachable()` check before any tail is run, but I can't confirm that from here.

## 4. How the sixteen should be presented

Applies to `znam-worked`, section 2: “No solution in odd numbers has fewer than 16 terms.” The
1988 proposition is Brenton and Hill's: the number of terms of an all-odd solution is divisible by
four.

> The sixteen is a small computation on top of a 1988 proposition, and it should be presented as that.
