"""Check the hard-rock TBM models (CSM penetration and Farrokh downtime per km) against published project rates.

Data (open sources, read and cited, not redistributed):
- Follo Line TBM1 (9.96 m Herrenknecht double shield, 71 x 19" discs, 4,550 kW, 11,115 kNm; gneiss, UCS 152.45 MPa,
  BTS 10.38 MPa, Q 21.2, quartz 39 %): 4.5 km weighted means 5.08 rpm, 21,217 kN gross thrust, 3,200 kN shield drag,
  6.32 mm/rev, 1.92 m/h. Hansen (2018), NTNU MSc, Tables 2.4 and 5.1, Figs 5.6-5.14: https://hdl.handle.net/11250/2503069
- Follo northbound machines to August 2018, including probing and pre-grouting: average day 14.1 m (best 31 m), week
  85 m (144 m), month 364 m (568 m). Iddeng (2019), NTNU MSc, Table 3.3, after Kalager & Gammelsaeter (2019, WTC):
  https://nva.sikt.no/registration/0198e6b19388-e58a5658-5843-49c9-8b5e-13171b80cf86
- Follo cutter changes: about 4,200 per machine over about 9.5 km. Herrenknecht reference:
  https://herrenknecht.com/en/references/referencesdetail/follo-line
- Gotthard S-210 (9.33 m gripper): 13,427 m in 1,405 days, best day 38 m, best week 183.6 m. Tunnels & Tunnelling
  (Oct 2006): https://tunnelsandtunnelling.com/?p=5739 . Gotthard gripper TBMs 3,500 kW, 8,526 kNm; best day 56 m:
  https://www.herrenknecht.com/en/references/referencesdetail/gotthard-base-tunnel/
- Guadarrama (9.5 m double shields, granite and gneiss): 16-20 m/day per drive, best day 64 m, best month 980 m.
  Tunnelbuilder (18 Mar 2004), trade press.
- Brenner Base Tunnel: Aicha-Mauls exploratory double shield (6.3 m) about 16 m/day net (Michael et al. 2011, IS-Rome,
  p. 263: https://www.issmge.org/uploads/publications/6/13/2011_030.pdf); Mules main-tunnel double shields (10.65 m)
  typical 15 m/day, record month 860 m (BBT SE newsroom, March 2021).
- Niagara (14.4 m Robbins main beam, Queenston shale): 18 m/day by April 2007; about 3 m/day with spiling in poor
  ground. Robbins (2010), WTC: https://www.robbinstbm.com/wp-content/uploads/2010/07/Large-Diameter-TBMs_WTC2010.pdf

No open source gives utilisation (boring time / total time) or a downtime breakdown for these projects.

Section by section (Follo TBM1, 18 sections of 219-316 m): per-section length (Table 4.7), UCS and BTS (one laboratory test
per section; BTS from UCS by Hansen's Eq. 4.9; Figs 5.10-5.11), total fracturing factor ks (Fig. 5.2), and the median
cutter thrust, rpm and net penetration rate (box plots, Figs 5.12-5.14), read from the vector graphics of the thesis PDF.
Their length-weighted means reproduce Hansen's Table 5.1 within 1 % (UCS 152.1, BTS 10.35, 301 kN, 5.11 rpm, 1.93 m/h).

The Yinsong (Jilin) hard-rock TBM dataset is not open: the shared CSRME dataset is described in CC BY-NC-ND reviews
(Underground Space 2023) and the papers using it give the data "on reasonable request" (e.g. Sci. Rep. 13:10420, 2023,
doi:10.1038/s41598-023-37306-7). No open paper tabulates its thrust, rpm and penetration by rock class.

Run:  uv run python validation/hard_rock_projects.py      (prints a Markdown summary)
"""
from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from tunnelsim_models.csm import Cutter, tbm_performance  # noqa: E402
from tunnelsim_models.hard_rock import CUTTER_CHANGE_H, hard_rock_utilisation  # noqa: E402

FOLLO = {"d": 9.96, "n": 71, "rpm": 5.08, "gross_kn": 21216.91, "drag_kn": 3200.0, "ucs": 152.45, "bts": 10.38, "q": 21.16,
         "torque": 11115.0, "power": 4550.0, "pen": 6.32, "rop": 1.92, "avg_day": 14.1, "changes_per_km": 4200 / 9.5}
