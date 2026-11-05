"""Rankine active-wall element test: a gravity-loaded sand block between frictionless walls (plane strain across y);
the front wall (frictionless) moves away slowly and the force on it falls to the active value. K_a = 2 F / (gamma H^2 W).

For a Mohr-Coulomb soil, K_a = (1 - sin phi) / (1 + sin phi) (Rankine 1857). It separates the two ways of matching
Newton's friction to phi: in plane strain with psi = 0, mu = sin(phi); in triaxial compression a given mu means a lower
phi and a higher K_a. Kinematic walls only: Newton's colliders cannot hold a constant normal stress, so a simple-shear
test under constant normal load is not possible; this wall test plays its role.
"""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass

import numpy as np

from ..materials import Soil
from ..probes import collider_forces
from .common import add_walls, fill_box, make_particles, make_solver

G = 9.81


@dataclass(frozen=True)
class RankineConfig:
    height: float = 2.0  # m, soil height H
    length: float = 4.0  # m, block length behind the wall (2 H: longer than the active wedge)
    width: float = 1.0  # m, across the plane-strain direction
    voxel: float = 0.1
    ppc: int = 2
    move: float = 0.08  # m, wall translation (4 % of H; the plateau is read at 0.5-3 %)
    speed: float = 0.05  # m/s
    fps: float = 60.0
    settle: int = 60
    iterations: int = 50
    seed: int = 0


def run(cfg: RankineConfig, soil: Soil) -> tuple[dict, dict]:
    import warp as wp

    import newton

    wp.init()
    H, L, W, dx = cfg.height, cfg.length, cfg.width, cfg.voxel
    t = max(0.3, 2 * dx)  # walls at least one voxel thick (Phase 0)
    b = newton.ModelBuilder()
    fixed = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
    add_walls(b, fixed, [((-t, L / 2, 0), (t, L, 2 * H)),  # back wall at x = 0 (x is along the block)
                         ((L / 2, -t, H), (L + 1.0, t, 2 * H)), ((L / 2, W + t, H), (L + 1.0, t, 2 * H))])
    b.add_ground_plane()
    wall = b.add_body(xform=wp.transform(wp.vec3(L + t, W / 2, H), wp.quat_identity()), mass=100.0, is_kinematic=True)
    b.add_shape_box(wall, xform=wp.transform_identity(), hx=t, hy=W / 2 + t, hz=H * 1.2)
    cm = b.finalize()

    h = dx / cfg.ppc
    pts = fill_box((0, 0, 0), (L, W, H), h, cfg.seed)
    pm = make_particles(pts, h, soil).finalize()
    # base rough (soil on soil), side and back walls frictionless, the moving wall frictionless
    solver = make_solver(pm, cm, dx, cfg.iterations, {-1: 1.0, fixed: 0.0, wall: 0.0})
    st = cm.state()
    s = pm.state()
    s.body_q, s.body_qd, s.body_f = wp.clone(st.body_q), wp.zeros_like(st.body_qd), wp.zeros_like(st.body_f)
    body_index = solver.collider_body_index.numpy()

    dt = 1.0 / cfg.fps
    q = s.body_q.numpy()
    qd = np.zeros((cm.body_count, 6), dtype=np.float32)
    qd[wall, 0] = cfg.speed
    n_move = int(round(cfg.move / cfg.speed * cfg.fps))
    log, times = [], []
    for f in range(cfg.settle + n_move):
        if f >= cfg.settle:
            q[wall, 0] += cfg.speed * dt
            s.body_q.assign(q)
            if f == cfg.settle:
                s.body_qd.assign(qd)
        wp.synchronize()
        t0 = time.perf_counter()
        solver.step(s, s, contacts=None, control=None, dt=dt)
        wp.synchronize()
        times.append(time.perf_counter() - t0)
        fx = float(collider_forces(solver, s, body_index, dt).get(wall, np.zeros(3))[0])
        log.append((max(0.0, (f - cfg.settle + 1) * cfg.speed * dt), fx))
    log = np.array(log)
    gamma = soil.density * G
    norm = 0.5 * gamma * H**2 * W
    k_settled = float(log[cfg.settle - 10:cfg.settle, 1].mean() / norm)
    # active plateau: wall movement 0.5-3 % of H; beyond that the soil slumps after the wall and H no longer applies
    d = log[cfg.settle:, 0]
    plateau = (d >= 0.005 * H) & (d <= 0.03 * H)
    k_active = float(-log[cfg.settle:, 1][plateau].mean() / norm)
    return {"particles": len(pts), "K_settled": round(-k_settled, 4), "K_active": round(k_active, 4),
            "ms_per_frame": round(float(np.mean(times[5:]) * 1000), 2)}, {"force_log": log}


def params(cfg: RankineConfig, soil: Soil) -> dict:
    return {**asdict(cfg), "soil": asdict(soil)}
