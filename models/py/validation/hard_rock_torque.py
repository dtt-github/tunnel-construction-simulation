"""Cutterhead torque T = 0.3 D N F_r (CSM rolling force) against logged torque on two projects. Nothing is fitted.

At a logged thrust and penetration the model torque is 0.3 * D * thrust * (F_r / F_n), and the CSM ratio F_r / F_n
depends only on penetration and disc diameter, not on rock strength. So logged torque tests the torque formula even
where the rock strength along the drive is unknown.

Data (open sources, read and cited, not redistributed):
- Brenner Base Tunnel, three Herrenknecht double shields in Buendner schist, 19" discs: means over 500 m each from
  Maggio (2020), Politecnico di Torino (see brenner_csm.py).
- Tehran Metro Line 6 southern extension, 9.19 m Herrenknecht EPB (S-523) in open mode in limestone (UCS 50-120 MPa),
  17" discs: means of 457 records, thrust 15.8 MN, torque 2.2 MNm, penetration 3.5 mm/rev (median 3), 2.6 rpm.
  Samadi & Hassanpour (2024), Heliyon 10(11): e31773, Table 2 (CC BY-NC-ND): https://pmc.ncbi.nlm.nih.gov/articles/PMC11140792/
- Follo Line TBM1: the open thesis data (Hansen 2018, digital appendix F1) log thrust, speed and penetration, not torque.

Assumed: the share of the logged thrust lost to shield friction (0-15 % for the double shields, as at Follo; 0-30 % for
the EPB, whose shield is longer and loaded by the ground).

Run:  uv run python validation/hard_rock_torque.py      (prints a Markdown summary)
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunnelsim_models.csm import Cutter, cutter_forces, max_rpm, tbm_performance  # noqa: E402
from validation.brenner_csm import MACHINES as BRENNER  # noqa: E402

K = 0.3  # torque radius factor in tbm_performance (Rostami-Ozdemir)
# name: (diameter m, disc mm, thrust MN, torque MNm, penetration mm/rev, drag shares)
CASES = {name: (d, 482.6, f, t, p, (0.0, 0.15)) for name, (d, n, rpm, f, t, p) in BRENNER.items()}
CASES["Tehran TML6, EPB in open mode, 9.19 m"] = (9.19, 431.8, 15.8, 2.2, 3.5, (0.0, 0.3))
# demo machines: diameter, discs, default thrust kN, rpm, installed torque kNm, power kW (web/hard-rock)
DEMOS = {"Double shield": (9.9, 71, 18000.0, 5.1, 11115.0, 4550.0), "Gripper": (9.58, 58, 14750.0, 5.5, 8526.0, 3500.0)}
ZONES = (("Gneiss", 150, 10), ("Granite", 180, 12), ("Fault zone", 40, 4), ("Mica schist", 90, 7))  # web/hard-rock/main.js


def rolling_coefficient(pen_mm: float, disc_mm: float) -> float:
    f = cutter_forces(pen_mm, 100.0, 10.0, replace(Cutter(), diameter_mm=disc_mm))
    return f.rolling_n / f.normal_n


def ratios(d: float, disc: float, f: float, t: float, p: float, drags: tuple[float, ...]) -> list[float]:
    """Logged / model torque for each assumed drag share."""
    return [t / (K * d * f * (1 - dr) * rolling_coefficient(p, disc)) for dr in drags]


if __name__ == "__main__":
    print("### Logged against model torque\n")
    print("| Machine | Thrust (MN) | Penetration (mm/rev) | Logged torque (MNm) | Logged / model |")
    print("|---|---|---|---|---|")
    for name, (d, disc, f, t, p, drags) in CASES.items():
        r = ratios(d, disc, f, t, p, drags)
        print(f"| {name} | {f:.1f} | {p:.1f} | {t:.2f} | {min(r):.2f}-{max(r):.2f} |")
    print("\n### What half the torque would change in the demos (default thrust and speed)\n")
    print("| Demo | Zone | Now: penetration, limit, torque | Half the torque: penetration, limit, torque |")
    print("|---|---|---|---|")
    for m, (d, n, thrust, rpm, tq, pw) in DEMOS.items():
        c = replace(Cutter(), spacing_mm=1000 * d / 2 / n)
        for z, ucs, bts in ZONES:
            out = []
            for k in (K, K / 2):
                p = tbm_performance(thrust, min(rpm, max_rpm(d)), n, d, ucs, bts, cutter=c, torque_radius_factor=k,
                                    max_torque_knm=tq, max_power_kw=pw, max_penetration_mm=15.0)
                out.append(f"{p.penetration_mm_rev:.1f} mm/rev, {p.limited_by}, {p.cutterhead_torque_knm / 1000:.1f} MNm")
            print(f"| {m} | {z} | {out[0]} | {out[1]} |")
