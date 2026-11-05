# Server (Phase 2): GPU ground physics

Newton implicit MPM scenes for the tunnel face, the EPB chamber and the screw conveyor, run on the NVIDIA DGX Spark (Newton 1.7.0 / Warp 1.19.0 on CUDA 13). The plan, its calibration targets and checks are in [docs/plans/phase2-mpm-face-chamber.md](../docs/plans/phase2-mpm-face-chamber.md).

Every result is **uncalibrated** until it passes the checks named in the plan. The label travels with the result.

## Set up and run

```bash
cd server
UV_PROJECT_ENVIRONMENT=.venv-server uv sync
UV_PROJECT_ENVIRONMENT=.venv-server uv run pytest -q
.venv-server/bin/python -m tunnelsim_server.runner face --voxel 0.2 --name face_v0.2
```

Results go to `results/<name>.json`, with a run record:
- the git commit and the Newton, Warp and NumPy versions;
- the parameters, seed and resolution;
- the GPU load before the run;
- whether the timing counts for decisions;
- the calibration status.

## Layout

| Path | What it holds | Work package |
|---|---|---|
| `tunnelsim_server/scenes/face.py` | Tunnel face in dry sand under a retracting plate, ported unchanged from `phase0/face_bench.py` | WP0; WP2 adds pressure control |
| `tunnelsim_server/materials.py` | Soil parameters and their mapping to Newton's Drucker–Prager material: μ = sin φ′, s = c′ cos φ′; Tresca μ = 0, s = cu | WP1 |
| `tunnelsim_server/probes.py` | Forces on collider bodies from the contact impulses | WP0 |
| `tunnelsim_server/runrecord.py` | Run records and the GPU load and reservation check | WP0 |
| `tunnelsim_server/runner.py` | Batch runs to JSON | WP0 |
| `tests/test_golden_face.py` | Golden test: the Phase 0 face numbers must not drift | WP0 |
| `tunnelsim_server/scenes/k0.py`, `rankine.py`, `collapse.py` | Element tests: at-rest stress, Rankine active wall, Rousseau et al. column collapse ([results](../docs/validation/mpm-element-tests.md)) | WP1 |
| `tests/test_materials.py`, `tests/test_element_gpu.py` | The Mohr–Coulomb mapping; Rankine and B00 collapse pinned on the GPU | WP1 |
| `tunnelsim_server/scenes/tunnel_2d.py` | Plane-strain tunnel with a closing ring of segments; the clay investigation ([status](../docs/validation/mpm-clay.md)) | WP3 (blocked) |
| `tunnelsim_server/scenes/face_sand.py`, `tests/test_face_sand_gpu.py` | Face in dry sand, half-model, displacement or pressure (servo) control, mechanism and settlement outputs ([results](../docs/validation/mpm-face-sand.md)) | WP2 |
| `tunnelsim_server/scenes/chamber.py` | EPB chamber under pressure with an analytical screw sink and a PI screw controller ([results](../docs/validation/mpm-chamber.md)) | WP4 (blocked) |
| `tunnelsim_server/live.py` | Live dry-sand face over a WebSocket for the EPB demo's "Ground physics" panel (`web/epb/ground.js`); local only | WP6 (face only) |
| `diagnostics/` | One-off investigation scripts (packing, cohesion scaling, ring piling, equilibrium), each with its result in the docstring | WP0b, WP3 |
| `gpu_reservations.json` | GPU windows reserved for this project on the shared Spark (local time) | WP0 |

Still to come: `scenes/screw.py` (WP5), and the chamber in the live view once WP4 is unblocked.

## Live view (local only)

```bash
cd server
.venv-server/bin/python -m tunnelsim_server.live            # ws://127.0.0.1:8765, Idinger dry-sand face, C/D 1, D/10
cd .. && python3 -m http.server 8741 --bind 127.0.0.1         # in a second terminal
```

Open `http://127.0.0.1:8741/web/epb/index.html?ground=ws://127.0.0.1:8765`. The EPB demo then shows a "Ground physics" panel. Without the `ground` parameter, the demo is unchanged.

- **What it shows:** the MPM section through the face, coloured by movement, with its own support-pressure slider (0–30 kPa).
- **What it does:** above the limit the face holds; below it the face gives way and the chimney rises to the surface. "Reset the face" rebuilds the scene.
- **Readouts:** the face pressure, with the measured limit, the MPM bracket and the analytical value beside it, and the real-time factor.
- **What it is not:** this is the WP2 benchmark face, not the demo's own ground.

## GPU time

The Spark is shared with the sister project ([construction-site-simulation](https://github.com/dtt-github/construction-site-simulation)).
- A run's timing counts for decisions only inside a window in `gpu_reservations.json` and with no other process on the GPU.
- Every other timing is recorded as a lower bound.
- Physics results do not depend on GPU load: the golden runs give identical numbers on a busy and on an idle GPU.

## Golden test

`tests/test_golden_face.py` pins the Phase 0 face run (D 2 m, C/D 1, voxel D/10, tan φ 0.75):
- 208,068 particles;
- settled pressure 8.216 kPa;
- limit 1.629 kPa, 0.529 of Vermeer;
- tolerance ±2 %.

The D/20 run also reproduces Phase 0: 0.785 of Vermeer.

If a Newton or Warp upgrade breaks the test, recalibrate on purpose and re-pin with a note. Don't just edit the numbers. The test is skipped where there is no CUDA GPU, as in CI.
