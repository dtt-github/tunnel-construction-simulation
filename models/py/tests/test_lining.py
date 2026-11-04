"""Segmental lining against ITA WG2 (2000) Design Example 1 and the jacking check, ITA 2019 bursting formulas and the
DAUB taper."""
import pytest

from tunnelsim_models import lining as L


def test_ita2000_design_example_1():
    # JSCE sewer: Do 3.35 m, Rc 1.6125 m, t 0.125 m, E 33 GPa, I 1.6276e-4 m^4/m, k 20 MN/m^3
    r = L.jsce_ring(183.60, 157.68, 202.83, 3.25, 1.6125, 33e6 * 1.6276e-4, 20000, [0, 40, 70, 90])
    assert r.moment == pytest.approx([6.52, -0.39, -5.07, -4.20], abs=0.015)
    assert r.normal == pytest.approx([278.00, 291.31, 302.44, 304.29], abs=0.02)
    assert r.reaction == pytest.approx(3.27, abs=0.03)  # p_k = k delta
    assert r.deflection == pytest.approx(1.6374e-4, rel=0.01)


def test_ring_symmetry_and_hydrostatic_limit():
    # equal all-round pressure, no self weight: pure compression N = p R, no bending
    r = L.jsce_ring(200, 200, 200, 0, 3.3, 1e5, 10000)
    assert max(abs(m) for m in r.moment) < 1e-9
    assert all(n == pytest.approx(200 * 3.3) for n in r.normal)
    assert r.deflection == pytest.approx(0)


def test_wood_and_bedding():
    assert L.wood_inertia(1.0, 8) == pytest.approx(0.25)
    assert L.wood_inertia(1.0, 6) == pytest.approx(0.4444, abs=1e-4)
    assert L.wood_inertia(1.0, 4) == 1.0
    assert L.subgrade_modulus(30000, 3.0) == pytest.approx(10000)


def test_jacking_and_bursting():
    # ITA 2000 p. 326: 10 jacks of 1000 kN, gap 0.1 m, t 0.125 m, e 10 mm: about 13 MPa
    assert L.jacking_stress(1000, 10, 1.6125, 0.125) == pytest.approx(13_000, rel=0.01)
    t, d = L.bursting_force(3000, 0.35, 0.20, 0.03, "aci")
    assert (t, d) == pytest.approx((321.4, 0.145), abs=0.1)
    t, d = L.bursting_force(3000, 0.35, 0.20, 0.03)
    assert (t, d) == pytest.approx((232.8, 0.116), abs=0.1)


def test_grout_and_taper():
    assert L.annulus_volume(7.06, 6.90, 1.5) == pytest.approx(2.631, abs=0.001)
    lo, hi = L.grout_window(16.5, 20, 3)
    assert lo == pytest.approx(135) and hi == pytest.approx(204)
    assert L.taper(6.9, 1.5, 250) == pytest.approx(0.0414)
    assert L.taper(6.9, 1.5, 250, 22.5) == pytest.approx(0.0430, abs=1e-4)


def test_loads_and_stresses():
    p, q1, q2 = L.ring_loads(20, 3.4, 20, 0.5, 3)
    assert p == pytest.approx(20 * 16.6)
    assert q1 == pytest.approx(0.5 * (332 - 136) + 136)
    hi, lo = L.section_stresses(1000, 50, 0.3)
    assert hi == pytest.approx(1000 / 0.3 + 50 / 0.015)
