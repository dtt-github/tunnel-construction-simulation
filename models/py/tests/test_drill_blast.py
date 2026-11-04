"""Drill & blast: round design against Yilmaz (2023), vibration against SS 460 48 66 tables and the Northern Link fit,
cycle against NFF figures for Norwegian road tunnels."""
import math

import pytest

from tunnelsim_models import drill_blast as db


def test_yilmaz_worked_example():
    qb = db.bottom_charge(38, 1.5, 0.8)
    assert qb == pytest.approx(1.36, abs=0.005)
    assert db.burden(38, qb) == pytest.approx(1.07, abs=0.005)
    # first cut burden with drilling deviation (Karadon example, H = 2.85 m)
    assert db.first_cut_burden(0.076, 2.85, 0.02, 0.02) == pytest.approx(0.052, abs=0.001)
    assert db.first_cut_burden(0.115, 2.85, 0.02, 0.02) == pytest.approx(0.1185, abs=0.001)
    # V-cut example (Table 5): 32 mm, emulsion 1.1 g/cm^3, AWS 0.56
    qv = db.bottom_charge(32, 1.1, 0.56)
    assert qv == pytest.approx(0.495, abs=0.002)
    assert db.burden(32, qv) == pytest.approx(0.46, abs=0.005)


def test_pull_from_empty_holes():
    assert db.hole_depth(0.102) == pytest.approx(3.218, abs=0.001)
    assert db.advance(db.hole_depth(0.127)) == pytest.approx(3.653, abs=0.001)
    # four 102 mm reamed holes (equivalent 204 mm) pull a 5.2 m round; three do not
    assert db.empty_holes_for_depth(5.2) == 4
    with pytest.raises(ValueError):
        db.hole_depth(0.3)


def test_cut_follows_dyno_table():
    # 102 mm empty hole: first square side 210 mm in the Dyno Nobel table (p. 15; a = 150 mm rounded)
    w = db.cut_sections(0.102, 10.0)
    assert w[0] == pytest.approx(0.210, abs=0.01)
    assert w[1] / w[0] == pytest.approx(1.5 * math.sqrt(2))


def test_round_matches_norwegian_practice():
    rd = db.design_round(10.6, 2.9, 5.2)  # T10.5 profile, about 75 m^2
    assert rd.area == pytest.approx(74.6, abs=0.5)
    contour = sum(1 for h in rd.holes if h.kind == "contour")
    assert 45 <= contour <= 50  # Jakobsen et al. 2024
    assert 126 <= rd.n_charged <= 158
    assert 1.2 < rd.specific_charge < 2.5
    tb = db.design_round(10.6, 2.9, 5.2, design="textbook")
    assert tb.n_charged < rd.n_charged


def test_vibration():
    assert db.max_charge_per_delay(50, 20) == pytest.approx(14.2, abs=0.05)
    assert db.max_charge_per_delay(30, 10) == pytest.approx(2.08, abs=0.02)
    assert db.ppv(50, db.max_charge_per_delay(50, 20)) == pytest.approx(20)
    # SS 460 48 66, rock: 51 / 43 / 26 mm/s at 20 / 30 / 100 m for v0 = 70 (Solna risk analysis)
    assert [round(db.ss4604866_limit(d)) for d in (20, 30, 100)] == [51, 43, 26]
    assert db.ss4604866_limit(1000) == db.ss4604866_limit(350)


def test_kuz_ram():
    x50 = db.kuz_ram_x50(7, 0.6, 34.79)
    assert x50 == pytest.approx(20.8, abs=0.05)
    n = db.uniformity_index(2.5, 2.44, 89, 0.1, 8, 9.5)
    assert n == pytest.approx(1.153, abs=0.001)  # by hand from the 1987 formula
    assert db.retained(x50, x50, n) == pytest.approx(0.5, abs=0.001)


def test_cycle_against_nff():
    rd = db.design_round(10.6, 2.9, 5.2)
    good = db.round_cycle(rd, 10.6, 2.9, "I")
    d_c_b = sum(h for a, h in good.steps if a in ("Drilling", "Charging", "Connect and blast"))
    assert 4.0 <= d_c_b <= 5.0  # NFF Publication 14: drill, charge and blast 4-5 h
    assert 10 <= good.total_h <= 12.5  # about 12 h per round
    assert 40 <= good.m_per_week <= 80  # 40-80 m per week per face (NFF Publication 23)
    weeks = [db.round_cycle(rd, 10.6, 2.9, c).m_per_week for c in ("I", "II", "III", "IV")]
    assert weeks == sorted(weeks, reverse=True)
    assert db.overbreak_percent(86.0, 74.6) == pytest.approx(15.28, abs=0.01)
