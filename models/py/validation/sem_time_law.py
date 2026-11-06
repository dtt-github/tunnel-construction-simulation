"""The SEM demo's Sulem convergence-law parameters against an independent fit at the Frejus road tunnel. Nothing is fitted.

The demo's weak-rock scenario uses Sulem et al. (1987) with parameters fitted to a claystone drift (D = 5.2 m) at the
Meuse/Haute-Marne URL: X = 0.885 D, T = 6 days, m = 5.7, n = 0.3 (Guayacan-Carrillo et al. 2016, Table 1).

Data (open, read and cited, not redistributed):
- de La Fuente, M., Sulem, J., Taherzadeh, R., Subrin, D. (2020). Tunneling in squeezing ground: effect of the
  excavation method. Rock Mechanics and Rock Engineering 53, doi:10.1007/s00603-019-01931-4. Free-access version on HAL:
  https://hal.science/hal-03119942 . Frejus road tunnel (squeezing calc-schist), section 4.1: the same law fitted to
  the convergence records of almost all sections with X = 10.5 m (0.9 D), m = 4.5, n = 0.3; T fitted per section,
  0.5-5 days along direction 2-4; section 23 (typical of zone A): T 3.3 and 1.9 days in two directions.

The comparison is the time factor 1 + m (1 - (T / (T + t))^n): convergence far behind the face as a multiple of the
instantaneous convergence.

Run:  uv run python validation/sem_time_law.py      (prints a Markdown summary)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunnelsim_models.sem import SULEM_EXAMPLE  # noqa: E402

DAYS = (1, 7, 30, 100, 365)
FREJUS = {"m": 4.5, "n": 0.3, "x_over_d": 0.9, "t_range": (0.5, 5.0), "t_section_23": (1.9, 3.3)}


def time_factor(t_days: float, t_ref: float, m: float, n: float) -> float:
    return 1 + m * (1 - (t_ref / (t_ref + t_days)) ** n)


if __name__ == "__main__":
    demo = SULEM_EXAMPLE
    print("### Sulem parameters\n")
    print("| | X / D | T (days) | m | n |")
    print("|---|---|---|---|---|")
    print(f"| Demo (Meuse/Haute-Marne claystone) | {demo['x_over_d']:.3f} | {demo['t_ref']:g} | {demo['m']:g} | {demo['n']:g} |")
    print(f"| Frejus road tunnel (de La Fuente et al. 2020) | {FREJUS['x_over_d']:g} | {FREJUS['t_range'][0]:g}-{FREJUS['t_range'][1]:g} "
          f"(section 23: {FREJUS['t_section_23'][0]:g}, {FREJUS['t_section_23'][1]:g}) | {FREJUS['m']:g} | {FREJUS['n']:g} |")
    print("\n### Convergence far behind the face, as a multiple of the instantaneous convergence\n")
    print("| Days | " + " | ".join(str(d) for d in DAYS) + " | Final |")
    print("|---|" + "---|" * (len(DAYS) + 1))
    print("| Demo | " + " | ".join(f"{time_factor(d, demo['t_ref'], demo['m'], demo['n']):.2f}" for d in DAYS) + f" | {1 + demo['m']:.1f} |")
    lo, hi = FREJUS["t_range"]
    band = [sorted((time_factor(d, lo, FREJUS["m"], FREJUS["n"]), time_factor(d, hi, FREJUS["m"], FREJUS["n"]))) for d in DAYS]
    print("| Frejus, T 0.5-5 days | " + " | ".join(f"{a:.2f}-{b:.2f}" for a, b in band) + f" | {1 + FREJUS['m']:.1f} |")
