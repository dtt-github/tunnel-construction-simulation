# Roadmap

Status: [x] done · [ ] planned. Sources for each model: [research/research-survey.md](research/research-survey.md), section B, and [MODELS.md](MODELS.md).

## Phase 0: platform (DGX Spark)

- [x] Reuse the sister project's Spark setup (Newton 1.7, Warp 1.19, CUDA 13, uv)
- [x] Benchmark Newton implicit MPM: (a) EPB chamber with rotating cutterhead and screw conveyor, (b) face slice under support pressure. Record particles, real-time factor and stability ([results](../phase0/RESULTS.md); screw discharge still needs pressure control and a resolved inlet)
- [x] WebSocket streaming of 100k–300k quantized particles at 20–30 Hz; choose the binary protocol (TSP0, u16)
- [ ] WebGPU Drucker–Prager MLS-MPM patch on Apple GPU and on Chrome/Linux ARM

## Phase 1: analytical simulator, browser only

Models (Python reference + JS twin + tests):

1. [x] CSM disc-cutter forces, penetration, ROP, torque, power, torque limit
2. [ ] Cutter wear and change events (CAI, NTNU CLI)
3. [ ] Face support pressure: Anagnostou–Kovári wedge-silo with seepage, DAUB 2016 p_min/p_max window (wedge-silo without seepage and the DAUB window done, [MODELS](MODELS.md); seepage forces and checking the DAUB factors still open)
4. [ ] EPB chamber pressure mass balance and screw conveyor (Merritt & Mair), FIR/FER conditioning; slurry pressure and filter cake (DIN 4126) (EPB chamber, foam and simplified screw done, [MODELS](MODELS.md); slurry branch and the full Merritt & Mair screw model still open)
5. [ ] Thrust and torque component decomposition (shield friction, face, tools, tail seal, backup)
6. [x] Hoek–Brown/GSI parameters, rock-mass modulus
7. [ ] Convergence–confinement: GRC (Carranza-Torres & Fairhurst), support curves, LDP (Vlachopoulos & Diederichs)
8. [ ] Squeezing (Hoek & Marinos) and shield jamming (Ramoni & Anagnostou)
9. [x] Settlement trough (Peck, O'Reilly & New, Attewell & Woodman) and Burland damage categories
10. [ ] Segment lining (Muir Wood, Duddeck–Erdmann), jack loads, taper ring selection, annular grout volume/pressure
11. [ ] Drill & blast: Holmberg/Langefors pattern, Kuz-Ram fragmentation, PPV limits

Client:

- [x] Hard-rock single-shield demo: CSM-driven advance, boring/ring-build cycle, Jolt muck, alarms
- [ ] EPB TBM: chamber pressure gauges, screw speed control, conditioning, settlement heatmap on the surface with buildings
- [ ] Geology editor along the alignment; scenario files (JSON)
- [ ] Downtime / activity-time model (discrete-event) for realistic utilisation; downtime broken down by subsystem
- [ ] Open TBM signal schema and CSV/OPC-UA-style export of simulated machine data
- [ ] Machine presets named by class, never by brand (e.g. "7.1 m urban EPB", "14.4 m hard-rock main beam"), built from published spec numbers ([industry survey](research/industry-survey.md))
- [ ] Advance-rate check: simulated best day/week/month versus the industry world-record table by diameter class, as an upper bound
- [ ] Guidance loop: simulated total station and active target (noise, line-of-sight loss in curves), head/tail deviation from the design alignment, steering by differential thrust-cylinder pressure, tolerance alarms (default ±75 mm)
- [ ] Ring building: universal-ring key-position selection (tailskin clearance, even cylinder strokes, look-ahead over several rings), segment placement trainer
- [ ] Cutter change logistics: wear-driven change events, intervention time, hyperbaric interventions for closed-mode machines
- [ ] Spoil removal capacity (conveyor or muck trains) as a limit on advance
- [ ] Shift reports and timeline replay of a drive (settlement against TBM position, ring QA, tool wear)

## Phase 2: server ground physics (Newton on the DGX Spark)

- [ ] Newton MPM face and chamber, two-way coupled to cutterhead, screw and shield
- [ ] Calibrate against analytical face pressure and screw discharge
- [ ] Slurry machine variant with a pump-circuit model
- [ ] Mode switching on the same machine (EPB ↔ slurry ↔ open, variable-density style) while face pressure is held; convertible rock/EPB machines
- [ ] Record and replay for GPU-free web demos

## Phase 3: method breadth

- [ ] Open gripper and double shield (gripper/shoe kinematics, Kamino closed loops)
- [ ] Continuous advance: lining installed while mining, with no ring-build stop; small-diameter machines launched from the surface (porting)
- [ ] NATM/SEM sequencing with CCM/LDP and shotcrete ageing E(t); shotcrete deposition
- [ ] Drill & blast cycle: jumbo, charging, blast, ventilation, mucking
- [ ] Roadheader (Bilgin ICR, Evans pick forces)
- [ ] Pipe jacking and microtunnelling (jacking force, lubrication)
- [ ] Shaft sinking (VSM, caisson); cut-and-cover with props, dewatering and basal heave
- [ ] Tunnel ventilation (1-D network, reduced-order models)

## Phase 4: fidelity and validation (ongoing)

- [ ] Surrogates from Kratos staged-excavation runs (settlement, lining forces) and DEM cutter–rock runs
- [ ] Calibration on open datasets (Yinsong hard-rock TBM dataset; RMRE 2025 synthetic datasets) and partner data
- [ ] Uncertainty: random fields of GSI and UCS
- [ ] Validation report per model, with published case histories (e.g. Jubilee Line Extension settlement, CIRIA SP200)

## Phase 5: training and research

- [ ] Scenario editor, trainee scoring, instructor station
- [ ] Training curriculum: EPB scenario set (after the 2017 Colorado School of Mines operator-simulator paper), erector trainer, trainee records
- [ ] Multi-user sessions; optional OPC UA server with neutral tag names; IFC 4.3 / LandXML import and export of alignment and as-built rings
- [ ] Gymnasium environments (face-pressure control, steering); ROS 2 bridge shared with the sister project
