import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
AUTOGRAM = HERE.parent / "sessions" / "shelf-1" / "autogram"
sys.path.insert(0, str(AUTOGRAM))
import autogram as ag
rows = [l.rstrip("\n").split("\t") for l in open(AUTOGRAM / "census" / "english.tsv") if not l.startswith("#")]
for p, n, nodes, vecs in rows[:12]:
    for seed in range(3):
        t0 = time.time(); s, it = ag.walk(p, seed, 300000); dt = time.time() - t0
        print(repr(p)[:30], n, seed, "FOUND" if s else "none", it, f"{dt:.1f}s", f"{it/dt if dt else 0:.0f} it/s", flush=True)
