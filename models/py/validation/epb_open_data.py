"""Check the EPB thrust and torque models against open field data (CC BY 4.0, Mendeley Data).

Datasets (downloaded on first run into validation/.cache/, not committed):
- Changsha Metro Line 4 EPB, 294 averaged ring records: Zhang, Chen & Wu (2019), Automation in Construction 106:102860,
  data doi:10.17632/ndy5r67zxz.1. Columns used: To (cutterhead torque, MN m), Th (thrust, MN), Fp (chamber pressure,
  bar), C (cover, m), W (water-table depth, m), Gc (ground class). The unit and meaning of the columns are not stated
  with the data; they follow a paper by the same group on the same line (Geng et al., arXiv:2305.05128, Table 2),
  which also gives the machine: 6.28 m cutterhead, 35 % opening, 1.5 m rings (section 4.1, Table 1).
- Guangzhou-Foshan intercity railway EPB, 1,197 records in mixed soil and rock: Yan (2022), Data in Brief 108726,
  data doi:10.17632/cjwbjttf88.1. MF = thrust / cutterhead area (kPa), MT = torque / D^3 (kN m / m^3), UEP / LEP =
  upper / lower earth pressure (MPa), ground class 1 soft soil, 2 mostly soft soil, 3 mostly hard rock. The cutterhead
  diameter, 9.15 m, is recovered from the data (thrust = FPI x PR and torque = TPI x PR give the same D in every row).

Published operating points (numbers copied from the tables of open documents; no data files):
- Mashhad Metro Line 3 EPB, 9.4 m, opening 0.33: Farrokh, Lotfi & Dalir (2025), Analysis of EPB TBM torque calculation
  and component assessment, SETC-2025 pp. 105-113, doi:10.5937/SETC25011F, Table 4 (six points of face pressure, thrust,
  torque). Western tunnel: silty / gravelly sand, phi 35-40 deg, cover 15-20 m, groundwater 30-80 m deep (pp. 107-108).
  Which point is in which tunnel is not stated; the four points near 0.27 bar are reported separately.
- Sofia Metro Line 3 EPB (Herrenknecht S-1014), bore 9.39 m, shield 10.28 m long: Benli (2019), MSc thesis, Bogazici
  University, Tables 5.4 and 6.4-6.8 (mean thrust, torque and earth pressure per soil class and pressure bin, 3,996
  rings); crown cover 5.2-21.3 m, mean 13.0 m (p. 32). Earth pressure is read at sensor P1, 2.08 m below the shield
  top. Groundwater depth is not tabulated: results are given dry and with water 3 m below ground.

The defaults of the thrust and torque model were fitted here (mu_shield 0.17, mu_rim 0.07); the previous defaults
(0.3, 0.3) are printed alongside.

Run:  uv run python validation/epb_open_data.py      (prints a Markdown summary)
"""
from __future__ import annotations

import math
import statistics as st
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from tunnelsim_models.thrust_torque import cutterhead_torque, reference_installed, shield_thrust, tool_torque, vertical_stress  # noqa: E402
from xlsx_reader import read  # noqa: E402

CACHE = HERE / ".cache"
FILES = {
    "changsha.xlsx": "https://data.mendeley.com/public-files/datasets/ndy5r67zxz/files/900fe00b-d70a-41ea-aa59-9350b10143a0/file_downloaded",
    "guangfo.xlsx": "https://data.mendeley.com/public-files/datasets/cjwbjttf88/files/dea488f5-1a4d-468d-9a05-f3de5bf10ae3/file_downloaded",
}

# Machine and ground assumptions for Changsha (marked assumed in the docs). Weights and tool counts scale the urban
# EPB demo's values by (6.28 / 7.08)^2; unit weight 20 kN/m^3, K0 0.5, shield length 8.5 m.
CS = {"D": 6.28, "opening": 0.35, "L": 8.5, "gamma": 20.0, "k0": 0.5, "shield_weight": 3200, "backup_weight": 4700, "tools_thrust": 800,
      "tail_seal": 400, "n_tools": 70, "tool_force": 4.0, "seals": 250, "arms": 4, "arm_area": 0.5, "arm_radius": 2.0}


