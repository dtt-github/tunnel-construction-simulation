"""WP1 element tests on the GPU, at their fast resolutions (docs/validation/mpm-element-tests.md)."""
import math

import pytest

from tunnelsim_server import materials as m


def _cuda() -> bool:
    try:
        import warp as wp

        wp.init()
        return wp.is_cuda_available()
    except Exception:
        return False


gpu = pytest.mark.skipif(not _cuda(), reason="needs a CUDA GPU")


@pytest.mark.gpu
@gpu
def test_rankine_plane_strain_mapping():
    from tunnelsim_server.scenes import rankine

    mu = m.mu_plane_strain(34.0)
    r, _ = rankine.run(rankine.RankineConfig(voxel=0.2), m.Soil("t", 1600.0, mu, "test"))
    assert r["K_active"] == pytest.approx(m.rankine_ka(34.0), rel=0.05)  # 0.2855 against 0.283 when pinned


@pytest.mark.gpu
@gpu
def test_collapse_b00_rousseau():
    from tunnelsim_server.scenes import collapse

    r, _ = collapse.run(collapse.CollapseConfig(run="B00", gate_speed=1.0))
    assert r["Hf_sim"] == pytest.approx(0.11, rel=0.05)  # measured 0.11 m
    assert r["runout_sim_5mm"] == pytest.approx(0.18, rel=0.10)  # measured 0.18 m
