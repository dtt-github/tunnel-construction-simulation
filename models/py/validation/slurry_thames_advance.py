"""Check the drive model (ring cycle and downtime, simulate_drive) against the Crossrail Thames Tunnel Mixshields.

Data (open sources, read and cited, not redistributed):
- King, Thomas & Stenning (2017), Proc. ICE Civil Engineering 170(CE5), doi:10.1680/jcien.16.00028, Table 3, drive H
  (Plumstead - North Woolwich, 7.12 m Mixshields): Sophia 392 days (217 without delays), 4.4 rings/d with delays, 7.9
  without, best day 16 rings, best week 91; Mary 367 days (171), 4.6 and 10.0, best day 17, best week 100. Free PDF:
  https://learninglegacy.crossrail.co.uk/wp-content/uploads/2017/04/Machine-driven-tunnels-on-the-Elizabeth-line-London.pdf
- Cheng & Mikulski (2014), Crossrail Learning Legacy, Ground settlement behaviour in chalk due to TBM excavations:
  "6 to 7 rings per day" on the first drive and "10 rings per day" on the second, put down to the learning curve; only
  one TBM worked at a time. https://learninglegacy.crossrail.co.uk/documents/ground-settlement-behaviour-in-chalk-due-to-tbm-excavations/
- Tunnels & Tunnelling (2014), Crossrail C310: maximum advance up to 80 mm/min, with 1,600 m^3/h of slurry to treat at
  that rate; flint 5-25 %; six filter presses. https://tunnelsandtunnelling.com/?p=7323
- Ring build "around 32 minutes" on Crossrail: Tunnels & Tunnelling, 25 Feb 2021, https://www.tunnelsandtunnelling.com/?p=9006

The downtime distributions come from a 6.88 m metro EPB (Moosazadeh et al. 2018); separation-plant stops are not modelled.

Run:  uv run python validation/slurry_thames_advance.py      (prints a Markdown summary)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from epb_crossrail_advance import forecast  # noqa: E402  (1.6 m rings, 32 min build, no train delays: slurry is pumped)

DRIVE_H = (("Sophia", 392, 217, 4.4, 7.9, 16, 91), ("Mary", 367, 171, 4.6, 10.0, 17, 100))

if __name__ == "__main__":
    print("### Crossrail Thames Tunnel, drive H (King et al. 2017, Table 3)\n")
    print("| TBM | Days | Days without delays | Rings/day with delays | Rings/day without delays | Best day (rings) | Best week (rings) |")
    print("|---|---|---|---|---|---|---|")
    for t in DRIVE_H:
        print("| " + " | ".join(str(x) for x in t) + " |")
    print("\n### The model, 20 runs of 90 days, 1.6 m rings, 32 min build, 2 x 12 h with maintenance in each cycle\n")
    print("| Advance speed (mm/min) | Tool interventions | Rings/day | Best day (rings) | Best week (rings) | Utilisation |")
    print("|---|---|---|---|---|---|")
    for adv in (40, 60, 80):
        for iv in (False, True):
            f = forecast("2x12h_maintenance_per_cycle", adv, iv)
            print(f"| {adv} | {'yes' if iv else 'no'} | {f['rings_day']:.1f} | {f['best_day']:.0f} | {f['best_week']:.0f} | {f['util'] * 100:.0f} % |")
