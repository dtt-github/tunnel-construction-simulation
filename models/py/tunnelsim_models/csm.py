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
C ~= 2.12 (dimensionless), psi in [-0.2, 0.2] (pressure-distribution exponent). Default psi = -0.1: with the spacing
taken as cutterhead radius / number of cutters (Bruland's average spacing), it reproduces the 4.5 km weighted mean of
Follo Line TBM1 (9.96 m double shield, 71 x 19" discs, gneiss UCS 152 MPa, BTS 10.4 MPa, 5.08 rpm, net thrust
21217 - 3200 kN shield drag): 6.36 against 6.32 mm/rev measured. Hansen (2018), NTNU MSc, Tables 2.4 and 5.1,
https://hdl.handle.net/11250/2503069. With psi = 0.1 the model gave 11.8 mm/rev there (1.9x).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

C_DEFAULT = 2.12

# Gauge-cutter linear speed limits (m/min) by disc diameter, Rostami & Chang (2017), Engineering 3(6) 892-904,
# doi:10.1016/j.eng.2017.12.009: rpm_max = V_L / (pi D).
GAUGE_SPEED_LIMIT_M_MIN = {432: 165.0, 483: 200.0}
# Brief maximum penetration before the muck conveyor overloads: 15-20 mm/rev (Macias & Barton 2022, Bergmekanikkdagen,
# https://www.rmteceng.com/wp-content/uploads/2024/01/MaciasandBarton_2022_Bergmekanikkdag.pdf). The lower bound is used.
PRACTICAL_MAX_PENETRATION_MM = 15.0


def max_rpm(head_diameter_m: float, cutter_diameter_mm: float = 482.6) -> float:
    """Cutterhead speed limit from the gauge-cutter linear speed (17-inch: 165 m/min; 19-inch and larger: 200 m/min)."""
    v = GAUGE_SPEED_LIMIT_M_MIN[432] if cutter_diameter_mm <= 440 else GAUGE_SPEED_LIMIT_M_MIN[483]
    return v / (math.pi * head_diameter_m)


@dataclass(frozen=True)
class Cutter:
    diameter_mm: float = 482.6  # 19-inch disc
    tip_width_mm: float = 19.0
    spacing_mm: float = 85.0
    psi: float = -0.1  # back-analysed on Follo TBM1 (see module docstring)
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
    limited_by: str  # "thrust", "penetration", "torque" or "power"
    thrust_used_kn: float  # thrust the cutters actually carry at this penetration (excess thrust above a limit is not used)
    torque_available_knm: float | None  # drive limit at this speed: min(installed torque, power / angular speed)


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
    max_power_kw: float | None = None,
    max_penetration_mm: float | None = None,
) -> TbmPerformance:
    """Steady-state penetration, ROP, torque and power for a given cutting thrust.

    thrust_kn is the net thrust reaching the cutters (total jack force minus shield friction,
    backup drag etc.). Torque uses the Rostami-Ozdemir approximation T = k * D * N * Fr with k ~= 0.3.
    If max_torque_knm is given and the thrust-limited penetration would exceed it (typical in weak
    rock), penetration is reduced until torque equals the installed limit.

    Drive characteristic: the available torque is the installed torque up to the speed where torque x speed reaches
    the installed power, and power / angular speed above it (constant-torque then constant-power drive).
    max_penetration_mm caps penetration per revolution (muck handling and block loading in practice); the thrust
    above what that penetration needs is reported as unused (thrust_used_kn < thrust_kn).
    """
    k = torque_radius_factor * head_diameter_m * n_cutters / 1000

    def torque_at(pen: float) -> float:
        return k * cutter_forces(pen, ucs_mpa, bts_mpa, cutter).rolling_n

    t_avail = max_torque_knm
    by_power = False
    if max_power_kw is not None and rpm > 0:
        t_power = max_power_kw * 60 / (2 * math.pi * rpm)
        if t_avail is None or t_power < t_avail:
            t_avail, by_power = t_power, True

    fn = thrust_kn * 1000 / n_cutters
    p = penetration_for_normal_force(fn, ucs_mpa, bts_mpa, cutter)
    limited_by = "thrust"
    if max_penetration_mm is not None and p > max_penetration_mm:
        p, limited_by = max_penetration_mm, "penetration"
    if t_avail is not None and torque_at(p) > t_avail:
        lo, hi = 0.0, p
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if torque_at(mid) < t_avail else (lo, mid)
        p = 0.5 * (lo + hi)
        limited_by = "power" if by_power else "torque"
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
        thrust_used_kn=f.normal_n * n_cutters / 1000,
        torque_available_knm=t_avail,
    )
