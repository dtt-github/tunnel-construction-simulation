# Phase 0 results: tunnel MPM and streaming on the DGX Spark

Date: 4 Nov 2026. Machine: DGX Spark (GB10, sm_121, 128 GB unified memory), Ubuntu 24.04.5, kernel 7.0.0-1019-nvidia, driver 580.178.04, CUDA 13.0.
Software: Newton 1.7.0, Warp 1.19.0, websockets 17.4, Python 3.12 (uv venv `.venv-newton`), Node 22.22, Chrome 156 (Linux ARM64, from the sister project's `tools/`).

Engine choice and the general Newton/Chrono/Isaac comparison are in the sister project ([construction-site-simulation](https://github.com/dtt-github/construction-site-simulation), `phase0/RESULTS.md`). This page covers the tunnel-specific checks from [ROADMAP Phase 0](../docs/ROADMAP.md#phase-0-platform-dgx-spark).

**Timing caveat.** Another project's GPU benchmark was running on the same GB10 throughout these runs (40–85 % GPU utilisation before ours started). Real-time factors here are therefore **lower bounds**; they have not yet been repeated on an idle GPU.

## Setup

```bash
cd phase0
uv venv -p 3.12 .venv-newton
uv pip install -p .venv-newton "newton[examples]==1.7.0" "warp-lang==1.19.0" "websockets==17.4"
```

## (b) Tunnel face under a retracting support plate (`face_bench.py`)

Dry sand block with a 2 m shield (polygonal tube) and a kinematic face plate. After 1 s of settling the plate retracts 0.2 m (10 % of D) at 0.05 m/s. The normal force on the plate drops from the settled value to a limit value once a failure mechanism forms ahead of the face. Side walls are frictionless; soil–steel friction is 0.3; density 1600 kg/m³; one implicit step per 1/60 s frame with 50 solver iterations; 2 particles per voxel per axis.

Reference: Vermeer, Ruse & Marcher (2002), *Tunnel heading stability in drained ground*, Felsbau 20(6): for c′ = 0, p_f = γ D N_γ with N_γ = 1/(9 tan φ) − 0.05, independent of cover. Centrifuge tests in dry sand (Chambon & Corté 1994, doi:10.1061/(ASCE)0733-9410(1994)120:7(1148)) give values of the same order.

| Voxel | Particles | μ = tan φ | C/D | ms/frame | Real-time factor | p settled (kPa) | p limit (kPa) | Vermeer (kPa) | Sim / Vermeer |
|---|---|---|---|---|---|---|---|---|---|
| 0.20 m | 208,068 | 0.75 | 1 | 27.7 | 0.60× | 8.2 | 1.63 | 3.08 | 0.53 |
| 0.15 m | 493,873 | 0.75 | 1 | 59 | 0.28× | 11.0 | 2.03 | 3.08 | 0.66 |
| 0.10 m | 1,671,766 | 0.75 | 1 | 218 | 0.08× | 12.9 | 2.42 | 3.08 | **0.79** |
| 0.15 m | 681,794 | 0.75 | **2** | 91 | 0.18× | 18.7 | 2.00 | 3.08 | 0.65 |
| 0.15 m | 493,873 | **0.58** | 1 | 61 | 0.27× | 19.6 | 3.18 | 4.44 | 0.72 |
| 0.15 m | 493,873 | **0.90** | 1 | 63 | 0.27× | 6.8 | 1.27 | 2.31 | 0.55 |

What this shows:
1. **The mechanism is right.** The limit pressure does not depend on cover (C/D = 1 and 2 give 2.03 and 2.00 kPa), as Vermeer et al. found for sand. It falls with friction angle in the right direction.
2. **It converges towards the reference from below:** 0.53 → 0.66 → 0.79 of Vermeer as the voxel shrinks from D/10 to D/20. Real-time resolution (D/10) underestimates the required support by about half. A production face zone needs either about D/20 locally or a calibration factor.
3. **The at-rest state is not reliable.** The settled pressure (7–20 kPa) is below K₀γz (18.8 kPa at the axis) and depends on resolution. Newton's default rigid-plastic material (E = 10¹⁵ Pa) has no unique elastic at-rest state. Earth pressure at rest should come from the analytical model, not from MPM.
4. Leakage through the thin shield walls is negligible (130–306 particles end up behind the plate).

## (a) EPB chamber, cutterhead and screw conveyor (`epb_bench.py`)

6 m chamber, 0.8 m long, plus a 0.3 m soil slab pushed in by a "ground" piston at 50 mm/min. Conditioned soil: μ = 0.35, yield stress 2 kPa, 1800 kg/m³, about 90 % full. Cutterhead: 6 spokes and 6 mixing arms at 2 rpm. Screw: 0.8 m diameter, 0.6 m pitch, 4 m long at 20°, in a square casing through the bulkhead. Each run is 10 s simulated (600 frames). Bulkhead pressure is measured in three bands (top, axis, bottom) on either side of the screw opening, like the chamber pressure sensors on a real EPB.

| Voxel | Particles | Screw rpm | ms/frame | Real-time factor | p top / axis / bottom (kPa) | Gradient (kPa/m) | Cutterhead torque (kNm) | Screw torque (kNm) | Discharge (m³/s) | Q_th (m³/s) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.2 m | 32,892 | 0 | 20.3 | 0.82× | 22.6 / 42.4 / 77.1 | 18.3 | 1,513 | 1.4 | 0 | 0 |
| 0.2 m | 32,892 | 10 | 21.9 | 0.76× | 22.5 / 42.2 / 75.6 | 17.8 | 1,461 | 44.0 | 0.012 | 0.047 |
| 0.1 m | 265,858 | 0 | 42.2 | 0.40× | 9.8 / 27.5 / 48.6 | 13.0 | 955 | 0.8 | 0 | 0 |
| 0.1 m | 265,858 | 5 | 43.3 | 0.39× | 9.8 / 27.6 / 48.8 | 13.1 | 952 | 27.4 | 0.011 | 0.024 |
| 0.1 m | 265,858 | 10 | 45.1 | 0.37× | 9.8 / 27.6 / 48.6 | 13.0 | 943 | 26.7 | 0.008 | 0.047 |
| 0.1 m | 265,858 | 20 | 44.6 | 0.37× | 9.8 / 27.5 / 48.9 | 13.1 | 946 | 27.9 | 0.006 | 0.094 |

Q_th = π(r² − r_shaft²) · pitch · n is the theoretical screw capacity (Merritt & Mair 2006, doi:10.1680/geot.2006.56.9.605). ρg = 17.7 kPa/m.

What this shows:
1. **Speed:** the chamber with cutterhead and screw runs at 0.8× real time at 33k particles and 0.4× at 266k, both with the GPU shared (see caveat). Real time at 0.1 m needs a smaller active domain or fewer solver iterations.
2. **Chamber pressure is plausible.** It rises linearly with depth, with a gradient of 0.74ρg (0.1 m) to 1.0ρg (0.2 m), i.e. a lateral pressure ratio below 1 for a frictional, cohesive paste. The absolute level is gravity-only (about 0.5 bar at the bottom), because the piston only moves at the real advance rate. A pressure-controlled piston (thrust-driven) is needed to reach realistic 1–3 bar support.
3. **Torque:** about 950 kNm on the cutterhead from chamber mixing alone, with no cutting at the face. That is the right order for a 6 m EPB (installed torque is typically several MNm). Screw torque is about 27 kNm and almost independent of rpm.
4. **The screw is not yet credible.** Discharge falls as rpm rises (0.011 → 0.006 m³/s from 5 to 20 rpm), so the screw is starved: the open inlet can't feed it at gravity-only chamber pressure, and the 0.1 m grid only just resolves a 0.8 m screw (4 voxels across). Volumetric efficiency is 47 % at 5 rpm and drops after that. Two earlier geometry faults were found and fixed along the way: soil leaked under the casing at the bulkhead, and soil tunnelled through walls thinner than one voxel. Walls must be **at least one voxel thick**.

## Particle streaming (`stream/`)

The server keeps positions on the GPU, moves them each frame with a Warp kernel (standing in for the MPM step), quantizes on the GPU, copies to the host and sends one binary WebSocket message per frame. Clients decode into a `Float32Array`, the format a three.js/WebGL buffer takes. 8 s per case, localhost.

### Wire format "TSP0" (chosen)

48-byte little-endian header: magic, frame index, send time (f64 ms), N, encoding, bbox min (3×f32), quantization step (3×f32). Then the payload:
- `0` f32 xyz (12 B/particle);
- `1` u16 xyz (6 B/particle);
- `2` u16 xyz plus a u8 attribute such as speed or material (7 B/particle).

With a fixed 10 m box, the u16 step is 0.15 mm, far below the voxel size. The decoder is `stream/tsp0.mjs`, shared by Node and the browser.

### Node client

| Particles | Hz | Encoding | MB/s | Received fps | Latency mean / p95 (ms) | Server encode (ms) | Client decode (ms) |
|---|---|---|---|---|---|---|---|
| 100k | 30 | u16 | 18.1 | 30.0 | 0.19 / 0.84 | 1.1 | 0.21 |
| 200k | 30 | u16 | 36.2 | 30.0 | 0.54 / 1.5 | 1.3 | 0.59 |
| 300k | 20 | u16 | 36.2 | 20.0 | 0.66 / 1.8 | 1.3 | 0.85 |
| 300k | 30 | f32 | 108.5 | 30.0 | 1.32 / 2.3 | 1.5 | 0.17 |
| 300k | 30 | u16 | 54.2 | 30.0 | 0.75 / 1.7 | 1.3 | 0.90 |
| 300k | 30 | u16 + u8 | 63.3 | 30.0 | 0.90 / 2.4 | 1.5 | 1.07 |
| 300k | 30 | u16 + permessage-deflate | 20.8 | **11.4** | 49 / 59 | 1.2 | 1.05 |
| 1M | 30 | u16 | 180.9 | 30.0 | 3.6 / 7.5 | 2.2 | 3.5 |

No frames were dropped in any case. Full table: `logs/stream.json`.

### Chrome 156 on the Spark (WebGL2 via ANGLE/Vulkan on the GB10, headed X11)

| Particles | Encoding | Received fps | Render fps | MB/s | Latency mean / p95 (ms) | Decode + upload (ms) |
|---|---|---|---|---|---|---|
| 100k | u16 | 30.0 | 58.8 | 18.1 | 3.0 / 4.1 | 0.45 |
| 300k | u16 | 30.1 | 58.4 | 54.3 | 7.4 / 9.4 | 1.25 |
| 300k | f32 | 30.0 | 58.6 | 108.6 | 11.8 / 15.0 | 0.43 |
| 1M | u16 | **24.7** | 53.7 | 148.8 | 130 / 179 | 2.7 |

Screenshot: `logs/stream_browser.png`. Results: `logs/stream_browser.json`.

### Decision

- **Use TSP0 u16 (encoding 1)** as the default and u16 + u8 (encoding 2) when the client colours by speed or material. 300k particles at 30 Hz costs about 1.5 ms on the server and 1 ms in the browser, which is negligible next to the MPM step.
- **Don't use permessage-deflate.** Quantized, unordered particle positions barely compress, and deflate drops the rate to 11 fps.
- **Bandwidth is the real limit, not CPU.** 300k × 30 Hz × 6 B = 54 MB/s (≈ 430 Mbit/s). That is fine on localhost or wired gigabit, but too much for Wi-Fi or the internet. For remote viewers, Phase 2 should add these options (not measured yet): stream only active, moving particles; lower the rate to 10–15 Hz; send u8 deltas against a keyframe.
- About 1M particles is the ceiling for one browser tab (backpressure builds and latency grows to more than 100 ms).

## Not done in Phase 0

- **WebGPU Drucker–Prager MLS-MPM patch** (Apple GPU and Chrome/Linux ARM). The sister project confirmed that Chrome WebGPU works on the GB10 with flags (2.4 billion particle updates/s). The sand patch itself and the Apple test remain open.
- Pressure-controlled (thrust-driven) chamber support, and a calibrated screw inlet. Both are needed before the EPB chamber numbers mean anything beyond speed.
- Live coupling of the MPM step to the stream. Both work separately; coupling them is Phase 2 server work.
- Timing on an idle GPU.

## Phase 0 verdict

| Component | Go / no-go |
|---|---|
| Newton implicit MPM, face stability | **Go.** Correct trends (cover-independent, friction-dependent). 0.6× real time at D/10, but that underestimates p_f by about 50 %. D/20 reaches 0.79 of Vermeer offline |
| Newton implicit MPM, EPB chamber + cutterhead + screw | **Go for speed and pressure distribution** (0.4–0.8× real time, shared GPU). **Not yet** for screw discharge: it needs pressure control and a resolved inlet |
| WebSocket streaming, 100k–300k at 20–30 Hz | **Go.** TSP0 u16, no compression. Wired network for full rate |

## Reproduce

```bash
cd phase0
./run_face_sweep.sh        # logs/face_*.json (+ .npz with force history and final particles)
./run_epb_sweep.sh         # logs/epb_*.json (+ .npz with pressure/torque rows and discharge counts)
.venv-newton/bin/python stream/run_stream_sweep.py
DISPLAY=:1 ~/Documents/construction-site-simulation/phase0/.venv-newton/bin/python stream/run_browser.py
```

Single runs, for example: `.venv-newton/bin/python face_bench.py --voxel 0.1 --out logs/x.json` or `.venv-newton/bin/python epb_bench.py --voxel 0.1 --screw-rpm 10 --frames 600`.
