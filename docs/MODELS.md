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

Also: [machine class presets](#machine-class-presets) and [where default parameters come from](#default-parameter-sources).

---

## CSM disc cutter

Disc-cutter forces, penetration from thrust, rate of penetration, cutterhead torque (T ≈ 0.3·D·N·F_r), power and the torque limit.

- **References:** Rostami & Ozdemir (1993); Rostami (1997).
- **Validated against:** a hand calculation for a 19″ disc (p = 5 mm, UCS 150 MPa, BTS 10 MPa → F_t ≈ 201 kN, RC ≈ 0.10).
- **Limits:**
  - Penetration is bounded only by the solver at 30 mm/rev; a muck-capacity limit is planned.
  - No constant-power region in the drive.
  - Field validation against the Yinsong dataset is pending.

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
