# Changelog

Notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions will be tagged from the first complete Phase 1 slice; until then, changes are grouped by date.

## [Unreleased]

### Added

- **Phase 2, WP0 and WP1: GPU ground physics groundwork** ([plan](docs/plans/phase2-mpm-face-chamber.md), [element tests](docs/validation/mpm-element-tests.md)):
  - `server/`: Newton MPM package with run records, a GPU-load check and a golden test reproducing Phase 0 exactly;
  - Newton's yield criterion read from the solver: √J2 ≤ s + μp. The Mohr–Coulomb mapping is μ = sin φ′ (plane strain, ψ = 0), confirmed by a Rankine active-wall test within ±6 % for φ′ ≤ 34°; Phase 0's μ = tan φ′ was not a valid match;
  - the at-rest state cannot come from the MPM (K 0.74–0.86, independent of ν); it comes from the analytical model;
  - granular column collapse against Rousseau et al. (2022, CC-BY data): 7 of 8 measured runouts within ±17 %, as close as the source's own simulation.

- **Mixshield demo checked against the Thames Tunnel drive** ([validation](docs/validation/slurry-thames-advance.md)):
  - ring build 32 min (Crossrail average), was 35 min; two 12 h shifts by default on the Thames route; the 80 mm/min advance limit now sourced (T&T 2014);
  - the forecast panel shows drive H (Sophia and Mary, King et al. 2017) beside the model. The working day is 7–58 % fast (10.7–12.5 against 7.9–10.0 rings), the best week close (77–92 against 91–100); separation-plant stops are not modelled and no open source quantifies them.

- **EPB demo checked against the Crossrail drives** ([validation](docs/validation/epb-crossrail-advance.md)):
  - the ring is now Crossrail's: 1.6 m, 7 segments + small key, 300 mm (King, Thomas & Stenning 2017). It was 1.2 m and 6 + key, taken from a Moscow metro source;
  - ring build 32 min, the Crossrail average (Tunnels & Tunnelling 2021), was 35 min; shield 12 m (Crossrail station-transits paper), was an assumed 9.5 m, which raises the shield-friction thrust;
  - two 12 h shifts a day, seven days a week, as on Crossrail, by default on the London route;
  - the forecast panel shows Crossrail's Table 3 beside the model. The average working day matches (11.8–12.5 rings against 12.3–14.9); the best day and week stay well below Crossrail's, which is stated as a limit.

- **Drill & blast cycle checked against Norwegian data** ([validation](docs/validation/drill-blast-cycle.md)):
  - logged rounds at the Ulvin rail tunnel (Messelt 2013): mucking 220 m³/h and downtime 13 % of the round are now in the model, which had no downtime;
  - a contractor's T10.5 estimate (Furunes & Strype 2022): ventilation 20 min and scaling 1.5 h, replacing assumed 0.5 h and 1 h. Every activity of the demo's round is inside the estimate's P5–P95;
  - 101 production hours a week (Tunnelbyggetid basis, was 110);
  - class I is now 12.7 h per round and 39 m/week (was 10.9 h and 50 m/week), against NFF's "about 12 h" and a Tunnelbyggetid model case of about 48 m/week.

- **Second bore** ([settlement](docs/validation/settlement.md)):
  - the twin-trough model takes the second bore's trough width away from the first bore as well as towards it;
  - Hyde Park (Wan et al. 2017): the second bore is 16.2 m away, read from the paper's vector figure, with 1.5–1.9× the first bore's volume loss, Ky 0.44 towards the first bore and 0.33 away;
  - Thames chalk: reading the table's "WB & EB" column as the second bore's own volume loss reproduces the 17 measured Smax values (median ratio 1.10, was 1.57), so the first-bore default drops from 0.35 % to 0.25 %, with the second bore 17 m away at 1.2×;
  - the EPB and Mixshield demos have a "Second bore" choice: "after both drives" shows the final settlement of both bores over the buildings, with the second tunnel drawn at its offset.

