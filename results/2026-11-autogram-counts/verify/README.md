# verify/

Checks of the autogram code in `../sessions/shelf-1/autogram/` (`autogram.py`, `fast.py`, the
census in `census/english.tsv`). `myverify.py` is the independent part. The other scripts run the
session code unmodified and judge what it returns with `myverify.py`.

| File | What it is |
|---|---|
| `myverify.py` | Independent autogram checker: its own number words, parser and letter count. Imports nothing from the session code. |
| `walk_driver.py` | Runs `autogram.walk` (the random search) on census rows, one JSON line per (row, seed). |
| `analyze.py` | Part 1. Recounts every stored census solution of the tested rows with `myverify`, then checks each sentence the walk found: is it true, and is it in the census? |
| `resolve.py` | Reruns `fast.FastSolver` on census rows and compares solution count, node count and solutions with the stored census row. |
| `extra_checks.py` | The `autogram.py walk` CLI gives the same sentence as the imported function. The aborted 12-seed walk run agrees with the final run where they overlap. Counts by distinct opening string. |
| `part2_analyze.py` | Part 2. Checks with `myverify` the output of `fast.py solve` and `autogram.py walk` for the second and third visitor openings, and the sentence in `second_visitor.txt`. |
| `second_visitor.txt` | The second visitor's sentence, as given. |
| `speed.py` | Timing probe for the walk (12 rows, 3 seeds); its output was not kept. |
| `run_walks.sh`, `run_extra.sh`, `run_part2.sh` | Run the walk driver, the re-solve with the extra checks, and the part-2 CLI commands in offline `python:3.12-slim` Docker containers, one CPU each, with `sessions/` mounted read-only. |
| `session_reruns.sh` | Reruns the shelf-1 session's own commands on a copy (`fast.py solve`, `check`, `tally` on all six census files, `planted 200`, `volume.py selftest`) and times them. |
| `out/` | Outputs, listed below. |

## Running

The `.sh` scripts need Docker and write into `out/`, replacing the outputs kept there. The analysis
scripts need only Python 3 and read `out/`. Run `.py` files with `python3 -B` so that no
`__pycache__` is written. Timings are with one CPU per container.

| Command | Writes | Time |
|---|---|---|
| `bash run_walks.sh` | `out/walk_shard*.jsonl`, `out/walk_start`, `out/walk_end` | 15 min (8 containers) |
| `python3 -B analyze.py 300 6` | `out/part1_report.txt` (redirect stdout) | seconds |
| `bash run_extra.sh` | `out/resolve_shard*.txt`, `out/extra_checks.txt` | under 1 min |
| `bash run_part2.sh solve` | `out/solve_third.txt`, `out/solve_second.txt` | a few seconds |
| `bash run_part2.sh walk` | `out/walk_third_seed*.txt`, `out/walk_second_seed*.txt` | about 1 min |
| `python3 -B part2_analyze.py` | `out/part2_report.txt` (redirect stdout) | under 1 s |
| `./session_reruns.sh` | `out/session_reruns.txt` | about 3 min, one core, no Docker |

`analyze.py 300 6` means the first 300 census rows and seeds 0 to 5, the arguments `run_walks.sh`
passes to `walk_driver.py`. `out/aborted_12seeds/` holds the partial output of an earlier walk run
with 12 seeds that was stopped; `extra_checks.py` compares it with the final run.
