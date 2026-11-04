#!/bin/sh
# EPB chamber sweep: resolution and screw speed, 10 s simulated each. Writes logs/epb_*.json/.npz
set -e
PY=.venv-newton/bin/python
for v in 0.2 0.1; do
  for n in 0 5 10 20; do
    $PY epb_bench.py --voxel $v --screw-rpm $n --frames 600 --out logs/epb_v${v}_screw${n}.json > /dev/null 2>&1
  done
done
