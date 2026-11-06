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

**Not found in any open source:** utilisation or a downtime breakdown for Follo, Gotthard or Brenner; ring-build time for a 10 m double shield; gripper and auxiliary thrust for a 10 m machine; Follo segment thickness. Guadarrama's time split and double-shield cycle data from smaller machines are in [Double shield cycle](#double-shield-cycle) below. An NTNU thesis analysing Follo utilisation (Andreev 2017) is embargoed.

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

## Penetration section by section: Follo TBM1

**The Yinsong dataset is not open.** The roadmap planned this test on the Yinsong (Jilin) hard-rock TBM dataset. Its two reviews in *Underground Space* (2023) are CC BY-NC-ND. The papers that use the data give it only "on reasonable request", for example [Sci. Rep. 13:10420 (2023)](https://doi.org/10.1038/s41598-023-37306-7), which is CC BY. That paper publishes the machine (7.93 m open TBM, 56 discs, 89 mm spacing, 23,260 kN) and property ranges by rock class, but no thrust, rpm or penetration per class. So the test uses Follo instead.

**Data.** Hansen's thesis plots 18 sections of 219–316 m. Its PDF draws the charts as vector graphics, so the values can be read exactly rather than by eye:
- UCS and BTS per section (Figs 5.10–5.11). There is one laboratory test per section, and BTS is derived from UCS by Hansen's Eq. 4.9.
- The total fracturing factor (Fig. 5.2).
- The median cutter thrust, rpm and net penetration rate (box plots, Figs 5.12–5.14).

Weighted by section length, these give UCS 152.1 MPa, BTS 10.35 MPa, 301 kN/cutter, 5.11 rpm and 1.93 m/h, against Table 5.1's 152.45, 10.38, 298.83, 5.08 and 1.92.

| Section | Length (m) | UCS (MPa) | ks | Thrust (kN/cutter) | rpm | Measured (mm/rev) | Predicted (mm/rev) | Predicted / measured |
|---|---|---|---|---|---|---|---|---|
| 1 | 219 | 179 | 0.75 | 295 | 4.68 | 5.74 | 3.79 | 0.66 |
| 2 | 270 | 144 | 0.76 | 303 | 4.97 | 6.68 | 7.92 | 1.18 |
| 3 | 316 | 148 | 0.81 | 300 | 5.12 | 6.64 | 7.04 | 1.06 |
| 4 | 270 | 124 | 0.69 | 318 | 5.07 | 6.64 | 11.86 | 1.79 |
| 5 | 231 | 208 | 0.74 | 309 | 4.87 | 6.60 | 2.87 | 0.43 |
| 6 | 220 | 200 | 0.60 | 303 | 5.20 | 4.99 | 2.97 | 0.60 |
| 7 | 270 | 200 | 0.77 | 307 | 5.05 | 5.17 | 3.15 | 0.61 |
| 8 | 226 | 102 | 0.68 | 315 | 5.15 | 5.10 | 14.73 | 2.89 |
| 9 | 226 | 124 | 0.69 | 313 | 5.12 | 5.25 | 11.78 | 2.24 |
| 10 | 224 | 124 | 0.65 | 315 | 5.14 | 5.91 | 11.72 | 1.98 |
| 11 | 226 | 142 | 0.61 | 314 | 5.16 | 5.97 | 9.31 | 1.56 |
| 12 | 270 | 142 | 0.70 | 300 | 5.14 | 6.44 | 7.94 | 1.23 |
| 13 | 225 | 154 | 0.77 | 297 | 5.15 | 6.72 | 6.09 | 0.91 |
| 14 | 316 | 130 | 0.87 | 288 | 5.17 | 7.06 | 8.86 | 1.25 |
| 15 | 225 | 129 | 0.70 | 284 | 5.21 | 6.91 | 8.63 | 1.25 |
| 16 | 270 | 128 | 1.20 | 272 | 5.23 | 7.26 | 7.60 | 1.05 |
| 17 | 225 | 165 | 0.87 | 292 | 5.21 | 6.58 | 4.67 | 0.71 |
| 18 | 270 | 201 | 0.94 | 296 | 5.24 | 6.66 | 2.70 | 0.41 |

| Rock input | ψ | Weighted measured (mm/rev) | Weighted predicted (mm/rev) | RMS of ln(pred/meas) | Correlation with UCS |
|---|---|---|---|---|---|
| section UCS and BTS | −0.1 | 6.28 | 7.42 | 0.54 | −0.94 |
| section UCS and BTS | −0.15 | 6.28 | 6.48 | 0.58 | −0.93 |
| tunnel-mean UCS and BTS | −0.1 | 6.28 | 6.57 | 0.24 | +0.05 |
| tunnel-mean UCS and BTS | −0.15 | 6.28 | 5.52 | 0.26 | +0.05 |

**What this shows:**

- **The model does not follow section-to-section changes.** With each section's own UCS, predictions range from 0.41× to 2.89× the measurement. The error follows UCS almost exactly (correlation −0.94), while the measured penetration barely moves (5.0–7.3 mm/rev for UCS of 102–208 MPa).
- **The strength input is the main cause.** Each section has one lab test, and BTS is derived from UCS rather than measured. With the tunnel-mean strength and each section's own thrust and speed, the error drops to 0.24 (about ±27 %). The crew's thrust and speed, which follow the ground, carry more of the information than a single core does. That is a limit of the inputs as much as of CSM.
- **ψ depends on how it is fitted.** Fitting the length-weighted mean of the section predictions gives ψ ≈ −0.15. Fitting the tunnel means gives −0.1. Both are inside Rostami's range. The demos feed zone-average rock values, so the default stays at −0.1. A user should read CSM penetration as about ±30 % at best, and much less certain where the rock strength comes from a single test.
- **Fracturing does not explain the remaining scatter.** The CSM model has no fracturing term, and ks varies little here (0.6–1.2, mostly 0.6–0.9).

## Penetration on a second project: Queens Water Tunnel No. 3

- **Script:** [`models/py/validation/queens_csm.py`](../../models/py/validation/queens_csm.py). ψ stays at the Follo value, −0.1; nothing is refitted.
- **Rock and machine data:** Yagiz (2006), IAEG2006 paper 383 ([open PDF](https://media.geolsoc.org.uk/iaeg2006/PAPERS/IAEG_383.PDF)), Tables 2–4. It gives 10 of the 151 stations openly, each with UCS, BTS, fracture spacing, cutter load and advance rate.
- **Machine:** Khalighi & Diehl (1997), RETC ([Robbins, open PDF](https://robbinstbm.com/wp-content/uploads/2010/09/QueensWaterTunnel_RETC_1997.pdf)). A 7.06 m open TBM with 50 × 19″ discs rated at 311 kN, turning at 8.3 rpm.
- **Rock:** biotite-hornblende and granitic gneiss with amphibolite, pegmatite and schist (Khalighi & Diehl). UCS is 168–200 MPa, against Follo's 152. So this is a second project in stronger crystalline rock, **not a different rock type**.

**Reading the data:**
- **Penetration:** the column printed as "mm/rev" is in cm/rev. For example, 2.19 m/h at 8.3 rpm is 4.4 mm/rev, not 0.44. So the measured penetration here is the advance rate divided by 8.3 rpm.
- **Cutter loads** are in short tons (8.896 kN). Read as tonnes, the highest load would be above the disc rating.
- **Disc tip width and spacing** are not published. The model defaults, 19 mm and 85 mm, are assumed.

| Station (m) | UCS (MPa) | BTS (MPa) | Fracture spacing (m) | Cutter load (kN) | Measured (mm/rev) | Model, ψ −0.1 (mm/rev) | Ratio |
|---|---|---|---|---|---|---|---|
| 269 | 200 | 9.3 | 0.8 | 267 | 4.40 | 3.94 | 0.90 |
| 280 | 199 | 9.3 | 1.6 | 267 | 4.26 | 3.98 | 0.93 |
| 301 | 199 | 9.1 | >1.60 | 267 | 3.78 | 4.06 | 1.08 |
| 473 | 190 | 9.0 | 0.2 | 285 | 5.64 | 5.49 | 0.97 |
| 600 | 189 | 9.0 | >1.60 | 302 | 4.42 | 6.68 | 1.51 |
| 929 | 168 | 9.8 | 1.6 | 311 | 4.76 | 8.50 | 1.79 |
| 989 | 174 | 9.9 | >1.60 | 320 | 4.70 | 8.54 | 1.82 |
| 1021 | 178 | 10.1 | 0.4 | 258 | 5.82 | 4.14 | 0.71 |
| 1026 | 181 | 10.1 | 0.2 | 311 | 6.10 | 7.08 | 1.16 |
| 1045 | 184 | 10.2 | 0.4 | 285 | 6.16 | 5.16 | 0.84 |

**Ratio of model to measured penetration:**

| Model | Median | Range | RMS of ln ratio |
|---|---|---|---|
| ψ −0.1, as fitted at Follo | **1.02** | 0.71–1.82 | 0.33 |
| ψ 0 | 1.41 | 0.98–2.51 | 0.53 |
| ψ +0.1, the earlier default | 1.89 | 1.31–3.38 | 0.79 |
| The original CSM run printed in the source (Table 4) | 1.39 | 0.86–1.59 | 0.31 |

**What this shows:**
- **The level carries over.** On the median, the Follo ψ predicts Queens without refitting. The earlier ψ +0.1 would have been about 1.9× fast.
- **The scatter does not shrink.** Station by station, the spread (0.71–1.82×) is like Follo's section-by-section result.
- **Fractures matter, and the model has no term for them.**
  - In massive rock (fracture spacing 1.6 m or more, 5 stations), the model is a median 1.51× fast, up to 1.82×.
  - In fractured rock (0.2–0.4 m, 4 stations), it is 0.91× (0.71–1.16).
  - The CSM is an intact-rock model. Yagiz's own regression adds fracture spacing and orientation for this reason. Adding a rock-mass term would need more than 10 stations to fit and test it.
- **The sample is small.** Ten stations is a sample, not the drive. The full 151-station set is not open.

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

## Double shield cycle

- **Script:** [`models/py/validation/double_shield_cycle.py`](../../models/py/validation/double_shield_cycle.py). Nothing is fitted. One default changed: installed thrust 150 → 95 MN (see below).
- **What is checked:** the demo's assumed ring build (30 min), main stroke (equal to the 1.8 m ring), installed thrust (150 MN) and segment thickness (320 mm).

**Data** (open):
- **Comis, Younis & Goodfellow (2016)**, WTC 2016, [Robbins](https://www.robbinstbm.com/wp-content/uploads/2017/04/5_SegmentDesign_WTC2016.pdf). Table 1: main strokes of three 6.1–6.5 m double shields. The text gives the rule: stroke = segment width + 100–200 mm for a radially inserted key. Table 2, Job B (6.53 m double shield, 1.66 m rings of 4 segments): 7,990 min of ring building for 120 rings over the first 199 m, learning curve included.
- **Bheri Babai, 5.06 m Robbins double shield:** the contractor gives about 15 min per ring, in single-shield mode after boring ([NASTT, 2018](https://nastt.org/2018/08/29/robbins-double-shield-himalayas/)).
- **Maggio (2020)**, [Politecnico di Torino thesis](https://webthesis.biblio.polito.it/15216/1/tesi.pdf), Brenner Mules 2–3. Table 3.2, 10.71 m Herrenknecht double shields: 95,000 kN nominal main thrust, 450 mm segments, 1.75 m long, 6+1. Table 4.9: logged main thrust, mean 14.2 MN (281 values).
- **Alfero (2022)**, [Politecnico di Torino thesis](https://webthesis.biblio.polito.it/23141/1/tesi.pdf). Brenner exploratory double shield (6.8 m): main stroke 1.70 m for 1.5 m rings; gripper force about 37 MN.
- **Melis Maynar (2006)**, [Revista de Obras Públicas 3472](https://quickclick.es/rop/pdf/publico/2006/2006_diciembre_3472_02.pdf), Tables 5 and 7. Guadarrama's four TBMs: 439–549 m/month over whole drives, and machine time by activity to December 2004. The paper does not name the machine type or the rock; the press gives 9.5 m double shields in granite and gneiss.

**Results:**

| Item | Demo | Sources | What it means |
|---|---|---|---|
| Ring build | 30 min (assumed) | 15 min (5.06 m, stated); 67 min (6.53 m, logged, first 200 m) | In double-shield mode the ring is built while boring. At the Follo rate one 1.8 m ring takes 56 min to bore (51 min in the demo's gneiss), so anything shorter is hidden. Only the 67 min would show: 12.4 instead of 13.1 m/day in the Follo case (−5 %) |
| Main stroke | 1.80 m, equal to the ring | ring + 0.10 to +0.35 m on three of four machines (one is 0.10 m short) | The demo's stroke is the advance per regrip, one per ring, so the regrip time per km is right; a real cylinder is 0.1–0.2 m longer |
| Boring (with ring build) / all time | 28 % (Follo case) | Guadarrama 32 % | Consistent. The first independent utilisation check for the double shield |
| Disc inspection and change / all time | 26 % (Follo's own cutter changes) | Guadarrama 19 % | Follo changed more cutters per metre bored (disc time / boring 0.93 against 0.61); the rock is different |
| Installed thrust | 150 MN, now 95 MN | 95 MN main nominal (10.71 m Brenner) | Adopted: the one open figure for a 10 m double shield. Auxiliary thrust for single-shield mode is not published |
| Logged thrust | 18.0 MN on the cutters (Follo) | 14.2 MN mean main thrust (Brenner, 10.71 m) | Same order; different rock |
| Segment thickness | 320 mm (Guadarrama, press) | 450 mm (10.71 m Brenner) | Bracket: 320–450 mm for 9.5–10.7 m |

**What this shows:**
- **Ring build is not limiting** in double-shield mode for any published value up to about 50 min. The 30 min assumption only matters in single-shield mode, where boring and ring building alternate.
- **Utilisation agrees** with the one open time split for a large double-shield drive.
- **Installed thrust changed to 95 MN** (6 Nov 2026). The old 150 MN was the low end of a general range for 10 m shields (Ramoni & Anagnostou); the only open 10 m double shield has 95 MN main thrust. In the fault zone (300 m cover) the shield needs about 148 MN to keep sliding and 229 MN to restart:
  - with 150 MN the demo said "Jamming risk after any standstill";
  - with 95 MN it says "Shield jammed: skin friction 148 MN exceeds the installed thrust".
  - The auxiliary thrust that pushes in single-shield mode is not published, so this stays a screening estimate. The alarm is a warning only: the demo keeps boring through the zone.

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

- **Penetration:**
  - It is fitted to one project. Section by section, with mean rock strength, it follows the operator's thrust and speed well (±27 %), but not single-test UCS (0.4–2.9×).
  - Tested without refitting on 10 Queens Water Tunnel stations, also gneiss: median 1.02×, but up to 1.8× fast in massive rock, because there is no fracture term.
  - Rock types other than strong crystalline rock (sandstone, limestone, schist-dominated rock) are untested. The Yinsong data is not open.
- **Advance at Follo** used the measured penetration and cutter changes, so it tests the downtime model, not the whole chain. With the demo's own CAI wear model, cutter changes are about 40 % fewer than at Follo.
- **Fault zones:** in the fault zone (RMR 22) the demos give about 12–13 m/day, because Farrokh's support curve at that RMR is about 1,000 h/km. Niagara's 3 m/day with spiling was in a 14.4 m bore with up to 3 m of overbreak, so it is not a direct test; no open source gives a like-for-like fault-zone rate.
- **Gotthard and Niagara** publish calendar-day averages over whole drives. The model's working-day rate excludes holidays and long stoppages.
