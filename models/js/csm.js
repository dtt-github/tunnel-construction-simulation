// CSM disc-cutter model (Rostami & Ozdemir 1993; Rostami 1997). Twin of models/py/tunnelsim_models/csm.py.
// Lengths mm, stresses MPa, forces N.

export const C_DEFAULT = 2.12;

// Gauge-cutter speed limits (Rostami & Chang 2017) and the practical penetration maximum (Macias & Barton 2022);
// see csm.py for the sources.
export const GAUGE_SPEED_LIMIT_M_MIN = Object.freeze({ 432: 165, 483: 200 });
export const PRACTICAL_MAX_PENETRATION_MM = 15;
/** Cutterhead speed limit from the gauge-cutter linear speed. */
export const maxRpm = (headDiameterM, cutterDiameterMm = 482.6) =>
  (cutterDiameterMm <= 440 ? GAUGE_SPEED_LIMIT_M_MIN[432] : GAUGE_SPEED_LIMIT_M_MIN[483]) / (Math.PI * headDiameterM);

/** 19-inch constant-cross-section disc. */
export const DEFAULT_CUTTER = Object.freeze({
  diameter_mm: 482.6,
  tip_width_mm: 19.0,
  spacing_mm: 85.0,
  psi: -0.1, // back-analysed on Follo TBM1, Hansen (2018); see csm.py
  max_load_kn: 311.0, // 19" rated load, Robbins disc-cutter spec sheet
});

export function cutterForces(penetrationMm, ucsMpa, btsMpa, cutter = DEFAULT_CUTTER, c = C_DEFAULT) {
  if (penetrationMm <= 0) return { phi_rad: 0, p0_mpa: 0, total_n: 0, normal_n: 0, rolling_n: 0 };
  const r = cutter.diameter_mm / 2;
  if (penetrationMm >= r) throw new RangeError("penetration must be smaller than the cutter radius");
  const phi = Math.acos((r - penetrationMm) / r);
  const p0 = c * ((cutter.spacing_mm * ucsMpa ** 2 * btsMpa) / (phi * Math.sqrt(r * cutter.tip_width_mm))) ** (1 / 3);
  const ft = (cutter.tip_width_mm * r * phi * p0) / (1 + cutter.psi);
  return { phi_rad: phi, p0_mpa: p0, total_n: ft, normal_n: ft * Math.cos(phi / 2), rolling_n: ft * Math.sin(phi / 2) };
}

export function penetrationForNormalForce(normalForceN, ucsMpa, btsMpa, cutter = DEFAULT_CUTTER, c = C_DEFAULT) {
  if (normalForceN <= 0) return 0;
  let lo = 0;
  let hi = Math.min((cutter.diameter_mm / 2) * 0.25, 30.0);
  if (cutterForces(hi, ucsMpa, btsMpa, cutter, c).normal_n < normalForceN) return hi;
  for (let k = 0; k < 80; k++) {
    const mid = 0.5 * (lo + hi);
    if (cutterForces(mid, ucsMpa, btsMpa, cutter, c).normal_n < normalForceN) lo = mid;
    else hi = mid;
  }
  return 0.5 * (lo + hi);
}

/**
 * Steady-state hard-rock TBM performance for a given net cutting thrust. Drive: installed torque up to the speed where
 * it meets the installed power, then constant power. max_penetration_mm caps penetration per revolution.
 * @param {{thrust_kn:number,rpm:number,n_cutters:number,head_diameter_m:number,ucs_mpa:number,bts_mpa:number,
 *          max_torque_knm?:number|null,max_power_kw?:number|null,max_penetration_mm?:number|null,cutter?:object,
 *          torque_radius_factor?:number}} o
 */
export function tbmPerformance(o) {
  const cutter = o.cutter ?? DEFAULT_CUTTER;
  const k = ((o.torque_radius_factor ?? 0.3) * o.head_diameter_m * o.n_cutters) / 1000;
  const torqueAt = (p) => k * cutterForces(p, o.ucs_mpa, o.bts_mpa, cutter).rolling_n;
  let tmax = o.max_torque_knm ?? null;
  let byPower = false;
  if (o.max_power_kw != null && o.rpm > 0) {
    const tPower = (o.max_power_kw * 60) / (2 * Math.PI * o.rpm);
    if (tmax === null || tPower < tmax) { tmax = tPower; byPower = true; }
  }
  let p = penetrationForNormalForce((o.thrust_kn * 1000) / o.n_cutters, o.ucs_mpa, o.bts_mpa, cutter);
  let limited_by = "thrust";
  if (o.max_penetration_mm != null && p > o.max_penetration_mm) { p = o.max_penetration_mm; limited_by = "penetration"; }
  if (tmax !== null && torqueAt(p) > tmax) {
    let lo = 0;
    let hi = p;
    for (let i = 0; i < 80; i++) {
      const mid = 0.5 * (lo + hi);
      if (torqueAt(mid) < tmax) lo = mid;
      else hi = mid;
    }
    p = 0.5 * (lo + hi);
    limited_by = byPower ? "power" : "torque";
  }
  const f = cutterForces(p, o.ucs_mpa, o.bts_mpa, cutter);
  const torque = k * f.rolling_n;
  return {
    penetration_mm_rev: p,
    rop_m_h: (p * o.rpm * 60) / 1000,
    normal_per_cutter_kn: f.normal_n / 1000,
    rolling_per_cutter_kn: f.rolling_n / 1000,
    cutterhead_torque_knm: torque,
    cutterhead_power_kw: (torque * 2 * Math.PI * o.rpm) / 60,
    cutter_overloaded: f.normal_n / 1000 > cutter.max_load_kn,
    limited_by,
    thrust_used_kn: (f.normal_n * o.n_cutters) / 1000,
    torque_available_knm: tmax,
  };
}
