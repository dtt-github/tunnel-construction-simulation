"""Regenerate models/test-vectors/*.json from the Python reference implementation.

Run: uv run --project models/py python models/py/make_vectors.py
The JS tests (node --test models/js/test) must reproduce these values to 1e-9 relative.
"""
import json
import math
import pathlib
from dataclasses import asdict

from tunnelsim_models import critical_stability_ratio, face_volume_loss, load_factor, macklin_volume_loss
from tunnelsim_models import deflection_modification_factor, deflection_ratios, frame_bending_stiffness, relative_bending_stiffness
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
for thrust, rpm, n, d, ucs, bts, tmax, pmax, pen in [(12000, 6, 50, 7.0, 150, 10, None, None, None), (18000, 5, 70, 9.5, 220, 14, 8000, None, None),
                                                    (6000, 8, 40, 5.5, 60, 5, 1500, None, None), (11000, 6, 50, 7.0, 40, 4, 4200, 2500, 12.0),
                                                    (15000, 9, 50, 7.0, 140, 10, 4200, 2500, 12.0), (20000, 4, 62, 9.5, 180, 12, 9000, 3500, 10.0)]:
    perf.append({"in": {"thrust_kn": thrust, "rpm": rpm, "n_cutters": n, "head_diameter_m": d, "ucs_mpa": ucs, "bts_mpa": bts, "max_torque_knm": tmax,
                        "max_power_kw": pmax, "max_penetration_mm": pen},
                 "out": asdict(tbm_performance(thrust, rpm, n, d, ucs, bts, max_torque_knm=tmax, max_power_kw=pmax, max_penetration_mm=pen))})
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
for dia, z0, vl, k, kl, kr, comps, il in [
    (6.0, 20.0, 0.01, 0.5, 0.7, 0.5, None, None),
    (5.0, 19.5, 0.006, 0.5, None, 0.35, [(0.2, 0.0), (0.3, 4.0), (0.5, 8.0)], None),
    (8.0, 15.0, 0.012, 0.4, 0.45, 0.6, [(0.5, 0.0), (0.5, 6.0)], None),
    (6.0, 20.0, 0.008, 0.5, None, None, [(0.1, 0.0), (0.4, 9.0), (0.5, 18.0)], 6.0),
]:
    t = gaussian_trough(dia, z0, vl, k, k_left=kl, k_right=kr, components=comps, i_long=il)
    asym.append({"in": {"diameter_m": dia, "axis_depth_m": z0, "volume_loss": vl, "k": k, "k_left": kl, "k_right": kr, "components": comps, "i_long": il},
                 "out": trough_out(t, [-2 * t.i, -5.0, 0.0, 5.0, t.i, 2 * t.i], ys)})

presets = []
for method, dia, z0, length, il in [("open_face_stiff_clay", 4.85, 20.0, None, None), ("closed_face_clay", 6.0, 18.0, 9.0, None),
                                    ("closed_face_sand", 10.0, 25.0, 12.0, None), ("scl_stiff_clay", 7.0, 22.0, None, None),
                                    ("closed_face_clay", 6.0, 18.0, 9.0, 5.0)]:
    t = preset_trough(method, dia, z0, shield_length_m=length, i_long=il)
    presets.append({"in": {"method": method, "diameter_m": dia, "axis_depth_m": z0, "shield_length_m": length, "i_long": il},
                    "out": trough_out(t, [0.0, 5.0, t.i], ys)})

twins = []
for dia, z0, sp, vl1, vl2, k, f, kin, kout in [(5.0, 19.5, 26.0, 0.006, None, 0.5, 1.0, None, None), (5.0, 19.5, 26.0, 0.006, 0.006, 0.5, 1.3, 0.8, None),
                                              (6.0, 20.0, -15.0, 0.01, 0.008, 0.45, 1.1, 0.6, None), (7.1, 34.5, 16.2, 0.005, None, 0.43, 1.7, 0.44, 0.33),
                                              (7.1, 20.0, -17.0, 0.0025, None, 0.5, 1.2, None, 0.4)]:
    tw = twin_troughs(dia, z0, sp, vl1, vl2, k, second_vl_factor=f, second_inner_k=kin, second_outer_k=kout)
    xs = [-30.0, -10.0, 0.0, sp / 2, sp, sp + 10.0]
    twins.append({"in": {"diameter_m": dia, "axis_depth_m": z0, "spacing_m": sp, "volume_loss_first": vl1, "volume_loss_second": vl2, "k": k,
                         "second_vl_factor": f, "second_inner_k": kin, "second_outer_k": kout},
                  "out": {"samples": [{"x": x, "s": tw.settlement(x), "u": tw.horizontal(x)} for x in xs]}})

