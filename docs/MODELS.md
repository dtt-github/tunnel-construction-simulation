# Model catalogue

Every model exists twice: a Python reference in [`models/py/tunnelsim_models/`](../models/py/tunnelsim_models) and a JavaScript twin in [`models/js/`](../models/js) for the browser. Both are checked against the shared vectors in [`models/test-vectors/`](../models/test-vectors). The Python tests also check hand-calculated anchor values. Each source file starts with its references, equations and units.

## Overview

| Model | Python | JavaScript | Status |
|---|---|---|---|
| [CSM disc cutter](#csm-disc-cutter) | `csm.py` | `csm.js` | Hand-checked; field validation pending |
| [Hoek–Brown rock mass](#hoekbrown-rock-mass) | `hoek_brown.py` | `hoek_brown.js` | Hand-checked |
| [Settlement and building damage](#settlement-and-building-damage) | `settlement.py` | `settlement.js` | Hand-checked; checked privately against published case histories |
| [Face support pressure](#face-support-pressure) | `face_support.py` | `face_support.js` | Hand-checked; seepage not yet modelled |
| [EPB chamber and screw conveyor](#epb-chamber-and-screw-conveyor) | `epb_chamber.py` | `epb_chamber.js` | Hand-checked; screw simplified |
| [Thrust and torque](#thrust-and-torque) | `thrust_torque.py` | `thrust_torque.js` | Hand-checked; friction coefficients illustrative |
| [Hard-rock drive](#hard-rock-drive) | `hard_rock.py` | `hard_rock.js` | Reproduces Farrokh's worked example within 3 %; support curve digitised |
| [Utilisation and downtime](#utilisation-and-downtime) | `utilisation.py` | `utilisation.js` | Deterministic limits hand-checked; default EPB inside a 40-EPB survey; one-project distributions |

Also: [machine class presets](#machine-class-presets) and [where default parameters come from](#default-parameter-sources).

---

## CSM disc cutter

Disc-cutter forces, penetration from thrust, rate of penetration, cutterhead torque (T ≈ 0.3·D·N·F_r), power and the torque limit.

- **References:** Rostami & Ozdemir (1993); Rostami (1997).
- **Validated against:** a hand calculation for a 19″ disc (p = 5 mm, UCS 150 MPa, BTS 10 MPa → F_t ≈ 201 kN, RC ≈ 0.10).
- **Drive and speed limits:**
  - Available torque is the installed torque up to the speed where it meets the installed power, then power / angular speed. The two Niagara torque points (18,800 kNm at 2.4 rpm, 9,025 kNm at 5 rpm) both give 4,725 kW.
  - Speed limit from the gauge-cutter linear speed: rpm = V_L / (π D), with V_L = 165 m/min for 17″ and 200 m/min for 19″ discs (Rostami & Chang 2017, [doi:10.1016/j.eng.2017.12.009](https://doi.org/10.1016/j.eng.2017.12.009)).
  - Optional penetration cap. The practical maximum is 15 mm/rev, the lower end of the 15–20 mm/rev "brief maximum before the conveyor overloads" (Macias & Barton 2022).
  - The limit that binds is reported (thrust, penetration, torque or power), together with the thrust actually carried by the cutters.
- **Limits:** field validation against the Yinsong dataset is pending.

## Hoek–Brown rock mass

Generalised Hoek–Brown constants (m_b, s, a), global rock-mass strength σ_cm and rock-mass modulus.

- **References:** Hoek, Carranza-Torres & Corkum (2002); Hoek & Diederichs (2006).
- **Validated against:** a hand calculation (GSI 50, m_i 10); the intact limit (GSI 100 gives s = 1).

## Settlement and building damage

What it computes:

- the Gaussian transverse trough, symmetric or asymmetric, with horizontal displacement;
- the longitudinal profile, built from face, shield, tail-void and behind-the-tail volume-loss components, with an optional longitudinal width;
- excavation-method presets (volume loss and K);
- twin-tunnel interaction;
- Burland damage categories.

**References:**

- Peck (1969); O'Reilly & New (1982); Attewell & Woodman (1982);
- Mair & Taylor (1997);
- Addenbrooke & Potts (2001), [doi:10.1061/(ASCE)1532-3641(2001)1:2(249)](https://doi.org/10.1061/(ASCE)1532-3641(2001)1:2(249));
- Burland (1995).

**Validated against:**

- a hand calculation: D 6 m, z₀ 20 m, VL 1 % → S_max 11.3 mm;
- numerical integration equals V_s, also for asymmetric troughs;
- one component at the face gives half the final settlement at the face; a tail-only component gives Φ(−L/i);
- the closed-face preset leaves 0.1–0.2 of the final trough at the face; a narrower longitudinal width lowers it without changing the final trough;
- twin-tunnel defaults equal plain superposition;
- also checked privately against published UK case histories (licensed material, not in this repository).

## Face support pressure

Wedge-silo limit equilibrium for closed-face shields, the Vermeer cohesionless limit, and the DAUB operating window.

- **Mechanism:** a Horn wedge loaded by a Janssen silo. The silo is layered above and below the water table; water is hydrostatic. The circular face is replaced by a square of equal area.
- **Operating window:** p_min = 1.5 × earth + 1.05 × water at the axis; p_max = 0.9 × overburden at the crown. The factors are parameters and still need checking against the DAUB document.

**References:**

- Horn (1961); Janssen (1895);
- Anagnostou & Kovári (1994), [doi:10.1016/0886-7798(94)90028-0](https://doi.org/10.1016/0886-7798(94)90028-0);
- Vermeer, Ruse & Marcher (2002);
- DAUB / ITA-AITES (2016).

**Validated against:**

- silo limits: deep → (rγ − c)/(K tan φ); φ = 0 → overburden;
- dry sand within 1.0–1.3 × Vermeer for φ 25–40°, as expected for limit equilibrium;
- nearly cover-independent; stiff undrained clay is self-supporting;
- the window closes at very shallow cover under water;
- the Phase 0 MPM face benchmark reached 0.79 of Vermeer at D/20 ([results](../phase0/RESULTS.md)).

**Limits:**

- no seepage forces yet;
- the DAUB partial factors are not yet verified.

## EPB chamber and screw conveyor

What it computes:

- the support pressure from a volume balance of soil, foam liquid and foam air (Boyle's law, exact integration per step);
- the foam split from FIR and FER;
- the steady screw flow for a target pressure;
- chamber stiffness;
- screw capacity and efficiency, with an exponential pressure drop along the screw.

**References:**

- EFNARC (2005) for FIR and FER;
- Merritt & Mair (2006, 2008), simplified;
- Yeh (1996).

**Validated against:**

- the Boyle limit with air only;
- p = K·ε without air;
- stiffness (K − p)²/(K·V) unconditioned, and ≈ (p + p_atm)/V_air with foam;
- the solution converges to the steady state independent of step size;
- stopping the screw raises the pressure; an over-fast screw empties the chamber.

**Limits:**

- screw efficiency and decay length are illustrative defaults;
- no slurry branch yet.

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

- friction coefficients are illustrative;
- the Krause α·D³ band was dropped because modern EPBs exceed it.

## Hard-rock drive

Cutter wear and changes, rock support by class, and utilisation as downtime per kilometre for open, single- and double-shield TBMs.

- **Cutter wear:**
  - cutter life CL = 1026 / CAI m³ per cutter (Frenzel 2011, via Zhang et al. 2025, [doi:10.1007/s40789-025-00787-0](https://doi.org/10.1007/s40789-025-00787-0));
  - cutters consumed per km = excavated volume / CL;
  - 66 min per change (Farrokh 2013);
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
- the wear model gives 25.6 h/km against Farrokh's 30 h/km for low-quartz rock at CAI 2.

**Limits:**

- the support curve is digitised from a figure;
- the CAI wear model excludes chipping and bearing failures, so it is a lower bound;
- the NTNU cutter-life model (CLI) is not implemented, because its charts are not available in closed form;
- there are no per-bolt or per-ring-beam installation times (no open source found).

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
- Shift pattern of 2 × 10 h + 4 h maintenance: Johnson (2014), San Francisco Central Subway, NAT 2014.
- Utilisation definition: McMillan et al. (2022), TAC.
- Weekly advance of 40 EPBs: Roby & Willis (2014), NAT 2014.
- Best published EPB rates and the record table by diameter class: sources in `EPB_REFERENCES` and `WORLD_RECORDS`.

**Validated against:**

- 20 min boring + 30 min build with no downtime gives exactly 43.2 m/day and 40 % utilisation;
- a 4 h maintenance shift removes a sixth of production;
- interventions and rail haulage slow the drive;
- default urban EPB settings give about 15–29 % utilisation and a weekly mean within two standard deviations of the survey (85 ± 36 m/week);
- best day and month stay below the published references.

**Limits:**

- the distributions come from one project;
- locomotive travel time growing with tunnel length is not modelled: on the source project's own settings the model gives about 19 % utilisation against the paper's 14 %;
- no learning curve, breakdowns by subsystem or ground-related stops besides tool interventions;
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
