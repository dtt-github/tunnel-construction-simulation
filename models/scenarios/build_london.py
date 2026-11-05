"""Build the Farringdon - Liverpool Street ground scenario (tunnelsim-scenario/1) from open BGS borehole data.

Boreholes: 14 Crossrail ground-investigation holes held by the British Geological Survey, project 202002061142130,
accession 121953, downloaded through the BGS AGS API (https://agsapi.bgs.ac.uk) and licensed under the Open Government
Licence v3.0. Contains British Geological Survey materials (c) UKRI 2026. The stratigraphic codes are those of the
Crossrail consultant's logs.

Corridor: straight line from E 531300 N 181780 (Farringdon) to E 533420 N 181580 (Liverpool Street), British National
Grid; one deep hole about every 150 m within 120 m of the line. F27P (drilled from the railway cutting at Farringdon,
ground level 5.3 m OD) is replaced by F32R (street level, 14.5 m OD, 11 m off the line).

Unit parameters and groundwater are set in UNITS and GROUNDWATER below, each with its source; values without an open
source are marked as assumed. The tunnel axis is an assumed vertical alignment inside the published depth range.

Run:  python models/scenarios/build_london.py      (writes london-farringdon-liverpool-street.json next to this file)
"""
from __future__ import annotations

import csv
import io
import json
import math
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
OUT = HERE / "london-farringdon-liverpool-street.json"
API = "https://agsapi.bgs.ac.uk/v7/ags_export/?bgs_loca_id="
PREFIX = "202002061142130"
HOLES = {  # Crossrail hole id -> BGS_LOCA_ID suffix
    "RT131": "870", "RT132R": "871", "F32R": "300", "F6": "272", "F14": "285", "RT48": "805", "RT83": "826",
    "RT84": "827", "L24": "486", "L27P": "490", "L30R": "496", "L47R": "511", "LW11A": "522", "LW9": "520",
}
A, B = (531300.0, 181780.0), (533420.0, 181580.0)

PAD = "Chandegra & Kokkinou (2016), Crossrail Learning Legacy, Design of the deep cut-and-cover Crossrail Paddington Station, Table 1, https://learninglegacy.crossrail.co.uk/documents/design-deep-cut-cover-crossrail-paddington-station-using-finite-element-method/"
LG = "Entwisle et al. (2013), BGS OR/13/006, Engineering Geology of British Rocks and Soils: Lambeth Group, https://nora.nerc.ac.uk/id/eprint/503110/"
TS = "Menkiti et al. (2015), Crossrail Learning Legacy, Geology and geotechnical properties of the Thanet Sand Formation, section 4, https://learninglegacy.crossrail.co.uk/documents/geology-geotechnical-properties-thanet-sand-formation-update-crossrail-project-2/"
WAN19 = "Wan, Standing, Potts & Burland (2019), Geotechnique 69(5):434-457, doi:10.1680/jgeot.17.P.309 (CC BY 4.0), Table 2 and p. 440"
EA22 = "Environment Agency (2022), Management of the London Basin Chalk Aquifer, status report, https://www.gov.uk/government/publications/london-basin-chalk-aquifer-annual-status-report (OGL)"
BGSLON = "BGS Earthwise, London - Applied geology, https://earthwise.bgs.ac.uk/index.php/London_-_Applied_geology"

