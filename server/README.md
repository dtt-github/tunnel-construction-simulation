# Server (Phase 2)

Python simulation server for the NVIDIA DGX Spark: NVIDIA Newton 1.7 / Warp 1.19 on CUDA 13.

Planned:

- **Face, EPB chamber, screw conveyor, muck:** `SolverImplicitMPM`.
- **Machine:** `SolverMuJoCo` / Kamino, coupled to the soil.
- **Transport:** binary WebSocket stream to `web/` at 20–30 Hz.
- **Cross-checks:** `models/py` is used for the analytical comparisons.

The environment follows the sister project ([construction-site-simulation](https://github.com/dtt-github/construction-site-simulation), `phase0/RESULTS.md`):

```bash
uv venv .venv-newton && uv pip install -p .venv-newton "newton[examples]" websockets
```