# load factor and Macklin volume loss: (sigma_v, support, S_u, C/D, base VL)
face_vl = []
for sv, pt, su, cd, base in [(600, 220, 235, 3.7, 0.005), (600, 0, 235, 3.7, 0.005), (300, 50, 120, 1.0, 0.003), (400, 300, 150, 2.2, 0.01)]:
    lf = load_factor(sv, pt, su, cd)
    face_vl.append({"in": {"sigma_v": sv, "support": pt, "su": su, "cover_over_d": cd, "base_vl": base},
                    "out": {"n_tc": critical_stability_ratio(cd), "lf": lf, "macklin": macklin_volume_loss(lf), "vl": face_volume_loss(base, lf)}})
# building stiffness and deflection ratio (Potts & Addenbrooke 1997 via Mair 1997 Fig. 4)
bending = {"m_dr": [{"in": [mode, r, e], "out": deflection_modification_factor(mode, r, e)}
                    for mode in ("sag", "hog") for r in (1e-8, 3e-6, 1e-4, 2.5e-3, 0.5, 30.0) for e in (0.0, 0.1, 0.3, 0.5, 0.8)],
           "frame": [{"in": n, "out": frame_bending_stiffness(n)} for n in (1, 4, 9)],
           "rho": relative_bending_stiffness(frame_bending_stiffness(4), 77.6e3, 20.0)}
dr_cases = []
for z0, vl, k, xmin, xmax in [(30, 0.005, 0.5, -10, 10), (30, 0.005, 0.5, 5, 30), (20, 0.01, 0.43, -40, 2), (34.5, 0.0078, 0.44, -3, 0.5)]:
    t = gaussian_trough(7.08, z0, vl, k)
    r = deflection_ratios(t.settlement, xmin, xmax, t.i, t.i)
    dr_cases.append({"in": {"z0": z0, "vl": vl, "k": k, "x_min": xmin, "x_max": xmax}, "out": {kk: (list(v) if v else None) for kk, v in r.items()}})
bending["deflection_ratios"] = dr_cases
write("settlement", {"symmetric": st, "asymmetric": asym, "presets": presets, "twin": twins, "face_volume_loss": face_vl, "bending": bending})
face = []
# (D, cover, gamma, phi, c, water_depth, q, k_wedge)
for dia, cov, g, phi, c, hw, q, kw in [(10, 15, 20, 30, 0, None, 0, None), (8, 12, 20, 30, 0, 3, 0, None), (6, 9, 19, 25, 8, 0, 10, 0.4),
                                       (12, 20, 21, 35, 2, 5, 20, None), (8, 12, 20, 0, 40, None, 0, None), (7, 10, 20, 35, 0, -8, 0, None)]:
    kw_args = {"q": q, "k_wedge": kw} | ({} if hw is None else {"water_depth": hw})
    fs = wedge_silo(dia, cov, g, phi, c, **kw_args)
    win = daub_window(fs, dia, cov, g, deviation=30.0 if c else 10.0, **({} if hw is None else {"water_depth": hw}))
    face.append({"in": {"diameter": dia, "cover": cov, "gamma": g, "phi_deg": phi, "c": c, "water_depth": hw, "q": q, "k_wedge": kw},
                 "out": {"support": asdict(fs), "window": asdict(win) | {"feasible": win.feasible, "p_min_crown_operating": win.p_min_crown_operating,
                                                                           "p_max_crown_operating": win.p_max_crown_operating}}})
