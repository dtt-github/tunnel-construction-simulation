"""Material mapping: Mohr-Coulomb to Newton's Drucker-Prager cone (see materials.py)."""
import math

import pytest

from tunnelsim_server import materials as m


def test_plane_strain_and_triaxial_mapping():
    assert m.mu_plane_strain(34.0) == pytest.approx(math.sin(math.radians(34.0)))
    assert m.phi_from_mu_plane_strain(m.mu_plane_strain(30.0)) == pytest.approx(30.0)
    # mu = 0.75 (Phase 0) is 48.6 deg in plane strain and 32.3 deg in triaxial compression
    assert m.phi_from_mu_plane_strain(0.75) == pytest.approx(48.59, abs=0.01)
    s = 3 * 0.75 / (2 * math.sqrt(3) + 0.75)
    assert m.mu_triaxial_compression(math.degrees(math.asin(s))) == pytest.approx(0.75)


def test_rankine_jaky_poisson():
    assert m.rankine_ka(30.0) == pytest.approx(1 / 3)
    assert m.jaky_k0(30.0) == pytest.approx(0.5)
    nu = m.poisson_for_k0(0.5)
    assert nu / (1 - nu) == pytest.approx(0.5)


def test_soils():
    sand = m.drained_sand("s", 1600, 34.0, 5e6, "test", cohesion=2000.0)
    assert sand.friction == pytest.approx(math.sin(math.radians(34)))
    assert sand.yield_stress == pytest.approx(2000 * math.cos(math.radians(34)))
    clay = m.undrained_clay("c", 2000, 100e3, 50e6, "test")
    assert clay.friction == 0.0 and clay.yield_stress == 100e3
    # the Phase 0 sand keeps Newton's defaults, so the golden face test is unchanged
    assert m.PHASE0_SAND.young_modulus == 1.0e15 and m.PHASE0_SAND.yield_stress == 0.0


def test_dilatancy_mapping_round_trip():
    # (phi', psi) -> (mu, theta) -> (phi', psi); psi = 0 is the WP1 mapping
    for phi, psi in ((34.0, 0.0), (34.0, 4.7), (30.0, 10.0), (40.0, 20.0)):
        mu, theta = m.plane_strain_dp(phi, psi)
        back = m.plane_strain_mc(mu, theta)
        assert back[0] == pytest.approx(phi, abs=1e-6) and back[1] == pytest.approx(psi, abs=1e-6)
    assert m.plane_strain_dp(34.0, 0.0) == (pytest.approx(math.sin(math.radians(34))), 0.0)
    # theta = 1 (associated) with mu 0.5592 is phi = psi = 36.2 deg, not 34 deg
    phi, psi = m.plane_strain_mc(0.5592, 1.0)
    assert phi == pytest.approx(psi) and phi == pytest.approx(36.22, abs=0.01)


def test_bolton_idinger():
    # Idinger et al. (2011): e 0.77, emin 0.61, emax 0.84 -> Dr 0.304; p' about 69 kPa at the axis
    assert m.bolton_psi(0.304, 69.0) == pytest.approx(4.71, abs=0.01)
    assert m.bolton_psi(0.0, 100.0) == 0.0  # I_R clipped at 0
    assert m.bolton_psi(1.0, 1.0) == pytest.approx(25.0)  # I_R clipped at 4
