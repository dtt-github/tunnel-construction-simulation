"""Check the undrained ground response with an ageing sprayed-concrete ring against the crown settlement measured in
the Crossrail Farringdon platform tunnels (SEM enlargements in Lambeth Group and London Clay).

Data and parameters (Crossrail Learning Legacy, read and cited, not redistributed):
- Measured crown settlement, platform tunnels PTW and PTE: 10.3-16.5 mm and mean 13.5 / 13.7 mm outside the zone of
  concurrent compensation grouting; 12.8-18.9 mm, mean 15.9 / 16.4 mm inside it (about 2.5 mm from the grouting).
  Readings rose linearly until ring closure (3-5 days), decelerated for 3-5 more days, then stayed steady. The design 2D
  FE (Mohr-Coulomb, these design lines) gave 10 mm without grouting. Gakis, Grau & Schwind (2016), Tunnel deformations
  caused by compensation grouting at Crossrail Farringdon Station, Table 1, Table 4 and In-tunnel monitoring:
  https://learninglegacy.crossrail.co.uk/documents/tunnel-deformations-caused-compensation-grouting-crossrail-farringdon-station/
- Whole-ring settlement 2-3 mm in the 10.5-11.5 m Whitechapel enlargements in London Clay (crown 7-10 mm): Staerk,
  Jimenez Rangel & Wade, Analyses of convergence and utilisation of SCL-tunnels during excavation:
  https://learninglegacy.crossrail.co.uk/documents/analyses-convergence-utilisation-scl-tunnels-excavation/
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
face: u_final - u_free(x = 1 m) from the Vlachopoulos & Diederichs profile. That movement is the mean radial one; the
crown takes it times the Kirsch factor for the total-stress ratio at the axis (in undrained ground the crown follows the
vertical stress, so K0 0.6 and 1.2 nearly agree), plus 2-3 mm settlement of the whole ring (Whitechapel).

Run:  uv run python validation/sem_farringdon.py      (prints a Markdown summary)
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from tunnelsim_models.ground_response import ground_reaction, ldp  # noqa: E402
from tunnelsim_models.scenario import Scenario  # noqa: E402
from tunnelsim_models.sem import WHOLE_BODY_SETTLEMENT, crown_settlement, lining_interaction  # noqa: E402

SCENARIO = HERE.parent.parent / "scenarios" / "london-farringdon-liverpool-street.json"
D, R, NU, LINING, SURVEY_X, RATE = 11.0, 5.5, 0.495, 0.4, 1.0, 1.1 / 24
DESIGN = {"LC": (lambda z: 85 + 6.5 * z, lambda z: 40 + 3.7 * z), "LG": (lambda z: 95 + 10 * z, lambda z: 36 + 5.9 * z)}
MEASURED = (10.3, 16.5, 13.6)  # min, max, mean outside the concurrent compensation grouting (mm)
CROSSRAIL_FE = 10.0  # mm, design 2D FE without grouting


def ground(s: Scenario, ch: float) -> dict:
    f = s.face(ch, D)
    lc_top = next(l.top for l in s.column(ch) if l.unit == "LC")
    z = lc_top - s.axis_at(ch)
    clay = "LC" if f.unit_at_axis == "LC" else "LG"
    sv = f.gamma * f.axis_depth
    return {"ch": ch, "clay": clay, "z": z, "cu": DESIGN[clay][0](z) / 1000, "e": DESIGN[clay][1](z), "sv": sv, "u": f.u_axis,
            "shares": f.units_on_face}


def crown_mm(g: dict, k0: float, closure_x: float, whole_body: float = 0.0) -> tuple[float, float]:
    """(mean radial movement after the first survey, crown settlement with the Kirsch factor and whole-ring term), mm."""
    sh = k0 * (g["sv"] - g["u"]) + g["u"]
    p0 = (g["sv"] + sh) / 2000
    free = ground_reaction(p0, 0, R, g["e"], NU, 0.0, g["cu"])
    li = lining_interaction(p0, R, g["e"], NU, 0.0, g["cu"], LINING, closure_x, RATE, "kielder")
    u_survey = free.u * ldp(SURVEY_X, R, free.r_p)
    return max(li.u_final - u_survey, 0) * 1000, crown_settlement(li.u_final, u_survey, sh / g["sv"], NU, whole_body) * 1000


if __name__ == "__main__":
    s = Scenario.load(SCENARIO)
    closures = (5.0, 7.5, 10.0)
    wb = sum(WHOLE_BODY_SETTLEMENT) / 2
    print("| Scenario chainage | Clay at the axis | z below LC top (m) | cu (kPa) | E (MPa) | K0 | "
          + " | ".join(f"Ring closed {x:g} m back: mean radial / crown (mm)" for x in closures) + " |")
    print("|---" * (6 + len(closures)) + "|")
    rows = []
    for ch in range(360, 661, 60):
        g = ground(s, ch)
        for k0 in (0.6, 1.2):
            r = [crown_mm(g, k0, x, wb) for x in closures]
            rows.append((ch, k0, r))
            vals = " | ".join(f"{a:.1f} / {b:.1f}" for a, b in r)
            print(f"| {ch} | {g['clay']} | {g['z']:.1f} | {g['cu'] * 1000:.0f} | {g['e']:.0f} | {k0} | {vals} |")
    mid = [r[1][1] for _, k0, r in rows if k0 == 0.6]
    print(f"\nCrown settlement with the ring closed 7.5 m back, K0 0.6, whole ring {wb * 1000:.1f} mm: {min(mid):.1f}-{max(mid):.1f} mm.")
    print(f"Measured (outside compensation grouting): {MEASURED[0]}-{MEASURED[1]} mm, mean {MEASURED[2]} mm. Crossrail design FE: {CROSSRAIL_FE:.0f} mm.")
