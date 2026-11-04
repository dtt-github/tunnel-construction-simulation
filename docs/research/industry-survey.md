# Industry survey: Tunnelsoft, VMT, Herrenknecht, Robbins, The Boring Company

Research date: 2026-11-04. Method: company websites, product sheets and public trade-press or conference papers, gathered with web fetch and web search. Everything below is a paraphrase written for this project. Nothing is copied marketing text.

**Conventions**
- Each number carries its source URL. Sources are marked as **[vendor]** (the manufacturer's own claim), **[trade press]**, **[paper]**, or **[secondary]** (a blog or aggregator that repeats a company claim).
- **UNVERIFIED** means the figure came from a search snippet or a secondary source that we could not confirm against a primary document, or that sources disagree on it.
- Several vendor product PDFs (VMT `Produktinfo` sheets) now return 404. Where that happened, this report relies on the live web pages.

---

## 0. Executive summary

| Company | Relevance to the simulator | Key takeaways |
|---|---|---|
| **Herrenknecht** | Full TBM family (EPB, Mixshield, Variable Density, Multi-Mode, single, double and gripper shields), microtunnelling (AVN, Direct Pipe, E-Power Pipe), shaft machines (VSM, SBR, SBC), segment plants. Has an **erector training simulator**. | Diameter ranges per machine type. Variable-density mode switching with no chamber entry. Published machine data (power, torque) from reference pages. Herrenknecht.Connected portal, which exports PDF and Excel and has announced IFC. **VMT is a Herrenknecht group company.** |
| **VMT** | The guidance, navigation and ring-sequencing reference: TUnIS Navigation (TBM, double shield, gripper, microtunnelling, roadheader, excavator, rockbolter), TUnIS Ring Sequencing, SLuM tailskin clearance, RCMS ring convergence, MovingStation, Segment.Check, SDS segment logistics, and formerly IRIS. | The closed loop of total station, active laser target, inclinometer, steering display and ring choice. This loop is the most valuable thing for the simulator to model generically. |
| **Robbins** | Hard-rock TBMs (Main Beam, single and double shield), Crossover XRE (rock/EPB) and XSE (slurry/EPB), EPB machines, disc cutters from 6.5" to 20" with published load ratings, continuous conveyors. Also the "command chair" simulator paper. | **The industry-wide world-record advance-rate table by diameter class** (excellent validation targets). Cutter load capacities by size. Niagara 14.4 m machine data. |
| **The Boring Company (TBC)** | Prufrock: small-diameter (~12 ft ID) soft-ground TBM that mines continuously while installing the lining. Launches from the surface by "porpoising". Remote, zero-people-in-tunnel operation is the stated aim. Prufrock-MB hard-rock variant. | Continuous advance with no stop for ring build. Surface launch and retrieval. Targets of 1 mile/week and $5M/mile. Mostly company targets, with little independently verified performance data. |
| **Tunnelsoft (BabEng GmbH)** | TPC (Tunnelling Process Control): manufacturer-independent data management and monitoring for TBM, pipe jacking and conventional tunnelling, with a mobile app and segment tracking. | The KPI, report and dashboard vocabulary contractors use: availability, utilisation, downtime by subsystem, settlement correlated with TBM position, ring QA, tool wear. A model for our telemetry export and replay. |

---

## 1. Tunnelsoft (tunnelsoft.com)

### 1.1 What they do
Tunnelsoft is a business unit of **BabEng GmbH**, formerly Babendererde Engineers. Its single product family is **TPC (Tunnelling Process Control)**, a web-based data management, monitoring and reporting platform for underground construction. TPC does not make machines and does not offer guidance hardware. ([tunnelsoft.com](https://tunnelsoft.com) [vendor]; [ITA member page](https://about.ita-aites.org/members/supporters/490-babeng))

Product variants ([tunnelsoft.com](https://tunnelsoft.com) [vendor]):
- **TPC for TBM Tunnelling** covers EPB, slurry and hard-rock machines from small to very large diameters.
- **TPC for Pipe Jacking**.
- **TPC for Conventional Tunnelling** provides mobile capture of crew activities, completed work and material consumption.
- **TPC Group Server** is a multi-project central platform for a contractor's control room.
- **TPC Mobile** is a native iOS and Android app with an offline mode and a demo version.
- **TPC Segment Tracker** captures, inspects and tracks segments, with photo documentation. ([search result, tunnelsoft.com](https://tunnelsoft.com/solutions/tbm-tunnelling/) [vendor])

### 1.2 Features relevant to us
These come from the TBM solution page ([tunnelsoft.com/solutions/tbm-tunnelling](https://tunnelsoft.com/solutions/tbm-tunnelling/) [vendor]):
- **Data collection:** high-frequency machine data from TBMs, conveyors and other plant, buffered against network outages. Imports geotechnical and geodetic monitoring data from any vendor. Raw sensor values are processed with user formulas.
- **Visualisation:** live dashboards, sensor trends, a **process-history viewer that replays past operation**, and operator "driver screens" with thresholds.
- **Alarms:** static and location-dependent thresholds, sent by SMS or e-mail, with escalation to external stakeholders.
- **Reports:** automated daily, weekly and monthly reports, plus shift reports with annotations, images and approvals. Configurable "special reports" export to Excel.
- **KPIs:** TBM availability and utilisation, downtime by machine system and subsystem, productivity, cutter tool performance and inventory, and settlement trends.
- **Surroundings:** settlement curves aligned to TBM chainage (leading and lagging settlement), settlement-trough maps, and movement-vector maps with colour-coded alerts.
- **Segments:** production data comes in through APIs or database views. On site: inventory, storage maps, barcodes, damage logs, automatic ring ordering, and ring acceptance workflows with QA reports and digital signatures.
- **Extensibility:** SQL and Python scripting for custom calculations.
- **Interfaces:** the site says TPC connects to "all interfaces" and is manufacturer-independent, but **it names no protocol** (OPC UA, Modbus and so on are not stated). A developer presentation cites handling **more than 6,000 values every 10 s** per project ([search result: Babendererde NFF paper](https://nff.no/wp-content/uploads/sites/2/2020/04/27-Babendererde.pdf) [paper], UNVERIFIED: snippet only).
- **References:** Elbe crossing SuedLink (ELB-X), HS2, the Kalvebod Brygge cloudburst tunnel (pipe jacking). On HRBT Expansion (Virginia), TPC handled real-time data from **more than 3,700 monitoring points** ([Tunnel Business Magazine, Oct 2025](https://www.mydigitalpublication.com/article/XXL+Tunnel%2C+XXL+Data%3A+How+Smart+Software+Keeps+It+Moving/5053264/854291/article.html) [trade press], UNVERIFIED: snippet).

### 1.3 Simulator or training offerings
None found.

### 1.4 Implications
- TPC shows what a contractor expects to *see* from a TBM. Our simulator's telemetry stream and post-run reports should use the same concepts: ring-by-ring and shift-based reports, availability and utilisation, downtime coded by subsystem, settlement plotted against TBM face position, tool-wear logs, and segment QA.
- **Replay** of a recorded drive is a standard feature in this class of tool. Our simulator already produces time-series data, so a deterministic replay and timeline scrubber is cheap and expected.
- **Interoperability:** with no published protocol, the safest bet is plain, documented exports: CSV or Parquet time series per ring and per stroke, JSON event logs, and possibly an OPC UA server (see §6). A generic "machine data" export lets tools of this kind ingest simulated drives, for example for training or for testing dashboards.

---

## 2. VMT GmbH (vmt.global) — guidance, navigation, segment management, data

### 2.1 Company
VMT is based in Bruchsal, Germany. It works on automated surveying and navigation for tunnelling, plus industrial measurement (VMT IMS). ([vmt.global/en](https://vmt.global/en/) [vendor]) Herrenknecht describes VMT as a **Herrenknecht subsidiary** ([Herrenknecht, Vortriebsprozesse steuern](https://www.herrenknecht.com/de/produkte/productdetail/vortriebsprozesse-steuern/) [vendor]). VMT data now flows into **Herrenknecht.Connected** (§3.6).

### 2.2 TBM navigation (TUnIS Navigation family)
These come from the [TBM product list](https://vmt.global/tunnelling/de/tbm/) [vendor]:
- **TUnIS Navigation TBMLaser** (EPB, Mixshield, hard-rock shield). A **robotic total station** on the tunnel wall tracks an **active laser target** in the shield. Position relative to the design alignment (DTA) is computed continuously and in real time, and the drive is documented in a database with redundant storage. Accuracy is stated only as "millimetre-accurate", with no number given. Re-setting the total station with the TUnIS.mobile app is claimed to be 2× faster. ([product page](https://vmt.global/tunnelling/de/system/tunis-navigation-tbmlaser/) [vendor])
  - The electronic target unit has a built-in **inclination sensor for pitch and roll** ([search snippet of VMT product info](https://vmt-gmbh.de/wp-content/uploads/2019/05/TUnIS%20Navigation%20TBM%20Laser_Product_Info_GB.pdf) [vendor], PDF itself not retrievable).
- **TUnIS Navigation Double Shield.** The laser target is in the **gripper shield**. A **measurement camera** looks at marker plates in the **front shield** to get the front shield's position relative to the gripper shield, and a front-versus-gripper roll comparison is also available. TUnIS.mono cam serves machines without stroke sensors in the thrust cylinders. ([product page](https://vmt.global/tunnelling/de/system/tunis-navigation-double-shield/) [vendor])
- **TUnIS Navigation Gripper** uses an external 2-axis inclinometer hardened for gripper-TBM vibration ([search snippet, VMT Gripper sheet](https://www.vmt-gmbh.de/wp-content/uploads/Produktinfos/TUnIS_Navigation_Gripper_GB.pdf) [vendor]).
- **TUnIS.MovingStation.** The total station rides on the **back-up gantry**. **Three wireless reference prisms** are fixed temporarily on the lining and leapfrogged forward. Positioning works in two steps: the station locates itself from the prisms, then measures the laser target. Position is fixed once per advance while the station is stationary. Customer-reported results: on Brasov–Sighisoara, surveyors fell from 7 to 4 across 4 TBMs and daily survey time dropped from 2 h to 25 min. On Thames Tideway about 270 wall-bracket positions were avoided. Known limitations: vibration caused early position jumps, and no fix was possible during ring build because of conveyor vibration. ([product page](https://vmt.global/tunnelling/de/system/tunis-moving-station/) [vendor testimonials])
- **SLuM (automatic tailskin clearance measurement).** Measures the **gap between the ring and the tailskin**, in mechanical or ultrasonic versions. It feeds ring-sequence optimisation and also runs stand-alone. ([product page](https://vmt.global/tunnelling/de/system/automatic-tailskin-clearance-measurement-system-slum/) [vendor])
- **RCMS (ring convergence measurement).** A glued-on, reusable, battery-powered **inclinometer on each segment** reports wirelessly. Ring deformation is inferred from changes in segment tilt, starting as soon as the ring leaves the tail. Customer-reported installation time fell from 2–3 people and ≥2 h to 2 people and ≤15 min (Stuttgart 21). ([product page](https://vmt.global/tunnelling/de/system/ring-convergence-measurement-system-rcms/) [vendor])
- **Segment.Check.** **Four cameras** in the TBM plus AI vision inspect each segment just before it is built into the ring, looking for missing dowels, misplaced gaskets, cracks and spalling ([product page](https://vmt.global/tunnelling/de/system/segment-check/) [vendor]).
- **SDS / SDS.Onsite.** Tracks the life cycle of each segment from the precast plant to installation ([Herrenknecht page](https://www.herrenknecht.com/de/produkte/productdetail/vortriebsprozesse-steuern/) [vendor]; [VMT TBM list](https://vmt.global/tunnelling/de/tbm/)).

### 2.3 TUnIS Ring Sequencing ("Ringfolgeberechnung")
From the [product page](https://vmt.global/tunnelling/de/system/tunis-ring-sequencing/) [vendor]:
- **Inputs:** position of the last-built ring, its position relative to the tailskin (from SLuM), TBM position and trend, **thrust-cylinder strokes**, the planned alignment and constraints, and user settings, including the handling of unplanned events.
- **Outputs:** the optimal **orientation of the next ring**, which for a universal tapered ring means its key or rotation position, ready **before the current stroke ends**. Several rings are pre-computed, which helps segment logistics and avoids mis-deliveries. A **Ring Roll Check** add-on compares actual against target ring roll and logs it.
- **Stated objectives:** keep the ring centred in the tailskin, extend the propel cylinders evenly, and avoid overloading segments.
- The algorithm itself is proprietary and not published. The open literature on universal-ring position selection covers the same problem: optimising over key positions to minimise deviation from the DTA, tailskin-clearance violation and cylinder-stroke differences. See [Skelhorn, "A Practical Approach for Precast Concrete Segmental Ring Selection"](https://onemine.org/documents/a-practical-approach-for-precast-concrete-segmental-ring-selection) [paper, paywalled] and a 2025 Chinese study validated on Nanjing Jiangxinzhou Tunnel ([dxkjxb.cqu.edu.cn](https://dxkjxb.cqu.edu.cn/CN/abstract/article/1673-0836/12543) [paper], UNVERIFIED: abstract only).

### 2.4 Microtunnelling and pipe jacking navigation
From the [MT product list](https://vmt.global/tunnelling/en/mt/) [vendor] and the [Herrenknecht Navigation & Monitoring page](https://www.herrenknecht.com/de/produkte/productdetail/navigation-und-monitoring/) [vendor]:
- **MTLaser:** a laser in the launch shaft shines onto a photosensitive target in the machine. Suits straight drives **up to 250 m**.
- **MTHydroLevel:** adds an electronic hose water level for elevation. Straight drives **up to ~450 m**, depending on the project.
- **MTGyro:** gyro-based and needs no line of sight. For small diameters and tight curves, and also for Direct Pipe.
- **MTGyroEMS:** for E-Power Pipe long non-entry drives.
- **MTLaserTotalstation:** for **≥ DN1600**. Claimed to need about 50% fewer control surveys than the gyro option.
- **TUnIS.pipelight / SmartTraverseMT:** automated control traverses.
- **Pipe-jacking monitoring:** bentonite lubrication monitoring and **joint-gap measurement used to compute the maximum permissible jacking force**.
- Example drive (E-Power Pipe, Amprion Bacharach): about 4,150 m total length, longest single drive 688 m, best 130 m in 24 h, curve radius 500 m, 17 m elevation change ([VMT MT page](https://vmt.global/tunnelling/en/mt/) [vendor]).

### 2.5 Conventional tunnelling
TUnIS Navigation **Roadheader** (positions the cutting boom), **Excavator** (positions the cutter head), **Rockbolter** (positions the drill rod), **Positioning Shutter** (formwork), TUnIS.multi measure, TUnIS.wing detect, CT Office, and CT.Connected ([VMT CT page](https://vmt.global/tunnelling/en/ct/) [vendor]). No drill-jumbo or profile-scanner product appears on the current page.

### 2.6 Data management: IRIS → Herrenknecht.Connected
- **IRIS (Integrated Risk and Information System)** is a web database that merged TBM PLC data, manual records, geology and settlement monitoring, with daily, weekly and monthly reports and interactive shift logs. It was developed through **ITC Engineering, a 2010 JV of Züblin and VMT** ([TunnelTalk, Dec 2010](https://www.tunneltalk.com/New-Products-Dec10-Data-management-JV.php) [trade press]). Microtunnel projects used an IRIS.microtunnel variant fed from the Herrenknecht PLC ([vmt-gmbh.de 2014](https://vmt-gmbh.de/en/2014) [vendor]).
- **Current status (UNVERIFIED):** VMT's current TBM product list shows **Herrenknecht.Connected** as the data platform and no longer lists IRIS ([VMT TBM list](https://vmt.global/tunnelling/de/tbm/)). IRIS may have been rebranded or retired.
- **SLS-T** (older VMT TBM guidance system name): we found no current public product page. Older VMT systems used the same architecture of robotic total station, active laser target (ELS, "Electronic Laser System"), radio modems and an industrial PC ([acta.polito.uz paper](https://acta.polito.uz/index.php/journal/article/download/207/58/976) [paper]). An ISARC 2014 paper recommends keeping total-station-to-target distances to about **≤100 m** so refraction does not degrade accuracy ([ISARC 2014](https://www.iaarc.org/publications/fulltext/isarc2014_submission_93.pdf) [paper], via search snippet).

### 2.7 Typical alignment tolerance
Alignment tolerances are commonly specified at around **±75 mm horizontal and vertical** over the whole project ([ISARC 2014 submission 78](https://www.iaarc.org/publications/fulltext/isarc2014_submission_78.pdf) [paper]). This is project-specific. ±50 mm and ±100 mm also appear in contracts (UNVERIFIED: no source found in this survey).

### 2.8 Simulator or training offerings
None found from VMT.

### 2.9 Implications
Section 7 has the full list. In short, the VMT product set describes, piece by piece, the **survey → steer → build ring → measure clearance → choose next ring** loop. We should model that loop generically:
- a simulated total station with noise, line-of-sight and range limits, and periodic re-setup;
- an active target with pitch and roll;
- head and tail deviation from the DTA, with trend;
- a steering display;
- thrust-cylinder stroke differences;
- tailskin clearance;
- a universal-ring key-position optimiser.

---

## 3. Herrenknecht AG (herrenknecht.com)

### 3.1 Machine families and diameter ranges [vendor]

| Type | Diameter range | Ground / principle | Source |
|---|---|---|---|
| EPB shield | **1.7–16 m** | Cohesive soils. The chamber is filled with conditioned spoil, and the screw speed and advance rate set the support pressure. Conditioning with water, bentonite or foam. An open mode is possible in stable ground. Thick-matter pumps or a "Slurryfier box" can follow the screw. Used on more than 500 projects. | [EPB](https://www.herrenknecht.com/de/produkte/productdetail/epb-schild/) |
| Mixshield (slurry) | **4–19 m** (overview: 4.8–19 m) | Bentonite filter cake at the face. An **air cushion** in the working chamber behind a **submerged wall** sets the support pressure. Closed slurry circuit to a separation plant. Jaw crusher in front of the intake screen. Rated for water pressure **above 15 bar**. Saturation divers are preferred above **3.6 bar**. | [Mixshield](https://www.herrenknecht.com/de/produkte/productdetail/mixschild/) |
| Variable Density TBM | **4.8–14 m** | **Four modes in one machine:** (1) slurry with low-density medium (LDSM); (2) closed EPB with bentonite support; (3) classic EPB; (4) slurry with **high-density medium (HDSM)**. Switching happens **in the tunnel with no mechanical change and no chamber entry, while support pressure is held**. Spoil always leaves through a screw. In slurry modes, a Slurryfier box and crusher sit behind the screw. A double-screw option exists from about 6 m. | [VD TBM](https://www.herrenknecht.com/de/produkte/productdetail/variable-density-tbm/) |
| Multi-Mode TBM | **2.4–19 m** | EPB, slurry and open modes. Either a modular design (longer conversion) or a design with parallel integrated systems (quicker conversion, more complex). Shiftable gearbox for high speed in open mode and high torque in EPB mode. | [Multi-Mode](https://www.herrenknecht.com/de/produkte/productdetail/multi-mode-tbm/) |
| Single shield (hard rock) | **2.8–14 m** segmental; **≥1.54 m** pipe jacking (overview: 1.5–14 m) | Disc cutters, rock above **250 MPa** cited. Overcut offset upward for steering. Continuous grouting of the annulus with mortar or pea gravel. Back-loading cutters. | [Single shield](https://www.herrenknecht.com/de/produkte/productdetail/einfachschild-tbm/) |
| Double shield | **2.8–14 m** | Front shield and gripper shield joined by a telescopic shield. **Rings are built during boring in stable ground.** The re-grip changeover takes "a few minutes". In faults the machine switches to single-shield mode (thrust off the last ring, sequential). Fixed lattice-cylinder drives for 3.8–8.2 m, sliding drives above 8.2 m. | [Double shield](https://www.herrenknecht.com/de/produkte/productdetail/doppelschild-tbm/) |
| Gripper TBM | **3.5–12.5 m** (shielded gripper 3.0–3.5 m; overview says 2–12.5 m) | Grippers brace on the rock and the main beam is shifted hydraulically to steer. Probe drilling **up to 100 m** ahead. Support zone L1 (bolts, mesh, arches) and L2 (shotcrete, invert segments). All shields retract to reduce diameter **by up to 150 mm** in squeezing ground. On inclines, 2 of 3 bracing systems are kept engaged. | [Gripper](https://www.herrenknecht.com/de/produkte/productdetail/gripper-tbm/) |
| AVN (microtunnelling, slurry) | **0.4–4.8 m** OD; pipe jacking from DN250, segmental from DN3200 | Cone crusher. Drives **over 1,000 m** possible with interjack stations and bentonite lubrication. AVND variant adds an air cushion. | [AVN](https://www.herrenknecht.com/de/produkte/productdetail/avn-maschine/) |
| VSM shaft sinking | **4.5–18 m** (also stated as 4.5–16 m), depth **up to 250 m** | Telescopic cutting boom with a milling drum (up to 80 rpm). The shaft is flooded and spoil removed hydraulically. The lining is built at the surface and lowered on strand jacks. Rock **up to 140 MPa**. **Up to 5 m per shift**. No people in the shaft. | [VSM](https://www.herrenknecht.com/de/produkte/productdetail/schachtabsenkanlage-vsm/) |

Other Herrenknecht lines, not examined in detail: Direct Pipe, E-Power Pipe, Pipe Thruster, auger boring, Shaft Boring Roadheader (SBR), Shaft Boring Cutterhead (SBC), SBE, Shaft Drilling Jumbo, segment production plants, Combisegments ([Herrenknecht DE home](https://www.herrenknecht.com/de/)).

Common features across the range [vendor]:
- **Adaptive tail-seal greasing** dosed in kg per m² of segment surface, claimed to save up to 30% grease ([EPB page](https://www.herrenknecht.com/de/produkte/productdetail/epb-schild/)).
- A pressure lock for hyperbaric interventions.
- Back-loading cutters on hard-rock machines.
- Optional real-time sensors that detect blocked or damaged cutters, plus a cutter database of change intervals ([Abbauwerkzeuge](https://www.herrenknecht.com/de/produkte/productdetail/abbauwerkzeuge/)).

### 3.2 Published machine data (validation targets)

| Project | Machine | Diameter | Power | Torque | Other | Source |
|---|---|---|---|---|---|---|
| Crossrail, London | 6× EPB | 7,080 mm | 1,920 kW | 9,800 kNm | segmental lining | [Herrenknecht ref](https://herrenknecht.com/en/references/referencesdetail/crossrail-london) [vendor, via snippet] |
| Crossrail, London | 2× Mixshield | 7,080 mm | 1,120 kW | 3,709 kNm | | same |
| Tuen Mun–Chek Lap Kok, HK | Mixshield S-880 | 17,630 mm | 5,600 kW | 27,722 kNm | | [Herrenknecht ref](https://herrenknecht.com/en/references/referencesdetail/hong-kong-tuen-mun-chek-lap-kok-link) [vendor, via snippet] |
| Tuen Mun–Chek Lap Kok, HK | 2× Mixshield | 13,950 mm | 4,900 kW | 24,256 kNm | | same |
| Gotthard Base Tunnel | Gripper S-210 | 9.33 m | 3,500 kW | 5,290 kNm | 27,488 kN thrust | trade press via search, **UNVERIFIED** (candidates: [Tunnelbuilder](https://tunnelbuilder.com/News/Herrenknecht-TBM-Tackles-Gotthard-Base-Tunnel-from-North.aspx), [T&T](https://tunnelsandtunnelling.com/?p=5739)) |
| Gotthard Base Tunnel | Gripper S-229 | 9.58 m | 3,500 kW | — | 5.3 rpm rated | same, **UNVERIFIED** |
| Follo Line, Norway | 4× double shield | 9.96 m | 4,550 kW (stated; sources inconsistent) | — | 265 t cutterhead; rock to 300 MPa; peak **155 m/week**; 14–15 rings/day ≈ **27 m/day** typical | [TunnelTalk Oct 2018](https://tunneltalk.com/Technical-achievements-and-specifications-of-the-Follo-Line-breakthrough-TBMs-11Oct2018.php) [trade press]; [Tunneling Online](https://tunnelingonline.com/final-double-breakthrough-on-norways-follo-line/) |
| Palomino, Dominican Rep. | double shield | — | — | — | **250 m/week**, bored and lined | [Double shield page](https://www.herrenknecht.com/de/produkte/productdetail/doppelschild-tbm/) [vendor] |
| Legacy Way, Brisbane | (Herrenknecht, 11–13 m class) | — | — | — | best day **49.7 m**, week **248.8 m**, month **787.8 m** | [Robbins world-records table](https://www.robbinstbm.com/news-and-media/world-records/) [vendor, industry-wide] |
| La Cabrera, Spain | Herrenknecht S-373 (9–10 m class) | — | — | — | best day **105.6 m**, week **435 m**, month **1,600 m** | same |
| Waterview, NZ | Herrenknecht S-764 (≥14 m) | 14.4 m (per VMT) | — | — | best day **29.8 m**, avg **303 m/month** | same; [VMT Waterview](https://www.vmt-gmbh.de/en/waterview-connection-new-zealands-largest-infrastructure-project/) |

### 3.3 Segment erection, automation and cutter changing
- **Erector simulator** ([Herrenknecht erector simulator brochure, CN](https://www.herrenknecht.com.cn/fileadmin/user_upload/Main_Website/06_Innovation/Erector_simulator_CN.pdf) [vendor], translated):
  - stand-alone trainer built around **original control panels**, which can later be used on the real TBM unchanged;
  - project-specific virtual environment covering machine layout, segment division and segment design;
  - trains erector degrees of freedom (proportional and digital), thrust cylinders, the **segment feeder** and the **vacuum lifter**;
  - visualises each segment's placement against its target position and keeps a digital record of trainee performance;
  - **used on Crossrail (8 TBMs)**.
- **Automated segment placement:** Herrenknecht holds a patent on automated erection with a manipulator moving axially, radially and tangentially, and a feeder that delivers segments in a set order ([US11913337B2](https://patents.google.com/patent/US11913337) [patent]). Do not copy patented mechanisms. Generic kinematics are fine.
- **Robotics on site:** on HS2, a KUKA robot arm on a Herrenknecht TBM removes timber spacers from segments ([Construction Index](https://www.theconstructionindex.co.uk/news/view/robot-arm-eliminates-hazard-for-hs2-tunnellers-video) [trade press]).
- **Cutter changing:** back-loading cutters changed from inside the cutterhead are standard on hard-rock machines [vendor]. We found **no public Herrenknecht spec for a cutter-changing robot** (UNVERIFIED). Industry examples include the Bouygues "Telemach" arm and research robots from the EU NeTTUN project ([NFF paper, Lorant & Combe](https://nff.no/wp-content/uploads/sites/2/2020/04/21-Lorant-and-Combe.pdf); [TunnelTalk 2013](https://www.tunneltalk.com/Research-and-Development-14May2013-Robotised-maintenance-of-TBM-cutting-tools.php)).

### 3.4 Customer training
Utility-tunnelling customer training (operation, hydraulics, TBM monitoring) runs at factory acceptance in Schwanau or on site ([Herrenknecht training](https://www.herrenknecht.com/en/services/transportation-and-jobsite-assembly/utility-tunnelling-customer-training/) [vendor]). A VR training programme on the TELT CO67 site (Turin–Lyon) covered three modules: safety induction, erector simulator and disc-cutter replacement ([Taylor & Francis chapter](https://www.taylorfrancis.com/chapters/oa-edit/10.1201/9781042001064-252/immersive-vr-training-tbm-operations-case-study-telt-co67-construction-site-chedly-comin-positano-rodriguez-polania-bsaibes-alfonso-blersch) [paper]). Whether Herrenknecht was the vendor of that programme is **UNVERIFIED**.

### 3.5 Navigation and monitoring
Herrenknecht sells VMT navigation (see §2). For pipe jacking it also offers a bus system that moves the control container to the launch shaft for non-man-entry diameters ([Navigation & Monitoring](https://www.herrenknecht.com/de/produkte/productdetail/navigation-und-monitoring/) [vendor]).

### 3.6 Herrenknecht.Connected (data platform)
From the [Herrenknecht.Connected page](https://www.herrenknecht.com/de/services/herrenknechtconnected/) [vendor]:
- Herrenknecht equipment carries **up to 3,000 sensors**.
- **TBM.Connected** mirrors the operator cockpit screens almost in real time. It provides dashboards (daily, weekly and monthly advance, drive power, **ring cycle times**), automatic PDF reports, sensor charts, navigation and map views (with VMT TUnIS), and data export.
- **Add-ons:** Shift.On (shift log, availability), Maintenance.On, Tools.On (cutter performance), Spares.On, SDS.ON (segment production), **3D.ON** (3D tunnel with rings and segments enriched by sensor data), MT.ON (machines up to 4.8 m), SBR.Connected, Conveyor.On.
- **Exports:** sensor data, instantaneous values, and **per-ring statistics (min, max, start, end)** as **PDF and Excel**. An **IFC interface is announced** for BIM. OPC UA or a public API are **not mentioned**.

### 3.7 Implications
- Define diameter-bounded presets for each machine type using the table in §3.1.
- Model the Variable Density modes as states of a single machine, with continuous transitions and support pressure conserved.
- Build an erector-training module, with original-panel-like controls and a segment feeder and vacuum lifter, using generic kinematics only.
- Produce per-ring statistics exports.

---

## 4. The Robbins Company (robbinstbm.com)

### 4.1 Machine families [vendor]

| Type | Diameter | Cutters | Notes | Source |
|---|---|---|---|---|
| Main Beam (open gripper) | **3–15 m** | **14"–20"** discs | Floating grippers allow steering during the stroke. Rear legs lower at the end of the stroke while the machine re-grips. Muck buckets feed a conveyor in the main beam. Options: probe drills, roof drills, ring-beam erectors, McNally-type supports, and a data logger recording penetration rate, thrust pressure, cutterhead rpm and gripper pressure. Robbins Main Beams have bored about **3,000 km** in total. | [Main Beam](https://www.robbinstbm.com/products/tunnel-boring-machines/main-beam/) |
| Double Shield | **1.6–15 m** | — | Built since 1972. Double-shield mode bores while erecting rings. Single-shield mode is sequential. China Challenge: **1,349 m in one month** with 4.2–5.0 m machines. | [Double Shield](https://www.robbinstbm.com/products/tunnel-boring-machines/double-shield/) |
| Single Shield | **1.6–15 m** | **11"–20"** | Articulated cutterhead steering. **10,000 h** design life. Options include an ultra-high emergency thrust for squeezing ground and probe drilling. | [Single Shield](https://www.robbinstbm.com/products/tunnel-boring-machines/single-shield/) |
| EPB | e.g. 6.3 m (SF Central Subway) | discs or picks | Seals against up to **10 bar** water. 10,000 h design life. Copy cutter for overcut. Chengdu Metro L2: disc wear only **4.1 mm** after 1,400 m of drive. | [EPB](https://www.robbinstbm.com/products/tunnel-boring-machines/earth-pressure-balance/) |
| Crossover **XRE** (rock/EPB) | e.g. 8 m (Grosvenor decline), 8.7 m (TEP II, Mexico City, 20" cutters), 9.26 m (Akron) | discs plus carbide bits | Converts between pressurised EPB, open EPB and open hard-rock modes by changing the muck path: rock-capable screw, or screw versus belt. **Above 12 m the belt and screw can coexist**, with a hydraulic muck ring moving the belt into position. Single-direction cutterhead. Two-speed gearboxes and VFDs give high torque at low rpm. | [Crossover](https://www.robbinstbm.com/products/tunnel-boring-machines/crossover-machines/); [TEP II / Akron via search](https://www.unitracc.com/e-journal/news-and-articles/mexico-city2019s-record-breaking-crossover-tbm-makes-final-breakthrough), [TunnelTalk 2017](https://tunneltalk.com/USA-29Jun2017-Robbins-Crossover-TBM-first-for-USA.php) |
| Crossover **XSE** (slurry/EPB) | — | — | EPB mode for low-permeability ground. Slurry mode uses a closed slurry box with a crusher for high permeability or pressure. | [Crossover](https://www.robbinstbm.com/products/tunnel-boring-machines/crossover-machines/) |

The page also lists back-up systems, SBUs and Rockhead units (small-bore). It shows **no "XRS"** product (UNVERIFIED whether one exists).

### 4.2 Disc cutters: rated capacity by size
Source: [Robbins Disc Cutters spec sheet](https://www.robbinstbm.com/wp-content/uploads/2017/04/DiscCutters_SpecSheet_V3.pdf) [vendor], text extracted from the PDF.

| Size | Mounting | Rated load |
|---|---|---|
| 6.5 in / 165 mm | front, V-block | 53 kN (12,000 lb) |
| 9.5 in / 241 mm | front, V-block | 80 kN |
| 11.5 in / 292 mm | front, V-block | 111 kN |
| 12 in / 305 mm | front/back, wedge-lock or V/O-block | 120 kN |
| 13 in / 330 mm | front/back | 120 kN |
| 14 in / 356 mm | front & back | 178 kN |
| 15.5 in / 394 mm | front & back | 267 kN |
| 17 in / 432 mm | front & back | 267 kN |
| **19 in / 483 mm** | front & back, wedge-lock | **311 kN** (70,000 lb) |
| **20 in / 508 mm** | front & back, wedge-lock | **311 kN** (70,000 lb) |

Robbins says it was first with 19" cutters and with the wedge-lock mount, and that 20" cutters exist mainly for longer life ([Cutters](https://www.robbinstbm.com/products/cutters/) [vendor]). Construction: Timken tapered roller bearings, preloaded; metal face seals; a pressure-compensation retainer; disc rings forged from vacuum-degassed EAF tool steel [vendor].

### 4.3 Niagara Tunnel (largest hard-rock Main Beam at the time)
- **14.4 m diameter**. **85 cutters**: 20" face and gauge cutters, 17" centre cutters. Nominal **35 t per cutter** (≈343 kN), operating up to **50 t per cutter**. Cutterhead **0–5.0 rpm**. Torque about **18,800 kNm at low speed (0–2.4 rpm)** and **9,025 kNm at 5 rpm**. ([technical fact sheet on Scribd](https://www.scribd.com/doc/250968184/Niagara-Tunnel-Project-Technical) [secondary, via search])
- Thrust **18,462 kN**, max torque **18,670 kNm** ([Robbins project page](https://www.robbinstbm.com/projects/niagara-tunnel-project/) [vendor, via search snippet])
- Power: **about 4.7 MW from 15 motors** ([Wikipedia](https://en.wikipedia.org/wiki/Niagara_Tunnel_Project) [secondary]). The contract figure was 4,725 kW VFD, upgradable to 5,040 kW. The power figures are **inconsistent**.
- Records: best week **153 m**, best month **468 m** in the ≥14 m class ([world records](https://www.robbinstbm.com/news-and-media/world-records/)).

### 4.4 World advance-rate records by diameter (industry-wide, all manufacturers)
Source: [Robbins World Records page](https://www.robbinstbm.com/news-and-media/world-records/) [vendor; the table covers competitors too]. Years are not given in the table. MB = Main Beam, DS = Double Shield.

| Diameter class | Best day | Best week | Best month | Best monthly average |
|---|---|---|---|---|
| 3.01–4.00 m | 172.4 m (Robbins Mk12C, Katoomba Carrier, AUS) | 703 m (same) | 2,066 m (Robbins MB, Oso Tunnel, USA) | 1,189 m (Katoomba) |
| 4.01–5.00 m | 128.0 m (Robbins MB, SSC No.4, Texas) | 477 m (same) | 1,822 m (Robbins DS, Yellow River 4&5, CHN) | 1,352 m (Robbins DS, Yellow River Lot V) |
| 5.01–6.00 m | 99.1 m (Robbins MB, Little Calumet, Chicago) | 562 m | 2,163 m | 1,095 m (Robbins DS, Yindaruqin) |
| 6.01–7.00 m | 124.7 m (Robbins MB, Indianapolis DRT) | 515.1 m | 1,754 m | 1,187 m (Robbins MB, Dallas) |
| 7.01–8.00 m | 115.7 m (Robbins MB, Kárahnjúkar, ISL) | 428 m | 1,482 m (Robbins MB, TARP Chicago) | 770 m |
| 8.01–9.00 m | 75.5 m (Robbins, Channel Tunnel) | 428 m | 1,719 m | 873 m |
| 9.01–10.00 m | 105.6 m (Herrenknecht S-373, La Cabrera) | 435 m | 1,600 m | 715 m (Robbins, TARP) |
| 10.01–11.00 m | 48.8 m (Robbins, TARP) | 235 m (Robbins, West Qinling) | 841.8 m | — |
| 11.01–13.00 m | 49.7 m (Herrenknecht, Legacy Way) | 248.8 m | 787.8 m | — |
| 13.01–14.00 m | 32.4 m (Robbins, Esme–Salihli, TUR) | 178.2 m | 721.8 m | — |
| ≥14.01 m | 29.8 m (Herrenknecht S-764, Waterview) | 153 m (Robbins, Niagara) | 468 m (Niagara) | 303 m (Waterview) |

Other Robbins-reported performance: a 7.9 m Main Beam in Jilin, China, made **1,423.5 m in a month** (a national record) ([Robbins news via search](https://robbinstbm.com/category/news/page/2) [vendor], UNVERIFIED). Himalayan geology: **1,224.13 m in June 2023** ([same](https://www.robbinstbm.com/category/news/) [vendor], UNVERIFIED).

### 4.5 Conveyors
Continuous tunnel conveyors that extend as the TBM advances, then vertical conveyors (**up to 200 m shaft lift**), overland conveyors and stackers. Capacity **above 1,000 t/h**. Used on more than 100 projects. Benefits claimed: fewer and smaller trains, less ventilation, lighter track. ([Conveyors](https://www.robbinstbm.com/products/conveyors/) [vendor]) Belt-storage cassettes and booster drives are a standard part of continuous-conveyor practice, but **this page does not detail them** (UNVERIFIED for Robbins).

### 4.6 Simulator and operator training
Robbins (S. Chorley, RETC 2017) published "Use of 'Command Chair' Simulator Technology to Optimize Modern TBM Performance" ([PDF](https://www.robbinstbm.com/wp-content/uploads/2017/07/Chorley_CommandChair_RETC2017.pdf) [paper], text extracted):
- It argues for formal TBM-operator certification: ITA-CET classroom training of **80 h over 10 days**, plus a simulator.
- An **EPB simulator was developed by the Colorado School of Mines** with input from a US TBM maker. It runs **five scenarios**, each simulating chamber-pressure control during boring and during ring-build standstill, with **1.5 m ring advances**:
  1. sand;
  2. clay (from normally consolidated soft clay to over-consolidated stiff clay);
  3. a sand↔clay transition at a set distance into the ring;
  4. mixed face, clay over sand or the reverse, over up to five rings with a moving interface;
  5. homogeneous ground with horizontal and vertical curves.
- Adjustable parameters: tunnel depth, groundwater table and soil parameters. **Ring building itself is not simulated.**
- Next step proposed in the paper: run the simulator inside a real **operator cab or "command chair"**, with ergonomic seating, a minimal hard-panel set, two touchscreens, and a line of sight to the conveyor and the top 120° of the ring-build area.
- Related: ITA-CET's TBM driver certification includes simulator training and assessment ([ITA-CET](https://www.itacet.org/all-news/tbm-driver-certification-scheme/)). EFNARC runs a TBM pilot scheme ([EFNARC](https://efnarc.org/tbm-pilot-scheme)).

### 4.7 Implications
- Use the cutter load table as the cutter-capacity limit in the CSM model.
- Use the world-record table as an **upper-bound sanity check**: a simulated machine should not beat these rates in its diameter class without a reason.
- Treat the CSM EPB simulator scenarios as a ready-made **training curriculum** we can reproduce, and go further than it did by also simulating ring build.

---

## 5. The Boring Company (boringcompany.com)

### 5.1 Machines
From [boringcompany.com/prufrock](https://boringcompany.com/prufrock) [vendor] unless noted:
- **Prufrock (soft ground)** **installs the precast lining while it mines**. The page contrasts this with conventional soft-ground TBMs that mine about 5 ft, stop to build the ring, then resume.
- **"Porpoising" launch and exit.** The TBM arrives by truck, tilts down and launches from the surface **within 24 hours**, with no launch pit and no large crane. It finishes by mining up onto a trailer ("The Monster") that carries it to the next site.
- **Remote operation:** designed for **zero people in the tunnel during normal operation**, run from an Operations Control Center in **Bastrop, Texas**.
- **Prufrock-MB (Main Beam)** is the hard-rock variant, where the rock itself serves as the lining. **MB1 and MB2** are boring limestone of **10,000+ psi (about 69 MPa)** in Nashville for Music City Loop.
- TBC makes its own TBMs and liners and uses **one standard tunnel design** with large structural safety factors.
- Targets: **more than 1 mile per week** (≈1.6 km/week, ≈230 m/day), and an **all-in Loop tunnel cost under $5M per mile**. A secondary source says **under $8M per mile** ([basenor](https://www.basenor.com/blogs/news/boring-company-prufrock-mines-continuously-runs-globally-from-texas) [secondary]), so the figures conflict and the primary $5M figure is preferred. The 1 mile/week target is described as about **6× the previous-generation Godot+** ([basenor](https://www.basenor.com/blogs/news/boring-company-prufrock-mines-continuously-runs-globally-from-texas) [secondary]).
- Long-term goal of **7 miles per day**, framed as "1/10 of human walking speed" ([secondary, via search](https://www.basenor.com/blogs/news/boring-company-prufrock-mines-continuously-runs-globally-from-texas)). **UNVERIFIED**, and sources disagree whether it applies to Prufrock-3 or Prufrock-5.

### 5.2 Geometry
- **LVCC Loop** tunnels: **outer diameter 13.5 ft (4.11 m), inner diameter 12 ft (3.66 m)**. Each tunnel was bored in about 4 months. ([ENR](https://enr.com/articles/51596-elon-musks-boring-co-completes-first-commercial-project) [trade press])
- Hawthorne test tunnel: a 14 ft TBM gave a 12 ft internal diameter ([Wikipedia mirror, via search](https://www.doc.surf/wiki/the-boring-company) [secondary], UNVERIFIED).
- Dubai Loop: 12 ft (3.6 m) tunnels. About 25,000 segments for phase 1, each roughly **1,800 kg (~4,000 lb)**. ([Gulf Construction](https://gulfconstructiononline.com/Article/465870/Dubai_Loop_work_kicks_off_with_tunnel_lining_production); [TradeArabia](https://www.tradearabia.com/News/464737/Dubai-Loop-work-begins-as-production-starts-on-45-000-tonne-tunnel-lining/CONS) [trade press])
- Typical depth is **more than 30 ft**. The company says surface noise and vibration become negligible once the TBM is two diameters deep. ([boringcompany.com/tunnels](https://boringcompany.com/tunnels) [vendor])

### 5.3 Projects and performance
- **LVCC Loop:** 1.7 miles of tunnel and 3 stations, built in about a year for about $47M fixed price. Opened April 2021. ([tunnels page](https://boringcompany.com/tunnels) [vendor])
- **Vegas Loop:** approved for 68 miles and 123 stations, with more than 4 million passengers carried ([tunnels page](https://boringcompany.com/tunnels) [vendor]).
- Other projects: Music City Loop (Nashville, under construction); **Dubai Loop pilot** (6.4 km, 4 stations); Tesla Gigafactory "Cybertunnel", where **Prufrock-3 was extracted through the factory building**; 7 R&D tunnels at Hawthorne, Adelanto and Bastrop ([tunnels page](https://boringcompany.com/tunnels) [vendor]).
- **Prufrock-2 record:** a **2.28-mile single drive** for the Vegas Loop in March 2026, moving about 68,000 yd³ of spoil through a **4.8-mile continuous conveyor driven by 6 motors totalling 825 hp** ([basenor](https://www.basenor.com/blogs/news/boring-company-prufrock-mines-continuously-runs-globally-from-texas) [secondary, citing a TBC X post]). **UNVERIFIED.**
- "About one mile per week as of early 2026" ([Plunkett Research](https://www.plunkettresearch.com/?p=1932898) [secondary]). **UNVERIFIED.** No independently audited sustained rate was found.
- Fleet (secondary, **UNVERIFIED**): Prufrock-1 has completed 6 tunnels; Prufrock-4 is planned for Nashville; Prufrock-5 left the factory in Nov 2025; Prufrock-6 and -7 are in development ([basenor](https://www.basenor.com/blogs/news/boring-company-prufrock-mines-continuously-runs-globally-from-texas)).
- **Not published:** thrust, torque, power, rpm, cutter layout, segment ring width, or the continuous-erection mechanism. Do not invent these. Any Prufrock-like preset in our simulator must be labelled as a generic "continuous small-bore EPB" with assumed parameters.

### 5.4 Implications
- **Continuous advance** (ring build overlapping excavation) should be a first-class machine capability. The double shield already does this in hard rock, and we would extend it to soft ground. It changes the cycle-time model and the thrust-reaction path: part of the jacks thrust while others hold the ring being built. It also needs a consistent rule for how thrust is shared with the new ring. A 2024 patent family describes one approach (thrust shells and expanding ring) and estimates up to about 2× daily advance in soft ground ([US12209498](https://patents.google.com/patent/US12209498) [patent]). Japanese "F-NAVI" simultaneous excavation and erection is a prior example (ITA WTC 2003, details UNVERIFIED).
- **Porpoising:** a launch and retrieval scenario from the surface, at shallow cover, with an inclined entry. It must include a check on face stability and settlement at very low cover (C/D < 1 at the start), which our Peck and wedge models can handle.
- **Remote and autonomous operation:** a "zero people in tunnel" mode, meaning the operator drives from a remote control-room UI and the logistics are all automated. Our browser UI can play that control room.
- **Small-diameter logistics:** the continuous conveyor is the bottleneck when advance is fast, so conveyor capacity, belt extension and storage need to be modelled.

---

## 6. Interoperability and data standards (cross-cutting)

- **OPC UA:** none of the five companies publicly names OPC UA as an export interface, and **no tunnelling-specific OPC UA companion specification** turned up in this search. It is still the de facto industrial interface for PLC data, so a simulator-side **OPC UA server exposing a generic TBM tag tree** would let real SCADA, HMI and data-platform tools connect to the simulator. That is useful for operator training and for testing data platforms. Use a neutral tag naming scheme, not any vendor's.
- **Exports seen:** PDF and Excel (Herrenknecht.Connected, TPC), per-ring min/max/start/end statistics (Herrenknecht.Connected), APIs and DB views for segment data (TPC). **IFC** was announced by Herrenknecht.Connected. buildingSMART's **IFC 4.3** covers alignment (`IfcAlignment`), and IFC Tunnel extensions are in development (UNVERIFIED: status not checked in this survey).
- **Recommendation:** use our own open, documented schema:
  - `run.json` (machine preset, geology, alignment);
  - `timeseries.parquet` or `.csv` (1 Hz to 10 Hz channels);
  - `rings.csv` (ring number, key position, taper, start and end chainage, cylinder strokes, tailskin clearances, deviations);
  - `events.jsonl` (mode switches, cutter changes, alarms, stoppages coded by subsystem);
  - alignment input in **LandXML** or IFC 4.3 alignment.

---

## 7. Implications for the simulator: prioritized list

**P0: core realism and validation (do first)**
1. **Machine presets from public numbers.** Diameter-bounded families per type: EPB 1.7–16 m; slurry 4–19 m; VD 4.8–14 m; single shield 1.5–15 m; double shield 1.6–15 m; gripper/main beam 2–15 m; microtunnel 0.4–4.8 m; VSM shaft 4.5–18 m. Seed with concrete reference machines:
   - "Generic 7.1 m urban EPB": 1,920 kW, 9,800 kNm (Crossrail-class).
   - "Generic 14.4 m hard-rock main beam": 85 cutters, 20"/17", 0–5 rpm, ≈18,500 kN thrust, ≈18,700 kNm (Niagara-class).
   - "Generic 9.9 m double shield": rock to 300 MPa, ~27 m/day typical (Follo-class).
   - "Generic 17.6 m slurry": 5,600 kW, 27,700 kNm (TM-CLK-class).
   - "Generic 3.7 m continuous small-bore EPB" (Loop-class, parameters assumed).

   Name presets by class, never by brand or project. Keep the source URL in preset metadata.
2. **Cutter capacity table** (Robbins sheet): rated load by disc diameter, used as the hard limit on normal force in the CSM model. Thrust per cutter × number of cutters bounds the total thrust.
3. **Advance-rate validation harness.** Compare simulated best-day, week and month against the industry world-record table by diameter class (§4.4) as an upper bound, and against typical rates (Follo 27 m/day; Palomino 250 m/week; China Challenge 1,349 m/month). Flag any run that exceeds a record.
4. **Guidance loop.** Simulated total station (range ≲100 m before re-setup; noise; loss of line of sight in tight curves), active target with pitch and roll, head and tail deviation from the DTA, trend arrows, steering via differential thrust-cylinder pressure groups or articulation, and project tolerance (default ±75 mm, configurable). Include a "moving station" option (station on the back-up, prisms leapfrogging) as an alternative survey mode.
5. **Ring build and universal-ring selection.** Tapered universal ring with N key positions. Choose the next key position by minimising a weighted cost of (a) predicted deviation from the DTA, (b) tailskin-clearance violation, (c) spread of cylinder strokes, (d) joint-pattern rules such as no cruciform joints. Pre-compute several rings ahead. Log the result to `rings.csv`. This is a generic optimisation from public principles, not VMT's algorithm.

**P1: process features that distinguish machine types**
6. **Mode switching:**
   - Variable-density style: LDSM ↔ EPB+bentonite ↔ EPB ↔ HDSM, switched continuously with support pressure held. In fluid modes, pressure is set by the air cushion. In EPB modes, it is set by screw speed and advance rate.
   - Crossover style: EPB ↔ open rock, with a muck-path change and a downtime cost.
   - Multi-mode: modular (long conversion) versus integrated (short conversion, higher capex).
7. **Continuous advance:** double-shield simultaneous boring and ring build, and a Prufrock-style soft-ground continuous mode in which a subset of jacks holds the ring under erection. Default stroke-and-build cycle for single shields and EPB machines. Report utilisation separately for each.
8. **Cutter wear and change logistics:** wear per disc from the CSM/CAI model, real-time "blocked cutter" detection, back-loading change time versus hyperbaric intervention (divers above ~3.6 bar, saturation for high pressure), cutter inventory. Keep a "robotic changer" as an optional, generic module.
9. **Muck logistics:** continuous conveyor (>1,000 t/h class, vertical lift up to ~200 m), versus trains, versus a slurry circuit to a separation plant. Conveyor or slurry capacity caps the advance rate.
10. **Hard-rock open-machine cycle:** gripper re-grip at the end of the stroke, L1 and L2 support zones (bolts, mesh, arches, shotcrete), probe drilling ahead (up to ~100 m), and retracting shields to reduce diameter (−150 mm) in squeezing ground.

**P2: training and operations layer**
11. **Operator-training scenarios**, modelled on the CSM/Robbins EPB set: sand; clay; transition; mixed face with a moving interface; curves. Add the pieces that set missed: ring build, standstill pressure decay, and settlement feedback (Peck). Build a **segment-erector trainer** with joystick DOFs, segment feeder and vacuum lifter, and score placement accuracy.
12. **Telemetry, reports and replay** in TPC and Connected style: shift, daily, weekly and monthly reports, availability and utilisation, downtime coded by subsystem, per-ring statistics, settlement plotted against face chainage, a timeline replay, and alarms with thresholds.
13. **Monitoring sensors:** tailskin clearance (SLuM-like), ring convergence from segment tilt (RCMS-like), surface settlement markers. Feed them all into the same alarm system.
14. **Remote and "zero people in tunnel" control-room mode**, plus a shallow **surface-launch (porpoising) scenario** with low-cover face-stability checks.

**P3: interoperability**
15. An **OPC UA server** with a neutral TBM tag model, CSV/Parquet/JSON exports, LandXML or IFC 4.3 alignment import, and optional IFC export of the as-built rings.
16. Microtunnelling and pipe jacking: jacking-force build-up from skin friction, interjack stations, a lubrication model, a joint-gap → allowable-force check, and guidance mode chosen by drive length (laser ≤250 m, hose level ≤450 m, gyro or total station beyond).
17. Shaft sinking (VSM-like): lining lowered from the surface, flooded excavation, up to 5 m per shift.

### IP and trademark cautions
- **Do not use** company names, logos, colour schemes or product names as UI labels or preset names. This covers Herrenknecht, VMT, Robbins, The Boring Company and Tunnelsoft, and product names such as **Mixshield, Variable Density TBM, Direct Pipe, E-Power Pipe, TUnIS, SLuM, RCMS, IRIS, Crossover/XRE/XSE, Wedge Lock, Prufrock, Loop, TPC, Herrenknecht.Connected**. Use generic terms instead: "slurry shield with air cushion", "variable-density / multi-mode shield", "rock/EPB convertible", "universal-ring sequencing", "tailskin-clearance sensor". Factual references with citations in documentation are fine.
- **Do not copy** vendor HMI screen layouts, control-panel graphics, PDF diagrams, 3D models or photos. Model cutterhead layouts from public principles (spiral or rule-based cutter spacing, gauge and centre cutters) rather than tracing vendor drawings.
- **Patents:** automated segment erection (Herrenknecht US11913337B2), a continuous-advance thrust-shell concept (US12209498), and TBM simulator equipment (US12106683) are patented. Simulating the *physics* of a process is generally different from building the patented apparatus, but avoid reproducing claimed mechanisms in detail and get legal review before any hardware-in-the-loop or control-software use.
- **Data:** citing published numbers as defaults and validation targets with attribution is fine. Do not redistribute vendor PDFs. Link to them instead.
- **Disclaimers:** presets labelled "X-class" should state that they are approximations from public data and are not endorsed by, or representative of, any manufacturer.

---

## Appendix: key source URLs
- Tunnelsoft: https://tunnelsoft.com , https://tunnelsoft.com/solutions/tbm-tunnelling/
- VMT: https://vmt.global/tunnelling/de/tbm/ , https://vmt.global/tunnelling/en/mt/ , https://vmt.global/tunnelling/en/ct/ , product pages under https://vmt.global/tunnelling/de/system/
- Herrenknecht: https://www.herrenknecht.com/de/ , product pages under https://www.herrenknecht.com/de/produkte/productdetail/ , https://www.herrenknecht.com/de/services/herrenknechtconnected/
- Robbins: https://www.robbinstbm.com/products/tunnel-boring-machines/ , https://www.robbinstbm.com/news-and-media/world-records/ , https://www.robbinstbm.com/wp-content/uploads/2017/04/DiscCutters_SpecSheet_V3.pdf , https://www.robbinstbm.com/wp-content/uploads/2017/07/Chorley_CommandChair_RETC2017.pdf
- The Boring Company: https://boringcompany.com/prufrock , https://boringcompany.com/tunnels , https://enr.com/articles/51596-elon-musks-boring-co-completes-first-commercial-project
