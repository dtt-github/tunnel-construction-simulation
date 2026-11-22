# MPM EPB chamber under pressure (Phase 2, WP4): holds pressure with a volume correction

- **Plan:** [Phase 2, WP4](../plans/phase2-mpm-face-chamber.md#wp4-epb-chamber-with-a-pressure-controlled-shove-about-3-weeks).
- **Code:** [`server/tunnelsim_server/scenes/chamber.py`](../../server/tunnelsim_server/scenes/chamber.py). Runs with `python -m tunnelsim_server.runner chamber ...`; records `ch_*` in [`server/results/`](../../server/results/), the volume-balance runs as `ch_vb_*`. `ChamberConfig.seal_shell` (default off) is a diagnosis option: paste pushed into the shell wall is put back inside each frame.
- **Status:** **uncalibrated; holds the chamber pressure with a correction** ([9 Nov 2026](#volume-balance-and-a-sourced-paste-89-nov-2026)).
  - Newton's implicit MPM loses paste volume wherever a solid moves through it, so the chamber loses its pressure under the turning cutterhead ([newton-physics/newton#5180](https://github.com/newton-physics/newton/issues/5180)). A volume balance by region corrects this: it holds the mean elastic volume of each region of the paste to what the piston and the screw leave.
  - With that correction, an undrained paste and wall friction from open sources, the chamber holds 200 kPa through a 20 s excavation at voxel 0.15 m and 0.12 m. The vertical gradient is inside Botlek's range, and the screw removes about the volume the piston displaces.
  - **Cause found and reported ([13 Nov 2026](#cause-of-the-loss-screw-step-thrust-and-the-gradient-13-and-14-nov-2026)):** Newton's elastic volume follows the velocity divergence only and is not tied to the particle density. A density-coupled correction recovers part of the loss; the balance by region stays the default.
  - **Screw step and thrust (13 Nov 2026; repeated 17 Nov):** the pressure responds to a screw-speed step at 97–114 % of the rate predicted from the net flow after the step, in both directions ([17 Nov](#screw-step-and-thrust-on-a-settled-chamber-17-nov-2026)). The earlier 77–80 %, and 73 % / 129 % with four solver steps, came from a prediction that assumed the chamber was in balance before the step. Under a set thrust the screw sets the advance and the thrust sets the pressure.
  - **Three voxels hold ([16 Nov 2026](#solver-substeps-and-a-collapse-at-the-screw-inlet-15-and-16-nov-2026)):** with 4 solver steps of 50 iterations per frame, and the screw taking paste from the middle of its inlet, the set point holds at 0.15 m, 0.12 m and 0.10 m in three seeds of three. Before, the 0.10 m chamber was over-packed by the piston push, and a crushed particle in the screw inlet corner could turn a whole chamber invalid within one solver step.
  - **Gradient at four voxels ([16 Nov 2026](#the-bulkhead-reading-and-the-gradient-at-four-voxels-16-nov-2026)):** the bulkhead pressure bands caught an uneven share of Newton's two lattices of force points, which biased the gradient and held the 0.15 m chamber at about 227 kPa for 200. With the bands on the grid, the contact gradient in excavation is 13.5 / 14.7 / 12.9 / 15.2 kPa/m at 0.15 / 0.12 / 0.10 / 0.08 m: 14.1 ± 1.1 with no trend, about the weight of the paste at its fill (14.1–14.4), and within 1.1 kPa/m of the paste inside the chamber. Over a 100 s excavation, 0.15 m and 0.12 m agree within 0.5 kPa/m (15.1 and 15.6) and 0.10 m reads 13.05.
  - **Screw ([17 Nov 2026](#screw-speed-the-controllers-swing-and-the-screw-volume-17-nov-2026)):** the screw speed scattered (8–14 rpm) because the pressure controller swings with a period of 40–50 s, longer than a 20 s excavation. Read by volume over the whole excavation, less the paste's elastic swing, the screw removes the displaced volume times the paste's fill (1.06–1.11) within 2 % at every voxel and seed.
  - **Watertight shell ([19 Nov 2026](#the-shell-leak-a-watertight-tube-18-and-19-nov-2026)):** the paste leaked into the shell because Newton merges a body's overlapping shapes into one mesh and mis-signs grid nodes behind buried faces. The shell is now one tube mesh: resets fell from 0.2–14 M to about 10 thousand per run, and the gradient no longer depends on where the wall falls on the grid.
  - **Gradient at seven voxels ([21 Nov 2026](#the-bulkhead-gradient-at-seven-voxels-19-to-21-nov-2026)):** read in rows across the full section, the bulkhead gradient in excavation is 14.53 ± 0.18 kPa/m at seven voxels from 0.15 m to 0.08 m, with no trend. It is within 3 % of the paste's weight at its fill and inside Botlek's 10–20 kPa/m. A force balance in the chamber matched it to the paste's own stress. The bands had read 0.12 m 0.9 kPa/m high.
  - **Open:** 0.10 m read about 2 kPa/m low in 100 s runs before the tube shell, and its controller swing does not die down. 0.25 m does not hold. The pressure band at a gauge is 1.3–2.5 times narrower than Botlek's ([21 Nov](#the-pressure-band-at-one-gauge-21-nov-2026)). A sudden loss of the whole chamber came back in one run on 20 Nov. It starts from extreme particles in the corner of the ground face and the shell; since 21 Nov a check after every solver step resets the particle that fails, and the chamber holds ([21 Nov](#the-bulkhead-gradient-at-seven-voxels-19-to-21-nov-2026)). The gradient does not fall at a stop as Botlek's does; the paper's causes, drainage and foam, are not in the model ([21 Nov](#the-gradient-at-the-stop-21-nov-2026)). The MPM's torque is the paste's only and falls with the voxel without converging (0.37 MNm at 0.06 m); with the demo's rim, tools and seals the total is 23–37 % of installed ([22 Nov](#torque-with-the-face-cutting-21-and-22-nov-2026)). The thrust's shield friction is analytical; in London Clay the total is 1.0–1.9× two open records ([22 Nov](#shield-friction-in-the-thrust-22-nov-2026)).
  - The runs before 8 Nov, below, used the Phase 0 paste and no correction. They stand as the record of the loss.
  - **Correction (7 Nov 2026):** from 6 Nov the docs, the v1.0.0 release notes and our comment on [newton-physics/newton#5180](https://github.com/newton-physics/newton/issues/5180) said that under GIMP the chamber keeps 162 of 207 kPa (172 of 216 before the scaling fix), "a fifth lost". Those runs excavated for 4 s only. Over the scene's 20 s excavation the pressure falls to 51 kPa.
- **Run on:** 5 Nov 2026; GIMP and 20 s diagnosis runs 7 Nov 2026; volume balance and sourced paste 8–9 Nov 2026; cause, screw step, thrust and gradient 13–14 Nov 2026; substeps and the screw inlet 15–16 Nov 2026; bulkhead reading and four voxels 16 Nov 2026; screw volume, step and thrust 17 Nov 2026; shell leak and the tube shell 18–19 Nov 2026; gradient at seven voxels, diagnostic tank and force balance 19–21 Nov 2026; sudden-loss trace, the stop gradient and the band at one gauge 21 Nov 2026; torque at 0.07 and 0.06 m and shield friction 22 Nov 2026

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

**Readings:** the bulkhead pressure in nine horizontal bands clear of the screw inlet, as the bulkhead pressure cells of an EPB. The vertical gradient was a least-squares fit across them until 20 Nov 2026. Since then it is fitted to rows one voxel high across the full section ([why](#the-bulkhead-gradient-at-seven-voxels-19-to-21-nov-2026)).

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

- **Pressure band:** ±4–5 kPa against DAUB's ±30 kPa. The scene has no ring builds, screw surges or ground entering at the face, so a narrow band is expected, but it is not yet checked against a field record. (Checked at a gauge on 21 Nov: [1.3–2.5 times narrower than Botlek's](#the-pressure-band-at-one-gauge-21-nov-2026).)
- **Torque:** the scene cuts no ground; it stirs the paste. 0.4–0.5 MNm agrees with a hand estimate (cu × both faces of the cutterhead × mean lever arm, about 0.9 MNm). Comparing with the installed 9.8 MNm needs the face-cutting torque of the demo's torque model added. (Done on 22 Nov: [23–37 % of installed](#torque-with-the-face-cutting-21-and-22-nov-2026); the paste torque falls with the voxel and is not converged.)
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

- The pressure responds at 77–80 % of the predicted rate, in both directions. (17 Nov: that prediction assumed the chamber was in balance at the speed before the step; see [the repeat](#screw-step-and-thrust-on-a-settled-chamber-17-nov-2026).)
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
- **Not included:** shield friction, the tail seal and backup drag. The thrust here is the net force on the face of the chamber, not the machine's total. (Added from the analytical model on 22 Nov: [shield friction in the thrust](#shield-friction-in-the-thrust-22-nov-2026).)

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
3. **The gradient is not converged, and the two kinds of reading diverge.** With refinement the contact reading rises (12 → 16 → 17 kPa/m) and the stress readings fall (11–14 → 6 kPa/m). The balance is the same at both voxels, so the forces are not the cause; how the pressure is distributed over the height is. The cause was not found on 14 Nov; part of it is the paste's density ([15 Nov](#gradient-paste-density-by-height-15-nov-2026)).
4. **0.10 m is not a valid third point.** The chamber does not hold its set point (176–187 kPa with the screw shut), eight times as many particles leave it as at 0.15 m, and with 100 iterations it collapses at the stop.
5. **Repeatability:** `ch_g_v015` and `ch_g_vbal` have the same settings. During excavation they agree (12.3 and 12.1 kPa/m by contact); at the stop they give 13.7 and 11.6.

### Gradient: paste density by height (15 Nov 2026)

One suspect for the diverging readings was tested: Newton's particle stress acts per unit of particle volume, so the stress the paste carries per unit of space is the particle stress times the fill of that space. If the fill varies with height, the plain particle-stress gradient is biased.

- **Reading:** two prisms clear of the shell (R/4 < |y| < R/2, |z − axis| < 0.8 R, bulkhead to the spokes), ten bins over the height. Per bin, summed over each phase: paste mass and mean particle stress. Fill = mass / (paste density × bin volume).
- **Code:** `chamber.run` returns the profile with `stress_log`; [`chamber_run.py`](../../server/diagnostics/chamber_run.py) prints it. Records `ch_pf_v015`, `ch_pf_v012`.
- **Runs:** the settings of `ch_g_vbal` and `ch_g_vbal012`, one run each, on a node shared with other projects.

Gradient in the prisms (kPa/m; in brackets without the lowest bin):

| Phase | Voxel | Bulkhead contact | Stress, chamber (as above) | Particle stress, prisms | Stress × fill, prisms |
|---|---|---|---|---|---|
| Standstill | 0.15 m | 9.3 | 8.7 | 10.1 (11.0) | 12.0 (12.9) |
| Standstill | 0.12 m | 11.5 | 5.8 | 7.3 (7.1) | 10.8 (11.0) |
| Excavation | 0.15 m | 12.1 | 10.7 | 15.1 (12.0) | **15.4 (15.6)** |
| Excavation | 0.12 m | 15.8 | 8.8 | 12.1 (10.8) | **14.9 (15.8)** |
| After the stop | 0.15 m | 12.7 | 10.4 | 17.8 (12.8) | 16.4 (17.2) |
| After the stop | 0.12 m | 17.1 | 10.0 | 14.5 (12.3) | 15.7 (16.5) |

**What this shows:**

1. **The fill is not 1 and not uniform.** It is mostly 1.05–1.25 in the prisms (0.94–1.08 in the lowest bin): the paste in the interior is about a tenth denser than its nominal density, as found on [13 Nov](#cause-of-the-pressure-loss), and denser towards the bottom. At 0.12 m it rises from 1.10 at the top to 1.25 in the second bin from the bottom.
2. **Stress × fill agrees between the voxels:** 15.4 and 14.9 kPa/m during excavation (15.6 and 15.8 without the lowest bin), where the particle stress alone gives 15.1 and 12.1 (12.0 and 10.8). The fall of the stress readings with refinement was in part this bias. At standstill and after the stop the two voxels agree to about 1 kPa/m.
3. **The level is consistent with the denser paste.** At a fill of 1.10–1.15 the paste in the prisms weighs 14.4–15.0 kPa/m, not the nominal 13.05.
4. **The contact reading is not explained.** It still moves from 12.1 to 15.8 kPa/m. At 0.12 m it is within 1 kPa/m of stress × fill; at 0.15 m it is 3 kPa/m below.
5. **Limits:** identical settings have differed by about 2 kPa/m at the stop (the table is seed 0; repeats below); the prisms leave out the paste near the shell and the screw inlet; the lowest bin is an outlier in every profile (high stress, low fill), which is why both fits are given; 0.10 m is still not a valid third point.

**Repeats with two more seeds** (the seed sets the initial particle jitter; records `ch_pf_v015_s1`, `_s2`, `ch_pf_v012_s1`, `_s2`). Stress × fill in the prisms and the bulkhead contact reading, kPa/m, seeds 0 / 1 / 2:

| Phase | Stress × fill, 0.15 m | Stress × fill, 0.12 m | Contact, 0.15 m | Contact, 0.12 m |
|---|---|---|---|---|
| Standstill | 12.0 / 11.8 / 12.4 | 10.8 / 11.5 / 13.7 | 9.3 / 9.2 / 9.5 | 11.5 / 12.3 / 14.1 |
| Excavation | 15.4 / 15.2 / 15.3 | 14.9 / failed / 15.1 | 12.1 / 12.0 / 12.2 | 15.8 / failed / 15.5 |
| After the stop | 16.4 / 15.3 / 15.1 | 15.7 / failed / 16.9 | 12.7 / 12.0 / 12.0 | 17.1 / failed / 17.7 |

- **Excavation repeats to 0.2–0.3 kPa/m** in both readings at both voxels. The interior gradient of about 15 kPa/m stands, and so does the unexplained step in the contact reading (12.1 → 15.7): it is not scatter.
- **Standstill at 0.12 m scatters by about 3 kPa/m** between seeds (0.6 at 0.15 m); after the stop the scatter is 1.2–1.3 kPa/m at both voxels.
- **One of the three 0.12 m runs lost its chamber** (`ch_pf_v012_s1`; cause and remedy [below](#the-lost-chamber-at-012-m-overfilled-corner-regions-15-nov-2026)). It held 203 kPa at standstill; during excavation the pressure sagged to 180–195 kPa from about 10 s with the screw throttled almost shut, and fell to zero at about 20 s. The volume balance made 189 million repairs in that run, against about 3,000–5,500 in the other two: it ran away instead of holding. The shell was sealed and the particles leaving the chamber were as in the other runs. At 0.15 m all three seeds hold.

### The lost chamber at 0.12 m: overfilled corner regions (15 Nov 2026)

The failed seed was rerun with a per-frame log of the volume balance (record `ch_vb_v012_s1`); it failed again, at 16.5 s.

- **The trigger:** the balance works on 108 regions (1.2 m columns, three slices along the axis). A full region holds about 3,000 particles at 0.12 m; the four corner columns of each slice are cut by the round shell and hold 80–125. During excavation paste collects in the two bottom corners beside the cutterhead: one went from 120 to 1,354 particles, 12.5 times its reference.
- **The mechanism:** the balance takes more particles in a region as paste that must be compressed, by the log of the count ratio. At 12.5 times that is a volume ratio of 0.08. The first degenerate particle (elastic volume ≤ 0) appears at 6.7 s, a few dozen by 14 s, and at 16.5 s the whole chamber degenerates within a few frames. The "repairs" counted earlier are these degenerate particles, summed over frames.
- **Regions under 50 reference particles were already left out.** At 0.15 m the corners hold about 60 and mostly fall under that; at 0.12 m they do not.

Two remedies were run (seeds 0 / 1 / 2 at 0.12 m, seed 0 at 0.15 m and 0.10 m; records `ch_vbf_*`, `ch_vbm_*`):

| Variant | Axis pressure, 0.12 m (kPa) | Contact gradient, 0.12 m | Stress × fill, 0.12 m | 0.15 m: pressure; screw volume against 0.79 m³ displaced |
|---|---|---|---|---|
| As before | 200.7 / lost / 200.3 | 15.8 / – / 15.5 | 14.9 / – / 15.1 | 199.9; 0.79 |
| Corners left out of the balance | 196.5 / 197.4 / 196.8 | 15.6 / 15.4 / 15.7 | 15.2 / 14.9 / 15.3 | 198.1; 0.69 |
| **Corners merged into the next region towards the axis** | 200.8 / 201.1 / 200.2 | 15.7 / 15.4 / 15.8 | 15.3 / 14.8 / 15.1 | 200.6; 0.78 |

- **Merging is adopted as the default** (`ChamberConfig.vb_merge_region_frac` = 0.1: a region with less than a tenth of the fullest region's particles joins the next one towards the axis, in the same slice; 96 regions remain, the smallest at about half the fullest). All three seeds hold the set point at 0.12 m with at most one degenerate particle in a frame, and 0.15 m is unchanged within the seed scatter.
- **Leaving the corners out is rejected:** their paste is then open to the volume loss, the pressure sits 2–4 kPa low and the screw discharges 12 % less than the machine displaces at 0.15 m.
- **The tenth is an assumed numerical setting,** not from a source and not fitted to any validation figure. At these voxels only the 12 corner regions fall under it; a second fraction was not run.
- **The gradients do not change** with either remedy, so the readings above stand.
- **0.10 m is not fixed by this** ([next section](#the-010-m-chamber-over-packed-by-the-piston-push-15-nov-2026)).
- **Screw volume at 0.12 m:** 0.84–1.01 m³ against 0.79 displaced, with or without merging (counted at the nominal particle volume; the paste being about a tenth denser explains about half of the excess). Open.

### The 0.10 m chamber: over-packed by the piston push (15 Nov 2026)

With the corner regions merged, the 0.10 m chamber still does not hold. The logs of the three voxels side by side (seed 0, records `ch_vbm_*`):

| | 0.15 m | 0.12 m | 0.10 m |
|---|---|---|---|
| Piston travel to reach 200 kPa | 0.18 m | 0.24 m | 0.35 m |
| Fill at standstill (paste mass over nominal density and space) | 1.11 | 1.13 | 1.27 |
| Mean elastic volume change at standstill, ln J | −0.075 | −0.068 | −0.056 |
| Pressure at standstill (kPa) | 205 | 209 | 187 |
| Balance correction undone by the solver per frame in excavation, ln J | 0.002 | 0.002 | 0.023 |

- **The piston push over-packs the paste, more at finer voxels.** To carry 200 kPa the paste needs about 7 % of elastic compression (K = 2.8 MPa). The piston delivers 11–27 % more paste into the space, because Newton sheds elastic volume while the piston moves and the balance is not active in that phase.
- **At 0.10 m the chamber starts excavation below the set point,** the controller shuts the screw, and the solver undoes ten times more of the balance each frame than at the coarser voxels. The pressure settles at 169 kPa and the paste degenerates after the stop.
- **A check on the density reading above:** at all three voxels the pressure on the piston equals the mean particle stress times the fill within 1 % (234 against 233 kPa, 218 against 219, 200 against 198).

Four remedies were run at 0.10 m. None holds the set point:

| Remedy | Record | Outcome |
|---|---|---|
| Corner regions merged | `ch_vbm_v010_s0` | no effect: no region overfills at 0.10 m (at most 1.25 times its reference) |
| Piston push at a quarter of the speed | `ch_v010_slow` | worse: 0.8 m of travel in 32 s without reaching 200 kPa; the paste is packed to 2.4 times its density and degenerates. The loss runs with time under load, not with piston speed |
| 400 solver iterations | `ch_v010_it400` | partial: 199 kPa at standstill, 185 kPa in excavation with the screw shut (192 by the end), paste valid; fill still 1.29 and 0.021 undone per frame |
| Pre-stressed start (`prestress`: elastic volume set to −p/K with the paste's weight, no push) | `ch_pre_v015`, `_v012`, `_v010` | sheds 38 / 44 / 57 % of the pressure within half a second (124 / 112 / 86 kPa at 0.15 / 0.12 / 0.10 m) and does not recover in 20 s. The paste stays at nominal density (fill 0.96–0.99), valid, with 0.002–0.005 undone per frame |
| Pre-stress followed by the push (`prestress_top_up`) | `ch_pret_*` | 0.10 m: the same travel and fill as without (3.7 s, 1.27), lost in excavation. 0.15 m: fill 1.03 and 204 kPa, but the screw discharges 1.03 m³ against 0.79 displaced, where the standard start balances. 0.12 m: little change |

**What follows:**
- The loss is in how the solver carries elastic volume, and it grows as the voxel shrinks: the behaviour reported on [newton#5180](https://github.com/newton-physics/newton/issues/5180). No change to the scene removes it.
- **The gradient can be compared at 0.15 m and 0.12 m only.** A third voxel is out of reach with this solver at an affordable iteration count (400 iterations at 0.10 m: 0.22 s per frame on the GPU alone, and still 15 kPa short).
- **The fill of 1.11–1.13 at 0.15 m and 0.12 m is the same effect at a smaller size.** The gradients above are for paste about a tenth denser than nominal.
- Both pre-stress options stay in the code, off.

### Solver substeps, and a collapse at the screw inlet (15 and 16 Nov 2026)

The chamber loses paste volume in two separate ways, and they need different cures:

1. **Under a standing load**, the solver sheds elastic volume each frame because its iterative solve stops short. This is the loss that over-packs the 0.10 m chamber above.
2. **Where a solid moves through the paste** (the turning cutterhead), the elastic volume does not follow the particle density ([13 Nov](#cause-of-the-pressure-loss)). The balance by region corrects this one.

**Loss 1: solver options at a standing load.** The 0.10 m chamber was started pre-stressed with no balance (as `ch_pre_v010`), and each solver option was changed on its own. The table gives the axis pressure held at standstill, from 200 kPa set:

| Record | Change | Held at standstill (kPa) | ms per frame |
|---|---|---|---|
| `ch_ws_base` | none: 1 solver step of 100 iterations per frame, Newton's default warm start | 73 | 154 |
| `ch_ws_none` | warm start off | 10 | 145 |
| `ch_ws_part` | warm start from the particles | 38 | 153 |
| `ch_ws_left` | the strain the solve leaves unexplained kept in the elastic strain (Newton's `_INCLUDE_LEFTOVER_STRAIN`) | 80 | 155 |
| `ch_ws_both` | particles warm start and leftover strain | 67 | 156 |
| `ch_cv_crgs`, `ch_cv_cggs` | a Krylov solve (conjugate residual or conjugate gradient) ahead of Gauss–Seidel | 73, 73 | 157–159 |
| `ch_cv_sub4` | 4 solver steps of 25 iterations | 112 | 501 |
| `ch_cv_sub4x100` | 4 steps of 100 | 118 | 617 |
| `ch_cv_sub8` | 8 steps of 13 | 125 | 977 |

- Only smaller solver steps help much: a quarter of the time step, at the same total iterations, keeps half as much again. More iterations per step add little.
- **Adopted as the default (15 Nov): 4 solver steps of 50 iterations per frame** (`ChamberConfig.substeps`, `iterations`; the runner's `--iterations` default is now 50). This is an assumed numerical setting, chosen on cost against the table above, not fitted to any validation figure.

**Loss 2 stays:** with 4 × 50 and the balance off, the chamber falls to 29 / 31 / 29 kPa in excavation at 0.15 / 0.12 / 0.10 m (`ch_subnb_*`). The balance by region stays on.

**With 4 × 50 and the balance, all three voxels hold** (seeds 0, 1, 2; records `ch_sub_*`):

| | 0.15 m | 0.12 m | 0.10 m |
|---|---|---|---|
| Axis pressure in excavation (kPa) | 200.6 / 200.5 / 200.6 | 197.3 / 196.9 / **lost at 16.5 s** | 198.8 / 198.6 / 199.0 |
| Contact gradient (kPa/m) | 11.0 / 10.9 / 10.8 | 14.7 / 14.7 / – | 12.7 / 12.6 / 12.8 |
| Screw (rpm) | 13.5–13.9 | 10.2 | 7.5–7.8 |
| ms per frame | 167–181 | 289–301 | 464–524 |

- **0.10 m now holds the set point**, for the first time. Seed 2 there went invalid after the stop.
- **0.12 m seed 2 was lost suddenly:** the pressure was at the set point one moment and gone within a few frames, unlike the slow runaway of the corner regions.

**Cause of the sudden loss: the screw inlet.** The screw is analytical: each frame it removes the paste it owes from a box at the bulkhead/invert corner. Until now it took the particles deepest in its casing first, the ones hard against the bulkhead. Seed 2 at 0.12 m was rerun with a check after every solver step (`ChamberConfig.substep_check`):

- **Emptying that corner drew jets into it.** Paste rushed into the gap at 37–235 m/s, against under 4 m/s anywhere else in the chamber (fastest particle up to 125–235 m/s in runs that held, `ch_sc_v012_s2`, `ch_sr_*`).
- **The collapse starts with one crushed particle.** In `ch_se_v012_s2` the first invalid particle (elastic volume ≤ 0) appeared at (0.01, 0.07, 0.63) m, in the inlet corner, at 17.6 s. All 244,230 particles were invalid one solver step later: the solver couples every particle, so one invalid particle spoils the whole solve.
- **A GPU timing fault is ruled out:** the run with a check (and a device sync) after every step also collapsed.
- **Wall pick, 0.12 m, seed 2, no repair:** 3 of the 4 recorded runs were lost: `ch_sub_v012_s2` at 16.5 s, `ch_se_v012_s2` at 17.6 s and `ch_rp_v012_s2` at 21.4 s. Only `ch_sc_v012_s2` held. A fifth run, which split the discharge over the solver steps, also collapsed, and the script then stopped before writing its record.
- **Resetting invalid particles after each solver step stops the spread** (`substep_repair`, records `ch_sr_v012_s2`, `_a`, `_b`, `_c`, `ch_sr_v010_s2`): all five held. Only one particle needed a reset, at 12.5 s, at (0.00, −0.20, 0.55) m, in the inlet corner again.

**Fix (16 Nov): take the paste from the middle of the inlet.** `ChamberConfig.screw_pick = "centre"` takes the particles nearest the middle of the box; the old behaviour stays as `"wall"`. At 0.12 m seed 2, four runs held with no particle above 12.1 m/s (`ch_gs_c_a`, once per frame; `ch_gs_cs_a`, `_b`, `_c`, with the discharge split over the solver steps, `screw_per_substep`). Splitting adds nothing visible, so it stays off. The repair stays in the code, off: with the middle pick it has not been needed.

**Check of the new defaults** (4 × 50, middle pick, balance with merged corners; seeds 0 / 1 / 2; records `ch_dv_*`). All nine runs hold through the 20 s excavation and the stop, with no invalid particle:

| | 0.15 m | 0.12 m | 0.10 m |
|---|---|---|---|
| Axis pressure at standstill (kPa) | 206.3 / 207.8 / 208.6 | 210.0 / 211.2 / 210.6 | 204.6 / 205.5 / 204.9 |
| Axis pressure in excavation (kPa) | 200.4 / 200.4 / 200.6 | 197.1 / 196.8 / 197.0 | 199.1 / 198.7 / 199.1 |
| Lowest after pressurising (kPa) | 194–195 | 191–193 | 194 |
| Contact gradient in excavation (kPa/m; fixed bands, [aliased](#the-bulkhead-reading-and-the-gradient-at-four-voxels-16-nov-2026)) | 10.9 / 10.8 / 10.8 | 14.6 / 14.6 / 14.6 | 12.7 / 12.7 / 12.8 |
| Screw in excavation (rpm; 9.95 balances the advance) | 13.6 / 13.3 / 13.9 | 10.2 / 10.2 / 10.3 | 7.7 / 7.9 / 7.8 |
| Bulkhead thrust (MN) | 8.8 | 7.7 | 8.1 |
| Mixing torque (MNm) | 0.60–0.61 | 0.54 | 0.40–0.41 |
| ms per frame (GB10 GPU) | 187–192 | 314–340 | 549–560 |

- **The set point holds at three voxels, in every seed.** In excavation the seeds agree to within 0.4 kPa in pressure and 0.1 kPa/m in gradient. Against the wall pick, the numbers do not change where both held.
- **Neither the contact gradient nor the screw seemed to converge with the voxel:** the gradient read 10.8 → 14.6 → 12.7 kPa/m and the screw speed 13.6 → 10.2 → 7.8 rpm from 0.15 m to 0.10 m. The gradient spread was mostly the band reading, and the screw does not keep falling at 0.08 m ([next section](#the-bulkhead-reading-and-the-gradient-at-four-voxels-16-nov-2026)).
- **Paste escapes the chamber:** 360–780 particles per run leave the chamber and fly ballistically (up to about 370 m away). They take no part in the solve, but they should be deleted. Open.

**Step and thrust runs repeated with 4 × 50** (0.15 m, seed 0, before the middle pick; records `ch_sub_step_*`, `ch_sub_thr_*`; set-up as [above](#response-to-a-screw-speed-step)). The predicted rate here is the balance's own: bulk modulus × change in discharge / chamber volume.

| Record | Change at 10 s (step) or 12 s (thrust) | Result |
|---|---|---|
| `ch_sub_step_stop` | screw 14.2 → 0 rpm | +2.34 kPa/s, 73 % of the predicted +3.20; 206 → 252 kPa |
| `ch_sub_step_up` | screw 14.4 → 22 rpm (the cap) | −2.20 kPa/s, 129 % of the predicted −1.71; 207 → 163 kPa |
| `ch_sub_thr_base` | none | advance 60 mm/min (50–68), screw's discharge 60; axis 214 kPa over the last 5 s |
| `ch_sub_thr_f110` | thrust +10 % | axis 235 kPa over the last 5 s, +9.5 %; the advance rises to the cap and returns to 66 |
| `ch_sub_thr_screw` | screw +50 % | advance 83 mm/min over the last 5 s (90 from the discharge); axis 210 kPa |

- **Under thrust the result stands:** the screw sets the advance and the thrust sets the pressure.
- **The step response is no longer symmetric:** a stopped screw raises the pressure at 73 % of the predicted rate, but the faster screw lowers it at 129 %. With one solver step, both directions were at 77–80 %. Explained on 17 Nov: the prediction assumed the chamber was in balance before the step ([repeat](#screw-step-and-thrust-on-a-settled-chamber-17-nov-2026)).

### The bulkhead reading and the gradient at four voxels (16 Nov 2026)

The bulkhead contact gradient read 10.8 / 14.6 / 12.7 kPa/m at 0.15 / 0.12 / 0.10 m, while the paste inside the chamber (stress × fill) read 14.3 / 14.7 / 13.6. The contact reading was checked first.

**The cause: two force lattices and fixed bands.**
- Newton reports the force a solid takes from the paste at two lattices of points: cell centres, half a voxel inside the bulkhead plate (about three quarters of the points and two thirds of the force), and grid vertices on its face, with gaps.
- The scene summed these forces in nine bands of fixed height (±0.9 R) and divided by each band's area. A band 0.71 m high holds 4–5 rows of each lattice at 0.15 m, 5–6 at 0.12 m and 7–8 at 0.10 m, in a pattern that changes from band to band. Each band read 0.82–1.25 times its pressure.
- **The gradient and the controlled pressure were both biased.** The controller holds the band at the axis, so at 0.15 m the chamber was held at a mean contact pressure of about 227 kPa for a reading of 200. The bulkhead thrust showed it: 8.81 MN against 7.89 for 200 kPa over the area. At 0.12 m and 0.10 m the error was 1–2 %.

**Logged by row** (`ChamberConfig.contact_rows`: the force summed per row of each lattice over every frame; records `ch_cl_*`, seeds 0 and 1). Summed in 2-voxel bins, each holding two rows of each lattice, the reading has no aliasing:

| Excavation | 0.15 m | 0.12 m | 0.10 m |
|---|---|---|---|
| Band reading, fixed edges (kPa/m) | 10.6 / 10.6 | 14.5 / 14.5 | 12.7 / 12.7 |
| Contact in 2-voxel bins (kPa/m) | 11.4 / 11.5 | 13.2 / 13.2 | 11.3 / 11.3 |
| Mean contact pressure at the axis (kPa) | 227 / 227 | 198 / 198 | 199 / 199 |

**Fix (16 Nov): band edges on the grid.** Each band edge now sits a quarter voxel below a vertex row, so every band holds the same number of rows of each lattice. Band heights become whole voxels (4–5, 5–6 and 7 at 0.15, 0.12 and 0.10 m). Checked on the logged rows, the bands now lie within ±1.5 % of a straight line, against 0.85–1.09 before. This changes the controlled pressure at 0.15 m.

**Two other readings were tried and dropped or kept aside:**
- **A fixed-width strip** (1 m each side of the screw column, edges also on the grid, ±0.8 R) needs no area. It changed from 12.1 to 16.7 kPa/m when the machine was raised by half a voxel. Its rows are too narrow for the gaps in the vertex lattice. Dropped.
- **The 2-voxel bins** stay in the records (`contact_two_voxel_bins`). They read 1.3–1.9 kPa/m below the snapped bands in excavation at every voxel, with the same order across the voxels. The two differ in the weight given to the rows near the shell, where the force points across a row do not fill the chord. Which weighting is right is not settled. The snapped bands are used because they agree with the paste inside the chamber (below).

**Alignment with the grid** (records `ch_sb_v015_zh`, `ch_sb_v012_zh`): raising the whole machine by half a voxel moves the band gradient by 0.6 kPa/m at 0.15 m and 0.1 kPa/m at 0.12 m. The earlier high reading at 0.12 m came from the bands, not from the alignment.

**Four voxels with the fixed reading** (seed 0; records `ch_sb_v015`, `_v012`, `_v010`, `_v008`):

| | 0.15 m | 0.12 m | 0.10 m | 0.08 m |
|---|---|---|---|---|
| Particles | 130,112 | 247,043 | 434,812 | 852,040 |
| Axis pressure in excavation (kPa) | 196.1 | 197.1 | 199.1 | 198.5 |
| Bulkhead thrust / axis pressure × area (MN) | 7.75 / 7.72 | 7.83 / 7.76 | 8.02 / 7.84 | 7.76 / 7.81 |
| **Contact gradient, excavation (kPa/m)** | **13.5** | **14.7** | **12.9** | **15.2** |
| Contact gradient, standstill / after the stop | 13.5 / 13.7 | 13.1 / 15.2 | 12.3 / 11.6 | 13.9 / 15.5 |
| Paste inside, stress × fill, excavation | 14.6 | 14.7 | 13.6 | 15.1 |
| Paste weight at its fill (13.05 × fill) | 14.2 | 14.1 | 14.3 | 14.4 |
| Screw in excavation (rpm; 9.95 balances the advance) | 13.6 | 10.1 | 8.0 | 13.8 |
| ms per frame (GB10 GPU) | 183 | 311 | 555 | 1,170 |

- **The bulkhead and the paste inside now agree** within 1.1 kPa/m at every voxel (before: up to 3.7).
- **No trend with the voxel:** in excavation the contact gradient is 14.1 ± 1.1 kPa/m over the four voxels, and the paste inside 14.5 ± 0.6. Both scatter about the weight of the paste at its fill, 14.1–14.4 kPa/m. The paste is about a tenth denser than nominal ([15 Nov](#gradient-paste-density-by-height-15-nov-2026)). All values are inside Botlek's 10–20 kPa/m.
- **The scatter is not seed noise:** seeds repeat to 0.3 kPa/m at each voxel. 0.10 m is the low one in both readings, also in three earlier seeds (paste inside 13.6–13.7); the reason is not shown.
- **The screw speed scatters with the voxel too** (8.0–13.8 rpm), against 9.95 for the advance. The earlier statement that it falls as the voxel shrinks does not hold at 0.08 m. This scatter is the pressure controller's swing, not a voxel effect ([17 Nov](#screw-speed-the-controllers-swing-and-the-screw-volume-17-nov-2026)).
- **These are 20 s readings.** At 0.15 m the gradient was still rising at the end: over the last 50 s of a 100 s excavation it reads 15.1 kPa/m ([17 Nov](#screw-speed-the-controllers-swing-and-the-screw-volume-17-nov-2026)).
- **Earlier contact gradients in this page used the fixed bands.** Their pattern across voxels is affected. The 0.15 m runs ran 11–13 % above the set point, measured at the bulkhead as a whole: in every 0.15 m record from 8 Nov on, the bulkhead thrust is 1.11–1.12 times the axis pressure × area (1.00 with the fix); the 0.12 m and 0.10 m runs were within 2 %. The paste-inside readings (stress × fill) do not use the bands and stand.

### Screw speed: the controller's swing, and the screw volume (17 Nov 2026)

The screw speed needed to hold the set point read 13.6 / 10.1 / 8.0 / 13.8 rpm at 0.15 / 0.12 / 0.10 / 0.08 m, against 9.95 rpm for the advance. The screw is analytical: it removes the volume its speed discharges, and the pressure controller sets the speed. So the spread must be in the chamber's volume budget or in the controller.

**The controller has not settled in a 20 s excavation.**
- Its gains (kp 0.2 rpm/kPa, ki 0.05 rpm/(kPa·s), assumed) and the chamber's stiffness (bulk modulus over paste volume, about 0.22 kPa/s per rpm; the step tests measured the same) give a loop with a period of about 60 s and a damping ratio of about 0.2.
- Each voxel starts excavation at a different pressure after the hold (218 / 210 / 205 / 210 kPa at 0.15 / 0.12 / 0.10 / 0.08 m). The reported speed is the mean of the second half of the excavation, a different point of the swing at each voxel.
- **Runs with a 100 s excavation** (seed 0; records `ch_lx_v015`, `_v012`, `_v010`, with 10 s means in `by_10_s_excavate`): the screw speed swings with a period of 40–50 s. The swing dies down at 0.15 m and 0.12 m but not at 0.10 m, where it is still ±2.5 rpm after 100 s (why the damping is lower there is not shown).

| Screw (rpm) | 0–10 s | 10–20 | 20–30 | 30–40 | 40–50 | 50–60 | 60–70 | 70–80 | 80–90 | 90–100 | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.15 m | 15.2 | 13.8 | 9.6 | 7.2 | 9.2 | 12.3 | 12.8 | 11.3 | 10.0 | 9.5 | 11.1 |
| 0.12 m | 11.4 | 10.0 | 8.8 | 9.0 | 10.9 | 11.9 | 11.4 | 10.3 | 9.6 | 9.7 | 10.3 |
| 0.10 m | 8.9 | 8.1 | 9.5 | 12.1 | 12.2 | 11.0 | 9.9 | 10.1 | 12.5 | 12.9 | 10.7 |

**Reading the screw by volume (adopted 17 Nov).** `chamber.run` now reports `screw_volume_excavate`, over the whole excavation:
- the volume the screw removed (particles × their in-situ volume) and the volume the piston displaced;
- their ratio, raw and less the change of the paste's elastic volume over the excavation (the balance's mean ln J target times the paste's particle volume). That change is the part of the swing still under way when the excavation ends.

Set against the paste's fill (mass over nominal density and space, in the prisms of the [density profile](#gradient-paste-density-by-height-15-nov-2026)):

| Run | Voxel | Screw / displaced, raw | Elastic swing (m³) | Less the swing | Fill |
|---|---|---|---|---|---|
| `ch_dv_v015_s0`–`s2` (20 s) | 0.15 m | 1.31–1.36 | +0.16 to +0.19 | 1.103–1.112 | 1.096–1.099 |
| `ch_dv_v012_s0`–`s2` (20 s) | 0.12 m | 1.10 | +0.02 to +0.03 | 1.064–1.065 | 1.083–1.084 |
| `ch_dv_v010_s0`–`s2` (20 s) | 0.10 m | 0.82–0.84 | −0.21 to −0.23 | 1.103–1.108 | 1.094–1.096 |
| `ch_sb_v008` (20 s) | 0.08 m | 1.41 | +0.25 | 1.091 | 1.100 |
| `ch_lx_v015` (100 s) | 0.15 m | 1.12 | +0.08 | 1.093 | 1.109 |
| `ch_lx_v012` (100 s) | 0.12 m | 1.04 | −0.14 | 1.071 | 1.083 |
| `ch_lx_v010` (100 s) | 0.10 m | 1.08 | −0.11 | 1.106 | 1.106 |

- **The screw volume closes at every voxel and seed:** less the elastic swing, it is the displaced volume times the fill, within 2 % (0.12 m reads 1–2 % below its fill, the others within 1.5 %). The raw ratio spans 0.82–1.45 in 20 s runs.
- **The screw removes about a tenth more than the piston displaces because the paste is about a tenth denser than nominal,** packed so by the piston push before excavation ([15 Nov](#the-010-m-chamber-over-packed-by-the-piston-push-15-nov-2026)). The budget closes without the paste that escapes the chamber (0.02–0.5 m³ per run); where it escapes was not traced.
- **The screw speed is not a voxel effect:** averaged over 100 s it is 11.1 / 10.3 / 10.7 rpm, 1.04–1.11 times the advance's rate. The scatter of 8–14 rpm in 20 s runs was the controller's swing.
- **The gradient needs the long window too at 0.15 m.** Over the last 50 s of the 100 s runs the contact gradient is 15.1 / 15.6 / 13.05 kPa/m at 0.15 / 0.12 / 0.10 m. In 20 s runs 0.15 m read 13.5. So 0.15 m and 0.12 m agree within 0.5 kPa/m once settled, and 0.10 m stays about 2 kPa/m below both. 0.08 m was run for 20 s only.
- **The screw-step asymmetry has a related cause:** the step was made while the controller was still swinging, and the prediction assumed the chamber was in balance at the speed before the step ([next section](#screw-step-and-thrust-on-a-settled-chamber-17-nov-2026)).
- **The controller gains are assumed.** Gains that damp the swing within one period (kp about 0.7 rpm/kPa) would make a 20 s excavation readable, but they would change the step and thrust results, and no open source for an EPB screw controller has been found. Left as they are.

### Screw step and thrust on a settled chamber (17 Nov 2026)

The step and thrust runs were repeated at 0.15 m with the fixed bulkhead reading (a true 200 kPa) and a 90 s excavation, each change made 60 s in (seed 0; records `ch_st_*`).

**Why the step response looked uneven.** The predicted rate was the bulk modulus times the *change* of the screw's discharge, over the paste volume. That assumes the chamber was in balance at the screw speed before the step. It was not: the controller was still swinging, and the screw turned at 13.4–14.4 rpm where about 10.9 rpm balances the advance (9.95 rpm times the paste's fill of 1.09–1.10, [above](#screw-speed-the-controllers-swing-and-the-screw-volume-17-nov-2026)).

**Prediction from the net flow (adopted 17 Nov).** The rate after the step follows from the piston's displacement against the screw's discharge after the step. The discharge is counted at the paste's particle density (particles times their in-situ volume over the chamber space), as the volume balance counts it. `chamber.run` reports it as `rate_net_flow_kPa_per_s` beside the old prediction; it was added to `ch_sub_step_stop` and `_up` from their own logs.

| Record | Screw (rpm) | Measured (kPa/s) | Old prediction | Net-flow prediction | Measured / net flow |
|---|---|---|---|---|---|
| `ch_sub_step_stop` (20 s run, step at 10 s, fixed bands) | 14.2 → 0 | +2.34 | +3.20 (73 %) | +2.24 | 1.04 |
| `ch_sub_step_up` (same) | 14.4 → 22 | −2.20 | −1.71 (129 %) | −2.25 | 0.98 |
| `ch_st_stop` (90 s run, step at 60 s) | 13.5 → 0 | +2.63 | +3.12 (84 %) | +2.30 | 1.14 |
| `ch_st_up` (same) | 13.4 → 22 | −2.56 | −2.00 (128 %) | −2.37 | 1.08 |

- **The asymmetry is explained:** both directions agree within 6–7 % in each pair. It was the prediction's assumption, not the chamber.
- **The 90 s runs read 8–14 % above the net-flow prediction, the 20 s runs within 4 %.** In the 90 s stopped-screw run the pressure climbs from 208 to 282 kPa over the 30 s after the step and the fit runs over all of it; whether the curvature explains the excess is not checked.
- **At 0.15 m the controller still swings at 60 s:** the screw was at 13.4 rpm when the step came, so "+10 rpm" reached the 22 rpm cap again. The prediction uses the actual speeds.
- **The 13 Nov results (77–80 %, one solver step) used the same prediction** from the speed before the step. They are not recomputed: those runs did not log the particle count.
- Still checked against the analytical chamber model only; no open record of a screw step on a machine has been found.

**Shove under thrust at a true set point:**

| Record | Change at 60 s | Axis pressure (kPa) | Advance (mm/min) |
|---|---|---|---|
| `ch_st_thr_base` | none | 216 | 55 (52–58); the screw's 60 over the fill of 1.10 is 54.7 |
| `ch_st_thr_f110` | thrust +10 % | 216 → 237 (+9.9 %) | to the 120 mm/min cap, back to 57 |
| `ch_st_thr_screw` | screw +50 % | 215 → 210 (−2.6 %) | 55 → 85 (82 from the discharge over the fill) |

- **The screw sets the advance and the thrust sets the pressure,** as found on 13 Nov, and the numbers now close: under a fixed screw the advance is the screw's discharge divided by the paste's fill.
- **Under thrust the chamber sits at 216 kPa, not 200:** the set thrust is the force that held the piston at standstill, and at 0.15 m the hold ends at about 218 kPa.
- **The screw volume closes in all five runs:** less the elastic swing it is 1.094–1.099 times the displaced volume, the fill again.
- The net-flow prediction does not apply under thrust, where the advance changes with the step.

### The shell leak: a watertight tube (18 and 19 Nov 2026)

Without `seal_shell` the paste leaked into the shell wall, and how much depended on where the wall's inner face fell on the grid. Moved by an eighth of a voxel at 0.11 m, the same chamber needed 14.05 M particle resets in one run and 3.19 M in another, and its gradient read 11.97 or 13.34 kPa/m.

**What did not help** (all at 0.11 m, recorded as negative results):
- a thicker shell (3 and 4 voxels, in place of 2);
- moving the inner face by fractions of a voxel (eight positions): each position leaks, or does not, in a fixed pattern;
- more plates (96 and 192 in place of 48): 192 plates leaked worst of all, 20.19 M resets, at the crown, where the paste pressure is lowest.

So the leak was not driven by pressure, and it came back wherever a plate landed at a bad position on the grid.

**The cause is in how Newton 1.7.0 builds a collider from several shapes.**
- The implicit MPM solver merges all shapes of a body into one triangle mesh (`_create_body_collider_mesh`). The shell's 48 overlapping box plates become one mesh that still holds their side faces, buried inside the wall.
- Each grid node is signed inside or outside from the face normals at its closest point on that mesh. Where the closest point lies on a buried face, a node inside the wall is signed outside.
- An offline check of Newton's sign rule at 0.11 m, for all eight face positions:
  - the box plates sign 86–104 of about 410 wall nodes as outside at every position;
  - one watertight tube mesh of 256 segments signs none wrongly (distances right to 0.002 voxel).
- Which of the mis-signed nodes sit shallow enough to let paste in changes with the face position. That fits the on/off pattern found above.

**Fix, the default since 19 Nov:** the shell is one watertight tube mesh (`ChamberConfig.shell_mesh = 256`). `shell_mesh = 0` keeps the old plates.

| Case | Shell | Particle resets | Gradient in excavation (kPa/m) | Paste escaped |
|---|---|---|---|---|
| 0.11 m, face moved ⅛ voxel | plates / **tube** | 14.05 M / **0.01 M** | 11.97 / **14.60** | 1948 / 200 |
| 0.11 m, face at R | plates / **tube** | 3.19 M / **0.01 M** | 13.34 / **14.34** | 465 / 107 |
| 0.10 m, face at R | plates / **tube** | 2.82 M / **0.01 M** | 12.82 / **14.37** | 945 / 250 |
| 0.12 m, face at R | plates / **tube** | 0.20 M / **0.00 M** | 14.74 / **15.33** | 454 / 98 |

- **The leak is gone at every case.** Even the 0.12 m chamber, which had looked clean, was leaking 0.2 M particles and reading 0.6 kPa/m low.
- **The balance's corrections shrink:** every region takes about 0.15 % per frame. The bottom regions no longer take the large ones.
- **The tube is no slower:** 308–586 ms per frame, the same as the plates.
- **The runs here still use `seal_shell`** (off by default) for stray particles: 5–23 thousand resets per run, against 0.2–14 M with the plates.
- **The cutterhead** is also built from overlapping boxes. The same offline check of its merged mesh, at seven voxels from 0.08 m to 0.15 m and six angles, found no mis-signed nodes.
- **Newton's open pull request [#5021](https://github.com/newton-physics/newton/pull/5021)** adds a setting, `collider_winding_number`, that treats merged shapes as their union when signing nodes. It is not in a release and not tested here. The tube is the fix on Newton 1.7.0.

### The bulkhead gradient at seven voxels (19 to 21 Nov 2026)

**With the tube shell, the band reading** (nine bands snapped to the grid, [16 Nov](#the-bulkhead-reading-and-the-gradient-at-four-voxels-16-nov-2026)) gives 15.21 / 15.16 / 14.37 / 14.34 / 15.33 / 15.06 / 14.42 kPa/m at 0.08 / 0.09 / 0.10 / 0.11 / 0.12 / 0.13 / 0.15 m. That has no trend, but there is a step of 0.9 kPa/m between 0.10 m and 0.12 m. Three seeds give 14.37 / 14.38 / 14.44 at 0.10 m and 15.33 / 15.32 / 15.27 at 0.12 m, so the step is systematic, not scatter.

**Ruled out as the cause of the step:**
- **The cutterhead's signs** (above).
- **The bulkhead's friction:** a frictionless bulkhead (`bulkhead_friction = 0`, the shell kept at 0.3) reads 14.40 and 15.24.
- **Where the bands sit:** the step is not tied to the band positions.

**The paste does not show the step.** The paste's horizontal stress per unit of space (particle stress × nominal particle volume / space) reads 14.4–14.5 kPa/m 1–4 voxels from the bulkhead at both voxels. That equals the paste's weight at its fill.

**A diagnostic tank checked that stress measure, and the contact reading itself.** The tank holds chamber paste with one measured wall, and has its own lid, seal and volume balance. Its script is not in the repository.
- **Under gravity alone,** the wall gradient is 0.92–1.02 of the paste's gradient beside it at every voxel, with no excess at 0.12 m.
- **Under a 200 kPa lid with frictionless walls** (three seeds each), the wall reads 0.958 ± 0.042 of the paste's weight at 0.10 m and 0.922 ± 0.031 at 0.12 m.
- **With friction 0.3 on the side walls,** the tank arches like a silo. The side walls carry 68–70 % of the paste's weight, and the measured wall reads 0.40–0.46 of it.
- **Checked against the forces over whole cuts of the tank,** the stress measure closes the vertical balance to 0.1 % and the horizontal balance to 1–4 %, with rough or smooth side walls.
  - The particles' nominal volume is the right one to use. Their current volume reads 7–8 % low.
  - The first voxel next to a wall reads high.

**The same force balance in the chamber locates the step.** Summed over the 20 s excavation (`ChamberConfig.stress_log`), the bulkhead's axial force is compared with the paste's axial stress, by rows one voxel high across the full section (edges a quarter voxel below the vertex rows):

| | 0.10 m (seed 1) | 0.12 m (seed 0) |
|---|---|---|
| Band reading (kPa/m) | 14.41 | 15.25 |
| Bulkhead, full-section rows (kPa/m) | 14.38 | 14.65 |
| Paste 1–2 / 2–4 voxels out (kPa/m) | 14.61 / 14.52 | 14.49 / 14.53 |
| Bulkhead / paste total force (MN) | 8.255 / 8.394 | 7.898 / 8.005 |

- **Read across the full section, the bulkhead reads the paste at both voxels:**
  - within 0.3 kPa/m in gradient;
  - within 1.3–1.7 % in total force.
- **So the step is in the bands, not in the paste or in what Newton reports on the bulkhead.** The bands leave out the strip round the screw inlet (|y| < 0.75 m, the screw's radius plus 0.3 m). A likely cause, not shown: the edge of that strip catches the lattices of contact points unevenly at some voxels, as fixed band edges did in height before 16 Nov.

**The reported gradient now uses full-section rows (since 20 Nov):**
- rows one voxel high, edges a quarter voxel below the vertex rows;
- every bulkhead contact, so the rows add up to the bulkhead thrust;
- least squares over |z − zc| < 0.8 R.

The bands still give the axis pressure that the controller holds, and their gradient stays in the records as `gradient_bands_hold_excavate_kPa_per_m`. This changes how the force is read, justified by the force balance. Nothing is fitted to Botlek.

The seven voxels were rerun with this reading (seed 0; records `ch_rg_v008` to `ch_rg_v015`):

| | 0.15 m | 0.13 m | 0.12 m | 0.11 m | 0.10 m | 0.09 m | 0.08 m |
|---|---|---|---|---|---|---|---|
| Axis pressure in excavation (kPa) | 198.2 | 197.5 | 197.5 | 196.7 | 202.3 | 197.9 | 198.0 |
| **Gradient, full-section rows (kPa/m)** | **14.63** | **14.69** | **14.67** | **14.23** | **14.36** | **14.48** | **14.67** |
| Gradient, bands (kPa/m) | 14.44 | 15.09 | 15.29 | 14.38 | 14.37 | 15.16 | 15.20 |
| Paste 2–4 voxels out (kPa/m) | 14.16 | 14.13 | 14.44 | 14.37 | 14.59 | 14.50 | 14.75 |
| Bulkhead force / thrust (MN) | 8.06 / 8.06 | 8.01 / 8.01 | 7.90 / 7.90 | 8.00 / 8.00 | 8.26 / 8.26 | 7.91 / 7.91 | 7.94 / 7.94 |

- **The gradient is 14.53 ± 0.18 kPa/m over the seven voxels** (range 0.46), with no trend with the voxel. With the bands it was 14.85 ± 0.43 (range 0.92).
- **Repeat runs agree within 0.07 kPa/m:**
  - 0.12 m, seed 0 twice: 14.65 and 14.67;
  - 0.10 m, seeds 0 and 1: 14.36 and 14.38;
  - 0.15 m, seed 0 twice: 14.63 and 14.70 (the second run computing the reading in the scene, record `ch_rg_v015_check`).
  So the remaining spread between voxels (0.46 kPa/m) is small but larger than the repeat scatter.
- **It is inside Botlek's 10–20 kPa/m,** within 3 % of the paste's weight at its fill (14.1–14.4) and within 0.6 kPa/m of the paste 2–4 voxels out.
- **The paste 1–2 voxels out reads up to 15.6 kPa/m at 0.15 m.** That is the first voxel's excess, also seen in the tank.

**A sudden loss came back once.** One 0.10 m run (seed 0, the force-balance logging on, otherwise the defaults) lost its whole chamber 16.1 s into excavation (20.35 s into the run). An identical earlier run and seed 1 held. Runs on the GPU do not repeat bit for bit, so the loss fixed on [16 Nov](#solver-substeps-and-a-collapse-at-the-screw-inlet-15-and-16-nov-2026) is rarer, not gone.

The per-frame logs of that run (`stress_log`, the balance's log) show:
- **The chamber was healthy until the last frame.** No particle was invalid at any frame of the excavation. The balance's largest correction per frame stayed at its usual size (median 0.006 in ln J, at most 0.047). The axis pressure was 198–208 kPa, the screw 15–17 rpm, and the torque and cutterhead forces were steady.
- **In the frame that ended at 20.35 s**:
  - the largest correction rose to 0.036, in the region at the invert, just off the centreline, in the third of the chamber nearest the ground face (x 0.84–1.26 m, in front of the cutterhead's face at 0.75 m);
  - the shell's vertical force fell from 734 to 717 kN;
  - the pressure on the ground face fell from 206.9 to 205.6 kPa.
- **One frame later 427,197 of 427,221 particles were invalid.** The spread took at most four solver steps.

So the trigger was local. Unlike 16 Nov, it was not at the screw inlet, and it gave no warning a frame earlier. These logs cannot say which particle failed first: that needs the check after each solver step (`substep_check`), which was off.

**Traced with a check on the GPU (21 Nov, `ChamberConfig.substep_guard`).** After every solver step a Warp kernel counts invalid and extreme particles (J outside 0.1–10) and the fastest speed. It reads back three numbers, and every quarter second it saves where the extreme and fast particles are. On an invalid particle it saves that particle and its neighbours before and after the step, then resets it as `substep_repair` does. A test with one particle broken on purpose was caught, saved and reset in the same step, and the run went on.

Seven runs with the guard (records in `server/diagnostics/out_box`, `gd_*`). The onset is the first solver step with an extreme particle. In excavation the face moves 20 mm, from x = 1.273 m to 1.253 m in the standard runs.

| Run | Face position at onset | Solver steps with extreme particles | Fastest (m/s) | Invalid |
|---|---|---|---|---|
| 0.10 m, seed 0 | x = 1.2605 m, 17.1 s into the run | 3158 | 56 | 0 |
| 0.10 m, seed 1 | 1.2607 m, 16.9 s | 3212 | 89 | 0 |
| 0.10 m, seed 2 | 1.2619 m, 15.7 s | 2882 | 13 | 0 |
| 0.12 m, seed 0 | 1.2634 m, 15.9 s | 3463 | 11 | 0 |
| 0.10 m, slab 0.65 m (face 5 cm further out) | not reached (face 1.323 → 1.303 m) | 1 | 17 | 0 |
| 0.10 m, seed 0, cutterhead 1 cm nearer the face (21 Nov) | 1.2644 m, 14.9 s | 3009 | 11 | 0 |
| 0.10 m, seed 0, shell tube's end 10 cm nearer (21 Nov) | 1.2599 m, 17.7 s | 3020 | 48 | 0 |

- **The extreme particles sit in the corner of the ground face and the shell:**
  - within about 4 cm of the face and 4–40 cm of the shell;
  - in clusters at a few angles around the circumference;
  - with J from 0.007 to 7 × 10⁴;
  - a few inside the ground piston, where it overlaps the shell.
  Once they appear they stay to the end of the run. The lost run's last warning sign was in the same corner, at the invert.
- **They appear when the ground face reaches x ≈ 1.26 m, at both voxels.** The face then stands about 0.51 m in front of the cutterhead's face and 0.64 m from the end of the shell tube. With the slab 5 cm longer the face never got there, and the run had extreme particles in one solver step only.
- **Not a sign error:** an offline check of the tube and the piston, with Newton's rule (nearest collider, sign from the averaged normal), finds no mis-signed node near that corner at any face position.
- **None of the seven runs had an invalid particle,** so the guard reset nothing. The lost run probably failed from one of these corner particles. That makes it a rare event among many runs that carry them; this is likely, not shown.
- **Not the shell tube's end (21 Nov, `shell_end_shift = -0.10`):**
  - With the end 10 cm nearer, the onset stays at 1.2599 m, within 1 mm of the three seeds.
  - The slab 0.65 m run agrees: its face passed the same distance from the end, 0.64 m, with no onset.
- **Not the cutterhead gap alone (21 Nov, `cutter_shift = 0.01`):**
  - If the gap set it off, moving the cutterhead 1 cm toward the face would move the onset 1 cm, to about 1.270 m. It moved 3 mm, to 1.2644 m, from 1.2605–1.2619 m in the three seeds. That is one seed; at most a small part of the shift can come from the gap.
  - This run started excavation with the face 1.7 mm further out (1.2750 m), because the chamber between the moved cutterhead and the face is smaller. Its onset came 10.6 mm into the advance, against 11.4–12.8 mm in the seeds.
  - It had at most 7 extreme particles at a time, against 17–47.
- **Open:** what fixes the face position at about 1.26 m. Neither the shell's end, nor the cutterhead gap alone, nor the face's place on the grid explains it.

**Closed with the guard on by default (21 Nov).** Since the cause of the corner particles is not found, `substep_guard` is now on by default. It is a numerical safeguard, not physics, and every result reports how many particles it reset (`substep_guard.particles_reset`). The lost set-up (0.10 m, seed 0, the same logs) was run three more times with it:

| Repeat | Onset (face) | Steps with extreme particles | Fastest (m/s) | Particles reset | Axis pressure in excavation | Gradient |
|---|---|---|---|---|---|---|
| 1 | 1.2608 m | 3247 | 193 | 0 | 202.4 kPa | 14.58 kPa/m |
| 2 | 1.2605 m | 3162 | 14 | 0 | 202.4 kPa | 14.56 kPa/m |
| 3 | 1.2603 m | 3120 | 369 | 1 | 202.3 kPa | 14.58 kPa/m |

- **Repeat 3 caught the failure.** It happened 17.7 s into excavation, with the face at x = 1.2557 m.
  - One particle went invalid: its J was 1.4 × 10¹⁰ before the step and negative after.
  - It was one of the last particles placed, so it started beside the ground face. By then it was 0.35 m back along the shell, at x = 1.03 m, moving at 17 m/s.
  - Its 58 neighbours within 2 voxels stayed valid through the step. Six of them were extreme too, with J down to 0.0007 before the step and 0.00015 after.
  - The guard reset it, and the chamber held. Pressure and gradient match the repeats that needed no reset.
- **The failure path, as far as the guard shows it:** an extreme particle forms in the corner, is carried along the shell, and goes invalid. Without the guard, one such particle most likely lost the whole chamber on 20 Nov; this fits, but is not shown for that run. Here it came once in three repeats.
- **Cost:** none to measure. Frame times here are set by the thermal pauses (686–836 ms per frame, against 719–818 in the trace runs). Peaks were 79–81 °C. The node was shared with another CPU job.
- **Known limit:** the corner particles remain. They carry no measurable error in pressure or gradient (above), but a run is sound only while the reset count stays small. The result reports it.

## The gradient at the stop (21 Nov 2026)

**Check:** at Botlek the vertical gradient is high while excavating and falls when excavation stops or a ring is built, sometimes below 10 kPa/m ([Data](#data-bezuijen-talmon-joustra--grote-2005)).

**Runs:** the eleven runs made with the current reading (full-section rows, every bulkhead contact):
- 0.10 m, nine runs: three seeds, the five trace runs and the three repeats;
- 0.12 m and 0.15 m, one run each.

Each has a 3 s standstill before the 20 s excavation and a 6 s stop after it; records `ch_gd_*`, `ch_gc_*` and `ch_rg_v015_check` in `server/results/`.

| Phase | Gradient (kPa/m), mean ± sd of 11 runs |
|---|---|
| Standstill before excavation | 13.39 ± 0.17 |
| Excavation | 14.64 ± 0.12 |
| Stop after excavation | **14.76 ± 0.18** |

- **The gradient does not fall at the stop.** It stays at the excavation value or above it, by −0.14 to +0.33 kPa/m (+0.12 on average).
  - It has settled: in every run the two halves of the stop agree within 0.1 kPa/m.
  - It sits at the paste's weight at its fill, about 14.4 kPa/m, and inside Botlek's 10–20.
- **Why the model cannot show the fall:** Bezuijen et al. (2005, sections 2 and 3.1) give three causes, and none is in the model:
  - groundwater flows from the chamber into the ground, driven by the excess pore pressure, and is replaced by foam of about 90 % air;
  - foam is injected during ring building;
  - the muck arches more once excavation stops.

  The model's paste is a single undrained material at constant density. It has no pore water, no foam added at a stop, and no change of strength at rest.
- **The model was not tuned to produce the fall.** That would need drainage and foam injection in the scene: a matter for calibration (Phase 3), not WP4. The stop check is met only in part: the level is inside Botlek's range, but the fall is not reproduced.
- **Before excavation the gradient is lower, 13.4 against 14.6.** Something lowers the gradient at that standstill but not at the stop; this is not shown. The paper's adhesion term is a candidate: the muck's shear strength at the steel faces shifts the gradient by up to 2τ/L (about 12 kPa/m at 5 kPa over the 0.8 m chamber). Its sign depends on the direction of flow.
- **Correction to the committed records `ch_rg_v010`–`v015`:** their excavation gradient was recomputed with every contact on 21 Nov. Their hold and stop gradients were not: they still use the reading that left out contacts beyond the shell radius. They are not used here.

## The pressure band at one gauge (21 Nov 2026)

**Check:** how far the bulkhead pressure swings while excavating, against a field gauge. Until now the band was read from the axis pressure, an average over two bands across the section: ±4–10 kPa (5–95 %), a standard deviation of 3–7 kPa in 20 s runs and 2.9–5.5 kPa in 100 s runs. An average over a wide area could narrow the band by itself, so the model is read here on gauge-sized patches.

**Field band, digitised.** Bezuijen et al. (2005), Figs 8 and 9, plot the chamber gauges against time for rings 318 N and 814 S. PC E5 sits low on the bulkhead, beside the screw. Its trace was taken from the vector paths of the paper's PDF and scaled on the plot frame (0–4 bar). While excavating, after the first 3 % of the trace:

| Ring | Median (kPa) | sd (kPa) | 5–95 % (kPa) | sd with the slow drift removed (kPa) | sd at the stop that follows (kPa) |
|---|---|---|---|---|---|
| 318 N (Fig 8) | 334 | 15.2 | 311–360 | 10.2 | 4.1 |
| 814 S (Fig 9) | 306 | 11.6 | 290–329 | 8.3 | 6.8 |

The slow drift is a moving median over a twentieth of the excavation. The statistics are taken over the trace's vertices, so they weight the parts the plot draws in detail; two rings only.

**Model:** a new option, `gauge_log` (off by default), logs every frame the bulkhead pressure on square patches 0.2, 0.4 and 0.8 m wide at three positions, scaled to this radius from Botlek's E1 (top), E3 (axis, to the side) and E5 (low, beside the screw) in Figs 3 and 7. The positions are approximate. Patch edges are snapped to the grid as the bands are ([16 Nov](#the-bulkhead-reading-and-the-gradient-at-four-voxels-16-nov-2026)). Two runs with 60 s of excavation, longer than one controller swing of 40–50 s: 0.10 m and 0.15 m voxels, seed 0; records `ch_gg_v010` and `ch_gg_v015`. Statistics over the excavation after its first 5 s:

| Reading | sd at 0.10 m (kPa) | sd at 0.15 m (kPa) | sd after a 3 s median, 0.10 / 0.15 m (kPa) |
|---|---|---|---|
| Axis band | 5.9 | 7.0 | 1.2 / 1.9 |
| E5, 0.8 m patch | 6.1 | 8.4 | 1.7 / 3.2 |
| E5, 0.4 m patch | 6.5 | 8.8 | 2.0 / 3.2 |
| E5, 0.2 m patch | 8.6 | 12.2 | 3.0 / 8.6 |
| E3, 0.4 m patch | 7.3 | 8.8 | 2.1 / 3.2 |
| E1, 0.4 m patch | 7.7 | 8.7 | 2.1 / 3.0 |

- **The averaging explains little of the narrow band.** On 0.4–0.8 m patches the band is 3–26 % wider than the axis band, and it stays 1.3–2.5 times narrower than at Botlek's PC E5.
- **The 0.2 m patch is mostly numerical noise.** It reads wider, but it widens again as the voxel grows (12.2 kPa at 0.15 m, where the patch spans one or two voxels), so its extra spread comes from the grid, not the paste.
- **Most of the model's band is the controller's slow swing.** With a 3 s median removed, 1.7–3.2 kPa is left at 0.4–0.8 m. The field drift was removed over a much longer window (a twentieth of a ring's excavation, against 3 s here), so those two figures are a rough comparison only.
- **At the stop the model is almost still:** 0.1–0.3 kPa at every patch, against 4–7 kPa at Botlek's PC E5.
- **Likely sources at Botlek that the model does not have:** ground and groundwater changing across the face, foam and water flowing through the chamber, and ring building. The paper's causes for the fall at a stop ([above](#the-gradient-at-the-stop-21-nov-2026)) are among them. None was added, and nothing was tuned.
- **Consistency:** E1, E3 and E5 read 161, 203 and 238 kPa at 0.10 m, about 14.7 kPa/m over their 5.2 m of height, as the gradient reading gives.
- **The levels are not compared.** Botlek's PC E5 read medians of 306 and 334 kPa; this chamber's set point is 200 kPa at the axis.
- **Caveats:** one run per voxel, one seed; 55 s of model excavation against a ring's excavation in the field; approximate gauge positions.
- **Runs:** peaks of 81 °C and 78 °C, each paused by the thermal guard; the node was shared with another project's job. The guard reset no particle in either run.

So the check is met in part: the model's band at a gauge is of the right order but narrower than Botlek's, because the sources of variation at a real face are not in the scene.

## Torque with the face cutting (21 and 22 Nov 2026)

**Check:** the cutterhead torque against the 9.8 MNm installed, with the parts the scene does not have added from the demo's torque model. The scene cuts no ground: the slab in front of the cutterhead is the same paste as the chamber, so the MPM gives the torque to stir the paste only.

**MPM paste torque against voxel.** The seven-voxel series of 20–21 Nov (records `ch_rg_v015` to `ch_rg_v008`) was extended to 0.07 m and 0.06 m (`ch_rg_v007`, `ch_rg_v006`; same set-up, with the step check on, which reset no particle). Mean over the second half of the 20 s excavation:

| Voxel (m) | 0.15 | 0.13 | 0.12 | 0.11 | 0.10 | 0.09 | 0.08 | 0.07 | 0.06 |
|---|---|---|---|---|---|---|---|---|---|
| Particles (M) | 0.13 | 0.20 | 0.25 | 0.32 | 0.43 | 0.60 | 0.85 | 1.27 | 2.04 |
| Paste torque (MNm) | 0.688 | 0.666 | 0.572 | 0.560 | 0.513 | 0.513 | 0.442 | 0.399 | 0.370 |

- **Not converged.** The torque falls with the voxel at every step but one. The fall slows (−9.7 % from 0.08 to 0.07 m, −7.3 % from 0.07 to 0.06 m) but has not stopped.
- **The limit is not pinned.** A straight line through the points gives 0.13–0.15 MNm at zero voxel (all nine points, or the last five). Fits of a power of the voxel have uncertainties larger than their values.
- **It also drifts within a run.** At 0.07 m and 0.06 m the four quarters of the excavation read 0.474 / 0.421 / 0.403 / 0.396 and 0.448 / 0.395 / 0.375 / 0.365 MNm. The second half, used above, still falls 2–3 % between its quarters.
- **Likely cause, not shown:** an undrained paste is close to incompressible, and a coarse grid stiffens such a material, so the force to shear it falls as the grid is refined. The pressure, the gradient (14.9 and 15.5 kPa/m) and the guard were as in the rest of the series.
- **So the MPM paste torque is an upper bound, at most 0.37 MNm,** with the converged value perhaps well below it. It sits below a hand estimate of 0.47–0.59 MNm (cu 5 kPa on the faces of the spokes and arms, plus their bearing with Nc 9–12), which assumes the paste fails on the faces of the tools.

**The parts the scene does not have,** from the demo's torque model (`cutterhead_torque` in [`thrust_torque.py`](../../models/py/tunnelsim_models/thrust_torque.py); the [EPB demo](../../web/epb/main.js) inputs: opening 0.401, cutting tools, 300 kNm for the seals, and the face, back and arms at the paste's 2 kPa shear in conditioned clay ([validation](epb-open-data.md#torque-in-conditioned-ground-paste-shear))), at 200 kPa along the Crossrail drive:

| Part | London Clay | Lambeth Group | Basis |
|---|---|---|---|
| Rim friction | 1.23–1.43 MNm | 2.08–2.36 MNm | μ 0.07, fitted on Changsha ([validation](epb-open-data.md)) |
| Cutting tools | 0.57 MNm | 0.57 MNm | assumed tool forces |
| Seals | 0.30 MNm | 0.30 MNm | assumed |
| Face, back and arms at 2 kPa (the demo) | 0.23 MNm | 0.23 MNm | paste shear |
| Demo total | 2.33–2.53 MNm | 3.17–3.46 MNm | |

- **Total with the MPM's paste in place of the demo's:** 2.2–3.6 MNm, taking the MPM's paste torque from its straight-line limit (0.13 MNm) to its finest run (0.37 MNm). That is 23–37 % of the 9.8 MNm installed. The first look on 21 Nov, with the paste torque at 0.44–0.69 MNm, gave 26–40 %.
- **Against the field:** the Guangzhou–Foshan EPB worked at 3–7 MNm, about 15–35 % of the installed torque of reference machines scaled to its 9.15 m ([validation](epb-open-data.md)). The total here is in that range.
- **The rim decides the total**, not the paste. Rim friction is 50–68 % of it, and the MPM's paste 4–15 %. Halving the paste torque again would move the total by less than 0.2 MNm.
- **The two pastes differ:** the MPM's paste has cu 5 kPa (sourced, [9 Nov](#paste-and-walls-from-open-sources)), and the demo shears its paste at 2 kPa. The demo's 0.23 MNm and the MPM's ≤ 0.37 MNm are of the same order. In the demo's sand and gravel units (HF) the face and back use friction × pressure, and the demo total is 5.4–5.5 MNm (55–56 %); no MPM run covers that ground.
- **Caveats:** one seed per voxel; 20 s excavations; the MPM's cutterhead (6 spokes, 6 arms) is not the demo's (4 arms); the field comparison is to another machine's data.
- **Runs:** the node was shared with another project's jobs. The 0.07 m run needed two tries and the 0.06 m run four; the thermal guard stopped the others at 86–91 °C. Each finished run was paused many times and peaked at 80–81 °C.

So the check is met with a stated limit: the cutterhead total is 23–37 % of installed, inside the field's working range, but the MPM's share of it, the paste torque, is not converged with the voxel.

## Shield friction in the thrust (22 Nov 2026)

**Check:** the plan's thrust balances chamber pressure, face resistance and shield friction. The chamber scene has no ground around the shield, so the MPM gives the face force only, and the shove under thrust sets the net force on the chamber ([13–14 Nov](#shove-under-thrust)). Shield friction, the tail seal and backup drag come from the analytical thrust model (`shield_thrust` in [`thrust_torque.py`](../../models/py/tunnelsim_models/thrust_torque.py): friction 0.17 fitted on Changsha on the normal stress σv′(1 + K0)/2 over the shield; tools 1 MN, tail seal 0.5 MN and backup 0.6 MN assumed, as in the EPB demo).

**Face force:** the MPM's bulkhead force while excavating is 7.86 MN at 0.06 m (`ch_rg_v006`), within 0.5 % of the axis pressure × area (7.82 MN). The model's face term is the same.

**Total along the Crossrail drive** (demo scenario, 12 m shield, 200 kPa):

| Ground at the axis | Total thrust (MN) | Shield friction (MN) | Face share |
|---|---|---|---|
| London Clay | 31–34 | 21–24 | 23–25 % |
| Lambeth Group | 45–50 | 35–40 | 16–18 % |
| Sand and gravel | 37–40 | 27–30 | 20–21 % |

All are below the jacks' maximum of 58.5 MN ([Araque et al. 2014](https://learninglegacy.crossrail.co.uk/documents/crossrail-western-running-tunnels-crossing-of-london-underground-victoria-line-and-bakerloo-line-assets/)). At Guangzhou–Foshan the face carried 38–51 % of the thrust in soft ground ([open data](epb-open-data.md#guangzhoufoshan-bounds-from-the-data)), so the model's shield friction already looks high here.

**Against two open records in London Clay** (details in [EPB open data](epb-open-data.md#london-clay-two-thrust-records-22-nov-2026)):

| Record | Model (MN) | Measured (MN) | Model ÷ measured |
|---|---|---|---|
| Crossrail western running tunnels under Regent Street, axis about 31–36 m, 1.6–1.95 bar | 24.6–32.5 | 17.9 (eastbound mean) | 1.4–1.8 |
| CTRL Dagenham up-line, axis 18.9 m, 200 kPa | 21.3–30.0 | 16 | 1.3–1.9 |
| CTRL Dagenham down-line, 150 kPa | 18.7–27.4 | 18 | 1.0–1.5 |

- **The excess is shield friction.** The face force is pressure × area in both model and field; what is left after it is 1.1–3.5× the measured in the model.
- **The field scatters as much:** the two CTRL lines differ by about 2× in what is left after the face force, in the same ground.
- **Likely causes, not shown:** in stiff clay with an overcut and a tapered shield the ground does not press on the whole shield, and K0 = 1.5 raises the normal stress the model assumes. Changsha, where 0.17 was fitted, is mostly weathered rock and soft soil.
- **Nothing was tuned.** A contact factor or a lower K0 for London Clay would be a fit to two records.
- **For the chamber:** shield friction only offsets the set thrust in the scene, so no chamber result changes. The machine's total would be lower than the model gives, still well below the jacks' maximum.

So the check is met with a stated limit: the thrust is assembled from the MPM's face force and the analytical shield friction, and in London Clay that friction makes the total 1.0–1.9× the two open records.

## Where this leaves WP4

- The chamber scene, the pressure controller, a volume correction and the open validation data are in place. The scene's defaults are:
  - the sourced paste and wall friction 0.3;
  - the balance by region, with its corner regions merged (since 15 Nov 2026);
  - 4 solver steps of 50 iterations per frame (since 15 Nov 2026; before, 1 step of 100);
  - the screw taking paste from the middle of its inlet (since 16 Nov 2026);
  - the shell as one watertight tube mesh (since 19 Nov 2026);
  - the gradient read in rows across the full section (since 20 Nov 2026);
  - a check after every solver step that resets an invalid particle (since 21 Nov 2026; a numerical safeguard, reported in every result).
- **Checked (16–17 Nov 2026):** the screw removes the displaced volume times the paste's fill, within 2 % at four voxels ([17 Nov](#screw-speed-the-controllers-swing-and-the-screw-volume-17-nov-2026)). With these defaults the set point holds through excavation and the stop at 0.15 m, 0.12 m and 0.10 m, in three seeds of three at each voxel ([above](#solver-substeps-and-a-collapse-at-the-screw-inlet-15-and-16-nov-2026)). The vertical force balance closes. The bulkhead contact gradient, read with bands on the grid, is 12.9–15.2 kPa/m at four voxels from 0.15 m to 0.08 m, inside Botlek's 10–20 ([16 Nov](#the-bulkhead-reading-and-the-gradient-at-four-voxels-16-nov-2026)).
- **Checked (19–21 Nov 2026):** with the tube shell and the full-section reading, the gradient in excavation is 14.53 ± 0.18 kPa/m at seven voxels from 0.15 m to 0.08 m, with no trend and repeats within 0.07 kPa/m. The bulkhead and the paste beside it agree in a force balance ([21 Nov](#the-bulkhead-gradient-at-seven-voxels-19-to-21-nov-2026)). This meets the gradient check against Botlek for the excavation phase. At the stop the gradient stays at 14.76 ± 0.18 kPa/m in eleven runs, inside Botlek's range, but it does not fall as Botlek's does: the causes the paper gives, drainage and foam, are not in the model ([21 Nov](#the-gradient-at-the-stop-21-nov-2026)). At a gauge-sized patch near Botlek's PC E5 the pressure band is 6–9 kPa (sd) against 11.6–15.2 kPa in the field: averaging over the axis band explains little, and the sources of a wider band at a real face are not in the scene ([21 Nov](#the-pressure-band-at-one-gauge-21-nov-2026)). With the demo's rim, tools and seals added to the MPM's paste torque, the cutterhead total is 2.2–3.6 MNm, 23–37 % of installed, inside the 15–35 % worked at Guangzhou–Foshan; the paste torque itself falls with the voxel and is not converged ([22 Nov](#torque-with-the-face-cutting-21-and-22-nov-2026)). The MPM's face force is pressure × area within 0.5 %; with the analytical shield friction, tail seal and backup added, the thrust in London Clay is 1.0–1.9× two open records, the excess in the shield friction ([22 Nov](#shield-friction-in-the-thrust-22-nov-2026)).
- **WP4 outputs produced:** bulkhead pressure in bands, its gradient, mixing torque, the response to a screw-speed step, and a shove under thrust.
- **Gradient (15 Nov 2026):** multiplied by the fill, the paste's stress gradient in the interior is about 15 kPa/m during excavation at both 0.15 m and 0.12 m; the paste there is about a tenth denser than nominal.
- **Not done:**
  - the 0.10 m gradient over 100 s, about 2 kPa/m below 0.15 m and 0.12 m when settled (13.05 against 15.1 and 15.6 kPa/m over the last 50 s), from runs before the tube shell and the row reading; not rerun. Also its undamped controller swing;
  - controller gains from a source (assumed now; a 20 s excavation does not settle);
  - why the bands read 0.12 m high (the screw strip's edge is likely, not shown);
  - why extreme particles form in the corner of the ground face and the shell. The sudden loss they cause (once on 20 Nov) is stopped by the guard since 21 Nov;
  - the 0.15 m results recorded before 16 Nov ran 11–13 % above the set point (the step and thrust runs are repeated, 17 Nov);
  - the screw step at 8–14 % above the net-flow prediction in 90 s runs (within 4 % in 20 s runs);
  - deleting paste that escapes the chamber;
  - the fall of the gradient at a stop: the level is inside Botlek's range, but the fall needs drainage and foam, which the model does not have ([21 Nov](#the-gradient-at-the-stop-21-nov-2026));
  - the sources of a wider band (ground, water and foam at the face, ring building): at a gauge the band is 1.3–2.5 times narrower than Botlek's ([21 Nov](#the-pressure-band-at-one-gauge-21-nov-2026));
  - a converged paste torque: it falls from 0.69 MNm at 0.15 m to 0.37 MNm at 0.06 m and has not levelled off ([22 Nov](#torque-with-the-face-cutting-21-and-22-nov-2026));
  - shield friction in stiff clay: the analytical model is 1.0–1.9× two open London Clay records, not fitted ([22 Nov](#shield-friction-in-the-thrust-22-nov-2026));
  - the stray particles still sealed, a field record for the screw step.
- Nothing from the MPM chamber is used on the console yet.
