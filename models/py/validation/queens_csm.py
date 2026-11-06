"""Test the CSM penetration model, with psi back-analysed on Follo TBM1 (not refitted), on the Queens Water Tunnel.

Data (open sources, read and cited, not redistributed):
- Yagiz, S. (2006). A model for the prediction of tunnel boring machine performance. IAEG2006 paper 383, Geological
  Society of London, https://media.geolsoc.org.uk/iaeg2006/PAPERS/IAEG_383.PDF. Tables 2-4: ten stations of Queens Water
  Tunnel No. 3, stage 2 (New York) with UCS, BTS, fracture spacing and alpha angle, cutter load (short tons, 8.896 kN;
  thrust / 50 cutters), advance rate (m/h) and the original CSM model's own prediction (m/h). The column printed as
  "mm/rev" is the advance rate divided by the cutterhead speed in cm/rev (2.19 m/h at 8.3 rpm is 4.4 mm/rev), so
  penetration is taken from the advance rate and the rpm here.
- Khalighi & Diehl (1997), High performance TBM for Queens Water Tunnel No. 3, RETC, Robbins:
  https://robbinstbm.com/wp-content/uploads/2010/09/QueensWaterTunnel_RETC_1997.pdf. 7.06 m open TBM, 50 x 482.6 mm
  (19 in) cutters, 311 kN rated, 8.3 rpm, 15,550 kN thrust.

Cutter tip width and spacing are not published; the model defaults (19 mm, 85 mm) are used, as for Follo.

Run:  uv run python validation/queens_csm.py      (prints a Markdown table)
"""
from __future__ import annotations

import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunnelsim_models.csm import Cutter, penetration_for_normal_force  # noqa: E402

SHORT_TON_KN = 8.896
RPM = 8.3  # Khalighi & Diehl (1997)
# station (m), UCS MPa, BTS MPa, fracture spacing (m; ">1.60" as 1.61), alpha (deg), cutter load (short ton), advance m/h, source CSM m/h
STATIONS = ((269, 200, 9.3, 0.80, 25, 30, 2.19, 2.98), (280, 199, 9.3, 1.60, 21, 30, 2.12, 3.12), (301, 199, 9.1, 1.61, 20, 30, 1.88, 2.98),
            (473, 190, 9.0, 0.20, 42, 32, 2.81, 3.34), (600, 189, 9.0, 1.61, 40, 34, 2.20, 3.34), (929, 168, 9.8, 1.60, 41, 35, 2.37, 3.34),
            (989, 174, 9.9, 1.61, 35, 36, 2.34, 3.34), (1021, 178, 10.1, 0.40, 61, 29, 2.90, 2.50), (1026, 181, 10.1, 0.20, 55, 35, 3.04, 3.34),
            (1045, 184, 10.2, 0.40, 49, 32, 3.07, 3.34))


def run(psi: float) -> list[tuple]:
    out = []
    for s, ucs, bts, fs, alpha, load, rop, csm_rop in STATIONS:
        measured = rop * 1000 / (RPM * 60)
        predicted = penetration_for_normal_force(load * SHORT_TON_KN * 1000, ucs, bts, Cutter(psi=psi))
        out.append((s, ucs, bts, fs, load * SHORT_TON_KN, measured, predicted, csm_rop / rop))
    return out


def summary(ratios: list[float]) -> str:
    rms = math.sqrt(sum(math.log(r) ** 2 for r in ratios) / len(ratios))
    return f"median {st.median(ratios):.2f}, range {min(ratios):.2f}-{max(ratios):.2f}, RMS ln {rms:.2f}"


if __name__ == "__main__":
    rows = run(Cutter().psi)
    print("| Station (m) | UCS (MPa) | BTS (MPa) | Fracture spacing (m) | Cutter load (kN) | Measured (mm/rev) | Model, psi -0.1 (mm/rev) | Ratio |")
    print("|---|---|---|---|---|---|---|---|")
    for s, ucs, bts, fs, kn, m, p, _ in rows:
        print(f"| {s} | {ucs} | {bts} | {'>1.60' if fs > 1.6 else fs} | {kn:.0f} | {m:.2f} | {p:.2f} | {p / m:.2f} |")
    print(f"\nModel, psi -0.1 (Follo): {summary([r[6] / r[5] for r in rows])}")
    for psi in (0.0, 0.1):
        print(f"Model, psi {psi}: {summary([r[6] / r[5] for r in run(psi)])}")
    print(f"The source's own CSM run (Table 4): {summary([r[7] for r in rows])}")
    massive = [r[6] / r[5] for r in rows if r[3] >= 1.6]
    fractured = [r[6] / r[5] for r in rows if r[3] <= 0.4]
    print(f"Massive rock (spacing >= 1.6 m, {len(massive)} stations): {summary(massive)}; fractured (<= 0.4 m, {len(fractured)}): {summary(fractured)}")
