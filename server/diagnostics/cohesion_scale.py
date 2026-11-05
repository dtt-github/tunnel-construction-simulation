"""WP0b diagnostic: does Newton's cohesion scale with the particle packing (2r/h)^3? Rankine active wall in Tresca
clay, cu / (gamma H) = 0.06: theory K = 1 - 4 cu / (gamma H) = 0.76 (sigma_h = sigma_v - 2 cu). If the effective
cohesion is k cu, with k the nominal packing, K falls to 1 - 4 k cu / (gamma H).
Usage: python diagnostics/cohesion_scale.py <radius/h> <critical_fraction> [scale_cohesion 0|1]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tunnelsim_server.scenes.common as common  # noqa: E402
from tunnelsim_server import materials as m  # noqa: E402
from tunnelsim_server.scenes import rankine  # noqa: E402

common.RADIUS, common.CRITICAL_FRACTION = float(sys.argv[1]), float(sys.argv[2])
k = (2 * common.RADIUS) ** 3
cfg = rankine.RankineConfig()
rho, ratio = 1600.0, 0.06
cu = ratio * rho * 9.81 * cfg.height
scale = len(sys.argv) > 3 and sys.argv[3] == "1"
soil = m.undrained_clay("test clay", rho, cu / k if scale else cu, 1.0e15, "test")
res, _ = rankine.run(cfg, soil)
print(f"radius {common.RADIUS} (packing {k:.3f}) cf {common.CRITICAL_FRACTION} cohesion/{k if scale else 1:.3f}: K_active {res['K_active']}, "
      f"theory {1 - 4 * ratio:.3f}, theory with cohesion x packing {1 - 4 * ratio * (1 if scale else k):.3f}")
