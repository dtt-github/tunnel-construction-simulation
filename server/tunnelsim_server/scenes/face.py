"""Tunnel face in dry sand under a retracting support plate (Newton implicit MPM). Ported unchanged from the Phase 0
benchmark (phase0/face_bench.py) so its results can be reproduced and pinned; WP2 replaces the retracting plate with
a pressure-controlled face.

Scene (Z up, tunnel axis along +x, face at x = 0): a sand block with a circular shield of diameter D (a static polygonal
tube for x < 0) and a kinematic face plate inside it. Side walls are frictionless, so they act like symmetry planes.
The bed settles with the plate fixed, then the plate retracts slowly into the shield. The normal force on the plate
falls from about the at-rest value to a limit value once a failure mechanism forms ahead of the face.

Reference: Vermeer, Ruse & Marcher (2002), Tunnel heading stability in drained ground, Felsbau 20(6): for c' = 0 the
limit support pressure is p_f = gamma D N_gamma, N_gamma = 1 / (9 tan phi) - 0.05, independent of cover.
"""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass

import numpy as np

from ..materials import PHASE0_SAND, Soil
from ..probes import collider_forces

G = 9.81


@dataclass(frozen=True)
class FaceConfig:
    diameter: float = 2.0  # m
    cover: float = 1.0  # C/D above the crown
    voxel: float = 0.1  # m
    ppc: int = 2  # particles per voxel per axis
    steel_friction: float = 0.3  # soil-shield and soil-plate
    retract: float = 0.2  # m, total plate retraction
    speed: float = 0.05  # m/s
    fps: float = 60.0
    settle: int = 60  # frames with the plate fixed
    iterations: int = 50
    seed: int = 0


def vermeer_limit_pressure(gamma: float, d: float, phi: float) -> tuple[float, float]:
    n_gamma = 1.0 / (9.0 * math.tan(phi)) - 0.05
    return gamma * d * n_gamma, n_gamma


