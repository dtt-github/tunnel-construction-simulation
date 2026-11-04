# Realism checklist: urban EPB, Slice A

Demo: [`web/epb/`](../../web/epb/) · Class preset: `urban-epb-7m` in [machine-classes.json](../../models/presets/machine-classes.json) · Method card: [EPB](../research/methods-reference.md#epb-and-slurry) · Rules: [ROADMAP realism rules](../ROADMAP.md#realism-rules-apply-to-every-phase)

Reviewed 4 Nov 2026 against the page as committed with this file. Status: ✅ meets the rule · ⚠️ partly, gap listed · ❌ not yet.

| # | Rule | Status | Evidence | Known gaps |
|---|---|---|---|---|
| 1 | One method, one machine class, one ground | ✅ | EPB shield, class "7 m urban EPB" (Ø 7.08 m, 9,800 kNm, 1,920 kW from the Crossrail reference). Ground: stiff clay, then clayey sand, axis 20 m deep, water table 3 m. DAUB pairs cohesive, low-permeability ground with EPB (main range) and clayey sand with EPB (extended to main range). | Ground strengths (φ′, c′, γ, K₀) are illustrative, not from a project. |
| 2 | Right support and lining for the method | ⚠️ | Universal ring of 6 segments + key, key inserted last; 1.2 m rings. Two-component grout through the tailskin during the shove; the grout annulus appears as each ring leaves the tail. Three rows of greased wire brushes in the tail seal. | Segment geometry (OD 6.8 m, 300 mm) is assumed. Grout pressure, taper and ring steering are not modelled. |
| 3 | Right layout and muck path | ✅ | Front to back: spoke cutterhead with rippers and scrapers, ≈ 40 % opening; mixing arms and stators; pressure bulkhead with five earth-pressure cells; main drive; man-lock; inclined screw with outlet gate; articulated front and tail shield; 16 pairs of thrust cylinders on the last ring; erector and segment feeder; backup gantries (foam plant, grout plant, control cabin, power pack, ventilation); belt conveyor to the portal; segment and grout supply train. | The foam plant and gantry equipment are visual only. A muck-train alternative to the belt is not shown. |
| 4 | Right cycle and utilisation | ⚠️ | Push one ring width, then build the ring (sequential). The cutterhead stops and the screw gate closes during the build. Build time 35 min (sourced); push time follows the advance speed. Thrust cylinders retract only in the sector of the segment being placed, then re-extend onto it. | **No downtime model yet**: logistics, maintenance, tool changes and breakdowns are missing. The cycle-only rate (≈ 31 m/day at 60 mm/min) is above the typical 12–20 m/day and is labelled "no downtime". Roadmap model 12 is needed. |
| 5 | Every number in a cited range | ⚠️ | Advance speed 0–80 mm/min (sourced cycle: 1.2 m in 16 min ≈ 75 mm/min). Cutterhead 0–3.2 rpm (preset value 3.19 rpm, unverified source). Screw 0–22 rpm (sourced). Face pressure is held inside the DAUB window computed for the ground: ≈ 1.8–3.5 bar at the axis, within DAUB's 1–4 bar main range. Torque 6.4 MNm, below the 9.8 MNm installed. Thrust ≈ 24 MN, below ≈ 52 MN (6.6 m reference machine scaled). FER 8–15. | The FIR and FER ranges come from an unverified source. The check of best day, week and month against the record table is not built. The DAUB partial factors are still unverified. |
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

- [ ] Downtime and utilisation model (roadmap model 12), so that advance per day is realistic.
- [ ] Record-table check of best day, week and month for the 6–8 m class.
- [ ] Volume loss responding to face-pressure deficit and grout filling. This needs a published relation; until then volume loss stays a labelled scenario input.
