// Ground scenarios along an alignment ("tunnelsim-scenario/1", docs/SCENARIOS.md): ground surface, groundwater, the
// stratigraphic column interpolated between boreholes, and the averaged ground at a face.
// Twin of models/py/tunnelsim_models/scenario.py, which documents the interpolation rules. Units: m, kN/m^3, kPa, deg.

export const SCENARIO_FORMAT = "tunnelsim-scenario/1";

function interp(points, x) {
  if (x <= points[0][0]) return points[0][1];
  for (let i = 0; i + 1 < points.length; i++) {
    const [x0, y0] = points[i], [x1, y1] = points[i + 1];
    if (x <= x1) return x1 > x0 ? y0 + ((y1 - y0) * (x - x0)) / (x1 - x0) : y1;
  }
  return points.at(-1)[1];
}
const byX = (a) => [...a].map((p) => [+p[0], +p[1]]).sort((p, q) => p[0] - q[0] || p[1] - q[1]);

export function scenario(data) {
  if (data?.format !== SCENARIO_FORMAT) throw new Error(`not a ${SCENARIO_FORMAT} file`);
  const units = data.units, order = Object.keys(units);
  const surface = byX(data.ground_surface), water = byX(data.groundwater.level), axis = byX(data.alignment.axis_level);
  const deep = data.groundwater.deep_head ? byX(data.groundwater.deep_head) : null;
  const bhs = [...data.boreholes].sort((a, b) => a.chainage - b.chainage);
  if (!bhs.length) throw new Error("a scenario needs at least one borehole");
  const tops = Object.fromEntries(order.map((u) => [u, []]));
  for (const b of bhs) {
    const unknown = Object.keys(b.tops).filter((u) => !(u in units));
    if (unknown.length) throw new Error(`borehole ${b.id}: units not in the scenario: ${unknown.sort()}`);
    let below = null;
    for (const u of [...order].reverse()) {
      if (u in b.tops) below = +b.tops[u];
      if (below !== null) tops[u].push([+b.chainage, below]);
    }
  }
  for (const [u, pts] of Object.entries(tops)) if (!pts.length) throw new Error(`unit ${u} is not defined by any borehole`);

  const surfaceAt = (ch) => interp(surface, ch);
  const waterAt = (ch) => interp(water, ch);
  const axisAt = (ch) => interp(axis, ch);
  function column(ch) {
    const surf = surfaceAt(ch), t = [];
    let above = surf;
    for (const u of order) { above = Math.min(interp(tops[u], ch), above); t.push(above); }
    const out = [];
    order.forEach((u, i) => {
      const base = i + 1 < t.length ? t[i + 1] : -1e9;
      if (t[i] > base) out.push({ unit: u, top: t[i], base });
    });
    return out;
  }
  function unitAt(ch, level) {
    for (const l of column(ch)) if (l.base < level && level <= l.top) return l.unit;
    return order.at(-1);
  }
  function porePressure(ch, level, gammaW = 10) {
    const unit = units[unitAt(ch, level)];
    const head = (unit.water ?? "upper") === "lower" && deep ? interp(deep, ch) : waterAt(ch);
    return Math.max(head - level, 0) * gammaW * +(unit.pore_pressure_ratio ?? 1);
  }
  function weighted(ch, top, base, key) {
    let total = 0;
    const shares = {};
    for (const l of column(ch)) {
      const h = Math.max(Math.min(l.top, top) - Math.max(l.base, base), 0);
      if (h > 0) { shares[l.unit] = (shares[l.unit] ?? 0) + h; total += h * +units[l.unit][key]; }
    }
    const span = Object.values(shares).reduce((a, v) => a + v, 0);
    return [span > 0 ? total / span : 0, span > 0 ? Object.fromEntries(Object.entries(shares).map(([u, h]) => [u, h / span])) : {}];
  }
  function face(ch, diameter, axisLevel = null) {
    const ax = axisLevel ?? axisAt(ch), surf = surfaceAt(ch), r = diameter / 2;
    const crown = ax + r, invert = ax - r;
    const [gamma] = weighted(ch, surf, crown, "gamma");
    const [phi, shares] = weighted(ch, crown, invert, "phi");
    const [c] = weighted(ch, crown, invert, "c");
    const [e] = weighted(ch, crown, invert, "E");
    const unit = unitAt(ch, ax), u = porePressure(ch, ax);
    return { unit_at_axis: unit, units_on_face: shares, gamma, phi, c, k0: +units[unit].k0, e_soil: e, cover: surf - crown, axis_depth: surf - ax,
      water_depth: Math.max(surf - waterAt(ch), 0), u_axis: u, water_depth_equiv: surf - ax - u / 10 };
  }
  return { data, units, order, length: +data.alignment.length, boreholes: bhs, surfaceAt, waterAt, axisAt, column, unitAt, porePressure, face };
}
