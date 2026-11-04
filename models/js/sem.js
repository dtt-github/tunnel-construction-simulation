// Sprayed concrete lining (SEM/NATM): shotcrete ageing (Oreste 2003; MC90 fit; EN 14487 classes), ageing-ring
// interaction with the ground reaction curve during advance (Oreste 2003), sequence rules (FHWA 2009) and convergence
// monitoring (Sulem et al. 1987; Crossrail trigger levels). Twin of models/py/tunnelsim_models/sem.py, which documents
// the sources. Units: m, MPa, hours unless stated.

import { groundReaction, pressureForDisplacement, ringSupport } from "./ground_response.js";

export const SHOTCRETE = Object.freeze({
  oreste_example: { e0: 12000, alpha: 0.05, sc0: 27, beta: 0.025, nu: 0.15, source: "Oreste (2003) Table 3" },
  kielder: { e0: 28000, alpha: 0.0187, sc0: 35, beta: 0.0187, nu: 0.15, source: "Oreste (2003) Table 5" },
});
export const BRENNER_SHOTCRETE = Object.freeze([[6, 5.46, null], [8, 6.01, null], [16, 14.85, null], [24, 18.57, 13943], [48, 20.64, 18054],
  [72, 28.63, 19410], [168, 32.9, 21485], [672, 40.84, 21537]]);

export const shotcreteModulus = (tH, preset = "kielder") => SHOTCRETE[preset].e0 * (1 - Math.exp(-SHOTCRETE[preset].alpha * Math.max(tH, 0)));
export const shotcreteStrength = (tH, preset = "kielder") => SHOTCRETE[preset].sc0 * (1 - Math.exp(-SHOTCRETE[preset].beta * Math.max(tH, 0)));
export function mc90Modulus(tDays, e28, e1) {
  const s = -Math.log(e1 / e28) / (Math.sqrt(28) - 1);
  return e28 * Math.exp(s * (1 - Math.sqrt(28 / tDays)));
}

const J_LINES = {
  A: [[10 / 60, 0.1], [1, 0.2], [12, 1.0], [24, 2.0]],
  B: [[0.1, 0.2], [0.5, 0.4], [12, 2.8], [24, 5.0]],
  C: [[0.1, 0.5], [0.5, 1.2], [12, 8.0], [24, 16.0]],
};
function loglog(points, t) {
  const lt = Math.log(t);
  const pts = points.map(([a, b]) => [Math.log(a), Math.log(b)]);
  for (let i = 0; i + 1 < pts.length; i++) {
    const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
    if (lt <= x1 || i + 2 === pts.length) return Math.exp(y0 + ((y1 - y0) * (lt - x0)) / (x1 - x0));
  }
  return Math.exp(pts.at(-1)[1]);
}
export function earlyStrengthClass(tH, strength) {
  if (!(tH >= 0.1 && tH <= 24)) throw new RangeError("classes are defined from 6 min to 24 h");
  if (strength < loglog(J_LINES.A, tH)) return "below J1";
  if (strength < loglog(J_LINES.B, tH)) return "J1";
  return strength < loglog(J_LINES.C, tH) ? "J2" : "J3";
}

export const fictitiousPressure = (x, p0, r0) => (0.72 * p0 * 0.845 * r0) / (Math.max(x, 0) + 0.845 * r0);
export const averageAdvanceRate = (vM, deadTimeH, step) => vM / (1 + (deadTimeH * vM) / step);

