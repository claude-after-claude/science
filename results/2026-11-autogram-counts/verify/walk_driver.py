"""Run autogram.walk (their code, unmodified, imported) on census rows; one JSONL line per (row, seed)."""
import argparse, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
AUTOGRAM = HERE.parent / "sessions" / "shelf-1" / "autogram"
sys.path.insert(0, str(AUTOGRAM))
import autogram as ag

ap = argparse.ArgumentParser()
ap.add_argument("--shard", type=int, required=True)
ap.add_argument("--nshards", type=int, default=8)
ap.add_argument("--nrows", type=int, default=300)
ap.add_argument("--nseeds", type=int, default=12)
ap.add_argument("--max-iter", type=int, default=300000)
ap.add_argument("--out", required=True)
a = ap.parse_args()

rows = [l.rstrip("\n").split("\t") for l in open(AUTOGRAM / "census" / "english.tsv") if not l.startswith("#")]
assert all(len(r) == 4 for r in rows) and len(rows) == 2000
with open(a.out, "w") as f:
    for idx in range(a.nrows):
        if idx % a.nshards != a.shard: continue
        prefix = rows[idx][0]
        for seed in range(a.nseeds):
            t0 = time.time()
            s, it = ag.walk(prefix, seed, a.max_iter)
            f.write(json.dumps(dict(row=idx, prefix=prefix, seed=seed, sentence=s, steps=it, sec=round(time.time() - t0, 2))) + "\n")
            f.flush()
print("shard", a.shard, "done", flush=True)
