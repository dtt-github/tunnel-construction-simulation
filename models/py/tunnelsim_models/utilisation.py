"""TBM utilisation: activity-time model of the drive, with downtime, shift pattern and a check against record rates.

References
- Moosazadeh, S., Aghababaie, H., Hoseinie, S.H., Rostami, J. (2018). Simulation of tunnel boring machine utilization:
  a case study. Journal of Mining & Environment 9(1), 53-60, doi:10.22044/jme.2017.5707.1384.
  6.88 m EPB, Tabriz metro: fitted distributions (minutes) for ring build, general tunnelling activities and train
  delay; TBM and logistics maintenance 25 and 12 min per cycle; rings between cutting-tool stops (Weibull) and time to
  repair per stop (log-logistic, hours); simulated utilisation about 14 %.
- Johnson, M. (2014). Urban EPBs, San Francisco Central Subway. NAT 2014. Production day of 2 x 10 h shifts plus a
  4 h maintenance shift.
- McMillan, S. et al. (2022). Time usage models for TBM tunnelling. Tunnelling Association of Canada.
  Utilisation = boring time / calendar time (the definition used here).
- Roby, J., Willis, D. (2014). Achieving fast EPB advance rates. NAT 2014. 40 EPBs, 5.9-10.2 m: mean 85.4 m/week
  (SD 36.0, max 178.5).
- Record and reference rates: see ADVANCE_REFERENCES (each entry has its source).
- Barcelona Metro Line 9, 9.40 m EPBs (Sustainability 17(9), 3966, 2025, CC BY, https://www.mdpi.com/2071-1050/17/9/3966): the first machine took "a
  little over three months to reach average speed" (learning curve). Learning curve here: production activities run
  at a fraction of their steady rate that rises linearly from LEARNING_START to 1 over learning_days of calendar time;
  the linear shape and the starting fraction are assumptions, only the duration has a source.

Model (discrete events, one ring at a time):
    per ring: boring (from the advance speed, or the fitted distribution) -> ring build -> general activities
              -> train delay (rail haulage only) -> TBM and logistics maintenance (when no maintenance shift)
    shift pattern: production hours per day; the rest of each day is a maintenance shift (no boring or building).
    cutting-tool interventions: after a Weibull-distributed number of rings, the drive stops for a log-logistic
              time to repair, in calendar time (interventions run round the clock).
Distribution parameters are as fitted for one project (Tabriz) and are illustrative for others; calibrate per project.
Not modelled: locomotive travel time growing with tunnel length (Tabriz models it; there our simplified rail haulage
gives about 19 % utilisation against their 14 %), ground-related stops other than tool interventions. The learning
curve is optional (learning_days, off by default).

A seeded generator (mulberry32) makes runs reproducible and identical in the JavaScript twin.
Units: minutes inside the model; outputs in metres, days and fractions.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- random numbers and distributions


class Rng:
    """mulberry32: small, fast, reproducible, and bit-identical in JavaScript."""

    def __init__(self, seed: int):
        self.a = seed & 0xFFFFFFFF

    def uniform(self) -> float:
        self.a = (self.a + 0x6D2B79F5) & 0xFFFFFFFF
        t = self.a
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return (((t ^ (t >> 14)) & 0xFFFFFFFF) + 0.5) / 4294967296.0  # in (0, 1)


def normal_inv(p: float) -> float:
    """Inverse standard normal CDF (Acklam's rational approximation, |error| < 1.2e-9)."""
    a = (-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02, 1.383577518672690e02,
         -3.066479806614716e01, 2.506628277459239e00)
    b = (-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01,
         -1.328068155288572e01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00, -2.549732539343734e00,
         4.374664141464968e00, 2.938163982698783e00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00)
    if p < 0.02425:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > 1 - 0.02425:
        return -normal_inv(1 - p)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
        (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def sample(dist: dict, u: float) -> float:
    """Inverse-CDF sample of a distribution spec at uniform u."""
    k = dist["kind"]
    if k == "fixed":
        return dist["value"]
    if k == "loglogistic":  # shape alpha, scale beta, location gamma
        return dist["gamma"] + dist["beta"] * (u / (1 - u)) ** (1 / dist["alpha"])
    if k == "lognormal":  # sigma, mu, location gamma
        return dist["gamma"] + math.exp(dist["mu"] + dist["sigma"] * normal_inv(u))
    if k == "weibull":  # shape k, scale lam
        return dist["lam"] * (-math.log(1 - u)) ** (1 / dist["k"])
    if k == "triangular":  # min a, mode m, max b
        a, m, b = dist["a"], dist["m"], dist["b"]
        f = (m - a) / (b - a)
        return a + math.sqrt(u * (b - a) * (m - a)) if u < f else b - math.sqrt((1 - u) * (b - a) * (b - m))
    raise ValueError(f"unknown distribution {k}")


def median(dist: dict) -> float:
    return sample(dist, 0.5)


# --------------------------------------------------------------------------- parameter sets

TABRIZ = "Moosazadeh et al. (2018), doi:10.22044/jme.2017.5707.1384"
DIST = {
    "ring_build": {"kind": "lognormal", "sigma": 0.62899, "mu": 2.123, "gamma": 9.0618, "source": TABRIZ},
    "boring": {"kind": "loglogistic", "alpha": 3.9756, "beta": 17.769, "gamma": 16.368, "source": TABRIZ},
    "general": {"kind": "loglogistic", "alpha": 2.3998, "beta": 18.654, "gamma": 1.0364, "source": TABRIZ},
    "train_delay": {"kind": "triangular", "a": 20.0, "m": 30.0, "b": 70.0, "source": TABRIZ},
    "rings_between_stops": {"kind": "weibull", "k": 1.549, "lam": 274.91, "source": TABRIZ},
    "stop_hours": {"kind": "loglogistic", "alpha": 2.013, "beta": 105.11, "gamma": 0.0, "source": TABRIZ},
}

# Shift patterns: production minutes per day (the rest is a maintenance shift). Per-cycle maintenance applies only
# where there is no maintenance shift, so the two are not counted twice.
SHIFT_PATTERNS = {
    "2x10h_plus_4h_maintenance": {"production_h": 20.0, "per_cycle_maintenance": False,
                                   "source": "Johnson (2014), SF Central Subway, NAT 2014"},
    "2x12h_maintenance_per_cycle": {"production_h": 24.0, "per_cycle_maintenance": True,
                                     "source": TABRIZ},
    "idealised_24h": {"production_h": 24.0, "per_cycle_maintenance": False,
                      "source": "none: no maintenance at all, for checks and upper bounds only"},
}
PER_CYCLE_MAINTENANCE_MIN = 25.0 + 12.0  # TBM + logistics system, Tabriz
LEARNING_DAYS_BARCELONA = 90.0  # "a little over three months to reach average speed", Barcelona Line 9 (see above)
LEARNING_START = 0.5  # productivity on the first day as a fraction of the steady rate: assumed


@dataclass
class DriveSettings:
    ring_length: float = 1.5  # m
    boring_min: float | None = None  # fixed boring time per ring; None = fitted distribution
    ring_build: dict = field(default_factory=lambda: DIST["ring_build"])
    general: dict = field(default_factory=lambda: DIST["general"])
    shift_pattern: str = "2x10h_plus_4h_maintenance"
    haulage: str = "conveyor"  # "rail": train delay every cycle; "conveyor": none
    interventions: bool = True
    learning_days: float = 0.0  # learning curve length (calendar days); 0 = steady from the start
    learning_start: float = LEARNING_START  # productivity on day 0 as a fraction of the steady rate


@dataclass(frozen=True)
class DriveResult:
    days: int
    rings: int
    metres: float
    utilisation: float  # boring time / calendar time
    mean_m_per_day: float
    mean_m_per_week: float
    best_day: float
    best_week: float
    best_month: float
    shares: dict  # fraction of calendar time per activity; the remainder is maintenance shift and idle time
    interventions: int


# --------------------------------------------------------------------------- simulation

DAY = 1440.0


def _production_window(t: float, prod_min: float) -> tuple[float, float]:
    """Start and end of the production window that contains t, or the next one."""
    day0 = math.floor(t / DAY) * DAY
    if t < day0 + prod_min:
        return day0, day0 + prod_min
    return day0 + DAY, day0 + DAY + prod_min


def simulate_drive(settings: DriveSettings, days: int = 90, seed: int = 1) -> DriveResult:
    """Run the drive for `days` calendar days and report utilisation and daily, weekly and monthly advance."""
    rng = Rng(seed)
    pattern = SHIFT_PATTERNS[settings.shift_pattern]
    prod_min = pattern["production_h"] * 60
    horizon = days * DAY
    t = 0.0
    time = {"boring": 0.0, "ring_build": 0.0, "general": 0.0, "train_delay": 0.0, "maintenance_per_cycle": 0.0,
            "intervention": 0.0}
    daily = [0.0] * days
    rings = 0
    stops = 0
    next_stop = sample(DIST["rings_between_stops"], rng.uniform()) if settings.interventions else math.inf

    def work(t, dur, key):
        """Spend `dur` minutes of production time from t, booking it; returns (end time, minutes left at the horizon)."""
        while dur > 1e-9 and t < horizon:
            w0, w1 = _production_window(t, prod_min)
            t = max(t, w0)
            d = min(dur, w1 - t, horizon - t)
            time[key] += d
            t += d
            dur -= d
        return t, max(dur, 0.0)

    def slow(t: float) -> float:
        """Duration factor of production activities at time t: 1 / productivity on the learning curve."""
        if settings.learning_days <= 0:
            return 1.0
        f = min(t / (settings.learning_days * DAY), 1.0)
        return 1.0 / (settings.learning_start + (1.0 - settings.learning_start) * f)

    while t < horizon:
        bore = settings.boring_min if settings.boring_min is not None else sample(DIST["boring"], rng.uniform())
        t, left = work(t, bore * slow(t), "boring")
        if left > 1e-9:
            break  # horizon reached during boring: the partial ring is not credited
        daily[min(int((t - 1e-9) / DAY), days - 1)] += settings.ring_length  # credited when boring ends
        rings += 1
        t, _ = work(t, sample(settings.ring_build, rng.uniform()) * slow(t), "ring_build")
        t, _ = work(t, sample(settings.general, rng.uniform()) * slow(t), "general")
        if settings.haulage == "rail":
            t, _ = work(t, sample(DIST["train_delay"], rng.uniform()), "train_delay")
        if pattern["per_cycle_maintenance"]:
            t, _ = work(t, PER_CYCLE_MAINTENANCE_MIN, "maintenance_per_cycle")
        if rings >= next_stop and t < horizon:
            d = min(sample(DIST["stop_hours"], rng.uniform()) * 60, horizon - t)
            time["intervention"] += d
            t += d
            stops += 1
            next_stop = rings + sample(DIST["rings_between_stops"], rng.uniform())

    total = days * DAY
    shares = {k: v / total for k, v in time.items()}
    shares["maintenance_shift_and_idle"] = max(0.0, 1 - sum(shares.values()))
    weeks = [sum(daily[i:i + 7]) for i in range(0, days - 6)]
    months = [sum(daily[i:i + 30]) for i in range(0, days - 29)]
    metres = sum(daily)
    return DriveResult(
        days=days, rings=rings, metres=metres, utilisation=time["boring"] / total,
        mean_m_per_day=metres / days, mean_m_per_week=metres / days * 7,
        best_day=max(daily), best_week=max(weeks) if weeks else 0.0, best_month=max(months) if months else 0.0,
        shares=shares, interventions=stops,
    )


# --------------------------------------------------------------------------- record and reference rates

ROBBINS_RECORDS = "https://www.robbinstbm.com/news-and-media/world-records/"
# Industry-wide records by diameter class (any TBM type; the 6-11 m entries are hard-rock machines). Upper bounds.
WORLD_RECORDS = (
    {"class": (6.01, 7.0), "day": 124.7, "week": 515.1, "month": 1754.0, "source": ROBBINS_RECORDS},
    {"class": (7.01, 8.0), "day": 115.7, "week": 428.0, "month": 1482.0, "source": ROBBINS_RECORDS},
    {"class": (8.01, 9.0), "day": 75.5, "week": 428.0, "month": 1719.0, "source": ROBBINS_RECORDS},
    {"class": (9.01, 10.0), "day": 105.6, "week": 435.0, "month": 1600.0, "source": ROBBINS_RECORDS},
    {"class": (10.01, 11.0), "day": 48.8, "week": 235.0, "month": 841.8, "source": ROBBINS_RECORDS},
)
# Best published EPB rates (project reports, not a curated record table). Exceeding them needs a reason.
EPB_REFERENCES = (
    {"what": "best day", "metric": "day", "value": 40.6, "diameter": 6.39, "project": "Bangkok Orange Line E3",
     "source": "https://tunnelingonline.com/terratec-marks-major-milestone-in-bangkok/"},
    {"what": "best month", "metric": "month", "value": 920.0, "diameter": None, "project": "Doha Gold Line (contractor claim)",
     "source": "https://tunnelbuilder.com/News/SELI-breaks-through-on-the-Gold-Line-on-the-Doha-Metro-in-record-time.aspx"},
    {"what": "best week in a survey of 40 EPBs, 5.9-10.2 m", "metric": "week", "value": 178.5, "diameter": None,
     "project": "Roby & Willis (2014)", "source": "https://www.robbinstbm.com/wp-content/uploads/2014/08/FastEPBAdvance_NAT2014.pdf"},
    {"what": "week, 9.73 m EPB", "metric": "week", "value": 260.0, "diameter": 9.73, "project": "Riyadh Metro Line 5",
     "source": "https://www.herrenknecht.com/en/references/referencesdetail/riyadh-metro/"},
)
EPB_WEEKLY_SURVEY = {"mean": 85.4, "sd": 36.0, "min": 32.6, "max": 178.5,
                     "source": "https://www.robbinstbm.com/wp-content/uploads/2014/08/FastEPBAdvance_NAT2014.pdf"}


def record_check(diameter: float, best_day: float, best_week: float, best_month: float, method: str = "epb") -> dict:
    """Compare simulated best rates with the world record of the diameter class and, for EPB, the best references.

    Returns {metric: {"value", "world_record", "above_world_record", "epb_reference", "above_epb_reference"}}.
    """
    rec = next((r for r in WORLD_RECORDS if r["class"][0] <= diameter <= r["class"][1] + 0.0099), None)
    out = {}
    for metric, v in (("day", best_day), ("week", best_week), ("month", best_month)):
        wr = rec[metric] if rec else None
        refs = [r["value"] for r in EPB_REFERENCES if r["metric"] == metric] if method == "epb" else []
        ref = max(refs) if refs else None
        out[metric] = {"value": v, "world_record": wr, "above_world_record": wr is not None and v > wr,
                       "epb_reference": ref, "above_epb_reference": ref is not None and v > ref}
    return out