/** Oreste (2003) incremental interaction of an ageing closed shotcrete ring with the ground reaction curve. */
export function liningInteraction(p0, r0, eRock, nuRock, phiDeg, c, thickness, xInstall, advanceMPerH, preset = "kielder", steps = 400) {
  const nu = SHOTCRETE[preset].nu;
  const uStar = groundReaction(p0, Math.min(fictitiousPressure(xInstall, p0, r0), p0), r0, eRock, nuRock, phiDeg, c).u;
  const uFree = groundReaction(p0, 0, r0, eRock, nuRock, phiDeg, c).u;
  const du = (uFree - uStar) / steps;
  if (!(du > 0)) return { u_install: uStar, u_final: uStar, p_final: 0, hours_to_95: 0, min_safety: Infinity, min_safety_age_h: 0, history: [] };
  const geo = ringSupport(r0, thickness, 1, nu, 1);
  const stressPerE = (2 * r0) / ((1 + nu) * ((r0 - thickness) ** 2 + (1 - 2 * nu) * r0 ** 2));
  let pLin = 0, sig = 0, tPrev = 0, u = uStar, fsMin = Infinity, fsAge = 0;
  const hist = [];
  const result = () => ({ u_install: uStar, u_final: u, p_final: pLin, hours_to_95: hist.find((h) => h[3] >= 0.95 * pLin)[0], min_safety: fsMin, min_safety_age_h: fsAge, history: hist });
  for (let i = 0; i < steps; i++) {
    const ePrev = shotcreteModulus(tPrev, preset);
    u += du;
    pLin += geo.k * ePrev * du;
    sig += stressPerE * ePrev * du;
    const pFict = pressureForDisplacement(u, p0, r0, eRock, nuRock, phiDeg, c) - pLin;
    if (pFict <= 0) {
      const fs = sig > 0 ? shotcreteStrength(tPrev, preset) / sig : Infinity;
      hist.push([tPrev, null, u, pLin, fs]);
      if (fs < fsMin) { fsMin = fs; fsAge = tPrev; }
      return result();
    }
    const x = 0.845 * r0 * ((0.72 * p0) / pFict - 1);
    tPrev = Math.max((x - xInstall) / advanceMPerH, 0);
    const fs = sig > 0 ? shotcreteStrength(tPrev, preset) / sig : Infinity;
    if (fs < fsMin) { fsMin = fs; fsAge = tPrev; }
    hist.push([tPrev, x, u, pLin, fs]);
  }
  return result();
}

export const SEM_ROCK_CLASSES = Object.freeze({
  intact: { sequence: "full face or top heading + bench", lining_mm: [0, 50], support_lag_rounds: [3, 6], presupport: "none", ring_closure: false },
  stratified: { sequence: "top heading + bench", lining_mm: [100, 100], support_lag_rounds: [2, 3], presupport: "none", ring_closure: false },
  moderately_jointed: { sequence: "top heading + bench", lining_mm: [150, 200], support_lag_rounds: [1, 2], presupport: "local", ring_closure: false },
  blocky_seamy: { sequence: "top heading + bench", lining_mm: [200, 300], support_lag_rounds: [0, 1], presupport: "systematic spiling", ring_closure: false },
  crushed_squeezing: { sequence: "top heading, bench, invert, ring closure", lining_mm: [300, 400], support_lag_rounds: [0, 0], presupport: "grouted pipe spiles or pipe-arch canopy", ring_closure: true },
});
export const CYCLE = Object.freeze({ top_heading: [1.0, 1.75], bench: [2.0, 2.65], invert: [2.0, 3.35] });
export const ringClosureOk = (invertLagM, diameter, wet = false) => invertLagM <= (wet ? 0.75 : 1.0) * diameter;

export function sulemConvergence(x, tDays, cInf, xRef, tRef, m, n) {
  if (x <= 0) return 0;
  return cInf * (1 - (xRef / (xRef + x)) ** 2) * (1 + m * (1 - (tRef / (tRef + tDays)) ** n));
}
export const SULEM_EXAMPLE = Object.freeze({ x_over_d: 4.6 / 5.2, t_ref: 6.0, m: 5.7, n: 0.3 });
export const TRIGGERS = Object.freeze([["green", 0.75], ["amber", 1.05], ["red", 1.5]]);
export const FINAL_LINING_RATE_MM_PER_MONTH = 1.0;
export function triggerLevel(measured, predicted) {
  let level = "none";
  for (const [name, f] of TRIGGERS) if (measured >= f * predicted) level = name;
  return level;
}
