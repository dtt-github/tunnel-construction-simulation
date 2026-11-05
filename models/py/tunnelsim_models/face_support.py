"""Face support pressure for closed-face shields: wedge-silo limit equilibrium and the DAUB operating window.

References
- Horn, N. (1961). Horizontaler Erddruck auf senkrechte Abschlussflächen von Tunnelröhren. Landeskonferenz der
  Ungarischen Tiefbauindustrie, 7-16. (Wedge-prism mechanism.)
- Janssen, H.A. (1895). Versuche über Getreidedruck in Silozellen. Z. Verein Deutscher Ingenieure 39, 1045-1049.
  Terzaghi, K. (1943). Theoretical Soil Mechanics. Wiley. (Silo / arching vertical stress.)
- Anagnostou, G., Kovári, K. (1994). The face stability of slurry-shield-driven tunnels. Tunnelling and Underground
  Space Technology 9(2), 165-174, doi:10.1016/0886-7798(94)90028-0. (Wedge loaded by a silo, K = 0.8 in the silo.)
- Vermeer, P.A., Ruse, N., Marcher, T. (2002). Tunnel heading stability in drained ground. Felsbau 20(6), 8-18.
  (Cohesionless limit pressure p_f = gamma D N_gamma, N_gamma = 1/(9 tan phi) - 0.05, for cover > D.)
- DAUB / ITA-AITES WG14 (2016). Recommendations for face support pressure calculations for shield tunnelling in soft
  ground. (Minimum support from factored earth and water pressure; maximum against blow-out.)

Mechanism (x into the ground, z up, face of width B and height H, crown at depth C below the surface):
the wedge has a vertical face, a slip plane at angle theta to the horizontal and length L = H / tan(theta) at the
crown. A prism of cross-section B x L above it carries the silo stress sigma_v(C) onto the wedge.

    sigma_v(z)  = (r g - c) / (K tan phi) * (1 - exp(-K tan phi z / r)) + q exp(-K tan phi z / r),   r = B L / (2 (B + L))
    G = B H L g_w / 2,   V = sigma_v(C) B L,   A_s = B H / sin(theta)
    T (each side triangle) = c H L / 2 + tan(phi) K_w L (sigma_v(C) H / 2 + g_w H^2 / 6)
    S(theta) = [(G + V)(sin theta - cos theta tan phi) - c A_s - 2 T] / (cos theta + sin theta tan phi)

The required effective support force is max over theta of S; s' = S / (B H) is its mean over the face. The circular
face is replaced by a square of the same area, B = H = D sqrt(pi) / 2. Water is hydrostatic (no seepage: a perfect
filter cake or a chamber head equal to the ground-water head); seepage forces are not modelled yet.

Units: m, kPa, kN/m^3, degrees for angles.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

GAMMA_W = 10.0  # kN/m^3

# DAUB (2016) partial factors on the earth and water parts of the minimum support pressure, and the fraction of the
# crown overburden allowed as maximum. Common defaults; not checked against the document here, so verify per project.
DAUB_DEFAULTS = {"eta_earth": 1.5, "eta_water": 1.05, "max_fraction_of_overburden": 0.9}


def silo_stress(depth: float, width: float, length: float, gamma: float, c: float, phi_deg: float, k: float = 0.8,
                q: float = 0.0) -> float:
    """Janssen/Terzaghi vertical stress at `depth` in a prism of plan B x L (kPa), never below zero."""
    if depth <= 0:
        return max(q, 0.0)
    r = width * length / (2 * (width + length))
    kt = k * math.tan(math.radians(phi_deg))
    if kt < 1e-12:
        return max(q + (gamma - c / r) * depth, 0.0)
    e = math.exp(-kt * depth / r)
    return max((r * gamma - c) / kt * (1 - e) + q * e, 0.0)


@dataclass(frozen=True)
class FaceSupport:
    s_eff: float  # required mean effective support over the face, kPa (negative: self-supporting)
    theta_deg: float  # critical slip-plane angle to the horizontal
    wedge_length: float  # L at the crown, m
    silo_stress: float  # sigma_v on top of the wedge, kPa
    u_crown: float  # pore pressure at the crown, kPa
    u_axis: float  # pore pressure at the axis, kPa
    side: float  # side of the equivalent square face, m


def _layered_silo(cover, b, length, gamma, gamma_sub, c, phi, k, q, water_depth):
    """Silo stress at the crown with dry soil above the water table and submerged soil below it."""
    hw = min(max(water_depth, 0.0), cover)
    s = silo_stress(hw, b, length, gamma, c, phi, k, q)
    return silo_stress(cover - hw, b, length, gamma_sub, c, phi, k, s)


def wedge_silo(diameter: float, cover: float, gamma: float, phi_deg: float, c: float = 0.0, *,
               gamma_sub: float | None = None, water_depth: float = math.inf, q: float = 0.0, k_silo: float = 0.8,
               k_wedge: float | None = None) -> FaceSupport:
    """Required effective face support (wedge-silo). cover = depth of the crown; water_depth = water table depth.

    gamma: unit weight above the water table; gamma_sub: submerged unit weight below it (default gamma - 10).
    k_wedge: earth pressure coefficient on the wedge sides (default 1 - sin phi).
    """
    if diameter <= 0 or cover <= 0:
        raise ValueError("diameter and cover must be positive")
    if not 0 <= phi_deg < 90:
        raise ValueError("phi must be in [0, 90) degrees")
    gsub = gamma - GAMMA_W if gamma_sub is None else gamma_sub
    kw = 1 - math.sin(math.radians(phi_deg)) if k_wedge is None else k_wedge
    b = h = diameter * math.sqrt(math.pi) / 2
    g_wedge = gsub if water_depth <= cover + h / 2 else gamma
    tp = math.tan(math.radians(phi_deg))

    def support(theta_deg):
        th = math.radians(theta_deg)
        length = h / math.tan(th)
        sv = _layered_silo(cover, b, length, gamma, gsub, c, phi_deg, k_silo, q, water_depth)
        g = b * h * length * g_wedge / 2
        v = sv * b * length
        t = c * h * length / 2 + tp * kw * length * (sv * h / 2 + g_wedge * h * h / 6)
        a_s = b * h / math.sin(th)
        s = ((g + v) * (math.sin(th) - math.cos(th) * tp) - c * a_s - 2 * t) / (math.cos(th) + math.sin(th) * tp)
        return s, length, sv

    # grid search then golden-section refinement (deterministic, so the JS twin gives the same result)
    best = max((support(a)[0], a) for a in (1 + 0.5 * i for i in range(177)))[1]
    lo, hi = max(best - 0.5, 0.5), min(best + 0.5, 89.5)
    gr = (math.sqrt(5) - 1) / 2
    for _ in range(60):
        a1, a2 = hi - gr * (hi - lo), lo + gr * (hi - lo)
        if support(a1)[0] < support(a2)[0]:
            lo = a1
        else:
            hi = a2
    theta = (lo + hi) / 2
    s, length, sv = support(theta)
    u_crown = GAMMA_W * max(cover - water_depth, 0.0)
    u_axis = GAMMA_W * max(cover + diameter / 2 - water_depth, 0.0)
    return FaceSupport(s_eff=s / (b * h), theta_deg=theta, wedge_length=length, silo_stress=sv, u_crown=u_crown,
                       u_axis=u_axis, side=b)


def vermeer_limit(diameter: float, gamma: float, phi_deg: float) -> float:
    """Vermeer et al. (2002) limit support pressure for cohesionless drained ground, cover > D (kPa)."""
    if not 20 <= phi_deg <= 45:
        raise ValueError("fit valid for phi between 20 and 45 degrees")
    return gamma * diameter * (1 / (9 * math.tan(math.radians(phi_deg))) - 0.05)


@dataclass(frozen=True)
class SupportWindow:
    p_min_axis: float  # kPa
    p_max_axis: float
    p_min_crown: float
    p_max_crown: float
    overburden_crown: float  # total vertical stress at the crown, kPa

    @property
    def feasible(self) -> bool:
        return self.p_min_crown <= self.p_max_crown


def daub_window(fs: FaceSupport, diameter: float, cover: float, gamma: float, *, gamma_sub: float | None = None,
                water_depth: float = math.inf, q: float = 0.0, support_unit_weight: float = 12.0,
                eta_earth: float = DAUB_DEFAULTS["eta_earth"], eta_water: float = DAUB_DEFAULTS["eta_water"],
                max_fraction: float = DAUB_DEFAULTS["max_fraction_of_overburden"]) -> SupportWindow:
    """Operating window for the support pressure (DAUB 2016 structure, factors as parameters).

    p_min = eta_earth * max(s', 0) + eta_water * u, taken at the axis; p_max = max_fraction * total overburden at the
    crown. The support medium (EPB paste ~12 kN/m^3, bentonite slurry ~11) sets the gradient from crown to axis.
    A negative water_depth means free water above the ground surface (river bed); it raises u and the total overburden.
    """
    gsub = gamma - GAMMA_W if gamma_sub is None else gamma_sub
    hw = min(max(water_depth, 0.0), cover)
    # a negative water depth is free water above the ground (a river): its weight adds to the total overburden
    sigma_crown = q + gamma * hw + (gsub + GAMMA_W) * (cover - hw) + GAMMA_W * max(-water_depth, 0.0)
    dz = diameter / 2 * support_unit_weight
    p_min_axis = eta_earth * max(fs.s_eff, 0.0) + eta_water * fs.u_axis
    p_max_crown = max_fraction * sigma_crown
    return SupportWindow(p_min_axis=p_min_axis, p_max_axis=p_max_crown + dz, p_min_crown=max(p_min_axis - dz, 0.0),
                         p_max_crown=p_max_crown, overburden_crown=sigma_crown)
