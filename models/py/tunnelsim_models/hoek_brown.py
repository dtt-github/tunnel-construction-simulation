"""Generalised Hoek-Brown rock-mass parameters.

References
- Hoek, E., Carranza-Torres, C., Corkum, B. (2002). Hoek-Brown failure criterion - 2002 edition.
  Proc. NARMS-TAC, Toronto, 267-273.
- Hoek, E., Diederichs, M.S. (2006). Empirical estimation of rock mass modulus.
  Int. J. Rock Mech. Min. Sci. 43, 203-215.

Units: stresses in MPa, moduli in MPa.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class HoekBrownParams:
    mb: float
    s: float
    a: float
    sigma_cm: float  # global rock-mass strength (Hoek et al. 2002, eq. 13), MPa
    sigma_c_mass: float  # uniaxial compressive strength of the rock mass (s**a * sigma_ci), MPa
    e_rm: float | None  # rock-mass modulus, MPa (None if e_i not given)


def hoek_brown(gsi: float, mi: float, sigma_ci: float, d: float = 0.0, e_i: float | None = None) -> HoekBrownParams:
    """Rock-mass constants from GSI, intact constant mi, intact UCS sigma_ci and disturbance D."""
    if not 0 <= gsi <= 100:
        raise ValueError("GSI must be in [0, 100]")
    if not 0 <= d <= 1:
        raise ValueError("D must be in [0, 1]")
    mb = mi * math.exp((gsi - 100) / (28 - 14 * d))
    s = math.exp((gsi - 100) / (9 - 3 * d))
    a = 0.5 + (math.exp(-gsi / 15) - math.exp(-20 / 3)) / 6
    sigma_cm = sigma_ci * ((mb + 4 * s - a * (mb - 8 * s)) * (mb / 4 + s) ** (a - 1)) / (2 * (1 + a) * (2 + a))
    e_rm = None
    if e_i is not None:
        e_rm = e_i * (0.02 + (1 - d / 2) / (1 + math.exp((60 + 15 * d - gsi) / 11)))
    return HoekBrownParams(mb=mb, s=s, a=a, sigma_cm=sigma_cm, sigma_c_mass=sigma_ci * s**a, e_rm=e_rm)


def sigma1_at_failure(sigma3: float, sigma_ci: float, p: HoekBrownParams) -> float:
    """Major principal stress at failure for a given minor principal stress (MPa)."""
    return sigma3 + sigma_ci * (p.mb * sigma3 / sigma_ci + p.s) ** p.a
