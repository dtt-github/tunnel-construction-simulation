# Roadmap

Status: [x] done · [ ] planned · [~] partly done.

Sources:

- [research/methods-reference.md](research/methods-reference.md): what each method really looks like.
- [research/research-survey.md](research/research-survey.md): the models.
- [research/industry-survey.md](research/industry-survey.md): machine numbers.
- [MODELS.md](MODELS.md): what is implemented.

## Release 1 (first complete release): tagged v1.0.0 on 6 Nov 2026

- **Scope:** Phase R, the five Phase 1 slices as built (six demos), the model library, the validation report, and Phase 0 with Phase 2 WP0 to WP2 and WP7 (one recorded GPU sand face).
- **Not in it:** the MPM clay tunnel and EPB chamber (WP3, WP4), the open Phase 1 items below, Phases 3 to 5.
- **Stop line:** no new features went in after the scope was set. Before the tag: README, validation report and roadmap at the release state; a full test pass (94 Python, 21 JavaScript and 14 server tests including GPU) and a live check of the six demos; the changelog cut and the tag.
- **Done for it (6 Nov 2026):** the gap plan (one gap closed, eight shipped as disclosed in the [validation report](validation/REPORT.md#ranked-gaps), two blocked); the [realism checklist template](realism/TEMPLATE.md); the [release audit](RELEASE-AUDIT.md).

## Realism rules (apply to every phase)

1. **One method, one machine class, one ground.**
   - Every demo states its method (for example "open gripper TBM"), a class preset (for example "7 m hard-rock main beam") and a ground that DAUB or FHWA pair with that method.
   - The ground-to-method pairing table is in [methods-reference](research/methods-reference.md#ground--method-pairing-scenario-editor-rules).
2. **Right support and lining for the method.**
   - Open gripper TBM: bolts, mesh and ring beams at L1; shotcrete at L2; cast-in-place final lining.
   - Single and double shield: segments with pea gravel or grout.
   - EPB and slurry: segments with two-component grout.
   - SEM: shotcrete, lattice girders and a cast-in-place inner lining.
   - Drill & blast: bolts and shotcrete, plus cast-in-place where the scenario follows Alpine practice.
3. **Right layout and muck path.** Follow the front-to-back layout of the method card: buckets and centre belt (hard rock), bulkhead and screw (EPB), pipes and separation plant (slurry).
4. **Right cycle and utilisation.**
   - Model the stroke, regrip, ring build or support installation, cutter changes, logistics and bad-ground delays.
   - Never show advance at 100 % of instantaneous ROP.
   - Bad ground slows the drive.
5. **Every number in a cited range.**
   - Inputs, limits and outputs (rpm, thrust, torque, pressure, advance per day) must sit inside the reference-machine or project ranges.
   - Best days, weeks and months must stay below the record table for the diameter class.
6. **Honest labels.**
   - Say "recorded", "illustrative" or "not calibrated" wherever that is true.
   - A realism checklist (a short table built from rules 1–5) is filled in and reviewed before any demo is published.

## Phase 0: platform (DGX Spark)

- [x] Reuse the sister project's Spark setup (Newton 1.7, Warp 1.19, CUDA 13, uv)
- [x] Benchmark Newton implicit MPM:
  - (a) EPB chamber with rotating cutterhead and screw conveyor;
  - (b) face slice under support pressure.
  - [Results](../phase0/RESULTS.md); screw discharge still needs pressure control and a resolved inlet.
- [x] WebSocket streaming of 100k–300k quantized particles at 20–30 Hz (TSP0, u16)
- [x] Record and replay format (TSR0) with a browser viewer
- [ ] WebGPU Drucker–Prager MLS-MPM patch on Apple GPU and on Chrome/Linux ARM

## Phase R: realism reset (now, before any new demo work)

- [x] Sourced reference card per method ([methods-reference](research/methods-reference.md))
- [x] Public site:
  - [x] label the hard-rock demo "being rebuilt" on the landing page and on the demo itself, until slice B is done;
  - [x] correct the replay viewer text:
    - "Live readouts" → "Recorded readouts";
    - EPB torque comes from chamber mixing only, with no cutting;
    - the screw is starved and not credible yet;
    - the chamber pressure is gravity-only, with no pressure control.
- [x] Replace the Krause α·D³ torque band with a table of reference machines. Modern EPBs exceed it: Crossrail 7.08 m has 9.8 MNm.
- [x] Class presets as data ([machine-classes.json](../models/presets/machine-classes.json), a source and a verified flag on every field; unsourced fields left empty), built from the reference projects in the method cards:
  - 7 m urban EPB;
  - 10 m double shield;
  - 9.5 m main beam;
  - 7 m Mixshield;
  - SEM heading in stiff soil;
  - drill & blast road tunnel.
- [x] Realism checklist template, used by every demo PR ([template](realism/TEMPLATE.md); the six checklists follow it, 6 Nov 2026)

## Phase 1: browser simulator, one method slice at a time

Each slice delivers everything for one method:

- its models;
- a 3-D machine or heading that follows the method card;
- its operating cycle and utilisation;
- support or lining, and logistics;
- operator console and alarms;
- a check against a reference project.

A slice is not done until its realism checklist passes.

### Model library (Python reference + JS twin + shared vectors)

1. [x] CSM disc-cutter forces, penetration, ROP, torque, power, torque limit
   - [x] Cap penetration (practical maximum 15 mm/rev, Macias & Barton 2022), not the solver bound.
   - [x] Add a power limit and a constant-power region to the drive; speed limit from gauge-cutter speed.
2. [~] Cutter wear and change events (CAI model and 66 min per change done, [MODELS](MODELS.md#hard-rock-drive); NTNU CLI open)
3. [x] Face support (wedge-silo and DAUB window done; the factors, the maximum and the operating deviations checked against DAUB 2016, which also reproduces its example 8.1). Seepage forces are not needed in closed mode: DAUB applies them only when the support is below the groundwater pressure.
4. [~] EPB chamber (volume balance, foam, simplified screw done) and slurry (air cushion, filter cake per DIN 4126, circuit mass balance and deposit velocity done, [MODELS](MODELS.md#slurry-shield-mixshield)). Still open:
   - the full Merritt & Mair screw model;
   - separation-plant capacity and fines.
5. [x] Thrust and torque components
6. [x] Hoek–Brown / GSI, rock-mass modulus
7. [x] Convergence–confinement: GRC, support curves (bolts, shotcrete, ribs), LDP ([MODELS](MODELS.md#ground-response-and-squeezing))
8. [~] Squeezing (Hoek & Marinos) and shield jamming (Ramoni & Anagnostou) (squeezing done; jamming as a screening estimate; time-dependent creep and standstills open)
9. [x] Settlement trough and Burland categories
10. [~] Segment lining: ring forces (JSCE elastic equation method, ITA 2000, with Wood's joint reduction), jacking stress and bursting, annulus volume and grout pressure window, taper done ([MODELS](MODELS.md#segment-lining)); open: Muir Wood / Duddeck–Erdmann (no open copy), universal-ring key position, ring loads in rock for the double shield
11. [~] Rock support: RMR classes → support pattern and support downtime per km by machine type done; per-bolt and per-ring-beam installation times open
12. [~] Utilisation / activity-time model (discrete events) (EPB done: ring build, general activities, train delays, per-cycle maintenance, maintenance shift, cutting-tool interventions, record-rate check, [MODELS](MODELS.md#utilisation-and-downtime); open: hard-rock stroke/regrip/support/cutter-change terms, locomotive travel time, breakdowns by subsystem)
13. [x] Drill & blast: round design (Holmberg cut, Olofsson burden), Kuz-Ram fragmentation, PPV limits, cycle times ([MODELS](MODELS.md#drill--blast)); Langefors' burden formula and the NTNU advance model open (no open copy)
14. [x] SEM: excavation sequence and ring-closure distance, shotcrete ageing E(t) ([MODELS](MODELS.md#sem--natm-sprayed-concrete-lining))

### Slice A: urban EPB, 7 m class (first; most models already exist)

Demo: [web/epb/](../web/epb/) ([live](https://dtt-github.github.io/tunnel-construction-simulation/web/epb/)). Realism checklist: [realism/epb-slice-a.md](realism/epb-slice-a.md).

- [x] Machine, front to back:
  - cutterhead with soft-ground tools and ≈ 35 % opening, plus mixing arms;
  - pressure bulkhead with earth-pressure cells;
  - screw with outlet gate;
  - man-lock;
  - articulated shield;
  - thrust cylinders on the last ring;
  - brush tail seal;
  - erector and segment feeder;
  - two-component grout through the tailskin;
  - backup with foam plant and belt or muck cars.
- [~] Cycle (done except key-position selection driven by steering; keys follow a fixed alternating pattern):
  - push one ring (1.6 m, Crossrail), then build a ring of 7 segments + key with key-position selection;
  - grout during the push;
  - rates: 32 min build (Crossrail average); 12.3–14.9 rings per working day on Crossrail drives X and Y ([validation](validation/epb-crossrail-advance.md)).
- [~] Console (done except grout pressure):
  - chamber pressure gauges by height inside the DAUB window;
  - screw speed and FIR/FER;
  - cutterhead at ≈ 1.5–3 rpm;
  - thrust and torque breakdown;
  - grout volume and pressure.
- [~] Surface: settlement heatmap with buildings and damage categories by Mair, Taylor & Burland (done); volume loss from the face pressure in London Clay (Macklin 1999, done); from grouting and in other ground (open: needs a published relation).
- [x] Check against reference machine numbers (Crossrail, Moscow) and the published EPB rates (40-EPB survey, best day and month references, world record by diameter class).

### Slice B: hard rock, open gripper and double shield

- [x] Hard-rock cutterhead ([web/hard-rock/](../web/hard-rock/), [realism checklist](realism/hard-rock-gripper.md)):
  - flat face with curved gauge and tilted gauge cutters;
  - 17″ or 19″ discs at 75–100 mm spacing, with a centre cluster;
  - 6–8 buckets with grill bars;
  - muck ring and centre belt.
  - Speed limited by gauge-cutter speed.
- [x] Open gripper TBM (final lining stated as a later stage, not drawn):
  - roof and side shields with invert shoe, main beam, grippers and propel cylinders, rear legs;
  - L1: roof drills, ring-beam erector, mesh, probe drill;
  - L2: shotcrete robot, invert segments;
  - backup conveyor;
  - stroke → regrip cycle, with support installed in parallel;
  - support class from the rock mass (model 11);
  - cast-in-place final lining shown as a later stage, or on the backup.
- [x] Double shield (variant) ([realism checklist](realism/hard-rock-double-shield.md)):
  - telescopic shield, gripper shield, segments with pea gravel;
  - concurrent boring and ring build;
  - falls back to single-shield mode in faults.
- [ ] Single shield as a further variant: sequential bore and ring build, with segments and pea gravel or grout.
- [~] Geology (fault zone done: slower drive, heavy support; jamming risk screened against the Brenner machines' thrust by mode; creep and standstill time open):
  - fault zones cut penetration and utilisation;
  - they need heavy support (ribs at 1 m, shotcrete);
  - they raise the jamming risk (model 8).
- [~] Check against reference projects ([validation](validation/hard-rock-projects.md)): Follo penetration and average advance reproduced (CSM ψ back-analysed); Gotthard machine data verified; Guadarrama, Brenner and Niagara bracket the rates. Follo section by section done: ±27 % with mean rock strength, 0.4–2.9× with single-test UCS. Queens Water Tunnel (gneiss, 10 open stations) checked without refitting: median 1.02×, massive rock up to 1.8× fast. Guadarrama's share of time boring (32 %) against the model's 28 %. Brenner calc-schist: penetration consistent, not tested; cutterhead torque 1.25–2.4× the logged value on Brenner and Tehran. Open: penetration in other rock types with logged strength (the Yinsong dataset is not open); the torque formula.

### Slice C: slurry / Mixshield

Demo: [web/slurry/](../web/slurry/) ([live](https://dtt-github.github.io/tunnel-construction-simulation/web/slurry/)). Realism checklist: [realism/slurry-mixshield.md](realism/slurry-mixshield.md).

- [x] Submerged wall and air cushion, crusher, feed and discharge lines, slurry pumps, separation plant at the portal (labelled); no screw and no belt.
- [x] Filter cake and pressure transfer (DIN 4126); lower torque than EPB.
- [ ] Booster pumps and pipe extensions drawn; separation-plant stops in the downtime model.

### Slice D: SEM / NATM

Demo: [web/sem/](../web/sem/) ([live](https://dtt-github.github.io/tunnel-construction-simulation/web/sem/)). Realism checklist: [realism/sem-heading.md](realism/sem-heading.md).

- [x] Heading, bench and invert sequence, lattice girders, mesh and spiles, sprayed shotcrete, temporary invert, optical targets, convergence monitoring
- [x] Real ground: the Farringdon platform tunnels on the London scenario, undrained (Tresca) ground response with Crossrail's design lines, prediction checked against measured crown settlement ([validation](validation/sem-convergence.md#farringdon-platform-tunnels-undrained-ground-london-clays))
- [ ] Membrane and cast-in-place inner lining with a formwork traveller, cast once convergence is below 1 mm/month

### Slice E: drill & blast

Demo: [web/drill-blast/](../web/drill-blast/) ([live](https://dtt-github.github.io/tunnel-construction-simulation/web/drill-blast/)). Realism checklist: [realism/drill-blast-heading.md](realism/drill-blast-heading.md).

- [x] Jumbo drilling pattern, charging, blast, ventilation, scaling, loader and trucks
- [x] Bolts and shotcrete by rock class, rough perimeter with half-barrels
- [ ] Probe drilling and pre-grouting; overlap of support work with the next round; waterproofing and inner lining

### Cross-cutting client work

- [~] Ground scenario files (JSON, [format](SCENARIOS.md)) with a loader in Python and JS; real alignments from open BGS boreholes: Farringdon – Liverpool Street (EPB demo) and the Thames crossing Plumstead – North Woolwich (Mixshield demo). The SEM demo runs on the London scenario at the Farringdon platform tunnels. Open: a geology editor, scenarios for drill & blast and the hard-rock TBMs, a method picker restricted by the DAUB and FHWA pairing
- [ ] Logistics: muck removal capacity (belt or trains), segment and grout supply, ventilation
- [ ] Guidance loop:
  - total station and active target;
  - head and tail deviation;
  - steering by differential cylinder pressure;
  - ±75 mm tolerance alarms.
- [ ] Shift reports and timeline replay of a drive (advance, utilisation by cause, settlement, ring QA, tool wear)
- [ ] Open signal schema and CSV / OPC-UA-style export

## Phase 2: server ground physics (Newton on the DGX Spark)

- [~] Work packages ([plan](plans/phase2-mpm-face-chamber.md)): WP0 to WP2 and WP7 done (element tests, dry-sand face, recorded face in the EPB demo); WP3 clay unblocked on 7 Nov 2026: with GIMP integration and an initial particle jitter of 0.05 h ([newton#5180](https://github.com/newton-physics/newton/issues/5180)) the clay tunnel is within 11 % of Kimura & Mair in plane strain and at 0.80–1.00 in 3D headings, the deep heading 12–20 % weak ([MPM clay](validation/mpm-clay.md)); WP4 chamber holds its pressure since 9 Nov 2026 with a volume balance by region (Newton loses volume around a moving solid) and an undrained paste and wall friction from open sources: 200 kPa through a 20 s excavation, gradient 12–16 kPa/m against Botlek's 10–20, screw volume balanced at voxel 0.15 m; open: gradient convergence, the stop gradient, the band, the leak, torque with the face ([MPM chamber](validation/mpm-chamber.md#volume-balance-and-a-sourced-paste-8-9-nov-2026))
- [ ] MPM face and chamber two-way coupled to the cutterhead, screw and shield, with a pressure-controlled shove; screw inlet resolved
- [ ] Calibrate against the analytical face pressure and screw discharge
- [ ] Slurry variant with the pump circuit; mode switching (variable density, crossover rock/EPB)
- [ ] Record and replay of calibrated runs, labelled with their calibration status

## Phase 3: further methods

- [ ] Roadheader (Bilgin ICR, Evans pick forces)
- [ ] Pipe jacking and microtunnelling
- [ ] Shafts (VSM, caisson); cut-and-cover with props, dewatering and basal heave
- [ ] Tunnel ventilation (1-D network)

## Phase 4: fidelity and validation (ongoing)

- [x] Validation report per model and per slice, against published case histories ([report](validation/REPORT.md)); kept up to date with each validation page
- [ ] Calibration on open datasets (RMRE 2025 synthetic datasets) and partner data. The Yinsong hard-rock dataset is not open (on request only); Follo TBM1 sections are used instead ([validation](validation/hard-rock-projects.md)).
- [ ] Surrogates from Kratos staged-excavation runs and DEM cutter–rock runs
- [ ] Uncertainty: random fields of GSI and UCS

## Phase 5: training and research

- [ ] Scenario editor, trainee scoring, instructor station
- [ ] Training curriculum: EPB scenario set, erector trainer, trainee records
- [ ] Multi-user sessions; optional OPC UA server; IFC 4.3 / LandXML alignment and as-built rings
- [ ] Gymnasium environments (face-pressure control, steering); ROS 2 bridge shared with the sister project
