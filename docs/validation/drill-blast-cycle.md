# Drill & blast round cycle against Norwegian data

- **Script:** [`models/py/validation/drill_blast_cycle.py`](../../models/py/validation/drill_blast_cycle.py). It prints the tables below.
- **Model:** [drill & blast](../MODELS.md#drill--blast), `round_cycle`. Activities run one after another, then downtime is added as a share of the round, and the advance is taken over the production hours of a week.
- **Demo:** the [drill & blast road tunnel](../../web/drill-blast/), T10.5.
- **Run on:** 5 Nov 2026

## Data

The documents are read and cited, not redistributed. Only their numbers are quoted.

| Source | What it gives | Type | Open |
|---|---|---|---|
| Messelt (2013), NMBU MSc, Ulvin tunnel (E6/Dovrebanen, Veidekke), Table 4, p. 40, [hdl:11250/189202](https://hdl.handle.net/11250/189202) | 120 m² rail tunnel, 200 × 45 mm holes 5.2 m deep, three-boom XE3 C30, 105 h/week, 21 weeks. Hours per round: drilling 4.54, charging 1.99, mucking 2.90 (220.6 m³ solid/h), downtime 2.46, scaling 2.52 + 0.77, clean-up mucking 0.76, bolting 1.38, sprayed concrete 1.70; total 19.02 h; 5.09 m pull; 4.57 rounds a week | **logged** | yes |
| Furunes & Strype (2022), NTNU MSc, Table 4.3, p. 110, [hdl:11250/3020752](https://hdl.handle.net/11250/3020752) | One contractor's estimate for a T10.5 round, median (P5–P95) in minutes: drilling 120 (90–360), charging 90 (60–180), ventilation 20 (10–30), mucking 90 (75–120), scaling 90 (60–180), sprayed concrete 60, bolting 90 (60–210). Ventilation often overlaps mucking with emulsion explosives | expert estimate | yes |
| Same thesis, Table 3.2, p. 90 | Tunnelbyggetid 2021 for a 74.6 m² case (109 charged holes, 5.5 m holes, three booms, 2 m bolt spacing, 8 cm sprayed concrete every round): about 48 m/week | model | yes |
| Tunnelbyggetid guidance v2.0 (EBA, Statens vegvesen, Bane NOR, NTNU, 2024), p. 3–4, [PDF](https://www.eba.no/siteassets/dokumenter/vei-og-jernbane/tunnellbyggetid/veileder-byggetidsmodell-april-2024-ver-2.0.pdf) | Basis of 101 production hours a week, from about 30 recent projects. The capacity tables are in an Excel model that is not open | guideline | yes |
| Anderssen & Olsen (2022), NTNU MSc, Table 5-9, [hdl:11250/3013947](https://hdl.handle.net/11250/3013947) | Sprayed concrete time studies at Sollihøgda (E16, T9.5): gross 12.1, 13.1 and 8.2 m³/h | measured | yes |
| Lau (2020), NTNU MSc, Tables 11.13 and 12.16, [hdl:11250/2779502](https://hdl.handle.net/11250/2779502) | Rates back-fitted to weekly Statens vegvesen logs at Svartås and Kongsberg (T9.5): bolts 4.2–11.7 per h, sprayed concrete 3.2–6.8 m³/h. The author warns the fit is unreliable | regression on logs | yes |
| NFF Publications 14, 23 and 26 ([tunnel.no](https://tunnel.no/english-publications/)) | About 12 h per round and about 50 m/week (14); 40–80 m/week per face (23); contract standard capacities of 12 bolts/h and 6 m³/h (26) | guideline | yes |

**Not found in any open source:**
- weekly advance by support class or Q class;
- reaming and charging time per hole;
- time per bolt measured on site.

## Changes made

| Rate | Before | Now | Basis |
|---|---|---|---|
| Mucking | 200 m³/h (NFF range 190–220) | 220 m³/h | logged at Ulvin, 220.6 m³/h |
| Ventilation | 0.5 h | 20 min | contractor median for T10.5; off the critical path at Ulvin |
| Scaling | 1.0 h (assumed) | 1.5 h | contractor median for T10.5 (1–3 h); Ulvin 3.3 h at 120 m² |
| Downtime | none | 13 % of the round | logged at Ulvin, 2.46 of 19.02 h |
| Production hours | 110 h/week | 101 h/week | Tunnelbyggetid basis; Ulvin 105 h |

Bolting (12/h) and sprayed concrete (6 m³/h) stay at the NFF contract rates. The logged and measured values scatter on both sides (4–12 bolts/h; 3–13 m³/h). Drill rate, positioning, reaming and charging rates are unchanged.

## Ulvin: the model's rates on the logged round

| Activity | Logged (h/round) | Model (h/round) | Model / logged |
|---|---|---|---|
| Drilling | 4.54 | 3.98 | 0.88 |
| Charging (with connect and fire) | 1.99 | 2.50 | 1.26 |
| Mucking | 2.90 | 2.91 | 1.00 |

- **Drilling and charging** are not fitted to Ulvin: drilling is 12 % fast and charging 26 % slow. Positioning, reaming and charging time per hole stay assumptions, because no open source times them separately.
- **Downtime** was 12.9 % of the round. Ulvin also managed only 4.57 rounds a week against the 5.52 its cycle allowed, so the logged advance is 23.3 m/week.

## The demo's T10.5 round, class II, against a contractor's estimate

| Activity | Model (min) | Contractor median (min) | P5–P95 (min) |
|---|---|---|---|
| Drilling | 170 | 120 | 90–360 |
| Charging (with connect and fire) | 110 | 90 | 60–180 |
| Ventilation | 20 | 20 | 10–30 |
| Mucking | 113 | 90 | 75–120 |
| Scaling | 90 | 90 | 60–180 |
| Sprayed concrete | 86 | 60 | – |
| Bolting | 105 | 90 | 60–210 |

- **Every activity is inside the contractor's range.** Drilling, mucking and sprayed concrete sit above the median.
- **Extra time:** the model adds 18 min of survey and 107 min of downtime, which the estimate does not list.

## Weekly advance at 101 h/week

| Support class | Round (h) | Model (m/week) |
|---|---|---|
| I | 12.7 | 39 |
| II | 13.7 | 37 |
| III | 15.4 | 32 |
| IV | 22.3 | 22 |

- **Before:** class I gave 10.9 h per round and 50 m/week at 110 h.
- **Against NFF:** the round now matches NFF's "about 12 h" (12.7 h, downtime included). NFF's "about 50 m/week" implies about 120 h a week; at 120 h the model gives 46 m/week.
- **Against Tunnelbyggetid:** class II gives 37 m/week, against about 48 m/week for the Tunnelbyggetid case. That case uses 109 charged holes, against the demo's 134 (published 120–148 for 80 m² in medium to poor blastability, Jakobsen et al. 2024). It is also a model, not a log, and its downtime assumptions are not open.
- **Against Ulvin:** the logged 23 m/week was for a 120 m² profile, so it is a lower bound.

## Rates against practitioner statements and the NTNU model

Searched again on 6 Nov 2026 for a time study of charging per hole: none is open. Two brackets were found.

- **Jennemyr (2020)**, AECOM, [Tunnel Business Magazine](https://tunnelingonline.com/advancements-in-tunneling-and-underground-excavation-by-drill-blast/): a charging truck with two pumps charges 80–100 holes an hour, and an automated three-boom jumbo drills 800–1,200 ft an hour. These are practitioner statements, not measurements.
- **Kim & Lee (2021)**, [Applied Sciences 11: 10096](https://www.mdpi.com/2076-3417/11/21/10096) (CC BY), Table 6: NTNU-model times for a 77–82 m² road tunnel in five support types. Model output, not logs.

| Rate | Demo (T10.5, class II) | Source |
|---|---|---|
| Charging (holes/h) | 100 | 80–100 (Jennemyr) |
| Jumbo drilling, three booms (ft/h) | 991 | 800–1,200 (Jennemyr) |
| Charging, connecting and firing (min/round) | 110 | 88–119 (NTNU model) |
| Ventilation (min/round) | 20 | 28 (NTNU model) |
| Scaling (min/round) | 90 | 43–112 (NTNU model) |

**What this shows:**
- **Every rate is inside the brackets.** Charging at 0.6 min per hole is at the fast end of the practitioner range; at 80 holes an hour the 134 holes would take 20 min longer, about 2.5 % of the round.
- **None of it is a measurement,** so charging per hole stays an assumption, now bracketed.

## Specific charge and charged holes against current practice

**Data:** [Gjengedal & Jakobsen 2025](https://airdrive.eventsair.com/eventsairwesteuprod/production-atlanticmice-public/927385ad0d3e425bbbf6581c4573f524), Eurock 2025, Trondheim (ISBN 978-82-8208-079-8, open on the conference site). They compiled 353 logged blast rounds from four Norwegian tunnels driven in 2021–2025, with explosive weight per round from the contractors' reports to the authorities, mostly bulk emulsion. Their Fig. 5 gives each project's best-fit trend of specific charge (kg per m³ of solid rock) against cross-section A. At the T10.5 area (74.6 m²):

| Project | Trend (Fig. 5) | At 74.6 m² (kg/m³) |
|---|---|---|
| Pro. 12, rural road, poor blastability | 13.6 A^−0.35 | 3.01 |
| Pro. 13, rural road, poor blastability | 11.515 A^−0.339 | 2.67 |
| Pro. 15, rural road, good blastability | 11.63 A^−0.321 | 2.92 |
| Pro. 14, urban utility tunnel with blasting limits | 14.327 A^−0.452 | 2.04 |
| NTNU prognosis model, 48 mm holes (read from Fig. 5) | – | about 1.2–1.45 |
| **Demo, Norwegian practice pattern, textbook charging** | – | **1.81** |

**Charged holes (Fig. 4):** the logged rounds at 75–80 m² have about 125–180 charged holes; the demo's 134 is inside, as against the earlier published 126–158.

**What this shows:**
- **Hole count matches practice;** the hole pattern was fitted to published counts (see Changes made), so this is a consistency check.
- **Specific charge is about a third low** (32–40 % below the road-tunnel trends), though above the NTNU model. The authors find that current road practice uses about twice the NTNU model and suspect over-consumption of bulk emulsion.
- **Not fitted:** charging every column fully gives only 2.3 kg/m³. Matching practice would need assumptions about contour charging, stemming and waste that no open source gives hole by hole, so the design is unchanged and the demo shows the logged range beside its own value.
- **Consequence for vibration:** the vibration estimate uses the designed charge per delay, so it is likely low by a similar factor.

## Limits

- Only one logged round breakdown is open (Ulvin, 120 m², 2013). The T10.5 activity times are one contractor's estimate.
- Weekly advance by support class is not published openly, so the class IV rate (22 m/week) is untested.
- Charging time per hole is still an assumption (0.6 min per hole, two lines); no open source times it. It sits at the fast end of a practitioner's 80–100 holes an hour (Jennemyr 2020). Searched again 6 Nov 2026.
- The specific charge is about a third below logged road-tunnel practice (see above); the design is not fitted to it.
- Activities do not overlap. On site, ventilation often overlaps mucking, and charging sometimes overlaps drilling: at Ulvin by 16 min a round.
