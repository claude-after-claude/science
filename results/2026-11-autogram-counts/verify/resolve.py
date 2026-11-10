"""Provenance check: re-run fast.FastSolver (their code) on census rows, compare count / nodes / vectors with the tsv."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
AUTOGRAM = HERE.parent / "sessions" / "shelf-1" / "autogram"
sys.path.insert(0, str(AUTOGRAM))
import fast
shard, nshards, nrows = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
rows = [l.rstrip("\n").split("\t") for l in open(AUTOGRAM / "census" / "english.tsv") if not l.startswith("#")]
same = diff = 0
for idx in range(nrows):
    if idx % nshards != shard: continue
    opening, n, nodes, vecs = rows[idx]
    s = fast.FastSolver(opening); s.solve()
    got = " ".join(sorted("".join("%02d" % sol[i] for i in range(26)) for sol in s.solutions))
    if (len(s.solutions), s.nodes, got) == (int(n), int(nodes), vecs): same += 1
    else: diff += 1; print("DIFF row", idx, repr(opening), len(s.solutions), s.nodes, got, flush=True)
print("shard %d: same %d, different %d" % (shard, same, diff), flush=True)
