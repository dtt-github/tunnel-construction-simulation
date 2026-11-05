// The JS models must reproduce the Python reference vectors (models/test-vectors) to 1e-9 relative.
// Run: node --test models/js/test
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { cutterForces, tbmPerformance, hoekBrown, gaussianTrough, presetTrough, twinTroughs, burlandCategory, wedgeSilo, daubWindow, siloStress, chamber, screw, crownPressure, shieldThrust, cutterheadTorque, verticalStress, referenceInstalled, Rng, normalInv, sample as sampleDist, DIST, simulateDrive, recordCheck, maxRpm, cutterChangeHPerKm, supportDowntime, rmrClass, hardRockUtilisation, equivalentMohrCoulomb, groundReaction, pressureForDisplacement, ldp, squeezingStrain, squeezingClass, ringSupport, steelSetSupport, boltSupport, combine, supportEquilibrium, shieldFriction, shotcreteModulus, shotcreteStrength, mc90Modulus, earlyStrengthClass, fictitiousPressure, liningInteraction, sulemConvergence, triggerLevel, kirschCrownFactor, crownSettlement, infiltration as slurryInfiltration, cushion, dischargeDensity, drySolidsFlow, theoreticalDryFlow, durandVelocity, pipeVelocity, excessPorePressure, designRound, roundCycle, bottomCharge, burden, firstCutBurden, holeDepth, cutSections, kuzRamX50, uniformityIndex, ppv, maxChargePerDelay, ss4604866Limit, SUPPORT_CLASSES, jsceRing, woodInertia, ringLoads, sectionStresses, jackingStress, burstingForce, annulusVolume, groutWindow, taper, scenario, terzaghiLoads, activeCoefficient } from "../index.js";

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
      { secondVlFactor: i.second_vl_factor, secondInnerK: i.second_inner_k, secondOuterK: i.second_outer_k });
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

test("ground response matches python", () => {
  const v = vec("ground_response");
  for (const { in: a, out } of v.mc) close(equivalentMohrCoulomb(...a), out, `mc ${a}`);
  for (const { in: a, out, p_inv } of v.grc) {
    close(groundReaction(...a), out, `grc ${a}`);
    close(pressureForDisplacement(groundReaction(...a).u * 1.1, a[0], ...a.slice(2)), p_inv, `inverse ${a}`, 1e-7);
  }
  for (const [x, r0, rp, out] of v.ldp) close(ldp(x, r0, rp), out, `ldp ${x}`);
  for (const [scm, p0, pi, eps, cls] of v.squeeze) { close(squeezingStrain(scm, p0, pi), eps, "squeeze"); assert.equal(squeezingClass(eps)[0], cls); }
  const ring = ringSupport(3.0, 0.2, 30000, 0.15, 35), sets = steelSetSupport(3.0, 1.0, 0.0125), bolts = boltSupport(3.0, 12, 1.0, 3.0, 0.025, 0.18);
  close({ ring, sets, bolts, combined: combine(ring, sets) }, { ring: v.support.ring, sets: v.support.sets, bolts: v.support.bolts, combined: v.support.combined }, "supports");
  close(supportEquilibrium(2, 3, 749.9, 0.3, 24.72, 0.22, combine(ring, sets), 0.005), v.support.eq, "equilibrium", 1e-7);
  for (const { in: a, out } of v.shield) close(shieldFriction(...a), out, `shield ${a}`, 1e-7);
});

test("sem models match python", () => {
  const v = vec("sem");
  for (const [t, e, f, e2, e90] of v.ageing) close([shotcreteModulus(t), shotcreteStrength(t), shotcreteModulus(t, "oreste_example"), mc90Modulus(t / 24, 21537, 13943)], [e, f, e2, e90], `ageing ${t}`);
  for (const [t, f, cls] of v.classes) assert.equal(earlyStrengthClass(t, f), cls, `class ${t} ${f}`);
  for (const [x, p] of v.fict) close(fictitiousPressure(x, 2.7, 5.0), p, `fict ${x}`);
  for (const { in: a, out } of v.lining) {
    const li = liningInteraction(...a);
    close({ u_install: li.u_install, u_final: li.u_final, p_final: li.p_final, hours_to_95: li.hours_to_95, min_safety: li.min_safety, min_safety_age_h: li.min_safety_age_h }, out, `lining ${a}`, 1e-6);
  }
  for (const [x, t, c] of v.sulem) close(sulemConvergence(x, t, 20, 4.6, 6, 5.7, 0.3), c, `sulem ${x} ${t}`);
  for (const [m, lvl] of v.triggers) assert.equal(triggerLevel(m, 10), lvl);
  for (const [k, nu, uf, us, f, c] of v.crown) close([kirschCrownFactor(k, nu), crownSettlement(uf, us, k, nu)], [f, c], `crown ${k} ${nu}`);
});

