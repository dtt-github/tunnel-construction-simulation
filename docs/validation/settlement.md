# Settlement trough against measured Crossrail settlement

- **Script:** [`models/py/validation/settlement_open_data.py`](../../models/py/validation/settlement_open_data.py). It prints the table below.
- **Model:** [settlement and building damage](../MODELS.md#settlement-and-building-damage). The Gaussian trough (Peck; O'Reilly & New) gives Smax = 0.313 VL D² / i, with i = K z0.
- **Run on:** 5 Nov 2026

## Data

The numbers below are quoted from the documents' tables. The documents themselves are read and cited, not redistributed.

| Site | What was measured | Source |
|---|---|---|
| Hyde Park greenfield site, Crossrail western running tunnels | 7.1 m EPBs in London Clay, axis about 34.5 m. First bore, X-line: VL 0.78 %, Ky 0.44, Smax 8.3 mm; one fit for all lines Ky = 0.43; about 30 % of the final settlement above the cutterhead. Second bore (Table 2, Fig. 13), 16.2 m from the first (read from the dashed "TBM1 axis position" line in the vector figure): incremental VL 1.18 / 0.82 / 0.82 % against 0.78 / 0.44 / 0.48 % for the first bore on the same three lines; Ky 0.42–0.47 towards the first bore, 0.29–0.43 away from it | Wan, Standing, Potts & Burland (2017), *Géotechnique* 67(5):420–445, [doi:10.1680/jgeot.16.P.099](https://doi.org/10.1680/jgeot.16.P.099), Tables 1–2, Figs 10, 13, 15 ([open copy on Spiral](https://spiral.imperial.ac.uk/entities/publication/bd6c2271-92c0-42b6-b16a-3d26994562c7)) |
| Crossrail Thames Tunnel C310, Plumstead – Woolwich | 7.12 m Mixshields in Seaford Chalk, Thanet Sand and river gravel. 17 twin-bore sections: depth, distance between the two tunnels (10–37 m), Smax 3–10 mm, back-analysed VL in two columns, "WB" (0.10–0.25 %) and "WB & EB" (0.10–0.35 %), with K fixed at 0.5. The paper defines neither column nor the distance. Crossrail designed for 1 % (0.5 % in controlled zones) | Cheng & Mikulski (2014), [Crossrail Learning Legacy](https://learninglegacy.crossrail.co.uk/documents/ground-settlement-behaviour-in-chalk-due-to-tbm-excavations/), Table 1 |
| Crossrail western drive, Paddington – Farringdon | VL "generally lower (<0.5 %)"; damage assessments assumed 1 % for TBMs | Lazarus & Jung (2018), *The Structural Engineer* 96(7), [PDF](https://www.istructe.org/IStructE/media/Public/TSE-Archive/2018/e31e8e27-9eb1-4a67-b0d8-59d82a878be2.pdf) |

No greenfield volume loss or trough width is published for Farringdon – Liverpool Street. The open close-out report for the Barbican – Moorgate Underground line records 2–5 mm per TBM passage on the Metropolitan line above, "well below the predicted values". That is asset data, from which a volume loss cannot be back-fitted.

## Hyde Park: reproduced

From VL 0.78 % and K 0.44 at 34.5 m, the model gives Smax = 8.1 mm. The measured value is 8.3 mm.

## Thames chalk: how the table is read

The first version of this page took "WB & EB" as the volume loss of both bores together, and the second bore as the difference. With that reading the published values gave Smax 1.1–3.1× smaller than measured (median 1.6×). Reading "WB & EB" as the second bore's own volume loss reproduces the measured Smax with no fitting:

| Second-bore VL | Distance between tunnels | Measured / predicted Smax: median | Range | RMS of ln |
|---|---|---|---|---|
| WB & EB minus WB | centre to centre | 1.57 | 1.07–3.14 | 0.63 |
| WB & EB minus WB | clear gap (+ D) | 1.68 | 1.07–3.14 | 0.66 |
| **the WB & EB value** | **centre to centre** | **1.10** | 0.80–2.38 | 0.44 |
| the WB & EB value | clear gap (+ D) | 1.31 | 1.01–2.99 | 0.53 |

The demos use this reading, because it is the one under which the paper's own numbers agree with its own measurements. The paper does not state it, though.

With it, the first-bore volume loss that reproduces each measured Smax (keeping the published ratio between the bores) has a median of **0.25 %** (range 0.10–0.54 %). The published second-bore VL is 1.0–2.5× the first (median **1.2**). The distance between the tunnels has a median of **17 m**. The paper notes clear interaction between the bores up to about 3 D apart and none beyond 4.5 D.

## Hyde Park: the second bore

| Line | First bore VL (%) | Second bore VL, incremental (%) | Ratio | Ky towards the first bore | Ky away from it |
|---|---|---|---|---|---|
| X (greenfield) | 0.78 | 1.18 | 1.51 | 0.467 | 0.38 (0.33–0.435) |
| Y | 0.44 | 0.82 | 1.86 | 0.419 | 0.314 |
| Extensometer | 0.48 | 0.82 | 1.71 | 0.435 | 0.292 |

- **The second bore loses more ground:** 1.5–1.9× the first (median 1.7). The paper puts this down to the ground on that side having been disturbed and softened by the first drive.
- **Its trough is asymmetric:** wider towards the first bore (Ky about 0.44) and narrower away from it (about 0.33).
- **Spacing:** the two bores are 16.2 m apart, about 2.3 D.
- **In the model:** `twin_troughs` takes these as `second_vl_factor`, `second_inner_k` and `second_outer_k`. The volume of each trough is kept, so the asymmetric trough's peak is set by the two half-widths.

## Defaults in the demos

Each scenario file carries its settlement defaults, with their sources.

| Scenario | Volume loss | K | Basis |
|---|---|---|---|
| Thames crossing (Mixshield) | 0.25 % | 0.5 | The median first-bore VL that reproduces the 17 measured Smax values (3–10 mm), with the second bore at its published ratio. K as in the Crossrail back-analysis. There is no data under the river. |
| Farringdon – Liverpool Street (EPB) | 0.5 % | 0.43 | Transferred from Hyde Park (first bore 0.44–0.78 %, Ky 0.43 for deep tunnels) and from the western drive ("generally below 0.5 %"). These are not measured on this stretch. |

**Second bore** (scenario `settlement.second_bore`). The demos show it with "Second bore: after both drives". All troughs are then final.

| Scenario | Distance | VL ratio | K towards / away from the first bore | Basis |
|---|---|---|---|---|
| Thames crossing | 17 m | 1.2 | 0.5 / 0.5 | Thames table medians. Final Smax of both bores about 6.5 mm at the demo's start, against 3–10 mm measured. |
| Farringdon – Liverpool Street | 16.2 m | 1.7 | 0.44 / 0.33 | Hyde Park, transferred. The spacing on this stretch is not published. |

In both scenarios the side of the second bore is assumed.

The volume-loss slider still covers the published range (0.1–2 %), including Crossrail's design value of 1 %.

## Limits

- The second bore is driven "later" as a final trough only; the demos do not animate it. Its spacing and side are assumed on both routes, and the Thames reading of the table is inferred, not stated.
- The building check uses the greenfield trough and the horizontal strain under each footprint. Building stiffness and the deflection ratio are not modelled.
- OS OpenMap Local merges terraces into blocks. A block's strain is the largest along its width at its centroid chainage.