def fetch(name: str) -> Path:
    CACHE.mkdir(exist_ok=True)
    p = CACHE / name
    if not p.exists():
        req = urllib.request.Request(FILES[name], headers={"User-Agent": "tunnel-construction-simulation validation"})
        with urllib.request.urlopen(req, timeout=120) as r:
            p.write_bytes(r.read())
    return p


def changsha_rows() -> list[dict]:
    keys = ["ring", "S", "To", "Pr", "Th", "Fp", "Gf", "C", "W", "MSPT", "MDPT", "MUCS", "Gc", "St"]
    out = []
    for sheet in read(fetch("changsha.xlsx")).values():
        for r in sheet[1:]:
            if r and isinstance(r[0], float):
                out.append(dict(zip(keys, r)))
    return out


OLD = {"mu_shield": 0.3, "mu_rim": 0.3}  # defaults before this validation
NEW = {"mu_shield": 0.17, "mu_rim": 0.07}

MASHHAD = [(1.31, 34174, 8662), (1.30, 32085, 7903), (0.28, 8756, 2489), (0.278, 10054, 2943), (0.27, 12095, 1882), (0.265, 12457, 4523)]
SOFIA = [("CH", 0.25, 14190, 3.31), ("SM", 0.28, 20300, 2.20), ("CL", 0.26, 15690, 1.77), ("CH", 0.77, 17270, 3.16), ("SM", 0.76, 20700, 3.25),
         ("CL", 0.86, 21200, 3.16), ("CH", 1.28, 23400, 3.45), ("SM", 1.22, 21900, 4.01), ("CL", 1.30, 24000, 2.97), ("CH", 1.73, 27400, 3.81),
         ("SM", 1.75, 29800, 3.95), ("CL", 1.58, 24200, 2.96), ("CH", 2.18, 33500, 4.54), ("SM", 2.30, 38400, 4.77)]
SOFIA_K0 = {"CH": 0.6, "CL": 0.55, "SM": 0.45}  # assumed, normally consolidated


def generic(d: float, length: float, axis_depth: float, gamma: float, p: float, k0: float, water: float, opening: float, mu: dict,
            rim_width: float = 0.5) -> tuple:
    """Thrust (kN) and torque (kNm) with the urban EPB demo's weights and tools scaled by (D / 7.08)^2."""
    s, r = (d / 7.08) ** 2, d / 2
    th = shield_thrust(d, length, axis_depth, gamma, p, water_depth=water, k0=k0, mu_shield=mu["mu_shield"], shield_weight=4000 * s,
                       tools=1000 * s, tail_seal=500 * s, backup_weight=6000 * s)
    sv = vertical_stress(axis_depth, gamma, water_depth=water)
    tq = cutterhead_torque(d, p, sv * (1 + k0) / 2, opening_ratio=opening, mu_rim=mu["mu_rim"], rim_width=rim_width, n_arms=4, arm_area=0.5,
                           arm_radius=0.32 * d, tools=tool_torque(round(80 * s), 4.0, r), seals=300 * s)
    return th.total, tq.total


def mashhad(mu: dict) -> list[tuple]:
    """(pressure bar, thrust ratio, torque ratio) per point; western-tunnel ground: phi 37 deg, cover 17.5 m, dry,
    gamma 20 (assumed), K0 = 1 - sin phi, shield length 10 m (assumed), rim width 0.7 m (cutterhead width, p. 108)."""
    k0 = 1 - math.sin(math.radians(37))
    out = []
    for pb, f, t in MASHHAD:
        th, tq = generic(9.4, 10.0, 17.5 + 4.7, 20.0, pb * 100, k0, math.inf, 0.33, mu, rim_width=0.7)
        out.append((pb, th / f, tq / t))
    return out


def sofia(mu: dict, water: float) -> list[tuple]:
    """(soil, pressure bar, thrust ratio, torque ratio); axis at the mean cover 13.0 m + R, gamma 19.5 (assumed), the
    sensor pressure moved to the axis with a 15 kN/m^3 chamber paste, opening 0.3 (assumed)."""
    d = 9.39
    out = []
    for soil, pb, f, t in SOFIA:
        p = pb * 100 + 15 * (d / 2 - 2.08)
        th, tq = generic(d, 10.28, 13.0 + d / 2, 19.5, p, SOFIA_K0[soil], water, 0.3, mu)
        out.append((soil, pb, th / f, tq / 1000 / t))
    return out


