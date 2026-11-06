# Realism checklist: SEM / NATM heading, Slice D

- **Demo:** [`web/sem/`](../../web/sem/). It opens on the Farringdon platform tunnel; `?ground=rock` gives the illustrative weak-rock heading.
- **Class preset:** `sem-stiff-soil` in [machine-classes.json](../../models/presets/machine-classes.json)
- **Method card:** [SEM / NATM](../research/methods-reference.md#overview)
- **Rules:** [ROADMAP realism rules](../ROADMAP.md#realism-rules-apply-to-every-phase)
- **Models:** [ground response](../MODELS.md#ground-response-and-squeezing), [SEM](../MODELS.md#sem--natm-sprayed-concrete-lining)
- **Validation:** [measured convergence and crown settlement](../validation/sem-convergence.md)

Reviewed 5 Nov 2026. Status: ✅ meets the rule · ⚠️ partly, gap listed · ❌ not yet. Format: [template](TEMPLATE.md).

Sources for Farringdon (Crossrail Learning Legacy, read and cited, not redistributed):

- **GRM:** [Geotechnical risk management for SCL tunnels in Farringdon](https://learninglegacy.crossrail.co.uk/documents/geotechnical-risk-management-for-sprayed-concrete-lining-tunnels-in-farringdon-crossrail-station/) (Gakis et al. 2014).
- **SAND:** [Tunnelling in sand in Farringdon Crossrail Station](https://learninglegacy.crossrail.co.uk/documents/tunnelling-sand-farringdon-crossrail-station/).
- **DES:** [Farringdon Station SCL design](https://learninglegacy.crossrail.co.uk/documents/farringdon-station-scl-design-reducing-risk-at-the-heart-of-crossrail/).
- **VAL:** [Delivering value through innovation and best practice](https://learninglegacy.crossrail.co.uk/documents/crossrail-farringdon-station-scl-tunnels-delivering-value-through-innovation-and-best-practice/).
- **TEMP:** [Temporary SCL tunnels in Farringdon](https://learninglegacy.crossrail.co.uk/documents/temporary-sprayed-concrete-lining-tunnels-farringdon-crossrail-station/).
- **WCH:** [Analyses of convergence and utilisation of SCL-tunnels during excavation](https://learninglegacy.crossrail.co.uk/documents/analyses-convergence-utilisation-scl-tunnels-excavation/) (Stärk et al., Whitechapel).
- **CG:** [Tunnel deformations caused by compensation grouting](https://learninglegacy.crossrail.co.uk/documents/tunnel-deformations-caused-compensation-grouting-crossrail-farringdon-station/) (Gakis, Grau & Schwind 2016).
- **SG:** [Stepney Green SCL caverns](https://learninglegacy.crossrail.co.uk/documents/design-and-construction-of-crossrail-stepney-green-sprayed-concrete-lined-caverns/), for the cycle times.

## Farringdon platform tunnel (default)

| # | Rule | Status | Evidence | Known gaps |
|---|---|---|---|---|
| 1 | One method, one machine class, one ground | ✅ | SEM enlargement of a 6.2 m TBM pilot to an 11 m platform tunnel (11.4 × 10.6 m) [GRM, TEMP]. The ground comes from the Farringdon – Liverpool Street scenario (BGS boreholes F32R, F6, F14), one zone per 10 m: mostly Lambeth Group at the axis, London Clay coming in at the east end, about 31 m to the axis (about 30 m below street level [DES]). Strength and stiffness are Crossrail's undrained design lines [TEMP Table 1, CG Table 2]. | The section is a circle of radius 5.5 m. The clay at the axis sets the strength, even where the scenario puts Thanet Sand in the invert. Farringdon itself had about 83 % Lambeth Group, 15 % London Clay and 2 % Thanet Sand [GRM]. |
| 2 | Right support and lining for the method | ✅ | 400 mm steel-fibre sprayed concrete on a 75 mm sealing layer, no lattice girders [CG Fig. 5, DES, SAND, TEMP, VAL]. In the sand lens: wellpoints, the face in 3–4 pockets, 4 m grouted spiles every second top heading [SAND]. The pilot tunnel is drawn ahead of the face. | The pilot is drawn on the axis; its position in the section is schematic. Pilot segments, the waterproofing membrane and the cast secondary lining are not drawn. |
| 3 | Right layout and muck path | ✅ | Top heading in 2 × 1 m rounds, bench 2 m, invert 2 m, faces staggered [TEMP]. The ring closes 6.5–8.5 m behind the face (Farringdon: 5–10 m [CG]). Prisms every 10 m [CG]. | One tunnel. The 15 m minimum between closed rings of neighbouring tunnels [VAL] is not modelled. |
| 4 | Right cycle and utilisation | ⚠️ | Excavation and spraying times per metre are from Stepney Green [SG]. Further time per metre keeps the heading at the published 1.1 m/day for the platform enlargements, and 0.5 m/day in sand-lens zones [VAL]. It covers pilot segment removal, survey, sealing, face pockets and depressurisation. | That further time is not itemised in the sources, and the spile drilling time (4 h) is assumed. |
| 5 | Every number in a cited range | ⚠️ | The ground response is undrained (Tresca), with K0 0.6 for deformation and 1.2 for lining load, as in Crossrail's design [TEMP]. Predicted crown settlement is about 10.5–11 mm in the Lambeth Group (ring closed 7.5 m back): the ring movement times the Kirsch crown factor, plus 2.5 mm settlement of the whole ring measured at Whitechapel [WCH]. It is shown beside the measured 10.3–16.5 mm (mean 13.6 mm outside grouting) [CG Table 1] and Crossrail's 10 mm FE [CG Table 4]. Stability ratio σv/cu about 1.7–1.9 (Broms & Bennermark: limit about 6). Lining load about 0.19 MPa, safety about 13. | The prediction is in the measured range but below its mean by about 1.2–1.3× ([validation](../validation/sem-convergence.md#farringdon-platform-tunnels-undrained-ground-london-clays)). The whole-ring term is transferred from Whitechapel, not computed. The sand lens has the length, thickness, pressure and treatment of Lens B under PTE [SAND], but its position is illustrative. The scenario's pore pressure at the axis (0 kPa in the drawn-down Lambeth Group) is shown beside the published 100–150 kPa [DES]. |
| 6 | Honest labels | ✅ | "Analytical (browser)" badge. The Model limits panel states the circle, the crown factor, the missing pilot, the transferred whole-ring settlement, the closure assumption, where the prediction sits in the measured range, the lens position and the calibrated time per metre. Every Farringdon number in the console names its source. | — |

## Weak rock with a fault zone (`?ground=rock`)

| # | Rule | Status | Evidence | Known gaps |
|---|---|---|---|---|
| 1 | One method, one machine class, one ground | ✅ | SEM/NATM 10 m heading in weak rock under 100 m of cover: moderately jointed siltstone and a 40 m crushed fault zone. FHWA Table 9-1 rock classes "moderately jointed" and "crushed / squeezing". | Geology is illustrative. The horseshoe section is treated as a 5 m-radius circle for the ground response. |
| 2 | Right support and lining for the method | ✅ | **Siltstone:** 200 mm shotcrete with lattice girders. **Fault zone:** 350 mm with girders, a temporary top-heading invert (Fort Canning practice), and pipe canopies of 40 pipes, 12.5 m long, advancing 9 m per umbrella (Fort Canning). Girder spacing 1 m. Linings are within FHWA's ranges (150–200 mm and 300–400 mm). | Mesh layers and the waterproofing membrane are not drawn. The final cast-in-place lining is only signalled (rate < 1 mm/month), not built. |
| 3 | Right layout and muck path | ✅ | Stepped face: top heading, bench 24–34 m behind in siltstone; bench, invert and ring closure within one diameter in the fault zone (FHWA Table 9-2 rule applied to the squeezing class). Excavator at the face, shotcrete robot, monitoring targets (5 per section, every 10 m). | Equipment is schematic; no muck haulage is shown. |
| 4 | Right cycle and utilisation | ✅ | One crew works the face the rules call for: canopy when due, ring closure first in the fault zone, bench when it lags too far, otherwise the top heading. Time per metre from Crossrail Stepney Green (top heading 1.75 h/m, bench 1.33 h/m, invert 1.68 h/m); canopy about 20 h (Fort Canning: about 2 working days). Advance about 13 m/day of top heading in siltstone and about 3 m/day in the fault zone. | Crossrail times are from London Clay, not rock. There are no breaks, maintenance or logistics delays. |
| 5 | Every number in a cited range | ⚠️ | Shotcrete stiffness and strength gain (Oreste 2003, Kielder and example parameters; checked against Brenner measurements). Early-strength class from EN 14487 lines. Lining load and safety from Oreste's method: about 0.3 MPa and safety 4.3 in siltstone; 1.6 MPa and safety 1.45 in the fault zone. Convergence triggers at 75 / 105 / 150 % of prediction (Crossrail). | Sulem's time parameters come from one claystone site. The ±20 % scatter between sections and the 1.5× convergence without ring closure are illustrative, not published values. |
| 6 | Honest labels | ✅ | "Analytical (browser)" badge; the Model limits panel states the circular idealisation, the closed-ring assumption in siltstone, the Sulem parameters and scatter, and the source of the cycle times. | — |

## Before the next publish

- [x] Real ground: the Farringdon platform tunnels on the Farringdon – Liverpool Street scenario, with Crossrail's undrained design lines.
- [x] Predicted crown settlement checked against the measured Farringdon platform tunnels ([validation](../validation/sem-convergence.md#farringdon-platform-tunnels-undrained-ground-london-clays)).
- [ ] The open top heading before ring closure (gravity, arch settlement) and consolidation after the face: the two main reasons the prediction is low.
- [ ] Rock-specific SEM cycle times from a primary source.
- [x] Ground-response magnitudes checked against 14 monitored sections in weak flysch ([validation](../validation/sem-convergence.md)). The readings are reproduced within the installed support capacity.
- [ ] Convergence time parameters from a site in comparable rock. The Albanian data have one reading per section, not a time series.
- [ ] The final cast-in-place lining stage, with its formwork traveller and waterproofing membrane.
