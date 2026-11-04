"""Class presets: every field cited or explicitly unsourced; values consistent with the models."""
import json
import math
import pathlib

import pytest

from tunnelsim_models import REFERENCE_MACHINES

PRESETS = json.loads((pathlib.Path(__file__).resolve().parents[2] / "presets" / "machine-classes.json").read_text())


def test_every_field_is_cited_or_marked_unsourced():
    keys = PRESETS["sources"]
    for p in PRESETS["presets"]:
        assert p["id"] and p["class"] and p["method"]
        for name, f in p["fields"].items():
            assert set(f) >= {"value", "unit", "source", "verified"}, (p["id"], name)
            if f["verified"]:
                assert f["source"] in keys, (p["id"], name)  # verified only against a listed source
                assert f["value"] is not None
            if f["value"] is None:
                assert not f["verified"], (p["id"], name)  # never a verified empty value
            if f["source"] is None:
                assert f["value"] is None or not f["verified"]


def test_rpm_from_gauge_speed():
    # Rostami & Chang (2017): rpm = V_L / (pi D), V_L = 200 m/min for 19-inch discs
    for p in PRESETS["presets"]:
        f = p["fields"]
        if f.get("cutterhead_rpm_max", {}).get("source") == "ROSTAMI-CHANG-2017":
            assert f["cutterhead_rpm_max"]["value"] == pytest.approx(200 / (math.pi * f["diameter"]["value"]), abs=0.05)


def test_epb_preset_matches_reference_table():
    epb = next(p for p in PRESETS["presets"] if p["id"] == "urban-epb-7m")["fields"]
    ref = next(m for m in REFERENCE_MACHINES if m["type"] == "epb" and m["project"].startswith("Crossrail"))
    assert epb["cutterhead_torque"]["value"] == ref["torque_knm"]
    assert epb["diameter"]["value"] == ref["diameter"]
