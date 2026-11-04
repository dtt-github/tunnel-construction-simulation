# Tunnel Construction Simulation

An open-source, physics-based simulator of tunnel construction that runs in the browser, built in the open by universities and industry.

Initiated and maintained by **[DigitalTwin Technology GmbH](https://www.digitaltwin.technology)** as part of its work on **[ConstructionWare](https://www.constructionware.app)**. Sister project: [construction-site-simulation](https://github.com/dtt-github/construction-site-simulation) (same stack, shared know-how).

**Goal:** a tunnel you can trust numerically. TBMs that penetrate, stall and wear cutters like real ones, faces that need the support pressure the ground demands, rings that load like real linings, and surface settlement you can check against monitoring data. Every model is cited, unit-tested against worked examples, and validated against published case histories.

**Scope:** all common methods:

- **TBM:** EPB, slurry/mixshield, hard-rock open gripper, single and double shield.
- **Conventional:** NATM/SEM, drill & blast, roadheader.
- **Other methods:** cut-and-cover, pipe jacking/microtunnelling, shaft sinking.

## What works today (Phase 1 skeleton)

| Area | Status |
|---|---|
| Model library | CSM disc-cutter model (forces, penetration, rate of penetration, torque, power, torque limit), generalised Hoek–Brown and rock-mass modulus, Peck/O'Reilly–New settlement trough with the longitudinal profile, Burland damage categories. Python reference + JavaScript twin, checked against shared test vectors to 1e-9 |
| Browser demo | Ø 7 m single-shield hard-rock TBM driving through a four-zone alignment (granite, fault zone, gneiss, quartzite). Penetration, torque, power and cutter loads come live from the CSM model. Boring and ring-build cycle with staggered six-segment rings. Jolt rigid-body muck fills muck cars at the excavated volume rate. Alarms for cutter overload, torque limit and poor rock mass |
| GPU server | Not started (Phase 2: NVIDIA Newton MPM for the EPB chamber and the face, on a DGX Spark) |

## Quick start

```bash
npm run serve        # static server on http://127.0.0.1:8741
```

Open http://127.0.0.1:8741/web/index.html in Chrome, Edge or Safari. No GPU server and no build step needed.

Tests:

```bash
npm test             # JS models vs shared vectors (Node >= 20)
npm run test:py      # Python reference models (uv)
npm run vectors      # regenerate models/test-vectors from the Python reference
```

## Architecture

The design is hybrid, and the same as the sister project. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

- **Browser:** three.js rendering, Jolt (WASM) rigid-body machinery, and every analytical/empirical model in JavaScript. This always works, with no server.
- **GPU server (DGX Spark):** NVIDIA Newton/Warp for heavy ground physics (implicit MPM for the face, the EPB chamber, the screw conveyor and the muck), coupled to the machine and streamed over WebSockets.
- **Offline:** Kratos GeoMechanics, Project Chrono and YADE for calibration and surrogate training.

A badge in the UI shows which fidelity level is driving the numbers: *Analytical*, *Local GPU* or *Server MPM*.

| Folder | What's in it |
|---|---|
| `models/` | Model library: `py/` reference implementations, `js/` browser twins, `test-vectors/` shared expected values |
| `web/` | Browser client (plain ES modules, three.js + Jolt from CDN, no build step) |
| `server/` | Newton/Warp simulation server (Phase 2) |
| `phase0/` | Platform benchmarks on the DGX Spark |
| `docs/` | Architecture, roadmap, model catalogue, [research survey](docs/research/research-survey.md) (literature, engines, standards), [industry survey](docs/research/industry-survey.md) (TBM makers, guidance, monitoring) |
| `knowledge/` | Curated notes from books and papers (`notes/` public; `books/` and `private/` are never committed) |

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

- **Phase 0:** DGX Spark benchmarks.
- **Phase 1:** browser-only analytical simulator with an EPB machine.
- **Phase 2:** Newton MPM for the chamber and the face.
- **Phase 3:** the other tunnelling methods.
- **Phase 4:** validation and surrogates.
- **Phase 5:** training and RL.

## Contributing

We especially want measured data: TBM machine logs, settlement monitoring, face-pressure records, cutter wear. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

- **Code:** Apache-2.0 ([LICENSE](LICENSE)).
- **Assets and data:** each keeps its own license ([NOTICE](NOTICE)).
- **Standards** (DAUB, ITA, EN, DIN): cited, never reproduced.
