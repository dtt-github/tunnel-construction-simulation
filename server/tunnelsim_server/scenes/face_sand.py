"""WP2: tunnel face in dry sand, half-model, with displacement or pressure control (Newton implicit MPM).

Scene (Z up, tunnel axis along +x, face at x = 0). As in the centrifuge tests of Idinger, Aklik, Wu & Borja (2011,
doi:10.1007/s11440-011-0139-2), the model is a half: a frictionless symmetry wall at y = 0 through the tunnel axis,
the soil at y > 0. A shield tube (static) runs back from the face; a face plate inside it is either
- **displacement-controlled:** retracted into the shield at a fixed rate while the soil force on it is measured, as in
  the centrifuge (Idinger) and 1g (Liu et al. 2019, reproduced by Wang et al. 2024) tests; or
- **pressure-controlled:** a retract-only servo lets the plate give way while the soil pressure on it exceeds a
  target, as when the operator's support pressure drops. Above the limit pressure the face stops; below it the plate
  keeps retracting at the maximum rate.

The soil is perfectly plastic Drucker-Prager with mu = sin(phi') (plane strain, psi = 0; WP1). Its at-rest state is
not taken from the MPM (WP1: the MPM's K does not follow nu); only the limit state and the mechanism are compared.

Outputs: pressure against face displacement, the pressure at 1, 3 and 5 % of D, the failure zone (height of the
moving zone above the crown, inclination of the wedge from the extent at crown level, after Idinger's Table 3) and the
surface settlement trough.
"""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass

import numpy as np

from ..materials import Soil
from ..probes import collider_forces
from . import common
from .common import add_walls, make_particles, make_solver

G = 9.81


@dataclass(frozen=True)
class FaceSandConfig:
    diameter: float = 5.0  # m (Idinger's prototype at 50 g)
    cover: float = 1.0  # C/D above the crown
    voxel_per_d: float = 10.0  # D / voxel
    ppc: int = 2
    control: str = "displacement"  # or "pressure"
    retract_over_d: float = 0.05  # total plate retraction / D (displacement control)
    rate_over_d: float = 0.025  # retraction speed / D per second
    target_kpa: float = 0.0  # pressure control: target support pressure on the face
    servo_gain: float = 0.05  # pressure control: plate speed (D/s) per unit (p - target) / (gamma D)
    # pressure control: fastest plate movement, D/s. At 0.025 D/s (the displacement-controlled rate) the plate outruns
    # the soil at packing 2.744 and the loop cycles between about 2 and 25 kPa; 0.01 holds (WP0b).
    servo_max_rate_over_d: float = 0.01
    duration: float = 5.0  # s of control after settling (up to 0.05 D at the fastest rate)
    steel_friction: float = 0.3
    fps: float = 60.0
    settle: int = 60
    iterations: int = 50
    seed: int = 0
    moving_threshold_over_d: float = 0.002  # displacement that marks the failure zone, / D
    # Unlined length P behind the face, / D (Kimura & Mair 1981, Fig. 9). 0: the shield tube reaches the face. Above 0 the
    # face moves forward by P and the unlined walls are a ring of kinematic segments that retract inward at the plate's
    # rate (displacement control, as tunnel_2d); Kimura's air bag pressed evenly on face and walls instead.
    unlined_over_d: float = 0.0


