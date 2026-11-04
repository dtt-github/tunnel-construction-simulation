// Ground response around a circular tunnel: equivalent Mohr-Coulomb (Hoek et al. 2002), ground reaction curve (Duncan
// Fama 1993, as in Hoek), longitudinal displacement profile (Vlachopoulos & Diederichs 2009), squeezing (Hoek & Marinos
// 2000), support curves, and a screening estimate of shield friction (after Ramoni & Anagnostou 2010).
// Twin of models/py/tunnelsim_models/ground_response.py, which documents the equations and limits. m, MPa, MN.

import { hoekBrown } from "./hoek_brown.js";

const rad = (d) => (d * Math.PI) / 180;

export function equivalentMohrCoulomb(gsi, mi, sigmaCi, eI, p0, d = 0) {
  const hb = hoekBrown(gsi, mi, sigmaCi, d, eI);
  const s3max = 0.47 * hb.sigma_cm * (hb.sigma_cm / p0) ** -0.94;
  const s3n = s3max / sigmaCi;
  const { mb, s, a } = hb;
  const t = 6 * a * mb * (s + mb * s3n) ** (a - 1);
  const phi = (Math.asin(t / (2 * (1 + a) * (2 + a) + t)) * 180) / Math.PI;
  const c = (sigmaCi * ((1 + 2 * a) * s + (1 - a) * mb * s3n) * (s + mb * s3n) ** (a - 1)) / ((1 + a) * (2 + a) * Math.sqrt(1 + t / ((1 + a) * (2 + a))));
  return { phi_deg: phi, c, sigma_cm: hb.sigma_cm, e_rm: hb.e_rm, sigma3_max: s3max };
}

export function mcStrength(phiDeg, c) {
  const sp = Math.sin(rad(phiDeg));
  return [(2 * c * Math.cos(rad(phiDeg))) / (1 - sp), (1 + sp) / (1 - sp)];
}

export function groundReaction(p0, pi, r0, e, nu, phiDeg, c) {
  if (!(pi >= 0 && pi <= p0)) throw new RangeError("support pressure must be between 0 and p0");
  const [scm, k] = mcStrength(phiDeg, c);
  const pCr = (2 * p0 - scm) / (1 + k);
  let u, rp;
  if (pi >= pCr) { u = (r0 * (1 + nu) * (p0 - pi)) / e; rp = r0; } else {
    rp = r0 * ((2 * (p0 * (k - 1) + scm)) / ((1 + k) * ((k - 1) * pi + scm))) ** (1 / (k - 1));
    u = ((r0 * (1 + nu)) / e) * (2 * (1 - nu) * (p0 - pCr) * (rp / r0) ** 2 - (1 - 2 * nu) * (p0 - pi));
  }
  return { u, r_p: rp, p_cr: Math.max(pCr, 0), strain_percent: (100 * u) / r0 };
}

export function pressureForDisplacement(u, p0, r0, e, nu, phiDeg, c) {
  if (u <= 0) return p0;
  if (groundReaction(p0, 0, r0, e, nu, phiDeg, c).u <= u) return 0;
  let lo = 0, hi = p0;
  for (let n = 0; n < 100; n++) {
    const mid = 0.5 * (lo + hi);
    if (groundReaction(p0, mid, r0, e, nu, phiDeg, c).u > u) lo = mid;
    else hi = mid;
  }
  return 0.5 * (lo + hi);
}

export function ldp(x, r0, rP) {
  const rstar = Math.max(rP / r0, 1);
  const u0 = Math.exp(-0.15 * rstar) / 3;
  const xs = x / r0;
  return xs < 0 ? u0 * Math.exp(xs) : 1 - (1 - u0) * Math.exp((-1.5 * xs) / rstar);
}

