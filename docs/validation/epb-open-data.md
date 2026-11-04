# EPB thrust and torque against open field data

- **Script:** [`models/py/validation/epb_open_data.py`](../../models/py/validation/epb_open_data.py). It downloads the data on first run into a local cache that is not committed, then prints the tables below.
- **Models:** [thrust and torque](../MODELS.md#thrust-and-torque)
- **Run on:** 5 Nov 2026

## Data

Both datasets are published under CC BY 4.0. Credit them wherever these results are used.

| Dataset | Records | What it has | Source |
|---|---|---|---|
| Changsha Metro Line 4 EPB | 294 averaged ring records | thrust, cutterhead torque, chamber pressure, cover, water-table depth, SPT / UCS, ground class 1–4 | Zhang, Chen & Wu (2019), *Automation in Construction* 106:102860; data [doi:10.17632/ndy5r67zxz.1](https://doi.org/10.17632/ndy5r67zxz.1) |
| Guangzhou–Foshan intercity railway EPB | 1,197 records | thrust per cutterhead area, torque per D³, upper and lower earth pressure, advance, ground class (1 soft soil, 2 mostly soft soil, 3 mostly hard rock) | Yan (2022), *Data in Brief* 108726, [doi:10.1016/j.dib.2022.108726](https://doi.org/10.1016/j.dib.2022.108726); data [doi:10.17632/cjwbjttf88.1](https://doi.org/10.17632/cjwbjttf88.1) |

**What is known about each dataset, and what is not:**

- **Changsha columns:** the data carry no column definitions. The units (thrust in MN, torque in MN·m, chamber pressure in bar) follow a paper by the same group on the same line: Geng et al., [arXiv:2305.05128](https://arxiv.org/abs/2305.05128), Table 2.
- **Changsha machine and site** (same paper, section 4.1 and Table 1):
  - 6.28 m cutterhead with 35 % opening, 1.5 m rings;
  - cover 6.7–35.5 m;
  - ground from silty clay and gravel to weathered rock, with UCS up to 59 MPa.
- **Changsha, not published openly:** shield length, weights and the ground parameters for each ring.
- **Guangzhou–Foshan diameter:** recovered from the data. Thrust = FPI × PR and torque = TPI × PR give D = 9.15 m in every row.
- **Guangzhou–Foshan, not published openly:** cover, groundwater and soil strength. They are in a paywalled companion paper, so this dataset can only bound the model, not test it ring by ring.

## Changsha: model against measurement

**Model set-up:**

- **Inputs from the data, ring by ring:** chamber pressure at the axis, cover, and water-table depth.
- **From the machine data:** 6.28 m diameter and 35 % opening.
- **Assumed:**
  - shield length 8.5 m;
  - unit weight 20 kN/m³ and K0 0.5;
  - weights and tool counts scaled from the urban EPB demo;
  - friction coefficients at the model defaults: shield 0.3, rim 0.3, face 0.15, chamber 0.1.

**Results by ground class.** Each cell is the median of predicted ÷ measured, with the interquartile range in brackets.

| Ground class | Rings | Thrust | Torque |
|---|---|---|---|
| all | 281 | 1.43 (1.07–1.81) | 1.70 (1.35–2.35) |
| 1 | 5 | 1.49 (1.33–1.60) | 2.16 (2.00–2.29) |
| 2 | 13 | 1.71 (1.35–2.26) | 2.85 (2.30–3.67) |
| 3 | 236 | 1.42 (1.08–1.83) | 1.66 (1.29–2.27) |
| 4 | 27 | 1.11 (0.90–1.50) | 1.65 (1.39–2.29) |

**Medians and spread:**

| | Measured | Predicted |
|---|---|---|
| Thrust (MN) | 12.6 (10.5–15.6) | 18.7 (16.7–20.6) |
| Torque (MN·m) | 2.37 (1.87–3.00) | 4.36 (3.75–4.71) |

**What this shows:**

- **Over-prediction:** with the default coefficients the model gives about 1.4× the measured thrust and 1.7× the measured torque.
- **Thrust:** the excess is mostly shield skin friction, 70 % of the predicted thrust. Shield friction of 0.17, instead of 0.3, brings the median thrust to the measured one.
- **Torque:** the excess is mostly rim friction, 52 % of the predicted torque. A rim friction of 0.07 brings the median torque to the measured one. A value that low suggests the model's rim load is too high: the full radial ground stress over a 0.5 m rim, with no overcut and no conditioning. The friction coefficient alone is probably not the cause.
- **Ring-to-ring variation is not reproduced:** the correlation between predicted and measured values ring by ring is 0.03 for thrust and 0.05 for torque. The measured scatter comes from things the model does not take as inputs: ground at the face, conditioning, operator settings. Cover and chamber pressure explain almost none of it.

## Guangzhou–Foshan: bounds from the data

| Class | Records | Thrust (MN) | Torque (MN·m) | T / D³ (kN·m/m³) | Mean earth pressure × area / thrust | Advance (mm/min) |
|---|---|---|---|---|---|---|
| 1 soft soil | 519 | 23.0 (20.8–26.8) | 3.3 (2.4–4.7) | 4.3 (3.1–6.1) | 0.44 (0.38–0.51) | 35 (25–42) |
| 2 mostly soft soil | 536 | 39.0 (33.0–45.5) | 7.0 (5.4–8.9) | 9.1 (7.1–11.6) | 0.40 (0.35–0.45) | 12 (10–15) |
| 3 mostly hard rock | 142 | 15.0 (13.0–18.6) | 3.0 (2.7–3.5) | 3.9 (3.5–4.6) | 0.10 (0.07–0.18) | 10 (8–12) |

**What this shows:**

- **Torque against installed:** the working torque is 3–7 MN·m. That is about 15–35 % of the installed torque of the reference EPB machines scaled to 9.15 m (18.8–21.2 MN·m).
- **Face pressure share of thrust:**
  - In soft ground, the earth pressure on the face carries about 40–44 % of the thrust; the rest is friction and the other terms.
  - In mostly hard rock the chamber runs at low pressure, so the face term falls to about 10 %.
- **Mixed face:** class 2 needs about twice the thrust and torque of soft soil, at a third of the advance rate.

## Consequences for the demos

- **Thrust and torque bars:** in the EPB and Mixshield demos these use the default coefficients, so they are probably on the high side. The Changsha data suggest a shield friction near 0.17 and a much smaller rim term.
- **No defaults changed yet:**
  - the two datasets come from two Chinese metro projects in mixed ground;
  - the Changsha machine geometry is partly assumed;
  - the rim result points to the model's form rather than a coefficient.
- **Before changing defaults:** add a third dataset with published site parameters, then decide whether to recalibrate.
