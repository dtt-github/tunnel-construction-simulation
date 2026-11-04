"""Slurry shield (Mixshield): filter cake and slurry penetration, support-pressure transfer, air-cushion pressure
control, slurry-circuit mass balance and pipe deposition limit.

References
- DAUB / ITA-AITES (2016). Recommendations for face support pressure calculations for shield tunnelling in soft ground:
  eq (1) stagnation gradient f_s0 = 3.5 tau_f / d10 (Mueller-Kirchenbauer 1977); eq (2) f_s0 = dp / e_max; a filter cake
  (membrane) forms when f_s0 >= 200 kN/m^3 (DIN 4126); section 8.1 worked example; section 7.1 design deviations of the
  support pressure: +/- 10 kPa with an air cushion, +/- 30 kPa for EPB; section 2.2.4 working-chamber slurry level kept
  slightly above the machine axis.
- Broere, W., van Tol, A.F. (2000). Influence of infiltration and groundwater flow on tunnel face stability (ISSMGE):
  eq (8) e_max = dp d10 / (alpha tau_F), alpha between 2 and 4; eq (9) e_t / e_max = t / (a + t) (Krause 1987);
  eqs (10)-(11) pressure drop over the partial cake and the remaining excess pressure; eqs (12)-(13) excess pore
  pressure ahead of the face dp(x) = dp_p exp(-x / lambda), lambda = sqrt(k H c).
- Shomee et al. (2022), PEAT 3(2): dry volume V_dry = V (rho - rho_w) / (rho_s - rho_w), applied here to the feed and
  discharge flows (slurry-circuit mass balance).
- Miedema, Slurry Transport, section 6.27: Durand limit deposit velocity v = F_L sqrt(2 g R_sd D_p).

The air-cushion dynamics are this project's own derivation (no open source with equations was found): Boyle's law
for the air volume above the working-chamber slurry, a level balance from feed, excavation and discharge flows, and a
first-order pressure regulator that adds or vents air.
Units: m, s, kPa, kN/m^3, m^3/s unless stated; densities in t/m^3.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

G = 9.81
GAMMA_W = 10.0  # kN/m^3, as in face_support
P_ATM = 101.325  # kPa
DIN4126_MEMBRANE_F_S0 = 200.0  # kN/m^3
CONTROL_TOLERANCE = {"slurry": 10.0, "epb": 30.0}  # kPa, DAUB (2016) section 7.1


# --------------------------------------------------------------------------- filter cake and penetration

def stagnation_gradient(tau_f: float, d10: float) -> float:
    """f_s0 (kN/m^3) = 3.5 tau_f / d10; tau_f in kPa (kN/m^2), d10 in m (DAUB 2016 eq 1)."""
    return 3.5 * tau_f / d10


def penetration_depth(dp: float, tau_f: float, d10: float, alpha: float = 3.5) -> float:
    """e_max (m) for an excess slurry pressure dp (kPa) over the pore pressure (Broere & van Tol eq 8; DAUB alpha 3.5)."""
    return dp * d10 / (alpha * tau_f)


def forms_membrane(tau_f: float, d10: float) -> bool:
    """DIN 4126: a filter cake forms at the face when f_s0 >= 200 kN/m^3; otherwise the slurry penetrates the ground."""
    return stagnation_gradient(tau_f, d10) >= DIN4126_MEMBRANE_F_S0


def penetration_at(t: float, e_max: float, a: float) -> float:
    """Krause (1987): penetration after t seconds, a = time to reach half of e_max."""
    return e_max * t / (a + t)


@dataclass(frozen=True)
class Infiltration:
    f_s0: float  # kN/m^3
    membrane: bool
    e_max: float  # m
    e_t: float  # m, penetration reached between cutter passes
    dp_cake: float  # kPa carried by the (partial) cake
    dp_excess: float  # kPa left as excess pore pressure at the face
    transfer: float  # fraction of the support force transferred to the ground (approximation of DAUB AA/BB)


def infiltration(dp: float, tau_f: float, d10: float, wedge_length: float, alpha: float = 3.5, t_between_passes: float | None = None,
                 a_half: float | None = None) -> Infiltration:
    """Slurry infiltration at the face for an excess support pressure dp (kPa).

    With a membrane, the full excess pressure acts on the face. With penetration, part of the support force is lost in
    the penetrated zone; DAUB (2016) section 8.1 reduces it by the share of the sliding wedge that the penetration
    zone leaves effectively supported (AA/BB). Here that share is approximated as 1 - e / L, with L the wedge length
    at the crown from the wedge-silo analysis (compare: DAUB example e = 0.54 m, AA/BB = 0.92).
    Between cutter passes the penetration grows by Krause's law (Broere & van Tol); the cake then carries
    e_t alpha tau_f / d10 and the rest remains as excess pore pressure.
    """
    fs = stagnation_gradient(tau_f, d10)
    e_max = penetration_depth(dp, tau_f, d10, alpha)
    if fs >= DIN4126_MEMBRANE_F_S0:
        return Infiltration(fs, True, e_max, 0.0, dp, 0.0, 1.0)
    e_t = e_max if t_between_passes is None or a_half is None else penetration_at(t_between_passes, e_max, a_half)
    dp_cake = min(e_t * alpha * tau_f / d10, dp)
    return Infiltration(fs, False, e_max, e_t, dp_cake, dp - dp_cake, max(0.0, 1 - e_t / wedge_length))


def excess_pore_pressure(x: float, dp_excess: float, k: float, aquifer_thickness: float, resistance: float) -> float:
    """Broere & van Tol eq (12)-(13): excess pore pressure (kPa) at x m ahead of the face."""
    lam = math.sqrt(k * aquifer_thickness * resistance)
    return dp_excess * math.exp(-x / lam)


# --------------------------------------------------------------------------- air cushion (project derivation)

@dataclass(frozen=True)
class CushionState:
    p_air: float  # kPa gauge
    level: float  # slurry level in the working chamber above the axis, m
    air_volume: float  # m^3


@dataclass(frozen=True)
class Cushion:
    chamber_area: float  # plan area of the working chamber at the slurry level, m^2
    tau_regulator: float = 5.0  # s, response time of the air regulator (assumed)

    def step(self, st: CushionState, dt: float, q_feed: float, q_exc: float, q_dis: float, setpoint: float) -> CushionState:
        """Level from the flow balance; the air compresses (Boyle) and the regulator pulls p_air back to the setpoint."""
        dh = (q_feed + q_exc - q_dis) * dt / self.chamber_area
        v_new = max(st.air_volume - dh * self.chamber_area, 0.05)
        p_abs = (st.p_air + P_ATM) * st.air_volume / v_new  # isothermal compression or expansion
        p = p_abs - P_ATM
        p += (setpoint - p) * (1 - math.exp(-dt / self.tau_regulator))  # regulator adds or vents air
        return CushionState(p_air=p, level=st.level + dh, air_volume=v_new)


def face_pressure(p_air: float, level: float, z: float, slurry_unit_weight: float = 11.0) -> float:
    """Support pressure (kPa) at height z relative to the axis: air pressure plus the slurry column above z."""
    return p_air + slurry_unit_weight * (level - z)


# --------------------------------------------------------------------------- slurry circuit

def dry_solids_flow(q_feed: float, rho_feed: float, q_dis: float, rho_dis: float, rho_solid: float = 2.65, rho_w: float = 1.0) -> float:
    """Dry solids removed (m^3/s of grains): discharge minus feed solids (Shomee et al. 2022, applied to flows)."""
    return (q_dis * (rho_dis - rho_w) - q_feed * (rho_feed - rho_w)) / (rho_solid - rho_w)


def theoretical_dry_flow(area: float, advance: float, rho_insitu: float, rho_solid: float = 2.65, rho_w: float = 1.0) -> float:
    """Dry solids excavated at advance rate (m/s) through face area (m^2) for in-situ density rho_insitu."""
    return area * advance * (rho_insitu - rho_w) / (rho_solid - rho_w)


def discharge_density(q_feed: float, rho_feed: float, area: float, advance: float, rho_insitu: float, rho_w: float = 1.0) -> tuple[float, float]:
    """Discharge flow and density when the excavated soil (in-situ volume and density) joins the feed flow."""
    q_exc = area * advance
    q_dis = q_feed + q_exc
    return q_dis, (q_feed * rho_feed + q_exc * rho_insitu) / q_dis


def durand_velocity(pipe_diameter: float, f_l: float = 1.34, rho_solid: float = 2.65, rho_fluid: float = 1.0) -> float:
    """Durand limit deposit velocity (m/s): below it, solids settle in the pipe (Miedema 6.27; F_L ~1.34 coarse)."""
    return f_l * math.sqrt(2 * G * (rho_solid - rho_fluid) / rho_fluid * pipe_diameter)


def pipe_velocity(q: float, pipe_diameter: float) -> float:
    return q / (math.pi * pipe_diameter**2 / 4)
