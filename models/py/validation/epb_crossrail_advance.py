"""Check the EPB drive model (ring cycle and downtime, simulate_drive) against the Crossrail running-tunnel drives.

Data (open sources, read and cited, not redistributed):
- King, Thomas & Stenning (2017). Crossrail project: machine-driven tunnels on the Elizabeth line, London. Proc. ICE
  Civil Engineering 170(CE5), 31-38, doi:10.1680/jcien.16.00028; free PDF on the Crossrail Learning Legacy:
  https://learninglegacy.crossrail.co.uk/wp-content/uploads/2017/04/Machine-driven-tunnels-on-the-Elizabeth-line-London.pdf
  Table 3 (p. 37): days, rings/day including and excluding delays, best day and week per TBM. Text: seven segments plus
  a small key, 1.6 m, 300 mm, 6.2 m ID; two 12 h shifts a day, seven days a week (west: three 8 h shifts).
- Average ring build on Crossrail "around 32 minutes": Tunnels & Tunnelling, 25 Feb 2021, "Lord of the rings",
  https://www.tunnelsandtunnelling.com/?p=9006
- 12 m shield: Crossrail Learning Legacy, TBM station transits,
  https://learninglegacy.crossrail.co.uk/documents/tbm-station-transits/
- About 110 m a week under Hyde Park (drive X, London Clay): Wan et al. (2017), Geotechnique 67(5), p. 421.

The model's downtime distributions come from a 6.88 m metro EPB in Tabriz (Moosazadeh et al. 2018); push time per ring
is not published for Crossrail, so the advance speed is varied.

Run:  uv run python validation/epb_crossrail_advance.py      (prints a Markdown summary)
"""
from __future__ import annotations

import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunnelsim_models.utilisation import DriveSettings, simulate_drive  # noqa: E402

RING, BUILD = 1.6, 32.0
# King et al. Table 3, EPB drives: TBM, drive, total days, days excluding delays, rings/d incl., rings/d excl., best day, best week
TABLE3 = (("Phyllis", "X", 519, 358, 9.0, 13.1, 33, 179), ("Ada", "X", 522, 313, 8.9, 14.9, 38, 185),
          ("Elizabeth", "Y", 896, 362, 5.1, 12.5, 43, 169), ("Victoria", "Y", 895, 402, 5.5, 12.3, 59, 216),
          ("Ellie", "Z", 127, 94, 13.9, 18.7, 45, 186), ("Jessica", "Z", 172, 99, 9.8, 17.0, 30, 127),
          ("Ellie", "G", 69, 39, 7.6, 13.4, 29, 159), ("Jessica", "G", 42, 33, 12.4, 15.7, 27, 159))
SHIFTS = (("2x12h_maintenance_per_cycle", "2 x 12 h, maintenance in each cycle"), ("2x10h_plus_4h_maintenance", "2 x 10 h + 4 h maintenance shift"))


def forecast(shift: str, adv_mm_min: float, interventions: bool, runs: int = 20, days: int = 90) -> dict:
    rs = [simulate_drive(DriveSettings(ring_length=RING, boring_min=RING / (adv_mm_min / 1000), ring_build={"kind": "fixed", "value": BUILD},
                                       shift_pattern=shift, haulage="conveyor", interventions=interventions), days, seed) for seed in range(1, runs + 1)]
    return {"rings_day": st.mean(r.mean_m_per_day for r in rs) / RING, "best_day": st.median(r.best_day for r in rs) / RING,
            "best_week": st.median(r.best_week for r in rs) / RING, "util": st.mean(r.utilisation for r in rs)}


if __name__ == "__main__":
    print("### Crossrail EPB drives (King et al. 2017, Table 3; rings of 1.6 m)\n")
    print("| TBM | Drive | Days | Days without delays | Rings/day with delays | Rings/day without delays | Best day (rings) | Best week (rings) |")
    print("|---|---|---|---|---|---|---|---|")
    for t in TABLE3:
        print("| " + " | ".join(str(x) for x in t) + " |")
    xy = [t for t in TABLE3 if t[1] in "XY"]
    print(f"\nDrives X and Y: {min(t[5] for t in xy)}-{max(t[5] for t in xy)} rings a day without delays, "
          f"{min(t[4] for t in xy)}-{max(t[4] for t in xy)} with delays; days without delays {min(t[3] / t[2] for t in xy) * 100:.0f}-"
          f"{max(t[3] / t[2] for t in xy) * 100:.0f} % of the drive.")
    print("\n### The model, 20 runs of 90 days, 1.6 m rings, 32 min build, conveyor\n")
    print("| Shift pattern | Advance speed (mm/min) | Tool interventions | Rings/day | Best day (rings) | Best week (rings) | Utilisation |")
    print("|---|---|---|---|---|---|---|")
    for shift, label in SHIFTS:
        for adv in (60, 80):
            for iv in (False, True):
                f = forecast(shift, adv, iv)
                print(f"| {label} | {adv} | {'yes' if iv else 'no'} | {f['rings_day']:.1f} | {f['best_day']:.0f} | {f['best_week']:.0f} | {f['util'] * 100:.0f} % |")
