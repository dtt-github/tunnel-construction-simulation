"""Slurry shield: DAUB worked example, circuit balance, deposition limit, air cushion behaviour."""
import math

import pytest

from tunnelsim_models.slurry import (
    Cushion, CushionState, discharge_density, dry_solids_flow, durand_velocity, excess_pore_pressure, face_pressure,
    forms_membrane, infiltration, penetration_at, penetration_depth, pipe_velocity, stagnation_gradient,
    theoretical_dry_flow,
)


def test_daub_example():
    # DAUB (2016) section 8.1: tau_f 0.03 kN/m^2. d10 0.15 mm: f_s0 700 kN/m^3 (membrane). d10 0.8 mm: 131 kN/m^3 and
    # e_max 0.464 / 0.541 / 0.617 m at crown / axis / invert for dp 60.8 / 70.8 / 80.8 kPa
    assert stagnation_gradient(0.03, 0.15e-3) == pytest.approx(700) and forms_membrane(0.03, 0.15e-3)
    assert stagnation_gradient(0.03, 0.8e-3) == pytest.approx(131.25) and not forms_membrane(0.03, 0.8e-3)
    for dp, e in ((60.8, 0.464), (70.8, 0.541), (80.8, 0.617)):
        assert penetration_depth(dp, 0.03, 0.8e-3) == pytest.approx(e, abs=0.002)  # DAUB rounds dp
    # factor 2 (Anagnostou & Kovari 1996) gives deeper penetration
    assert penetration_depth(60.8, 0.03, 0.8e-3, alpha=2) == pytest.approx(0.811, abs=0.001)


def test_infiltration_and_pore_pressure():
    mem = infiltration(70.8, 0.03, 0.15e-3, wedge_length=6.0)
    assert mem.membrane and mem.transfer == 1 and mem.dp_excess == 0
    pen = infiltration(70.8, 0.03, 0.8e-3, wedge_length=6.8)
    assert not pen.membrane and pen.transfer == pytest.approx(1 - 0.541 / 6.8, abs=0.001)  # DAUB AA/BB 0.92 for this case
    # partial cake between cutter passes (Krause): less penetration, part of dp stays as excess pore pressure
    part = infiltration(70.8, 0.03, 0.8e-3, wedge_length=6.8, t_between_passes=10, a_half=10)
    assert part.e_t == pytest.approx(pen.e_max / 2) and 0 < part.dp_excess < 70.8
    assert penetration_at(1e9, 1.0, 10) == pytest.approx(1.0, abs=1e-6)
    lam = math.sqrt(1e-4 * 10 * 1e6)
    assert excess_pore_pressure(lam, 30, 1e-4, 10, 1e6) == pytest.approx(30 / math.e)


def test_slurry_circuit():
    # 7.08 m at 40 mm/min, feed 900 m^3/h at 1.05 t/m^3, in-situ 2.0 t/m^3: discharge 994.5 m^3/h at ~1.14 t/m^3,
    # dry solids ~57.3 m^3/h, equal to the theoretical value (no over-excavation)
    area, v = math.pi * 7.08**2 / 4, 0.040 / 60
    qf = 900 / 3600
    qd, rho_d = discharge_density(qf, 1.05, area, v, 2.0)
    assert qd * 3600 == pytest.approx(994.5, abs=0.5) and rho_d == pytest.approx(1.14, abs=0.005)
    assert dry_solids_flow(qf, 1.05, qd, rho_d) * 3600 == pytest.approx(57.3, abs=0.2)
    assert dry_solids_flow(qf, 1.05, qd, rho_d) == pytest.approx(theoretical_dry_flow(area, v, 2.0))
    # Durand limit for DN300 with sand in water ~4.2 m/s; 1000 m^3/h in DN300 runs at ~3.9 m/s
    assert durand_velocity(0.3) == pytest.approx(4.18, abs=0.02)
    assert pipe_velocity(1000 / 3600, 0.3) == pytest.approx(3.93, abs=0.01)


def test_air_cushion():
    c = Cushion(chamber_area=12.0)
    st = CushionState(p_air=200.0, level=0.5, air_volume=20.0)
    same = c.step(st, 1.0, 0.25, 0.0, 0.25, 200.0)
    assert same.p_air == pytest.approx(200.0) and same.level == pytest.approx(0.5)
    # more in than out: the level rises and the air compresses, the regulator pulls the pressure back
    up = st
    for _ in range(10):
        up = c.step(up, 1.0, 0.25, 0.04, 0.25, 200.0)
    assert up.level > 0.5 and 200.0 < up.p_air < 210.0
    assert face_pressure(200, 0.5, -3.5, 11) == pytest.approx(200 + 11 * 4.0)
