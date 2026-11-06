# Validation report: what each demo and model is checked against

- **What this is:** one page that gathers every check in the project: the data, the result and what kind of check it is. It also lists what is still assumed or unchecked. The details are on the validation pages it links.
- **Status:** as of 5 Nov 2026 (main at `0c11cb4`). Update it whenever a validation page changes.
- **Sources:** every data source is openly published. The links are on the validation pages.

## How to read it

**Kinds of check.** The difference matters, because a model can always be made to fit the data it was tuned on.

| Kind | Meaning |
|---|---|
| **Independent** | The data were not used to set anything in the model. This is a real test. |
| **Calibrated** | A parameter was set from these data. Agreement afterwards is expected, not evidence. The same parameter must then be tested on other data. |
| **Consistency** | The site's own back-analysed parameters are put into the model, and the model reproduces the site's result. This tests the arithmetic, not the prediction. |
| **Bracket** | The data come from other projects or conditions. They show the model is in a sensible range; they cannot confirm a value. |
| **Failed / blocked** | The check was run and not met, or cannot be run yet. |

**Words used for the results:**
- **Matches:** within the scatter of the data or the tolerance stated on the page.
- **Over / under:** the ratio model ÷ measured, unless stated otherwise.

## Summary by demo

| Demo | Strongest independent check | Calibrated on | Biggest known gap |
|---|---|---|---|
| [Urban EPB](../../web/epb/) | Thrust at Mashhad 1.3 bar 0.89× and Sofia 1.02–1.28×; ring cycle on an average Crossrail working day, 11.8–12.5 against 12.3–14.9 rings | Shield and rim friction on 281 Changsha rings; Hyde Park settlement uses the site's own back-analysis | Torque in foam-conditioned clay 2.7× over (Sofia); best days and weeks far too low; volume loss is an input, not predicted |
| [Mixshield](../../web/slurry/) | Thames settlement 1.10× median over 17 sections (see the caveat below) | Thames volume loss 0.25 % fitted to those same 17 sections | Working day 7–58 % fast; no separation-plant stops; whole drive about 2× faster than measured; air-cushion model is this project's own derivation |
| [Gripper TBM](../../web/hard-rock/) | None of its own: it shares the CSM penetration fitted at Follo | Penetration (ψ = −0.1) on Follo | No open section-by-section data for Gotthard; advance only bracketed (calendar against working days) |
| [Double shield](../../web/hard-rock/) | Follo advance 12.9–14.9 against 14.1 m/day (tests the downtime model only) | Penetration on the Follo 4.5 km mean; discs, thrust and rpm are the Follo means | Penetration does not follow section-to-section strength (0.41–2.89×); cutter changes about 40 % too few |
| [Drill & blast](../../web/drill-blast/) | Ulvin drilling 0.88× and charging 1.26× (logged round); every T10.5 activity inside a contractor's P5–P95 range | Mucking rate and downtime share at Ulvin; ventilation and scaling at the contractor median | Weekly advance by support class not published, so class IV is untested; activities do not overlap |
| [SEM / NATM](../../web/sem/) | Farringdon crown settlement 10.4–13.7 mm against 10.3–16.5 measured; Albanian flysch convergence of the right order | None fitted; the 2.5 mm whole-ring term is taken from Whitechapel | Prediction sits in the lower half of the measured range; Sulem time law from one site; not a tight test |
| [Ground physics (GPU MPM)](../../web/epb/) | Element tests: Rankine within ±6 %, column collapse 7 of 8 within ±17 % | The friction mapping μ = sin φ′ was chosen from the Rankine test | Face pressure only bracketed (Idinger); K0 failed; clay and chamber blocked by solver volume loss |

## Checks by model

### Settlement and building damage ([settlement](settlement.md))

| Check | Data | Result | Kind |
|---|---|---|---|
| Smax, Hyde Park first bore | Wan, Standing, Potts & Burland (2017) | 8.1 against 8.3 mm | Consistency: the site's own VL 0.78 % and K 0.44 |
| Smax, Thames chalk, 17 twin-bore sections | Cheng & Mikulski (2014), Table 1 | Median 1.10 (0.80–2.38) | Calibrated: VL 0.25 % fitted to these sections. The paper doesn't state how its table should be read; the reading that agrees was chosen |
| Second bore, Hyde Park | Wan et al. (2017) | VL ratio median 1.7, Ky 0.44 → 0.33 | Calibrated parameters, then transferred to Farringdon |
| Farringdon – Liverpool Street | none on this stretch | VL 0.5 %, K 0.43 transferred from Hyde Park | Untested |

