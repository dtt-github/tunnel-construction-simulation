// The JS models must reproduce the Python reference vectors (models/test-vectors) to 1e-9 relative.
// Run: node --test models/js/test
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { cutterForces, tbmPerformance, hoekBrown, gaussianTrough, presetTrough, twinTroughs, burlandCategory, wedgeSilo, daubWindow, siloStress, chamber, screw, crownPressure, shieldThrust, cutterheadTorque, verticalStress, referenceInstalled, Rng, normalInv, sample as sampleDist, DIST, simulateDrive, recordCheck, maxRpm, cutterChangeHPerKm, supportDowntime, rmrClass, hardRockUtilisation } from "../index.js";

const vec = (name) => JSON.parse(readFileSync(new URL(`../../test-vectors/${name}.json`, import.meta.url)));

function close(actual, expected, path, rel = 1e-9) {
  if (typeof expected === "number") {
    const tol = rel * Math.max(1, Math.abs(expected));
    assert.ok(Math.abs(actual - expected) <= tol, `${path}: ${actual} != ${expected}`);
  } else if (expected === null || typeof expected !== "object") {
    assert.equal(actual, expected, path);
  } else {
    for (const k of Object.keys(expected)) close(actual[k], expected[k], `${path}.${k}`, rel);
  }
}

test("hoek-brown matches python", () => {
  for (const { in: i, out } of vec("hoek_brown")) close(hoekBrown(i.gsi, i.mi, i.sigma_ci, i.d, i.e_i), out, "hb");
});

test("csm cutter forces match python", () => {
  for (const { in: i, out } of vec("csm").cutter_forces) close(cutterForces(i.penetration_mm, i.ucs_mpa, i.bts_mpa, i.cutter), out, "csm");
});

test("csm tbm performance matches python", () => {
  for (const { in: i, out } of vec("csm").tbm_performance) close(tbmPerformance(i), out, "perf");
});

test("settlement trough matches python", () => {
  for (const { in: i, out } of vec("settlement").symmetric) {
    const t = gaussianTrough(i.diameter_m, i.axis_depth_m, i.volume_loss, i.k);
    close({ i: t.i, volume_m3_per_m: t.volume_m3_per_m, s_max: t.s_max }, { i: out.i, volume_m3_per_m: out.volume_m3_per_m, s_max: out.s_max }, "trough");
    for (const s of out.samples) close({ s: t.settlement(s.x), u: t.horizontal(s.x), s3d_at_face: t.settlement3d(s.x, 0) }, { s: s.s, u: s.u, s3d_at_face: s.s3d_at_face }, `x=${s.x}`);
  }
});

function checkTrough(t, out, path) {
  close({ i: t.i, volume_m3_per_m: t.volume_m3_per_m, s_max: t.s_max, fraction_at_face: t.fractionAtFace },
    { i: out.i, volume_m3_per_m: out.volume_m3_per_m, s_max: out.s_max, fraction_at_face: out.fraction_at_face }, path);
  for (const s of out.samples) close({ x: s.x, s: t.settlement(s.x), u: t.horizontal(s.x), slope: t.slope(s.x) }, s, `${path} x=${s.x}`);
  const xs = out.samples[1].x;
  for (const l of out.longitudinal) close({ y: l.y, f: t.longitudinalFraction(l.y), s3d: t.settlement3d(xs, l.y) }, l, `${path} y=${l.y}`);
}

test("asymmetric and multi-component troughs match python", () => {
  for (const { in: i, out } of vec("settlement").asymmetric) {
    const t = gaussianTrough(i.diameter_m, i.axis_depth_m, i.volume_loss, i.k, { kLeft: i.k_left, kRight: i.k_right, components: i.components ?? undefined, iLong: i.i_long ?? null });
    checkTrough(t, out, "asym");
  }
});

test("method presets match python", () => {
  for (const { in: i, out } of vec("settlement").presets) {
    checkTrough(presetTrough(i.method, i.diameter_m, i.axis_depth_m, { shieldLengthM: i.shield_length_m, iLong: i.i_long ?? null }), out, i.method);
  }
});

test("twin troughs match python", () => {
  for (const { in: i, out } of vec("settlement").twin) {
    const tw = twinTroughs(i.diameter_m, i.axis_depth_m, i.spacing_m, i.volume_loss_first, i.volume_loss_second, i.k,
      { secondVlFactor: i.second_vl_factor, secondInnerK: i.second_inner_k });
    for (const s of out.samples) close({ s: tw.settlement(s.x), u: tw.horizontal(s.x) }, { s: s.s, u: s.u }, `twin x=${s.x}`);
  }
});

test("burland categories", () => {
  assert.deepEqual(burlandCategory(0.01), [0, "Negligible"]);
  assert.equal(burlandCategory(0.2)[0], 3);
});

