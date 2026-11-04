"""Regenerate models/test-vectors/*.json from the Python reference implementation.

Run: uv run --project models/py python models/py/make_vectors.py
The JS tests (node --test models/js/test) must reproduce these values to 1e-9 relative.
"""
import json
import pathlib
from dataclasses import asdict

from tunnelsim_models import Cutter, daub_window, silo_stress, wedge_silo, cutter_forces, gaussian_trough, hoek_brown, preset_trough, tbm_performance, twin_troughs

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

def trough_out(t, xs, ys):
    return {"i": t.i, "volume_m3_per_m": t.volume_m3_per_m, "s_max": t.s_max, "fraction_at_face": t.fraction_at_face,
            "samples": [{"x": x, "s": t.settlement(x), "u": t.horizontal(x), "slope": t.slope(x)} for x in xs],
            "longitudinal": [{"y": y, "f": t.longitudinal_fraction(y), "s3d": t.settlement_3d(xs[1], y)} for y in ys]}


ys = [-20.0, -5.0, 0.0, 4.0, 9.0, 30.0]
asym = []
for dia, z0, vl, k, kl, kr, comps in [
    (6.0, 20.0, 0.01, 0.5, 0.7, 0.5, None),
    (5.0, 19.5, 0.006, 0.5, None, 0.35, [(0.2, 0.0), (0.3, 4.0), (0.5, 8.0)]),
    (8.0, 15.0, 0.012, 0.4, 0.45, 0.6, [(0.5, 0.0), (0.5, 6.0)]),
]:
    t = gaussian_trough(dia, z0, vl, k, k_left=kl, k_right=kr, components=comps)
    asym.append({"in": {"diameter_m": dia, "axis_depth_m": z0, "volume_loss": vl, "k": k, "k_left": kl, "k_right": kr, "components": comps},
                 "out": trough_out(t, [-2 * t.i, -5.0, 0.0, 5.0, t.i, 2 * t.i], ys)})

presets = []
for method, dia, z0, length in [("open_face_stiff_clay", 4.85, 20.0, None), ("closed_face_clay", 6.0, 18.0, 9.0), ("closed_face_sand", 10.0, 25.0, 12.0), ("scl_stiff_clay", 7.0, 22.0, None)]:
    t = preset_trough(method, dia, z0, shield_length_m=length)
    presets.append({"in": {"method": method, "diameter_m": dia, "axis_depth_m": z0, "shield_length_m": length},
                    "out": trough_out(t, [0.0, 5.0, t.i], ys)})

twins = []
for dia, z0, sp, vl1, vl2, k, f, kin in [(5.0, 19.5, 26.0, 0.006, None, 0.5, 1.0, None), (5.0, 19.5, 26.0, 0.006, 0.006, 0.5, 1.3, 0.8), (6.0, 20.0, -15.0, 0.01, 0.008, 0.45, 1.1, 0.6)]:
    tw = twin_troughs(dia, z0, sp, vl1, vl2, k, second_vl_factor=f, second_inner_k=kin)
    xs = [-30.0, -10.0, 0.0, sp / 2, sp, sp + 10.0]
    twins.append({"in": {"diameter_m": dia, "axis_depth_m": z0, "spacing_m": sp, "volume_loss_first": vl1, "volume_loss_second": vl2, "k": k,
                         "second_vl_factor": f, "second_inner_k": kin},
                  "out": {"samples": [{"x": x, "s": tw.settlement(x), "u": tw.horizontal(x)} for x in xs]}})

write("settlement", {"symmetric": st, "asymmetric": asym, "presets": presets, "twin": twins})
face = []
# (D, cover, gamma, phi, c, water_depth, q, k_wedge)
for dia, cov, g, phi, c, hw, q, kw in [(10, 15, 20, 30, 0, None, 0, None), (8, 12, 20, 30, 0, 3, 0, None), (6, 9, 19, 25, 8, 0, 10, 0.4),
                                       (12, 20, 21, 35, 2, 5, 20, None), (8, 12, 20, 0, 40, None, 0, None)]:
    kw_args = {"q": q, "k_wedge": kw} | ({} if hw is None else {"water_depth": hw})
    fs = wedge_silo(dia, cov, g, phi, c, **kw_args)
    win = daub_window(fs, dia, cov, g, q=q, **({} if hw is None else {"water_depth": hw}))
    face.append({"in": {"diameter": dia, "cover": cov, "gamma": g, "phi_deg": phi, "c": c, "water_depth": hw, "q": q, "k_wedge": kw},
                 "out": {"support": asdict(fs), "window": asdict(win) | {"feasible": win.feasible}}})
