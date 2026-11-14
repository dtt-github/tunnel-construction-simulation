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
import os
import time
from dataclasses import asdict, dataclass

import numpy as np

from ..materials import Soil
from . import common
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
    # undrained paste: no friction, cu 5 kPa, the middle of the 3-7 kPa target for conditioned soil in Scientific Reports
    # (2026), doi:10.1038/s41598-026-38868-y (abstract). Phase 0's assumed 0.35 / 2 kPa arched between the walls
    paste_friction: float = 0.0
    paste_cohesion: float = 5000.0  # Pa
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
    # WP4 screw-speed step: this long into the excavation the controller is switched off and the screw held at its
    # mean speed of the 2 s before, changed by screw_step_rpm; 0 s: no step
    screw_step_s: float = 0.0
    screw_step_rpm: float = 0.0
    # WP4 shove under thrust: during excavation the ground piston is not driven at advance_mm_min but moves as the
    # machine would under a set net thrust (the jacks' thrust less shield friction, tail seal and backup drag):
    # M dv/dt = F_set - F_ground - c v, F_ground the paste's force on the piston. F_set is thrust_factor times the
    # force that held the piston at standstill; the screw turns at the fixed speed that discharges advance_mm_min
    thrust_control: bool = False
    thrust_factor: float = 1.0
    thrust_step_s: float = 0.0  # this long into the excavation the set thrust is multiplied by thrust_step_factor; 0: no step
    thrust_step_factor: float = 1.0
    machine_mass: float = 5.0e5  # kg, assumed (shield and cutterhead); it shapes the transient only
    # assumed: the jacks' damping as a multiple of critical (machine mass on the paste's stiffness K A / length).
    # Flow-limited hydraulics are far over critical; at 30 the advance settles in about 5 s, the damping force at
    # 60 mm/min is about 4 % of the thrust, and the +-40 kN noise of the piston force moves the advance by a few mm/min
    jack_damping_ratio: float = 30.0
    advance_max_mm_min: float = 120.0  # assumed cap of the thrust hydraulics
    # WP4 leak diagnosis only: paste pushed into the shell wall is put back inside each frame (radius R - h/2, radial
    # velocity removed), so no paste is lost through the shell
    seal_shell: bool = False
    # paste on steel (shell, bulkhead, piston): 0.3, within conditioned soil on steel by inclined plate, 0.31-0.58
    # (Applied Sciences 10 (2020) 3300, doi:10.3390/app10093300), and kaolin on steel, 0.33 (Henke & Wiesenthal, WCCM
    # 2024); < 0 keeps the Phase 0 values 0.3 / 0.3 / 0.5
    wall_friction: float = 0.3
    stress_log: bool = False  # log the paste's own stress beside the bulkhead next to the contact-force reading
    # WP4 correction for Newton's volume drift where a solid moves through the paste (newton#5180): once pressurised,
    # the mean elastic volume strain of each region follows the chamber's volume balance (piston advance, paste removed
    # by the screw); deviations within a region are the solver's own
    vb_from_hold: bool = True  # take the balance reference when pressurising ends, not when excavation starts
    volume_balance: int = 3  # 0 off, 1 whole chamber, 2 by region (columns ~1.2 m across, the chamber's length), 3 as 2 cut in 3 along the axis
    # density-coupled volume correction (scenes/volume_correction.py), from the first frame: rate per frame, 0 off;
    # replaces the regional balance above
    volume_correction: float = 0.0
    vc_support: str = "node"  # node | cell
    vc_interior: bool = True  # use only the grid nodes clear of every solid
    fps: float = 60.0
    iterations: int = 100  # 50 diverges at voxel 0.12 m (WP4, 9 Nov 2026)
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
                f"chamber model at {cfg.target_kpa:g} kPa, FIR {cfg.fir:g}, FER {cfg.fer:g}; strength: undrained cu, Scientific Reports (2026)",
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
    j = common.JITTER  # initial jitter, a fraction of h (as fill_box)
    pts = (pts + rng.uniform(-j * h, j * h, pts.shape)).astype(np.float32)
    pm = make_particles(pts, h, soil).finalize()
    mass_p = pm.particle_mass.numpy()
    solver = make_solver(pm, cm, dx, cfg.iterations, {shell: wf if (wf := cfg.wall_friction) >= 0 else 0.3, bulkhead: wf if wf >= 0 else 0.3, cutter: 0.3, piston: wf if wf >= 0 else 0.5, -1: 0.5})
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
    resealed = 0
    vb_ref = None
    vb_log: list = []
    vb_repaired = 0
    stress_log: list = []
    step = None
    f_set, c_jack, v_dyn = None, 0.0, 0.0
    pp_hist: list = []
    vc = None
    if cfg.volume_correction > 0:
        from .volume_correction import VolumeCorrection

        spokes = [(2 * math.pi * k / 6, (r0 + r1) / 2, (r1 - r0) / 2, 0.0, 0.1, 0.15) for k in range(6)]
        arms = [(2 * math.pi * k / 6 + math.pi / 6, 0.6 * R, 0.08, -0.3, 0.25, 0.08) for k in range(6)]

        def vc_static(p):  # shell, bulkhead
            return (np.hypot(p[:, 1], p[:, 2] - zc) >= R) | (p[:, 0] <= 0.0)

        def vc_moving(p):  # ground piston and cutterhead, at their current pose
            out = p[:, 0] >= x_p - t / 2
            near = np.where((p[:, 0] > x_ch - 0.56) & (p[:, 0] < x_ch + 0.11) & ~out)[0]
            xl, yw, zw = p[near, 0] - x_ch, p[near, 1], p[near, 2] - zc
            c_, s_ = math.cos(ang), math.sin(ang)
            yl, zl = c_ * yw + s_ * zw, -s_ * yw + c_ * zw  # into the cutterhead's frame
            hit = (abs(xl) < 0.1) & (np.hypot(yl, zl) < r0)
            for th, rc, hr, xc, hx, ht in spokes + arms:  # boxes: radial, axial and tangential half sizes
                rho, tau = yl * math.cos(th) + zl * math.sin(th), yl * math.sin(th) - zl * math.cos(th)
                hit |= (abs(xl - xc) < hx) & (abs(tau) < ht) & (abs(rho - rc) < hr)
            out[near[hit]] = True
            return out

        lo_vc = np.floor(np.array([0.0, -R, zc - R]) / dx) * dx
        vc = VolumeCorrection(dx, lo_vc, (x_face, R, zc + R), vc_moving, rate=cfg.volume_correction, support=cfg.vc_support, samples=3, static=vc_static, interior=cfg.vc_interior)
        vc.calibrate(s.particle_q.numpy(), s.mpm.particle_elastic_strain.numpy(), (flags & active) != 0, h)
        vc_log: list = []
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
            if cfg.thrust_control:
                if f_set is None:
                    f_set = cfg.thrust_factor * float(np.mean(pp_hist[-int(cfg.fps):])) * area
                    c_jack = cfg.jack_damping_ratio * 2.0 * math.sqrt(soil.extra["bulk_modulus_Pa"] * area / (x_p - t / 2) * cfg.machine_mass)
                f_now = f_set * (cfg.thrust_step_factor if cfg.thrust_step_s > 0 and t_phase >= cfg.thrust_step_s else 1.0)
                f_ground = float(np.mean(pp_hist[-3:])) * area
                # implicit in the damping: c dt / M is well above 2
                v_dyn = float(np.clip((v_dyn + (f_now - f_ground) / cfg.machine_mass * dt) / (1.0 + c_jack * dt / cfg.machine_mass), 0.0, cfg.advance_max_mm_min / 6e4))
                v_piston = v_dyn
                rpm = screw.rpm_for_flow(area * v_adv)  # fixed screw speed: under thrust it sets the advance rate
            if cfg.screw_step_s > 0 and t_phase >= cfg.screw_step_s:  # open loop from the step on
                if step is None:
                    rpm_before = float(np.mean([r[4] for r in log[-int(2 * cfg.fps):]]))
                    step = {"t_s": f * dt, "rpm_before": rpm_before, "rpm_after": float(np.clip(rpm_before + cfg.screw_step_rpm, 0.0, cfg.max_screw_rpm)),
                            "paste_volume_m3": area * (x_p - t / 2)}
                rpm = step["rpm_after"]
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
        if vc is not None:
            s.mpm.particle_elastic_strain.assign(vc.apply(s.particle_q.numpy(), s.mpm.particle_elastic_strain.numpy(), (flags & active) != 0, h).astype(np.float32))
            vc_log.append((phase == "excavate", vc.stats["mismatch_mean"], vc.stats["mismatch_rms"], vc.stats["clipped"]))
            if os.environ.get("VC_DEBUG") and f % 20 == 0:  # where the mismatch sits: zones of the chamber
                ok_, dp_, tot_, out_ = vc.last
                xq_ = s.particle_q.numpy()[ok_]
                rr_ = np.hypot(xq_[:, 1], xq_[:, 2] - zc)
                zones = {"cutter": (xq_[:, 0] > x_ch - 0.56) & (xq_[:, 0] < x_ch + 0.11), "piston": xq_[:, 0] > x_p - t / 2 - 2 * dx,
                         "bulkhead": xq_[:, 0] < 2 * dx, "shell": rr_ > R - 2 * dx}
                zones["interior"] = ~np.any(list(zones.values()), axis=0)
                lnj_ = np.log(np.linalg.det(s.mpm.particle_elastic_strain.numpy()[ok_]))
                print("VCDBG", f, phase, f"p {p_axis_avg:.0f} n {len(dp_)} mat/spc {tot_:.4f} outside {out_:.4f} clipped {vc.stats['clipped']}",
                      " ".join(f"{k} n{int(m.sum())} dp {dp_[m].mean() * 1e3:.0f}/{dp_[m].std() * 1e3:.0f} lnJ {lnj_[m].mean() * 1e3:.0f}" for k, m in zones.items() if m.any()), flush=True)
        elif cfg.volume_balance and phase != "pressurise":
            act = (flags & active) != 0
            fe = s.mpm.particle_elastic_strain.numpy()
            if cfg.volume_balance == 2:  # region of each particle: a column of the cross-section, the chamber's length
                xq_ = s.particle_q.numpy()
                n_side = max(1, round(2 * R / 1.2))
                iy = np.clip(((xq_[:, 1] + R) / (2 * R) * n_side).astype(int), 0, n_side - 1)
                iz = np.clip(((xq_[:, 2] - zc + R) / (2 * R) * n_side).astype(int), 0, n_side - 1)
                reg = np.where(act, iy * n_side + iz, -1)
            elif cfg.volume_balance == 3:  # as 2, cut in three along the axis, as fractions of the current chamber length
                xq_ = s.particle_q.numpy()
                n_side, n_ax = max(1, round(2 * R / 1.2)), 3
                iy = np.clip(((xq_[:, 1] + R) / (2 * R) * n_side).astype(int), 0, n_side - 1)
                iz = np.clip(((xq_[:, 2] - zc + R) / (2 * R) * n_side).astype(int), 0, n_side - 1)
                ix = np.clip((xq_[:, 0] / (x_p - t / 2) * n_ax).astype(int), 0, n_ax - 1)
                reg = np.where(act, (ix * n_side + iy) * n_side + iz, -1)
            else:
                reg = np.where(act, 0, -1)
            n_reg = int(reg.max()) + 1 if (reg >= 0).any() else 1
            if vb_ref is None and (phase == "excavate" or cfg.vb_from_hold):  # reference: the pressurised paste
                lnj = np.log(np.linalg.det(fe))
                ok = act & np.isfinite(lnj)
                cnt = np.bincount(reg[ok], minlength=n_reg).astype(float)
                vb_ref = (np.bincount(reg[ok], weights=lnj[ok], minlength=n_reg) / np.maximum(cnt, 1), x_p, cnt)
            if vb_ref is not None:
                lnj = np.log(np.linalg.det(fe))
                ok = act & np.isfinite(lnj)  # a degenerate particle (det <= 0) must not spread NaN to all others
                m = len(vb_ref[2])
                r_ok = np.where(ok & (reg < m), reg, -1)
                use = r_ok >= 0
                cnt = np.bincount(r_ok[use], minlength=m).astype(float)
                mean = np.bincount(r_ok[use], weights=lnj[use], minlength=m) / np.maximum(cnt, 1)
                ref_mean, ref_cnt = vb_ref[0], vb_ref[2]
                valid = (ref_cnt >= 50) & (cnt > 0)
                target = ref_mean + math.log((x_p - t / 2) / (vb_ref[1] - t / 2)) - np.log(np.where(valid, cnt / np.maximum(ref_cnt, 1), 1.0))
                shift = np.where(valid, target - mean, 0.0)
                vb_log.append((f * dt, float(target[valid].mean()), float(mean[valid].mean()), int(act.sum()), x_p, int((act & ~ok).sum())))
                fac = np.ones(len(fe))
                fac[use] = np.exp(shift[r_ok[use]] / 3.0)
                fe *= fac[:, None, None]
                bad = act & ~ok & (reg >= 0) & (reg < m)  # degenerate inside Newton: back to its region's isotropic target
                if bad.any():
                    fe[bad] = np.exp(np.where(valid, target, ref_mean)[reg[bad]] / 3.0)[:, None, None] * np.eye(3)
                    vb_repaired += int(bad.sum())
                s.mpm.particle_elastic_strain.assign(fe.astype(np.float32))
        if cfg.seal_shell:
            xq, vq = s.particle_q.numpy(), s.particle_qd.numpy()
            ry, rz = xq[:, 1], xq[:, 2] - zc
            r = np.hypot(ry, rz)
            out = (r > R - h / 4) & (xq[:, 0] > -t) & (xq[:, 0] < x_p - t / 2)
            if out.any():
                ny, nz = ry[out] / r[out], rz[out] / r[out]
                vr = vq[out, 1] * ny + vq[out, 2] * nz
                vq[out, 1] -= np.maximum(vr, 0) * ny
                vq[out, 2] -= np.maximum(vr, 0) * nz
                xq[out, 1], xq[out, 2] = (R - h / 2) * ny, zc + (R - h / 2) * nz
                s.particle_q.assign(xq)
                s.particle_qd.assign(vq)
                resealed += int(out.sum())

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
        pp_hist.append(p_piston)
        if cfg.stress_log:  # the paste's own stress: within one voxel of the bulkhead, by band, and the chamber mean
            sig = common.particle_stress(s)
            xq_ = s.particle_q.numpy()
            a_ = (flags & active) != 0
            near = a_ & (xq_[:, 0] < dx) & (np.abs(xq_[:, 1]) > y_min)
            zp = xq_[near, 2] - zc
            sxx = sig[near, 0, 0]  # the solver's particle stress comes out compression positive here (checked against the contact pressure)
            pp = np.trace(sig[near], axis1=1, axis2=2) / 3
            sb = np.array([sxx[(zp >= lo) & (zp < hi)].mean() if ((zp >= lo) & (zp < hi)).any() else np.nan for lo, hi in zip(edges[:-1], edges[1:])])
            pb = np.array([pp[(zp >= lo) & (zp < hi)].mean() if ((zp >= lo) & (zp < hi)).any() else np.nan for lo, hi in zip(edges[:-1], edges[1:])])
            okb = np.isfinite(sb)
            g_s = -float(np.polyfit(band_z[okb], sb[okb], 1)[0]) if okb.sum() > 2 else np.nan
            p_part = np.trace(sig, axis1=1, axis2=2) / 3
            p_all = float(p_part[a_].mean())
            # gradient of the paste's mean stress over the whole chamber (bulkhead to the cutterhead's spokes), and over
            # its core, two voxels clear of the shell and the bulkhead
            rr_ = np.hypot(xq_[:, 1], xq_[:, 2] - zc)
            in_ch = a_ & (xq_[:, 0] > 0) & (xq_[:, 0] < x_ch - 0.1) & (rr_ < R) & np.isfinite(p_part)
            core = in_ch & (xq_[:, 0] > 2 * dx) & (rr_ < R - 2 * dx)
            g_ch = -float(np.polyfit(xq_[in_ch, 2], p_part[in_ch], 1)[0]) if in_ch.sum() > 100 else np.nan
            g_core = -float(np.polyfit(xq_[core, 2], p_part[core], 1)[0]) if core.sum() > 100 else np.nan
            stress_log.append((f * dt, p_band[axis_band] / 1e3, sb[axis_band] / 1e3, pb[axis_band] / 1e3, grad / 1e3, g_s / 1e3, p_all / 1e3, int(near.sum()), g_ch / 1e3, g_core / 1e3,
                               ["pressurise", "hold", "excavate", "stop"].index(phase),
                               # vertical balance: the paste's weight in the chamber and the vertical force it puts on each solid (N, down positive)
                               float(mass_p[a_ & (xq_[:, 0] > 0) & (rr_ < R)].sum()) * G,
                               -float(F[bid == shell, 2].sum()), -float(F[bid == bulkhead, 2].sum()), -float(F[bid == piston, 2].sum()), -float(F[bid == cutter, 2].sum())))
        p_hist.append(float(p_band[axis_band]))
        log.append((f * dt, ["pressurise", "hold", "excavate", "stop"].index(phase), p_band[axis_band] / 1e3, grad / 1e3,
                    rpm, thrust / 1e6, abs(torque) / 1e6, x_face + t / 2 - x_p, removed, p_piston / 1e3, f_cutter_x / 1e6, v_piston * 6e4))
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
    step_res = None
    if step is not None:  # pressure rate after the step against the volume balance K dQ / V
        exc = log[log[:, 1] == 2]
        before = exc[(exc[:, 0] >= step["t_s"] - 2.0) & (exc[:, 0] < step["t_s"])]
        after = exc[exc[:, 0] >= step["t_s"]]
        ex = exc[(exc[:, 0] >= step["t_s"] / 2) & (exc[:, 0] < step["t_s"])]  # the closed-loop figures: before the step only
        d_q = screw.discharge(step["rpm_after"]) - screw.discharge(step["rpm_before"])
        k_kpa = soil.extra["bulk_modulus_Pa"] / 1e3
        p0 = float(before[:, 2].mean())
        moved = np.where(abs(after[:, 2] - p0) >= 30.0)[0]
        step_res = {
            "at_s_into_excavation": cfg.screw_step_s, "rpm_before": round(step["rpm_before"], 2), "rpm_after": round(step["rpm_after"], 2),
            "discharge_change_l_per_s": round(d_q * 1e3, 2), "p_axis_before_kPa": round(p0, 1),
            "p_axis_rate_kPa_per_s": round(float(np.polyfit(after[:, 0], after[:, 2], 1)[0]), 3),
            "p_axis_rate_first_5s_kPa_per_s": round(float(np.polyfit(after[:int(5 * cfg.fps), 0], after[:int(5 * cfg.fps), 2], 1)[0]), 3),
            "rate_volume_balance_kPa_per_s": round(-k_kpa * d_q / step["paste_volume_m3"], 3),
            "s_to_30_kPa": round(float(after[moved[0], 0] - step["t_s"]), 2) if len(moved) else None,
            "p_axis_end_kPa": round(float(after[-int(cfg.fps):, 2].mean()), 1),
        }
    res = {
        "diameter_m": D, "voxel_m": dx, "particles": int(len(pts)), "paste_bulk_modulus_kPa": round(soil.extra["bulk_modulus_Pa"] / 1e3),
        "rho_g_kPa_per_m": round(cfg.paste_density * G / 1e3, 2),
        "pressurised_after_s": round(float(log[log[:, 1] == 0][-1, 0]) if (log[:, 1] == 0).any() else 0.0, 2),
        "screw_step": step_res,
        "thrust_control": None if f_set is None else {
            "net_thrust_set_MN": round(f_set / 1e6, 3), "thrust_factor": cfg.thrust_factor,
            "thrust_step": [cfg.thrust_step_s, cfg.thrust_step_factor] if cfg.thrust_step_s > 0 else None,
            "advance_mm_min_excavate": round(float(ex[:, 11].mean()), 1), "advance_band_mm_min": [round(float(np.percentile(ex[:, 11], 5)), 1), round(float(np.percentile(ex[:, 11], 95)), 1)],
            "advance_from_screw_discharge_mm_min": round(float(np.mean([screw.discharge(r) for r in ex[:, 4]])) / area * 6e4, 1),
            "p_piston_excavate_kPa": round(float(ex[:, 9].mean()), 1), "jack_damping_force_kN_at_mean_advance": round(c_jack * float(ex[:, 11].mean()) / 6e4 / 1e3, 2),
            "advance_last_5s_mm_min": round(float(log[log[:, 1] == 2][-int(5 * cfg.fps):, 11].mean()), 1), "p_axis_last_5s_kPa": round(float(log[log[:, 1] == 2][-int(5 * cfg.fps):, 2].mean()), 1),
            "p_piston_last_5s_kPa": round(float(log[log[:, 1] == 2][-int(5 * cfg.fps):, 9].mean()), 1),
        },
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
        "volume_balance_repaired": vb_repaired,
        "volume_correction_mismatch_mean_rms_excavate": [round(float(np.mean([r[k] for r in vc_log if r[0]])), 5) for k in (1, 2)] if vc is not None and any(r[0] for r in vc_log) else None,
        "particle_reseals": resealed,
        "escaped_back_front_side": [int(esc_back.sum()), int(esc_front.sum()), int(esc_side.sum())],
        "particles_per_m3_start_end": [round(len(pts) / (area * x_face)), round((n_active - escaped) / vol_now)],
        "ms_per_frame": round(float(np.mean(times[5:]) * 1000), 2),
    }
    return res, {"log": log, "q_end": s.particle_q.numpy(), "active": (flags & active) != 0, "x_cutter": x_ch, "zc": zc, "vb": np.array(vb_log), "stress": np.array(stress_log)}


def params(cfg: ChamberConfig) -> dict:
    return {**asdict(cfg), "soil": asdict(paste(cfg))}
