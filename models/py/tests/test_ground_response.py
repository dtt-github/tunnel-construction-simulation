"""Ground response: published worked examples and limiting cases."""
import math

import pytest

from tunnelsim_models.ground_response import (
    Support, bolt_support, combine, equivalent_mohr_coulomb, gripper_pressure, ground_reaction, ldp, mc_strength,
    pressure_for_displacement, ring_support, shield_friction, squeezing_class, squeezing_strain, steel_set_support,
    support_equilibrium,
)


def test_duncan_fama_hoek_example():
    # Hoek, Tunnels in weak rock, Fig. 4: phi 24.72, c 0.22 MPa, E 749.9 MPa, nu 0.3, r0 3 m, p0 2 MPa, pi 0:
    # p_cr 0.96 MPa, r_p 6.43 m, u 30.6 mm (the spreadsheet rounds k to 2.44)
    g = ground_reaction(2, 0, 3, 749.9, 0.3, 24.72, 0.22)
    assert mc_strength(24.72, 0.22)[0] == pytest.approx(0.69, abs=0.005)
    assert g.p_cr == pytest.approx(0.96, abs=0.01)
    assert g.r_p == pytest.approx(6.43, rel=0.01)
    assert g.u == pytest.approx(0.0306, rel=0.015)
    # elastic branch above p_cr and continuity at p_cr
    assert ground_reaction(2, 1.5, 3, 749.9, 0.3, 24.72, 0.22).r_p == 3
    lo, hi = ground_reaction(2, g.p_cr - 1e-9, 3, 749.9, 0.3, 24.72, 0.22), ground_reaction(2, g.p_cr + 1e-9, 3, 749.9, 0.3, 24.72, 0.22)
    assert lo.u == pytest.approx(hi.u, rel=1e-6)
    # inverse
    assert pressure_for_displacement(ground_reaction(2, 0.5, 3, 749.9, 0.3, 24.72, 0.22).u, 2, 3, 749.9, 0.3, 24.72, 0.22) == pytest.approx(0.5, abs=1e-6)


def test_equivalent_mohr_coulomb():
    # sigma_ci 10, mi 10, GSI 25, D 0, gamma H 2 MPa: sigma'cm 0.954, sigma'3max 0.899, phi' 30.6 deg, c' 0.159 MPa
    m = equivalent_mohr_coulomb(25, 10, 10, 10000, 2.0)
    assert m.sigma_cm == pytest.approx(0.954, abs=0.002)
    assert m.sigma3_max == pytest.approx(0.899, abs=0.002)
    assert m.phi_deg == pytest.approx(30.6, abs=0.1)
    assert m.c == pytest.approx(0.159, abs=0.002)


def test_ldp():
    # V&D 2009: at the face u0/umax = exp(-0.15 R*)/3; ahead decays with exp(x/r0); far behind tends to 1
    assert ldp(0, 5, 5) == pytest.approx(math.exp(-0.15) / 3)
    assert ldp(-5, 5, 10) == pytest.approx(math.exp(-0.3) / 3 * math.exp(-1))
    assert ldp(500, 5, 10) == pytest.approx(1.0, abs=1e-6)
    assert ldp(10, 5, 10) > ldp(10, 5, 20)  # a larger plastic zone develops more slowly behind the face


def test_squeezing():
    # Hoek & Marinos (2000) example: sigma_cm 1.01, p0 2.6 MPa -> 1.33 % (class B)
    assert squeezing_strain(1.01, 2.6) == pytest.approx(1.325, abs=0.005)
    assert squeezing_class(1.33)[0] == "B" and squeezing_class(0.5)[0] == "A" and squeezing_class(12)[0] == "E"
    assert squeezing_strain(1.01, 2.6, 0.5) < squeezing_strain(1.01, 2.6)  # support reduces closure


def test_supports_and_equilibrium():
    ring = ring_support(3.0, 0.2, 30000, 0.15, 35)
    assert ring.p_max == pytest.approx(35 / 2 * (1 - 2.8**2 / 9))
    # thin-ring limit: K -> E t / r^2
    thin = ring_support(3.0, 0.001, 30000, 0.0, 35)
    assert thin.k == pytest.approx(30000 * 0.001 / 9, rel=0.01)
    sets = steel_set_support(3.0, 1.0, 0.0125)
    assert sets.p_max == pytest.approx(1.5 * 245 * 0.0125 / 3.0)
    both = combine(ring, sets)
    assert both.k == pytest.approx(ring.k + sets.k)
    assert both.p_max <= ring.p_max + sets.p_max
    bolts = bolt_support(3.0, 12, 1.0, 3.0, 0.025, 0.18)
    assert bolts.p_max == pytest.approx(0.18 / (2 * math.pi * 3 / 12))
    # equilibrium: a stiff ring installed early carries more and closure stays below the unsupported value
    eq = support_equilibrium(2, 3, 749.9, 0.3, 24.72, 0.22, ring, 0.005)
    free = ground_reaction(2, 0, 3, 749.9, 0.3, 24.72, 0.22).u
    assert 0 < eq.pressure <= ring.p_max and eq.u < free and not eq.fails
    weak = support_equilibrium(2, 3, 749.9, 0.3, 24.72, 0.22, Support(k=5, p_max=0.05), 0.005)
    assert weak.fails


def test_shield_friction_against_ramoni_anagnostou():
    # VSS 1341 Table 5.1: D 10 m, sigma0 10 MPa, E 1 GPa, f_c 3 MPa, phi 25 deg, L 10 m: F_f* = 0.26 / 0.08 / 0 for
    # overcuts of 5 / 10 / 15 cm. This screening estimate gives 0.23 / 0.04 / 0 (documented as under-predicting).
    phi, fc = 25, 3
    c = fc * (1 - math.sin(math.radians(phi))) / (2 * math.cos(math.radians(phi)))
    star = [shield_friction(5, 10, dr, 10, 1000, 0.25, phi, c, mu=1).friction_force / (2 * math.pi * 5 * 10 * 10) for dr in (0.05, 0.10, 0.15)]
    assert star[0] == pytest.approx(0.26, abs=0.04)
    assert 0 < star[1] < 0.08
    assert star[2] == 0
    assert shield_friction(5, 10, 0.05, 10, 1000, 0.25, phi, c, mu=0.45).friction_force > shield_friction(5, 10, 0.05, 10, 1000, 0.25, phi, c, mu=0.30).friction_force


def test_gripper_pressure():
    # gripper force 2.0-3.5 x installed thrust (VSS 1341); 27.5 MN on 16.6 m^2 of shoes at factor 2 -> 3.3 MPa
    assert gripper_pressure(27.5, 16.6) == pytest.approx(3.31, abs=0.01)


def test_undrained_tresca_limit():
    # phi = 0 matches the general solution at a very small friction angle, and the Tresca plastic radius
    a = ground_reaction(0.6, 0.0, 5.5, 180.0, 0.495, 0.0, 0.3)
    b = ground_reaction(0.6, 0.0, 5.5, 180.0, 0.495, 1e-4, 0.3)
    assert a.u == pytest.approx(b.u, rel=1e-3) and a.r_p == pytest.approx(b.r_p, rel=1e-3)
    assert a.p_cr == pytest.approx(0.3)
    assert a.r_p == pytest.approx(5.5 * math.exp((0.6 - 0.3) / 0.6))