# Parameters: gamma kN/m^3, phi deg, c kPa, k0, E kPa. "water": which water system the unit follows.
UNITS = {
    "MG": {"name": "Made Ground", "gamma": 18, "phi": 25, "c": 0, "k0": 0.58, "E": 10000, "color": "#8a7f72",
           "source": PAD, "notes": "PAD prints c' 20 kPa; 0 is used. K0 = K0nc 0.577."},
    "AL": {"name": "Alluvium", "gamma": 17, "phi": 20, "c": 0, "k0": 0.6, "E": 5000, "color": "#6f7a5a",
           "source": BGSLON, "assumed": ["gamma", "phi", "c", "k0", "E"],
           "notes": "Soft, normally consolidated, with peat (BGS); no open parameters found, values assumed."},
    "RTD": {"name": "River Terrace Deposits (gravel)", "gamma": 20, "phi": 36, "c": 0, "k0": 0.41, "E": 60000, "color": "#b59a62",
            "source": PAD, "notes": "E = E50,ref 60 MPa."},
    "LC": {"name": "London Clay Formation", "gamma": 20, "phi": 24, "c": 1, "k0": 1.5, "E": 77600, "color": "#6f6252",
           "pore_pressure_ratio": 0.9, "source": f"{PAD}; K0 and pore pressure: {WAN19}",
           "notes": "K0 1.5: top of the central-London design range 1.0-1.5 quoted in Wan et al.; measured 1.9-2.4 at 29-35 m (Hyde Park). "
                    "Pore pressure about 0.9 x hydrostatic at Hyde Park (under-drained), derived from Wan et al. Table 2. "
                    "cu = 83.1 + 7.4 z kPa (z below the top of the clay; Brosse et al. 2025, ISGSR, doi:10.3850/GRF-25280825_isgsr-185-P110-cd)."},
    "HF": {"name": "Harwich Formation (basal London Clay sands and gravels)", "gamma": 20, "phi": 33, "c": 0, "k0": 1.0, "E": 80000,
           "color": "#9a8a62", "water": "lower", "source": EA22, "assumed": ["gamma", "phi", "c", "k0", "E"],
           "notes": "Part of the Chalk-Basal Sands aquifer (EA); no open strength or stiffness, values assumed like Upnor sand (LG Table 6.7)."},
    "LG": {"name": "Lambeth Group", "gamma": 20.2, "phi": 22, "c": 12, "k0": 1.5, "E": 100000, "color": "#8c6a5a", "water": "lower",
           "source": LG, "assumed": ["k0", "E"],
           "notes": "Bulk density medians 2.04-2.08 Mg/m3 (6.1.1); c', phi' of Reading Formation clay, triaxial (Table 6.7). "
                    "Under-drained by the Thanet Sand and Chalk in central London (p. 186), but sand channels can hold high water pressure. "
                    "K0 2.5 measured at Limehouse (7.3.5); 1.5 assumed. Drained E assumed."},
    "TS": {"name": "Thanet Sand Formation", "gamma": 18.6, "phi": 37, "c": 0, "k0": 0.8, "E": 150000, "color": "#c2ad7a", "water": "lower",
           "source": TS, "assumed": ["k0", "E"],
           "notes": "Bulk density 1.88-1.9 Mg/m3, c' 0, peak phi' 37-39 deg at 400-700 kPa (4.1-4.2). K0 and E only in figures there; assumed."},
    "CK": {"name": "Chalk", "gamma": 20, "phi": 35, "c": 100, "k0": 1.0, "E": 500000, "color": "#d9d6c8", "water": "lower",
           "source": BGSLON, "assumed": ["gamma", "phi", "c", "k0", "E"],
           "notes": "UCS 1.25-5 MPa saturated (BGS); no open strength or stiffness parameters, values assumed."},
}
CODES = {"MG": "MG", "VOID": "MG", "AL": "AL", "RTD": "RTD", "LC": "LC", "HF": "HF", "LG": "LG", "TS": "TS", "CK": "CK"}

GROUNDWATER = {
    # upper water table from water strikes in the gravels: about 13 m OD at Farringdon (F9, F76) and 9 m OD at
    # Liverpool Street (L27P 9.4 m OD after 20 min, L35R 8.6 m OD)
    "level": [[0, 13.0], [2129, 9.0]],
    # deep head from rising-head strikes in the Lambeth Group / Thanet Sand in 2009: RT84 -23.4 m OD (60 min),
    # LW11A -23.2 m OD (90 min). The Environment Agency reports -30 to -35 m OD in central London in 2020-2022.
    "deep_head": [[0, -23.0], [2129, -23.0]],
    "source": "Water strikes in the BGS/Crossrail borehole logs (WSTG/WSTD); " + EA22,
    "notes": "Strike readings, not equilibrium levels. London Clay pore pressure 0.9 x hydrostatic on the upper table.",
}

