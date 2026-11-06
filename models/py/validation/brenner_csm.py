"""CSM penetration and cutterhead torque on the Brenner Base Tunnel double shields (calc-schist). Nothing is fitted.

Data (open sources, read and cited, not redistributed):
- Maggio, G. (2020). MSc thesis, Politecnico di Torino, Brenner Base Tunnel lot Mules 2-3:
  https://webthesis.biblio.polito.it/15216/1/tesi.pdf
  Tables 3.1 and 3.2: Herrenknecht double shields with 19" discs; S-1054 exploratory tunnel 6.85 m, 28 face + 5 gauge
  + 4 double centre discs; S-1071/1072 main tunnels 10.71 m, 46 face + 10 gauge + 4 double centre discs.
  Tables 4.1-4.19: logged means over the 500 m before the S-1071 stop (281 values each): head speed (rpm), main-cylinder
  thrust (MN), cutterhead torque (MNm), penetration (mm/rev). S-1071 bored pk 43+676 to 43+177, geomechanical zone 10
  (Table 2.2): Buendner schist (calc-schist 50 %, calc-phyllite 20 %, mica marble 25 %). The stretch ends where face
  instability stopped the machine. The thesis gives no rock strength for zone 10. S-1054 was logged over pk 15+590 to
  16+089 of the exploratory tunnel (its own chainage); its rock is not described.
- Giacomin, Maffucci & Paddeu (2022). Long and deep hard rock TBM tunnelling under the Alps, Brenner Base Tunnel,
  Italian section. TAC 2022 (open):
  https://www.tunnelcanada.ca/members/documents/2022/papers/SESO3I569Z2AV8KEI_Long_and_deep_hard_rock_TBM_Tunnelling_under_the_Alps_Brenner_Base_Tunnel_Italian_section_-_Giacomin_et_al.pdf
  Calc-schists, amphibolite and marble over the first 10 km: UCS 30-120 MPa. Table 2: main-tunnel machines 95 MN
  nominal and 210 MN exceptional thrust; text: auxiliary cylinders up to 200 MN on the last ring in single-shield mode.

Assumed: BTS = UCS / 10; the thrust reaching the cutters is the logged main-cylinder thrust, less 0 or 15 % shield drag
(15 % is Follo's 3.2 of 21.2 MN, Hansen 2018). Means of products are taken as products of means.

Run:  uv run python validation/brenner_csm.py      (prints a Markdown summary)
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunnelsim_models.csm import Cutter, cutter_forces, penetration_for_normal_force  # noqa: E402

DRAG = (0.0, 0.15)  # share of the main-cylinder thrust lost to shield drag (bracket)
# name: (diameter m, discs, rpm, thrust MN, torque MNm, penetration mm/rev), Maggio (2020) Tables 3.1-3.2 and 4.1-4.19
MACHINES = {
    "S-1054, exploratory, 6.85 m": (6.85, 28 + 5 + 8, 3.694, 6.116, 1.081, 10.837),
    "S-1071, main, 10.71 m": (10.71, 46 + 10 + 8, 2.747, 14.166, 3.234, 14.406),
    "S-1072, main, 10.71 m": (10.71, 46 + 10 + 8, 2.578, 13.317, 3.223, 15.902),
}
UCS_RANGE = (30.0, 120.0)  # MPa, Giacomin et al. (2022)
TORQUE_RADIUS_FACTOR = 0.3  # as in tbm_performance (Rostami-Ozdemir)


def cutter(d: float, n: int) -> Cutter:
    return replace(Cutter(), spacing_mm=1000 * d / 2 / n)  # spacing as in the Follo back-analysis


def ucs_for(pen_mm: float, thrust_mn: float, d: float, n: int) -> float:
    """UCS (MPa, BTS = UCS / 10) at which the Follo-fitted CSM gives the logged penetration."""
    lo, hi = 5.0, 400.0
    for _ in range(80):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if penetration_for_normal_force(thrust_mn * 1e6 / n, m, m / 10, cutter(d, n)) > pen_mm else (lo, m)
    return (lo + hi) / 2


def model_torque(d: float, n: int, thrust_mn: float, pen_mm: float) -> float:
    """Cutterhead torque (MNm) from the CSM rolling coefficient at the logged penetration; independent of UCS."""
    f = cutter_forces(pen_mm, 100.0, 10.0, cutter(d, n))
    return TORQUE_RADIUS_FACTOR * d * thrust_mn * f.rolling_n / f.normal_n


if __name__ == "__main__":
    print("### Penetration: rock strength the CSM needs (Follo psi, not refitted)\n")
    print("| Machine | Thrust (MN) | rpm | Logged penetration (mm/rev) | UCS that reproduces it, drag 0 / 15 % (MPa) |")
    print("|---|---|---|---|---|")
    for name, (d, n, rpm, f, t, p) in MACHINES.items():
        u = [ucs_for(p, f * (1 - dr), d, n) for dr in DRAG]
        print(f"| {name} | {f:.1f} | {rpm:.2f} | {p:.1f} | {u[0]:.0f} / {u[1]:.0f} |")
    print(f"\nPublished UCS for these rocks: {UCS_RANGE[0]:.0f}-{UCS_RANGE[1]:.0f} MPa. Within that range the CSM gives "
          "anything from over 30 down to 2-5 mm/rev on S-1071, so penetration is consistent but not tested.")
    print("\n### Torque: model against logged (independent of UCS)\n")
    print("| Machine | Logged torque (MNm) | Model, drag 0 / 15 % (MNm) | Logged / model |")
    print("|---|---|---|---|")
    for name, (d, n, rpm, f, t, p) in MACHINES.items():
        m = [model_torque(d, n, f * (1 - dr), p) for dr in DRAG]
        print(f"| {name} | {t:.2f} | {m[0]:.2f} / {m[1]:.2f} | {t / m[0]:.2f}-{t / m[1]:.2f} |")
