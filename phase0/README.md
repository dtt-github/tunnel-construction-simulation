# Phase 0: platform benchmarks (DGX Spark)

See [docs/ROADMAP.md](../docs/ROADMAP.md#phase-0-platform-dgx-spark). Results go into `phase0/RESULTS.md`, recording hardware, versions, particle counts, real-time factor and the commands used.

| File | What it measures |
|---|---|
| `face_bench.py` | Tunnel face in dry sand, retracting support plate; limit pressure vs Vermeer et al. (2002) |
| `epb_bench.py` | EPB chamber with rotating cutterhead and screw conveyor; bulkhead pressure, torques, discharge |
| `stream/` | WebSocket particle streaming (TSP0 format): Python/Warp server, Node and Chrome clients |