# DAUB (2016) example 8.1, case 1: slurry shield, D 10 m, crown 15 m deep, sand phi' 30, gamma 18 / 8 (min 17 / 7),
# water 2 m below the surface, 10 kPa traffic load, no silo, side friction (K0 + Ka) / 2, square face of side D
daub_fs = wedge_silo(10, 15, 18, 30, 0, gamma_sub=8, water_depth=2, q=10, k_silo=0.0, k_wedge=0.417, side=10)
daub_win = daub_window(daub_fs, 10, 15, 18, gamma_sub=8, water_depth=2, gamma_min=17, gamma_sub_min=7, deviation=10.0)
daub_example = {"in": {"diameter": 10, "cover": 15, "gamma": 18, "gamma_sub": 8, "gamma_min": 17, "gamma_sub_min": 7, "phi_deg": 30,
                       "water_depth": 2, "q": 10, "k_silo": 0.0, "k_wedge": 0.417, "side": 10, "deviation": 10.0},
                "out": {"support": asdict(daub_fs), "window": asdict(daub_win) | {"p_min_crown_operating": daub_win.p_min_crown_operating,
                                                                                   "p_max_crown_operating": daub_win.p_max_crown_operating}},
                "daub_published": {"theta_crit_deg": 66.56, "E_re_kN": 4122.32, "s_crown_min": 190.8, "s_axis_min": 250.8,
                                   "sigma_v_crown_min": 255.0, "s_crown_max": 229.5, "operating_crown": [200.8, 219.5]}}
silo = [{"in": [d, b, l, g, c, phi, k, q], "out": silo_stress(d, b, l, g, c, phi, k, q)}
        for d, b, l, g, c, phi, k, q in [(10, 5, 3, 20, 0, 30, 0.8, 0), (25, 7, 4, 10, 5, 28, 0.8, 50), (4, 6, 6, 18, 0, 0, 0.8, 10)]]
write("face_support", {"wedge_silo": face, "silo": silo, "daub_example_8_1": daub_example})
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
for d, ds, pitch, length, eta, lam, fe, rpm in [(0.9, 0.3, 0.7, 12, 0.6, 3, 1.0, 10), (1.2, 0.4, 0.9, 16, 0.5, 4, 1.0, 6), (0.9, 0.3, 0.7, 11, 0.6, 16, 0.85, 8)]:
    sc = Screw(d, ds, pitch, length, eta, lam, fe)
    screws.append({"in": {"diameter": d, "shaftDiameter": ds, "pitch": pitch, "length": length, "efficiency": eta, "decayLength": lam,
                          "entranceFactor": fe, "rpm": rpm},
                   "out": {"q_th": sc.theoretical_flow(rpm), "q": sc.discharge(rpm), "outlet": sc.outlet_pressure(250), "mid": sc.pressure_along(length / 2, 250)}})
write("epb_chamber", {"chamber": epb, "screw": screws})
from tunnelsim_models.thrust_torque import cutterhead_torque, reference_installed, shield_thrust, vertical_stress  # noqa: E402

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
    tqp = cutterhead_torque(d, p, sn, opening_ratio=xi, n_arms=na, arm_area=aa, arm_radius=ar, tools=ttool, seals=seals, tau_paste=2.0)
    tt.append({"in": dict(zip("d ln z g p hw k0 mus ws tools tail wb xi na aa ar ttool seals".split(), row)),
               "out": {"sv_eff": vertical_stress(z, g, **wkw), "sv_total": vertical_stress(z, g, effective=False, **wkw),
                       "thrust": asdict(th) | {"total": th.total}, "sigma_n": sn, "torque": asdict(tq) | {"total": tq.total},
                       "torque_paste": asdict(tqp) | {"total": tqp.total},
                       "reference": {t: reference_installed(t, d) for t in ("epb", "slurry", "gripper")},
                       "reference_all": {t: reference_installed(t, d, include_unverified=True) for t in ("epb", "slurry", "gripper")}}})
write("thrust_torque", tt)
from tunnelsim_models.utilisation import DIST, DriveSettings, Rng, normal_inv, record_check, sample, simulate_drive  # noqa: E402

rng = Rng(42)
uni = [rng.uniform() for _ in range(20)]
util = {"uniform_seed42": uni, "normal_inv": [[p, normal_inv(p)] for p in (0.001, 0.01, 0.2, 0.5, 0.8, 0.99, 0.999)],
        "samples": {k: [sample(d, u) for u in (0.05, 0.3, 0.5, 0.7, 0.95)] for k, d in DIST.items()}, "drives": []}
