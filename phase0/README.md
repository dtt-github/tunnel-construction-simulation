# Phase 0: GPU platform benchmarks (DGX Spark)

These benchmarks check whether NVIDIA Newton's implicit MPM can carry the face and chamber physics in real time, and whether particle states can be streamed to a browser.

- **Findings:** [RESULTS.md](RESULTS.md) records hardware, versions, particle counts, real-time factors and the exact commands.
- **Plan:** [ROADMAP.md, Phase 0](../docs/ROADMAP.md#phase-0-platform-dgx-spark).
- **Demo:** the [replay viewer](https://dtt-github.github.io/tunnel-construction-simulation/phase0/replays/) plays back two recorded runs.

## Files

| File | What it does |
|---|---|
| [`face_bench.py`](face_bench.py) | Tunnel face in dry sand with a retracting support plate. Compares the limit pressure with Vermeer et al. (2002). `--record` writes a replay |
| [`epb_bench.py`](epb_bench.py) | EPB chamber with a rotating cutterhead and screw conveyor: bulkhead pressure, torques, discharge. `--record` writes a replay |
| [`run_face_sweep.sh`](run_face_sweep.sh), [`run_epb_sweep.sh`](run_epb_sweep.sh) | Parameter sweeps; results go to [`logs/`](logs) |
| [`stream/`](stream) | WebSocket particle streaming (TSP0 format): Python/Warp server, Node and Chrome clients, sweep and browser runners |
| [`replay.py`](replay.py) | TSR0 recorder: gzip, u16 positions for frame 0, i16 deltas for later frames, per-frame scalars and scene metadata |
| [`replays/index.html`](replays/index.html) | Browser viewer for TSR0 replays (three.js), with charts. The recordings themselves are published on GitHub Pages, not in `main` |

## Running

Use the Newton environment from the sister project ([construction-site-simulation](https://github.com/dtt-github/construction-site-simulation)):

```bash
uv venv .venv-newton && uv pip install -p .venv-newton "newton[examples]" websockets
```

```bash
.venv-newton/bin/python face_bench.py --voxel 0.1 --record replays/face.tsr.gz
```

```bash
.venv-newton/bin/python epb_bench.py --voxel 0.2 --screw-rpm 10 --record replays/epb.tsr.gz
```