- **Hard-rock TBMs checked against real projects** ([validation](docs/validation/hard-rock-projects.md)):
  - the CSM disc-cutter model over-predicted the Follo Line TBM1 mean penetration by 1.9×. Its pressure-distribution exponent ψ is now −0.1, inside Rostami's range, which reproduces 6.32 mm/rev (6.36);
  - with Follo's measured penetration and cutter changes, the downtime model gives 12.9–14.9 m/day against the measured 14.1 m/day average;
  - double shield demo: 71 discs as at Follo; default thrust and speed are the logged Follo means. In gneiss it gives 6.85 mm/rev and 15.6 m/day (was 12.6 mm/rev and about 21 m/day);
  - gripper demo: the Gotthard 9.58 m machine data (8,526 kNm, 3,500 kW, 58 discs at 26 t, 2 m stroke), replacing a torque that belonged to the 9.33 m S-210;
  - Guadarrama, Brenner, Gotthard and Niagara averages listed as brackets; no open source gives their utilisation.
  - Follo section by section (18 sections read from the thesis's vector charts): CSM is within about ±27 % with mean rock strength and each section's thrust and speed, but 0.4–2.9× with single-test UCS. The Yinsong dataset turned out not to be open.
  - the hard-rock demos show the penetration with the Follo section scatter as a band (about ±27 %), and the limits panel says how far the CSM check goes.

- **SEM demo on real London ground** ([checklist](docs/realism/sem-heading.md), [validation](docs/validation/sem-convergence.md#farringdon-platform-tunnels-undrained-ground-london-clays)):
  - the SEM demo now opens on the Crossrail Farringdon platform tunnel: an 11 m sprayed-concrete enlargement of a 6.2 m TBM pilot, on the Farringdon – Liverpool Street scenario, with Crossrail's undrained design lines;
  - the sequence follows Farringdon: 1 m top headings, 2 m bench and invert, the ring closed 5–10 m back, 400 mm fibre-reinforced lining without girders. A water-bearing sand lens brings wellpoints, face pockets and 4 m spiles. The heading keeps the published 1.1 m/day (0.5 m/day in the lens);
  - the predicted crown settlement (about 10.5–14 mm) is shown beside the measured 10.3–16.5 mm outside compensation grouting and Crossrail's 10 mm FE;
  - the weak-rock heading stays selectable (`?ground=rock`);
  - Reset now puts the camera on the new face.
- **Crown settlement in undrained clay:** `sem.crown_settlement` (Python and JS, with test vectors) scales the ring movement to the crown with the Kirsch factor and adds 2–3 mm settlement of the whole ring measured at Crossrail Whitechapel. The Farringdon prediction moves from 5–8 mm (low by 1.3–2.7×) to 10.4–13.7 mm, inside the measured 10.3–16.5 mm. In-tunnel readings levelled out within days of ring closure, so consolidation is ruled out as the cause.
- **Undrained ground response:** the ground reaction curve handles φ = 0 (Tresca) as the limit of Duncan Fama, in Python and JavaScript, with a test and test vectors. Script: `models/py/validation/sem_farringdon.py`.
- **Urban EPB demo** (Slice A, [live](https://dtt-github.github.io/tunnel-construction-simulation/web/epb/)):
  - a 7 m EPB laid out front to back, with an articulated shield and 16 pairs of thrust cylinders;
  - push and ring-build cycle with a universal 6 + key ring;
  - chamber pressure against the DAUB window, with automatic or manual screw control and foam conditioning;
  - thrust and torque breakdown;
  - surface settlement with Burland categories for buildings.
  - Assumptions and gaps are listed in its [realism checklist](docs/realism/epb-slice-a.md).
- **Real buildings and measured settlement** ([buildings](docs/SCENARIOS.md), [settlement](docs/validation/settlement.md)):
  - both London scenarios carry the buildings within 60 m of the line: OS OpenMap Local footprints, Environment Agency LIDAR heights, Historic England listing (all OGL), built by `models/scenarios/build_buildings.py`;
  - the EPB and Mixshield demos place them at their real footprints, follow the face with the settlement surface, and list the most affected buildings near the face;
  - default volume loss and trough width from measured Crossrail settlement: Thames 0.35 %, K 0.5; Farringdon – Liverpool Street 0.5 %, K 0.43 (from Hyde Park). The trough reproduces Hyde Park (8.1 mm against 8.3 mm); in the Thames chalk the published volume losses do not reproduce the published Smax, and the volume loss that does is used.
- **Thames crossing for the Mixshield** ([sources](docs/SCENARIOS.md)): the Crossrail Thames Tunnel, Plumstead to North Woolwich, from 15 BGS/Crossrail boreholes (four over the river; OGL) and the OpenStreetMap line, built by `models/scenarios/build_thames.py`. The Mixshield demo drives through it by default, with the river in the long section. Under the river the support window is 2.96–3.57 bar (Crossrail: above 3 bar). The scenario format gains `river`, `d10` per unit and `ends`.
- **River above the ground:** the DAUB support window and the grout window now add the river column to the total overburden when the water level is above the ground surface.
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
