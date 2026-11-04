"""Shield thrust and cutterhead torque as sums of components (soft-ground shields, EPB and slurry).

References
- Shi, H., Yang, H., Gong, G., Wang, L. (2011). Determination of the cutterhead torque for EPB shield tunneling machine.
  Automation in Construction 20(8), 1087-1095, doi:10.1016/j.autcon.2011.04.010. (Torque = cutting tools + front-face
  friction + rim friction + back-face friction + mixing arms + seals; opening ratio and earth pressure dominate.)
- Krause, T. (1987). Schildvortrieb mit flüssigkeits- und erdgestützter Ortsbrust. Dissertation, TU Braunschweig.
  (Empirical installed torque M = alpha D^3, used here only as a sanity band.)

Thrust (kN):
    F_face   = p_axis * pi D^2 / 4                       chamber (support) pressure on the bulkhead and cutterhead
    F_shield = mu_s * (contact * pi D L sigma_n + W_shield)       skin friction; sigma_n = sigma_v,axis (1 + K0) / 2
    F_tools, F_tail_seal: given (tool contact forces, tail-seal friction)
    F_backup = mu_b * W_backup                           drag of the backup train
Torque (kNm), cutterhead radius R, opening ratio xi:
    T_face  = 2/3 pi mu p (1 - xi) R^3                   front face against the ground at the support pressure
    T_back  = 2/3 pi mu_c p (1 - xi) R^3                 back face against the chamber paste
    T_rim   = 2 pi R^2 B mu_r sigma_n                    rim (width B) against the ground
    T_arms  = n mu_c p A r_arm                           mixing arms of area A at radius r_arm
    T_tools = n F_t r_mean ,  r_mean = f R               scrapers/rippers (f = 0.5 for uniform radial spacing);
                                                         for disc cutters use csm.tbm_performance instead
    T_seals: given

sigma_v is the effective vertical stress at the axis by default (friction on effective contact stress), with the
water table splitting dry and submerged unit weights. The friction coefficients are illustrative defaults:
steel on natural ground about 0.2-0.4 (shield, rim), lower for conditioned soil at the face and in the chamber
(conditioning reduces torque, Shi et al. 2011); calibrate them per project.

Units: m, kPa, kN, kNm.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

GAMMA_W = 10.0

# Empirical sanity bands, ranges vary by source and are not checked against the originals:
# installed torque alpha D^3 and thrust beta D^2.
KRAUSE_ALPHA = (9.0, 23.0)  # kNm/m^3
THRUST_BETA = (500.0, 1200.0)  # kN/m^2


def vertical_stress(depth: float, gamma: float, *, gamma_sub: float | None = None, water_depth: float = math.inf,
                    q: float = 0.0, effective: bool = True) -> float:
    """Vertical stress at `depth` (kPa); effective by default, total if effective=False."""
    gsub = gamma - GAMMA_W if gamma_sub is None else gamma_sub
    hw = min(max(water_depth, 0.0), depth)
    sv = q + gamma * hw + gsub * (depth - hw)
    return sv if effective else sv + GAMMA_W * (depth - hw)


@dataclass(frozen=True)
class Thrust:
    face: float
    shield: float
    tools: float
    tail_seal: float
    backup: float

    @property
    def total(self) -> float:
        return self.face + self.shield + self.tools + self.tail_seal + self.backup


def shield_thrust(diameter: float, shield_length: float, axis_depth: float, gamma: float, p_axis: float, *,
                  gamma_sub: float | None = None, water_depth: float = math.inf, q: float = 0.0, k0: float = 0.5,
                  mu_shield: float = 0.3, contact: float = 1.0, shield_weight: float = 0.0, tools: float = 0.0,
                  tail_seal: float = 0.0, backup_weight: float = 0.0, mu_backup: float = 0.1) -> Thrust:
    """Thrust components (kN). p_axis: support pressure at the axis (kPa); weights in kN."""
    if diameter <= 0 or shield_length <= 0 or axis_depth <= diameter / 2:
        raise ValueError("need positive sizes and the axis deeper than the radius")
    sv = vertical_stress(axis_depth, gamma, gamma_sub=gamma_sub, water_depth=water_depth, q=q)
    sigma_n = sv * (1 + k0) / 2
    return Thrust(
        face=p_axis * math.pi * diameter**2 / 4,
        shield=mu_shield * (contact * math.pi * diameter * shield_length * sigma_n + shield_weight),
        tools=tools,
        tail_seal=tail_seal,
        backup=mu_backup * backup_weight,
    )


@dataclass(frozen=True)
class Torque:
    tools: float
    face: float
    rim: float
    back: float
    arms: float
    seals: float

    @property
    def total(self) -> float:
        return self.tools + self.face + self.rim + self.back + self.arms + self.seals


def tool_torque(n_tools: int, tangential_force: float, radius: float, radius_factor: float = 0.5) -> float:
    """Torque of n scrapers/rippers with tangential force F_t (kN) at mean radius f R (kNm)."""
    return n_tools * tangential_force * radius_factor * radius


def cutterhead_torque(diameter: float, p_axis: float, sigma_n: float, *, opening_ratio: float = 0.3,
                      mu: float = 0.15, mu_rim: float = 0.3, mu_chamber: float = 0.1, rim_width: float = 0.5, n_arms: int = 0,
                      arm_area: float = 0.0, arm_radius: float = 0.0, tools: float = 0.0,
                      seals: float = 0.0) -> Torque:
    """Cutterhead torque components (kNm). sigma_n: radial ground stress on the rim (kPa); arm_area in m^2."""
    if not 0 <= opening_ratio < 1:
        raise ValueError("opening ratio must be in [0, 1)")
    r = diameter / 2
    disc = 2 / 3 * math.pi * (1 - opening_ratio) * r**3 * p_axis
    return Torque(
        tools=tools,
        face=mu * disc,
        rim=2 * math.pi * r * r * rim_width * mu_rim * sigma_n,
        back=mu_chamber * disc,
        arms=n_arms * mu_chamber * p_axis * arm_area * arm_radius,
        seals=seals,
    )


def sanity_bands(diameter: float) -> dict[str, tuple[float, float]]:
    """Empirical installed-torque (kNm) and thrust (kN) bands for this diameter."""
    d = diameter
    return {"torque": (KRAUSE_ALPHA[0] * d**3, KRAUSE_ALPHA[1] * d**3),
            "thrust": (THRUST_BETA[0] * d**2, THRUST_BETA[1] * d**2)}
