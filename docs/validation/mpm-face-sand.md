# MPM tunnel face in dry sand (Phase 2, WP2)

- **Plan:** [Phase 2, WP2](../plans/phase2-mpm-face-chamber.md#wp2-dry-sand-face-with-pressure-control-about-3-weeks).
- **Code:** [`server/tunnelsim_server/scenes/face_sand.py`](../../server/tunnelsim_server/scenes/face_sand.py). Runs with `python -m tunnelsim_server.runner face_sand ...`; one JSON record per run in [`server/results/`](../../server/results/) (`fs_*`).
- **Tests:** `server/tests/test_face_sand_gpu.py`.
- **Solver:** Newton 1.7.0 implicit MPM, rigid-plastic Drucker–Prager with μ = sin φ′ and no dilation (the [WP1 mapping](mpm-element-tests.md)).
- **Status:** **uncalibrated, bracketed.** After WP1b, Idinger's measured pressures lie between the two Drucker–Prager cone matches at every cover. No single cone matches pressure, wedge and settlement together (see below).
- **Run on:** 5 Nov 2026
- **WP0b re-baseline (5 Nov 2026):**
  - The new packing default (particle radius 0.7 h, cohesion and stiffness divided by the packing; see [mpm-clay](mpm-clay.md#wp0b-correction-5-nov-2026)) moves the face pressures at 5 % of D by 1–6 % (records `*_r07`). The tables below keep the WP2 numbers.
  - The servo is slower: at most 0.01 D/s over 5 s.

## Set-up

- **Model:** a half-model like Idinger's centrifuge tests. A frictionless symmetry wall runs through the tunnel axis, with a shield tube behind the face and a face plate inside it. The base, back and front of the block are at 0.75D, 0.75D and 2.5D from the tunnel; the side wall is 1.5D away.
- **Displacement control** (as in the experiments): after 1 s of settling, the plate retracts into the shield to 5 % of D at 0.025 D/s, and the soil pressure on it is recorded.
  - Slower rates change the pressure by at most +7 % (0.0025–0.01 D/s: 8.7–9.3 kPa against 8.6), within the run-to-run scatter.
- **Pressure control** (for the live view): a retract-only servo lets the plate give way while the soil pressure on it is above a target.
- **Scale:** prototype scale, D = 5 m. A cohesionless rigid-plastic soil has no length scale, so p/(γD) does not depend on D.
- **Outputs:**
  - the pressure at 1, 3 and 5 % of D;
  - the moving zone: displacement above 0.2 % of D since the retraction began, within 0.25D of the symmetry plane;
  - its top above the crown, and whether it reaches the surface;
  - the wedge inclination, as atan(D / extent at crown level), following Idinger's Table 3;
  - the largest surface settlement and its position.

## Data

| Source | What it gives | Access |
|---|---|---|
| Idinger, Aklik, Wu & Borja (2011), Acta Geotech. 6:105–117, [doi:10.1007/s11440-011-0139-2](https://doi.org/10.1007/s11440-011-0139-2), [author copy](https://web.stanford.edu/~borja/pub/ag2011(1).pdf) | 50 g centrifuge, half-model, D = 100 mm (5 m prototype), dry loose sand, ρd 1.5 t/m³, φ 34° from direct shear. **Table 2:** required support at C/D 1.5 / 1.0 / 0.5 of 6.5–9.5 / 4.5–6.0 / 3.0–6.0 kPa (prototype). The same table lists Vermeer et al. 7.5–10.5, Kirsch 6.0–11.3 and Chambon & Corté 3.0–6.0 kPa. **Table 3** (5 % of D): failure zone up to 85 mm below the surface at C/D 1.5, 50 mm at 1.0, reaching the surface at 0.5; wedge 68.0 / 66.5 / 64.0°; largest settlement 0.95 / 1.03 / 5.51 mm (model scale). The text gives 100 mm at C/D 1.5 where the table gives 85 mm | author copy |
| Wang et al. (2024), Underground Space 16:164–182, [doi:10.1016/j.undsp.2023.11.001](https://doi.org/10.1016/j.undsp.2023.11.001) | 1g tests of Liu et al. (2019), D = 0.15 m, γ 15.5 kN/m³, φ 33.1°, c 0 (Table 1). **Table 2:** measured Pu/P₀ = 0.206 / 0.167 / 0.109 at C/D 0.5 / 1 / 2, with P₀ = K₀γ(C + D/2), K₀ = 1 − sin φ | open (CC BY-NC-ND) |

## Results

### Pressure against Idinger (kPa, prototype)

| C/D | MPM D/10, 3 % / 5 % of D | MPM D/20, 3 % / 5 % | Measured | Vermeer (φ 34°) |
|---|---|---|---|---|
| 0.5 | 8.0 / 8.0 | 9.7 / 10.3 | 3.0–6.0 | 8.4 |
| 1.0 | 7.6 / 8.6 | 9.5 / 10.3 | 4.5–6.0 | 8.4 |
| 1.5 | 8.2 / 8.7 | 10.0 / 10.4 | 6.5–9.5 | 8.4 |

At C/D 1.0 the 5 % pressure is 8.6 kPa at D/10, 10.3 at D/20 and 10.3 at D/30 (2.8 million particles). The face converges between D/20 and D/30.

### Pressure against Wang et al. / Liu et al. (Pu/P₀)

| C/D | MPM D/10 | MPM / measured | MPM D/20 | MPM / measured | Measured |
|---|---|---|---|---|---|
| 0.5 | 0.252 | 1.22 | 0.319 | 1.55 | 0.206 |
| 1 | 0.181 | 1.09 | 0.214 | 1.28 | 0.167 |
| 2 | 0.102 | 0.93 | 0.127 | 1.17 | 0.109 |

### Mechanism and settlement against Idinger (D/10, at 5 % of D)

| C/D | Moving zone top above the crown | Reaches the surface (MPM / Idinger) | Wedge (MPM / Idinger) | Largest settlement / D (MPM / Idinger) |
|---|---|---|---|---|
| 0.5 | 0.48D (the surface) | yes / yes | 53.8° / 64.0° | 0.076 / 0.055 |
| 1.0 | 0.97D (the surface) | yes / no, 0.5D below | 53.6° / 66.5° | 0.057 / 0.010 |
| 1.5 | 1.47D (the surface) | yes / no, 0.85D below | 53.8° / 68.0° | 0.039 / 0.0095 |

### Dilatancy as a sensitivity, not a calibration (C/D 1.0, D/10)

| Newton `dilatancy` | Pressure at 5 % (kPa) | Zone top above the crown | Wedge | Settlement / D |
|---|---|---|---|---|
| 0 (WP1 mapping) | 8.6 | 0.97D (the surface) | 53.6° | 0.057 |
| 0.3 | 6.6 | 0.98D (the surface) | 57.5° | 0.015 |
| 1.0 | 4.9 | 0.17D | 68.9° | ≈ 0 |
| Idinger, measured | 4.5–6.0 | 0.5D | 66.5° | 0.010 |

### Pressure control (C/D 1.0, D/10, retract-only servo, 2 s; WP0b: 0.01 D/s, 5 s)

- **WP0b change:** with the new packing, the servo at 0.025 D/s outran the soil and cycled between about 2 and 25 kPa.
- **New default:** at most 0.01 D/s over 5 s. At 12 kPa the face holds after 0.0017 D (p 11.8 kPa); at 6 kPa it gives way to 0.05 D (p 9.2 kPa).
- **The table** keeps the WP2 runs.

| Target (kPa) | Face movement / D | Final soil pressure (kPa) |
|---|---|---|
| 12 (above the limit) | 0.004, then it holds | 12.0 |
| 6 (below) | 0.050, still moving at the maximum rate | 8.5 |
| 3 (below) | 0.050, still moving at the maximum rate | 8.5 |

## What this shows

- **Pressure:**
  - **Against Wang et al.:** **met at D/10.** All three covers are within ±25 % (−7 % to +22 %), and the drop with cover is right.
  - **Against Idinger:** **not met** at C/D ≤ 1. The MPM is 40–100 % above the measured range and sits on the analytical values Idinger lists (Vermeer 8.4, Kirsch 6.0–11.3), while their loose sand needed less.
  - **Refinement:** a finer grid raises the pressure by about 20 % (D/20 ≈ D/30), so the D/10 agreement with Wang et al. is partly the grid. The finer grids converge to about 1.2× Vermeer.
- **Mechanism and settlement: not met.** The moving zone always reaches the surface, the wedge is 10–14° too flat, and settlement is 4–6× too large at C/D 1–1.5.
  - **The cause:** the plastic flow has no volume change, so the whole face movement is carried up a chimney to the surface. Real sand dilates as it shears and arches over the face.
- **Dilatancy controls all of this.** Raising Newton's dilatancy factor moves the pressure, wedge and settlement towards Idinger together. At 1.0 the pressure and wedge match, but the zone and settlement become too small.
  - **Why it isn't set here:** the factor's meaning (how it maps to a dilation angle ψ) has not been derived from the solver. Choosing it to match Idinger would make Idinger a calibration target, not a check.
  - **What should set it:** an independent source, such as Bolton's (1986) relation for a loose sand (Idinger's Dr ≈ 30 %).
- **Pressure control: met.** Above the limit the face holds at the target; below it the face keeps moving. That is the behaviour the live view needs.
  - A first servo that also pushed the plate back into the soil oscillated, and pressure spikes from the pushing inflated the readings. The retract-only servo replaced it.

## Status of the WP2 checks

| Check (plan) | Result |
|---|---|
| Pressure within Idinger's measured range at each C/D | **Not met** at C/D 0.5 and 1.0 (MPM 8.0–10.3 kPa against 3.0–6.0 and 4.5–6.0). Met at 1.5 at D/10 (8.7 in 6.5–9.5) |
| Pressure within ±25 % of Wang et al.'s Pu/P₀ | **Met at D/10** (0.93–1.22); not at D/20 (1.17–1.55) |
| Independent of cover above C/D ≈ 1 | **Met** (8.6–8.7 kPa at D/10, 10.3–10.4 at D/20) |
| Wedge 64–68° ± 5°; chimney to the surface at C/D 0.5 but not at 1.5 | **Not met** (54°; the chimney reaches the surface at every cover) |
| Production resolution | D/10 runs at about 1× real time with a shared GPU (27–35 ms per 16.7 ms frame); D/20 at about 0.13× |
| Pressure control holds above the limit and gives way below | **Met** |

## Prediction with dilation from Bolton (WP1b)

WP1b derived Newton's dilatancy factor and checked it ([element tests](mpm-element-tests.md#dilatancy-wp1b)). The WP2 runs were then repeated with ψ = 4.7° from Bolton (1986) for Idinger's sand (Dr 0.30): μ 0.551, θ 0.148. Nothing was tuned to Idinger.

| C/D | Pressure at 5 % D (kPa), D/10 / D/20 | Before (ψ 0), D/10 | Measured | Settlement / D, D/10 (before) | Measured | Zone to the surface (Idinger) | Wedge (Idinger) |
|---|---|---|---|---|---|---|---|
| 0.5 | 7.6 / 9.9 | 8.0 | 3.0–6.0 | 0.063 (0.076) | 0.055 | yes (yes) | 54° (64°) |
| 1.0 | 7.5 / 9.7 | 8.6 | 4.5–6.0 | 0.030 (0.057) | 0.010 | yes (no) | 55° (66.5°) |
| 1.5 | 7.9 / 9.7 | 8.7 | 6.5–9.5 | 0.018 (0.039) | 0.0095 | yes (no) | 54° (68°) |

**Bolton's range** (C/D 1.0, D/10): ψ 3.2° gives 7.7 kPa and 0.037D; ψ 7.1° gives 7.3 kPa and 0.022D.

**What dilation explains:**
- **Settlement:** it halves, and comes within 1.1× (C/D 0.5) to 3× (C/D 1.0) of the measurements.
- **Pressure:** it drops by about 10 %, and is still 25–70 % above Idinger at C/D ≤ 1.
- **Mechanism:** the chimney still reaches the surface, and the wedge stays at 54–56°.

### The remaining gap: the shape of the Drucker–Prager cone

A Drucker–Prager cone is round in the deviatoric plane, while Mohr–Coulomb's is a hexagon. It can match φ′ in one stress state only:
- **matched in plane strain** (the WP1 mapping, μ = sin φ′), φ′ = 34° is only 24.6° in triaxial compression;
- **matched in triaxial compression** (μ = 0.794), the same φ′ is 52° in plane strain.

A 3D face has zones close to both. The two matches therefore bracket the face, without anything being tuned (D/10, ψ 0):

| C/D | Pressure, triaxial match / plane-strain match (kPa) | Idinger, measured | Wedge, triaxial / plane-strain match | Idinger | Settlement / D, triaxial match |
|---|---|---|---|---|---|
| 0.5 | 4.0 / 8.0 | 3.0–6.0 | 61.8° / 53.8° | 64.0° | 0.099 |
| 1.0 | 4.1 / 8.6 | 4.5–6.0 | 62.0° / 53.6° | 66.5° | 0.078 |
| 1.5 | 4.4 / 8.7 | 6.5–9.5 | 66.4° / 53.8° | 68.0° | 0.065 |

- **Pressure:** Idinger's measurements lie inside the bracket at every cover.
- **Wedge:** the triaxial match gets it close (62–66° against 64–68°).
- **Settlement:** neither match without dilation comes close. With Bolton's dilation the plane-strain match is nearest.

**Consequence.** Newton offers only this cone. A single cone cannot match a sand's face pressure, wedge and settlement at once, and choosing a cone between the two matches to fit Idinger would be tuning.

**For the live view:**
- report the face pressure as the bracket (triaxial match to plane-strain match), with the plane-strain match as the conservative upper value;
- use Bolton's dilation.

A Mohr–Coulomb (Lode-angle) yield surface would need a change to the solver's yield kernel. That is a possible later step, not done here.

## Limits

- **Wedge detection** at D/30 and in two D/20 runs reports nonsense (22–41°), because the band at crown level catches too few particles. Those values are left out above.
- **Settlement detection** failed in the D/30 run.
- **The pressure probe is noisy** (±10 % frame to frame). Values are averaged over seven frames.
- **Half-model:** the symmetry wall is frictionless, while Idinger's acrylic window had friction, which they note may have reduced their measured displacements.
