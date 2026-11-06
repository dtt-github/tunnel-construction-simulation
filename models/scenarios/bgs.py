"""Shared helpers for the scenario builders: download borehole logs from the BGS AGS API, parse AGS4 groups, read the
stratigraphic tops of a hole, and place a hole on an alignment polyline.

BGS AGS API: https://agsapi.bgs.ac.uk (v7 ags_export, batches of 10 BGS_LOCA_IDs). Each download carries
FILE/BGSFileSet01/BGS_download_metadata.txt with its licence; the builders accept only Open Government Licence data.
"""
from __future__ import annotations

import csv
import io
import math
import urllib.request
import zipfile
from pathlib import Path

API = "https://agsapi.bgs.ac.uk/v7/ags_export/?bgs_loca_id="
UA = {"User-Agent": "tunnel-construction-simulation scenario builder"}


def parse(text: str, groups: dict) -> None:
    group, heading = None, []
    for row in csv.reader(io.StringIO(text)):
        if not row:
            continue
        if row[0] == "GROUP":
            group = row[1]
        elif row[0] == "HEADING":
            heading = row[1:]
        elif row[0] == "DATA" and group in groups:
            groups[group].append(dict(zip(heading, row[1:])))


def fetch(ids: list[str], cache: Path, tag: str, groups=("LOCA", "GEOL", "WSTG", "WSTD")) -> dict:
    """AGS groups for the holes (cached as <tag>_batchN.zip); stops unless every download is under the OGL."""
    cache.mkdir(exist_ok=True)
    out: dict[str, list[dict]] = {g: [] for g in groups}
    for i in range(0, len(ids), 10):
        batch = ids[i:i + 10]
        p = cache / (f"{tag}_batch{i // 10}.zip" if tag else f"batch{i // 10}.zip")
        if not p.exists():
            with urllib.request.urlopen(urllib.request.Request(API + ";".join(batch), headers=UA), timeout=180) as r:
                p.write_bytes(r.read())
        z = zipfile.ZipFile(p)
        for name in z.namelist():
            if name.lower().endswith(".ags"):
                parse(z.read(name).decode("utf-8", "replace"), out)
            elif name.endswith("BGS_download_metadata.txt") and "Open Government Licence" not in z.read(name).decode("utf-8", "replace"):
                raise SystemExit(f"{p.name}: download is not under the Open Government Licence")
    return out


def tops(groups: dict, loca: dict, codes: dict) -> dict:
    """Level (m above datum) of the first logged top of each mapped unit: ground level minus GEOL_TOP."""
    gl = float(loca["LOCA_GL"])
    out: dict[str, float] = {}
    rows = sorted((r for r in groups["GEOL"] if r["LOCA_ID"] == loca["LOCA_ID"]), key=lambda r: float(r["GEOL_TOP"]))
    for r in rows:
        code = codes.get(r["GEOL_GEOL"].split("/")[0])
        if code and code not in out:
            out[code] = round(gl - float(r["GEOL_TOP"]), 2)
    return out


def on_line(poly: list[list[float]], e: float, n: float) -> tuple[float, float]:
    """Chainage along the polyline of the nearest point, and the offset (positive to the right of the direction).
    Points beyond the ends are placed on the extension of the first or last segment (negative or > length)."""
    best, run, last = None, 0.0, len(poly) - 2
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(poly, poly[1:])):
        dx, dy = x1 - x0, y1 - y0
        seg = math.hypot(dx, dy)
        t = ((e - x0) * dx + (n - y0) * dy) / (seg * seg)
        t = max(0.0 if i > 0 else -math.inf, min(1.0 if i < last else math.inf, t))  # extend beyond the two ends
        px, py = x0 + t * dx, y0 + t * dy
        d = math.hypot(e - px, n - py)
        if best is None or d < best[0]:
            side = 1.0 if (dx * (n - y0) - dy * (e - x0)) < 0 else -1.0
            best = (d, run + t * seg, side * d)
        run += seg
    return round(best[1], 1), round(best[2], 1)


def length(poly: list[list[float]]) -> float:
    return sum(math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(poly, poly[1:]))
