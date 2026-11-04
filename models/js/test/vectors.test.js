// The JS models must reproduce the Python reference vectors (models/test-vectors) to 1e-9 relative.
// Run: node --test models/js/test
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { cutterForces, tbmPerformance, hoekBrown, gaussianTrough, burlandCategory } from "../index.js";

const vec = (name) => JSON.parse(readFileSync(new URL(`../../test-vectors/${name}.json`, import.meta.url)));

function close(actual, expected, path) {
  if (typeof expected === "number") {
    const tol = 1e-9 * Math.max(1, Math.abs(expected));
    assert.ok(Math.abs(actual - expected) <= tol, `${path}: ${actual} != ${expected}`);
  } else if (expected === null || typeof expected !== "object") {
    assert.equal(actual, expected, path);
  } else {
    for (const k of Object.keys(expected)) close(actual[k], expected[k], `${path}.${k}`);
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
  for (const { in: i, out } of vec("settlement")) {
    const t = gaussianTrough(i.diameter_m, i.axis_depth_m, i.volume_loss, i.k);
    close({ i: t.i, volume_m3_per_m: t.volume_m3_per_m, s_max: t.s_max }, { i: out.i, volume_m3_per_m: out.volume_m3_per_m, s_max: out.s_max }, "trough");
    for (const s of out.samples) close({ s: t.settlement(s.x), u: t.horizontal(s.x), s3d_at_face: t.settlement3d(s.x, 0) }, { s: s.s, u: s.u, s3d_at_face: s.s3d_at_face }, `x=${s.x}`);
  }
});

test("burland categories", () => {
  assert.deepEqual(burlandCategory(0.01), [0, "Negligible"]);
  assert.equal(burlandCategory(0.2)[0], 3);
});
