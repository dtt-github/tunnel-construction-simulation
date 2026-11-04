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


def predict(row: dict, mu_shield: float = 0.3, mu_rim: float = 0.3) -> tuple:
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


def changsha() -> dict:
    rows = [r for r in changsha_rows() if r["Fp"] > 0 and r["C"] > 0]
    pred = [predict(r) for r in rows]
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
    out["mu_shield_fit"], out["mu_rim_fit"] = 0.3 * fs, 0.3 * fr
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
    c = changsha()
    print(f"## Changsha Line 4 (n = {c['n']})\n")
    print("| Ground class | Rings | Thrust predicted / measured | Torque predicted / measured |\n|---|---|---|---|")
    for k, v in c["classes"].items():
        print(f"| {k} | {v['n']} | {fmt3(v['thrust_ratio'])} | {fmt3(v['torque_ratio'])} |")
    print(f"\nMeasured thrust {fmt3(c['thrust_measured'])} MN, predicted {fmt3(c['thrust_predicted'])} MN; "
          f"torque measured {fmt3(c['torque_measured'])} MN m, predicted {fmt3(c['torque_predicted'])} MN m.")
    print(f"Correlation ring by ring: thrust {c['corr_thrust']:.2f}, torque {c['corr_torque']:.2f}.")
    print("Predicted thrust shares: " + ", ".join(f"{k} {v:.0%}" for k, v in c["thrust_shares"].items()))
    print("Predicted torque shares: " + ", ".join(f"{k} {v:.0%}" for k, v in c["torque_shares"].items()))
    print(f"Friction coefficients that match the medians: shield {c['mu_shield_fit']:.2f} (default 0.3), rim {c['mu_rim_fit']:.2f} (default 0.3).")
    g = guangfo()
    print(f"\n## Guangzhou-Foshan (n = {g['n']}, D = {g['D']} m; installed EPB torque scaled to D: {g['installed_torque_range']})\n")
    print("| Class | Records | Thrust MN | Torque MN m | T / D³ kN m/m³ | Earth pressure × A / thrust | Advance mm/min |\n|---|---|---|---|---|---|---|")
    for k, v in g["classes"].items():
        print(f"| {k} | {v['n']} | {fmt3(v['thrust_MN'])} | {fmt3(v['torque_MNm'])} | {fmt3(v['alpha'])} | {fmt3(v['face_share'])} | {fmt3(v['advance'])} |")
