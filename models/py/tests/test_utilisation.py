"""Utilisation model: distributions, deterministic limits, and plausibility against published rates."""
import math
import statistics

import pytest

from tunnelsim_models.utilisation import (
    DIST, EPB_WEEKLY_SURVEY, DriveSettings, Rng, median, normal_inv, record_check, sample, simulate_drive,
)

FIXED = lambda v: {"kind": "fixed", "value": v}  # noqa: E731


def test_rng_reproducible_and_in_range():
    a, b = Rng(7), Rng(7)
    xs = [a.uniform() for _ in range(1000)]
    assert xs == [b.uniform() for _ in range(1000)]
    assert 0 < min(xs) and max(xs) < 1
    assert statistics.mean(xs) == pytest.approx(0.5, abs=0.03)


def test_normal_inverse():
    assert normal_inv(0.5) == pytest.approx(0.0, abs=1e-12)
    assert normal_inv(0.975) == pytest.approx(1.959964, abs=1e-6)
    assert normal_inv(0.001) == pytest.approx(-3.090232, abs=1e-6)


def test_distribution_medians_and_shapes():
    assert median(DIST["ring_build"]) == pytest.approx(9.0618 + math.exp(2.123))  # ~17.4 min
    assert median(DIST["boring"]) == pytest.approx(16.368 + 17.769)  # ~34 min, inside the measured 22-125 min
    assert median(DIST["stop_hours"]) == pytest.approx(105.11)
    w = DIST["rings_between_stops"]
    assert median(w) == pytest.approx(w["lam"] * math.log(2) ** (1 / w["k"]))
    t = DIST["train_delay"]
    assert sample(t, (t["m"] - t["a"]) / (t["b"] - t["a"])) == pytest.approx(t["m"])  # CDF at the mode
    assert sample(t, 1e-12) == pytest.approx(t["a"], abs=1e-3) and sample(t, 1 - 1e-12) == pytest.approx(t["b"], abs=1e-3)


def test_deterministic_cycle():
    # 20 min boring + 30 min build, no other activities, no maintenance: 1.5 m per 50 min
    s = DriveSettings(ring_length=1.5, boring_min=20, ring_build=FIXED(30), general=FIXED(0), shift_pattern="idealised_24h",
                      interventions=False)
    r = simulate_drive(s, days=10)
    assert r.rings == 288
    assert r.mean_m_per_day == pytest.approx(43.2)
    assert r.utilisation == pytest.approx(0.4)
    # a 4 h maintenance shift removes a sixth of the production time
    s.shift_pattern = "2x10h_plus_4h_maintenance"
    r2 = simulate_drive(s, days=10)
    assert r2.mean_m_per_day == pytest.approx(43.2 * 20 / 24, rel=0.02)
    assert r2.shares["maintenance_shift_and_idle"] == pytest.approx(4 / 24, abs=0.01)


def test_interventions_and_haulage_slow_the_drive():
    base = DriveSettings(boring_min=25, interventions=False)
    fast = statistics.mean(simulate_drive(base, days=120, seed=s).mean_m_per_day for s in range(1, 6))
    stops = statistics.mean(simulate_drive(DriveSettings(boring_min=25), days=120, seed=s).mean_m_per_day for s in range(1, 6))
    rail = statistics.mean(simulate_drive(DriveSettings(boring_min=25, haulage="rail", interventions=False), days=120, seed=s).mean_m_per_day
                           for s in range(1, 6))
    assert stops < fast and rail < fast


def test_default_epb_is_plausible():
    # default urban EPB (2 x 10 h + 4 h maintenance, conveyor, tool interventions): weekly mean within two standard
    # deviations of the 40-EPB survey, best day and month below the best published EPB references
    runs = [simulate_drive(DriveSettings(), days=90, seed=s) for s in range(1, 11)]
    wk = statistics.mean(r.mean_m_per_week for r in runs)
    assert abs(wk - EPB_WEEKLY_SURVEY["mean"]) < 2 * EPB_WEEKLY_SURVEY["sd"]
    for r in runs:
        chk = record_check(7.08, r.best_day, r.best_week, r.best_month)
        assert not any(v["above_world_record"] for v in chk.values())
        assert not chk["day"]["above_epb_reference"] and not chk["month"]["above_epb_reference"]
        assert 0.1 < r.utilisation < 0.45


def test_record_check_flags():
    chk = record_check(7.08, 130, 600, 2000)
    assert all(v["above_world_record"] for v in chk.values())  # 7.01-8 m class: 115.7 / 428 / 1482
    assert chk["day"]["world_record"] == 115.7
    chk = record_check(6.5, 45, 100, 500)
    assert chk["day"]["above_epb_reference"] and not chk["day"]["above_world_record"]
    assert record_check(15, 10, 10, 10)["day"]["world_record"] is None
