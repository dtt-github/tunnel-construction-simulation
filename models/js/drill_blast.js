// Drill & blast: round design (Holmberg cut, Olofsson burden, smooth contour, NFF spacings), Kuz-Ram fragmentation,
// ground vibration (scaled distance, SS 460 48 66), overbreak, Norwegian support classes and the round cycle.
// Twin of models/py/tunnelsim_models/drill_blast.py, which documents the sources. Units: m, kg, kg/m^3, mm/s, h.

export const equivalentEmptyDiameter = (dEmpty, n) => dEmpty * Math.sqrt(n);

export function holeDepth(dEmpty) {
  if (!(dEmpty >= 0.05 && dEmpty <= 0.25)) throw new RangeError("empty-hole diameter outside 0.05-0.25 m");
  return 0.15 + 34.1 * dEmpty - 39.4 * dEmpty ** 2;
}
export const advance = (depth) => 0.95 * depth;

export function emptyHolesForDepth(depth, dEmpty = 0.102) {
  for (let n = 1; n <= 12; n++) {
    const de = equivalentEmptyDiameter(dEmpty, n);
    if (de <= 0.25 && holeDepth(de) >= depth) return n;
  }
  throw new RangeError("depth not reachable with up to 12 empty holes");
}

export function firstCutBurden(dEmpty, depth = 0, angularDev = 0, collarDev = 0) {
  if (angularDev === 0 && collarDev === 0) return 1.5 * dEmpty;
  return 1.7 * dEmpty - (angularDev * depth + collarDev);
}

export function cutSections(dEmpty, pull, nMax = 6) {
  const w = [1.5 * dEmpty * Math.SQRT2];
  while (w.at(-1) < 0.8 * Math.sqrt(pull) && w.length < nMax) w.push(1.5 * w.at(-1) * Math.SQRT2);
  return w;
}

export function bottomCharge(dHoleMm, density, aws) {
  const d = dHoleMm / 1000;
  return ((Math.PI * d * d) / 4) * density * 1000 * aws;
}
export const burden = (dHoleMm, qb, f = 1) => (30 * qb * f) / dHoleMm;

export const HOLE_RULES = Object.freeze({
  stoping_up: { burden: 1.0, spacing: 1.1, bottom: 1 / 3, column: 0.5, stemming: 0.5 },
  stoping_down: { burden: 1.0, spacing: 1.2, bottom: 1 / 3, column: 0.5, stemming: 0.5 },
  roof: { burden: 0.9, spacing: 1.1, bottom: 1 / 6, column: 0.3, stemming: 0.5 },
  wall: { burden: 0.9, spacing: 1.1, bottom: 1 / 6, column: 0.4, stemming: 0.5 },
  floor: { burden: 1.0, spacing: 1.1, bottom: 1 / 3, column: 1.0, stemming: 0.2 },
});

export function smoothContour(dHoleMm, factor = 15) {
  const s = (factor * dHoleMm) / 1000;
  return [s, 1.25 * s];
}

export function horseshoe(width, wallHeight) {
  const r = width / 2;
  return [r, wallHeight + r, width * wallHeight + (Math.PI * r * r) / 2];
}

function inside(x, y, r, wallH, margin) {
  if (y < margin || Math.abs(x) > r - margin) return false;
  if (y <= wallH) return true;
  return Math.hypot(x, y - wallH) <= r - margin;
}

function ring(r, wallH, inset, spacing, y0) {
  const rr = r - inset, wall = Math.max(wallH - y0, 0), arc = Math.PI * rr, total = 2 * wall + arc;
  const n = Math.max(Math.floor(total / spacing + 0.5), 2);
  const pts = [];
  for (let k = 0; k <= n; k++) {
    const t = (total * k) / n;
    if (t <= wall) pts.push([-rr, y0 + t]);
    else if (t <= wall + arc) {
      const a = Math.PI - (t - wall) / rr;
      pts.push([rr * Math.cos(a), wallH + rr * Math.sin(a)]);
    } else pts.push([rr, wallH - (t - wall - arc)]);
  }
  return pts;
}

