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
from tunnelsim_server.scenes import chamber

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
json.dump({"params": dataclasses.asdict(cfg), "result": res, "log": log.tolist(), "stress": st.tolist() if st is not None else None}, open(os.path.join(d, sys.argv[1] + ".json"), "w"))
