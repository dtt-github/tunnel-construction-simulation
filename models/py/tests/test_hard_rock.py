"""Hard-rock drive: cutter wear, support, utilisation against Farrokh's worked example; speed limit; drive."""
import math

import pytest

from tunnelsim_models import max_rpm
from tunnelsim_models.hard_rock import (
    cutter_change_h_per_km, cutter_downtime_farrokh, cutter_life_m3, cutters_per_km, hard_rock_utilisation, rmr_class,
    rmr_from_gsi, support_downtime,
)


def test_gauge_speed_limit():
    # Rostami & Chang (2017): rpm = V_L / (pi D); 19-inch 200 m/min, 17-inch 165 m/min
    assert max_rpm(10.0) == pytest.approx(200 / (math.pi * 10))  # 6.37 rpm
    assert max_rpm(7.0, 432) == pytest.approx(165 / (math.pi * 7))
    # Niagara (14.4 m, 20-inch gauge discs) ran up to 5 rpm, slightly above this 4.4 rpm guide: a design guide, not a bound
    assert max_rpm(14.4) == pytest.approx(4.42, abs=0.01)


def test_cutter_wear():
    assert cutter_life_m3(2) == pytest.approx(513)
    assert cutters_per_km(3.9, 2) == pytest.approx(1000 * math.pi * 3.9**2 / 4 / 513)  # ~23.3
    # wear model against Farrokh's low-quartz fit (30 h/km): same order
    assert cutter_change_h_per_km(3.9, 2) == pytest.approx(25.6, abs=0.1)
    assert cutter_downtime_farrokh(4.7, 3) == 30
    assert cutter_downtime_farrokh(2.5, 15) > cutter_downtime_farrokh(5.0, 15)  # slower boring, more cutter time per km


def test_support_classes_and_downtime():
    assert rmr_class(85)["class"] == "I" and rmr_class(45)["class"] == "III" and rmr_class(10)["class"] == "V"
    assert rmr_from_gsi(55) == 60
    # open TBM: worse rock, more support time; larger diameter, more support time
    assert support_downtime(40, 10) > support_downtime(40, 4) > support_downtime(70, 4)
    assert support_downtime(85, 8) == 0
    # double shield builds segments while boring: ~100 h/km in fair to good rock, single-shield mode below RMR 50
    assert support_downtime(60, 10, "double") == 100
    assert support_downtime(30, 10, "double") == support_downtime(30, 10, "single")


def test_farrokh_worked_example():
    # Farrokh (2018): open TBM 3.9 m, PR 4.7 m/h, stroke 1.25 m, regrip 4 min, rail, quartz < 5 %, RMR 45:
    # 1021 h/km, U = 21 %, AR = 23.5 m/day (support read from a digitised figure, hence a small difference)
    r = hard_rock_utilisation(4.7, 3.9, stroke_m=1.25, regrip_min=4, ucs_mpa=90, rmr=45, haulage="rail", quartz_percent=3,
                              maintenance="good", transport="normal", utilities=40, survey=0, other=0)
    assert r.h_per_km["boring"] == pytest.approx(212.8, abs=0.1)
    assert r.h_per_km["regrip"] == pytest.approx(53.3, abs=0.1)
    assert r.total_h_per_km == pytest.approx(1021, rel=0.03)
    assert r.utilisation == pytest.approx(0.21, abs=0.01)
    assert r.advance_m_day == pytest.approx(23.5, abs=0.6)


def test_double_shield_and_curves():
    base = hard_rock_utilisation(3.0, 10, rmr=60)
    ds = hard_rock_utilisation(3.0, 10, rmr=60, machine="double", stroke_m=1.8, regrip_min=10)
    assert ds.h_per_km["regrip"] == pytest.approx(1000 * 10 / (60 * 1.8))  # boring stops for each regrip
    assert ds.h_per_km["support"] < base.h_per_km["support"]  # segments built while boring
    assert ds.advance_m_day > base.advance_m_day
    curved = hard_rock_utilisation(3.0, 10, rmr=60, curve_radius_m=300)
    assert curved.h_per_km["regrip"] == pytest.approx(base.h_per_km["regrip"] + 409000 / 300**2)
