"""WP0b diagnostic: does the soil pile up against a fixed tunnel lining? The plane-strain slab of tunnel_2d (C/D 2,
D/10, kaolin) held for 4 s with the lining still. Lining: the 24-segment ring of tunnel_2d, or one solid cylinder.
Reports the mean |v| at 2 and 4 s, the surface drop, and particle counts in shells around the lining.
Usage: python diagnostics/ringpile.py <segments|cylinder> <clay|stiff|elastic> [lining friction] [vpd]
  clay: cu 26 kPa (Kimura), rigid; clayE: cu 26 kPa, E 13 MPa (500 cu); stiff: cu 2600 kPa (never yields);
  elastic: cu 2600 kPa, E 50 MPa. Environment ITERS sets the solver iterations (50); OPTS sets solver options, e.g.
  OPTS=velocity_basis=B2,strain_basis=P1d."""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import warp as wp  # noqa: E402

import newton  # noqa: E402
from tunnelsim_server import materials as m  # noqa: E402
import tunnelsim_server.scenes.common as common  # noqa: E402
from tunnelsim_server.scenes.common import add_walls, fill_box, make_particles, make_solver  # noqa: E402

lining, kind = sys.argv[1], sys.argv[2]
fric = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
vpd = float(sys.argv[4]) if len(sys.argv) > 4 else 10.0
import os  # noqa: E402
iters = int(os.environ.get("ITERS", 50))
opts = dict(kv.split("=") for kv in os.environ.get("OPTS", "").split(",") if kv)
common.SOLVER_OPTIONS.update(opts)
cu, E = {"clay": (26e3, 1e15), "clayE": (26e3, 13e6), "stiff": (2.6e6, 1e15), "elastic": (2.6e6, 5e7)}[kind]
soil = m.undrained_clay(kind, 14.4e3 / 9.81, cu, E, "test")
D, R, cover = 4.5, 2.25, 2.0
dx = D / vpd
T, hw = 0.4 * D, 3.0 * D
zc = 1.5 * D + R
zs = zc + R + cover * D
t = max(0.05 * D, dx)
wp.init()
b = newton.ModelBuilder()
fixed = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
w = 0.5 * D
add_walls(b, fixed, [((-hw - w, T / 2, zs / 2), (w, T, zs)), ((hw + w, T / 2, zs / 2), (w, T, zs)),
                     ((0.0, -w, zs / 2), (hw + 2 * w, w, zs)), ((0.0, T + w, zs / 2), (hw + 2 * w, w, zs))])
b.add_ground_plane()
ring = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
if lining == "cylinder":
    b.add_shape_cylinder(ring, xform=wp.transform(wp.vec3(0.0, T / 2, zc), wp.quat_from_axis_angle(wp.vec3(1.0, 0.0, 0.0), math.pi / 2)),
                         radius=R, half_height=T / 2 + 0.1 * D)
else:
    n_seg = 24
    for k in range(n_seg):
        th = 2 * math.pi * (k + 0.5) / n_seg
        c = np.array([math.cos(th), 0.0, math.sin(th)]) * (R - t / 2) + np.array([0.0, T / 2, zc])
        q = wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), -th)
        b.add_shape_box(ring, xform=wp.transform(wp.vec3(*c), q), hx=t / 2, hy=T / 2 + 0.1 * D, hz=1.04 * R * math.tan(math.pi / n_seg))
cm = b.finalize()
h = dx / 2
pts = fill_box((-hw, 0.0, 0.0), (hw, T, zs), h, 0)
pts = pts[np.hypot(pts[:, 0], pts[:, 2] - zc) > R + 0.5 * h]
pm = make_particles(pts, h, soil).finalize()
solver = make_solver(pm, cm, dx, iters, {fixed: 0.0, -1: 0.5, ring: fric})
st = cm.state()
s = pm.state()
s.body_q, s.body_qd, s.body_f = wp.clone(st.body_q), wp.zeros_like(st.body_qd), wp.zeros_like(st.body_f)
top0 = float(np.percentile(pts[:, 2], 99.5))
out = []
for f in range(1, 241):
    solver.step(s, s, contacts=None, control=None, dt=1 / 60)
    if f in (120, 240):
        q, v = s.particle_q.numpy(), s.particle_qd.numpy()
        out.append(f"t {f / 60:.0f} s: mean |v| {np.linalg.norm(v, axis=1).mean() * 1e3:5.1f} mm/s, drop {top0 - np.percentile(q[:, 2], 99.5):.3f} m")
r0 = np.hypot(pts[:, 0], pts[:, 2] - zc)
r1 = np.hypot(q[:, 0], q[:, 2] - zc)
shells = " ".join(f"{lo:.2f}-{hi:.2f}: {((r0 >= lo) & (r0 < hi)).sum()}->{((r1 >= lo) & (r1 < hi)).sum()}"
                  for lo, hi in ((0, R), (R, R + h), (R + h, R + 2 * h), (R + 2 * h, R + 4 * h), (R + 4 * h, R + 8 * h)))
print(f"{lining} {kind} friction {fric} D/{vpd:g} iters {iters} {opts}: " + " | ".join(out) + f"\n  shells r (m): {shells}")
outside = (q[:, 1] < -0.01) | (q[:, 1] > T + 0.01) | (np.abs(q[:, 0]) > hw + 0.01) | (q[:, 2] < -0.01)
print(f"  outside the slab: {outside.sum()} of {len(q)}; y range {q[:, 1].min():.2f}..{q[:, 1].max():.2f} (slab 0..{T:.2f})")
zb = np.linspace(0, zs, 10)
c0, _ = np.histogram(pts[:, 2], zb)
c1, _ = np.histogram(q[~outside, 2], zb)
print("  density ratio by height (bottom->top): " + " ".join(f"{a / b:.3f}" for a, b in zip(c1, c0)))