export const NFF_CONTOUR_MAX_SPACING = 0.7;
export const NFF_HELPER_MAX_SPACING = 0.9;

export function roundPattern(width, wallHeight, { dHoleMm = 48, dEmpty = 0.102, nEmpty = 4, density = 1.15, aws = 0.8, contourFactor = 15,
  contourSpacing = null, burdenFactor = 1 } = {}) {
  const [r, totalH] = horseshoe(width, wallHeight);
  const qb = bottomCharge(dHoleMm, density, aws);
  const b = burden(dHoleMm, qb) * burdenFactor;
  let [sC, bC] = smoothContour(dHoleMm, contourFactor);
  sC = contourSpacing !== null ? contourSpacing : Math.min(sC, NFF_CONTOUR_MAX_SPACING);
  const edge = 0.15;
  const holes = [];
  const cy = Math.min(1.5, totalH / 3);
  const de = equivalentEmptyDiameter(dEmpty, nEmpty);
  for (let k = 0; k < nEmpty; k++) {
    const a = (2 * Math.PI * k) / nEmpty + Math.PI / 4;
    holes.push({ x: 0.12 * Math.cos(a), y: cy + 0.12 * Math.sin(a), kind: "empty", delay: 0 });
  }
  let delay = 1;
  const secs = cutSections(de, advance(holeDepth(Math.min(de, 0.25))));
  secs.forEach((w, i) => {
    for (let k = 0; k < 4; k++) {
      const a = (Math.PI / 2) * k + (i % 2 === 0 ? Math.PI / 4 : 0);
      const rr = w / Math.SQRT2;
      holes.push({ x: rr * Math.cos(a), y: cy + rr * Math.sin(a), kind: "cut", delay: delay++ });
    }
  });
  const last = secs.length - 1;
  const nearCut = (x, y) => {
    const dx = Math.abs(x), dy = Math.abs(y - cy), w = secs[last];
    return last % 2 === 0 ? Math.max(dx, dy) < w / 2 + 0.75 * b : dx + dy < w / Math.SQRT2 + 0.75 * b;
  };
  const contour = ring(r, wallHeight, edge, sC, 0.15 + 0.6);
  const helper = ring(r, wallHeight, edge + bC, Math.min(NFF_HELPER_MAX_SPACING, 1.1 * b), 0.15 + b);
  const floorS = HOLE_RULES.floor.spacing * b;
  const nFloor = Math.max(Math.ceil((width - 2 * edge) / floorS), 1);
  const floorPts = [];
  for (let k = 0; k <= nFloor; k++) floorPts.push([-(r - edge) + (k * (width - 2 * edge)) / nFloor, 0.15]);
  const stoping = [];
  const sb = HOLE_RULES.stoping_up.spacing * b;
  const ny = Math.floor(totalH / b) + 2;
  for (let j = 0; j < ny; j++) {
    const y = 0.15 + b * j;
    const nx = Math.floor(width / sb) + 1;
    for (let i = -nx; i <= nx; i++) {
      const x = i * sb + (j % 2 ? sb / 2 : 0);
      if (!inside(x, y, r, wallHeight, edge + bC + 0.8 * b) || y < 0.15 + 0.8 * b || nearCut(x, y)) continue;
      stoping.push([x, y]);
    }
  }
  // stable sort by distance from the cut, as Python's sort
  stoping.sort((p, q) => Math.hypot(p[0], p[1] - cy) - Math.hypot(q[0], q[1] - cy));
  for (const [x, y] of stoping) holes.push({ x, y, kind: "stoping", delay: delay++ });
  for (const [kind, pts] of [["helper", helper], ["floor", floorPts], ["contour", contour]]) {
    for (const [x, y] of pts) holes.push({ x, y, kind, delay });
    delay++;
  }
  return holes;
}

