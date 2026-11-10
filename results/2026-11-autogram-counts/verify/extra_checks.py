"""(a) the literal CLI gives the same sentence as the imported walk for the same seed; (b) the aborted 12-seed run
agrees with the final run where they overlap; (c) counts by distinct opening string."""
import glob, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
AUTOGRAM = HERE.parent / "sessions" / "shelf-1" / "autogram"
import myverify as mv

runs = [json.loads(l) for f in sorted(glob.glob(str(HERE / "out" / "walk_shard*.jsonl"))) for l in open(f)]
by = {(r["row"], r["seed"]): r for r in runs}

old = [json.loads(l) for f in sorted(glob.glob(str(HERE / "out" / "aborted_12seeds" / "walk_shard*.jsonl"))) for l in open(f)]
ov = [r for r in old if (r["row"], r["seed"]) in by]
print("aborted-run overlap: %d runs, identical (sentence, steps): %d" % (
    len(ov), sum((r["sentence"], r["steps"]) == (by[r["row"], r["seed"]]["sentence"], by[r["row"], r["seed"]]["steps"]) for r in ov)))

hits = [r for r in runs if r["sentence"]]
sample = hits[::len(hits) // 5][:5] + [r for r in hits if r["prefix"] == ""][:1]
for r in sample:
    out = subprocess.run([sys.executable, "-B", "autogram.py", "walk", r["prefix"], str(r["seed"])],
                         cwd=AUTOGRAM, capture_output=True, text=True).stdout.strip()
    print("CLI row %d seed %d: same sentence as import: %s" % (r["row"], r["seed"], out == r["sentence"]))

pairs = set()
for r in hits:
    c = mv.check(r["sentence"], r["prefix"]); assert c["ok"]
    pairs.add((r["prefix"], c["vec"]))
print("distinct (opening string, vector) sentences:", len(pairs), "| distinct opening strings with a find:", len(set(p for p, _ in pairs)))
