"""Volume drift of a frictionless undrained paste in a closed box around a moving kinematic paddle (Newton implicit MPM, newton#5180).

The box is sealed and the paddle rigid, so the paste's true mean volume strain stays 0; anything else is the solver's.
usage: moving_collider_box.py name [mode=translate|rotate] [v=0.5] [voxel=0.1] [fps=60] [T=3] [cvm=forward|backward]
       [basis=S2] [shape=box|cyl] [scheme=gimp] [it=50] [pre=0.07]
       [tolerance=1e-4] [warmstart_mode=auto] [solver=auto] [transfer_scheme=apic] [cu=5000]
Set NEWTON_PATCHED to a directory holding a patched copy of the newton package to test it; PROJECT=1 calls
project_outside after each step; DUMP=1 adds particle count and mean ln det Fe per 0.1 m slab along x every 0.5 s;
RESID=1 adds the change of ln det Fe beyond dt div v per particle, summed in bins of (x - paddle x, lateral distance). 
VC=<rate> applies scenes/volume_correction.py after each step (VCS=node|cell picks its support); DEVICE=cpu runs on the CPU.
Writes out_box/<name>.json beside this file.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if os.environ.get("NEWTON_PATCHED"):
    sys.path.insert(0, os.environ["NEWTON_PATCHED"])
import numpy as np
import warp as wp

import newton
from tunnelsim_server.scenes import chamber, common

name = sys.argv[1]
a = dict(x.split("=") for x in sys.argv[2:])
mode, shape, cvm = a.get("mode", "translate"), a.get("shape", "box"), a.get("cvm", "forward")
v, dx, fps, T = float(a.get("v", 0.5)), float(a.get("voxel", 0.1)), float(a.get("fps", 60)), float(a.get("T", 3))
common.INTEGRATION_SCHEME = a.get("scheme", "gimp")
if "basis" in a:
    common.SOLVER_OPTIONS["collider_basis"] = a["basis"]
common.SOLVER_OPTIONS["collider_velocity_mode"] = cvm
for k, typ in (("tolerance", float), ("warmstart_mode", str), ("solver", str), ("transfer_scheme", str)):
    if k in a:
        common.SOLVER_OPTIONS[k] = typ(a[k])
wp.init()
if os.environ.get("DEVICE"):
    wp.set_device(os.environ["DEVICE"])
soil = chamber.paste(chamber.ChamberConfig(paste_friction=0.0, paste_cohesion=float(a.get("cu", 5000.0))))  # undrained paste; cu=1e9 makes it an elastic solid
Lx, Ly, Lz, t = 2.0, 1.0, 1.0, 0.3
b = newton.ModelBuilder()
walls = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True, label="walls")
common.add_walls(b, walls, [((-t / 2, Ly / 2, Lz / 2), (t / 2, Ly / 2 + t, Lz / 2 + t)), ((Lx + t / 2, Ly / 2, Lz / 2), (t / 2, Ly / 2 + t, Lz / 2 + t)),
                            ((Lx / 2, -t / 2, Lz / 2), (Lx / 2 + t, t / 2, Lz / 2 + t)), ((Lx / 2, Ly + t / 2, Lz / 2), (Lx / 2 + t, t / 2, Lz / 2 + t)),
                            ((Lx / 2, Ly / 2, -t / 2), (Lx / 2 + t, Ly / 2 + t, t / 2)), ((Lx / 2, Ly / 2, Lz + t / 2), (Lx / 2 + t, Ly / 2 + t, t / 2))])
c0 = np.array([0.5, Ly / 2, Lz / 2])
pad = b.add_body(xform=wp.transform(wp.vec3(*c0), wp.quat_identity()), mass=1.0, is_kinematic=True, label="paddle")
h = dx / 2
pts = common.fill_box((0, 0, 0), (Lx, Ly, Lz), h, seed=0)
rel = pts - c0
if shape == "cyl":  # disc, axis along x
    b.add_shape_cylinder(pad, xform=wp.transform(wp.vec3(0.0), wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), math.pi / 2)), radius=0.3, half_height=0.05)
    inside = (abs(rel[:, 0]) < 0.05) & (np.hypot(rel[:, 1], rel[:, 2]) < 0.3)
elif mode == "translate":  # plate, normal along the motion
    b.add_shape_box(pad, xform=wp.transform_identity(), hx=0.05, hy=0.3, hz=0.3)
    inside = (abs(rel[:, 0]) < 0.05) & (abs(rel[:, 1]) < 0.3) & (abs(rel[:, 2]) < 0.3)
else:  # arm turning about x
    b.add_shape_box(pad, xform=wp.transform(wp.vec3(0.0, 0.0, 0.2), wp.quat_identity()), hx=0.1, hy=0.05, hz=0.2)
    inside = (abs(rel[:, 0]) < 0.1) & (abs(rel[:, 1]) < 0.05) & (abs(rel[:, 2] - 0.2) < 0.2)
cm = b.finalize()
pts = pts[~inside]
pm = common.make_particles(pts, h, soil).finalize()
solver = common.make_solver(pm, cm, dx, int(a.get("it", 50)), {walls: 0.0, pad: 0.0, -1: 0.0})
pm.gravity.zero_()
s, st = pm.state(), cm.state()
s.body_q, s.body_qd, s.body_f = wp.clone(st.body_q), wp.zeros_like(st.body_qd), wp.zeros_like(st.body_f)
# prestress: the paste starts compressed (ln det Fe = -pre), as in a pressurised chamber, so it stays in contact with
# the trailing face of the paddle; without it a gap opening there is physical, not a solver error
pre = float(a.get("pre", 0.07))
fe0 = s.mpm.particle_elastic_strain.numpy()
s.mpm.particle_elastic_strain.assign((fe0 * math.exp(-pre / 3.0)).astype(np.float32))
dt = 1 / fps
# VC=rate: density-coupled volume correction (tunnelsim_server/scenes/volume_correction.py); VCS=node|cell its support
VC = float(os.environ.get("VC", 0))
if VC:
    from tunnelsim_server.scenes.volume_correction import VolumeCorrection

    def solid(p):
        r = p - np.array(q[pad, :3])
        if mode == "translate" and shape == "box":
            return (abs(r[:, 0]) < 0.05) & (abs(r[:, 1]) < 0.3) & (abs(r[:, 2]) < 0.3)
        if shape == "cyl":
            return (abs(r[:, 0]) < 0.05) & (np.hypot(r[:, 1], r[:, 2]) < 0.3)
        c_, s_ = math.cos(ang_now), math.sin(ang_now)  # arm turned about x by ang_now
        ry, rz = c_ * r[:, 1] + s_ * r[:, 2], -s_ * r[:, 1] + c_ * r[:, 2]
        return (abs(r[:, 0]) < 0.1) & (abs(ry) < 0.05) & (abs(rz - 0.2) < 0.2)

    vc = VolumeCorrection(dx, (0, 0, 0), (Lx, Ly, Lz), solid, rate=VC, support=os.environ.get("VCS", "node"))
ang_now = 0.0
q = s.body_q.numpy()
if VC:
    vc.calibrate(s.particle_q.numpy(), s.mpm.particle_elastic_strain.numpy(), np.ones(len(pts), bool), h)
w = v / 0.4  # rotate: tip speed v at r 0.4
out = []
prof = []
RESID = bool(os.environ.get("RESID"))
racc, dacc = np.zeros((5, 20)), np.zeros((5, 20))
kin = np.zeros(len(pts))
ncell, dcell, pcell = np.zeros((20, 16)), np.zeros((20, 16)), np.zeros((20, 16))
every = max(1, round(fps / 10))
for f in range(int(T * fps)):
    tt = (f + 1) * dt
    qd = np.zeros((cm.body_count, 6), np.float32)
    if mode == "translate":
        x = c0[0] + v * tt
        if x > Lx - 0.5:
            x = Lx - 0.5
        else:
            qd[pad, 0] = v
        q[pad, 0] = x
    else:
        ang = w * tt
        ang_now = ang
        q[pad, 3:7] = [math.sin(ang / 2), 0, 0, math.cos(ang / 2)]
        qd[pad, 3] = w
    s.body_q.assign(q)
    s.body_qd.assign(qd)
    if RESID:
        lj0 = np.log(np.linalg.det(s.mpm.particle_elastic_strain.numpy()))
    solver.step(s, s, contacts=None, control=None, dt=dt)
    if RESID:  # change of ln det Fe not explained by the particle's own velocity divergence, binned around the paddle
        res = np.log(np.linalg.det(s.mpm.particle_elastic_strain.numpy())) - lj0
        dv = dt * np.trace(s.mpm.particle_qd_grad.numpy(), axis1=1, axis2=2)
        kin += np.nan_to_num(dv)
        xp = s.particle_q.numpy()
        i = np.clip(((xp[:, 0] - q[pad, 0] + 1.0) / 0.1).astype(int), 0, 19)
        j = np.clip((np.maximum(abs(xp[:, 1] - Ly / 2), abs(xp[:, 2] - Lz / 2)) / 0.1).astype(int), 0, 4)
        np.add.at(racc, (j, i), np.nan_to_num(res - dv) / len(xp))
        np.add.at(dacc, (j, i), np.nan_to_num(dv) / len(xp))
        m = (abs(xp[:, 2] - Lz / 2) < 0.1) & (abs(xp[:, 0] - q[pad, 0]) < 0.4) & (0.3 < tt < 1.7)  # mid slab, y against x
        ii, jj = ((xp[m, 0] - q[pad, 0] + 0.4) / 0.05).astype(int), np.clip((xp[m, 1] / 0.05).astype(int), 0, 19)
        np.add.at(ncell, (jj, ii), 1.0)
        np.add.at(dcell, (jj, ii), dv[m] / dt)
        np.add.at(pcell, (jj, ii), lj0[m])
    if VC:
        s.mpm.particle_elastic_strain.assign(vc.apply(s.particle_q.numpy(), s.mpm.particle_elastic_strain.numpy(), np.ones(len(pts), bool), h).astype(np.float32))
    if os.environ.get("PROJECT"):
        solver.project_outside(s, s, dt)
    if f % every == every - 1:
        lj = np.log(np.linalg.det(s.mpm.particle_elastic_strain.numpy()))
        ok = np.isfinite(lj)
        tr = np.trace(common.particle_stress(s), axis1=1, axis2=2) / 3
        out.append((tt, float(lj[ok].mean()), float(tr.mean()) / 1e3, int((~ok).sum())))
        if os.environ.get("DUMP") and (f + 1) % round(fps / 2) == 0:  # every 0.5 s: slab profile along x
            xp = s.particle_q.numpy()
            k = np.clip((xp[:, 0] / 0.1).astype(int), 0, int(Lx / 0.1) - 1)
            cnt = np.bincount(k, minlength=int(Lx / 0.1))
            mlj = np.bincount(k, weights=np.where(ok, lj, 0.0), minlength=int(Lx / 0.1)) / np.maximum(cnt, 1)
            prof.append((tt, float(q[pad, 0]), cnt.tolist(), mlj.tolist(), float(xp[:, 0].min()), float(xp[:, 0].max()),
                         float(xp[:, 1].min()), float(xp[:, 1].max())))
o = np.array(out)
if RESID:
    np.set_printoptions(linewidth=250, suppress=True)
    print("residual (1e-3 of mean ln det Fe), rows lateral 0-0.5, cols x - paddle -1..1; total", round(racc.sum() * 1e3, 2), "div total", round(dacc.sum() * 1e3, 2))
    print(np.round(racc * 1e3, 1))
    print("div"); print(np.round(dacc * 1e3, 1))
    nst = ((0.3 < (np.arange(int(T * fps)) + 1) * dt) & ((np.arange(int(T * fps)) + 1) * dt < 1.7)).sum()
    print("mid slab |z-0.5|<0.1, rows y 0..1, cols x - paddle -0.4..0.4 (0.05 bins): particles per bin (uniform = 8)"); print(np.round(ncell / nst, 1))
    print("mean div v 1/s"); print(np.round(dcell / np.maximum(ncell, 1), 2))
    print("mean ln det Fe 1e-3"); print(np.round(1e3 * pcell / np.maximum(ncell, 1), 0))
if RESID:  # does the particles' own accumulated div v match how dense they actually got?
    xp = s.particle_q.numpy()
    c = np.clip((xp / dx).astype(int), 0, [int(Lx / dx) - 1, int(Ly / dx) - 1, int(Lz / dx) - 1])
    key = (c[:, 0] * 100 + c[:, 1]) * 100 + c[:, 2]
    u, inv, n = np.unique(key, return_inverse=True, return_counts=True)
    dens = np.log(8.0 / n[inv])
    lje = np.log(np.linalg.det(s.mpm.particle_elastic_strain.numpy()))
    print("per particle: mean ln(8/n_cell)", round(dens.mean(), 4), "mean accumulated div", round(kin.mean(), 4), "mean ln det Fe", round(np.nanmean(lje), 4))
    for lo, hi in ((0, 5), (5, 7), (7, 9), (9, 12), (12, 20), (20, 99)):
        m = (n[inv] >= lo) & (n[inv] < hi)
        print(f"  cells with {lo}-{hi} particles: {m.mean():.3f} of particles, accumulated div {kin[m].mean():+.3f}, ln det Fe {np.nanmean(lje[m]):+.3f}, ln(8/n) {dens[m].mean():+.3f}")
if VC:
    print("volume correction", vc.stats)
print(name, "mean ln det Fe at start, 1/3, 2/3, end:", np.round(o[[0, len(o) // 3, 2 * len(o) // 3, -1], 1], 5), "mean stress trace/3 kPa end", round(o[-1, 2], 2), "bad", int(o[:, 3].max()))
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_box")
os.makedirs(d, exist_ok=True)
json.dump({"args": a, "particles": len(pts), "series": o.tolist(), "profile": prof, "resid": racc.tolist(), "div": dacc.tolist()}, open(os.path.join(d, name + ".json"), "w"))
