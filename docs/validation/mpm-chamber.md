# MPM EPB chamber under pressure (Phase 2, WP4): first runs, blocked

- **Plan:** [Phase 2, WP4](../plans/phase2-mpm-face-chamber.md#wp4-epb-chamber-with-a-pressure-controlled-shove-about-3-weeks).
- **Code:** [`server/tunnelsim_server/scenes/chamber.py`](../../server/tunnelsim_server/scenes/chamber.py). Runs with `python -m tunnelsim_server.runner chamber ...`; records `ch_*` in [`server/results/`](../../server/results/). `ChamberConfig.seal_shell` (default off) is a diagnosis option: paste pushed into the shell wall is put back inside each frame.
- **Status:** **uncalibrated, blocked.** The paste loses its pressure while the cutterhead shears it, under every solver setting tried: GIMP integration slows the loss but does not stop it ([20 s runs, 7 Nov 2026](#gimp-and-the-20-s-excavation-7-nov-2026)). The alternative element (P1d) holds the pressure, but it locks and gives the wrong vertical gradient. This is the same limitation that blocked the clay ([mpm-clay](mpm-clay.md#the-piling-investigated-5-nov-2026)).
  - **Correction (7 Nov 2026):** from 6 Nov the docs, the v1.0.0 release notes and our comment on [newton-physics/newton#5180](https://github.com/newton-physics/newton/issues/5180) said that under GIMP the chamber keeps 162 of 207 kPa (172 of 216 before the scaling fix), "a fifth lost". Those runs excavated for 4 s only. Over the scene's 20 s excavation the pressure falls to 51 kPa.
- **Run on:** 5 Nov 2026; GIMP and 20 s diagnosis runs 7 Nov 2026

## Set-up

**Machine:** the Crossrail EPB, D 7.08 m with 9.8 MNm installed torque. The chamber is 0.8 m long, with 0.6 m of ground in front of the cutterhead. The cutterhead has 6 spokes and 6 mixing arms and turns at 2 rpm.

**Advance:** a ground piston pushes the ground in at 60 mm/min.

**Paste:**

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

## Where this leaves WP4

- The chamber scene, the pressure controller and the open validation data are in place.
- **Blocked:** the yielding paste loses its pressure under the turning cutterhead with every solver setting in Newton 1.7.0. Reported on [newton-physics/newton#5180](https://github.com/newton-physics/newton/issues/5180).
- **Also to fix:** about 2 % of the paste pushes into the shell wall in 20 s.
- Nothing from the MPM chamber is used on the console.

**If Newton offers no route, the fall-backs are:**
1. keep the chamber analytical, as it is now;
2. use the MPM only for things that do not depend on the chamber pressure, such as the mixing pattern and torque trends, clearly labelled.
