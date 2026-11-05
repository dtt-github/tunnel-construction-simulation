# Hard-rock TBMs against published project rates

- **Script:** [`models/py/validation/hard_rock_projects.py`](../../models/py/validation/hard_rock_projects.py). It prints the tables below.
- **Models:** [CSM disc cutter](../MODELS.md#csm-disc-cutter) (penetration from thrust) and [hard-rock drive](../MODELS.md#hard-rock-drive) (Farrokh 2018 downtime per km).
- **Demos:** the [gripper and double shield](../../web/hard-rock/).
- **Run on:** 5 Nov 2026

## Data

The documents are read and cited, not redistributed. Only their numbers are quoted.

| Project | What is published | Source | Open |
|---|---|---|---|
| Follo Line TBM1, 9.96 m Herrenknecht double shield | 71 × 19″ discs, 4,550 kW, 11,115 kNm, 25,565 kN maximum thrust including 3,200 kN shield drag. Over 4.5 km of gneiss (weighted means): UCS 152.45 MPa, BTS 10.38 MPa, Q 21.2, quartz 39 %; 5.08 rpm, 21,217 kN gross thrust, **6.32 mm/rev, 1.92 m/h** | Hansen (2018), NTNU MSc, Tables 2.4 and 5.1, Figs 5.6–5.14, [hdl:11250/2503069](https://hdl.handle.net/11250/2503069) | yes |
| Follo Line, northbound machines to August 2018 | Including probing and pre-grouting: average day **14.1 m** (best 31), week 85 m (144), month 364 m (568) | Iddeng (2019), NTNU MSc, Table 3.3, after Kalager & Gammelsæter (2019, WTC), [NVA](https://nva.sikt.no/registration/0198e6b19388-e58a5658-5843-49c9-8b5e-13171b80cf86) | yes |
| Follo Line, per machine | About 4,200 cutter changes over about 9.5 km (about 442 per km); best day 36 m, best week over 158 m | [Herrenknecht reference](https://herrenknecht.com/en/references/referencesdetail/follo-line) | yes |
| Gotthard Base Tunnel, gripper TBMs 9.43 / 9.58 m | 3,500 kW, 8,526 kNm; best day 56 m | [Herrenknecht reference](https://www.herrenknecht.com/en/references/referencesdetail/gotthard-base-tunnel/) | yes |
| Gotthard, the same machines | 58 discs at 26 t each; one gripper stroke gives 2 m; June 2010 average about 8.1 m/day | Baublatt, "410 Meter lang und gefrässig", on the [AlpTransit portal](https://www.alptransit-portal.ch) (Swiss Federal Archives, milestone Pin_039) | yes |
| Gotthard S-210, 9.33 m gripper | 5,290 kNm, 27,488 kN, 3,500 kW; 13,427 m in 1,405 days (9.6 m/day); best day 38 m, best week 183.6 m | [Tunnels & Tunnelling, Oct 2006](https://tunnelsandtunnelling.com/?p=5739) | yes |
| Guadarrama, 9.5 m double shields | 16–20 m/day per drive; best day 64 m, best month 980 m; 1.6 m rings of 7 segments | Tunnelbuilder (18 Mar 2004), trade press | yes |
| Brenner, Aicha – Mauls exploratory double shield 6.3 m | About 16 m/day net | Michael et al. (2011), IS-Rome, p. 263, [PDF](https://www.issmge.org/uploads/publications/6/13/2011_030.pdf) | yes |
| Brenner, Mules main-tunnel double shields 10.65 m | 14.4 and 15.9 mm/rev at 2.6–2.75 rpm over 500 m of calcschist; typical 15 m/day, record month 860 m | Maggio (2020), PoliTo MSc, pp. 98–113, [PDF](https://webthesis.biblio.polito.it/15216/1/tesi.pdf); BBT SE newsroom (March 2021) | yes |
| Niagara, 14.4 m Robbins main beam | UCS mostly 40–100 MPa; 18 m/day by April 2007; with spiling about 3 m/day (maximum 5) over about 500 m; overbreak up to 3 m | Robbins (2010), WTC, [PDF](https://www.robbinstbm.com/wp-content/uploads/2010/07/Large-Diameter-TBMs_WTC2010.pdf), §2 | yes |

**Not found in any open source:** utilisation (boring time over total time) or a downtime breakdown for any of these projects; regrip and ring-build times; Follo segment thickness. An NTNU thesis analysing Follo utilisation (Andreev 2017) is embargoed.

## Penetration: Follo TBM1

The CSM model predicts penetration from the net thrust on the cutters (gross 21,217 kN less 3,200 kN shield drag, as Hansen defines it). The cutter spacing is taken as the cutterhead radius divided by the number of discs (Bruland's average spacing, 70 mm here).

| ψ | Predicted (mm/rev) | Measured (mm/rev) | Predicted / measured |
|---|---|---|---|
| +0.1 | 11.77 | 6.32 | 1.86 |
| 0.0 | 8.78 | 6.32 | 1.39 |
| −0.1 | 6.36 | 6.32 | 1.01 |

- **Before:** the default ψ = 0.1 over-predicted Follo by 1.9×. That value was a typical one for sharp discs, not a fit to anything.
- **Now:** ψ is the pressure-distribution exponent, which Rostami gives as −0.2 to +0.2. ψ = −0.1 reproduces the 4.5 km mean, so it is now the default.
- **One project only:** this is one tunnel in strong gneiss. Hansen's own CSM run, with inputs not stated in the thesis, was 8.9 % high.

## Advance: Follo

The downtime model is fed the measured net penetration rate (1.92 m/h) and Follo's cutter changes (442 per km at Farrokh's 66 min each). Rock support is from RMR 71, using RMR = 9 ln Q + 44 with Q 21.2.

| Regrip (min) | Organisation | Haulage | Utilisation (%) | Advance (m/day) | Measured average day (m) |
|---|---|---|---|---|---|
| 4 | good | conveyor | 32 | 14.9 | 14.1 |
| 4 | good | rail | 32 | 14.7 | 14.1 |
| 4 | normal | conveyor | 29 | 13.5 | 14.1 |
| 4 | normal | rail | 29 | 13.3 | 14.1 |
| 10 | good | conveyor | 31 | 14.4 | 14.1 |
| 10 | good | rail | 31 | 14.3 | 14.1 |
| 10 | normal | conveyor | 28 | 13.1 | 14.1 |
| 10 | normal | rail | 28 | 12.9 | 14.1 |

- **Result:** the model gives 12.9–14.9 m/day against 14.1 m/day measured.
- **Implied utilisation:** 1.92 m/h and 14.1 m/day give about 31 %. The model gives 28–32 %.
- **Cutter changes are about a third of the downtime.** The wear model (Frenzel; CAI 3.5) gives about 266 changes per km in this volume of rock; Follo changed about 442. The CAI model excludes chipping and bearing failures, so it stays a lower bound.
- **Probing and pre-grouting** are in Follo's rates; the model has them only inside its "other" term.

## Other projects

| Project | Machine | Average advance | Basis |
|---|---|---|---|
| Follo Line (northbound) | double shield 9.96 m | 14.1 m/day (best 31) | per day, including probing and grouting |
| Guadarrama | double shield 9.5 m | 16–20 m/day (best 64) | per drive, trade press |
| Brenner, Aicha – Mauls | double shield 6.3 m | about 16 m/day | net |
| Brenner, Mules main tunnels | double shield 10.65 m | about 15 m/day (record month 27.7) | BBT SE |
| Gotthard S-210 | gripper 9.33 m | 9.6 m/day (best 38) | 13,427 m in 1,405 days |
| Niagara | main beam 14.4 m | about 3 m/day with spiling; 18 m/day in better ground | Robbins 2010 |

None of these publish the rock and machine inputs needed to run the model section by section, so they bracket the demos rather than test them.

## Changes made

- **CSM default ψ:** from 0.1 to −0.1 (Follo back-analysis). The hard-rock demos now use the spacing as radius / number of discs, the definition under which ψ was fitted.
- **Double shield demo:**
  - 71 discs, as at Follo (was 60, after Brenner);
  - default thrust 18.0 MN on the cutters and 5.1 rpm, the logged Follo means.
  - In gneiss (UCS 150 MPa) it now gives 6.85 mm/rev, 15.6 m/day and 31 % utilisation, against Follo's 6.32 mm/rev, 14.1 m/day and an implied 31 %. Before: 12.6 mm/rev and about 21 m/day.
- **Gripper demo:**
  - The preset was labelled "Gotthard-class" but mixed the 9.33 m S-210 torque (5,290 kNm) into a 9.58 m machine. It now uses the Gotthard 9.58 m data: 8,526 kNm, 3,500 kW, 58 discs, 2 m stroke and 26 t per disc as the default thrust (14.75 MN). The 27.5 MN installed thrust is still the S-210 value.
  - In gneiss it gives 5.8 mm/rev and about 16 m per working day. Gotthard averaged about 8–10 m per calendar day over whole drives, including fault zones and stoppages; that is not a like-for-like comparison.
- **Presets:** the class presets and the Gotthard reference machine now carry these sources and are marked verified.

## Limits

- **Penetration** is fitted to one mean over 4.5 km of one project. Section-by-section scatter (Hansen's standard deviation is 0.87 mm/rev) is not tested.
- **Advance at Follo** used the measured penetration and cutter changes, so it tests the downtime model, not the whole chain. With the demo's own CAI wear model, cutter changes are about 40 % fewer than at Follo.
- **Fault zones:** in the fault zone (RMR 22) the demos give about 12–13 m/day, because Farrokh's support curve at that RMR is about 1,000 h/km. Niagara's 3 m/day with spiling was in a 14.4 m bore with up to 3 m of overbreak, so it is not a direct test; no open source gives a like-for-like fault-zone rate.
- **Gotthard and Niagara** publish calendar-day averages over whole drives. The model's working-day rate excludes holidays and long stoppages.
