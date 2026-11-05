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
