"""WP4: EPB excavation chamber under pressure (Newton implicit MPM), the Phase 0 chamber made pressure-controlled.

Scene (Z up, machine axis along +x, excavation towards +x), in the machine's frame:
- the chamber, diameter D and length L, between the bulkhead (x = 0, its own body, so its pressure can be read) and
  a rotating cutterhead with spokes and mixing arms; a slab of ground in front of it is pushed in by a "ground"
  piston at the advance rate (the machine advancing into the ground);
- the screw conveyor is **analytical** here (WP5 resolves it): a sink at its inlet, at the invert in front of the
  bulkhead, removes paste at the screw model's discharge eta * Q_th(rpm) (tunnelsim_models.epb_chamber.Screw);
- the paste is elastic-plastic. Its bulk modulus is the foam-paste stiffness of the analytical chamber model at the
  target pressure (Boyle's law for the foam air, FIR / FER as on the console), so the MPM chamber is as compliant as
  the console's; friction and cohesion of the paste are assumptions until a source is found.

Run phases: pressurise (the piston compresses the chamber to the target, screw shut), standstill, excavation (advance
at the set rate, cutterhead turning, the screw speed held by a PI controller on the axis pressure), standstill again.

Measured per frame: bulkhead pressure in horizontal bands clear of the screw inlet (as the bulkhead pressure cells
of an EPB), its vertical gradient (least squares over the bands), cutterhead torque, screw speed and the bulkhead
thrust. The checks (docs/validation/mpm-chamber.md): the vertical gradient against Bezuijen, Talmon, Joustra & Grote
(2005, Botlek Rail Tunnel: high during excavation, falling at standstill, between under 10 and over 20 kPa/m with
the muck at about 13 kPa/m), the pressure held within the control band, and the torque below the installed value.
"""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass

import numpy as np

from ..materials import Soil
from .common import add_walls, make_particles, make_solver

G = 9.81


@dataclass(frozen=True)
class ChamberConfig:
    diameter: float = 7.08  # m, Crossrail EPB (9.8 MNm installed torque)
    chamber: float = 0.8  # m, bulkhead to cutterhead
    slab: float = 0.6  # m of ground in front of the cutterhead
    voxel: float = 0.15
    ppc: int = 2
    paste_density: float = 1330.0  # kg/m3: 13 kN/m3 foam-water-sand mixture, Bezuijen et al. (2005)
    paste_friction: float = 0.35  # assumed (Phase 0)
    paste_cohesion: float = 2000.0  # Pa, assumed (Phase 0)
    paste_poisson: float = 0.3  # assumed
    fir: float = 0.4  # foam injection ratio (fraction)
    fer: float = 10.0  # foam expansion ratio
    target_kpa: float = 200.0  # axis pressure set point
    advance_mm_min: float = 60.0
    cutter_rpm: float = 2.0
    pressurise_speed: float = 0.1  # m/s, piston speed while pressurising
    pressurise_max_s: float = 8.0
    hold_s: float = 3.0  # standstill before excavation
    excavate_s: float = 20.0
    stop_s: float = 6.0  # standstill after excavation
    kp_rpm_per_kpa: float = 0.2  # screw PI controller on the axis pressure
    ki_rpm_per_kpa_s: float = 0.05
    max_screw_rpm: float = 22.0  # EPB demo's screw range
    fps: float = 60.0
    iterations: int = 50
    seed: int = 0


def paste_bulk_modulus(cfg: ChamberConfig) -> float:
    """Pa: chamber stiffness of the analytical model at the target pressure, as a bulk modulus K = V dp/dV."""
    from tunnelsim_models.epb_chamber import Chamber

    area = math.pi * cfg.diameter**2 / 4
    vol = area * cfg.chamber
    q_exc = area * cfg.advance_mm_min / 1000 / 60
    ch = Chamber(vol)
    st = ch.steady_state(q_exc, ch.screw_flow_for_pressure(cfg.target_kpa, q_exc, cfg.fir, cfg.fer), cfg.fir, cfg.fer)
    return vol * ch.stiffness(st) * 1e3


def paste(cfg: ChamberConfig) -> Soil:
    k = paste_bulk_modulus(cfg)
    e = 3 * k * (1 - 2 * cfg.paste_poisson)
    return Soil("EPB chamber paste", cfg.paste_density, cfg.paste_friction,
                "density: Bezuijen et al. (2005) 13 kN/m3 mixture; stiffness: foam-paste bulk modulus of the analytical "
                f"chamber model at {cfg.target_kpa:g} kPa, FIR {cfg.fir:g}, FER {cfg.fer:g}; friction and cohesion assumed",
                yield_stress=cfg.paste_cohesion, young_modulus=e, poisson_ratio=cfg.paste_poisson,
                extra={"bulk_modulus_Pa": round(k)})


