# Realism checklist: urban slurry shield (Mixshield), Slice C

- **Demo:** [`web/slurry/`](../../web/slurry/)
- **Method card:** [slurry / Mixshield](../research/methods-reference.md#overview)
- **Rules:** [ROADMAP realism rules](../ROADMAP.md#realism-rules-apply-to-every-phase)
- **Models:** [slurry shield](../MODELS.md#slurry-shield-mixshield), [face support](../MODELS.md#face-support-pressure), [thrust and torque](../MODELS.md#thrust-and-torque), [utilisation](../MODELS.md#utilisation-and-downtime)

Reviewed 4 Nov 2026. Status: ✅ meets the rule · ⚠️ partly, gap listed · ❌ not yet.

| # | Rule | Status | Evidence | Known gaps |
|---|---|---|---|---|
| 1 | One method, one class, one ground | ✅ | 7.08 m Mixshield, Crossrail class: 3,709 kNm and 1,120 kW installed ([Herrenknecht, Crossrail](https://herrenknecht.com/en/references/referencesdetail/crossrail-london)). Saturated dense sand, then sandy gravel, water table 1 m below ground: the slurry machine's ground in the [DAUB 2025 machine selection](https://www.daub-ita.de/fileadmin/documents/daub/gtcrec1/2025-08_Selection_of_Tunnel_Borng_Machines.pdf). | Geology is illustrative; no clay or mixed face, where clogging and separation of fines become the issue. |
| 2 | Right support and lining for the method | ✅ | Universal ring of 7 segments + key, 1.6 m wide, 6.2 m inner diameter (Crossrail Thames tunnels, [Rail Engineer](https://www.railengineer.co.uk/crossrail-thames-tunnels/)); annulus grouted through the tail. Segment lining panel: ring forces by the elastic equation method ([ITA WG2 2000](https://about.ita-aites.org/publications/wg-publications/download/80_37554c46d738a06a0d79e03e8e7c5f59)) with Wood's joint reduction, concrete stress, ovalisation against 0.5 % of ID ([DAUB 2024](https://www.daub-ita.de/fileadmin/documents/daub/gtcrec2/2024-12_Tuebbingdesign_EN_final_web.pdf)), jacking stress and bursting under the shoes, grout pressure window ([ITA 2019](https://about.ita-aites.org/publications/wg-publications/download/1825_470d8f379299b5ad89de378875dd1b8f)). | Segment thickness (300 mm), ground stiffness for the ring bedding, concrete modulus and shoe pad size are assumed. |
| 3 | Right layout and muck path | ✅ | Excavation chamber full of bentonite slurry; submerged wall with its opening at the invert; working chamber with the air cushion over the slurry; pressure bulkhead; jaw crusher and intake grid at the suction; DN300 feed and discharge lines along the backup ([Herrenknecht Mixshield](https://herrenknecht.com/en/products/productdetail/mixshield)); slurry pumps on the backup; separation plant at the portal ([Herrenknecht separation technology](https://herrenknecht.com/en/products/productdetail/separation-technology)). No screw and no belt. Between pushes the circuit runs in bypass. | Booster pumps along the tunnel, the pipe extension and the plant (screens, hydrocyclones, filter press) are labelled, not drawn in detail. |
| 4 | Right cycle | ⚠️ | Push and ring build as on the EPB page (35 min per ring); pressure held by the air regulator; the discharge pump holds the working-chamber level; pump interlocks on a high or low level. | Downtime uses distributions fitted on one EPB project; there are no separation-plant stops, line extensions or slurry treatment delays. |
| 5 | Every number in a cited range | ⚠️ | Filter cake: f_s0 = 3.5 τ_f / d₁₀, membrane at ≥ 200 kN/m³ (DIN 4126), penetration e_max = Δp d₁₀ / (3.5 τ_f) ([DAUB 2016](https://www.daub-ita.de/fileadmin/documents/daub/gtcrec1/2016-10_DAUB_Recommendations_for_Face_Support_Pressure_Calculations_for_Shield_Tunnelling_in_Soft_Ground.pdf); [Broere & van Tol 2000](https://repository.tudelft.nl/file/File_9dc608e8-3df5-4344-8d2a-b6e420392119)). Control tolerance ±10 kPa with an air cushion against ±30 kPa for EPB, and the level kept slightly above the axis (DAUB 2016). Dry-mass balance ([Shomee et al. 2022](https://penerbit.uthm.edu.my/periodicals/index.php/peat/article/download/7927/3148/55023)). Durand deposit limit with the coefficient corrected after [Miedema](https://eng.libretexts.org/Bookshelves/Civil_Engineering/Slurry_Transport_(Miedema)/06%3A_Slurry_Transport_a_Historical_Overview/6.27%3A_The_Limit_Deposit_Velocity_(LDV)): 3.25 m/s in DN300, against ≈ 3.9 m/s at the data-sheet 1000 m³/h. Torque at 2.3 MNm, 62 % of installed. | The air-cushion dynamics are this project's derivation (no open source with equations). Support transfer as 1 − e/L is an approximation of DAUB's wedge method. Friction coefficients, chamber sizes, regulator time and the over-excavation response are assumed. No open thrust figure for a slurry machine: the bar shows the EPB reference. |
| 6 | Honest labels | ✅ | "Analytical (browser)" badge; the Model limits panel names the own derivation, the e_max and transfer approximations, ideal meters and the EPB downtime distributions. | — |

## Behaviour checked in the browser

- Sand (d₁₀ 0.15 mm, τ_f 30 Pa): f_s0 = 700 kN/m³, filter cake, 100 % of the support transferred; discharge 1.18 t/m³; dry solids equal to the theoretical 86 m³/h.
- Gravel (d₁₀ 1 mm): penetration 0.57 m at τ_f 30 Pa (78 % transferred) and 1.72 m at 10 Pa (34 %), with alarms.
- Manual discharge 1300 m³/h: the level falls by ≈ 0.6 m and the support pressure at the axis drops by ≈ 10 kPa while the air regulator holds the cushion pressure.
- Feed 650 m³/h: feed and discharge velocities fall below the deposit limit, with alarms.

## Before the next publish

- [ ] A published Mixshield thrust figure for the reference bar.
- [ ] Air-cushion response measured on a machine (step test) to check the regulator time.
- [ ] Separation-plant capacity and stops in the downtime model.
