"""EPB chamber and screw: hand checks and limiting cases (independent of the generated vectors)."""
import math

import pytest

from tunnelsim_models.epb_chamber import P_ATM, Chamber, ChamberState, Screw, crown_pressure, foam_split


def test_foam_split():
    # FIR 40 %, FER 10: 0.4 m^3 foam per m^3 soil, 0.04 liquid and 0.36 air
    liq, air = foam_split(1.0, 0.4, 10)
    assert liq == pytest.approx(0.04) and air == pytest.approx(0.36)
    with pytest.raises(ValueError):
        foam_split(1.0, 0.4, 0.5)


def test_screw_hand():
    s = Screw(diameter=0.9, shaft_diameter=0.3, pitch=0.7, efficiency=0.6, length=12, decay_length=3)
    q = math.pi * (0.81 - 0.09) / 4 * 0.7 * 10 / 60
    assert s.theoretical_flow(10) == pytest.approx(q)
    assert s.discharge(10) == pytest.approx(0.6 * q)
    assert s.rpm_for_flow(s.discharge(7.5)) == pytest.approx(7.5)
    assert s.outlet_pressure(200) == pytest.approx(0.85 * 200 * math.exp(-4))  # default entrance factor 0.85


def test_screw_botlek_defaults():
    # defaults calibrated between the two Botlek rings (Bezuijen et al. 2005, Figs 8-9): each gauge within the two rings'
    # readings scaled by +-50 %, and far more pressure left along the screw than the old 3 m decay length gave
    s = Screw()
    for pc, gauges in ((3.35, {2.5: 2.05, 5: 1.95, 11.5: 0.9}), (3.1, {2.5: 2.6, 5: 2.45, 11.5: 1.75})):
        for x, measured in gauges.items():
            assert 0.5 < s.pressure_along(x, pc) / measured < 1.6
    assert s.pressure_along(11.5, 3.35) > 10 * Screw(decay_length=3, entrance_factor=1).pressure_along(11.5, 3.35)


def test_equation_of_state():
    ch = Chamber(30.0, k_solid=1e5)
    # air only: Boyle, half the volume -> twice the absolute pressure
    assert ch.pressure(ChamberState(0.0, 60.0)) == pytest.approx(P_ATM)
    # no air: p = K eps for V_i = V_ch / (1 - eps)
    assert ch.pressure(ChamberState(30 / (1 - 0.002), 0.0)) == pytest.approx(200, rel=1e-9)
    # part-empty chamber
    st = ChamberState(20.0, 2.0)
    assert ch.pressure(st) == 0.0 and ch.fill(st) == pytest.approx(22 / 30)
    # state_at inverts pressure
    st = ch.state_at(250, 0.1)
    assert ch.pressure(st) == pytest.approx(250) and ch.air_fraction(st) == pytest.approx(0.1)


def test_conditioning_softens_chamber():
    ch = Chamber(30.0)
    stiff = ch.stiffness(ch.state_at(200, 0.0))
    soft = ch.stiffness(ch.state_at(200, 0.1))
    assert stiff == pytest.approx((1e5 - 200) ** 2 / (1e5 * 30), rel=1e-6)  # V_i (1 - p/K) = V_ch
    # gas: dp/dV = (p + p_atm) / V_air_here
    assert soft == pytest.approx((200 + P_ATM) / 3.0, rel=0.05)
    assert soft < stiff / 10


def test_steady_state_and_dynamics():
    ch = Chamber(30.0)
    qe, fir = 0.032, 0.4
    q = ch.screw_flow_for_pressure(200, qe, fir)
    assert ch.pressure(ch.steady_state(qe, q, fir)) == pytest.approx(200, rel=1e-6)
    # stepping from any start converges to the steady state (time constant V_ch / Q ~ 800 s);
    # exact integration: step size does not matter
    st = ch.state_at(50, 0.2)
    a = b = st
    for _ in range(20000):
        a = ch.step(a, 1.0, qe, q, fir)
    for _ in range(200):
        b = ch.step(b, 100.0, qe, q, fir)
    assert ch.pressure(a) == pytest.approx(200, rel=1e-4)
    assert ch.pressure(a) == pytest.approx(ch.pressure(b), rel=1e-9)
    # screw stopped: contents only grow and pressure rises
    c = ch.step(ch.steady_state(qe, q, fir), 30, qe, 0.0, fir)
    assert ch.pressure(c) > 200
    # screw much faster than the advance: chamber empties below full
    d = st
    for _ in range(600):
        d = ch.step(d, 1.0, qe, 5 * q, fir)
    assert ch.pressure(d) == 0 and ch.fill(d) < 1


def test_crown_pressure():
    assert crown_pressure(200, 3.5, 12) == pytest.approx(158)
    assert crown_pressure(20, 3.5, 12) == 0
