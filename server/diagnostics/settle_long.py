"""WP3 diagnostic: does the clay come to rest before the ring closes? Surface height and mean |vz| every second.
Usage: python diagnostics/settle_long.py <settle frames> [critical_fraction]
Result (5 Nov 2026): with critical_fraction 0 the clay creeps at about 29 mm/s indefinitely; with 0.8-0.9 it comes to
rest after compacting 13-17 %."""
import sys, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import newton.solvers as ns
import tunnelsim_server.scenes.common as common
common.CRITICAL_FRACTION = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
from tunnelsim_server.scenes import tunnel_2d as t2
from tunnelsim_server import materials as m
settle = int(sys.argv[1])
cfg = t2.Tunnel2DConfig(cover=2.0, voxel_per_d=10, settle=settle)
track = []; cnt = {"n": 0}; z0 = {}
orig = ns.SolverImplicitMPM.step
def step(self, s0, s1, **kw):
    out = orig(self, s0, s1, **kw); cnt["n"] += 1
    if cnt["n"] % 60 == 0 or cnt["n"] == settle:
        q = s1.particle_q.numpy(); v = s1.particle_qd.numpy()
        top = q[:, 2] > np.percentile(q[:, 2], 99)
        track.append((cnt["n"] / 60, float(q[top, 2].mean()), float(np.abs(v[:, 2]).mean() * 1000)))
    return out
ns.SolverImplicitMPM.step = step
soil = m.undrained_clay("kaolin", 14.4e3 / 9.81, 26e3, 1.0e15, "test")
r, a = t2.run(cfg, soil)
for t, ztop, vz in track:
    print(f"  t {t:4.1f} s: surface {ztop:7.3f} m, mean |vz| {vz:6.1f} mm/s" + ("  <- ring starts closing" if abs(t - settle / 60) < 1e-6 else ""))
print("critical_fraction", common.CRITICAL_FRACTION, "settle", settle, "frames: N 2/5/10 %R", r.get("N_2pctR"), r.get("N_5pctR"), r.get("N_10pctR"), "p_settled", r["p_settled_kPa"])
