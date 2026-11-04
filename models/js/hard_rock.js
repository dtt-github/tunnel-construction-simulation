// Hard-rock TBM drive: cutter wear (Frenzel 2011), rock support by RMR class (Bieniawski 1989) and utilisation as
// downtime per km (Farrokh 2018, doi:10.22044/jme.2018.6815.1509). Twin of models/py/tunnelsim_models/hard_rock.py,
// which documents the sources. Units: m, m/h, h/km, MPa.

export const CUTTER_CHANGE_H = 66 / 60;

export function cutterLifeM3(cai) {
  if (!(cai > 0)) throw new RangeError("CAI must be positive");
  return 1026 / cai;
}
export const cuttersPerKm = (diameterM, cai) => (1000 * Math.PI * diameterM ** 2) / 4 / cutterLifeM3(cai);
export const cutterChangeHPerKm = (diameterM, cai, changeH = CUTTER_CHANGE_H) => cuttersPerKm(diameterM, cai) * changeH;
export function cutterDowntimeFarrokh(prMh, quartzPercent) {
  if (quartzPercent < 5) return 30;
  if (quartzPercent <= 20) return 178.38 * prMh ** -0.707;
  return 384.74 * prMh ** -0.745;
}

export const rmrFromGsi = (gsi) => gsi + 5;
export const RMR_CLASSES = Object.freeze([
  { class: "I", rmr: [81, 100], name: "Very good", bolts: "spot bolting only", shotcrete: "none", ribs: "none" },
  { class: "II", rmr: [61, 80], name: "Good", bolts: "locally in crown, 3 m long at 2.5 m, occasional mesh", shotcrete: "50 mm in crown where required", ribs: "none" },
  { class: "III", rmr: [41, 60], name: "Fair", bolts: "systematic 4 m at 1.5-2 m in crown and walls, mesh in crown", shotcrete: "50-100 mm in crown, 30 mm in sides", ribs: "none" },
  { class: "IV", rmr: [21, 40], name: "Poor", bolts: "systematic 4-5 m at 1-1.5 m, with mesh", shotcrete: "100-150 mm in crown, 100 mm in sides", ribs: "light to medium ribs at 1.5 m where required" },
  { class: "V", rmr: [0, 20], name: "Very poor", bolts: "systematic 5-6 m at 1-1.5 m, mesh, bolt the invert", shotcrete: "150-200 mm crown, 150 mm sides, 50 mm face", ribs: "medium to heavy ribs at 0.75 m, steel lagging, close the invert" },
]);
export const rmrClass = (rmr) => RMR_CLASSES.find((c) => rmr >= c.rmr[0]) ?? RMR_CLASSES.at(-1);

function interp(x, pts) {
  let a, b;
  if (x <= pts[0][0]) [a, b] = [pts[0], pts[1]];
  else if (x >= pts.at(-1)[0]) [a, b] = [pts.at(-2), pts.at(-1)];
  else { const i = pts.findIndex((p) => x <= p[0]); [a, b] = [pts[i - 1], pts[i]]; }
  return Math.max(a[1] + ((b[1] - a[1]) * (x - a[0])) / (b[0] - a[0]), 0);
}
const SUPPORT_OPEN_4M = [[40, 500], [70, 100], [80, 0]];
const SUPPORT_OPEN_10M = [[40, 700], [70, 100], [80, 0]];
const SUPPORT_SINGLE = [[20, 1000], [40, 225], [100, 225]];

/** Ground-support downtime (h/km) by RMR and machine ("open", "single", "double"). */
export function supportDowntime(rmr, diameterM, machine = "open") {
  if (machine === "open") {
    const a = interp(rmr, SUPPORT_OPEN_4M), b = interp(rmr, SUPPORT_OPEN_10M);
    return a + (b - a) * Math.min(Math.max((diameterM - 4) / 6, 0), 1);
  }
  if (machine === "single") return interp(rmr, SUPPORT_SINGLE);
  if (machine === "double") return rmr >= 50 ? 100 : interp(rmr, SUPPORT_SINGLE);
  throw new RangeError(`unknown machine ${machine}`);
}

export const MAINTENANCE_CLASSES = Object.freeze({ good: 75, normal: 150, poor: 300 });
export const TRANSPORT_CLASSES = Object.freeze({ very_good: 25, good: 50, normal: 150, poor: 350, very_poor: 500 });
export function tbmBreakdownDowntime(prMh, ucsMpa) {
  if (ucsMpa > 150) return 337.6 * Math.exp(-0.394 * prMh);
  if (ucsMpa >= 100) return 238.12 * Math.exp(-0.407 * prMh);
  return 149.15 * Math.exp(-0.407 * prMh);
}
export const backupDowntime = (prMh, haulage = "rail") => (haulage === "rail" ? 85.586 * Math.exp(-0.31 * prMh) : 36.873 * Math.exp(-0.195 * prMh));

/** Downtime per km and utilisation (Farrokh 2018). */
export function hardRockUtilisation(prMh, diameterM, {
  stroke_m = 1.8, regrip_min = 4, curve_radius_m = Infinity, ucs_mpa = 150, rmr = 60, machine = "open", haulage = "conveyor",
  cutter_h_per_km = null, quartz_percent = 10, maintenance = "normal", transport = "good", utilities = 40, survey = 12.5, other = 100,
} = {}) {
  if (!(prMh > 0)) throw new RangeError("penetration rate must be positive");
  const curve = Number.isFinite(curve_radius_m);
  const t = {
    boring: 1000 / prMh,
    regrip: (1000 * regrip_min) / (60 * stroke_m) + (curve ? 409000 / curve_radius_m ** 2 : 0),
    tbm_breakdown: tbmBreakdownDowntime(prMh, ucs_mpa),
    backup: backupDowntime(prMh, haulage),
    cutters: cutter_h_per_km === null ? cutterDowntimeFarrokh(prMh, quartz_percent) : cutter_h_per_km,
    support: supportDowntime(rmr, diameterM, machine),
    maintenance: MAINTENANCE_CLASSES[maintenance],
    transport: TRANSPORT_CLASSES[transport],
    utilities,
    survey: survey + (curve ? 192000 / curve_radius_m ** 2 : 0),
    other,
  };
  const total = Object.values(t).reduce((a, b) => a + b, 0);
  return { h_per_km: t, total_h_per_km: total, utilisation: t.boring / total, advance_m_day: 24000 / total };
}
