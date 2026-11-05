// Precast segmental lining: JSCE elastic equation method (ITA WG2 2000 Table II-2) with Wood's joint reduction, jacking
// stress and bursting under the shoes (ITA 2000; ITA 2019), annulus grout volume and pressure window, ring taper (DAUB).
// Twin of models/py/tunnelsim_models/lining.py, which documents the sources. Units: m, kN, kPa, kN/m^3, per metre.

export const woodInertia = (iFull, nSegments, iJoint = 0) => (nSegments <= 4 ? iFull : iJoint + (4 / nSegments) ** 2 * iFull);
export const subgradeModulus = (eSoil, radius) => eSoil / radius;

export function jsceRing(pV, qTop, qBottom, g, rc, ei, k, { anglesDeg = null, eta = 1, deadLoadInDeflection = false } = {}) {
  const angles = anglesDeg ?? Array.from({ length: 19 }, (_, i) => i * 10);
  const num = 2 * pV - qTop - qBottom + (deadLoadInDeflection ? Math.PI * g : 0);
  const delta = (num * rc ** 4) / (24 * (eta * ei + 0.045 * k * rc ** 4));
  const kd = k * delta, dq = qBottom - qTop;
  const moment = [], normal = [];
  for (const aDeg of angles) {
    const f = (aDeg * Math.PI) / 180, s = Math.sin(f), c = Math.cos(f);
    let m = ((1 - 2 * s * s) * pV * rc * rc) / 4 + ((1 - 2 * c * c) * qTop * rc * rc) / 4 + ((6 - 3 * c - 12 * c * c + 4 * c ** 3) * dq * rc * rc) / 48;
    let n = s * s * rc * pV + c * c * rc * qTop + ((c + 8 * c * c - 4 * c ** 3) * dq * rc) / 16;
    const fa = f <= Math.PI / 2 ? f : Math.PI - f, sa = Math.sin(fa), ca = Math.cos(fa);
    if (fa <= Math.PI / 4) {
      m += (0.2346 - 0.3536 * ca) * rc * rc * kd;
      n += 0.3536 * ca * rc * kd;
    } else {
      m += (-0.3487 + 0.5 * sa * sa + 0.2357 * ca ** 3) * rc * rc * kd;
      n += (-0.7071 * ca + ca * ca + 0.7071 * sa * sa * ca) * rc * kd;
    }
    if (f <= Math.PI / 2) {
      m += ((3 * Math.PI) / 8 - f * s - (5 * c) / 6) * rc * rc * g;
      n += (f * s - c / 6) * rc * g;
    } else {
      m += (-Math.PI / 8 + (Math.PI - f) * s - (5 * c) / 6 - 0.5 * Math.PI * s * s) * rc * rc * g;
      n += (-Math.PI * s + f * s + Math.PI * s * s - c / 6) * rc * g;
    }
    moment.push(m);
    normal.push(n);
  }
  return { angles_deg: angles, moment, normal, deflection: delta, reaction: kd };
}

export function ringLoads(depthAxis, radius, gamma, k0, waterDepth, gammaW = 10, surcharge = 0) {
  const at = (z) => {
    const hw = Math.min(Math.max(waterDepth, 0), z);
    return [surcharge + gamma * z, gammaW * Math.max(z - hw, 0)];
  };
  const [svc, uc] = at(depthAxis - radius), [svi, ui] = at(depthAxis + radius);
  return [svc, k0 * (svc - uc) + uc, k0 * (svi - ui) + ui];
}

/** Terzaghi-reduced vertical earth pressure (ITA WG2 2000, Formula 2.2.1) and the lateral loads; see lining.py. */
export function terzaghiLoads(depthAxis, radius, gamma, phiDeg, c, lam, waterDepth, gammaW = 10, surcharge = 0) {
  const h = depthAxis - radius, hw = Math.min(Math.max(waterDepth, 0), h);
  const g = (gamma * hw + (gamma - gammaW) * (h - hw)) / h;
  const t = Math.tan((phiDeg * Math.PI) / 180);
  const b1 = radius / Math.tan(Math.PI / 8 + (phiDeg * Math.PI) / 180 / 4);
  const e = Math.exp((-t * h) / b1);
  const h0 = Math.min((b1 * (1 - c / (b1 * g)) * (1 - e)) / t + (surcharge * e) / g, h + surcharge / g);
  const pe = g * Math.max(h0, 0);
  const uTop = gammaW * Math.max(h - waterDepth, 0), uBot = gammaW * Math.max(h + 2 * radius - waterDepth, 0);
  const gBelow = waterDepth <= h ? gamma - gammaW : gamma;
  return [pe + uTop, lam * pe + uTop, lam * (pe + gBelow * 2 * radius) + uBot];
}
export const activeCoefficient = (phiDeg) => Math.tan(((45 - phiDeg / 2) * Math.PI) / 180) ** 2;

export function sectionStresses(n, m, thickness, width = 1) {
  const a = width * thickness, w = (width * thickness ** 2) / 6;
  return [n / a + Math.abs(m) / w, n / a - Math.abs(m) / w];
}

export const ITA2000_ALLOWABLE = Object.freeze({ concrete_42: 15000, jacking_factor: 1.65 });

export function jackingStress(jackForce, nShoes, rc, thickness, gap = 0.1, eccentricity = 0.01) {
  const b = (2 * Math.PI * rc) / nShoes - gap, a = b * thickness, i = (b * thickness ** 3) / 12;
  return jackForce / a + (jackForce * eccentricity * (thickness / 2)) / i;
}

export function burstingForce(force, thickness, pad, edge = 0.03, method = "daub") {
  if (method === "aci") return [0.25 * force * (1 - pad / thickness), 0.5 * (thickness - 2 * edge)];
  return [0.25 * force * (1 - pad / (thickness - 2 * edge)), 0.4 * (thickness - 2 * edge)];
}

export const annulusVolume = (dExcavated, dRingOuter, ringWidth) => (Math.PI / 4) * (dExcavated ** 2 - dRingOuter ** 2) * ringWidth;

export function groutWindow(depthCrown, gamma, waterDepth, gammaW = 10, maxOverWater = 69) {
  const hw = Math.min(Math.max(waterDepth, 0), depthCrown);
  const u = gammaW * Math.max(depthCrown - hw, 0);
  return [u, Math.min(gamma * depthCrown, u + maxOverWater)];
}

export function taper(dOuter, ringWidth, curveRadius, offsetDeg = null) {
  let k = (dOuter * ringWidth) / curveRadius;
  if (offsetDeg !== null) k *= 2 / (1 + Math.cos((offsetDeg * Math.PI) / 180));
  return k;
}
