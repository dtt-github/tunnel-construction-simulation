"""Test the drive model (simulate_drive) on a second slurry-shield project: the Betuweroute Sophia and PanKan tunnels.

Nothing here is fitted to these data. The day-to-day variation is the one fitted on the Crossrail EPBs.

Data (open sources, read and cited, not redistributed):
- Jonker, J.H. (2004). Boortunnels in de Betuweroute. Cement 2004(1), progress table ("Voortgangsprestaties"), open
  on the article page: https://www.cementonline.nl/artikelen/boortunnels-in-de-betuweroute
  Sophia tunnel (slurry, 4,240 m, Pleistocene sand) and PanKan tunnel (slurry, 1,640 m, sand with clay lenses),
  8.65 m inner diameter. Average m/day, tube 1 / tube 2: Sophia 9.6 / 15.2, PanKan 10 / 14.4; best day 36 m for both;
  best week 213 and 216 m; average ring build 41 min for both; average boring time per ring 38 and 52 min.
  Ring length 1.5 m (Sophia) and 1.8 m (PanKan), segment table of the same article. Both machines Herrenknecht slurry
  shields; Sophia's could bore and build at once, but most of the tunnel was bored discontinuously (boring, then
  building), as the model does. Sophia worked mostly seven days a week; PanKan five days on tube 1 and seven on tube 2.
  Tube 2 took 40 weeks (Sophia, 4,240 m) and 16 weeks (PanKan, 1,640 m): 15.1 and 14.6 m per calendar day, so the
  averages are per calendar day over the whole tube. Sophia tube 1 stood about twelve weeks for cutterhead repairs and
  PanKan tube 1 was paced by a dam it had to pass, so only tube 2 is compared.
- Shift pattern: not published for these drives. The Groene Hart slurry tunnel (same country, same years) bored
  "twenty hours a day, seven days a week", with the other four hours for preventive maintenance (Rijkswaterstaat 2007,
  symposium Levensduur en Onderhoud van de Groene Harttunnel, p. 6:
  https://open.rijkswaterstaat.nl/publish/pages/125614/symposium_levensduur_en_onderhoud_van_de_groene_harttunnel.pdf).
  Both patterns are run.
- Slurry pipe extensions: done during ring build (Mimura, Abe & Wada 1992, ISARC, "concurrently with segment assembly
  work"); 57.5 min by hand per 12 m of feed and discharge line.
  https://www.iaarc.org/publications/fulltext/Automatic_extension_%20robot_%20for_slurry_transport_pipes.PDF
  Against a 41 min ring build every 1.5-1.8 m, the excess is at most about 17 min per 12 m (2-3 min per ring), so it is
  left out.

Run:  uv run python validation/slurry_betuweroute_advance.py      (prints a Markdown table)
"""
from __future__ import annotations

import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunnelsim_models.utilisation import DAY_VARIATION_CROSSRAIL_EPB, DriveSettings, simulate_drive  # noqa: E402

# name, ring length (m), boring min per ring, ring build min, measured m/day tube 2, best day m, best week m
TUNNELS = (("Sophia", 1.5, 38, 41, 15.2, 36, 213), ("PanKan", 1.8, 52, 41, 14.4, 36, 216))
PATTERNS = (("2x10h_plus_4h_maintenance", "20 h + 4 h maintenance"), ("2x12h_maintenance_per_cycle", "24 h, maintenance each cycle"))
RUNS, DAYS = 20, 180


def run(ring, bore, build, pattern, interventions, variation):
    extra = DAY_VARIATION_CROSSRAIL_EPB if variation else {}
    rs = [simulate_drive(DriveSettings(ring_length=ring, boring_min=bore, ring_build={"kind": "fixed", "value": build},
                                       shift_pattern=pattern, interventions=interventions, **extra), days=DAYS, seed=s)
          for s in range(1, RUNS + 1)]
    return (st.mean(r.mean_m_per_day for r in rs), st.mean(r.best_day for r in rs), st.mean(r.best_week for r in rs),
            st.mean(r.utilisation for r in rs))


if __name__ == "__main__":
    print(f"{RUNS} runs of {DAYS} days, measured tube 2 in brackets\n")
    print("| Tunnel | Shift pattern | Tool interventions | Day variation | m/day | Ratio | Best day (m) | Best week (m) | Utilisation |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, ring, bore, build, mean, bday, bweek in TUNNELS:
        for pattern, label in PATTERNS:
            for iv in (False, True):
                for var in (False, True):
                    m, d, w, u = run(ring, bore, build, pattern, iv, var)
                    print(f"| {name} | {label} | {'yes' if iv else 'no'} | {'Crossrail' if var else 'none'} | {m:.1f} ({mean}) | "
                          f"{m / mean:.2f} | {d:.0f} ({bday}) | {w:.0f} ({bweek}) | {u * 100:.0f} % |")
