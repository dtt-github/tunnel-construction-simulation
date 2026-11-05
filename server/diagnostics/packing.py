"""WP0b diagnostic: does a laterally confined soil column come to rest without compacting? Clay (cu 26 kPa) or sand
column 4 x 1 x 10 m between frictionless walls; surface drop and mean |vz| after 1 and 3 s.
Usage: python diagnostics/packing.py <clay|sand> <ppc> <jitter> <critical_fraction> [voxel]"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import warp as wp  # noqa: E402

import newton  # noqa: E402
import tunnelsim_server.scenes.common as common  # noqa: E402
from tunnelsim_server import materials as m  # noqa: E402

kind, ppc, jit, cf = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
dx = float(sys.argv[5]) if len(sys.argv) > 5 else 0.25
import os  # noqa: E402
common.CRITICAL_FRACTION = cf
common.RADIUS = float(os.environ.get("RADIUS", 0.5))
iters = int(os.environ.get("ITERS", 50))
soil = m.undrained_clay("clay", 1600.0, 26e3, 1.0e15, "test") if kind == "clay" else m.drained_sand("sand", 1600.0, 34.0, 1.0e15, "test")
L, W, H = 4.0, 1.0, 10.0
wp.init()
b = newton.ModelBuilder()
body = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
t = 0.5
common.add_walls(b, body, [((-t, W / 2, H / 2), (t, W, H)), ((L + t, W / 2, H / 2), (t, W, H)),
                           ((L / 2, -t, H / 2), (L, t, H)), ((L / 2, W + t, H / 2), (L, t, H))])
b.add_ground_plane()
cm = b.finalize()
h = dx / ppc
pts = common.fill_box((0, 0, 0), (L, W, H), h, 0, jitter=jit)
pm = common.make_particles(pts, h, soil).finalize()
solver = common.make_solver(pm, cm, dx, iters, {body: 0.0, -1: 0.5})
st = cm.state()
s = pm.state()
s.body_q, s.body_qd, s.body_f = wp.clone(st.body_q), wp.zeros_like(st.body_qd), wp.zeros_like(st.body_f)
top0 = float(np.percentile(pts[:, 2], 99.5))
out = []
for f in range(1, 181):
    solver.step(s, s, contacts=None, control=None, dt=1 / 60)
    if f in (60, 180):
        q, v = s.particle_q.numpy(), s.particle_qd.numpy()
        mid = (pts[:, 2] > 0.6 * H) & (pts[:, 2] < 0.8 * H)
        out.append(f"t {f / 60:.0f} s: 0.7H sinks {(pts[mid, 2] - q[mid, 2]).mean() / H * 100:5.2f} % H, drop {(top0 - np.percentile(q[:, 2], 99.5)) / H * 100:5.2f} % H, mean |vz| {np.abs(v[:, 2]).mean() * 1000:6.2f} mm/s")
q = s.particle_q.numpy()
bins = np.arange(0, H + 1e-6, 1.0)
c0, _ = np.histogram(pts[:, 2], bins)
c1, _ = np.histogram(q[:, 2], bins)
xb = np.linspace(0, L, 9)
m0, _, _ = np.histogram2d(pts[:, 0], pts[:, 2], [xb, bins])
m1, _, _ = np.histogram2d(q[:, 0], q[:, 2], [xb, bins])
if "--map" in sys.argv:
    print("density ratio, rows z (top->bottom), columns x 0.5 m:")
    for k in range(len(bins) - 2, -1, -1):
        print("  " + " ".join(f"{a / b:5.2f}" for a, b in zip(m1[:, k], m0[:, k])))
print("density ratio per metre (bottom->top):", " ".join(f"{a / b:.3f}" for a, b in zip(c1, c0)))
print(f"{kind} ppc {ppc} jitter {jit} cf {cf} voxel {dx} radius {common.RADIUS} iters {iters}: " + " | ".join(out) + f" | {len(pts)} particles")
