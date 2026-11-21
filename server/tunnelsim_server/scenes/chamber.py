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
of an EPB; the axis band feeds the controller), its vertical gradient (least squares over rows one voxel high across
the full section, |z - zc| < 0.8 R; the bands' own gradient is kept beside it), cutterhead torque, screw speed and the bulkhead
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
    # Start the paste already at the target pressure (elastic volume set to -p/K, with the paste's own weight below the
    # axis) and skip the piston push. The push packs 11-29 % more paste into the chamber than its nominal density, more at
    # finer voxels, because Newton loses elastic volume while the piston moves (15 Nov 2026).
    prestress: bool = False
    prestress_top_up: bool = False  # after the pre-stress, let the piston push to the target as usual
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
    # where the seal acts, in particle spacings beyond the shell radius: -0.25 (before 18 Nov) also moved paste resting just
    # inside the wall; 0 acts on paste in the wall only (18 Nov 2026 diagnosis of the grid-alignment cases)
    seal_margin: float = -0.25
    # shell plate thickness in voxels (0: the walls' thickness t, 2 voxels); its inner face stays at R (18 Nov 2026 leak test)
    shell_voxels: float = 0.0
    # move the shell's inner face out by this fraction of a voxel (18 Nov 2026 alignment test); the paste is placed and the
    # seal acts against the moved face, the rest of the machine stays sized by R
    shell_face_offset: float = 0.0
    # number of flat plates making up the round shell (48 before 19 Nov 2026; smoother-wall test)
    shell_facets: int = 48
    # > 0: the shell is one watertight tube mesh with this many segments (default since 19 Nov 2026); 0: the overlapping flat
    # plates used before, which leak at some grid alignments.
    # Newton merges a body's shapes into one collider mesh and signs the distance by the face normals at the closest point;
    # the plates' buried side faces then sign about a quarter of the grid nodes inside the wall as outside (offline check),
    # and paste is let into the wall where those nodes sit just behind the face
    shell_mesh: int = 256
    # sudden-loss trace only (21 Nov 2026): move the shell tube's far end (normally slab + 0.5 m past the chamber) or the
    # cutterhead along the axis by this many metres, everything else unchanged
    shell_end_shift: float = 0.0
    cutter_shift: float = 0.0
    # paste on steel (shell, bulkhead, piston): 0.3, within conditioned soil on steel by inclined plate, 0.31-0.58
    # (Applied Sciences 10 (2020) 3300, doi:10.3390/app10093300), and kaolin on steel, 0.33 (Henke & Wiesenthal, WCCM
    # 2024); < 0 keeps the Phase 0 values 0.3 / 0.3 / 0.5
    wall_friction: float = 0.3
    # diagnostic: friction on the bulkhead alone (< 0: as wall_friction)
    bulkhead_friction: float = -1.0
    # volume balance 3: join regions smaller than this fraction of the fullest to the next one towards the axis (0: off).
    # An assumed numerical setting; at 0.12-0.15 m only the 12 corner regions fall under a tenth (15 Nov 2026).
    vb_merge_region_frac: float = 0.1
    vb_min_region_frac: float = 0.0  # volume balance: leave out regions with fewer reference particles than this fraction of the fullest region
    stress_log: bool = False  # log the paste's own stress beside the bulkhead next to the contact-force reading
    # gradient diagnosis (16 Nov 2026): the bulkhead contact force summed by grid-node row (world z / voxel) per phase, and
    # the last frame's per-node forces of each phase, so the gradient can be read without the fixed height bands
    contact_rows: bool = False
    # log, every frame, the bulkhead pressure on square patches 0.2, 0.4 and 0.8 m wide at three gauge positions, placed
    # as Botlek's E1 (top), E3 (axis, to the side) and E5 (low, beside the screw) in Bezuijen et al. (2005), Figs 3 and 7,
    # scaled to this radius (approximate); for comparing the pressure band with one gauge (21 Nov 2026)
    gauge_log: bool = False
    # alignment test (16 Nov 2026): raise the whole machine by this much (m), moving its axis relative to the solver grid
    z_shift: float = 0.0
    # balance diagnosis (18 Nov 2026): per region of the balance, over the excavation, the correction it takes each frame
    # (mean, mean absolute, frames) and where the region is (particle centroid)
    vb_region_log: bool = False
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
    # Solver steps per frame, and iterations per step. Newton takes each particle's elastic strain from the stress its
    # iteration has reached and drops the rest, so a solve that has not converged loses elastic volume, more at finer
    # voxels. With one step of 100 iterations the piston push packed 11 / 13 / 27 % more paste into the chamber at
    # 0.15 / 0.12 / 0.10 m and 0.10 m did not hold; with 4 steps of 50 it is 8 % at all three and all hold (15 Nov 2026).
    iterations: int = 50
    substeps: int = 4
    substep_check: bool = False  # log invalid particles and speeds after every solver step
    substep_repair: bool = False  # reset invalid particles after every solver step, not once per frame
    # the same check on the GPU, at almost no cost (21 Nov 2026): after every solver step, count invalid particles (elastic
    # volume <= 0 or not finite, velocity not finite) and extreme ones (J outside 0.1-10), and the fastest speed; every 15
    # frames, where the extreme and fast (> 15 m/s) ones are. When one is
    # invalid: save it and its neighbours (2 voxels) before and after that step, then reset it as substep_repair does.
    # On by default since 21 Nov 2026: a numerical safeguard, not physics. Extreme particles collect in the corner of the
    # ground face and the shell once the face passes x ~ 1.26 m (cause not found); one of them going invalid most likely
    # lost a whole 0.10 m chamber on 20 Nov. The result reports how many particles were reset
    substep_guard: bool = True
    # where and when the analytical screw takes paste from its inlet. "centre" (default since 16 Nov 2026): the particles
    # nearest the middle of the inlet. "wall" (before): those deepest in the casing, against the bulkhead; emptying that
    # corner drew jets of paste into it (up to 235 m/s against under 4 m/s elsewhere), and a particle crushed there turned
    # the whole chamber invalid within one solver step (0.12 m, seed 2: 3 of 4 recorded runs lost; with "centre" 0 of 5, no
    # particle above 12 m/s). Per substep: the frame's discharge split over the solver steps (no further effect seen).
    screw_pick: str = "centre"
    screw_per_substep: bool = False
    # diagnosis of Newton PR 5021's volume recovery (16 Nov 2026, needs that PR's Newton with our probe patch): log the packing
    # fraction it measures against the space it counts free, by distance from the shell, every few frames
    vr_probe: bool = False
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


def _tube_mesh(R, zc, t, n, x0, x1):
    """Watertight tube along x (inner radius R, outer R + t, x0..x1), every face wound away from the solid."""
    th = 2 * np.pi * np.arange(n) / n
    ring = lambda r, x: np.stack([np.full(n, x), r * np.cos(th), zc + r * np.sin(th)], 1)
    V = np.vstack([ring(R, x0), ring(R, x1), ring(R + t, x0), ring(R + t, x1)])
    k = np.arange(n); j = (k + 1) % n
    i0, i1, o0, o1 = 0, n, 2 * n, 3 * n
    quads = [(i0 + k, i1 + k, i1 + j, i0 + j), (o0 + k, o0 + j, o1 + j, o1 + k), (i0 + k, i0 + j, o0 + j, o0 + k), (i1 + k, o1 + k, o1 + j, i1 + j)]
    T = np.concatenate([np.concatenate([np.stack([a, b, c], 1), np.stack([a, c, d], 1)]) for a, b, c, d in quads])
    P = V[T]; c = P.mean(1); nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    rad = np.stack([np.zeros(len(c)), c[:, 1], c[:, 2] - zc], 1)
    rad /= np.linalg.norm(rad, axis=1)[:, None]
    out = np.concatenate([-rad[:2 * n], rad[2 * n:4 * n], np.tile([-1.0, 0, 0], (2 * n, 1)), np.tile([1.0, 0, 0], (2 * n, 1))])
    flip = np.einsum("ij,ij->i", nrm, out) < 0
    T[flip] = T[flip][:, [0, 2, 1]]
    return V.astype(np.float32), T.astype(np.int32)


_GUARD_KERNEL = None


def _guard_kernel():
    """Warp kernel for ChamberConfig.substep_guard, built once (warp is imported lazily here, as in the rest of the scene)."""
    global _GUARD_KERNEL
    if _GUARD_KERNEL is None:
        import warp as wp

        @wp.kernel
        def guard(fe: wp.array(dtype=wp.mat33), qd: wp.array(dtype=wp.vec3), flags: wp.array(dtype=wp.int32), active: wp.int32,
                  j_lo: float, j_hi: float, v_fast: float, out: wp.array(dtype=wp.int32), idx: wp.array(dtype=wp.int32),
                  vmax: wp.array(dtype=float), odd: wp.array(dtype=wp.int32)):
            i = wp.tid()
            if (flags[i] & active) == 0:
                return
            j = wp.determinant(fe[i])
            v = qd[i]
            ok_v = wp.isfinite(v)
            if (not wp.isfinite(j)) or j <= 0.0 or (not ok_v):
                k = wp.atomic_add(out, 0, 1)
                if k < idx.shape[0]:
                    idx[k] = i
            else:
                if j < j_lo or j > j_hi:
                    wp.atomic_add(out, 1, 1)
                if j < j_lo or j > j_hi or wp.length(v) > v_fast:  # extreme or fast: keep the index, to see where
                    k2 = wp.atomic_add(out, 2, 1)
                    if k2 < odd.shape[0]:
                        odd[k2] = i
            if ok_v:
                wp.atomic_max(vmax, 0, wp.length(v))

        _GUARD_KERNEL = guard
    return _GUARD_KERNEL


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
    zc = R + 0.5 + cfg.z_shift
    t = max(0.2, 2 * dx)  # walls at least one voxel thick (Phase 0)
    area = math.pi * R**2
    R_f = R + cfg.shell_face_offset * dx  # the shell's inner face

    b = newton.ModelBuilder()
    shell = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True, label="shell")
    n_seg = cfg.shell_facets
    x0, x1 = -t, L + cfg.slab + 0.5 + cfg.shell_end_shift
    t_sh = cfg.shell_voxels * dx if cfg.shell_voxels > 0 else t
    if cfg.shell_mesh > 0:
        V_sh, T_sh = _tube_mesh(R_f, zc, t_sh, cfg.shell_mesh, x0, x1)
        b.add_shape_mesh(shell, mesh=newton.Mesh(V_sh, T_sh.ravel(), compute_inertia=False))
    for k in range(n_seg if cfg.shell_mesh <= 0 else 0):
        th = 2 * math.pi * k / n_seg
        b.add_shape_box(shell, xform=_rot_x_plate(((x0 + x1) / 2, (R_f + t_sh / 2) * math.cos(th), zc + (R_f + t_sh / 2) * math.sin(th)), th),
                        hx=(x1 - x0) / 2, hy=1.08 * R_f * math.tan(math.pi / n_seg), hz=t_sh / 2)
    bulkhead = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True, label="bulkhead")
    add_walls(b, bulkhead, [((-t / 2, 0.0, zc), (t / 2, R + t, R + t))])
    x_ch = L - 0.15 + cfg.cutter_shift
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
    gx, gy, gz = np.arange(h / 2, x_face, h),np.arange(-R_f, R_f, h), np.arange(zc - R_f, zc + R_f, h)
    X, Y, Z = np.meshgrid(gx, gy, gz, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    pts = pts[np.hypot(pts[:, 1], pts[:, 2] - zc) < R_f - h / 2]
    j = common.JITTER  # initial jitter, a fraction of h (as fill_box)
    pts = (pts + rng.uniform(-j * h, j * h, pts.shape)).astype(np.float32)
    pm = make_particles(pts, h, soil).finalize()
    mass_p = pm.particle_mass.numpy()
    solver = make_solver(pm, cm, dx, cfg.iterations, {shell: wf if (wf := cfg.wall_friction) >= 0 else 0.3, bulkhead: cfg.bulkhead_friction if cfg.bulkhead_friction >= 0 else (wf if wf >= 0 else 0.3), cutter: 0.3, piston: wf if wf >= 0 else 0.5, -1: 0.5})
    if cfg.vr_probe:
        solver._ts_probe = True
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
    # band edges on the solver grid, a quarter voxel below a vertex row (16 Nov 2026): Newton reports the contact force at
    # cell centres and at vertices, and a band with fixed edges caught an uneven share of the two lattices, so each band
    # read 0.8-1.25 times its pressure depending on the voxel (gradient 10.6 / 14.5 / 12.7 kPa/m at 0.15 / 0.12 / 0.10 m
    # against 11.5 / 13.2 / 11.3 read without it; the 0.15 m chamber was held at 227 kPa for 200). Snapped edges hold the
    # same number of rows of each lattice.
    edges = (np.round((zc + np.linspace(-0.9 * R, 0.9 * R, 10)) / dx) - 0.25) * dx - zc
    zz = np.linspace(-R, R, 40001)
    chord = 2 * np.maximum(np.sqrt(np.maximum(R**2 - zz**2, 0)) - y_min, 0)
    band_area = np.array([np.trapezoid(chord * ((zz >= lo) & (zz < hi)), zz) for lo, hi in zip(edges[:-1], edges[1:])])
    band_z = np.array([np.trapezoid(chord * zz * ((zz >= lo) & (zz < hi)), zz) for lo, hi in zip(edges[:-1], edges[1:])]) / band_area
    axis_band = len(band_z) // 2
    # the reported gradient (20 Nov 2026): rows one voxel high across the full section (edges a quarter voxel below the
    # vertex rows), every bulkhead contact, least squares over |z - zc| < 0.8 R. In a force balance over the excavation the bulkhead read this
    # way matched the paste's own stress 1-4 voxels out (14.38 / 14.65 kPa/m at 0.10 / 0.12 m against 14.5-14.6), while
    # the bands, which leave out the strip |y| < y_min round the screw inlet, read 14.41 / 15.25.
    row_e = (np.arange(np.floor((zc - R) / dx), np.ceil((zc + R) / dx) + 1) - 0.25) * dx - zc
    chord_full = 2 * np.sqrt(np.maximum(R**2 - zz**2, 0))
    # gauge patches: (name, y, z - zc), each with side 0.2 / 0.4 / 0.8 m, edges snapped a quarter voxel below the vertex
    # lines in y and z as the bands are, so each patch holds the same share of Newton's two lattices of contact points
    gauges = [("E1", 0.12 * R, 0.78 * R), ("E3", 0.7 * R, 0.0), ("E5", 0.18 * R, -0.7 * R)]
    gauge_sides = (0.2, 0.4, 0.8)
    snap = lambda v: (np.round(v / dx) - 0.25) * dx
    gauge_box = [(snap(y - a / 2), snap(y + a / 2), snap(zc + z - a / 2) - zc, snap(zc + z + a / 2) - zc) for _, y, z in gauges for a in gauge_sides]
    gauge_hist = []
    row_area = np.array([np.trapezoid(chord_full * ((zz >= lo) & (zz < hi)), zz) for lo, hi in zip(row_e[:-1], row_e[1:])])
    row_ok = row_area > 0
    row_z = np.where(row_ok, np.array([np.trapezoid(chord_full * zz * ((zz >= lo) & (zz < hi)), zz) for lo, hi in zip(row_e[:-1], row_e[1:])]) / np.where(row_ok, row_area, 1.0), 0.0)
    row_fit = row_ok & (np.abs(row_z) < 0.8 * R)

    dt = 1.0 / cfg.fps
    w_c = cfg.cutter_rpm * 2 * math.pi / 60
    v_adv = cfg.advance_mm_min / 1000 / 60
    q = s.body_q.numpy()
    q0_cut = q[cutter, 3:7].copy()
    x_p = x_face + t / 2
    ang = 0.0
    phase, t_phase = "pressurise", 0.0
    if cfg.prestress:
        z0 = s.particle_q.numpy()[:, 2]
        p0 = cfg.target_kpa * 1e3 + soil.density * G * (zc - z0)
        fe0 = np.exp(-p0 / soil.extra["bulk_modulus_Pa"] / 3.0)[:, None, None] * np.eye(3)[None]
        s.mpm.particle_elastic_strain.assign(fe0.astype(np.float32))
        if not cfg.prestress_top_up:  # otherwise the piston makes up what the first steps shed (38-57 % of the pressure)
            phase = "hold"
    rpm, integ, owed = 0.0, 0.0, 0.0
    p_hist: list[float] = []
    log, times = [], []
    removed = 0
    resealed = 0
    vb_ref = None
    vb_log: list = []
    vb_reg_acc = None
    seal_facets = np.zeros((2, n_seg), dtype=np.int64)  # resets by shell facet: all phases, excavation only (18 Nov 2026)
    seal_x_edges = np.arange(-t, x_face + 0.5, 0.1)  # and, over the excavation, by facet and 0.1 m slice along the axis
    seal_fx = np.zeros((n_seg, len(seal_x_edges) - 1), dtype=np.int64)
    vb_map = None
    sub_log: list = []
    sub_bad: list = []
    sub_ext: list = []
    vrp_log: list = []
    sub_repaired = 0
    guard_log: list = []  # substep_guard: per solver step (t, step, invalid, extreme, fastest m/s)
    guard_events: list = []  # substep_guard: each step with an invalid particle, the particles and their neighbours
    guard_buf = None
    guard_odd: list = []  # substep_guard: every 15 frames, the extreme (J outside 0.1-10) and fast (> 15 m/s) particles
    vb_repaired = 0
    stress_log: list = []
    # diagnostic (20 Nov 2026), with stress_log: the bulkhead's axial force against the paste's own axial stress, summed
    # over the excavation. Cuts across the whole section every voxel from the bulkhead (sigma_xx x nominal particle
    # volume / cut thickness, as checked against the forces in a tank), the other solids' axial forces between, and by
    # height rows (a quarter voxel below the vertex rows) the bulkhead force and the paste 1-2 and 2-4 voxels out
    # (cuts run to the ground face, through the mixing arms and the cutterhead: the paste clear of solids is only about
    # 0.1 m deep, under one voxel)
    bal_x = np.arange(0.0, x_face + 1e-6, dx)
    bal_z = (np.arange(np.floor((zc - R) / dx), np.ceil((zc + R) / dx) + 1) - 0.25) * dx
    bal = {"x_edges": bal_x.tolist(), "z_edges": bal_z.tolist(), "frames": 0, "thrust": 0.0, "cut": np.zeros(len(bal_x) - 1),
           "other_x": np.zeros(len(bal_x) - 1), "bh_row": np.zeros(len(bal_z) - 1), "paste_row": np.zeros((2, len(bal_z) - 1))}
    n_rows = int(round((zc + R + 1.0) / dx)) + 2
    crow = np.zeros((4, 2, 2, 2, n_rows))  # by phase, lattice (centres, vertices), points (all, 2 voxels clear of the shell): summed x force, count; per row
    cframes = np.zeros(4)
    csnap: dict = {}
    n_prof, prof, prof_x = 10, np.zeros((4, 4, 10)), 0.0  # by phase: mass, summed mean stress, particle count, frames; per height bin
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
                    step = {"t_s": f * dt, "n_particles": int(((flags & active) != 0).sum()), "rpm_before": rpm_before, "rpm_after": float(np.clip(rpm_before + cfg.screw_step_rpm, 0.0, cfg.max_screw_rpm)),
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
        def take_from_inlet(owed):
            nonlocal removed
            if not owed >= 1.0:  # also NaN, once the chamber has collapsed
                return owed
            xq = s.particle_q.numpy()
            inside = np.where(((flags & active) != 0) & np.all((xq >= sink_lo) & (xq <= sink_hi), axis=1))[0]
            n = min(int(owed), len(inside))
            if n:
                if cfg.screw_pick == "centre":
                    key = np.linalg.norm(xq[inside] - (sink_lo + sink_hi) / 2, axis=1)
                else:
                    key = xq[inside, 0]
                take = inside[np.argsort(key)[:n]]
                flags[take] &= ~active
                pm.particle_flags.assign(flags)
                solver.notify_model_changed(newton.ModelFlags.MODEL_PROPERTIES)
                removed += n
            return owed - int(owed)

        if not cfg.screw_per_substep:
            owed = take_from_inlet(owed + screw.discharge(rpm) * dt / v_particle)

        wp.synchronize()
        t0 = time.perf_counter()
        for k_sub in range(cfg.substeps):
            if cfg.screw_per_substep:
                owed = take_from_inlet(owed + screw.discharge(rpm) * dt / cfg.substeps / v_particle)
            solver.step(s, s, contacts=None, control=None, dt=dt / cfg.substeps)
            if cfg.substep_guard:
                if guard_buf is None:
                    n_all = s.particle_q.shape[0]
                    guard_buf = {"out": wp.zeros(3, dtype=wp.int32), "idx": wp.zeros(64, dtype=wp.int32), "vmax": wp.zeros(1, dtype=float), "odd": wp.zeros(256, dtype=wp.int32),
                                 "q": wp.clone(s.particle_q), "qd": wp.clone(s.particle_qd), "fe": wp.clone(s.mpm.particle_elastic_strain), "n": n_all}
                gb = guard_buf
                gb["out"].zero_()
                gb["vmax"].zero_()
                wp.launch(_guard_kernel(), dim=gb["n"], inputs=[s.mpm.particle_elastic_strain, s.particle_qd, pm.particle_flags, active,
                                                                0.1, 10.0, 15.0, gb["out"], gb["idx"], gb["vmax"], gb["odd"]])
                o_ = gb["out"].numpy()
                guard_log.append((f * dt, k_sub, int(o_[0]), int(o_[1]), float(gb["vmax"].numpy()[0]), int(o_[2])))
                if o_[2] > 0 and k_sub == cfg.substeps - 1 and f % 15 == 0 and len(guard_odd) < 400:  # where the extreme and fast ones are
                    io_ = gb["odd"].numpy()[:min(int(o_[2]), 256)]
                    with np.errstate(all="ignore"):
                        jo_ = np.linalg.det(s.mpm.particle_elastic_strain.numpy()[io_])
                    guard_odd.append({"t": f * dt, "phase": phase, "n": int(o_[2]), "x_ground": x_p - t / 2, "idx": io_.tolist(), "q": s.particle_q.numpy()[io_].round(3).tolist(),
                                      "v": s.particle_qd.numpy()[io_].round(2).tolist(), "J": np.nan_to_num(jo_, nan=-1.0).round(4).tolist()})
                if o_[0] > 0:
                    ib = gb["idx"].numpy()[:min(int(o_[0]), 64)]
                    q1, qd1, fe1 = s.particle_q.numpy(), s.particle_qd.numpy(), s.mpm.particle_elastic_strain.numpy()
                    q0, qd0, fe0 = gb["q"].numpy(), gb["qd"].numpy(), gb["fe"].numpy()
                    act_ = (flags & active) != 0
                    if len(guard_events) < 20:
                        with np.errstate(all="ignore"):
                            near_ = act_ & (np.min(np.linalg.norm(q0[:, None, :] - q0[ib[:8]][None], axis=2), axis=1) < 2 * dx)
                            j0, j1 = np.linalg.det(fe0[near_]), np.linalg.det(fe1[near_])
                        guard_events.append({"t": f * dt, "step": k_sub, "phase": phase, "invalid": int(o_[0]), "extreme": int(o_[1]),
                                             "first": ib[:8].tolist(), "x_cutter": x_ch, "x_ground": x_p - t / 2, "screw_rpm": rpm,
                                             "near": np.nonzero(near_)[0].tolist(), "q_before": q0[near_].round(4).tolist(), "q_after": np.nan_to_num(q1[near_], nan=1e9).round(4).tolist(),
                                             "v_before": qd0[near_].round(3).tolist(), "v_after": np.nan_to_num(qd1[near_], nan=1e9).round(3).tolist(),
                                             "J_before": np.nan_to_num(j0, nan=-1.0).round(5).tolist(), "J_after": np.nan_to_num(j1, nan=-1.0).round(5).tolist()})
                    # reset, as substep_repair: the invalid particles to the mean elastic volume of the rest, at rest
                    with np.errstate(all="ignore"):
                        dj1 = np.linalg.det(fe1)
                    bad_fe = act_ & ~(np.isfinite(dj1) & (dj1 > 0))
                    bad_v = act_ & ~np.isfinite(qd1).all(axis=1)
                    good = act_ & ~bad_fe
                    fe1[bad_fe] = math.exp(float(np.log(dj1[good]).mean()) / 3.0) * np.eye(3, dtype=np.float32)
                    qd1[bad_v] = 0.0
                    if bad_v.any():  # a particle with no finite velocity has no finite position either: put it back where it was
                        q1[bad_v] = q0[bad_v]
                        s.particle_q.assign(q1)
                    s.mpm.particle_elastic_strain.assign(fe1)
                    s.particle_qd.assign(qd1)
                    sub_repaired += int(bad_fe.sum()) + int(bad_v.sum())
                wp.copy(gb["q"], s.particle_q)
                wp.copy(gb["qd"], s.particle_qd)
                wp.copy(gb["fe"], s.mpm.particle_elastic_strain)
            if cfg.substep_check or cfg.substep_repair:  # diagnosis of a sudden collapse (16 Nov 2026)
                fe_ = s.mpm.particle_elastic_strain.numpy()
                qd_ = s.particle_qd.numpy()
                act_ = (flags & active) != 0
                with np.errstate(all="ignore"):
                    dj_ = np.linalg.det(fe_)
                bad_fe = act_ & ~(np.isfinite(dj_) & (dj_ > 0))
                bad_v = act_ & ~np.isfinite(qd_).all(axis=1)
                spd = np.linalg.norm(np.nan_to_num(qd_[act_]), axis=1)
                sub_log.append((f * dt, k_sub, int(bad_fe.sum()), int(bad_v.sum()), float(spd.max()), float(np.percentile(spd, 99.9)),
                                float(np.nanmin(np.where(act_ & ~bad_fe, dj_, np.nan))), float(np.nanmax(np.where(act_ & ~bad_fe, dj_, np.nan)))))
                ext_ = act_ & ~bad_fe & ((dj_ > 10.0) | (dj_ < 0.1))  # extreme volume change: where, and how many
                if ext_.any() and len(sub_ext) < 3000:
                    xq_e = s.particle_q.numpy()
                    i_hi = int(np.nanargmax(np.where(act_ & ~bad_fe, dj_, np.nan)))
                    i_v = int(np.argmax(np.where(act_, np.linalg.norm(np.nan_to_num(qd_), axis=1), -1.0)))
                    sub_ext.append((f * dt, k_sub, int(ext_.sum()), int((act_ & (dj_ > 10.0)).sum()), float(dj_[i_hi]), xq_e[i_hi].round(2).tolist(),
                                    float(np.linalg.norm(qd_[i_v])), xq_e[i_v].round(2).tolist(), int(i_hi), int(i_v)))
                if (bad_fe.any() or bad_v.any()) and len(sub_bad) < 20:
                    xq_b = s.particle_q.numpy()[bad_fe | bad_v][:5]
                    sub_bad.append((f * dt, k_sub, int(bad_fe.sum()), int(bad_v.sum()), xq_b.round(2).tolist()))
                if cfg.substep_repair and (bad_fe.any() or bad_v.any()):
                    good = act_ & ~bad_fe
                    lj = float(np.log(dj_[good]).mean())
                    fe_[bad_fe] = math.exp(lj / 3.0) * np.eye(3, dtype=np.float32)
                    qd_[bad_v] = 0.0
                    s.mpm.particle_elastic_strain.assign(fe_)
                    s.particle_qd.assign(qd_)
                    sub_repaired += int(bad_fe.sum()) + int(bad_v.sum())
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
            if vb_map is None and cfg.volume_balance == 3 and cfg.vb_merge_region_frac > 0 and (phase == "excavate" or cfg.vb_from_hold):
                # regions cut small by the shell join the next region towards the axis, in the same slice, until the joined
                # region holds vb_merge_region_frac of the fullest one. Fixed when the reference is taken.
                raw = np.bincount(reg[reg >= 0], minlength=n_side * n_side * n_ax).astype(float)
                vb_map, c_mid = np.arange(len(raw)), (n_side - 1) / 2
                order = sorted(range(len(raw)), key=lambda rq: -max(abs((rq // n_side) % n_side - c_mid), abs(rq % n_side - c_mid)))
                for rq in order:
                    if raw[rq] == 0 or raw[rq] >= cfg.vb_merge_region_frac * raw.max():
                        continue
                    qx, qy, qz = rq // (n_side * n_side), (rq // n_side) % n_side, rq % n_side
                    dy_, dz_ = abs(qy - c_mid), abs(qz - c_mid)
                    if dy_ >= dz_ and dy_ > 0.5:
                        qy += 1 if qy < c_mid else -1
                    if dz_ >= dy_ and dz_ > 0.5:
                        qz += 1 if qz < c_mid else -1
                    tgt = (qx * n_side + qy) * n_side + qz
                    if tgt != rq:
                        vb_map[vb_map == rq] = tgt
                        raw[tgt] += raw[rq]
                        raw[rq] = 0
            if vb_map is not None:
                reg = np.where(reg >= 0, vb_map[np.clip(reg, 0, len(vb_map) - 1)], -1)
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
                # regions cut small by the shell are left uncorrected: fewer than 50 reference particles, or (vb_min_region_frac)
                # less than that fraction of the fullest region. A sliver's count can grow many times over as particles
                # collect in it, and the count term then compresses them until their strain degenerates (15 Nov 2026).
                valid = (ref_cnt >= max(50.0, cfg.vb_min_region_frac * ref_cnt.max())) & (cnt > 0)
                target = ref_mean + math.log((x_p - t / 2) / (vb_ref[1] - t / 2)) - np.log(np.where(valid, cnt / np.maximum(ref_cnt, 1), 1.0))
                shift = np.where(valid, target - mean, 0.0)
                vb_log.append((f * dt, float(target[valid].mean()), float(mean[valid].mean()), int(act.sum()), x_p, int((act & ~ok).sum()),
                               # diagnosis of a runaway: the regions in use, the emptiest one against its reference count, the largest
                               # correction of a frame (in ln J), and the region that takes it
                               int(valid.sum()), float((cnt / np.maximum(ref_cnt, 1))[valid].min()), float(np.abs(shift).max()), int(np.abs(shift).argmax()),
                               float(cnt[int(np.abs(shift).argmax())]), float(ref_cnt[int(np.abs(shift).argmax())])))
                if cfg.vb_region_log and phase == "excavate" and cfg.volume_balance == 3:
                    if vb_reg_acc is None:
                        vb_reg_acc = np.zeros((m, 8))  # sum shift, sum |shift|, frames, sum count, sum x, y, z of centroid, valid frames
                    cx = [np.bincount(r_ok[use], weights=xq_[use, k], minlength=m) / np.maximum(cnt, 1) for k in range(3)]
                    vb_reg_acc[:, 0] += shift
                    vb_reg_acc[:, 1] += np.abs(shift)
                    vb_reg_acc[:, 2] += 1.0
                    vb_reg_acc[:, 3] += cnt
                    vb_reg_acc[:, 4] += cx[0]
                    vb_reg_acc[:, 5] += cx[1]
                    vb_reg_acc[:, 6] += cx[2] - zc
                    vb_reg_acc[:, 7] += valid
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
            out = (r > R_f + cfg.seal_margin * h) & (xq[:, 0] > -t) & (xq[:, 0] < x_p - t / 2)
            if out.any():
                ny, nz = ry[out] / r[out], rz[out] / r[out]
                vr = vq[out, 1] * ny + vq[out, 2] * nz
                vq[out, 1] -= np.maximum(vr, 0) * ny
                vq[out, 2] -= np.maximum(vr, 0) * nz
                xq[out, 1], xq[out, 2] = (R_f - h / 2) * ny, zc + (R_f - h / 2) * nz
                s.particle_q.assign(xq)
                s.particle_qd.assign(vq)
                resealed += int(out.sum())
                kf = np.round(np.arctan2(nz, ny) / (2 * math.pi / n_seg)).astype(int) % n_seg
                fc = np.bincount(kf, minlength=n_seg)
                seal_facets[0] += fc
                if phase == "excavate":
                    seal_facets[1] += fc
                    kx = np.clip(np.searchsorted(seal_x_edges, xq[out, 0]) - 1, 0, seal_fx.shape[1] - 1)
                    np.add.at(seal_fx, (kf, kx), 1)

        imp, pos, cid = solver.collect_collider_impulses(s)
        imp, pos, cid = imp.numpy(), pos.numpy(), cid.numpy()
        valid = cid >= 0
        bid = np.full(cid.shape, -2)
        bid[valid] = body_index[np.clip(cid[valid], 0, len(body_index) - 1)]
        F = imp / (dt / cfg.substeps)
        on = (bid == bulkhead) & (np.abs(pos[:, 1]) > y_min) & (np.hypot(pos[:, 1], pos[:, 2] - zc) < R)
        zb = pos[on, 2] - zc
        fx = -F[on, 0]  # F is along -x where the soil presses on the bulkhead
        p_band = np.array([fx[(zb >= lo) & (zb < hi)].sum() for lo, hi in zip(edges[:-1], edges[1:])]) / band_area
        grad_band = -float(np.polyfit(band_z, p_band, 1)[0])  # pressure rises downwards
        on_r = bid == bulkhead  # every bulkhead contact, so the rows add up to the thrust; leaving out the points beyond
        # the shell radius took force out unevenly by row (0.12 m read 14.90 for 14.67, same seed)
        p_row = np.histogram(pos[on_r, 2] - zc, row_e, weights=-F[on_r, 0])[0][row_fit] / row_area[row_fit]
        grad = -float(np.polyfit(row_z[row_fit], p_row, 1)[0])
        if cfg.gauge_log:
            yb_, zb_, fb_ = pos[on_r, 1], pos[on_r, 2] - zc, -F[on_r, 0]
            gauge_hist.append([f * dt, ["pressurise", "hold", "excavate", "stop"].index(phase)]
                              + [float(fb_[(yb_ >= y0) & (yb_ < y1) & (zb_ >= z0) & (zb_ < z1)].sum() / ((y1 - y0) * (z1 - z0)) / 1e3) for y0, y1, z0, z1 in gauge_box])
        if cfg.contact_rows:
            ph_c = ["pressurise", "hold", "excavate", "stop"].index(phase)
            # Newton's collider forces sit on two lattices: cell centres (z = (k + 1/2) voxel) and vertices (z = k voxel);
            # each is summed by its own rows, over all points and over those two voxels or more inside the shell
            zw = pos[on, 2] / dx
            cen = np.abs(zw % 1.0 - 0.5) < 0.25
            kr = np.clip(np.where(cen, np.floor(zw), np.round(zw)).astype(int), 0, n_rows - 1)
            clear = np.hypot(pos[on, 1], pos[on, 2] - zc) < R - 2 * dx
            for li, lm in ((0, cen), (1, ~cen)):
                for ci, cmask in ((0, np.ones_like(clear)), (1, clear)):
                    mm = lm & cmask
                    crow[ph_c, li, ci, 0] += np.bincount(kr[mm], weights=fx[mm], minlength=n_rows)
                    crow[ph_c, li, ci, 1] += np.bincount(kr[mm], minlength=n_rows)
            cframes[ph_c] += 1.0
            onb = bid == bulkhead
            csnap[ph_c] = {"pos": pos[onb].tolist(), "fx": (-F[onb, 0]).tolist()}
        thrust = -float(F[bid == bulkhead, 0].sum())
        m = bid == cutter
        torque = float(np.cross(pos[m] - np.array([x_ch, 0.0, zc]), F[m])[:, 0].sum())
        f_cutter_x = -float(F[m, 0].sum())  # soil pushing the cutterhead back (towards -x)
        p_piston = float(F[bid == piston, 0].sum()) / area  # soil pushing the piston forwards (+x)
        pp_hist.append(p_piston)
        if cfg.vr_probe and f % 6 == 0 and getattr(solver, "_ts_fractions", None):
            xq_ = s.particle_q.numpy()
            a_ = (flags & active) != 0
            n_p = len(xq_)
            jq_ = np.linalg.det(s.mpm.particle_elastic_strain.numpy())
            d_sh = (R - np.hypot(xq_[:, 1], xq_[:, 2] - zc)) / dx  # voxels from the shell
            inner_x = (xq_[:, 0] > 4 * dx) & (xq_[:, 0] < x_p - t / 2 - 4 * dx) & ((xq_[:, 0] < x_ch - 0.56 - 2 * dx) | (xq_[:, 0] > x_ch + 0.11 + 2 * dx))
            bins = {"sh<0.5": d_sh < 0.5, "sh0.5-1": (d_sh >= 0.5) & (d_sh < 1), "sh1-2": (d_sh >= 1) & (d_sh < 2), "sh2-4": (d_sh >= 2) & (d_sh < 4),
                    "sh>4": d_sh >= 4, "sh>4 off walls": (d_sh >= 4) & inner_x, "bulkhead<1": (xq_[:, 0] < dx) & (d_sh >= 1), "piston<1": (xq_[:, 0] > x_p - t / 2 - dx) & (d_sh >= 1), "all": np.ones(n_p, bool)}
            row = {"t": f * dt, "phase": phase}
            for meas, (m_, a_f) in solver._ts_fractions.items():
                mv, av = m_.numpy()[:n_p], a_f.numpy()[:n_p]
                ok = a_ & (av > 0) & np.isfinite(mv) & np.isfinite(jq_)
                for k_, b_ in bins.items():
                    sel = ok & b_
                    if sel.any():
                        rr_ = mv[sel] / av[sel]
                        row[f"{meas}:{k_}"] = (int(sel.sum()), float(np.mean(rr_)), float(np.percentile(rr_, 5)), float(np.percentile(rr_, 95)),
                                               float(np.mean(av[sel])), float(np.mean(jq_[sel])), float(np.mean(rr_ / jq_[sel])))
            vrp_log.append(row)
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
            # diagnostic (20 Nov 2026): vertical gradient of the stress per unit of space (particle stress x mass over the
            # paste density and the bin volume) in the two prisms R/4 < |y| < R/2, by slab along the axis from the bulkhead.
            # The first slab (within a voxel of the bulkhead) reads high, as the first voxel off a wall did in the tank; the
            # last is empty (nan) where the mixing arms start less than four voxels from the bulkhead.
            g_slab = []
            zb_ = np.linspace(-0.8 * R, 0.8 * R, 11)
            for xa, xb in ((0.0, dx), (dx, 2 * dx), (2 * dx, 4 * dx), (4 * dx, x_ch - 0.6)):
                if xb <= xa:
                    g_slab.append(np.nan)
                    continue
                sl =a_ & (xq_[:, 0] >= xa) & (xq_[:, 0] < xb) & (np.abs(xq_[:, 1]) > R / 4) & (np.abs(xq_[:, 1]) < R / 2) & np.isfinite(p_part)
                kz = np.digitize(xq_[sl, 2] - zc, zb_) - 1
                okz = (kz >= 0) & (kz < 10)
                ps_ = np.bincount(kz[okz], weights=(p_part[sl] * mass_p[sl])[okz], minlength=10) / (cfg.paste_density * (xb - xa) * R / 2 * (zb_[1] - zb_[0]))
                g_slab.append(-float(np.polyfit((zb_[:-1] + zb_[1:]) / 2, ps_, 1)[0]) / 1e3 if okz.sum() > 50 else np.nan)
            if phase == "excavate":
                v0_ = mass_p / cfg.paste_density
                sx_ = np.where(np.isfinite(sig[:, 0, 0]), sig[:, 0, 0], 0.0) * v0_
                in_ = a_ & (rr_ < R)
                bal["cut"] += np.histogram(xq_[in_, 0], bal_x, weights=sx_[in_])[0] / dx
                ob_ = valid & (bid != bulkhead)
                bal["other_x"] += np.histogram(pos[ob_, 0], bal_x, weights=F[ob_, 0])[0]
                bh_ = bid == bulkhead
                bal["thrust"] += -float(F[bh_, 0].sum())
                bal["bh_row"] += np.histogram(pos[bh_, 2], bal_z, weights=-F[bh_, 0])[0]
                for k_, (xa_, xb_) in enumerate(((dx, 2 * dx), (2 * dx, 4 * dx))):
                    m_ = in_ & (xq_[:, 0] >= xa_) & (xq_[:, 0] < xb_)
                    bal["paste_row"][k_] += np.histogram(xq_[m_, 2], bal_z, weights=sx_[m_])[0] / (xb_ - xa_)
                bal["frames"] += 1
            stress_log.append((f * dt, p_band[axis_band] / 1e3, sb[axis_band] / 1e3, pb[axis_band] / 1e3, grad / 1e3, g_s / 1e3, p_all / 1e3, int(near.sum()), g_ch / 1e3, g_core / 1e3,
                               ["pressurise", "hold", "excavate", "stop"].index(phase),
                               # vertical balance: the paste's weight in the chamber and the vertical force it puts on each solid (N, down positive)
                               float(mass_p[a_ & (xq_[:, 0] > 0) & (rr_ < R)].sum()) * G,
                               -float(F[bid == shell, 2].sum()), -float(F[bid == bulkhead, 2].sum()), -float(F[bid == piston, 2].sum()), -float(F[bid == cutter, 2].sum()), *g_slab))
            # profile by height in two prisms clear of the shell (R/4 < |y| < R/2, |z - zc| < 0.8 R, bulkhead to the
            # spokes): paste mass and mean stress per bin, summed over the frames of each phase. Fill = mass / (paste
            # density x bin volume); Newton's stress acts per unit of particle volume, so the stress the paste carries per
            # unit of space is the particle stress times the fill.
            pr = in_ch & (np.abs(xq_[:, 1]) > R / 4) & (np.abs(xq_[:, 1]) < R / 2)
            kb = np.floor((xq_[pr, 2] - zc + 0.8 * R) / (1.6 * R / n_prof)).astype(int)
            okp = (kb >= 0) & (kb < n_prof)
            ph_i = ["pressurise", "hold", "excavate", "stop"].index(phase)
            prof[ph_i, 0] += np.bincount(kb[okp], weights=mass_p[pr][okp], minlength=n_prof)
            prof[ph_i, 1] += np.bincount(kb[okp], weights=p_part[pr][okp], minlength=n_prof)
            prof[ph_i, 2] += np.bincount(kb[okp], minlength=n_prof)
            prof[ph_i, 3] += 1.0
            prof_x = x_ch - 0.1
        p_hist.append(float(p_band[axis_band]))
        log.append((f * dt, ["pressurise", "hold", "excavate", "stop"].index(phase), p_band[axis_band] / 1e3, grad / 1e3,
                    rpm, thrust / 1e6, abs(torque) / 1e6, x_face + t / 2 - x_p, removed, p_piston / 1e3, f_cutter_x / 1e6, v_piston * 6e4, grad_band / 1e3))
        t_phase += dt

    log = np.array(log)
    xq = s.particle_q.numpy()[(flags & active) != 0]
    esc_back = xq[:, 0] < -0.02
    esc_front = xq[:, 0] > x_p - t / 2 + 0.02
    esc_side = (np.hypot(xq[:, 1], xq[:, 2] - zc) > R_f + 0.02) & ~esc_back & ~esc_front
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
            # from the net flow after the step (17 Nov 2026): the piston's displacement against the screw's discharge, the
            # discharge counted at the paste's particle density (particles x in-situ volume over the chamber space, as the
            # volume balance counts it). The rate above assumes the chamber was in balance at the speed before the step;
            # with the controller still swinging it was not, and the two step directions came out at 73 % and 129 %
            "rate_net_flow_kPa_per_s": round(k_kpa * (area * v_adv / step["paste_volume_m3"] - screw.discharge(step["rpm_after"]) / (step["n_particles"] * v_particle)), 3),
            "s_to_30_kPa": round(float(after[moved[0], 0] - step["t_s"]), 2) if len(moved) else None,
            "p_axis_end_kPa": round(float(after[-int(cfg.fps):, 2].mean()), 1),
        }
    # screw volume over the whole excavation (17 Nov 2026): the screw speed swings with the pressure controller (period
    # 40-50 s), so a mean over part of the excavation depends on where the window falls. The volume removed, less the
    # change of the paste's elastic volume over the excavation (the balance's mean ln J target times the paste's particle
    # volume), against the volume the piston displaced, does not; it is compared with the paste's fill.
    screw_vol = None
    exa = log[log[:, 1] == 2]
    if len(exa) > 1:
        rem_v = float(exa[-1, 8] - exa[0, 8]) * v_particle
        disp_v = area * float(exa[-1, 7] - exa[0, 7])
        screw_vol = {"removed_m3": round(rem_v, 3), "displaced_m3": round(disp_v, 3), "ratio": round(rem_v / disp_v, 3) if disp_v > 0 else None}
        if vb_log:
            vba = np.array(vb_log)
            v0, v1 = vba[np.argmin(np.abs(vba[:, 0] - exa[0, 0]))], vba[np.argmin(np.abs(vba[:, 0] - exa[-1, 0]))]
            swing = float(v1[1] - v0[1]) * float(v1[3]) * v_particle
            screw_vol.update({"elastic_swing_m3": round(swing, 3), "ratio_less_swing": round((rem_v - swing) / disp_v, 3) if disp_v > 0 else None})
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
        "gradient_bands_hold_excavate_kPa_per_m": [round(float(hold[:, 12].mean()), 2) if len(hold) else None, round(float(ex[:, 12].mean()), 2) if len(ex) else None],
        "screw_rpm_excavate": round(float(ex[:, 4].mean()), 2) if len(ex) else None,
        "screw_rpm_feedforward": round(screw.rpm_for_flow(area * v_adv), 2),
        "bulkhead_thrust_MN_excavate": round(float(ex[:, 5].mean()), 2) if len(ex) else None,
        "p_axis_times_area_MN": round(float(ex[:, 2].mean()) * area / 1e3, 2) if len(ex) else None,
        "cutter_torque_MNm_excavate": round(float(ex[:, 6].mean()), 3) if len(ex) else None,
        "p_piston_hold_excavate_kPa": [round(float(hold[:, 9].mean()), 1) if len(hold) else None, round(float(ex[:, 9].mean()), 1) if len(ex) else None],
        "cutter_axial_MN_hold_excavate": [round(float(hold[:, 10].mean()), 2) if len(hold) else None, round(float(ex[:, 10].mean()), 2) if len(ex) else None],
        "advance_m": round(float(log[-1, 7]), 3),
        "particles_removed": int(removed),
        "screw_volume_excavate": screw_vol,
        "particles_escaped": escaped,
        "volume_balance_repaired": vb_repaired,
        "volume_correction_mismatch_mean_rms_excavate": [round(float(np.mean([r[k] for r in vc_log if r[0]])), 5) for k in (1, 2)] if vc is not None and any(r[0] for r in vc_log) else None,
        "particle_reseals": resealed,
        "substep_guard": {"steps_with_invalid": int(sum(1 for g in guard_log if g[2] > 0)), "particles_reset": sub_repaired,
                          "steps_with_extreme": int(sum(1 for g in guard_log if g[3] > 0)), "fastest_m_s": round(max((g[4] for g in guard_log), default=0.0), 2)} if cfg.substep_guard else None,
        "escaped_back_front_side": [int(esc_back.sum()), int(esc_front.sum()), int(esc_side.sum())],
        "particles_per_m3_start_end": [round(len(pts) / (area * x_face)), round((n_active - escaped) / vol_now)],
        "ms_per_frame": round(float(np.mean(times[5:]) * 1000), 2),
    }
    return res, {"log": log, "q_end": s.particle_q.numpy(), "active": (flags & active) != 0, "x_cutter": x_ch, "zc": zc, "vb": np.array(vb_log), "stress": np.array(stress_log), "balance": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in bal.items()} if cfg.stress_log else None, "sub": np.array(sub_log), "sub_bad": sub_bad, "sub_ext": sub_ext, "vrp": vrp_log, "sub_repaired": sub_repaired, "guard": {"log": guard_log, "events": guard_events, "odd": guard_odd} if cfg.substep_guard else None, "vb_regions": vb_reg_acc, "seal_facets": seal_facets, "seal_fx": {"counts": seal_fx.tolist(), "x_edges": seal_x_edges.tolist(), "x_cutter": x_ch, "x_face": x_face, "sink_hi": sink_hi.tolist()}, "gauges": {"names": [g[0] for g in gauges], "yz": [g[1:] for g in gauges], "sides": list(gauge_sides), "boxes": gauge_box, "zc": zc, "log": gauge_hist} if cfg.gauge_log else None, "contact_rows": {"sums": crow, "frames": cframes, "snap": csnap, "voxel": dx, "zc": zc, "R": R, "y_min": y_min, "edges": edges, "band_z": band_z, "band_area": band_area} if cfg.contact_rows else None,
                 "profile": {"sums": prof, "z_over_R": (np.arange(n_prof) + 0.5) * 1.6 / n_prof - 0.8, "bin_volume_m3": prof_x * (R / 2) * (1.6 * R / n_prof), "paste_density": cfg.paste_density}}


def params(cfg: ChamberConfig) -> dict:
    return {**asdict(cfg), "soil": asdict(paste(cfg))}
