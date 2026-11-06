"""Test the Thames chalk settlement defaults (VL 0.25 %, K 0.5, second bore 1.2 x the first) on data not used to set them.

The defaults come from the 17 Plumstead - Woolwich sections of Cheng & Mikulski (2014); see settlement_open_data.py.
Nothing here is fitted.

Data (open sources, read and cited, not redistributed):
- Liew, A. (2016). Observations of tunnelling effects on a large diameter jointed concrete pipe, Crossrail Contract
  C310, North Woolwich, Newham, London. Crossrail Learning Legacy (free access):
  https://learninglegacy.crossrail.co.uk/documents/observations-tunnelling-effects-large-diameter-jointed-concrete-pipe-crossrail-contract-c310-north-woolwich-newham-london/
  Store Road Inlet, north of the river: the same drive H slurry shields (7.1 m), but not one of the 17 sections (those
  cover Plumstead - Woolwich only). Axis 14.1 m deep; 7 m made ground and alluvium over 3 m river terrace deposits;
  chalk (Haven Brow Beds) in the whole face. Surface line, Table 2 and text: westbound (first) Smax 9 mm, VL 0.32 %,
  K 0.40; eastbound (second) Smax 5 mm, VL 0.165 %, K 0.39, Smax 3 m off its centre line; both together 12 mm. The
  second bore's VL was about half the first, a trend "prevalent along this section". The distance between the tunnels
  is not given, so the combined trough is not computed.
- Wongsaroj, Borghi, Soga, Mair, Sugiyama, Hagiwara & Bowers (2006). Effect of TBM driving parameters on ground surface
  movements: Channel Tunnel Rail Link Contract 220. TC28, pp. 335-340 (ISSMGE library, open):
  https://www.issmge.org/uploads/publications/6/11/2005_044.pdf . 8.11 m EPBs in closed mode; Table 4, face in
  Thanet Sand over Upper Chalk: VL 0.28 % mean (0.18-0.53 %), K 0.43 mean (0.4-0.5). No section depths, so only the
  parameters are compared (a bracket: different machine type and a mixed face).

Run:  uv run python validation/settlement_chalk_independent.py      (prints a Markdown summary)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunnelsim_models.settlement import gaussian_trough  # noqa: E402

D, Z0 = 7.12, 14.1  # drive H shield (as in settlement_open_data.py); axis depth at the Store Road Inlet (Liew 2016)
VL, K, SECOND_RATIO = 0.25, 0.5, 1.2  # the Thames scenario defaults
MEASURED = (("Westbound, first bore", 9.0, 0.32, 0.40, 1.0), ("Eastbound, second bore", 5.0, 0.165, 0.39, SECOND_RATIO))


def smax_mm(vl_pct: float, k: float) -> float:
    return gaussian_trough(D, Z0, vl_pct / 100, k=k).s_max * 1000


if __name__ == "__main__":
    print("### Store Road Inlet, North Woolwich (Liew 2016), surface line, axis 14.1 m, chalk face\n")
    print("| Bore | Measured Smax (mm) | Model, defaults (mm) | Model / measured | Measured VL / K | Defaults VL / K |")
    print("|---|---|---|---|---|---|")
    for name, smax, vl, k, factor in MEASURED:
        pred = smax_mm(VL * factor, K)
        print(f"| {name} | {smax:g} | {pred:.1f} | {pred / smax:.2f} | {vl} % / {k} | {VL * factor:.2f} % / {K} |")
    print(f"\nWith the measured VL and K, the formula gives {smax_mm(0.32, 0.40):.1f} and {smax_mm(0.165, 0.39):.1f} mm "
          f"(checks the reading). With VL 0.25 % and K 0.40 the first bore would be {smax_mm(0.25, 0.40):.1f} mm.")
    print("Measured second / first bore VL: 0.52 (the defaults use 1.2).")
    print("\n### CTRL Contract 220, Thanet Sand over Upper Chalk (Wongsaroj et al. 2006, Table 4)\n")
    print("VL 0.28 % mean (0.18-0.53 %), K 0.43 mean (0.4-0.5), against the defaults VL 0.25 %, K 0.5.")
