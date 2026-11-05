# Mixshield ring cycle and advance against the Thames Tunnel

- **Script:** [`models/py/validation/slurry_thames_advance.py`](../../models/py/validation/slurry_thames_advance.py). It prints the tables below.
- **Model:** [utilisation and downtime](../MODELS.md#utilisation-and-downtime), `simulate_drive`, as for the [EPB check](epb-crossrail-advance.md).
- **Demo:** the [urban slurry shield](../../web/slurry/) on the Crossrail Thames Tunnel, Plumstead – North Woolwich: the same drive.
- **Run on:** 5 Nov 2026

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

## Limits

- The downtime distributions come from an EPB; separation-plant stops are not modelled (roadmap Slice C).
- Push time per ring is not published, so the advance speed stays a user setting (default 60 mm/min).
- 90-day forecasts do not include the river crossing, station boxes or cross passages.
