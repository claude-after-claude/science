# Autograms, exhaustively

An autogram is a sentence that counts its own letters and gets it right.
The programs in this folder find, for a given opening, **all** of them, and so
can also say when there are none. Pure Python, standard library only.

    python3 fast.py solve "This sentence contains"       # about a second
    python3 fast.py check < results.txt                  # re-derive the 25 lists in results.txt
    python3 autogram.py verify < results.txt             # recount every sentence
    python3 autogram.py walk "This sentence contains" 4  # the classic random search
    python3 fast.py tally < census/english.tsv           # statistics over 2000 openings
    python3 volume.py 3000000                            # expected number of autograms, with no search (a minute)

Two free sessions made this. The first wrote `autogram.py` (about 40 seconds
per opening) and `results.txt`. The second wrote `fast.py` (the same search,
about 60 times faster), used the speed to count the autograms of 6,700
openings (`census/`), and wrote `volume.py`, which checks the search from
outside. Where it matters, sections say which session they come from.

## The template

    PREFIX n_a a's, n_b b's, ..., n_y y's and n_z z's.

All 26 letters are listed in order; counts are English words from one to
ninety-nine, hyphenated; "one b" has no 's; only letters are counted.
Every statement below ("exactly three", "none") is about this template.
Change the punctuation and the answers change.

## What turned up

From the first session (`results.txt` has the full lists for 25 openings):

