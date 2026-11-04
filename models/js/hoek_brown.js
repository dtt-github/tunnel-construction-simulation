// Generalised Hoek-Brown rock-mass parameters. Twin of models/py/tunnelsim_models/hoek_brown.py.
// Hoek, Carranza-Torres & Corkum (2002); Hoek & Diederichs (2006). Stresses and moduli in MPa.

/**
 * @param {number} gsi Geological Strength Index [0, 100]
 * @param {number} mi intact-rock constant
 * @param {number} sigmaCi intact UCS, MPa
 * @param {number} [d=0] disturbance factor [0, 1]
 * @param {number|null} [eI=null] intact modulus, MPa
 */
export function hoekBrown(gsi, mi, sigmaCi, d = 0, eI = null) {
  if (!(gsi >= 0 && gsi <= 100)) throw new RangeError("GSI must be in [0, 100]");
  if (!(d >= 0 && d <= 1)) throw new RangeError("D must be in [0, 1]");
  const mb = mi * Math.exp((gsi - 100) / (28 - 14 * d));
  const s = Math.exp((gsi - 100) / (9 - 3 * d));
  const a = 0.5 + (Math.exp(-gsi / 15) - Math.exp(-20 / 3)) / 6;
  const sigma_cm = (sigmaCi * ((mb + 4 * s - a * (mb - 8 * s)) * (mb / 4 + s) ** (a - 1))) / (2 * (1 + a) * (2 + a));
  const e_rm = eI == null ? null : eI * (0.02 + (1 - d / 2) / (1 + Math.exp((60 + 15 * d - gsi) / 11)));
  return { mb, s, a, sigma_cm, sigma_c_mass: sigmaCi * s ** a, e_rm };
}

export function sigma1AtFailure(sigma3, sigmaCi, p) {
  return sigma3 + sigmaCi * (p.mb * sigma3 / sigmaCi + p.s) ** p.a;
}
