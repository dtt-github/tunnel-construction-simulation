"""Precast segmental lining: ring forces (JSCE elastic equation method with Wood's joint reduction), jacking stress and
bursting under the thrust shoes, annulus grout volume and pressure window, ring taper, and a section stress check.

References
- ITA WG2 (2000). Guidelines for the design of shield tunnel lining, TUST 15(3): 303-331,
  https://about.ita-aites.org/publications/wg-publications/download/80_37554c46d738a06a0d79e03e8e7c5f59 :
  Table II-2 (p. 316) member forces of the elastic equation method; Design Example 1 (pp. 323-326) reproduced in the
  tests; jacking stress check (p. 326); allowable stresses 15 MPa for f_ck 42 MPa, x1.65 for the temporary jacking state.
  The triangular lateral load enters with the factor (Q' - Q), which reproduces the example (ITA 2019 Table 6 drops it).
  Formula 2.2.1 (Terzaghi's reduced vertical earth pressure for deep tunnels) and section 2.2 (lateral coefficient
  between the active and the at-rest value).
- ITA WG2 Report 22 (2019). Guidelines for the design of segmental tunnel linings,
  https://about.ita-aites.org/publications/wg-publications/download/1825_470d8f379299b5ad89de378875dd1b8f :
  eq (8) Wood's reduced inertia I_r = I_j + (4/n)^2 I (n > 4); eqs (2)-(3) bursting force (ACI 318, DAUB 2013);
  section 5.2 grout pressure above groundwater and below overburden (AASHTO <= 69 kPa above groundwater);
  eq (1) taper; Table 2 load factors.
- DAUB (2024). Recommendations for the design, production and installation of segmental rings,
  https://www.daub-ita.de/fileadmin/documents/daub/gtcrec2/2024-12_Tuebbingdesign_EN_final_web.pdf : section 5.5
  bedding K_r = E_s / R; p. 12-13 taper with offset joints; Table 3 tolerances; ovalisation below 0.5 % of ID.
Units: m, kN, kPa (kN/m^2), kN/m^3; ring forces per metre of tunnel (b = 1 m) unless stated.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


def wood_inertia(i_full: float, n_segments: int, i_joint: float = 0.0) -> float:
    """Effective ring inertia for n segments (Wood): I_j + (4 / n)^2 I, for n > 4; the full inertia for n <= 4."""
    if n_segments <= 4:
        return i_full
    return i_joint + (4 / n_segments) ** 2 * i_full


def subgrade_modulus(e_soil: float, radius: float) -> float:
    """Radial bedding k (kN/m^3) from the ground stiffness (kPa): K_r = E_s / R (DAUB, ITA 2019 Table 5)."""
    return e_soil / radius


@dataclass(frozen=True)
class RingForces:
    angles_deg: list  # from the crown
    moment: list  # kNm per m
    normal: list  # kN per m (compression positive)
    deflection: float  # horizontal displacement at the springline, m
    reaction: float  # soil reaction at the springline k delta, kPa


def jsce_ring(p_v: float, q_top: float, q_bottom: float, g: float, rc: float, ei: float, k: float,
              angles_deg: list | None = None, eta: float = 1.0, dead_load_in_deflection: bool = False) -> RingForces:
    """Elastic equation method (ITA 2000 Table II-2) for a ring of centroid radius rc under the vertical load p_v at the
    crown (earth + water), lateral loads q_top at the crown level and q_bottom at the invert level (triangular between),
    self weight g (kPa of lining) and a triangular soil reaction over 45-135 degrees with modulus k. eta scales the
    bending rigidity (Wood's factor). By default the springline deflection omits the dead-load term, as the published
    Design Example 1 does."""
    if angles_deg is None:
        angles_deg = list(range(0, 181, 10))
    num = 2 * p_v - q_top - q_bottom + (math.pi * g if dead_load_in_deflection else 0.0)
    delta = num * rc**4 / (24 * (eta * ei + 0.045 * k * rc**4))
    kd = k * delta
    dq = q_bottom - q_top
    ms, ns = [], []
    for a_deg in angles_deg:
        f = math.radians(a_deg)
        s, c = math.sin(f), math.cos(f)
        # uniform vertical, uniform lateral, triangular lateral
        m = (1 - 2 * s * s) * p_v * rc * rc / 4 + (1 - 2 * c * c) * q_top * rc * rc / 4 + (6 - 3 * c - 12 * c * c + 4 * c**3) * dq * rc * rc / 48
        n = s * s * rc * p_v + c * c * rc * q_top + (c + 8 * c * c - 4 * c**3) * dq * rc / 16
        # soil reaction (symmetric about the springline)
        fa = f if f <= math.pi / 2 else math.pi - f
        sa, ca = math.sin(fa), math.cos(fa)
        if fa <= math.pi / 4:
            m += (0.2346 - 0.3536 * ca) * rc * rc * kd
            n += 0.3536 * ca * rc * kd
        else:
            m += (-0.3487 + 0.5 * sa * sa + 0.2357 * ca**3) * rc * rc * kd
            n += (-0.7071 * ca + ca * ca + 0.7071 * sa * sa * ca) * rc * kd
        # dead load
        if f <= math.pi / 2:
            m += (3 * math.pi / 8 - f * s - 5 * c / 6) * rc * rc * g
            n += (f * s - c / 6) * rc * g
        else:
            m += (-math.pi / 8 + (math.pi - f) * s - 5 * c / 6 - 0.5 * math.pi * s * s) * rc * rc * g
            n += (-math.pi * s + f * s + math.pi * s * s - c / 6) * rc * g
        ms.append(m)
        ns.append(n)
    return RingForces(list(angles_deg), ms, ns, delta, kd)


def ring_loads(depth_axis: float, radius: float, gamma: float, k0: float, water_depth: float, gamma_w: float = 10.0,
               surcharge: float = 0.0) -> tuple[float, float, float]:
    """Full-overburden loads on a shallow ring (cover below about two diameters): vertical earth + water at the crown,
    lateral = k0 times the effective vertical stress plus water, at crown and invert levels (kPa)."""
    def at(z: float) -> tuple[float, float]:
        hw = min(max(water_depth, 0.0), z)
        sv_total = surcharge + gamma * z
        u = gamma_w * max(z - hw, 0.0)
        return sv_total, u
    zc, zi = depth_axis - radius, depth_axis + radius
    svc, uc = at(zc)
    svi, ui = at(zi)
    p_v = svc
    return p_v, k0 * (svc - uc) + uc, k0 * (svi - ui) + ui


def terzaghi_loads(depth_axis: float, radius: float, gamma: float, phi_deg: float, c: float, lam: float, water_depth: float,
                   gamma_w: float = 10.0, surcharge: float = 0.0) -> tuple[float, float, float]:
    """Loads on a ring (kPa) with the vertical earth pressure reduced by Terzaghi's formula (ITA WG2 2000, Formula 2.2.1):
    h0 = B1 (1 - c / (B1 g)) (1 - exp(-tan(phi) H / B1)) / tan(phi) + P0 exp(-tan(phi) H / B1) / g,
    B1 = R0 cot(pi/8 + phi/4), with K = 1 in the formula and g the effective unit weight above the crown. For shallow
    cover it tends to the full overburden. Lateral earth pressure = lam x the vertical effective pressure, varying
    linearly from crown to invert (ITA 2000 section 2.2: lam between the active and the at-rest coefficient); water
    pressure hydrostatic. Returns (vertical at the crown, lateral at the crown, lateral at the invert), total."""
    h = depth_axis - radius
    hw = min(max(water_depth, 0.0), h)
    g = (gamma * hw + (gamma - gamma_w) * (h - hw)) / h  # effective unit weight above the crown
    t = math.tan(math.radians(phi_deg))
    b1 = radius / math.tan(math.pi / 8 + math.radians(phi_deg) / 4)
    e = math.exp(-t * h / b1)
    h0 = min(b1 * (1 - c / (b1 * g)) * (1 - e) / t + surcharge * e / g, h + surcharge / g)
    pe = g * max(h0, 0.0)
    u_top = gamma_w * max(h - water_depth, 0.0)
    u_bot = gamma_w * max(h + 2 * radius - water_depth, 0.0)
    g_below = gamma - gamma_w if water_depth <= h else gamma
    return pe + u_top, lam * pe + u_top, lam * (pe + g_below * 2 * radius) + u_bot


def active_coefficient(phi_deg: float) -> float:
    return math.tan(math.radians(45 - phi_deg / 2)) ** 2


def section_stresses(n: float, m: float, thickness: float, width: float = 1.0) -> tuple[float, float]:
    """Extreme-fibre stresses (kPa, compression positive) of an uncracked rectangular section: N/A +- M/W."""
    a = width * thickness
    w = width * thickness**2 / 6
    return n / a + abs(m) / w, n / a - abs(m) / w


# --------------------------------------------------------------------------- jacking, bursting

ITA2000_ALLOWABLE = {"concrete_42": 15_000.0, "jacking_factor": 1.65}  # kPa


def jacking_stress(jack_force: float, n_shoes: int, rc: float, thickness: float, gap: float = 0.1, eccentricity: float = 0.01) -> float:
    """Compressive stress (kPa) in the ring under one shoe (ITA 2000 p. 326): the force spread over the ring sector of
    one shoe, B = 2 pi rc / n - gap, plus the bending from the eccentricity: P/A + P e (t/2) / I."""
    b = 2 * math.pi * rc / n_shoes - gap
    a = b * thickness
    i = b * thickness**3 / 12
    return jack_force / a + jack_force * eccentricity * (thickness / 2) / i


def bursting_force(force: float, thickness: float, pad: float, edge: float = 0.03, method: str = "daub") -> tuple[float, float]:
    """Splitting (bursting) tension under a thrust shoe of height `pad` on a segment `thickness` thick (ITA 2019 eqs
    2-3): ACI 318 T = 0.25 P (1 - pad / h) at 0.5 (h - 2e); DAUB T = 0.25 P (1 - pad / (h - 2e)) at 0.4 (h - 2e).
    Returns (force, depth of its centroid from the loaded face)."""
    if method == "aci":
        return 0.25 * force * (1 - pad / thickness), 0.5 * (thickness - 2 * edge)
    return 0.25 * force * (1 - pad / (thickness - 2 * edge)), 0.4 * (thickness - 2 * edge)


# --------------------------------------------------------------------------- grout and geometry


def annulus_volume(d_excavated: float, d_ring_outer: float, ring_width: float) -> float:
    """Annular gap volume per ring (m^3)."""
    return math.pi / 4 * (d_excavated**2 - d_ring_outer**2) * ring_width


def grout_window(depth_crown: float, gamma: float, water_depth: float, gamma_w: float = 10.0, max_over_water: float = 69.0) -> tuple[float, float]:
    """Grout pressure window at the crown (kPa): at least the groundwater pressure, at most the smaller of the total
    overburden and the groundwater pressure plus `max_over_water` (AASHTO 69 kPa; South-East Asian practice up to 150)."""
    hw = min(max(water_depth, 0.0), depth_crown)
    u = gamma_w * max(depth_crown - hw, 0.0)
    return u, min(gamma * depth_crown, u + max_over_water)


def taper(d_outer: float, ring_width: float, curve_radius: float, offset_deg: float | None = None) -> float:
    """Total taper (m) of a universal ring to follow a curve: D lm / R, times 2 / (1 + cos alpha) with offset
    longitudinal joints (DAUB 2024 p. 12-13)."""
    k = d_outer * ring_width / curve_radius
    if offset_deg is not None:
        k *= 2 / (1 + math.cos(math.radians(offset_deg)))
    return k
