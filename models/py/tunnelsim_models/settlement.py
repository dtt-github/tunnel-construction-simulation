"""Greenfield surface settlement above a tunnel (empirical Gaussian trough).

References
- Peck, R.B. (1969). Deep excavations and tunnelling in soft ground. Proc. 7th ICSMFE, Mexico, State-of-the-art vol., 225-290.
- O'Reilly, M.P., New, B.M. (1982). Settlements above tunnels in the United Kingdom - their magnitude and prediction.
  Tunnelling '82, IMM, London, 173-181.
- Mair, R.J., Taylor, R.N., Bracegirdle, A. (1993). Subsurface settlement profiles above tunnels in clays. Geotechnique 43(2).
- Burland, J.B. (1995). Assessment of risk of damage to buildings due to tunnelling and excavation. Proc. 1st IC Earthquake Geotech. Eng.

    i      = K * z0                       trough width (inflection point)
    V_s    = VL * pi * D^2 / 4            settlement volume per metre of tunnel (m^3/m)
    S_max  = V_s / (sqrt(2 pi) * i)
    S(x)   = S_max * exp(-x^2 / (2 i^2))
    u(x)   = -(x / z0) * S(x)             horizontal displacement (radial-flow assumption, O'Reilly & New)
    Longitudinal: S(x, y) = S(x) * Phi(-(y - y_face) / i)   (Attewell & Woodman 1982 cumulative-normal)

Units: metres; VL as a fraction (0.01 = 1 %). Settlement positive downward.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Typical trough-width parameter K (O'Reilly & New 1982; Mair & Taylor 1997)
K_TYPICAL = {"stiff_clay": 0.5, "soft_clay": 0.6, "sand_gravel": 0.35}

# Burland (1995) damage categories by limiting tensile strain (%)
BURLAND_CATEGORIES = [
    (0.05, 0, "Negligible"),
    (0.075, 1, "Very slight"),
    (0.15, 2, "Slight"),
    (0.3, 3, "Moderate"),
    (float("inf"), 4, "Severe to very severe"),
]


@dataclass(frozen=True)
class Trough:
    i: float
    volume_m3_per_m: float
    s_max: float
    z0: float

    def settlement(self, x: float) -> float:
        return self.s_max * math.exp(-(x * x) / (2 * self.i * self.i))

    def horizontal(self, x: float) -> float:
        return -(x / self.z0) * self.settlement(x)

    def slope(self, x: float) -> float:
        return -(x / (self.i * self.i)) * self.settlement(x)

    def settlement_3d(self, x: float, y_behind_face: float) -> float:
        """y_behind_face > 0 means the point is behind (already passed by) the face."""
        return self.settlement(x) * 0.5 * (1 + math.erf(y_behind_face / (self.i * math.sqrt(2))))


def gaussian_trough(diameter_m: float, axis_depth_m: float, volume_loss: float, k: float = 0.5) -> Trough:
    if axis_depth_m <= diameter_m / 2:
        raise ValueError("axis depth must exceed the tunnel radius")
    i = k * axis_depth_m
    vs = volume_loss * math.pi * diameter_m**2 / 4
    return Trough(i=i, volume_m3_per_m=vs, s_max=vs / (math.sqrt(2 * math.pi) * i), z0=axis_depth_m)


def burland_category(tensile_strain_percent: float) -> tuple[int, str]:
    for limit, cat, name in BURLAND_CATEGORIES:
        if tensile_strain_percent < limit:
            return cat, name
    raise AssertionError("unreachable")