for sp, hl, bore, iv, days, seed in [("2x10h_plus_4h_maintenance", "conveyor", None, True, 90, 1), ("2x12h_maintenance_per_cycle", "rail", None, True, 60, 7),
                                     ("2x10h_plus_4h_maintenance", "conveyor", 20.0, False, 30, 3), ("idealised_24h", "conveyor", 25.0, True, 120, 11)]:
    r = simulate_drive(DriveSettings(shift_pattern=sp, haulage=hl, boring_min=bore, interventions=iv), days=days, seed=seed)
    util["drives"].append({"in": {"shift_pattern": sp, "haulage": hl, "boring_min": bore, "interventions": iv, "days": days, "seed": seed},
                           "out": asdict(r) | {"check": record_check(7.08, r.best_day, r.best_week, r.best_month)}})
util["learning"] = []
for ld, ls, days, seed in [(90.0, 0.5, 120, 2), (30.0, 0.3, 60, 5)]:
    r = simulate_drive(DriveSettings(shift_pattern="2x12h_maintenance_per_cycle", boring_min=26.7, ring_length=1.6,
                                     ring_build={"kind": "fixed", "value": 32.0}, interventions=True, learning_days=ld, learning_start=ls),
                       days=days, seed=seed)
    util["learning"].append({"in": {"learning_days": ld, "learning_start": ls, "days": days, "seed": seed}, "out": asdict(r)})
util["day_variation"] = []
for sig, rho, days, seed in [(0.4, 0.7, 120, 4), (0.25, 0.0, 60, 9)]:
    r = simulate_drive(DriveSettings(shift_pattern="2x12h_maintenance_per_cycle", boring_min=26.7, ring_length=1.6,
                                     ring_build={"kind": "fixed", "value": 32.0}, interventions=True, day_sigma=sig, day_rho=rho),
                       days=days, seed=seed)
    util["day_variation"].append({"in": {"day_sigma": sig, "day_rho": rho, "days": days, "seed": seed}, "out": asdict(r)})
write("utilisation", util)
from tunnelsim_models import max_rpm  # noqa: E402
from tunnelsim_models.hard_rock import cutter_change_h_per_km, hard_rock_utilisation, rmr_class, support_downtime  # noqa: E402

hr = {"max_rpm": [[d, c, max_rpm(d, c)] for d, c in [(7.0, 482.6), (10.0, 482.6), (7.0, 432.0), (14.4, 508.0)]],
      "cutters": [[d, cai, cutter_change_h_per_km(d, cai)] for d, cai in [(3.9, 2), (7.0, 3.5), (10.0, 5)]],
      "support": [[rmr, d, m, support_downtime(rmr, d, m)] for rmr in (15, 35, 50, 65, 85) for d, m in [(4, "open"), (7, "open"), (10, "open"), (10, "single"), (10, "double")]],
      "classes": [[rmr, rmr_class(rmr)["class"]] for rmr in (95, 70, 45, 25, 5)], "utilisation": []}
for pr, d, kw in [(4.7, 3.9, {"stroke_m": 1.25, "ucs_mpa": 90, "rmr": 45, "haulage": "rail", "quartz_percent": 3, "maintenance": "good", "transport": "normal", "survey": 0, "other": 0}),
                  (3.0, 9.5, {"rmr": 65, "ucs_mpa": 180, "quartz_percent": 25, "curve_radius_m": 600.0}),
                  (2.2, 10.0, {"rmr": 35, "machine": "double", "ucs_mpa": 120, "cutter_h_per_km": 80.0, "maintenance": "poor", "transport": "very_good"})]:
    r = hard_rock_utilisation(pr, d, **kw)
    hr["utilisation"].append({"in": {"pr": pr, "d": d, **kw}, "out": asdict(r)})
write("hard_rock", hr)
from tunnelsim_models import ground_response as gr  # noqa: E402

grv = {"mc": [], "grc": [], "ldp": [], "squeeze": [], "support": [], "shield": []}
for gsi, mi, sci, ei, p0 in [(25, 10, 10, 10000, 2.0), (65, 28, 150, 60000, 8.1), (17, 10, 40, 15000, 8.1), (45, 12, 90, 30000, 16.2)]:
    grv["mc"].append({"in": [gsi, mi, sci, ei, p0], "out": asdict(gr.equivalent_mohr_coulomb(gsi, mi, sci, ei, p0))})
