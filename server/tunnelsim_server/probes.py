"""Probes: forces on collider bodies from the MPM contact impulses (the way a pressure cell or a load cell would see
them). Taken from the Phase 0 benchmarks (phase0/face_bench.py, phase0/epb_bench.py)."""
from __future__ import annotations

import numpy as np


def collider_forces(solver, state, body_index: np.ndarray, dt: float) -> dict[int, np.ndarray]:
    """Force vector (N) exerted by the soil on each collider body over the last step, keyed by body id."""
    imp, _pos, cid = solver.collect_collider_impulses(state)
    imp, cid = imp.numpy(), cid.numpy()
    valid = cid >= 0
    bids = np.full(cid.shape, -1)
    bids[valid] = body_index[np.clip(cid[valid], 0, len(body_index) - 1)]
    out = {}
    for b in np.unique(bids[valid]):
        out[int(b)] = -imp[bids == b].sum(axis=0) / dt
    return out
