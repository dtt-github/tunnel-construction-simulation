# Ground scenarios

A scenario file describes the ground along a tunnel alignment. The demos load it to get the ground at the face as the drive advances. The format is JSON, identified as `"format": "tunnelsim-scenario/1"`.

- **Loader:** [`scenario.py`](../models/py/tunnelsim_models/scenario.py) and its JavaScript twin [`scenario.js`](../models/js/scenario.js), checked against shared test vectors.
- **Scenarios:** [`models/scenarios/`](../models/scenarios/)

## Format

| Key | Content |
|---|---|
| `format` | `"tunnelsim-scenario/1"` |
| `name`, `description`, `method` | Free text. `method` is the tunnelling method the scenario was built for. |
| `crs`, `datum` | Coordinate reference system of the coordinates and the datum of the levels (e.g. `EPSG:27700`, m OD). |
| `licence` | Licence and attribution of the data. |
| `units` | Soil and rock units, **in order from the top down**. See the table below. |
| `alignment` | `length` (m), `axis_level` as `[[chainage, level], …]`, optionally `diameter`, `start`, `end`, `source`. |
| `ground_surface` | `[[chainage, level], …]` |
| `groundwater` | `level`: the upper water table as `[[chainage, level], …]`. Optionally `deep_head`: the piezometric level of a lower aquifer. Also `source` and `notes`. |
| `boreholes` | `id`, `chainage`, `offset`, `ground_level`, optionally `base_level` (bottom of the hole), and `tops`: the level of the top of each unit logged in the hole. |

Each unit has these fields:

| Field | Meaning |
|---|---|
| `name`, `color` | Display name and colour (`#rrggbb`). |
| `gamma` | Bulk unit weight, kN/m³. |
| `phi`, `c` | Effective friction angle (degrees) and cohesion (kPa). |
| `k0` | Coefficient of earth pressure at rest. |
| `E` | Drained stiffness, kPa. |
| `water` | `"upper"` (default) or `"lower"`: which water system sets the pore pressure in the unit. |
| `pore_pressure_ratio` | Factor on the hydrostatic pore pressure, for under-drained clay. Default 1. |
| `source`, `assumed`, `notes` | Where the values come from, which of them are assumptions, and remarks. |

## How the loader reads the ground

- **Between boreholes:** each unit's top is interpolated linearly along the chainage, and held constant beyond the first and last borehole that define it.
- **Missing units:** a unit missing from a borehole that logs a deeper unit has zero thickness there. A unit below the bottom of a borehole is unknown there, so that borehole is skipped for it.
- **Ordering:** interpolated tops are kept in order, so no unit can rise above the unit over it.
- **Ground at the face**, for a face of diameter D at the axis level:
  - the units across the face and their shares;
  - the mean unit weight above the crown;
  - φ′, c′ and E averaged over the face height;
  - K0 of the unit at the axis;
  - cover and axis depth;
  - the pore pressure at the axis, from the unit's water system.

  Models that take a water depth get the depth of a water table that gives the same pore pressure.

## Scenario: Farringdon – Liverpool Street, London

[`london-farringdon-liverpool-street.json`](../models/scenarios/london-farringdon-liverpool-street.json), built by [`build_london.py`](../models/scenarios/build_london.py) from the BGS AGS API.

- **Corridor:** 2.13 km along the Elizabeth line, from E 531300 N 181780 to E 533420 N 181580 (British National Grid).
- **Boreholes:** 14 Crossrail ground-investigation holes held by the British Geological Survey (project 202002061142130, accession 121953), one about every 150 m within 120 m of the line.
  - Licence: Open Government Licence v3.0. *Contains British Geological Survey materials © UKRI 2026.* The stratigraphic codes are those of the Crossrail consultant's logs.
  - F27P was drilled from the railway cutting at Farringdon (ground 5.3 m OD), so it is replaced by F32R (street level, 14.5 m OD).
- **Ground:** Made Ground, alluvium in the Fleet and Walbrook valleys, River Terrace gravels, then London Clay. The base of the London Clay falls from about −2 m OD at Farringdon to about −23 m OD at Liverpool Street. Below it:
  - the Harwich Formation, east of chainage 950 m;
  - the Lambeth Group, 15–20 m thick;
  - the Thanet Sand;
  - the Chalk, whose top is at −27 to −53 m OD.