def predict(row: dict, mu_shield: float = 0.17, mu_rim: float = 0.07) -> tuple:
    r = CS["D"] / 2
    z, p = row["C"] + r, row["Fp"] * 100
    th = shield_thrust(CS["D"], CS["L"], z, CS["gamma"], p, water_depth=row["W"], k0=CS["k0"], mu_shield=mu_shield,
                       shield_weight=CS["shield_weight"], tools=CS["tools_thrust"], tail_seal=CS["tail_seal"], backup_weight=CS["backup_weight"])
    sv = vertical_stress(z, CS["gamma"], water_depth=row["W"])
    tq = cutterhead_torque(CS["D"], p, sv * (1 + CS["k0"]) / 2, opening_ratio=CS["opening"], mu_rim=mu_rim, n_arms=CS["arms"],
                           arm_area=CS["arm_area"], arm_radius=CS["arm_radius"], tools=tool_torque(CS["n_tools"], CS["tool_force"], r), seals=CS["seals"])
    return th, tq


def quart(xs: list[float]) -> tuple[float, float, float]:
    q = st.quantiles(xs, n=4)
    return q[0], st.median(xs), q[2]


def corr(a: list[float], b: list[float]) -> float:
    ma, mb = st.mean(a), st.mean(b)
    return sum((i - ma) * (j - mb) for i, j in zip(a, b)) / math.sqrt(sum((i - ma) ** 2 for i in a) * sum((j - mb) ** 2 for j in b))


def changsha(mu: dict = NEW) -> dict:
    rows = [r for r in changsha_rows() if r["Fp"] > 0 and r["C"] > 0]
    pred = [predict(r, **mu) for r in rows]
    out = {"n": len(rows), "classes": {}}
    for gc in (None, 1.0, 2.0, 3.0, 4.0):
        idx = [i for i, r in enumerate(rows) if gc is None or r["Gc"] == gc]
        out["classes"]["all" if gc is None else int(gc)] = {
            "n": len(idx),
            "thrust_ratio": quart([pred[i][0].total / 1000 / rows[i]["Th"] for i in idx]),
            "torque_ratio": quart([pred[i][1].total / 1000 / rows[i]["To"] for i in idx]),
        }
    out["thrust_measured"] = quart([r["Th"] for r in rows])
    out["torque_measured"] = quart([r["To"] for r in rows])
    out["thrust_predicted"] = quart([t.total / 1000 for t, _ in pred])
    out["torque_predicted"] = quart([q.total / 1000 for _, q in pred])
    out["corr_thrust"] = corr([r["Th"] for r in rows], [t.total for t, _ in pred])
    out["corr_torque"] = corr([r["To"] for r in rows], [q.total for _, q in pred])
    # shares of the predicted totals
    out["thrust_shares"] = {k: st.median(getattr(t, k) / t.total for t, _ in pred) for k in ("face", "shield", "tools", "tail_seal", "backup")}
    out["torque_shares"] = {k: st.median(getattr(q, k) / q.total for _, q in pred) for k in ("tools", "face", "rim", "back", "arms", "seals")}
    # friction factors that bring the median ratios to 1, all other terms unchanged
    fs = st.median((r["Th"] * 1000 - (t.total - t.shield)) / t.shield for r, (t, _) in zip(rows, pred))
    fr = st.median((r["To"] * 1000 - (q.total - q.rim)) / q.rim for r, (_, q) in zip(rows, pred))
    out["mu_shield_fit"], out["mu_rim_fit"] = mu["mu_shield"] * fs, mu["mu_rim"] * fr
    return out


def guangfo() -> dict:
    sheet = read(fetch("guangfo.xlsx"))["Sheet1"]
    rows = [r for r in sheet[3:] if r and isinstance(r[0], float) and len(r) > 29 and r[29]]
    d = 9.15
    area = math.pi * d * d / 4
    ref = reference_installed("epb", d)
    out = {"n": len(rows), "D": d, "installed_torque_range": ref["torque"], "classes": {}}
    for gc in (1.0, 2.0, 3.0):
        rs = [r for r in rows if r[29] == gc]
        out["classes"][int(gc)] = {
            "n": len(rs),
            "thrust_MN": quart([r[2] * area / 1000 for r in rs]),
            "torque_MNm": quart([r[3] * d**3 / 1000 for r in rs]),
            "alpha": quart([r[3] for r in rs]),  # T / D^3 in kN m / m^3
            "face_share": quart([(r[4] + r[5]) / 2 * 1000 / r[2] for r in rs]),  # mean earth pressure / (F / A)
            "advance": quart([r[1] for r in rs]),
        }
    return out