class Face:
    """The face scene, built once and stepped one frame at a time (by run() below, or live by tunnelsim_server.live)."""

    def __init__(self, cfg: FaceSandConfig, soil: Soil):
        import warp as wp

        import newton

        wp.init()
        D, R = cfg.diameter, cfg.diameter / 2
        dx = D / cfg.voxel_per_d
        zc = R + 0.75 * D
        zs = zc + R + cfg.cover * D
        lu = cfg.unlined_over_d * D  # unlined length: the face is at x = lu, the tube ends at x = 0
        x_back, x_front, half_w = 0.75 * D, lu + 2.5 * D, 1.5 * D
        t = max(0.025 * D, dx)  # walls at least one voxel thick (Phase 0)

        b = newton.ModelBuilder()
        tube = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
        side = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
        n_seg, tube_len = 32, x_back + 0.1 * D
        for k in range(n_seg):
            th = 2 * math.pi * k / n_seg
            c = wp.vec3(-tube_len / 2, (R + t / 2) * math.cos(th), zc + (R + t / 2) * math.sin(th))
            q = wp.quat_from_axis_angle(wp.vec3(1.0, 0.0, 0.0), th - math.pi / 2)
            b.add_shape_box(tube, xform=wp.transform(c, q), hx=tube_len / 2, hy=1.08 * R * math.tan(math.pi / n_seg), hz=t / 2)
        w = 0.5 * D
        add_walls(b, side, [((-x_back - w, half_w / 2, zs / 2), (w, half_w, zs)), ((x_front + w, half_w / 2, zs / 2), (w, half_w, zs)),
                            ((0.5 * (x_front - x_back), -w, zs / 2), (x_front + x_back, w, zs)),  # symmetry plane y = 0
                            ((0.5 * (x_front - x_back), half_w + w, zs / 2), (x_front + x_back, w, zs))])
        b.add_ground_plane()
        # unlined walls: one kinematic body per segment, half circle y > 0 (the model is symmetric about y = 0)
        walls, wall_dirs = [], []
        if lu > 0:
            for k in range(n_seg):
                th = 2 * math.pi * (k + 0.5) / n_seg
                if math.cos(th) <= 0:
                    continue
                body = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
                c = wp.vec3(lu / 2, (R + t / 2) * math.cos(th), zc + (R + t / 2) * math.sin(th))
                qs = wp.quat_from_axis_angle(wp.vec3(1.0, 0.0, 0.0), th - math.pi / 2)
                b.add_shape_box(body, xform=wp.transform(c, qs), hx=lu / 2, hy=1.08 * R * math.tan(math.pi / n_seg), hz=t / 2)
                walls.append(body)
                wall_dirs.append(np.array([0.0, math.cos(th), math.sin(th)]))
        plate = b.add_body(xform=wp.transform(wp.vec3(lu - t / 2, 0.0, zc), wp.quat_identity()), mass=100.0, is_kinematic=True)
        b.add_shape_cylinder(plate, xform=wp.transform(wp.vec3(0.0), wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), math.pi / 2)),
                             radius=R - 0.25 * t, half_height=t / 2)
        cm = b.finalize()

        h = dx / cfg.ppc
        rng = np.random.default_rng(cfg.seed)
        gx, gy, gz = np.arange(-x_back + h / 2, x_front, h), np.arange(h / 2, half_w, h), np.arange(h / 2, zs, h)
        X, Y, Z = np.meshgrid(gx, gy, gz, indexing="ij")
        pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
        pts += rng.uniform(-common.JITTER * h, common.JITTER * h, pts.shape)  # as fill_box
        pts[:, 1] = np.abs(pts[:, 1])
        r_axis = np.hypot(pts[:, 1], pts[:, 2] - zc)
        pts = pts[~((pts[:, 0] < lu + h / 2) & (r_axis < R + t + h / 2))].astype(np.float32)
        pm = make_particles(pts, h, soil).finalize()
        friction = {-1: 0.5, tube: cfg.steel_friction, side: 0.0, plate: cfg.steel_friction}
        friction.update({w: cfg.steel_friction for w in walls})
        solver = make_solver(pm, cm, dx, cfg.iterations, friction)
        st = cm.state()
        s = pm.state()
        s.body_q, s.body_qd, s.body_f = wp.clone(st.body_q), wp.zeros_like(st.body_qd), wp.zeros_like(st.body_f)
        body_index = solver.collider_body_index.numpy()

        dt = 1.0 / cfg.fps
        q = s.body_q.numpy()
        qd = np.zeros((cm.body_count, 6), dtype=np.float32)
        area = 0.5 * math.pi * (R - 0.25 * t) ** 2  # half model
        wall_area = (2 * math.pi * R / n_seg) * lu  # one segment's soil-side area
        gamma = soil.density * G

        self.cfg, self.soil, self.D, self.R, self.zc, self.zs, self.t, self.h = cfg, soil, D, R, zc, zs, t, h
        self.pts, self.solver, self.s, self.cm, self.plate, self.body_index = pts, solver, s, cm, plate, body_index
        self.dt, self.q, self.qd, self.area, self.gamma = dt, q, qd, area, gamma
        self.lu, self.walls, self.wall_dirs, self.wall_area = lu, walls, wall_dirs, wall_area
        self.wall_p = 0.0  # mean pressure on the unlined walls over the last step, Pa
        self.box = (np.array([-x_back, 0.0, 0.0]), np.array([x_front, half_w, zs]))

    def servo_speed(self, log: list, target_kpa: float) -> float:
        """Retract-only servo: the face gives way while the soil presses harder than the target, and stops otherwise.
        Retract-only: pushing the plate back into the soil spikes the pressure and makes the loop oscillate."""
        cfg = self.cfg
        p_avg = float(np.mean([e[1] for e in log[-6:]])) if log else 0.0  # average over 0.1 s: the probe is noisy
        vmax = cfg.servo_max_rate_over_d * self.D
        return float(np.clip(cfg.servo_gain * self.D * (p_avg - target_kpa * 1e3) / (self.gamma * self.D) * cfg.fps, 0.0, vmax))

    def step(self, v: float) -> tuple[float, float, float]:
        """Move the plate back at v (m/s) for one frame and step the soil. Returns (plate retraction m, face pressure
        Pa, step time s)."""
        import warp as wp

        s, q, qd, dt, plate = self.s, self.q, self.qd, self.dt, self.plate
        q[plate, 0] -= v * dt
        qd[plate, 0] = -v
        for w, u in zip(self.walls, self.wall_dirs):  # the unlined walls retract towards the axis at the same rate
            q[w, 0:3] -= v * dt * u
            qd[w, 0:3] = -v * u
        s.body_q.assign(q)
        s.body_qd.assign(qd)
        wp.synchronize()
        t0 = time.perf_counter()
        self.solver.step(s, s, contacts=None, control=None, dt=dt)
        wp.synchronize()
        elapsed = time.perf_counter() - t0
        forces = collider_forces(self.solver, s, self.body_index, dt)
        fx = float(forces.get(plate, np.zeros(3))[0])
        if self.walls:  # same sign convention as the plate: positive when the soil presses on the wall
            self.wall_p = float(np.mean([forces.get(w, np.zeros(3)) @ u for w, u in zip(self.walls, self.wall_dirs)])) / self.wall_area
        delta = max(0.0, -(q[plate, 0] - (self.lu - self.t / 2)))
        return delta, fx / self.area, elapsed


