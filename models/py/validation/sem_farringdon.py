"""Check the undrained ground response with an ageing sprayed-concrete ring against the crown settlement measured in
the Crossrail Farringdon platform tunnels (SEM enlargements in Lambeth Group and London Clay).

Data and parameters (Crossrail Learning Legacy, read and cited, not redistributed):
- Measured crown settlement, platform tunnels PTW and PTE: 10.3-18.9 mm; mean 13.5 / 13.7 mm outside the compensation
  grouting zone, 15.9 / 16.4 mm inside it. Gakis, Grau & Schwind (2016), Tunnel deformations caused by compensation
  grouting at Crossrail Farringdon Station, Table 1:
  https://learninglegacy.crossrail.co.uk/documents/tunnel-deformations-caused-compensation-grouting-crossrail-farringdon-station/
- Undrained design lines, z = depth below the top of the London Clay: London Clay cu = 85 + 6.5 z kPa, E = 40 + 3.7 z MPa;
  Lambeth Group cu = 95 + 10 z kPa, E = 36 + 5.9 z MPa; nu 0.495; K0 0.6 gave realistic deformations and 1.2 governed
  lining stress. Temporary sprayed concrete lining tunnels in Farringdon Crossrail Station, Table 1:
  https://learninglegacy.crossrail.co.uk/documents/temporary-sprayed-concrete-lining-tunnels-farringdon-crossrail-station/
- Ring closure 3-5 days after a monitoring section was installed, at 1.5-2 m/day (Gakis et al. 2016): about 5-10 m
  behind the face. Platform enlargements advanced at 1.1 m/day (Crossrail Farringdon Station SCL tunnels: delivering
  value through innovation and best practice, section 4.6). Primary lining 400 mm SFRC.
- Ground, depth and pore pressure along the line: the Farringdon - Liverpool Street scenario (BGS boreholes, OGL),
  scenario chainage 360-660 m.

Set-up: an 11 m circle (the 11.4 x 10.6 m section), Tresca ground (phi = 0, c = cu), p0 the mean of the total vertical
and horizontal stress at the axis. The ring is taken to carry load from closure; before that the open top-heading arch
counts as no support. The quantity compared is the crown movement after the first survey, one 1 m round behind the
face: u_final - u_free(x = 1 m) from the Vlachopoulos & Diederichs profile.

Run:  uv run python validation/sem_farringdon.py      (prints a Markdown summary)
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from tunnelsim_models.ground_response import ground_reaction, ldp  # noqa: E402
from tunnelsim_models.scenario import Scenario  # noqa: E402
from tunnelsim_models.sem import lining_interaction  # noqa: E402

SCENARIO = HERE.parent.parent / "scenarios" / "london-farringdon-liverpool-street.json"
D, R, NU, LINING, SURVEY_X, RATE = 11.0, 5.5, 0.495, 0.4, 1.0, 1.1 / 24
DESIGN = {"LC": (lambda z: 85 + 6.5 * z, lambda z: 40 + 3.7 * z), "LG": (lambda z: 95 + 10 * z, lambda z: 36 + 5.9 * z)}
MEASURED = (10.3, 18.9, 13.6)  # min, max, mean outside compensation grouting (mm)


def ground(s: Scenario, ch: float) -> dict:
    f = s.face(ch, D)
    lc_top = next(l.top for l in s.column(ch) if l.unit == "LC")
    z = lc_top - s.axis_at(ch)
    clay = "LC" if f.unit_at_axis == "LC" else "LG"
    sv = f.gamma * f.axis_depth
    return {"ch": ch, "clay": clay, "z": z, "cu": DESIGN[clay][0](z) / 1000, "e": DESIGN[clay][1](z), "sv": sv, "u": f.u_axis,
            "shares": f.units_on_face}


def crown_mm(g: dict, k0: float, closure_x: float) -> float:
    p0 = (g["sv"] + k0 * (g["sv"] - g["u"]) + g["u"]) / 2000
    free = ground_reaction(p0, 0, R, g["e"], NU, 0.0, g["cu"])
    li = lining_interaction(p0, R, g["e"], NU, 0.0, g["cu"], LINING, closure_x, RATE, "kielder")
    return (li.u_final - free.u * ldp(SURVEY_X, R, free.r_p)) * 1000


if __name__ == "__main__":
    s = Scenario.load(SCENARIO)
    closures = (1.0, 5.0, 7.5, 10.0)
    print("| Scenario chainage | Clay at the axis | z below LC top (m) | cu (kPa) | E (MPa) | K0 | "
          + " | ".join(f"Ring closed {x:g} m back (mm)" for x in closures) + " |")
    print("|---" * (6 + len(closures)) + "|")
    for ch in range(360, 661, 60):
        g = ground(s, ch)
        for k0 in (0.6, 1.2):
            vals = " | ".join(f"{max(crown_mm(g, k0, x), 0):.1f}" for x in closures)
            print(f"| {ch} | {g['clay']} | {g['z']:.1f} | {g['cu'] * 1000:.0f} | {g['e']:.0f} | {k0} | {vals} |")
    print(f"\nMeasured crown settlement: {MEASURED[0]}-{MEASURED[1]} mm, mean {MEASURED[2]} mm outside compensation grouting.")
