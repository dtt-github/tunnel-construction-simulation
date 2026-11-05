"""Shared scene pieces: particle fill, box walls as kinematic colliders, solver set-up and stress read-out."""
from __future__ import annotations

import numpy as np


def fill_box(lo, hi, h: float, seed: int = 0) -> np.ndarray:
    """Jittered grid of particles at spacing h inside the box lo..hi."""
    rng = np.random.default_rng(seed)
    axes = [np.arange(a + h / 2, b, h) for a, b in zip(lo, hi)]
    g = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)
    return (g + rng.uniform(-0.25 * h, 0.25 * h, g.shape)).astype(np.float32)


def add_walls(builder, body: int, boxes):
    """Static boxes (centre (x, y, z), half sizes (hx, hy, hz)) on one kinematic body, so they share a friction."""
    import warp as wp

    for c, (hx, hy, hz) in boxes:
        builder.add_shape_box(body, xform=wp.transform(wp.vec3(*c), wp.quat_identity()), hx=hx, hy=hy, hz=hz)


def make_particles(pts: np.ndarray, h: float, soil):
    import warp as wp

    import newton
    from newton.solvers import SolverImplicitMPM

    b = newton.ModelBuilder()
    SolverImplicitMPM.register_custom_attributes(b)
    n = len(pts)
    b.add_particles(pos=[wp.vec3(*q) for q in pts], vel=[wp.vec3(0.0)] * n, mass=[float(h**3 * soil.density)] * n,
                    radius=[h * 0.5] * n, custom_attributes=soil.custom_attributes(n))
    return b


def make_solver(particle_model, collider_model, voxel: float, iterations: int, friction_by_body: dict, gravity=None):
    from newton.solvers import SolverImplicitMPM

    cfg = SolverImplicitMPM.Config()
    cfg.voxel_size = voxel
    cfg.max_iterations = iterations
    cfg.critical_fraction = 0.0
    cfg.strain_basis = "P0"
    solver = SolverImplicitMPM(particle_model, config=cfg)
    solver.setup_collider(model=collider_model)
    solver.setup_collider(model=collider_model, collider_friction=[friction_by_body.get(int(b), 0.0) for b in solver.collider_body_index.numpy()])
    return solver


def particle_stress(state) -> np.ndarray:
    """Cauchy stress per particle (n, 3, 3), Pa, as Newton stores it (tension positive)."""
    return state.mpm.particle_stress.numpy()
