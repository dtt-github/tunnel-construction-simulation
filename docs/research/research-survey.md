# Open-Source Tunnel Construction Simulator: Research Survey

*Compiled 4 Nov 2026. Covers physics engine options, published models and numerical methods, and standards, then gives a recommended stack and phased roadmap.*

**Verification legend:**
- **[V]** means the claim was checked against a web source during this survey, and the source is linked.
- **[R]** means a standard reference from the literature, cited from domain knowledge. Author, year and venue are believed correct, but the paper text was not re-fetched. Check equations against the original before coding.
- **[UNVERIFIED]** means the claim could not be confirmed. Treat it as a lead, not a fact.

---

## 0. Sister project: `dtt-github/construction-site-simulation` [V]

Source: https://github.com/dtt-github/construction-site-simulation and its `phase0/RESULTS.md`.

| Aspect | Finding |
|---|---|
| Owner | DigitalTwin Technology GmbH, with contributions from universities and industry |
| License | Code is **Apache-2.0**. Assets and data have per-item licenses listed in `NOTICE` and `assets/registry.json` |
| Browser rendering | **three.js** (MIT). Uses WebGPU in Chrome; on Linux ARM this needs `--enable-unsafe-webgpu --enable-features=Vulkan` |
| Browser physics | **Jolt Physics** (MIT), via WASM, for rigid-body site physics |
| Server physics | **NVIDIA Newton 1.7.0 + Warp 1.19.0** on a DGX Spark (GB10, sm_121, driver 580.178.04, CUDA 13.0, Ubuntu 24.04). Soil uses implicit MPM (`SolverImplicitMPM`); machines use MuJoCo articulations |
| Reference engine | Project Chrono / PyChrono 10.0.0 (BSD-3). Its CRM (SPH) terrain is used only as an offline soil reference |
| Server language | Python, with the environment managed by `uv` |
| Transport | WebSockets (`websockets` package) on `ws://127.0.0.1:8765`. The message schema is not documented in the README |
| Other | CoACD collider generation; OpenUSD, URDF and GLB/glTF assets; Gymnasium environment; lidar, depth and IMU sensors; ROS 2 Jazzy bridge; Playwright tests |
| Structure | `phase0/` (platform benchmarks), `phase1/` (SimReady-to-web pipeline, three.js + Jolt site), `phase2/` (Newton soil servers, excavator environment, sensors), `assets/`, `ros2_bridge/`, `reports/`, `research_notes/` |

**Key Phase-0 benchmark results on the DGX Spark:**

- **Soil cutting test:** a 1 m blade cutting 0.2 m deep at 0.5 m/s in sand with φ ≈ 37°.
  - Newton implicit MPM ran about 270k particles at 1.07× real time, about 32 million particle-steps per second. Blade force was 4.0–4.6 kN.
  - Chrono CRM ran 160k particles at 0.038× real time. Blade force was 8.5 kN.
  - Both forces fall inside the analytic range of 3.3–10.9 kN. The authors note that neither has been validated yet.
- **Platform:** all engines ran on ARM64 without source builds. The conda PyChrono build lacks DEM-Engine and Chrono::GPU.
- **Browser compute:** Chrome 156 with WebGPU ran about 2.4 billion particle updates per second on the GB10 with the Vulkan flags, and only about 105 million per second on the CPU software fallback.
- **Determinism:** results are deterministic within a process but vary between processes because of GPU atomics.

**Implication:** reuse this stack (three.js + Jolt in the browser, Newton/Warp on the Spark, WebSockets, Apache-2.0, phased folders). The tunnel simulator can then share assets, tooling and know-how with the sister project, and possibly a common "site" layer later.

---

## A. Physics engine options

### A.1 NVIDIA Newton (Linux Foundation; NVIDIA, Google DeepMind, Disney Research)

- **Status [V]:**
  - The beta was announced in September 2025 (CoRL), and 1.0 GA followed at GTC in March 2026.
  - Releases in 2026: v1.4.0 (16 Jul), v1.5.0 (11 Aug), v1.6.0 (10 Sep), v1.6.1 (5 Oct) and **v1.7.0 (14 Oct 2026, latest)**.
  - Sources: https://github.com/newton-physics/newton/releases and https://github.com/newton-physics/newton
- **License [V]:** Apache-2.0 for code, CC-BY-4.0 for docs.
- **Platforms [V]:** Linux x86-64 and **aarch64**, Windows x86-64, and macOS (CPU only).
  - Requires Python 3.11 or later; 3.10 is deprecated.
  - Warp 1.18+ needs a CUDA GPU with compute capability 7.5+ and driver R580+.
  - v1.7.0 deprecates CUDA 12 GPU support, so CUDA 13 is the forward path. That suits GB10, whose sm_121 target needs CUDA 13.
