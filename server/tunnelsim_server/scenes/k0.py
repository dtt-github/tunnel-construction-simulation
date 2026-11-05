"""At-rest element test: a laterally confined sand column (frictionless walls) loads under its own weight. For a soil
that stays elastic, sigma_h / sigma_v = nu / (1 - nu); materials.drained_sand sets nu = K0 / (1 + K0) so that this
equals Jaky's K0 = 1 - sin phi'. The test reads Newton's particle stress (compression positive) in the middle of the
column and reports K = sigma_h / sigma_v and sigma_v / (gamma depth).

WP1 result (docs/validation/mpm-element-tests.md): K does not follow nu (0.74-0.86 for target K0 0.15-0.90), so the
at-rest state is taken from the analytical model and the MPM is used for the failure phase.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from ..materials import Soil
from .common import add_walls, fill_box, make_particles, make_solver, particle_stress

G = 9.81


@dataclass(frozen=True)
class K0Config:
    width: float = 1.0
    height: float = 2.0
    voxel: float = 0.1
    ppc: int = 2
    steps: int = 120  # 2 s at 60 fps; static after about 1 s
    fps: float = 60.0
    iterations: int = 50
    seed: int = 0


def run(cfg: K0Config, soil: Soil) -> tuple[dict, dict]:
    import warp as wp

    import newton

    wp.init()
    W, H, dx = cfg.width, cfg.height, cfg.voxel
    t = max(0.3, 2 * dx)
    b = newton.ModelBuilder()
    body = b.add_body(xform=wp.transform_identity(), mass=1.0, is_kinematic=True)
    add_walls(b, body, [((-t, W / 2, H / 2), (t, W, H)), ((W + t, W / 2, H / 2), (t, W, H)),
                        ((W / 2, -t, H / 2), (W, t, H)), ((W / 2, W + t, H / 2), (W, t, H))])
    b.add_ground_plane()
    cm = b.finalize()
    h = dx / cfg.ppc
    pts = fill_box((0, 0, 0), (W, W, H), h, cfg.seed)
    pm = make_particles(pts, h, soil).finalize()
    solver = make_solver(pm, cm, dx, cfg.iterations, {body: 0.0, -1: 0.0})
    st = cm.state()
    s = pm.state()
    s.body_q, s.body_qd, s.body_f = wp.clone(st.body_q), wp.zeros_like(st.body_qd), wp.zeros_like(st.body_f)
    for _ in range(cfg.steps):
        solver.step(s, s, contacts=None, control=None, dt=1.0 / cfg.fps)
    sig, z = particle_stress(s), s.particle_q.numpy()[:, 2]
    top = float(z.max())
    m = (z > 0.3 * H) & (z < 0.7 * H)
    sv = sig[m, 2, 2]
    sh = 0.5 * (sig[m, 0, 0] + sig[m, 1, 1])
    gamma = soil.density * G
    return {"particles": len(pts), "K": round(float(sh.mean() / sv.mean()), 4),
            "sigma_v_over_gamma_depth": round(float(np.mean(sv / (gamma * (top - z[m])))), 4),
            "K_target": round(soil.poisson_ratio / (1 - soil.poisson_ratio), 4), "top_after_settling": round(top, 4)}, {}


def params(cfg: K0Config, soil: Soil) -> dict:
    return {**asdict(cfg), "soil": asdict(soil)}
