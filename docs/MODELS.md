# Model catalogue

Every model exists twice: a Python reference in [`models/py/tunnelsim_models/`](../models/py/tunnelsim_models) and a JavaScript twin in [`models/js/`](../models/js) for the browser. Both are checked against the shared vectors in [`models/test-vectors/`](../models/test-vectors). The Python tests also check hand-calculated anchor values. Each source file starts with its references, equations and units.

## Overview

| Model | Python | JavaScript | Status |
|---|---|---|---|
| [CSM disc cutter](#csm-disc-cutter) | `csm.py` | `csm.js` | Reproduces the Follo TBM1 mean penetration (6.36 against 6.32 mm/rev) with ψ = −0.1 |
| [Hoek–Brown rock mass](#hoekbrown-rock-mass) | `hoek_brown.py` | `hoek_brown.js` | Hand-checked |
| [Settlement and building damage](#settlement-and-building-damage) | `settlement.py` | `settlement.js` | Hand-checked; checked privately against published case histories |
| [Face support pressure](#face-support-pressure) | `face_support.py` | `face_support.js` | Hand-checked; seepage not yet modelled |
| [EPB chamber and screw conveyor](#epb-chamber-and-screw-conveyor) | `epb_chamber.py` | `epb_chamber.js` | Hand-checked; screw pressure profile calibrated on the Botlek screw gauges ([validation](validation/epb-screw-botlek.md)) |
| [Slurry shield (Mixshield)](#slurry-shield-mixshield) | `slurry.py` | `slurry.js` | Reproduces the DAUB worked example; air cushion is this project's derivation |
| [Thrust and torque](#thrust-and-torque) | `thrust_torque.py` | `thrust_torque.js` | Shield and rim friction fitted on open field data; thrust within about ±25 % on three EPB projects, torque high in conditioned clays ([validation](validation/epb-open-data.md)) |
| [Hard-rock drive](#hard-rock-drive) | `hard_rock.py` | `hard_rock.js` | Reproduces Farrokh's worked example within 3 %; support curve digitised |
| [Ground response and squeezing](#ground-response-and-squeezing) | `ground_response.py` | `ground_response.js` | Reproduces Hoek's and Hoek & Marinos's worked examples; consistent with measured convergence in an Albanian flysch tunnel ([validation](validation/sem-convergence.md)); shield friction a screening estimate |
| [SEM / NATM sprayed concrete lining](#sem--natm-sprayed-concrete-lining) | `sem.py` | `sem.js` | Checked against Brenner shotcrete data and Oreste's trends; Sulem parameters from one site |
| [Ground scenarios](#ground-scenarios) | `scenario.py` | `scenario.js` | Interpolation, water systems and river unit-tested; two scenarios from open BGS boreholes ([format and sources](SCENARIOS.md)) |
| [Segment lining](#segment-lining) | `lining.py` | `lining.js` | Reproduces ITA WG2 (2000) Design Example 1 and its jacking check |
| [Drill & blast](#drill--blast) | `drill_blast.py` | `drill_blast.js` | Reproduces Yilmaz's worked example, SS 460 48 66 tables and NFF cycle figures; Norwegian pattern fitted to published hole counts; cycle checked against logged Ulvin rounds and a T10.5 contractor estimate |
| [Utilisation and downtime](#utilisation-and-downtime) | `utilisation.py` | `utilisation.js` | Deterministic limits hand-checked; default EPB inside a 40-EPB survey; one-project distributions |

Also: [machine class presets](#machine-class-presets) and [where default parameters come from](#default-parameter-sources).

---

## CSM disc cutter

Disc-cutter forces, penetration from thrust, rate of penetration, cutterhead torque (T ≈ 0.3·D·N·F_r), power and the torque limit.

- **References:** Rostami & Ozdemir (1993), RETC proceedings, not openly published; Rostami (1997), [PhD thesis, Colorado School of Mines](https://repository.mines.edu/entities/publication/139ea21b-d9e0-4c87-ab35-7f312216fde9).
- **Validated against:**
  - a hand calculation for a 19″ disc (p = 5 mm, UCS 150 MPa, BTS 10 MPa, ψ 0.1 → F_t ≈ 201 kN, RC ≈ 0.10);
  - Follo Line TBM1, the 4.5 km weighted mean (Hansen 2018, NTNU, [hdl:11250/2503069](https://hdl.handle.net/11250/2503069)): 71 discs, net thrust 18,017 kN, 5.08 rpm, UCS 152 MPa, BTS 10.4 MPa. Measured 6.32 mm/rev. With the spacing as radius / number of discs, ψ = −0.1 gives 6.36 mm/rev; the earlier ψ = 0.1 gave 11.8 mm/rev. ψ = −0.1 is now the default, inside Rostami's −0.2 to +0.2 ([validation](validation/hard-rock-projects.md)).
- **Drive and speed limits:**
  - Available torque is the installed torque up to the speed where it meets the installed power, then power / angular speed. The two Niagara torque points (18,800 kNm at 2.4 rpm, 9,025 kNm at 5 rpm) both give 4,725 kW.
  - Speed limit from the gauge-cutter linear speed: rpm = V_L / (π D), with V_L = 165 m/min for 17″ and 200 m/min for 19″ discs (Rostami & Chang 2017, [doi:10.1016/j.eng.2017.12.009](https://doi.org/10.1016/j.eng.2017.12.009)).
  - Optional penetration cap. The practical maximum is 15 mm/rev, the lower end of the 15–20 mm/rev "brief maximum before the conveyor overloads" (Macias & Barton 2022).
  - The limit that binds is reported (thrust, penetration, torque or power), together with the thrust actually carried by the cutters.
- **Section by section** (18 Follo sections, digitised from the thesis's vector charts): with each section's single-test UCS the prediction is 0.41–2.89× the measurement, and the error follows UCS (r = −0.94). With the tunnel-mean UCS and each section's thrust and rpm, it is within about ±27 % (RMS of ln ratio 0.24). Fitted on section averages, ψ would be about −0.15.
- **Second project, not refitted:** Queens Water Tunnel No. 3, 10 stations from Yagiz (2006, [IAEG paper 383](https://media.geolsoc.org.uk/iaeg2006/PAPERS/IAEG_383.PDF)), machine from Khalighi & Diehl (1997). Median 1.02× (0.71–1.82×). Massive rock comes out fast (median 1.51×), fractured rock slightly slow (0.91×): the model has no fracture term.
- **Calc-schist, Brenner (not refitted):** three double shields logged by Maggio (2020). Penetration is reproduced at UCS 53–85 MPa, inside the published 30–120 MPa, so it is consistent but not tested. Torque from T ≈ 0.3·D·N·F_r is 1.5–2.4× the logged torque on all three machines, independent of UCS ([validation](validation/hard-rock-projects.md#penetration-and-torque-on-the-brenner-double-shields)).
- **Torque on a second project:** an open-mode EPB in Tehran limestone (Samadi & Hassanpour 2024) logged 0.56–0.80 of the model torque. Not changed: the radius factor and the rolling force cannot be separated, and halving the torque moves advance in one demo zone only ([validation](validation/hard-rock-projects.md#cutterhead-torque-on-a-second-project)).
- **Limits:** two projects, both in strong gneiss. The Yinsong dataset, planned for other rock types, is not open (data on request only).

## Hoek–Brown rock mass

Generalised Hoek–Brown constants (m_b, s, a), global rock-mass strength σ_cm and rock-mass modulus.

- **References:** Hoek, Carranza-Torres & Corkum (2002), [authors' pre-print](https://www.d.umn.edu/~carranza/HB02/); Hoek & Diederichs (2006), [doi:10.1016/j.ijrmms.2005.06.005](https://doi.org/10.1016/j.ijrmms.2005.06.005).
- **Validated against:** a hand calculation (GSI 50, m_i 10); the intact limit (GSI 100 gives s = 1).

## Settlement and building damage

What it computes:

- the Gaussian transverse trough, symmetric or asymmetric, with horizontal displacement;
- the longitudinal profile, built from face, shield, tail-void and behind-the-tail volume-loss components, with an optional longitudinal width;
- excavation-method presets (volume loss and K);
- twin tunnels: the second bore's trough at its own volume loss, with separate widths towards and away from the first bore;
- volume loss from the face's load factor in overconsolidated clay (Macklin 1999): LF = N / N_TC, N = (σv − σT)/S_u, VL = 0.23 % × e^(4.4 LF), with N_TC from Kimura & Mair (1981) for a face supported up to the cutterhead (7.05 at C/D 1.5 to 9.0 at C/D ≥ 3);
- the deflection ratio Δ/L of a footprint in sagging and hogging, and its modification by the building's bending stiffness: M_DR against ρ* = EI / (E_s H⁴), H = B/2, and e/B (Potts & Addenbrooke 1997, digitised from [Mair 1997](https://www.issmge.org/uploads/publications/1/31/1997_04_0052.pdf) Fig. 4 to about ±0.03), with an assumed EI from floor slabs;
- the building's tensile strain by the second-stage assessment of Mair, Taylor & Burland (1996): the footprint follows the greenfield trough, is split at the points of inflection into hogging and sagging spans and limited to 2.5 i; each span's Δ/L gives the bending and diagonal strain of a deep beam (Burland & Wroth 1974; E/G 2.6 for masonry), combined with the span's average tensile horizontal strain (their Eqs 7–10);
- Burland damage categories from that strain.

**References:**

- Peck (1969); O'Reilly & New (1982); Attewell & Woodman (1982);
- Mair & Taylor (1997);
- Addenbrooke & Potts (2001), [doi:10.1061/(ASCE)1532-3641(2001)1:2(249)](https://doi.org/10.1061/(ASCE)1532-3641(2001)1:2(249));
- Wan, Standing, Potts & Burland (2017), [doi:10.1680/jgeot.16.P.099](https://doi.org/10.1680/jgeot.16.P.099) (second bore at Hyde Park);
- Burland (1995);
- Mair, Taylor & Burland (1996), IS-London, [ISSMGE library](https://www.issmge.org/uploads/publications/6/8/1996_118.pdf) (second-stage building strain, Eqs 7–10, Table 2, Fig. 4);
- Macklin (1999), *Ground Engineering* 32(4), not open; the relation as quoted in [Divall et al. 2023](https://openaccess.city.ac.uk/id/eprint/31563/), Eq. (4)–(6), accepted version open;
- Mair (1997), theme lecture, [ISSMGE library](https://www.issmge.org/uploads/publications/1/31/1997_04_0052.pdf) (Potts & Addenbrooke's deflection-ratio factors, Fig. 4);
- Potts & Addenbrooke (1996), IS-London, [ISSMGE library](https://www.issmge.org/uploads/publications/6/8/1996_093.pdf) (horizontal-strain factors against α* = EA / (E_s H), Fig. 5);
- Kimura & Mair (1981), [ISSMGE library](https://www.issmge.org/uploads/publications/1/35/1981_01_0061.pdf), digitised in [mpm-clay](validation/mpm-clay.md).

**Validated against:**

- a hand calculation: D 6 m, z₀ 20 m, VL 1 % → S_max 11.3 mm;
- measured Crossrail settlement ([validation](validation/settlement.md)):
  - Hyde Park reproduced (8.1 mm against 8.3 mm).
  - In the Thames chalk, the published per-bore volume losses reproduce the 17 measured Smax values (median ratio 1.10). This reads the "WB & EB" column as the second bore's own VL; read as both bores together, they were 1.6× low. The first-bore VL that fits has a median of 0.25 % with K 0.5, or 0.20 % with K 0.4. The demo uses K 0.4, the trough width of three chalk sources not used for the fit, and so 0.20 %.
- the second bore: Hyde Park gives 1.5–1.9× the first bore's volume loss, Ky 0.44 towards the first bore and 0.33 away, 16.2 m apart; the Thames table gives a ratio of 1.2 at a median of 17 m. These are the scenario defaults;
- numerical integration equals V_s, also for asymmetric troughs;
- one component at the face gives half the final settlement at the face; a tail-only component gives Φ(−L/i);
- the closed-face preset leaves 0.1–0.2 of the final trough at the face; a narrower longitudinal width lowers it without changing the final trough;
- twin-tunnel defaults equal plain superposition;
- also checked privately against published UK case histories (licensed material, not in this repository);
- the load-factor relation: at the EPB demo's normal 2.2 bar in London Clay (axis about 31 m, S_u from the Crossrail Paddington design profile 85 + 5z kPa), LF ≈ 0.18 gives 0.51 %, the measured Hyde Park value (0.44–0.78 %) the demo already uses. This is a consistency check, not an independent test: no open data pair face pressure with volume loss on one drive.

**Limits of the face volume loss:**

- Macklin's relation is fitted on overconsolidated clay with C/D mostly above 1, and on LF ≥ 0.2; in the demo it is applied only where London Clay is at the axis;
- the volume loss used is the larger of the measured value and Macklin's, so it rises when support drops but never falls below what was measured;
- S_u is the Paddington design profile carried along the line; N_TC comes from two digitised centrifuge points;
- grout filling and tail-void loss are not modelled separately; they remain in the measured value.

**Limits of the building stiffness:**

- the deflection ratio and the horizontal strain are both modified and shown beside the greenfield values. The horizontal-strain factors come from Potts & Addenbrooke (1996) Fig. 5, digitised to about ±0.003. They are upper-bound design curves, at most about 0.11 of greenfield, stated valid for α* > 0.5;
- the damage category uses the greenfield second-stage strain (Mair, Taylor & Burland 1996), as that method intends: conservative, because the building is assumed to follow the greenfield trough. The stiffness-modified values are shown only, because the slab stiffness is assumed. With the assumed slabs, α* is about 2–22 for the buildings checked, so the horizontal strain with stiffness is at most a few per cent of greenfield;
- the building strain checks: Fig. 4 of Mair, Taylor & Burland is reproduced (L/H = 1, hogging: the category 2/3 boundary at Δ/L 0.16 % with no horizontal strain); with no bending the strain equals the horizontal strain;
- E/G is 2.6 (masonry) for every building; framed buildings (12.5) would give less strain. Horizontal compression is not allowed to reduce the strain;
- the chart is digitised from a scan (about ±0.03); between the plotted e/B curves the factor is interpolated, and e/B above 0.6 uses the 0.6 curve;
- EI and EA are assumed estimates: floor slabs (0.15 m, E 23 GPa, every 3.4 m, storeys from the LIDAR height) acting together, bending about mid-height. Real frames act less than fully together, and masonry on strip footings is far less stiff axially, so this is an upper estimate of stiffness and of the reduction;
- no field data check: no open source gives a building's measured deflection ratio with its stiffness on these drives.

## Face support pressure

Wedge-silo limit equilibrium for closed-face shields, the Vermeer cohesionless limit, and the DAUB operating window.

- **Mechanism:** a Horn wedge loaded by a Janssen silo. The silo is layered above and below the water table; water is hydrostatic. The circular face is replaced by a square of equal area.
- **Operating window (DAUB 2016, chapter 3):**
  - p_min = 1.5 × earth + 1.05 × water at the axis;
  - p_max = 0.9 × the total vertical stress at the crown, with the minimum unit weights and no surface load;
  - the set point must stay inside the window by the machine's pressure deviation: ±30 kPa for an EPB, ±10 kPa for a slurry shield.
- **Seepage:** DAUB applies seepage forces only when the support pressure is set below the groundwater pressure (EPB open or transition mode, after Anagnostou & Kovári 1996, [doi:10.1016/0886-7798(96)00017-X](https://doi.org/10.1016/0886-7798(96)00017-X)). With the 1.05 factor on the water pressure they don't arise in closed mode, so they aren't modelled.

**References:**

- Horn (1961); Janssen (1895);
- Anagnostou & Kovári (1994), [doi:10.1016/0886-7798(94)90028-0](https://doi.org/10.1016/0886-7798(94)90028-0);
- Vermeer, Ruse & Marcher (2002);
- DAUB (2016), *Recommendations for Face Support Pressure Calculations for Shield Tunnelling in Soft Ground*, version 10/2016, [free PDF](https://www.daub-ita.de/fileadmin/documents/daub/gtcrec1/2016-10_DAUB_Recommendations_for_Face_Support_Pressure_Calculations_for_Shield_Tunnelling_in_Soft_Ground.pdf).

**Validated against:**

- silo limits: deep → (rγ − c)/(K tan φ); φ = 0 → overburden;
- dry sand within 1.0–1.3 × Vermeer for φ 25–40°, as expected for limit equilibrium;
- nearly cover-independent; stiff undrained clay is self-supporting;
- the window closes at very shallow cover under water;
- the Phase 0 MPM face benchmark reached 0.79 of Vermeer at D/20 ([results](../phase0/RESULTS.md));
- DAUB (2016) example 8.1, slurry shield in sand, run with DAUB's options (no silo, side friction (K0 + Ka)/2, square face of side D):
  - critical angle 66.56° (DAUB 66.56°);
  - earth force 4,120.7 kN against DAUB's 4,122.3 kN;
  - minimum crown pressure 190.8 kPa, maximum 229.5 kPa and operating range 200.8–219.5 kPa, all as published (a test vector in Python and JavaScript).

**Limits:**

- seepage forces are not modelled: they only arise with the support below the groundwater pressure (EPB open or transition mode);
- the demos use the average unit weight for the maximum too, because the scenarios carry no minimum values. DAUB uses the minimum, which lowers the maximum slightly;
- the defaults (silo K 0.8, side friction 1 − sin φ′, equal-area square) differ from DAUB's example options; both are available.

## EPB chamber and screw conveyor

What it computes:

- the support pressure from a volume balance of soil, foam liquid and foam air (Boyle's law, exact integration per step);
- the foam split from FIR and FER;
- the steady screw flow for a target pressure;
- chamber stiffness;
- screw capacity and efficiency, with a drop at the screw entrance and an exponential pressure drop along the screw.

**References:**

- EFNARC (2005) for FIR and FER, [free download](https://efnarc.org/publications) after a short form;
- Merritt & Mair (2006, [doi:10.1680/geot.2006.56.9.605](https://doi.org/10.1680/geot.2006.56.9.605); 2008, [doi:10.1680/geot.2008.58.2.79](https://doi.org/10.1680/geot.2008.58.2.79)), simplified;
- Yeh (1997), [doi:10.1016/S0926-5805(96)00165-3](https://doi.org/10.1016/S0926-5805(96)00165-3).

**Validated against:**

- the Boyle limit with air only;
- p = K·ε without air;
- stiffness (K − p)²/(K·V) unconditioned, and ≈ (p + p_atm)/V_air with foam;
- the solution converges to the steady state independent of step size;
- stopping the screw raises the pressure; an over-fast screw empties the chamber.

**Limits:**

- screw efficiency is an illustrative default. The entrance factor (0.85) and decay length (16 m) are calibrated between two Botlek rings (Bezuijen et al. 2005; 0.73–1.54× at every gauge) and not tested on another machine ([validation](validation/epb-screw-botlek.md)). The old 3 m left 1.4–25× too little pressure along the screw (12–25× at 11.5 m);
- the slurry branch is a separate model: [slurry shield](#slurry-shield-mixshield).

## Slurry shield (Mixshield)

What it computes:

- the stagnation gradient f_s0 = 3.5 τ_f / d₁₀ and whether a filter cake (membrane) forms, at f_s0 ≥ 200 kN/m³ (DIN 4126);
- the slurry penetration e_max = Δp d₁₀ / (α τ_f), with α = 3.5 by default (2–4 in the literature), and its growth in time e(t) = e_max t / (a + t) (Krause 1987, not openly published, as given by Broere & van Tol 2000);
- the share of the support force transferred to the sliding wedge, approximated as 1 − e / L over the wedge length L;
- the excess pore pressure ahead of the face, Δp(x) = Δp_p exp(−x / λ), λ = √(k H c);
- the air cushion: the working-chamber level from feed, excavated and discharge flows; the air compressed or expanded isothermally (Boyle); a first-order regulator that adds or vents air towards the setpoint;
- the support pressure at any height from the air pressure and the slurry column;
- the slurry circuit: discharge flow and density, dry solids measured from the feed and discharge flows and densities against the theoretical dry solids, pipe velocity and the Durand limit deposit velocity;
- the control tolerances: ±10 kPa with an air cushion, ±30 kPa for EPB.

**References:**

- [DAUB / ITA-AITES (2016)](https://www.daub-ita.de/fileadmin/documents/daub/gtcrec1/2016-10_DAUB_Recommendations_for_Face_Support_Pressure_Calculations_for_Shield_Tunnelling_in_Soft_Ground.pdf), recommendations for face support pressure calculations: eqs (1)–(2), section 7.1 tolerances, section 8.1 worked example;
- [Broere & van Tol (2000)](https://repository.tudelft.nl/file/File_9dc608e8-3df5-4344-8d2a-b6e420392119), infiltration and groundwater flow at the face: eqs (8)–(13);
- [Shomee et al. (2022)](https://penerbit.uthm.edu.my/periodicals/index.php/peat/article/download/7927/3148/55023), dry-mass balance;
- [Miedema, Slurry Transport, 6.27](https://eng.libretexts.org/Bookshelves/Civil_Engineering/Slurry_Transport_(Miedema)/06%3A_Slurry_Transport_a_Historical_Overview/6.27%3A_The_Limit_Deposit_Velocity_(LDV)), Durand limit deposit velocity;
- [Herrenknecht Mixshield](https://herrenknecht.com/en/products/productdetail/mixshield): DN300 lines at 1000 m³/h.

**Validated against:**

- the DAUB section 8.1 example: e_max 0.464, 0.541 and 0.617 m, within 0.002 m;
- a circuit hand calculation: 994.5 m³/h discharge at 1.14 t/m³ carrying 57.3 m³/h of dry solids;
- Durand: 4.18 m/s in DN300 with F_L 1.34; 1000 m³/h in DN300 is 3.93 m/s;
- the air cushion: a flow surplus raises the level and, briefly, the air pressure, which the regulator returns to the setpoint; balanced flows keep the state.

**Limits:**

- the air-cushion dynamics are this project's own derivation: no open source with the equations was found;
- the support transfer 1 − e / L approximates DAUB's reduction of the wedge (AA/BB);
- the deposit velocity uses a single coefficient for the whole grading; fines, clay and the separation plant are not modelled.

## Thrust and torque

Shield thrust:

- face (chamber) pressure;
- shield skin friction;
- tools;
- tail seal;
- backup drag.

Cutterhead torque:

- tools;
- front face;
- rim;
- back face;
- mixing arms;
- seals.

The ground stress on the shield is effective or total vertical stress, with a water table. Results are compared with built machines of the same type, scaled by D³ for torque and D² for thrust.

**References:**

- Shi, Yang, Gong & Wang (2011), [doi:10.1016/j.autcon.2011.04.010](https://doi.org/10.1016/j.autcon.2011.04.010);
- built machines with sources in `REFERENCE_MACHINES`: Crossrail EPB and Mixshield, and a 6.6 m mixed-face EPB. The gripper entries are not yet verified.

**Validated against:**

- a hand calculation of every component;
- a 7 m EPB example: thrust 20 MN and torque 5.9 MNm, both below what built 7 m EPBs carry (≈ 50 MN, 8.4–9.5 MNm scaled);
- torque rises with pressure and falls with opening ratio; face terms scale with R³.

**Limits:**

- face and chamber friction coefficients are illustrative; shield and rim are effective values fitted on open data;
- the Krause α·D³ band was dropped because modern EPBs exceed it.

**Against open field data** ([validation](validation/epb-open-data.md)): the old defaults (shield and rim friction 0.3) gave 1.43× the measured thrust and 1.70× the measured torque on 281 Changsha Metro Line 4 rings. The defaults are now effective values fitted there: shield 0.17, rim 0.07.

Checked on two other projects:

- **Mashhad Line 3:** at 1.3 bar, thrust comes out at 0.89× and torque at 1.06× the measured values.
- **Sofia Line 3, 14 means:** thrust 1.02× with groundwater, 1.28× dry. Torque with friction alone is 2.7× over in foam-conditioned clays and sands; with the face, back and arm shear capped at the paste's shear strength (`tau_paste` 2 kPa, [Bezuijen et al. 2005](https://www.issmge.org/uploads/publications/6/11/2005_023.pdf), not fitted) it is 0.98–1.14×. Paste shear is used only in fine-grained conditioned ground; Changsha and Mashhad keep friction (this split is the project's reading of the data).
- **Low face pressure in dense, dry ground:** about 2× over.
- **Ring-to-ring scatter:** not reproduced.

## Hard-rock drive

Cutter wear and changes, rock support by class, and utilisation as downtime per kilometre for open, single- and double-shield TBMs.

- **Cutter wear:**
  - cutter life CL = 1026 / CAI m³ per cutter (Frenzel 2011, via Zhang et al. 2025, [doi:10.1007/s40789-025-00787-0](https://doi.org/10.1007/s40789-025-00787-0));
  - cutters consumed per km = excavated volume / CL;
  - 66 min per change (Farrokh 2013, SME OneMine, not openly published);
  - Farrokh's fits of cutter downtime by quartz content as a cross-check.
- **Support:**
  - Bieniawski (1989) RMR classes with their bolts, shotcrete and ribs;
  - RMR from GSI (GSI = RMR89′ − 5);
  - support downtime per km by RMR, diameter and machine type, digitised from Farrokh (2018) Fig. 12 (about ±20 h/km);
  - a double shield below RMR 50 is assumed to fall back to single-shield mode.
- **Utilisation:** Farrokh (2018), [doi:10.22044/jme.2018.6815.1509](https://doi.org/10.22044/jme.2018.6815.1509), with downtime terms in h/km:
  - boring, 1000 / PR;
  - regrip, 1000 t_r / (60 L_s) plus a curve term; double shields also stop for each regrip (a few minutes to 15–30 min, Herrenknecht; Maggio 2020);
  - TBM breakdown (fits by rock strength) and backup (fits for rail or conveyor);
  - cutters and support;
  - maintenance and transport classes;
  - utilities, survey and other.

  U = T_boring / ΣT, and the advance rate is 24000 / ΣT m/day.

**Validated against:**

- Farrokh's worked example (open TBM, 3.9 m, PR 4.7 m/h): 1,036 against 1,021 h/km, U 20.5 % against 21 %, 23.2 against 23.5 m/day;
- the wear model gives 25.6 h/km against Farrokh's 30 h/km for low-quartz rock at CAI 2;
- Follo Line (9.96 m double shield): with the measured 1.92 m/h and Follo's 442 cutter changes per km, the model gives 12.9–14.9 m/day and 28–32 % utilisation, against the measured 14.1 m/day average and an implied 31 % ([validation](validation/hard-rock-projects.md)).

**Limits:**

- the support curve is digitised from a figure;
- the CAI wear model excludes chipping and bearing failures, so it is a lower bound;
- the NTNU cutter-life model (CLI) is not implemented, because its charts are not available in closed form;
- there are no per-bolt or per-ring-beam installation times (no open source found).

## Ground response and squeezing

Convergence–confinement around a circular tunnel, squeezing classes, and two machine checks for hard-rock TBMs.

- **Rock mass:** equivalent Mohr–Coulomb φ′ and c′ from Hoek–Brown, for the stress range of a deep tunnel (σ′3max). Source: Hoek, Carranza-Torres & Corkum 2002, eqs 12–18 ([authors' pre-print](https://www.d.umn.edu/~carranza/HB02/)).
- **Ground reaction curve:** closure and plastic radius against support pressure, for an elastic–perfectly plastic Mohr–Coulomb rock mass (Duncan Fama 1993, as given in Hoek, *Practical Rock Engineering*, "Tunnels in weak rock", eqs 1–7). Includes the inverse, the pressure needed to hold a given closure. For undrained clay (φ = 0) it uses the Tresca limit of the same solution: p_cr = p0 − c and R_p = r0·exp((p0 − c − p_i)/2c).
- **Longitudinal displacement profile:** closure ahead of and behind the face (Vlachopoulos & Diederichs 2009, [doi:10.1007/s00603-009-0176-4](https://doi.org/10.1007/s00603-009-0176-4)).
- **Squeezing:** strain and classes A–E (Hoek & Marinos 2000).
- **Support curves and equilibrium:**
  - closed shotcrete or concrete ring, from thick-walled cylinder elasticity;
  - full steel sets (unblocked) and mechanically anchored bolts, after Carranza-Torres & Fairhurst 2000 ([doi:10.1016/S0886-7798(00)00046-8](https://doi.org/10.1016/S0886-7798(00)00046-8)), as given by Dang et al. 2022;
  - combined supports, and the equilibrium point with the ground reaction curve.
- **Shield friction (screening estimate):** F_f = μ·2πR·∫p dy (Ramoni & Anagnostou 2010, [doi:10.1016/j.tust.2010.02.008](https://doi.org/10.1016/j.tust.2010.02.008)). The rock contacts the shield where its closure since the face exceeds the overcut, and then presses with the pressure that holds it at the gap. Friction coefficients come from their Table 2.3 for rock.
- **Gripper bearing:** total gripper force 2.0–3.5 × installed thrust (VSS 1341), spread over the shoe area. Comparing that pressure with the rock-mass strength is our own simple check.

**Validated against:**

- Hoek's worked example (φ 24.72°, c 0.22 MPa, E 750 MPa, r0 3 m, p0 2 MPa): p_cr 0.96 MPa, r_p 6.47 m against 6.43 m, u 30.9 mm against 30.6 mm;
- the Hoek & Marinos example: 1.33 %, class B;
- the equivalent Mohr–Coulomb parameters, checked by hand;
- the LDP limits and the continuity of the ground reaction curve at p_cr.
- the Tresca branch against the general formula at φ = 10⁻⁴ (p_cr = p0 − c, R_p = r0·e^((p0 − c)/2c) for p_i = 0).
- Shield friction against Ramoni & Anagnostou's worked example (D 10 m, σ0 10 MPa): normalised thrust 0.23 / 0.04 / 0 against 0.26 / 0.08 / 0 for overcuts of 5 / 10 / 15 cm.

**Against field data** ([validation](validation/sem-convergence.md)): 14 monitored sections of a headrace tunnel in weak flysch, Albania (Terron-Almenara & Panthi 2025, CC BY 4.0).

- **Farringdon platform tunnels** ([validation](validation/sem-convergence.md#farringdon-platform-tunnels-undrained-ground-london-clays)): with Crossrail's undrained design lines and the ring closed 7.5 m behind the face, the predicted crown settlement is 10.4–13.7 mm, against 10.3–16.5 mm measured outside compensation grouting (mean 13.6 mm) and 10 mm from Crossrail's design FE. The ring movement alone (5–10 mm) read 1.3–2.7× low; the crown factor and the whole-ring settlement below close most of that.
- **Crown settlement in undrained clay** (`sem.crown_settlement`): the axisymmetric ring movement times the Kirsch crown factor 1 + (1 − K)(3 − 4ν)/(1 + K), with K the total-stress ratio (Brady & Brown 2006), plus 2–3 mm settlement of the ring as a whole, measured in the Crossrail Whitechapel enlargements (Stärk et al.). For ν → 0.5 the crown follows σv whatever K is.

- Unsupported, the chain gives a median 1.77× the measured convergence after the station.
- Every reading is reproduced with 1–51 % of the installed support capacity (median 11–19 %).
- The result is consistent, but it cannot separate rock stiffness from mobilised support.

**Limits:**

- **Shield friction** can under-predict by up to about 2×, ignores creep and standstill time, and is not a design method.
- **Ground reaction curve:** the closed form has no dilation, so it is severe for very weak rock. In the demo fault zone it gives 7.9 % strain, against 1.55 % from Hoek & Marinos's empirical fit; both are shown.
- **Gripper bearing check:** not a published rule.

## SEM / NATM sprayed concrete lining

Shotcrete ageing, the interaction of an ageing lining with the ground during advance, excavation sequence rules by ground class, and convergence monitoring.

- **Shotcrete ageing:**
  - E(t) = E₀(1 − e^(−αt)) and σc(t) = σc₀(1 − e^(−βt)), with t in hours (Oreste 2003, [doi:10.1007/s00603-002-0043-z](https://doi.org/10.1007/s00603-002-0043-z), after Weber and Pöttler), using Oreste's example and Kielder parameter sets;
  - a CEB-FIP MC90 age function fitted through measured Brenner shotcrete (Neu et al. 2017, [doi:10.3390/ma10091067](https://doi.org/10.3390/ma10091067));
  - EN 14487-1 early-strength classes J1–J3 (boundary lines as drawn in the Sika handbook).
- **Lining interaction:** Oreste's incremental method.
  - The face effect is a fictitious pressure 0.72·p0·b/(x + b) with b = 0.845R (Panet & Guenot).
  - Each displacement step loads the lining with its stiffness at that age; the age follows from the distance to the face and the advance rate.
  - Output: final load and closure, time to 95 % of the load, and the minimum safety factor (strength at age / stress).
- **Sequence:**
  - FHWA (2009) Table 9-1 rock classes: sequence, initial lining, support timing and pre-support;
  - ring closure within one diameter (Table 9-2);
  - cycle times per metre from Crossrail Stepney Green.
- **Monitoring:**
  - convergence law C(x, t) of Sulem et al. 1987, [doi:10.1016/0148-9062(87)90522-5](https://doi.org/10.1016/0148-9062(87)90522-5), with one site's parameters (Guayacán-Carrillo et al. 2016);
  - trigger levels at 75 / 105 / 150 % of the prediction (Crossrail);
  - final lining once the rate is below 1 mm/month (FHWA p. 8-15).

**Validated against:**

- ageing limits and the time constant;
- the MC90 fit passes through the measured 1 d and 28 d moduli and is within 10 % at 7 d;
- the Sika early-strength rules of thumb (1 MPa at 1 h and 10 MPa at 24 h are J2);
- the face-effect values at x = 0 and x = b;
- the lining responds as Oreste reports: a stiffer lining gives less closure and more load, and a faster advance gives less load.

**Limits:**

- Oreste's method assumes a closed ring.
- The Sulem time parameters come from one claystone site.
- Weber, Pöttler and Chang originals were not available; the forms used are as cited by Oreste.

## Ground scenarios

Loads a scenario file (`tunnelsim-scenario/1`) and answers, at any chainage:

- the ground surface and both water levels;
- the stratigraphic column, interpolated between boreholes;
- the unit at a given level;
- the ground at a face of given diameter: units and their shares, mean overburden unit weight, face-averaged φ′, c′ and E, K0 at the axis, cover, and the pore pressure at the axis from the unit's water system.

The format, the interpolation rules and the scenarios are described in [SCENARIOS.md](SCENARIOS.md): Farringdon – Liverpool Street (EPB, 14 open BGS/Crossrail boreholes) and the Thames crossing Plumstead – North Woolwich (Mixshield, 15 boreholes, four over the river). Under a river the water depth is negative; the face-support and grout windows add the river column.

**Validated against:** hand-calculated interpolation; absent units and units below the bottom of a hole; the two water systems; Python and JavaScript agree on shared vectors.

**Limits:**

- linear interpolation between boreholes, no geological model;
- one parameter set per unit (no sub-units, no depth profiles such as cu increasing with depth).

## Segment lining

What it computes:

- bending moment, normal force and springline deflection around a ring by the elastic equation method (JSCE, ITA WG2 2000 Table II-2): uniform vertical load, uniform and triangular lateral load, self weight, and a triangular soil reaction over 45–135° with bedding k = E_s / R;
- Wood's reduction of the bending stiffness for n segments, I_r = (4/n)² I;
- full-overburden loads for shallow rings (earth and water at the crown, lateral K0 times the effective stress plus water at crown and invert);
- extreme-fibre concrete stresses and ovalisation;
- jacking stress under one thrust shoe (ITA 2000) and the bursting force behind it (ACI 318 and DAUB forms, ITA 2019);
- annulus grout volume per ring and the grout pressure window at the crown (above groundwater, at most 69 kPa over it);
- ring taper for a curve, with offset longitudinal joints (DAUB).

**References:**

- [ITA WG2 (2000)](https://about.ita-aites.org/publications/wg-publications/download/80_37554c46d738a06a0d79e03e8e7c5f59), Guidelines for the design of shield tunnel lining: Table II-2, Design Example 1, jacking check;
- [ITA WG2 Report 22 (2019)](https://about.ita-aites.org/publications/wg-publications/download/1825_470d8f379299b5ad89de378875dd1b8f): Wood's reduction, bursting, grout pressure, taper, load factors;
- [DAUB (2024)](https://www.daub-ita.de/fileadmin/documents/daub/gtcrec2/2024-12_Tuebbingdesign_EN_final_web.pdf): bedding, taper with offset joints, tolerances, ovalisation.

**Validated against:**

- ITA 2000 Design Example 1: M 6.52 / −0.39 / −5.07 / −4.20 kNm/m and N 278.00 / 291.31 / 302.44 / 304.29 kN/m at 0 / 40 / 70 / 90°, soil reaction 3.27 kPa;
- the ITA 2000 jacking check: about 13 MPa for 10 jacks of 1000 kN;
- an all-round pressure gives pure compression N = p R and no bending;
- bursting forces and taper by hand.

**Limits:**

- ITA 2019 Table 6 drops the (Q′ − Q) factor of the triangular load; the ITA 2000 form is used, which reproduces the example;
- the published example's deflection omits the self-weight term, and so does the default here;
- Muir Wood, Curtis and Duddeck–Erdmann closed forms are not used (no open copy); no bedded-beam model with joint springs;
- the demos use Terzaghi's reduced vertical load (ITA 2000, Formula 2.2.1), which tends to the full overburden for shallow rings, and check the lateral coefficient at both ends of the ITA range (active and at rest); no rock loads for the double shield.

## Drill & blast

What it computes:

- the pull of a parallel cut from the empty-hole diameter, H = 0.15 + 34.1 Ø − 39.4 Ø² and advance 0.95 H (Holmberg), with several reamed holes acting as one of diameter d√n, and the number of 102 mm empty holes a round depth needs;
- the four-section cut: first burden 1.5 Ø (or 1.7 Ø minus the drilling deviation), squares growing by 1.5√2 until the opening approaches √pull;
- the bottom-charge concentration q_b = π d²/4 ρ AWS and burden B = 30 q_b / d, with Olofsson's spacing, charge-length and stemming rules for stoping, roof, wall and floor holes;
- smooth contour holes at 15 d (at most 0.7 m apart, NFF) and a helper row at most 0.9 m apart;
- a full face pattern and charges for a horseshoe profile, with two settings: textbook rules, and "Norwegian practice" (contour 0.47 m, stoping burden 0.75 B) fitted to the hole counts of current Norwegian road-tunnel rounds;
- explosive per round, specific charge, specific drilling, charge per delay;
- Kuz-Ram mean fragment size, uniformity index and Rosin–Rammler passing;
- peak particle velocity v = A (R/√Q)^B (Stockholm Northern Link fit) and the largest charge per delay for a vibration limit; SS 460 48 66 guide values with the distance factor per ground;
- Norwegian road-tunnel support classes I–IV (bolt spacing, sprayed concrete, reinforced ribs) and the bolts and sprayed concrete per round;
- the round cycle activity by activity, downtime as a share of the round, and the advance per week (101 h, the Tunnelbyggetid basis).

**References:**

- [Yilmaz (2023)](https://doi.org/10.1038/s41598-023-29803-6), Holmberg pull, four-section cut, Olofsson burden and Table 2, worked example;
- [Dyno Nobel (2010)](https://www.leg.mn.gov/docs/2015/other/150681/PFEISref_1/Dyno%20Nobel%202010.pdf), smooth blasting, cut tables, scaled distance;
- [Cunningham (2005)](https://www.wits.ac.za/media/wits-university/conferences/misgsa/documents/The%20Kuz-Ram%20fragmentation%20model%20%C3%A2%C2%80%C2%93%2020%20years%20on.pdf), Kuz-Ram;
- [Bahrekazemi, Johansson & Bodare (2011)](https://www.issmge.org/uploads/publications/59/67/10.3.GVRBA.pdf), ground vibration from tunnel blasting in Stockholm;
- SS 460 48 66 as applied in a [published Solna risk analysis](https://www.Solna.se/download/18.76f8a05e16faf0319722153d/1580131008510/Riskanalys%20vibrationer.pdf);
- [NFF publications](https://tunnel.no/english-publications/) 14, 23, 26, 27 and 28: cycle rates, weekly advance, support classes, safety;
- [Jakobsen et al. (2024), summary in Tunnels & Tunnelling](https://www.tunnelsandtunnelling.com/?p=23436): holes and contour holes in current Norwegian rounds.

**Validated against:**

- Yilmaz's example: q_b 1.36 kg/m, B 1.07 m, first cut burdens 0.052 and 0.1185 m; the V-cut example q_b 0.495 kg/m, B 0.46 m;
- the Dyno Nobel cut table (first square 210 mm for a 102 mm hole);
- SS 460 48 66 guide values 51 / 43 / 26 mm/s at 20 / 30 / 100 m on rock;
- the Northern Link fit: 14.2 kg per delay at 50 m for 20 mm/s;
- a T10.5 round: 134 charged holes and 45 contour holes (published 126–158 and 45–50);
- the cycle: drill, charge and blast 4–5 h and about 12 h per round in class I (NFF); every T10.5 activity inside one contractor's P5–P95 estimate; mucking (220 m³/h) and downtime (13 %) as logged at Ulvin; 37–39 m/week in classes I–II at 101 h, against about 48 m/week for a Tunnelbyggetid model case ([validation](validation/drill-blast-cycle.md)).

**Limits:**

- the Norwegian pattern factors are fitted, not a design rule;
- charging, positioning, reamer and RRS times are assumed; activities do not overlap; weekly advance by support class is not published openly;
- one vibration fit; Langefors' burden formula and the NTNU advance-rate model are not used (no open copy).

## Utilisation and downtime

An activity-time model of the drive, run ring by ring over calendar days. It covers:

- boring (fixed from the advance speed, or a fitted distribution);
- ring build;
- general tunnelling activities;
- train delays (rail haulage only);
- per-cycle maintenance;
- a shift pattern with a maintenance shift;
- cutting-tool interventions that stop the drive round the clock.

Outputs: utilisation (boring time / calendar time); mean advance per day and week; best day, week and month; the share of time per activity; and a check of the best values against published EPB rates and the world record of the diameter class. A seeded mulberry32 generator makes runs reproducible and bit-identical in Python and JavaScript.

**References:**

- Moosazadeh, Aghababaie, Hoseinie & Rostami (2018), [doi:10.22044/jme.2017.5707.1384](https://doi.org/10.22044/jme.2017.5707.1384). Fitted distributions from a 6.88 m metro EPB:
  - ring build: lognormal;
  - boring and general activities: log-logistic;
  - train delay: triangular;
  - rings between tool stops: Weibull;
  - stop duration: log-logistic;
  - maintenance per cycle.
- Shift pattern of 2 × 10 h + 4 h maintenance: Johnson (2014), San Francisco Central Subway, NAT 2014 (proceedings, not openly published).
- Utilisation definition: McMillan et al. (2022), TAC (proceedings, not openly published).
- Weekly advance of 40 EPBs: Roby & Willis (2014), NAT 2014 (proceedings, not openly published).
- Best published EPB rates and the record table by diameter class: sources in `EPB_REFERENCES` and `WORLD_RECORDS`.

**Validated against:**

- 20 min boring + 30 min build with no downtime gives exactly 43.2 m/day and 40 % utilisation;
- a 4 h maintenance shift removes a sixth of production;
- interventions and rail haulage slow the drive;
- default urban EPB settings give about 15–29 % utilisation and a weekly mean within two standard deviations of the survey (85 ± 36 m/week);
- best day and month stay below the published references;
- the Crossrail drives (King, Thomas & Stenning 2017, Table 3; [validation](validation/epb-crossrail-advance.md)): with 1.6 m rings, a 32 min build and two 12 h shifts, the model gives 11.8–12.5 rings a day without tool interventions, against 12.3–14.9 on drives X and Y excluding delays. Its best day (13–14 rings) and best week (about 90 rings) are well below Crossrail's 33–59 and 169–216, because ring times are drawn independently and days average out.

**Limits:**

- the distributions come from one project;
- locomotive travel time growing with tunnel length is not modelled: on the source project's own settings the model gives about 19 % utilisation against the paper's 14 %;
- no breakdowns by subsystem, station transits or ground-related stops besides tool interventions;
- the learning curve is optional (`learning_days`): about three months to average speed from [Barcelona Line 9](https://www.mdpi.com/2071-1050/17/9/3966), with a linear ramp from half speed that is assumed;
- Barcelona Line 9, a second project, also runs about 30 % faster than the model on average and 3.5–4× on its best day ([validation](validation/epb-crossrail-advance.md#a-second-project-barcelona-metro-line-9));
- day-to-day variation is optional (`day_sigma`, `day_rho`): a daily productivity factor **fitted** to Crossrail's best days and weeks ([King et al. 2017](https://learninglegacy.crossrail.co.uk/wp-content/uploads/2017/04/Machine-driven-tunnels-on-the-Elizabeth-line-London.pdf); σ 0.4, ρ 0.7) and tested on [Barcelona Line 9](https://www.mdpi.com/2071-1050/17/9/3966) (best day / mean 2.65–2.71 against 2.67–3.16). Used for the EPB demo, not for the Mixshield, whose drive varies less;
- on the Thames Tunnel Mixshields (drive H) the working day is 7–58 % fast (10.7–12.5 against 7.9–10.0 rings), with no separation-plant stops in the model ([validation](validation/slurry-thames-advance.md));
- hard-rock terms (stroke, regrip, rock support, cutter changes per cutter) are still to come.

---

## Machine class presets

[`models/presets/machine-classes.json`](../models/presets/machine-classes.json) holds scenario presets by class:

- 7 m urban EPB;
- 7 m Mixshield;
- 10 m double shield;
- 9.5 m main beam;
- SEM in stiff soil;
- drill & blast road tunnel.

Every field carries its source and a verified flag, and fields without a source stay empty. [`tests/test_presets.py`](../models/py/tests/test_presets.py) enforces this.

## Default parameter sources

- [research/methods-reference.md](research/methods-reference.md): how each method works, with typical numbers.
- [research/research-survey.md](research/research-survey.md): models, ranges, datasets and standards, with verification tags.
- [research/industry-survey.md](research/industry-survey.md): manufacturer specifications, such as disc-cutter ratings of 267 kN (17″) and 311 kN (19″/20″), machine power and torque, and record advance rates by diameter class.
