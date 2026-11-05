# MPM tunnel in undrained clay (Phase 2, WP3): blocked

- **Plan:** [Phase 2, WP3](../plans/phase2-mpm-face-chamber.md#wp3-undrained-clay-face-about-2-weeks).
- **Code:**
  - [`server/tunnelsim_server/scenes/tunnel_2d.py`](../../server/tunnelsim_server/scenes/tunnel_2d.py), a plane-strain tunnel with a closing ring of segments;
  - [`face_sand.py`](../../server/tunnelsim_server/scenes/face_sand.py) with the kaolin soil;
  - records `t2d_*` and `fc_*` in [`server/results/`](../../server/results/).
- **Status:** **blocked, cause found.** The MPM clay tunnel collapses at about half the stability ratio measured by Kimura & Mair (1981), in 2D and 3D alike. The cause is Newton's packing constraint (`critical_fraction`), which was off in every scene so far. Without it the soil never stops compacting and never becomes static. With it on, the plane-strain tunnel comes close to Kimura (see [diagnosis](#diagnosis-5-nov-2026)). A clean set-up and a re-baseline of WP1–WP3 come next.
- **Run on:** 5 Nov 2026

## Data: Kimura & Mair (1981)

The paper is open in the [ISSMGE library](https://www.issmge.org/uploads/publications/1/35/1981_01_0061.pdf). Its numbers are digitised from the scanned Figs 6, 9 and 10 by mapping the axis ticks to pixels, to about ±0.2 in N.

**The tests:**
- kaolin, cu = 26 kPa;
- a 60 mm tunnel at 75 g and 125 g (4.5 m and 7.5 m prototypes), supported by compressed air in a rubber bag;
- N = (σz − σT)/cu, with σz the overburden at the axis.

**The unit weight** is not stated. It comes from pairing Fig. 6 (σT/cu, 2D) with Fig. 10 (N, 2D) at the same C/D: σz/cu = N + σT/cu gives γD/cu ≈ 2.5 at C/D 1.2, 2.0 and 2.8 alike. That is γ ≈ 14.4 kN/m³ at D = 4.5 m.

| Series | C/D | N at collapse |
|---|---|---|
| Plane strain (2D, Fig. 10) | 1.2 / 1.8 / 2.0 / 2.3 / 2.8 | 3.5 / 3.7 / 4.3 / 3.8–4.2 / 4.2 |
| Heading supported to the face, P/D = 0 (Fig. 9) | 1.5 / 3.0 | 7.05 / 9.0 |
| Unlined heading, C/D 3.0 (Fig. 9) | P/D 0.5 / 1.0 / 2.0 / 3.0 | 7.75 / 6.85 / 5.6 / 5.05 |

**Not modelled:** headings with unlined length (P/D > 0). They need pressure on the heading walls, and Newton's colliders cannot apply a traction.

## Results

Rigid-plastic Tresca (friction 0, `yield_stress` = cu). The tunnel wall or face plate is frictionless, as a pressurised bag would be. N is read at 5 % of R (2D) or D (3D) of movement. The pressure keeps falling with further movement and never levels off.

| Case | MPM N | Kimura N | MPM / Kimura |
|---|---|---|---|
| Plane strain, C/D 1.2, D/10 | 2.7 | 3.5 | 0.76 |
| Plane strain, C/D 2.0, D/10 / D/20 / D/30 | 2.1 / 1.9 / 2.8 | 4.3 | 0.44–0.65 |
| Plane strain, C/D 2.8, D/10 | 2.0 | 4.2 | 0.48 |
| Heading at P/D 0, C/D 1.5, D 7.5 m, D/10 | 4.3 | 7.05 | 0.61 |
| Heading at P/D 0, C/D 3.0, D 4.5 m, D/10 | 3.8 | 9.0 | 0.42 |

The MPM clay is about **twice too weak** in plane strain and in 3D alike. The plane-strain values fall below the weightless plasticity lower bound for a circular tunnel, N = 2·ln(2C/D + 1) (Davis et al. 1980), which is about 3.2 at C/D 2.0. A correct rigid-plastic solution cannot do that.

## What has been ruled out

| Suspect | Test | Result |
|---|---|---|
| The cohesion term is scaled wrongly in Newton | Rankine active wall in Tresca clay | Matches theory: K 0.767 against 0.766 (cu/γH 0.06), 0.394 against 0.375–0.473 (0.16) |
| Stress level | The same wall test scaled ×10 (H 20 m) | Still matches: 0.722 and 0.353 |
| Clay leaking past the face plate | Particles behind the plate at the end | About 200 of 181,000 |
| Friction on the shield tube | Tube and plate frictionless | No change (N 2.6 against 3.3 at 5 %) |
| Rate | Retraction 5× slower | Weaker, not stronger |
| Solver convergence | 250 iterations; 4× smaller time step | No change (N 3.1–3.3 at 5 %) |
| Resolution | Plane strain at D/10, D/20, D/30 | N 1.9–2.8, no trend towards 4.3 |
| The yield condition is not enforced | Particle stress with a finite stiffness | √J2 = cu exactly where yielded, never above |

## Diagnosis (5 Nov 2026)

The diagnostic scripts are in [`server/diagnostics/`](../../server/diagnostics/), and the key runs have records (`t2d_kaolin_c2.0_d10_cf*`).

**1. Equilibrium holds: the earlier explanation is withdrawn.** On sections between the crown and the surface (`diagnostics/equil.py`), the integrated σzz equals the weight above within 0.3–3 %, in the elastic case and in the clay at yield, during the closure. The low mean stress around the tunnel quoted earlier was a ring average mixing crown and invert depths, so it did not stand for the axis level.

**2. The weightless benchmark is not possible in Newton.**
- Gravity is global, and colliders cannot apply a uniform traction.
- A near-weightless clay under a heavy fluid surcharge fails: the fluid is about 900× denser and sinks through the clay at up to 11 m/s (`diagnostics/weightless.py`).

**3. Leakage through the ring is negligible:** about 0.3 % of particles by the end (`diagnostics/ringleak.py`).

**4. The clay never comes to rest** (`diagnostics/settle_long.py`, C/D 2):
- The surface drops about 0.9 m (4 %) in the first second.
- With the ring held still, it keeps sinking at about 29 mm/s. After 6 s of settling, N is unchanged (2.0–2.7).
- During the closure the surface falls about three times faster than the lost tunnel area explains, so the soil is compacting by about 1 % of its volume as well. Undrained clay is incompressible.

**5. The cause: Newton's packing constraint.**
- **What it is:** `SolverImplicitMPM.Config.critical_fraction` ("fraction for particles under which the yield surface collapses"). Above 0 it turns on a void-fraction unilateral incompressibility offset.
- **How it was set:** 0, off, in Phase 0 and every WP0–WP3 scene.
- **Effect on the clay tunnel** (plane strain, C/D 2, D/10, 3 s settling):

| critical_fraction | Surface drop before closure | Static before closure? | N at 5 % R (Kimura ≈ 4.3) |
|---|---|---|---|
| 0 (as WP0–WP3) | 0.9 m, then creep | no (≈ 29 mm/s) | 2.0–2.2 |
| 0.5 | 0.9 m | no | 2.1 |
| 0.7 | 1.3 m | nearly (12 mm/s) | 2.2 |
| 0.8 | 2.6 m | yes (1.3 mm/s) | 3.0 |
| 0.9 | 3.5 m | yes (0.3 mm/s) | 3.7 |

**With the constraint active the clay becomes static, and N approaches Kimura's.** But the soil first compacts by 13–17 % of its height.

**Why the start compacts.** Newton takes a particle's volume as (2r)³, so the nominal packing is 1.0. The fraction it measures per grid node is noisy at 8 particles per cell, so nodes below the critical fraction lose their strength and compact. The overburden by weight is unchanged, but the cover shrinks: C/D 2 becomes about 1.2 at 0.9, where Kimura's N is 3.5. So N ≈ 3.7 still sits on the measured values.

## Next step (proposed): WP0b, packing

1. **Find a start that does not compact:** more particles per cell to cut the noise, and particles packed at the critical fraction. The check is a static soil with less than 1 % settling before loading, and a fixed critical fraction.
2. **Re-baseline:** repeat the WP1 element tests, the WP2 sand face and WP3 with the constraint on. It changes the at-rest state too, so WP1's failed K0 check may change.
3. **Fix it for all later work** in `scenes/common.py`, and re-pin the golden tests on purpose.

Until then, WP3 is blocked and the clay face is not used anywhere. The sand results (WP1, WP2) were also run without the constraint and will be repeated in WP0b.