def fmt3(q: tuple) -> str:
    return f"{q[1]:.2f} ({q[0]:.2f}–{q[2]:.2f})"


if __name__ == "__main__":
    old, c = changsha(OLD), changsha(NEW)
    print("## Summary: median predicted / measured (interquartile or full range)\n")
    print("| Data | Thrust, old defaults | Thrust, new | Torque, old | Torque, new |\n|---|---|---|---|---|")
    print(f"| Changsha, {c['n']} rings | {fmt3(old['classes']['all']['thrust_ratio'])} | {fmt3(c['classes']['all']['thrust_ratio'])} | "
          f"{fmt3(old['classes']['all']['torque_ratio'])} | {fmt3(c['classes']['all']['torque_ratio'])} |")
    for label, sel in (("Mashhad, 1.3 bar (2 points)", lambda x: x[0] > 1), ("Mashhad, 0.27 bar (4 points)", lambda x: x[0] < 1)):
        o = [x for x in mashhad(OLD) if sel(x)]
        n = [x for x in mashhad(NEW) if sel(x)]
        rng = lambda xs: f"{st.median(xs):.2f} ({min(xs):.2f}–{max(xs):.2f})"
        print(f"| {label} | {rng([x[1] for x in o])} | {rng([x[1] for x in n])} | {rng([x[2] for x in o])} | {rng([x[2] for x in n])} |")
    for water, label in ((math.inf, "dry"), (3.0, "water 3 m below ground")):
        o, n = sofia(OLD, water), sofia(NEW, water)
        rng = lambda xs: f"{st.median(xs):.2f} ({min(xs):.2f}–{max(xs):.2f})"
        print(f"| Sofia, 14 bin means, {label} | {rng([x[2] for x in o])} | {rng([x[2] for x in n])} | {rng([x[3] for x in o])} | {rng([x[3] for x in n])} |")
    print(f"\n## Changsha Line 4 (n = {c['n']}, new defaults)\n")
    print("| Ground class | Rings | Thrust predicted / measured | Torque predicted / measured |\n|---|---|---|---|")
    for k, v in c["classes"].items():
        print(f"| {k} | {v['n']} | {fmt3(v['thrust_ratio'])} | {fmt3(v['torque_ratio'])} |")
    print(f"\nMeasured thrust {fmt3(c['thrust_measured'])} MN, predicted {fmt3(c['thrust_predicted'])} MN; "
          f"torque measured {fmt3(c['torque_measured'])} MN m, predicted {fmt3(c['torque_predicted'])} MN m.")
    print(f"Correlation ring by ring: thrust {c['corr_thrust']:.2f}, torque {c['corr_torque']:.2f}.")
    print("Predicted thrust shares: " + ", ".join(f"{k} {v:.0%}" for k, v in c["thrust_shares"].items()))
    print("Predicted torque shares: " + ", ".join(f"{k} {v:.0%}" for k, v in c["torque_shares"].items()))
    print(f"Friction coefficients that match the medians: shield {old['mu_shield_fit']:.3f}, rim {old['mu_rim_fit']:.3f} (fitted from the old defaults 0.3 / 0.3).")
    g = guangfo()
    print(f"\n## Guangzhou-Foshan (n = {g['n']}, D = {g['D']} m; installed EPB torque scaled to D: {g['installed_torque_range']})\n")
    print("| Class | Records | Thrust MN | Torque MN m | T / D³ kN m/m³ | Earth pressure × A / thrust | Advance mm/min |\n|---|---|---|---|---|---|---|")
    for k, v in g["classes"].items():
        print(f"| {k} | {v['n']} | {fmt3(v['thrust_MN'])} | {fmt3(v['torque_MNm'])} | {fmt3(v['alpha'])} | {fmt3(v['face_share'])} | {fmt3(v['advance'])} |")