### Thrust and torque ([EPB field data](epb-open-data.md))

| Check | Data | Result (new defaults) | Kind |
|---|---|---|---|
| Changsha Line 4, 281 rings | Zhang, Chen & Wu (2019), CC BY 4.0 | Thrust 0.99 (0.76–1.23), torque 0.99 (0.74–1.44) | Calibrated (shield 0.17, rim 0.07) |
| Mashhad Line 3, 1.3 bar | Farrokh, Lotfi & Dalir (2025) | Thrust 0.89, torque 1.06 | Independent: matches |
| Mashhad Line 3, 0.27 bar | same | Thrust 2.04, torque 1.85 | Independent: fails (ground arching suspected) |
| Sofia Line 3, 14 bin means | Benli (2019) | Thrust 1.02–1.28, torque 2.67–2.80 | Independent: thrust matches, torque fails |
| Ring-to-ring variation, Changsha | Zhang et al. (2019) | Correlation about 0.1 | Fails: not reproduced |
| Guangzhou–Foshan | Yan (2022), CC BY 4.0 | Working torque 15–35 % of installed | Bracket (cover and ground not published openly) |

### Utilisation, downtime and advance ([Crossrail EPB](epb-crossrail-advance.md), [Thames Mixshield](slurry-thames-advance.md))

| Check | Data | Result | Kind |
|---|---|---|---|
| EPB rings per average working day | King, Thomas & Stenning (2017), Table 3 | 11.8–12.5 against 12.3–14.9 | Independent: matches (ring length, build time and shifts are taken from the sources) |
| EPB whole drive | same | 9.2–9.6 against drive X 8.9–9.0; drive Y 5.1–5.5 | Matches X; Y has station transits, not modelled |
| EPB best day and week | same | 13–14 against 33–59 rings; about 90 against 169–216 per week | Fails |
| Mixshield rings per working day | same, drive H | 10.7–12.5 against 7.9–10.0 | Fails: 7–58 % fast |
| Mixshield best day and week | same | 12–14 against 16–17; 77–92 against 91–100 | Matches roughly |
| Mixshield whole drive | same | 8.4–9.6 against 4.4–4.6 | Fails: about 2× fast (river crossing and interventions not modelled) |

### Disc-cutter penetration (CSM) and the hard-rock drive ([hard-rock projects](hard-rock-projects.md))

| Check | Data | Result | Kind |
|---|---|---|---|
| Follo TBM1, 4.5 km mean penetration | Hansen (2018), NTNU | 6.36 against 6.32 mm/rev at ψ −0.1 | Calibrated (ψ back-analysed) |
| Follo, 18 sections | same | 0.41–2.89× with each section's strength test; about ±27 % with the tunnel-mean strength | Independent: fails section by section; other rock types untested |
| Follo advance and utilisation | Iddeng (2019); Herrenknecht reference | 12.9–14.9 against 14.1 m/day; 28–32 % against about 31 % | Independent for the downtime model only (fed the measured penetration) |
| Cutter changes per km (CAI wear) | Herrenknecht Follo reference | About 266 against 442 | Fails: a lower bound |
| Gotthard, Guadarrama, Brenner, Niagara | project reports | Average advance 3–20 m/day | Bracket |

### Ground response, Hoek–Brown and SEM lining ([SEM convergence](sem-convergence.md))

| Check | Data | Result | Kind |
|---|---|---|---|
| Convergence, 14 sections in flysch (Albania) | Terron-Almenara & Panthi (2025), CC BY 4.0 | Unsupported prediction a median 1.77× the reading; the support share needed is 1–51 % | Independent: order of magnitude only (stiffness and support cannot be separated) |
| Farringdon platform crown settlement | Gakis, Grau & Schwind (2016) | 10.4–13.7 against 10.3–16.5 mm (mean 13.6) | Independent, but the 2.5 mm whole-ring term is transferred from Whitechapel; in the lower half of the range |
| Hoek–Brown on its own | hand calculation only | – | Not checked against field data |
| Sprayed-concrete ageing | Brenner shotcrete moduli at 1 d and 28 d | Passes through both | Laboratory data, not a tunnel |

### Drill & blast ([drill & blast cycle](drill-blast-cycle.md))

