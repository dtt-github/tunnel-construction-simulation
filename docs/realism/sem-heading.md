# Realism checklist: SEM / NATM heading, Slice D

- **Demo:** [`web/sem/`](../../web/sem/)
- **Method card:** [SEM / NATM](../research/methods-reference.md#overview)
- **Rules:** [ROADMAP realism rules](../ROADMAP.md#realism-rules-apply-to-every-phase)
- **Models:** [ground response](../MODELS.md#ground-response-and-squeezing), [SEM](../MODELS.md#sem--natm-sprayed-concrete-lining)

Reviewed 4 Nov 2026. Status: ✅ meets the rule · ⚠️ partly, gap listed · ❌ not yet.

| # | Rule | Status | Evidence | Known gaps |
|---|---|---|---|---|
| 1 | One method, one class, one ground | ✅ | SEM/NATM 10 m heading in weak rock under 100 m of cover: moderately jointed siltstone and a 40 m crushed fault zone. FHWA Table 9-1 rock classes "moderately jointed" and "crushed / squeezing". | Geology is illustrative. The horseshoe section is treated as a 5 m-radius circle for the ground response. |
| 2 | Right support and lining for the method | ✅ | **Siltstone:** 200 mm shotcrete with lattice girders. **Fault zone:** 350 mm with girders, a temporary top-heading invert (Fort Canning practice), and pipe canopies of 40 pipes, 12.5 m long, advancing 9 m per umbrella (Fort Canning). Girder spacing 1 m. Linings are within FHWA's ranges (150–200 mm and 300–400 mm). | Mesh layers and the waterproofing membrane are not drawn. The final cast-in-place lining is only signalled (rate < 1 mm/month), not built. |
| 3 | Right layout | ✅ | Stepped face: top heading, bench 24–34 m behind in siltstone; bench, invert and ring closure within one diameter in the fault zone (FHWA Table 9-2 rule applied to the squeezing class). Excavator at the face, shotcrete robot, monitoring targets (5 per section, every 10 m). | Equipment is schematic; no muck haulage is shown. |
| 4 | Right cycle | ✅ | One crew works the face the rules call for: canopy when due, ring closure first in the fault zone, bench when it lags too far, otherwise the top heading. Time per metre from Crossrail Stepney Green (top heading 1.75 h/m, bench 1.33 h/m, invert 1.68 h/m); canopy about 20 h (Fort Canning: about 2 working days). Advance about 13 m/day of top heading in siltstone and about 3 m/day in the fault zone. | Crossrail times are from London Clay, not rock. There are no breaks, maintenance or logistics delays. |
| 5 | Every number in a cited range | ⚠️ | Shotcrete stiffness and strength gain (Oreste 2003, Kielder and example parameters; checked against Brenner measurements). Early-strength class from EN 14487 lines. Lining load and safety from Oreste's method: about 0.3 MPa and safety 4.3 in siltstone; 1.6 MPa and safety 1.45 in the fault zone. Convergence triggers at 75 / 105 / 150 % of prediction (Crossrail). | Sulem's time parameters come from one claystone site. The ±20 % scatter between sections and the 1.5× convergence without ring closure are illustrative, not published values. |
| 6 | Honest labels | ✅ | "Analytical (browser)" badge; the Model limits panel states the circular idealisation, the closed-ring assumption in siltstone, the Sulem parameters and scatter, and the source of the cycle times. | — |

## Before the next publish

- [ ] Rock-specific SEM cycle times from a primary source.
- [x] Ground-response magnitudes checked against 14 monitored sections in weak flysch ([validation](../validation/sem-convergence.md)). The readings are reproduced within the installed support capacity.
- [ ] Convergence time parameters from a site in comparable rock. The Albanian data have one reading per section, not a time series.
- [ ] The final cast-in-place lining stage, with its formwork traveller and waterproofing membrane.
