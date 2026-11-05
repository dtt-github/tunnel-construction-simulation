"""Granular column collapse in a narrow flume, after Rousseau, Metivet, Rousseau, Daviet & Bertails-Descoubes (2022),
Nonsmooth simulations of 3D Drucker-Prager granular flows and validation against experimental column collapses,
arXiv:2211.04865 (data CC-BY 4.0, doi:10.5281/zenodo.7288829).

Set-up as in their section 3.2 and table 1: a column L0 long and H0 high behind a gate at x = L0, in a W = 6 cm wide
flume whose floor carries a 2 cm erodible bed of the same material; the flume is inclined by i (here: gravity tilted,
x downslope). Side walls and the upstream wall have the measured wall friction mu_w. The material is perfectly plastic
Drucker-Prager with mu equal to the measured avalanche coefficient mu_a (their recommendation), which Newton's
`friction` represents directly (same criterion, see materials.py).

The gate's lifting speed is not given in the paper; it is either removed at t = 0 or lifted at an assumed speed.
Measured: the final upslope height H_f at the upstream wall and the run-out L_f - L0 from the gate (their table 2).
"""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass

import numpy as np

from ..materials import Soil
from .common import add_walls, fill_box, make_particles, make_solver

G = 9.81
SOURCE = "Rousseau et al. (2022), arXiv:2211.04865, tables 1-2"
BEADS = Soil("0.5 mm glass beads", 1470.0, 0.44, SOURCE + ": rho_c 1470 kg/m3, mu_a 0.44, mu_w 0.23", extra={"mu_w": 0.23})
GRANULES = Soil("2.7 mm granules", 1520.0, 0.75, SOURCE + ": rho_c 1520 kg/m3, mu_a 0.75, mu_w 0.3", extra={"mu_w": 0.3})
# run: (material, inclination deg, H0 m, aspect a, H_f exp m, run-out exp m (None: not measured), run-out of their simulation m)
RUNS = {
    "B00": ("beads", 0, 0.11, 0.5, 0.11, 0.18, 0.19), "B05": ("beads", 5, 0.11, 0.5, 0.11, 0.22, 0.21),
    "B10": ("beads", 10, 0.11, 0.5, 0.09, 0.31, 0.30), "B15": ("beads", 15, 0.11, 0.5, 0.07, 0.49, 0.46),
    "B20": ("beads", 20, 0.11, 0.5, 0.04, None, 0.88),
    "G00": ("granules", 0, 0.11, 0.6, 0.12, 0.11, 0.10), "G05": ("granules", 5, 0.12, 0.6, 0.12, 0.15, 0.13),
    "G10": ("granules", 10, 0.12, 0.4, 0.12, 0.10, 0.15), "G15": ("granules", 15, 0.12, 0.4, 0.12, 0.24, 0.19),
}


@dataclass(frozen=True)
class CollapseConfig:
    run: str = "B00"
    voxel: float = 0.005
    ppc: int = 2
    width: float = 0.06
    bed: float = 0.02
    gate_speed: float | None = None  # m/s; None removes the gate at t = 0 (speed not published)
    fps: float = 240.0
    t_max: float = 4.0
    rest_speed: float = 0.01  # m/s, their rest criterion
    iterations: int = 50
    seed: int = 0


