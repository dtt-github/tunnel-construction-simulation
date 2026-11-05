# Phase 2 plan: GPU ground physics for the EPB face and chamber

- **Status:** approved 5 Nov 2026. WP0 started.
- **Roadmap items:** [Phase 2](../ROADMAP.md#phase-2-server-ground-physics-newton-on-the-dgx-spark): MPM face and chamber coupled to the machine with a pressure-controlled shove; calibration against the analytical face pressure and the screw; record and replay labelled with calibration status. The slurry variant and mode switching are left for a later plan.
- **Starting point:** [Phase 0 results](../../phase0/RESULTS.md).

## 1. Goal

The EPB demo gets a **ground-physics view** of the face and the chamber. A material-point (MPM) soil model on the DGX Spark responds to what the operator does:
- the face holds or fails under the support pressure the operator sets;
- the chamber fills and its pressure rises and falls with the advance and the screw;
- the screw discharges muck.

The analytical models stay in charge of the numbers on the console. The MPM view is shown beside them, never instead of them, and it carries a calibration label:

| Label | Meaning |
|---|---|
| **Uncalibrated** | It runs, but has not passed the checks below. Shown only with this label, or not shown on the public site. |
| **Calibrated against X** | It has passed the named checks within the stated tolerance. The tolerance and the check are linked from the label. |

Everything else in the project's rules applies:
- open, cited sources only;
- nothing from the owner's system;
- Phase 2 data and recordings are produced on our own runs.

## 2. Where Phase 0 left off

| Item | Phase 0 result | What it means for Phase 2 |
|---|---|---|
| Face, dry sand, retracting plate | Right mechanism: limit pressure independent of cover, falls with φ. 0.53 / 0.66 / 0.79 of Vermeer at D/10, D/15, D/20 | Resolution decides the answer. D/10 halves the required support |
| At-rest pressure | 7–20 kPa against K₀γz = 18.8 kPa, resolution-dependent; Newton's default material is rigid-plastic (E = 10¹⁵ Pa) | The installed solver also has finite E and ν, cohesion (`yield_stress`), tensile yield, dilatancy, hardening and softening. These were not used in Phase 0 |
| Chamber, cutterhead, screw | 0.4–0.8× real time on a shared GPU; pressure linear with depth; about 950 kNm from mixing | Speed is close. Pressure is gravity-only (≈ 0.5 bar), because the piston was speed-driven |
| Screw | Discharge falls with rpm; inlet only 4 voxels across | Not credible yet: it needs chamber pressure and a resolved inlet |
| Streaming | TSP0 u16, 300k particles at 30 Hz, about 1.5 ms server and 1 ms browser | Ready. Bandwidth (54 MB/s) limits remote viewers |
| GPU | Shared with the sister project (91 % busy on 5 Nov 2026) | Timings so far are lower bounds; a scheduling rule is needed |

## 3. Calibration and validation targets

All open or freely readable. Numbers are quoted, the documents are not redistributed. A target used to **calibrate** a parameter is not also used to **validate** it.

| Target | What it gives | Access | Use |
|---|---|---|---|
| Vermeer, Ruse & Marcher (2002), Felsbau 20(6); the project's `face_support` models (wedge-silo, DAUB window) | Limit support pressure in drained ground, p_f = γ D N_γ, independent of cover | already used in Phase 0 | analytical bracket for the face |
| Idinger, Aklik, Wu & Borja (2011), Acta Geotech. 6:105–117, [doi:10.1007/s11440-011-0139-2](https://doi.org/10.1007/s11440-011-0139-2); [author copy](https://web.stanford.edu/~borja/pub/ag2011(1).pdf) | Centrifuge (50g, 5 m prototype), dry sand φ 34°. Table 2: required support 6.5–9.5 / 4.5–6.0 / 3.0–6.0 kPa at C/D 1.5 / 1.0 / 0.5, tending to about 6 kPa at 3–5 % of D. Table 3: failure tip depth, wedge angle 64–68°, settlement. Table 2 also restates the Chambon & Corté and Kirsch ranges | author copy | **validation** of the dry-sand face: pressure, mechanism and settlement |
| Wang et al. (2024), Underground Space 16:164–182, [doi:10.1016/j.undsp.2023.11.001](https://doi.org/10.1016/j.undsp.2023.11.001) | MPM (Anura3D, Mohr–Coulomb) against 1g tests (Liu et al. 2019): Pu/P₀ 0.206 / 0.167 / 0.109 measured at C/D 0.5 / 1 / 2, with P₀ = K₀γ(C + D/2); parameters in Table 1 | open (CC BY-NC-ND) | **validation**, a second sand dataset; a code-to-code check of the mechanism (bulb to chimney) |
| Leca, Garnier, Chambon et al. (1997), ICSMFE Hamburg, [PDF](https://www.issmge.org/uploads/publications/1/31/1997_03_0008.pdf) | LCPC centrifuge, 5 m prototype, C = 2D: about 5 kPa stabilises the face; failure zone about 0.5D ahead | open | cross-check |
| Durand, Saboya, Tibana & Cabral (2026), ICPMG Zurich, [PDF](https://www.issmge.org/uploads/publications/53/144/ICPMG2026-164.pdf) | Centrifuge, loose and dense sand, C/D 0.5–2: face displacement and surface settlement against support pressure; chimney to the surface at C/D ≤ 1, local wedge at 2 | open | **validation** of settlement before collapse |
| Kimura & Mair (1981), 10th ICSMFE, [PDF](https://www.issmge.org/uploads/publications/1/35/1981_01_0061.pdf) | Centrifuge, kaolin cu 26 kPa: stability ratio N = (σv − σT)/cu at collapse against C/D (constant above C/D ≈ 3; 3–9 for C/D 1–3); the Broms & Bennermark N ≈ 6 | open | **validation** of the undrained clay face (London Clay route) |
| Rousseau et al. (2022), [arXiv:2211.04865](https://arxiv.org/abs/2211.04865), data [doi:10.5281/zenodo.7288829](https://doi.org/10.5281/zenodo.7288829) (CC-BY) | Drucker–Prager MPM granular column collapse against experiments; μ should be the avalanche, not the stop, angle | open | **calibration** of the friction mapping (element test) |
| Borio & Peila (2011), Gospodarka Surowcami Mineralnymi 27(1), [free](https://czasopisma.pan.pl/Content/118913) | Laboratory screw (30°, 168 mm casing, 100 mm pitch), conditioned soil (FER 16, FIR 30 %), pressure cells along the screw at 6 rpm, tank at 60 and 90 kPa | free | **validation** of the pressure drop along the screw |
| Guangzhou–Foshan EPB data, [doi:10.17632/cjwbjttf88.1](https://doi.org/10.17632/cjwbjttf88.1) (CC BY 4.0), and Changsha Line 4, [doi:10.17632/ndy5r67zxz.1](https://doi.org/10.17632/ndy5r67zxz.1) | Upper and lower earth pressure, chamber pressure, thrust and torque per ring | open, already used | **validation** of the chamber pressure gradient and level |

**Not available openly:**
- Chambon & Corté (1994) and Kirsch (2010) originals (secondary values via Idinger);
- Mair (1979);
- Merritt & Mair (2006, 2008), the screw discharge against rpm;
- any CC-BY field data pairing EPB face pressure with volume loss.

So screw discharge can only be checked against the theoretical capacity and the Phase 0 trend, and it stays labelled accordingly.

## 4. Work packages

Each package ends with a check. A package is done only when its check passes, or when its failure is written up and accepted.

### WP0: platform and rules (about 1 week)

- **GPU scheduling** with the sister project: either reserved hours or MPS partitioning. All timings are repeated on an idle GPU, and every log records GPU load.
- **Golden tests.** Short seeded runs whose key outputs (limit pressure, at-rest pressure, discharge) are pinned in `server/tests/`, to catch Newton upgrades. Newton 1.7 already changed MPM material scaling once.
- **`server/` layout:**
  - `scenes/` (face, chamber, screw);
  - `materials.py` (soil parameters to Newton parameters, with sources);
  - `probes.py` (plate and bulkhead pressures, torque, discharge, face displacement);
  - `runner.py` (batch runs to JSON);
  - `live.py` (WebSocket server).
- **Run records:** every run writes its Newton/Warp version, parameters, resolution, seed and calibration status next to the results.

**Check:** the Phase 0 face run is reproduced within 2 % on an idle GPU, and its golden test passes.

### WP1: material model and element tests (about 2 weeks)

- Map φ′, c′ (or cu), E, ν, ψ and γ to Newton's `friction`, `yield_stress`, `yield_pressure`, `tensile_yield_ratio`, `dilatancy`, `young_modulus`, `poisson_ratio` and `hardening`. The mapping, with its derivation, goes in `materials.py` and `docs/MODELS.md`.
- **Element tests in MPM:**
  - **Gravity loading** of a soil column with finite E: K₀ against Jaky (1 − sin φ′).
  - **Simple shear** of a block: peak friction against the input φ′.
  - **Granular column collapse** against the Rousseau et al. dataset (runout and final height for aspect ratios up to about 10), using their μ.

**Check:**
- K₀ within ±10 % of 1 − sin φ′, independent of resolution between D/10 and D/20;
- column runout within the experimental scatter of the dataset;
- the friction mapping is fixed here and not tuned again later.

### WP2: dry-sand face with pressure control (about 3 weeks)

- **Pressure control.** Replace the retracting plate with a pressure-controlled face: the support pressure is set and lowered in steps, and face displacement is measured. This is how the centrifuge tests were run, and how the demo's operator acts.
- **Idinger's prototype:** 5 m, φ 34°, ρd 1.5 t/m³, C/D 0.5, 1.0 and 1.5. Also Wang et al.'s geometry (C/D 0.5, 1, 2).
- **Resolution study** at D/10, D/15, D/20 and D/30. If uniform D/20 is too slow, test local refinement near the face: a finer particle spacing in a box ahead of the face.
- **Outputs:**
  - support pressure against face displacement;
  - the pressure at 3–5 % of D;
  - failure tip depth and wedge angle;
  - surface settlement and its position ahead of the face.

**Check:**
- **Pressure:** within Idinger's measured range at each C/D, and within ±25 % of Wang et al.'s Pu/P₀.
- **Cover:** the same independence from cover as Vermeer (above C/D ≈ 1).
- **Mechanism:**
  - wedge angle within ±5° of 64–68°;
  - chimney to the surface at C/D 0.5 but not at 1.5.
- **Production resolution:** the coarsest resolution that passes. If none that runs live passes, the live view gets a stated correction factor and the label says so.

### WP3: undrained clay face (about 2 weeks)

- Tresca-like material (friction 0, `yield_stress` = cu, finite E), as on the SEM page.
- Kimura & Mair's geometry (D 4.5–7.5 m prototype, C/D 1.5–3, kaolin cu 26 kPa). Support pressure is lowered to collapse.
- Then the London route: London Clay and Lambeth Group from the scenario, with Crossrail's undrained design lines.

**Check:**
- N at collapse inside the published band (3–9 for C/D 1–3), and constant above C/D ≈ 3;
- N ≈ 6 stays a conservative bound for an unlined heading length below 1D.

### WP4: EPB chamber with a pressure-controlled shove (about 3 weeks)

- The shield and face advance under a **thrust**, not a fixed speed. Thrust balances chamber pressure, face resistance and shield friction from the analytical thrust model.
- Conditioned soil from the WP1 mapping, with paste parameters stated as assumptions until a source is found. Chamber pressure is held at 1–3 bar by the screw speed, as on the console today.
- **Outputs:**
  - bulkhead pressure in three bands;
  - its vertical gradient;
  - cutterhead torque from mixing;
  - response time to a screw-speed step.

**Check:**
- The vertical pressure gradient falls within the range of the Guangzhou–Foshan and Changsha upper/lower earth-pressure records at similar depth (open data already in the repository).
- The chamber holds a target within the demo's control band. That band (±0.2–0.3 bar) is still marked unverified in the research survey; it needs a source before this check is final.
- Torque from mixing stays below the installed 9.8 MNm.

### WP5: screw conveyor (about 3 weeks)

- **Resolved inlet:** at least 8 voxels across the screw, with local refinement in the casing. Walls at least one voxel thick, as Phase 0 learnt.
- **Borio & Peila's rig** at 6 rpm and 60 / 90 kPa tank pressure: pressure at the cells along the screw.
- **Discharge against rpm** at the demo's scale, compared with the theoretical capacity (Merritt & Mair's formula, already in `epb_chamber.py`).

**Check:**
- The pressure profile along the screw is within ±25 % of Borio & Peila at the cells.
- Discharge rises with rpm up to a volumetric efficiency that stays below 1.

Discharge against rpm has no open measured data. It stays labelled "checked against theory only".

### WP6: live coupling to the EPB demo (about 3 weeks)

- `live.py` runs the face and chamber scene and takes the console inputs over the WebSocket: advance or thrust, cutterhead rpm, screw rpm, target pressure.
- It streams particles (TSP0 u16 + u8 material or speed) and probe values at 20–30 Hz.
- **Browser:** the EPB demo gets a "Ground physics" panel and view. It shows the MPM chamber and face beside the analytical gauges, with both values next to each other and the calibration label. If no server is reachable, it plays a recording (WP7).
- **Performance budget:** the live scene runs at at least 1× real time at the production resolution of WP2/WP4, with time scaling handled as today (the MPM runs only around the face and chamber; the drive between is analytical). If 1× is not reached, the live view runs slower than real time and says so.

**Check:**
- An operator can drop the support pressure below the WP2 limit and see the face move. Raising it stops the movement.
- The chamber gauges in both views agree within the WP4 tolerance.

### WP7: recordings for the public site (about 1 week)

- Short recorded runs, each with its calibration label and settings:
  - a stable face at the DAUB window;
  - support lowered to collapse in sand and in clay;
  - the chamber and screw responding to a screw-speed step.
- They play in the browser without a GPU, replacing the Phase 0 replays on the landing page.

**Check:** each recording links to its validation page. The landing card says which checks it passed.

### WP8: documentation (throughout)

- `docs/validation/mpm-face.md`, `mpm-chamber.md` and `mpm-screw.md`, in the same form as the other validation pages: data, set-up, results, limits.
- `MODELS.md` section "MPM ground physics"; realism checklist rows for the ground-physics view; roadmap and changelog.

## 5. Order and size

| Order | Package | Size (person-weeks, rough) | Depends on |
|---|---|---|---|
| 1 | WP0 platform and rules | 1 | – |
| 2 | WP1 material and element tests | 2 | WP0 |
| 3 | WP2 dry-sand face | 3 | WP1 |
| 4 | WP3 clay face | 2 | WP1 (parallel to WP2 once the mapping is fixed) |
| 5 | WP4 chamber with pressure-controlled shove | 3 | WP1 |
| 6 | WP5 screw | 3 | WP4 |
| 7 | WP6 live coupling | 3 | WP2, WP4 |
| 8 | WP7 recordings | 1 | WP2–WP6 |

About 18 person-weeks in all. The first milestone that can be shown publicly is the end of WP2: a calibrated dry-sand face collapse, recorded, with its validation page. That is about 6 weeks in.

## 6. Risks

| Risk | Effect | Response |
|---|---|---|
| D/20 or finer is needed for the face and does not run live | The live view underestimates the support pressure | Local refinement; a smaller live domain; a stated correction factor in the label; recordings at full resolution |
| The elastoplastic material does not give a stable at-rest state | WP1 fails | Initialise stresses from the analytical K₀ and keep the MPM only for the failure phase; say so on the page |
| The shared GPU slows every run | Timings and the schedule slip | WP0 scheduling rule; idle-GPU timings only for decisions |
| Newton changes material scaling again | Calibration silently shifts | Golden tests; versions pinned; recalibrate on purpose |
| Conditioned-soil parameters have no open source | Chamber and screw stay partly assumed | Labelled as assumptions; validated on what is measurable (gradient, screw pressure profile) |
| No open screw discharge data | Discharge can't be validated | Label "checked against theory only"; keep asking for partner data (outreach) |
| Remote viewers lack bandwidth | The live view is local only | Active-particle streaming and 10–15 Hz options from Phase 0; recordings for everyone else |

## 7. Decisions (5 Nov 2026)

1. **GPU time:** reserve hours with the sister project. Each run records the GPU load it saw, and timings for decisions come only from reserved, idle hours.
2. **Live view:** local only for now (on the Spark). The public site gets recordings.
3. **First ground:** dry sand (WP2), then clay (WP3).
