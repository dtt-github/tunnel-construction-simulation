# Realism checklist: urban EPB, Slice A

Demo: [`web/epb/`](../../web/epb/) · Class preset: `urban-epb-7m` in [machine-classes.json](../../models/presets/machine-classes.json) · Method card: [EPB](../research/methods-reference.md#epb-and-slurry) · Rules: [ROADMAP realism rules](../ROADMAP.md#realism-rules-apply-to-every-phase)

Reviewed 4 Nov 2026 against the page as committed with this file; rule 4 updated the same day for the utilisation model. Status: ✅ meets the rule · ⚠️ partly, gap listed · ❌ not yet.

| # | Rule | Status | Evidence | Known gaps |
|---|---|---|---|---|
| 1 | One method, one machine class, one ground | ✅ | EPB shield, class "7 m urban EPB" (Ø 7.08 m, 9,800 kNm, 1,920 kW from the Crossrail reference). Ground: stiff clay, then clayey sand, axis 20 m deep, water table 3 m. DAUB pairs cohesive, low-permeability ground with EPB (main range) and clayey sand with EPB (extended to main range). | Ground strengths (φ′, c′, γ, K₀) are illustrative, not from a project. |
| 2 | Right support and lining for the method | ⚠️ | Universal ring of 6 segments + key, key inserted last; 1.2 m rings. Two-component grout through the tailskin during the shove; the grout annulus appears as each ring leaves the tail. Three rows of greased wire brushes in the tail seal. Segment lining panel: ring forces by the elastic equation method ([ITA WG2 2000](https://about.ita-aites.org/publications/wg-publications/download/80_37554c46d738a06a0d79e03e8e7c5f59)) with Wood's joint reduction, concrete stress, ovalisation against 0.5 % of ID ([DAUB 2024](https://www.daub-ita.de/fileadmin/documents/daub/gtcrec2/2024-12_Tuebbingdesign_EN_final_web.pdf)), jacking stress and bursting under the shoes, grout pressure window ([ITA 2019](https://about.ita-aites.org/publications/wg-publications/download/1825_470d8f379299b5ad89de378875dd1b8f)). | Segment geometry (OD 6.8 m, 300 mm) is assumed. Ground stiffness for the ring bedding, concrete modulus and shoe pad size are assumed. Taper and ring steering are not modelled. |
| 3 | Right layout and muck path | ✅ | Front to back: spoke cutterhead with rippers and scrapers, ≈ 40 % opening; mixing arms and stators; pressure bulkhead with five earth-pressure cells; main drive; man-lock; inclined screw with outlet gate; articulated front and tail shield; 16 pairs of thrust cylinders on the last ring; erector and segment feeder; backup gantries (foam plant, grout plant, control cabin, power pack, ventilation); belt conveyor to the portal; segment and grout supply train. | The foam plant and gantry equipment are visual only. A muck-train alternative to the belt is not shown. |
| 4 | Right cycle and utilisation | ✅ | Push one ring width, then build the ring; cutterhead stopped and screw gate closed during the build (35 min, sourced). Between rings: general tunnelling activities, train delays with rail haulage, per-cycle maintenance (distributions from a 6.88 m metro EPB, Moosazadeh et al. 2018). Shift pattern 2 × 10 h + 4 h maintenance (SF Central Subway) or 2 × 12 h. Cutting-tool interventions after a Weibull number of rings, lasting a log-logistic time (median 105 h). Default forecast: utilisation ≈ 15 %, ≈ 91 m/week, inside the 40-EPB survey (85 ± 36 m/week). | Distributions are from one project. Locomotive travel time, learning curve, breakdowns by subsystem and ground-related stops other than tool interventions are not modelled. The cycle-only rate is still shown, labelled "no downtime". |
| 5 | Every number in a cited range | ⚠️ | Advance speed 0–80 mm/min (sourced cycle: 1.2 m in 16 min ≈ 75 mm/min). Cutterhead 0–3.2 rpm (preset value 3.19 rpm, unverified source). Screw 0–22 rpm (sourced). Face pressure is held inside the DAUB window computed for the ground: ≈ 1.8–3.5 bar at the axis, within DAUB's 1–4 bar main range. Torque 6.4 MNm, below the 9.8 MNm installed. Thrust ≈ 24 MN, below ≈ 52 MN (6.6 m reference machine scaled). FER 8–15. | The FIR and FER ranges come from an unverified source. Best day, week and month are checked against the best published EPB rates (40.6 m day, 178.5 m week in the survey, 920 m month claim) and the world record of the diameter class; at default settings all are below. The DAUB partial factors are still unverified. |
| 6 | Honest labels | ✅ | "Analytical (browser)" badge. The "Model limits" panel states that volume loss is a scenario input, building categories use greenfield horizontal strain only, the daily rate excludes downtime, and lists the assumed values. Surface heights are marked as exaggerated ×150. | — |

## Assumed values (illustrative, not sourced)

These values are in `web/epb/main.js`:

- **Machine:**
  - shield length 9.5 m;
  - chamber length 0.9 m (≈ 35 m³);
  - screw Ø 0.9 m, shaft 0.3 m, pitch 0.7 m, length 11 m, efficiency 0.6, pressure-decay length 3 m;
  - segment OD 6.8 m and ID 6.2 m;
  - shield weight 4,000 kN, backup weight 6,000 kN, tail-seal friction 500 kN;
  - 80 tools at 4 kN tangential force;
  - friction coefficients (model defaults).
- **Chamber:** paste unit weight 18 kN/m³ × (1 − air fraction); automatic screw control gain 0.06 rpm/kPa with feed-forward from the steady balance.
- **Scenario:** ground parameters per zone, axis depth 20 m, water table 3 m, volume loss 1 % (the default of the `closed_face_clay` preset, Mair & Taylor 1997 range), building positions and sizes.

## Before the next publish

- [x] Downtime and utilisation model (roadmap model 12), so that advance per day is realistic.
- [x] Record-rate check of best day, week and month for the diameter class.
- [ ] Thrust and torque bars: on open field data (Changsha Metro Line 4, 281 rings) the default coefficients over-predict thrust ×1.43 and torque ×1.70 ([validation](../validation/epb-open-data.md)). Recalibrate the shield and rim terms after a third dataset with published site parameters.
- [ ] Volume loss responding to face-pressure deficit and grout filling. This needs a published relation; until then volume loss stays a labelled scenario input.
