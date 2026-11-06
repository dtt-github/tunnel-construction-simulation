// Greenfield Gaussian settlement trough (Peck 1969; O'Reilly & New 1982; Attewell & Woodman 1982),
// volume-loss components along the drive (Mair & Taylor 1997) and twin-tunnel interaction (Addenbrooke & Potts 2001).
// Twin of models/py/tunnelsim_models/settlement.py, which documents the equations. Metres; volume loss as a fraction.

export const K_TYPICAL = Object.freeze({ stiff_clay: 0.5, soft_clay: 0.6, sand_gravel: 0.35 });

// VL and K: typical values from Mair & Taylor (1997). Split (face, shield, tail, behind the tail): illustrative,
// calibrate per project.
export const METHOD_PRESETS = Object.freeze({
  open_face_stiff_clay: Object.freeze({ volume_loss: 0.015, range: [0.01, 0.02], k: 0.5, split: [0.6, 0.3, 0.1, 0.0] }),
  scl_stiff_clay: Object.freeze({ volume_loss: 0.01, range: [0.005, 0.015], k: 0.5, split: [0.8, 0.2, 0.0, 0.0] }),
  closed_face_clay: Object.freeze({ volume_loss: 0.01, range: [0.005, 0.02], k: 0.5, split: [0.05, 0.15, 0.4, 0.4] }),
  closed_face_sand: Object.freeze({ volume_loss: 0.005, range: [0.002, 0.01], k: 0.35, split: [0.05, 0.15, 0.4, 0.4] }),
});

const BURLAND = [
  [0.05, 0, "Negligible"],
  [0.075, 1, "Very slight"],
  [0.15, 2, "Slight"],
  [0.3, 3, "Moderate"],
  [Infinity, 4, "Severe to very severe"],
];

// Abramowitz & Stegun 7.1.26 is too coarse for 1e-9 agreement; use a series/continued-fraction erf.
export function erf(x) {
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  if (x < 3) {
    // Maclaurin series
    let sum = x, term = x;
    for (let n = 1; n < 200; n++) {
      term *= (-x * x) / n;
      const add = term / (2 * n + 1);
      sum += add;
      if (Math.abs(add) < 1e-17 * Math.abs(sum)) break;
    }
    return sign * (2 / Math.sqrt(Math.PI)) * sum;
  }
  // Continued fraction for erfc (Lentz), accurate for x >= 3
  let f = x, C = x, D = 0;
  for (let n = 1; n < 200; n++) {
    const an = n / 2;
    D = x + an * D; D = 1 / D;
    C = x + an / C;
    const delta = C * D;
    f *= delta;
    if (Math.abs(delta - 1) < 1e-16) break;
  }
  return sign * (1 - Math.exp(-x * x) / (f * Math.sqrt(Math.PI)));
}

const phi = (z) => 0.5 * (1 + erf(z / Math.SQRT2));

/**
 * Gaussian trough. opts.kLeft / opts.kRight override k on either side (asymmetric trough);
 * opts.components = [[fraction, yBehindFaceM], ...] splits the volume loss along the drive; opts.iLong (m) sets the
 * longitudinal width (default: the mean transverse i).
 */
