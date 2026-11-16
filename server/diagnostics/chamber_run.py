"""One chamber run with ChamberConfig fields overridden: chamber_run.py name key=value ...; writes out_box/<name>.json
(result, parameters and the per-frame log: t, phase, axis pressure kPa, gradient kPa/m, screw rpm, ...)."""
import dataclasses
import json

import numpy as np
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if os.environ.get("NEWTON_PATCHED"):
    sys.path.insert(0, os.environ["NEWTON_PATCHED"])
from tunnelsim_server.scenes import chamber, common

# diagnosis switches for Newton's solver (15 Nov 2026): TS_SOLVER_OPTIONS="name=value,..." sets SolverImplicitMPM.Config
# fields (strings, or numbers where they parse); TS_LEFTOVER=1 keeps the strain the iterative solve leaves unexplained
# in the elastic strain (Newton's compile-time constant _INCLUDE_LEFTOVER_STRAIN, off as shipped).
for kv in filter(None, os.environ.get("TS_SOLVER_OPTIONS", "").split(",")):
    k_, v_ = kv.split("=")
    try:
        v_ = int(v_)
    except ValueError:
        try:
            v_ = float(v_)
        except ValueError:
            pass
    common.SOLVER_OPTIONS[k_] = tuple(v_.split("+")) if isinstance(v_, str) and "+" in v_ else v_
if os.environ.get("TS_LEFTOVER"):
    import warp as wp
    from newton._src.solvers.implicit_mpm import rheology_solver_kernels as _rk

    _rk._INCLUDE_LEFTOVER_STRAIN = wp.constant(True)

types = {f.name: f.type for f in dataclasses.fields(chamber.ChamberConfig)}
cast = {"float": float, "int": int, "bool": lambda v: v in ("1", "True", "true"), "str": str}
kw = {k: cast[str(types[k])](v) for k, v in (x.split("=") for x in sys.argv[2:])}
cfg = chamber.ChamberConfig(**kw)
res, extra = chamber.run(cfg)
print(json.dumps(res, indent=1))
log = extra["log"]
for ph, nm in enumerate(["pressurise", "hold", "excavate", "stop"]):
    r = log[log[:, 1] == ph]
    if len(r):
        print(f"{nm:10s} p axis kPa every {max(1, len(r) // 12)} frames:", " ".join(f"{v:.0f}" for v in r[:: max(1, len(r) // 12), 2]))
st = extra.get("stress")
if st is not None and len(st) and st.shape[1] >= 11:  # gradients kPa/m by phase: bulkhead contact, paste stress at the bulkhead, whole chamber, core
    for ph, nm in enumerate(["pressurise", "hold", "excavate", "stop"]):
        r = st[st[:, 10] == ph]
        r = r[len(r) // 2:]
        if len(r):
            print(f"gradient {nm:10s} contact {r[:, 4].mean():5.2f} (sd {r[:, 4].std():.2f})  bulkhead stress {np.nanmean(r[:, 5]):5.2f}  chamber {np.nanmean(r[:, 8]):5.2f} (sd {np.nanstd(r[:, 8]):.2f})  core {np.nanmean(r[:, 9]):5.2f} (sd {np.nanstd(r[:, 9]):.2f})")
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_box")
os.makedirs(d, exist_ok=True)
if st is not None and len(st) and st.shape[1] >= 16:  # vertical balance, kN down: paste weight, and the paste's vertical force on each solid
    for ph, nm in enumerate(["pressurise", "hold", "excavate", "stop"]):
        r = st[st[:, 10] == ph]
        r = r[len(r) // 2:]
        if len(r):
            print(f"vertical {nm:10s} weight {r[:, 11].mean() / 1e3:6.1f}  shell {r[:, 12].mean() / 1e3:6.1f}  bulkhead {r[:, 13].mean() / 1e3:6.1f}  piston {r[:, 14].mean() / 1e3:6.1f}  cutter {r[:, 15].mean() / 1e3:6.1f}")
pf = extra.get("profile")
prof_out = None
if pf is not None and pf["sums"][:, 3].max() > 0:  # by height: fill, particle stress, and stress per unit of space (= particle stress x fill)
    prof_out = {"z_over_R": pf["z_over_R"].tolist()}
    dz = (pf["z_over_R"][1] - pf["z_over_R"][0]) * cfg.diameter / 2
    for ph, nm in enumerate(["pressurise", "hold", "excavate", "stop"]):
        m, ps, n, fr = pf["sums"][ph]
        if fr[0] == 0:
            continue
        fill = m / fr / (pf["paste_density"] * pf["bin_volume_m3"])
        pk = ps / np.maximum(n, 1) / 1e3
        z = pf["z_over_R"] * cfg.diameter / 2
        prof_out[nm] = {"fill": fill.tolist(), "p_particle_kPa": pk.tolist(), "p_space_kPa": (pk * fill).tolist()}
        print(f"profile {nm:10s} gradient kPa/m: particle stress {-np.polyfit(z, pk, 1)[0]:5.2f}   stress x fill {-np.polyfit(z, pk * fill, 1)[0]:5.2f}   fill top to bottom", " ".join(f"{v:.3f}" for v in fill[::-1]))
        print(f"        {nm:10s} particle stress kPa top to bottom", " ".join(f"{v:.0f}" for v in pk[::-1]))
vb = extra.get("vb")
if vb is not None and len(vb) and vb.shape[1] >= 12:  # volume balance by frame: t, degenerate particles, regions, emptiest region, largest correction
    print("balance: t s, degenerate, regions, least count/ref, largest |shift| ln J, its region, count, ref count")
    for r in vb[:: max(1, len(vb) // 40)]:
        print(f"balance {r[0]:6.2f} {int(r[5]):7d} {int(r[6]):4d} {r[7]:6.3f} {r[8]:9.4f} {int(r[9]):5d} {int(r[10]):6d} {int(r[11]):6d}")
sub = extra.get("sub")
if sub is not None and len(sub):
    print("substeps: frames with an invalid particle", int((sub[:, 2] + sub[:, 3] > 0).sum()), "repaired", extra.get("sub_repaired"))
    for e in extra.get("sub_bad", [])[:10]:
        print("sub_bad", e)
    big = np.argsort(sub[:, 4])[-5:]
    print("sub fastest particle (t, substep, m/s, 99.9 pct):", [(round(float(sub[i, 0]), 2), int(sub[i, 1]), round(float(sub[i, 4]), 2), round(float(sub[i, 5]), 3)) for i in big])
    print("sub det range min/max:", round(float(np.nanmin(sub[:, 6])), 4), round(float(np.nanmax(sub[:, 7])), 4))
cr = extra.get("contact_rows")
if cr is not None:
    cr = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in cr.items()}
json.dump({"contact_rows": cr, "vrp": extra.get("vrp"), "sub_ext": extra.get("sub_ext"), "sub": np.nan_to_num(sub, nan=-1.0, posinf=1e30, neginf=-1e30).tolist() if sub is not None and len(sub) else None, "vb": np.nan_to_num(vb, nan=-1.0, posinf=1e30, neginf=-1e30).tolist() if vb is not None and len(vb) else None, "profile": prof_out, "params": dataclasses.asdict(cfg), "result": res, "log": log.tolist(), "stress": st.tolist() if st is not None else None}, open(os.path.join(d, sys.argv[1] + ".json"), "w"))
