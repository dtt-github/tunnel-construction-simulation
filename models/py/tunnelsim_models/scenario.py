"""Ground scenarios along an alignment: load a scenario file (JSON, format "tunnelsim-scenario/1", documented in
docs/SCENARIOS.md) and answer what the ground is at a chainage: the ground surface, groundwater, the stratigraphic
column interpolated between boreholes, the unit at a given level, and the averaged parameters a face or a lining
check needs.

Interpolation: each unit's top level is linear in chainage between the boreholes that define it and constant beyond
the first and last. In a borehole, a unit that is missing while a deeper unit is logged has zero thickness there (its
top equals the top of the next logged unit down); a unit below the bottom of the borehole is unknown there and that
borehole is skipped for it. Interpolated tops are kept in order (a unit's top is never above the one above it).
Units are ordered from the top down in the file. Levels are in m above a datum (m OD in the UK).

Groundwater: `groundwater.level` is the upper water table. An optional `groundwater.deep_head` is the piezometric
level of a lower aquifer (in London the Chalk, Thanet Sand and, under-drained by them, the Lambeth Group). Each unit
says which system it follows ("water": "upper" by default, or "lower") and may scale the hydrostatic pore pressure by
"pore_pressure_ratio" (under-drained clay). The pore pressure at the tunnel axis follows the unit there; for models
that take a water depth, `FaceGround.water_depth_equiv` is the depth of a water table that gives the same pressure.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

FORMAT = "tunnelsim-scenario/1"


def _interp(points: list[list[float]], x: float) -> float:
    """Piecewise-linear interpolation in sorted [x, y] pairs, constant beyond the ends."""
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0) if x1 > x0 else y1
    return points[-1][1]


@dataclass(frozen=True)
class Layer:
    unit: str
    top: float  # level of the top, m
    base: float  # level of the base, m


@dataclass(frozen=True)
class FaceGround:
    """Ground for a face of diameter D centred at axis_level: what the face-support, thrust and lining checks need."""
    unit_at_axis: str
    units_on_face: dict  # unit -> share of the face height
    gamma: float  # mean bulk unit weight of the overburden above the crown, kN/m^3
    phi: float  # face-height weighted effective friction angle, deg
    c: float  # face-height weighted effective cohesion, kPa
    k0: float  # at the axis
    e_soil: float  # face-height weighted stiffness, kPa
    cover: float  # crown depth below the ground surface, m
    axis_depth: float  # axis depth below the ground surface, m
    water_depth: float  # upper water table depth below the ground surface, m
    u_axis: float  # pore pressure at the axis, kPa
    water_depth_equiv: float  # water-table depth that gives u_axis hydrostatically, m


class Scenario:
    def __init__(self, data: dict):
        if data.get("format") != FORMAT:
            raise ValueError(f"not a {FORMAT} file")
        self.data = data
        self.units = data["units"]  # code -> parameters, in order from the top down
        self.order = list(self.units)
        self.length = float(data["alignment"]["length"])
        self.surface = sorted(data["ground_surface"])
        self.water = sorted(data["groundwater"]["level"])
        self.deep = sorted(data["groundwater"]["deep_head"]) if data["groundwater"].get("deep_head") else None
        bhs = sorted(data["boreholes"], key=lambda b: b["chainage"])
        if not bhs:
            raise ValueError("a scenario needs at least one borehole")
        # top of each unit at each borehole: logged, absent (zero thickness), or not reached (skipped)
        self.tops: dict[str, list[list[float]]] = {u: [] for u in self.order}
        for b in bhs:
            unknown = set(b["tops"]) - set(self.order)
            if unknown:
                raise ValueError(f"borehole {b['id']}: units not in the scenario: {sorted(unknown)}")
            below = None
            for u in reversed(self.order):
                if u in b["tops"]:
                    below = float(b["tops"][u])
                if below is not None:
                    self.tops[u].append([float(b["chainage"]), below])
        for u, pts in self.tops.items():
            if not pts:
                raise ValueError(f"unit {u} is not defined by any borehole")
        self.boreholes = bhs

    @classmethod
    def load(cls, path: str | Path) -> "Scenario":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def surface_at(self, ch: float) -> float:
        return _interp(self.surface, ch)

    def water_at(self, ch: float) -> float:
        return _interp(self.water, ch)

    def pore_pressure(self, ch: float, level: float, gamma_w: float = 10.0) -> float:
        """Pore pressure (kPa) at a level, from the water system of the unit there."""
        unit = self.units[self.unit_at(ch, level)]
        head = _interp(self.deep, ch) if unit.get("water", "upper") == "lower" and self.deep else self.water_at(ch)
        return max(head - level, 0.0) * gamma_w * float(unit.get("pore_pressure_ratio", 1.0))

    def axis_at(self, ch: float) -> float:
        return _interp(sorted(self.data["alignment"]["axis_level"]), ch)

    def column(self, ch: float) -> list[Layer]:
        """Layers from the ground surface down; the top unit is cut at the ground surface."""
        surf = self.surface_at(ch)
        tops, above = [], surf
        for u in self.order:
            above = min(_interp(self.tops[u], ch), above)
            tops.append(above)
        out = []
        for i, u in enumerate(self.order):
            base = tops[i + 1] if i + 1 < len(tops) else -1e9
            if tops[i] > base:
                out.append(Layer(u, tops[i], base))
        return out

    def unit_at(self, ch: float, level: float) -> str:
        for layer in self.column(ch):
            if layer.base < level <= layer.top:
                return layer.unit
        return self.order[-1]

    def _weighted(self, ch: float, top: float, base: float, key: str) -> tuple[float, dict]:
        total, shares = 0.0, {}
        for layer in self.column(ch):
            h = max(min(layer.top, top) - max(layer.base, base), 0.0)
            if h > 0:
                shares[layer.unit] = shares.get(layer.unit, 0.0) + h
                total += h * float(self.units[layer.unit][key])
        span = sum(shares.values())
        return (total / span if span > 0 else 0.0), {u: h / span for u, h in shares.items()} if span > 0 else {}

    def face(self, ch: float, diameter: float, axis_level: float | None = None) -> FaceGround:
        axis = self.axis_at(ch) if axis_level is None else axis_level
        surf, r = self.surface_at(ch), diameter / 2
        crown, invert = axis + r, axis - r
        gamma, _ = self._weighted(ch, surf, crown, "gamma")
        phi, shares = self._weighted(ch, crown, invert, "phi")
        c, _ = self._weighted(ch, crown, invert, "c")
        e, _ = self._weighted(ch, crown, invert, "E")
        unit = self.unit_at(ch, axis)
        u = self.pore_pressure(ch, axis)
        return FaceGround(unit, shares, gamma, phi, c, float(self.units[unit]["k0"]), e, surf - crown, surf - axis,
                          max(surf - self.water_at(ch), 0.0), u, (surf - axis) - u / 10.0)
