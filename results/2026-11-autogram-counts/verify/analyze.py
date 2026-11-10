"""Part 1 analysis. Reads walk_shard*.jsonl + census/english.tsv; uses only myverify (none of the code under test)."""
import glob, json, sys
from pathlib import Path
from collections import Counter, defaultdict
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
AUTOGRAM = HERE.parent / "sessions" / "shelf-1" / "autogram"
import myverify as mv

NROWS, NSEEDS = int(sys.argv[1]), int(sys.argv[2])
rows = [l.rstrip("\n").split("\t") for l in open(AUTOGRAM / "census" / "english.tsv") if not l.startswith("#")]
assert len(rows) == 2000 and all(len(r) == 4 for r in rows)
census = []
for opening, n, nodes, vecs in rows[:NROWS]:
    vecs = vecs.split(" ") if vecs else []
    assert len(vecs) == int(n) == len(set(vecs))
    census.append((opening, vecs))

# every stored census solution for the tested rows: recount with my own renderer and counter
bad_census = 0
for opening, vecs in census:
    for v in vecs:
        counts = [int(v[2 * i:2 * i + 2]) for i in range(26)]
        r = mv.check(mv.my_render(opening, counts), opening)
        if not (r["ok"] and r["vec"] == v): bad_census += 1

runs = []
for f in sorted(glob.glob(str(HERE / "out" / "walk_shard*.jsonl"))):
    runs += [json.loads(l) for l in open(f)]
assert Counter((r["row"], r["seed"]) for r in runs) == Counter((i, s) for i in range(NROWS) for s in range(NSEEDS)), "missing or duplicate runs"

found = defaultdict(set)          # row -> set of vectors of verified sentences
false_sentences = []              # walk output that fails my count
missing = []                      # verified sentences not in the census
hits = 0
for r in runs:
    opening = census[r["row"]][0]
    assert r["prefix"] == opening
    if r["sentence"] is None: continue
    hits += 1
    c = mv.check(r["sentence"], opening)
    if not c["ok"] or c["oxford"]:
        false_sentences.append((r, c["problems"])); continue
    found[r["row"]].add(c["vec"])
    if c["vec"] not in census[r["row"]][1]: missing.append(r)

n_distinct = sum(len(v) for v in found.values())
n_in = sum(len(v & set(census[i][1])) for i, v in found.items())
zero_rows = [i for i, (o, vecs) in enumerate(census) if not vecs]
census_total = sum(len(v) for _, v in census)
never = sum(len(set(v) - found.get(i, set())) for i, (_, v) in enumerate(census))
steps = sum(r["steps"] for r in runs)
print("rows tested: first %d data rows of census/english.tsv; seeds 0..%d; runs %d; total walk steps %d" % (NROWS, NSEEDS - 1, len(runs), steps))
print("distinct openings (as strings) among tested rows:", len(set(o for o, _ in census)), " empty openings:", sum(o == "" for o, _ in census))
print("stored census solutions in tested rows: %d; failing my recount: %d" % (census_total, bad_census))
print("runs that returned a sentence: %d; sentences failing my letter count: %d" % (hits, len(false_sentences)))
print("openings where walk found >=1 true sentence:", len(found))
print("distinct true sentences found by walk (row, vector):", n_distinct)
print("  of which in census:", n_in)
print("  of which NOT in census:", n_distinct - n_in, " (runs: %d)" % len(missing))
for r in missing: print("   MISSING", json.dumps(r))
for r, p in false_sentences: print("   FALSE", json.dumps(r), p)
print("census solutions never found by the walk: %d of %d" % (never, census_total))
print("tested openings with 0 stored solutions: %d; of those, openings where the walk returned anything: %d" % (
    len(zero_rows), sum(1 for i in zero_rows if any(r["row"] == i and r["sentence"] for r in runs))))
print("tested openings with >=1 stored solution: %d; walk found >=1 in %d of them" % (NROWS - len(zero_rows), len(found)))
k = Counter(len(v) for _, v in census)
print("census solution-count histogram over tested rows:", sorted(k.items()))
print("max steps of a successful run:", max((r["steps"] for r in runs if r["sentence"]), default=None))