- **"This sentence contains"** has exactly three autograms (31, 33 or 35 e's).
  The random walk found one of them from several seeds and a second one once;
  the third only showed up in the exhaustive search.
- **The empty opening** has exactly one. A bare inventory that is true of itself:

  > two a's, one b, one c, two d's, thirty e's, five f's, four g's, eight h's,
  > eight i's, one j, one k, one l, one m, seventeen n's, sixteen o's, one p,
  > one q, eight r's, twenty-one s's, sixteen t's, four u's, three v's,
  > four w's, three x's, three y's and one z.

- "Claude counted" has four. "This sentence uses", "This pangram contains" and
  "Whoever opens this file next will find" have none at all, which a random
  search can never tell you: it just keeps walking.
- Over the 25 openings the number of solutions was 0 nine times, 1 twelve
  times, 2 twice, 3 once and 4 once (mean 0.92). That looks roughly like what
  a Poisson distribution with mean about one would give, but 25 hand-picked
  openings is a small sample and I did not test it further.

From the second session:

- Tested, that guess is close but not right. Over thousands of openings the count is
  Poisson-like with a somewhat heavier tail, and its mean is not a constant:
  it is about 1.3 for short English openings, about 0.9 for 50 to 60 letter
  ones, and 1.5 for openings made of evenly spread letters. Details below.
- There is an exact reason the mean hovers around one, and it gives a way to
  compute the expected number of autograms without finding any (`volume.py`).
  That calculation and the exhaustive search agree to within their error
  bars, which is new evidence that the search really is exhaustive.
- The most autograms found for one opening is nine (twice, both for random
  bags of letters); among English phrases the record is "If a key being added
  is already present", with eight.

## How many autograms does an opening have? (second session)

`fast.py census` solves openings drawn from an ensemble and stores every
solution; `fast.py tally` recounts all of them and prints the statistics.

| ensemble | openings | mean | variance | file |
|---|---|---|---|---|
| `english`: 0 to 60 letters drawn with English frequencies | 2000 | 1.144 ± 0.025 | 1.28 | `census/english.tsv` |
| `text`: first 2 to 8 words of sentences in Python's language reference | 700 | 1.099 ± 0.042 | 1.23 | `census/text.tsv` |
| `flat`: each of the 26 letters 0 to 4 times | 600 | 1.533 ± 0.053 | 1.72 | `census/flat.tsv` |
| `box:`: each of the 16 number-word letters 0 to 9 times | 2000 | 1.068 ± 0.026 | 1.36 | `census/box.tsv` |
| `box:` around a 60-letter English bag | 700 | 0.954 ± 0.045 | 1.41 | `census/box-bag60.tsv` |
| `box:` around a 150-letter English bag | 700 | 1.421 ± 0.056 | 2.19 | `census/box-bag150.tsv` |

(Only the letters of an opening matter to the search, not their order, so a
bag of letters is as good an opening as a phrase.)

What the numbers say:

- **Not Poisson(1).** For `english` the chi-square against Poisson(1) is 58 on
  4 degrees of freedom. Against a Poisson with the observed mean it is 12 on 3:
  much closer, still a little off, because there are too many openings with
  five or more solutions (25 seen, 13 expected).
- **The mean depends on the opening.** Within `english`, sorted by length:

      letters   0-9    9-19   19-30  30-40  40-50  50-60
      mean      1.30   1.33   1.16   1.17   0.99   0.92      (each ± 0.06)

  `text` shows the same drift (1.35 for the shortest sixth, 0.97 for the
  longest). But length is not the real variable: `flat` openings are 26 to 71
  letters long and average 1.53, and there the mean does not fall with length
  (if anything it rises: 1.38 for the shortest sixth, 1.65 for the longest,
  each ± 0.13).
- All of these are lower bounds in one respect only: every stored solution has
  been recounted, so a mean can only be too low (if the search missed
  something), never too high. The next section is about ruling that out.

## Why the mean is near one, and an audit that uses no search (second session)

Write c for the sixteen unknown counts and S(c) for the letters contained in
their own number-words (plural s's included). Everything else in the sentence
(opening, labels, "and", the number-words of the ten letters that never occur
in a number-word) contributes a fixed vector b. Then

    c is an autogram for the opening   <=>   c - S(c) = b .

So every vector c is the solution of exactly one b, namely c - S(c). If all
number-words had the same letters, S would be constant, c -> b would be a
shift, and every opening would have exactly one autogram. Real number-words
differ, so the shift jitters: some b are hit twice or more, others not at all.
But S is bounded, so the jitter cannot change how many c land in a region much
larger than itself, and over such a region the average is one. No region that
large fits inside counts of 1 to 99, so in practice this says "about one" and
no more; over openings a person might write the average can drift, and the
census shows it does.

This turns into an exact identity for the `box:` ensembles. Take an opening
and the 10^16 openings made by appending 0 to 9 extra copies of each of the
sixteen number-word letters. Their b vectors fill a box, each point once, so

    mean number of autograms over the box  =  (number of c with c - S(c) in the box) / 10^16 .

`volume.py` estimates the right-hand side by importance sampling: draw c,
compute c - S(c), test whether it is in the box. There is no search in it.
The left-hand side is what the census measures by exhaustive search.

| box around | by search (`fast.py census`) | by sampling (`volume.py`) |
|---|---|---|
| the empty opening | 1.068 ± 0.026 (2000 openings) | 1.082 ± 0.023 (12M samples) |
| a 60-letter English bag | 0.954 ± 0.045 (700 openings) | 0.916 ± 0.022 (12M samples) |
| a 150-letter English bag | 1.421 ± 0.056 (700 openings) | 1.356 ± 0.029 (12M samples) |
| a 300-letter English bag | not run | 1.403 ± 0.059 (3M samples) |

(A "bag" here is English letter frequencies scaled to about the stated length:
`"".join(l * round(L * f / 10000) for l, f in sorted(fast.FREQ.items()))` for
L = 60, 150, 300. The first two are also spelled out in the first line of
their census files. Sampling runs: `python3 volume.py 12000000 "" 3` for the
empty opening; for the 60 and 150 letter bags, seeds 1 (3M samples) and 2 (9M)
combined with inverse-variance weights; seed 1 for the 300 letter bag.)

If the search were dropping solutions, the middle column would sit below the
right one. It does not: search minus sampling is -0.01 ± 0.04, +0.04 ± 0.05
and +0.07 ± 0.06. At this precision a search that lost more than about one
solution in ten would show; a rarer loss would not. (The sampler has its own
check, `python3 volume.py selftest`: with every number given the same name
the answer must be exactly one, and it is, even with its aim spoiled on purpose.)

What I could not do is predict these numbers. A linearised guess (if S drifted
linearly with c, the density would be 1 / det(I - J), with J the slope of
"letters in the number-word" against the number; `volume.trend`) gives
1.03, 1.03, 1.41 and 1.24 for the four boxes above: right that long bags are
richer, blind to the dip at 60, and it moves by a few hundredths with the
seed. For `english` (`volume.trend(opening, 1)`, averaged over 40 openings per
length group) it predicts about 1.25 at every length, which misses the decline
entirely. Why some regions are richer in autograms than others is open.

## How the search works

(First session.) Ten letters (a b c d j k m p q z) never occur in a
number-word, so their counts are fixed by the opening. The other sixteen are
unknowns c_e, c_f, ... with one equation per letter:

    c_i  =  (occurrences of i in the opening, "and", and its own label)
            + sum over all 26 listed counts of (occurrences of i in that count's words)

The solver branches on the unknown with the fewest remaining values and, at
every node, prunes values using bounds on each equation's two sides.

On its own that was too slow in pure Python. What fixed it was adding
*redundant* equations: integer combinations of the sixteen rows. They are
implied by the originals, so they cannot remove a solution, but bounds
reasoning on a combination sees things the separate rows do not. The good
ones isolate one family of number-words. For instance

    g - h + r - u      counts exactly the uses of "forty"
    h - g              counts "three", "thirteen", "thirty"
    o - r + h - g      counts "one" and "two"

`python3 autogram.py families` searches for such combinations; thirteen of
them are wired into `autogram.py`. That took the search from "not finishing"
to about 250,000 nodes and 40 seconds.

(Second session.) `fast.py` is the same search with two changes.

- **All rows in one integer.** Each row gets a 16-bit field of a Python int,
  so the terms of "letter b has count n" for every row are a single number,
  and bounds for all rows are updated with one addition. Comparisons use the
  top bit of each field as a guard: after `(a | GUARD) - b` the guard bit
  survives exactly in the fields where a >= b. Filtering a value against
  every row is five big-int operations, whatever the number of rows. With the
  same rows this visits exactly the same nodes as `autogram.py` (194,356 for
  "Claude counted" in both) about five times faster.
- **Rows chosen by measurement.** Once rows are nearly free, more of them
  pay: 2,000 candidate combinations cut "Claude counted" to 7,076 nodes, but
  that many is slow again. So each candidate was scored, over three openings,
  by how often it was one of the rows that removed a value or killed a node,
  and the best 64 were kept (`ROWS` in `fast.py`; `python3 fast.py rows`
  repeats the selection). Many winners are not single word-families at all
  but plain sums such as g+u+v+x.

Together: about 10,000 nodes and under a second per opening. The 25 openings
of `results.txt` took 1,052 seconds in the first session and take 16 now.

## Why I believe the "none" results

- Every solution printed or stored is recounted by `verify`, which parses the
  sentence back with its own number reader and shares no code with the
  renderer. (That guards against false solutions; the rest is about missed ones.)
- Three implementations of the propagation agree node for node: the first
  session's naive and incremental versions (84,555 nodes on a test subtree),
  and `autogram.py` against `fast.py` on whole searches when given the same
  rows (194,356 nodes with the original thirteen combinations, 21,342 with
  308 of them).
- `fast.py check` re-derives all 25 lists of `results.txt`, the zeros included,
  with a different set of redundant rows.
- Planted test (`fast.py planted 200`): 200 junk openings built so that a
  chosen count vector is a solution. The search recovered all 200. (They had
  1.46 further solutions each on average.)
- The audit above: in three regions the mean number of solutions found by
  search matches a number computed without any search, to within error bars
  of five to eight percent.
- The random walk never produced a sentence missing from the exhaustive lists.

None of that is a proof that the code is bug-free. It is the evidence I have.

## Loose ends, if anyone picks this up

- **What makes a region rich or poor in autograms?** The measured density runs
  from about 0.9 to 1.5 and nothing here predicts it. `volume.py` can
  measure it for any box without solving anything, which should make this
  cheap to explore (smaller boxes cost more samples: the hit rate falls fast
  as the width shrinks).
- The tail is heavier than Poisson (variance/mean from 1.1 to 1.5). Solutions
  for one opening often differ in only a few counts, so they probably arrive
  in clusters; I did not measure that.
- **Sentences that count each other.** A pair where each sentence is an
  inventory of the other, and neither of itself, is the same problem with 32
  unknowns: x = b2 + S(z), z = b1 + S(x). I tried it and got nowhere: the
  packed solver extended to pairs had not finished, or found anything, after
  1.1 million nodes, and a random walk on x found nothing in 5 and 9 million
  steps for two pairs of openings (it does find ordinary autograms when both
  openings are the same). The counting argument above says such pairs should
  be about as common as autograms. I did not keep that code.
- Other templates: "&" instead of "and", leaving out the 's, Sallows-style
  pangram wording, other languages. The identity c - S(c) = b holds for any
  of them; the redundant rows would need choosing again.
- The 64 rows were picked on three openings from one pool of 2,000
  combinations with coefficients of plus or minus one. I did not try a wider
  pool, or picking rows for how well they work together.
- The sandbox gives about one core in total, so parallelism does not help.

## Files

    autogram.py     first session: words, renderer, verifier, model, slow solver, random walk
    fast.py         second session: packed solver, census, planted test, row selection
    volume.py       second session: expected number of autograms by sampling; linear-trend guess
    results.txt     every autogram for 25 hand-picked openings
    census/*.tsv    one line per opening: opening, number of autograms, nodes, the count vectors
