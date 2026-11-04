"""Phase 0 benchmark (b): tunnel face in dry sand under a retracting support plate (Newton implicit MPM).

Scene (Z up, tunnel axis along +x, face at x = 0):
- Sand block with a circular shield of diameter D: a static polygonal tube for x < 0 and a
  kinematic face plate (disc) inside it. Side walls are frictionless, so they act like symmetry planes.
- The bed settles with the plate fixed, then the plate retracts slowly into the shield
  (displacement control, as in centrifuge face tests). The normal force on the plate falls from
  roughly the at-rest value to a limit value when a failure mechanism forms in front of the face.

Reference (public): Vermeer, Ruse & Marcher (2002), "Tunnel heading stability in drained ground",
Felsbau 20(6), 8-18. For c' = 0 and phi' >= 20 deg, the limit support pressure is independent of
cover depth: p_f = gamma * D * N_gamma, with N_gamma = 1 / (9 tan phi) - 0.05.
Centrifuge tests in dry sand (Chambon & Corte 1994, J. Geotech. Eng. 120(7), 1148-1165,
doi:10.1061/(ASCE)0733-9410(1994)120:7(1148)) give limit pressures of the same order (about 0.1 gamma D).
"""

import argparse
import json
import math
import time

import numpy as np
import warp as wp

import newton
from newton.solvers import SolverImplicitMPM

G = 9.81


