"""Hard-rock TBM drive: cutter wear and changes, rock support by class, and utilisation as downtime per kilometre.

References
- Farrokh, E. (2018). Study of utilization factor and advance rate of hard rock TBMs. Journal of Mining & Environment
  9(2), 457-472, doi:10.22044/jme.2018.6815.1509. Downtime categories in h/km with fitted curves, NTNU terms
  (Table 4), maintenance and transport classes (Tables 5-6), cutter (Fig. 9) and support (Fig. 12) downtime,
  regrip and curve terms (Eq. 4), and a worked example (open TBM, 3.9 m: 1021 h/km, U = 21 %, 23.5 m/day).
- Frenzel, C. (2011), via Zhang et al. (2025), Int. J. Coal Sci. Technol. 12:50, doi:10.1007/s40789-025-00787-0
  (Table 11): cutter life CL = 1026 / CAI m^3 per cutter (17-inch disc, 10 cm spacing, 5 mm/rev).
- Farrokh, E. (2013), SME (OneMine): average cutter change time about 66 min.
- Bieniawski, Z.T. (1989), via Hoek, Practical Rock Engineering, ch. 3 (rocscience.com): RMR support classes for a
  10 m span (drill and blast); GSI = RMR89' - 5 for RMR89' > 23.

Downtime model (Farrokh 2018):
    T_b  = 1000 / PR                                       boring, h/km (PR = net penetration rate, m/h)
    T_r  = 1000 t_r / (60 L_s) + 409000 / R^2              regrip (t_r min per stroke, L_s stroke m, R curve radius m)
    T_tbm, T_bu, T_c, T_sp, T_m, T_tr, T_u, T_s, T_o       TBM, backup, cutter, support, maintenance, transport,
                                                           utilities, survey, other (h/km)
    U    = T_b / sum(T)            AR = 24000 / sum(T)  m/day
Support downtime is digitised from Farrokh's Fig. 12 (about +/- 20 h/km) and interpolated in diameter and RMR.
Units: m, m/h, h/km, MPa.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

FARROKH = "Farrokh (2018), doi:10.22044/jme.2018.6815.1509"

# --------------------------------------------------------------------------- cutter wear

CUTTER_CHANGE_H = 66 / 60  # average time per changed cutter (Farrokh 2013)


def cutter_life_m3(cai: float) -> float:
    """Frenzel (2011): rock volume excavated per disc cutter, m^3 (17-inch disc reference conditions)."""
    if cai <= 0:
        raise ValueError("CAI must be positive")
    return 1026.0 / cai


def cutters_per_km(diameter_m: float, cai: float) -> float:
    return 1000 * math.pi * diameter_m**2 / 4 / cutter_life_m3(cai)


def cutter_change_h_per_km(diameter_m: float, cai: float, change_h: float = CUTTER_CHANGE_H) -> float:
    """Cutter-change downtime from wear: cutters consumed per km x time per change."""
    return cutters_per_km(diameter_m, cai) * change_h


def cutter_downtime_farrokh(pr_m_h: float, quartz_percent: float) -> float:
    """Farrokh (2018) Fig. 9 fits of cutter-change downtime (h/km) by quartz content; a cross-check for the wear model."""
    if quartz_percent < 5:
        return 30.0
    if quartz_percent <= 20:
        return 178.38 * pr_m_h**-0.707
    return 384.74 * pr_m_h**-0.745


# --------------------------------------------------------------------------- rock mass and support

def rmr_from_gsi(gsi: float) -> float:
    """RMR89' (dry, no orientation adjustment) from GSI, inverting GSI = RMR89' - 5 (valid for RMR89' > 23)."""
    return gsi + 5


# Bieniawski (1989) support for a 10 m span, drill and blast (via Hoek). Shown as the support pattern per class.
RMR_CLASSES = (
    {"class": "I", "rmr": (81, 100), "name": "Very good", "bolts": "spot bolting only", "shotcrete": "none", "ribs": "none"},
    {"class": "II", "rmr": (61, 80), "name": "Good", "bolts": "locally in crown, 3 m long at 2.5 m, occasional mesh",
     "shotcrete": "50 mm in crown where required", "ribs": "none"},
    {"class": "III", "rmr": (41, 60), "name": "Fair", "bolts": "systematic 4 m at 1.5-2 m in crown and walls, mesh in crown",
     "shotcrete": "50-100 mm in crown, 30 mm in sides", "ribs": "none"},
    {"class": "IV", "rmr": (21, 40), "name": "Poor", "bolts": "systematic 4-5 m at 1-1.5 m, with mesh",
     "shotcrete": "100-150 mm in crown, 100 mm in sides", "ribs": "light to medium ribs at 1.5 m where required"},
    {"class": "V", "rmr": (0, 20), "name": "Very poor", "bolts": "systematic 5-6 m at 1-1.5 m, mesh, bolt the invert",
     "shotcrete": "150-200 mm crown, 150 mm sides, 50 mm face", "ribs": "medium to heavy ribs at 0.75 m, steel lagging, close the invert"},
)


def rmr_class(rmr: float) -> dict:
    for c in RMR_CLASSES:
        if rmr >= c["rmr"][0]:
            return c
    return RMR_CLASSES[-1]


def _interp(x: float, pts: tuple[tuple[float, float], ...]) -> float:
    """Piecewise-linear interpolation, linear extrapolation beyond the ends, never below zero."""
    if x <= pts[0][0]:
        (x0, y0), (x1, y1) = pts[0], pts[1]
    elif x >= pts[-1][0]:
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
    else:
        i = next(k for k in range(1, len(pts)) if x <= pts[k][0])
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
    return max(y0 + (y1 - y0) * (x - x0) / (x1 - x0), 0.0)


# Farrokh (2018) Fig. 12, digitised (RMR, h/km). Open TBM at 4 m and 10 m; shields independent of diameter.
_SUPPORT_OPEN_4M = ((40.0, 500.0), (70.0, 100.0), (80.0, 0.0))
_SUPPORT_OPEN_10M = ((40.0, 700.0), (70.0, 100.0), (80.0, 0.0))
_SUPPORT_SINGLE = ((20.0, 1000.0), (40.0, 225.0), (100.0, 225.0))
_SUPPORT_DOUBLE_MIN_RMR = 50.0  # double shield: about 100 h/km for RMR >= 50; below, single-shield mode (assumption)


def support_downtime(rmr: float, diameter_m: float, machine: str = "open") -> float:
    """Ground-support downtime (h/km) by RMR and machine type ("open", "single", "double")."""
    if machine == "open":
        a, b = _interp(rmr, _SUPPORT_OPEN_4M), _interp(rmr, _SUPPORT_OPEN_10M)
        f = min(max((diameter_m - 4) / 6, 0.0), 1.0)
        return a + (b - a) * f
    if machine == "single":
        return _interp(rmr, _SUPPORT_SINGLE)
    if machine == "double":
        return 100.0 if rmr >= _SUPPORT_DOUBLE_MIN_RMR else _interp(rmr, _SUPPORT_SINGLE)
    raise ValueError(f"unknown machine {machine}")


# --------------------------------------------------------------------------- utilisation

MAINTENANCE_CLASSES = {"good": 75.0, "normal": 150.0, "poor": 300.0}  # Table 5 (mid-range of 50-100, 100-200)
TRANSPORT_CLASSES = {"very_good": 25.0, "good": 50.0, "normal": 150.0, "poor": 350.0, "very_poor": 500.0}  # Table 6


def tbm_breakdown_downtime(pr_m_h: float, ucs_mpa: float) -> float:
    """Farrokh (2018) TBM breakdown downtime fits (h/km) by rock strength."""
    if ucs_mpa > 150:
        return 337.6 * math.exp(-0.394 * pr_m_h)
    if ucs_mpa >= 100:
        return 238.12 * math.exp(-0.407 * pr_m_h)
    return 149.15 * math.exp(-0.407 * pr_m_h)


def backup_downtime(pr_m_h: float, haulage: str = "rail") -> float:
    """Farrokh (2018) backup downtime fits (h/km): rail haulage or continuous conveyor."""
    return 85.586 * math.exp(-0.31 * pr_m_h) if haulage == "rail" else 36.873 * math.exp(-0.195 * pr_m_h)


@dataclass(frozen=True)
class HardRockUtilisation:
    h_per_km: dict  # each category
    total_h_per_km: float
    utilisation: float
    advance_m_day: float


def hard_rock_utilisation(
    pr_m_h: float, diameter_m: float, *, stroke_m: float = 1.8, regrip_min: float = 4.0, curve_radius_m: float = math.inf,
    ucs_mpa: float = 150.0, rmr: float = 60.0, machine: str = "open", haulage: str = "conveyor",
    cutter_h_per_km: float | None = None, quartz_percent: float = 10.0, maintenance: str = "normal",
    transport: str = "good", utilities: float = 40.0, survey: float = 12.5, other: float = 100.0,
) -> HardRockUtilisation:
    """Downtime per km and utilisation (Farrokh 2018). cutter_h_per_km overrides the quartz-based cutter fit.

    Double shields build rings while boring, but boring still stops for each regrip (the gripper shield is pulled up to
    the front shield): "a few minutes" (Herrenknecht) to 15-30 min (Maggio 2020, citing Wittke 2006); pass regrip_min.
    """
    if pr_m_h <= 0:
        raise ValueError("penetration rate must be positive")
    t = {
        "boring": 1000 / pr_m_h,
        "regrip": 1000 * regrip_min / (60 * stroke_m) + (409000 / curve_radius_m**2 if math.isfinite(curve_radius_m) else 0.0),
        "tbm_breakdown": tbm_breakdown_downtime(pr_m_h, ucs_mpa),
        "backup": backup_downtime(pr_m_h, haulage),
        "cutters": cutter_downtime_farrokh(pr_m_h, quartz_percent) if cutter_h_per_km is None else cutter_h_per_km,
        "support": support_downtime(rmr, diameter_m, machine),
        "maintenance": MAINTENANCE_CLASSES[maintenance],
        "transport": TRANSPORT_CLASSES[transport],
        "utilities": utilities,
        "survey": survey + (192000 / curve_radius_m**2 if math.isfinite(curve_radius_m) else 0.0),
        "other": other,
    }
    total = sum(t.values())
    return HardRockUtilisation(h_per_km=t, total_h_per_km=total, utilisation=t["boring"] / total, advance_m_day=24000 / total)
