# Changelog

Notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions will be tagged from the first complete Phase 1 slice; until then, changes are grouped by date.

## [Unreleased]

### Added

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
