"""WP2 face in dry sand on the GPU, at D/10 (docs/validation/mpm-face-sand.md). Pinned 5 Nov 2026, newton 1.7.0."""
import pytest

from tests.test_element_gpu import gpu


@pytest.mark.gpu
@gpu
def test_face_idinger_cd1_displacement():
    from tunnelsim_server.runner import FACE_SOILS
    from tunnelsim_server.scenes import face_sand

    r, _ = face_sand.run(face_sand.FaceSandConfig(cover=1.0, voxel_per_d=10), FACE_SOILS["idinger"])
    assert r["p_5pct_kPa"] == pytest.approx(8.62, rel=0.10)  # pinned; Vermeer 8.44, Idinger measured 4.5-6.0
    assert r["zone_reaches_surface"]  # the known mismatch: no dilation, the chimney reaches the surface


@pytest.mark.gpu
@gpu
def test_face_servo_holds_above_limit_and_gives_way_below():
    from tunnelsim_server.runner import FACE_SOILS
    from tunnelsim_server.scenes import face_sand

    hold, _ = face_sand.run(face_sand.FaceSandConfig(control="pressure", target_kpa=12.0), FACE_SOILS["idinger"])
    assert hold["face_displacement_over_D"] < 0.01 and hold["p_final_kPa"] == pytest.approx(12.0, rel=0.1)
    fail, _ = face_sand.run(face_sand.FaceSandConfig(control="pressure", target_kpa=6.0), FACE_SOILS["idinger"])
    assert fail["face_displacement_over_D"] > 0.04