- **Solvers [V]** (from https://newton-physics.github.io/newton/latest/api/newton_solvers.html):

  | Solver | What it does |
  |---|---|
  | `SolverMuJoCo` | MuJoCo through mujoco_warp; the primary rigid and articulation backend. v1.7 moved to MuJoCo 3.15 |
  | `SolverFeatherstone` | Reduced-coordinate articulated bodies (composite rigid body algorithm) |
  | `SolverKamino` | Constrained multibody with **kinematic loops**, actuation, limits and friction. Experimental. Useful for hydraulic linkages such as thrust cylinders and erector parallelograms |
  | `SolverSteel` | Reduced-coordinate articulations with a projected Gauss-Seidel constraint solve |
  | `SolverXPBD` | Implicit extended position-based dynamics for rigid and soft bodies |
  | `SolverVBD` | Vertex Block Descent for particles, cloth, cables and volumetric soft bodies, plus Augmented VBD for rigids |
  | `SolverStyle3D` | Cloth |
  | `SolverSemiImplicit` | Semi-implicit symplectic Euler integrator |
  | **`SolverImplicitMPM`** | Implicit material point method for **granular and elasto-plastic materials**. This is the soil solver |
  | `SolverCoupled` (v1.4+) | Composes MuJoCo, Kamino, VBD, XPBD and MPM in one workflow. Experimental |

- **Granular / soil [V]:**
  - Implicit MPM supports granular and elasto-plastic soil, including yield pressure and yield stress, Young's modulus and viscosity parameters.
  - v1.7 corrected MPM stress scaling. Scenes tuned before 1.7 must halve `young_modulus`, `yield_pressure`, `yield_stress` and `viscosity`.
  - v1.6 added USD import of authored MPM particles and materials. v1.5 added multi-world isolated MPM.
- **Gaps for tunnelling:**
  - No built-in bonded-particle DEM for brittle rock fracture under disc cutters.
  - No pore-pressure (u–p) two-phase coupling, which matters for groundwater at an EPB face.
  - No critical-state constitutive models (e.g. MCC) documented. **[UNVERIFIED]** whether a custom constitutive hook is exposed. Custom Warp kernels can fill these gaps.
- **DGX Spark [V]:** the sister project runs Newton 1.7.0 and Warp 1.19.0 on GB10 with no workarounds. With 128 GB of unified memory, tens of millions of MPM particles are feasible in memory, but throughput, not memory, will set the real-time limit.
- **Mac development:** Newton runs CPU-only on macOS. That is fine for unit tests and small scenes; real-time MPM needs the Spark.

### A.2 Newton Dynamics (Julio Jerez, C++)

- **License [V]:** zlib. A rigid-body engine (v4.x) with no third-party dependencies. Source: https://github.com/MADEAPPS/newton-dynamics
- **WebAssembly:** the README shows an Emscripten logo, but **no documented or maintained WASM/npm build was found [UNVERIFIED]**.
- **Not recommended:** it has no granular/MPM capability and a small web community. Do not confuse it with NVIDIA Newton; the owner's request "Newton physics library" almost certainly means NVIDIA Newton, given the sister project.

### A.3 Browser-native engines

| Engine | Current status | License | Notes for this project |
|---|---|---|---|
| **Jolt (JoltPhysics.js)** | npm `jolt-physics` **1.1.1** [V], wrapping Jolt C++ ~5.6 [V via pmndrs migration guide] | MIT | Fast, stable and deterministic. Has multithreaded WASM, soft bodies, vehicles, constraints and motors. Already used by the sister project. **Recommended** for browser rigid and kinematic physics |
| Rapier (`@dimforge/rapier3d`) | **0.21.0** [V] | Apache-2.0 | Rust→WASM with a clean API and cross-platform determinism option. The GPU successor (Nexus/wgrapier) is early or dormant [V] |
| PhysX 5 WASM (`physx-js-webidl`, fabmax) | ~2.7.x wrapping PhysX 5.6.x [V, partial] | BSD-3 | Full PhysX feature set, but a large binary and community-maintained. GPU PhysX is not available in the browser |
| ammo.js (Bullet) | Legacy and largely unmaintained [R] | zlib | Avoid for new work |
| MuJoCo WASM (official `@mujoco/mujoco`) | 3.9.0 seen [V]; may be newer | Apache-2.0 | Official DeepMind bindings with single- and multi-thread builds. Good for running the *same* MJCF machine models in browser and server; less suited to many free rigid bodies |
| **WebGPU compute** | Shipping in Chrome, Edge and Safari 26 [R]. Linux needs flags [V] | n/a | MLS-MPM fluids reach 100k particles on an iGPU and about 500k on an RTX 3060 laptop [V]. On GB10, about 2.4 billion particle updates per second with flags [V]. **No published WebGPU Drucker–Prager sand solver found** [V], but porting Klár et al. 2016 to WGSL is straightforward. Use for a local, visual-grade muck and face-collapse patch in the fallback mode |

### A.4 Scientific and geomechanics codes (backend or reference)

| Code | Relevance | License | Status notes |
|---|---|---|---|
| **Kratos Multiphysics: GeoMechanicsApplication** (Deltares/CIMNE) | FE staged construction and excavation, K0 procedure, coupled UPw hydro-mechanics, 2D/3D [V]. Also has MPM, DEM and FEM-DEM applications | BSD-4 (Kratos) [R] | PyPI `KratosGeoMechanicsApplication` 9.5 [V]. Good **offline** generator of ground response surfaces. Docs: https://deltares.github.io/Kratos-GeoMechanicsApplication-Documentation/ |
| **Project Chrono 10** (UW-Madison SBEL) | CRM SPH terrain (MCC, μ(I) rheology), SCM terramechanics, DEM-Engine GPU DEM (150M elements on two A100s), Chrono::Vehicle [V] | BSD-3 | Offline reference for soil cutting and vehicle-on-muck. ARM conda build lacks DEM-Engine [V] |
| **Genesis World** | Multi-solver platform: rigid, FEM, MPM (sand), PBD and SPH [V] | Apache-2.0 [V, third-party] | `genesis-world` 1.1.2 on PyPI [V]. A Newton alternative; smaller geotechnical validation base |
| **Taichi / Taichi-MPM** | MLS-MPM (Hu et al. 2018, SIGGRAPH) [R] | Apache-2.0 | Taichi itself is slowing [UNVERIFIED]. **GeoTaichi** (Taichi-based DEM/MPM for geomechanics) [UNVERIFIED name and venue] |
| **Anura3D** (Deltares-led MPM research community) | Geotechnical MPM with two-phase (soil-water) formulation [R] | Open source; exact license [UNVERIFIED] | Reference for large-deformation face collapse with water |
| **CB-Geo MPM** | C++ MPM for geomechanics [R] | MIT [R] | Reference implementation |
| **YADE** | DEM in C++ and Python; bonded and cohesive contacts, rock fracture [R] | GPL-2 | Offline cutter–rock DEM; GPL means keep it as a separate tool, not linked |
| **MercuryDPM** | DEM with granular rheology and coarse-graining [R] | BSD-3 [R] | Calibration of muck and conditioned-soil DEM parameters |
| **LIGGGHTS(-PUBLIC)** | DEM; CFD-DEM via CFDEMcoupling [R] | GPL | Classic EPB chamber CFD-DEM studies used it; the public version is dormant [R] |
| **OpenSees** | Structural and soil FE; good for lining ring beam-spring models and seismic [R] | BSD-like | Offline lining checks |
| **FEniCSx / MOOSE / Code_Aster** | General FE; MOOSE has geomechanics and porous-flow modules, Code_Aster has hydro-mechanical models [R] | LGPL / LGPL / GPL | Research back-ends; heavy for real-time |
| **Itasca PFC/FLAC, PLAXIS, Abaqus, RS2/RS3** | Industry references (commercial) [R] | Commercial | Use published results from these for validation |

### A.5 Recommended architecture

```
┌──────────────────────────── Browser (Mac/any) ────────────────────────────┐
│ three.js (WebGPU renderer, WebGL2 fallback) + TypeScript                  │
│ Jolt WASM: rigid/kinematic machine parts, segments, erector, muck cars,  │
│            locomotives, conveyors, drill jumbo booms, roadheader boom     │
│ tunnel-models (TS): analytical/empirical models (CSM, NTNU, face support,│
│   CCM/LDP, settlement, lining, Kuz-Ram, PPV...)  → always available      │
│ WebGPU compute (optional): local MLS-MPM/DEM patch for visual muck/face  │
│ HMI layer: operator console (thrust, RPM, screw speed, chamber pressure) │
└──────────────▲───────────────────────────────────────────▲───────────────┘
               │ WebSocket (binary, 20–60 Hz)              │ static assets
┌──────────────┴──────────── DGX Spark (GB10) ─────────────┴───────────────┐
│ Python sim server (uv), Newton 1.7 / Warp 1.19 / CUDA 13                  │
│  - SolverImplicitMPM: face soil, EPB chamber + screw, muck, cut&cover     │
│  - SolverMuJoCo/Kamino: cutterhead drive, thrust cylinders, erector,      │
│    articulation joint, gripper shoes (closed loops → Kamino)              │
│  - SolverCoupled: MPM ⇄ rigid machine coupling                            │
│  - Custom Warp kernels: bonded-particle DEM for cutter–rock, pore         │
│    pressure field, grout/slurry 1-D networks                              │
│  - Same tunnel-models (Python reference impl.) for cross-checks           │
│  - Surrogate/ROM models trained offline (Kratos/Chrono/YADE runs, TBM data)│
└──────────────────────────────────────────────────────────────────────────┘
        Offline (batch, not real time): Kratos GeoMechanics, Chrono CRM/DEM-Engine,
        YADE/MercuryDPM → parameter calibration and surrogate training data
```

**Why this split:**

1. **Tunnel scale versus face scale.**
   - At tunnel scale (km length, 10⁵–10⁶ m³ of ground), continuum ground response cannot run in real time. Analytical models (CCM, Peck) and pretrained surrogates are the right tool there. They are also the models industry practice relies on (DAUB, ITA).
   - At face scale (a few m³ around the cutterhead, chamber and screw), particle methods add real value: muck flow, face collapse, chamber pressure dynamics. Newton MPM sustains about 270k particles at 1× real time on GB10 [V], which is enough for one EPB chamber plus a face slice at about 3–5 cm resolution.
2. **The browser stays responsive.**
   - Operator input runs locally through Jolt and the TS models at 60 fps.
   - The server only streams the heavy-ground state: particle positions as quantized int16 relative to a local frame, or a surface heightfield/mesh, plus scalar fields such as face pressure, torque and thrust.
   - Latency tolerance is moderate, because TBM dynamics are slow (advance rates of mm/s).
3. **One model library, two languages.**
   - Write each analytical model once as a Python reference (NumPy) and once in TypeScript.
   - Keep shared JSON test vectors and run both in CI, so the browser and server always agree.
   - Alternative: a single Rust core compiled to WASM and to Python via PyO3. This is cleaner but adds toolchain weight. It is not recommended for v1 to stay aligned with the sister project.
4. **Rock cutting.**
   - Real-time fracture of rock under 19-inch disc cutters is not feasible at whole-cutterhead scale.
   - Use the CSM/NTNU models for forces and penetration, and Jolt or visual-grade particles for chips.
   - Optionally run a GPU bonded-DEM "single cutter" lab in Warp or Chrono DEM-Engine for education, and to calibrate CSM coefficients offline.
5. **Groundwater.**
   - Represent groundwater with an analytical or 1-D seepage model: Broere's infiltration, and a DIN 4126 slurry stagnation gradient.
   - Do not attempt two-phase MPM in v1.

**Fallback (no GPU server) mode:**

1. All analytical and empirical models run in the browser in TypeScript, and drive machine kinematics, gauges and alarms: face pressure versus DAUB limits, torque, thrust, settlement trough on the surface, and lining ring loads.
2. Jolt handles all machinery, segments, muck chunks and conveyors.
3. If WebGPU is available, a capped local MLS-MPM patch (50k–300k particles, Drucker–Prager sand) gives visual muck in the chamber or at the face. It is clearly labelled as visual-grade.
4. Otherwise, prerecorded server runs (recorded MPM sequences) play back, as the sister project's demo does.
5. The UI shows a "fidelity level" badge (Analytical / Local GPU / Server MPM), so users and trainers know which physics drove the results.

---

## B. Published models a simulator should implement

Each entry gives the reference and the core equation, and is cited [R] unless noted otherwise.

### B.1 Hard-rock TBM performance and cutters

- **CSM model.** Rostami & Ozdemir (1993), *RETC Proc.*; Rostami (1997), PhD thesis, Colorado School of Mines.
  - Total cutter force: F_t = C·φ·R·T/(1+ψ) · [σc²·σt·S / (φ·√(R·T))]^(1/3), with C ≈ 2.12.
  - Contact angle: φ = arccos((R−p)/R), where p is penetration per revolution.
  - Force components: normal F_n = F_t·cos(φ/2) and rolling F_r = F_t·sin(φ/2).
  - Penetration: solve F_n = installed thrust per cutter for p. Then ROP = p·RPM·60/1000 m/h.
  - Torque is approximately 0.3·D·N_c·F_r.
- **NTNU model.** Bruland (1998), *Hard Rock Tunnel Boring*, PhD thesis, NTNU, Project Report 1B-98; Macias (2016), PhD thesis, NTNU, updated model.
  - Basic penetration: i₀ = (M_ekv/M₁)^b mm/rev.
  - M_ekv is the gross thrust per cutter corrected for cutter diameter and spacing. M₁ and b are functions of the equivalent fracturing factor k_ekv = k_s-tot·k_DRI·k_por.
  - Cutter life comes from the Cutter Life Index CLI = 13.84·(SJ/AVS)^0.3847, together with quartz content, diameter and RPM.
  - Requires NTNU lab indices (DRI, SJ, AVS) and the joint fracturing class.
- **Gehring (1995).** *Felsbau* 13(6).
  - Basic penetration: p₀ ≈ 4·F_n/σc, in mm/rev with F_n in kN and σc in MPa.
  - p₀ is then multiplied by correction factors k_i for jointing, fracture toughness, cutter spacing and so on. Cutter ring wear comes from CAI.
- **Q_TBM.** Barton (2000), *TBM Tunnelling in Jointed and Faulted Rock*, Balkema.
  - Q_TBM = (RQD₀/Jn)(Jr/Ja)(Jw/SRF) · SIGMA/(F¹⁰/20⁹) · (20/CLI) · (q/20) · (σθ/5).
  - Penetration rate: PR ≈ 5·Q_TBM^(−0.2) m/h. Advance rate: AR = PR·T^m, with m < 0, a decline gradient that depends on Q.
  - Q_TBM has been criticised, notably by Blindheim (2005, TUST).
- **Yagiz (2008).** *TUST* 23(3).
  - ROP (m/h) = 1.093 + 0.029·PSI − 0.003·UCS + 0.437·log₁₀(α) − 0.219·DPW.
  - PSI is the punch-test peak slope index, α the angle between tunnel axis and planes of weakness, and DPW the distance between planes of weakness.
- **Hassanpour et al. (2011).** *TUST* 26(5).
  - Field Penetration Index FPI = F_n/p (kN per cutter per mm/rev), regressed against UCS, RQD and joint parameters as exp(a·UCS + b·RQD + c).
  - Coefficients differ between the papers' versions. Take them from the paper **[UNVERIFIED exact coefficients]**.
- **Abrasivity and wear.**
  - Cerchar Abrasivity Index: CAI = 10 × wear flat (mm) on a steel pin scratched 10 mm under 70 N. Standards: ASTM D7625 and NF P94-430-1; Alber et al. (2014), *RMRE* (ISRM Suggested Method).
  - Cutter life (m³/cutter or h/cutter) is a function of CAI, UCS and RPM: Rostami (2005) and the NTNU CLI approach.
  - Ring wear rate drives cutter changes. This is an important gameplay and cost mechanic.
- **Wear in soft ground.** Köppl, Thuro & Thewes (2015), *TUST*: soil abrasivity index SAI. Also LCPC breakability and abrasivity tests (NF P18-579).

### B.2 Soft-ground TBM: face support, EPB, slurry, torque and thrust

- **Horn (1961)** wedge-prism mechanism. Combine it with the **Janssen/Terzaghi silo**: σ_v(z) = (r·γ − c)/(K·tanφ) · (1 − e^(−K·tanφ·z/r)) + q·e^(−K·tanφ·z/r), with r = area/perimeter of the prism.
- **Anagnostou & Kovári.**
  - Slurry shields: (1994), *TUST* 9(2), "The face stability of slurry-shield-driven tunnels".
  - EPB shields: (1996), *TUST* 11(2), "Face stability conditions with earth-pressure-balanced shields".
  - Required support: s = F₀·γ′·D − F₁·c + F₂·γ′·Δh/D − F₃·c·Δh/D, with nomograms for F₀–F₃. The method includes seepage forces, the key EPB effect.
- **Leca & Dormieux (1990).** *Géotechnique* 40(4). Limit-analysis upper and lower bounds using conical blocks: σ_T = N_γ·γ·D + N_s·σ_s (for c = 0).
- **Jancsecz & Steiner (1994).** *Tunnelling '94*. 3-D earth pressure coefficient K_A3D, widely used in German practice.
- **Broere (2001).** PhD thesis, TU Delft, *Tunnel Face Stability & New CPT Applications*. Multilayer wedge with groundwater flow and slurry or foam infiltration, giving excess pore pressure ahead of the face.
- **DAUB / ITA-AITES (2016).** *Recommendations for Face Support Pressure Calculations for Shield Tunnelling in Soft Ground* [V] (https://tunnelsandtunnelling.com/?p=8156).
  - Minimum support pressure: E_re (earth, from an active failure mechanism, partial factor about 1.5) plus W_re (water, factor about 1.05). Factor values are [R]; check them in the document.
  - Maximum support pressure: at most 0.9 × total vertical stress at the crown, against blow-out and break-up [V].
  - The simulator should show the operating window between p_min and p_max and the control tolerance (e.g. ±0.2–0.3 bar) **[UNVERIFIED typical tolerance]**.
- **EPB chamber and screw conveyor.**
  - Chamber pressure dynamics follow from mass balance: dp/dt ≈ (K_c/V_ch)·(Q_excavated·(1+FIR/100·φ_gas) − Q_screw), where K_c is the bulk compressibility of the conditioned soil. Practical control models of this form appear in Yeh (1996) and in many 2010s control papers. The form is generic **[R, generic form]**.
  - Screw conveyor: Merritt & Mair (2006), *Géotechnique* 56(9), model tests; and Merritt & Mair (2008), *Géotechnique* 58(2), theoretical model. They give the pressure drop along the screw from soil–casing and soil–flight friction (roughly exponential decay with length) and screw discharge Q = η·A_eff·pitch·N.
  - Also see Talebi et al. (2015), *TUST*, a DEM screw conveyor study **[UNVERIFIED details]**.
- **Soil conditioning.**
  - Foam Injection Ratio: FIR = Q_foam/Q_soil × 100%.
  - Foam Expansion Ratio: FER = V_foam/V_liquid, typically 5–20.
  - Surfactant concentration c_f is 0.5–5%. There is also a polymer injection ratio.
  - References: EFNARC (2005), *Specification and Guidelines for the Use of Specialist Products for Mechanised Tunnelling (TBM) in Soft Ground and Hard Rock*; Peila et al. (2009), *TUST*; Thewes & Budach (2010), *Geomechanics & Tunnelling*.
  - The target is a slump of about 10–20 cm and low permeability (< 10⁻⁵ m/s) in the chamber.
- **Slurry / filter cake.**
  - Penetration of slurry into soil: e_max = Δp·d₁₀/(α·τ_F), with α = 2 (Müller-Kirchenbauer, 1972) or 3.5 (DIN 4126).
  - Stagnation gradient: f_s0 = Δp/e_max.
  - Membrane versus penetration: Anagnostou & Kovári (1994). Excess pore pressure: Bezuijen (2002).
  - Slurry circuit: pump curves, Durand settling velocity, separation plant.
- **Cutterhead torque.**
  - Krause (1987) empirical sizing: installed torque T = α·D³, with α ≈ 9–23 kN·m/m³ (higher for EPB). Thrust is about β·D², with β around 500–1200 kN/m² **[R, ranges vary by source]**.
  - Analytical sum of components: T = T_cut (tools) + T_face friction (μ·σ'·A_face·(1−opening ratio)·2R/3) + T_periphery (shell friction) + T_back face (chamber soil friction) + T_mixing arms + T_seals/bearing.
  - Reference: Shi, Yang, Gong et al. (2011), "Determination of the cutterhead torque for EPB shield tunneling machine", *Automation in Construction* 20(8) **[R; verify authors]**.
- **Thrust.**
  - F = p_face·A_face + ΣF_tools + μ_shield·∫σ_n dA_shield + F_tail seal + F_backup drag + F_steering.
  - Shield skin friction is μ ≈ 0.2–0.4 times the average radial earth pressure, usually the dominant term.
  - Jacks react off the last ring, which is the link to the lining model.

### B.3 Ground response and rock mass classification

- **Hoek–Brown (2002 edition).** Hoek, Carranza-Torres & Corkum (2002), *NARMS-TAC*.
  - Failure criterion: σ₁ = σ₃ + σci·(m_b·σ₃/σci + s)^a.
  - m_b = m_i·exp((GSI−100)/(28−14D)).
  - s = exp((GSI−100)/(9−3D)).
  - a = ½ + ⅙·(e^(−GSI/15) − e^(−20/3)).
  - Rock mass modulus: E_rm = E_i·(0.02 + (1−D/2)/(1+e^((60+15D−GSI)/11))), from Hoek & Diederichs (2006), *IJRMMS* 43.
  - GSI chart: Marinos & Hoek (2000).
- **RMR.** Bieniawski (1989), *Engineering Rock Mass Classifications*. Sum of ratings for UCS, RQD, joint spacing, joint condition and groundwater, adjusted for orientation.
- **Q system.** Barton, Lien & Lunde (1974), *Rock Mechanics* 6. Q = (RQD/Jn)(Jr/Ja)(Jw/SRF). Support chart from Grimstad & Barton (1993). Approximate conversion: RMR ≈ 9·ln Q + 44.
- **Convergence–confinement method.**
  - Panet (1995), *Le calcul des tunnels par la méthode convergence-confinement*, Presses ENPC (AFTES method).
  - Carranza-Torres & Fairhurst (2000), *TUST* 15(2), Hoek–Brown ground reaction curve.
  - Mohr–Coulomb elastic-plastic closed form, with k = (1+sinφ)/(1−sinφ):
    - Critical support pressure: p_cr = (2p₀ − σ_cm)/(1+k).
    - Elastic wall displacement: u = r₀·(1+ν)·(p₀−p_i)/E.
    - Plastic radius: R_p = r₀·[2(p₀(k−1)+σ_cm)/((1+k)((k−1)p_i+σ_cm))]^(1/(k−1)).
  - Support characteristic curves for shotcrete, steel sets and bolts follow Hoek & Brown (1980) and Carranza-Torres & Fairhurst (2000).
- **Longitudinal displacement profile.** Vlachopoulos & Diederichs (2009), *RMRE* 42.
  - u₀* = ⅓·e^(−0.15·R*), with R* = R_p/r₀.
  - Ahead of the face (X* = x/r₀ ≤ 0): u* = u₀*·e^(X*).
  - Behind the face (X* ≥ 0): u* = 1 − (1−u₀*)·e^(−3X*/(2R*)).
  - Panet (1995) alternative: u/u_max = 0.25 + 0.75·[1 − (0.75/(0.75 + x/r₀))²].
- **Squeezing.** Hoek & Marinos (2000), *Tunnels & Tunnelling International*.
  - Strain without support: ε (%) = 0.2·(σ_cm/p₀)^(−2).
  - With support pressure p_i: ε = 0.15·(1 − p_i/p₀)·(σ_cm/p₀)^(−(3p_i/p₀+1)/(3.8p_i/p₀+0.54)).
  - Classes: < 1% few problems; 1–2.5% minor; 2.5–5% severe; 5–10% very severe; > 10% extreme.
  - Rock mass strength: σ_cm = 0.0034·σci^0.8·[1.029 + 0.025·e^(−0.1·m_i)]^GSI (Hoek & Marinos 2000).
- **Shield jamming.**
  - Ramoni & Anagnostou (2010), *RMRE* 43, "Thrust force requirements for TBMs in squeezing ground"; Ramoni & Anagnostou (2010), *TUST* 25, "Tunnel boring machines under squeezing conditions".
  - The shield jams when μ·∫σ_n dA (with ground closing on the shield after the overcut gap is consumed) exceeds the available thrust.
  - The model needs overcut, shield taper, advance rate and standstill duration, because creep and consolidation over time matter.
- **Time-dependent behaviour.** Sulem et al. (1987), *IJRMMS*, convergence law C(x,t) = C_x∞·[1−(X/(X+x))²]·[1 + m·(1−(T/(T+t))^n)]. Captures standstill effects.

### B.4 Settlement and building damage

- **Peck (1969).** *Proc. 7th ICSMFE, Mexico City*, State-of-the-Art volume.
  - Transverse trough: S(y) = S_max·exp(−y²/(2i²)).
  - Settlement volume: V_s = √(2π)·i·S_max.
  - Volume loss: V_L = V_s/(πD²/4).
- **O'Reilly & New (1982).** *Tunnelling '82*, IMM.
  - Trough width i = K·z₀, with K ≈ 0.5 for clay and 0.25–0.35 for sand and gravel.
  - Regressions: i = 0.43·z₀ + 1.1 (cohesive) and i = 0.28·z₀ − 0.12 (granular), in m.
- **Mair, Taylor & Bracegirdle (1993).** *Géotechnique* 43(2). Subsurface trough: K(z) = [0.175 + 0.325·(1 − z/z₀)]/(1 − z/z₀).
- **Horizontal and longitudinal movements.**
  - Horizontal displacement: S_h(y) = (y/z₀)·S(y), following O'Reilly & New.
  - Longitudinal profile: cumulative Gaussian, Attewell & Woodman (1982), *Ground Engineering*.
- **Volume loss typical values.** Modern EPB and slurry machines in clays achieve about 0.5–1.5%, and good practice is below 1%. Use Mair & Taylor (1997), *14th ICSMFE* state-of-the-art, for ranges.
- **Building damage.**
  - Burland & Wroth (1974): deep-beam limiting tensile strain.
  - Boscardin & Cording (1989), *JGE ASCE*: angular distortion plus horizontal strain.
  - Burland (1995), *1st Int. Conf. Earthquake Geotech. Eng.*, damage categories 0–5 by ε_lim:
    - 0–0.05%: negligible to very slight
    - 0.05–0.075%: slight
    - 0.075–0.15%: moderate
    - > 0.15%: severe to very severe
  - Mair, Taylor & Burland (1996), *Geotechnical Aspects of Underground Construction in Soft Ground*, London: three-stage assessment.
  - Potts & Addenbrooke (1997), *Proc. ICE Geotech. Eng.*: relative stiffness modification factors.

### B.5 Segmental lining, ring build and grouting

- **Muir Wood (1975).** *Géotechnique* 25(1), "The circular tunnel in elastic ground"; corrected by Curtis (1976).
  - Lining forces from the ovalisation term.
  - Joint-reduced effective stiffness: I_e = I_j + (4/n)²·I, for n > 4 segments.
- **Duddeck & Erdmann (1985).** *Underground Space* 9, "On structural design models for tunnels in soft soil". Covers continuum and bedded-beam (spring) models for thrust, moment and deformation.
- **ITA WG2 lining guidance.** ITA WG2 (2000), "Guidelines for the design of shield tunnel lining", *TUST* 15(3). ITA WG2 (2019), *Guidelines for the Design of Segmental Tunnel Linings*, ITA Report No. 22 **[R; verify report number]**. Also fib Bulletin 83 (2017), *Precast Tunnel Segments in Fibre-Reinforced Concrete*.
- **Construction load cases** (from the ITA 2019 guidelines):
  - **Thrust jacks:** bursting and spalling under the jack shoes, from Leonhardt / Iyengar splitting-force formulas and Groeneweg (2007), MSc thesis, TU Delft.
  - **Erector handling:** demoulding, stacking and handling.
  - **Gasket:** EPDM, design water head × safety factor, with the gasket load–compression curve (STUVA tests).
  - **Bolts/dowels:** connections between segments.
  - **Ring build:** sequence and keystone, taper ring selection for curve following, and ring build tolerance (lipping, stepping).
- **Annular grouting.**
  - Grout volume per ring: π/4·(D_cut² − D_ext²)·L_ring, multiplied by a fill factor of about 1.1–1.3 **[R, typical]**.
  - Two-component grout (bentonite-cement + silicate accelerator) has a gel time of a few seconds to about 20 s **[R, typical]**.
  - Grout pressure distribution: Talmon & Bezuijen (2005, *Proc. 5th IS-GACSS*; 2009, *TUST*). A vertical gradient below the hydrostatic gradient of grout weight, dissipating with consolidation.
  - Also check ring buoyancy (floating) in liquid grout.

### B.6 NATM/SEM, shotcrete and rock bolts

- **NATM/SEM sequencing.** Top heading, bench and invert, or side drifts; ring closure distance; observational method with convergence monitoring.
  - ÖGG Guideline for the Geotechnical Design of Underground Structures with Conventional Excavation (2010) [R].
  - ÖNORM B 2203-1 (rock mass behaviour types and excavation classes).
  - Couple sequencing to CCM and LDP: install support at distance d → u_install from the LDP.
- **Shotcrete hardening.**
  - Time-dependent stiffness: E(t) = E₂₈·[exp(s·(1−√(28/t)))]^0.5, the CEB-FIP / fib Model Code ageing form, where s depends on cement type.
  - Early-age strength classes J1/J2/J3 (EN 14487, ÖBV guideline).
  - Constitutive models: Meschke (1996), *Int. J. Numer. Anal. Methods Geomech.*, viscoplastic shotcrete; Schädlich & Schweiger (2014), PLAXIS shotcrete model (*Numerical Methods in Geotechnical Engineering*).
  - The common simple engineering approach is a "hypothetical modulus" (e.g. 5 GPa soft, 15 GPa hard).
- **Shotcrete ring support stiffness.** Thin-ring formula: k = E_c·[r₀² − (r₀−t)²]/[(1+ν)·((1−2ν)·r₀² + (r₀−t)²)·r₀]. Maximum pressure: p_max = σ_c/2·[1 − (r₀−t)²/r₀²] (Hoek & Brown 1980 / Hoek 2008).
- **Rock bolts.** Point-anchored and fully grouted. References:
  - Stillborg (1994), *Professional Users Handbook for Rock Bolting*.
  - Li & Stillborg (1999), *IJRMMS* 36, analytical model of fully grouted bolts.
  - Bobet & Einstein (2011), *TUST* 26.
  - Carranza-Torres (2009), *Rock Mech. Rock Eng.* — bolt reaction curves **[R; verify]**.
  - Systematic bolting adds equivalent support pressure p_b = T_bf/(s_c·s_l).

### B.7 Drill and blast

- **Langefors & Kihlström (1963).** *The Modern Technique of Rock Blasting*, Wiley/Almqvist & Wiksell.
  - Maximum burden: B_max = (d/33)·√(ρ·s/(c̄·f·(E/B))), with d the hole diameter in mm, ρ the charge density, s the weight strength, c̄ the rock constant, f the fixation factor and E/B the spacing-to-burden ratio.
- **Holmberg (1982).** "Charge calculations for tunnelling", *Underground Mining Methods Handbook* / SveDeFo **[R]**.
  - Four-section parallel cut: first burden B₁ ≈ 1.5·Φ (large empty hole diameter).
  - Stoping, contour and lifter hole patterns.
  - Pull ≈ 0.95 × hole depth (Persson, Holmberg & Lee 1994, *Rock Blasting and Explosives Engineering*, CRC).
- **Kuz-Ram fragmentation.** Kuznetsov (1973), *Soviet Mining Science*; Cunningham (1983, 1987), *1st/2nd Int. Symp. Rock Fragmentation by Blasting*.
  - Median fragment size: x₅₀ = A·K^(−0.8)·Q^(1/6)·(115/RWS)^(19/20), with A the rock factor, K the powder factor (kg/m³) and Q the charge per hole (kg).
  - Size distribution (Rosin–Rammler): R(x) = exp(−0.693·(x/x₅₀)ⁿ).
  - Improved distribution: Swebrec (Ouchterlony 2005, *Mining Technology*).
- **Ground vibration.** Scaled-distance law PPV = K·(R/√W)^(−β), from Duvall & Petkof (1959), USBM RI 5483, and Siskind et al. (1980), USBM RI 8507.
  - Limits: DIN 4150-3, BS 7385-2, USBM RI 8507.
  - Near-field and contour damage: Holmberg & Persson (1979).
- **Gameplay hooks.** Drill pattern design, charging, delay timing (Nonel), overbreak/underbreak from contour quality, ventilation and re-entry time (fume dilution), scaling, mucking cycle time.

### B.8 Roadheaders and point-attack picks

- **Evans (1962, 1984).** *IJRMMS*, point-attack pick force: F_c = 16π·σt²·d²/(σc·cos²(φ/2)), with d the cut depth and φ the tip angle. Improved by Goktan (1997), *IJRMMS*.
- **Bilgin et al. (2004/2006).** *IJRMMS*, instantaneous cutting rate.
  - ICR = 0.28·P·(0.974)^RMCI m³/h, where P is cutterhead power in kW.
  - Rock mass cuttability index: RMCI = UCS·(RQD/100)^(2/3).
- **Rostami, Ozdemir & Neil (1994).** *SME Annual Meeting*. ICR = k·P/SE_opt, with SE_opt from linear cutting tests.
- **Pick consumption.** A function of CAI and UCS (Thuro & Plinninger 2003, *ISRM Congress*).

### B.9 Pipe jacking, microtunnelling, shafts, cut-and-cover

- **Pipe jacking.**
  - Jacking force: F = F_face (face or slurry pressure × A) + π·D·L·τ_skin.
  - Skin friction τ is about 1–5 kPa with bentonite lubrication and 5–20+ kPa without **[R, typical ranges]**.
  - References: Pellet-Beaucour & Kastner (2002), *TUST* 17; Staheli (2006), PhD thesis, Georgia Tech **[R]**; Pipe Jacking Association (UK) guide; ASCE/CI 36-15 *Standard Design and Construction Guidelines for Microtunneling*; DWA-A 125 (Germany).
  - Also model intermediate jacking stations, steering (laser/gyro), and the curve and joint pressure transfer (Zarges & Lacher? **[UNVERIFIED]**).
- **Shaft sinking.**
  - Axisymmetric active pressure: Prater (1977) and Berezantzev (1958); silo arching for shafts.
  - Base heave: Bjerrum & Eide (1956), *Géotechnique*.
  - Caisson sinking: skirt friction plus cutting-edge bearing.
  - Mechanised options: VSM (vertical shaft sinking machine, Herrenknecht) and shaft boring.
  - Ground freezing: Stefan problem, Sanger & Sayles (1979), *Cold Regions Sci. Tech.*
- **Cut-and-cover.**
  - Embedded walls: CIRIA C760 (2017); EAB *Recommendations on Excavations* (DGGT).
  - Peck (1969) apparent earth pressure diagrams for strutted walls.
  - Wall deflection versus system stiffness: Clough & O'Rourke (1990), *ASCE GSP 25*.
  - Basal heave: Terzaghi, and Bjerrum–Eide.
  - Dewatering drawdown: Dupuit–Thiem.
  - Top-down versus bottom-up construction sequencing.

### B.10 Numerical approaches in recent literature (2018–2026), digital twins, simulators

- **FEM process simulation of mechanised tunnelling.**
  - Kasper & Meschke (2004), *IJNAMG*, and (2006), *TUST*: 3-D FE shield model, the precursor of **"ekate"** (Ruhr-Universität Bochum).
  - Alsahly, Stascheit & Meschke (2016), *TUST* 51, "Advanced finite element modeling of excavation and advancement processes in mechanized tunneling".
  - **BIM-to-FEM and SATBIM.** Vonthron, Bui, Koch, König & Meschke (2021), *TUST*: TIM → ekate, and parametric multi-level BIM → FE/IGA [V] (via the RUB pages listed below). SATBIM was an MSCA project (Ninić, 2016–18) with code on GitHub [V].
  - Book: Meschke, Freitag, König, Thewes et al. (eds.), *Interaction Modeling in Mechanized Tunneling*, Springer 2023 [V] (https://link.springer.com/book/10.1007/978-3-031-24066-9). This is the SFB 837 synthesis.
  - **Note: "ekkehard" could not be found.** The Bochum code is **ekate** ("Enhanced Kernel for Analysis of Tunnelling Excavation" **[UNVERIFIED expansion]**). It is not open source as far as found **[UNVERIFIED]**.
  - **Surrogates for real-time use:** Ninić, Freitag & Meschke (2017), *Comput. Methods Appl. Mech. Eng.*; Cao, Freitag et al. (2020), *TUST* — recurrent NN surrogates for real-time settlement prediction **[R; verify details]**. These directly inspire the "surrogate in the loop" design used here.
- **Commercial FE.** PLAXIS 3D and Abaqus are standard for face pressure, settlement and segment studies. Use their published benchmark results for validation.
- **DEM cutter and cutterhead models.**
  - Gong, Zhao & Jiao (2005/2006), *TUST*: UDEC jointing effects.
  - Cho, Jeon, Yu & Chung (2010), *TUST* 25: optimum disc cutter spacing using 3-D dynamic fracturing (AUTODYN).
  - Moon & Oh (2012), *TUST*: PFC cutter spacing **[R; verify]**.
  - Many PFC2D/3D linear cutting machine replicas since 2018.
- **EPB DEM and CFD-DEM.**
  - Maynar & Rodríguez (2005), *J. Geotech. Geoenviron. Eng.* 131(10), "Discrete numerical model for analysis of earth pressure balance tunnel excavation".
  - Later coupled DEM-CFD chamber and screw studies used LIGGGHTS/CFDEM and PFC-FLAC. Specific 2018–2026 papers were not re-verified in this survey.
- **MPM and SPH.**
  - Geotechnical MPM for face collapse and large deformation (Anura3D community; Soga et al. 2016, *Géotechnique* 66(3), "Trends in large-deformation analysis of landslide mass movements" [R]).
  - Graphics-grade Drucker–Prager MPM sand: Klár, Gast, Pradhana, Fu, Schroeder, Jiang & Teran (2016), *ACM TOG (SIGGRAPH)*.
  - MLS-MPM: Hu et al. (2018), *ACM TOG*. These are the basis for Newton and WebGPU MPM.
- **Machine-learning models on TBM data.** A very large literature: ROP and penetration prediction, rock mass classification from machine data, attitude and steering prediction, cutter wear.
  - Review: Shahrour & Zhang (2021), *Underground Space*, "Use of soft computing techniques for tunneling optimization of tunnel boring machines" **[R; verify]**.
  - Erharter et al. (TU Graz) — data-driven hard-rock TBM advance classification [V].
- **Digital twins and industry tools.**
  - Herrenknecht machine data systems; **VMT** (Herrenknecht subsidiary) navigation and data management, e.g. TUnIS and IRIS.tunnel **[R; product names unverified]**.
  - Robbins data loggers. Babcock — **[UNVERIFIED: no TBM operator simulator product found]**.
- **Operator and VR training simulators.**
  - VR TBM operator simulator coupled to the PLC via OPC UA [V]: *Frontiers in Virtual Reality* (2022), https://www.frontiersin.org/articles/10.3389/frvir.2022.1034431
  - TELT CO67 (Lyon–Turin) immersive VR training [V]: three modules covering induction, an erector ring-building simulator with a real remote, and cutter change. https://www.taylorfrancis.com/chapters/oa-edit/10.1201/9781042001064-252/
  - Tideway (London) VR safety training [V].
  - Herrenknecht ICIDO VR shield walkthrough [V]: https://www.worldconstructionnetwork.com/analysis/virtually-reality/
  - Korean patent US 12106683, TBM operation simulator [V].
  - **No open-source, physics-based tunnelling simulator was found.** This project would appear to be the first [UNVERIFIED by exhaustive search].

### B.11 Open TBM datasets for calibration and validation

- **Yinsong water diversion project, Jilin, China (CSRME shared big dataset).**
  - About a 20 km hard-rock TBM section, with 199 parameters logged at 1 Hz. It was used for the 2019 CSRME TBM machine-learning competition **[competition year R]**.
  - Reviewed in two papers: "Feedback on a shared big dataset for intelligent TBM", Parts I and II, *Underground Space* (2023), DOI 10.1016/j.undsp.2023.01.002 (Part II) [V]. 45 journal papers have used the dataset [V].
  - The access route is in the data availability statement **[UNVERIFIED direct download]**.
- **Three open synthetic TBM operational datasets (TU Graz group).** *Rock Mechanics and Rock Engineering* (2025), DOI 10.1007/s00603-025-04542-4 [V]. They were generated by neural networks trained on real records to avoid confidentiality issues, with code on GitHub [V]. Authorship is probably Erharter, Unterlass et al. **[UNVERIFIED]**.
- **TU Graz BBT (Brenner Base Tunnel) data theses** [V, as thesis topics; data is not necessarily public].
- **Norwegian (NTNU) datasets.** The NTNU model database is the basis of Bruland and Macias, but it is **not openly published [UNVERIFIED]**.
- **Other.** Several Chinese papers publish supplementary data (e.g. the Jilin Fengman water diversion project, *Scientific Reports* 2023, DOI 10.1038/s41598-023-37306-7 [V]). Licenses vary.
- **Recommendation:**
  - Use the Yinsong data to calibrate the CSM/NTNU/FPI models for hard rock.
  - Use the TU Graz synthetic sets for CI benchmarks, since they are redistributable.
  - Ask industry partners for EPB data, as the sister project asks for field data.

---

## C. Standards and guidelines to respect

| Body | Document | Use in simulator |
|---|---|---|
| CEN | **EN 16191:2014** *Tunnelling machinery — Safety requirements* (replaced EN 815 and EN 12336). Revision **FprEN 16191** is at stage 50.20, with publication targeted for **24 Sep 2026** — **[UNVERIFIED whether published]** [V for status] | Interlocks, emergency stops, gas monitoring, man-lock references, operator cabin rules |
| CEN | EN 12110-1/-2 (air locks; 2023 revision drafts) [V via 16191 scope]. EN 12111 (roadheaders, continuous miners, impact rippers) [R] | Hyperbaric interventions (cutter change under pressure), roadheader safety |
| DAUB / ITA-AITES | *Recommendations for Face Support Pressure Calculations for Shield Tunnelling in Soft Ground* (10/2016) [V] | p_min and p_max window |
| DAUB | *Recommendations for the Selection of Tunnelling Machines* (10/2010 [V]; a newer edition is **[UNVERIFIED]**) | Machine type selection screen: grain size distribution ranges for EPB versus slurry |
| DAUB | Recommendations on segment design and production; *BIM in Tunnelling* (2019) [R] | Lining, data model |
| ITA-AITES | WG2 (Research): lining design guidelines (2000; 2019 Report 22 [R]), settlement reports. WG14 (Mechanized Tunnelling); WG19 (Conventional Tunnelling); WG5 (Health & Safety); ITA-COSUF (fire and safety) [R] | Methods taxonomy, safety, lining checks |
| BTS | *Specification for Tunnelling*, 3rd ed. (2010); BTS/ICE *Closed-Face Tunnelling Machines and Ground Stability* (2005); *Guide to the Work in Compressed Air* [R] | UK practice, face stability, interventions |
| ÖGG | Guideline for Geotechnical Design of Underground Structures with Conventional Excavation (2010) and with Continuous Excavation (2013) [R]; ÖNORM B 2203-1/-2 [R] | NATM behaviour types and excavation classes; TBM classes |
| Others | Eurocode 7 (EN 1997, 2nd generation), EN 1992 (segments), DIN 4126 (slurry stability), DIN 4150-3 / BS 7385-2 (vibration), EFNARC 2005 (conditioning), ASTM D7625 (CAI), ISRM Suggested Methods, ASCE/CI 36-15 (microtunnelling), CIRIA C760 and EAB (excavations), SIA 197/198 (Switzerland) [R] | Parameter defaults, limits, test definitions |

Treat these documents as **sources of default parameters, limits and alarm thresholds**. Implement them as data, in versioned JSON with citations. Most are copyrighted, so the repository should cite them and store only the derived numbers, not reproduce text.

---

## Recommended stack and phased roadmap

### Stack

- **Repository and license.** Apache-2.0 code and per-asset licenses, mirroring the sister project. Use monorepo folders by phase.
- **Browser.**
  - TypeScript, Vite, three.js (WebGPURenderer with WebGL2 fallback), Jolt (`jolt-physics` 1.1.x).
  - A `@tunnelsim/models` package holding all analytical models.
  - Optional WebGPU WGSL MLS-MPM patch for visuals.
- **Server.**
  - Python 3.12 via `uv`, Newton 1.7.x (pin it; note the MPM scaling change in 1.7), Warp 1.19.x, CUDA 13, running on the DGX Spark.
  - `websockets` (later WebTransport) with a binary schema (FlatBuffers or a custom quantized layout).
  - `numpy` and `scipy` for the reference models.
- **Offline.** Kratos GeoMechanicsApplication for staged ground response, Chrono 10 (CRM/DEM-Engine, built from source on ARM) and YADE/MercuryDPM for calibration, and PyTorch for surrogates.
- **Data.** Geology as a voxel/block model (borehole → 3-D model) with Hoek–Brown, Mohr–Coulomb and HS parameters. Use OpenUSD and glTF for machines, and IFC-Tunnel (IFC 4.3+ / buildingSMART) for the alignment and lining **[R]**.
- **Validation.** Each model gets textbook worked examples as unit tests, and published case histories as regression tests: for example London Crossrail or the JLE settlement data in the literature, and the Yinsong dataset.

### Top 10 models to implement first (Phase 1, browser TS plus Python reference)

1. CSM disc cutter forces and penetration/ROP (Rostami & Ozdemir), plus cutterhead torque and power.
2. Cutter wear from CAI or NTNU CLI, turned into cutter change events (Gehring / Bruland).
3. Face support window: Anagnostou–Kovári wedge-silo with seepage, plus DAUB 2016 p_min/p_max.
4. EPB chamber pressure mass balance and screw conveyor (Merritt & Mair), with FIR/FER conditioning. Add the slurry pressure and filter cake (DIN 4126) branch.
5. Thrust and torque component decomposition (shield friction, face, tools, tail seal, backup), and Krause sanity bounds.
6. Hoek–Brown/GSI parameters, then the convergence–confinement method (Carranza-Torres & Fairhurst GRC, support curves, Vlachopoulos–Diederichs LDP).
7. Squeezing classification (Hoek & Marinos) and shield jamming check (Ramoni & Anagnostou).
8. Peck/O'Reilly–New settlement trough with volume loss, plus Burland damage categories for surface buildings.
9. Segment lining (Muir Wood / Duddeck–Erdmann bedded ring), thrust-jack load checks, ring build and taper selection, and annular grout volume and pressure.
10. Drill and blast: Holmberg cut and pattern design, Langefors burden, Kuz-Ram fragmentation, and PPV scaled-distance compliance.

These come next: shotcrete ageing E(t) with NATM sequencing; roadheader ICR (Bilgin) with Evans pick forces; pipe-jacking force; shaft and cut-and-cover earth pressure and basal heave.

### Phased roadmap

- **Phase 0: platform (2–4 weeks).**
  - Reuse the sister project's DGX Spark setup.
  - Benchmark Newton MPM for (a) an EPB chamber with a rotating cutterhead and screw conveyor, and (b) a face slice with support pressure. Measure particles, real-time factor and stability.
  - Prototype WebSocket streaming of 100k–300k quantized particles at 20–30 Hz.
  - Test a WebGPU Drucker–Prager MLS-MPM patch on the Mac (Apple GPU) and on Chrome/Linux.
  - Decide on the binary protocol.
- **Phase 1: analytical simulator, browser-only (2–3 months).**
  - TS models #1–#10 with Python twins and shared test vectors.
  - A single-shield / EPB TBM as the first machine (three.js + Jolt): cutterhead, thrust jacks, erector, screw, conveyor, backup.
  - Operator console UI, geology along the alignment, a settlement heatmap on the surface, and alarms tied to DAUB/EN 16191 thresholds.
  - Fallback mode fully functional.
- **Phase 2: server ground physics (3–4 months).**
  - Newton MPM for the EPB chamber and face, two-way coupled with cutterhead, screw and shield through SolverCoupled/MuJoCo.
  - Calibrate against analytical face pressure and screw discharge; muck flow to the conveyor.
  - Slurry machine variant with a pump circuit model.
  - Record and replay so web demos work without a GPU.
- **Phase 3: method breadth (4–6 months).**
  - Hard-rock open gripper and double shield, with gripper and shoe kinematics (Kamino closed loops) and CSM/NTNU.
  - NATM/SEM sequencing with CCM/LDP and shotcrete ageing.
  - Drill & blast cycle: jumbo, charging, blast, ventilation, mucking.
  - Roadheader. Pipe jacking and microtunnelling. Shaft sinking (VSM, caisson). Cut-and-cover with props and dewatering.
- **Phase 4: fidelity and validation (ongoing).**
  - Surrogates trained on Kratos staged-excavation runs (settlement, lining forces) and Chrono/YADE cutter–rock DEM.
  - Calibration on the Yinsong and TU Graz datasets, plus partner EPB data.
  - Uncertainty (random fields of GSI and UCS).
  - Validation reports per model.
- **Phase 5: training and research features.**
  - Scenario editor and trainee scoring.
  - Multi-user sessions, and an OPC UA / PLC-style tag interface (as in the Frontiers VR simulator).
  - Gymnasium RL environment for TBM control (face pressure, steering), and a ROS 2 bridge shared with the sister project.

### Key risks

- **Newton is changing fast.** v1.7 changed MPM stress scaling, so pin versions and keep golden tests.
- **MPM soil is not yet validated** against measured cutting forces, as the sister project also notes.
- **No native pore-pressure coupling** in Newton.
- **WebGPU on Linux needs flags.**
- **Copyrighted standards:** cite them and store only parameters.
- **Rock fracture at cutterhead scale stays empirical** in real time.

---

## Source URLs (checked during this survey)

- Sister repo: https://github.com/dtt-github/construction-site-simulation ; https://raw.githubusercontent.com/dtt-github/construction-site-simulation/main/phase0/RESULTS.md
- Newton: https://github.com/newton-physics/newton ; https://github.com/newton-physics/newton/releases ; https://newton-physics.github.io/newton/latest/api/newton_solvers.html ; https://developer.nvidia.com/blog/newton-adds-contact-rich-manipulation-and-locomotion-capabilities-for-industrial-robotics ; https://dataconomy.com/2026/03/17/nvidia-launches-newton-1-0-physics-engine-for-industrial-robot-training/
- DGX Spark toolchain notes: https://github.com/natolambert/dgx-spark-setup ; https://forums.developer.nvidia.com/t/physx-gpu-not-working-on-dgx-spark-gb10-blackwell-arm64-isaac-sim-5-1-0/361709
- Newton Dynamics: https://github.com/MADEAPPS/newton-dynamics
- Jolt: https://registry.npmjs.org/jolt-physics/latest ; https://pmndrs.github.io/react-three-jolt/advanced/migration
- Rapier: https://registry.npmjs.org/@dimforge/rapier3d/latest ; https://awesome.ecosyste.ms/projects/github.com%2Fdimforge%2Fnexus
- PhysX WASM: https://github.com/fabmax/physx-js-webidl
- MuJoCo WASM: https://cdn.jsdelivr.net/npm/@mujoco/mujoco@3.9.0/README.md ; https://raw.githubusercontent.com/google-deepmind/mujoco/main/wasm/README.md
- WebGPU MPM: https://tympanus.net/codrops/2025/02/26/webgpu-fluid-simulations-high-performance-real-time-rendering/ ; https://luma.gl/docs/api-reference/experimental/mls-mpm-fluid-simulation
- Kratos GeoMechanics: https://deltares.github.io/Kratos-GeoMechanicsApplication-Documentation/about/ ; https://pypi.org/project/KratosGeoMechanicsApplication/9.5
- Chrono: https://api.projectchrono.org/vehicle_terrain_crm_api_.html ; https://arxiv.org/html/2507.05643v2
- Genesis: https://pypi.org/project/genesis-world/1.1.2/
- Bochum / SATBIM: https://www.sd.ruhr-uni-bochum.de/downloads/SFB_837_Gastvortrag_Ninic.pdf ; https://cordis.europa.eu/project/id/702874/reporting ; https://link.springer.com/book/10.1007/978-3-031-24066-9
- Simulators: https://www.frontiersin.org/articles/10.3389/frvir.2022.1034431 ; https://www.taylorfrancis.com/chapters/oa-edit/10.1201/9781042001064-252/ ; https://www.worldconstructionnetwork.com/analysis/virtually-reality/ ; https://patents.google.com/patent/US12106683
- Datasets: https://doaj.org/article/6ee45313cc174ddcb3143c04e25d6357 ; https://link.springer.com/article/10.1007/s00603-025-04542-4 ; https://doi.org/10.1038/s41598-023-37306-7 ; https://www.tugraz.at/institute/fmt/research/publications-2/
- Standards: https://genorma.com/en/standards/fpren-16191 ; https://iteh.es/catalog/standards/sist/6c1e4325-75e7-48a2-94a2-b37ceda2746d/osist-pren-16191-2023 ; https://tunnelsandtunnelling.com/?p=8156 ; https://www.worldconstructionnetwork.com/?p=122065
