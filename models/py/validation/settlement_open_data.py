"""Check the Gaussian settlement trough (Peck; O'Reilly & New: Smax = 0.313 VL D^2 / i, i = K z0) against measured
Crossrail settlement, and derive the defaults the demos use.

Data (numbers quoted from the documents' tables; the documents are read and cited, not redistributed):
- Hyde Park greenfield site, Crossrail western running tunnels, 7.1 m EPBs in London Clay, axis depth about 34.5 m:
  Wan, Standing, Potts & Burland (2017), Geotechnique 67(5):420-445, doi:10.1680/jgeot.16.P.099, Table 1 and
  Fig. 10/15 (first bore, X-line greenfield: VL 0.78 %, Ky 0.44, Smax 8.3 mm; single fit Ky = 0.43), Table 2 / Fig. 13
  (second bore incremental VL 0.82-1.18 %); about 30 % of the final settlement has occurred above the cutterhead.
  Second bore (TBM2, eastbound, Table 2 / Fig. 13): incremental VL X 1.18 %, Y 0.82 %, extensometer line 0.82 % against
  0.78 / 0.44 / 0.48 % for the first bore on the same lines; Ky towards the first bore 0.467 / 0.419 / 0.435, away from
  it 0.33-0.435 / 0.314 / 0.292. The TBM1 axis is drawn 16.2 m from the TBM2 axis in Fig. 13 (read from the vector
  figure; dashed "TBM1 axis position" line).
- Crossrail Thames Tunnel C310, Plumstead - Woolwich, 7.12 m Mixshields in Seaford Chalk, Thanet Sand and river
  gravels: Cheng & Mikulski (2014), Crossrail Learning Legacy, Ground settlement behaviour in chalk due to TBM
  excavations, Table 1 (17 sections: depth, pillar spacing, Smax, VL after the first bore and after both, with K fixed
  at 0.5 in the back-analysis). The paper does not define its two VL columns ("WB" and "WB & EB") or whether the
  "distance between two tunnels" is centre to centre; both readings are tested below.

Run:  uv run python validation/settlement_open_data.py      (prints a Markdown summary)
"""
from __future__ import annotations

import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import math  # noqa: E402

from tunnelsim_models.settlement import gaussian_trough  # noqa: E402

# Cheng & Mikulski Table 1: (section, depth m, pillar spacing m, Smax mm, VL % first bore, VL % both bores, ground)
C310 = [(1, 12.0, 10, 5, 0.125, 0.125, "RTD"), (2, 12.5, 11, 5, 0.125, 0.125, "RTD"), (3, 16.0, 16, 6, 0.125, 0.150, "TS/Chalk"),
        (4, 18.0, 18, 6, 0.125, 0.125, "Chalk"), (5, 18.0, 20, 7, 0.250, 0.350, "Chalk"), (6, 18.5, 32.5, 9, 0.250, 0.300, "Chalk"),
        (7, 24.0, 30, 9, 0.250, 0.300, "Chalk"), (8, 19.6, 37, 4, 0.125, 0.125, "Chalk"), (9, 20.8, 19, 6, 0.125, 0.125, "Chalk"),
        (10, 21.3, 19, 2, 0.125, 0.125, "Chalk"), (11, 22.0, 18, 6, 0.250, 0.300, "Chalk"), (12, 23.0, 14, 5, 0.125, 0.250, "Chalk"),
        (13, 18.0, 15.5, 3, 0.100, 0.125, "TS/Chalk"), (14, 17.0, 14, 5, 0.100, 0.250, "TS/Chalk"), (15, 13.0, 17, 7, 0.250, 0.250, "TS"),
        (16, 13.0, 14, 10, 0.250, 0.350, "RTD/TS"), (17, 12.0, 15, 3, 0.100, 0.100, "TS")]
D_C310 = 7.12
HYDE_PARK = {"D": 7.1, "z0": 34.5, "VL": 0.0078, "K": 0.44, "Smax_mm": 8.3}
# Hyde Park lines (X, Y, extensometer): first-bore VL %, second-bore incremental VL %, Ky towards / away from the first bore
HYDE_PARK_TWIN = (("X", 0.78, 1.18, 0.467, (0.33 + 0.435) / 2), ("Y", 0.44, 0.82, 0.419, 0.314), ("Extensometer", 0.48, 0.82, 0.435, 0.292))
HYDE_PARK_SPACING = 16.2


def twin_smax(d: float, z0: float, pillar: float, vl1: float, vl2: float, k: float) -> float:
    """Largest settlement (m) of two Gaussian troughs `pillar` apart."""
    t1 = gaussian_trough(d, z0, vl1, k=k)
    t2 = gaussian_trough(d, z0, vl2, k=k) if vl2 > 0 else None
    xs = [-60 + 0.25 * i for i in range(int((pillar + 120) / 0.25))]
    return max(t1.settlement(x) + (t2.settlement(x - pillar) if t2 else 0.0) for x in xs)


