"""Soil parameters and their mapping to Newton's implicit MPM material.

Newton's yield criterion (newton/_src/solvers/implicit_mpm/rheology_solver_kernels.py, `shear_yield_stress`, with the
DB16 orthonormal stress basis of warp.fem.SymmetricTensorMapper) reduces to a Drucker-Prager cone

    sqrt(J2) <= s + mu * p        p = mean pressure (compression positive), s = `yield_stress`, mu = `friction`

with an optional compressive cap (`yield_pressure`, off by default) and tensile cut-off (`tensile_yield_ratio`).
`dilatancy` = 0 selects the non-associated flow rule (no plastic volume change, psi = 0). Rousseau et al. (2022,
arXiv:2211.04865, eq. 2.4) write the same criterion, ||Dev sigma|| <= mu p with ||tau|| = sqrt(tau:tau / 2), so their
measured mu carries over unchanged.

Matching a Mohr-Coulomb soil (phi', c') to the cone depends on the stress path:
- plane strain, psi = 0: sqrt(J2) = sin(phi') p + c' cos(phi') at failure, so mu = sin(phi'), s = c' cos(phi');
- triaxial compression: q = 6 sin(phi') / (3 - sin(phi')) p, so mu = 2 sqrt(3) sin(phi') / (3 - sin(phi')).
Phase 0 used mu = tan(phi'), which is neither: mu = 0.75 is phi' 48.6 deg in plane strain and 32.3 deg in triaxial
compression. The Rankine active-wall element test (WP1) checks which match the solver follows.

Undrained clay (Tresca, phi = 0): mu = 0 and s = cu (plane strain, sqrt(J2) = (sigma1 - sigma3) / 2 = cu).

Elasticity: Young's modulus E and Poisson's ratio nu. For a gravity-loaded, laterally confined soil that stays
elastic, sigma_h / sigma_v = nu / (1 - nu); nu = K0 / (1 + K0) therefore gives the at-rest ratio K0 (Jaky:
K0 = 1 - sin phi'). The K0 element test checks this.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


def mu_plane_strain(phi_deg: float) -> float:
    """Newton friction for a Mohr-Coulomb angle matched in plane strain with no dilation."""
    return math.sin(math.radians(phi_deg))


def mu_triaxial_compression(phi_deg: float) -> float:
    s = math.sin(math.radians(phi_deg))
    return 2 * math.sqrt(3) * s / (3 - s)


def phi_from_mu_plane_strain(mu: float) -> float:
    return math.degrees(math.asin(min(mu, 1.0)))


def jaky_k0(phi_deg: float) -> float:
    return 1 - math.sin(math.radians(phi_deg))


def poisson_for_k0(k0: float) -> float:
    return k0 / (1 + k0)


def rankine_ka(phi_deg: float) -> float:
    s = math.sin(math.radians(phi_deg))
    return (1 - s) / (1 + s)


@dataclass(frozen=True)
class Soil:
    """A soil for the MPM. friction and yield_stress are Newton's parameters; phi_deg and cohesion record the soil
    they were derived from and how (match)."""

    name: str
    density: float  # bulk density, kg/m^3
    friction: float  # Newton `mpm:friction` (mu)
    source: str
    yield_stress: float = 0.0  # Pa, Newton `mpm:yield_stress` (s)
    young_modulus: float = 1.0e15  # Pa; Newton's default is rigid-plastic
    poisson_ratio: float = 0.3
    dilatancy: float = 0.0
    phi_deg: float | None = None
    cohesion: float = 0.0
    match: str = "none"
    extra: dict = field(default_factory=dict)

    def custom_attributes(self, n: int) -> dict:
        return {"mpm:friction": [self.friction] * n, "mpm:yield_stress": [self.yield_stress] * n,
                "mpm:young_modulus": [self.young_modulus] * n, "mpm:poisson_ratio": [self.poisson_ratio] * n,
                "mpm:dilatancy": [self.dilatancy] * n}


def drained_sand(name: str, density: float, phi_deg: float, young_modulus: float, source: str, cohesion: float = 0.0,
                 k0: float | None = None, match: str = "plane_strain") -> Soil:
    """Drained sand from Mohr-Coulomb parameters. nu is set so the elastic at-rest ratio equals K0 (Jaky by default)."""
    mu = mu_plane_strain(phi_deg) if match == "plane_strain" else mu_triaxial_compression(phi_deg)
    k0 = jaky_k0(phi_deg) if k0 is None else k0
    return Soil(name, density, mu, source, yield_stress=cohesion * math.cos(math.radians(phi_deg)), young_modulus=young_modulus,
                poisson_ratio=poisson_for_k0(k0), phi_deg=phi_deg, cohesion=cohesion, match=match, extra={"k0": k0})


def undrained_clay(name: str, density: float, cu: float, young_modulus: float, source: str, nu: float = 0.49) -> Soil:
    return Soil(name, density, 0.0, source, yield_stress=cu, young_modulus=young_modulus, poisson_ratio=nu, phi_deg=0.0,
                cohesion=cu, match="tresca")


# Phase 0 dry sand: density and friction chosen for the benchmark, not a measured soil (phase0/RESULTS.md). Default
# (rigid-plastic) elasticity, so the golden test keeps its numbers.
PHASE0_SAND = Soil("Phase 0 dry sand", 1600.0, 0.75, "phase0/RESULTS.md (benchmark values, not a measured soil)")