silo = [{"in": [d, b, l, g, c, phi, k, q], "out": silo_stress(d, b, l, g, c, phi, k, q)}
        for d, b, l, g, c, phi, k, q in [(10, 5, 3, 20, 0, 30, 0.8, 0), (25, 7, 4, 10, 5, 28, 0.8, 50), (4, 6, 6, 18, 0, 0, 0.8, 10)]]
write("face_support", {"wedge_silo": face, "silo": silo})
from tunnelsim_models.epb_chamber import Chamber, Screw, crown_pressure  # noqa: E402

epb = []
# (chamber m^3, K_s kPa, excavated m^3/s, target kPa, FIR, FER, screw stop s)
for vol, ks, qe, p, fir, fer, stop in [(30, 1e5, 0.032, 200, 0.0, 10, 20), (30, 1e5, 0.032, 200, 0.4, 10, 60), (55, 5e4, 0.09, 320, 0.6, 15, 30),
                                       (8, 1e5, 0.004, 120, 0.2, 8, 10)]:
    ch = Chamber(vol, ks)
    q = ch.screw_flow_for_pressure(p, qe, fir, fer)
    st = ch.steady_state(qe, q, fir, fer)
    trace = []
    for t in range(0, 241, 20):  # screw stopped for `stop` s, then 1.5x the balance flow
        trace.append({"t": t, "p": ch.pressure(st), "fill": ch.fill(st), "air": ch.air_fraction(st)})
        for _ in range(20):
            st = ch.step(st, 1.0, qe, 0.0 if t < stop else 1.5 * q, fir, fer)
    st_at = ch.state_at(p, 0.1)
    epb.append({"in": {"volume": vol, "k_solid": ks, "q_exc": qe, "p": p, "fir": fir, "fer": fer, "stop": stop},
                "out": {"screw_flow": q, "steady": asdict(ch.steady_state(qe, q, fir, fer)), "stiffness": ch.stiffness(ch.steady_state(qe, q, fir, fer)),
                        "state_at": asdict(st_at), "crown": crown_pressure(p, 3.5), "trace": trace}})
screws = []
for d, ds, pitch, length, eta, lam, rpm in [(0.9, 0.3, 0.7, 12, 0.6, 3, 10), (1.2, 0.4, 0.9, 16, 0.5, 4, 6)]:
    sc = Screw(d, ds, pitch, length, eta, lam)
    screws.append({"in": {"diameter": d, "shaftDiameter": ds, "pitch": pitch, "length": length, "efficiency": eta, "decayLength": lam, "rpm": rpm},
                   "out": {"q_th": sc.theoretical_flow(rpm), "q": sc.discharge(rpm), "outlet": sc.outlet_pressure(250), "mid": sc.pressure_along(length / 2, 250)}})
write("epb_chamber", {"chamber": epb, "screw": screws})
from tunnelsim_models.thrust_torque import cutterhead_torque, sanity_bands, shield_thrust, vertical_stress  # noqa: E402

tt = []
# (D, L, axis depth, gamma, p_axis, water, k0, mu_s, shield W, tools, tail, backup W, opening, n arms, arm A, arm r, tool T, seals)
for row in [(7, 9, 18, 20, 200, 3, 0.5, 0.3, 4000, 1000, 500, 6000, 0.3, 4, 0.5, 2.5, 525, 300),
            (12, 12, 25, 21, 320, None, 0.45, 0.25, 15000, 3000, 1200, 20000, 0.4, 6, 1.0, 4.0, 2000, 800),
            (4, 6, 9, 19, 90, 0, 0.6, 0.35, 900, 200, 150, 1500, 0.25, 0, 0.0, 0.0, 80, 50)]:
    d, ln, z, g, p, hw, k0, mus, ws, tools, tail, wb, xi, na, aa, ar, ttool, seals = row
    wkw = {} if hw is None else {"water_depth": hw}
    th = shield_thrust(d, ln, z, g, p, k0=k0, mu_shield=mus, shield_weight=ws, tools=tools, tail_seal=tail, backup_weight=wb, **wkw)
    sn = vertical_stress(z, g, **wkw) * (1 + k0) / 2
    tq = cutterhead_torque(d, p, sn, opening_ratio=xi, n_arms=na, arm_area=aa, arm_radius=ar, tools=ttool, seals=seals)
    tt.append({"in": dict(zip("d ln z g p hw k0 mus ws tools tail wb xi na aa ar ttool seals".split(), row)),
               "out": {"sv_eff": vertical_stress(z, g, **wkw), "sv_total": vertical_stress(z, g, effective=False, **wkw),
                       "thrust": asdict(th) | {"total": th.total}, "sigma_n": sn, "torque": asdict(tq) | {"total": tq.total},
                       "bands": sanity_bands(d)}})
write("thrust_torque", tt)
print("wrote", sorted(p.name for p in OUT.glob("*.json")))
