"""Reference (Python) implementations of the tunnelling models used by the simulator.

Each model has a JavaScript twin in models/js/ used by the browser. Both are checked against the
shared vectors in models/test-vectors/ so the browser and the GPU server always agree.
"""
from .csm import PRACTICAL_MAX_PENETRATION_MM, Cutter, cutter_forces, max_rpm, penetration_for_normal_force, tbm_performance
from .epb_chamber import P_ATM, Chamber, ChamberState, Screw, crown_pressure, foam_split
from .thrust_torque import REFERENCE_MACHINES, Thrust, Torque, cutterhead_torque, reference_installed, shield_thrust, tool_torque, vertical_stress
from .utilisation import DriveResult, DriveSettings, record_check, simulate_drive
from .hard_rock import RMR_CLASSES, HardRockUtilisation, cutter_change_h_per_km, hard_rock_utilisation, rmr_class, support_downtime
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
    "max_rpm",
    "PRACTICAL_MAX_PENETRATION_MM",
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
    "shield_thrust",
    "cutterhead_torque",
    "tool_torque",
    "vertical_stress",
    "reference_installed",
    "Thrust",
    "Torque",
    "REFERENCE_MACHINES",
    "simulate_drive",
    "record_check",
    "DriveSettings",
    "DriveResult",
    "hard_rock_utilisation",
    "HardRockUtilisation",
    "cutter_change_h_per_km",
    "support_downtime",
    "rmr_class",
    "RMR_CLASSES",
]