export function holeCharge(hole, depth, wallHeight, qb, dHoleMm = 48) {
  if (hole.kind === "empty") return 0;
  let rule = { cut: "stoping_up", stoping: "stoping_up", helper: "stoping_up", floor: "floor" }[hole.kind];
  if (!rule) rule = hole.y > wallHeight ? "roof" : "wall";
  const rr = HOLE_RULES[rule];
  const b = burden(dHoleMm, qb);
  const bottom = rr.bottom * depth, stem = rr.stemming * b;
  const column = Math.max(depth - bottom - stem, 0);
  return qb * bottom + rr.column * qb * column;
}

export const DESIGNS = Object.freeze({
  textbook: { contourSpacing: null, burdenFactor: 1.0 },
  norwegian: { contourSpacing: 0.47, burdenFactor: 0.75 },
});

export function designRound(width, wallHeight, depth, { dHoleMm = 48, dEmpty = 0.102, density = 1.15, aws = 0.8, design = "norwegian" } = {}) {
  const nEmpty = emptyHolesForDepth(depth, dEmpty);
  const holes = roundPattern(width, wallHeight, { dHoleMm, dEmpty, nEmpty, density, aws, ...DESIGNS[design] });
  const qb = bottomCharge(dHoleMm, density, aws);
  const kg = holes.map((h) => holeCharge(h, depth, wallHeight, qb, dHoleMm));
  const perDelay = new Map();
  holes.forEach((h, i) => { if (h.delay) perDelay.set(h.delay, (perDelay.get(h.delay) ?? 0) + kg[i]); });
  const [, , area] = horseshoe(width, wallHeight);
  const pull = advance(depth);
  const total = kg.reduce((a, v) => a + v, 0);
  const drill = depth * holes.length;
  return {
    holes, charges: kg, n_charged: holes.filter((h) => h.kind !== "empty").length, drill_metres: drill, explosive: total,
    specific_charge: total / (area * pull), specific_drilling: drill / (area * pull), max_charge_per_delay: Math.max(...perDelay.values()),
    pull, area,
  };
}

// ---------------------------------------------------------------- fragmentation, vibration, overbreak
export const kuzRamX50 = (rockFactor, powderFactor, chargePerHole, rws = 100, exponent = 19 / 30) =>
  rockFactor * powderFactor ** -0.8 * chargePerHole ** (1 / 6) * (115 / rws) ** exponent;

export const uniformityIndex = (b, s, dHoleMm, deviation, chargeLength, bench, bottomLen = 0, columnLen = 0) =>
  (2.2 - (14 * b) / dHoleMm) * Math.sqrt((1 + s / b) / 2) * (1 - deviation / b)
  * (Math.abs(bottomLen - columnLen) / chargeLength + 0.1) ** 0.1 * (chargeLength / bench);

export const retained = (x, x50, n) => Math.exp(-0.693 * (x / x50) ** n);

export const NORTHERN_LINK = Object.freeze({ A: 1072, B: -1.54, sigma_log10: 0.19 });
export const ppv = (distance, charge, a = NORTHERN_LINK.A, b = NORTHERN_LINK.B) => a * (distance / Math.sqrt(charge)) ** b;
export function maxChargePerDelay(distance, vLimit, a = NORTHERN_LINK.A, b = NORTHERN_LINK.B) {
  const sd = (vLimit / a) ** (1 / b);
  return (distance / sd) ** 2;
}

export const SS4604866_V0 = Object.freeze({ rock: 70, moraine: 35, clay: 18 });
export const SS4604866_FD = Object.freeze({ rock: [2.57, 0.42], sand_gravel: [1.91, 0.29], clay: [1.56, 0.19] });
export function ss4604866Limit(distance, { foundation = "rock", groundPath = "rock", fB = 1, fM = 1, fT = 1 } = {}) {
  const [c, k] = SS4604866_FD[groundPath];
  return SS4604866_V0[foundation] * fB * fM * fT * c * Math.min(Math.max(distance, 1), 350) ** -k;
}

