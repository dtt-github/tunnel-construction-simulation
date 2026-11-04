# Contributing

This project aims to be an open, physically realistic tunnel construction simulator that universities and companies build together. It was initiated by [DigitalTwin Technology GmbH](https://www.digitaltwin.technology), which maintains it and is its main contributor, as part of its work on [ConstructionWare](https://www.constructionware.app). Contributions of every kind help: code, models, 3D assets, measured data, validation studies and bug reports.

By contributing, you agree that your contribution is licensed under the same terms as the part of the project it goes into (see [Licensing](#licensing)). You also agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## What we need most

| Area | Examples | Where |
|---|---|---|
| **Field data for validation** | TBM machine logs (thrust, torque, penetration, chamber pressure, screw speed, grout volumes) with geology; cutter wear and change records; settlement and convergence monitoring; face-pressure records; drill & blast vibration | Open an issue (label *validation-data*) |
| **Models** | Face stability, EPB/slurry chamber models, lining design, squeezing, shotcrete ageing, blast design, roadheader cutting, ventilation | `models/py` + `models/js` + vectors + tests |
| **3D assets of real machinery** | TBMs (cutterheads, shields, erectors, backup), segments, jumbos, roadheaders, locomotives, muck cars. Separate moving parts, correct dimensions and masses | `assets/` (to be created), with a registry entry and license |
| **Server physics** | Newton MPM soil at the face and in the chamber, coupling to machines, pore pressure | `server/` |
| **Web client** | Rendering, operator console, scenario editor, UX, performance | `web/` |

If you're unsure where something fits, open an issue first.

## Adding a model

1. Write the Python reference in `models/py/tunnelsim_models/`. Start the docstring with the references (author, year, venue), the equations and the units.
2. Add hand-checked anchor tests in `models/py/tests/`, using worked examples from the source where possible.
3. Add cases to `models/py/make_vectors.py` and run `npm run vectors`.
4. Write the JavaScript twin in `models/js/` and export it from `index.js`. `npm test` must reproduce the vectors to 1e-9.
5. Add a row to [docs/MODELS.md](docs/MODELS.md).

Do not copy text, tables or figures from copyrighted standards or books. Implement from the published equations and cite them.

## How to contribute code

1. Fork the repository and create a branch from `main`.
2. Keep changes focused.
   - Python follows PEP 8 (long lines allowed).
   - JavaScript uses ES modules with no build step.
3. If you change physics, include numbers: tests, a benchmark run, or a comparison against data.
4. Sign off your commits (`git commit -s`) to certify the [Developer Certificate of Origin](https://developercertificate.org/).
5. Open a pull request. Describe what changed, how you tested it, and on which hardware.

## Licensing

- **Code:** Apache License 2.0 ([LICENSE](LICENSE)).
- **3D assets and data:** each keeps its own license, recorded in [NOTICE](NOTICE). CC0 or CC-BY-4.0 are preferred for data.
- **Documentation and research notes:** Apache-2.0 unless a file says otherwise. Cited third-party material remains with its owners.

## Reporting bugs and asking questions

Use GitHub issues. Include:

- the browser and OS;
- for the server: GPU, driver and Newton/Warp versions;
- the steps you took and what you saw.
