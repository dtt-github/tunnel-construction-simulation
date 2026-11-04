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
