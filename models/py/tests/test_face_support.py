"""Face support: limiting cases and hand checks (independent of the generated vectors)."""
import math

import pytest

from tunnelsim_models import daub_window, silo_stress, vermeer_limit, wedge_silo


def test_silo_limits():
    # deep silo tends to (r gamma - c) / (K tan phi); shallow silo is the overburden
    r = 5 * 3 / (2 * 8)
    assert silo_stress(1e4, 5, 3, 20, 0, 30) == pytest.approx(r * 20 / (0.8 * math.tan(math.radians(30))))
    assert silo_stress(1e-6, 5, 3, 20, 0, 30, q=7) == pytest.approx(7, abs=1e-4)
    # no friction: plain overburden minus cohesion on the walls
    assert silo_stress(4, 6, 6, 18, 0, 0, q=10) == pytest.approx(10 + 18 * 4)


def test_vermeer_hand():
    # D 10, gamma 20, phi 30: 200 * (1 / (9 * 0.57735) - 0.05) = 28.49 kPa
    assert vermeer_limit(10, 20, 30) == pytest.approx(28.49, abs=0.01)


def test_wedge_silo_vs_vermeer_dry_sand():
    # limit equilibrium is an upper-bound style estimate: at or a little above the FE-based Vermeer fit
    for phi in (25, 30, 35, 40):
        ratio = wedge_silo(10, 15, 20, phi).s_eff / vermeer_limit(10, 20, phi)
        assert 1.0 <= ratio <= 1.3, (phi, ratio)


def test_wedge_silo_trends():
    base = wedge_silo(8, 12, 20, 30).s_eff
    assert wedge_silo(8, 12, 20, 35).s_eff < base  # stronger ground needs less support
    assert wedge_silo(8, 12, 20, 30, 5).s_eff < base
    assert wedge_silo(8, 24, 20, 30).s_eff == pytest.approx(base, rel=0.1)  # arching: nearly cover-independent
    assert wedge_silo(8, 12, 20, 0, 40).s_eff < 0  # stiff undrained clay stands unsupported
    # theta from the optimiser is a maximum of S
    fs = wedge_silo(8, 12, 20, 30)
    assert 45 < fs.theta_deg < 80


def test_daub_window():
    fs = wedge_silo(8, 12, 20, 30, water_depth=3)
    assert fs.u_crown == pytest.approx(90) and fs.u_axis == pytest.approx(130)
    w = daub_window(fs, 8, 12, 20, water_depth=3)
    assert w.overburden_crown == pytest.approx(20 * 3 + 20 * 9)
    assert w.p_min_axis == pytest.approx(1.5 * fs.s_eff + 1.05 * 130)
    assert w.p_max_crown == pytest.approx(0.9 * 240)
    assert w.p_min_crown == pytest.approx(w.p_min_axis - 4 * 12)
    assert w.feasible
    # very shallow cover under high water: the window closes
    shallow = wedge_silo(8, 0.5, 20, 30, water_depth=0)
    assert not daub_window(shallow, 8, 0.5, 20, water_depth=0).feasible


def test_river_above_the_ground():
    # 8 m of river over the bed: pore pressure and total overburden both carry the water column
    fs = wedge_silo(7, 10, 20, 35, water_depth=-8)
    assert fs.u_axis == 10 * (10 + 3.5 + 8)
    w = daub_window(fs, 7, 10, 20, water_depth=-8)
    assert w.overburden_crown == (10 + 10) * 10 + 10 * 8
    dry_river = daub_window(fs, 7, 10, 20, water_depth=0)
    assert w.overburden_crown - dry_river.overburden_crown == 80
