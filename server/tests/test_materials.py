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
