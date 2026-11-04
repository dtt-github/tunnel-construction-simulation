// Greenfield Gaussian settlement trough (Peck 1969; O'Reilly & New 1982; Attewell & Woodman 1982).
// Twin of models/py/tunnelsim_models/settlement.py. Metres; volume loss as a fraction.

export const K_TYPICAL = Object.freeze({ stiff_clay: 0.5, soft_clay: 0.6, sand_gravel: 0.35 });

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

export function gaussianTrough(diameterM, axisDepthM, volumeLoss, k = 0.5) {
  if (axisDepthM <= diameterM / 2) throw new RangeError("axis depth must exceed the tunnel radius");
  const i = k * axisDepthM;
  const vs = (volumeLoss * Math.PI * diameterM ** 2) / 4;
  const sMax = vs / (Math.sqrt(2 * Math.PI) * i);
  const settlement = (x) => sMax * Math.exp(-(x * x) / (2 * i * i));
  return {
    i,
    volume_m3_per_m: vs,
    s_max: sMax,
    z0: axisDepthM,
    settlement,
    horizontal: (x) => -(x / axisDepthM) * settlement(x),
    slope: (x) => -(x / (i * i)) * settlement(x),
    /** yBehindFace > 0: point already passed by the face. */
    settlement3d: (x, yBehindFace) => settlement(x) * 0.5 * (1 + erf(yBehindFace / (i * Math.SQRT2))),
  };
}

export function burlandCategory(tensileStrainPercent) {
  for (const [limit, cat, name] of BURLAND) if (tensileStrainPercent < limit) return [cat, name];
}