# Assumed vertical alignment: axis -16 m OD at Farringdon to -19 m OD at Liverpool Street, inside the published depth
# of the running tunnels (about 25-35 m below ground) and mostly in the Lambeth Group at Farringdon (about 83-85 %).
ALIGNMENT = {
    "ends": ["Farringdon", "Liverpool Street"],
    "length": 2129, "start": {"E": A[0], "N": A[1]}, "end": {"E": B[0], "N": B[1]},
    "axis_level": [[0, -16.0], [2129, -19.0]], "diameter": 7.1,
    "source": "Assumed. Depth and geology at Farringdon: Crossrail Learning Legacy, Tunnelling in sand in Farringdon Crossrail Station, "
              "https://learninglegacy.crossrail.co.uk/documents/tunnelling-sand-farringdon-crossrail-station/; Geotechnical risk management for "
              "SCL tunnels in Farringdon, https://learninglegacy.crossrail.co.uk/documents/geotechnical-risk-management-for-sprayed-concrete-lining-tunnels-in-farringdon-crossrail-station/",
}


def fetch() -> dict:
    """AGS groups LOCA and GEOL for the holes, from the BGS AGS API in batches of 10 (cached)."""
    CACHE.mkdir(exist_ok=True)
    ids = [PREFIX + s for s in HOLES.values()]
    groups: dict[str, list[dict]] = {"LOCA": [], "GEOL": []}
    for i in range(0, len(ids), 10):
        batch = ids[i:i + 10]
        p = CACHE / f"batch{i // 10}.zip"
        if not p.exists():
            req = urllib.request.Request(API + ";".join(batch), headers={"User-Agent": "tunnel-construction-simulation scenario builder"})
            with urllib.request.urlopen(req, timeout=180) as r:
                p.write_bytes(r.read())
        z = zipfile.ZipFile(p)
        for name in z.namelist():
            if name.lower().endswith(".ags"):
                parse(z.read(name).decode("utf-8", "replace"), groups)
            elif name.endswith("BGS_download_metadata.txt") and "Open Government Licence" not in z.read(name).decode("utf-8", "replace"):
                raise SystemExit(f"{p.name}: download is not under the Open Government Licence")
    return groups


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


def build() -> dict:
    g = fetch()
    by_bgs = {r["BGS_LOCA_ID"]: r for r in g["LOCA"]}
    L = math.dist(A, B)
    ux = ((B[0] - A[0]) / L, (B[1] - A[1]) / L)
    holes = []
    for hid, suffix in HOLES.items():
        loca = by_bgs[PREFIX + suffix]
        e, n, gl = float(loca["LOCA_NATE"]), float(loca["LOCA_NATN"]), float(loca["LOCA_GL"])
        tops: dict[str, float] = {}
        rows = sorted((r for r in g["GEOL"] if r["LOCA_ID"] == loca["LOCA_ID"]), key=lambda r: float(r["GEOL_TOP"]))
        for r in rows:
            code = CODES.get(r["GEOL_GEOL"].split("/")[0])
            if code and code not in tops:
                tops[code] = round(gl - float(r["GEOL_TOP"]), 2)
        holes.append({"id": hid, "bgs_loca_id": PREFIX + suffix, "E": e, "N": n,
                      "chainage": round((e - A[0]) * ux[0] + (n - A[1]) * ux[1], 1),
                      "offset": round(-(e - A[0]) * ux[1] + (n - A[1]) * ux[0], 1), "ground_level": gl,
                      "base_level": round(gl - float(loca["LOCA_FDEP"]), 2), "tops": tops})
    holes.sort(key=lambda h: h["chainage"])
    return {
        "format": "tunnelsim-scenario/1",
        "name": "Farringdon - Liverpool Street (Elizabeth line corridor), London",
        "description": "Ground along a 2.1 km corridor of the Elizabeth line between Farringdon and Liverpool Street, from 14 open BGS/Crossrail boreholes.",
        "method": "epb",
        "crs": "EPSG:27700",
        "datum": "m OD (ground levels of the logs; datum not stated in the files, values fit m OD)",
        "licence": "Borehole data: Open Government Licence v3.0. Contains British Geological Survey materials (c) UKRI 2026. "
                   "Contains public sector information licensed under the Open Government Licence v3.0.",
        "units": UNITS,
        "alignment": ALIGNMENT,
        "ground_surface": [[h["chainage"], h["ground_level"]] for h in holes],
        "groundwater": GROUNDWATER,
        "boreholes": holes,
        "build": "models/scenarios/build_london.py",
    }


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}: {len(data['boreholes'])} boreholes")
