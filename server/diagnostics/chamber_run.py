"""One chamber run with ChamberConfig fields overridden: chamber_run.py name key=value ...; writes out_box/<name>.json
(result, parameters and the per-frame log: t, phase, axis pressure kPa, gradient kPa/m, screw rpm, ...)."""
import dataclasses
import json
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
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_box")
os.makedirs(d, exist_ok=True)
json.dump({"params": dataclasses.asdict(cfg), "result": res, "log": log.tolist()}, open(os.path.join(d, sys.argv[1] + ".json"), "w"))
