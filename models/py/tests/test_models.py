"""Hand-checked anchor values (independent of the generated vectors)."""
import math

import pytest

from tunnelsim_models import Cutter, burland_category, cutter_forces, gaussian_trough, hoek_brown, tbm_performance


def test_hoek_brown_gsi50():
    # Hoek et al. (2002) formulas evaluated by hand: GSI 50, mi 10, D 0
    p = hoek_brown(50, 10, 100, 0, 30000)
    assert p.mb == pytest.approx(1.6767, rel=1e-4)
    assert p.s == pytest.approx(0.0038659, rel=1e-4)
    assert p.a == pytest.approx(0.50573, rel=1e-4)
    # Hoek & Diederichs (2006): Erm/Ei = 0.02 + 1/(1+exp(10/11))
    assert p.e_rm == pytest.approx(30000 * (0.02 + 1 / (1 + math.exp(10 / 11))), rel=1e-12)


def test_hoek_brown_intact_limit():
    p = hoek_brown(100, 10, 100)
    assert p.s == pytest.approx(1.0)
    assert p.mb == pytest.approx(10.0)


def test_csm_19inch_disc():
    # 19" disc, T=19 mm, S=85 mm, p=5 mm in 150 MPa / 10 MPa rock: hand calc ~ 200 kN total, RC ~ 0.10
    f = cutter_forces(5, 150, 10, Cutter())
    assert f.total_n / 1000 == pytest.approx(200.8, rel=5e-3)
    assert f.normal_n / 1000 == pytest.approx(199.8, rel=5e-3)
    assert f.rolling_coefficient == pytest.approx(math.tan(f.phi_rad / 2))
    assert f.rolling_coefficient == pytest.approx(0.102, abs=2e-3)


def test_csm_monotonic_and_inverse():
    perf = tbm_performance(12000, 6, 50, 7.0, 150, 10)
    assert perf.normal_per_cutter_kn == pytest.approx(240.0, rel=1e-6)
    assert 3 < perf.penetration_mm_rev < 10
    assert perf.rop_m_h == pytest.approx(perf.penetration_mm_rev * 0.36)
    harder = tbm_performance(12000, 6, 50, 7.0, 220, 14)
    assert harder.penetration_mm_rev < perf.penetration_mm_rev
    weak = tbm_performance(6000, 8, 40, 5.5, 60, 5, max_torque_knm=1500)
    assert weak.limited_by == "torque"
    assert weak.cutterhead_torque_knm == pytest.approx(1500, rel=1e-6)


def test_peck_trough():
    # D 6 m, z0 20 m, VL 1 %, K 0.5 -> i 10 m, Vs 0.2827 m3/m, Smax 11.28 mm
    t = gaussian_trough(6, 20, 0.01, 0.5)
    assert t.i == 10
    assert t.volume_m3_per_m == pytest.approx(0.28274, rel=1e-4)
    assert t.s_max * 1000 == pytest.approx(11.279, rel=1e-3)
    assert t.settlement(t.i) == pytest.approx(t.s_max * math.exp(-0.5))
    # Trough integrates to Vs
    dx = 0.01
    vol = sum(t.settlement(-60 + k * dx) for k in range(12001)) * dx
    assert vol == pytest.approx(t.volume_m3_per_m, rel=1e-4)
    # Half the final settlement directly above the face (Attewell & Woodman)
    assert t.settlement_3d(0, 0) == pytest.approx(t.s_max / 2)


def test_burland():
    assert burland_category(0.01) == (0, "Negligible")
    assert burland_category(0.2)[0] == 3
