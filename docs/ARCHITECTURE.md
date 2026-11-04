# Architecture

Full reasoning and sources: [research/research-survey.md](research/research-survey.md), section A.

## Principle: the right physics at the right scale

| Scale | Physics | Where it runs |
|---|---|---|
| Alignment (km) | Analytical/empirical models: convergence–confinement, settlement troughs, TBM performance, lining design. Trained surrogates later | Browser (JS) and server (Python), the same model in both |
| Machine (m) | Rigid/articulated bodies: cutterhead drive, thrust cylinders, erector, gripper, screw, conveyors, muck cars, jumbo booms | Browser: Jolt (WASM). Server: Newton MuJoCo-Warp/Kamino when coupled to soil |
| Face and chamber (cm–m) | Continuum particles: implicit MPM for soil at the face, in the EPB chamber and screw, and in muck flow | Server: NVIDIA Newton on a DGX Spark. Optional visual-grade WebGPU patch in the browser |
| Cutter (mm) | Rock fragmentation under discs/picks | Empirical in real time (CSM, NTNU). Offline bonded-particle DEM for calibration and teaching |

```
Browser (any machine)                                    DGX Spark (GB10, CUDA 13)
three.js + Jolt + models/js  ◄── WebSocket, binary ──►   Python (uv) + Newton 1.7 / Warp 1.19
operator console, HUD, alarms     20–30 Hz state          SolverImplicitMPM  (face, chamber, muck)
fallback: analytical only         commands up             SolverMuJoCo/Kamino (machine)
                                                          models/py (same models, cross-check)
Offline: Kratos GeoMechanics · Chrono · YADE  →  calibration, surrogate training
```

## The model library contract

- Every model exists twice: `models/py/tunnelsim_models/<model>.py` (reference) and `models/js/<model>.js` (browser).
- `models/py/make_vectors.py` writes `models/test-vectors/<model>.json`. The JS tests must match it to 1e-9 relative.
- The Python tests also check hand-calculated anchor values taken from the cited papers or worked examples. This makes the reference itself verifiable, not only consistent.
- Each model file starts with its references, equations and units. SI units at interfaces, except where the discipline convention is clearer and documented (CSM uses mm/MPa/N).
- Models are pure functions with no rendering or state, so they can be called from the browser, the server, notebooks and Gymnasium environments.

## Fidelity levels (shown in the UI)

1. **Analytical:** browser only. Always available, deterministic.
2. **Local GPU:** adds a WebGPU particle patch for visuals. Labelled visual-grade.
3. **Server MPM:** Newton on the GPU server drives face, chamber and muck physics.
4. **Replay:** recorded server runs played back for public demos without a GPU.

## Coordinate frame

Metres, Y up. In the web client the machine stays at the origin with its face at z = 0, and the world moves by +chainage (excavation along −z). This keeps physics near the origin for float precision and avoids moving Jolt bodies with the machine.

## Data

- **Geology:** zones and blocks along the alignment, holding intact properties (UCS, BTS, CAI, mi, Ei), rock-mass properties (GSI, RMR, Q) and soil parameters (γ, c′, φ′, k, E). Later: voxel models from boreholes.
- **Machine signals:** an original, open signal schema for TBM channels (thrust groups, strokes, chamber pressures, grout lines, slurry circuit). It is informed by industry practice but does not copy proprietary signal lists.
- **Geometry exchange:** glTF for machines, IFC 4.3 (IfcTunnel) for alignment and lining, OpenUSD on the server.

## Machines, presets and industry practice

Industry context: [research/industry-survey.md](research/industry-survey.md), covering Herrenknecht, Robbins, VMT, Tunnelsoft and The Boring Company.

- **Presets by class, not brand.** For example "7.1 m urban EPB" or "14.4 m hard-rock main beam", with diameter, cutter count and size, thrust, torque, power and rpm taken from published spec sheets. Each number cites its source in the preset file.
- **Process features to model.** These are generic engineering principles, well documented in public, and not any vendor's implementation:
  - guidance and steering loop;
  - universal-ring key-position selection;
  - mode switching on convertible machines;
  - continuous advance (lining installed while boring);
  - cutter-change interventions;
  - spoil-removal capacity.
- **Validation bounds.** The industry world-record advance rates by diameter class are the upper limit for simulated rates. Published project data (power, torque, weekly rates) gives typical targets.

## Interfaces

- **Signals:** our own open, neutral tag names (e.g. `thrust.total_kN`, `cutterhead.torque_kNm`, `chamber.pressure_top_bar`, `guidance.tail_dev_h_mm`). None of the surveyed vendors publishes an OPC UA tunnelling model, so no vendor schema is copied.
- **Export:** CSV/Parquet time series and per-ring reports.
- **Planned:** an optional OPC UA server, and IFC 4.3 / LandXML for alignment and as-built rings.
- **IP caution:** product names (e.g. Mixshield, TUnIS, Prufrock) are trademarks of their owners and are used only to cite sources. Do not copy proprietary designs, documents or brand assets. See the IP section of the industry survey, including relevant patents on automated segment erection, continuous advance and TBM simulators.

## Versions (pin them)

three.js 0.182.0 · jolt-physics 1.1.1 · Newton 1.7.x · Warp 1.19.x · Python 3.11+ (3.12 on the Spark).

Newton 1.7 changed MPM material scaling, so keep golden tests when upgrading.
