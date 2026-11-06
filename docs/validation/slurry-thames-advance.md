# Mixshield ring cycle and advance against the Thames Tunnel

- **Script:** [`models/py/validation/slurry_thames_advance.py`](../../models/py/validation/slurry_thames_advance.py). It prints the tables below.
- **Model:** [utilisation and downtime](../MODELS.md#utilisation-and-downtime), `simulate_drive`, as for the [EPB check](epb-crossrail-advance.md).
- **Demo:** the [urban slurry shield](../../web/slurry/) on the Crossrail Thames Tunnel, Plumstead – North Woolwich: the same drive.
- **Run on:** 5 Nov 2026; second project added 6 Nov 2026

## Data

The documents are read and cited, not redistributed. Only their numbers are quoted.

| Source | What it gives | Open |
|---|---|---|
| King, Thomas & Stenning (2017), Proc. ICE Civil Engineering 170(CE5), [doi:10.1680/jcien.16.00028](https://doi.org/10.1680/jcien.16.00028), Table 3; [free PDF](https://learninglegacy.crossrail.co.uk/wp-content/uploads/2017/04/Machine-driven-tunnels-on-the-Elizabeth-line-London.pdf) | Drive H, two 7.12 m Mixshields: days, rings a day with and without delays, best day and week (below). Two 12 h shifts a day, seven days a week, on all contracts but the west | free to read |
| Cheng & Mikulski (2014), [Crossrail Learning Legacy](https://learninglegacy.crossrail.co.uk/documents/ground-settlement-behaviour-in-chalk-due-to-tbm-excavations/) | "6 to 7 rings per day" on the first drive and "10 rings per day" on the second, on the Plumstead – Woolwich stretch, put down to the learning curve. Only one TBM worked at a time | yes |
| Tunnels & Tunnelling (2014), [Crossrail C310](https://tunnelsandtunnelling.com/?p=7323) | Maximum advance up to 80 mm/min, with 1,600 m³/h of slurry to treat at that rate; flint 5–25 %; six filter presses | yes |
| Tunnels & Tunnelling (2021), ["Lord of the rings"](https://www.tunnelsandtunnelling.com/?p=9006) | Average ring build on Crossrail "around 32 minutes" | yes |

**Not found:**
- push time per ring for these machines;
- separation-plant or slurry-circuit stoppages;
- a breakdown of the delays.

| TBM | Days | Days without delays | Rings/day with delays | Rings/day without delays | Best day (rings) | Best week (rings) |
|---|---|---|---|---|---|---|
| Sophia (first bore) | 392 | 217 | 4.4 | 7.9 | 16 | 91 |
| Mary (second bore) | 367 | 171 | 4.6 | 10.0 | 17 | 100 |

## Changes made

| Value | Before | Now | Basis |
|---|---|---|---|
| Ring build | 35 min (Moscow, as on the EPB page) | 32 min | Crossrail average |
| Shift pattern on the Thames route | 2 × 10 h + 4 h maintenance | 2 × 12 h, seven days, maintenance in each cycle | King et al. 2017 |
| Advance speed range | 0–80 mm/min, unsourced | the same, now sourced | Tunnels & Tunnelling 2014 |

The ring (1.6 m, 7 segments + key) was already Crossrail's. The forecast panel now shows drive H beside the model.

## The model against drive H

20 runs of 90 days, 1.6 m rings, 32 min build, 2 × 12 h with maintenance in each cycle:

| Advance speed (mm/min) | Tool interventions | Rings/day | Best day (rings) | Best week (rings) | Utilisation |
|---|---|---|---|---|---|
| 40 | no | 10.7 | 12 | 78 | 30 % |
| 40 | yes | 8.4 | 12 | 77 | 23 % |
| 60 | no | 11.8 | 13 | 87 | 22 % |
| 60 | yes | 9.2 | 13 | 86 | 17 % |
| 80 | no | 12.5 | 14 | 92 | 17 % |
| 80 | yes | 9.6 | 14 | 91 | 13 % |

**What this shows:**

- **The working day is 7–58 % fast.** Without tool interventions the model gives 10.7–12.5 rings a day, against Mary's 10.0 and Sophia's 7.9 on days without delays.
  - Mary, after the learning curve, is closest: 7–18 % below the model at 40–60 mm/min.
  - Sophia's lower rate is the learning curve, as the Crossrail paper says.
  - The rest is likely slurry-specific time that the model, built on an EPB's downtime, does not have: the separation plant, pipe extensions and the slurry circuit. No open source quantifies it, so nothing has been added.
- **Best day and week are close:** 12–14 rings against 16–17, and 77–92 rings a week against 91–100. Unlike the EPB drives, the Thames drive had few very fast days.
- **The whole-drive average is about twice the model's.** Drive H made 4.4–4.6 rings a day including delays, against 8.4–9.6 for the model with tool interventions. The drive included the river crossing with planned interventions before and after it, three more interventions at cross passages and the Woolwich box. None of those is in a 90-day forecast in open ground.

## A second slurry project: Betuweroute, Sophia and PanKan tunnels

- **Script:** [`models/py/validation/slurry_betuweroute_advance.py`](../../models/py/validation/slurry_betuweroute_advance.py). Nothing is fitted to these data. The day-to-day variation is the one fitted on the Crossrail EPBs.
- **Data:** Jonker (2004), "Boortunnels in de Betuweroute", Cement 2004(1). The progress table and the segment table are open on the [article page](https://www.cementonline.nl/artikelen/boortunnels-in-de-betuweroute).
  - **Machines:** two Herrenknecht slurry shields, 8.65 m inner diameter, in Pleistocene sand. PanKan's sand has clay lenses.
  - **Sophia:** 4,240 m, 1.5 m rings, ring build 41 min, boring 38 min per ring. The machine could bore and build at once, but most of the tunnel was bored one after the other, as the model does.
  - **PanKan:** 1,640 m, 1.8 m rings, ring build 41 min, boring 52 min per ring.
  - **Tube 2 averages** are 15.2 and 14.4 m/day. Seven days a week; 40 and 16 weeks for the whole tube, so these are calendar-day averages including every stop.
  - **Best day** 36 m on both; **best week** 213 and 216 m.
  - **Tube 1 is left out:** Sophia stood about twelve weeks for cutterhead repairs, and PanKan was paced by a dam it had to pass.
- **Shift pattern:** not published for these drives. Both patterns are run. The Groene Hart slurry tunnel, in the same country and years, bored 20 hours a day, seven days a week, with 4 hours of preventive maintenance ([Rijkswaterstaat 2007](https://open.rijkswaterstaat.nl/publish/pages/125614/symposium_levensduur_en_onderhoud_van_de_groene_harttunnel.pdf), p. 6).

20 runs of 180 days, measured tube 2 in brackets, with tool interventions:

| Tunnel | Shift pattern | m/day | Ratio | Best day (m), with Crossrail day variation | Best week (m), same |
|---|---|---|---|---|---|
| Sophia | 20 h + 4 h maintenance | 12.9 (15.2) | 0.85 | 42 (36) | 197 (213) |
| Sophia | 24 h, maintenance each cycle | 11.8 (15.2) | 0.78 | 37 (36) | 180 (213) |
| PanKan | 20 h + 4 h maintenance | 14.2 (14.4) | 0.98 | 45 (36) | 215 (216) |
| PanKan | 24 h, maintenance each cycle | 13.2 (14.4) | 0.92 | 40 (36) | 193 (216) |

Without tool interventions the averages are 1.00–1.27×. Without day variation the best days are 17–21 m and the best weeks 111–134 m. The script prints every case.

**What this shows:**
- **The drive model is not slurry-blind in general.** On these two whole drives it is 0.78–0.98× with tool interventions. That is slightly slow, not 2× fast.
- **The Thames shortfall is that drive's own.** Drive H had the river crossing with planned interventions, more interventions at cross passages and the Woolwich box, and only one TBM could work at a time from the Plumstead site. None of these is in a forecast in open ground.
- **Best days and weeks match** with the Crossrail-fitted day variation: 37–45 m against 36, and 180–215 m against 213–216. Without it they are about half. This is a second independent test of that variation, after Barcelona.
  - The Mixshield demo keeps no day variation, because its route is the Thames drive, which varied less.
- **Slurry pipe extensions are not a missing stop.** They are done during ring build ([Mimura, Abe & Wada 1992](https://www.iaarc.org/publications/fulltext/Automatic_extension_%20robot_%20for_slurry_transport_pipes.PDF), ISARC), taking 57.5 min by hand per 12 m of feed and discharge line. Against a 32–41 min ring build every 1.5–1.6 m, the excess is about 2–3 min per ring, so it is left out.
- **Still not found in any open source:** separation-plant stops, pipe blockages and clogging by cause. A Colorado School of Mines thesis (Kumas 2022) simulates slurry downtime, but its repository blocked automated access and it has not been read.

## Limits

- The downtime distributions come from an EPB. Separation-plant stops are not modelled, because no open source gives them (roadmap Slice C). On two Dutch slurry drives the EPB downtime gives 0.78–0.98× the measured advance.
- Push time per ring is not published, so the advance speed stays a user setting (default 60 mm/min).
- 90-day forecasts do not include the river crossing, station boxes or cross passages.