def run(cfg: CollapseConfig) -> tuple[dict, dict]:
    import warp as wp

    import newton

    wp.init()
    mat, incl, H0, a, hf_exp, ro_exp, ro_sim = RUNS[cfg.run]
    soil = BEADS if mat == "beads" else GRANULES
    L0 = H0 / a
    W, bed, dx = cfg.width, cfg.bed, cfg.voxel
    length = L0 + 1.1
    i = math.radians(incl)
    t = max(0.02, 2 * dx)
    b = newton.ModelBuilder(gravity=(G * math.sin(i), 0.0, -G * math.cos(i)))
    walls = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
    top = bed + H0 + 0.1
    add_walls(b, walls, [((-t, W / 2, top / 2), (t, W, top)),  # upstream wall at x = 0
                         ((length / 2, -t, top / 2), (length, t, top)), ((length / 2, W + t, top / 2), (length, t, top))])
    floor = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
    add_walls(b, floor, [((length / 2, W / 2, -t), (length + 0.2, W, t))])
    gate = b.add_body(xform=wp.transform(wp.vec3(L0 + t, W / 2, bed + H0 / 2 + 0.01), wp.quat_identity()), mass=1.0, is_kinematic=True)
    b.add_shape_box(gate, xform=wp.transform_identity(), hx=t, hy=W / 2 + t, hz=H0 / 2 + 0.02)
    cm = b.finalize()

    h = dx / cfg.ppc
    pts = np.concatenate([fill_box((0, 0, 0), (length, W, bed), h, cfg.seed), fill_box((0, 0, bed), (L0, W, bed + H0), h, cfg.seed + 1)])
    pb = make_particles(pts, h, soil)
    pb.gravity = b.gravity
    pm = pb.finalize()
    pm.set_gravity((G * math.sin(i), 0.0, -G * math.cos(i)))
    mu_w = soil.extra["mu_w"]
    solver = make_solver(pm, cm, dx, cfg.iterations, {walls: mu_w, gate: mu_w, floor: 1.0, -1: 1.0})
    st = cm.state()
    s = pm.state()
    s.body_q, s.body_qd, s.body_f = wp.clone(st.body_q), wp.zeros_like(st.body_qd), wp.zeros_like(st.body_f)
    q = s.body_q.numpy()
    dt = 1.0 / cfg.fps
    if cfg.gate_speed is None:  # remove the gate at once: move it far up out of the domain
        q[gate, 2] += 10.0
        s.body_q.assign(q)
    else:
        qd = np.zeros((cm.body_count, 6), dtype=np.float32)
        qd[gate, 2] = cfg.gate_speed
        s.body_qd.assign(qd)

    times, t_rest, step = [], None, 0
    while step * dt < cfg.t_max:
        if cfg.gate_speed is not None and q[gate, 2] < 5.0:
            q[gate, 2] += cfg.gate_speed * dt
            s.body_q.assign(q)
        wp.synchronize()
        t0 = time.perf_counter()
        solver.step(s, s, contacts=None, control=None, dt=dt)
        wp.synchronize()
        times.append(time.perf_counter() - t0)
        step += 1
        if step * dt > 0.3 and step % 12 == 0:
            vmax = float(np.linalg.norm(s.particle_qd.numpy(), axis=1).max())
            if vmax < cfg.rest_speed:
                t_rest = step * dt
                break

    p = s.particle_q.numpy()
    # deposit thickness above the original bed, in x bins one particle spacing wide (whole width)
    bins = np.arange(0.0, length + h, h)
    idx = np.digitize(p[:, 0], bins) - 1
    zmax = np.full(len(bins), -np.inf)
    np.maximum.at(zmax, np.clip(idx, 0, len(bins) - 1), p[:, 2])
    thick = zmax - bed
    hf = float(np.nanmax(thick[: max(int(0.01 / h), 1)]))  # within 1 cm of the upstream wall
    def front(threshold: float) -> float:
        k = np.where(thick > threshold)[0]
        return float(bins[k.max()] + h) if len(k) else float("nan")

    lf = front(h)  # thicker than one particle spacing
    lf5 = front(0.005)
    result = {"run": cfg.run, "material": soil.name, "inclination_deg": incl, "H0": H0, "L0": round(L0, 4), "particles": len(pts),
              "t_rest_s": t_rest, "Hf_sim": round(hf, 4), "Hf_exp": hf_exp, "runout_sim": round(lf - L0, 4), "runout_sim_5mm": round(lf5 - L0, 4), "runout_exp": ro_exp,
              "runout_rousseau_sim": ro_sim, "ms_per_step": round(float(np.mean(times[5:]) * 1000), 2)}
    return result, {"profile_x": bins, "profile_thickness": thick}


def params(cfg: CollapseConfig) -> dict:
    return asdict(cfg)