for args in [(2, 0, 3, 749.9, 0.3, 24.72, 0.22), (2, 0.5, 3, 749.9, 0.3, 24.72, 0.22), (2, 1.5, 3, 749.9, 0.3, 24.72, 0.22), (8.1, 0, 4.95, 595, 0.25, 22.9, 0.78),
             (0.6, 0, 5.5, 180.0, 0.495, 0.0, 0.3), (0.6, 0.1, 5.5, 180.0, 0.495, 0.0, 0.3)]:
    grv["grc"].append({"in": list(args), "out": asdict(gr.ground_reaction(*args)), "p_inv": gr.pressure_for_displacement(gr.ground_reaction(*args).u * 1.1, *args[:1], *args[2:])})
grv["ldp"] = [[x, r0, rp, gr.ldp(x, r0, rp)] for x in (-10, -2, 0, 3, 10, 40) for r0, rp in ((5, 5), (5, 12.9))]
grv["squeeze"] = [[scm, p0, pi, gr.squeezing_strain(scm, p0, pi), gr.squeezing_class(gr.squeezing_strain(scm, p0, pi))[0]] for scm, p0, pi in ((1.01, 2.6, 0), (2.9, 8.1, 0), (2.9, 8.1, 1.0), (30, 8.1, 0))]
ring, sets, bolts = gr.ring_support(3.0, 0.2, 30000, 0.15, 35), gr.steel_set_support(3.0, 1.0, 0.0125), gr.bolt_support(3.0, 12, 1.0, 3.0, 0.025, 0.18)
grv["support"] = {"ring": asdict(ring), "sets": asdict(sets), "bolts": asdict(bolts), "combined": asdict(gr.combine(ring, sets)),
                  "eq": asdict(gr.support_equilibrium(2, 3, 749.9, 0.3, 24.72, 0.22, gr.combine(ring, sets), 0.005))}
for args in [(5, 10, 0.05, 10, 1000, 0.25, 25, 0.9564, 0.30), (4.95, 13.7, 0.10, 8.1, 595, 0.25, 22.9, 0.78, 0.275), (4.79, 4.0, 0.05, 8.1, 595, 0.25, 22.9, 0.78, 0.425)]:
    grv["shield"].append({"in": list(args), "out": asdict(gr.shield_friction(*args))})
write("ground_response", grv)
from tunnelsim_models import sem  # noqa: E402

semv = {"ageing": [[t, sem.shotcrete_modulus(t), sem.shotcrete_strength(t), sem.shotcrete_modulus(t, "oreste_example"), sem.mc90_modulus(t / 24, 21537, 13943)]
                   for t in (2, 6, 24, 72, 168, 672)],
        "classes": [[t, f, sem.early_strength_class(t, f)] for t, f in ((1, 1.0), (24, 10), (24, 1.0), (24, 3), (24, 20), (0.5, 0.3), (6, 2.5))],
        "fict": [[x, sem.fictitious_pressure(x, 2.7, 5.0)] for x in (0, 2, 10, 40)], "lining": [], "sulem": [], "triggers": []}
for gsi, mi, sci, ei, p0, th, xi, v in [(22, 8, 15, 3000, 2.7, 0.35, 1.0, 0.125), (45, 9, 30, 8000, 2.7, 0.2, 1.0, 0.125), (22, 8, 15, 3000, 4.05, 0.35, 2.0, 0.25)]:
    m = gr.equivalent_mohr_coulomb(gsi, mi, sci, ei, p0)
    li = sem.lining_interaction(p0, 5.0, m.e_rm, 0.25, m.phi_deg, m.c, th, xi, v)
    semv["lining"].append({"in": [p0, 5.0, m.e_rm, 0.25, m.phi_deg, m.c, th, xi, v],
                           "out": {k: getattr(li, k) for k in ("u_install", "u_final", "p_final", "hours_to_95", "min_safety", "min_safety_age_h")}})
semv["sulem"] = [[x, t, sem.sulem_convergence(x, t, 20, 4.6, 6, 5.7, 0.3)] for x, t in ((0, 1), (2, 0.5), (10, 5), (50, 60))]
semv["triggers"] = [[m_, sem.trigger_level(m_, 10)] for m_ in (5, 8, 11, 16)]
semv["crown"] = [[k, nu, uf, us, sem.kirsch_crown_factor(k, nu), sem.crown_settlement(uf, us, k, nu)]
                 for k, nu, uf, us in ((0.6, 0.495, 0.012, 0.004), (1.0, 0.3, 0.01, 0.002), (1.2, 0.495, 0.009, 0.003), (0.6, 0.495, 0.002, 0.004))]
