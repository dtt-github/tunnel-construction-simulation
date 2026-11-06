# Realism checklist: hard-rock open gripper TBM, Slice B

- **Demo:** [`web/hard-rock/`](../../web/hard-rock/)
- **Class preset:** `hard-rock-main-beam-9.5m` in [machine-classes.json](../../models/presets/machine-classes.json)
- **Method card:** [open gripper](../research/methods-reference.md#open-gripper-layout-from-front-to-back)
- **Rules:** [ROADMAP realism rules](../ROADMAP.md#realism-rules-apply-to-every-phase)
- **Models:** [CSM disc cutter](../MODELS.md#csm-disc-cutter), [hard-rock drive](../MODELS.md#hard-rock-drive)
- **Validation:** [hard-rock projects](../validation/hard-rock-projects.md)

Reviewed 5 Nov 2026. Status: ✅ meets the rule · ⚠️ partly, gap listed · ❌ not yet. Format: [template](TEMPLATE.md).

| # | Rule | Status | Evidence | Known gaps |
|---|---|---|---|---|
| 1 | One method, one machine class, one ground | ✅ | Open gripper (main beam) TBM, class "9.5 m hard-rock main beam". Hard rock along the drive (gneiss, granite, a fault zone, mica schist). DAUB's main range for gripper TBMs is UCS 25 to over 250 MPa and RMR 41–100; the fault zone (RMR 22) is outside it, which is why it is slow and heavily supported. | Geology values are typical for the rock types, not a project. |
| 2 | Right support and lining for the method | ✅ | No segments and no pressure chamber. **L1** behind the roof shield: rock bolts by RMR class (Bieniawski 1989 pattern), mesh from class III, steel ring beams in classes IV–V (1.5 m and 0.75 m). **L2** on the backup: shotcrete in the crown (thickness by class) and precast invert segments carrying the track. The final cast-in-place lining is placed later and is stated, not shown. | Support patterns come from the drill-and-blast RMR table, which is the open reference; TBM practice uses lighter patterns in good rock. Per-bolt installation times are not modelled. |
| 3 | Right layout and muck path | ✅ | Front to back: flat cutterhead with a curved gauge, 19″ discs (tips 0.17 m proud), centre cluster, tilted gauge cutters and 8 buckets with grill bars; muck ring and chute onto the machine belt in the main beam; cutterhead support with roof shield fingers, side shields and invert shoe; L1 roof drills, ring-beam erector, mesh handler and probe drill; gripper carrier with shoes and propel cylinders; rear legs; backup gantries with the L2 shotcrete robot, invert segment erector, conveyor, ventilation duct and power. | Drives, hydraulics and cable reels are simplified; the 58 discs (Gotthard) are placed schematically. |
| 4 | Right cycle and utilisation | ✅ | Bore one 2 m stroke on the grippers (Gotthard; carrier stays on the rock while the beam slides through), then regrip: rear legs down, grippers in, carrier forward, grippers out (4 min, Farrokh 2018). After each stroke, the other downtime of that stroke from the per-km breakdown (support, cutter changes, maintenance, transport, TBM and backup repairs, utilities, survey). Fault zone: utilisation ≈ 10 %, as reported for weak ground (10–15 %). | Downtime is applied as one stop per stroke rather than as separate events; cutter changes are not tied to individual cutters. |
| 5 | Every number in a cited range | ⚠️ | Speed limited to 6.65 rpm by the 19″ gauge-cutter speed (Rostami & Chang 2017). Penetration capped at 15 mm/rev (Macias & Barton 2022). Cutter loads against the 311 kN rating. Drive: installed torque up to the power limit. Machine from the Gotthard Base Tunnel gripper TBMs: 9.58 m, 8,526 kNm, 3,500 kW (Herrenknecht), 58 discs at 26 t (the default thrust, 14.75 MN) and a 2 m stroke (AlpTransit portal). CSM penetration with ψ back-analysed on Follo: 5.8 mm/rev in gneiss. Mean rates about 12–16 m per working day, against Gotthard's 8–10 m per calendar day over whole drives and best days of 38–56 m ([validation](../validation/hard-rock-projects.md)). | The installed thrust (27.5 MN) is that of the 9.33 m S-210. No open source gives Gotthard utilisation, penetration or rock inputs section by section. |
| 6 | Honest labels | ✅ | "Analytical (browser)" badge; the Model limits panel lists the illustrative geology, the machine sources, the calendar-day comparison with Gotthard, the digitised support curve and the missing final lining. | — |

## Assumed values

- The cutter layout on the head, and the positions of the parts along the machine.
- Geology per zone: UCS, BTS, CAI, quartz content and RMR.
- Visual translation of the support table: bolts per row, arc lengths, shotcrete in the crown only.

## Before the next publish

- [x] Gotthard torque, power, cutters and stroke from Herrenknecht and the AlpTransit portal; the S-210 thrust from Tunnels & Tunnelling.
- [ ] Per-bolt and per-ring-beam installation times, when an open source is found.
- [x] Gripper bearing pressure against the rock-mass strength (our own simple check), with steel-set equilibrium and closure in the fault zone.
