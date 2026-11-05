// Face support pressure: wedge-silo limit equilibrium (Horn 1961; Janssen 1895; Anagnostou & Kovári 1994),
// Vermeer et al. (2002) cohesionless limit, and the DAUB (2016) operating window.
// Twin of models/py/tunnelsim_models/face_support.py, which documents the equations. m, kPa, kN/m^3, degrees.

export const GAMMA_W = 10;

// Common defaults; not checked against the DAUB document here, so verify per project.
export const DAUB_DEFAULTS = Object.freeze({ eta_earth: 1.5, eta_water: 1.05, max_fraction_of_overburden: 0.9 });

const rad = (d) => (d * Math.PI) / 180;

/** Janssen/Terzaghi vertical stress at `depth` in a prism of plan B x L (kPa), never below zero. */
export function siloStress(depth, width, length, gamma, c, phiDeg, k = 0.8, q = 0) {
  if (depth <= 0) return Math.max(q, 0);
  const r = (width * length) / (2 * (width + length));
  const kt = k * Math.tan(rad(phiDeg));
  if (kt < 1e-12) return Math.max(q + (gamma - c / r) * depth, 0);
  const e = Math.exp((-kt * depth) / r);
  return Math.max(((r * gamma - c) / kt) * (1 - e) + q * e, 0);
}

function layeredSilo(cover, b, length, gamma, gammaSub, c, phi, k, q, waterDepth) {
  const hw = Math.min(Math.max(waterDepth, 0), cover);
  const s = siloStress(hw, b, length, gamma, c, phi, k, q);
  return siloStress(cover - hw, b, length, gammaSub, c, phi, k, s);
}

/**
 * Required effective face support (wedge-silo). cover = crown depth; opts.waterDepth = water table depth.
 * Returns { s_eff, theta_deg, wedge_length, silo_stress, u_crown, u_axis, side }.
 */
export function wedgeSilo(diameter, cover, gamma, phiDeg, c = 0,
  { gammaSub = null, waterDepth = Infinity, q = 0, kSilo = 0.8, kWedge = null } = {}) {
  if (diameter <= 0 || cover <= 0) throw new RangeError("diameter and cover must be positive");
  if (!(phiDeg >= 0 && phiDeg < 90)) throw new RangeError("phi must be in [0, 90) degrees");
  const gsub = gammaSub ?? gamma - GAMMA_W;
  const kw = kWedge ?? 1 - Math.sin(rad(phiDeg));
  const b = (diameter * Math.sqrt(Math.PI)) / 2, h = b;
  const gWedge = waterDepth <= cover + h / 2 ? gsub : gamma;
  const tp = Math.tan(rad(phiDeg));

  const support = (thetaDeg) => {
    const th = rad(thetaDeg);
    const length = h / Math.tan(th);
    const sv = layeredSilo(cover, b, length, gamma, gsub, c, phiDeg, kSilo, q, waterDepth);
    const g = (b * h * length * gWedge) / 2;
    const v = sv * b * length;
    const t = (c * h * length) / 2 + tp * kw * length * ((sv * h) / 2 + (gWedge * h * h) / 6);
    const aS = (b * h) / Math.sin(th);
    const s = ((g + v) * (Math.sin(th) - Math.cos(th) * tp) - c * aS - 2 * t) / (Math.cos(th) + Math.sin(th) * tp);
    return [s, length, sv];
  };

  // grid search then golden-section refinement, as in the Python reference
  let best = 1, bestS = -Infinity;
  for (let i = 0; i < 177; i++) {
    const a = 1 + 0.5 * i, s = support(a)[0];
    if (s >= bestS) { bestS = s; best = a; }
  }
  let lo = Math.max(best - 0.5, 0.5), hi = Math.min(best + 0.5, 89.5);
  const gr = (Math.sqrt(5) - 1) / 2;
  for (let n = 0; n < 60; n++) {
    const a1 = hi - gr * (hi - lo), a2 = lo + gr * (hi - lo);
    if (support(a1)[0] < support(a2)[0]) lo = a1;
    else hi = a2;
  }
  const theta = (lo + hi) / 2;
  const [s, length, sv] = support(theta);
  return {
    s_eff: s / (b * h),
    theta_deg: theta,
    wedge_length: length,
    silo_stress: sv,
    u_crown: GAMMA_W * Math.max(cover - waterDepth, 0),
    u_axis: GAMMA_W * Math.max(cover + diameter / 2 - waterDepth, 0),
    side: b,
  };
}

/** Vermeer et al. (2002) limit support pressure for cohesionless drained ground, cover > D (kPa). */
export function vermeerLimit(diameter, gamma, phiDeg) {
  if (!(phiDeg >= 20 && phiDeg <= 45)) throw new RangeError("fit valid for phi between 20 and 45 degrees");
  return gamma * diameter * (1 / (9 * Math.tan(rad(phiDeg))) - 0.05);
}

/** Operating window for the support pressure (DAUB 2016 structure, factors as parameters). */
export function daubWindow(fs, diameter, cover, gamma, {
  gammaSub = null, waterDepth = Infinity, q = 0, supportUnitWeight = 12,
  etaEarth = DAUB_DEFAULTS.eta_earth, etaWater = DAUB_DEFAULTS.eta_water,
  maxFraction = DAUB_DEFAULTS.max_fraction_of_overburden,
} = {}) {
  const gsub = gammaSub ?? gamma - GAMMA_W;
  const hw = Math.min(Math.max(waterDepth, 0), cover);
  // a negative water depth is free water above the ground (a river): its weight adds to the total overburden
  const sigmaCrown = q + gamma * hw + (gsub + GAMMA_W) * (cover - hw) + GAMMA_W * Math.max(-waterDepth, 0);
  const dz = (diameter / 2) * supportUnitWeight;
  const pMinAxis = etaEarth * Math.max(fs.s_eff, 0) + etaWater * fs.u_axis;
  const pMaxCrown = maxFraction * sigmaCrown;
  const pMinCrown = Math.max(pMinAxis - dz, 0);
  return {
    p_min_axis: pMinAxis,
    p_max_axis: pMaxCrown + dz,
    p_min_crown: pMinCrown,
    p_max_crown: pMaxCrown,
    overburden_crown: sigmaCrown,
    feasible: pMinCrown <= pMaxCrown,
  };
}
