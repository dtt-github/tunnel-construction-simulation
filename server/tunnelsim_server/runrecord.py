"""Run records: what produced a result. Every run stores its software versions, git commit, parameters, resolution,
seed, GPU load and calibration status next to its results, so a number can always be traced and repeated.

GPU time is shared with the sister project (construction-site-simulation) on the same DGX Spark. Timings count for
decisions only when the run was inside a reserved window and the GPU was otherwise idle (plan, section 7).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import platform
import subprocess
from pathlib import Path

RESERVATIONS = Path(__file__).resolve().parent.parent / "gpu_reservations.json"
IDLE_UTILISATION = 5  # %, at most this much GPU use by other processes before a run counts as idle


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def gpu_snapshot() -> dict:
    """GPU name, utilisation and the other compute processes on it (from nvidia-smi), taken just before a run."""
    q = _run(["nvidia-smi", "--query-gpu=name,utilization.gpu,driver_version", "--format=csv,noheader,nounits"])
    apps = _run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"])
    name, util, driver = (q.split(", ") + ["", "", ""])[:3] if q else ("", "", "")
    # process names only (basename), never local paths
    others = [os.path.basename(line.split(", ", 1)[1]) for line in apps.splitlines() if ", " in line]
    try:
        util_pct = int(util)
    except ValueError:
        util_pct = None
    return {"name": name, "utilisation_percent": util_pct, "driver": driver, "other_processes": others}


def reserved_now(now: dt.datetime | None = None) -> bool:
    """True when `now` falls in a GPU window reserved for this project (gpu_reservations.json, local time)."""
    if not RESERVATIONS.exists():
        return False
    windows = json.loads(RESERVATIONS.read_text()).get("windows", [])
    now = now or dt.datetime.now()
    day, minute = now.strftime("%a"), now.hour * 60 + now.minute
    for w in windows:
        if day in w["days"]:
            h0, m0 = map(int, w["start"].split(":"))
            h1, m1 = map(int, w["end"].split(":"))
            if h0 * 60 + m0 <= minute < h1 * 60 + m1:
                return True
    return False


def versions() -> dict:
    import newton
    import numpy
    import warp

    return {"newton": newton.__version__, "warp": warp.__version__, "numpy": numpy.__version__, "python": platform.python_version()}


def git_commit() -> str:
    sha = _run(["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "--short", "HEAD"])
    dirty = _run(["git", "-C", str(Path(__file__).resolve().parent), "status", "--porcelain", "--", "."])
    return sha + ("+dirty" if dirty else "")


def record(scene: str, params: dict, result: dict, calibration: str, gpu_before: dict) -> dict:
    """Assemble the record. Timing is marked usable for decisions only in a reserved window on an idle GPU."""
    idle = gpu_before.get("utilisation_percent") is not None and gpu_before["utilisation_percent"] <= IDLE_UTILISATION \
        and not gpu_before.get("other_processes")
    reserved = reserved_now()
    return {
        "scene": scene,
        "time": dt.datetime.now().isoformat(timespec="seconds"),
        "git": git_commit(),
        "versions": versions(),
        "params": params,
        "gpu_before": gpu_before,
        "timing_valid_for_decisions": bool(idle and reserved),
        "timing_note": "reserved window, idle GPU" if idle and reserved else
                       ("GPU shared with other processes: timings are lower bounds" if not idle else "outside a reserved window"),
        "calibration": calibration,
        "result": result,
    }
