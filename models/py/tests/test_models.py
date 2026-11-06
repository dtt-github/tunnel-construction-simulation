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
    f = cutter_forces(5, 150, 10, Cutter(psi=0.1))
    assert f.total_n / 1000 == pytest.approx(200.8, rel=5e-3)
    assert f.normal_n / 1000 == pytest.approx(199.8, rel=5e-3)
    assert f.rolling_coefficient == pytest.approx(math.tan(f.phi_rad / 2))
    assert f.rolling_coefficient == pytest.approx(0.102, abs=2e-3)


def test_csm_follo_tbm1():
    # Hansen (2018) Table 5.1: 5.08 rpm, 21217 kN gross (3200 kN shield drag), 6.32 mm/rev, 1.92 m/h; Table 2.4: 71 discs
    perf = tbm_performance(21216.91 - 3200, 5.08, 71, 9.96, 152.45, 10.38, cutter=Cutter(spacing_mm=4980 / 71),
                           max_torque_knm=11115, max_power_kw=4550)
    assert perf.penetration_mm_rev == pytest.approx(6.32, rel=0.02)
    assert perf.rop_m_h == pytest.approx(1.92, rel=0.03)


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
    # longitudinal width: a narrower i_long steepens the profile but leaves the final trough unchanged
    narrow = gaussian_trough(6, 20, 0.01, components=[(1.0, 9.0)], i_long=5.0)
    assert narrow.fraction_at_face == pytest.approx(0.5 * (1 + math.erf(-9 / 5 / math.sqrt(2))))
    assert narrow.fraction_at_face < t.fraction_at_face
    assert narrow.settlement(3.0) == pytest.approx(t.settlement(3.0))
    with pytest.raises(ValueError):
        gaussian_trough(6, 20, 0.01, i_long=0.0)
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


def test_twin_hyde_park_second_bore():
    # Wan et al. (2017) X-line, second bore incremental: VL 1.18 %, Ky 0.467 towards the first bore; 16.2 m apart
    tw = twin_troughs(7.1, 34.5, 16.2, 0.0078, 0.0118, 0.44, second_inner_k=0.467, second_outer_k=0.38)
    v2 = 0.0118 * math.pi * 7.1**2 / 4
    assert tw.second.s_max == pytest.approx(2 * v2 / (math.sqrt(2 * math.pi) * (0.467 + 0.38) * 34.5))
    assert tw.second.settlement(-5) > tw.second.settlement(5)  # wider towards the first bore (x < 0 from the second)
    assert tw.second.volume_m3_per_m == pytest.approx(v2, rel=1e-9)


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


def test_tbm_drive_and_penetration_limits():
    # weak rock: thrust alone would push penetration to the solver bound; the cap holds it and reports unused thrust
    free = tbm_performance(11000, 6, 50, 7.0, 40, 4)
    capped = tbm_performance(11000, 6, 50, 7.0, 40, 4, max_penetration_mm=12.0)
    assert free.penetration_mm_rev > 12
    assert capped.penetration_mm_rev == pytest.approx(12.0) and capped.limited_by == "penetration"
    assert capped.thrust_used_kn < 11000
    assert capped.normal_per_cutter_kn * 50 == pytest.approx(capped.thrust_used_kn)
    # constant power above the base speed: available torque = P / omega
    fast = tbm_performance(15000, 9, 50, 7.0, 140, 10, max_torque_knm=4200, max_power_kw=2500)
    assert fast.torque_available_knm == pytest.approx(2500 * 60 / (2 * math.pi * 9))
    assert fast.limited_by == "power"
    assert fast.cutterhead_power_kw == pytest.approx(2500, rel=1e-6)
    slow = tbm_performance(15000, 4, 50, 7.0, 140, 10, max_torque_knm=4200, max_power_kw=2500)
    assert slow.torque_available_knm == 4200  # below the base speed the installed torque governs


def test_macklin_volume_loss():
    from tunnelsim_models import critical_stability_ratio, face_volume_loss, load_factor, macklin_volume_loss

    # Macklin (1999) as quoted by Divall et al. (2023): VL (%) = 0.23 exp(4.4 LF)
    assert macklin_volume_loss(0.2) == pytest.approx(0.0023 * math.exp(0.88))
    assert macklin_volume_loss(0.5) == pytest.approx(0.0208, rel=1e-2)
    # Kimura & Mair (1981), heading supported to the face: 7.05 at C/D 1.5, 9.0 at 3.0, constant beyond
    assert critical_stability_ratio(1.5) == pytest.approx(7.05)
    assert critical_stability_ratio(3.0) == critical_stability_ratio(5.0) == pytest.approx(9.0)
    assert critical_stability_ratio(2.25) == pytest.approx(8.025)
    # a well-supported face keeps the measured volume loss; dropping the support raises it
    lf_on = load_factor(600, 220, 235, 3.7)
    lf_off = load_factor(600, 0, 235, 3.7)
    assert face_volume_loss(0.005, lf_on) == pytest.approx(0.005, abs=3e-4)
    assert face_volume_loss(0.005, lf_off) > 0.007
    assert load_factor(600, 700, 235, 3.7) == 0.0  # support above the overburden: no driving stress


