"""Add the buildings along each scenario corridor to its scenario file: footprints from OS OpenMap Local, heights from
Environment Agency LIDAR, listed status from Historic England. All three are open under the Open Government Licence.

- OS OpenMap Local, tile TQ, layers Building and ImportantBuilding: https://api.os.uk/downloads/v1/products/OpenMapLocal
  (no key needed). Contains OS data (c) Crown copyright and database right 2026. Terraces are merged into blocks.
- Height: 90th percentile of DSM (first return) minus DTM inside the footprint, shrunk by 0.5 m, from the EA LIDAR
  Composite 1 m WCS services; at least 5 pixels and 2 m, otherwise an assumed 10 m. (c) Environment Agency copyright
  and/or database right.
- Listed buildings and scheduled monuments: Historic England National Heritage List for England, open FeatureServer;
  (c) Historic England 2026, contains OS data (c) Crown copyright 2026. A list entry joins a footprint when its point lies
  inside it or its polygon overlaps it by at least a quarter (or 50 m^2).

Selection: footprints within 60 m of the alignment polyline. Downloads are cached in models/scenarios/.cache/buildings.

Run:  uv run --no-project --with numpy --with shapely --with tifffile --with pyshp python models/scenarios/build_buildings.py
"""
from __future__ import annotations

import io
import json
import math
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import shapefile
import shapely
import tifffile
from shapely.geometry import LineString, Point, Polygon, shape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bgs  # noqa: E402

CACHE = HERE / ".cache" / "buildings"
UA = {"User-Agent": "tunnel-construction-simulation scenario builder"}
BUF, DEFAULT_H = 60.0, 10.0
SCENARIOS = {"london-farringdon-liverpool-street.json": "farr", "thames-plumstead-north-woolwich.json": "thames"}
OS_URL = "https://api.os.uk/downloads/v1/products/OpenMapLocal/downloads?area=TQ&format=ESRI%C2%AE+Shapefile&redirect"
WCS = {
    "dsm": ("https://environment.data.gov.uk/spatialdata/lidar-composite-digital-surface-model-first-return-dsm-1m/wcs",
            "df4e3ec3-315e-48aa-aaaf-b5ae74d7b2bb__Lidar_Composite_Elevation_FZ_DSM_1m"),
    "dtm": ("https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs",
            "13787b9a-26a4-4775-8523-806d13af58fc__Lidar_Composite_Elevation_DTM_1m"),
}
NHLE = "https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/ArcGIS/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer"
LICENCE = ("Buildings: OS OpenMap Local, contains OS data (c) Crown copyright and database right 2026; heights from Environment Agency "
           "LIDAR Composite 1 m DSM/DTM, (c) Environment Agency copyright and/or database right; listing from the National Heritage "
           "List for England, (c) Historic England 2026. All under the Open Government Licence v3.0.")


def get(url: str, path: Path, timeout: int = 600) -> Path:
    if not path.exists() or path.stat().st_size == 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            path.write_bytes(r.read())
    return path


def os_layer(name: str) -> Path:
    """Path stem of an OS OpenMap Local TQ layer (downloads the 220 MB zip once, keeps only the needed layers)."""
    stem = CACHE / "os" / f"TQ_{name}"
    if not Path(str(stem) + ".shp").exists():
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(OS_URL, headers=UA), timeout=1800).read()))
        for member in z.namelist():
            for layer in ("TQ_Building.", "TQ_ImportantBuilding."):
                if layer in member:
                    (CACHE / "os").mkdir(parents=True, exist_ok=True)
                    (CACHE / "os" / Path(member).name).write_bytes(z.read(member))
    return stem


