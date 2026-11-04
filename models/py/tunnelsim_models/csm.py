"""Colorado School of Mines (CSM) disc-cutter model for hard-rock TBMs.

References
- Rostami, J., Ozdemir, L. (1993). A new model for performance prediction of hard rock TBMs.
  Proc. RETC, Boston, 793-809.
- Rostami, J. (1997). Development of a force estimation model for rock fragmentation with disc
  cutters through theoretical modeling and physical measurement of crushed zone pressure.
  PhD thesis, Colorado School of Mines.

Core relations (constant-cross-section disc):
    phi  = acos((R - p) / R)                               contact angle
    P0   = C * cbrt( S * sigma_c**2 * sigma_t / (phi * sqrt(R * T)) )   base crushed-zone pressure
    Ft   = T * R * phi * P0 / (1 + psi)                    total resultant force
    Fn   = Ft * cos(phi / 2),   Fr = Ft * sin(phi / 2)

Units: lengths in mm, stresses in MPa -> pressures in MPa, forces in N (mm^2 * MPa = N).
C ~= 2.12 (dimensionless), psi in [-0.2, 0.2] (pressure-distribution exponent; ~0.1 for sharp discs).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

C_DEFAULT = 2.12


@dataclass(frozen=True)
class Cutter:
    diameter_mm: float = 482.6  # 19-inch disc
    tip_width_mm: float = 19.0
    spacing_mm: float = 85.0
    psi: float = 0.1
    max_load_kn: float = 311.0  # 19" rated load, Robbins disc-cutter spec sheet (docs/research/industry-survey.md §4.2)


@dataclass(frozen=True)
class CutterForces:
    phi_rad: float
    p0_mpa: float
    total_n: float
    normal_n: float
    rolling_n: float

    @property
    def rolling_coefficient(self) -> float:
        return self.rolling_n / self.normal_n


def cutter_forces(penetration_mm: float, ucs_mpa: float, bts_mpa: float, cutter: Cutter = Cutter(), c: float = C_DEFAULT) -> CutterForces:
    if penetration_mm <= 0:
        return CutterForces(0.0, 0.0, 0.0, 0.0, 0.0)
    r = cutter.diameter_mm / 2
    if penetration_mm >= r:
        raise ValueError("penetration must be smaller than the cutter radius")
    phi = math.acos((r - penetration_mm) / r)
    p0 = c * (cutter.spacing_mm * ucs_mpa**2 * bts_mpa / (phi * math.sqrt(r * cutter.tip_width_mm))) ** (1 / 3)
    ft = cutter.tip_width_mm * r * phi * p0 / (1 + cutter.psi)
    return CutterForces(phi, p0, ft, ft * math.cos(phi / 2), ft * math.sin(phi / 2))


def penetration_for_normal_force(normal_force_n: float, ucs_mpa: float, bts_mpa: float, cutter: Cutter = Cutter(), c: float = C_DEFAULT) -> float:
    """Invert the CSM model: penetration per revolution (mm) that a given per-cutter normal force achieves."""
    if normal_force_n <= 0:
        return 0.0
    lo, hi = 0.0, min(cutter.diameter_mm / 2 * 0.25, 30.0)
    if cutter_forces(hi, ucs_mpa, bts_mpa, cutter, c).normal_n < normal_force_n:
        return hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if cutter_forces(mid, ucs_mpa, bts_mpa, cutter, c).normal_n < normal_force_n:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


@dataclass(frozen=True)
class TbmPerformance:
    penetration_mm_rev: float
    rop_m_h: float
    normal_per_cutter_kn: float
    rolling_per_cutter_kn: float
    cutterhead_torque_knm: float
    cutterhead_power_kw: float
    cutter_overloaded: bool
    limited_by: str  # "thrust" or "torque"


def tbm_performance(
    thrust_kn: float,
    rpm: float,
    n_cutters: int,
    head_diameter_m: float,
    ucs_mpa: float,
    bts_mpa: float,
    cutter: Cutter = Cutter(),
    torque_radius_factor: float = 0.3,
    max_torque_knm: float | None = None,
) -> TbmPerformance:
    """Steady-state penetration, ROP, torque and power for a given cutting thrust.

    thrust_kn is the net thrust reaching the cutters (total jack force minus shield friction,
    backup drag etc.). Torque uses the Rostami-Ozdemir approximation T = k * D * N * Fr with k ~= 0.3.
    If max_torque_knm is given and the thrust-limited penetration would exceed it (typical in weak
    rock), penetration is reduced until torque equals the installed limit.
    """
    k = torque_radius_factor * head_diameter_m * n_cutters / 1000

    def torque_at(pen: float) -> float:
        return k * cutter_forces(pen, ucs_mpa, bts_mpa, cutter).rolling_n

    fn = thrust_kn * 1000 / n_cutters
    p = penetration_for_normal_force(fn, ucs_mpa, bts_mpa, cutter)
    limited_by = "thrust"
    if max_torque_knm is not None and torque_at(p) > max_torque_knm:
        lo, hi = 0.0, p
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if torque_at(mid) < max_torque_knm else (lo, mid)
        p = 0.5 * (lo + hi)
        limited_by = "torque"
    f = cutter_forces(p, ucs_mpa, bts_mpa, cutter)
    torque_knm = k * f.rolling_n
    power_kw = torque_knm * 2 * math.pi * rpm / 60
    return TbmPerformance(
        penetration_mm_rev=p,
        rop_m_h=p * rpm * 60 / 1000,
        normal_per_cutter_kn=f.normal_n / 1000,
        rolling_per_cutter_kn=f.rolling_n / 1000,
        cutterhead_torque_knm=torque_knm,
        cutterhead_power_kw=power_kw,
        cutter_overloaded=f.normal_n / 1000 > cutter.max_load_kn,
        limited_by=limited_by,
    )