def run(cfg: FaceSandConfig, soil: Soil) -> tuple[dict, dict]:
    face = Face(cfg, soil)
    D, R, zc, zs, h, pts, s, gamma = face.D, face.R, face.zc, face.zs, face.h, face.pts, face.s, face.gamma
    dx = D / cfg.voxel_per_d
    n_ctrl = int(round(cfg.duration * cfg.fps)) if cfg.control == "pressure" else int(round(cfg.retract_over_d / cfg.rate_over_d * cfg.fps))

    log, times, ref = [], [], None
    for f in range(cfg.settle + n_ctrl):
        if f == cfg.settle:
            ref = s.particle_q.numpy().copy()  # positions when control starts: the displacement field is measured from here
        v = 0.0
        if f >= cfg.settle:
            v = cfg.rate_over_d * D if cfg.control == "displacement" else face.servo_speed(log, cfg.target_kpa)
        delta, p, elapsed = face.step(v)
        times.append(elapsed)
        log.append((delta, p, face.wall_p))

    log = np.array(log)
    ctrl = log[cfg.settle:]

    def p_at(frac: float, col: int = 1) -> float | None:
        d = ctrl[:, 0] / D
        k = np.where(d >= frac)[0]
        if not len(k):
            return None
        i = k[0]
        return float(np.mean(ctrl[max(i - 3, 0):i + 4, col]) / 1e3)

    # failure zone from the displacement since control started
    p_end = s.particle_q.numpy()
    disp = np.linalg.norm(p_end - ref, axis=1)
    moving = disp > cfg.moving_threshold_over_d * D
    near = moving & (ref[:, 1] < 0.25 * D) & (ref[:, 0] > 0)  # close to the symmetry plane, ahead of the face
    z_crown = zc + R
    top_moving = float(ref[near, 2].max()) if near.any() else float("nan")
    reaches_surface = bool(near.any() and top_moving > zs - 0.5 * h - dx)
    band = near & (np.abs(ref[:, 2] - z_crown) < dx)
    l_crown = float(ref[band, 0].max()) if band.any() else float("nan")
    wedge = math.degrees(math.atan2(D, l_crown)) if band.any() else float("nan")
    surf = (ref[:, 2] > zs - 1.5 * h) & (ref[:, 1] < 0.25 * D)
    settle_v = ref[surf, 2] - p_end[surf, 2]
    i_max = int(np.argmax(settle_v)) if surf.any() else 0

    p_ref = soil.density * G * D * (1.0 / (9.0 * math.tan(math.radians(soil.phi_deg))) - 0.05) if soil.phi_deg else float("nan")
    result = {
        "diameter_m": D, "cover_over_D": cfg.cover, "voxel_per_D": cfg.voxel_per_d, "particles": len(pts), "control": cfg.control,
        "p_settled_kPa": round(float(log[cfg.settle - 10:cfg.settle, 1].mean()) / 1e3, 3),
        "p_1pct_kPa": _r(p_at(0.01)), "p_3pct_kPa": _r(p_at(0.03)), "p_5pct_kPa": _r(p_at(0.0499)),
        "p_min_kPa": round(float(ctrl[:, 1].min()) / 1e3, 3),
        "face_displacement_over_D": round(float(ctrl[-1, 0] / D), 4),
        "p_final_kPa": round(float(np.mean(ctrl[-10:, 1])) / 1e3, 3),
        "zone_top_above_crown_over_D": round((top_moving - z_crown) / D, 3) if near.any() else None,
        "zone_reaches_surface": reaches_surface,
        "wedge_inclination_deg": round(wedge, 1) if band.any() else None,
        "max_settlement_over_D": round(float(settle_v.max()) / D, 5) if surf.any() else None,
        "max_settlement_ahead_of_face_over_D": round(float(ref[surf, 0][i_max]) / D, 3) if surf.any() else None,
        "p_vermeer_kPa": round(p_ref / 1e3, 3),
        "gamma_kN_m3": round(gamma / 1e3, 3),
        "ms_per_frame": round(float(np.mean(times[5:]) * 1000), 2),
    }
    if face.walls:  # unlined heading: wall pressure and the area-weighted support pressure on face and walls
        a_face, a_wall = face.area, face.wall_area * len(face.walls)
        result["unlined_over_D"] = cfg.unlined_over_d
        result["sigma_z_axis_kPa"] = round(gamma * (zs - zc) / 1e3, 3)
        for tag, frac in (("1pct", 0.01), ("3pct", 0.03), ("5pct", 0.0499)):
            pf, pw = p_at(frac), p_at(frac, 2)
            result[f"p_wall_{tag}_kPa"] = _r(pw)
            result[f"p_support_{tag}_kPa"] = None if pf is None else round((pf * a_face + pw * a_wall) / (a_face + a_wall), 3)
        result["p_wall_settled_kPa"] = round(float(log[cfg.settle - 10:cfg.settle, 2].mean()) / 1e3, 3)
    return result, {"log": log}


def _r(v):
    return None if v is None else round(v, 3)


def params(cfg: FaceSandConfig, soil: Soil) -> dict:
    return {**asdict(cfg), "soil": asdict(soil)}