def polygons(stem: Path, bbox: list[float]) -> list[tuple[Polygon, dict]]:
    out = []
    r = shapefile.Reader(str(stem))
    for sr in r.iterShapeRecords(bbox=bbox):
        pts, parts = sr.shape.points, list(sr.shape.parts) + [len(sr.shape.points)]
        rings = [pts[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]
        out.append((Polygon(rings[0], rings[1:]).buffer(0), sr.record.as_dict()))
    return out


def lidar(kind: str, bbox: list[float]) -> tuple[np.ndarray, float, float]:
    """Mosaic of 500 m WCS tiles covering bbox: array, x of the left edge, y of the top edge."""
    x0, y0 = int(bbox[0] // 500 * 500), int(bbox[1] // 500 * 500)
    x1, y1 = int(math.ceil(bbox[2] / 500) * 500), int(math.ceil(bbox[3] / 500) * 500)
    a = np.full((y1 - y0, x1 - x0), np.nan, np.float32)
    base, cov = WCS[kind]
    for x in range(x0, x1, 500):
        for y in range(y0, y1, 500):
            url = f"{base}?service=WCS&version=2.0.1&request=GetCoverage&CoverageId={cov}&format=image/tiff&subset=E({x},{x + 500})&subset=N({y},{y + 500})"
            t = tifffile.imread(get(url, CACHE / "lidar" / f"{kind}_{x}_{y}.tif")).astype(np.float32)
            t[t < -1000] = np.nan
            a[y1 - (y + 500):y1 - y, x - x0:x - x0 + 500] = t
    return a, x0, y1


def sample(g: Polygon, a: np.ndarray, x0: float, ytop: float):
    minx, miny, maxx, maxy = g.bounds
    c0, c1, r0, r1 = int(np.floor(minx - x0)), int(np.ceil(maxx - x0)), int(np.floor(ytop - maxy)), int(np.ceil(ytop - miny))
    if c0 < 0 or r0 < 0 or c1 > a.shape[1] or r1 > a.shape[0]:
        return None
    cc, rr = np.meshgrid(np.arange(c0, c1), np.arange(r0, r1))
    inner = g.buffer(-0.5)
    m = shapely.contains_xy(inner if not inner.is_empty and inner.area > 4 else g, x0 + cc + 0.5, ytop - rr - 0.5)
    return a[rr[m], cc[m]] if m.any() else None


def nhle(tag: str, bbox: list[float]) -> list[list]:
    layers = []
    for layer in (0, 3, 6):  # listed points, listed polygons, scheduled monuments
        url = (f"{NHLE}/{layer}/query?geometry={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&geometryType=esriGeometryEnvelope&inSR=27700"
               f"&outSR=27700&outFields=ListEntry,Name,Grade&f=geojson")
        feats = json.loads(get(url, CACHE / "nhle" / f"{tag}_L{layer}.geojson").read_text())["features"]
        layers.append([(shape(f["geometry"]).buffer(0) if layer else shape(f["geometry"]), f["properties"]) for f in feats if f["geometry"]])
    return layers


def building(g: Polygon, rec: dict, poly: list, dsm, dtm, heritage, important) -> dict:
    c = g.centroid
    ch, off = bgs.on_line(poly, c.x, c.y)
    co = np.array([bgs.on_line(poly, x, y) for x, y in g.exterior.coords])
    out = {"id": rec["ID"], "chainage": ch, "offset": off, "ch_min": round(float(co[:, 0].min()), 1), "ch_max": round(float(co[:, 0].max()), 1),
           "off_min": round(float(co[:, 1].min()), 1), "off_max": round(float(co[:, 1].max()), 1), "area": round(g.area, 0)}
    s, t = sample(g, *dsm), sample(g, *dtm)
    h, src = DEFAULT_H, "assumed"
    if s is not None and t is not None:
        ok = np.isfinite(s) & np.isfinite(t)
        if ok.sum() >= 5:
            p90 = float(np.percentile(s[ok] - t[ok], 90))
            out["ground_level"] = round(float(np.median(t[ok])), 2)
            if p90 >= 2.0:
                h, src = p90, "lidar"
    out["height"], out["height_source"] = round(h, 1), src
    pts, pls, sms = heritage
    hits = {}
    for p, pr in pts:
        if g.contains(p):
            hits[pr["ListEntry"]] = pr
    for pg, pr in pls:
        if pg.intersects(g):
            ia = pg.intersection(g).area
            if ia > 0.25 * min(pg.area, g.area) or ia > 50:
                hits[pr["ListEntry"]] = pr
    if hits:
        out["listed"] = sorted(([str(v["Grade"]), v["Name"]] for v in hits.values()), key=lambda x: ({"I": 0, "II*": 1}.get(x[0], 2), x[1]))
    sm = [pr["Name"] for pg, pr in sms if pg.intersects(g) and pg.intersection(g).area > 0.1 * g.area]
    if sm:
        out["scheduled_monument"] = sm
    names = [r["DISTNAME"] for pg, r in important if pg.intersects(g) and pg.intersection(g).area > 0.3 * g.area]
    if names:
        out["name"] = names[0]
    return out


def run() -> None:
    for fname, tag in SCENARIOS.items():
        path = HERE / fname
        data = json.loads(path.read_text(encoding="utf-8"))
        al = data["alignment"]
        poly = al.get("polyline_bng") or [[al["start"]["E"], al["start"]["N"]], [al["end"]["E"], al["end"]["N"]]]
        corridor = LineString(poly).buffer(BUF)
        bbox = list(corridor.bounds)
        dsm, dtm = lidar("dsm", bbox), lidar("dtm", bbox)
        heritage = nhle(tag, bbox)
        important = polygons(os_layer("ImportantBuilding"), bbox)
        rows = [building(g, rec, poly, dsm, dtm, heritage, important)
                for g, rec in polygons(os_layer("Building"), bbox) if g.intersects(corridor)]
        rows.sort(key=lambda b: b["chainage"])
        data["buildings"] = rows
        data["buildings_meta"] = {"selection": f"OS OpenMap Local footprints within {BUF:.0f} m of the alignment", "licence": LICENCE,
                                  "fields": "chainage/offset of the centroid; ch_min..ch_max, off_min..off_max of the footprint (m); "
                                            "height (m, lidar or assumed 10 m); ground_level (m OD, LIDAR terrain); listed: [grade, name]",
                                  "build": "models/scenarios/build_buildings.py"}
        path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
        print(f"{fname}: {len(rows)} buildings, {sum(1 for r in rows if r['height_source'] == 'lidar')} with LIDAR heights, "
              f"{sum(1 for r in rows if 'listed' in r)} listed")


if __name__ == "__main__":
    run()
