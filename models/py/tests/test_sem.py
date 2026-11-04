"""SEM models: shotcrete ageing, rock-lining interaction, sequence rules, convergence monitoring."""
import math

import pytest

from tunnelsim_models.ground_response import equivalent_mohr_coulomb
from tunnelsim_models.sem import (
    BRENNER_SHOTCRETE, SEM_ROCK_CLASSES, SHOTCRETE, average_advance_rate, early_strength_class, fictitious_pressure,
    lining_interaction, mc90_modulus, ring_closure_ok, shotcrete_modulus, shotcrete_strength, sulem_convergence,
    trigger_level,
)


def test_shotcrete_ageing():
    k = SHOTCRETE["kielder"]
    assert shotcrete_modulus(1 / k["alpha"]) == pytest.approx(k["e0"] * (1 - math.exp(-1)))
    assert shotcrete_modulus(0) == 0 and shotcrete_modulus(1e5) == pytest.approx(k["e0"])
    assert shotcrete_strength(24) == pytest.approx(35 * (1 - math.exp(-0.0187 * 24)))  # ~12.7 MPa
    # MC90 fit through the measured Brenner values at 1 d and 28 d, checked at 7 d (21,485 MPa measured)
    e1, e28 = BRENNER_SHOTCRETE[3][2], BRENNER_SHOTCRETE[-1][2]
    assert mc90_modulus(1, e28, e1) == pytest.approx(e1) and mc90_modulus(28, e28, e1) == pytest.approx(e28)
    assert mc90_modulus(7, e28, e1) == pytest.approx(21485, rel=0.1)


def test_early_strength_classes():
    # Sika: J2 shotcrete should reach 1.0-1.5 MPa within the first one to two hours; rule of thumb 10 MPa at 24 h
    assert early_strength_class(1, 1.0) == "J2"
    assert early_strength_class(24, 10) == "J2"
    assert early_strength_class(24, 1.0) == "below J1" and early_strength_class(24, 3) == "J1" and early_strength_class(24, 20) == "J3"
    with pytest.raises(ValueError):
        early_strength_class(48, 20)


def test_face_effect_and_rates():
    assert fictitious_pressure(0, 4.0, 5.0) == pytest.approx(0.72 * 4.0)
    assert fictitious_pressure(0.845 * 5.0, 4.0, 5.0) == pytest.approx(0.36 * 4.0)
    assert average_advance_rate(1.0, 0, 1.2) == 1.0
    assert average_advance_rate(1.0, 1.0, 1.2) == pytest.approx(1.0 / (1 + 1 / 1.2))


def test_lining_interaction():
    p0 = 0.027 * 100
    m = equivalent_mohr_coulomb(22, 8, 15, 3000, p0)
    args = (p0, 5.0, m.e_rm, 0.25, m.phi_deg, m.c)
    thin, thick = lining_interaction(*args, 0.2, 1.0, 3 / 24), lining_interaction(*args, 0.4, 1.0, 3 / 24)
    assert thick.u_final < thin.u_final and thick.p_final > thin.p_final  # stiffer lining: less closure, more load
    slow, fast = lining_interaction(*args, 0.35, 1.0, 1 / 24), lining_interaction(*args, 0.35, 1.0, 6 / 24)
    assert fast.p_final < slow.p_final  # faster advance: the lining is younger when loaded (Oreste 2003)
    assert thin.u_install < thin.u_final and 0 < thin.hours_to_95


def test_sequence_and_monitoring():
    assert SEM_ROCK_CLASSES["crushed_squeezing"]["ring_closure"] and not SEM_ROCK_CLASSES["moderately_jointed"]["ring_closure"]
    assert ring_closure_ok(9.0, 10.0) and not ring_closure_ok(12.0, 10.0) and not ring_closure_ok(9.0, 10.0, wet=True)
    assert sulem_convergence(0, 10, 20, 4.6, 6, 5.7, 0.3) == 0
    # far from the face the distance term is ~1; the time term tends slowly to 1 + m (n = 0.3)
    assert sulem_convergence(1e6, 1e9, 20, 4.6, 6, 5.7, 0.3) == pytest.approx(20 * (1 + 5.7 * (1 - (6 / (6 + 1e9)) ** 0.3)), rel=1e-6)
    assert sulem_convergence(10, 30, 20, 4.6, 6, 5.7, 0.3) > sulem_convergence(10, 3, 20, 4.6, 6, 5.7, 0.3)
    assert trigger_level(7, 10) == "none" and trigger_level(8, 10) == "green" and trigger_level(11, 10) == "amber" and trigger_level(16, 10) == "red"
