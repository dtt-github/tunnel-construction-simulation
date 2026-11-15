"""WP3 diagnostic: one heading under stepped load control (as `runner.py face_sand --control stepped`), with options the
runner does not expose: friction of the shield tube and face plate, the size of the soil box, and a clay other than
Kimura & Mair's kaolin.

usage: heading_run.py name key=value ...
  FaceSandConfig fields (cover=3.0 diameter=4.5 steel_friction=0 half_width_over_d=3 front_over_d=4 hold_s=15 step_kpa=5 ...)
  clay: gamma=<kN/m3> cu=<kPa> clay_name=<text> clay_source=<text>   (default: Kimura & Mair's kaolin)
"""
import dataclasses, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tunnelsim_server.materials import undrained_clay
from tunnelsim_server.runner import FACE_SOILS
from tunnelsim_server.scenes import face_sand

name, kv = sys.argv[1], dict(a.split("=", 1) for a in sys.argv[2:])
soil = FACE_SOILS["kaolin"]
if "cu" in kv:
    soil = undrained_clay(kv.pop("clay_name", "clay"), float(kv.pop("gamma")) * 1e3 / 9.81, float(kv.pop("cu")) * 1e3, 1.0e15, kv.pop("clay_source", "see the run's note"))
types = {f.name: f.type for f in dataclasses.fields(face_sand.FaceSandConfig)}
cfg = face_sand.FaceSandConfig(control="stepped", **{k: (int(v) if types[k] == "int" else v if types[k] == "str" else float(v)) for k, v in kv.items()})
res, _ = face_sand.run(cfg, soil)
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_box")
os.makedirs(d, exist_ok=True)
json.dump({"params": face_sand.params(cfg, soil), "result": res}, open(os.path.join(d, name + ".json"), "w"), indent=1)
sz, cu = res["sigma_z_axis_kPa"], soil.cohesion / 1e3
pc = res["p_collapse_kPa"]
print(name, "sigma_z", sz, "p_collapse", pc, "N", round((sz - pc) / cu, 2) if pc is not None else None, "last at rest", res["p_last_at_rest_kPa"],
      "not at rest", res["p_not_at_rest_kPa"], "face/D", res["face_displacement_over_D"], "particles", res["particles"])
for s in res["steps"]:
    if s["face_over_D"] > 0.02 or s is res["steps"][-1]:
        print("  ", s["target_kPa"], s["support_kPa"], s["face_over_D"], s["speed_D_per_s"], s["at_rest"])