write("sem", semv)
from tunnelsim_models import slurry as sl  # noqa: E402

slv = {"inf": [], "cushion": [], "circuit": []}
for dp, tau, d10, L, t, a in [(70.8, 0.03, 0.8e-3, 6.8, None, None), (70.8, 0.03, 0.15e-3, 6.0, None, None), (50, 0.02, 1.2e-3, 5.0, 10, 8), (120, 0.05, 2e-3, 7.0, 20, 5)]:
    slv["inf"].append({"in": [dp, tau, d10, L, 3.5, t, a], "out": asdict(sl.infiltration(dp, tau, d10, L, 3.5, t, a))})
c = sl.Cushion(12.0)
st = sl.CushionState(200.0, 0.5, 20.0)
trace = []
for i in range(30):
    st = c.step(st, 1.0, 0.25, 0.04 if i < 15 else 0.0, 0.25 if i < 20 else 0.3, 200.0)
    trace.append(asdict(st))
slv["cushion"] = trace
area, v = math.pi * 7.08**2 / 4, 0.040 / 60
qd, rd = sl.discharge_density(0.25, 1.05, area, v, 2.0)
slv["circuit"] = {"qd": qd, "rd": rd, "dry": sl.dry_solids_flow(0.25, 1.05, qd, rd), "theo": sl.theoretical_dry_flow(area, v, 2.0),
                  "durand": sl.durand_velocity(0.3), "vpipe": sl.pipe_velocity(1000 / 3600, 0.3), "pore": sl.excess_pore_pressure(5, 30, 1e-4, 10, 1e6)}
write("slurry", slv)
from tunnelsim_models import drill_blast as db  # noqa: E402

dbv = {"rounds": [], "cycles": [], "basic": {}}
for w, h, d, design in [(10.6, 2.9, 5.2, "norwegian"), (10.6, 2.9, 5.2, "textbook"), (9.6, 2.55, 4.0, "norwegian"), (12.0, 3.6, 5.5, "norwegian")]:
    rd = db.design_round(w, h, d, design=design)
    dbv["rounds"].append({"in": [w, h, d, design], "out": {"holes": [[x.x, x.y, x.kind, x.delay] for x in rd.holes], "n_charged": rd.n_charged,
                          "explosive": rd.explosive, "specific_charge": rd.specific_charge, "max_charge_per_delay": rd.max_charge_per_delay,
                          "pull": rd.pull, "area": rd.area}})
    for cls in db.SUPPORT_CLASSES:
        cy = db.round_cycle(rd, w, h, cls)
        dbv["cycles"].append({"in": [len(dbv["rounds"]) - 1, cls], "out": {"steps": [x[1] for x in cy.steps], "total_h": cy.total_h, "m_per_week": cy.m_per_week,
                              "muck_m3": cy.muck_m3}})
dbv["basic"] = {"qb": db.bottom_charge(38, 1.5, 0.8), "b": db.burden(38, 1.36), "b1": db.first_cut_burden(0.115, 2.85, 0.02, 0.02),
                "h": db.hole_depth(0.204), "cut": db.cut_sections(0.204, 5.2), "x50": db.kuz_ram_x50(7, 0.6, 34.79),
                "n": db.uniformity_index(2.5, 2.44, 89, 0.1, 8, 9.5), "ppv": db.ppv(40, 8), "qmax": db.max_charge_per_delay(50, 20),
                "ss": [db.ss4604866_limit(d_, "rock", g) for d_ in (15, 60, 500) for g in ("rock", "sand_gravel", "clay")]}
dbv["practice"] = [{"in": [a, r], "out": list(db.practice_specific_charge(a, r))} for a in (30, 74.59, 120) for r in (True, False)]
write("drill_blast", dbv)
from tunnelsim_models import lining as ln  # noqa: E402

