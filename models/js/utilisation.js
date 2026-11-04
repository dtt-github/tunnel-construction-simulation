// TBM utilisation: activity-time model with downtime, shift pattern and a record-rate check.
// Twin of models/py/tunnelsim_models/utilisation.py, which documents the sources (Moosazadeh et al. 2018 for the
// fitted distributions; SF Central Subway shift pattern; Roby & Willis 2014 survey; record tables). Minutes inside.

/** mulberry32, bit-identical to the Python Rng. */
export class Rng {
  constructor(seed) { this.a = seed >>> 0; }
  uniform() {
    this.a = (this.a + 0x6d2b79f5) >>> 0;
    let t = this.a;
    t = Math.imul(t ^ (t >>> 15), t | 1) >>> 0;
    t = (t ^ ((t + (Math.imul(t ^ (t >>> 7), t | 61) >>> 0)) >>> 0)) >>> 0;
    return (((t ^ (t >>> 14)) >>> 0) + 0.5) / 4294967296;
  }
}

/** Inverse standard normal CDF (Acklam). */
export function normalInv(p) {
  const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.38357751867269e2, -3.066479806614716e1, 2.506628277459239];
  const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1];
  const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416];
  if (p < 0.02425) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p > 1 - 0.02425) return -normalInv(1 - p);
  const q = p - 0.5, r = q * q;
  return ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q) / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
}

/** Inverse-CDF sample of a distribution spec at uniform u. */
export function sample(dist, u) {
  switch (dist.kind) {
    case "fixed": return dist.value;
    case "loglogistic": return dist.gamma + dist.beta * (u / (1 - u)) ** (1 / dist.alpha);
    case "lognormal": return dist.gamma + Math.exp(dist.mu + dist.sigma * normalInv(u));
    case "weibull": return dist.lam * (-Math.log(1 - u)) ** (1 / dist.k);
    case "triangular": {
      const { a, m, b } = dist, f = (m - a) / (b - a);
      return u < f ? a + Math.sqrt(u * (b - a) * (m - a)) : b - Math.sqrt((1 - u) * (b - a) * (b - m));
    }
    default: throw new RangeError(`unknown distribution ${dist.kind}`);
  }
}
export const median = (dist) => sample(dist, 0.5);

const TABRIZ = "Moosazadeh et al. (2018), doi:10.22044/jme.2017.5707.1384";
export const DIST = Object.freeze({
  ring_build: { kind: "lognormal", sigma: 0.62899, mu: 2.123, gamma: 9.0618, source: TABRIZ },
  boring: { kind: "loglogistic", alpha: 3.9756, beta: 17.769, gamma: 16.368, source: TABRIZ },
  general: { kind: "loglogistic", alpha: 2.3998, beta: 18.654, gamma: 1.0364, source: TABRIZ },
  train_delay: { kind: "triangular", a: 20, m: 30, b: 70, source: TABRIZ },
  rings_between_stops: { kind: "weibull", k: 1.549, lam: 274.91, source: TABRIZ },
  stop_hours: { kind: "loglogistic", alpha: 2.013, beta: 105.11, gamma: 0, source: TABRIZ },
});
export const SHIFT_PATTERNS = Object.freeze({
  "2x10h_plus_4h_maintenance": { production_h: 20, per_cycle_maintenance: false, source: "Johnson (2014), SF Central Subway, NAT 2014" },
  "2x12h_maintenance_per_cycle": { production_h: 24, per_cycle_maintenance: true, source: TABRIZ },
  idealised_24h: { production_h: 24, per_cycle_maintenance: false, source: "none: no maintenance at all, for checks and upper bounds only" },
});
export const PER_CYCLE_MAINTENANCE_MIN = 25 + 12;
const DAY = 1440;

export const defaultDriveSettings = () => ({
  ring_length: 1.5, boring_min: null, ring_build: DIST.ring_build, general: DIST.general,
  shift_pattern: "2x10h_plus_4h_maintenance", haulage: "conveyor", interventions: true,
});

function productionWindow(t, prodMin) {
  const day0 = Math.floor(t / DAY) * DAY;
  return t < day0 + prodMin ? [day0, day0 + prodMin] : [day0 + DAY, day0 + DAY + prodMin];
}

