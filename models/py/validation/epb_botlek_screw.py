"""Check the EPB screw pressure profile against the Botlek screw gauges, and derive the defaults the model uses.

Data (open source, read and cited, not redistributed):
- Bezuijen, Talmon, Joustra & Grote (2005). Pressure gradients and muck properties at the face of an EPB.
  ISSMGE library (open): https://www.issmge.org/uploads/publications/6/11/2005_023.pdf . Botlek Rail Tunnel EPB,
  15 m screw at 23 degrees, gauges 2.5, 5 and 11.5 m from the entrance (Fig. 7). Figs 8 and 9: Ring 318 N and
  Ring 814 S, which the authors show as the two extremes (large drop at the entrance; small drop). Values read from the
  vector figures while boring, about +-0.1 bar: chamber gauge E5 at the screw inlet 3.35 / 3.1 bar; screw 2.05 / 2.6,
  1.95 / 2.45, 0.9 / 1.75 bar. Pressure "of 1 bar or more" was lost before the entrance on most rings (text, 3.2).

The defaults (entrance factor 0.85, decay length 16 m) are set between the two rings: this is a calibration on Botlek,
and no other open screw profile has been found to test it.

Run:  uv run python validation/epb_botlek_screw.py      (prints a Markdown summary)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunnelsim_models.epb_chamber import Screw  # noqa: E402

RINGS = (("318 N", 3.35, {2.5: 2.05, 5: 1.95, 11.5: 0.9}), ("814 S", 3.1, {2.5: 2.6, 5: 2.45, 11.5: 1.75}))
OLD = Screw(decay_length=3.0, entrance_factor=1.0)
NEW = Screw()


def fit(pc: float, g: dict) -> tuple[float, float]:
    """Decay length through the 2.5 and 11.5 m gauges, and the entrance factor it implies."""
    lam = (11.5 - 2.5) / math.log(g[2.5] / g[11.5])
    return lam, g[2.5] * math.exp(2.5 / lam) / pc


if __name__ == "__main__":
    print("| Ring | Gauge (m) | Measured (bar) | Old model, 3 m, no entrance drop | Model now, 16 m, 0.85 |")
    print("|---|---|---|---|---|")
    for name, pc, g in RINGS:
        for x, m in g.items():
            print(f"| {name} | {x:g} | {m:.2f} | {OLD.pressure_along(x, pc):.2f} ({OLD.pressure_along(x, pc) / m:.2f}x) | "
                  f"{NEW.pressure_along(x, pc):.2f} ({NEW.pressure_along(x, pc) / m:.2f}x) |")
    print()
    for name, pc, g in RINGS:
        lam, fe = fit(pc, g)
        print(f"Ring {name}: decay length {lam:.1f} m, entrance factor {fe:.2f} (chamber {pc} bar)")
