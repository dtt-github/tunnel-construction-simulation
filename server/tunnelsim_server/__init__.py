"""GPU ground physics for the tunnel construction simulator (Phase 2): Newton implicit MPM scenes for the tunnel face,
the EPB chamber and the screw conveyor, with probes, run records and calibration status.

Plan: docs/plans/phase2-mpm-face-chamber.md. Every result carries its calibration status; nothing is shown as calibrated
until it has passed the checks named there.
"""

UNCALIBRATED = "uncalibrated"
