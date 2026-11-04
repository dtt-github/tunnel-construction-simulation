# Realism checklist: hard-rock open gripper TBM, Slice B

- **Demo:** [`web/hard-rock/`](../../web/hard-rock/)
- **Class preset:** `hard-rock-main-beam-9.5m` in [machine-classes.json](../../models/presets/machine-classes.json)
- **Method card:** [open gripper](../research/methods-reference.md#open-gripper-layout-from-front-to-back)
- **Rules:** [ROADMAP realism rules](../ROADMAP.md#realism-rules-apply-to-every-phase)
- **Models:** [CSM disc cutter](../MODELS.md#csm-disc-cutter), [hard-rock drive](../MODELS.md#hard-rock-drive)

Reviewed 4 Nov 2026. Status: ✅ meets the rule · ⚠️ partly, gap listed · ❌ not yet.

| # | Rule | Status | Evidence | Known gaps |
|---|---|---|---|---|
| 1 | One method, one machine class, one ground | ✅ | Open gripper (main beam) TBM, class "9.5 m hard-rock main beam". Hard rock along the drive (gneiss, granite, a fault zone, mica schist). DAUB's main range for gripper TBMs is UCS 25 to over 250 MPa and RMR 41–100; the fault zone (RMR 22) is outside it, which is why it is slow and heavily supported. | Geology values are typical for the rock types, not a project. |
| 2 | Right support and lining for the method | ✅ | No segments and no pressure chamber. **L1** behind the roof shield: rock bolts by RMR class (Bieniawski 1989 pattern), mesh from class III, steel ring beams in classes IV–V (1.5 m and 0.75 m). **L2** on the backup: shotcrete in the crown (thickness by class) and precast invert segments carrying the track. The final cast-in-place lining is placed later and is stated, not shown. | Support patterns come from the drill-and-blast RMR table, which is the open reference; TBM practice uses lighter patterns in good rock. Per-bolt installation times are not modelled. |
| 3 | Right layout and muck path | ✅ | Front to back: flat cutterhead with a curved gauge, 19″ discs (tips 0.17 m proud), centre cluster, tilted gauge cutters and 8 buckets with grill bars; muck ring and chute onto the machine belt in the main beam; cutterhead support with roof shield fingers, side shields and invert shoe; L1 roof drills, ring-beam erector, mesh handler and probe drill; gripper carrier with shoes and propel cylinders; rear legs; backup gantries with the L2 shotcrete robot, invert segment erector, conveyor, ventilation duct and power. | Drives, hydraulics and cable reels are simplified; cutter count (62) is an assumption. |
| 4 | Right cycle and utilisation | ✅ | Bore one stroke on the grippers (carrier stays on the rock while the beam slides through), then regrip: rear legs down, grippers in, carrier forward, grippers out (4 min, Farrokh 2018). After each stroke, the other downtime of that stroke from the per-km breakdown (support, cutter changes, maintenance, transport, TBM and backup repairs, utilities, survey). Fault zone: utilisation ≈ 10 %, as reported for weak ground (10–15 %). | Downtime is applied as one stop per stroke rather than as separate events; cutter changes are not tied to individual cutters. |
| 5 | Every number in a cited range | ⚠️ | Speed limited to 6.65 rpm by the 19″ gauge-cutter speed (Rostami & Chang 2017). Penetration capped at 15 mm/rev (Macias & Barton 2022). Cutter loads against the 311 kN rating. Drive: installed torque up to the power limit. Mean rates (≈ 12–20 m/day) are far below the 9.01–10 m class record (105.6 m best day). | Torque, power and thrust are the Gotthard-class preset values from trade press (unverified). Stroke 1.8 m is an informal value. |
| 6 | Honest labels | ✅ | "Analytical (browser)" badge; the Model limits panel lists the illustrative geology, the unverified machine values, the digitised support curve and the missing final lining. | — |

## Assumed values

- Cutter count 62, stroke 1.8 m, and the positions of the parts along the machine.
- Geology per zone: UCS, BTS, CAI, quartz content and RMR.
- Visual translation of the support table: bolts per row, arc lengths, shotcrete in the crown only.

## Before the next publish

- [ ] Verify the Gotthard-class torque, power and thrust on a primary source, or switch to a verified machine.
- [ ] Per-bolt and per-ring-beam installation times, when an open source is found.
- [ ] Gripper bearing pressure against the wall strength (gripper slip in weak rock).
