# Documentation

Start with the [project README](../README.md) for the live demo and quick start.

## Where to start

| If you want to… | Read |
|---|---|
| Understand how the system is built | [Architecture](ARCHITECTURE.md) |
| See what is planned and in what order | [Roadmap](ROADMAP.md) |
| Look up a model, its equations, sources and tests | [Model catalogue](MODELS.md) |
| Check what a tunnelling method really looks like before building or reviewing a demo | [Methods reference](research/methods-reference.md) |
| Find literature, open-source engines, standards and datasets | [Research survey](research/research-survey.md) |
| Find machine specifications, guidance systems and record advance rates | [Industry survey](research/industry-survey.md) |
| See what every demo and model is checked against, and what is still assumed | [Validation report](validation/REPORT.md) |
| See the GPU benchmark results | [Phase 0 results](../phase0/RESULTS.md) |
| Contribute code, models or data | [Contributing](../CONTRIBUTING.md) |

## All documents

| Document | Purpose |
|---|---|
| [SCENARIOS.md](SCENARIOS.md) | Ground scenario file format; the Farringdon – Liverpool Street and Thames crossing scenarios from open BGS boreholes, with their sources |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Physics by scale (alignment, machine, face and chamber, cutter); browser and GPU-server split; the model library contract |
| [ROADMAP.md](ROADMAP.md) | Realism rules for every demo; Phase 0 to 5; the method-by-method slices of Phase 1 |
| [MODELS.md](MODELS.md) | One section per implemented model: what it computes, files, references, validation, known limits |
| [validation/REPORT.md](validation/REPORT.md) | Validation report: every check by demo and by model, its kind (independent, calibrated, consistency, bracket), and the ranked gaps |
| [validation/settlement.md](validation/settlement.md) | Settlement trough against measured Crossrail settlement (Hyde Park, Thames chalk); the demo defaults |
| [validation/sem-convergence.md](validation/sem-convergence.md) | Ground-response chain against measured convergence in a weak-rock tunnel (Albania, CC BY 4.0), and against measured crown settlement in the Farringdon platform tunnels |
| [validation/drill-blast-cycle.md](validation/drill-blast-cycle.md) | Drill & blast round cycle against logged Ulvin rounds, a T10.5 contractor estimate and Tunnelbyggetid |
| [validation/hard-rock-projects.md](validation/hard-rock-projects.md) | Hard-rock TBM penetration and advance against Follo, Gotthard, Guadarrama, Brenner and Niagara |
| [validation/epb-crossrail-advance.md](validation/epb-crossrail-advance.md) | EPB ring cycle and advance against the Crossrail running-tunnel drives |
| [validation/slurry-thames-advance.md](validation/slurry-thames-advance.md) | Mixshield ring cycle and advance against the Crossrail Thames Tunnel drive |
| [validation/mpm-element-tests.md](validation/mpm-element-tests.md) | GPU MPM (Phase 2) element tests: material mapping, at-rest stress, Rankine wall, Rousseau column collapse |
| [validation/mpm-face-sand.md](validation/mpm-face-sand.md) | GPU MPM (Phase 2) tunnel face in dry sand against Idinger et al. (2011) and Wang et al. (2024); still uncalibrated |
| [validation/mpm-clay.md](validation/mpm-clay.md) | GPU MPM (Phase 2) tunnel in undrained clay against Kimura & Mair (1981): blocked, about half the measured stability ratio |
| [validation/mpm-chamber.md](validation/mpm-chamber.md) | GPU MPM (Phase 2) EPB chamber under pressure against Bezuijen et al. (2005), Botlek: blocked |
| [validation/epb-screw-botlek.md](validation/epb-screw-botlek.md) | EPB screw pressure profile against the Botlek screw gauges (Bezuijen et al. 2005): old default failed, now calibrated |
| [validation/epb-open-data.md](validation/epb-open-data.md) | EPB thrust and torque models against open field data (Changsha Metro Line 4, Guangzhou–Foshan), CC BY 4.0 |
| [realism/TEMPLATE.md](realism/TEMPLATE.md) | Template every realism checklist follows: header links, the six rules, assumed values, open items |
| [realism/drill-blast-heading.md](realism/drill-blast-heading.md) | Realism checklist for the drill & blast road tunnel demo |
| [realism/slurry-mixshield.md](realism/slurry-mixshield.md) | Realism checklist for the urban slurry shield (Mixshield) demo |
| [realism/sem-heading.md](realism/sem-heading.md) | Realism checklist for the SEM/NATM heading demo |
| [realism/hard-rock-gripper.md](realism/hard-rock-gripper.md) | Realism checklist for the hard-rock open gripper demo |
| [realism/hard-rock-double-shield.md](realism/hard-rock-double-shield.md) | Realism checklist for the hard-rock double shield demo |
| [realism/epb-slice-a.md](realism/epb-slice-a.md) | Realism checklist for the urban EPB demo: each rule, evidence, known gaps, assumed values |
| [research/methods-reference.md](research/methods-reference.md) | Sourced cards per method: layout front to back, support and lining, cycle, typical numbers, ground pairing |
| [research/research-survey.md](research/research-survey.md) | Literature review behind the models and architecture, with verification tags |
| [research/industry-survey.md](research/industry-survey.md) | Manufacturers, published specifications, reference projects, world-record advance rates |
| [../phase0/RESULTS.md](../phase0/RESULTS.md) | Measured speed and accuracy of Newton MPM on the DGX Spark |
| [../CHANGELOG.md](../CHANGELOG.md) | Notable changes |

## Conventions

- **Sources:** every factual claim links an openly published source (URL or DOI). Claims that could not be confirmed are marked **[UNVERIFIED]**.
- **Units:** SI at interfaces, unless a discipline convention is clearer and documented (the CSM model uses mm, MPa and N).
- **Names:** machines are named by class ("7 m urban EPB"), never by brand. Manufacturer data is cited as a reference only.
- **Copyright:** standards and books are cited, never reproduced.
