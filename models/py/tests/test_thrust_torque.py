"""Thrust and torque components: hand checks (independent of the generated vectors)."""
import math

import pytest

from tunnelsim_models.thrust_torque import REFERENCE_MACHINES, cutterhead_torque, reference_installed, shield_thrust, tool_torque, vertical_stress


def test_vertical_stress():
    # 3 m dry at 20, 15 m submerged at 10: 60 + 150 effective; + 150 water total
    assert vertical_stress(18, 20, water_depth=3) == pytest.approx(210)
    assert vertical_stress(18, 20, water_depth=3, effective=False) == pytest.approx(360)
    assert vertical_stress(18, 20, q=10) == pytest.approx(370)  # dry


def test_thrust_hand():
    t = shield_thrust(7, 9, 18, 20, 200, water_depth=3, k0=0.5, mu_shield=0.3, shield_weight=4000, tools=1000,
                      tail_seal=500, backup_weight=6000, mu_backup=0.1)
    assert t.face == pytest.approx(200 * math.pi * 49 / 4)
    assert t.shield == pytest.approx(0.3 * (math.pi * 7 * 9 * 210 * 0.75 + 4000))
    assert t.backup == pytest.approx(600)
    assert t.total == pytest.approx(t.face + t.shield + 1000 + 500 + 600)
    # shield friction dominates for a long shield in soft ground, and the total stays below built 7 m EPBs
    assert t.shield > t.face
    lo, hi = reference_installed("epb", 7)["thrust"]
    assert t.total < lo


def test_torque_hand():
    r = 3.5
    q = cutterhead_torque(7, 200, 157.5, opening_ratio=0.3, mu=0.15, mu_rim=0.3, mu_chamber=0.1, rim_width=0.5,
                          n_arms=4, arm_area=0.5, arm_radius=2.5, tools=tool_torque(60, 5, r), seals=300)
    disc = 2 / 3 * math.pi * 0.7 * r**3 * 200
    assert q.face == pytest.approx(0.15 * disc)
    assert q.back == pytest.approx(0.1 * disc)
    assert q.rim == pytest.approx(2 * math.pi * r * r * 0.5 * 0.3 * 157.5)
    assert q.arms == pytest.approx(4 * 0.1 * 200 * 0.5 * 2.5)
    assert q.tools == pytest.approx(60 * 5 * 0.5 * r)
    lo, hi = reference_installed("epb", 7)["torque"]
    assert q.total < lo  # required torque below what built 7 m EPBs carry


def test_torque_trends():
    # Shi et al. (2011): opening ratio and earth pressure dominate
    base = cutterhead_torque(7, 200, 150).total
    assert cutterhead_torque(7, 300, 150).total > base
    assert cutterhead_torque(7, 200, 150, opening_ratio=0.5).total < base
    # face and back terms scale with R^3
    a = cutterhead_torque(6, 200, 0, rim_width=0)
    b = cutterhead_torque(12, 200, 0, rim_width=0)
    assert b.face / a.face == pytest.approx(8)
    with pytest.raises(ValueError):
        cutterhead_torque(7, 200, 150, opening_ratio=1.0)


def test_reference_machines():
    ref = reference_installed("epb", 7.08)
    assert ref["torque"][1] == pytest.approx(9800)  # Crossrail at its own diameter
    assert reference_installed("epb", 6.6)["thrust"] == pytest.approx((45000, 45000))
    # scaling: torque with D^3, thrust with D^2
    half = reference_installed("epb", 3.54)
    assert half["torque"][1] == pytest.approx(9800 / 8)
    assert reference_installed("epb", 3.3)["thrust"][1] == pytest.approx(45000 / 4)
    # Gotthard S-210 (9.33 m, Tunnels & Tunnelling 2006), scaled with D^3
    assert reference_installed("gripper", 9)["torque"][1] == pytest.approx(5290 * (9 / 9.33) ** 3)
    for m in REFERENCE_MACHINES:
        assert m["source"] and m["type"] in ("epb", "slurry", "gripper")


def test_paste_shear_caps_face_and_chamber_torque():
    # Bezuijen et al. (2005): conditioned muck shears at 1-3 kPa, far below mu p at operating pressures
    fr = cutterhead_torque(7, 200, 150, n_arms=4, arm_area=0.5, arm_radius=2.3)
    pa = cutterhead_torque(7, 200, 150, n_arms=4, arm_area=0.5, arm_radius=2.3, tau_paste=2.0)
    assert pa.face == pytest.approx(fr.face * 2.0 / (0.15 * 200))
    assert pa.back == pytest.approx(fr.back * 2.0 / (0.1 * 200))
    assert pa.rim == fr.rim and pa.total < 0.5 * fr.total
    # at very low pressure friction is the lower bound and stays
    assert cutterhead_torque(7, 10, 150, tau_paste=2.0).face == cutterhead_torque(7, 10, 150).face