def test_deflection_modification_factor():
    from tunnelsim_models import deflection_modification_factor, deflection_ratios, frame_bending_stiffness, gaussian_trough

    # Mair (1997) Fig. 4 as digitised: flexible about 1.4, stiff about 0.1 (sag) and 0.17 (hog)
    assert deflection_modification_factor("sag", 1e-8, 0.0) == pytest.approx(1.40)
    assert deflection_modification_factor("sag", 10, 0.0) == pytest.approx(0.096)
    assert deflection_modification_factor("hog", 10, 0.0) == pytest.approx(0.168)
    # hogging stiffens over a narrow range; eccentric buildings need more stiffness to reach the same M
    assert deflection_modification_factor("hog", 1e-3, 0.0) < deflection_modification_factor("hog", 1e-3, 0.6)
    assert deflection_modification_factor("sag", 1e-4, 0.6) < deflection_modification_factor("sag", 1e-4, 0.0)
    # slabs about mid-height: more storeys, much stiffer
    assert frame_bending_stiffness(9) > 5 * frame_bending_stiffness(4)
    # a footprint centred over the trough is all sagging; one beyond the inflection point is mostly hogging
    t = gaussian_trough(7.08, 30, 0.005, 0.5)
    centred = deflection_ratios(t.settlement, -10, 10, t.i, t.i)
    assert centred["hog"] is None and centred["sag"][0] == 20
    side = deflection_ratios(t.settlement, 20, 40, t.i, t.i)
    assert side["sag"] is None and side["hog"][1] > 0


def test_strain_modification_factor():
    from tunnelsim_models import frame_axial_stiffness, relative_axial_stiffness, strain_modification_factor

    # Potts & Addenbrooke (1996) Fig. 5 as digitised: at most about 0.11 of greenfield, falling to 0 for stiff buildings
    assert strain_modification_factor("comp", 0.316, 0.0) == pytest.approx(0.113)
    assert strain_modification_factor("tens", 1.0, 0.6) == pytest.approx(0.065)
    assert strain_modification_factor("tens", 1000, 0.0) == 0.0
    assert all(strain_modification_factor(m, a, e) <= 0.113 for m in ("comp", "tens") for a in (0.01, 0.5, 3) for e in (0, 0.3, 0.7))
    # tension grows with eccentricity, compression falls
    assert strain_modification_factor("tens", 2, 0.6) > strain_modification_factor("tens", 2, 0.0)
    assert strain_modification_factor("comp", 2, 0.6) < strain_modification_factor("comp", 2, 0.0)
    # slabs acting together: a 4-storey frame on 20 m in stiff clay is axially stiff (alpha* far above 0.5)
    assert relative_axial_stiffness(frame_axial_stiffness(4), 77.6e3, 20.0) > 10


def test_practice_specific_charge():
    from tunnelsim_models import design_round, practice_specific_charge

    lo, hi = practice_specific_charge(74.59)  # Gjengedal & Jakobsen (2025) road-tunnel trends at the T10.5 area
    assert (round(lo, 2), round(hi, 2)) == (2.67, 3.01)
    assert practice_specific_charge(74.59, road_only=False)[0] < 2.1  # the urban tunnel with blasting limits
    # the demo's Norwegian-practice round charges less than the road tunnels logged in 2021-2024
    assert design_round(10.6, 2.9, 5.2).specific_charge < 0.7 * lo


def test_learning_curve():
    from tunnelsim_models.utilisation import LEARNING_DAYS_BARCELONA, DriveSettings, simulate_drive

    kw = {"shift_pattern": "2x12h_maintenance_per_cycle", "boring_min": 26.7, "ring_length": 1.6,
          "ring_build": {"kind": "fixed", "value": 32.0}, "interventions": False}
    steady = simulate_drive(DriveSettings(**kw), days=180, seed=3)
    learn = simulate_drive(DriveSettings(**kw, learning_days=LEARNING_DAYS_BARCELONA), days=180, seed=3)
    # a slower start, the same steady rate once learnt (no randomness without interventions and with fixed times)
    assert learn.metres < steady.metres
    first = simulate_drive(DriveSettings(**kw, learning_days=LEARNING_DAYS_BARCELONA), days=30, seed=3)
    assert first.mean_m_per_day < 0.7 * steady.mean_m_per_day
    assert learn.best_day == pytest.approx(steady.best_day, rel=0.15)


def test_day_variation():
    from tunnelsim_models.utilisation import DAY_VARIATION_CROSSRAIL_EPB, DriveSettings, simulate_drive

    kw = {"shift_pattern": "2x12h_maintenance_per_cycle", "boring_min": 26.7, "ring_length": 1.6,
          "ring_build": {"kind": "fixed", "value": 32.0}, "interventions": False}
    flat = [simulate_drive(DriveSettings(**kw), 360, s) for s in range(1, 6)]
    var = [simulate_drive(DriveSettings(**kw, **DAY_VARIATION_CROSSRAIL_EPB), 360, s) for s in range(1, 6)]
    mean = lambda rs, k: sum(getattr(r, k) for r in rs) / len(rs)
    # the mean day is kept within a few per cent; best day and week rise to about 3x and 2x the mean (Crossrail)
    assert mean(var, "mean_m_per_day") == pytest.approx(mean(flat, "mean_m_per_day"), rel=0.05)
    assert 2.4 < mean(var, "best_day") / mean(var, "mean_m_per_day") < 3.6
    assert 1.6 < mean(var, "best_week") / (7 * mean(var, "mean_m_per_day")) < 2.4
    assert mean(flat, "best_day") / mean(flat, "mean_m_per_day") < 1.3