/** Run the drive for `days` calendar days; same algorithm and random stream as the Python reference. */
export function simulateDrive(settings, days = 90, seed = 1) {
  const s = { ...defaultDriveSettings(), ...settings };
  const rng = new Rng(seed);
  const pattern = SHIFT_PATTERNS[s.shift_pattern];
  const prodMin = pattern.production_h * 60, horizon = days * DAY;
  let t = 0, rings = 0, stops = 0;
  const time = { boring: 0, ring_build: 0, general: 0, train_delay: 0, maintenance_per_cycle: 0, intervention: 0 };
  const daily = new Array(days).fill(0);
  let nextStop = s.interventions ? sample(DIST.rings_between_stops, rng.uniform()) : Infinity;
  const work = (t0, dur, key) => {
    let tt = t0;
    while (dur > 1e-9 && tt < horizon) {
      const [w0, w1] = productionWindow(tt, prodMin);
      tt = Math.max(tt, w0);
      const d = Math.min(dur, w1 - tt, horizon - tt);
      time[key] += d;
      tt += d;
      dur -= d;
    }
    return [tt, Math.max(dur, 0)];
  };
  while (t < horizon) {
    const bore = s.boring_min !== null ? s.boring_min : sample(DIST.boring, rng.uniform());
    let left;
    [t, left] = work(t, bore, "boring");
    if (left > 1e-9) break;
    daily[Math.min(Math.floor((t - 1e-9) / DAY), days - 1)] += s.ring_length;
    rings++;
    [t] = work(t, sample(s.ring_build, rng.uniform()), "ring_build");
    [t] = work(t, sample(s.general, rng.uniform()), "general");
    if (s.haulage === "rail") [t] = work(t, sample(DIST.train_delay, rng.uniform()), "train_delay");
    if (pattern.per_cycle_maintenance) [t] = work(t, PER_CYCLE_MAINTENANCE_MIN, "maintenance_per_cycle");
    if (rings >= nextStop && t < horizon) {
      const d = Math.min(sample(DIST.stop_hours, rng.uniform()) * 60, horizon - t);
      time.intervention += d;
      t += d;
      stops++;
      nextStop = rings + sample(DIST.rings_between_stops, rng.uniform());
    }
  }
  const total = days * DAY;
  const shares = Object.fromEntries(Object.entries(time).map(([k, v]) => [k, v / total]));
  shares.maintenance_shift_and_idle = Math.max(0, 1 - Object.values(shares).reduce((a, b) => a + b, 0));
  const windowSums = (n) => { const out = []; for (let i = 0; i + n <= days; i++) out.push(daily.slice(i, i + n).reduce((a, b) => a + b, 0)); return out; };
  const weeks = windowSums(7), months = windowSums(30);
  const metres = daily.reduce((a, b) => a + b, 0);
  return {
    days, rings, metres, utilisation: time.boring / total, mean_m_per_day: metres / days, mean_m_per_week: (metres / days) * 7,
    best_day: Math.max(...daily), best_week: weeks.length ? Math.max(...weeks) : 0, best_month: months.length ? Math.max(...months) : 0,
    shares, interventions: stops,
  };
}

const ROBBINS_RECORDS = "https://www.robbinstbm.com/news-and-media/world-records/";
export const WORLD_RECORDS = Object.freeze([
  { class: [6.01, 7.0], day: 124.7, week: 515.1, month: 1754.0, source: ROBBINS_RECORDS },
  { class: [7.01, 8.0], day: 115.7, week: 428.0, month: 1482.0, source: ROBBINS_RECORDS },
  { class: [8.01, 9.0], day: 75.5, week: 428.0, month: 1719.0, source: ROBBINS_RECORDS },
  { class: [9.01, 10.0], day: 105.6, week: 435.0, month: 1600.0, source: ROBBINS_RECORDS },
  { class: [10.01, 11.0], day: 48.8, week: 235.0, month: 841.8, source: ROBBINS_RECORDS },
]);
export const EPB_REFERENCES = Object.freeze([
  { what: "best day", metric: "day", value: 40.6, diameter: 6.39, project: "Bangkok Orange Line E3", source: "https://tunnelingonline.com/terratec-marks-major-milestone-in-bangkok/" },
  { what: "best month", metric: "month", value: 920.0, diameter: null, project: "Doha Gold Line (contractor claim)", source: "https://tunnelbuilder.com/News/SELI-breaks-through-on-the-Gold-Line-on-the-Doha-Metro-in-record-time.aspx" },
  { what: "best week in a survey of 40 EPBs, 5.9-10.2 m", metric: "week", value: 178.5, diameter: null, project: "Roby & Willis (2014)", source: "https://www.robbinstbm.com/wp-content/uploads/2014/08/FastEPBAdvance_NAT2014.pdf" },
  { what: "week, 9.73 m EPB", metric: "week", value: 260.0, diameter: 9.73, project: "Riyadh Metro Line 5", source: "https://www.herrenknecht.com/en/references/referencesdetail/riyadh-metro/" },
]);
export const EPB_WEEKLY_SURVEY = Object.freeze({ mean: 85.4, sd: 36.0, min: 32.6, max: 178.5, source: "https://www.robbinstbm.com/wp-content/uploads/2014/08/FastEPBAdvance_NAT2014.pdf" });

/** Compare best rates with the world record of the diameter class and, for EPB, the best published references. */
export function recordCheck(diameter, bestDay, bestWeek, bestMonth, method = "epb") {
  const rec = WORLD_RECORDS.find((r) => r.class[0] <= diameter && diameter <= r.class[1] + 0.0099) ?? null;
  const out = {};
  for (const [metric, v] of [["day", bestDay], ["week", bestWeek], ["month", bestMonth]]) {
    const wr = rec ? rec[metric] : null;
    const refs = method === "epb" ? EPB_REFERENCES.filter((r) => r.metric === metric).map((r) => r.value) : [];
    const ref = refs.length ? Math.max(...refs) : null;
    out[metric] = { value: v, world_record: wr, above_world_record: wr !== null && v > wr, epb_reference: ref, above_epb_reference: ref !== null && v > ref };
  }
  return out;
}
