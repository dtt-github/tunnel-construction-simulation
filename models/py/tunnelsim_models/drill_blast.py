"""Drill & blast tunnelling: round design (parallel cut, stoping, contour, lifters), fragmentation, ground vibration and
overbreak.

References
- Yilmaz, O. (2023). Drilling and blasting designs for parallel hole cut and V-cut, Sci. Rep. 13:2449,
  https://doi.org/10.1038/s41598-023-29803-6: eqs (1)-(2) hole depth and advance from the empty-hole diameter
  (Holmberg); eqs (3)-(6) four-section cut; eqs (7)-(8) and Table 2 bottom-charge concentration, burden and the
  stoping / roof / wall / floor rules (after Olofsson); worked example pp. 8-10.
- Dyno Nobel (2010). Blasting and Explosives Quick Reference Guide,
  https://www.leg.mn.gov/docs/2015/other/150681/PFEISref_1/Dyno%20Nobel%202010.pdf: p. 4 smooth blasting S = 15-20 d,
  B = 1.25 S; p. 13 scaled-distance law; p. 15 equivalent diameter of several empty holes, d sqrt(n).
- Cunningham, C.V.B. (2005). The Kuz-Ram fragmentation model - 20 years on, EFEE Brighton, pp. 201-210,
  https://www.wits.ac.za/media/wits-university/conferences/misgsa/documents/The%20Kuz-Ram%20fragmentation%20model%20%C3%A2%C2%80%C2%93%2020%20years%20on.pdf:
  mean size, uniformity index (1987 form), Rosin-Rammler. The explosive-strength exponent is printed 19/20 there and
  19/30 in the original Kuznetsov form (Tosun et al. 2014, https://doi.org/10.2478/amsc-2014-0034); it is a parameter.
- Bahrekazemi, Johansson & Bodare (2011). Ground vibrations from rock blasting, 5th ICEGE,
  https://www.issmge.org/uploads/publications/59/67/10.3.GVRBA.pdf: v = A (R / sqrt(Q))^B; Stockholm Northern Link
  tunnel fit A = 1072, B = -1.54.
- SS 460 48 66:2011 as applied in published Swedish risk analyses (Nitro Consult for Solna 2019,
  https://www.Solna.se/download/18.76f8a05e16faf0319722153d/1580131008510/Riskanalys%20vibrationer.pdf; Haninge 2022):
  v = v0 F_b F_m F_t F_d, v0 = 70 / 35 / 18 mm/s on rock / moraine / clay, distance factor F_d per ground.
- Overbreak percentage (A_actual - A_payable) / A_payable (Chao et al. 2026, https://doi.org/10.14456/seagj.2026.11).
Units: m, kg, kg/m^3, mm/s unless stated.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# --------------------------------------------------------------------------- round design


def equivalent_empty_diameter(d_empty: float, n: int) -> float:
    """Several empty (reamed) holes act as one of diameter d sqrt(n) (Dyno Nobel p. 15)."""
    return d_empty * math.sqrt(n)


def hole_depth(d_empty: float) -> float:
    """Holmberg: hole depth H (m) a parallel cut can pull for an empty-hole diameter (m), 0.05-0.25 m (Yilmaz eq 2)."""
    if not 0.05 <= d_empty <= 0.25:
        raise ValueError("empty-hole diameter outside 0.05-0.25 m")
    return 0.15 + 34.1 * d_empty - 39.4 * d_empty**2


def advance(depth: float) -> float:
    """Pull per round: 95 % of the hole depth, for drilling deviation up to 2 % (Yilmaz eq 1)."""
    return 0.95 * depth


def empty_holes_for_depth(depth: float, d_empty: float = 0.102) -> int:
    """Smallest number of empty holes of diameter d_empty whose equivalent diameter pulls `depth`."""
    for n in range(1, 13):
        de = equivalent_empty_diameter(d_empty, n)
        if de <= 0.25 and hole_depth(de) >= depth:
            return n
    raise ValueError("depth not reachable with up to 12 empty holes")


def first_cut_burden(d_empty: float, depth: float = 0.0, angular_dev: float = 0.0, collar_dev: float = 0.0) -> float:
    """First cut section: B1 = 1.5 D0, or 1.7 D0 - (alpha H + beta) when drilling deviation exceeds 1 % (Yilmaz eqs 3-4)."""
    if angular_dev == 0.0 and collar_dev == 0.0:
        return 1.5 * d_empty
    return 1.7 * d_empty - (angular_dev * depth + collar_dev)


def cut_sections(d_empty: float, pull: float, n_max: int = 6) -> list[float]:
    """Side lengths W of the cut squares (m): W1 = B1 sqrt(2), then W_{n+1} = 1.5 W_n sqrt(2) (Dyno Nobel p. 15),
    until the opening approaches sqrt(pull) (Yilmaz: last side about the square root of the advance). Here the cut
    stops at the first side of at least 0.8 sqrt(pull); the stoping holes take over beyond it."""
    w = [1.5 * d_empty * math.sqrt(2)]
    while w[-1] < 0.8 * math.sqrt(pull) and len(w) < n_max:
        w.append(1.5 * w[-1] * math.sqrt(2))
    return w


def bottom_charge(d_hole_mm: float, density: float, aws: float) -> float:
    """Charge concentration (kg/m) of a fully coupled bottom charge, weighted by the weight strength relative to ANFO
    (Yilmaz eq 7): q_b = pi d^2 / 4 rho AWS; density in g/cm^3."""
    d = d_hole_mm / 1000
    return math.pi * d * d / 4 * density * 1000 * aws


def burden(d_hole_mm: float, q_b: float, f: float = 1.0) -> float:
    """Burden (m) for stoping holes: B = 30 q_b f / d (Yilmaz eq 8; f for V-cut angles)."""
    return 30 * q_b * f / d_hole_mm


# Burden and spacing factors, charge-length factors (Yilmaz Table 2, after Olofsson).
HOLE_RULES = {
    "stoping_up": {"burden": 1.0, "spacing": 1.1, "bottom": 1 / 3, "column": 0.5, "stemming": 0.5},
    "stoping_down": {"burden": 1.0, "spacing": 1.2, "bottom": 1 / 3, "column": 0.5, "stemming": 0.5},
    "roof": {"burden": 0.9, "spacing": 1.1, "bottom": 1 / 6, "column": 0.3, "stemming": 0.5},
    "wall": {"burden": 0.9, "spacing": 1.1, "bottom": 1 / 6, "column": 0.4, "stemming": 0.5},
    "floor": {"burden": 1.0, "spacing": 1.1, "bottom": 1 / 3, "column": 1.0, "stemming": 0.2},
}


def smooth_contour(d_hole_mm: float, factor: float = 15.0) -> tuple[float, float]:
    """Smooth-blasting contour: spacing 15 d (hard rock) to 20 d (soft rock), burden 1.25 S (Dyno Nobel p. 4)."""
    s = factor * d_hole_mm / 1000
    return s, 1.25 * s


@dataclass(frozen=True)
class Hole:
    x: float
    y: float
    kind: str  # "empty", "cut", "stoping", "contour", "floor"
    delay: int  # firing order number (0 = empty hole, not fired)


def horseshoe(width: float, wall_height: float) -> tuple[float, float, float]:
    """Profile of vertical walls with a semicircular roof: (radius, total height, area)."""
    r = width / 2
    return r, wall_height + r, width * wall_height + math.pi * r * r / 2


def _inside(x: float, y: float, r: float, wall_h: float, margin: float) -> bool:
    if y < margin or abs(x) > r - margin:
        return False
    if y <= wall_h:
        return True
    return math.hypot(x, y - wall_h) <= r - margin


def _ring(r: float, wall_h: float, inset: float, spacing: float, y0: float) -> list[tuple[float, float]]:
    """Points at `spacing` along the profile offset `inset` inwards, from height y0 up one wall, over the roof and
    down the other wall."""
    rr = r - inset
    wall = max(wall_h - y0, 0.0)
    arc = math.pi * rr
    total = 2 * wall + arc
    n = max(math.floor(total / spacing + 0.5), 2)  # half up, as in the JS twin
    pts = []
    for k in range(n + 1):
        t = total * k / n
        if t <= wall:
            pts.append((-rr, y0 + t))
        elif t <= wall + arc:
            a = math.pi - (t - wall) / rr
            pts.append((rr * math.cos(a), wall_h + rr * math.sin(a)))
        else:
            pts.append((rr, wall_h - (t - wall - arc)))
    return pts


NFF_CONTOUR_MAX_SPACING = 0.7  # m, contour holes "max 0.7 m apart" (NFF Publication 14, section 7.5)
NFF_HELPER_MAX_SPACING = 0.9  # m, row inside the contour "<= 0.9 m" (same)


def round_pattern(width: float, wall_height: float, d_hole_mm: float = 48, d_empty: float = 0.102, n_empty: int = 4,
                  density: float = 1.15, aws: float = 0.8, contour_factor: float = 15.0, contour_spacing: float | None = None,
                  burden_factor: float = 1.0) -> list[Hole]:
    """Face pattern for a horseshoe profile (origin at the floor centre).

    Empty holes and the four-section cut about 1.5 m above the floor; smooth contour holes along walls and roof at
    15 d, at most 0.7 m apart; a helper row one contour burden inside, at most 0.9 m apart; lifters along the floor at
    1.1 B; stoping holes on a staggered grid of burden B and spacing 1.1 B between the cut, the helper row and the
    lifters (Yilmaz Table 2; Dyno Nobel; NFF Publication 14). `contour_spacing` and `burden_factor` (applied to B)
    select a denser practice pattern (see DESIGNS)."""
    r, total_h, _ = horseshoe(width, wall_height)
    qb = bottom_charge(d_hole_mm, density, aws)
    b = burden(d_hole_mm, qb) * burden_factor
    s_c, b_c = smooth_contour(d_hole_mm, contour_factor)
    s_c = contour_spacing if contour_spacing is not None else min(s_c, NFF_CONTOUR_MAX_SPACING)
    edge = 0.15  # contour holes collared just inside the profile, looking out
    holes: list[Hole] = []
    cy = min(1.5, total_h / 3)
    de = equivalent_empty_diameter(d_empty, n_empty)
    for k in range(n_empty):
        a = 2 * math.pi * k / n_empty + math.pi / 4
        holes.append(Hole(0.12 * math.cos(a), cy + 0.12 * math.sin(a), "empty", 0))
    delay = 1
    secs = cut_sections(de, advance(hole_depth(min(de, 0.25))))
    for i, w in enumerate(secs):
        for k in range(4):
            a = math.pi / 2 * k + (math.pi / 4 if i % 2 == 0 else 0)
            rr = w / math.sqrt(2)  # corners of a square of side w; successive squares turned by 45 degrees
            holes.append(Hole(rr * math.cos(a), cy + rr * math.sin(a), "cut", delay))
            delay += 1
    last = len(secs) - 1  # even index: square with sides along x and y; odd: turned 45 degrees

    def near_cut(x: float, y: float) -> bool:
        dx, dy, w = abs(x), abs(y - cy), secs[last]
        return (max(dx, dy) < w / 2 + 0.75 * b) if last % 2 == 0 else (dx + dy < w / math.sqrt(2) + 0.75 * b)

    contour = _ring(r, wall_height, edge, s_c, 0.15 + 0.6)
    helper = _ring(r, wall_height, edge + b_c, min(NFF_HELPER_MAX_SPACING, 1.1 * b), 0.15 + b)
    floor_s = HOLE_RULES["floor"]["spacing"] * b
    n_floor = max(int(math.ceil((width - 2 * edge) / floor_s)), 1)
    floor_pts = [(-(r - edge) + k * (width - 2 * edge) / n_floor, 0.15) for k in range(n_floor + 1)]
    stoping = []
    sb = HOLE_RULES["stoping_up"]["spacing"] * b
    for j in range(int(total_h / b) + 2):
        y = 0.15 + b * j
        nx = int(width / sb) + 1
        for i in range(-nx, nx + 1):
            x = i * sb + (sb / 2 if j % 2 else 0)
            if not _inside(x, y, r, wall_height, edge + b_c + 0.8 * b) or y < 0.15 + 0.8 * b or near_cut(x, y):
                continue
            stoping.append((x, y))
    # firing order: cut, stoping from the cut outwards, helper row, lifters, contour last (each row on one delay)
    stoping.sort(key=lambda p: math.hypot(p[0], p[1] - cy))
    for x, y in stoping:
        holes.append(Hole(x, y, "stoping", delay))
        delay += 1
    for kind, pts in (("helper", helper), ("floor", floor_pts), ("contour", contour)):
        for x, y in pts:
            holes.append(Hole(x, y, kind, delay))
        delay += 1
    return holes


def hole_charge(hole: Hole, depth: float, wall_height: float, q_b: float, d_hole_mm: float = 48) -> float:
    """Explosive in one hole (kg) from Table 2: bottom charge over a share of the depth, column charge at a fraction of
    q_b, stemming of 0.5 B (0.2 B for lifters). Cut holes are charged as stoping holes; contour holes use the roof or
    wall rule by position."""
    if hole.kind == "empty":
        return 0.0
    rule = {"cut": "stoping_up", "stoping": "stoping_up", "helper": "stoping_up", "floor": "floor"}.get(hole.kind)
    if rule is None:
        rule = "roof" if hole.y > wall_height else "wall"
    rr = HOLE_RULES[rule]
    b = burden(d_hole_mm, q_b)  # stemming scales with the Olofsson burden
    bottom = rr["bottom"] * depth
    stem = rr["stemming"] * b
    column = max(depth - bottom - stem, 0.0)
    return q_b * bottom + rr["column"] * q_b * column


@dataclass(frozen=True)
class Round:
    holes: list
    n_charged: int
    drill_metres: float
    explosive: float  # kg
    specific_charge: float  # kg/m^3 of solid rock pulled
    specific_drilling: float  # drill m per m^3
    max_charge_per_delay: float  # kg
    pull: float  # m
    area: float  # theoretical, m^2


# Pattern settings. "textbook": Olofsson burden and smooth-blasting spacing (Yilmaz Table 2, Dyno Nobel, NFF max 0.7 m).
# "norwegian": calibrated to current Norwegian road-tunnel rounds, about 45-50 contour holes and 126-158 charged holes
# on 71-95 m^2 (Jakobsen et al. 2024 as summarised in Tunnels & Tunnelling, https://www.tunnelsandtunnelling.com/?p=23436;
# Gjengedal, Jakobsen & Nilsen, Eurock 2025): contour spacing 0.47 m and stoping burden 0.75 B (fitted, not a rule).
DESIGNS = {
    "textbook": {"contour_spacing": None, "burden_factor": 1.0},
    "norwegian": {"contour_spacing": 0.47, "burden_factor": 0.75},
}


def design_round(width: float, wall_height: float, depth: float, d_hole_mm: float = 48, d_empty: float = 0.102,
                 density: float = 1.15, aws: float = 0.8, design: str = "norwegian") -> Round:
    """Pattern, charges and key figures for a round drilled `depth` m deep; the number of empty holes is the smallest
    that pulls that depth (Holmberg)."""
    n_empty = empty_holes_for_depth(depth, d_empty)
    holes = round_pattern(width, wall_height, d_hole_mm, d_empty, n_empty, density, aws, **DESIGNS[design])
    qb = bottom_charge(d_hole_mm, density, aws)
    kg = [hole_charge(h, depth, wall_height, qb, d_hole_mm) for h in holes]
    per_delay: dict[int, float] = {}
    for h, q in zip(holes, kg):
        if h.delay:
            per_delay[h.delay] = per_delay.get(h.delay, 0.0) + q
    _, _, area = horseshoe(width, wall_height)
    pull = advance(depth)
    total = sum(kg)
    drill = depth * len(holes)
    return Round(holes, sum(1 for h in holes if h.kind != "empty"), drill, total, total / (area * pull), drill / (area * pull),
                 max(per_delay.values()), pull, area)


# --------------------------------------------------------------------------- fragmentation (Kuz-Ram)


def kuz_ram_x50(rock_factor: float, powder_factor: float, charge_per_hole: float, rws: float = 100.0,
                exponent: float = 19 / 30) -> float:
    """Mean fragment size (cm): x50 = A K^-0.8 Q^(1/6) (115 / RWS)^e (Cunningham 2005)."""
    return rock_factor * powder_factor**-0.8 * charge_per_hole ** (1 / 6) * (115 / rws) ** exponent


def uniformity_index(burden_m: float, spacing: float, d_hole_mm: float, deviation: float, charge_length: float,
                     bench: float, bottom_len: float = 0.0, column_len: float = 0.0) -> float:
    """Cunningham (1987) uniformity index n."""
    return ((2.2 - 14 * burden_m / d_hole_mm) * math.sqrt((1 + spacing / burden_m) / 2) * (1 - deviation / burden_m)
            * (abs(bottom_len - column_len) / charge_length + 0.1) ** 0.1 * (charge_length / bench))


def retained(x: float, x50: float, n: float) -> float:
    """Rosin-Rammler fraction coarser than x (same units as x50)."""
    return math.exp(-0.693 * (x / x50) ** n)


# --------------------------------------------------------------------------- vibration

NORTHERN_LINK = {"A": 1072.0, "B": -1.54, "sigma_log10": 0.19}  # Bahrekazemi et al. (2011), Stockholm


def ppv(distance: float, charge: float, a: float = NORTHERN_LINK["A"], b: float = NORTHERN_LINK["B"]) -> float:
    """Peak particle velocity (mm/s) at `distance` (m) for the maximum instantaneous charge per delay (kg)."""
    return a * (distance / math.sqrt(charge)) ** b


def max_charge_per_delay(distance: float, v_limit: float, a: float = NORTHERN_LINK["A"], b: float = NORTHERN_LINK["B"]) -> float:
    """Largest charge per delay (kg) that keeps the PPV below v_limit (mm/s) at `distance` (m)."""
    sd = (v_limit / a) ** (1 / b)
    return (distance / sd) ** 2


# SS 460 48 66:2011: uncorrected vibration value v0 and distance factor F_d = c d^-k (d capped at 350 m).
SS4604866_V0 = {"rock": 70.0, "moraine": 35.0, "clay": 18.0}
SS4604866_FD = {"rock": (2.57, 0.42), "sand_gravel": (1.91, 0.29), "clay": (1.56, 0.19)}


def ss4604866_limit(distance: float, foundation: str = "rock", ground_path: str = "rock", f_b: float = 1.0, f_m: float = 1.0,
                    f_t: float = 1.0) -> float:
    """Guide value of vertical PPV (mm/s) for a building at `distance` (m): v = v0 F_b F_m F_t F_d."""
    c, k = SS4604866_FD[ground_path]
    return SS4604866_V0[foundation] * f_b * f_m * f_t * c * min(max(distance, 1.0), 350.0) ** -k


# --------------------------------------------------------------------------- overbreak


def overbreak_percent(area_actual: float, area_payable: float) -> float:
    return (area_actual - area_payable) / area_payable * 100


# --------------------------------------------------------------------------- support classes and cycle
# Norwegian road-tunnel support classes (NFF Publication 26, 2017, p. 52; Q ranges from the NGI Q-system):
# roof bolts 4 m and wall bolts 3 m at a square spacing (None = spot bolting only), sprayed concrete thickness on the
# roof and on the walls (walls down to 1.5 m above the floor), reinforced ribs of sprayed concrete (RRS) in class IV.
SUPPORT_CLASSES = {
    "I": {"q": (10, 1000), "roof_bolt": 2.5, "wall_bolt": None, "roof_sc": 0.08, "wall_sc": 0.0, "rrs": False},
    "II": {"q": (4, 10), "roof_bolt": 2.0, "wall_bolt": None, "roof_sc": 0.08, "wall_sc": 0.08, "rrs": False},
    "III": {"q": (1, 4), "roof_bolt": 1.7, "wall_bolt": 2.0, "roof_sc": 0.10, "wall_sc": 0.08, "rrs": False},
    "IV": {"q": (0.01, 1), "roof_bolt": 1.3, "wall_bolt": 1.5, "roof_sc": 0.15, "wall_sc": 0.10, "rrs": True},
}
SPOT_BOLTS_PER_ROUND = 4  # assumed for spot bolting

# Contract "equivalent time" standard capacities (NFF Publication 26, 2017, p. 45): bolts up to 5 m 12 per hour,
# sprayed concrete 6 m^3/h (logged elsewhere: 4-12 bolts/h and 3-7 m^3/h from weekly records, Lau 2020, NTNU,
# https://hdl.handle.net/11250/2779502; 8-13 m^3/h gross in time studies, Anderssen & Olsen 2022, NTNU,
# https://hdl.handle.net/11250/3013947). Drill rate up to 3 m/min per drill (NFF Publication 14, 2004, section 7.5;
# 1.8-2.0 m/min in a Publication 28 MWD log).
# Checked against logged rounds at the Ulvin rail tunnel (120 m^2, 200 x 5.2 m holes, three booms, 105 h/week; Messelt
# 2013, NMBU, Table 4, https://hdl.handle.net/11250/189202): mucking 220.6 m^3 solid/h, downtime 2.46 of 19.02 h per round
# (13 %), ventilation off the critical path; and a contractor's estimate for T10.5 (Furunes & Strype 2022, NTNU, Table 4.3,
# https://hdl.handle.net/11250/3020752): ventilation 20 min, scaling 90 min (60-180) median. 101 h/week is the production
# basis of Tunnelbyggetid (EBA, Statens vegvesen, Bane NOR, NTNU, guidance v2.0, 2024). See
# docs/validation/drill-blast-cycle.md.
RATES = {
    "drill_m_per_min": 2.0,  # per boom, net
    "move_min_per_hole": 0.5,  # positioning and collaring per hole, assumed
    "reamer_min_per_hole": 8.0,  # 102 mm empty hole, assumed
    "booms": 3,
    "charge_min_per_hole": 0.6,  # emulsion, two charging lines together, assumed; fits the NFF 4-5 h drill-charge-blast
    "connect_blast_h": 0.5,  # tie-in, clear the tunnel, fire, assumed
    "ventilation_h": 1 / 3,  # contractor median for T10.5 (Furunes & Strype); off the critical path at Ulvin
    "scaling_h": 1.5,  # contractor median for T10.5, 60-180 min (Furunes & Strype); Ulvin 3.3 h at 120 m^2
    "muck_m3_per_h": 220.0,  # solid, logged at Ulvin (Messelt 2013)
    "bolts_per_h": 12.0,
    "shotcrete_m3_per_h": 6.0,
    "rrs_h": 3.0,  # one RRS arch per round including the extra sprayed layer, assumed
    "survey_h": 0.3,  # marking the next round, assumed
    "downtime_fraction": 0.13,  # of the round, logged at Ulvin: 2.46 of 19.02 h (breakdowns, waiting, hose bursts)
}
HOURS_PER_WEEK = 101.0  # production basis of Tunnelbyggetid (about 30 recent Norwegian projects); Ulvin 105 h


def support_quantities(width: float, wall_height: float, pull: float, cls: str) -> dict:
    """Bolts and sprayed concrete for one round of length `pull` in a support class."""
    c = SUPPORT_CLASSES[cls]
    r = width / 2
    roof_len = math.pi * r
    wall_len = 2 * max(wall_height - 1.5, 0.0)
    if c["roof_bolt"]:
        bolts = roof_len * pull / c["roof_bolt"] ** 2
    else:
        bolts = SPOT_BOLTS_PER_ROUND
    bolts += 2 * wall_height * pull / c["wall_bolt"] ** 2 if c["wall_bolt"] else 0
    sc = (roof_len * c["roof_sc"] + wall_len * c["wall_sc"]) * pull
    return {"bolts": math.ceil(bolts), "shotcrete": sc, "rrs": c["rrs"]}


@dataclass(frozen=True)
class Cycle:
    steps: list  # (activity, hours)
    total_h: float
    pull: float
    m_per_week: float
    muck_m3: float  # solid, including overbreak


def round_cycle(rd: Round, width: float, wall_height: float, cls: str, overbreak: float = 0.15, hours_per_week: float = HOURS_PER_WEEK,
                rates: dict | None = None) -> Cycle:
    """Time of one round, activity by activity, done one after another at the face, plus downtime as a share of the
    round, and the weekly advance for `hours_per_week` of production. `overbreak` is the area fraction above the
    theoretical profile (smooth blasting 9-23 % median at Vastlanken)."""
    k = {**RATES, **(rates or {})}
    drilled = [h for h in rd.holes if h.kind != "empty"]
    n_empty = len(rd.holes) - len(drilled)
    depth = rd.drill_metres / len(rd.holes)
    drill_h = (depth * len(drilled) / k["drill_m_per_min"] + len(drilled) * k["move_min_per_hole"]) / k["booms"] / 60
    drill_h += n_empty * k["reamer_min_per_hole"] / 60
    charge_h = len(drilled) * k["charge_min_per_hole"] / 60
    muck = rd.area * (1 + overbreak) * rd.pull
    sup = support_quantities(width, wall_height, rd.pull, cls)
    steps = [
        ("Survey and marking", k["survey_h"]),
        ("Drilling", drill_h),
        ("Charging", charge_h),
        ("Connect and blast", k["connect_blast_h"]),
        ("Ventilation", k["ventilation_h"]),
        ("Scaling", k["scaling_h"]),
        ("Mucking", muck / k["muck_m3_per_h"]),
        ("Bolting", sup["bolts"] / k["bolts_per_h"]),
        ("Sprayed concrete", sup["shotcrete"] * (1 + overbreak) / k["shotcrete_m3_per_h"] + (k["rrs_h"] if sup["rrs"] else 0)),
    ]
    work = sum(h for _, h in steps)
    steps.append(("Downtime and waiting", work * k["downtime_fraction"] / (1 - k["downtime_fraction"])))
    total = sum(h for _, h in steps)
    return Cycle(steps, total, rd.pull, hours_per_week / total * rd.pull, muck)
