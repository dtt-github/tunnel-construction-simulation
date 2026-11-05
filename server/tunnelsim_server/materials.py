"""Soil parameters and their mapping to Newton's implicit MPM material.

WP0 carries only what Phase 0 used: Newton's default rigid-plastic material with a friction coefficient (tan phi') and
a bulk density. WP1 adds the elastoplastic mapping (E, nu, c' or cu, dilatancy, tensile yield) with its derivation and
element tests (K0 under gravity, simple shear, granular column collapse; plan, WP1).
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Soil:
    name: str
    density: float  # bulk density, kg/m^3
    friction: float  # tan(phi'), Newton's `mpm:friction`
    source: str

    @property
    def phi_deg(self) -> float:
        return math.degrees(math.atan(self.friction))

    def custom_attributes(self, n: int) -> dict:
        return {"mpm:friction": [self.friction] * n}


# Phase 0 dry sand: density and friction chosen for the benchmark, not a measured soil (phase0/RESULTS.md).
PHASE0_SAND = Soil("Phase 0 dry sand", 1600.0, 0.75, "phase0/RESULTS.md (benchmark values, not a measured soil)")
