"""Regenerate models/test-vectors/*.json from the Python reference implementation.

Run: uv run --project models/py python models/py/make_vectors.py
The JS tests (node --test models/js/test) must reproduce these values to 1e-9 relative.
"""
import json
import pathlib
from dataclasses import asdict

from tunnelsim_models import Cutter, cutter_forces, gaussian_trough, hoek_brown, tbm_performance

OUT = pathlib.Path(__file__).resolve().parents[1] / "test-vectors"


def write(name, cases):
    OUT.mkdir(exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(cases, indent=1) + "\n")


hb = []
for gsi, mi, sci, d, ei in [(50, 10, 100, 0, 30000), (75, 25, 180, 0, 60000), (30, 7, 40, 0.5, 8000), (90, 17, 250, 0.8, 70000)]:
    hb.append({"in": {"gsi": gsi, "mi": mi, "sigma_ci": sci, "d": d, "e_i": ei}, "out": asdict(hoek_brown(gsi, mi, sci, d, ei))})
write("hoek_brown", hb)

csm = []
for p, ucs, bts in [(2, 80, 6), (5, 150, 10), (8, 200, 12), (12, 50, 4)]:
    csm.append({"in": {"penetration_mm": p, "ucs_mpa": ucs, "bts_mpa": bts, "cutter": asdict(Cutter())}, "out": asdict(cutter_forces(p, ucs, bts))})
perf = []
for thrust, rpm, n, d, ucs, bts, tmax in [(12000, 6, 50, 7.0, 150, 10, None), (18000, 5, 70, 9.5, 220, 14, 8000), (6000, 8, 40, 5.5, 60, 5, 1500)]:
    perf.append({"in": {"thrust_kn": thrust, "rpm": rpm, "n_cutters": n, "head_diameter_m": d, "ucs_mpa": ucs, "bts_mpa": bts, "max_torque_knm": tmax},
                 "out": asdict(tbm_performance(thrust, rpm, n, d, ucs, bts, max_torque_knm=tmax))})
write("csm", {"cutter_forces": csm, "tbm_performance": perf})

st = []
for dia, z0, vl, k in [(6.0, 20.0, 0.01, 0.5), (12.0, 25.0, 0.005, 0.5), (4.0, 10.0, 0.02, 0.35)]:
    t = gaussian_trough(dia, z0, vl, k)
    xs = [0.0, 5.0, t.i, 2 * t.i]
    st.append({
        "in": {"diameter_m": dia, "axis_depth_m": z0, "volume_loss": vl, "k": k},
        "out": {"i": t.i, "volume_m3_per_m": t.volume_m3_per_m, "s_max": t.s_max,
                "samples": [{"x": x, "s": t.settlement(x), "u": t.horizontal(x), "s3d_at_face": t.settlement_3d(x, 0.0)} for x in xs]},
    })
write("settlement", st)
print("wrote", sorted(p.name for p in OUT.glob("*.json")))