test("face support matches python", () => {
  const v = vec("face_support");
  for (const { in: a, out } of v.silo) close(siloStress(...a), out, "silo");
  for (const { in: i, out } of v.wedge_silo) {
    const water = i.water_depth === null ? {} : { waterDepth: i.water_depth };
    const fs = wedgeSilo(i.diameter, i.cover, i.gamma, i.phi_deg, i.c, { q: i.q, kWedge: i.k_wedge, ...water });
    // the optimum is flat in theta: the pressure agrees to 1e-9, the critical angle and wedge geometry to 1e-6
    const { theta_deg, wedge_length, silo_stress, ...rest } = out.support;
    close(fs, rest, `face D=${i.diameter} phi=${i.phi_deg}`);
    close(fs, { theta_deg, wedge_length, silo_stress }, `face geometry D=${i.diameter}`, 1e-6);
    close(daubWindow(fs, i.diameter, i.cover, i.gamma, { q: i.q, ...water }), out.window, `window D=${i.diameter}`);
  }
});

test("epb chamber and screw match python", () => {
  const v = vec("epb_chamber");
  for (const { in: i, out } of v.screw) {
    const sc = screw(i);
    close({ q_th: sc.theoreticalFlow(i.rpm), q: sc.discharge(i.rpm), outlet: sc.outletPressure(250), mid: sc.pressureAlong(i.length / 2, 250) }, out, "screw");
  }
  for (const { in: i, out } of v.chamber) {
    const ch = chamber(i.volume, i.k_solid);
    const q = ch.screwFlowForPressure(i.p, i.q_exc, i.fir, i.fer);
    const steady = ch.steadyState(i.q_exc, q, i.fir, i.fer);
    close({ screw_flow: q, steady, stiffness: ch.stiffness(steady), state_at: ch.stateAt(i.p, 0.1), crown: crownPressure(i.p, 3.5) },
      { screw_flow: out.screw_flow, steady: out.steady, stiffness: out.stiffness, state_at: out.state_at, crown: out.crown }, `chamber V=${i.volume}`, 1e-7);
    let st = steady;
    for (const tr of out.trace) {
      close({ t: tr.t, p: ch.pressure(st), fill: ch.fill(st), air: ch.airFraction(st) }, tr, `trace V=${i.volume} t=${tr.t}`, 1e-7);
      for (let n = 0; n < 20; n++) st = ch.step(st, 1, i.q_exc, tr.t < i.stop ? 0 : 1.5 * q, i.fir, i.fer);
    }
  }
});

test("thrust and torque match python", () => {
  for (const { in: i, out } of vec("thrust_torque")) {
    const water = i.hw === null ? {} : { waterDepth: i.hw };
    const th = shieldThrust(i.d, i.ln, i.z, i.g, i.p, { k0: i.k0, muShield: i.mus, shieldWeight: i.ws, tools: i.tools, tailSeal: i.tail, backupWeight: i.wb, ...water });
    const sn = (verticalStress(i.z, i.g, water) * (1 + i.k0)) / 2;
    const tq = cutterheadTorque(i.d, i.p, sn, { openingRatio: i.xi, nArms: i.na, armArea: i.aa, armRadius: i.ar, tools: i.ttool, seals: i.seals });
    close({ sv_eff: verticalStress(i.z, i.g, water), sv_total: verticalStress(i.z, i.g, { ...water, effective: false }), thrust: th, sigma_n: sn, torque: tq,
      reference: Object.fromEntries(["epb", "slurry", "gripper"].map((t) => [t, referenceInstalled(t, i.d)])),
      reference_all: Object.fromEntries(["epb", "slurry", "gripper"].map((t) => [t, referenceInstalled(t, i.d, { includeUnverified: true })])) }, out, `D=${i.d}`);
  }
});

test("utilisation model matches python", () => {
  const v = vec("utilisation");
  const rng = new Rng(42);
  assert.deepEqual(v.uniform_seed42.map(() => rng.uniform()), v.uniform_seed42); // bit-identical stream
  for (const [p, z] of v.normal_inv) close(normalInv(p), z, `normalInv(${p})`);
  for (const [k, xs] of Object.entries(v.samples)) [0.05, 0.3, 0.5, 0.7, 0.95].forEach((u, i) => close(sampleDist(DIST[k], u), xs[i], `${k}@${u}`));
  for (const { in: i, out } of v.drives) {
    const r = simulateDrive({ shift_pattern: i.shift_pattern, haulage: i.haulage, boring_min: i.boring_min, interventions: i.interventions }, i.days, i.seed);
    close({ ...r, check: recordCheck(7.08, r.best_day, r.best_week, r.best_month) }, out, `drive ${i.shift_pattern} seed ${i.seed}`, 1e-6);
  }
});

test("hard-rock models match python", () => {
  const v = vec("hard_rock");
  for (const [d, c, out] of v.max_rpm) close(maxRpm(d, c), out, `maxRpm ${d} ${c}`);
  for (const [d, cai, out] of v.cutters) close(cutterChangeHPerKm(d, cai), out, `cutters ${d} ${cai}`);
  for (const [rmr, d, m, out] of v.support) close(supportDowntime(rmr, d, m), out, `support ${rmr} ${d} ${m}`);
  for (const [rmr, cls] of v.classes) assert.equal(rmrClass(rmr).class, cls);
  for (const { in: i, out } of v.utilisation) {
    const { pr, d, ...kw } = i;
    close(hardRockUtilisation(pr, d, kw), out, `utilisation ${pr} ${d}`);
  }
});