export function gaussianTrough(diameterM, axisDepthM, volumeLoss, k = 0.5, opts = {}) {
  if (axisDepthM <= diameterM / 2) throw new RangeError("axis depth must exceed the tunnel radius");
  const { kLeft = null, kRight = null, components = [[1, 0]], iLong = null } = opts;
  const il = (kLeft ?? k) * axisDepthM;
  const ir = (kRight ?? k) * axisDepthM;
  const sumW = components.reduce((s, [w]) => s + w, 0);
  if (Math.abs(sumW - 1) > 1e-9 || components.some(([w]) => w < 0)) {
    throw new RangeError("component fractions must be non-negative and sum to 1");
  }
  if (iLong !== null && !(iLong > 0)) throw new RangeError("iLong must be positive");
  const i = (il + ir) / 2;
  const vs = (volumeLoss * Math.PI * diameterM ** 2) / 4;
  const sMax = (2 * vs) / (Math.sqrt(2 * Math.PI) * (il + ir));
  const iSide = (x) => (x < 0 ? il : ir);
  const settlement = (x) => sMax * Math.exp(-(x * x) / (2 * iSide(x) ** 2));
  const longitudinalFraction = (y) => components.reduce((s, [w, yk]) => s + w * phi((y - yk) / (iLong ?? i)), 0);
  return {
    i,
    i_left: il,
    i_right: ir,
    volume_m3_per_m: vs,
    s_max: sMax,
    z0: axisDepthM,
    components: components.map(([w, y]) => [w, y]),
    i_long: iLong,
    settlement,
    horizontal: (x) => -(x / axisDepthM) * settlement(x),
    slope: (x) => -(x / iSide(x) ** 2) * settlement(x),
    /** Fraction of the final transverse trough developed at y (y > 0: behind the face). */
    longitudinalFraction,
    get fractionAtFace() {
      return longitudinalFraction(0);
    },
    /** yBehindFace > 0: point already passed by the face. */
    settlement3d: (x, yBehindFace) => settlement(x) * longitudinalFraction(yBehindFace),
  };
}

/**
 * Face (y = 0), shield passage (y = L/2), tail void (y = L) and behind-the-tail (y = L + behindOffsetM, default 2 L)
 * components. Zero-weight components are dropped.
 */
export function volumeLossComponents(face, shield, tail, shieldLengthM, behind = 0, behindOffsetM = null) {
  const total = face + shield + tail + behind;
  if (total <= 0 || Math.min(face, shield, tail, behind) < 0) {
    throw new RangeError("split must be non-negative with a positive sum");
  }
  const offset = behindOffsetM ?? shieldLengthM;
  return [[face, 0], [shield, shieldLengthM / 2], [tail, shieldLengthM], [behind, shieldLengthM + offset]]
    .filter(([w]) => w > 0)
    .map(([w, y]) => [w / total, y]);
}

/** Trough from METHOD_PRESETS; shield length defaults to 1.5 D (set it from the machine preset). */
export function presetTrough(method, diameterM, axisDepthM, { shieldLengthM = null, volumeLoss = null, k = null, iLong = null } = {}) {
  const p = METHOD_PRESETS[method];
  if (!p) throw new RangeError(`unknown method ${method}`);
  const length = shieldLengthM ?? 1.5 * diameterM;
  return gaussianTrough(diameterM, axisDepthM, volumeLoss ?? p.volume_loss, k ?? p.k, {
    components: volumeLossComponents(...p.split.slice(0, 3), length, ...p.split.slice(3)),
    iLong,
  });
}

/**
 * Two parallel tunnels, the second at x = spacing (either sign), driven after the first. Defaults give plain
 * superposition; secondVlFactor scales the second tunnel's volume loss and secondInnerK widens the arm of its
 * trough that faces the first tunnel (Addenbrooke & Potts 2001); secondOuterK sets the arm facing away (Wan et al. 2017).
 */
export function twinTroughs(diameterM, axisDepthM, spacingM, volumeLossFirst, volumeLossSecond = null, k = 0.5,
  { secondVlFactor = 1, secondInnerK = null, secondOuterK = null } = {}) {
  const vl2 = (volumeLossSecond ?? volumeLossFirst) * secondVlFactor;
  const first = gaussianTrough(diameterM, axisDepthM, volumeLossFirst, k);
  let second;
  const kIn = secondInnerK ?? k, kOut = secondOuterK ?? k;
  if (secondInnerK === null && secondOuterK === null) second = gaussianTrough(diameterM, axisDepthM, vl2, k);
  else if (spacingM >= 0) second = gaussianTrough(diameterM, axisDepthM, vl2, k, { kLeft: kIn, kRight: kOut });
  else second = gaussianTrough(diameterM, axisDepthM, vl2, k, { kLeft: kOut, kRight: kIn });
  return {
    first,
    second,
    spacing: spacingM,
    settlement: (x) => first.settlement(x) + second.settlement(x - spacingM),
    horizontal: (x) => first.horizontal(x) + second.horizontal(x - spacingM),
  };
}