lnv = {"rings": [], "basic": {}}
for args in [(183.60, 157.68, 202.83, 3.25, 1.6125, 33e6 * 1.6276e-4, 20000, 1.0, False), (332.0, 234.0, 300.0, 7.5, 3.25, 35e6 * 0.3**3 / 12, 15000, 0.327, False),
             (250.0, 150.0, 220.0, 8.75, 3.4, 37e6 * 0.35**3 / 12, 30000, 0.25, True)]:
    r = ln.jsce_ring(*args[:7], eta=args[7], dead_load_in_deflection=args[8])
    lnv["rings"].append({"in": list(args), "out": {"moment": r.moment, "normal": r.normal, "deflection": r.deflection, "reaction": r.reaction}})
lnv["basic"] = {"wood": [ln.wood_inertia(1.0, n) for n in (4, 6, 7, 8)], "loads": list(ln.ring_loads(20, 3.4, 20, 0.5, 3)),
                "sec": list(ln.section_stresses(1000, 50, 0.3)), "jack": ln.jacking_stress(1000, 10, 1.6125, 0.125),
                "burst_aci": list(ln.bursting_force(3000, 0.35, 0.2, 0.03, "aci")), "burst_daub": list(ln.bursting_force(3000, 0.35, 0.2)),
                "annulus": ln.annulus_volume(7.06, 6.9, 1.5), "grout": list(ln.grout_window(16.5, 20, 3)), "grout_river": list(ln.grout_window(12, 19, -12.5)), "taper": [ln.taper(6.9, 1.5, 250), ln.taper(6.9, 1.5, 250, 22.5)],
                "terzaghi": [list(ln.terzaghi_loads(*a)) for a in ((6.0, 3.4, 20, 30, 0, 0.5, 100), (40.0, 3.4, 20, 30, 0, 0.5, 100), (40.0, 3.4, 20, 30, 0, 0.5, 0.0),
                             (35.0, 3.5, 20.2, 22, 12, 1.5, 9.0), (30.0, 3.5, 19.5, 24, 1, 0.42, 4.0, 10.0, 15.0))],
                "ka": ln.active_coefficient(24)}
write("lining", lnv)
from tunnelsim_models import scenario as sc  # noqa: E402

SC_DATA = {
    "format": sc.FORMAT, "name": "vectors",
    "units": {"MG": {"gamma": 19, "phi": 25, "c": 0, "k0": 0.5, "E": 10000}, "TG": {"gamma": 20, "phi": 35, "c": 0, "k0": 0.45, "E": 40000, "d10": 0.0008},
              "LC": {"gamma": 20, "phi": 23, "c": 5, "k0": 1.5, "E": 60000, "pore_pressure_ratio": 0.9},
              "LM": {"gamma": 20.5, "phi": 26, "c": 10, "k0": 1.2, "E": 80000, "water": "lower"}},
    "alignment": {"length": 1000, "axis_level": [[0, -15.0], [600, -18.0], [1000, -16.0]]},
    "ground_surface": [[0, 12.0], [1000, 10.0]], "groundwater": {"level": [[0, 5.0], [1000, 4.0]], "deep_head": [[0, -24.0], [1000, -22.0]]},
    "boreholes": [{"id": "A", "chainage": 0, "tops": {"MG": 12, "TG": 9, "LC": 5, "LM": -30}}, {"id": "B", "chainage": 500, "tops": {"MG": 11, "LC": 6, "LM": -26}},
                  {"id": "C", "chainage": 1000, "tops": {"MG": 10, "TG": 8, "LC": 3}, "base_level": -20}],
}
scn = sc.Scenario(SC_DATA)
scv = {"data": SC_DATA, "points": []}
for ch in (0, 120, 250, 500, 640, 800, 1000, 1200):
    f = scn.face(ch, 7.1) if ch != 120 else scn.face(ch, 9.0, axis_level=6.0)  # one face in the gravel
    scv["points"].append({"ch": ch, "column": [[l.unit, l.top, l.base] for l in scn.column(ch)], "unit_m20": scn.unit_at(ch, -20),
                          "face": {"unit_at_axis": f.unit_at_axis, "units_on_face": f.units_on_face, "gamma": f.gamma, "phi": f.phi, "c": f.c,
                                   "k0": f.k0, "e_soil": f.e_soil, "cover": f.cover, "axis_depth": f.axis_depth, "water_depth": f.water_depth,
                                   "u_axis": f.u_axis, "water_depth_equiv": f.water_depth_equiv, "d10": f.d10}, "u_m30": scn.pore_pressure(ch, -30)})
write("scenario", scv)
print("wrote", sorted(p.name for p in OUT.glob("*.json")))
