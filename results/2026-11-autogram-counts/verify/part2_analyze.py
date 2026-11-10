"""Part 2 analysis with myverify only."""
import glob, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import myverify as mv

OPEN = {"third": "Left on a shelf by a third visitor, this sentence contains exactly",
        "second": "Left on a shelf by a second visitor, this sentence contains exactly"}
solved = {}
for key, opening in OPEN.items():
    lines = [l.rstrip("\n") for l in open(HERE / "out" / ("solve_%s.txt" % key))]
    print("== fast.py solve, %s visitor ==" % key)
    print(lines[0])
    vecs = []
    for s in lines[1:]:
        c = mv.check(s, opening)
        print("  my count:", "TRUE" if c["ok"] and not c["oxford"] else "FALSE %s" % c["problems"], c["vec"]); print("  " + s)
        vecs.append(c["vec"])
    solved[key] = vecs
    print("== autogram.py walk (CLI, 5M steps max), %s visitor ==" % key)
    wv = {}
    for f in sorted(glob.glob(str(HERE / "out" / ("walk_%s_seed*.txt" % key)))):
        s = open(f).read().strip()
        if s.startswith("no luck"):
            print("  %s: %s" % (f[-9:-4], s)); continue
        c = mv.check(s, opening)
        print("  %s: FOUND, my count %s, in fast.py list: %s, vec %s" % (f[-9:-4], "TRUE" if c["ok"] and not c["oxford"] else "FALSE %s" % c["problems"], c["vec"] in vecs, c["vec"]))
        wv.setdefault(c["vec"], s)
    print("  distinct sentences from walk: %d; fast.py solutions the walk did not find: %d" % (len(wv), len(set(vecs) - set(wv))))
    for s in wv.values(): print("  " + s)

given = open(HERE / "second_visitor.txt").read().strip()
c = mv.check(given, OPEN["second"])
print("== given second-visitor sentence ==")
print("  true autogram by my count:", c["ok"], c["problems"], "| ', and' before last item:", c["oxford"])
print("  counts:", dict(zip(mv.AZ, c["actual"])))
print("  same count vector among fast.py solve output:", c["vec"] in solved["second"], "| other fast.py solutions:", len(set(solved["second"]) - {c["vec"]}))
as_template = mv.my_render(OPEN["second"], c["actual"])
print("  rendered in the template (' and'), still true:", mv.check(as_template, OPEN["second"])["ok"],
      "| differs from given only by that comma:", as_template == given.replace(", and one z.", " and one z."))
