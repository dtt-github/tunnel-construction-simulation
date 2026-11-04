"""EPB excavation chamber: support pressure from a volume balance, foam conditioning and the screw conveyor.

References
- EFNARC (2005). Specification and guidelines for the use of specialist products for mechanised tunnelling (TBM) in
  soft ground and hard rock. (FIR = Q_foam / Q_soil, FER = V_foam / V_liquid.)
- Merritt, A.S., Mair, R.J. (2006). Mechanics of tunnelling machine screw conveyors: model tests. Geotechnique 56(9).
- Merritt, A.S., Mair, R.J. (2008). Mechanics of tunnelling machine screw conveyors: a theoretical model.
  Geotechnique 58(2). (Discharge below the theoretical capacity; pressure falls along the screw by wall and flight
  friction. Here: a constant efficiency and an exponential pressure drop, a simplification of their model.)
- Yeh, I.-C. (1996). Application of neural networks to automatic soil pressure balance control for shield tunneling.
  Automation in Construction 5(5). (Chamber pressure driven by the difference between excavated and discharged volume.)

Chamber contents (generic mixture model, isothermal gas):
the chamber of volume V_ch holds a nearly incompressible part (soil grains, pore water, foam liquid), stored as its
volume at atmospheric pressure V_i, and foam air, stored as its volume at atmospheric pressure V_a. At gauge
pressure p (absolute p + p_atm) they occupy

    V_i (1 - p / K_s)  +  V_a p_atm / (p + p_atm)  =  V_ch          (Boyle's law for the air)

which is solved in closed form for p (a quadratic). If the contents do not fill the chamber at p = 0, the chamber is
part-empty: p = 0 and fill = (V_i + V_a) / V_ch < 1.

Volume balance (contents removed by the screw in proportion to their share, inflows at constant rates):

    dV_i/dt = Q_exc + Q_foam / FER                      - (Q_screw / V_ch) V_i
    dV_a/dt = Q_foam (1 - 1 / FER)                        - (Q_screw / V_ch) V_a ,     Q_foam = FIR Q_exc

with Q_exc = A_face * v the excavated in-situ volume and Q_screw the volume the screw takes from a full chamber. The
linear ODE is integrated exactly over each step. Foam air makes the chamber compliant (pressure changes slowly with a
volume imbalance); unconditioned soil makes it stiff (K_s alone).

Screw conveyor: theoretical capacity Q_th = pi (r^2 - r_shaft^2) pitch n; discharge Q = eta Q_th. Pressure along the
screw p(s) = p_in exp(-s / lambda), lambda the decay length.

Units: m, s, kPa (gauge unless stated), rpm for screw speed, fractions for FIR (1.0 = 100 %).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

P_ATM = 101.325  # kPa


def foam_split(q_soil: float, fir: float, fer: float) -> tuple[float, float]:
    """Foam liquid and foam air (at atmospheric pressure) flows for FIR (fraction) and FER (EFNARC 2005)."""
    if fer < 1:
        raise ValueError("FER must be at least 1")
    q_foam = fir * q_soil
    return q_foam / fer, q_foam * (1 - 1 / fer)


@dataclass(frozen=True)
class Screw:
    diameter: float = 0.9  # m (flight outer diameter)
    shaft_diameter: float = 0.3  # m
    pitch: float = 0.7  # m
    length: float = 12.0  # m
    efficiency: float = 0.6  # discharge / theoretical capacity
    decay_length: float = 3.0  # m, pressure falls by e over this length

    def theoretical_flow(self, rpm: float) -> float:
        """m^3/s."""
        return math.pi * (self.diameter**2 - self.shaft_diameter**2) / 4 * self.pitch * rpm / 60

    def discharge(self, rpm: float) -> float:
        return self.efficiency * self.theoretical_flow(rpm)

    def rpm_for_flow(self, q: float) -> float:
        return q / self.discharge(1.0)

    def pressure_along(self, s: float, p_in: float) -> float:
        return p_in * math.exp(-s / self.decay_length)

    def outlet_pressure(self, p_in: float) -> float:
        return self.pressure_along(self.length, p_in)


@dataclass(frozen=True)
class ChamberState:
    v_inc: float  # incompressible contents, m^3 at atmospheric pressure
    v_air: float  # foam air, m^3 at atmospheric pressure


@dataclass(frozen=True)
class Chamber:
    volume: float  # m^3
    k_solid: float = 100_000.0  # kPa, bulk modulus of the unconditioned soil-water paste (illustrative)

    def pressure(self, st: ChamberState) -> float:
        """Gauge pressure (kPa) at the chamber reference level (the axis)."""
        b = st.v_inc - self.volume
        if b + st.v_air <= 0:
            return 0.0
        a = st.v_inc / self.k_solid
        # a p^2 - (b - a p_atm) p - p_atm (b + V_a) = 0, positive root
        bb = b - a * P_ATM
        cc = P_ATM * (b + st.v_air)
        if a == 0:
            return cc / -bb
        disc = math.sqrt(bb * bb + 4 * a * cc)
        # numerically stable form of the positive root
        return (bb + disc) / (2 * a) if bb >= 0 else 2 * cc / (disc - bb)

    def fill(self, st: ChamberState) -> float:
        """Fraction of the chamber filled (1 once pressurised)."""
        return min((st.v_inc + st.v_air) / self.volume, 1.0)

    def air_fraction(self, st: ChamberState) -> float:
        """Volume fraction of air in the chamber at the current pressure."""
        p = self.pressure(st)
        return st.v_air * P_ATM / (p + P_ATM) / self.volume

    def state_at(self, p: float, air_fraction: float) -> ChamberState:
        """Full chamber at gauge pressure p with the given in-chamber air volume fraction."""
        v_air_here = air_fraction * self.volume
        v_inc_here = self.volume - v_air_here
        return ChamberState(v_inc=v_inc_here / (1 - p / self.k_solid), v_air=v_air_here * (p + P_ATM) / P_ATM)

    def step(self, st: ChamberState, dt: float, q_exc: float, q_screw: float, fir: float = 0.0,
             fer: float = 10.0) -> ChamberState:
        """Advance dt seconds with constant excavated flow, screw flow (m^3/s) and conditioning."""
        q_liq, q_air = foam_split(q_exc, fir, fer)
        k = q_screw / self.volume
        if k <= 0:
            return ChamberState(st.v_inc + (q_exc + q_liq) * dt, st.v_air + q_air * dt)
        e = math.exp(-k * dt)

        def go(x, s):
            return x * e + s / k * (1 - e)

        return ChamberState(go(st.v_inc, q_exc + q_liq), go(st.v_air, q_air))

    def steady_state(self, q_exc: float, q_screw: float, fir: float = 0.0, fer: float = 10.0) -> ChamberState:
        """Contents once inflow and screw outflow balance (state after a long time at constant rates)."""
        q_liq, q_air = foam_split(q_exc, fir, fer)
        return ChamberState((q_exc + q_liq) * self.volume / q_screw, q_air * self.volume / q_screw)

    def screw_flow_for_pressure(self, p: float, q_exc: float, fir: float = 0.0, fer: float = 10.0) -> float:
        """Screw flow that holds the steady chamber pressure at p (kPa gauge, p > 0)."""
        q_liq, q_air = foam_split(q_exc, fir, fer)
        # steady contents scale as 1/Q; find Q with pressure(steady(Q)) = p. Pressure falls with Q: bisection on log Q.
        lo, hi = 1e-9, 1e3
        for _ in range(200):
            mid = math.sqrt(lo * hi)
            if self.pressure(ChamberState((q_exc + q_liq) * self.volume / mid, q_air * self.volume / mid)) > p:
                lo = mid
            else:
                hi = mid
        return math.sqrt(lo * hi)

    def stiffness(self, st: ChamberState) -> float:
        """dp/dV: pressure rise per m^3 of extra incompressible volume (kPa/m^3), by central difference."""
        h = 1e-6 * self.volume
        return (self.pressure(ChamberState(st.v_inc + h, st.v_air)) -
                self.pressure(ChamberState(st.v_inc - h, st.v_air))) / (2 * h)


def crown_pressure(p_axis: float, radius: float, unit_weight: float = 12.0) -> float:
    """Chamber pressure at the crown from the axis value and the paste unit weight (kN/m^3)."""
    return max(p_axis - unit_weight * radius, 0.0)
