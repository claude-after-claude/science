#!/bin/bash
# Rerun the shelf-1 session's own commands on a copy and time them. Output: out/session_reruns.txt
#   ./session_reruns.sh            # about 3 minutes, one core, Python 3 only
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d)
cp -r "$HERE/../sessions/shelf-1/autogram" "$T/"
cd "$T/autogram"
OUT="$HERE/out/session_reruns.txt"
run() {
  echo "\$ $*"
  local t0=$(date +%s.%N)
  bash -c "$*" 2>&1
  echo "[$(echo "$(date +%s.%N) - $t0" | bc | xargs printf '%.1f') s]"
  echo
}
{
  echo "# $(date -u +%Y-%m-%dT%H:%MZ), python $(python3 -c 'import platform; print(platform.python_version())')"
  run 'python3 -B fast.py solve "This sentence contains"'
  run 'python3 -B fast.py check < results.txt'
  for f in english text flat box box-bag60 box-bag150; do
    run "python3 -B fast.py tally < census/$f.tsv"
  done
  run 'python3 -B fast.py planted 200'
  run 'python3 -B volume.py selftest'
} > "$OUT"
rm -rf "$T"
echo "wrote $OUT"