| Check | Data | Result | Kind |
|---|---|---|---|
| Ulvin round: drilling, charging | Messelt (2013), NMBU | 0.88×, 1.26× | Independent |
| Ulvin round: mucking, downtime | same | 1.00; 13 % | Calibrated |
| T10.5 class II activities | Furunes & Strype (2022), NTNU, contractor estimate | All inside P5–P95; drilling, mucking and spraying above the median | Independent, except ventilation and scaling, set at the median |
| Round time and weekly advance by class | NFF Publication 14 | 12.7 h against "about 12 h" | Matches; production hours set from the Tunnelbyggetid basis |
| Hole count, T10.5 | published counts | 134 and 45 against 126–158 and 45–50 | Matches, but the contour spacing and burden were fitted to these counts |

### Face support, chamber, slurry and lining (analytical)

| Model | What it is checked against | Kind |
|---|---|---|
| Face support (wedge-silo, DAUB window) | DAUB (2016) example 8.1 (reproduced: 66.56°, 4,121 against 4,122 kN, operating range 200.8–219.5 kPa); Vermeer et al. (2002); the Phase 0 GPU face | Worked example and analytical bracket, no field data. Factors and deviations checked against DAUB; seepage only arises below groundwater pressure (not in closed mode) |
| EPB chamber and screw | Analytical limits (Boyle, stiffness), behaviour checks | Not checked against field data. Screw efficiency and decay length are illustrative |
| Slurry shield (Mixshield) | DAUB section 8.1 worked example (within 0.002 m) | Worked example only. Air-cushion dynamics are this project's derivation |
| Segment lining | ITA 2000 Design Example 1 | Worked example only |
| Ground scenarios | Interpolation between real BGS boreholes; unit tests | Inputs are real. No geological model between the boreholes |

### Ground physics on the GPU (Phase 2, MPM)

