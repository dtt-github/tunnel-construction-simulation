"""WP3 diagnostic: clay leaking between the ring segments into the plane-strain tunnel.
Usage: python diagnostics/ringleak.py <n_seg> <vpd>. Result (5 Nov 2026): about 0.3 % of particles by the end."""
import sys, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import newton.solvers as ns
from tunnelsim_server.scenes import tunnel_2d as t2
from tunnelsim_server import materials as m
nseg = int(sys.argv[1]); vpd = float(sys.argv[2])
snaps = {}; cnt = {"n": 0}
orig = ns.SolverImplicitMPM.step
cfg = t2.Tunnel2DConfig(cover=2.0, voxel_per_d=vpd, n_seg=nseg)
def step(self, s0, s1, **kw):
    out = orig(self, s0, s1, **kw); cnt["n"] += 1
    if cnt["n"] in (1, cfg.settle, cfg.settle + 120): snaps[cnt["n"]] = s1.particle_q.numpy().copy()
    snaps["last"] = s1.particle_q
    return out
ns.SolverImplicitMPM.step = step
soil = m.undrained_clay("kaolin", 14.4e3 / 9.81, 26e3, 1.0e15, "test")
r, a = t2.run(cfg, soil)
snaps["last"] = snaps["last"].numpy()
D = cfg.diameter; R = D / 2; zc = cfg.base_below_invert_over_d * D + R
for k, q in snaps.items():
    rr = np.hypot(q[:, 0], q[:, 2] - zc)
    print(f"  step {k}: particles inside r < 0.9 R: {(rr < 0.9 * R).sum()}, inside r < 0.5 R: {(rr < 0.5 * R).sum()} of {len(q)}")
print("n_seg", nseg, "vpd", vpd, "N_5pctR", r.get("N_5pctR"), "settled", r["p_settled_kPa"])
