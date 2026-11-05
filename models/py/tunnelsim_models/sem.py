"""Sprayed concrete lining (SEM/NATM): shotcrete ageing, rock-shotcrete interaction during advance, excavation
sequence by ground class, and convergence monitoring.

References
- Oreste, P.P. (2003). A procedure for determining the reaction curve of shotcrete lining considering transient
  conditions. Rock Mech. Rock Eng. 36(3), 209-236, doi:10.1007/s00603-002-0043-z. Shotcrete ageing E(t) = E0 (1 - exp(-a t)),
  sigma_c(t) = sigma_c0 (1 - exp(-b t)) with t in hours (eqs 2-3, after Weber 1979 and Poettler 1990); the closed-ring
  stiffness (eq 1); the fictitious face pressure p = a p0 b / (x + b), a = 0.72, b = 0.845 R (eq 4, Panet & Guenot 1982);
  the average advance rate v_a = v_m / (1 + t0 v_m / delta); and the incremental rock-lining interaction (steps 1-9).
- Neu, G.E., Gall, V., Freitag, S., Meschke, G. (2017). Materials 10(9), 1067, doi:10.3390/ma10091067: measured shotcrete
  strength and stiffness from 6 h to 28 d (Brenner Base Tunnel, SpC25/30(56)/J2), and the CEB-FIP MC90 age function.
- EN 14487-1 early-strength classes J1-J3 (boundary lines as drawn in the Sika Sprayed Concrete Handbook 2021, Fig. 8.1).
- FHWA (2009). Technical Manual for Design and Construction of Road Tunnels, FHWA-NHI-09-010, Tables 9-1 (rock) and
  9-2 (soil): sequence, initial lining thickness, support timing and pre-support by ground class; p. 8-15: final lining
  ideally when convergence is below 1 mm per month.
- Sulem, J., Panet, M., Guenot, A. (1987). IJRMMS 24, 145-154, doi:10.1016/0148-9062(87)90522-5: convergence law
  C(x, t) = C_inf [1 - (X / (X + x))^2] [1 + m (1 - (T / (T + t))^n)], as given by Guayacan-Carrillo et al. (2016).
- Crossrail Learning Legacy, Stepney Green caverns: cycle times (top heading 1 m in 1.5-2.0 h, bench 2 m in 2.5-2.8 h,
  invert 2 m in 3.2-3.5 h) and trigger levels at 75 / 105 / 150 % of the predicted lining displacement.
- Brady, B.H.G., Brown, E.T. (2006). Rock Mechanics for Underground Mining, 3rd ed.: Kirsch displacement around a
  circular opening under vertical stress p and horizontal K p, u_r = (p a / 4G)[(1 + K) - (1 - K)(3 - 4 nu) cos 2theta] at
  the wall (as given in the open GeoStudio SIGMA/W verification "Kirsch", files.seequent.com/GeoStudio/SigmaW/Verification-Kirsch.pdf).
- Staerk, Jimenez Rangel & Wade, Analyses of convergence and utilisation of SCL-tunnels during excavation (Crossrail
  Whitechapel, Learning Legacy): the 10.5-11.5 m enlargements in London Clay settled as a whole by 2-3 mm, with 7-10 mm
  at the crown; movements faded within 5-12 days.

Units: m, MPa, hours unless stated.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .ground_response import ground_reaction, pressure_for_displacement, ring_support

# --------------------------------------------------------------------------- shotcrete ageing

# Oreste (2003) parameter sets: E0, sigma_c0 (MPa) and rates alpha, beta (1/h); nu.
SHOTCRETE = {
    "oreste_example": {"e0": 12000.0, "alpha": 0.050, "sc0": 27.0, "beta": 0.025, "nu": 0.15, "source": "Oreste (2003) Table 3"},
    "kielder": {"e0": 28000.0, "alpha": 0.0187, "sc0": 35.0, "beta": 0.0187, "nu": 0.15, "source": "Oreste (2003) Table 5"},
}
# Measured Brenner Base Tunnel shotcrete (Neu et al. 2017, Table 2): age (h), cube strength (MPa), E (MPa or None).
BRENNER_SHOTCRETE = ((6, 5.46, None), (8, 6.01, None), (16, 14.85, None), (24, 18.57, 13943), (48, 20.64, 18054),
                     (72, 28.63, 19410), (168, 32.90, 21485), (672, 40.84, 21537))


def shotcrete_modulus(t_h: float, preset: str = "kielder") -> float:
    p = SHOTCRETE[preset]
    return p["e0"] * (1 - math.exp(-p["alpha"] * max(t_h, 0.0)))


def shotcrete_strength(t_h: float, preset: str = "kielder") -> float:
    p = SHOTCRETE[preset]
    return p["sc0"] * (1 - math.exp(-p["beta"] * max(t_h, 0.0)))


def mc90_modulus(t_days: float, e28: float, e1: float) -> float:
    """CEB-FIP MC90 age function fitted through E(1 d) and E(28 d): E(t) = E28 exp(s (1 - sqrt(28 / t)))."""
    s = -math.log(e1 / e28) / (math.sqrt(28) - 1)
    return e28 * math.exp(s * (1 - math.sqrt(28 / t_days)))


# EN 14487-1 class boundaries (MPa) at ages (h); straight lines on a log-log plot.
_J_LINES = {
    "A": ((10 / 60, 0.1), (1, 0.2), (12, 1.0), (24, 2.0)),
    "B": ((0.1, 0.2), (0.5, 0.4), (12, 2.8), (24, 5.0)),
    "C": ((0.1, 0.5), (0.5, 1.2), (12, 8.0), (24, 16.0)),
}


def _loglog(points, t):
    lt = math.log(t)
    pts = [(math.log(a), math.log(b)) for a, b in points]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if lt <= x1 or (x1, y1) == pts[-1]:
            return math.exp(y0 + (y1 - y0) * (lt - x0) / (x1 - x0))
    return math.exp(pts[-1][1])


def early_strength_class(t_h: float, strength: float) -> str:
    """EN 14487-1 early-strength class of a strength reached at age t (6 min to 24 h): 'below J1', 'J1', 'J2' or 'J3'."""
    if not 0.1 <= t_h <= 24:
        raise ValueError("classes are defined from 6 min to 24 h")
    if strength < _loglog(_J_LINES["A"], t_h):
        return "below J1"
    if strength < _loglog(_J_LINES["B"], t_h):
        return "J1"
    return "J2" if strength < _loglog(_J_LINES["C"], t_h) else "J3"


# --------------------------------------------------------------------------- rock-shotcrete interaction (Oreste 2003)

def fictitious_pressure(x: float, p0: float, r0: float) -> float:
    """Panet & Guenot (1982) fictitious support pressure at x m behind the face (Oreste eq 4)."""
    b = 0.845 * r0
    return 0.72 * p0 * b / (max(x, 0.0) + b)


def average_advance_rate(v_m: float, dead_time_h: float, step: float) -> float:
    """Average advance rate (m/h) with stops of t0 hours every `step` m at excavation speed v_m (Oreste, Fig. 2)."""
    return v_m / (1 + dead_time_h * v_m / step)


@dataclass(frozen=True)
class LiningInteraction:
    u_install: float  # wall displacement when the lining starts to carry, m
    u_final: float  # at equilibrium, m
    p_final: float  # lining pressure at equilibrium, MPa
    hours_to_95: float  # age when the lining carries 95 % of its final pressure (the last part comes very slowly)
    min_safety: float  # minimum of (strength at age) / (lining stress) during loading
    min_safety_age_h: float
    history: tuple  # (hours since spraying, x behind face m, u m, lining pressure MPa, safety)


def lining_interaction(p0: float, r0: float, e_rock: float, nu_rock: float, phi_deg: float, c: float, thickness: float,
                       x_install: float, advance_m_per_h: float, preset: str = "kielder", steps: int = 400) -> LiningInteraction:
    """Oreste (2003) incremental interaction of an ageing closed shotcrete ring with the ground reaction curve.

    The lining is sprayed at x_install behind the face and the face advances at advance_m_per_h (average rate). Each
    displacement step adds load to the lining with its stiffness at that age; the face effect still carried by the
    ground is the remaining fictitious pressure, which fixes the distance to the face and hence the age.
    """
    nu = SHOTCRETE[preset]["nu"]
    u_star = ground_reaction(p0, min(fictitious_pressure(x_install, p0, r0), p0), r0, e_rock, nu_rock, phi_deg, c).u
    u_free = ground_reaction(p0, 0.0, r0, e_rock, nu_rock, phi_deg, c).u
    du = (u_free - u_star) / steps
    if du <= 0:
        return LiningInteraction(u_star, u_star, 0.0, 0.0, math.inf, 0.0, ())
    geo = ring_support(r0, thickness, 1.0, nu, 1.0)  # stiffness per unit modulus
    stress_per_e = 2 * r0 / ((1 + nu) * ((r0 - thickness) ** 2 + (1 - 2 * nu) * r0**2))  # max ring stress per unit E du
    p_lin, sig, t_prev, u = 0.0, 0.0, 0.0, u_star
    hist, fs_min, fs_age = [], math.inf, 0.0
    for _ in range(steps):
        e_prev = shotcrete_modulus(t_prev, preset)
        u += du
        p_lin += geo.k * e_prev * du
        sig += stress_per_e * e_prev * du
        p_ground = pressure_for_displacement(u, p0, r0, e_rock, nu_rock, phi_deg, c)
        p_fict = p_ground - p_lin
        if p_fict <= 0:
            fs = shotcrete_strength(t_prev, preset) / sig if sig > 0 else math.inf
            hist.append((t_prev, None, u, p_lin, fs))
            if fs < fs_min:
                fs_min, fs_age = fs, t_prev
            return LiningInteraction(u_star, u, p_lin, _hours_to(hist, 0.95 * p_lin), fs_min, fs_age, tuple(hist))
        x = 0.845 * r0 * (0.72 * p0 / p_fict - 1)
        t_prev = max((x - x_install) / advance_m_per_h, 0.0)
        fs = shotcrete_strength(t_prev, preset) / sig if sig > 0 else math.inf
        if fs < fs_min:
            fs_min, fs_age = fs, t_prev
        hist.append((t_prev, x, u, p_lin, fs))
    return LiningInteraction(u_star, u, p_lin, _hours_to(hist, 0.95 * p_lin), fs_min, fs_age, tuple(hist))


def _hours_to(hist, p_target):
    return next(h[0] for h in hist if h[3] >= p_target)


# --------------------------------------------------------------------------- excavation sequence by ground class

# FHWA (2009) Table 9-1 (rock): sequence, initial lining (mm), when support goes in, pre-support.
SEM_ROCK_CLASSES = {
    "intact": {"sequence": "full face or top heading + bench", "lining_mm": (0, 50), "support_lag_rounds": (3, 6), "presupport": "none", "ring_closure": False},
    "stratified": {"sequence": "top heading + bench", "lining_mm": (100, 100), "support_lag_rounds": (2, 3), "presupport": "none", "ring_closure": False},
    "moderately_jointed": {"sequence": "top heading + bench", "lining_mm": (150, 200), "support_lag_rounds": (1, 2), "presupport": "local", "ring_closure": False},
    "blocky_seamy": {"sequence": "top heading + bench", "lining_mm": (200, 300), "support_lag_rounds": (0, 1), "presupport": "systematic spiling", "ring_closure": False},
    "crushed_squeezing": {"sequence": "top heading, bench, invert, ring closure", "lining_mm": (300, 400), "support_lag_rounds": (0, 0), "presupport": "grouted pipe spiles or pipe-arch canopy", "ring_closure": True},
}
# Crossrail Stepney Green cycle times (hours per advance): top heading 1 m, bench 2 m, invert 2 m (mid-range).
CYCLE = {"top_heading": (1.0, 1.75), "bench": (2.0, 2.65), "invert": (2.0, 3.35)}


def ring_closure_ok(invert_lag_m: float, diameter: float, wet: bool = False) -> bool:
    """FHWA Table 9-2: ring closure within one tunnel diameter of the face (less in wet or non-cohesive ground)."""
    return invert_lag_m <= (0.75 if wet else 1.0) * diameter


# --------------------------------------------------------------------------- convergence monitoring

def sulem_convergence(x: float, t_days: float, c_inf: float, x_ref: float, t_ref: float, m: float, n: float) -> float:
    """Sulem et al. (1987): convergence at distance x behind the face and t days after the face passed."""
    if x <= 0:
        return 0.0
    return c_inf * (1 - (x_ref / (x_ref + x)) ** 2) * (1 + m * (1 - (t_ref / (t_ref + t_days)) ** n))


# Fitted to a claystone drift at 490 m depth, D = 5.2 m (Guayacan-Carrillo et al. 2016, Table 1): X = 0.885 D.
SULEM_EXAMPLE = {"x_over_d": 4.6 / 5.2, "t_ref": 6.0, "m": 5.7, "n": 0.3}
# Trigger levels as fractions of the predicted displacement (Crossrail Stepney Green).
TRIGGERS = (("green", 0.75), ("amber", 1.05), ("red", 1.50))
FINAL_LINING_RATE_MM_PER_MONTH = 1.0  # FHWA p. 8-15


def trigger_level(measured: float, predicted: float) -> str:
    level = "none"
    for name, f in TRIGGERS:
        if measured >= f * predicted:
            level = name
    return level


# --------------------------------------------------------------------------- in-tunnel crown settlement (undrained clay)

def kirsch_crown_factor(k: float, nu: float) -> float:
    """Crown displacement over the mean radial displacement of an elastic circular opening under total vertical stress
    sv and horizontal k sv (Kirsch; Brady & Brown 2006). For nu -> 0.5 the crown follows sv alone, whatever k."""
    return 1 + (1 - k) * (3 - 4 * nu) / (1 + k)


WHOLE_BODY_SETTLEMENT = (0.002, 0.003)  # m, settlement of the whole ring, Crossrail Whitechapel enlargements (Staerk et al.)


def crown_settlement(u_final: float, u_survey: float, k: float, nu: float, whole_body: float = 0.0025) -> float:
    """Crown settlement after the first survey: the axisymmetric (mean-stress) movement u_final - u_survey scaled to the
    crown by the Kirsch factor, plus the settlement of the ring as a whole, which a plane-strain ring cannot produce."""
    return max(u_final - u_survey, 0.0) * kirsch_crown_factor(k, nu) + whole_body