| Check | Data | Result | Kind | Page |
|---|---|---|---|---|
| Rankine active wall, sand (friction mapping) | Rankine theory | Within −6 % to +6 % for φ′ ≤ 34° | Calibrated: μ = sin φ′ chosen from this test | [element tests](mpm-element-tests.md) |
| Granular column collapse | Rousseau et al. (2022), CC BY | 7 of 8 runouts within ±17 % (G10 58 % long) | Independent | [element tests](mpm-element-tests.md) |
| Dilatancy mapping | Newton's flow rule (derived) | ψ within 0.5° | Independent | [element tests](mpm-element-tests.md) |
| At-rest stress K0 | 1 − sin φ′ | 0.74–0.86 for any target | Failed: the analytical value is used | [element tests](mpm-element-tests.md) |
| Face pressure, dry sand | Idinger et al. (2011), centrifuge | Measured 4.5–6.0 kPa lies inside the MPM bracket 4.0–8.7 kPa at C/D 1, at every cover | Bracket: no single soil match fits pressure, wedge and settlement | [face sand](mpm-face-sand.md) |
| Face pressure, dry sand | Wang et al. (2024) / Liu et al. | 0.93–1.22 at D/10; 1.17–1.55 at D/20 | Independent: matches at D/10 only | [face sand](mpm-face-sand.md) |
| Face mechanism and settlement | Idinger et al. (2011) | Wedge 10–14° too flat; settlement 1.1–3× with Bolton dilation | Failed | [face sand](mpm-face-sand.md) |
| Clay tunnel stability ratio | Kimura & Mair (1981) | About 0.5× the measured N | Blocked: numerical volume loss in yielding material ([newton#5180](https://github.com/newton-physics/newton/issues/5180)) | [clay](mpm-clay.md) |
| EPB chamber pressure and gradient | Bezuijen et al. (2005), Botlek | Pressure collapses under cutterhead rotation (P0); the P1d element locks | Blocked: same cause | [chamber](mpm-chamber.md) |

## What is still assumed or unchecked

Each demo's realism checklist ([EPB](../realism/epb-slice-a.md), [Mixshield](../realism/slurry-mixshield.md), [gripper](../realism/hard-rock-gripper.md), [double shield](../realism/hard-rock-double-shield.md), [drill & blast](../realism/drill-blast-heading.md), [SEM](../realism/sem-heading.md)) lists its assumed values in full. No rule in any checklist is "not met". Every demo is "partly met" on rule 5, "every number in a cited range".

### Ranked gaps

Ranked by how much each changes what a user sees, then by whether open data could close it.

| # | Gap | Demos | Effect | Open data to close it |
|---|---|---|---|---|
| 1 | Volume loss is a scenario input; it doesn't respond to face pressure or grouting. **Partly closed 6 Nov 2026:** in London Clay (half the EPB drive) it now rises with the face's load factor (Macklin 1999); at normal pressure it equals the measured value. Still open: grouting, other ground, the Mixshield in Chalk | EPB, Mixshield | Settlement doesn't change with the operator's actions outside London Clay | Needs paired face pressure and volume loss: none found under CC BY |
| 2 | Downtime distributions come from one 6.88 m EPB (Tabriz); no learning curve, day-to-day correlation, locomotive travel or slurry-plant stops | EPB, Mixshield | Best days too low; Mixshield working day 7–58 % fast; whole drive 2× fast | Crossrail and Thames delay breakdowns are not published; look for other open drive logs |
| 3 | Torque in foam-conditioned clay 2.7× over | EPB | Torque bar over-reads in clay | Sofia gives the target; needs face and chamber friction for conditioned soil |
| 4 | CSM penetration fitted to one project (Follo gneiss); doesn't follow section strength | Gripper, double shield | Penetration in other rocks is untested | An open TBM dataset in other rock types (Yinsong is not open) |
| 5 | Chamber model (screw efficiency, decay length, paste weight) unchecked; the GPU chamber is blocked | EPB | Chamber pressure dynamics illustrative | Botlek gradients (Bezuijen 2005) are now in hand; needs the MPM fix or an analytical gradient model |
| 6 | ~~Face support: DAUB factors unverified; no seepage forces~~ Closed 6 Nov 2026: factors and deviations checked against DAUB (2016), example 8.1 reproduced; seepage arises only below the groundwater pressure. The Mixshield's operating range is as narrow as 36 kPa in places | EPB, Mixshield | – | – |
| 7 | Gripper force, stroke and ring-build time for a 10 m double shield are not published | Double shield | Cycle times assumed | Manufacturer or thesis data |
| 8 | Drill & blast specific charge (1.8 kg/m³), charging time per hole and support-work overlap | Drill & blast | Round time and peak weeks | Norwegian theses (NTNU) with logged rounds |
| 9 | SEM: Sulem time law from one claystone site; sand-lens position illustrative; the whole-ring term transferred | SEM | Convergence history is illustrative | A convergence time series in comparable ground |
| 10 | Building damage uses greenfield strain only. **Partly addressed 6 Nov 2026:** the greenfield and stiffness-modified deflection ratio are shown per building (Potts & Addenbrooke via Mair 1997, digitised; EI assumed); the category still uses greenfield horizontal strain | EPB, Mixshield | Damage categories conservative | Relative-stiffness factors of Potts & Addenbrooke (1997). Searched 6 Nov 2026: the method and the deflection-ratio chart are in Mair (1997, [ISSMGE library](https://www.issmge.org/uploads/publications/1/31/1997_04_0052.pdf)), scanned; the horizontal-strain curves the demos need (M vs α*) were not found in any open source |

### Calibrated parameters and where they are tested

A calibrated parameter is trustworthy only once data it was not fitted on confirm it.

| Parameter | Fitted on | Tested independently on |
|---|---|---|
| Shield friction 0.17, rim 0.07 | Changsha, 281 rings | Mashhad and Sofia: thrust yes; torque at Mashhad 1.3 bar yes, Sofia no |
| CSM ψ = −0.1 | Follo 4.5 km mean | Follo sections: not followed; no other project |
| Thames volume loss 0.25 %, K 0.5 | 17 Thames sections | Nothing independent yet |
| Second-bore ratio 1.7, Ky 0.44 → 0.33 | Hyde Park | Thames ratios 1.0–2.5 (median 1.2): consistent, not a test |
| Ulvin mucking rate and downtime share | Ulvin | T10.5 contractor estimate: inside the range |
| Norwegian contour spacing 0.47 m, burden 0.75 B | Published T10.5 hole counts | Nothing else |
| MPM friction mapping μ = sin φ′ | Rankine wall | Column collapse (yes); face pressure (bracket only) |

## Keeping this page right

- **When a validation page changes,** update its row here and the summary line for that demo.
- **When a demo gets a new check,** add it with its kind. "Calibrated" needs the name of the data it was fitted on.
- **The landing-page cards** quote the strongest check per demo. They must agree with this page.
