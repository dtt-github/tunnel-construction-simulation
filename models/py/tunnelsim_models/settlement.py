"""Greenfield surface settlement above a tunnel (empirical Gaussian trough).

References
- Peck, R.B. (1969). Deep excavations and tunnelling in soft ground. Proc. 7th ICSMFE, Mexico, State-of-the-art vol., 225-290.
- O'Reilly, M.P., New, B.M. (1982). Settlements above tunnels in the United Kingdom - their magnitude and prediction.
  Tunnelling '82, IMM, London, 173-181.
- Attewell, P.B., Woodman, J.P. (1982). Predicting the dynamics of ground settlement and its derivatives caused by
  tunnelling in soil. Ground Engineering 15(8), 13-22.
- Mair, R.J., Taylor, R.N., Bracegirdle, A. (1993). Subsurface settlement profiles above tunnels in clays. Geotechnique 43(2).
- Mair, R.J., Taylor, R.N. (1997). Bored tunnelling in the urban environment. Proc. 14th ICSMFE, Hamburg, 4, 2353-2385.
  (Volume-loss components: face, shield passage, tail void, lining deformation and grout behind the tail;
  typical VL by method and ground.)
- Addenbrooke, T.I., Potts, D.M. (2001). Twin tunnel interaction: surface and subsurface effects. Int. J. Geomechanics
  1(2), 249-271, doi:10.1061/(ASCE)1532-3641(2001)1:2(249). (Second-tunnel trough larger and shifted towards the first.)
- Wan, M.S.P., Standing, J.R., Potts, D.M., Burland, J.B. (2017). Measured short-term ground surface response to EPBM
  tunnelling in London Clay. Geotechnique 67(5), 420-445, doi:10.1680/jgeot.16.P.099, Tables 1-2, Figs 10-13 (Hyde Park:
  second bore 16.2 m from the first, incremental VL 1.5-1.9 x the first bore's, Ky 0.42-0.47 towards the first bore
  and 0.29-0.43 away from it).
- Burland, J.B. (1995). Assessment of risk of damage to buildings due to tunnelling and excavation. Proc. 1st IC Earthquake Geotech. Eng.
- Macklin, S.R. (1999). The prediction of volume loss due to tunnelling in overconsolidated clay based on heading
  geometry and stability number. Ground Engineering 32(4). Not open; the relation is quoted from Divall, Goodey,
  Davies, Le & Nguyen (2023), Twin-tunnelling: case studies in clay, J. Mining and Earth Sciences 64(6), 66-78,
  doi:10.46326/jmes.2023.64(6).08, accepted version open at https://openaccess.city.ac.uk/id/eprint/31563/, Eq. (4)-(6)
  and Fig. 1 (VL (%) = 0.23 e^(4.4 LF) for LF >= 0.2, LF = N / N_TC,
  N = (sigma_v - sigma_T) / S_u, N_TC from Kimura & Mair (1981); field data from overconsolidated clay, mostly C/D > 1.)
- Kimura, T., Mair, R.J. (1981). Centrifugal testing of model tunnels in soft clay. Proc. 10th ICSMFE, Stockholm, 1,
  319-322, https://www.issmge.org/uploads/publications/1/35/1981_01_0061.pdf. N at collapse for a heading supported to
  the face (P/D 0): 7.05 at C/D 1.5 and 9.0 at C/D 3.0, digitised from Fig. 9 (docs/validation/mpm-clay.md); N is
  constant above C/D about 3.

    i      = K * z0                       trough width (inflection point); i_left / i_right for an asymmetric trough
    V_s    = VL * pi * D^2 / 4            settlement volume per metre of tunnel (m^3/m)
    S_max  = 2 V_s / (sqrt(2 pi) (i_left + i_right))      (= V_s / (sqrt(2 pi) i) when symmetric)
    S(x)   = S_max * exp(-x^2 / (2 i_side^2)),  i_side = i_left for x < 0, i_right for x >= 0
    u(x)   = -(x / z0) * S(x)             horizontal displacement (radial-flow assumption, O'Reilly & New)

Longitudinal profile (Attewell & Woodman 1982 cumulative normal, generalised to volume-loss components):
the volume loss is split into components k with fraction w_k, each generated at a distance y_k behind the face
(face loss at 0, shield passage over the shield, tail void at the shield tail, and loss behind the tail from
lining deformation and grout shrinkage; Mair & Taylor 1997):

    S(x, y) = S(x) * sum_k w_k * Phi((y - y_k) / i_long)     y = distance behind the face, i_long defaults to i

A single component at y = 0 gives the classic profile with half the final settlement above the face. Closed-face
machines with good face control put most of the volume loss at and behind the tail, which shifts the profile back and
reduces the fraction that has occurred when the face passes. With the longitudinal width equal to the transverse i,
a loss at the tail alone still leaves Phi(-L/i) (about 0.2 for L = 8 m, i = 9 m) at the face, so a lower fraction at
the face needs loss further back; the "behind" component sits one shield length behind the tail by default. Attewell &
Woodman use the transverse i along the drive; i_long sets a different longitudinal width (below i for a steeper
profile, so less settlement ahead of the loss). Calibrate it per project.

Units: metres; VL as a fraction (0.01 = 1 %). Settlement positive downward.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

# Typical trough-width parameter K (O'Reilly & New 1982; Mair & Taylor 1997)
K_TYPICAL = {"stiff_clay": 0.5, "soft_clay": 0.6, "sand_gravel": 0.35}

# Excavation-method presets (classes, not brands). Volume loss and its range are the typical values summarised by
# Mair & Taylor (1997). The component split (face, shield, tail, behind) is an illustrative default following their
# decomposition; calibrate it per project. Split positions: face at 0, shield at L/2, tail at L, behind the tail at
# 2 L (L = shield length). Closed-face splits keep the face and shield shares small, so that only about 0.1-0.2 of
# the final trough has formed when the face passes.
METHOD_PRESETS = {
    "open_face_stiff_clay": {"volume_loss": 0.015, "range": (0.01, 0.02), "k": 0.5, "split": (0.6, 0.3, 0.1, 0.0)},
    "scl_stiff_clay": {"volume_loss": 0.01, "range": (0.005, 0.015), "k": 0.5, "split": (0.8, 0.2, 0.0, 0.0)},
    "closed_face_clay": {"volume_loss": 0.01, "range": (0.005, 0.02), "k": 0.5, "split": (0.05, 0.15, 0.4, 0.4)},
    "closed_face_sand": {"volume_loss": 0.005, "range": (0.002, 0.01), "k": 0.35, "split": (0.05, 0.15, 0.4, 0.4)},
}

# Burland (1995) damage categories by limiting tensile strain (%)
BURLAND_CATEGORIES = [
    (0.05, 0, "Negligible"),
    (0.075, 1, "Very slight"),
    (0.15, 2, "Slight"),
    (0.3, 3, "Moderate"),
    (float("inf"), 4, "Severe to very severe"),
]


def _phi(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


@dataclass(frozen=True)
class Trough:
    i: float  # mean width (i_left + i_right) / 2, also used for the longitudinal profile
    volume_m3_per_m: float
    s_max: float
    z0: float
    i_left: float | None = None
    i_right: float | None = None
    components: tuple[tuple[float, float], ...] = ((1.0, 0.0),)  # (fraction of VL, distance behind face m)
    i_long: float | None = None  # longitudinal width; None = i

    def _i_side(self, x: float) -> float:
        if x < 0:
            return self.i_left if self.i_left is not None else self.i
        return self.i_right if self.i_right is not None else self.i

    def settlement(self, x: float) -> float:
        i = self._i_side(x)
        return self.s_max * math.exp(-(x * x) / (2 * i * i))

    def horizontal(self, x: float) -> float:
        return -(x / self.z0) * self.settlement(x)

    def slope(self, x: float) -> float:
        i = self._i_side(x)
        return -(x / (i * i)) * self.settlement(x)

    def longitudinal_fraction(self, y_behind_face: float) -> float:
        """Fraction of the final transverse trough developed at y (y > 0: behind the face)."""
        il = self.i if self.i_long is None else self.i_long
        return sum(w * _phi((y_behind_face - yk) / il) for w, yk in self.components)

    @property
    def fraction_at_face(self) -> float:
        return self.longitudinal_fraction(0.0)

    def settlement_3d(self, x: float, y_behind_face: float) -> float:
        """y_behind_face > 0 means the point is behind (already passed by) the face."""
        return self.settlement(x) * self.longitudinal_fraction(y_behind_face)


def gaussian_trough(
    diameter_m: float,
    axis_depth_m: float,
    volume_loss: float,
    k: float = 0.5,
    *,
    k_left: float | None = None,
    k_right: float | None = None,
    components: Sequence[tuple[float, float]] | None = None,
    i_long: float | None = None,
) -> Trough:
    """Gaussian trough. k_left / k_right override k on either side; components = [(fraction, y_behind_face_m)];
    i_long (m) sets the longitudinal width (default: the mean transverse i)."""
    if axis_depth_m <= diameter_m / 2:
        raise ValueError("axis depth must exceed the tunnel radius")
    il = (k if k_left is None else k_left) * axis_depth_m
    ir = (k if k_right is None else k_right) * axis_depth_m
    comps = tuple((float(w), float(y)) for w, y in (components or [(1.0, 0.0)]))
    if abs(sum(w for w, _ in comps) - 1) > 1e-9 or any(w < 0 for w, _ in comps):
        raise ValueError("component fractions must be non-negative and sum to 1")
    if i_long is not None and i_long <= 0:
        raise ValueError("i_long must be positive")
    vs = volume_loss * math.pi * diameter_m**2 / 4
    asym = k_left is not None or k_right is not None
    return Trough(
        i=(il + ir) / 2,
        volume_m3_per_m=vs,
        s_max=2 * vs / (math.sqrt(2 * math.pi) * (il + ir)),
        z0=axis_depth_m,
        i_left=il if asym else None,
        i_right=ir if asym else None,
        components=comps,
        i_long=i_long,
    )


def volume_loss_components(face: float, shield: float, tail: float, shield_length_m: float, behind: float = 0.0,
                           behind_offset_m: float | None = None) -> list[tuple[float, float]]:
    """Split of the volume loss into face (y = 0), shield passage (y = L/2), tail void (y = L) and behind-the-tail
    (y = L + behind_offset_m, default 2 L) components. Zero-weight components are dropped."""
    total = face + shield + tail + behind
    if total <= 0 or min(face, shield, tail, behind) < 0:
        raise ValueError("split must be non-negative with a positive sum")
    offset = shield_length_m if behind_offset_m is None else behind_offset_m
    comps = [(face, 0.0), (shield, shield_length_m / 2), (tail, shield_length_m), (behind, shield_length_m + offset)]
    return [(w / total, y) for w, y in comps if w > 0]


def preset_trough(method: str, diameter_m: float, axis_depth_m: float, *, shield_length_m: float | None = None,
                  volume_loss: float | None = None, k: float | None = None, i_long: float | None = None) -> Trough:
    """Trough from METHOD_PRESETS; shield length defaults to 1.5 D (set it from the machine preset)."""
    p = METHOD_PRESETS[method]
    length = 1.5 * diameter_m if shield_length_m is None else shield_length_m
    return gaussian_trough(
        diameter_m,
        axis_depth_m,
        p["volume_loss"] if volume_loss is None else volume_loss,
        p["k"] if k is None else k,
        components=volume_loss_components(*p["split"][:3], length, *p["split"][3:]),
        i_long=i_long,
    )


@dataclass(frozen=True)
class TwinTroughs:
    first: Trough  # centred at x = 0
    second: Trough  # centred at x = spacing
    spacing: float

    def settlement(self, x: float) -> float:
        return self.first.settlement(x) + self.second.settlement(x - self.spacing)

    def horizontal(self, x: float) -> float:
        return self.first.horizontal(x) + self.second.horizontal(x - self.spacing)


def twin_troughs(
    diameter_m: float,
    axis_depth_m: float,
    spacing_m: float,
    volume_loss_first: float,
    volume_loss_second: float | None = None,
    k: float = 0.5,
    *,
    second_vl_factor: float = 1.0,
    second_inner_k: float | None = None,
    second_outer_k: float | None = None,
) -> TwinTroughs:
    """Two parallel tunnels, the second at x = spacing (either sign), driven after the first.

    With the defaults this is plain superposition. Addenbrooke & Potts (2001) found the second tunnel's trough is
    larger and shifted towards the first tunnel, because it passes through ground already disturbed by the first.
    second_vl_factor scales the second tunnel's volume loss; second_inner_k widens the arm of its trough that faces
    the first tunnel (the volume is kept, so the trough's centroid moves towards the first tunnel); second_outer_k sets
    the arm facing away (Hyde Park: narrower than the first bore's trough, Wan et al. 2017).
    """
    vl2 = (volume_loss_first if volume_loss_second is None else volume_loss_second) * second_vl_factor
    first = gaussian_trough(diameter_m, axis_depth_m, volume_loss_first, k)
    k_in, k_out = (k if second_inner_k is None else second_inner_k), (k if second_outer_k is None else second_outer_k)
    if second_inner_k is None and second_outer_k is None:
        second = gaussian_trough(diameter_m, axis_depth_m, vl2, k)
    elif spacing_m >= 0:  # first tunnel lies to the left of the second
        second = gaussian_trough(diameter_m, axis_depth_m, vl2, k, k_left=k_in, k_right=k_out)
    else:
        second = gaussian_trough(diameter_m, axis_depth_m, vl2, k, k_left=k_out, k_right=k_in)
    return TwinTroughs(first=first, second=second, spacing=spacing_m)


def burland_category(tensile_strain_percent: float) -> tuple[int, str]:
    for limit, cat, name in BURLAND_CATEGORIES:
        if tensile_strain_percent < limit:
            return cat, name
    raise AssertionError("unreachable")


# Kimura & Mair (1981) Fig. 9, heading supported to the face (P/D 0): (C/D, N at collapse), digitised to about +/-0.2
KIMURA_MAIR_NTC_FACE_SUPPORTED = ((1.5, 7.05), (3.0, 9.0))


def critical_stability_ratio(cover_over_d: float) -> float:
    """N at collapse for a closed-face shield (P/D 0), linear between Kimura & Mair's two points; constant beyond them
    (their tests show N constant above C/D about 3; below C/D 1.5 the value at 1.5 is kept, an extrapolation)."""
    (c0, n0), (c1, n1) = KIMURA_MAIR_NTC_FACE_SUPPORTED
    t = min(max((cover_over_d - c0) / (c1 - c0), 0.0), 1.0)
    return n0 + t * (n1 - n0)


def load_factor(sigma_v_axis: float, support_axis: float, su_axis: float, cover_over_d: float) -> float:
    """LF = N / N_TC with the stability ratio N = (sigma_v - sigma_T) / S_u at the axis (Broms & Bennermark 1967;
    Mair 1989). Stresses in kPa: total overburden, support pressure and undrained strength at the axis."""
    if su_axis <= 0:
        raise ValueError("undrained strength must be positive")
    return max(sigma_v_axis - support_axis, 0.0) / su_axis / critical_stability_ratio(cover_over_d)


def macklin_volume_loss(lf: float) -> float:
    """Macklin (1999): VL = 0.23 % x exp(4.4 LF), as a fraction. Fitted for LF >= 0.2 in overconsolidated clay."""
    return 0.0023 * math.exp(4.4 * lf)


def face_volume_loss(base_volume_loss: float, lf: float) -> float:
    """Volume loss with the face's contribution: the larger of the base value (measured for the drive, which carries
    the tail void and grouting) and Macklin's value for the load factor at the face. It equals the base value while
    the face is well supported and rises once a lower support pressure raises the load factor."""
    return max(base_volume_loss, macklin_volume_loss(lf))

