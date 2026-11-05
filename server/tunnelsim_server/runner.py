"""Batch runner: run a scene, write its result with a run record to results/<name>.json.

    python -m tunnelsim_server.runner face --voxel 0.2 --name face_v0.2
    python -m tunnelsim_server.runner k0 --phi 34 --E 5e6 --name k0_phi34
    python -m tunnelsim_server.runner rankine --mu 0.5592 --voxel 0.1 --name rankine_mu0.56_v0.1
    python -m tunnelsim_server.runner collapse --run B00 --gate-speed 1.0 --name collapse_B00
"""
from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

from . import UNCALIBRATED
from .materials import PHASE0_SAND, Soil, drained_sand, undrained_clay
from .runrecord import gpu_snapshot, record
from .scenes import collapse, face, face_sand, k0, rankine, tunnel_2d

RESULTS = Path(__file__).resolve().parent.parent / "results"
# Face soils (WP2): rigid-plastic Drucker-Prager, mu = sin phi' (WP1)
FACE_SOILS = {
    "idinger": drained_sand("Idinger et al. (2011) dry sand", 1500.0, 34.0, 1.0e15,
                            "Idinger, Aklik, Wu & Borja (2011), doi:10.1007/s11440-011-0139-2: rho_d 1.5 t/m3, phi 34 deg (direct shear), c' 0"),
    # Kimura & Mair (1981): kaolin, cu 26 kPa; gamma D / cu = 2.5 derived from their Figs 6 and 10 (gamma 14.4 kN/m3 at D 4.5 m)
    "kaolin": undrained_clay("Kimura & Mair (1981) kaolin", 14.4e3 / 9.81, 26.0e3, 1.0e15,
                             "Kimura & Mair (1981), 10th ICSMFE: cu 26 kPa; unit weight 14.4 kN/m3 from gamma D / cu = 2.5 (Figs 6 and 10)"),
    "wang33": drained_sand("Wang et al. (2024) sand, phi 33.1", 1580.0, 33.1, 1.0e15,
                           "Wang et al. (2024), doi:10.1016/j.undsp.2023.11.001, Table 1: gamma 15.5 kN/m3, phi 33.1 deg, c 0"),
}


def run(args) -> dict:
    gpu = gpu_snapshot()
    if args.scene == "face":
        cfg = face.FaceConfig(diameter=args.diameter, cover=args.cover, voxel=args.voxel, iterations=args.iterations, seed=args.seed)
        result, _ = face.run(cfg, PHASE0_SAND)
        return record("face", face.params(cfg, PHASE0_SAND), result, UNCALIBRATED, gpu)
    if args.scene == "face_sand":
        soil = FACE_SOILS[args.soil]
        if args.psi or args.match != "plane_strain":  # WP1b: dilation (Bolton 1986); cone matched in plane strain or triaxial
            soil = drained_sand(soil.name + f", psi {args.psi} deg, {args.match} match", soil.density, soil.phi_deg, soil.young_modulus,
                                soil.source + f"; psi {args.psi} deg (Bolton 1986); cone matched in {args.match}", psi_deg=args.psi,
                                match=args.match)
        if args.dilatancy:  # sensitivity only (WP2): not a calibrated parameter
            soil = dataclasses.replace(soil, dilatancy=args.dilatancy, name=soil.name + f", dilatancy {args.dilatancy}")
        cfg = face_sand.FaceSandConfig(diameter=args.diameter, cover=args.cover, retract_over_d=args.retract, voxel_per_d=args.vpd, control=args.control, target_kpa=args.target_kpa, rate_over_d=args.rate,
                                       iterations=args.iterations, seed=args.seed)
        result, _ = face_sand.run(cfg, soil)
        return record("face_sand", face_sand.params(cfg, soil), result, UNCALIBRATED, gpu)
    if args.scene == "tunnel_2d":
        soil = FACE_SOILS[args.soil]
        cfg = tunnel_2d.Tunnel2DConfig(diameter=args.diameter, cover=args.cover, voxel_per_d=args.vpd, iterations=args.iterations, seed=args.seed)
        result, _ = tunnel_2d.run(cfg, soil)
        return record("tunnel_2d", tunnel_2d.params(cfg, soil), result, UNCALIBRATED, gpu)
    if args.scene == "k0":
        soil = drained_sand("element-test sand", 1600.0, args.phi, args.E, "element test (assumed values)", k0=args.k0)
        cfg = k0.K0Config(voxel=args.voxel, iterations=args.iterations, seed=args.seed)
        result, _ = k0.run(cfg, soil)
        return record("k0", k0.params(cfg, soil), result, UNCALIBRATED, gpu)
    if args.scene == "rankine":
        if args.psi is not None:  # WP1b: (phi', psi) through the plane-strain mapping
            soil = drained_sand("element-test sand", 1600.0, args.phi, 1.0e15, "element test (assumed values)", psi_deg=args.psi)
        else:
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
    for name, voxel in (("face", 0.1), ("face_sand", 0.0), ("tunnel_2d", 0.0), ("k0", 0.1), ("rankine", 0.1), ("collapse", 0.005)):
        s = sub.add_parser(name)
        s.add_argument("--voxel", type=float, default=voxel)
        s.add_argument("--iterations", type=int, default=50)
        s.add_argument("--seed", type=int, default=0)
        s.add_argument("--name", type=str, default=None)
        if name == "face":
            s.add_argument("--diameter", type=float, default=2.0)
            s.add_argument("--cover", type=float, default=1.0)
        if name == "tunnel_2d":
            s.add_argument("--soil", choices=["kaolin"], default="kaolin")
            s.add_argument("--diameter", type=float, default=4.5)
            s.add_argument("--cover", type=float, default=2.0)
            s.add_argument("--vpd", type=float, default=10.0)
        if name == "face_sand":
            s.add_argument("--soil", choices=["idinger", "wang33", "kaolin"], default="idinger")
            s.add_argument("--diameter", type=float, default=5.0)
            s.add_argument("--retract", type=float, default=0.05, help="total retraction / D")
            s.add_argument("--cover", type=float, default=1.0)
            s.add_argument("--vpd", type=float, default=10.0, help="D / voxel")
            s.add_argument("--control", choices=["displacement", "pressure"], default="displacement")
            s.add_argument("--target-kpa", type=float, default=0.0)
            s.add_argument("--dilatancy", type=float, default=0.0, help="Newton dilatancy factor 0-1 (sensitivity only)")
            s.add_argument("--rate", type=float, default=0.025, help="retraction speed, D per second (displacement control)")
            s.add_argument("--psi", type=float, default=0.0, help="dilation angle (deg), mapped with phi (WP1b)")
            s.add_argument("--match", choices=["plane_strain", "triaxial"], default="plane_strain",
                           help="Drucker-Prager cone matched to phi in plane strain (weakest) or triaxial compression (strongest)")
        if name == "k0":
            s.add_argument("--phi", type=float, default=34.0)
            s.add_argument("--E", type=float, default=5e6)
            s.add_argument("--k0", type=float, default=None)
        if name == "rankine":
            s.add_argument("--mu", type=float, default=0.5592)
            s.add_argument("--phi", type=float, default=34.0, help="with --psi: Mohr-Coulomb friction angle")
            s.add_argument("--psi", type=float, default=None, help="dilation angle; maps (phi, psi) to Newton (WP1b)")
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
