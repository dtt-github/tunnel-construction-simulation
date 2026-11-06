# EPB ring cycle and advance against the Crossrail drives

- **Script:** [`models/py/validation/epb_crossrail_advance.py`](../../models/py/validation/epb_crossrail_advance.py). It prints the tables below.
- **Model:** [utilisation and downtime](../MODELS.md#utilisation-and-downtime), `simulate_drive`: push, ring build, general activities, maintenance, shift pattern and tool interventions, ring by ring over 90 days.
- **Demo:** the [urban EPB shield](../../web/epb/) on the Farringdon – Liverpool Street route.
- **Run on:** 5 Nov 2026

## Data

The documents are read and cited, not redistributed. Only their numbers are quoted.

| Source | What it gives | Open |
|---|---|---|
| King, Thomas & Stenning (2017), *Crossrail project: machine-driven tunnels on the Elizabeth line, London*, Proc. ICE Civil Engineering 170(CE5), [doi:10.1680/jcien.16.00028](https://doi.org/10.1680/jcien.16.00028); [free PDF](https://learninglegacy.crossrail.co.uk/wp-content/uploads/2017/04/Machine-driven-tunnels-on-the-Elizabeth-line-London.pdf) | Table 3: days, rings per day with and without delays, best day and best week for every TBM. Text: "seven segments plus a small key", 1.6 m, 300 mm, 6.2 m ID and 6.8 m OD; two 12 h shifts a day, seven days a week (the west contract: three 8 h shifts) | free to read |
| Tunnels & Tunnelling, 25 Feb 2021, ["Lord of the rings"](https://www.tunnelsandtunnelling.com/?p=9006) | Average ring build on Crossrail "around 32 minutes" (bolted segments); about 20 min on Tideway's boltless rings, fastest 12 min | yes |
| Crossrail Learning Legacy, [TBM station transits](https://learninglegacy.crossrail.co.uk/documents/tbm-station-transits/) | 7.08 m cutterhead, 12 m shield with mid-shield articulation, 120 m TBM, 6.8 m OD rings 1.6 m long | yes |
| Wan, Standing, Potts & Burland (2017), *Géotechnique* 67(5), p. 421 | About 110 m a week under Hyde Park (drive X, London Clay) | accepted copy on Spiral |

**Not found in any open source:**
- push time or advance speed per ring;
- a breakdown of the delays;
- station-transit and maintenance durations;
- the installed thrust.

## Crossrail EPB drives (Table 3, rings of 1.6 m)

| TBM | Drive | Days | Days without delays | Rings/day with delays | Rings/day without delays | Best day (rings) | Best week (rings) |
|---|---|---|---|---|---|---|---|
| Phyllis | X | 519 | 358 | 9.0 | 13.1 | 33 | 179 |
| Ada | X | 522 | 313 | 8.9 | 14.9 | 38 | 185 |
| Elizabeth | Y | 896 | 362 | 5.1 | 12.5 | 43 | 169 |
| Victoria | Y | 895 | 402 | 5.5 | 12.3 | 59 | 216 |
| Ellie | Z | 127 | 94 | 13.9 | 18.7 | 45 | 186 |
| Jessica | Z | 172 | 99 | 9.8 | 17.0 | 30 | 127 |
| Ellie | G | 69 | 39 | 7.6 | 13.4 | 29 | 159 |
| Jessica | G | 42 | 33 | 12.4 | 15.7 | 27 | 159 |

- **Drives X and Y**, the long London Clay and Lambeth Group drives through central London, made 12.3–14.9 rings a day on days without delays.
- **Over the whole drive** they made 5.1–9.0 rings a day; only 40–69 % of the days were free of delays. Drive Y passed through Stepney Green, Whitechapel and Liverpool Street on its way to Farringdon.
- **Drives Z and G** were short and run by experienced crews, which the paper says made them faster.

## Changes made

| Value | Before | Now | Basis |
|---|---|---|---|
| Ring | 1.2 m, 6 segments + key (Moscow metro source) | 1.6 m, 7 segments + small key | King et al. 2017 |
| Segment geometry | 6.8 / 6.2 m, 300 mm, assumed | the same, now sourced | King et al. 2017 |
| Ring build | 35 min (Moscow) | 32 min | Crossrail average, Tunnels & Tunnelling 2021 |
| Shield length | 9.5 m, assumed | 12 m | station-transits paper |
| Shift pattern on the London route | 2 × 10 h + 4 h maintenance | 2 × 12 h, seven days, maintenance in each cycle | King et al. 2017 |

The longer shield raises the shield-friction part of the thrust. Total thrust at the start of the drive goes from about 42 to about 50 MN, close to the ≈ 52 MN of the reference machine scaled to this diameter.

## The model against Table 3

20 runs of 90 days, 1.6 m rings, 32 min build, belt conveyor:

| Shift pattern | Advance speed (mm/min) | Tool interventions | Rings/day | Best day (rings) | Best week (rings) | Utilisation |
|---|---|---|---|---|---|---|
| 2 × 12 h, maintenance in each cycle | 60 | no | 11.8 | 13 | 87 | 22 % |
| 2 × 12 h, maintenance in each cycle | 60 | yes | 9.2 | 13 | 86 | 17 % |
| 2 × 12 h, maintenance in each cycle | 80 | no | 12.5 | 14 | 92 | 17 % |
| 2 × 12 h, maintenance in each cycle | 80 | yes | 9.6 | 14 | 91 | 13 % |
| 2 × 10 h + 4 h maintenance shift | 60 | no | 14.2 | 16 | 105 | 26 % |
| 2 × 10 h + 4 h maintenance shift | 60 | yes | 10.5 | 16 | 104 | 19 % |
| 2 × 10 h + 4 h maintenance shift | 80 | no | 15.4 | 18 | 114 | 21 % |
| 2 × 10 h + 4 h maintenance shift | 80 | yes | 11.2 | 18 | 113 | 16 % |

**What this shows:**

- **The average working day matches.** With the Crossrail shift pattern and no tool interventions, the model gives 11.8–12.5 rings a day, against 12.3–14.9 on Crossrail's days without delays. In other words, the general activities and per-cycle maintenance from the Tabriz project add about the time per ring that Crossrail lost on an ordinary day.
- **The whole-drive average matches drive X, not Y.** With tool interventions, the model gives 9.2–9.6 rings a day, close to drive X's 8.9–9.0. Drive Y's 5.1–5.5 includes three station transits and a maintenance stop at Stepney Green, which the model does not have.
- **The best days are far too low:** 13–14 rings against 33–59, and about 90 rings a week against 169–216. A 33–59 ring day needs a whole cycle of 24–44 min. The model draws each ring's push, build, activities and maintenance independently, so a day averages about 12 rings and never has a run of fast rings. Crossrail's 32 min average build must have had much faster rings in it; Tideway's fastest was 12 min. The model has no day-to-day correlation, and no open source gives one.

## A second project: Barcelona Metro Line 9

**Data:** [Barcelona Line 9](https://www.mdpi.com/2071-1050/17/9/3966) (Sustainability 17(9), 3966, 2025, CC BY), 9.40 m EPBs with 1.5 m rings in deltaic ground below the water table:
- Hades TBM: 26.37 m/day (about 18 rings) over more than 8 km; Section 1D: 28.5 m/day (19 rings), both excluding stationary periods;
- best days 72 m (48 rings) and 90 m (60 rings);
- face advance speed kept within 80 mm/min;
- 77 stops of more than a day in shafts and stations, 9 hyperbaric interventions;
- the first machine took "a little over three months to reach average speed".

**The model** with 1.5 m rings, the Crossrail 32 min build (assumed; Barcelona's is not published), 2 × 12 h and no tool interventions (the script prints this):

| Advance speed | Model | Barcelona |
|---|---|---|
| 60 mm/min | 18.0 m/day (12.0 rings), best day 20 m | 26.4–28.5 m/day (18–19 rings), best day 72–90 m |
| 80 mm/min | 19.0 m/day (12.6 rings), best day 21 m | |

**What this shows:** a second, independent project where the model is too slow, about 30 % on average and 3.5–4× on the best day. Crossrail's working day matched, Barcelona's did not; Barcelona's machines are larger and its build time is unknown, so part of the gap may be the cycle, but the best-day gap repeats Crossrail's and points to the missing day-to-day variation, not a single wrong time.

## Learning curve (added 6 Nov 2026)

Barcelona's first machine needed "a little over three months to reach average speed". The drive model now has an optional learning curve: production activities (boring, ring build, general activities) run at a fraction of their steady rate that rises linearly from 0.5 to 1 over 90 days. **Only the duration has a source; the linear shape and the starting half speed are assumptions.** At 60 mm/min the first 90 days average 0.78–0.83 of the steady rate (12.1 against 14.7 m/day with 2 × 12 h; 13.2 against 16.8 with 2 × 10 h + 4 h maintenance). The EPB and Mixshield demos show this "first 90 days of a new drive" beside the steady forecast; the steady forecast and the checks above are unchanged.

## Limits

- Push time per ring is not published for Crossrail, so the advance speed stays a user setting (default 60 mm/min).
- The downtime distributions are from one 6.88 m metro EPB in Tabriz. Crossrail's delays are not broken down.
- Best day and best week are not reproduced (see above); Barcelona's best days (72–90 m) confirm this on a second project. The demo states this beside its forecast.
- The learning curve's shape and starting rate are assumed; only its length (about three months) is from a source.
- Drive X used three 8 h shifts; this pattern is not in the model.
