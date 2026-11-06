# Realism checklist: drill & blast road tunnel, Slice E

- **Demo:** [`web/drill-blast/`](../../web/drill-blast/)
- **Class preset:** `drill-blast-road` in [machine-classes.json](../../models/presets/machine-classes.json)
- **Method card:** [drill & blast](../research/methods-reference.md#overview)
- **Rules:** [ROADMAP realism rules](../ROADMAP.md#realism-rules-apply-to-every-phase)
- **Models:** [drill & blast](../MODELS.md#drill--blast)
- **Validation:** [drill & blast cycle](../validation/drill-blast-cycle.md)

Reviewed 4 Nov 2026. Status: ✅ meets the rule · ⚠️ partly, gap listed · ❌ not yet. Format: [template](TEMPLATE.md).

| # | Rule | Status | Evidence | Known gaps |
|---|---|---|---|---|
| 1 | One method, one machine class, one ground | ✅ | Two-lane Norwegian road tunnel, profile T10.5 (74.6 m² theoretical blast area, [N500 2015](https://www.vegvesen.no/globalassets/fag/horinger/2015/2015082365-001-n500-frist-20150917/n500-vegtunneler-hoeringsutgave-26-06-2015.pdf)), in gneiss with a weakness zone and a clay-bearing fault, support classes I–IV. | The profile is drawn as walls with a semicircular roof of the same area; the real T10.5 is flatter. Geology is illustrative. |
| 2 | Right support and lining for the method | ✅ | Bolts and fibre-reinforced sprayed concrete by Norwegian road-tunnel class, with reinforced ribs of sprayed concrete (RRS) in class IV ([NFF Publication 26](https://tunnel.no/english-publications/), p. 52; [NGI Q-handbook 2025](https://prod.ngi.no/globalassets/bilder/forskning-og-radgivning/bygg-og-anlegg/q-handbook_2025_english_final.pdf)). No segments, no cast lining at the face. Half-barrels left on unsprayed walls. | No waterproofing or final inner lining (frost and water protection) is shown. Probe drilling and pre-grouting are not modelled. |
| 3 | Right layout and muck path | ✅ | Three-boom jumbo (Sandvik DT1132i class: 3 booms, 5.27 m hole on the standard feed, [spec sheet](https://gamma.rocktechnology.sandvik/globalassets/products/underground-drill-rigs-and-bolters/pdf/dt1132i-specification-sheet-eng.pdf)), charging truck with basket, scaling rig, wheel loader and 25–35 t dump trucks ([NFF Publication 14](https://tunnel.no/english-publications/), §7.5), sprayed-concrete rig, blowing ventilation duct. The crew withdraws beyond 50 m of the face to blast ([NFF Publication 27](https://tunnel.no/english-publications/)). | Equipment is schematic boxes. |
| 4 | Right cycle and utilisation | ✅ | Survey, drilling, charging, blast, ventilation (20 min), scaling (1.5 h), mucking (220 m³/h, logged at Ulvin), bolting (12 bolts/h), sprayed concrete (6 m³/h), one after another, then downtime (13 % of the round, logged at Ulvin). Class I round 12.7 h and 39 m/week at 101 h per week (Tunnelbyggetid basis), against "approximately 12 h" in NFF Publication 14. Every activity is inside a contractor's P5–P95 estimate for T10.5 ([validation](../validation/drill-blast-cycle.md)). | Charging time per hole, hole positioning, reamer time and the RRS time are assumed. Activities do not overlap, so peak weeks like the 110 m/week at E6 Nordnes are not reached. |
| 5 | Every number in a cited range | ⚠️ | Pull from the empty-hole diameter (Holmberg) and burden 30 q_b / d with Olofsson's table ([Yilmaz 2023](https://doi.org/10.1038/s41598-023-29803-6), worked example reproduced). Smooth contour 15 d ([Dyno Nobel 2010](https://www.leg.mn.gov/docs/2015/other/150681/PFEISref_1/Dyno%20Nobel%202010.pdf)). The "Norwegian practice" pattern gives 134 charged holes and 45 contour holes on T10.5, within the 126–158 and 45–50 reported for current Norwegian rounds ([Jakobsen et al. 2024, summary](https://www.tunnelsandtunnelling.com/?p=23436)). Vibration: Stockholm Northern Link fit ([Bahrekazemi et al. 2011](https://www.issmge.org/uploads/publications/59/67/10.3.GVRBA.pdf)) and SS 460 48 66 guide values with the factors of a [published Solna analysis](https://www.Solna.se/download/18.76f8a05e16faf0319722153d/1580131008510/Riskanalys%20vibrationer.pdf). Overbreak 9–23 % median at Västlänken ([Chalmers MSc 2022](https://odr.chalmers.se/bitstreams/5ef47ce7-d508-4d65-a3ea-6694af8d8d0f/download)). | The Norwegian pattern's 0.47 m contour spacing and 0.75 B stoping burden are fitted to the hole counts, not a design rule. Specific charge (1.8 kg/m³, textbook charging) is about a third below the 2.7–3.0 kg/m³ logged on three Norwegian road tunnels in 2021–24 at this size ([Gjengedal & Jakobsen 2025](https://airdrive.eventsair.com/eventsairwesteuprod/production-atlanticmice-public/927385ad0d3e425bbbf6581c4573f524), Fig. 5); charged holes (134) are in their range. Charging time per hole is still unsourced. The house and its distance are illustrative. |
| 6 | Honest labels | ✅ | "Analytical (browser)" badge; the Model limits panel names the profile idealisation, the fitted pattern, the non-overlapping cycle and assumed times, and the single vibration fit. | — |

## Behaviour checked in the browser

- All ten steps run in order, the last being downtime; round 12.7 h in class I, 15.4 h in class III, 22.3 h in class IV.
- Class IV near the house (41 m): one delay per row (157 kg) gives 171 mm/s mean; one hole per delay (8.3 kg) gives 17.8 mm/s mean and 43.8 mm/s on the 98 % bound against a 34 mm/s guide value, so the round has to be shortened.

## Before the next publish

- [ ] Specific charge and charging time from a published Norwegian round.
- [ ] Overlap of support work with the next round, as on site.
- [ ] Probe drilling and pre-grouting ahead of the face in poor rock.