### Unit parameters

| Unit | γ (kN/m³) | φ′ / c′ | K0 | E (MPa) | Water | Source |
|---|---|---|---|---|---|---|
| Made Ground | 18 | 25° / 0 | 0.58 | 10 | upper | Crossrail Paddington design, Table 1 ([Chandegra & Kokkinou 2016](https://learninglegacy.crossrail.co.uk/documents/design-deep-cut-cover-crossrail-paddington-station-using-finite-element-method/)); c′ set to 0 |
| Alluvium | 17 | 20° / 0 | 0.6 | 5 | upper | Assumed. BGS describes it as soft, normally consolidated, with peat ([BGS Earthwise](https://earthwise.bgs.ac.uk/index.php/London_-_Applied_geology)) |
| River Terrace Deposits | 20 | 36° / 0 | 0.41 | 60 | upper | Paddington Table 1 |
| London Clay | 20 | 24° / 1 | 1.5 | 77.6 | upper × 0.9 | Paddington Table 1. K0 and pore pressure from [Wan et al. 2019](https://doi.org/10.1680/jgeot.17.P.309) (CC BY): design range 1.0–1.5, measured 1.9–2.4 at Hyde Park, pore pressure about 0.9 × hydrostatic |
| Harwich Formation | 20 | 33° / 0 | 1.0 | 80 | lower | Assumed, like Upnor sand. Part of the Chalk–Basal Sands aquifer ([Environment Agency 2022](https://www.gov.uk/government/publications/london-basin-chalk-aquifer-annual-status-report)) |
| Lambeth Group | 20.2 | 22° / 12 | 1.5 | 100 | lower | [BGS OR/13/006](https://nora.nerc.ac.uk/id/eprint/503110/): density 6.1.1, Reading clay strength Table 6.7. K0 (2.5 measured at Limehouse) and E assumed |
| Thanet Sand | 18.6 | 37° / 0 | 0.8 | 150 | lower | [Menkiti et al. 2015](https://learninglegacy.crossrail.co.uk/documents/geology-geotechnical-properties-thanet-sand-formation-update-crossrail-project-2/), section 4; K0 and E assumed |
| Chalk | 20 | 35° / 100 | 1.0 | 500 | lower | Assumed. UCS 1.25–5 MPa saturated (BGS Earthwise) |

The Crossrail Learning Legacy papers are read and cited only; their content is not redistributed.

### Groundwater

- **Upper water table:** 13 m OD at Farringdon to 9 m OD at Liverpool Street, from water strikes in the gravels in the logs.
- **Deep head** in the Lambeth Group, Thanet Sand and Chalk: −23 m OD, from rising-head strikes in 2009 (RT84, LW11A). The Environment Agency reports −30 to −35 m OD in central London in 2020–2022.
- **Caveat:** these are strike readings, not equilibrium levels.
- **Effect at the tunnel:** a tunnel in the Lambeth Group sees almost no pore pressure, because it is drained from below. One in the London Clay sees about 0.9 × the hydrostatic pressure of the upper water table.

### Alignment

The tunnel axis is assumed: −16 m OD at Farringdon to −19 m OD at Liverpool Street, for a 7.1 m machine. It lies inside the published depth of the running tunnels at Farringdon, about 25–35 m below ground ([Crossrail Learning Legacy](https://learninglegacy.crossrail.co.uk/documents/tunnelling-sand-farringdon-crossrail-station/)). With this alignment the face at Farringdon is 82–100 % Lambeth Group. The published share for the Farringdon tunnels is about 83–85 % ([Crossrail Learning Legacy](https://learninglegacy.crossrail.co.uk/documents/geotechnical-risk-management-for-sprayed-concrete-lining-tunnels-in-farringdon-crossrail-station/)).

### Limits

- **Assumed values:** the alignment, and several unit parameters (marked `assumed` in the file).
- **Uniform units:** the Lambeth Group's sub-units and sand channels, which can hold water under pressure, are averaged into one unit.
- **Groundwater:** water levels come from strike readings.
- **Coverage:** there is no borehole between chainage 640 and 965 m.