# Follo TBM1 sections (Hansen 2018): length m, UCS MPa, BTS MPa, ks, median kN/cutter, median rpm, median NPR m/h
FOLLO_SECTIONS = (
    (219, 178.76, 12.06, 0.75, 295.2, 4.676, 1.611), (270, 144.04, 9.85, 0.76, 303.0, 4.967, 1.991),
    (316, 148.14, 10.12, 0.81, 300.3, 5.124, 2.041), (270, 124.20, 8.58, 0.69, 318.3, 5.069, 2.019),
    (231, 207.88, 13.87, 0.74, 309.3, 4.867, 1.928), (220, 200.33, 13.39, 0.60, 303.0, 5.198, 1.557),
    (270, 199.68, 13.35, 0.77, 307.0, 5.051, 1.567), (226, 101.55, 7.11, 0.68, 315.0, 5.150, 1.576),
    (226, 123.76, 8.55, 0.69, 313.3, 5.116, 1.611), (224, 123.76, 8.55, 0.65, 315.3, 5.138, 1.821),
    (226, 142.31, 9.75, 0.61, 313.9, 5.164, 1.851), (270, 142.31, 9.75, 0.70, 300.3, 5.143, 1.987),
    (225, 153.74, 10.47, 0.77, 297.4, 5.146, 2.075), (316, 130.23, 8.96, 0.87, 287.5, 5.166, 2.189),
    (225, 129.16, 8.91, 0.70, 283.7, 5.212, 2.160), (270, 128.29, 8.84, 1.20, 272.3, 5.226, 2.276),
    (225, 164.74, 11.17, 0.87, 292.4, 5.206, 2.055), (270, 201.41, 13.46, 0.94, 296.3, 5.239, 2.094),
)
REFERENCE_RATES = (  # project, machine, average, basis
    ("Follo Line (northbound)", "double shield 9.96 m", "14.1 m/day (best 31)", "per day, incl. probing and grouting"),
    ("Guadarrama", "double shield 9.5 m", "16-20 m/day (best 64)", "per drive, trade press"),
    ("Brenner, Aicha-Mauls", "double shield 6.3 m", "about 16 m/day", "net"),
    ("Brenner, Mules main tunnels", "double shield 10.65 m", "about 15 m/day (record month 27.7)", "BBT SE"),
    ("Gotthard S-210", "gripper 9.33 m", "9.6 m/day (best 38)", "13,427 m in 1,405 days"),
    ("Niagara", "main beam 14.4 m", "about 3 m/day with spiling; 18 m/day in better ground", "Robbins 2010"),
)


def follo_penetration(psi: float) -> float:
    f = FOLLO
    cutter = replace(Cutter(), spacing_mm=1000 * f["d"] / 2 / f["n"], psi=psi)
    return tbm_performance(f["gross_kn"] - f["drag_kn"], f["rpm"], f["n"], f["d"], f["ucs"], f["bts"], cutter=cutter,
                           max_torque_knm=f["torque"], max_power_kw=f["power"]).penetration_mm_rev


def follo_sections(psi: float = -0.1, mean_rock: bool = False) -> list[tuple[float, float]]:
    """(measured, predicted) penetration per section, mm/rev. mean_rock uses the tunnel-mean UCS and BTS everywhere."""
    f = FOLLO
    cutter = replace(Cutter(), spacing_mm=1000 * f["d"] / 2 / f["n"], psi=psi)
    out = []
    for _, ucs, bts, _, fn, rpm, npr in FOLLO_SECTIONS:
        u, b = (f["ucs"], f["bts"]) if mean_rock else (ucs, bts)
        p = tbm_performance(fn * f["n"] - f["drag_kn"], rpm, f["n"], f["d"], u, b, cutter=cutter, max_torque_knm=f["torque"],
                            max_power_kw=f["power"]).penetration_mm_rev
        out.append((npr * 1000 / (60 * rpm), p))
    return out


