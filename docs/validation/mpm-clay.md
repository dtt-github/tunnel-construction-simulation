# MPM tunnel in undrained clay (Phase 2, WP3): unblocked, checks continuing

- **Plan:** [Phase 2, WP3](../plans/phase2-mpm-face-chamber.md#wp3-undrained-clay-face-about-2-weeks).
- **Code:**
  - [`server/tunnelsim_server/scenes/tunnel_2d.py`](../../server/tunnelsim_server/scenes/tunnel_2d.py), a plane-strain tunnel with a closing ring of segments;
  - [`face_sand.py`](../../server/tunnelsim_server/scenes/face_sand.py) with the kaolin soil;
  - records `t2d_*` and `fc_*` in [`server/results/`](../../server/results/).
- **Status:** **unblocked (7 Nov 2026).** With PIC integration and the initial particle jitter of 0.25 h, the MPM clay tunnel collapsed at about half the stability ratio measured by Kimura & Mair (1981). With GIMP integration and a jitter of 0.05 h, the defaults since 7 Nov 2026, it reaches 0.92–0.98 of Kimura's N in plane strain and 0.81–1.04 in the two 3D headings ([current results](#gimp-integration-and-particle-jitter-6-and-7-nov-2026)). The history below is kept: it explains how the volume loss was found.
  - The first diagnosis blamed Newton's packing constraint (`critical_fraction`). WP0b withdrew it: that apparent gain came from compaction (see [WP0b correction](#wp0b-correction-5-nov-2026)).
  - The clay piling up against the ring is the tunnel-scale sign of a numerical volume loss in yielding clay. It comes from the default element (Q1 velocities, P0 strains), not from the colliders. The one element that removes it locks (see [piling](#the-piling-investigated-5-nov-2026)).
- **Run on:** 5 Nov 2026; GIMP and jitter runs 6–7 Nov 2026

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

## Results (PIC, jitter 0.25 h, as of 5 Nov 2026)

Superseded by [GIMP integration and particle jitter](#gimp-integration-and-particle-jitter-6-and-7-nov-2026); kept for the record.

Rigid-plastic Tresca (friction 0, `yield_stress` = cu). The tunnel wall or face plate is frictionless, as a pressurised bag would be. N is read at 5 % of R (2D) or D (3D) of movement. The pressure keeps falling with further movement and never levels off.

| Case | MPM N | Kimura N | MPM / Kimura |
|---|---|---|---|
| Plane strain, C/D 1.2, D/10 | 2.7 | 3.5 | 0.76 |
| Plane strain, C/D 2.0, D/10 / D/20 / D/30 | 2.1 / 1.9 / 2.8 | 4.3 | 0.44–0.65 |
| Plane strain, C/D 2.8, D/10 | 2.0 | 4.2 | 0.48 |
| Heading at P/D 0, C/D 1.5, D 7.5 m, D/10 | 4.3 | 7.05 | 0.61 |
| Heading at P/D 0, C/D 3.0, D 4.5 m, D/10 | 3.8 | 9.0 | 0.42 |

The MPM clay is about **twice too weak** in plane strain and in 3D alike. The plane-strain values fall below the weightless plasticity lower bound for a circular tunnel, N = 2·ln(2C/D + 1) (Davis et al. 1980, [doi:10.1680/geot.1980.30.4.397](https://doi.org/10.1680/geot.1980.30.4.397)), which is about 3.2 at C/D 2.0. A correct rigid-plastic solution cannot do that.

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

**5. Newton's packing constraint (withdrawn by WP0b, see [below](#wp0b-correction-5-nov-2026)).**
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

With the constraint active the clay became static and N approached Kimura's, but the soil first compacted by 13–17 % of its height. WP0b showed that the compaction itself, not the constraint, raised N.

**Why the start compacts.** Newton takes a particle's volume as (2r)³, so the nominal packing is 1.0. The fraction it measures per grid node is noisy at 8 particles per cell, so nodes below the critical fraction lose their strength and compact. The overburden by weight is unchanged, but the cover shrinks: C/D 2 becomes about 1.2 at 0.9, where Kimura's N is 3.5. So N ≈ 3.7 still sits on the measured values.

## WP0b correction (5 Nov 2026)

The scripts are [`diagnostics/packing.py`](../../server/diagnostics/packing.py) and [`diagnostics/cohesion_scale.py`](../../server/diagnostics/cohesion_scale.py).

**1. Newton's cohesion and stiffness scale with particle volume.**
- Newton takes a particle's volume as (2r)³ and works with stresses per unit of particle volume in each grid cell.
- The effective cohesion and Young's modulus are therefore the input values times the fill of the cell: the nominal packing k = (2r/h)³ inside the soil, less in part-filled cells.
- Friction is a ratio and does not change.
- The Rankine wall in Tresca clay (cu/γH 0.06; theory K = 1 − 4cu/γH = 0.76) shows it:

| Particle radius | Cohesion input | K_active |
|---|---|---|
| 0.5 h (k = 1) | cu | 0.771 |
| 0.7 h (k = 2.744) | cu | 0.366 (theory with 2.744 cu: 0.341) |
| 0.7 h | cu / 2.744 | 0.773 |

**2. This explains the critical-fraction result.**
- At `critical_fraction` 0.8–0.9 the cells compacted to 1.3–1.5 times their initial fill, so the clay there carried 1.3–1.5 times the cohesion.
- The cover also became shallower.
- Both raised N. The constraint itself did not strengthen the clay.

**3. A larger radius stops the start-up compaction.** In a 10 m clay column between frictionless walls:

| Radius | critical_fraction | Settlement in 3 s (% of H) |
|---|---|---|
| 0.5 h | 0 | 2.7 |
| 0.5 h | 0.9 | 10.5 |
| 0.6 h | 0.9 | 1.8 |
| 0.7 h | 0.9 | 0.8 |

- With the radius at 0.7 h, `critical_fraction` makes no measurable difference (Rankine, K0, tunnel).

**4. The new default** (all scenes, from WP0b on):
- radius 0.7 h;
- yield stress and Young's modulus divided by 2.744 when particles are built, so the soil behaves as specified;
- particle stresses multiplied by 2.744 when read out;
- `critical_fraction` 0.

Checks with this default:
- the sand Rankine wall is unchanged (K_a 0.302 against 0.301);
- K0 stresses add up to the weight (σv/γz 0.993);
- the Phase 0 golden face keeps its limit pressure (1.642 against 1.629 kPa).

**5. The clay tunnel is still about twice too weak.** At plane strain, C/D 2, D/10, with the correct cohesion, N at 5 % of R is 2.0 with the constraint on or off. Kimura measured ≈ 4.3.

**6. The clay piles up against the ring.** The ring is held still for 6 s, yet the slab keeps creeping at 15–25 mm/s.
- **The shell next to the ring fills up:** the 0.25 m shell outside the ring holds 75 % more particles than at the start, and about 240 particles have passed inside the ring.
- **The fastest particles** are all at the ring.

## The piling, investigated (5 Nov 2026)

The script is [`diagnostics/ringpile.py`](../../server/diagnostics/ringpile.py).
- **Set-up:** the plane-strain slab (C/D 2, D/10) held for 4 s with the lining still.
- **Readings:** surface drop and mean speed; particle counts in shells round the lining; density by height.

| Case | Mean speed at 4 s (mm/s) | Surface drop (m) | Shell next to the lining (particles) | Particles inside the lining |
|---|---|---|---|---|
| 24-segment ring, kaolin cu 26 kPa | 15 | 0.96 | 308 → 542 | 1145 |
| Solid cylinder, kaolin | 25 | 0.62 | 308 → 519 | 85 |
| Solid cylinder, kaolin, lining friction 0.5 | 14 | 0.52 | 308 → 362 | 33 |
| Solid cylinder, kaolin, D/20 | 32 | 1.36 | 1114 → 2400 | 692 |
| Solid cylinder, kaolin with E = 500 cu | 40 | 0.74 | 308 → 534 | 87 |
| Solid cylinder, kaolin, 250 iterations | 14 | 0.35 | 308 → 473 | 64 |
| 24-segment ring, cu 2.6 MPa (never yields) | 0.6 | 0.03 | 308 → 302 | 0 |

**What this shows:**
- **Yielding causes it, not the colliders.**
  - A clay that does not yield comes to rest with no piling.
  - A smooth cylinder piles up as much as the segment ring; its gaps only add leakage.
- **The volume loss is spread through the slab.** The density rises 2–7 % at every depth, not only at the lining. The pile at the lining is only about a tenth of the volume lost at the surface.
- **It is numerical.**
  - Newton's flow rule cannot compact under pressure: plastic volume change is only allowed where the normal stress is zero.
  - The loss shrinks with more solver iterations.
  - It grows with finer grids, so it does not converge away.
  - It is the particle-level volume error of the Q1–P0 element in plastic flow.

**Other elements Newton offers** (kaolin, solid cylinder or ring, D/10):

| Strain basis / velocity basis | Slab at 4 s | Clay tunnel N at 5 % R (C/D 1.2 / 2.0 / 2.8) | Sand Rankine K_a (theory 0.283) | Tresca Rankine K (theory 0.76) | Sand face p at 5 % D (kPa) |
|---|---|---|---|---|---|
| P0 / Q1 (default) | 25 mm/s, drop 0.62 m | 2.4 / 1.9 / 1.8 | 0.302 | 0.773 | 8.7 |
| P1d / Q1 | at rest (0.1 mm/s), drop 0.27 m | 3.0 / 3.4 / 3.6 | 0.256 | 0.708 | 5.5 |
| pic8 / Q1 | nearly at rest (3 mm/s), drop 0.26 m | – / 3.8 / – | 0.246 | 0.684 | not run |
| P0 / B2 | 3 mm/s, drop 0.87 m | not run | not run | not run | not run |
| Q1 / Q1 | 168 mm/s, drop 2.7 m | not run | not run | not run | not run |

- **P1d** brings the clay tunnel to 0.79–0.86 of Kimura's N, but the element tests show why:
  - it makes the soil too strong: about 10 % on friction and about 20 % on cohesion;
  - its N falls as the grid is refined (3.4 at D/10, 3.1 at D/20).
  - That is volumetric locking, not a correct incompressible solution.
  - It also moves the sand face to Idinger's measured range for the wrong reason.
- **pic8**, a strain basis per particle, gets the closest (N 3.8 at C/D 2), but it locks even more: about 13 % on friction and about 30 % on cohesion.
- **Neither is adopted.** P0 stays: it is the element that passes the element tests.

## GIMP integration and particle jitter (6 and 7 Nov 2026)

- **Source of the change:** we reported the volume loss to Newton ([newton-physics/newton#5180](https://github.com/newton-physics/newton/issues/5180)). A maintainer reproduced it and found two causes: with PIC integration the P0 incompressibility condition is summed at the particle positions, which is not exact when the particles are disordered; and our initial jitter of ±0.25 h was enough to make yielding material creep. Two remedies: GIMP integration (over particle–cell overlaps) or a smaller jitter.
- **Code:** `common.INTEGRATION_SCHEME = "gimp"` and `common.JITTER = 0.05` are the defaults since 7 Nov 2026; `runner.py --integration pic` repeats the PIC runs. The Phase 0 golden face keeps its own 0.25 h.
- **Particle-volume scaling:** cohesion and stiffness scale with the particle volume (2r/h)³ = 2.744 under GIMP as under PIC, and so does the stored particle stress. The scenes divide `yield_stress` and E by 2.744 and multiply the stress readout by it, in both schemes.

**Correction (7 Nov 2026).** The first version of this section, committed on 6 Nov and part of v1.0.0, said that GIMP removes the 2.744 scaling and that the clay tunnel under GIMP is too strong to collapse. Both were wrong. The test that seemed to show no scaling under GIMP already divided by 2.744 inside the scene's particle builder; the switch then left the clay 2.744× too strong, which is why the tunnel stood unsupported. Rerun properly, the Tresca wall under GIMP gives K 0.366 with the input cohesion (theory with 2.744 cu: 0.341) and 0.730–0.762 with cohesion / 2.744 (theory 0.760).

**Clay tunnel, plane strain, N at 5 % of R** (Newton 1.7.0, `S2` collider, D/10 unless stated):

| Setting | C/D 1.2 | C/D 2.0 | C/D 2.8 |
|---|---|---|---|
| PIC, jitter 0.25 h (WP0b) | 2.4 | 1.9 | 1.8 |
| PIC, jitter 0.05 h | 3.42 | 3.50 | 2.97 |
| GIMP, jitter 0.25 h | 3.18 | 3.41 | 3.55 |
| **GIMP, jitter 0.05 h (default)** | **3.43** | **3.95 (D/20: 3.89)** | **4.06** |
| Kimura & Mair, centrifuge | 3.5 | 4.3 | 4.2 |
| GIMP, jitter 0.05 h / Kimura | 0.98 | 0.92 (D/20: 0.90) | 0.97 |

**3D headings at P/D 0** (GIMP, jitter 0.05 h): C/D 1.5, D 7.5 m: N 7.3 against 7.05 (1.04); C/D 3.0, D 4.5 m: N 7.3 against 9.0 (0.81). N = (σv at the axis − face pressure at 5 % of D) / cu.

**Other checks with the default:**

| Check | PIC, jitter 0.25 h | GIMP, jitter 0.05 h |
|---|---|---|
| Clay slab round a fixed lining, 4 s (stiff control 0.03 m) | 0.62 m, still creeping at 25 mm/s | 0.25 m, at rest (0.6 mm/s) |
| Tresca Rankine wall, K at H/10, H/20, H/40 (theory 0.760) | 0.765 at H/20 | 0.735, 0.762, 0.730 |
| EPB chamber, bulkhead pressure, hold → cutterhead turning | 197 → 103 kPa | 207 → 162 kPa |

The jitter sweep (0.25, 0.1, 0.05 and 0 h) showed that the creep stops at 0.1 h and below under PIC, and that jitter barely moves the Rankine walls (within 2 %).

**Newton pull request #5021** (the maintainer's branch at `6fea33f0`, Newton 1.8.0.dev0, installed apart from the server environment; GIMP, jitter 0.25 h):
- with the `S2` collider: slab 0.10 m, at rest; K0 0.53 against 0.73 on 1.7.0 (target 0.44); chamber 210 → 173 kPa; clay tunnel N 3.28 / 3.49 / 3.53;
- with `pic8`: slab 0.045 m; but the chamber pressure rises from 214 to 344 kPa while the cutterhead turns, and the clay tunnel is weaker (3.23 / 3.23 / 3.06).
- Not adopted: unreleased, and not better on the clay tunnel. To test again when it is released.

## Where this leaves WP3

- **Unblocked.** In plane strain the clay tunnel is within 2–8 % of Kimura & Mair at three covers and at two resolutions; the 3D headings are at 0.81 and 1.04.
- **Still to do:** the rest of Kimura & Mair's series (C/D 1.8 and 2.3 in plane strain; unlined headings at P/D 0.5–3.0); settlement above the collapse; the heading at C/D 3.0 is 19 % weak.
- **Chamber (WP4):** still loses about a fifth of its pressure while the cutterhead turns ([chamber](mpm-chamber.md)).
