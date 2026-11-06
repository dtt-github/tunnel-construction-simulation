# EPB screw pressure against the Botlek screw gauges

- **Script:** [`models/py/validation/epb_botlek_screw.py`](../../models/py/validation/epb_botlek_screw.py). It prints the tables below.
- **Model:** [EPB chamber and screw conveyor](../MODELS.md#epb-chamber-and-screw-conveyor). The pressure along the screw is p(s) = f_e · p_in · exp(−s/λ): f_e is the drop at the entrance, λ the decay length.
- **Demo:** the [urban EPB](../../web/epb/) shows the screw outlet pressure on the console.
- **Run on:** 6 Nov 2026

## Data

Bezuijen, Talmon, Joustra & Grote (2005), "Pressure gradients and muck properties at the face of an EPB", Botlek Rail Tunnel ([ISSMGE library, open](https://www.issmge.org/uploads/publications/6/11/2005_023.pdf)). The document is read and cited, not redistributed.

- **Screw:** 15 m from the entrance to the valve-controlled outlet, at 23° to the horizontal, about 1 m in diameter. Gauges at 2.5, 5 and 11.5 m from the entrance (Fig. 7). The ground was mostly sand, conditioned with foam.
- **Two rings,** which the authors show as the extremes (Figs 8 and 9): Ring 318 N, with a large drop at the entrance, and Ring 814 S, with a small one.
- **Values read from the vector figures while boring** (about ±0.1 bar):

| Ring | Chamber at the screw inlet (E5) | 2.5 m | 5 m | 11.5 m |
|---|---|---|---|---|
| 318 N | 3.35 bar | 2.05 | 1.95 | 0.9 |
| 814 S | 3.1 bar | 2.6 | 2.45 | 1.75 |

- **The authors' text** says a drop "of 1 bar or more" before the entrance on most rings. They put it down to sand arching at the entrance.

## Results

| Ring | Gauge (m) | Measured (bar) | Old model: λ 3 m, no entrance drop | Model now: λ 16 m, f_e 0.85 |
|---|---|---|---|---|
| 318 N | 2.5 | 2.05 | 1.46 (0.71×) | 2.44 (1.19×) |
| 318 N | 5 | 1.95 | 0.63 (0.32×) | 2.08 (1.07×) |
| 318 N | 11.5 | 0.90 | 0.07 (0.08×) | 1.39 (1.54×) |
| 814 S | 2.5 | 2.60 | 1.35 (0.52×) | 2.25 (0.87×) |
| 814 S | 5 | 2.45 | 0.59 (0.24×) | 1.93 (0.79×) |
| 814 S | 11.5 | 1.75 | 0.07 (0.04×) | 1.28 (0.73×) |

**What this shows:**
- **The old default failed by an order of magnitude.** λ = 3 m was illustrative. It dropped the pressure to 2 % of the chamber's by 11.5 m, while Botlek still had 0.9–1.75 bar there. On the console that showed as an outlet pressure of about 0.1 bar at 3 bar in the chamber.
- **Each ring on its own:** an exponential through the 2.5 and 11.5 m gauges gives λ = 10.9 m and f_e = 0.77 for Ring 318 N, and λ = 22.7 m and f_e = 0.94 for Ring 814 S.
- **New defaults:** λ = 16 m and f_e = 0.85, between the two rings. Every gauge is now within 0.73–1.54× of both rings. The console's outlet pressure is now about 1.2 bar at the end of its 11 m screw.
- **Calibrated, not tested.** These values are set from Botlek. No other open screw pressure profile has been found to test them, so they stay labelled as calibrated.

## Limits

- **Simplified physics.** The exponential stands in for Merritt & Mair's (2008) friction model. It has no term for the muck's weight up a 23° screw (about 0.45 bar over the 9 m between the gauges), the outlet valve, or how the pressure changes with screw speed.
- **The entrance drop** varies from ring to ring with arching: about 0.5 bar for Ring 814 S, 1.3 bar for Ring 318 N, both read gauge to gauge. A constant factor can't follow that.
- **The screw's efficiency** (0.6) is still illustrative. Botlek doesn't publish the discharge.
- **One machine, in sand.** In clay or with other conditioning the profile will differ.
