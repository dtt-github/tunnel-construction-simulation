"""Build the Thames crossing ground scenario (tunnelsim-scenario/1): Crossrail Thames Tunnel, Plumstead to North
Woolwich, from open BGS borehole data.

Boreholes: 15 Crossrail ground-investigation holes held by the British Geological Survey (project 202002061142130,
accession 121953), four of them drilled over the river (TRC1-4), downloaded through the BGS AGS API and licensed under
the Open Government Licence v3.0. Contains British Geological Survey materials (c) UKRI 2026. WP33R is left out: it was
drilled open-hole to 16.5 m, so its logged Thanet Sand top is 15 m too deep.

Line: the bored section of the Elizabeth line from OpenStreetMap (ways 1300523852, 1300523861, 1300523860,
1300523854, 1300523856, 1300523858, 14183867, tagged layer=-2), (c) OpenStreetMap contributors, ODbL; converted to
British National Grid with an affine fit to BGS index points (0.04 m RMS). Chainage from the Plumstead end. Its
length, 2.30 km, is shorter than the published "about 2.6 km"; the difference is not resolved.

Run:  python models/scenarios/build_thames.py      (writes thames-plumstead-north-woolwich.json next to this file)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bgs  # noqa: E402

OUT = HERE / "thames-plumstead-north-woolwich.json"
PREFIX = "202002061142130"
HOLES = {  # Crossrail hole id -> BGS_LOCA_ID suffix
    "WP117R": "1599", "WP45R": "1514", "WP116R": "1598", "WP41R": "1510", "WP115R": "1596", "WP38R": "1507",
    "WP4R": "1474", "WP113R": "1594", "WP1R": "1471", "TRC4": "1396", "TRC3": "1395", "TRC2": "1394", "TRC1": "1393",
    "NW63R": "589", "NW15R": "539",
}
OVER_WATER = {"TRC1", "TRC2", "TRC3", "TRC4"}  # ground level of these logs is the river bed (mudline)
POLY = [[545108.3, 178880.7], [545027.9, 178886.0], [544961.4, 178894.9], [544914.2, 178902.7], [544872.3, 178911.2], [544826.6, 178918.1],
        [544701.3, 178939.4], [544645.8, 178947.0], [544604.6, 178949.4], [544431.7, 178964.1], [544371.3, 178967.8], [544344.1, 178967.8],
        [544313.8, 178965.1], [544275.3, 178960.2], [544231.8, 178952.8], [544196.8, 178947.7], [544174.3, 178945.2], [544149.4, 178943.4],
        [544125.0, 178942.4], [544106.3, 178945.7], [544094.7, 178947.8], [543831.0, 179030.6], [543821.9, 179033.4], [543796.0, 179041.2],
        [543754.2, 179055.5], [543740.5, 179061.2], [543712.2, 179072.8], [543677.8, 179090.1], [543650.7, 179105.7], [543630.0, 179122.0],
        [543607.7, 179141.6], [543574.6, 179175.2], [543551.7, 179205.4], [543537.7, 179230.4], [543532.2, 179241.4], [543519.5, 179266.4],
        [543518.7, 179267.9], [543514.5, 179276.1], [543499.5, 179314.9], [543489.5, 179349.2], [543469.1, 179425.6], [543457.5, 179473.7],
        [543440.9, 179550.4], [543430.7, 179585.7], [543417.2, 179620.9], [543393.3, 179669.0], [543367.6, 179712.2], [543339.2, 179752.7],
        [543322.6, 179773.3], [543311.8, 179784.9], [543301.5, 179794.3], [543298.1, 179797.2], [543287.5, 179806.3]]

PAD = "Chandegra & Kokkinou (2016), Crossrail Learning Legacy, Design of the deep cut-and-cover Crossrail Paddington Station, Table 1, https://learninglegacy.crossrail.co.uk/documents/design-deep-cut-cover-crossrail-paddington-station-using-finite-element-method/"
LAW = "Lawrence et al. (2015), Crossrail Learning Legacy, Variation in permeability and dewatering performance for part of the Crossrail route in east London, https://learninglegacy.crossrail.co.uk/documents/variation-permeability-dewatering-performance-part-crossrail-route-east-london-2/"
TS = "Menkiti et al. (2015), Crossrail Learning Legacy, Geology and geotechnical properties of the Thanet Sand Formation, https://learninglegacy.crossrail.co.uk/documents/geology-geotechnical-properties-thanet-sand-formation-update-crossrail-project-2/"
LG = "Entwisle et al. (2013), BGS OR/13/006, Engineering Geology of British Rocks and Soils: Lambeth Group, Table 6.7, https://nora.nerc.ac.uk/id/eprint/503110/"
VINCK = "Vinck et al. (2023), OSIG, Monotonic characterisation of low- to medium-density chalk, https://discovery.ucl.ac.uk/id/eprint/10200111/ (Seaford/Margate Chalk in Kent, analogue)"
TT = "Tunnels & Tunnelling (2014), Crossrail C310, https://tunnelsandtunnelling.com/?p=7323"

UNITS = {
    "MG": {"name": "Made Ground", "gamma": 18, "phi": 25, "c": 0, "k0": 0.58, "E": 10000, "d10": 1.0e-4, "color": "#8a7f72",
           "source": PAD, "assumed": ["d10"], "notes": "As the London scenario."},
    "AL": {"name": "Alluvium", "gamma": 17, "phi": 20, "c": 0, "k0": 0.6, "E": 5000, "d10": 2.0e-6, "color": "#6f7a5a",
           "source": LAW, "assumed": ["gamma", "phi", "c", "k0", "E", "d10"],
           "notes": "Clay, silt and peat; k 1e-9 to 1e-8 m/s (Lawrence 4.3). No open strength or grading; assumed."},
    "RTD": {"name": "River Terrace Deposits (gravel)", "gamma": 20, "phi": 36, "c": 0, "k0": 0.41, "E": 60000, "d10": 3.0e-4,
            "color": "#b59a62", "source": f"{PAD}; permeability {LAW}", "assumed": ["d10"],
            "notes": "Sandy gravel up to about 5 m thick, k about 1e-3 m/s (Lawrence 2.3, 4.3). d10 assumed for a sandy gravel; no grading in the open logs."},
    "LG": {"name": "Lambeth Group (Upnor Formation)", "gamma": 20, "phi": 33, "c": 8, "k0": 1.0, "E": 80000, "d10": 6.0e-5, "color": "#8c6a5a",
           "source": LG, "assumed": ["k0", "E", "d10"], "notes": "Upnor sand, shear box c' 8 kPa, phi' 33 deg (Table 6.7)."},
    "TS": {"name": "Thanet Sand Formation", "gamma": 18.6, "phi": 37, "c": 0, "k0": 0.8, "E": 150000, "d10": 3.0e-5, "color": "#c2ad7a",
           "source": TS, "assumed": ["k0", "E", "d10"],
           "notes": "Bulk density 1.88-1.9 Mg/m3, peak phi' 37-39 deg at 400-700 kPa, c' 0 (4.1-4.2); fines 0-70 % (3), d10 assumed for a silty fine sand."},
    "CK": {"name": "Chalk (Seaford Chalk Formation)", "gamma": 19, "phi": 31, "c": 20, "k0": 0.6, "E": 300000, "d10": 2.0e-6, "color": "#d9d6c8",
           "source": f"{LAW} (formation, grades, permeability); {VINCK} (phi', K0)", "assumed": ["gamma", "c", "E", "d10"],
           "notes": "Weak to moderately weak fractured chalk with flint bands (Seaford, CIRIA grades A to Dc/Dm). Critical-state phi' about 31 deg and K0 0.6 in "
                    "the analogue tests. Excavated chalk is mostly finer than 40 um (T&T 2014); d10 2 um assumed. The fractured mass, not the grains, "
                    "governs slurry loss at the face."},
}
CODES = {"MG": "MG", "AL": "AL", "RTD": "RTD", "LG": "LG", "TS": "TS", "CK": "CK"}

RIVER = {"from": 1840, "to": 2200, "level": [[1840, 3.2], [2200, 3.2]],
         "notes": "Mean high water about +3.2 m OD and mean low water about -2.0 m OD at the Environment Agency Charlton gauge 0003 (about 3 km "
                  "upstream; OGL), from one month of 15-minute readings, Oct-Nov 2026: estimates, not official MHWS/MLWS. "
                  "The tide changed the face pressure by about 0.8 bar on the drive (" + TT + ").",
         "source": "https://environment.data.gov.uk/flood-monitoring/id/stations/0003"}
GROUNDWATER = {
    # land: about +0.5 m OD at Plumstead and -1 to +1 m OD at North Woolwich, in hydraulic continuity through the gravel,
    # Thanet Sand and Chalk; under the river: the river level (mean high water)
    "level": [[0, 0.5], [1800, 0.5], [1840, 3.2], [2200, 3.2], [2240, 0.5], [2400, 0.5]],
    "source": LAW + "; " + TT,
    "notes": "Design groundwater 96.5-104.5 mATD, average 100.5 mATD (+0.5 m OD) (T&T). All units follow one water system. Tidal swing in the ground "
             "0.4-0.7 m at North Woolwich, under 0.1 m at Plumstead (Lawrence 3.1, 3.4).",
}
# Assumed vertical alignment: launch from the Plumstead portal box (about 20 m deep), down to about 12 m of cover under
# the river (published minimum 10-12 m, T&T), up to the North Woolwich portal.
ALIGNMENT = {
    "ends": ["Plumstead", "North Woolwich"],
    "length": 2302, "polyline_bng": POLY, "diameter": 7.08,
    "axis_level": [[0, -13.0], [400, -17.5], [1500, -21.5], [1900, -25.0], [2150, -25.0], [2302, -17.0]],
    "source": "Assumed. Cover under the river 10-12 m and support above 3 bar under the river (" + TT + "); the drive starts in gravel and "
              "Thanet Sand and meets Chalk about 100 m from launch, about 80 % in Chalk (" + TT + ").",
}


def build() -> dict:
    ids = [PREFIX + s for s in HOLES.values()]
    g = bgs.fetch(ids, HERE / ".cache", "thames")
    by = {r["BGS_LOCA_ID"]: r for r in g["LOCA"]}
    holes = []
    for hid, suffix in HOLES.items():
        loca = by[PREFIX + suffix]
        e, n, gl = float(loca["LOCA_NATE"]), float(loca["LOCA_NATN"]), float(loca["LOCA_GL"])
        ch, off = bgs.on_line(POLY, e, n)
        h = {"id": hid, "bgs_loca_id": PREFIX + suffix, "E": e, "N": n, "chainage": ch, "offset": off, "ground_level": gl,
             "base_level": round(gl - float(loca["LOCA_FDEP"]), 2), "tops": bgs.tops(g, loca, CODES)}
        if hid in OVER_WATER:
            h["over_water"] = True
        holes.append(h)
    holes.sort(key=lambda h: h["chainage"])
    return {
        "format": "tunnelsim-scenario/1",
        "name": "Thames crossing, Plumstead - North Woolwich (Crossrail Thames Tunnel), London",
        "description": "Ground along the 2.3 km bored Thames Tunnel of the Elizabeth line from 15 open BGS/Crossrail boreholes, four of them over the river.",
        "method": "slurry",
        "crs": "EPSG:27700",
        "datum": "m OD (ground levels of the logs; river-bed level for the over-water holes)",
        "licence": "Borehole data: Open Government Licence v3.0. Contains British Geological Survey materials (c) UKRI 2026. "
                   "Contains public sector information licensed under the Open Government Licence v3.0. Line (c) OpenStreetMap contributors, ODbL.",
        "units": UNITS,
        "alignment": ALIGNMENT,
        "ground_surface": [[h["chainage"], h["ground_level"]] for h in holes],
        "groundwater": GROUNDWATER,
        "river": RIVER,
        "boreholes": holes,
        "build": "models/scenarios/build_thames.py",
    }


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}: {len(data['boreholes'])} boreholes, length {bgs.length(POLY):.0f} m")
