"""Golden test: the Phase 0 face run (D = 2 m, C/D = 1, voxel D/10, tan phi 0.75) must keep its numbers. Newton 1.7 has
changed MPM material scaling before; a failure here means recalibrating on purpose, not editing the numbers.

Pinned 5 Nov 2026 with newton 1.7.0 / warp 1.19.0 (phase0/RESULTS.md table b, first row; repeated by server/runner).
Re-pinned 5 Nov 2026 for WP0b (particle radius 0.7 h, cohesion and stiffness divided by the packing): the settled
pressure fell from 8.216 to 7.611 kPa; the limit pressure (1.629 -> 1.642) and the Vermeer ratio (0.5287 -> 0.5329)
hardly moved."""
import pytest

PINNED = {"particles": 208068, "p_settled_kPa": 7.611, "p_limit_kPa": 1.642, "ratio_sim_over_vermeer": 0.5329}
TOL = 0.02  # relative


def _cuda() -> bool:
    try:
        import warp as wp

        wp.init()
        return wp.is_cuda_available()
    except Exception:
        return False


@pytest.mark.gpu
@pytest.mark.skipif(not _cuda(), reason="needs a CUDA GPU")
def test_face_phase0_d10():
    from tunnelsim_server.scenes import face

    result, arrays = face.run(face.FaceConfig(voxel=0.2))
    assert result["particles"] == PINNED["particles"]
    for k in ("p_settled_kPa", "p_limit_kPa", "ratio_sim_over_vermeer"):
        assert result[k] == pytest.approx(PINNED[k], rel=TOL), k
    # the plate force must fall from the settled value to the limit once the plate retracts
    assert result["p_limit_kPa"] < 0.3 * result["p_settled_kPa"]


def test_vermeer_reference():
    from tunnelsim_server.scenes.face import vermeer_limit_pressure

    p, n = vermeer_limit_pressure(1600 * 9.81, 2.0, 0.6435011087932844)  # tan phi = 0.75
    assert n == pytest.approx(1 / (9 * 0.75) - 0.05)
    assert p / 1e3 == pytest.approx(3.08, abs=0.01)  # phase0/RESULTS.md