export const overbreakPercent = (actual, payable) => ((actual - payable) / payable) * 100;

// ---------------------------------------------------------------- support classes and cycle
export const SUPPORT_CLASSES = Object.freeze({
  I: { q: [10, 1000], roof_bolt: 2.5, wall_bolt: null, roof_sc: 0.08, wall_sc: 0.0, rrs: false },
  II: { q: [4, 10], roof_bolt: 2.0, wall_bolt: null, roof_sc: 0.08, wall_sc: 0.08, rrs: false },
  III: { q: [1, 4], roof_bolt: 1.7, wall_bolt: 2.0, roof_sc: 0.10, wall_sc: 0.08, rrs: false },
  IV: { q: [0.01, 1], roof_bolt: 1.3, wall_bolt: 1.5, roof_sc: 0.15, wall_sc: 0.10, rrs: true },
});
export const SPOT_BOLTS_PER_ROUND = 4;

export const RATES = Object.freeze({
  drill_m_per_min: 2.0, move_min_per_hole: 0.5, reamer_min_per_hole: 8.0, booms: 3, charge_min_per_hole: 0.6, connect_blast_h: 0.5,
  ventilation_h: 0.5, scaling_h: 1.0, muck_m3_per_h: 200.0, bolts_per_h: 12.0, shotcrete_m3_per_h: 6.0, rrs_h: 3.0, survey_h: 0.3,
});

export function supportQuantities(width, wallHeight, pull, cls) {
  const c = SUPPORT_CLASSES[cls];
  const roofLen = (Math.PI * width) / 2;
  const wallLen = 2 * Math.max(wallHeight - 1.5, 0);
  let bolts = c.roof_bolt ? (roofLen * pull) / c.roof_bolt ** 2 : SPOT_BOLTS_PER_ROUND;
  if (c.wall_bolt) bolts += (2 * wallHeight * pull) / c.wall_bolt ** 2;
  return { bolts: Math.ceil(bolts), shotcrete: (roofLen * c.roof_sc + wallLen * c.wall_sc) * pull, rrs: c.rrs };
}

export function roundCycle(rd, width, wallHeight, cls, { overbreak = 0.15, hoursPerWeek = 110, rates = {} } = {}) {
  const k = { ...RATES, ...rates };
  const drilled = rd.holes.filter((h) => h.kind !== "empty").length;
  const nEmpty = rd.holes.length - drilled;
  const depth = rd.drill_metres / rd.holes.length;
  const drillH = ((depth * drilled) / k.drill_m_per_min + drilled * k.move_min_per_hole) / k.booms / 60 + (nEmpty * k.reamer_min_per_hole) / 60;
  const muck = rd.area * (1 + overbreak) * rd.pull;
  const sup = supportQuantities(width, wallHeight, rd.pull, cls);
  const steps = [
    ["Survey and marking", k.survey_h],
    ["Drilling", drillH],
    ["Charging", (drilled * k.charge_min_per_hole) / 60],
    ["Connect and blast", k.connect_blast_h],
    ["Ventilation", k.ventilation_h],
    ["Scaling", k.scaling_h],
    ["Mucking", muck / k.muck_m3_per_h],
    ["Bolting", sup.bolts / k.bolts_per_h],
    ["Sprayed concrete", (sup.shotcrete * (1 + overbreak)) / k.shotcrete_m3_per_h + (sup.rrs ? k.rrs_h : 0)],
  ];
  const total = steps.reduce((a, [, h]) => a + h, 0);
  return { steps, total_h: total, pull: rd.pull, m_per_week: (hoursPerWeek / total) * rd.pull, muck_m3: muck };
}
