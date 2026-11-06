"""Check the drill & blast round cycle against published Norwegian data.

Data (open sources, read and cited, not redistributed):
- Ulvin rail tunnel, FP2 E6/Dovrebanen (Veidekke), 120 m^2, 200 x 45 mm holes 5.2 m deep, three-boom Atlas Copco XE3 C30,
  105 h/week; 21 weeks of contractor reports, 578 m single face. Hours per round: drilling 4.54, charging 1.99, mucking
  2.90 (220.6 m^3 solid/h), downtime 2.46, machine scaling 2.52, manual scaling 0.77, clean-up mucking 0.76, bolting
  1.38, sprayed concrete 1.70; total 19.02 h, 639.8 m^3 solid, 5.09 m pull, 4.57 rounds a week. Messelt (2013), NMBU MSc,
  Table 4, p. 40: https://hdl.handle.net/11250/189202
- A contractor's estimates for a T10.5 round, median (P5-P95) in minutes: drilling 120 (90-360), charging 90 (60-180),
  ventilation 20 (10-30), mucking 90 (75-120), scaling 90 (60-180), sprayed concrete 60, bolting 90 (60-210).
  Tunnelbyggetid 2021 model case, 74.6 m^2, 109 charged holes, 5.5 m holes, three booms, 2 m bolt spacing, 8 cm sprayed
  concrete every round: 2,000 m in 41.43 weeks (about 48 m/week). Furunes & Strype (2022), NTNU MSc, Table 4.3, p. 110,
  and Table 3.2, p. 90: https://hdl.handle.net/11250/3020752
- Sprayed concrete time studies at Sollihoegda (E16, T9.5): gross 12.1, 13.1 and 8.2 m^3/h. Anderssen & Olsen (2022),
  NTNU MSc, Table 5-9: https://hdl.handle.net/11250/3013947
- Rates back-fitted to weekly logs (Statens vegvesen "Erfaringstall tunnel"): bolts 4.2-11.7 per h, sprayed concrete
  3.2-6.8 m^3/h. Lau (2020), NTNU MSc, Tables 11.13 and 12.16: https://hdl.handle.net/11250/2779502
- 101 production hours a week: Tunnelbyggetid guidance v2.0 (EBA, Statens vegvesen, Bane NOR, NTNU, 2024), p. 3-4:
  https://www.eba.no/siteassets/dokumenter/vei-og-jernbane/tunnellbyggetid/veileder-byggetidsmodell-april-2024-ver-2.0.pdf
- NFF Publication 14 (2004): about 12 h per round and about 50 m/week; Publication 23: 40-80 m/week per face.
- Jennemyr, L. (2020). Advancements in tunneling and underground excavation by drill & blast. Tunnel Business Magazine,
  15 Apr 2020: https://tunnelingonline.com/advancements-in-tunneling-and-underground-excavation-by-drill-blast/ .
  Practitioner statements: 80-100 holes/h from a charging truck with two pumps; an automated three-boom jumbo drills
  800-1,200 ft/h with 20 ft rods.
- Kim, Y. & Lee, S.S. (2021). A study of the effects of geological conditions on Korean tunnel construction time using the
  updated NTNU drill and blast prediction model. Applied Sciences 11(21): 10096 (CC BY), Table 6:
  https://www.mdpi.com/2076-3417/11/21/10096 . NTNU-model output for a 77-82 m^2 road tunnel, minutes per round,
  support types 1-5: charging and blasting 88-119, ventilation 28, scaling 43-112, rig time and lost time 43-51.

Run:  uv run python validation/drill_blast_cycle.py      (prints a Markdown summary)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunnelsim_models import drill_blast as db  # noqa: E402

ULVIN = {"holes": 200, "depth": 5.2, "reamed": 4, "muck": 639.8, "logged": {"Drilling": 4.54, "Charging": 1.99, "Mucking": 2.90,
         "Scaling (machine and manual)": 3.29, "Clean-up mucking": 0.76, "Bolting": 1.38, "Sprayed concrete": 1.70, "Downtime": 2.46},
         "total": 19.02, "pull": 5.09, "hours": 105.0, "rounds_per_week": 4.57}
JENNEMYR = {"charge_holes_per_h": (80, 100), "jumbo_ft_per_h": (800, 1200)}
NTNU_KOREA_MIN = {"Charging": (88, 119), "Ventilation": (28, 28), "Scaling": (43, 112)}  # Kim & Lee (2021) Table 6
T105_CONTRACTOR_MIN = {"Drilling": (120, 90, 360), "Charging": (90, 60, 180), "Ventilation": (20, 10, 30), "Mucking": (90, 75, 120),
                       "Scaling": (90, 60, 180), "Sprayed concrete": (60, None, None), "Bolting": (90, 60, 210)}
DEMO = {"width": 10.6, "wall": 2.9, "depth": 5.2, "overbreak": 0.12}


def ulvin_model() -> dict:
    """The model's rates applied to the Ulvin round's own quantities (holes, depth, reamed holes, muck)."""
    k = db.RATES
    drilled = ULVIN["holes"]
    drill = (ULVIN["depth"] * drilled / k["drill_m_per_min"] + drilled * k["move_min_per_hole"]) / k["booms"] / 60
    drill += ULVIN["reamed"] * k["reamer_min_per_hole"] / 60
    return {"Drilling": drill, "Charging": drilled * k["charge_min_per_hole"] / 60 + k["connect_blast_h"],
            "Mucking": ULVIN["muck"] / k["muck_m3_per_h"]}


def demo_cycles():
    rd = db.design_round(DEMO["width"], DEMO["wall"], DEMO["depth"])
    return rd, {c: db.round_cycle(rd, DEMO["width"], DEMO["wall"], c, overbreak=DEMO["overbreak"]) for c in ("I", "II", "III", "IV")}


if __name__ == "__main__":
    print("### Ulvin, the model's rates on the logged round\n")
    print("| Activity | Logged (h/round) | Model (h/round) | Model / logged |")
    print("|---|---|---|---|")
    m = ulvin_model()
    for a in ("Drilling", "Charging", "Mucking"):
        print(f"| {a} | {ULVIN['logged'][a]:.2f} | {m[a]:.2f} | {m[a] / ULVIN['logged'][a]:.2f} |")
    share = ULVIN["logged"]["Downtime"] / ULVIN["total"]
    print(f"\nDowntime {ULVIN['logged']['Downtime']} of {ULVIN['total']} h = {share * 100:.1f} % (model {db.RATES['downtime_fraction'] * 100:.0f} %). "
          f"Logged advance {ULVIN['rounds_per_week'] * ULVIN['pull']:.1f} m/week ({ULVIN['rounds_per_week']} rounds at {ULVIN['hours']:.0f} h; "
          f"the cycle alone would allow {ULVIN['hours'] / ULVIN['total']:.2f}).")
    rd, cycles = demo_cycles()
    print(f"\n### The demo's T10.5 round ({sum(1 for h in rd.holes if h.kind != 'empty')} charged holes, {rd.pull:.2f} m pull, "
          f"{rd.area:.1f} m^2), class II, against a contractor's T10.5 estimate\n")
    print("| Activity | Model (min) | Contractor median (min) | P5-P95 (min) |")
    print("|---|---|---|---|")
    steps = dict(cycles["II"].steps)
    model_min = {"Drilling": steps["Drilling"], "Charging": steps["Charging"] + steps["Connect and blast"], "Ventilation": steps["Ventilation"],
                 "Mucking": steps["Mucking"], "Scaling": steps["Scaling"], "Sprayed concrete": steps["Sprayed concrete"], "Bolting": steps["Bolting"]}
    for a, (med, lo, hi) in T105_CONTRACTOR_MIN.items():
        rng = f"{lo}-{hi}" if lo is not None else "-"
        print(f"| {a} | {model_min[a] * 60:.0f} | {med} | {rng} |")
    rest = steps["Survey and marking"] + steps["Downtime and waiting"]
    print(f"\nThe model also has survey {steps['Survey and marking'] * 60:.0f} min and downtime {steps['Downtime and waiting'] * 60:.0f} min "
          f"(together {rest:.1f} h), which the estimate does not list.")
    print(f"\n### Weekly advance at {db.HOURS_PER_WEEK:.0f} h/week\n")
    print("| Support class | Round (h) | Model (m/week) |")
    print("|---|---|---|")
    for c, cy in cycles.items():
        print(f"| {c} | {cy.total_h:.1f} | {cy.m_per_week:.0f} |")
    rd = demo_cycles()[0]
    drilled = [h for h in rd.holes if h.kind != "empty"]
    depth = rd.drill_metres / len(rd.holes)
    k = db.RATES
    jumbo_m_h = depth * len(drilled) / ((depth * len(drilled) / k["drill_m_per_min"] + len(drilled) * k["move_min_per_hole"]) / k["booms"]) * 60
    print("\n### Rates against practitioner statements and the NTNU model\n")
    print("| Rate | Demo | Source |")
    print("|---|---|---|")
    print(f"| Charging (holes/h) | {60 / k['charge_min_per_hole']:.0f} | {JENNEMYR['charge_holes_per_h'][0]}-{JENNEMYR['charge_holes_per_h'][1]} "
          "(Jennemyr 2020, two-pump truck) |")
    print(f"| Jumbo drilling, three booms (ft/h) | {jumbo_m_h * 3.281:.0f} | {JENNEMYR['jumbo_ft_per_h'][0]}-{JENNEMYR['jumbo_ft_per_h'][1]} "
          "(Jennemyr 2020) |")
    for a, (lo, hi) in NTNU_KOREA_MIN.items():
        print(f"| {a} (min/round) | {model_min[a] * 60:.0f} | {lo}-{hi} (NTNU model, Kim & Lee 2021) |".replace(f"{lo}-{lo} ", f"{lo} "))
    print("\nReferences: Tunnelbyggetid 2021 model case (74.6 m^2, about class II) about 48 m/week; NFF Publication 23 40-80 m/week per face; "
          "NFF Publication 14 about 12 h per round and about 50 m/week; logged Ulvin (120 m^2) 23 m/week at 105 h.")
