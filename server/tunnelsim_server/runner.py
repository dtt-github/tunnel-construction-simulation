"""Batch runner: run a scene, write its result with a run record to results/<name>.json.

    python -m tunnelsim_server.runner face --voxel 0.2 --cover 1 --name face_v0.2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import UNCALIBRATED
from .materials import PHASE0_SAND
from .runrecord import gpu_snapshot, record
from .scenes import face

RESULTS = Path(__file__).resolve().parent.parent / "results"


def run_face(args) -> dict:
    cfg = face.FaceConfig(diameter=args.diameter, cover=args.cover, voxel=args.voxel, iterations=args.iterations, seed=args.seed)
    gpu = gpu_snapshot()
    result, _arrays = face.run(cfg, PHASE0_SAND)
    return record("face", face.params(cfg, PHASE0_SAND), result, UNCALIBRATED, gpu)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="scene", required=True)
    f = sub.add_parser("face")
    f.add_argument("--diameter", type=float, default=2.0)
    f.add_argument("--cover", type=float, default=1.0)
    f.add_argument("--voxel", type=float, default=0.1)
    f.add_argument("--iterations", type=int, default=50)
    f.add_argument("--seed", type=int, default=0)
    f.add_argument("--name", type=str, default=None)
    args = p.parse_args()
    rec = run_face(args)
    print(json.dumps(rec["result"], indent=2))
    print(rec["timing_note"])
    RESULTS.mkdir(exist_ok=True)
    name = args.name or f"{args.scene}_v{args.voxel}_c{args.cover}"
    (RESULTS / f"{name}.json").write_text(json.dumps(rec, indent=2) + "\n")


if __name__ == "__main__":
    main()
