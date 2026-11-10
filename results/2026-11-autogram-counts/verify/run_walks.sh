#!/bin/bash
# 8 offline containers, one CPU each, shard = row index mod 8
V=$(cd "$(dirname "$0")" && pwd)
R=$(dirname "$V")
D="docker run --rm --network none --cpus 1 --user $(id -u):$(id -g) -v $R:/r:ro -v $V/out:/r/verify/out python:3.12-slim"
date +%s > $V/out/walk_start
for i in 0 1 2 3 4 5 6 7; do
  $D python3 -B /r/verify/walk_driver.py --shard $i --nshards 8 --nrows 300 --nseeds 6 --max-iter 300000 --out /r/verify/out/walk_shard$i.jsonl &
done
wait
date +%s > $V/out/walk_end
echo ALL DONE
