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
    print("\n### Published averages\n")
    print("| Project | Machine | Average advance | Basis |")
    print("|---|---|---|---|")
    for row in REFERENCE_RATES:
        print("| " + " | ".join(row) + " |")