export function burlandCategory(tensileStrainPercent) {
  for (const [limit, cat, name] of BURLAND) if (tensileStrainPercent < limit) return [cat, name];
}

// Volume loss from the face's load factor (Macklin 1999, quoted from Divall et al. 2023, open; Kimura & Mair 1981 for
// N at collapse). See settlement.py for the sources and limits.
export const KIMURA_MAIR_NTC_FACE_SUPPORTED = Object.freeze([[1.5, 7.05], [3.0, 9.0]]);

/** N at collapse for a closed-face shield (P/D 0), linear between Kimura & Mair's points, constant beyond them. */
export function criticalStabilityRatio(coverOverD) {
  const [[c0, n0], [c1, n1]] = KIMURA_MAIR_NTC_FACE_SUPPORTED;
  const t = Math.min(Math.max((coverOverD - c0) / (c1 - c0), 0), 1);
  return n0 + t * (n1 - n0);
}

/** LF = N / N_TC, N = (sigma_v - sigma_T) / S_u at the axis (kPa). */
export function loadFactor(sigmaVAxis, supportAxis, suAxis, coverOverD) {
  if (!(suAxis > 0)) throw new RangeError("undrained strength must be positive");
  return Math.max(sigmaVAxis - supportAxis, 0) / suAxis / criticalStabilityRatio(coverOverD);
}

/** Macklin (1999): VL = 0.23 % x exp(4.4 LF), as a fraction (fitted for LF >= 0.2, overconsolidated clay). */
export function macklinVolumeLoss(lf) {
  return 0.0023 * Math.exp(4.4 * lf);
}

/** The larger of the base volume loss (measured for the drive) and Macklin's value at the face's load factor. */
export function faceVolumeLoss(baseVolumeLoss, lf) {
  return Math.max(baseVolumeLoss, macklinVolumeLoss(lf));
}

// Building bending stiffness and the deflection ratio (Potts & Addenbrooke 1997, as plotted by Mair 1997 Fig. 4,
// ISSMGE library, open; digitised to about +/-0.03). See settlement.py for the sources and limits. Horizontal-strain
// factors are not used: no open source gives them.
const LOG_RHO = [-7.0, -6.5, -6.0, -5.5, -5.0, -4.75, -4.5, -4.25, -4.0, -3.75, -3.5, -3.25, -3.0, -2.75, -2.5, -2.25, -2.0, -1.75, -1.5, -1.0, 0.0, 1.0];
export const M_DR_SAG = Object.freeze({
  "0.0": [1.40, 1.403, 1.396, 1.371, 1.323, 1.298, 1.249, 1.195, 1.136, 1.059, 0.987, 0.891, 0.786, 0.667, 0.530, 0.411, 0.304, 0.226, 0.157, 0.113, 0.096, 0.096],
  "0.2": [1.40, 1.40, 1.39, 1.36, 1.31, 1.273, 1.222, 1.151, 1.084, 1.004, 0.922, 0.834, 0.730, 0.606, 0.476, 0.367, 0.266, 0.189, 0.150, 0.110, 0.096, 0.096],
  "0.4": [1.344, 1.344, 1.335, 1.306, 1.212, 1.138, 1.046, 0.954, 0.841, 0.704, 0.581, 0.455, 0.323, 0.215, 0.143, 0.117, 0.103, 0.090, 0.080, 0.073, 0.050, 0.050],
  "0.6": [0.82, 0.809, 0.765, 0.686, 0.556, 0.463, 0.351, 0.220, 0.124, 0.065, 0.057, 0.057, 0.057, 0.055, 0.050, 0.050, 0.046, 0.046, 0.042, 0.038, 0.040, 0.040],
});
export const M_DR_HOG = Object.freeze({
  "0.2": [1.40, 1.39, 1.376, 1.332, 1.218, 1.118, 1.000, 0.842, 0.632, 0.354, 0.190, 0.185, 0.180, 0.178, 0.178, 0.178, 0.172, 0.172, 0.170, 0.168, 0.168, 0.168],
  "0.4": [1.42, 1.42, 1.418, 1.408, 1.356, 1.320, 1.246, 1.172, 1.076, 0.964, 0.812, 0.626, 0.442, 0.304, 0.212, 0.178, 0.172, 0.172, 0.170, 0.168, 0.168, 0.168],
  "0.6": [1.42, 1.42, 1.418, 1.408, 1.394, 1.375, 1.356, 1.324, 1.280, 1.218, 1.130, 1.026, 0.880, 0.726, 0.548, 0.396, 0.274, 0.190, 0.174, 0.168, 0.168, 0.168],
});

