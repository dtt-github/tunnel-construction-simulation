"""Shared scene pieces: particle fill, box walls as kinematic colliders, solver set-up and stress read-out."""
from __future__ import annotations

import numpy as np


# Initial particle jitter as a fraction of the spacing (0.25 in Phase 0 and WP0-WP3; WP0b tests 0).
JITTER = 0.25


def fill_box(lo, hi, h: float, seed: int = 0, jitter: float | None = None) -> np.ndarray:
    """Grid of particles at spacing h inside the box lo..hi, jittered by +-jitter h (module default JITTER)."""
    j = JITTER if jitter is None else jitter
    rng = np.random.default_rng(seed)
    axes = [np.arange(a + h / 2, b, h) for a, b in zip(lo, hi)]
    g = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)
    return (g + rng.uniform(-j * h, j * h, g.shape)).astype(np.float32)


def add_walls(builder, body: int, boxes):
    """Static boxes (centre (x, y, z), half sizes (hx, hy, hz)) on one kinematic body, so they share a friction."""
    import warp as wp

    for c, (hx, hy, hz) in boxes:
        builder.add_shape_box(body, xform=wp.transform(wp.vec3(*c), wp.quat_identity()), hx=hx, hy=hy, hz=hz)


# Particle radius as a fraction of the spacing h. Newton takes a particle's volume as (2r)^3, so 0.5 gives a nominal
# packing of 1.0 (Phase 0 and WP0-WP3). WP0b default 0.7 (packing 2.744): the column barely compacts (diagnostics/packing.py).
RADIUS = 0.7


def packing() -> float:
    """Nominal packing (2 RADIUS)^3: Newton's stresses act per unit of particle volume, so its effective cohesion and
    stiffness are this many times the input values (diagnostics/cohesion_scale.py)."""
    return (2 * RADIUS) ** 3


def _attributes(soil, n: int) -> dict:
    """Soil attributes with yield stress and Young's modulus divided by the packing, so the soil behaves as specified."""
    a = soil.custom_attributes(n)
    k = packing()
    for key in ("mpm:yield_stress", "mpm:young_modulus"):
        a[key] = [v / k for v in a[key]]
    return a


def make_particles(pts: np.ndarray, h: float, soil):
    import warp as wp

    import newton
    from newton.solvers import SolverImplicitMPM

    b = newton.ModelBuilder()
    SolverImplicitMPM.register_custom_attributes(b)
    n = len(pts)
    b.add_particles(pos=[wp.vec3(*q) for q in pts], vel=[wp.vec3(0.0)] * n, mass=[float(h**3 * soil.density)] * n,
                    radius=[h * RADIUS] * n, custom_attributes=_attributes(soil, n))
    return b


def make_particles_multi(groups):
    """One particle builder with several materials: groups of (points, spacing h, soil)."""
    import warp as wp

    import newton
    from newton.solvers import SolverImplicitMPM

    b = newton.ModelBuilder()
    SolverImplicitMPM.register_custom_attributes(b)
    for pts, h, soil in groups:
        n = len(pts)
        b.add_particles(pos=[wp.vec3(*q) for q in pts], vel=[wp.vec3(0.0)] * n, mass=[float(h**3 * soil.density)] * n,
                        radius=[h * RADIUS] * n, custom_attributes=_attributes(soil, n))
    return b


# Newton's packing constraint ("fraction for particles under which the yield surface collapses"; > 0 enables the void-
# fraction unilateral incompressibility offset). 0 (off) is what Phase 0 and WP0-WP3 used; WP3 diagnostics test it.
CRITICAL_FRACTION = 0.0


# Further SolverImplicitMPM.Config settings (name: value); empty = Newton's defaults with strain basis P0 (WP0-WP3).
SOLVER_OPTIONS: dict = {}


def make_solver(particle_model, collider_model, voxel: float, iterations: int, friction_by_body: dict, gravity=None):
    from newton.solvers import SolverImplicitMPM

    cfg = SolverImplicitMPM.Config()
    cfg.voxel_size = voxel
    cfg.max_iterations = iterations
    cfg.critical_fraction = CRITICAL_FRACTION
    cfg.strain_basis = "P0"
    for k, v in SOLVER_OPTIONS.items():
        setattr(cfg, k, v)
    solver = SolverImplicitMPM(particle_model, config=cfg)
    solver.setup_collider(model=collider_model)
    solver.setup_collider(model=collider_model, collider_friction=[friction_by_body.get(int(b), 0.0) for b in solver.collider_body_index.numpy()])
    return solver


def particle_stress(state) -> np.ndarray:
    """Cauchy stress per particle (n, 3, 3), Pa, tension positive. Newton stores it per unit of particle volume, so it is
    scaled by the packing."""
    return state.mpm.particle_stress.numpy() * packing()
