# Tunnel Construction Simulation

**An open, physics-based tunnel construction simulator for the browser, with cited models and GPU ground physics.**

[![Live demo](https://img.shields.io/badge/demo-live-2a78d6)](https://dtt-github.github.io/tunnel-construction-simulation/)
[![Tests](https://github.com/dtt-github/tunnel-construction-simulation/actions/workflows/tests.yml/badge.svg)](https://github.com/dtt-github/tunnel-construction-simulation/actions/workflows/tests.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
![Status: Phase 1](https://img.shields.io/badge/status-phase%201%20in%20progress-c9862a)

### ▶ [Open the live demo](https://dtt-github.github.io/tunnel-construction-simulation/)

It runs in the browser, with no install and no GPU needed.

| Demo | What it shows | Checked against |
|---|---|---|
| [Recorded GPU runs](https://dtt-github.github.io/tunnel-construction-simulation/phase0/replays/) | Soil simulated with the material-point method on an NVIDIA DGX Spark, then replayed: a tunnel face collapsing as its support retracts, and an EPB chamber stirred by a rotating cutterhead | Nothing yet: a Phase 0 benchmark of speed and stability, not calibrated performance |
| [Hard-rock open gripper TBM](https://dtt-github.github.io/tunnel-construction-simulation/web/hard-rock/) | A 9.58 m main-beam TBM: disc cutterhead with buckets, grippers and regrip cycle, rock bolts, mesh and ring beams at L1 and shotcrete at L2 by rock class, fault zone, downtime per km | Gotthard machine data (Herrenknecht, AlpTransit archive); disc-cutter penetration against the Follo Line logs; working-day advance bracketed by Gotthard's 8–10 m per calendar day ([hard-rock projects](docs/validation/hard-rock-projects.md), [realism checklist](docs/realism/hard-rock-gripper.md)) |
| [Drill & blast road tunnel](https://dtt-github.github.io/tunnel-construction-simulation/web/drill-blast/) | A Norwegian T10.5 road tunnel round by round: the drilling pattern from published rules, a three-boom jumbo, charging, blast, ventilation, scaling, loader and trucks, bolts and sprayed concrete by support class, half-barrels, vibration at a house above | Hole counts of current Norwegian rounds; the round cycle against logged Ulvin rounds and a contractor's T10.5 estimate, 12.7 h against NFF's "about 12 h" ([drill & blast cycle](docs/validation/drill-blast-cycle.md), [realism checklist](docs/realism/drill-blast-heading.md)) |
| [Urban slurry shield (Mixshield)](https://dtt-github.github.io/tunnel-construction-simulation/web/slurry/) | A 7.08 m Crossrail-class Mixshield driving the Crossrail Thames Tunnel, Plumstead to North Woolwich, through real ground from open BGS boreholes (Chalk, Thanet Sand, the river above): submerged wall and air cushion, feed and discharge lines with a crusher at the suction, filter cake or slurry penetration at the face, dry-mass balance and deposit velocity in the circuit | Settlement of both bores against 17 measured sections of this drive, median ratio 1.10; the support window under the river (3.0–3.6 bar) against the more than 3 bar Crossrail needed; rings per working day against drive H, 10.7–12.5 against 7.9–10.0 ([settlement](docs/validation/settlement.md), [Thames advance](docs/validation/slurry-thames-advance.md), [realism checklist](docs/realism/slurry-mixshield.md)) |
| [SEM / NATM heading](https://dtt-github.github.io/tunnel-construction-simulation/web/sem/) | The Crossrail Farringdon platform tunnel in real London ground: an 11 m sprayed-concrete enlargement of a TBM pilot in Lambeth Group and London Clay, with undrained ground response, ring closure 5–10 m behind the face, spiles in a water-bearing sand lens, and predicted crown settlement (about 11 mm in the Lambeth Group) beside the measured 10–16.5 mm. A weak-rock heading with a fault zone stays selectable | Crown settlement 10.4–13.7 mm against the measured 10.3–16.5 mm and Crossrail's 10 mm design analysis; ground response against measured convergence in a weak-rock tunnel ([SEM convergence](docs/validation/sem-convergence.md), [realism checklist](docs/realism/sem-heading.md)) |
| [Hard-rock double shield TBM](https://dtt-github.github.io/tunnel-construction-simulation/web/hard-rock/?machine=double) | A 9.9 m Follo-class double shield: telescopic shields, gripper shield, main and auxiliary thrust cylinders, segment rings built while boring with pea gravel and grout, single-shield mode in the fault zone | Follo Line TBM1: penetration 6.4 against 6.32 mm/rev, about ±27 % section by section; advance 13–15 against 14.1 m a day ([hard-rock projects](docs/validation/hard-rock-projects.md), [realism checklist](docs/realism/hard-rock-double-shield.md)) |
| [Urban EPB shield](https://dtt-github.github.io/tunnel-construction-simulation/web/epb/) | A 7 m EPB laid out front to back, driven through real London ground: the Farringdon – Liverpool Street corridor from 14 open BGS/Crossrail boreholes, with a geological long section and the 60 real buildings over the line (OS footprints, LIDAR heights, listed status). Chamber pressure inside the DAUB window, automatic or manual screw control, foam conditioning, thrust and torque breakdown, the push and ring-build cycle with Crossrail's 1.6 m ring of 7 segments + key, and surface settlement over buildings, with the second bore | Thrust and torque against four open field datasets; settlement reproduces Hyde Park (8.1 against 8.3 mm), with the second bore from the same site; the 90-day advance forecast against published record rates ([EPB field data](docs/validation/epb-open-data.md), [settlement](docs/validation/settlement.md), [realism checklist](docs/realism/epb-slice-a.md)) |

[![Urban EPB shield: cut-away from the cutterhead to the backup, with the operator console](docs/images/epb-machine.png)](https://dtt-github.github.io/tunnel-construction-simulation/web/epb/)

---

## Why this project

Tunnelling simulators today are either closed training products or research codes that take hours per run. This project aims for a tunnel you can trust numerically and still drive in real time:

- **Real machines.** TBMs penetrate, stall and wear cutters like real ones. EPB chambers hold pressure like real ones. Each method is laid out front to back after [sourced reference cards](docs/research/methods-reference.md).
- **Real ground.** Faces need the support pressure the ground demands, and surface settlement can be checked against monitoring data.
- **Every number cited.** Each model has a Python reference, a JavaScript twin, hand-checked tests, and published sources ([model catalogue](docs/MODELS.md)).
- **Honest labels.** Demos say what is recorded, illustrative or not yet calibrated ([realism rules](docs/ROADMAP.md#realism-rules-apply-to-every-phase)).

**Scope:**

- **TBM:** EPB, slurry/Mixshield, variable density, hard-rock open gripper, single and double shield.
- **Conventional:** NATM/SEM, drill & blast, roadheader.
- **Other:** cut-and-cover, pipe jacking, shafts.

## What works today

| Area | Status |
|---|---|
| **Model library** (Python + JavaScript, shared test vectors) | 14 models: CSM disc cutter, Hoek–Brown, settlement (troughs, longitudinal profile, method presets, twin tunnels, Burland), face support (wedge-silo + DAUB window), EPB chamber and screw, slurry shield, thrust and torque, hard-rock drive, ground response and squeezing, SEM sprayed concrete, ground scenarios, segment lining, drill & blast, utilisation and downtime. [Details →](docs/MODELS.md) |
| **Machine class presets** | Six classes (urban EPB, Mixshield, double shield, main beam, SEM, drill & blast). Every field carries its source and a verified flag. [Presets →](models/presets/machine-classes.json) |
| **GPU physics (Phase 0)** | NVIDIA Newton implicit MPM on a DGX Spark: face stability and EPB chamber benchmarks, particle streaming, record and replay. [Results →](phase0/RESULTS.md) |
| **Browser client** | Six method demos and the [replay viewer](https://dtt-github.github.io/tunnel-construction-simulation/phase0/replays/) live; see the table above |
| **Validation** | Each demo checked against published project data: [Farringdon SCL](docs/validation/sem-convergence.md), [Follo and Gotthard](docs/validation/hard-rock-projects.md), [Hyde Park and the Thames sections](docs/validation/settlement.md), [EPB field data](docs/validation/epb-open-data.md), [Ulvin drill & blast](docs/validation/drill-blast-cycle.md) |

## Quick start

```bash
git clone https://github.com/dtt-github/tunnel-construction-simulation.git
cd tunnel-construction-simulation
npm run serve
```

Open http://127.0.0.1:8741/ and pick a demo (`web/` or `phase0/replays/`). There is no build step; any modern Chrome, Edge, Safari or Firefox works.

Run the tests:

```bash
npm test
```

```bash
npm run test:py
```

`npm test` checks the JavaScript models against the shared vectors (Node ≥ 22). `npm run test:py` runs the Python reference models with [uv](https://docs.astral.sh/uv/).

## Repository layout

| Folder | Contents |
|---|---|
| [`models/`](models) | Model library: [`py/`](models/py) reference implementations and tests, [`js/`](models/js) browser twins, [`test-vectors/`](models/test-vectors) shared expected values, [`presets/`](models/presets) machine class presets |
| [`web/`](web) | Browser client: plain ES modules, three.js and Jolt from a CDN, no build step |
| [`phase0/`](phase0) | GPU platform benchmarks, particle streaming, record and replay ([results](phase0/RESULTS.md)) |
| [`server/`](server) | Newton/Warp simulation server (Phase 2) |
| [`docs/`](docs) | Architecture, roadmap, model catalogue, realism checklists, research ([index](docs/README.md)) |
| [`knowledge/`](knowledge) | Local workspace for books and notes, never committed except its README |

## Documentation

| Document | What it covers |
|---|---|
| [Documentation index](docs/README.md) | Every document and where to start |
| [Architecture](docs/ARCHITECTURE.md) | The right physics at the right scale; the model library contract |
| [Roadmap](docs/ROADMAP.md) | Realism rules, phases and the method-by-method plan |
| [Model catalogue](docs/MODELS.md) | Every implemented model: equations, references, validation |
| [Methods reference](docs/research/methods-reference.md) | What each tunnelling method really looks like, with sources |
| [Research survey](docs/research/research-survey.md) | Literature, engines, standards and datasets |
| [Industry survey](docs/research/industry-survey.md) | Machine makers, published specifications, record advance rates |
| [Changelog](CHANGELOG.md) | What changed, release by release |

## Roadmap at a glance

1. **Phase 0, platform:** done. GPU benchmarks, streaming, record and replay.
2. **Phase R, realism reset:** done. Sourced method cards, corrected demo labels, cited presets.
3. **Phase 1, browser simulator:** one complete method at a time.
   - A: urban EPB (demo live, with downtime and record-rate check)
   - B: hard rock (open gripper and double shield live)
   - C: slurry / Mixshield (demo live)
   - D: SEM/NATM (heading live; final lining stage next)
   - E: drill & blast (demo live)
4. **Phase 2:** GPU ground physics coupled to the machine.
5. **Phase 3:** further methods.
6. **Phase 4:** validation against case histories.
7. **Phase 5:** training and research tools.

Full plan: [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributing

We especially want **measured data**: TBM machine logs, settlement monitoring, face-pressure records, cutter wear. We also welcome models, 3D assets of real machinery and validation studies. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

- **Code:** [Apache-2.0](LICENSE).
- **Third-party assets and data:** each keeps its own license, listed in [NOTICE](NOTICE).
- **Standards** (DAUB, ITA-AITES, EN, DIN): cited, never reproduced.

## Maintainers

Initiated and maintained by [DigitalTwin Technology GmbH](https://www.digitaltwin.technology) as part of [ConstructionWare](https://www.constructionware.app). Sister project: [construction-site-simulation](https://github.com/dtt-github/construction-site-simulation), which uses the same stack.
