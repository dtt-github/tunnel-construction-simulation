"""Reference (Python) implementations of the tunnelling models used by the simulator.

Each model has a JavaScript twin in models/js/ used by the browser. Both are checked against the
shared vectors in models/test-vectors/ so the browser and the GPU server always agree.
"""
from .csm import Cutter, cutter_forces, penetration_for_normal_force, tbm_performance
from .hoek_brown import hoek_brown, sigma1_at_failure
from .settlement import burland_category, gaussian_trough

__all__ = [
    "Cutter",
    "cutter_forces",
    "penetration_for_normal_force",
    "tbm_performance",
    "hoek_brown",
    "sigma1_at_failure",
    "gaussian_trough",
    "burland_category",
]
