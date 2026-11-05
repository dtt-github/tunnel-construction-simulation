"""Plane-strain circular tunnel: a slab of soil (thin across y, frictionless faces, so plane strain) with a tunnel of
diameter D along y. The tunnel wall is a ring of rigid segments that close in radially at a fixed rate; the soil's
radial pressure on them is the support pressure. In undrained clay it falls to the collapse value, compared with the
plane-strain centrifuge tests of Kimura & Mair (1981, Figs 6 and 10) and the plasticity bounds of Davis et al.
(1980). WP3 uses it to tell a material problem from a face-geometry problem.
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
class Tunnel2DConfig:
    diameter: float = 4.5
    cover: float = 2.0  # C/D
    voxel_per_d: float = 10.0
    ppc: int = 2
    thickness_over_d: float = 0.4  # slab thickness across y
    half_width_over_d: float = 3.0
    base_below_invert_over_d: float = 1.5
    contract_over_r: float = 0.1  # radial closure of the ring / R
    rate_over_r: float = 0.025  # per second
    n_seg: int = 24
    fps: float = 60.0
    settle: int = 60
    iterations: int = 50
    seed: int = 0


def run(cfg: Tunnel2DConfig, soil: Soil) -> tuple[dict, dict]:
    import warp as wp

    import newton

    wp.init()
    D, R = cfg.diameter, cfg.diameter / 2
    dx = D / cfg.voxel_per_d
    T = cfg.thickness_over_d * D
    hw = cfg.half_width_over_d * D
    zc = cfg.base_below_invert_over_d * D + R
    zs = zc + R + cfg.cover * D
    t = max(0.05 * D, dx)
    b = newton.ModelBuilder()
    fixed = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
    w = 0.5 * D
    add_walls(b, fixed, [((-hw - w, T / 2, zs / 2), (w, T, zs)), ((hw + w, T / 2, zs / 2), (w, T, zs)),
                         ((0.0, -w, zs / 2), (hw + 2 * w, w, zs)), ((0.0, T + w, zs / 2), (hw + 2 * w, w, zs))])
    b.add_ground_plane()
    segs, normals = [], []
    for k in range(cfg.n_seg):
        th = 2 * math.pi * (k + 0.5) / cfg.n_seg
        n = np.array([math.cos(th), 0.0, math.sin(th)])  # outward, in the x-z plane
        c = n * (R - t / 2) + np.array([0.0, T / 2, zc])
        q = wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), -th)
        body = b.add_body(xform=wp.transform(wp.vec3(*c), q), mass=1.0, is_kinematic=True)
        b.add_shape_box(body, xform=wp.transform_identity(), hx=t / 2, hy=T / 2 + 0.1 * D, hz=1.04 * R * math.tan(math.pi / cfg.n_seg))
        segs.append(body)
        normals.append(n)
    cm = b.finalize()

    h = dx / cfg.ppc
    pts = fill_box((-hw, 0.0, 0.0), (hw, T, zs), h, cfg.seed)
    pts = pts[np.hypot(pts[:, 0], pts[:, 2] - zc) > R + 0.5 * h]
    pm = make_particles(pts, h, soil).finalize()
    fr = {fixed: 0.0, -1: 0.5, **{s: 0.0 for s in segs}}  # smooth tunnel wall (as a pressurised bag)
    solver = make_solver(pm, cm, dx, cfg.iterations, fr)
    st = cm.state()
    s = pm.state()
    s.body_q, s.body_qd, s.body_f = wp.clone(st.body_q), wp.zeros_like(st.body_qd), wp.zeros_like(st.body_f)
    body_index = solver.collider_body_index.numpy()
    q0 = s.body_q.numpy().copy()
    dt = 1.0 / cfg.fps
    n_move = int(round(cfg.contract_over_r / cfg.rate_over_r * cfg.fps))
    area = 2 * math.pi * R * T
    log, times = [], []
    for f in range(cfg.settle + n_move):
        if f >= cfg.settle:
            u = min((f - cfg.settle + 1) * cfg.rate_over_r * R * dt, cfg.contract_over_r * R)
            q = q0.copy()
            qd = np.zeros((cm.body_count, 6), dtype=np.float32)
            for body, n in zip(segs, normals):
                q[body, 0] -= n[0] * u
                q[body, 2] -= n[2] * u
                qd[body, 0], qd[body, 2] = -n[0] * cfg.rate_over_r * R, -n[2] * cfg.rate_over_r * R
            s.body_q.assign(q)
            s.body_qd.assign(qd)
        wp.synchronize()
        t0 = time.perf_counter()
        solver.step(s, s, contacts=None, control=None, dt=dt)
        wp.synchronize()
        times.append(time.perf_counter() - t0)
        forces = collider_forces(solver, s, body_index, dt)
        # probes give the force of each body on the soil; the ring holds the soil back outwards, so p = sum(F . n_out) / area
        p = sum(float(np.dot(forces.get(body, np.zeros(3)), n)) for body, n in zip(segs, normals)) / area  # force of the ring on the soil, outward
        log.append((max(0.0, (f - cfg.settle + 1) * cfg.rate_over_r * R * dt) if f >= cfg.settle else 0.0, p))
    log = np.array(log)
    ctrl = log[cfg.settle:]

    def p_at(frac):
        i = np.searchsorted(ctrl[:, 0] / R, frac)
        return None if i >= len(ctrl) else float(np.mean(ctrl[max(i - 3, 0):i + 4, 1]) / 1e3)

    gamma = soil.density * G
    sz = gamma * (zs - zc)
    res = {"diameter_m": D, "cover_over_D": cfg.cover, "voxel_per_D": cfg.voxel_per_d, "particles": len(pts),
           "p_settled_kPa": round(float(np.mean(log[cfg.settle - 10:cfg.settle, 1])) / 1e3, 2), "sigma_z_axis_kPa": round(sz / 1e3, 2)}
    for frac in (0.02, 0.05, 0.1):
        p = p_at(frac)
        res[f"p_{int(frac * 100)}pctR_kPa"] = None if p is None else round(p, 2)
        if soil.cohesion and p is not None:
            res[f"N_{int(frac * 100)}pctR"] = round((sz / 1e3 - p) / (soil.cohesion / 1e3), 3)
    res["ms_per_frame"] = round(float(np.mean(times[5:]) * 1000), 2)
    return res, {"log": log}


def params(cfg: Tunnel2DConfig, soil: Soil) -> dict:
    return {**asdict(cfg), "soil": asdict(soil)}
