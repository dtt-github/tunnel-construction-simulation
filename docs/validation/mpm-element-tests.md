# MPM element tests (Phase 2, WP1)

- **Plan:** [Phase 2, WP1](../plans/phase2-mpm-face-chamber.md#wp1-material-model-and-element-tests-about-2-weeks).
- **Code:** [`server/tunnelsim_server/`](../../server/tunnelsim_server/):
  - `materials.py` (the mapping);
  - `scenes/k0.py`, `scenes/rankine.py`, `scenes/collapse.py`.
- **Run records:** [`server/results/`](../../server/results/), one JSON per run with versions, parameters and GPU load.
- **Tests:** [`server/tests/`](../../server/tests/), including two GPU checks pinned on the results below.
- **Solver:** Newton 1.7.0 implicit MPM, Warp 1.19.0, on the DGX Spark. The GPU was shared during these runs, so timings are lower bounds. The physics does not depend on GPU load.
- **Run on:** 5 Nov 2026

## The material model

Reading Newton's solver shows its yield criterion is a Drucker–Prager cone. The source is `shear_yield_stress` in `rheology_solver_kernels.py`, using the orthonormal DB16 stress basis of `warp.fem.SymmetricTensorMapper`:

**√J2 ≤ s + μ·p**

- p is the mean pressure, compression positive;
- s is `yield_stress`;
- μ is `friction`;
- `dilatancy` = 0 selects the non-associated flow rule (no plastic volume change, ψ = 0).

Rousseau et al. (2022, eq. 2.4) write the same criterion, ‖Dev σ‖ ≤ μp with ‖τ‖ = √(τ:τ/2). So their measured μ carries over unchanged.

**Matching a Mohr–Coulomb soil.** Phase 0 assumed μ = tan φ′. The two standard matches are:

| Match | μ | μ = 0.75 means |
|---|---|---|
| plane strain, ψ = 0 | sin φ′ | φ′ = 48.6° |
| triaxial compression | 2√3 sin φ′ / (3 − sin φ′) | φ′ = 32.3° |

The Rankine test below decides which one the solver follows.

## K0 under gravity: failed

A 1 × 1 × 2 m sand column between frictionless walls, loaded by its own weight, read after 2 s (it is static after 1 s). E 5 MPa, φ′ 34°. Poisson's ratio is set so that the elastic ratio ν/(1 − ν) equals the target K0.

| Target K0 (ν) | E | K = σh/σv measured | σv / γz |
|---|---|---|---|
| 0.15 (0.130) | 5 MPa | 0.78 | 0.99 |
| 0.44 = 1 − sin 34° (0.306) | 5 MPa | 0.76 | 0.99 |
| 0.90 (0.474) | 5 MPa | 0.74 | 0.99 |
| 0.44 (0.306) | 50 MPa | 0.82 | 0.99 |

- **Vertical stress is right:** σv = γz within 1 %.
- **Horizontal stress doesn't follow Poisson's ratio.** K is 0.74–0.86 whatever ν is, rising with stiffness and resolution (0.86 at D/40). The column also settles 2–5 cm, much more than elasticity allows: the particle packing compacts.
- **Newton's default material** is rigid-plastic (E = 10¹⁵ Pa). It stores no particle stress at all, so Phase 0 never had an at-rest state to read.

**Consequence:** the at-rest stress is not taken from the MPM. As the plan's fallback says, the face and chamber start from the analytical at-rest state (K0 = 1 − sin φ′). The MPM is used for the failure phase, where the limit pressure does not depend on the initial stress.

## Shear strength: Rankine active wall in place of simple shear

**Why not simple shear.** Newton's colliders are moved kinematically and cannot hold a constant normal stress, so a simple-shear test under constant normal load is not possible.

**The test instead.** A 4 m long, 2 m high, 1 m wide sand block sits on a rough base between frictionless side walls (plane strain). A frictionless front wall moves away at 0.05 m/s. K_a = 2F / (γH²W) is read on the plateau at 0.5–3 % of H of wall movement; beyond that the soil slumps after the wall.

Rankine gives K_a = (1 − sin φ′)/(1 + sin φ′).

| μ | φ′ if μ = sin φ′ | Rankine K_a | MPM, voxel H/10 | MPM, H/20 | MPM, H/40 | Triaxial match predicts | μ = tan φ′ predicts |
|---|---|---|---|---|---|---|---|
| 0.35 | 20.5° | 0.481 | 0.451 | 0.473 | – | 0.568 | 0.503 |
| 0.559 | 34.0° | 0.283 | 0.286 | 0.301 | 0.357 (0.329 with 200 iterations) | 0.411 | 0.344 |
| 0.75 | 48.6° | 0.143 | 0.189 | 0.195 | – | 0.304 | 0.250 |

**What this shows:**

- **The plane-strain match is the right one.** For φ′ up to 34° the MPM is within −6 % to +6 % of Rankine at H/10–H/20, and the triaxial and tan φ′ matches are far off. **μ = sin φ′ (ψ = 0) is now the project's mapping**, and it is not tuned again in later packages.
- **High friction is weaker than the mapping.** At φ′ ≈ 49° the solver acts about 10 % weaker in sin φ′ terms: K_a 0.19 against 0.143.
- **Refining the grid makes the soil weaker.** At H/40, K_a is 16–26 % above Rankine, depending on the solver iterations. That is the same direction as Phase 0's face runs, which needed more support on finer grids. The solver does not converge to the limit-analysis value with refinement in this range.
  - **For WP2:** the face calibration must be done at the production resolution and checked across resolutions, not assumed to converge.

## Granular column collapse: Rousseau et al. (2022)

**Source.** Rousseau, Metivet, Rousseau, Daviet & Bertails-Descoubes, [arXiv:2211.04865](https://arxiv.org/abs/2211.04865), data [doi:10.5281/zenodo.7288829](https://doi.org/10.5281/zenodo.7288829) (CC-BY 4.0). Measured values are from their Tables 1–2.

**Set-up as theirs:**
- a 6 cm wide flume with a 2 cm erodible bed of the same material, inclined 0–20° (gravity tilted);
- **glass beads:** μ = μ_a 0.44, ρ 1470 kg/m³, wall friction 0.23;
- **granules:** μ = μ_a 0.75, ρ 1520 kg/m³, wall friction 0.30;
- rigid-plastic, as theirs;
- 5 mm voxel, about 190k particles.

**Assumed.** The gate is lifted at 1 m/s; the paper does not give its speed. Removing the gate at once changes nothing at the 5 mm threshold for B00 (0.180 m either way).

The runout is the distance from the gate to where the deposit is thinner than 5 mm. The paper does not say how it locates the front. A 2.5 mm threshold is also recorded, and is discussed below.

| Run | Material, bed slope | Final height H_f, MPM / measured (m) | Runout, MPM (5 mm) / measured (m) | MPM / measured | Their simulation (m) |
|---|---|---|---|---|---|
| B00 | beads, 0° | 0.107 / 0.11 | 0.180 / 0.18 | 1.00 | 0.19 |
| B05 | beads, 5° | 0.106 / 0.11 | 0.233 / 0.22 | 1.06 | 0.21 |
| B10 | beads, 10° | 0.083 / 0.09 | 0.313 / 0.31 | 1.01 | 0.30 |
| B15 | beads, 15° | 0.058 / 0.07 | 0.468 / 0.49 | 0.95 | 0.46 |
| B20 | beads, 20° | 0.028 / 0.04 | 0.593 / not measured | – | 0.88 |
| G00 | granules, 0° | 0.108 / 0.12 | 0.092 / 0.11 | 0.83 | 0.10 |
| G05 | granules, 5° | 0.117 / 0.12 | 0.128 / 0.15 | 0.85 | 0.13 |
| G10 | granules, 10° | 0.117 / 0.12 | 0.158 / 0.10 | 1.58 | 0.15 |
| G15 | granules, 15° | 0.117 / 0.12 | 0.210 / 0.24 | 0.88 | 0.19 |

**What this shows:**

- **Runouts:** 7 of 8 measured runouts are within ±17 %, as close as the authors' own published simulation (their errors were −13 % to +6 % on the same seven).
- **G10:** 58 % long. Their simulation misses it in the same way (+50 %), which points to the experiment.
- **Final heights:** within 3–11 % on the gentle slopes, and 17–30 % low on the steepest bead runs.
- **B20:** had not come to rest after 4 s.
- **The front threshold matters for thin tails.** At 2.5 mm the steep bead runouts come out much longer (0.53 against 0.31 m for B10). The 5 mm figure matches the measured profiles, but the threshold was not stated by the source, so both are kept in the records.

## Status of the WP1 checks

| Check (plan) | Result |
|---|---|
| K0 within ±10 % of 1 − sin φ′, independent of resolution | **Failed.** 0.74–0.86, independent of ν. The at-rest state comes from the analytical model (plan fallback) |
| Friction mapping fixed | **Done.** μ = sin φ′ (plane strain, ψ = 0): within ±6 % of Rankine for φ′ ≤ 34° at H/10–H/20; weaker at high friction and on finer grids |
| Column runout within the experimental scatter | **Met** for 7 of 8 runs (±17 %), matching the source's own simulation; G10 is an outlier for both |

## Limits

- One solver version (Newton 1.7.0). The golden tests catch a change.
- The resolution dependence (soil weaker on finer grids) is measured, not explained. WP2 must calibrate the face at the resolution it will use.
- The gate speed and the front threshold are assumptions, stated in each run record.