def c310(k: float = 0.5) -> list[dict]:
    rows = []
    for s, z0, pillar, smax, vl1, vl12, ground in C310:
        pred = twin_smax(D_C310, z0, pillar, vl1 / 100, max(vl12 - vl1, 0) / 100, k) * 1000
        # volume loss per bore that reproduces the measured Smax with the same split, K fixed
        scale = smax / pred
        rows.append({"section": s, "z0": z0, "ground": ground, "measured": smax, "from_published_vl": pred, "ratio": scale,
                     "vl_fit": vl12 * scale})
    return rows


def c310_reading(second_vl: str, spacing: str, k: float = 0.5) -> list[float]:
    """Measured / predicted Smax per section. second_vl: "own" (the "WB & EB" column is the second bore's VL) or
    "increment" (second bore = "WB & EB" - "WB"); spacing: "centres" or "gap" (gap + D)."""
    out = []
    for s, z0, pillar, smax, vl1, vl12, ground in C310:
        vl2 = vl12 if second_vl == "own" else max(vl12 - vl1, 0)
        sp = pillar if spacing == "centres" else pillar + D_C310
        out.append(smax / (twin_smax(D_C310, z0, sp, vl1 / 100, vl2 / 100, k) * 1000))
    return out


def c310_defaults() -> dict:
    """First-bore VL that reproduces each Smax with the 'own' reading (published VL2/VL1 kept), and the medians."""
    v1, ratio, sp = [], [], []
    for (s, z0, pillar, smax, vl1, vl12, ground), r in zip(C310, c310_reading("own", "centres")):
        v1.append(vl1 * r)
        ratio.append(vl12 / vl1)
        sp.append(pillar)
    return {"vl1": st.median(v1), "vl1_range": (min(v1), max(v1)), "ratio": st.median(ratio), "ratio_range": (min(ratio), max(ratio)),
            "spacing": st.median(sp)}


def hyde_park() -> float:
    h = HYDE_PARK
    return gaussian_trough(h["D"], h["z0"], h["VL"], k=h["K"]).s_max * 1000


if __name__ == "__main__":
    print(f"Hyde Park, first bore: Smax from VL {HYDE_PARK['VL'] * 100:.2f} % and K {HYDE_PARK['K']} = {hyde_park():.1f} mm, measured {HYDE_PARK['Smax_mm']} mm.\n")
    rows = c310()
    print("| Section | Ground | Axis depth m | Smax measured mm | Smax from the published VL, K 0.5 mm | Measured / formula | VL (both bores) that fits, % |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['section']} | {r['ground']} | {r['z0']:.1f} | {r['measured']} | {r['from_published_vl']:.1f} | {r['ratio']:.1f} | {r['vl_fit']:.2f} |")
    ratios = [r["ratio"] for r in rows]
    print("\n### Reading of the Thames table\n")
    print("| Second-bore VL | Distance between tunnels | Measured / predicted Smax: median | Range | RMS of ln |")
    print("|---|---|---|---|---|")
    for vl_read, label_vl in (("increment", "WB & EB minus WB"), ("own", "the WB & EB value")):
        for sp_read, label_sp in (("centres", "centre to centre"), ("gap", "clear gap (+ D)")):
            r = c310_reading(vl_read, sp_read)
            rms = math.sqrt(sum(math.log(x) ** 2 for x in r) / len(r))
            print(f"| {label_vl} | {label_sp} | {st.median(r):.2f} | {min(r):.2f}-{max(r):.2f} | {rms:.2f} |")
    dflt = c310_defaults()
    print(f"\nWith the second bore at its own published VL, centre-to-centre spacing: first-bore VL that reproduces each Smax "
          f"median {dflt['vl1']:.2f} % (range {dflt['vl1_range'][0]:.2f}-{dflt['vl1_range'][1]:.2f} %); published VL2 / VL1 median "
          f"{dflt['ratio']:.2f} (range {dflt['ratio_range'][0]:.1f}-{dflt['ratio_range'][1]:.1f}); spacing median {dflt['spacing']:g} m.")
    print("\n### Hyde Park, second bore\n")
    print("| Line | First bore VL (%) | Second bore VL, incremental (%) | Ratio | Ky towards the first bore | Ky away from it |")
    print("|---|---|---|---|---|---|")
    for line, v1, v2, kin, kout in HYDE_PARK_TWIN:
        print(f"| {line} | {v1} | {v2} | {v2 / v1:.2f} | {kin} | {kout:.3f} |")
    hr = [v2 / v1 for _, v1, v2, _, _ in HYDE_PARK_TWIN]
    print(f"\nRatio median {st.median(hr):.2f} (range {min(hr):.2f}-{max(hr):.2f}); Ky towards {st.mean(t[3] for t in HYDE_PARK_TWIN):.2f}, "
          f"away {st.mean(t[4] for t in HYDE_PARK_TWIN):.2f} (means); spacing {HYDE_PARK_SPACING} m.")
    print(f"\nMeasured / formula: median {st.median(ratios):.2f}, range {min(ratios):.1f}-{max(ratios):.1f}. "
          f"VL that reproduces the measured Smax with K 0.5: median {st.median(r['vl_fit'] for r in rows):.2f} % "
          f"(range {min(r['vl_fit'] for r in rows):.2f}-{max(r['vl_fit'] for r in rows):.2f} %).")
