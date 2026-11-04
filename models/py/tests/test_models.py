"""Hand-checked anchor values (independent of the generated vectors)."""
import math

import pytest

from tunnelsim_models import (
    METHOD_PRESETS,
    Cutter,
    burland_category,
    cutter_forces,
    gaussian_trough,
    hoek_brown,
    preset_trough,
    tbm_performance,
    twin_troughs,
    volume_loss_components,
)


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


def _integrate(f, lo=-150.0, hi=150.0, dx=0.01):
    n = int((hi - lo) / dx)
    return sum(f(lo + k * dx) for k in range(n + 1)) * dx


def test_asymmetric_trough_keeps_volume():
    t = gaussian_trough(6, 20, 0.01, 0.5, k_left=0.8, k_right=0.4)
    assert (t.i_left, t.i_right) == (16, 8)
    assert t.i == 12
    assert _integrate(t.settlement) == pytest.approx(t.volume_m3_per_m, rel=1e-4)
    # continuous at the axis, and the wider arm carries more of the volume
    assert t.settlement(-1e-9) == pytest.approx(t.settlement(0))
    assert _integrate(t.settlement, -150, 0) > _integrate(t.settlement, 0, 150)


def test_longitudinal_components():
    # single component at the face: Attewell & Woodman, half the final settlement above the face
    assert gaussian_trough(6, 20, 0.01).fraction_at_face == pytest.approx(0.5)
    # tail-void-only loss L behind the face: Phi(-L / i)
    t = gaussian_trough(6, 20, 0.01, components=[(1.0, 9.0)])
    assert t.fraction_at_face == pytest.approx(0.5 * (1 + math.erf(-9 / 10 / math.sqrt(2))))
    assert t.longitudinal_fraction(9.0) == pytest.approx(0.5)
    assert t.longitudinal_fraction(200) == pytest.approx(1.0)
    comps = volume_loss_components(1, 1, 2, 8.0)
    assert comps == [(0.25, 0.0), (0.25, 4.0), (0.5, 8.0)]
    # behind-the-tail component: default one shield length behind the tail
    assert volume_loss_components(0, 0, 1, 8.0, behind=1) == [(0.5, 8.0), (0.5, 16.0)]
    assert volume_loss_components(1, 0, 0, 8.0, behind=1, behind_offset_m=4.0) == [(0.5, 0.0), (0.5, 12.0)]
    with pytest.raises(ValueError):
        volume_loss_components(1, 1, 1, 8.0, behind=-0.5)
    with pytest.raises(ValueError):
        gaussian_trough(6, 20, 0.01, components=[(0.5, 0.0), (0.4, 5.0)])


def test_presets_order_fraction_at_face():
    # moving volume loss from the face to the tail lowers the fraction developed when the face passes
    open_face = preset_trough("open_face_stiff_clay", 5, 20, shield_length_m=7)
    closed = preset_trough("closed_face_clay", 5, 20, shield_length_m=7)
    assert closed.fraction_at_face < open_face.fraction_at_face < 0.5
    # closed face: only a small part of the final trough has formed when the face passes
    epb = preset_trough("closed_face_clay", 6, 20, shield_length_m=9)
    assert 0.1 < epb.fraction_at_face < 0.2
    assert open_face.volume_m3_per_m == pytest.approx(METHOD_PRESETS["open_face_stiff_clay"]["volume_loss"] * math.pi * 25 / 4)
    for p in METHOD_PRESETS.values():
        lo, hi = p["range"]
        assert lo <= p["volume_loss"] <= hi


def test_twin_superposition_and_interaction():
    plain = twin_troughs(5, 19.5, 26, 0.006)
    a = gaussian_trough(5, 19.5, 0.006)
    for x in (-20.0, 0.0, 13.0, 26.0, 40.0):
        assert plain.settlement(x) == pytest.approx(a.settlement(x) + a.settlement(x - 26))
    # widening the inner arm keeps the second tunnel's volume and moves its centroid towards the first tunnel
    for sp in (26.0, -26.0):
        tw = twin_troughs(5, 19.5, sp, 0.006, second_inner_k=0.9)
        s2 = lambda x: tw.second.settlement(x - sp)  # noqa: E731
        vol = _integrate(s2)
        assert vol == pytest.approx(tw.second.volume_m3_per_m, rel=1e-4)
        centroid = _integrate(lambda x: x * s2(x)) / vol
        assert abs(centroid) < abs(sp)
        assert tw.settlement(sp / 2) > plain.settlement(sp / 2) if sp > 0 else True
    more = twin_troughs(5, 19.5, 26, 0.006, second_vl_factor=1.3)
    assert more.second.volume_m3_per_m == pytest.approx(1.3 * a.volume_m3_per_m)


def test_burland():
    assert burland_category(0.01) == (0, "Negligible")
    assert burland_category(0.2)[0] == 3
