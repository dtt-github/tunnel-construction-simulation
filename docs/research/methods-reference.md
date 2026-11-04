# Methods reference: what each tunnelling method really looks like

This page is the realism baseline for every model, machine and demo in the project. A demo of a method must match its card here, and every number shown must sit inside a range cited on this page or in [industry-survey.md](industry-survey.md). Items marked **[UNVERIFIED]** still need a primary source.

Compiled 4 Nov 2026 from manufacturer pages, the DAUB and FHWA documents and project reports. Every claim links its source.

Key documents:

- **DAUB (2022, rev. Aug 2025), *Recommendations for the selection of tunnel boring machines*:** [PDF](https://www.daub-ita.de/fileadmin/documents/daub/gtcrec1/2025-08_Selection_of_Tunnel_Borng_Machines.pdf)
- **FHWA (2009), *Technical Manual for Design and Construction of Road Tunnels*, FHWA-NHI-09-010:** [PDF](https://www.fhwa.dot.gov/bridge/tunnel/pubs/nhi09010/tunnel_manual.pdf)
- **Rostami & Chang (2017), *Engineering* 3(4), hard-rock TBM design:** [link](https://www.engineering.org.cn/engi/EN/1159834608697140017)

## Overview

| Method | Face support | Muck path | Support behind the face | Final lining | Cycle | Typical ground |
|---|---|---|---|---|---|---|
| **Open gripper (main beam) TBM** | None (rock self-supporting) | Buckets → chutes → muck ring → machine belt through the centre → backup conveyor or trains | **L1** (just behind the head): rock bolts, mesh, steel ring beams, McNally slats in bad ground, probe drilling. **L2** (backup): shotcrete, often precast invert segments | **Cast-in-place concrete with membrane**, during or after boring | Bore one stroke on the grippers → rear legs down → regrip → bore. Support installed in parallel | Hard, stable rock, UCS 25 to >250 MPa, RMR 41–100 (DAUB) |
| **Single shield TBM** | Shield only, no pressure chamber | Buckets → centre belt | Precast segment rings built in the tailskin. Annulus filled with pea gravel and/or grout | The segments | Bore one ring width, then build the ring (sequential). Thrust cylinders push off the last ring | Brittle or unstable rock, changing conditions, little water |
| **Double shield (telescopic) TBM** | Shield only | Buckets → centre belt | Segments (optional in ideal rock) with pea gravel and grout | The segments | **Bore and build the ring at the same time** (grippers take the thrust). In weak ground: single-shield mode, sequential | Long hard-rock drives with fault zones, UCS ≥ 25 MPa, RMR 21–100 |
| **Crossover rock/EPB** | EPB mode: pressurised chamber. Rock mode: none | Screw (EPB mode) or belt (rock mode) | Segments | Segments | Sequential | Mixed ground, faults, water inflows |
| **EPB shield** | Conditioned soil paste in a closed chamber behind a pressure bulkhead. Pressure set by screw speed against advance | Screw conveyor → belt or muck cars | Segment ring in the tail, two-component grout through the tailskin during the shove | The segments (one-pass) | Excavate one ring width, then build the ring | Fines > 15 % (best > 40 %), k < 10⁻⁶ m/s, soft to stiff (DAUB) |
| **Slurry / Mixshield** | Pressurised bentonite slurry, regulated by an air cushion behind a submerged wall | Pumped through feed and return pipes → separation plant on the surface | Segments + grout | Segments | As EPB | Fines < 40 %, k 10⁻²–10⁻⁶ m/s, high water pressure (DAUB) |
| **Variable density** | Slurry, high-density slurry or EPB paste, with an air cushion | Screw → pressurised hydraulic circuit | Segments | Segments | As EPB | Mixed and karstic ground |
| **SEM / NATM** | Shotcrete face seal, face wedge, spiles or pipe canopy | Excavator or roadheader → loader and trucks | Every round: shotcrete (150–400 mm in soil) with mesh or fibres, lattice girders, bolts in rock. Early ring closure (within ≈ 1 D in soil) | Membrane + cast-in-place concrete (≈ 300 mm), cast once convergence < 1 mm/month | Excavate a round (1–2 m in soil), support it, repeat. Sequence: top heading, bench, invert or side drifts | Short, odd-shaped or large sections, stiff soils, weak rock (FHWA ch. 9) |
| **Drill & blast** | Rock; probing and pre-grouting where needed | Loader → trucks | Bolts + shotcrete scaled to rock class; ribs and forepoling in class IV–V | Shotcrete (Nordic practice) or membrane + cast-in-place (Alpine practice) | Drill → charge → blast → ventilate → scale → muck → support. Rounds about 3–5 m in good rock | Medium to hard rock |

Sources for the table:

- **TBM types:**
  - Open gripper: [Herrenknecht Gripper TBM](https://herrenknecht.com/en/products/productdetail/gripper-tbm), [Robbins Main Beam](https://www.robbinstbm.com/products/tunnel-boring-machines/main-beam/)
  - Single shield: [Herrenknecht Single Shield](https://herrenknecht.com/en/products/productdetail/single-shield-tbm)
  - Double shield: [Herrenknecht Double Shield](https://herrenknecht.com/en/products/productdetail/double-shield-tbm), [Robbins Double Shield](https://www.robbinstbm.com/?p=94)
  - Crossover: [Robbins Crossover XRE](https://www.robbinstbm.com/products/crossover-xre/)
  - EPB and slurry: [Herrenknecht EPB](https://herrenknecht.com/en/products/productdetail/epb-shield), [Herrenknecht Mixshield](https://herrenknecht.com/en/products/productdetail/mixshield)
- **Selection ranges:** DAUB 2025, §5.2 and appendix 3.
- **SEM/NATM and drill & blast:** FHWA chapters 6 and 9, tables 6-9, 9-1 and 9-2.
- **Drill & blast practice:** [tunnelingonline drill & blast article](https://tunnelingonline.com/advancements-in-tunneling-and-underground-excavation-by-drill-blast/).

## Hard-rock TBMs

### Common to all hard-rock machines

- **Cutterhead**
  - Flat face, with the gauge curved on a radius of ≈ 450–550 mm. Gauge cutters are tilted up to ≈ 65–70°. Dome and cone heads are no longer used. (Rostami & Chang 2017)
  - Disc cutters: 17″ ≈ 250 kN, 19″ ≈ 310 kN, 20″ and larger above 10.5 m. Spacing 75–100 mm. (same source)
  - Disc exposure from the face is small, ≈ 150–180 mm [UNVERIFIED].
  - **Buckets** at the periphery: ≈ 4 on small heads in very hard rock, 6–8 on medium heads, more than 12 above 9 m. Bucket openings pass blocks of about 100 × 150 mm. (same source)
- **Speed:** rpm = V_L / (π D), with gauge-cutter speed limit V_L = 165 m/min (17″) or 200 m/min (19″). That gives ≈ 9 rpm at 7 m, 6.7 rpm at 9.5 m and 4.4 rpm at 14.4 m. (same source)
- **No pressure chamber, no screw.** Muck goes from the buckets through chutes and a muck ring onto the machine belt in the cutterhead centre. Cutters are changed from behind the head.
- **Utilisation:**
  - Downtime comes from support installation, regripping, cutter changes (≈ 66 min each on average), maintenance, logistics and bad ground.
  - Utilisation falls to 10–15 % in heavy-support ground ([Farrokh, OneMine](https://onemine.org/documents/a-discussion-on-tbm-cutter-change-time-and-cutter-life); [Farrokh 2018](https://journals.shahroodut.ac.ir/article_86_37947d0b6e5d16bc78d6c44fc0d2b66c.pdf)).
  - A ≈ 40 % baseline is often quoted [UNVERIFIED].
  - The NTNU model predicts net penetration, cutter life and utilisation per sub-operation ([Bruland, NFF](https://nff.no/wp-content/uploads/sites/2/2020/04/12-Bruland.pdf)).
- **Fault zones slow the drive:** overbreak, blocky face, heavy support, jamming. At Gotthard Bodio, steel arches were needed every metre in faults ([Tunnelbuilder](https://tunnelbuilder.com/News/Mixed-Fortune-at-Gotthard.aspx)).

### Open gripper: layout from front to back

1. Cutterhead.
2. Cutterhead support with roof shield (fingers), side shields and invert shoe.
3. Main beam carrying the machine belt.
4. **L1 zone:** roof drills, ring-beam erector, mesh handling, probe drill.
5. Gripper unit with propel cylinders.
6. Rear legs.
7. Backup gantries with the **L2 zone:** shotcrete robot, invert segment erector. Then the conveyor and ventilation.

Examples of L1 and L2 support:

- **Gotthard, Piora zone:** TH ribs at 1 m centres, immediate shotcrete seal, built up to 300 mm ([TunnelTalk](https://tunneltalk.com/Gotthard-TBM-safely-across-the-Piora-Mulda.php)).
- **McNally slats** in rockburst ground ([Robbins McNally](https://www.robbinstbm.com/about/advancements/mcnally/)).

Final lining examples:

- **Niagara:** 600 mm cast-in-place with a polyolefin membrane, poured while boring continued ([Robbins Niagara](https://www.robbinstbm.com/projects/niagara-tunnel-project/)).
- **Lötschberg:** final lining placed right behind the gripper TBM ([Gollegger, NFF](https://nff.no/wp-content/uploads/sites/2/2021/06/Johannes-Gollegger-20210610.pdf)).

Stroke ≈ 1.2–1.8 m [UNVERIFIED].

### Double shield

Front shield, then the telescopic joint with the main thrust cylinders, then the gripper shield (grippers, auxiliary thrust cylinders, erector), then the tailskin. Torque cylinders stop the machine rolling. Pea gravel bedding is disturbed by regripping, which is a known cause of ring ovalisation ([Geomechanics & Tunnelling 2018](https://zendy.io/title/10.1002/geot.201800034)).

## EPB and slurry

- **EPB, layout from front to back:**
  1. Cutterhead with knives, drag bits and rippers, plus discs in mixed ground. Opening ratio ≈ 30–40 % on spoke heads.
  2. Mixing arms (rotors on the head, stators on the bulkhead).
  3. Pressure bulkhead with earth-pressure cells.
  4. Screw conveyor with an outlet gate (two-stage above ≈ 3 bar).
  5. Man-lock.
  6. Articulated shield.
  7. Thrust cylinders on the last ring.
  8. Tail seal: 3–4 rows of wire brushes, greased (35–40 kg per metre).
  9. Erector and segment feeder.
  10. Two-component grout through the tailskin, 7–9 m³ per metre at Ø ≈ 9–10 m.
  11. Foam plant on the backup.

  Sources: DAUB §5.2.5; [Robbins, EPB technology](https://www.tunnel-online.info/download/160506/EPB-technology.pdf); [Dublin MetroLink EIAR A5.14](https://www.pleanala.ie/publicaccess/EIAR-NIS/314724/5_EIAR/Volume%205%20Appendices/Chapter%2005%20MetroLink%20Construction%20Phase/A5.14%20TBM%20Consumables.pdf).

- **EPB operating numbers:**
  - Cutterhead ≈ 1.5–3 rpm.
  - Screw ≈ 0–22 rpm.
  - Face pressure 1–4 bar (DAUB main range); plan for ±0.3 bar swings.
  - FER 8–15 [UNVERIFIED source], FIR 35–60 % at Rome Metro C [UNVERIFIED source].
  - Reference machines:
    - **7.08 m (Crossrail):** 9,800 kNm, 1,920 kW, ≈ 58 MN thrust ([Herrenknecht Crossrail](https://herrenknecht.com/en/references/referencesdetail/crossrail-london)).
    - **6.6 m mixed-face:** 45 MN, 7,038 kNm working ([Robbins RETC 2019](https://www.robbinstbm.com/wp-content/uploads/2019/07/RETC2019-14-05_Tunneling-in-Mixed-Face-Conditions.pdf)).
  - Cycle example (Moscow): 1.2 m rings, 6 + 1 segments, 16 min push + 35 min build, ≈ 12 m/day ([Tunnels & Tunnelling](https://tunnelsandtunnelling.com/?p=5953)).
- **Slurry:**
  - No belt and no muck cars. Twin feed and return pipes, booster pumps, and a separation plant at the portal.
  - Air cushion behind a submerged wall; crusher in front of the intake.
  - Lower torque than EPB: Crossrail Mixshield 3,709 kNm against 9,800 kNm for the EPB at the same 7.08 m.

## Ground → method pairing (scenario editor rules)

| Ground | Method |
|---|---|
| Cohesive or clayey soil, low permeability | EPB |
| Clean sand or gravel, high water pressure | Slurry / Mixshield |
| Karst, mixed ground | Variable density |
| Hard rock, long drives | Open gripper or double shield, or drill & blast |
| Short, large or complex sections | SEM, or drill & blast in rock |

DAUB rock stability classes: A1 RMR 81–100, A2 61–80, B1 51–60, B2 41–50, B3 21–40, C squeezing < 20.

## Corrections to our own material

- **Installed torque:**
  - The Krause band α·D³ with α 9–23 kNm/m³ is *below* modern EPB machines. Crossrail 7.08 m is 9.8 MNm, against a band of 3.2–8.2 MNm.
  - Replace the band with a table of reference machines (as above) in `thrust_torque` and its docs.
- **Current hard-rock demo** (`web/`): it shows a flat slab head with no buckets, no muck path, no thrust cylinders, no erector and no backfill.
  - A fault zone makes it *faster*, because penetration hits the 30 mm/rev solver cap.
  - There is no utilisation model.
  - The rpm slider goes to 10, above the ≈ 9 rpm limit for 7 m with 19″ cutters.
  - It is to be rebuilt to this page.
