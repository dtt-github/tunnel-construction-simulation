// Slurry shield (Mixshield): filter cake and penetration (DAUB 2016; DIN 4126; Broere & van Tol 2000), support
// transfer, air-cushion control (project derivation), slurry-circuit mass balance and Durand deposition limit.
// Twin of models/py/tunnelsim_models/slurry.py, which documents the sources. Units: m, s, kPa, kN/m^3, m^3/s, t/m^3.

const G = 9.81;
const P_ATM = 101.325;
export const DIN4126_MEMBRANE_F_S0 = 200;
export const CONTROL_TOLERANCE = Object.freeze({ slurry: 10, epb: 30 });

export const stagnationGradient = (tauF, d10) => (3.5 * tauF) / d10;
export const penetrationDepth = (dp, tauF, d10, alpha = 3.5) => (dp * d10) / (alpha * tauF);
export const formsMembrane = (tauF, d10) => stagnationGradient(tauF, d10) >= DIN4126_MEMBRANE_F_S0;
export const penetrationAt = (t, eMax, a) => (eMax * t) / (a + t);

export function infiltration(dp, tauF, d10, wedgeLength, alpha = 3.5, tBetweenPasses = null, aHalf = null) {
  const fs = stagnationGradient(tauF, d10);
  const eMax = penetrationDepth(dp, tauF, d10, alpha);
  if (fs >= DIN4126_MEMBRANE_F_S0) return { f_s0: fs, membrane: true, e_max: eMax, e_t: 0, dp_cake: dp, dp_excess: 0, transfer: 1 };
  const eT = tBetweenPasses === null || aHalf === null ? eMax : penetrationAt(tBetweenPasses, eMax, aHalf);
  const dpCake = Math.min((eT * alpha * tauF) / d10, dp);
  return { f_s0: fs, membrane: false, e_max: eMax, e_t: eT, dp_cake: dpCake, dp_excess: dp - dpCake, transfer: Math.max(0, 1 - eT / wedgeLength) };
}
export const excessPorePressure = (x, dpExcess, k, aquiferThickness, resistance) => dpExcess * Math.exp(-x / Math.sqrt(k * aquiferThickness * resistance));

/** Air cushion: level from the flow balance, isothermal air, first-order regulator back to the setpoint. */
export function cushion(chamberArea, tauRegulator = 5) {
  return {
    chamberArea,
    tauRegulator,
    step(st, dt, qFeed, qExc, qDis, setpoint) {
      const dh = ((qFeed + qExc - qDis) * dt) / chamberArea;
      const vNew = Math.max(st.air_volume - dh * chamberArea, 0.05);
      let p = ((st.p_air + P_ATM) * st.air_volume) / vNew - P_ATM;
      p += (setpoint - p) * (1 - Math.exp(-dt / tauRegulator));
      return { p_air: p, level: st.level + dh, air_volume: vNew };
    },
  };
}
export const facePressure = (pAir, level, z, slurryUnitWeight = 11) => pAir + slurryUnitWeight * (level - z);

export const drySolidsFlow = (qFeed, rhoFeed, qDis, rhoDis, rhoSolid = 2.65, rhoW = 1) => (qDis * (rhoDis - rhoW) - qFeed * (rhoFeed - rhoW)) / (rhoSolid - rhoW);
export const theoreticalDryFlow = (area, advance, rhoInsitu, rhoSolid = 2.65, rhoW = 1) => (area * advance * (rhoInsitu - rhoW)) / (rhoSolid - rhoW);
export function dischargeDensity(qFeed, rhoFeed, area, advance, rhoInsitu) {
  const qExc = area * advance, qDis = qFeed + qExc;
  return [qDis, (qFeed * rhoFeed + qExc * rhoInsitu) / qDis];
}
export const durandVelocity = (pipeDiameter, fL = 1.34, rhoSolid = 2.65, rhoFluid = 1) => fL * Math.sqrt(((2 * G * (rhoSolid - rhoFluid)) / rhoFluid) * pipeDiameter);
export const pipeVelocity = (q, pipeDiameter) => q / ((Math.PI * pipeDiameter ** 2) / 4);
