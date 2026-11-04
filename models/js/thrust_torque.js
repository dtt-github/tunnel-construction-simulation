// Shield thrust and cutterhead torque as sums of components (Shi et al. 2011; Krause 1987 sanity bands).
// Twin of models/py/tunnelsim_models/thrust_torque.py, which documents the equations. m, kPa, kN, kNm.

const GAMMA_W = 10;

// Ranges vary by source and are not checked against the originals.
export const KRAUSE_ALPHA = Object.freeze([9, 23]); // kNm/m^3
export const THRUST_BETA = Object.freeze([500, 1200]); // kN/m^2

/** Vertical stress at `depth` (kPa); effective by default. */
export function verticalStress(depth, gamma, { gammaSub = null, waterDepth = Infinity, q = 0, effective = true } = {}) {
  const gsub = gammaSub ?? gamma - GAMMA_W;
  const hw = Math.min(Math.max(waterDepth, 0), depth);
  const sv = q + gamma * hw + gsub * (depth - hw);
  return effective ? sv : sv + GAMMA_W * (depth - hw);
}

/** Thrust components (kN). pAxis: support pressure at the axis (kPa); weights in kN. */
export function shieldThrust(diameter, shieldLength, axisDepth, gamma, pAxis, {
  gammaSub = null, waterDepth = Infinity, q = 0, k0 = 0.5, muShield = 0.3, contact = 1, shieldWeight = 0,
  tools = 0, tailSeal = 0, backupWeight = 0, muBackup = 0.1,
} = {}) {
  if (diameter <= 0 || shieldLength <= 0 || axisDepth <= diameter / 2) {
    throw new RangeError("need positive sizes and the axis deeper than the radius");
  }
  const sigmaN = (verticalStress(axisDepth, gamma, { gammaSub, waterDepth, q }) * (1 + k0)) / 2;
  const t = {
    face: (pAxis * Math.PI * diameter ** 2) / 4,
    shield: muShield * (contact * Math.PI * diameter * shieldLength * sigmaN + shieldWeight),
    tools,
    tail_seal: tailSeal,
    backup: muBackup * backupWeight,
  };
  t.total = t.face + t.shield + t.tools + t.tail_seal + t.backup;
  return t;
}

/** Torque of n scrapers/rippers with tangential force Ft (kN) at mean radius f R (kNm). */
export const toolTorque = (nTools, tangentialForce, radius, radiusFactor = 0.5) => nTools * tangentialForce * radiusFactor * radius;

/** Cutterhead torque components (kNm). sigmaN: radial ground stress on the rim (kPa). */
export function cutterheadTorque(diameter, pAxis, sigmaN, {
  openingRatio = 0.3, mu = 0.15, muRim = 0.3, muChamber = 0.1, rimWidth = 0.5, nArms = 0, armArea = 0, armRadius = 0,
  tools = 0, seals = 0,
} = {}) {
  if (!(openingRatio >= 0 && openingRatio < 1)) throw new RangeError("opening ratio must be in [0, 1)");
  const r = diameter / 2;
  const disc = (2 / 3) * Math.PI * (1 - openingRatio) * r ** 3 * pAxis;
  const t = {
    tools,
    face: mu * disc,
    rim: 2 * Math.PI * r * r * rimWidth * muRim * sigmaN,
    back: muChamber * disc,
    arms: nArms * muChamber * pAxis * armArea * armRadius,
    seals,
  };
  t.total = t.tools + t.face + t.rim + t.back + t.arms + t.seals;
  return t;
}

/** Empirical installed-torque (kNm) and thrust (kN) bands for this diameter. */
export const sanityBands = (d) => ({
  torque: [KRAUSE_ALPHA[0] * d ** 3, KRAUSE_ALPHA[1] * d ** 3],
  thrust: [THRUST_BETA[0] * d ** 2, THRUST_BETA[1] * d ** 2],
});
