"""WP3 diagnostic: weightless plane-strain benchmark (near-weightless clay under a heavy fluid surcharge).
Usage: python diagnostics/weightless.py <C/D> <vpd> <surcharge kPa> <settle frames> [E]
Result (5 Nov 2026): not usable: the fluid is about 900x denser than the clay and sinks through it (11 m/s)."""
import sys, math, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import newton.solvers as ns
from tunnelsim_server.scenes import tunnel_2d as t2
from tunnelsim_server import materials as m
cd, vpd, qs, settle = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
E = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0e15
snap = {}; cnt = {"n": 0}
orig = ns.SolverImplicitMPM.step
def step(self, s0, s1, **kw):
    out = orig(self, s0, s1, **kw); cnt["n"] += 1
    if cnt["n"] == settle: snap["q"] = s1.particle_q.numpy().copy(); snap["v"] = s1.particle_qd.numpy().copy()
    return out
ns.SolverImplicitMPM.step = step
cu = 26e3
soil = m.undrained_clay("weightless clay", 10.0, cu, E, "test")
cfg = t2.Tunnel2DConfig(cover=cd, voxel_per_d=vpd, surcharge_kpa=qs, settle=settle)
r, a = t2.run(cfg, soil)
log = a["log"]
print(f"C/D {cd} vpd {vpd} q {qs} settle {settle} E {E:.0e}: ring p at settle {r['p_settled_kPa']} kPa (trace at 0.5,1,2,3 s: " +
      ", ".join(f"{log[min(int(t*60), len(log)-1),1]/1e3:.0f}" for t in (0.5, 1, 2, 3)) + f") | N 2/5/10 %R {r.get('N_2pctR')} {r.get('N_5pctR')} {r.get('N_10pctR')} | LB {2*math.log(2*cd+1):.2f}")
v = snap["v"]; print("  max speed at end of settling", round(float(np.linalg.norm(v, axis=1).max()), 3), "m/s")
