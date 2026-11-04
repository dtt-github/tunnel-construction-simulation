"""Phase 0 benchmark (a): EPB excavation chamber with a rotating cutterhead and a screw conveyor (Newton implicit MPM).

Scene (Z up, machine axis along +x, excavation towards +x):
- Chamber of diameter D between the bulkhead (x = 0) and the cutterhead (x = L), filled with
  conditioned soil (low friction, small cohesion). A slab of soil in front of the cutterhead is
  pushed into the chamber by a kinematic "ground" piston at the advance rate.
- Cutterhead: kinematic spokes and mixing arms rotating about the machine axis.
- Screw conveyor: rotating shaft with a staircase helix of flights inside a square casing. It enters
  through a hole at the bottom of the bulkhead, rises at angle alpha and discharges behind the machine.

Measured per frame: wall-clock time, bulkhead pressure (top/axis/bottom bands, like the chamber
sensors of a real EPB), cutterhead and screw torque, screw discharge. The theoretical screw capacity
Q = A_free * pitch * n is the usual reference (e.g. Merritt & Mair 2006, Geotechnique 56(9) 605-615,
doi:10.1680/geot.2006.56.9.605); the ratio Q_sim / Q_th is the volumetric efficiency.
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


def qmul(a, b):
    x1, y1, z1, w1 = a
    x2, y2, z2, w2 = b
    return np.array(
        [
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        ]
    )


def qaxis(axis, ang):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    return np.array([*(axis * math.sin(ang / 2)), math.cos(ang / 2)])


def rotate_x_plate(c, th):
    """Box transform at body-frame position c whose local z points radially at angle th about x."""
    return wp.transform(wp.vec3(*c), wp.quat_from_axis_angle(wp.vec3(1.0, 0.0, 0.0), th - math.pi / 2))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--diameter", type=float, default=6.0, help="chamber diameter D (m)")
    p.add_argument("--chamber", type=float, default=0.8, help="chamber length bulkhead to cutterhead (m)")
    p.add_argument("--slab", type=float, default=0.3, help="soil slab in front of the cutterhead (m)")
    p.add_argument("--voxel", type=float, default=0.1)
    p.add_argument("--ppc", type=int, default=2)
    p.add_argument("--density", type=float, default=1800.0)
    p.add_argument("--friction", type=float, default=0.35, help="conditioned soil friction coefficient")
    p.add_argument("--cohesion", type=float, default=2000.0, help="yield stress (Pa)")
    p.add_argument("--cutter-rpm", type=float, default=2.0)
    p.add_argument("--screw-rpm", type=float, default=10.0)
    p.add_argument("--screw-radius", type=float, default=0.4)
    p.add_argument("--screw-pitch", type=float, default=0.6)
    p.add_argument("--screw-length", type=float, default=4.0)
    p.add_argument("--screw-angle", type=float, default=20.0, help="inclination (deg)")
    p.add_argument("--advance", type=float, default=50.0, help="advance rate (mm/min)")
    p.add_argument("--fps", type=float, default=60.0)
    p.add_argument("--frames", type=int, default=300)
    p.add_argument("--iterations", type=int, default=50)
    p.add_argument("--out", type=str, default=None)
    args = p.parse_args()

    wp.init()
    D, L, dx = args.diameter, args.chamber, args.voxel
    R = D / 2
    zc = R + 0.5
    t = max(0.1, dx)  # walls at least one voxel thick, or soil tunnels through them
    a_s = args.screw_radius + 0.05  # casing inner half-width
    alpha = math.radians(args.screw_angle)
    u = np.array([-math.cos(alpha), 0.0, math.sin(alpha)])  # screw axis, from chamber to outlet
    z_b = zc - R + a_s + 0.6  # screw axis height where it crosses the bulkhead
    P_b = np.array([0.0, 0.0, z_b])
    s_in = -0.5  # flights protrude 0.5 m into the chamber
    s_c = -0.6  # the casing protrudes a little further, so it passes right through the bulkhead hole
    Ls = args.screw_length

    b = newton.ModelBuilder()
    shell = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True, label="shell")
    # Chamber skin: polygonal tube
    n_seg = 48
    x0, x1 = -0.1, L + args.slab + 0.4
    for k in range(n_seg):
        th = 2 * math.pi * k / n_seg
        b.add_shape_box(
            shell,
            xform=rotate_x_plate(((x0 + x1) / 2, (R + t / 2) * math.cos(th), zc + (R + t / 2) * math.sin(th)), th),
            hx=(x1 - x0) / 2,
            hy=1.08 * R * math.tan(math.pi / n_seg),
            hz=t / 2,
        )
    # Bulkhead (x in [-t, 0]) with a rectangular hole for the screw casing
    hole_y = a_s + t
    hole_lo = z_b - (a_s + t) / math.cos(alpha)
    hole_hi = z_b + (a_s + t) / math.cos(alpha)
    zb0, zb1 = zc - R - t, zc + R + t
    half = R + t
    for cz, hz, cy, hy in [
        ((hole_hi + zb1) / 2, (zb1 - hole_hi) / 2, 0.0, half),
        ((zb0 + hole_lo) / 2, (hole_lo - zb0) / 2, 0.0, half),
        ((hole_lo + hole_hi) / 2, (hole_hi - hole_lo) / 2, (hole_y + half) / 2, (half - hole_y) / 2),
        ((hole_lo + hole_hi) / 2, (hole_hi - hole_lo) / 2, -(hole_y + half) / 2, (half - hole_y) / 2),
    ]:
        b.add_shape_box(shell, xform=wp.transform(wp.vec3(-t / 2, cy, cz), wp.quat_identity()), hx=t / 2, hy=hy, hz=hz)
    bulkhead_shapes = 4

    # Screw casing: square duct along u from inside the chamber to the outlet, part of the shell body
    q_axis = qaxis([0, 1, 0], math.pi + alpha)  # maps local x onto u
    c_mid = P_b + u * (s_c + Ls) / 2
    for ly, lz, hy, hz in [(0, a_s + t / 2, a_s + t, t / 2), (0, -a_s - t / 2, a_s + t, t / 2), (a_s + t / 2, 0, t / 2, a_s), (-a_s - t / 2, 0, t / 2, a_s)]:
        off = np.array([0.0, ly, lz])
        # rotate the local offset by q_axis
        rot = wp.quat(*q_axis)
        c = c_mid + np.array(wp.quat_rotate(rot, wp.vec3(*off)))
        b.add_shape_box(shell, xform=wp.transform(wp.vec3(*c), rot), hx=(Ls - s_c) / 2, hy=hy, hz=hz)

    # Cutterhead: 6 spokes and 6 mixing arms, rotating about x through (x_ch, 0, zc)
    x_ch = L - 0.15
    cutter = b.add_body(xform=wp.transform(wp.vec3(x_ch, 0.0, zc), wp.quat_identity()), mass=1.0, is_kinematic=True, label="cutterhead")
    r0, r1 = 0.4, R - 0.08
    for k in range(6):
        th = 2 * math.pi * k / 6
        rm = (r0 + r1) / 2
        b.add_shape_box(cutter, xform=rotate_x_plate((0.0, rm * math.cos(th), rm * math.sin(th)), th), hx=0.1, hy=0.15, hz=(r1 - r0) / 2)
        # mixing arm reaching back into the chamber, at 0.6 R
        th2 = th + math.pi / 6
        ra = 0.6 * R
        b.add_shape_box(cutter, xform=rotate_x_plate((-0.3, ra * math.cos(th2), ra * math.sin(th2)), th2), hx=0.25, hy=0.08, hz=0.08)
    b.add_shape_cylinder(cutter, xform=wp.transform(wp.vec3(0.0), wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), math.pi / 2)), radius=r0, half_height=0.1)

    # Ground piston closing the front of the slab
    x_face = L + args.slab
    piston = b.add_body(xform=wp.transform(wp.vec3(x_face + t / 2, 0.0, zc), wp.quat_identity()), mass=1.0, is_kinematic=True, label="ground")
    b.add_shape_cylinder(piston, xform=wp.transform(wp.vec3(0.0), wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), math.pi / 2)), radius=R - 0.25 * t, half_height=t / 2)

    # Screw: shaft and staircase helix, body frame x along u, origin at P_b
    screw = b.add_body(xform=wp.transform(wp.vec3(*P_b), wp.quat(*q_axis)), mass=1.0, is_kinematic=True, label="screw")
    r_sh = 0.1
    rs = args.screw_radius
    b.add_shape_cylinder(
        screw,
        xform=wp.transform(wp.vec3((s_in + Ls) / 2, 0.0, 0.0), wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), math.pi / 2)),
        radius=r_sh,
        half_height=(Ls - s_in) / 2,
    )
    n_pt = 12
    pitch = args.screw_pitch
    n_fl = int((Ls - s_in) / pitch * n_pt)
    for k in range(n_fl):
        th = 2 * math.pi * k / n_pt
        s = s_in + k * pitch / n_pt
        rm = (r_sh + rs) / 2
        b.add_shape_box(screw, xform=rotate_x_plate((s, rm * math.cos(th), rm * math.sin(th)), th), hx=pitch / n_pt / 2, hy=1.1 * rs * math.tan(math.pi / n_pt), hz=(rs - r_sh) / 2)
    b.add_ground_plane()
    model = b.finalize()

    # Soil: chamber, slab and screw casing filled; a little headroom at the crown
    h = dx / args.ppc
    rng = np.random.default_rng(0)
    gx = np.arange(h / 2, x_face, h)
    gy = np.arange(-R, R, h)
    gz = np.arange(zc - R, zc + R, h)
    X, Y, Z = np.meshgrid(gx, gy, gz, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    pts = pts[(np.hypot(pts[:, 1], pts[:, 2] - zc) < R - h / 2) & (pts[:, 2] < zc + 0.9 * R)]
    # casing fill (in screw-axis coordinates)
    gs = np.arange(h / 2, Ls - h / 2, h)
    ga = np.arange(-a_s + h / 2, a_s, h)
    S, A1, A2 = np.meshgrid(gs, ga, ga, indexing="ij")
    ez = np.array([math.sin(alpha), 0.0, math.cos(alpha)])  # local z of the casing in world
    ey = np.array([0.0, 1.0, 0.0])
    cas = P_b + S.reshape(-1, 1) * u + A1.reshape(-1, 1) * ey + A2.reshape(-1, 1) * ez
    pts = np.concatenate([pts, cas])
    pts += rng.uniform(-0.25 * h, 0.25 * h, pts.shape)
    pts = pts.astype(np.float32)
    n_particles = len(pts)
    mass = float(h**3 * args.density)

    sb = newton.ModelBuilder()
    SolverImplicitMPM.register_custom_attributes(sb)
    sb.add_particles(
        pos=[wp.vec3(*q) for q in pts],
        vel=[wp.vec3(0.0)] * n_particles,
        mass=[mass] * n_particles,
        radius=[h / 2] * n_particles,
        custom_attributes={"mpm:friction": [args.friction] * n_particles, "mpm:yield_stress": [args.cohesion] * n_particles},
    )
    sand_model = sb.finalize()

    cfg = SolverImplicitMPM.Config()
    cfg.voxel_size = dx
    cfg.max_iterations = args.iterations
    cfg.critical_fraction = 0.0
    cfg.strain_basis = "P0"
    solver = SolverImplicitMPM(sand_model, config=cfg)
    solver.setup_collider(model=model)
    cbody = solver.collider_body_index.numpy()
    fric = {-1: 0.5, shell: 0.3, cutter: 0.3, piston: 0.5, screw: 0.3}
    solver.setup_collider(model=model, collider_friction=[fric[int(c)] for c in cbody])

    state = model.state()
    ss = sand_model.state()
    ss.body_q = wp.clone(state.body_q)
    ss.body_qd = wp.zeros_like(state.body_qd)
    ss.body_f = wp.zeros_like(state.body_f)

    dt = 1.0 / args.fps
    w_c = args.cutter_rpm * 2 * math.pi / 60
    w_s = args.screw_rpm * 2 * math.pi / 60
    v_a = args.advance / 1000 / 60
    q_np = ss.body_q.numpy()
    q0_cut = q_np[cutter, 3:7].copy()
    q0_scr = q_np[screw, 3:7].copy()
    qd = np.zeros((model.body_count, 6), dtype=np.float32)
    qd[piston, 0] = -v_a
    qd[cutter, 3:6] = [w_c, 0, 0]
    qd[screw, 3:6] = w_s * u
    ss.body_qd.assign(qd)

    c_cut = np.array([x_ch, 0.0, zc])
    x_out = (P_b + Ls * u)[0]

    def count_out(xq):
        rel = xq - P_b
        s_proj = rel @ u
        lat = rel - np.outer(s_proj, u)
        in_duct = (s_proj > s_c) & (s_proj < Ls) & (np.abs(lat @ ey) < a_s + t) & (np.abs(lat @ ez) < a_s + t)
        behind = xq[:, 0] < -t
        discharged = int(np.sum(behind & ~in_duct & (xq[:, 0] < x_out + 0.5)))  # came out of the outlet
        leaked = int(np.sum(behind & ~in_duct & (xq[:, 0] >= x_out + 0.5)))  # escaped elsewhere behind the bulkhead
        return behind, discharged, leaked

    counts = []  # (time, discharged particles), every 30 frames
    # Three horizontal bands (top, axis, bottom), each split into two side patches clear of the
    # screw hole: |y| > y_min.
    bands = [(0.4 * R, 0.6 * R), (-0.1 * R, 0.1 * R), (-0.6 * R, -0.4 * R)]
    y_min = hole_y + 0.1
    zz = np.linspace(-R, R, 20001)
    chord = 2 * np.maximum(np.sqrt(np.maximum(R**2 - zz**2, 0)) - y_min, 0)
    band_area = [float(np.trapezoid(chord * ((zz >= lo) & (zz < hi)), zz)) for lo, hi in bands]
    rows = []
    frame_times = []
    for f in range(args.frames):
        tt = (f + 1) * dt
        q_np[cutter, 3:7] = qmul(qaxis([1, 0, 0], w_c * tt), q0_cut)
        q_np[screw, 3:7] = qmul(qaxis(u, w_s * tt), q0_scr)
        q_np[piston, 0] = x_face + t / 2 - v_a * tt
        ss.body_q.assign(q_np)

        wp.synchronize()
        t0 = time.perf_counter()
        solver.step(ss, ss, contacts=None, control=None, dt=dt)
        wp.synchronize()
        frame_times.append(time.perf_counter() - t0)

        imp, pos, cid = solver.collect_collider_impulses(ss)
        imp, pos, cid = imp.numpy(), pos.numpy(), cid.numpy()
        valid = cid >= 0
        bid = np.full(cid.shape, -2)
        bid[valid] = cbody[np.clip(cid[valid], 0, len(cbody) - 1)]
        F = imp / dt
        # Bulkhead: sum the normal force of the shell collider nodes near x = 0 inside the chamber
        # over three horizontal bands, divided by each band's area (top, axis, bottom sensors).
        on_bh = (bid == shell) & (np.abs(pos[:, 0]) < 1.5 * dx) & (np.hypot(pos[:, 1], pos[:, 2] - zc) < R) & (np.abs(pos[:, 1]) > y_min)
        fb = -F[on_bh, 0]
        zb = pos[on_bh, 2] - zc
        p_band = [float(fb[(zb >= lo) & (zb < hi)].sum() / ar) for (lo, hi), ar in zip(bands, band_area)]
        p_top, p_axis, p_bot = p_band
        m = bid == cutter
        tau_c = float(np.cross(pos[m] - c_cut, F[m])[:, 0].sum())
        m = bid == screw
        tau_s = float((np.cross(pos[m] - P_b, F[m]) @ u).sum())
        rows.append((tt, p_top, p_axis, p_bot, tau_c, tau_s))
        if (f + 1) % 30 == 0:
            counts.append((tt, count_out(ss.particle_q.numpy())[1]))

    xq = ss.particle_q.numpy()
    behind, discharged, leaked = count_out(xq)
    counts = np.array(counts)
    rows = np.array(rows)
    frame_times = np.array(frame_times)
    timed = frame_times[5:]
    mean_ms = float(timed.mean() * 1000)
    sim_t = args.frames * dt
    A_free = math.pi * (rs**2 - r_sh**2)
    q_th = A_free * pitch * args.screw_rpm / 60  # m3/s
    q_th_safe = max(q_th, 1e-12)
    # discharge rate: slope of the outlet count over the second half of the run
    half_c = counts[len(counts) // 2 :]
    q_sim = float(np.polyfit(half_c[:, 0], half_c[:, 1], 1)[0] * h**3) if len(half_c) >= 2 else discharged * h**3 / sim_t
    steady = rows[len(rows) // 2 :]
    # band centroids, for the vertical pressure gradient
    z_top_c = float(np.trapezoid(chord * zz * ((zz >= bands[0][0]) & (zz < bands[0][1])), zz) / band_area[0])
    z_bot_c = float(np.trapezoid(chord * zz * ((zz >= bands[2][0]) & (zz < bands[2][1])), zz) / band_area[2])

    result = {
        "diameter_m": D,
        "voxel_m": dx,
        "particles": int(n_particles),
        "iterations": args.iterations,
        "frame_dt_s": dt,
        "frames": args.frames,
        "ms_per_frame": round(mean_ms, 2),
        "realtime_factor": round(dt / (mean_ms / 1000), 3),
        "particle_steps_per_s_millions": round(n_particles / (mean_ms / 1000) / 1e6, 2),
        "cutter_rpm": args.cutter_rpm,
        "screw_rpm": args.screw_rpm,
        "p_top_kPa": round(np.nanmean(steady[:, 1]) / 1e3, 1),
        "p_axis_kPa": round(np.nanmean(steady[:, 2]) / 1e3, 1),
        "p_bottom_kPa": round(np.nanmean(steady[:, 3]) / 1e3, 1),
        "p_gradient_kPa_per_m": round((np.nanmean(steady[:, 3]) - np.nanmean(steady[:, 1])) / 1e3 / (z_top_c - z_bot_c), 2),
        "rho_g_kPa_per_m": round(args.density * G / 1e3, 2),
        "cutter_torque_kNm": round(float(np.mean(np.abs(steady[:, 4]))) / 1e3, 1),
        "screw_torque_kNm": round(float(np.mean(np.abs(steady[:, 5]))) / 1e3, 2),
        "screw_discharge_m3_s": round(q_sim, 4),
        "screw_theoretical_m3_s": round(q_th, 4),
        "screw_efficiency": round(q_sim / q_th_safe, 3) if q_th > 0 else None,
        "particles_behind_bulkhead": int(behind.sum()),
        "particles_discharged": discharged,
        "particles_leaked": leaked,
    }
    print(json.dumps(result, indent=2))
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(result, fh, indent=2)
        np.savez_compressed(args.out.replace(".json", ".npz"), particles=xq, rows=rows, counts=counts, frame_times=frame_times)


if __name__ == "__main__":
    main()