def _rot_x_plate(c, th):
    import warp as wp

    return wp.transform(wp.vec3(*c), wp.quat_from_axis_angle(wp.vec3(1.0, 0.0, 0.0), th - math.pi / 2))


def _qaxis(axis, ang):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    return np.array([*(axis * math.sin(ang / 2)), math.cos(ang / 2)])


def _qmul(a, b):
    x1, y1, z1, w1 = a
    x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def run(cfg: ChamberConfig) -> tuple[dict, dict]:
    import warp as wp

    import newton
    from tunnelsim_models.epb_chamber import Screw

    wp.init()
    soil = paste(cfg)
    screw = Screw()
    D, L, dx = cfg.diameter, cfg.chamber, cfg.voxel
    R = D / 2
    zc = R + 0.5
    t = max(0.2, 2 * dx)  # walls at least one voxel thick (Phase 0)
    area = math.pi * R**2

    b = newton.ModelBuilder()
    shell = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True, label="shell")
    n_seg = 48
    x0, x1 = -t, L + cfg.slab + 0.5
    for k in range(n_seg):
        th = 2 * math.pi * k / n_seg
        b.add_shape_box(shell, xform=_rot_x_plate(((x0 + x1) / 2, (R + t / 2) * math.cos(th), zc + (R + t / 2) * math.sin(th)), th),
                        hx=(x1 - x0) / 2, hy=1.08 * R * math.tan(math.pi / n_seg), hz=t / 2)
    bulkhead = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True, label="bulkhead")
    add_walls(b, bulkhead, [((-t / 2, 0.0, zc), (t / 2, R + t, R + t))])
    x_ch = L - 0.15
    cutter = b.add_body(xform=wp.transform(wp.vec3(x_ch, 0.0, zc), wp.quat_identity()), mass=1.0, is_kinematic=True, label="cutterhead")
    r0, r1 = 0.4, R - 0.08
    for k in range(6):
        th = 2 * math.pi * k / 6
        rm = (r0 + r1) / 2
        b.add_shape_box(cutter, xform=_rot_x_plate((0.0, rm * math.cos(th), rm * math.sin(th)), th), hx=0.1, hy=0.15, hz=(r1 - r0) / 2)
        th2 = th + math.pi / 6
        ra = 0.6 * R
        b.add_shape_box(cutter, xform=_rot_x_plate((-0.3, ra * math.cos(th2), ra * math.sin(th2)), th2), hx=0.25, hy=0.08, hz=0.08)
    b.add_shape_cylinder(cutter, xform=wp.transform(wp.vec3(0.0), wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), math.pi / 2)), radius=r0, half_height=0.1)
    x_face = L + cfg.slab
    piston = b.add_body(xform=wp.transform(wp.vec3(x_face + t / 2, 0.0, zc), wp.quat_identity()), mass=1.0, is_kinematic=True, label="ground")
    b.add_shape_cylinder(piston, xform=wp.transform(wp.vec3(0.0), wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), math.pi / 2)),
                         radius=R + t / 2, half_height=t / 2)  # overlaps the shell wall: a gap under a voxel leaks
    b.add_ground_plane()
    cm = b.finalize()

    h = dx / cfg.ppc
    rng = np.random.default_rng(cfg.seed)
    gx, gy, gz = np.arange(h / 2, x_face, h), np.arange(-R, R, h), np.arange(zc - R, zc + R, h)
    X, Y, Z = np.meshgrid(gx, gy, gz, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    pts = pts[np.hypot(pts[:, 1], pts[:, 2] - zc) < R - h / 2]
    pts = (pts + rng.uniform(-0.25 * h, 0.25 * h, pts.shape)).astype(np.float32)
    pm = make_particles(pts, h, soil).finalize()
    solver = make_solver(pm, cm, dx, cfg.iterations, {shell: 0.3, bulkhead: 0.3, cutter: 0.3, piston: 0.5, -1: 0.5})
    st = cm.state()
    s = pm.state()
    s.body_q, s.body_qd, s.body_f = wp.clone(st.body_q), wp.zeros_like(st.body_qd), wp.zeros_like(st.body_f)
    body_index = solver.collider_body_index.numpy()

    # screw inlet (sink) at the invert in front of the bulkhead, as wide as the screw
    a_s = screw.diameter / 2
    sink_lo = np.array([0.0, -a_s, zc - R])
    sink_hi = np.array([2 * a_s, a_s, zc - R + 2 * a_s])
    flags = pm.particle_flags.numpy()
    active = int(newton.ParticleFlags.ACTIVE)
    v_particle = h**3  # in-situ volume of the ground each particle stands for

    # bulkhead pressure bands, clear of the screw inlet column |y| < y_min
    y_min = a_s + 0.3
    edges = np.linspace(-0.9 * R, 0.9 * R, 10)
    zz = np.linspace(-R, R, 40001)
    chord = 2 * np.maximum(np.sqrt(np.maximum(R**2 - zz**2, 0)) - y_min, 0)
    band_area = np.array([np.trapezoid(chord * ((zz >= lo) & (zz < hi)), zz) for lo, hi in zip(edges[:-1], edges[1:])])
    band_z = np.array([np.trapezoid(chord * zz * ((zz >= lo) & (zz < hi)), zz) for lo, hi in zip(edges[:-1], edges[1:])]) / band_area
    axis_band = len(band_z) // 2

    dt = 1.0 / cfg.fps
    w_c = cfg.cutter_rpm * 2 * math.pi / 60
    v_adv = cfg.advance_mm_min / 1000 / 60
    q = s.body_q.numpy()
    q0_cut = q[cutter, 3:7].copy()
    x_p = x_face + t / 2
    ang = 0.0
    phase, t_phase = "pressurise", 0.0
    rpm, integ, owed = 0.0, 0.0, 0.0
    p_hist: list[float] = []
    log, times = [], []
    removed = 0
    n_total = int(round((cfg.pressurise_max_s + cfg.hold_s + cfg.excavate_s + cfg.stop_s) * cfg.fps))
    for f in range(n_total):
        p_axis_avg = float(np.mean(p_hist[-6:])) / 1e3 if p_hist else 0.0
        if phase == "pressurise" and (p_axis_avg >= cfg.target_kpa or t_phase >= cfg.pressurise_max_s):
            phase, t_phase = "hold", 0.0
        elif phase == "hold" and t_phase >= cfg.hold_s:
            phase, t_phase, integ = "excavate", 0.0, 0.0
            rpm = screw.rpm_for_flow(area * v_adv)  # feed-forward: discharge equal to the excavated flow
        elif phase == "excavate" and t_phase >= cfg.excavate_s:
            phase, t_phase, rpm = "stop", 0.0, 0.0
        elif phase == "stop" and t_phase >= cfg.stop_s:
            break
        v_piston = cfg.pressurise_speed if phase == "pressurise" else v_adv if phase == "excavate" else 0.0
        if phase == "excavate":  # PI on the axis pressure: more pressure, faster screw
            err = p_axis_avg - cfg.target_kpa
            integ += err * dt
            rpm = float(np.clip(screw.rpm_for_flow(area * v_adv) + cfg.kp_rpm_per_kpa * err + cfg.ki_rpm_per_kpa_s * integ,
                                0.0, cfg.max_screw_rpm))
            ang += w_c * dt
        x_p -= v_piston * dt
        q[piston, 0] = x_p
        q[cutter, 3:7] = _qmul(_qaxis([1, 0, 0], ang), q0_cut)
        s.body_q.assign(q)
        qd = np.zeros((cm.body_count, 6), dtype=np.float32)
        qd[piston, 0] = -v_piston
        qd[cutter, 3] = w_c if phase == "excavate" else 0.0
        s.body_qd.assign(qd)

        # analytical screw: remove the discharged volume from the inlet, deepest-in-the-casing particles first
        owed += screw.discharge(rpm) * dt / v_particle
        if owed >= 1.0:
            xq = s.particle_q.numpy()
            inside = np.where(((flags & active) != 0) & np.all((xq >= sink_lo) & (xq <= sink_hi), axis=1))[0]
            n = min(int(owed), len(inside))
            if n:
                take = inside[np.argsort(xq[inside, 0])[:n]]
                flags[take] &= ~active
                pm.particle_flags.assign(flags)
                solver.notify_model_changed(newton.ModelFlags.MODEL_PROPERTIES)
                removed += n
            owed -= int(owed)

        wp.synchronize()
        t0 = time.perf_counter()
        solver.step(s, s, contacts=None, control=None, dt=dt)
        wp.synchronize()
        times.append(time.perf_counter() - t0)

        imp, pos, cid = solver.collect_collider_impulses(s)
        imp, pos, cid = imp.numpy(), pos.numpy(), cid.numpy()
        valid = cid >= 0
        bid = np.full(cid.shape, -2)
        bid[valid] = body_index[np.clip(cid[valid], 0, len(body_index) - 1)]
        F = imp / dt
        on = (bid == bulkhead) & (np.abs(pos[:, 1]) > y_min) & (np.hypot(pos[:, 1], pos[:, 2] - zc) < R)
        zb = pos[on, 2] - zc
        fx = -F[on, 0]  # F is along -x where the soil presses on the bulkhead
        p_band = np.array([fx[(zb >= lo) & (zb < hi)].sum() for lo, hi in zip(edges[:-1], edges[1:])]) / band_area
        grad = -float(np.polyfit(band_z, p_band, 1)[0])  # pressure rises downwards
        thrust = -float(F[bid == bulkhead, 0].sum())
        m = bid == cutter
        torque = float(np.cross(pos[m] - np.array([x_ch, 0.0, zc]), F[m])[:, 0].sum())
        f_cutter_x = -float(F[m, 0].sum())  # soil pushing the cutterhead back (towards -x)
        p_piston = float(F[bid == piston, 0].sum()) / area  # soil pushing the piston forwards (+x)
        p_hist.append(float(p_band[axis_band]))
        log.append((f * dt, ["pressurise", "hold", "excavate", "stop"].index(phase), p_band[axis_band] / 1e3, grad / 1e3,
                    rpm, thrust / 1e6, abs(torque) / 1e6, x_face + t / 2 - x_p, removed, p_piston / 1e3, f_cutter_x / 1e6))
        t_phase += dt

    log = np.array(log)
    xq = s.particle_q.numpy()[(flags & active) != 0]
    esc_back = xq[:, 0] < -0.02
    esc_front = xq[:, 0] > x_p - t / 2 + 0.02
    esc_side = (np.hypot(xq[:, 1], xq[:, 2] - zc) > R + 0.02) & ~esc_back & ~esc_front
    escaped = int(np.sum(esc_back | esc_front | esc_side))
    # paste volume left in the chamber and slab against its volume: a pressure drop with no outflow means lost volume
    vol_now = area * (x_p - t / 2)
    n_active = int(((flags & active) != 0).sum())

    def window(ph, frac=(0.5, 1.0)):
        rows = log[log[:, 1] == ph]
        if not len(rows):
            return rows
        a, z = int(len(rows) * frac[0]), int(len(rows) * frac[1])
        return rows[a:z]

    ex, hold, stop = window(2), window(1), window(3, (0.5, 1.0))
    res = {
        "diameter_m": D, "voxel_m": dx, "particles": int(len(pts)), "paste_bulk_modulus_kPa": round(soil.extra["bulk_modulus_Pa"] / 1e3),
        "rho_g_kPa_per_m": round(cfg.paste_density * G / 1e3, 2),
        "pressurised_after_s": round(float(log[log[:, 1] == 0][-1, 0]) if (log[:, 1] == 0).any() else 0.0, 2),
        "p_axis_hold_kPa": round(float(hold[:, 2].mean()), 1) if len(hold) else None,
        "gradient_hold_kPa_per_m": round(float(hold[:, 3].mean()), 2) if len(hold) else None,
        "p_axis_excavate_kPa": round(float(ex[:, 2].mean()), 1) if len(ex) else None,
        "p_axis_excavate_band_kPa": [round(float(np.percentile(ex[:, 2], 5)), 1), round(float(np.percentile(ex[:, 2], 95)), 1)] if len(ex) else None,
        "gradient_excavate_kPa_per_m": round(float(ex[:, 3].mean()), 2) if len(ex) else None,
        "gradient_stop_kPa_per_m": round(float(stop[:, 3].mean()), 2) if len(stop) else None,
        "screw_rpm_excavate": round(float(ex[:, 4].mean()), 2) if len(ex) else None,
        "screw_rpm_feedforward": round(screw.rpm_for_flow(area * v_adv), 2),
        "bulkhead_thrust_MN_excavate": round(float(ex[:, 5].mean()), 2) if len(ex) else None,
        "p_axis_times_area_MN": round(float(ex[:, 2].mean()) * area / 1e3, 2) if len(ex) else None,
        "cutter_torque_MNm_excavate": round(float(ex[:, 6].mean()), 3) if len(ex) else None,
        "p_piston_hold_excavate_kPa": [round(float(hold[:, 9].mean()), 1) if len(hold) else None, round(float(ex[:, 9].mean()), 1) if len(ex) else None],
        "cutter_axial_MN_hold_excavate": [round(float(hold[:, 10].mean()), 2) if len(hold) else None, round(float(ex[:, 10].mean()), 2) if len(ex) else None],
        "advance_m": round(float(log[-1, 7]), 3),
        "particles_removed": int(removed),
        "particles_escaped": escaped,
        "escaped_back_front_side": [int(esc_back.sum()), int(esc_front.sum()), int(esc_side.sum())],
        "particles_per_m3_start_end": [round(len(pts) / (area * x_face)), round((n_active - escaped) / vol_now)],
        "ms_per_frame": round(float(np.mean(times[5:]) * 1000), 2),
    }
    return res, {"log": log}


def params(cfg: ChamberConfig) -> dict:
    return {**asdict(cfg), "soil": asdict(paste(cfg))}
