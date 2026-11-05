"""Scenario files: interpolation between boreholes, absent and unreached units, face averages."""
import json

import pytest

from tunnelsim_models.scenario import FORMAT, Scenario

UNITS = {
    "MG": {"name": "Made Ground", "gamma": 19, "phi": 25, "c": 0, "k0": 0.5, "E": 10000},
    "TG": {"name": "Terrace gravel", "gamma": 20, "phi": 35, "c": 0, "k0": 0.45, "E": 40000},
    "LC": {"name": "London Clay", "gamma": 20, "phi": 23, "c": 5, "k0": 1.5, "E": 60000},
    "LM": {"name": "Lambeth Group", "gamma": 20.5, "phi": 26, "c": 10, "k0": 1.2, "E": 80000},
}


def make(boreholes, water=((0, 5.0), (1000, 5.0))):
    return Scenario({
        "format": FORMAT, "name": "test", "units": UNITS,
        "alignment": {"length": 1000, "axis_level": [[0, -15.0], [1000, -15.0]]},
        "ground_surface": [[0, 12.0], [1000, 10.0]],
        "groundwater": {"level": [list(w) for w in water]},
        "boreholes": boreholes,
    })


BH = [
    {"id": "A", "chainage": 0, "tops": {"MG": 12, "TG": 9, "LC": 5, "LM": -30}},
    {"id": "B", "chainage": 500, "tops": {"MG": 11, "LC": 6, "LM": -26}},  # no gravel: zero thickness
    {"id": "C", "chainage": 1000, "tops": {"MG": 10, "TG": 8, "LC": 3}, "base_level": -20},  # stops in London Clay
]


def test_interpolation_and_absent_units():
    s = make(BH)
    assert s.surface_at(250) == pytest.approx(11.5)
    col = {l.unit: (l.top, l.base) for l in s.column(250)}
    assert col["MG"] == pytest.approx((11.5, 7.5))  # TG top 9 -> 6 at B (absent), so 7.5 at 250
    assert col["LC"][0] == pytest.approx(5.5)
    assert col["LC"][1] == pytest.approx(-28)
    # B has no gravel: zero thickness there
    assert "TG" not in {l.unit for l in s.column(500)}
    # C did not reach the Lambeth Group: its top beyond 500 m comes from B only (constant)
    assert {l.unit: l.top for l in s.column(800)}["LM"] == pytest.approx(-26)


def test_unit_at_and_face():
    s = make(BH)
    assert s.unit_at(0, 10) == "MG"
    assert s.unit_at(0, 0) == "LC"
    assert s.unit_at(0, -40) == "LM"
    f = s.face(0, 7.0)  # axis -15, crown -11.5, invert -18.5: all London Clay
    assert f.unit_at_axis == "LC" and f.units_on_face == {"LC": pytest.approx(1.0)}
    assert f.phi == pytest.approx(23) and f.k0 == 1.5
    assert f.cover == pytest.approx(23.5) and f.axis_depth == pytest.approx(27)
    assert f.water_depth == pytest.approx(7)
    # overburden: 3 m MG, 4 m TG, 16.5 m LC above the crown
    assert f.gamma == pytest.approx((3 * 19 + 4 * 20 + 16.5 * 20) / 23.5)
    # a face crossing into the Lambeth Group
    g = s.face(0, 7.0, axis_level=-29)
    # crown -25.5, invert -32.5, Lambeth Group top -30: 2.5 m of the 7 m face
    assert set(g.units_on_face) == {"LC", "LM"} and g.units_on_face["LM"] == pytest.approx(2.5 / 7)


def test_errors(tmp_path):
    with pytest.raises(ValueError):
        Scenario({"format": "other"})
    with pytest.raises(ValueError):
        make([{"id": "X", "chainage": 0, "tops": {"MG": 10, "ZZ": 0}}])
    with pytest.raises(ValueError):
        make([{"id": "X", "chainage": 0, "tops": {"MG": 10}}])  # nothing defines TG, LC, LM
    p = tmp_path / "s.json"
    p.write_text(json.dumps(make(BH).data))
    assert Scenario.load(p).length == 1000


def test_two_water_systems():
    units = {**UNITS, "LC": {**UNITS["LC"], "pore_pressure_ratio": 0.9}, "LM": {**UNITS["LM"], "water": "lower"}}
    s = Scenario({**make(BH).data, "units": units, "groundwater": {"level": [[0, 5.0], [1000, 5.0]], "deep_head": [[0, -24.0], [1000, -24.0]]}})
    assert s.pore_pressure(0, -15) == pytest.approx(0.9 * 10 * 20)  # London Clay: under-drained upper system
    assert s.pore_pressure(0, -32) == pytest.approx(10 * 8)  # Lambeth Group: deep head -24
    assert s.pore_pressure(0, -20.0 + 0) == pytest.approx(0.9 * 250)
    f = s.face(0, 7.0, axis_level=-31)
    assert f.unit_at_axis == "LM" and f.u_axis == pytest.approx(70)
    assert f.water_depth_equiv == pytest.approx((12 + 31) - 7)


def test_river_and_d10():
    units = {**UNITS, "TG": {**UNITS["TG"], "d10": 0.0008}, "LC": {**UNITS["LC"], "d10": 0.00001}}
    data = {**make(BH).data, "units": units, "groundwater": {"level": [[0, 20.0], [1000, 20.0]]}, "river": {"level": [[0, 20.0], [1000, 20.0]], "from": 0, "to": 1000}}
    s = Scenario(data)
    f = s.face(0, 7.0, axis_level=6.0)  # gravel 9..5 and London Clay below 5 on the face
    assert f.d10 == pytest.approx(0.0008)
    assert f.u_axis == pytest.approx(10 * (20 - 6))
    assert f.water_depth_equiv == pytest.approx((12 - 6) - 14)  # negative: water above the ground surface
