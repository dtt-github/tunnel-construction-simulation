"""WP3 diagnostic: does friction on the shield tube hold the clay that the face has pushed into it?

Stepped load control on the Kimura & Mair heading (as `runner.py face_sand --control stepped`), with the friction of the
shield tube and face plate as an argument. With friction, a plug of clay of length L inside the tube can carry up to
4 cu L / D of support by shear on the tube wall; without it, the face should keep moving once it fails.

usage: heading_friction.py name cover diameter steel_friction [hold_s] [unlined_over_d] [half_width_over_d] [front_over_d]
"""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tunnelsim_server.runner import FACE_SOILS
from tunnelsim_server.scenes import face_sand

name, cover, diameter, mu = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
hold = float(sys.argv[5]) if len(sys.argv) > 5 else 15.0
unlined = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
half_w = float(sys.argv[7]) if len(sys.argv) > 7 else 1.5
front = float(sys.argv[8]) if len(sys.argv) > 8 else 2.5
soil = FACE_SOILS["kaolin"]
cfg = face_sand.FaceSandConfig(diameter=diameter, cover=cover, control="stepped", hold_s=hold, steel_friction=mu, unlined_over_d=unlined, half_width_over_d=half_w, front_over_d=front)
res, _ = face_sand.run(cfg, soil)
d = os.path.join(os.path.dirname(__file__), "out_box")
os.makedirs(d, exist_ok=True)
json.dump({"params": face_sand.params(cfg, soil), "result": res}, open(os.path.join(d, name + ".json"), "w"), indent=1)
sz, cu = res["sigma_z_axis_kPa"], soil.cohesion / 1e3
print(name, "p_collapse", res["p_collapse_kPa"], "N", round((sz - res["p_collapse_kPa"]) / cu, 2), "last at rest", res["p_last_at_rest_kPa"], "not at rest", res["p_not_at_rest_kPa"], "face/D", res["face_displacement_over_D"])
for s in res["steps"]:
    if s["face_over_D"] > 0.02:
        print("  ", s["target_kPa"], s["support_kPa"], s["face_over_D"], s["speed_D_per_s"], s["at_rest"])
