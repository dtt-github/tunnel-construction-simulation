# MPM EPB chamber under pressure (Phase 2, WP4): holds pressure with a volume correction

- **Plan:** [Phase 2, WP4](../plans/phase2-mpm-face-chamber.md#wp4-epb-chamber-with-a-pressure-controlled-shove-about-3-weeks).
- **Code:** [`server/tunnelsim_server/scenes/chamber.py`](../../server/tunnelsim_server/scenes/chamber.py). Runs with `python -m tunnelsim_server.runner chamber ...`; records `ch_*` in [`server/results/`](../../server/results/), the volume-balance runs as `ch_vb_*`. `ChamberConfig.seal_shell` (default off) is a diagnosis option: paste pushed into the shell wall is put back inside each frame.
- **Status:** **uncalibrated; holds the chamber pressure with a correction** ([9 Nov 2026](#volume-balance-and-a-sourced-paste-89-nov-2026)).
  - Newton's implicit MPM loses paste volume wherever a solid moves through it, so the chamber loses its pressure under the turning cutterhead ([newton-physics/newton#5180](https://github.com/newton-physics/newton/issues/5180)). A volume balance by region corrects this: it holds the mean elastic volume of each region of the paste to what the piston and the screw leave.
  - With that correction, an undrained paste and wall friction from open sources, the chamber holds 200 kPa through a 20 s excavation at voxel 0.15 m and 0.12 m. The vertical gradient is inside Botlek's range, and the screw removes about the volume the piston displaces.
  - **Cause found and reported ([13 Nov 2026](#cause-of-the-loss-screw-step-thrust-and-the-gradient-13-and-14-nov-2026)):** Newton's elastic volume follows the velocity divergence only and is not tied to the particle density. A density-coupled correction recovers part of the loss; the balance by region stays the default.
  - **Screw step and thrust (13 Nov 2026):** the pressure responds to a screw-speed step at 77–80 % of the chamber model's rate. Under a set thrust the screw sets the advance and the thrust sets the pressure.
  - **Open:** the gradient is not converged: with refinement the bulkhead contact reading rises and the paste's own stress gradient falls, and the 0.10 m chamber does not hold its pressure. 0.25 m does not hold either; the pressure band is narrower than on a machine; the paste leaks into the shell wall unless it is sealed; the torque is the paste's only.
  - The runs before 8 Nov, below, used the Phase 0 paste and no correction. They stand as the record of the loss.
  - **Correction (7 Nov 2026):** from 6 Nov the docs, the v1.0.0 release notes and our comment on [newton-physics/newton#5180](https://github.com/newton-physics/newton/issues/5180) said that under GIMP the chamber keeps 162 of 207 kPa (172 of 216 before the scaling fix), "a fifth lost". Those runs excavated for 4 s only. Over the scene's 20 s excavation the pressure falls to 51 kPa.
- **Run on:** 5 Nov 2026; GIMP and 20 s diagnosis runs 7 Nov 2026; volume balance and sourced paste 8–9 Nov 2026; cause, screw step, thrust and gradient 13–14 Nov 2026

## Set-up

**Machine:** the Crossrail EPB, D 7.08 m with 9.8 MNm installed torque. The chamber is 0.8 m long, with 0.6 m of ground in front of the cutterhead. The cutterhead has 6 spokes and 6 mixing arms and turns at 2 rpm.

**Advance:** a ground piston pushes the ground in at 60 mm/min.

**Paste (runs to 7 Nov; the paste from 8 Nov is in [its section](#volume-balance-and-a-sourced-paste-89-nov-2026)):**

| Property | Value | Source |
|---|---|---|
| Density | 1330 kg/m³ | the 13 kN/m³ foam-water-sand mixture of Bezuijen et al. (2005) |
| Bulk modulus | 2.8 MPa | the project's analytical chamber model at 2 bar with FIR 40 % and FER 10 (Boyle's law for about 10 % foam air), so the MPM chamber is as compliant as the console's |
| Friction μ | 0.35 | assumed (Phase 0) |
| Cohesion | 2 kPa | assumed (Phase 0) |
| Poisson's ratio | 0.3 | assumed |

**Screw:** analytical here. A sink at the screw inlet removes paste at the screw model's discharge, 0.6 × Q_th(rpm). WP5 resolves the screw itself.

**Pressure control:** a PI controller on the axis pressure sets the screw speed, from a feed-forward of 10 rpm (discharge equal to the excavated flow), capped at 22 rpm.

**Phases:**
1. pressurise to 2 bar, with the screw shut;
2. 3 s standstill;
3. 20 s excavation;
4. 6 s standstill.

**Readings:** the bulkhead pressure in nine horizontal bands clear of the screw inlet, as the bulkhead pressure cells of an EPB, with the vertical gradient as a least-squares fit across them.

## Data: Bezuijen, Talmon, Joustra & Grote (2005)

"Pressure gradients and muck properties at the face of an EPB", Botlek Rail Tunnel, IS-Amsterdam 2005 ([ISSMGE library, open](https://www.issmge.org/uploads/publications/6/11/2005_023.pdf)).

**Measurements:**
- total pressure at 9 points on the bulkhead;
- foam-conditioned saturated sand under a high water table.

**Findings:**
- **During excavation:** the vertical gradient is high and can exceed 20 kPa/m.
- **When excavation stops or a ring is built:** it falls, sometimes below 10 kPa/m.
- **References for scale:** the muck itself is about 13 kPa/m, total vertical stress in the ground about 20 kPa/m, and pore pressure 10 kPa/m.
- **About 1 bar is lost** where the muck enters the screw. That is for WP5.

The Guangzhou–Foshan data ([doi:10.17632/cjwbjttf88.1](https://doi.org/10.17632/cjwbjttf88.1)) give the lower minus the upper earth pressure: median 40 kPa (interquartile range 20–60) over 1,073 rings. The sensor spacing is not published openly, so this cannot be turned into a gradient.

## Results (voxel 0.15 m unless stated)

| | P0 strain basis (default) | P1d | P1d, voxel 0.1 m | Check |
|---|---|---|---|---|
| Axis pressure at standstill (kPa) | 185 | 209 | 200 | target 200 |
| Axis pressure while excavating, mean (5–95 %) | **32 (23–44)** | 236 (187–292) | 196 (154–243) | 200 ± 30 (DAUB 2016's EPB pressure deviation) |
| Screw speed while excavating (rpm) | 0 (the pressure is below target) | 22, at the cap | 20 | feed-forward 10 |
| Vertical gradient, standstill / excavating / stop (kPa/m) | 3.8 / 12.2 / 11.8 | 2.1 / −3.5 / −2.3 | 7.6 / 2.2 / 2.6 | Botlek: high while excavating (10–20+), lower at a stop; muck 13 |
| Cutterhead torque while excavating (MNm) | 1.8 | 9.4 | 7.7 | below 9.8 installed |
| Paste escaped (% of particles) | 0.4 | 1.0 | 1.3 | 0 |
| ms per frame (shared GPU) | 34 | 109 | 290 | |

**What this shows:**

1. **P0 cannot hold the chamber pressure.**
   - Pressurised to 2 bar with the cutterhead still, the paste holds its pressure.
   - Once the cutterhead turns, both the bulkhead and the ground piston fall to about 0.3 bar within seconds, although the screw takes almost nothing out.
   - That is the paste's volume being lost in plastic shear, about 5 % at a 2.8 MPa bulk modulus.
   - **Checks that rule out other causes** (voxel 0.25 m):
     - with the cutterhead stopped, the pressure holds at 198 kPa;
     - 150 solver iterations change nothing;
     - a frictionless paste loses the pressure even at standstill.
   - It is the same numerical volume loss in yielding material as in the clay tunnel.
2. **P1d holds the pressure, but the rest is wrong:**
   - **No real gradient:** the vertical gradient is near zero or negative, against 10–20+ kPa/m measured and 13 kPa/m for the muck's own weight;
   - **Too strong:** the element tests show P1d is 10–30 % too strong (see mpm-clay);
   - **Wide pressure band:** the pressure swings ±45 kPa while the screw runs at its cap.
   - So it cannot be called a validated chamber either.
3. **Leaks:**
   - **Fixed:** a gap under a voxel between the ground piston and the shell leaked, and the piston now overlaps the shell.
   - **Remaining:** about 1 % of the paste escapes through the polygonal shell and the bulkhead. That must also be fixed before any calibration.

## GIMP and the 20 s excavation (7 Nov 2026)

Under P0 with GIMP integration and a jitter of 0.05 h (the defaults since 7 Nov 2026), the chamber was first checked over a 4 s excavation and kept 162 of 207 kPa. Over the full 20 s it does not hold: the loss continues. The runs below find where the pressure goes.

- **Set-up:** as above, voxel 0.25 m, 2 rpm and 60 mm/min unless stated. Records `ch_*_20s` and `ch_gimp_j0.05_60s`.
- **Reading:** the bulkhead pressure at the axis, mean over each 5 s of excavation; target 200 kPa.

| Run | Standstill | 0–5 s | 5–10 s | 10–15 s | 15–20 s | Paste escaped |
|---|---|---|---|---|---|---|
| Default (GIMP, jitter 0.05 h) | 207 | 160 | 95 | 69 | 51 | 1.8 % |
| Cutterhead stopped | 207 | 210 | 216 | 220 | 220 | 0.1 % |
| Paste that cannot yield (cohesion 10 MPa) | 213 | 285 | 266 | 253 | 239 | 0.3 % |
| Advance 1 mm/min | 207 | 157 | 89 | 64 | 48 | 1.8 % |
| Cutterhead 1 rpm | 207 | 159 | 173 | 104 | 117 | 1.1 % |
| Cutterhead 4 rpm | 207 | 119 | 52 | 36 | 32 | 3.2 % |
| Shell sealed, 2 rpm | 206 | 157 | 90 | 63 | 46 | 0 |
| Shell sealed, 1 rpm | 206 | 157 | 168 | 98 | 108 | 0 |
| Shell sealed, 4 rpm | 206 | 115 | 48 | 34 | 31 | 0 |
| PIC, jitter 0.05 h | 202 | 116 | 49 | 35 | 31 | 2.0 % |
| GIMP, jitter 0.25 h | 206 | 156 | 87 | 60 | 46 | 1.9 % |

**What this shows:**

1. **The loss needs a turning cutterhead and a paste that yields.** With the cutterhead stopped, or with a paste too strong to yield, the pressure holds and the screw controls it. The advance rate makes no difference.
2. **It follows the cutterhead's rotation, not time.** After about a third of a revolution, 1, 2 and 4 rpm are all near 95–120 kPa. Over a 60 s excavation it levels off at about 30 kPa (15 % of the target), and it does not recover at the standstill after.
3. **It is not the leak.** About 2 % of the paste escapes by pushing into the 0.5 m shell wall, mostly in the lower half, not through the plate joints. With the shell sealed (`seal_shell`: paste that enters the wall is put back inside), nothing escapes and the pressure falls the same way, 3–10 kPa lower. The leak remains a fault of its own.
4. **It is stress lost in the yielding paste, under every solver setting.** GIMP slows it (51 kPa after 20 s against 31 under PIC); the jitter barely matters (46 kPa at 0.25 h). The screw stays shut throughout, as the pressure is below the target.
5. **The 5 Nov PIC result stands:** 32 kPa over the second half of a 20 s excavation at voxel 0.15 m (table above). The 4 s PIC runs of 6 Nov (197 → 103 kPa) were read too early, as were the GIMP ones.

The paste that cannot yield also needs 12 MNm of cutterhead torque, more than the 9.8 MNm installed: it is a test, not a remedy.

## Volume balance and a sourced paste (8–9 Nov 2026)

### What was found

1. **Newton loses volume around a moving solid, not only in yielding paste.** In a box test, an elastic paste loses pressure around a moving paddle but not around a cylinder. The paste compresses ahead of the paddle and expands round its tips, and the net is a loss. Newton takes the elastic strain from its stress solve, so nothing restores the volume.
2. **A volume balance by region holds the pressure.**
   - **Regions:** the paste is split into 1.2 m columns across the section, each cut into three slices along the axis.
   - **Each step:** the mean log elastic volume of each region is set to its value when pressurising ended, adjusted by the chamber volume the piston has taken and the paste the screw has removed. The solver keeps the deviations within each region.
   - **Without it,** the same run falls from 205 to 28 kPa (`ch_vb_off_v015`).
3. **The Phase 0 paste arched between the walls.** With friction 0.35 under 200 kPa it had about 70 kPa of shear strength, so the walls carried its weight (as in a silo) and the gradient was 3–4 kPa/m. The screw then ran fast: the bulkhead axis reading sat above the chamber mean, so the controller removed 1.5 times the piston's volume (`ch_vb_phase0paste_*`).
   - **Wall friction 0** gave a Botlek gradient but almost no torque, and the paste leaked through the shell.
   - Wall friction 0.1 and 0 were sensitivity runs only: the open data below support about 0.3.

### Paste and walls from open sources

| Property | Value | Source |
|---|---|---|
| Strength | undrained, cu 5 kPa, no friction | the middle of the 3–7 kPa target for conditioned soil, [Scientific Reports (2026)](https://doi.org/10.1038/s41598-026-38868-y) (from the abstract; the full text was not open to us) |
| Paste on steel (shell, bulkhead, piston) | Coulomb 0.3 | conditioned soil on steel by inclined plate, 0.31–0.58 ([Applied Sciences 10 (2020) 3300](https://doi.org/10.3390/app10093300), Fig. 15); kaolin on steel, 0.33 back-fitted to Geo-Tribometer tests ([Henke & Wiesenthal, WCCM 2024](https://scipedia.com/wd/images/c/cf/Draft_Sanchez_Pinedo_347100632118.pdf)) |
| Density, bulk modulus, Poisson's ratio | as above | as above |

None of these was tuned to Botlek or DAUB. The cutterhead's own friction stays at 0.3 (assumed).

### Results

20 s excavation at 2 rpm and 60 mm/min, shell sealed (`seal_shell`), volume balance from the end of pressurising.

| Record | Voxel, iterations | Axis pressure, mean (5–95 %) (kPa) | Gradient, excavating / stop (kPa/m) | Screw (rpm) | Removed / piston displaced (m³) | Torque (MNm) |
|---|---|---|---|---|---|---|
| `ch_vb_v015` | 0.15 m, 100 | **200 (197–204)** | **12.2 / 11.7** | 9.9 | 0.78 / 0.79 | 0.51 |
| `ch_vb_v012` | 0.12 m, 100 | **199 (195–205)** | **15.5 / 17.3** | 11.9 | 1.00 / 0.79 | 0.44 |
| `ch_vb_v015_it50` | 0.15 m, 50 | 204 (200–208) | 12.6 / 13.6 | 11.4 | 0.84 / 0.79 | 0.52 |
| `ch_vb_v012_it50` | 0.12 m, 50 | diverges at 13 s | — | — | — | — |
| `ch_vb_v025` | 0.25 m, 50 | 153 (136–166) | 12.0 / 11.6 | 0 | 0.11 / 0.79 | 0.70 |
| `ch_vb_off_v015` (no balance) | 0.15 m, 50 | 30 (25–35) | 13.0 / 13.3 | 0 | 0.02 / 0.79 | 0.80 |
| Check | | 200 ± 30 (DAUB 2016) | Botlek 10–20+, muck 13 | feed-forward 10 | equal | 9.8 installed, whole machine |

Undrained strength across the sourced range (0.15 m, 50 iterations, balance from the start of excavation): cu 3 kPa gives 200 kPa (192–208) and 12.5 kPa/m, but leaks much more into the shell and the screw nearly stops; cu 5 kPa gives 204 kPa and 12.6 kPa/m; cu 7 kPa gives 202 kPa and 11.6 kPa/m, with the screw at 10.4 rpm (`ch_vb_cu*`).

**What this shows:**

1. **Pressure and screw:** at 0.15 m and 0.12 m the chamber holds its set point, and the screw runs near the feed-forward speed. At 0.15 m it removes the volume the piston displaces to within 2 %; at 0.12 m it removes 27 % more.
2. **Gradient:** 12–17 kPa/m, inside Botlek's range during excavation and close to the muck's own 13 kPa/m. It does not fall at the stop as Botlek's does. The two voxels differ by about a quarter, and the paste's own stress beside the bulkhead (10–18 kPa/m) differs from the contact force by up to 5 kPa/m. So the gradient is not converged.
3. **Iterations:** at 0.12 m, 50 iterations let the solver's volume error grow fifteenfold at about 13 s and the run diverges. 100 iterations hold it. The error per step still grows with refinement (about 0.003 at 0.15 m, 0.005 at 0.12 m), which the balance corrects.
4. **0.25 m does not hold:** the pressure falls about 50 kPa in excavation whichever regions are used. It is too coarse for this paste.

### Open

- **Pressure band:** ±4–5 kPa against DAUB's ±30 kPa. The scene has no ring builds, screw surges or ground entering at the face, so a narrow band is expected, but it is not yet checked against a field record.
- **Torque:** the scene cuts no ground; it stirs the paste. 0.4–0.5 MNm agrees with a hand estimate (cu × both faces of the cutterhead × mean lever arm, about 0.9 MNm). Comparing with the installed 9.8 MNm needs the face-cutting torque of the demo's torque model added. That is not done.
- **Gradient at a stop:** Botlek's falls; ours does not. (Identical runs differ by about 2 kPa/m at the stop, see [13–14 Nov](#gradient-readings-refinement-and-a-vertical-force-balance).)
- **Leak:** the runs seal the shell. Without it, the paste pushes into the 0.5 m shell wall.
- **The correction is ours, not Newton's.** It sets the volume by region and leaves the solver's local deviations. Whether Newton can conserve volume around a moving solid itself is open on newton#5180.

## Cause of the loss, screw step, thrust and the gradient (13 and 14 Nov 2026)

Voxel 0.15 m, 100 iterations, shell sealed, balance by region, unless stated. Records `ch_step_*`, `ch_thr_*`, `ch_g_*` in [`server/results/`](../../server/results/).

### Cause of the pressure loss

- **Cause:** Newton updates a particle's elastic volume from the divergence of the velocity only. Nothing ties it to how densely the particles are packed. Around a moving solid the particles bunch and then spread, and the update records a net expansion.
- **In the chamber:** over 6 s of excavation without a correction, the interior becomes about 10 % denser (material per free volume +2.6 % to +12.9 %) while the recorded elastic volume strain relaxes from −0.068 to −0.008. The pressure falls from 200 to 33 kPa.
- **In a box** ([`moving_collider_box.py`](../../server/diagnostics/moving_collider_box.py)): a paddle moving through elastic paste takes 197 kPa down to 20–31 kPa.
- **Reported** on [newton-physics/newton#5180](https://github.com/newton-physics/newton/issues/5180#issuecomment-6855321863).
- **A density-coupled correction** ([`volume_correction.py`](../../server/tunnelsim_server/scenes/volume_correction.py)) pulls each particle's elastic volume towards what its local density implies. It is partial:
  - in the box it holds 184–190 kPa at 240 steps/s and 60–130 kPa at 60 steps/s;
  - in the chamber the free volume cannot be measured reliably beside the walls, so it is applied to the interior only. Excavation then holds 144–157 kPa (33 without any correction, 200 with the balance by region), and at standstill the pressure sags from 207 to 177 kPa in 3 s.
- **The balance by region stays the default.** It uses what the piston and the screw do to the chamber's volume; the density-coupled correction uses only the particles, and is the one that could go into the solver.

### Response to a screw-speed step

Screw controller switched off 10 s into a 30 s excavation and the screw speed stepped. The predicted rate is the chamber model's: bulk modulus × change in discharge / chamber volume (K 2,806 kPa).

| Record | Screw (rpm) | Discharge change (l/s) | Predicted (kPa/s) | Measured (kPa/s) | Axis pressure (kPa) | Time to ±30 kPa (s) |
|---|---|---|---|---|---|---|
| `ch_step_stop` | 10.5 → 0 | −41.5 | +2.45 | +1.87 | 203 → 236 | 14.6 |
| `ch_step_up` | 10.6 → 20.6 | +39.6 | −2.34 | −1.88 | 203 → 163 | 11.3 |

- The pressure responds at 77–80 % of the predicted rate, in both directions.
- The shortfall is not explained. Paste leaving the chamber would fit the stopped screw but not the faster one.
- Checked against the analytical chamber model only. No open record of a screw step on a machine has been found.

### Shove under thrust

The ground piston is no longer driven at the advance rate. It moves under a set net thrust against the paste's force on it, with the screw at the fixed speed that discharges 60 mm/min.

| Quantity | Value | Status |
|---|---|---|
| Net thrust | 9.16 MN, the force that held the piston at standstill | from the run |
| Moving mass | 500 t | assumed |
| Jack damping | 30 × critical | assumed; lower values let the advance chatter between 0 and the cap |
| Advance cap | 120 mm/min | assumed |

| Record | Change at 12 s | Advance (mm/min) | Piston pressure (kPa) | Axis pressure (kPa) |
|---|---|---|---|---|
| `ch_thr_base` | none | 62 (55–70); the screw's discharge equals 60 | 222 | 199 |
| `ch_thr_f110` | thrust +10 % | to the cap, then 73 and falling | 222 → 243 | 197 → 219 |
| `ch_thr_screw` | screw +50 % | 65 → 91 (90 from the discharge) | 222 → 217 | 196 → 195 |

- **The screw sets the advance and the thrust sets the pressure,** as on a machine in EPB mode: more thrust raises the pressure by the same 10 % and the advance returns towards the screw's rate; a faster screw raises the advance and leaves the pressure.
- The gradient (11.4–12.2 kPa/m) and torque (0.45–0.55 MNm) are as under a driven piston.
- **Not included:** shield friction, the tail seal and backup drag. The thrust here is the net force on the face of the chamber, not the machine's total.

### Gradient: readings, refinement and a vertical force balance

Four readings of the vertical gradient, each the mean over the second half of the phase:
- from the contact force on the bulkhead, in bands (as before);
- from the paste's own stress within one voxel of the bulkhead;
- from the paste's mean stress over the whole chamber;
- the same over its core, two voxels clear of the shell and the bulkhead.

Excavation (kPa/m; the paste's own weight is 13.05):

| Record | Voxel, iterations | Axis pressure (kPa) | Bulkhead contact | Stress at bulkhead | Stress, chamber | Stress, core | Particles leaving the chamber |
|---|---|---|---|---|---|---|---|
| `ch_g_v015` | 0.15 m, 100 | 199 | 12.3 | 19.8 | 10.6 | 13.8 | 717 |
| `ch_g_v012` | 0.12 m, 100 | 199 | 15.7 | 8.4 | 8.7 | 11.1 | 2,600 |
| `ch_g_v010` | 0.10 m, 100 | 176; collapses at the stop | 16.8 | 3.7 | 7.3 | 7.4 | 5,851 |
| `ch_g_v010_it200` | 0.10 m, 200 | 187 | 17.2 | 2.1 | 6.3 | 6.4 | 6,243 |

Vertical force of the paste on each solid (kN, downwards), and the gradient that the end walls' share implies (13.05 × shell share):

| Record, phase | Paste weight | Shell | Bulkhead | Piston | Cutterhead | Implied | Bulkhead contact | Stress, chamber |
|---|---|---|---|---|---|---|---|---|
| `ch_g_vbal` (0.15 m), standstill | 714 | 569 | 40 | 73 | 35 | 10.4 | 9.3 | 8.6 |
| `ch_g_vbal` (0.15 m), excavation | 703 | 773 | −35 | −29 | −3 | 14.3 | 12.1 | 11.4 |
| `ch_g_vbal012` (0.12 m), standstill | 694 | 545 | 57 | 24 | 71 | 10.2 | 11.2 | 5.7 |
| `ch_g_vbal012` (0.12 m), excavation | 681 | 691 | −13 | 10 | −5 | 13.3 | 15.5 | 8.7 |

**What this shows:**

1. **The vertical balance closes** within 1 % in every phase at both voxels: the solids together carry the paste's weight.
2. **The end walls shift the gradient.** At standstill the bulkhead, piston and cutterhead hold up about a fifth of the paste's weight, so the gradient sits below the paste's own. During excavation they hold up none of it, or press down. A paste of 5 kPa strength between end walls 1.4 m apart could shift the gradient by up to about ±7 kPa/m; the runs use −3 to +1 kPa/m of that.
3. **The gradient is not converged, and the two kinds of reading diverge.** With refinement the contact reading rises (12 → 16 → 17 kPa/m) and the stress readings fall (11–14 → 6 kPa/m). The balance is the same at both voxels, so the forces are not the cause; how the pressure is distributed over the height is. The cause is not found.
4. **0.10 m is not a valid third point.** The chamber does not hold its set point (176–187 kPa with the screw shut), eight times as many particles leave it as at 0.15 m, and with 100 iterations it collapses at the stop.
5. **Repeatability:** `ch_g_v015` and `ch_g_vbal` have the same settings. During excavation they agree (12.3 and 12.1 kPa/m by contact); at the stop they give 13.7 and 11.6.

## Where this leaves WP4

- The chamber scene, the pressure controller, a volume correction and the open validation data are in place. The scene's defaults are the sourced paste, wall friction 0.3, the balance by region and 100 iterations.
- **Checked:** the set point holds and the screw balances the excavated volume at 0.15 m and 0.12 m; the vertical force balance closes; the bulkhead contact gradient (9–17 kPa/m) is in or near Botlek's 10–20.
- **WP4 outputs produced:** bulkhead pressure in bands, its gradient, mixing torque, the response to a screw-speed step, and a shove under thrust.
- **Not done:** a converged gradient (the readings diverge with refinement and 0.10 m does not hold), the stop gradient, the band against a field record, the leak without sealing, torque with the face, shield friction in the thrust, a field record for the screw step.
- Nothing from the MPM chamber is used on the console yet.
