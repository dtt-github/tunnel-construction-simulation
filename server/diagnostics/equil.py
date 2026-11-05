"""WP3 diagnostic: integrated sigma_zz on horizontal sections above the crown against the weight above, in the
plane-strain tunnel (elastic, or clay at yield). Usage: python diagnostics/equil.py <E> <elastic|clay|sand> [vpd]
Result (5 Nov 2026): equilibrium holds within 0.3-3 %; the clay overburden keeps moving down at about 80 mm/s."""
import sys, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import newton.solvers as ns
from tunnelsim_server.scenes import tunnel_2d as t2
from tunnelsim_server import materials as m
E = float(sys.argv[1]); mode = sys.argv[2]  # mode: clay | sand | elastic
vpd = float(sys.argv[3]) if len(sys.argv) > 3 else 10
snap = {}
orig = ns.SolverImplicitMPM.step
count = {"n": 0}
cfg = t2.Tunnel2DConfig(cover=2.0, voxel_per_d=vpd)
marks = {cfg.settle - 1: "settled", cfg.settle + int(0.05 / cfg.rate_over_r * cfg.fps): "5% R", None: "end"}
def step(self, s0, s1, **kw):
    out = orig(self, s0, s1, **kw)
    k = count["n"]; count["n"] += 1
    if k in marks:
        snap[marks[k]] = (s1.particle_q.numpy().copy(), s1.particle_qd.numpy().copy(), s1.mpm.particle_stress.numpy().copy())
    snap["end"] = (s1.particle_q, s1.particle_qd, s1.mpm.particle_stress)
    return out
ns.SolverImplicitMPM.step = step
rho = 14.4e3 / 9.81
if mode == "clay":
    soil = m.undrained_clay("kaolin", rho, 26e3, E, "test")
elif mode == "sand":
    soil = m.drained_sand("sand", rho, 34.0, E, "test")
else:  # strong clay: stays elastic
    soil = m.undrained_clay("strong", rho, 1e9, E, "test")
r, _ = t2.run(cfg, soil)
end = snap["end"]; snap["end"] = (end[0].numpy(), end[1].numpy(), end[2].numpy())
D = cfg.diameter; R = D / 2; zc = cfg.base_below_invert_over_d * D + R; zs = zc + R + cfg.cover * D
h = D / vpd / cfg.ppc; mass = h**3 * rho; g = 9.81
area = 2 * cfg.half_width_over_d * D * cfg.thickness_over_d * D
print(f"mode {mode} E {E:.0e} vpd {vpd}: N_5pctR {r.get('N_5pctR')}  (zc {zc:.2f}, crown {zc+R:.2f}, surface {zs:.2f})")
for name in ("settled", "5% R", "end"):
    q, v, sig = snap[name]
    out = []
    for zsec in (zc + R + 0.25 * cfg.cover * D, zc + R + 0.5 * cfg.cover * D, zc + R + 0.75 * cfg.cover * D):
        band = np.abs(q[:, 2] - zsec) < h  # band 2h thick
        szz_int = (sig[band, 2, 2] * h**3).sum() / (2 * h)  # integral of sigma_zz over the section (N)
        weight = (q[:, 2] > zsec).sum() * mass * g
        vz = v[q[:, 2] > zsec, 2]
        out.append(f"z={zsec:5.2f}: int(szz)/W {szz_int/weight:5.3f}, mean vz above {vz.mean()*1000:6.2f} mm/s")
    print(f"  {name:8s} " + " | ".join(out))
