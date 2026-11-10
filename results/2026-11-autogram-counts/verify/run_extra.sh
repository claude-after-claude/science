#!/bin/bash
# provenance re-solve of the 300 rows (8 shards) + extra checks, offline containers
V=$(cd "$(dirname "$0")" && pwd)
R=$(dirname "$V")
D="docker run --rm --network none --cpus 1 --user $(id -u):$(id -g) -v $R:/r:ro -v $V/out:/r/verify/out python:3.12-slim"
for i in 0 1 2 3 4 5 6 7; do
  $D python3 -B /r/verify/resolve.py $i 8 300 > $V/out/resolve_shard$i.txt 2>&1 &
done
$D python3 -B /r/verify/extra_checks.py > $V/out/extra_checks.txt 2>&1 &
wait
cat $V/out/resolve_shard*.txt $V/out/extra_checks.txt