def _summary(pairs: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Length-weighted measured and predicted means, rms of ln(predicted / measured), and its correlation with UCS."""
    w = [s[0] for s in FOLLO_SECTIONS]
    wm = lambda xs: sum(x * l for x, l in zip(xs, w)) / sum(w)
    logs = [math.log(p / m) for m, p in pairs]
    ucs = [s[1] for s in FOLLO_SECTIONS]
    ml, mu = sum(logs) / len(logs), sum(ucs) / len(ucs)
    cov = sum((a - ml) * (b - mu) for a, b in zip(logs, ucs))
    r = cov / math.sqrt(sum((a - ml) ** 2 for a in logs) * sum((b - mu) ** 2 for b in ucs))
    return wm([m for m, _ in pairs]), wm([p for _, p in pairs]), math.sqrt(sum(x * x for x in logs) / len(logs)), r


def follo_advance(regrip_min: float, organisation: str, haulage: str):
    f = FOLLO
    rmr = 9 * math.log(f["q"]) + 44  # Bieniawski (1989) RMR = 9 ln Q + 44
    return hard_rock_utilisation(f["rop"], f["d"], stroke_m=1.8, regrip_min=regrip_min, ucs_mpa=f["ucs"], rmr=rmr, machine="double",
                                 haulage=haulage, cutter_h_per_km=f["changes_per_km"] * CUTTER_CHANGE_H,
                                 maintenance=organisation, transport=organisation)


if __name__ == "__main__":
    print("### Follo TBM1 penetration (CSM, net thrust, spacing = radius / discs)\n")
    print("| psi | Predicted (mm/rev) | Measured (mm/rev) | Predicted / measured |")
    print("|---|---|---|---|")
    for psi in (0.1, 0.0, -0.1):
        p = follo_penetration(psi)
        print(f"| {psi:+.1f} | {p:.2f} | {FOLLO['pen']} | {p / FOLLO['pen']:.2f} |")
    print("\n### Follo advance (measured 1.92 m/h; 442 cutter changes per km at 66 min)\n")
    print("| Regrip (min) | Organisation | Haulage | Utilisation (%) | Advance (m/day) | Measured average day (m) |")
    print("|---|---|---|---|---|---|")
    for rg in (4, 10):
        for org in ("good", "normal"):
            for haul in ("conveyor", "rail"):
                u = follo_advance(rg, org, haul)
                print(f"| {rg} | {org} | {haul} | {u.utilisation * 100:.0f} | {u.advance_m_day:.1f} | {FOLLO['avg_day']} |")
    implied = 1000 / FOLLO["rop"] / (24000 / FOLLO["avg_day"])
    print(f"\nUtilisation implied by the measured rates: {implied * 100:.0f} % (1.92 m/h and 14.1 m/day).")
    w = [sec[0] for sec in FOLLO_SECTIONS]
    chk = [sum(sec[k] * l for sec, l in zip(FOLLO_SECTIONS, w)) / sum(w) for k in (1, 2, 4, 5, 6)]
    print("\nDigitised sections, length-weighted: UCS %.1f, BTS %.2f, %.0f kN/cutter, %.2f rpm, %.2f m/h "
          "(Table 5.1: 152.45, 10.38, 298.83, 5.08, 1.92)." % tuple(chk))
    print("\n### Follo TBM1 section by section (psi -0.1)\n")
    print("| Section | Length (m) | UCS (MPa) | ks | Thrust (kN/cutter) | rpm | Measured (mm/rev) | Predicted (mm/rev) | Predicted / measured |")
    print("|---|---|---|---|---|---|---|---|---|")
    for i, ((m, p), sec) in enumerate(zip(follo_sections(), FOLLO_SECTIONS), 1):
        print(f"| {i} | {sec[0]} | {sec[1]:.0f} | {sec[3]:.2f} | {sec[4]:.0f} | {sec[5]:.2f} | {m:.2f} | {p:.2f} | {p / m:.2f} |")
    print("\n| Rock input | psi | Weighted measured (mm/rev) | Weighted predicted (mm/rev) | RMS of ln(pred/meas) | Correlation of ln(pred/meas) with UCS |")
    print("|---|---|---|---|---|---|")
    for mean_rock in (False, True):
        for psi in (-0.1, -0.15):
            wmeas, wpred, rms, r = _summary(follo_sections(psi, mean_rock))
            label = "tunnel-mean UCS and BTS" if mean_rock else "section UCS and BTS"
            print(f"| {label} | {psi} | {wmeas:.2f} | {wpred:.2f} | {rms:.2f} | {r:+.2f} |")
    print("\n### Published averages\n")
    print("| Project | Machine | Average advance | Basis |")
    print("|---|---|---|---|")
    for row in REFERENCE_RATES:
        print("| " + " | ".join(row) + " |")
