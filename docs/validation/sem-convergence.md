# Ground response against measured convergence in weak rock

- **Script:** [`models/py/validation/sem_convergence.py`](../../models/py/validation/sem_convergence.py). It downloads the data package on first run into a local cache that is not committed, then prints the table below.
- **Models:** [Hoek–Brown](../MODELS.md#hoekbrown-rock-mass), [ground response](../MODELS.md#ground-response-and-squeezing), which the [SEM demo](../realism/sem-heading.md) uses.
- **Run on:** 5 Nov 2026

## Data

The sections come from a hydropower headrace tunnel in weak flysch in central Albania, drilled and blasted with sprayed-concrete support. There are 14 monitored sections:

- GSI 25–35;
- rock cover 226–285 m;
- radius about 3 m;
- convergence read from a station installed 0.5–5 m behind the face, for 132–382 days.

They are Tables 5 and 9 of Terron-Almenara & Panthi (2025), *Rock Mechanics and Rock Engineering* 58:8111–8143, [doi:10.1007/s00603-025-04545-1](https://doi.org/10.1007/s00603-025-04545-1) (open access, CC BY 4.0). The transcription used here is in the data package of Zhang et al. (2026), [doi:10.5281/zenodo.23040284](https://doi.org/10.5281/zenodo.23040284) (CC BY 4.0).

**Set-up** (as in the package's own analysis):

- in-situ stress 0.025 MPa per metre of cover (the source's relation);
- mᵢ 7 for this siltstone-dominated flysch and Poisson's ratio 0.3;
- rock-mass modulus and σci from the source's Table 9;
- the model chain is Hoek–Brown, then equivalent Mohr–Coulomb at the in-situ stress, then the Duncan Fama ground reaction, then the Vlachopoulos & Diederichs longitudinal displacement profile.

**Reading the measurements:**

- The reading is the convergence after the station was installed, so the model's quantity is the wall displacement still to come at distance L behind the face.
- About a third of the deformation in this flysch is time-dependent (source, section 3.6). The time-independent part of each reading is therefore taken as two-thirds to all of it.
- The installed support capacity is known (1.4–2.0 MPa, Table 9), but how much of it was mobilised was not measured. So the check asks what support pressure the model needs to reproduce each reading, and whether that is within the installed capacity.

## Results

| Section | Class | GSI | P0 (MPa) | Reading, radial (mm) | Model, unsupported after the station (mm) | R_p / a | Support needed (MPa) | Installed (MPa) | Share mobilised |
|---|---|---|---|---|---|---|---|---|---|
| 7+029 | X | 25 | 5.65 | 17 | 26 | 2.41 | 0.13–0.24 | 2.0 | 6–12 % |
| 7+064 | X | 25 | 5.95 | 16 | 32 | 2.43 | 0.28–0.42 | 2.0 | 14–21 % |
| 7+092 | X | 25 | 6.25 | 15 | 25 | 2.45 | 0.14–0.24 | 1.6 | 9–15 % |
| 7+136 | VI | 35 | 6.78 | 10 | 15 | 1.96 | 0.17–0.34 | 1.6 | 11–21 % |
| 7+168 | VIII | 27 | 7.00 | 16 | 56 | 2.55 | 0.64–0.81 | 1.6 | 40–51 % |
| 7+194 | X | 25 | 7.03 | 9 | 21 | 2.41 | 0.22–0.29 | 1.6 | 14–18 % |
| 7+218 | X | 25 | 6.98 | 12 | 29 | 2.61 | 0.29–0.39 | 1.6 | 18–24 % |
| 7+266 | VIII | 35 | 6.93 | 6 | 14 | 2.02 | 0.42–0.59 | 1.4 | 30–42 % |
| 7+291 | VIII | 30 | 6.88 | 9 | 17 | 2.23 | 0.22–0.34 | 2.0 | 11–17 % |
| 7+316 | VIII | 30 | 6.78 | 8 | 13 | 2.05 | 0.19–0.32 | 1.6 | 12–20 % |
| 7+342 | VIII | 32 | 6.98 | 8 | 9 | 2.21 | 0.02–0.09 | 2.0 | 1–5 % |
| 7+423 | BIM | 35 | 7.10 | 3 | 8 | 1.77 | 0.37–0.49 | 1.6 | 23–31 % |
| 7+455 | BIM | 33 | 7.12 | 4 | 10 | 1.96 | 0.32–0.43 | 1.6 | 20–27 % |
| 7+531 | X | 25 | 6.25 | 23 | 24 | 2.50 | 0.02–0.12 | 1.4 | 1–8 % |

**What this shows:**

- **Consistent with the field data:**
  - Unsupported, the model gives a median 1.77× the measured convergence after the station.
  - Every reading is reproduced with a support pressure inside the installed capacity: 1–51 % of it, median 11–19 % in the flysch sections.
  - The plastic zone comes out at 1.8–2.6 radii.
- **Not a tight test:** the reading cannot separate the rock-mass stiffness from the share of support mobilised. The package's article draws the same conclusion about identifiability. So this check confirms the order of magnitude, not a calibrated value.
- **Rock-mass modulus:** the source's back-analysed values are higher than the Hoek–Diederichs (2006, [doi:10.1016/j.ijrmms.2005.06.005](https://doi.org/10.1016/j.ijrmms.2005.06.005)) estimate with Eᵢ 20 GPa that the demos use. The Hoek–Diederichs value is a median 0.64 of the source's. With it, our predicted displacements would be larger.
- **Time:** the data hold one reading per section, not a time series. So the Sulem convergence law and its time parameters in the SEM demo are not tested here.

## Consequences

- **No defaults change.** The ground-response chain is consistent with this tunnel.
- **Still open for the SEM demo:**
  - convergence time series from a site in comparable rock, to test the Sulem law (parameters now compared with an independent fit; see the next section);
  - a measured share of support mobilisation, for example from lining strain gauges, to test the lining interaction.

## Sulem time law: a second site

- **Script:** [`models/py/validation/sem_time_law.py`](../../models/py/validation/sem_time_law.py). Nothing is fitted; no default is changed.
- **Demo:** the weak-rock scenario uses the Sulem et al. (1987) law with parameters fitted to a claystone drift (D 5.2 m) at the Meuse/Haute-Marne laboratory: X = 0.885 D, T = 6 days, m = 5.7, n = 0.3 (Guayacan-Carrillo et al. 2016). At Farringdon the time term is off.
- **Second site:** de La Fuente, Sulem, Taherzadeh & Subrin (2020), Rock Mechanics and Rock Engineering, [free-access version on HAL](https://hal.science/hal-03119942), section 4.1. The same law fitted to the convergence records of the Fréjus road tunnel (squeezing calc-schist): X = 0.9 D, m = 4.5, n = 0.3 for almost all sections, and T fitted per section, 0.5–5 days.

Convergence far behind the face, as a multiple of the instantaneous convergence:

| Days | 1 | 7 | 30 | 100 | 365 | Final |
|---|---|---|---|---|---|---|
| Demo | 1.26 | 2.18 | 3.37 | 4.29 | 5.05 | 6.7 |
| Fréjus, T 0.5–5 days | 1.24–2.26 | 2.04–3.50 | 2.99–4.19 | 3.69–4.58 | 4.26–4.88 | 5.5 |

**What this shows:**
- **X agrees** (0.885 D against 0.9 D) and n is the same.
- **The first 100 days agree:** the demo’s curve lies inside the Fréjus band up to 100 days, at its slow edge early on, because its T (6 days) is just above Fréjus's 0.5–5.
- **The long term is higher:** m 5.7 against 4.5 puts the demo 3.5 % above the band at one year and its final value 22 % above (6.7 against 5.5 times the instantaneous convergence). The demo shows the first weeks, so this is not changed.
- **Not a time series test:** this compares fitted parameters, not records. The Fréjus records themselves are only plotted.

## Farringdon platform tunnels: undrained ground, London clays

- **Script:** [`models/py/validation/sem_farringdon.py`](../../models/py/validation/sem_farringdon.py). It prints the table below.
- **Demo:** the [SEM demo](../realism/sem-heading.md) runs on this ground by default.

### Data

The Crossrail platform tunnels at Farringdon are sprayed-concrete enlargements of a 6.2 m TBM pilot tunnel. The finished section is about 11.4 m wide by 10.6 m high, with a 400 mm steel-fibre primary lining. The axis is about 30 m below street level, mostly in the Lambeth Group, with London Clay above. Sources are the Crossrail Learning Legacy papers; their numbers are quoted here, not redistributed.

- **Measured crown settlement, platform tunnels PTW and PTE** (Gakis, Grau & Schwind (2016), [Tunnel deformations caused by compensation grouting at Crossrail Farringdon Station](https://learninglegacy.crossrail.co.uk/documents/tunnel-deformations-caused-compensation-grouting-crossrail-farringdon-station/), Table 1):
  - outside the zone of concurrent compensation grouting: 10.3–16.5 mm, mean 13.5 / 13.7 mm. This is the comparison target, because grouting is not modelled;
  - inside it: 12.8–18.9 mm, mean 15.9 / 16.4 mm, about 2.5 mm more.
- **Time history** (same paper, In-tunnel monitoring). Readings rose roughly linearly from installation to ring closure, 3–5 days. They slowed for another 3–5 days, then stayed steady within reading accuracy.
- **Crossrail's own prediction** (same paper, Table 4). The design 2D FE used the same design lines, Mohr–Coulomb, K0 1.2 with a zone of K0 0.6 around the tunnel, and 80 % stiffness relaxation before the lining. Without grouting it gave 10 mm of crown displacement after lining installation.
- **Whole-ring settlement** (Stärk, Jimenez Rangel & Wade, [Analyses of convergence and utilisation of SCL-tunnels during excavation](https://learninglegacy.crossrail.co.uk/documents/analyses-convergence-utilisation-scl-tunnels-excavation/), Crossrail Whitechapel). In the 10.5–11.5 m enlargements in London Clay, the crown settled 7–10 mm. The lower points settled 2–3 mm: "the tunnel on the whole settles". The design predicted less whole-body movement than this. Movements faded within 5–12 days.
- **Undrained design lines** (z is the depth below the top of the London Clay; source: [Temporary sprayed concrete lining tunnels in Farringdon Crossrail Station](https://learninglegacy.crossrail.co.uk/documents/temporary-sprayed-concrete-lining-tunnels-farringdon-crossrail-station/), Table 1):
  - London Clay: cu = 85 + 6.5z kPa, E = 40 + 3.7z MPa;
  - Lambeth Group: cu = 95 + 10z kPa, E = 36 + 5.9z MPa;
  - ν 0.495;
  - K0 0.6 gave realistic deformations; K0 1.2 governed lining stress.
- **Ring closure:** 3–5 days after a monitoring section was installed, at 1.5–2 m/day (Gakis et al. 2016), so about 5–10 m behind the face.
- **Advance:** the platform enlargements advanced at 1.1 m/day ([delivering value](https://learninglegacy.crossrail.co.uk/documents/crossrail-farringdon-station-scl-tunnels-delivering-value-through-innovation-and-best-practice/), section 4.6).
- **Ground along the line:** depth, unit at the axis and pore pressure come from the [Farringdon – Liverpool Street scenario](../SCENARIOS.md), at scenario chainage 360–660 m.

### Why the first version read low

The first version compared the axisymmetric ring movement directly with the crown and got 5–8 mm in the Lambeth Group, low by 1.3–2.7×. The sources point to two missing terms and rule out a third:

1. **The crown follows the vertical stress, not the mean.** The ring solution uses p0 = (σv + σh)/2 and gives one radial movement all round. Kirsch's elastic solution for unequal stresses gives u_r = (σv·a/4G)[(1 + K) − (1 − K)(3 − 4ν)cos 2θ] at the wall (Brady & Brown 2006; open form in the [GeoStudio Kirsch verification](https://files.seequent.com/GeoStudio/SigmaW/Verification-Kirsch.pdf)). Here θ is measured from the springline and K is the total-stress ratio. Crown over mean is 1 + (1 − K)(3 − 4ν)/(1 + K). For undrained ground (ν → 0.5) the crown moves σv·a/2G whatever K is, so mean-stress p0 at K 0.6 under-predicts the crown by about 1.25×.
2. **The ring settles as a whole.** At Whitechapel, 2–3 mm of the 7–10 mm crown settlement was movement of the whole ring, which a plane-strain ring around a fixed centre cannot produce. That measured term is added, not computed.
3. **Consolidation is not the cause.** At Farringdon the in-tunnel readings were steady within 3–5 days after ring closure. Long-term consolidation, which nearly doubled the surface settlement over Whitechapel over two years ([long-term settlement](https://learninglegacy.crossrail.co.uk/documents/long-term-settlement-following-scl-tunnel-excavation/)), is not in the in-tunnel numbers being compared.

### Set-up

- The section is an 11 m circle.
- The ground is undrained Tresca (φ = 0, c = cu). The ground reaction is the φ → 0 limit of Duncan Fama: p_cr = p0 − cu and R_p = a·exp((p0 − cu − p_i) / 2cu).
- p0 is the mean of the total vertical and total horizontal stress at the axis.
- The ring is taken to carry load only once it is closed. The open top-heading arch before that counts as no support.
- The ring movement after the first survey, one 1 m round behind the face, is u_final − u_free·LDP(1 m). Lining: 400 mm, Kielder shotcrete ageing, 1.1 m/day.
- Crown settlement = ring movement × Kirsch crown factor + 2.5 mm whole-ring settlement (the middle of 2–3 mm), in `sem.crown_settlement`.

### Results

Ring movement / crown settlement after the first survey (mm):

| Scenario chainage | Clay at the axis | z below LC top (m) | cu (kPa) | E (MPa) | K0 | Ring closed 5 m back | 7.5 m back | 10 m back |
|---|---|---|---|---|---|---|---|---|
| 360 | LG | 23.5 | 330 | 175 | 0.6 | 5.3 / 9.1 | 6.8 / 11.0 | 7.8 / 12.3 |
| 360 | LG | 23.5 | 330 | 175 | 1.2 | 6.4 / 8.3 | 9.5 / 11.1 | 11.8 / 13.2 |
| 480 | LG | 26.8 | 363 | 194 | 0.6 | 5.0 / 8.8 | 6.4 / 10.5 | 7.3 / 11.7 |
| 480 | LG | 26.8 | 363 | 194 | 1.2 | 6.2 / 8.1 | 8.8 / 10.5 | 10.7 / 12.2 |
| 600 | LG | 28.2 | 377 | 203 | 0.6 | 5.0 / 8.8 | 6.3 / 10.4 | 7.2 / 11.6 |
| 600 | LG | 28.2 | 377 | 203 | 1.2 | 6.1 / 8.1 | 8.7 / 10.4 | 10.5 / 12.1 |
| 660 | LC | 28.4 | 270 | 145 | 0.6 | 6.3 / 9.7 | 9.8 / 13.7 | 12.3 / 16.6 |
| 660 | LC | 28.4 | 270 | 145 | 1.2 | 7.1 / 9.2 | 12.8 / 14.6 | 17.2 / 18.7 |

The script prints every 60 m; the rows at 420 and 540 m lie between their neighbours.

**What this shows:**

- **Ring closed 7.5 m back:** the crown settlement is 10.4–11.0 mm in the Lambeth Group and 13.7 mm where London Clay is at the axis. Measured outside grouting: 10.3–16.5 mm, mean 13.6 mm. The prediction is now inside the measured range, in its lower half, and next to Crossrail's own FE (10 mm).
- **K0 hardly matters for the crown now:** 0.6 and 1.2 give results within 1 mm at 7.5 m, because undrained crown movement depends on σv. The choice of K0 still matters for the ring movement and the lining load.
- **Still below the mean in the Lambeth Group, by about 1.2–1.3×.** Possible reasons, none quantified in an open source:
  - the open top-heading arch settles on its footings before closure;
  - the design lines may be stiffer than the ground near an enlarged tunnel;
  - some sections may have had front injections of grouting.
  - The pilot tunnel acts the other way: it relaxed the ground before the enlargement, which would lower the measured movement.
- **Ring support at the face** still predicts almost no ring movement, so ring closure is what lets most of the movement happen.
- **Not a tight test:** these are design lines and published averages, not a section-by-section back-analysis. The whole-ring term comes from Whitechapel (London Clay), not Farringdon.

### Consequences for the demo

- The SEM demo uses K0 0.6 for the deformation prediction and K0 1.2 for the lining load, as Crossrail's design did. The ring is closed 7.5 m back, the middle of the published range.
- The predicted crown settlement is the ring movement × Kirsch factor + 2.5 mm. The demo shows it beside the measured 10.3–16.5 mm (outside grouting) and Crossrail's 10 mm FE.
- Readings use only the distance-to-face term, because the measured movements levelled out within days of ring closure.
