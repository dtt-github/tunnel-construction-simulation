"""Reference (Python) implementations of the tunnelling models used by the simulator.

Each model has a JavaScript twin in models/js/ used by the browser. Both are checked against the
shared vectors in models/test-vectors/ so the browser and the GPU server always agree.
"""
from .csm import Cutter, cutter_forces, penetration_for_normal_force, tbm_performance
from .epb_chamber import P_ATM, Chamber, ChamberState, Screw, crown_pressure, foam_split
from .face_support import DAUB_DEFAULTS, FaceSupport, SupportWindow, daub_window, silo_stress, vermeer_limit, wedge_silo
from .hoek_brown import hoek_brown, sigma1_at_failure
from .settlement import (
    K_TYPICAL,
    METHOD_PRESETS,
    Trough,
    TwinTroughs,
    burland_category,
    gaussian_trough,
    preset_trough,
    twin_troughs,
    volume_loss_components,
)

__all__ = [
    "Cutter",
    "cutter_forces",
    "penetration_for_normal_force",
    "tbm_performance",
    "hoek_brown",
    "sigma1_at_failure",
    "gaussian_trough",
    "preset_trough",
    "twin_troughs",
    "volume_loss_components",
    "Trough",
    "TwinTroughs",
    "K_TYPICAL",
    "METHOD_PRESETS",
    "burland_category",
    "wedge_silo",
    "silo_stress",
    "vermeer_limit",
    "daub_window",
    "FaceSupport",
    "SupportWindow",
    "DAUB_DEFAULTS",
    "Chamber",
    "ChamberState",
    "Screw",
    "foam_split",
    "crown_pressure",
    "P_ATM",
]