function interp(xs, ys, x) {
  if (x <= xs[0]) return ys[0];
  for (let k = 1; k < xs.length; k++) {
    if (x <= xs[k]) return ys[k - 1] + ((x - xs[k - 1]) / (xs[k] - xs[k - 1])) * (ys[k] - ys[k - 1]);
  }
  return ys.at(-1);
}

/** M_DR for "sag" or "hog" at relative bending stiffness rho* (1/m) and eccentricity e/B (clamped to 0-0.6). */
export function deflectionModificationFactor(mode, rhoStar, eOverB) {
  const table = { sag: M_DR_SAG, hog: M_DR_HOG }[mode];
  const lr = Math.log10(Math.max(rhoStar, 1e-12));
  const es = Object.keys(table).map(Number).sort((a, b) => a - b);
  const e = Math.min(Math.max(eOverB, es[0]), es.at(-1));
  for (let k = 1; k < es.length; k++) {
    if (e <= es[k]) {
      const lo = es[k - 1], hi = es[k], t = (e - lo) / (hi - lo);
      return (1 - t) * interp(LOG_RHO, table[lo.toFixed(1)], lr) + t * interp(LOG_RHO, table[hi.toFixed(1)], lr);
    }
  }
  return interp(LOG_RHO, table[es[0].toFixed(1)], lr);
}

/** Assumed estimate of a framed building's EI per metre run (kN m^2/m): floor slabs bending together about mid-height. */
export function frameBendingStiffness(storeys, storeyHeight = 3.4, slabThickness = 0.15, eConcrete = 23e6) {
  const n = Math.max(Math.trunc(storeys), 1);
  const zs = Array.from({ length: n + 1 }, (_, k) => k * storeyHeight);
  const zm = zs.reduce((a, z) => a + z, 0) / zs.length;
  return eConcrete * zs.reduce((a, z) => a + slabThickness ** 3 / 12 + slabThickness * (z - zm) ** 2, 0);
}

/** rho* = EI / (E_s H^4), H = B / 2, in 1/m. */
export function relativeBendingStiffness(ei, soilModulus, width) {
  return ei / (soilModulus * (width / 2) ** 4);
}

/** Greenfield deflection ratio of a footprint across a trough: { sag: [L, DR] | null, hog: [L, DR] | null }. */
export function deflectionRatios(settlement, xMin, xMax, iLeft, iRight, n = 200) {
  const part = (a, b) => {
    if (b - a < 1) return null;
    const sa = settlement(a), sb = settlement(b);
    let d = 0;
    for (let k = 0; k <= n; k++) d = Math.max(d, Math.abs(settlement(a + ((b - a) * k) / n) - (sa + ((sb - sa) * k) / n)));
    return [b - a, d / (b - a)];
  };
  const sag = part(Math.max(xMin, -iLeft), Math.min(xMax, iRight));
  const hogs = [part(xMin, Math.min(xMax, -iLeft)), part(Math.max(xMin, iRight), xMax)].filter((h) => h !== null);
  return { sag, hog: hogs.length ? hogs.reduce((m, h) => (h[1] > m[1] ? h : m)) : null };
}
