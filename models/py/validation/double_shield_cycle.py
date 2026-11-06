"""Check the double shield demo's assumed cycle values against open sources. Nothing is fitted.

The demo (web/hard-rock/double.js) assumes a 30 min ring build, a main stroke equal to the 1.8 m ring width, 150 MN
installed thrust (since this check: 210 MN double-shield mode, 200 MN single-shield mode) and 320 mm segments. Sources (open, read and cited, not redistributed):

- Comis, Younis & Goodfellow (2016). Concurrent segment lining and TBM design: a coordinated approach for tunneling
  success. WTC 2016 (Robbins): https://www.robbinstbm.com/wp-content/uploads/2017/04/5_SegmentDesign_WTC2016.pdf
  Table 1: three double shields of 6.1-6.5 m, main stroke 1,300 / 1,850 / 1,760 mm for rings of 1,400 / 1,500 /
  1,660 mm. Text: for radial key insertion the stroke should be the segment width plus 100-200 mm. Table 2, Job B
  (confidential, 1.66 m rings of 4 segments, the 6.53 m double shield of Table 1): 120 rings, 7,990 min of ring
  building over the first 199.2 m, learning curve included.
- COVEC Nepal general manager, quoted by NASTT (29 Aug 2018), Bheri Babai, 5.06 m Robbins double shield: ring erection
  "15 minutes in general"; in single-shield mode erection follows boring.
  https://nastt.org/2018/08/29/robbins-double-shield-himalayas/
- Maggio, G. (2020). MSc thesis, Politecnico di Torino (Brenner Base Tunnel, Mules 2-3):
  https://webthesis.biblio.polito.it/15216/1/tesi.pdf . Table 3.2, Herrenknecht double shields S-1071/1072, 10.71 m
  bore: main cylinders 95,000 kN total nominal thrust, 4,200 kW, segments 450 mm thick, 1,750 mm long, universal 6+1.
  Table 4.9, S-1071 logged main-cylinder thrust: mean 14.17 MN, median 14.01 MN, sd 2.19 MN, 281 values.
- Alfero (2022). MSc thesis, Politecnico di Torino: https://webthesis.biblio.polito.it/23141/1/tesi.pdf . Brenner
  exploratory double shield S-1054 (6.8 m): main stroke 1,700 mm for 1.5 m rings; gripper force about 37 MN.
- Melis Maynar, M. (2006). Revista de Obras Publicas 3472, pp. 36-37:
  https://quickclick.es/rop/pdf/publico/2006/2006_diciembre_3472_02.pdf . Guadarrama, four TBMs (1.6 m rings):
  Table 5 whole-drive rates 439-549 m/month; Table 7 machine time to 31 Dec 2004 in minutes. The machine type
  (9.5 m double shields) and the rock (granite and gneiss) come from the trade press, as in hard_rock_projects.py.

Run:  uv run python validation/double_shield_cycle.py      (prints a Markdown summary)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.hard_rock_projects import follo_advance  # noqa: E402

RING_W = 1.8  # m, Follo rings and the demo's stroke
DEMO = {"ring_build_min": 30.0, "regrip_min": 10.0, "thrust_installed_mn": 200.0, "segment_mm": 320}  # single-shield mode; 150 MN before this check
RING_BUILD = (  # (machine, minutes per ring, kind)
    ("Bheri Babai, 5.06 m", 15.0, "stated by the contractor"),
    ("Job B, 6.53 m, first 200 m", 7990 / 120, "logged, learning curve included"),
)
STROKES = (("6.1 m", 1.400, 1.300), ("6.2 m", 1.500, 1.850), ("6.53 m", 1.660, 1.760), ("Brenner S-1054, 6.8 m", 1.500, 1.700))
# Guadarrama Table 7 (minutes, to 31 Dec 2004, four machines): worked total, excavation and ring build, disc inspection
# and change, conveyors, other losses, not worked
GUADARRAMA = {"worked": 4_050_800, "boring_ring": 1_734_533, "discs": 1_053_702, "belts": 465_885, "other": 796_680,
              "not_worked": 1_367_920}


def with_ring_build(ring_build_min: float, regrip_min: float = DEMO["regrip_min"]) -> tuple[float, float, float]:
    """Follo case (normal organisation, conveyor): boring minutes per ring, advance (m/day) and utilisation with a ring
    build that is hidden while it is shorter than boring one ring (double-shield mode)."""
    u = follo_advance(regrip_min, "normal", "conveyor")
    bore_ring = u.h_per_km["boring"] / 1000 * RING_W * 60
    extra = max(ring_build_min - bore_ring, 0.0) * 1000 / RING_W / 60  # h/km of waiting for the ring
    total = u.total_h_per_km + extra
    return bore_ring, 24000 / total, u.h_per_km["boring"] / total


if __name__ == "__main__":
    bore_ring, adv, util = with_ring_build(DEMO["ring_build_min"])
    print("### Ring build (double-shield mode: built while boring)\n")
    print(f"Follo case: boring one 1.8 m ring takes {bore_ring:.0f} min, so a ring build up to that is hidden.\n")
    print("| Ring build | Minutes per ring | Kind | Follo case advance (m/day) | Utilisation (%) |")
    print("|---|---|---|---|---|")
    print(f"| Demo (assumed) | {DEMO['ring_build_min']:.0f} | assumption | {adv:.1f} | {util * 100:.0f} |")
    for name, m, kind in RING_BUILD:
        _, a, u = with_ring_build(m)
        print(f"| {name} | {m:.0f} | {kind} | {a:.1f} | {u * 100:.0f} |")
    print("\n### Main stroke against ring width\n")
    print("| Machine | Ring (m) | Main stroke (m) | Stroke - ring (m) |")
    print("|---|---|---|---|")
    for name, ring, stroke in STROKES:
        print(f"| {name} | {ring:.2f} | {stroke:.2f} | {stroke - ring:+.2f} |")
    print(f"| Demo | {RING_W:.2f} | {RING_W:.2f} | +0.00 |")
    g = GUADARRAMA
    cal = g["worked"] + g["not_worked"]
    u = follo_advance(DEMO["regrip_min"], "normal", "conveyor")
    print("\n### Time split: Guadarrama (four machines, to Dec 2004) and the model's Follo case\n")
    print("| Share | Guadarrama | Model, Follo case |")
    print("|---|---|---|")
    print(f"| Boring (with ring build) / all time | {g['boring_ring'] / cal * 100:.0f} % | {u.utilisation * 100:.0f} % |")
    print(f"| Disc inspection and change / all time | {g['discs'] / cal * 100:.0f} % | "
          f"{u.h_per_km['cutters'] / u.total_h_per_km * 100:.0f} % |")
    print(f"| Disc time / boring time | {g['discs'] / g['boring_ring']:.2f} | {u.h_per_km['cutters'] / u.h_per_km['boring']:.2f} |")
    print("\n### Thrust and segments (10.71 m Brenner double shields, Maggio 2020)\n")
    print(f"Main cylinders 95 MN nominal, 210 MN exceptional; auxiliary up to {DEMO['thrust_installed_mn']:.0f} MN in single-shield "
          "mode (Giacomin et al. 2022), now used by the demo (was 150 MN). Logged main thrust "
          "mean 14.2 MN (Follo default on the cutters 18.0 MN). Segments 450 mm against the demo's "
          f"{DEMO['segment_mm']} mm (Guadarrama, 9.5 m). Gripper force: about 37 MN on a 6.8 m machine only.")
