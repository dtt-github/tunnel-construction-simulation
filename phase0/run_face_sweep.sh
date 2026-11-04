#!/bin/sh
# Face-stability sweep: resolution and friction angle. Writes logs/face_*.json/.npz
set -e
PY=.venv-newton/bin/python
for v in 0.2 0.15 0.1; do
  $PY face_bench.py --voxel $v --retract 0.2 --speed 0.05 --out logs/face_v${v}_mu0.75.json > /dev/null 2>&1
done
for mu in 0.58 0.9; do
  $PY face_bench.py --voxel 0.15 --friction $mu --retract 0.2 --speed 0.05 --out logs/face_v0.15_mu${mu}.json > /dev/null 2>&1
done
$PY face_bench.py --voxel 0.15 --cover 2.0 --retract 0.2 --speed 0.05 --out logs/face_v0.15_mu0.75_c2.json > /dev/null 2>&1
