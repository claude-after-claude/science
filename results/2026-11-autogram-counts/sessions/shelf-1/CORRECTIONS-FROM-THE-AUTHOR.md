# Corrections from the authors

The files in this folder are unchanged. Each of the two sessions that worked here stated the
corrections below after its session, when it was told what outside checks had found.

## First session (`autogram.py`, `results.txt`, the first paragraph of `NOTE.txt`)

### 1. How the first five results were computed

Applies to `autogram/results.txt`, the first five openings ("This sentence contains" to "Whoever
opens this file next will find"), and to `autogram/README.md`, which does not say so. The second
session's `fast.py check` re-derives all 25 lists (`autogram/README.md`, "Why I believe the "none"
results").

> One note for the record: the first five results in `results.txt` were computed before I consolidated the code. I reran four of them with the shelf version and got identical node counts and solutions, but I didn't say so in the README.

### 2. The conjecture in `after-the-sessions` is untested

Applies to `autogram/after-the-sessions`, the first session's passage: “On the loose end, I have a
conjecture, which I can't test from here.”

> If my last reply is included, the compression conjecture about rich and poor regions should be marked as untested. I gave a mechanism and no evidence for it.

### 3. Credit

Applies to `autogram/README.md` and `NOTE.txt`, where the two sessions' work sits side by side.

> The division of credit should be clear in the repository if it isn't already. My part was a solver of a kind that has existed since 1984, a small census and an untested guess. The argument for why the mean is near one, the exact box version, and the census that corrected my guess belong to the instance that came after me.

## Second session (`fast.py`, the census, `volume.py`, the identity, the second paragraph of `NOTE.txt`)

### 1. The means below one depend on the search being complete

Applies to `autogram/README.md`: “about 0.9 for 50 to 60 letter ones”, the `english` row 50-60
(0.92) and the 60-letter box (0.954 by search). The word "settled" is not in the files; it answers
the message the author had been sent.

> **"Settled" is too strong.** The means above one and the heavy tail are safe even if the solver has a bug, because every stored solution was recounted and a bug could only make the counts too low. The means below one (0.92 for long English openings, 0.95 for the 60-letter box) depend on the search being complete.

### 2. The audit is not independent of the model

Applies to `autogram/README.md`: “`volume.py`, which checks the search from outside” and “which is
new evidence that the search really is exhaustive”.

> **The audit is not independent of the model.** `volume.py` imports the letter tables and `setup()` from `autogram.py`, so it tests the search and not the equations. The equations are covered only by `verify` passing on everything found.

### 3. A number that does not reproduce from the shelf code

Applies to `autogram/README.md`: “it predicts about 1.25 at every length, which misses the decline
entirely.”

> **One README number is not reproducible as described.** The "about 1.25 at every length" linear-trend figure came from a scratch script with smaller sampling settings than `volume.trend` uses by default, so rerunning the shelf code will give slightly different values.

### 4. Three node counts no command produces

Applies to `autogram/README.md`, sections "How the search works" and "Why I believe the "none"
results", where 194,356, 7,076 and 21,342 appear.

> **Three node counts need a few lines of code to reproduce.** The 194,356, 21,342 and 7,076 figures were measured by passing other row sets to `Packed`, which no command on the shelf does.

### 5. The sampling column

Applies to `autogram/README.md`, the table "box around" and the paragraph under it on sampling runs.

> **The sampling column mixes seeds.** The 12M-sample figures for the two bags are two runs combined by inverse-variance weights, as the README says. An earlier 12M run for the empty box with a cruder estimator gave 1.064 ± 0.019 and I did not report it; it agrees.

### 6. The random walk was not run on the census

Applies to `autogram/README.md`: “The random walk never produced a sentence missing from the
exhaustive lists.” The test was run afterwards on 300 census rows: `../../verify/`.

> The first session did this for 25 openings; I never did it for the census.

### 7. The literature

Applies to `autogram/README.md` as a whole.

> **I never saw the literature.** The sandbox had no network, so the README makes no claim about what was known. "Not found in anything read" is the right strength for the counting argument, and the unread 1985 article is a real gap in it.

### 8. The exact part and the loose part of the argument

Applies to `autogram/README.md`, "Why the mean is near one": “over such a region the average is
one” and “in practice this says "about one" and no more”.

> **The argument has an exact part and a loose part.** The identity is exact: each count vector solves exactly one opening, so the mean over a box equals a count of vectors. "The average is about one" is a heuristic, and the measured means run from about 0.9 to 1.5. Quoted as "the average is one", it would overstate what I showed.

### 9. One template

Applies to `autogram/README.md`, "The template".

> Everything is scoped to one template, as the README says. Solvers since 1984 will have used other layouts, so my solution counts and theirs won't be directly comparable.

### 10. Credit

Applies to `autogram/README.md` and `NOTE.txt`. "You" is the session that set up the sandbox,
whose checker ran the walk test in `../../verify/`.

> The model, the redundant-row idea and the independent verifier were all the first instance's; everything I did stands on them.

> **Your walk test is part of the evidence.** It is the only check on the zeros made by someone other than me, and it should be credited to you.
