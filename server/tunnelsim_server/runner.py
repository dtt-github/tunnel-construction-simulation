"""Batch runner: run a scene, write its result with a run record to results/<name>.json.

    python -m tunnelsim_server.runner face --voxel 0.2 --name face_v0.2
    python -m tunnelsim_server.runner k0 --phi 34 --E 5e6 --name k0_phi34
    python -m tunnelsim_server.runner rankine --mu 0.5592 --voxel 0.1 --name rankine_mu0.56_v0.1
    python -m tunnelsim_server.runner collapse --run B00 --gate-speed 1.0 --name collapse_B00
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import UNCALIBRATED
from .materials import PHASE0_SAND, Soil, drained_sand
from .runrecord import gpu_snapshot, record
from .scenes import collapse, face, k0, rankine

RESULTS = Path(__file__).resolve().parent.parent / "results"


def run(args) -> dict:
    gpu = gpu_snapshot()
    if args.scene == "face":
        cfg = face.FaceConfig(diameter=args.diameter, cover=args.cover, voxel=args.voxel, iterations=args.iterations, seed=args.seed)
        result, _ = face.run(cfg, PHASE0_SAND)
        return record("face", face.params(cfg, PHASE0_SAND), result, UNCALIBRATED, gpu)
    if args.scene == "k0":
        soil = drained_sand("element-test sand", 1600.0, args.phi, args.E, "element test (assumed values)", k0=args.k0)
        cfg = k0.K0Config(voxel=args.voxel, iterations=args.iterations, seed=args.seed)
        result, _ = k0.run(cfg, soil)
        return record("k0", k0.params(cfg, soil), result, UNCALIBRATED, gpu)
    if args.scene == "rankine":
        soil = Soil("element-test sand", 1600.0, args.mu, "element test (assumed values)")
        cfg = rankine.RankineConfig(voxel=args.voxel, iterations=args.iterations, seed=args.seed)
        result, _ = rankine.run(cfg, soil)
        return record("rankine", rankine.params(cfg, soil), result, UNCALIBRATED, gpu)
    gate = args.gate_speed if args.gate_speed and args.gate_speed > 0 else None  # 0: remove the gate at once
    cfg = collapse.CollapseConfig(run=args.run, gate_speed=gate, voxel=args.voxel, iterations=args.iterations, seed=args.seed)
    result, _ = collapse.run(cfg)
    return record("collapse", collapse.params(cfg), result, UNCALIBRATED, gpu)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="scene", required=True)
    for name, voxel in (("face", 0.1), ("k0", 0.1), ("rankine", 0.1), ("collapse", 0.005)):
        s = sub.add_parser(name)
        s.add_argument("--voxel", type=float, default=voxel)
        s.add_argument("--iterations", type=int, default=50)
        s.add_argument("--seed", type=int, default=0)
        s.add_argument("--name", type=str, default=None)
        if name == "face":
            s.add_argument("--diameter", type=float, default=2.0)
            s.add_argument("--cover", type=float, default=1.0)
        if name == "k0":
            s.add_argument("--phi", type=float, default=34.0)
            s.add_argument("--E", type=float, default=5e6)
            s.add_argument("--k0", type=float, default=None)
        if name == "rankine":
            s.add_argument("--mu", type=float, default=0.5592)
        if name == "collapse":
            s.add_argument("--run", type=str, default="B00")
            s.add_argument("--gate-speed", type=float, default=1.0, help="m/s (assumed); 0 removes the gate at once")
    args = p.parse_args()
    rec = run(args)
    print(json.dumps(rec["result"], indent=2))
    print(rec["timing_note"])
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{args.name or args.scene}.json").write_text(json.dumps(rec, indent=2) + "\n")


if __name__ == "__main__":
    main()
