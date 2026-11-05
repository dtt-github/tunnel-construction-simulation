# Changelog

Notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions will be tagged from the first complete Phase 1 slice; until then, changes are grouped by date.

## [Unreleased]

### Added

- **Urban EPB demo** (Slice A, [live](https://dtt-github.github.io/tunnel-construction-simulation/web/epb/)):
  - a 7 m EPB laid out front to back, with an articulated shield and 16 pairs of thrust cylinders;
  - push and ring-build cycle with a universal 6 + key ring;
  - chamber pressure against the DAUB window, with automatic or manual screw control and foam conditioning;
  - thrust and torque breakdown;
  - surface settlement with Burland categories for buildings.
  - Assumptions and gaps are listed in its [realism checklist](docs/realism/epb-slice-a.md).
- **Ground scenarios and real London geology** ([format and sources](docs/SCENARIOS.md)):
  - a scenario file format (`tunnelsim-scenario/1`) and loader (Python + JavaScript): ground surface, upper water table and deep aquifer head, units interpolated between boreholes, the ground at the face;
  - the first scenario: 2.1 km of the Elizabeth line from Farringdon to Liverpool Street, built from 14 Crossrail boreholes held by the British Geological Survey (Open Government Licence) by `models/scenarios/build_london.py`, with unit parameters from open sources;
  - the EPB demo now drives through it by default, with a geological long section, ground, depth and water changing every 10 m; the illustrative ground stays selectable.
- **Segment lining:** the vertical load is now reduced by Terzaghi's formula (ITA 2000, Formula 2.2.1), and the lateral coefficient is checked at the active and at-rest ends of the ITA range; ring overstress raises an alarm.
- **Ground response against measured convergence** ([write-up](docs/validation/sem-convergence.md)): the Hoek–Brown, ground-reaction and LDP chain against 14 monitored sections of a headrace tunnel in weak flysch (Terron-Almenara & Panthi 2025, CC BY 4.0, via Zenodo 10.5281/zenodo.23040284). Every reading is reproduced within the installed support capacity; no defaults changed. Script: `models/py/validation/sem_convergence.py`.
- **Validation against open field data** ([write-up](docs/validation/epb-open-data.md)): the EPB thrust and torque models against 281 rings of Changsha Metro Line 4 and 1,197 records of the Guangzhou–Foshan railway (CC BY 4.0, Mendeley Data), and published operating points from Mashhad Line 3 and Sofia Line 3. Script: `models/py/validation/epb_open_data.py`.
- **Changed:** shield and rim friction defaults are now 0.17 and 0.07, fitted on Changsha; they were 0.3, illustrative. Thrust is within about ±25 % on three projects. The EPB and Mixshield thrust and torque bars drop accordingly.
- **Segment lining model** (Python + JavaScript, `lining`): ring forces by the elastic equation method (ITA WG2 2000, reproduces its Design Example 1) with Wood's joint reduction, jacking stress and bursting under the shoes, annulus grout volume and pressure window, taper. The EPB and Mixshield demos show a Segment lining panel with these checks.
- **Drill & blast road tunnel** (Slice E, `web/drill-blast/`):
  - a Norwegian T10.5 road tunnel driven round by round: survey, drilling with a three-boom jumbo, charging, blast, ventilation, scaling, mucking with a loader and trucks, bolting and sprayed concrete;
  - the face pattern and charges from published rules (Holmberg cut, Olofsson burden, smooth contour), with a "Norwegian practice" setting fitted to published hole counts;
  - support classes I–IV with reinforced ribs of sprayed concrete in the fault; half-barrels on unsprayed walls;
  - vibration at a house above against the SS 460 48 66 guide value, firing one hole or one row per delay;
  - New `drill_blast` model (Python + JavaScript); its realism checklist is [here](docs/realism/drill-blast-heading.md).
- Labels of hidden equipment are no longer shown in the hard-rock, SEM and drill & blast demos.
- **Urban slurry shield (Mixshield)** (Slice C, `web/slurry/`):
  - a 7.08 m Crossrail-class Mixshield built from the EPB page: submerged wall, air cushion over the working-chamber slurry, pressure bulkhead, jaw crusher at the suction, DN300 feed and discharge lines, ring of 7 segments + key;
  - support pressure held by the air regulator within ±10 kPa; discharge pump on level control or manual, with pump interlocks; circuit in bypass between pushes;
  - filter cake or penetration at the face from the bentonite yield point and the ground's d₁₀, with the share of support transferred;
  - discharge density, dry-mass balance against the theoretical, pipe velocities against the deposit limit.
  - New `slurry` model (Python + JavaScript); its realism checklist is [here](docs/realism/slurry-mixshield.md).
- **SEM / NATM heading** (Slice D, `web/sem/`):
  - top heading, bench and invert by FHWA ground class;
  - lattice girders, pipe canopies and a temporary invert in the fault zone, with ring closure within one diameter;
  - shotcrete stiffening with age;
  - lining load and safety from Oreste's method;
  - convergence monitoring with Crossrail trigger levels and the final-lining criterion.
  - New `sem` model (Python + JavaScript) for shotcrete ageing, lining interaction, sequence rules and the Sulem convergence law.
- **Ground response model** (Python + JavaScript):
  - equivalent Mohr–Coulomb parameters, ground reaction curve and longitudinal displacement profile;
  - squeezing classes;
  - support curves and equilibrium;
  - shield friction (screening estimate) and gripper bearing.
  - It reproduces the published worked examples.
  - In the hard-rock demos:
    - the fault zone now closes in;
    - the double shield reports skin friction against its installed thrust, with a jamming-risk alarm;
    - the gripper checks shoe pressure against rock-mass strength and steel-set equilibrium.
- **Hard-rock double shield TBM** in the same page (`?machine=double`):
  - Follo-class 9.9 m machine with telescopic, gripper and tail shields;
  - main and auxiliary thrust cylinders, segment rings built while boring, pea gravel and grout;
  - single-shield mode in the fault zone.
  - The page is split into shared parts (`common.js`) and one module per machine.
  - The double-shield class preset now carries the verified Follo values.
  - The downtime model counts regrips for double shields (a few minutes to 15–30 min).
- **Hard-rock open gripper TBM demo** (Slice B, `web/hard-rock/`), replacing the early prototype at `web/`:
  - flat disc cutterhead with buckets, muck ring and belt;
  - roof shield, main beam, grippers with propel cylinders and the regrip cycle;
  - rock bolts, mesh and ring beams at L1 and shotcrete at L2 by RMR class, with invert segments;
  - geology with a fault zone, cutting limits and downtime per stroke from the per-km model.
- **Hard-rock models:**
  - CSM drive with constant torque, then constant power;
  - gauge-cutter speed limit and penetration cap;
  - cutter wear from CAI, with cutter-change downtime;
  - RMR support classes;
  - utilisation as downtime per km (Farrokh 2018), reproducing the paper's worked example within 3 %.
- **Utilisation and downtime model** (Python + JavaScript, seeded and bit-identical random stream):
  - ring build, general activities, train delays and per-cycle maintenance from distributions fitted on a 6.88 m metro EPB (Moosazadeh et al. 2018);
  - published shift patterns and cutting-tool interventions;
  - check of best day, week and month against published EPB rates and the world record of the diameter class.
  - Wired into the EPB demo: live shifts and stoppages, and a 90-day forecast panel.
- Documentation index ([docs/README.md](docs/README.md)), this changelog, and a GitHub Actions workflow that runs the JavaScript and Python model tests on every push and pull request.

### Changed

- README rewritten:
  - live demo links and a screenshot;
  - current status, documentation map, roadmap summary.
- Model catalogue restructured into one section per model.

## 2026-11-04

### Added

- **Realism baseline.**
  - [Methods reference](docs/research/methods-reference.md): sourced cards for every tunnelling method (layout, support and lining, cycle, numbers, ground pairing).
  - Realism rules in the [roadmap](docs/ROADMAP.md).
- **Machine class presets** ([machine-classes.json](models/presets/machine-classes.json)): every field carries a source and a verified flag; a test enforces this.
- **Models** (Python reference + JavaScript twin + shared vectors):
  - face support: wedge-silo with a DAUB operating window;
  - EPB chamber pressure from a volume balance with foam conditioning, and the screw conveyor;
  - shield thrust and cutterhead torque components;
  - settlement extended with volume-loss components along the drive, method presets, twin tunnels and a longitudinal width.
- **Phase 0, GPU platform on the DGX Spark** ([results](phase0/RESULTS.md)):
  - Newton implicit-MPM benchmarks for face stability and an EPB chamber;
  - WebSocket particle streaming (TSP0);
  - TSR0 record and replay with a browser viewer.
- **Public demo site** on GitHub Pages.

### Changed

- The thrust and torque plausibility check uses a table of built machines with sources, instead of the Krause α·D³ band, which modern EPBs exceed.
- The replay viewer labels recorded values as recorded and states the limits of each run.
- The hard-rock prototype is labelled "being rebuilt" until it matches real machines.

### Removed

- References to private material from the public documentation.

## 2026-11-04: initial release

### Added

- Model library: CSM disc cutter, Hoek–Brown, Gaussian settlement and Burland categories.
- Hard-rock TBM browser prototype.
- Research and industry surveys.