test("slurry models match python", () => {
  const v = vec("slurry");
  for (const { in: a, out } of v.inf) close(slurryInfiltration(...a), out, `infiltration ${a}`);
  const c = cushion(12);
  let st = { p_air: 200, level: 0.5, air_volume: 20 };
  v.cushion.forEach((exp, i) => { st = c.step(st, 1, 0.25, i < 15 ? 0.04 : 0, i < 20 ? 0.25 : 0.3, 200); close(st, exp, `cushion ${i}`); });
  const area = (Math.PI * 7.08 ** 2) / 4, adv = 0.04 / 60;
  const [qd, rd] = dischargeDensity(0.25, 1.05, area, adv, 2.0);
  close({ qd, rd, dry: drySolidsFlow(0.25, 1.05, qd, rd), theo: theoreticalDryFlow(area, adv, 2.0), durand: durandVelocity(0.3), vpipe: pipeVelocity(1000 / 3600, 0.3),
    pore: excessPorePressure(5, 30, 1e-4, 10, 1e6) }, v.circuit, "circuit");
});

test("drill and blast models match python", () => {
  const v = vec("drill_blast");
  const rounds = v.rounds.map(({ in: [w, h, d, design], out }) => {
    const rd = designRound(w, h, d, { design });
    assert.equal(rd.holes.length, out.holes.length, `holes ${w} ${design}`);
    rd.holes.forEach((x, i) => { close([x.x, x.y, x.delay], [out.holes[i][0], out.holes[i][1], out.holes[i][3]], `hole ${i}`); assert.equal(x.kind, out.holes[i][2]); });
    close({ n_charged: rd.n_charged, explosive: rd.explosive, specific_charge: rd.specific_charge, max_charge_per_delay: rd.max_charge_per_delay, pull: rd.pull, area: rd.area },
      { n_charged: out.n_charged, explosive: out.explosive, specific_charge: out.specific_charge, max_charge_per_delay: out.max_charge_per_delay, pull: out.pull, area: out.area }, "round");
    return [rd, w, h];
  });
  for (const { in: [i, cls], out } of v.cycles) {
    const [rd, w, h] = rounds[i];
    const cy = roundCycle(rd, w, h, cls);
    close({ steps: cy.steps.map((s) => s[1]), total_h: cy.total_h, m_per_week: cy.m_per_week, muck_m3: cy.muck_m3 }, out, `cycle ${i} ${cls}`);
  }
  const b = v.basic;
  close({ qb: bottomCharge(38, 1.5, 0.8), b: burden(38, 1.36), b1: firstCutBurden(0.115, 2.85, 0.02, 0.02), h: holeDepth(0.204), cut: cutSections(0.204, 5.2),
    x50: kuzRamX50(7, 0.6, 34.79), n: uniformityIndex(2.5, 2.44, 89, 0.1, 8, 9.5), ppv: ppv(40, 8), qmax: maxChargePerDelay(50, 20),
    ss: [15, 60, 500].flatMap((d) => ["rock", "sand_gravel", "clay"].map((g) => ss4604866Limit(d, { groundPath: g }))) }, b, "basic");
  assert.deepEqual(Object.keys(SUPPORT_CLASSES), ["I", "II", "III", "IV"]);
});

test("lining models match python", () => {
  const v = vec("lining");
  for (const { in: a, out } of v.rings) {
    const r = jsceRing(...a.slice(0, 7), { eta: a[7], deadLoadInDeflection: a[8] });
    close({ moment: r.moment, normal: r.normal, deflection: r.deflection, reaction: r.reaction }, out, `ring ${a[0]}`);
  }
  close({ wood: [4, 6, 7, 8].map((n) => woodInertia(1, n)), loads: ringLoads(20, 3.4, 20, 0.5, 3), sec: sectionStresses(1000, 50, 0.3),
    jack: jackingStress(1000, 10, 1.6125, 0.125), burst_aci: burstingForce(3000, 0.35, 0.2, 0.03, "aci"), burst_daub: burstingForce(3000, 0.35, 0.2),
    annulus: annulusVolume(7.06, 6.9, 1.5), grout: groutWindow(16.5, 20, 3), grout_river: groutWindow(12, 19, -12.5), taper: [taper(6.9, 1.5, 250), taper(6.9, 1.5, 250, 22.5)],
    terzaghi: [[6.0, 3.4, 20, 30, 0, 0.5, 100], [40.0, 3.4, 20, 30, 0, 0.5, 100], [40.0, 3.4, 20, 30, 0, 0.5, 0.0], [35.0, 3.5, 20.2, 22, 12, 1.5, 9.0],
      [30.0, 3.5, 19.5, 24, 1, 0.42, 4.0, 10.0, 15.0]].map((a) => terzaghiLoads(...a)), ka: activeCoefficient(24) }, v.basic, "basic");
});

test("scenario loader matches python", () => {
  const v = vec("scenario");
  const s = scenario(v.data);
  for (const p of v.points) {
    const col = s.column(p.ch).map((l) => [l.unit, l.top, l.base]);
    assert.equal(col.length, p.column.length, `column ${p.ch}`);
    col.forEach((l, i) => { assert.equal(l[0], p.column[i][0]); close([l[1], l[2]], [p.column[i][1], p.column[i][2]], `layer ${p.ch} ${i}`); });
    assert.equal(s.unitAt(p.ch, -20), p.unit_m20);
    close(s.porePressure(p.ch, -30), p.u_m30, `u ${p.ch}`);
    const f = p.ch === 120 ? s.face(p.ch, 9.0, 6.0) : s.face(p.ch, 7.1);
    assert.equal(f.unit_at_axis, p.face.unit_at_axis);
    close({ ...f, unit_at_axis: 0 }, { ...p.face, unit_at_axis: 0 }, `face ${p.ch}`);
  }
});