export const SQUEEZING_CLASSES = Object.freeze([
  [1.0, "A", "Few support problems", "rock bolts and shotcrete"],
  [2.5, "B", "Minor squeezing", "bolts and shotcrete, sometimes light steel sets or lattice girders"],
  [5.0, "C", "Severe squeezing", "rapid installation, heavy steel sets embedded in shotcrete"],
  [10.0, "D", "Very severe squeezing, face stability problems", "forepoling and face reinforcement, steel sets in shotcrete"],
  [Infinity, "E", "Extreme squeezing", "forepoling, face reinforcement, yielding support"],
]);
export const squeezingStrain = (sigmaCm, p0, pi = 0) => (0.2 - (0.25 * pi) / p0) * (sigmaCm / p0) ** ((2.4 * pi) / p0 - 2);
export function squeezingClass(strainPercent) {
  const [, cls, problems, support] = SQUEEZING_CLASSES.find(([limit]) => strainPercent < limit);
  return [cls, problems, support];
}

export function ringSupport(r0, thickness, e, nu, sigmaC) {
  const ri = r0 - thickness;
  return { k: (e * (r0 ** 2 - ri ** 2)) / ((1 + nu) * r0 * ((1 - 2 * nu) * r0 ** 2 + ri ** 2)), p_max: (sigmaC / 2) * (1 - ri ** 2 / r0 ** 2) };
}
export const steelSetSupport = (r0, spacing, area, e = 207000, sigmaY = 245) => ({ k: (e * area) / (spacing * r0 ** 2), p_max: (1.5 * sigmaY * area) / (spacing * r0) });
export function boltSupport(r0, nBolts, rowSpacing, length, diameter, pullout, q = 0.143, e = 207000) {
  const sc = (2 * Math.PI * r0) / nBolts;
  return { k: 1 / (sc * rowSpacing * ((4 * length) / (Math.PI * diameter ** 2 * e) + q)), p_max: pullout / (sc * rowSpacing) };
}
export function combine(...supports) {
  const k = supports.reduce((a, s) => a + s.k, 0);
  return { k, p_max: k * Math.min(...supports.map((s) => s.p_max / s.k)) };
}

export function supportEquilibrium(p0, r0, e, nu, phiDeg, c, support, uInstall) {
  const gap = (u) => Math.min(support.k * Math.max(u - uInstall, 0), support.p_max) - pressureForDisplacement(u, p0, r0, e, nu, phiDeg, c);
  const uFree = groundReaction(p0, 0, r0, e, nu, phiDeg, c).u;
  if (uInstall >= uFree) return { pressure: 0, u: uFree, support_used: 0, fails: false };
  if (gap(uInstall + support.p_max / support.k) < 0) return { pressure: support.p_max, u: uFree, support_used: 1, fails: true };
  let lo = uInstall, hi = uInstall + support.p_max / support.k;
  for (let n = 0; n < 100; n++) {
    const mid = 0.5 * (lo + hi);
    if (gap(mid) < 0) lo = mid;
    else hi = mid;
  }
  const u = 0.5 * (lo + hi);
  const p = Math.min(support.k * (u - uInstall), support.p_max);
  return { pressure: p, u, support_used: p / support.p_max, fails: false };
}

export const SKIN_FRICTION_ROCK = Object.freeze({ sliding: 0.275, static: 0.425 });

export function shieldFriction(r0, shieldLength, overcut, p0, e, nu, phiDeg, c, mu = SKIN_FRICTION_ROCK.sliding, steps = 60) {
  const free = groundReaction(p0, 0, r0, e, nu, phiDeg, c);
  const u0 = free.u * ldp(0, r0, free.r_p);
  const pContact = pressureForDisplacement(overcut, p0, r0, e, nu, phiDeg, c);
  let total = 0, first = null;
  for (let i = 0; i < steps; i++) {
    const x = ((i + 0.5) * shieldLength) / steps;
    if (free.u * ldp(x, r0, free.r_p) - u0 > overcut) {
      if (first === null) first = x;
      total += (pContact * shieldLength) / steps;
    }
  }
  return { contact_from: first, mean_pressure: total / shieldLength, friction_force: mu * 2 * Math.PI * r0 * total };
}

export const gripperPressure = (installedThrust, shoeArea, factor = 2.0) => (factor * installedThrust) / shoeArea;