def run(cfg: FaceConfig, soil: Soil = PHASE0_SAND) -> tuple[dict, dict]:
    """Run the scene. Returns (result, arrays): summary numbers, and the force log and frame times."""
    import warp as wp

    import newton
    from newton.solvers import SolverImplicitMPM

    wp.init()
    D, R, dx = cfg.diameter, cfg.diameter / 2, cfg.voxel
    zc = R + 0.75 * D  # tunnel axis height above the base
    zs = zc + R + cfg.cover * D  # ground surface
    x_back, x_front = 0.75 * D, 2.5 * D
    half_w = 1.5 * D
    t = max(0.05, dx * 0.5)  # plate and tube thickness

    builder = newton.ModelBuilder()
    tube = builder.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
    side = builder.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
    n_seg, tube_len = 32, x_back + 0.5
    for k in range(n_seg):
        th = 2 * math.pi * k / n_seg
        c = wp.vec3(-tube_len / 2, (R + t / 2) * math.cos(th), zc + (R + t / 2) * math.sin(th))
        q = wp.quat_from_axis_angle(wp.vec3(1.0, 0.0, 0.0), th - math.pi / 2)
        builder.add_shape_box(tube, xform=wp.transform(c, q), hx=tube_len / 2, hy=1.08 * R * math.tan(math.pi / n_seg), hz=t / 2)
    wall = 0.5
    for c, hx, hy, hz in (
        (wp.vec3(-x_back - wall, 0, zs / 2), wall, half_w + 2 * wall, zs),
        (wp.vec3(x_front + wall, 0, zs / 2), wall, half_w + 2 * wall, zs),
        (wp.vec3(0.5 * (x_front - x_back), -half_w - wall, zs / 2), x_front + x_back, wall, zs),
        (wp.vec3(0.5 * (x_front - x_back), half_w + wall, zs / 2), x_front + x_back, wall, zs),
    ):
        builder.add_shape_box(side, xform=wp.transform(c, wp.quat_identity()), hx=hx, hy=hy, hz=hz)
    builder.add_ground_plane()
    plate = builder.add_body(xform=wp.transform(wp.vec3(-t / 2, 0.0, zc), wp.quat_identity()), mass=100.0, is_kinematic=True)
    builder.add_shape_cylinder(plate, xform=wp.transform(wp.vec3(0.0), wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), math.pi / 2)),
                               radius=R - 0.25 * t, half_height=t / 2)
    model = builder.finalize()

    # Sand: jittered grid over the block, minus the shield interior behind the face
    h = dx / cfg.ppc
    rng = np.random.default_rng(cfg.seed)
    gx, gy, gz = np.arange(-x_back + h / 2, x_front, h), np.arange(-half_w + h / 2, half_w, h), np.arange(h / 2, zs, h)
    X, Y, Z = np.meshgrid(gx, gy, gz, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    pts += rng.uniform(-0.25 * h, 0.25 * h, pts.shape)
    r_axis = np.hypot(pts[:, 1], pts[:, 2] - zc)
    pts = pts[~((pts[:, 0] < h / 2) & (r_axis < R + t + h / 2))].astype(np.float32)
    n = len(pts)

    sand_builder = newton.ModelBuilder()
    SolverImplicitMPM.register_custom_attributes(sand_builder)
    sand_builder.add_particles(pos=[wp.vec3(*q) for q in pts], vel=[wp.vec3(0.0)] * n, mass=[float(h**3 * soil.density)] * n,
                               radius=[h * 0.5] * n, custom_attributes=soil.custom_attributes(n))
    sand_model = sand_builder.finalize()

    scfg = SolverImplicitMPM.Config()
    scfg.voxel_size = dx
    scfg.max_iterations = cfg.iterations
    scfg.critical_fraction = 0.0
    scfg.strain_basis = "P0"
    solver = SolverImplicitMPM(sand_model, config=scfg)
    body_friction = {-1: 0.5, tube: cfg.steel_friction, side: 0.0, plate: cfg.steel_friction}
    solver.setup_collider(model=model)
    solver.setup_collider(model=model, collider_friction=[body_friction[int(b)] for b in solver.collider_body_index.numpy()])

    state = model.state()
    sand_state = sand_model.state()
    sand_state.body_q = wp.clone(state.body_q)
    sand_state.body_qd = wp.zeros_like(state.body_qd)
    sand_state.body_f = wp.zeros_like(state.body_f)
    body_index = solver.collider_body_index.numpy()

    dt = 1.0 / cfg.fps
    q_np = sand_state.body_q.numpy()
    qd_np = np.zeros((model.body_count, 6), dtype=np.float32)
    qd_np[plate, 0] = -cfg.speed
    n_move = int(round(cfg.retract / cfg.speed * cfg.fps))
    area = math.pi * (R - 0.25 * t) ** 2

    log, frame_times = [], []
    for f in range(cfg.settle + n_move):
        moving = f >= cfg.settle
        if moving:
            q_np[plate, 0] -= cfg.speed * dt
            sand_state.body_q.assign(q_np)
            if f == cfg.settle:
                sand_state.body_qd.assign(qd_np)
        wp.synchronize()
        t0 = time.perf_counter()
        solver.step(sand_state, sand_state, contacts=None, control=None, dt=dt)
        wp.synchronize()
        frame_times.append(time.perf_counter() - t0)
        fx = float(collider_forces(solver, sand_state, body_index, dt).get(plate, np.zeros(3))[0])
        log.append((max(0.0, (f - cfg.settle + 1) * cfg.speed * dt) if moving else 0.0, fx))

    log, frame_times = np.array(log), np.array(frame_times)
    gamma, phi = soil.density * G, math.atan(soil.friction)
    p_ref, n_gamma = vermeer_limit_pressure(gamma, D, phi)
    p_limit = float(log[-int(0.25 * n_move):, 1].mean() / area)
    mean_ms = float(frame_times[5:].mean() * 1000)
    result = {
        "particles": n,
        "ms_per_frame": round(mean_ms, 2),
        "realtime_factor": round(dt / (mean_ms / 1000), 3),
        "p_settled_kPa": round(float(log[cfg.settle - 10:cfg.settle, 1].mean()) / area / 1e3, 3),
        "p_at_rest_axis_kPa": round((1 - math.sin(phi)) * gamma * (zs - zc) / 1e3, 3),
        "p_limit_kPa": round(p_limit / 1e3, 3),
        "p_min_kPa": round(float(log[cfg.settle:, 1].min()) / area / 1e3, 3),
        "p_vermeer_kPa": round(p_ref / 1e3, 3),
        "vermeer_N_gamma": round(n_gamma, 4),
        "ratio_sim_over_vermeer": round(p_limit / p_ref, 4),
    }
    return result, {"force_log": log, "frame_times": frame_times}


def params(cfg: FaceConfig, soil: Soil) -> dict:
    return {**asdict(cfg), "soil": asdict(soil)}
