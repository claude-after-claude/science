#!/bin/bash
# Part 2: literal CLI commands, offline containers. $1 = solve | walk
V=$(cd "$(dirname "$0")" && pwd)
R=$(dirname "$V")
THIRD="Left on a shelf by a third visitor, this sentence contains exactly"
SECOND="Left on a shelf by a second visitor, this sentence contains exactly"
D="docker run --rm --network none --cpus 1 --user $(id -u):$(id -g) -v $R:/r:ro -w /r/sessions/shelf-1/autogram python:3.12-slim"
if [ "$1" = solve ]; then
  $D python3 -B fast.py solve "$THIRD" > $V/out/solve_third.txt 2>&1
  $D python3 -B fast.py solve "$SECOND" > $V/out/solve_second.txt 2>&1
else
  for seed in 0 1 2 3 4 5 6 7; do
    $D python3 -B autogram.py walk "$THIRD" $seed > $V/out/walk_third_seed$seed.txt 2>&1 &
  done
  wait
  for seed in 0 1 2 3 4 5 6 7; do
    $D python3 -B autogram.py walk "$SECOND" $seed > $V/out/walk_second_seed$seed.txt 2>&1 &
  done
  wait
fi
echo PART2 $1 DONE
