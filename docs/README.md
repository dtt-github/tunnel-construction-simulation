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
| See the GPU benchmark results | [Phase 0 results](../phase0/RESULTS.md) |
| Contribute code, models or data | [Contributing](../CONTRIBUTING.md) |

## All documents

| Document | Purpose |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Physics by scale (alignment, machine, face and chamber, cutter); browser and GPU-server split; the model library contract |
| [ROADMAP.md](ROADMAP.md) | Realism rules for every demo; Phase 0 to 5; the method-by-method slices of Phase 1 |
| [MODELS.md](MODELS.md) | One section per implemented model: what it computes, files, references, validation, known limits |
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
