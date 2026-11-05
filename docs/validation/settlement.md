# Settlement trough against measured Crossrail settlement

- **Script:** [`models/py/validation/settlement_open_data.py`](../../models/py/validation/settlement_open_data.py). It prints the table below.
- **Model:** [settlement and building damage](../MODELS.md#settlement-and-building-damage). The Gaussian trough (Peck; O'Reilly & New) gives Smax = 0.313 VL D² / i, with i = K z0.
- **Run on:** 5 Nov 2026

## Data

The numbers below are quoted from the documents' tables. The documents themselves are read and cited, not redistributed.

| Site | What was measured | Source |
|---|---|---|
| Hyde Park greenfield site, Crossrail western running tunnels | 7.1 m EPBs in London Clay, axis about 34.5 m. First bore, X-line: VL 0.78 %, Ky 0.44, Smax 8.3 mm; one fit for all lines Ky = 0.43; second bore incremental VL 0.82–1.18 %; about 30 % of the final settlement above the cutterhead | Wan, Standing, Potts & Burland (2017), *Géotechnique* 67(5):420–445, [doi:10.1680/jgeot.16.P.099](https://doi.org/10.1680/jgeot.16.P.099), Tables 1–2, Figs 10, 13, 15 ([open copy on Spiral](https://spiral.imperial.ac.uk/entities/publication/bd6c2271-92c0-42b6-b16a-3d26994562c7)) |
| Crossrail Thames Tunnel C310, Plumstead – Woolwich | 7.12 m Mixshields in Seaford Chalk, Thanet Sand and river gravel. 17 twin-bore sections: depth, pillar spacing, Smax 3–10 mm, back-analysed VL 0.10–0.35 % with K fixed at 0.5. Crossrail designed for 1 % (0.5 % in controlled zones) | Cheng & Mikulski (2014), [Crossrail Learning Legacy](https://learninglegacy.crossrail.co.uk/documents/ground-settlement-behaviour-in-chalk-due-to-tbm-excavations/), Table 1 |
| Crossrail western drive, Paddington – Farringdon | VL "generally lower (<0.5 %)"; damage assessments assumed 1 % for TBMs | Lazarus & Jung (2018), *The Structural Engineer* 96(7), [PDF](https://www.istructe.org/IStructE/media/Public/TSE-Archive/2018/e31e8e27-9eb1-4a67-b0d8-59d82a878be2.pdf) |

No greenfield volume loss or trough width is published for Farringdon – Liverpool Street. The open close-out report for the Barbican – Moorgate Underground line records 2–5 mm per TBM passage on the Metropolitan line above, "well below the predicted values". That is asset data, from which a volume loss cannot be back-fitted.

## Hyde Park: reproduced

From VL 0.78 % and K 0.44 at 34.5 m, the model gives Smax = 8.1 mm. The measured value is 8.3 mm.

## Thames chalk: the published VL does not reproduce the published Smax

From each section's published volume loss (both bores superposed at the published pillar spacing, K = 0.5), the formula gives Smax that is 1.1–3.1× smaller than the measured Smax (median 1.6×). Either the troughs in the chalk were narrower than K = 0.5, or the back-analysis defined volume loss differently; the paper does not say which. The volume loss that reproduces each measured Smax with the same formula is:

| Section | Ground | Axis depth (m) | Smax measured (mm) | Smax from the published VL (mm) | Measured / formula | VL that fits, both bores (%) |
|---|---|---|---|---|---|---|
| 1 | RTD | 12.0 | 5 | 3.3 | 1.5 | 0.19 |
| 2 | RTD | 12.5 | 5 | 3.2 | 1.6 | 0.20 |
| 3 | TS/Chalk | 16.0 | 6 | 2.6 | 2.4 | 0.35 |
| 4 | Chalk | 18.0 | 6 | 2.2 | 2.7 | 0.34 |
| 5 | Chalk | 18.0 | 7 | 4.6 | 1.5 | 0.54 |
| 6 | Chalk | 18.5 | 9 | 4.3 | 2.1 | 0.63 |
| 7 | Chalk | 24.0 | 9 | 3.3 | 2.7 | 0.81 |
| 8 | Chalk | 19.6 | 4 | 2.0 | 2.0 | 0.25 |
| 9 | Chalk | 20.8 | 6 | 1.9 | 3.1 | 0.39 |
| 10 | Chalk | 21.3 | 2 | 1.9 | 1.1 | 0.13 |
| 11 | Chalk | 22.0 | 6 | 3.8 | 1.6 | 0.47 |
| 12 | Chalk | 23.0 | 5 | 2.9 | 1.7 | 0.44 |
| 13 | TS/Chalk | 18.0 | 3 | 1.9 | 1.6 | 0.20 |
| 14 | TS/Chalk | 17.0 | 5 | 3.4 | 1.5 | 0.36 |
| 15 | TS | 13.0 | 7 | 6.1 | 1.1 | 0.29 |
| 16 | RTD/TS | 13.0 | 10 | 6.4 | 1.6 | 0.55 |
| 17 | TS | 12.0 | 3 | 2.6 | 1.1 | 0.11 |

The median of the fitted values is 0.35 %, and the range is 0.11–0.81 %. The median equals the upper end of the published back-analysis, so the default below uses it either way.

## Defaults in the demos

Each scenario file carries its settlement defaults, with their sources.

| Scenario | Volume loss | K | Basis |
|---|---|---|---|
| Thames crossing (Mixshield) | 0.35 % | 0.5 | The median of the VL that reproduces the 17 measured Smax values (3–10 mm); K as in the Crossrail back-analysis. There is no data under the river. |
| Farringdon – Liverpool Street (EPB) | 0.5 % | 0.43 | Transferred from Hyde Park (first bore 0.44–0.78 %, Ky 0.43 for deep tunnels) and from the western drive ("generally below 0.5 %"). These are not measured on this stretch. |

The volume-loss slider still covers the published range (0.1–2 %), including Crossrail's design value of 1 %.

## Limits

- The demos model one bore. The second bore adds an incremental, larger volume loss (Hyde Park 0.8–1.2 %; Thames 0–0.15 % added) and an asymmetric trough.
- The building check uses the greenfield trough and the horizontal strain under each footprint. Building stiffness and the deflection ratio are not modelled.
- OS OpenMap Local merges terraces into blocks. A block's strain is the largest along its width at its centroid chainage.
