import datetime as dt
import json

from tunnelsim_server import runrecord


def test_reserved_window(tmp_path, monkeypatch):
    f = tmp_path / "res.json"
    f.write_text(json.dumps({"windows": [{"days": ["Sat"], "start": "08:00", "end": "12:00"}]}))
    monkeypatch.setattr(runrecord, "RESERVATIONS", f)
    assert runrecord.reserved_now(dt.datetime(2026, 11, 7, 9, 0))  # a Saturday
    assert not runrecord.reserved_now(dt.datetime(2026, 11, 7, 12, 0))
    assert not runrecord.reserved_now(dt.datetime(2026, 11, 6, 9, 0))  # Friday


def test_timing_valid_only_idle_and_reserved(monkeypatch):
    monkeypatch.setattr(runrecord, "reserved_now", lambda now=None: True)
    monkeypatch.setattr(runrecord, "git_commit", lambda: "test")
    busy = {"utilisation_percent": 90, "other_processes": ["sister"]}
    idle = {"utilisation_percent": 0, "other_processes": []}
    assert not runrecord.record("face", {}, {}, "uncalibrated", busy)["timing_valid_for_decisions"]
    assert runrecord.record("face", {}, {}, "uncalibrated", idle)["timing_valid_for_decisions"]
