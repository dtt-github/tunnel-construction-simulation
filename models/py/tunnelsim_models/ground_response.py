"""Ground response around a circular tunnel: convergence-confinement, squeezing, shield thrust and gripper bearing.

References
- Hoek, E. Practical Rock Engineering, ch. "Tunnels in weak rock" (rocscience.com), eqs 1-8 and Fig. 8: the Duncan Fama
  (1993) ground reaction curve for an elastic-perfectly plastic Mohr-Coulomb rock mass, and maximum support pressures.
- Hoek, E., Carranza-Torres, C., Corkum, B. (2002). Hoek-Brown failure criterion - 2002 edition. Proc. NARMS-TAC,
  267-273, eqs 12-18: equivalent Mohr-Coulomb parameters, and sigma'3max for tunnels.
- Vlachopoulos, N., Diederichs, M.S. (2009). Improved longitudinal displacement profiles for convergence-confinement
  analysis of deep tunnels. RMRE 42, 131-146, doi:10.1007/s00603-009-0176-4; as given in Hoek et al. (2008), Kersten
  Lecture, Appendix 1 (eqs A1.5-A1.7).
- Hoek, E., Marinos, P. (2000). Predicting tunnel squeezing problems in weak heterogeneous rock masses. Tunnels and
  Tunnelling International, eqs 3-4 and Fig. 7 (strain classes A-E).
- Ramoni, M., Anagnostou, G. (2010). Thrust force requirements for TBMs in squeezing ground. TUST 25(4), 433-455,
  doi:10.1016/j.tust.2010.02.008; and VSS report 1341 (2011): F_f = mu 2 pi R L p_s, skin friction coefficients,
  gripper force 2.0-3.5 x installed thrust.

Ground reaction curve (hydrostatic p0, circular tunnel radius r0, support as uniform internal pressure pi):
    sigma_cm = 2 c cos(phi) / (1 - sin(phi)),  k = (1 + sin(phi)) / (1 - sin(phi)),  p_cr = (2 p0 - sigma_cm) / (1 + k)
    pi > p_cr: u = r0 (1 + nu) (p0 - pi) / E
    pi < p_cr: r_p = r0 [2 (p0 (k - 1) + sigma_cm) / ((1 + k) ((k - 1) pi + sigma_cm))]^(1 / (k - 1))
               u   = r0 (1 + nu) / E [2 (1 - nu) (p0 - p_cr) (r_p / r0)^2 - (1 - 2 nu) (p0 - pi)]
Longitudinal displacement profile (x behind the face, R* = r_p / r0 for the unsupported tunnel):
    u0/umax = exp(-0.15 R*) / 3;  x < 0: u/umax = u0/umax exp(x / r0);  x >= 0: 1 - (1 - u0/umax) exp(-1.5 x / (r0 R*))
Squeezing strain (Hoek & Marinos 2000): eps(%) = (0.2 - 0.25 pi/p0) (sigma_cm/p0)^(2.4 pi/p0 - 2).

Shield thrust in squeezing ground (screening estimate; Ramoni & Anagnostou give nomograms from axisymmetric
analyses): the ground contacts the shield where its free closure since the face, u(x) - u(0), exceeds the radial gap
(overcut); there it presses with the ground-reaction pressure that holds the wall at the gap, measured from the
excavated radius (a stiff shield right behind the face suppresses most of the pre-convergence). Against Ramoni &
Anagnostou's worked example (D 10 m, sigma0 10 MPa, E 1 GPa, f_c 3 MPa, phi 25 deg, L 10 m) the normalised thrust
F_f / (mu 2 pi R L sigma0) is 0.23 / 0.04 / 0 for overcuts of 5 / 10 / 15 cm, against 0.26 / 0.08 / 0: it can
under-predict by up to about 2x and is not a design method.

Units: m, MPa, MN (stresses and pressures in MPa, forces in MN).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .hoek_brown import hoek_brown


# --------------------------------------------------------------------------- rock mass

@dataclass(frozen=True)
class RockMass:
    phi_deg: float  # equivalent Mohr-Coulomb friction angle
    c: float  # equivalent cohesion, MPa
    sigma_cm: float  # global rock-mass strength (Hoek et al. 2002 eq 17), MPa
    e_rm: float  # rock-mass modulus, MPa
    sigma3_max: float  # upper limit of the confining stress range used for the fit, MPa


def equivalent_mohr_coulomb(gsi: float, mi: float, sigma_ci: float, e_i: float, p0: float, d: float = 0.0) -> RockMass:
    """Hoek et al. (2002) equivalent Mohr-Coulomb parameters for a deep tunnel with in-situ stress p0 (MPa).

    p0 stands for gamma H; use the larger horizontal stress where it exceeds the vertical.
    """
    hb = hoek_brown(gsi, mi, sigma_ci, d, e_i)
    s3max = 0.47 * hb.sigma_cm * (hb.sigma_cm / p0) ** -0.94
    s3n = s3max / sigma_ci
    mb, s, a = hb.mb, hb.s, hb.a
    t = 6 * a * mb * (s + mb * s3n) ** (a - 1)
    phi = math.degrees(math.asin(t / (2 * (1 + a) * (2 + a) + t)))
    c = sigma_ci * ((1 + 2 * a) * s + (1 - a) * mb * s3n) * (s + mb * s3n) ** (a - 1) / ((1 + a) * (2 + a) * math.sqrt(1 + t / ((1 + a) * (2 + a))))
    return RockMass(phi_deg=phi, c=c, sigma_cm=hb.sigma_cm, e_rm=hb.e_rm, sigma3_max=s3max)


# --------------------------------------------------------------------------- ground reaction curve

@dataclass(frozen=True)
class GroundReaction:
    u: float  # radial wall displacement, m
    r_p: float  # plastic zone radius, m (r0 if elastic)
    p_cr: float  # critical support pressure, MPa
    strain_percent: float  # 100 u / r0


def mc_strength(phi_deg: float, c: float) -> tuple[float, float]:
    """(sigma_cm, k) of a Mohr-Coulomb material: uniaxial strength and passive slope."""
    sp = math.sin(math.radians(phi_deg))
    return 2 * c * math.cos(math.radians(phi_deg)) / (1 - sp), (1 + sp) / (1 - sp)


def ground_reaction(p0: float, pi: float, r0: float, e: float, nu: float, phi_deg: float, c: float) -> GroundReaction:
    """Duncan Fama (1993) wall displacement at support pressure pi (Hoek, Tunnels in weak rock, eqs 1-7)."""
    if not 0 <= pi <= p0:
        raise ValueError("support pressure must be between 0 and p0")
    scm, k = mc_strength(phi_deg, c)
    p_cr = (2 * p0 - scm) / (1 + k)
    if pi >= p_cr:
        u, rp = r0 * (1 + nu) * (p0 - pi) / e, r0
    else:
        rp = r0 * (2 * (p0 * (k - 1) + scm) / ((1 + k) * ((k - 1) * pi + scm))) ** (1 / (k - 1))
        u = r0 * (1 + nu) / e * (2 * (1 - nu) * (p0 - p_cr) * (rp / r0) ** 2 - (1 - 2 * nu) * (p0 - pi))
    return GroundReaction(u=u, r_p=rp, p_cr=max(p_cr, 0.0), strain_percent=100 * u / r0)


def pressure_for_displacement(u: float, p0: float, r0: float, e: float, nu: float, phi_deg: float, c: float) -> float:
    """Inverse of the ground reaction curve: support pressure (MPa) that holds the wall at displacement u (m)."""
    if u <= 0:
        return p0
    if ground_reaction(p0, 0.0, r0, e, nu, phi_deg, c).u <= u:
        return 0.0
    lo, hi = 0.0, p0  # displacement falls as pressure rises
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if ground_reaction(p0, mid, r0, e, nu, phi_deg, c).u > u:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def ldp(x: float, r0: float, r_p: float) -> float:
    """Vlachopoulos & Diederichs (2009): closure at distance x behind the face (x < 0 ahead) as a fraction of the final."""
    rstar = max(r_p / r0, 1.0)
    u0 = math.exp(-0.15 * rstar) / 3
    xs = x / r0
    return u0 * math.exp(xs) if xs < 0 else 1 - (1 - u0) * math.exp(-1.5 * xs / rstar)


# --------------------------------------------------------------------------- squeezing

SQUEEZING_CLASSES = (
    (1.0, "A", "Few support problems", "rock bolts and shotcrete"),
    (2.5, "B", "Minor squeezing", "bolts and shotcrete, sometimes light steel sets or lattice girders"),
    (5.0, "C", "Severe squeezing", "rapid installation, heavy steel sets embedded in shotcrete"),
    (10.0, "D", "Very severe squeezing, face stability problems", "forepoling and face reinforcement, steel sets in shotcrete"),
    (math.inf, "E", "Extreme squeezing", "forepoling, face reinforcement, yielding support"),
)


def squeezing_strain(sigma_cm: float, p0: float, pi: float = 0.0) -> float:
    """Hoek & Marinos (2000) eq 4: tunnel strain in percent (100 x closure / diameter)."""
    return (0.2 - 0.25 * pi / p0) * (sigma_cm / p0) ** (2.4 * pi / p0 - 2)


def squeezing_class(strain_percent: float) -> tuple[str, str, str]:
    for limit, cls, problems, support in SQUEEZING_CLASSES:
        if strain_percent < limit:
            return cls, problems, support
    raise AssertionError("unreachable")


# --------------------------------------------------------------------------- support

@dataclass(frozen=True)
class Support:
    k: float  # stiffness, MPa per m of wall displacement
    p_max: float  # capacity, MPa


def ring_support(r0: float, thickness: float, e: float, nu: float, sigma_c: float) -> Support:
    """Closed shotcrete or concrete ring loaded on its outer face (thick-walled cylinder elasticity).

    p_max = sigma_c / 2 (1 - (r - t)^2 / r^2); K = E (r^2 - (r - t)^2) / ((1 + nu) r ((1 - 2 nu) r^2 + (r - t)^2)).
    """
    ri = r0 - thickness
    return Support(k=e * (r0**2 - ri**2) / ((1 + nu) * r0 * ((1 - 2 * nu) * r0**2 + ri**2)), p_max=sigma_c / 2 * (1 - ri**2 / r0**2))


def steel_set_support(r0: float, spacing: float, area: float, e: float = 207000.0, sigma_y: float = 245.0) -> Support:
    """Full circular steel sets of cross-section area A (m^2) at spacing S (m), without blocking (Carranza-Torres &
    Fairhurst 2000, simplified form as given by Dang et al. 2022): p_max = 1.5 sigma_y A / (S r), K = E A / (S r^2).
    Steel defaults from Hoek (RocSupport): E 207 GPa, yield 245 MPa. Blocked sets are softer; this is an upper bound."""
    return Support(k=e * area / (spacing * r0**2), p_max=1.5 * sigma_y * area / (spacing * r0))


def bolt_support(r0: float, n_bolts: int, row_spacing: float, length: float, diameter: float, pullout: float,
                 q: float = 0.143, e: float = 207000.0) -> Support:
    """Mechanically anchored bolts (Carranza-Torres & Fairhurst 2000, as given by Dang et al. 2022): s_c = 2 pi r / n,
    p_max = T_bf / (s_c s_l), 1/K = s_c s_l (4 L / (pi d^2 E) + Q). T_bf in MN, Q in m/MN, lengths in m."""
    sc = 2 * math.pi * r0 / n_bolts
    return Support(k=1 / (sc * row_spacing * (4 * length / (math.pi * diameter**2 * e) + q)), p_max=pullout / (sc * row_spacing))


def combine(*supports: Support) -> Support:
    """Supports acting together: stiffnesses add; the combination fails when the first one reaches its capacity."""
    k = sum(s.k for s in supports)
    return Support(k=k, p_max=k * min(s.p_max / s.k for s in supports))


@dataclass(frozen=True)
class Equilibrium:
    pressure: float  # MPa
    u: float  # m
    support_used: float  # fraction of the support capacity mobilised
    fails: bool


def support_equilibrium(p0: float, r0: float, e: float, nu: float, phi_deg: float, c: float, support: Support,
                        u_install: float) -> Equilibrium:
    """Where the support line (installed at wall displacement u_install) meets the ground reaction curve."""
    def gap(u):
        p_support = min(support.k * max(u - u_install, 0.0), support.p_max)
        return p_support - pressure_for_displacement(u, p0, r0, e, nu, phi_deg, c)

    u_free = ground_reaction(p0, 0.0, r0, e, nu, phi_deg, c).u
    if u_install >= u_free:
        return Equilibrium(0.0, u_free, 0.0, False)
    if gap(u_install + support.p_max / support.k) < 0:  # still unbalanced at full capacity: support yields
        return Equilibrium(support.p_max, u_free, 1.0, True)
    lo, hi = u_install, u_install + support.p_max / support.k
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if gap(mid) < 0 else (lo, mid)
    u = 0.5 * (lo + hi)
    p = min(support.k * (u - u_install), support.p_max)
    return Equilibrium(p, u, p / support.p_max, False)


# --------------------------------------------------------------------------- shield thrust and gripper bearing

# Ramoni & Anagnostou (2010), Table 2.3 of VSS 1341: skin friction shield-rock (sliding / static, not lubricated).
SKIN_FRICTION_ROCK = {"sliding": 0.275, "static": 0.425}


@dataclass(frozen=True)
class ShieldLoad:
    contact_from: float | None  # m behind the face where the ground reaches the shield (None: no contact)
    mean_pressure: float  # MPa over the shield length
    friction_force: float  # MN


def shield_friction(r0: float, shield_length: float, overcut: float, p0: float, e: float, nu: float, phi_deg: float,
                    c: float, mu: float = SKIN_FRICTION_ROCK["sliding"], steps: int = 60) -> ShieldLoad:
    """Skin friction on a shield (simplified Ramoni & Anagnostou): F_f = mu 2 pi R integral of the contact pressure."""
    free = ground_reaction(p0, 0.0, r0, e, nu, phi_deg, c)
    u0 = free.u * ldp(0.0, r0, free.r_p)
    p_contact = pressure_for_displacement(overcut, p0, r0, e, nu, phi_deg, c)
    total, first = 0.0, None
    for i in range(steps):
        x = (i + 0.5) * shield_length / steps
        if free.u * ldp(x, r0, free.r_p) - u0 > overcut:
            first = x if first is None else first
            total += p_contact * shield_length / steps
    return ShieldLoad(contact_from=first, mean_pressure=total / shield_length, friction_force=mu * 2 * math.pi * r0 * total)


def gripper_pressure(installed_thrust: float, shoe_area: float, factor: float = 2.0) -> float:
    """Mean contact pressure (MPa) under the gripper shoes: total gripper force = factor x installed thrust (VSS 1341:
    2.0-3.5 as a rule), shared over the total shoe area (m^2). Comparing it with the rock-mass strength is our own
    simple check, not a published rule."""
    return factor * installed_thrust / shoe_area