def vermeer_limit_pressure(gamma, D, phi):
    n_gamma = 1.0 / (9.0 * math.tan(phi)) - 0.05
    return gamma * D * n_gamma, n_gamma


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--diameter", type=float, default=2.0, help="tunnel diameter D (m)")
    p.add_argument("--cover", type=float, default=1.0, help="cover C/D above the crown")
    p.add_argument("--voxel", type=float, default=0.1)
    p.add_argument("--ppc", type=int, default=2, help="particles per voxel per axis")
    p.add_argument("--density", type=float, default=1600.0, help="bulk density kg/m3")
    p.add_argument("--friction", type=float, default=0.75, help="internal friction coefficient (tan phi)")
    p.add_argument("--steel-friction", type=float, default=0.3, help="soil-shield and soil-plate friction")
    p.add_argument("--retract", type=float, default=0.2, help="total plate retraction (m)")
    p.add_argument("--speed", type=float, default=0.05, help="retraction speed (m/s)")
    p.add_argument("--fps", type=float, default=60.0)
    p.add_argument("--settle", type=int, default=60, help="frames with the plate fixed")
    p.add_argument("--iterations", type=int, default=50)
    p.add_argument("--out", type=str, default=None)
    args = p.parse_args()

    wp.init()
    D = args.diameter
    R = D / 2
    dx = args.voxel
    zc = R + 0.75 * D  # tunnel axis height above the base
    zs = zc + R + args.cover * D  # ground surface
    x_back, x_front = 0.75 * D, 2.5 * D
    half_w = 1.5 * D
    t = max(0.05, dx * 0.5)  # plate and tube thickness

    builder = newton.ModelBuilder()
    # Static parts are kinematic bodies at rest, so each group gets its own collider friction.
    tube = builder.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
    side = builder.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
    # Shield tube: n static plates around the circumference, from behind the back wall to the face.
    n_seg = 32
    tube_len = x_back + 0.5
    for k in range(n_seg):
        th = 2 * math.pi * k / n_seg
        c = wp.vec3(-tube_len / 2, (R + t / 2) * math.cos(th), zc + (R + t / 2) * math.sin(th))
        q = wp.quat_from_axis_angle(wp.vec3(1.0, 0.0, 0.0), th - math.pi / 2)
        builder.add_shape_box(tube, xform=wp.transform(c, q), hx=tube_len / 2, hy=1.08 * R * math.tan(math.pi / n_seg), hz=t / 2)
    # Containing walls (frictionless) and base
    wall = 0.5
    walls = [
        (wp.vec3(-x_back - wall, 0, zs / 2), wall, half_w + 2 * wall, zs),
        (wp.vec3(x_front + wall, 0, zs / 2), wall, half_w + 2 * wall, zs),
        (wp.vec3(0.5 * (x_front - x_back), -half_w - wall, zs / 2), x_front + x_back, wall, zs),
        (wp.vec3(0.5 * (x_front - x_back), half_w + wall, zs / 2), x_front + x_back, wall, zs),
    ]
    for c, hx, hy, hz in walls:
        builder.add_shape_box(side, xform=wp.transform(c, wp.quat_identity()), hx=hx, hy=hy, hz=hz)
    builder.add_ground_plane()
    # Face plate: kinematic disc, axis along x, front surface at x = 0
    plate = builder.add_body(xform=wp.transform(wp.vec3(-t / 2, 0.0, zc), wp.quat_identity()), mass=100.0, is_kinematic=True)
    builder.add_shape_cylinder(
        plate,
        xform=wp.transform(wp.vec3(0.0), wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), math.pi / 2)),
        radius=R - 0.25 * t,
        half_height=t / 2,
    )
    model = builder.finalize()

    # Sand: jittered grid over the block, minus the shield interior behind the face
    h = dx / args.ppc
    rng = np.random.default_rng(0)
    gx = np.arange(-x_back + h / 2, x_front, h)
    gy = np.arange(-half_w + h / 2, half_w, h)
    gz = np.arange(h / 2, zs, h)
    X, Y, Z = np.meshgrid(gx, gy, gz, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    pts += rng.uniform(-0.25 * h, 0.25 * h, pts.shape)
    r_axis = np.hypot(pts[:, 1], pts[:, 2] - zc)
    keep = ~((pts[:, 0] < h / 2) & (r_axis < R + t + h / 2))
    pts = pts[keep].astype(np.float32)
    n_particles = len(pts)
    mass = float(h**3 * args.density)

    sand_builder = newton.ModelBuilder()
    SolverImplicitMPM.register_custom_attributes(sand_builder)
    sand_builder.add_particles(
        pos=[wp.vec3(*q) for q in pts],
        vel=[wp.vec3(0.0)] * n_particles,
        mass=[mass] * n_particles,
        radius=[h * 0.5] * n_particles,
        custom_attributes={"mpm:friction": [args.friction] * n_particles},
    )
    sand_model = sand_builder.finalize()

    cfg = SolverImplicitMPM.Config()
    cfg.voxel_size = dx
    cfg.max_iterations = args.iterations
    cfg.critical_fraction = 0.0
    cfg.strain_basis = "P0"
    solver = SolverImplicitMPM(sand_model, config=cfg)
    body_friction = {-1: 0.5, tube: args.steel_friction, side: 0.0, plate: args.steel_friction}
    solver.setup_collider(model=model)
    cbody = solver.collider_body_index.numpy()
    solver.setup_collider(model=model, collider_friction=[body_friction[int(b)] for b in cbody])

    state = model.state()
    sand_state = sand_model.state()
    sand_state.body_q = wp.clone(state.body_q)
    sand_state.body_qd = wp.zeros_like(state.body_qd)
    sand_state.body_f = wp.zeros_like(state.body_f)
    body_index = solver.collider_body_index.numpy()

    dt = 1.0 / args.fps
    q_np = sand_state.body_q.numpy()
    qd_np = np.zeros((model.body_count, 6), dtype=np.float32)
    qd_np[plate, 0] = -args.speed
    n_move = int(round(args.retract / args.speed * args.fps))

    log = []  # (retraction m, plate normal force N)
    frame_times = []
    for f in range(args.settle + n_move):
        moving = f >= args.settle
        if moving:
            q_np[plate, 0] -= args.speed * dt
            sand_state.body_q.assign(q_np)
            if f == args.settle:
                sand_state.body_qd.assign(qd_np)
        wp.synchronize()
        t0 = time.perf_counter()
        solver.step(sand_state, sand_state, contacts=None, control=None, dt=dt)
        wp.synchronize()
        frame_times.append(time.perf_counter() - t0)

        imp, _pos, cid = solver.collect_collider_impulses(sand_state)
        imp, cid = imp.numpy(), cid.numpy()
        valid = cid >= 0
        bids = np.full(cid.shape, -1)
        bids[valid] = body_index[np.clip(cid[valid], 0, len(body_index) - 1)]
        fx = float(-imp[bids == plate, 0].sum() / dt)  # soil pushes the plate towards -x
        log.append((max(0.0, (f - args.settle + 1) * args.speed * dt) if moving else 0.0, fx))

    log = np.array(log)
    frame_times = np.array(frame_times)
    area = math.pi * (R - 0.25 * t) ** 2
    gamma = args.density * G
    phi = math.atan(args.friction)
    p_ref, n_gamma = vermeer_limit_pressure(gamma, D, phi)
    sv_axis = gamma * (zs - zc)
    k0 = 1 - math.sin(phi)

    settle_f = log[args.settle - 10 : args.settle, 1].mean()
    tail = log[-int(0.25 * n_move) :, 1]  # last quarter of the retraction
    p_limit = float(tail.mean() / area)
    p_min = float(log[args.settle :, 1].min() / area)
    timed = frame_times[5:]
    mean_ms = float(timed.mean() * 1000)

    result = {
        "diameter_m": D,
        "cover_over_D": args.cover,
        "voxel_m": dx,
        "ppc_per_axis": args.ppc,
        "particles": int(n_particles),
        "iterations": args.iterations,
        "frame_dt_s": dt,
        "ms_per_frame": round(mean_ms, 2),
        "realtime_factor": round(dt / (mean_ms / 1000), 3),
        "particle_steps_per_s_millions": round(n_particles / (mean_ms / 1000) / 1e6, 2),
        "p_settled_kPa": round(settle_f / area / 1e3, 2),
        "p_at_rest_axis_kPa": round(k0 * sv_axis / 1e3, 2),
        "p_limit_kPa": round(p_limit / 1e3, 2),
        "p_min_kPa": round(p_min / 1e3, 2),
        "p_vermeer_kPa": round(p_ref / 1e3, 2),
        "vermeer_N_gamma": round(n_gamma, 4),
        "sim_N_gamma": round(p_limit / (gamma * D), 4),
        "ratio_sim_over_vermeer": round(p_limit / p_ref, 3),
        "retraction_m": args.retract,
        "speed_m_s": args.speed,
    }
    print(json.dumps(result, indent=2))
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(result, fh, indent=2)
        np.savez_compressed(
            args.out.replace(".json", ".npz"),
            particles=sand_state.particle_q.numpy(),
            force_log=log,
            frame_times=frame_times,
        )


if __name__ == "__main__":
    main()
