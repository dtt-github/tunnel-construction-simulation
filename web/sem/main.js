// Slice D: SEM / NATM heading in weak rock. One crew works the top heading, bench and invert by the rules of the ground
// class (FHWA 2009, Table 9-1); the sprayed concrete stiffens with age (Oreste 2003); the lining load comes from the
// ageing-ring interaction with the ground reaction curve; monitoring sections read convergence with the Sulem et al.
// (1987) law and Crossrail trigger levels.
//
// World frame: metres, Y up, tunnel axis at y = 0, chainage along -z. The rock and lining stay put; the faces advance.

import {
  equivalentMohrCoulomb, groundReaction, squeezingStrain, squeezingClass, shotcreteModulus, shotcreteStrength,
  earlyStrengthClass, liningInteraction, SEM_ROCK_CLASSES, CYCLE, ringClosureOk, sulemConvergence, SULEM_EXAMPLE, triggerLevel,
  FINAL_LINING_RATE_MM_PER_MONTH, SHOTCRETE, Rng,
} from "../../models/js/index.js";
import { THREE, createScene, label, placeLabels, mat, box, fmt, dl } from "../hard-rock/common.js";

// ---------------------------------------------------------------- tunnel, ground, sequence
const D = 10, R = D / 2;
const Y_TH = 1.0, Y_BENCH = -3.0; // floor of the top heading and of the bench
const COVER = 100, P0 = COVER * 0.027, NU = 0.25; // m, MPa
const ZONES = [
  { name: "Siltstone, moderately jointed", from: -80, to: 60, gsi: 45, sci: 30, mi: 9, ei: 8000, cls: "moderately_jointed",
    th: 2.0, bench: 4.0, lining: 0.2, benchLag: 30, canopy: false, color: 0x8b8574 },
  { name: "Crushed fault zone", from: 60, to: 100, gsi: 22, sci: 15, mi: 8, ei: 3000, cls: "crushed_squeezing",
    th: 1.0, bench: 2.0, invert: 2.0, lining: 0.35, benchLag: 4, canopy: true, color: 0x6b5848 },
  { name: "Siltstone, moderately jointed", from: 100, to: 400, gsi: 45, sci: 30, mi: 9, ei: 8000, cls: "moderately_jointed",
    th: 2.0, bench: 4.0, lining: 0.2, benchLag: 30, canopy: false, color: 0x8b8574 },
];
const zoneAt = (ch) => ZONES.find((z) => ch >= z.from && ch < z.to) ?? ZONES.at(-1);
const H_PER_M = { top_heading: CYCLE.top_heading[1] / CYCLE.top_heading[0], bench: CYCLE.bench[1] / CYCLE.bench[0], invert: CYCLE.invert[1] / CYCLE.invert[0] };
const CANOPY = { length: 12.5, advance: 9, pipes: 40, hours: 20 }; // Fort Canning AGF umbrella; ~2 working days per umbrella
const SECTION_SPACING = 10;
const A_TH = Math.acos(Y_TH / R), A_BENCH = Math.acos(Y_BENCH / R); // half-angles from the crown

// ---------------------------------------------------------------- ground response per zone (cached per shotcrete)
const groundCache = new Map();
function groundAt(zone, shot) {
  const key = `${ZONES.indexOf(zone)}|${shot}`;
  if (!groundCache.has(key)) {
    const mc = equivalentMohrCoulomb(zone.gsi, zone.mi, zone.sci, zone.ei, P0);
    const free = groundReaction(P0, 0, R, mc.e_rm, NU, mc.phi_deg, mc.c);
    // planned average heading rate from the cycle: top heading rounds plus the bench, invert and canopy work they bring
    const perM = H_PER_M.top_heading + H_PER_M.bench + (zone.invert ? H_PER_M.invert : 0) + (zone.canopy ? CANOPY.hours / CANOPY.advance : 0);
    const rate = 1 / perM; // m/h
    const li = liningInteraction(P0, R, mc.e_rm, NU, mc.phi_deg, mc.c, zone.lining, zone.th, rate, shot);
    const strain = squeezingStrain(mc.sigma_cm, P0);
    groundCache.set(key, { mc, free, rate, li, strain, squeeze: squeezingClass(strain), predictedMm: 2 * (li.u_final - li.u_install) * 1000 });
  }
  return groundCache.get(key);
}

// ---------------------------------------------------------------- scene
const VIEWS = {
  heading: { title: "Heading", pos: [-13, 6, -4], target: [0, 0, 6] },
  face: { title: "Face", pos: [-6, 2, -12], target: [0, 0, 0] },
  sequence: { title: "Bench and invert", pos: [-16, 4, 14], target: [0, -2, 18] },
  monitoring: { title: "Monitoring", pos: [-12, 2, 22], target: [0, 1, 30] },
};
const { renderer, scene, camera, controls, updateCamera } = createScene(VIEWS);
// views are relative to the top-heading face: shift everything by the face position
const CUT = new THREE.Plane(new THREE.Vector3(1, 0, 0), 0); // keep x > 0: look in from -x
const AHEAD = new THREE.Plane(new THREE.Vector3(0, 0, -1), 0); // keep z <= -face (rock ahead)
const BEHIND = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0); // keep z >= -face (excavated tunnel)
const world = new THREE.Group();
scene.add(world);

for (const z of ZONES) {
  const len = z.to - z.from;
  const wall = new THREE.Mesh(new THREE.CylinderGeometry(R + 0.4, R + 0.4, len, 64, 1, true).rotateX(Math.PI / 2),
    new THREE.MeshStandardMaterial({ color: z.color, roughness: 1, side: THREE.DoubleSide, clippingPlanes: [CUT, BEHIND] }));
  wall.position.z = -(z.from + len / 2);
  world.add(wall);
  const ahead = box(16, 14, len, new THREE.MeshStandardMaterial({ color: z.color, roughness: 1, transparent: true, opacity: 0.25, depthWrite: false, clippingPlanes: [AHEAD, CUT] }));
  ahead.position.set(0, 0, -(z.from + len / 2));
  world.add(ahead);
}

// Lining pieces: annular sectors of the given thickness between angles measured counter-clockwise from +x.
const deg = (a) => (a * Math.PI) / 180;
const sectorGeo = (a0, a1, t, len) => {
  const s = new THREE.Shape();
  s.absarc(0, 0, R, a0, a1, false);
  s.absarc(0, 0, R - t, a1, a0, true);
  s.closePath();
  return new THREE.ExtrudeGeometry(s, { depth: len, bevelEnabled: false, curveSegments: 18 });
};
const PART_ANGLES = {
  top_heading: [[Math.PI / 2 - A_TH, Math.PI / 2 + A_TH]],
  bench: [[Math.PI / 2 - A_BENCH, Math.PI / 2 - A_TH], [Math.PI / 2 + A_TH, Math.PI / 2 + A_BENCH]],
  invert: [[Math.PI / 2 + A_BENCH, Math.PI / 2 + 2 * Math.PI - A_BENCH]],
};
const linings = [];
const girderMat = mat(0x3a3f45, { metalness: 0.8, clippingPlanes: [CUT] });
function sprayRound(part, ch0, len, thickness, simTime) {
  for (const [a0, a1] of PART_ANGLES[part]) {
    const m = new THREE.Mesh(sectorGeo(a0, a1, thickness, len), new THREE.MeshStandardMaterial({ color: 0x4a5560, roughness: 1, side: THREE.DoubleSide, clippingPlanes: [CUT] }));
    m.position.z = -(ch0 + len);
    world.add(m);
    linings.push({ mesh: m, t: simTime });
    // lattice girders at 1 m spacing in the sprayed concrete
    for (let g = 0.5; g < len; g += 1) {
      const gir = new THREE.Mesh(new THREE.TorusGeometry(R - thickness / 2, 0.04, 4, 24, a1 - a0).rotateZ(a0), girderMat);
      gir.position.z = -(ch0 + g);
      world.add(gir);
    }
  }
}

// Remaining rock cores: below the top heading between the bench and heading faces; below the bench between the invert
// and bench faces (segments of the circle, extruded and scaled to the current length).
const segmentGeo = (yTop) => {
  const s = new THREE.Shape(), a = Math.acos(yTop / R);
  s.absarc(0, 0, R, Math.PI / 2 + a, Math.PI / 2 + 2 * Math.PI - a, false);
  s.closePath();
  return new THREE.ExtrudeGeometry(s, { depth: 1, bevelEnabled: false, curveSegments: 32 });
};
const coreMat = (c) => new THREE.MeshStandardMaterial({ color: c, roughness: 1, clippingPlanes: [CUT] });
const benchCore = new THREE.Mesh(segmentGeo(Y_TH), coreMat(0x7d7768));
const invertCore = new THREE.Mesh(segmentGeo(Y_BENCH), coreMat(0x6f6a5d));
world.add(benchCore, invertCore);
const tempInverts = [];
const slabMat = mat(0x9a9a92, { roughness: 1, metalness: 0, clippingPlanes: [CUT] });

// Pipe canopies (umbrellas) over the crown in the fault zone.
const pipeGeo = new THREE.CylinderGeometry(0.057, 0.057, CANOPY.length, 6).rotateX(Math.PI / 2).translate(0, 0, -CANOPY.length / 2);
const pipeMat = mat(0x8b939b, { metalness: 0.7, clippingPlanes: [CUT] });
function installCanopy(ch) {
  const g = new THREE.Group();
  g.position.z = -ch;
  for (let k = 0; k < CANOPY.pipes; k++) {
    const a = Math.PI / 2 - deg(70) + (k / (CANOPY.pipes - 1)) * deg(140);
    const p = new THREE.Mesh(pipeGeo, pipeMat);
    p.position.set((R + 0.15) * Math.cos(a), (R + 0.15) * Math.sin(a), 0);
    p.rotation.set(0.06 * Math.sin(a), -0.06 * Math.cos(a), 0); // splayed outwards
    g.add(p);
  }
  world.add(g);
  return g;
}

// Monitoring sections: 5 targets (crown, shoulders, sidewalls) every 10 m.
const sections = [];
const targetGeo = new THREE.OctahedronGeometry(0.12);
const LEVEL_COLORS = { none: 0xd8d8d0, green: 0x57c38a, amber: 0xf2b43a, red: 0xff7a45 };
function addSection(ch, rng, t0 = S.simTime) {
  const g = new THREE.Group();
  g.position.z = -ch;
  const lt = zoneAt(ch).lining;
  const mats = new THREE.MeshBasicMaterial({ color: LEVEL_COLORS.none });
  for (const a of [0, 45, 90, 135, 180]) {
    const t = new THREE.Mesh(targetGeo, mats);
    t.position.set((R - lt - 0.1) * Math.cos(deg(a)), (R - lt - 0.1) * Math.sin(deg(a)), 0);
    if (t.position.x >= 0) g.add(t);
  }
  world.add(g);
  // scatter between sections (illustrative): lognormal, sigma 0.2
  const u1 = rng.uniform(), u2 = rng.uniform();
  const scatter = Math.exp(0.2 * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2));
  sections.push({ ch, t0, scatter, group: g, mat: mats, level: "none" });
}

// Equipment at the top heading face: excavator and spraying robot.
const excavator = new THREE.Group();
const exBody = box(2.2, 1.6, 3.2, mat(0xd9a400));
exBody.position.y = Y_TH + 1.0;
excavator.add(exBody);
const exBoom = box(0.35, 0.35, 3.4, mat(0xd9a400));
exBoom.position.set(0, Y_TH + 2.3, -2.4);
exBoom.rotation.x = 0.35;
excavator.add(exBoom);
const robot = new THREE.Group();
const rbBody = box(1.6, 1.2, 2.6, mat(0xe9e5dc));
rbBody.position.y = Y_TH + 0.8;
robot.add(rbBody);
const rbArm = box(0.2, 0.2, 3.0, mat(0xe9e5dc));
rbArm.position.set(0, Y_TH + 2.6, -1.4);
rbArm.rotation.x = 0.7;
robot.add(rbArm);
world.add(excavator, robot);
label("Top heading face: excavator", exBody, [0, 1.2, 0]);
label("Shotcrete robot", rbBody, [0, 1.0, 0]);
const benchAnchor = new THREE.Object3D(), invertAnchor = new THREE.Object3D();
world.add(benchAnchor, invertAnchor);
label("Bench face", benchAnchor, [0, Y_TH + 0.4, 0]);
label("Invert face (ring closure)", invertAnchor, [0, Y_BENCH + 0.4, 0]);

// ---------------------------------------------------------------- UI and state
const ids = ["start", "shot", "closure", "ts", "tsOut", "pause", "reset", "alarms", "sequence", "ground", "monitor", "showLabels"];
const ui = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));
const val = (id) => +ui[id].value;
let S;
const trash = [];
function reset() {
  for (const o of trash.splice(0)) world.remove(o);
  for (const l of linings.splice(0)) world.remove(l.mesh);
  for (const s of sections.splice(0)) world.remove(s.group);
  for (const t of tempInverts.splice(0)) world.remove(t);
  world.children.filter((c) => c.geometry?.type === "TorusGeometry" || c.userData.canopy).forEach((c) => world.remove(c));
  const start = val("start");
  // faces at the start follow the class there: bench 24 m and flat invert behind in siltstone; bench 4 m and invert
  // 8 m behind (ring closed within one diameter) in the fault zone
  const z0 = zoneAt(start);
  S = { th: start, bench: start - (z0.invert ? 4 : 24), invert: start - (z0.invert ? 8 : 24), canopyEnd: -Infinity, simTime: 0, task: null, paused: false, rng: new Rng(7), nextSection: Math.ceil(start / SECTION_SPACING) * SECTION_SPACING, done: { th: 0, bench: 0, invert: 0 } };
  // already excavated and lined behind the start (aged 30 days)
  for (let ch = start - 60; ch < start; ch += 1) {
    const z = zoneAt(ch);
    if (ch < S.th) sprayRound("top_heading", ch, 1, z.lining, -30 * 86400);
    if (ch < S.bench) sprayRound("bench", ch, 1, z.lining, -30 * 86400);
    if (ch < S.invert && z.invert) sprayRound("invert", ch, 1, z.lining, -30 * 86400);
  }
  // monitoring sections behind the start, read since the face passed them at the planned rate
  for (let ch = Math.ceil((start - 60) / SECTION_SPACING) * SECTION_SPACING; ch < start - 1; ch += SECTION_SPACING) {
    addSection(ch, S.rng, -((start - ch) / groundAt(zoneAt(ch), ui.shot.value).rate) * 3600);
  }
}

function needsClosure(ch) { return zoneAt(ch).invert && ui.closure.checked; }
function nextTask() {
  const zTh = zoneAt(S.th);
  if (zTh.canopy && S.th + zTh.th > S.canopyEnd - (CANOPY.length - CANOPY.advance)) return { kind: "canopy", len: 0, hours: CANOPY.hours };
  const benchLag = S.th - S.bench, invLag = S.bench - S.invert;
  const zB = zoneAt(S.invert);
  if (zB.invert && invLag >= zB.invert && (needsClosure(S.invert) ? S.th - S.invert >= 0.8 * D : S.th - S.invert >= 30))
    return { kind: "invert", len: Math.min(zB.invert, invLag), hours: Math.min(zB.invert, invLag) * H_PER_M.invert };
  if (benchLag >= zoneAt(S.bench).benchLag + zoneAt(S.bench).bench || (zTh.invert && benchLag >= zTh.benchLag)) {
    const len = Math.min(zoneAt(S.bench).bench, benchLag);
    return { kind: "bench", len, hours: len * H_PER_M.bench };
  }
  return { kind: "top_heading", len: zTh.th, hours: zTh.th * H_PER_M.top_heading };
}
function finishTask(t) {
  if (t.kind === "canopy") { const g = installCanopy(S.th); g.userData.canopy = true; trash.push(g); S.canopyEnd = S.th + CANOPY.length; return; }
  if (t.kind === "top_heading") {
    const z = zoneAt(S.th);
    sprayRound("top_heading", S.th, t.len, z.lining, S.simTime);
    if (z.invert && ui.closure.checked) { // temporary top-heading invert (Fort Canning practice)
      const slab = box(2 * Math.sqrt(R * R - Y_TH * Y_TH) - 0.4, 0.15, t.len, slabMat);
      slab.position.set(0, Y_TH + 0.08, -(S.th + t.len / 2));
      slab.userData.ch = S.th;
      world.add(slab);
      tempInverts.push(slab);
    }
    S.th += t.len;
    S.done.th += t.len;
    while (S.nextSection <= S.th - 1) { addSection(S.nextSection, S.rng); S.nextSection += SECTION_SPACING; }
  } else if (t.kind === "bench") {
    sprayRound("bench", S.bench, t.len, zoneAt(S.bench).lining, S.simTime);
    for (const s of tempInverts.filter((x) => x.userData.ch < S.bench + t.len)) { world.remove(s); tempInverts.splice(tempInverts.indexOf(s), 1); }
    S.bench += t.len;
    S.done.bench += t.len;
    if (!zoneAt(S.bench - 0.1).invert) S.invert = Math.max(S.invert, S.bench); // flat invert: no separate structural invert
  } else {
    sprayRound("invert", S.invert, t.len, zoneAt(S.invert).lining, S.simTime);
    S.invert += t.len;
    S.done.invert += t.len;
  }
}
function step(dtReal) {
  if (S.paused) return;
  let dt = dtReal * val("ts");
  while (dt > 0) {
    if (!S.task) { S.task = nextTask(); S.task.left = S.task.hours * 3600; }
    const h = Math.min(dt, S.task.left);
    S.task.left -= h;
    S.simTime += h;
    dt -= h;
    if (S.task.left <= 1e-6) { finishTask(S.task); S.task = null; }
  }
}

// ---------------------------------------------------------------- monitoring
function reading(sec, atTime = S.simTime) {
  const z = zoneAt(sec.ch), g = groundAt(z, ui.shot.value);
  const x = S.th - sec.ch, days = (atTime - sec.t0) / 86400;
  const cInf = g.predictedMm / (1 + SULEM_EXAMPLE.m);
  const xRef = SULEM_EXAMPLE.x_over_d * D;
  // no ring closure in a squeezing zone: larger deformation (illustrative factor 1.5, no published value)
  const noClosure = z.invert && !ui.closure.checked ? 1.5 : 1;
  return sec.scatter * noClosure * (sulemConvergence(x, Math.max(days, 0), cInf, xRef, SULEM_EXAMPLE.t_ref, SULEM_EXAMPLE.m, SULEM_EXAMPLE.n));
}

// ---------------------------------------------------------------- animation
let lastFace = null;
function animate() {
  const face = S.th;
  AHEAD.constant = -face;
  BEHIND.constant = face;
  if (lastFace !== null && face !== lastFace) {
    // follow the heading: keep the camera where it is relative to the face
    const dz = -(face - lastFace);
    camera.position.z += dz;
    controls.target.z += dz;
  }
  lastFace = face;
  benchCore.position.z = -S.th;
  benchCore.scale.z = Math.max(S.th - S.bench, 0.001);
  invertCore.position.z = -S.bench;
  invertCore.scale.z = Math.max(S.bench - S.invert, 0.001);
  benchAnchor.position.z = -S.bench;
  invertAnchor.position.z = -S.invert;
  invertAnchor.visible = S.bench - S.invert > 0.5;
  excavator.position.z = -(face - 2.5);
  robot.position.z = -(face - 7);
  excavator.visible = S.task?.kind === "top_heading" || S.task?.kind === "canopy";
  for (const l of linings) {
    const age = (S.simTime - l.t) / 3600;
    const f = shotcreteModulus(age, ui.shot.value) / SHOTCRETE[ui.shot.value].e0; // 0 fresh .. 1 cured
    l.mesh.material.color.setRGB(0.29 + 0.45 * f, 0.33 + 0.41 * f, 0.38 + 0.34 * f);
  }
  for (const s of sections) s.mat.color.setHex(LEVEL_COLORS[s.level]);
}

// ---------------------------------------------------------------- console
const hours = (h) => (h < 48 ? `${fmt(h, 1)} h` : `${fmt(h / 24, 1)} days`);
function hud() {
  ui.tsOut.textContent = `×${val("ts")} (${fmt(val("ts") / 60, 0)} min per s)`;
  const zTh = zoneAt(S.th), g = groundAt(zTh, ui.shot.value), cls = SEM_ROCK_CLASSES[zTh.cls];
  const days = S.simTime / 86400;
  const TASK = { top_heading: "excavating and spraying the top heading", bench: "excavating and spraying the bench", invert: "excavating and spraying the invert (ring closure)", canopy: "drilling a pipe canopy (40 pipes, 12.5 m)" };
  const invLag = S.th - S.invert;
  dl(ui.sequence, [
    ["Now", S.task ? `${TASK[S.task.kind]} (${fmt(S.task.left / 3600, 1)} h left)` : "—"],
    ["Ground class (FHWA)", `${zTh.cls.replaceAll("_", " ")}: ${cls.sequence}`],
    ["Top heading face", `${fmt(S.th, 1)} m (rounds of ${zTh.th} m)`],
    ["Bench face", `${fmt(S.bench, 1)} m, ${fmt(S.th - S.bench, 1)} m behind`],
    ["Invert / ring closure", zTh.invert ? `${fmt(S.invert, 1)} m, ${fmt(invLag, 1)} m behind the face (limit ${D} m)` : "not required in this class"],
    ["Pre-support", cls.presupport],
    ["Advance so far", days > 0.05 ? `${fmt(S.done.th, 1)} m top heading in ${fmt(days, 1)} days = ${fmt(S.done.th / days, 1)} m/day` : "—"],
  ]);
  const ageFace = 1; // hours after spraying, for the early-strength class
  dl(ui.ground, [
    ["Rock at the face", `${zTh.name} (GSI ${zTh.gsi}, σci ${zTh.sci} MPa)`],
    ["Rock-mass strength, modulus", `${fmt(g.mc.sigma_cm, 1)} MPa, ${fmt(g.mc.e_rm / 1000, 2)} GPa`],
    ["Squeezing (Hoek & Marinos)", `${fmt(g.strain, 2)} %, class ${g.squeeze[0]}`],
    ["Unsupported closure", `${fmt(g.free.u * 1000, 0)} mm (radial), plastic zone ${fmt(g.free.r_p / R, 2)} R`],
    ["Lining", `${fmt(zTh.lining * 1000, 0)} mm shotcrete with lattice girders (FHWA ${cls.lining_mm[0]}–${cls.lining_mm[1]} mm)`],
    ["Shotcrete at 1 h / 24 h", `${fmt(shotcreteStrength(ageFace, ui.shot.value), 1)} MPa (${earlyStrengthClass(ageFace, shotcreteStrength(ageFace, ui.shot.value))}) / ${fmt(shotcreteStrength(24, ui.shot.value), 1)} MPa (${earlyStrengthClass(24, shotcreteStrength(24, ui.shot.value))})`],
    ["Lining load (closed ring, Oreste)", `${fmt(g.li.p_final, 2)} MPa; 95 % reached after ${hours(g.li.hours_to_95)}`],
    ["Lining safety (strength / stress)", `${fmt(g.li.min_safety, 2)} at minimum, ${hours(g.li.min_safety_age_h)} after spraying`],
    ["Predicted convergence", `${fmt(g.predictedMm, 1)} mm (diametral, after spraying)`],
  ]);

  // monitoring table: the latest sections
  for (const s of sections) {
    const pred = groundAt(zoneAt(s.ch), ui.shot.value).predictedMm;
    s.c = reading(s);
    s.rate = (reading(s, S.simTime) - reading(s, S.simTime - 86400)) * 30; // mm per month over the last day
    s.level = triggerLevel(s.c, pred);
    s.pred = pred;
  }
  const rows = sections.slice(-7).reverse().map((s) => `<tr><td>${s.ch} m</td><td>${fmt(S.th - s.ch, 0)} m</td><td>${fmt(s.c, 1)}</td><td>${fmt(s.pred, 1)}</td><td>${fmt(s.rate, 1)}</td><td><span class="lvl ${s.level}">${s.level}</span></td><td>${s.rate < FINAL_LINING_RATE_MM_PER_MONTH && S.th - s.ch > 3 * D ? "yes" : "no"}</td></tr>`).join("");
  ui.monitor.innerHTML = `<table class="mon"><tr><th>Section</th><th>To face</th><th>Conv. mm</th><th>Pred. mm</th><th>mm/month</th><th>Level</th><th>Final lining</th></tr>${rows}</table>
    <p class="note">Five targets per section every ${SECTION_SPACING} m. Levels at 75 / 105 / 150 % of the predicted convergence (Crossrail). Final lining once the rate is below ${FINAL_LINING_RATE_MM_PER_MONTH} mm/month (FHWA).</p>`;

  const alarms = [];
  if (zTh.invert && !ringClosureOk(invLag, D)) alarms.push(`Ring not closed within one diameter: invert ${fmt(invLag, 1)} m behind the face (FHWA: within ${D} m in this ground)`);
  if (g.li.min_safety < 1.0) alarms.push(`Lining overstressed in this ground (safety ${fmt(g.li.min_safety, 2)}): thicker lining, yielding elements or earlier closure needed`);
  if (g.strain >= 2.5) alarms.push(`Squeezing class ${g.squeeze[0]}: ${g.squeeze[2]}`);
  for (const s of sections.filter((x) => x.level === "red" || x.level === "amber").slice(-3)) {
    alarms.push(s.level === "red" ? `Section ${s.ch} m at RED (${fmt(s.c, 1)} mm, ≥ 150 % of prediction): stop, make the face safe, emergency review` : `Section ${s.ch} m at AMBER (${fmt(s.c, 1)} mm): inspection and engineering review within 24 h`);
  }
  ui.alarms.innerHTML = alarms.length ? alarms.map((a) => `<div>${a}</div>`).join("") : `<div class="ok">Within limits</div>`;
}

ui.pause.onclick = () => { S.paused = !S.paused; ui.pause.textContent = S.paused ? "Resume" : "Pause"; };
ui.reset.onclick = () => { reset(); lastFace = null; ui.pause.textContent = "Pause"; };
ui.start.onchange = ui.reset.onclick;
ui.shot.onchange = () => { groundCache.clear(); };
if (innerWidth <= 640) ui.showLabels.checked = false;

// ---------------------------------------------------------------- loop
reset();
const shiftViews = (face) => { for (const v of Object.values(VIEWS)) { v.pos[2] = v.pos0 - face; v.target[2] = v.target0 - face; } };
for (const v of Object.values(VIEWS)) { v.pos0 = v.pos[2]; v.target0 = v.target[2]; }
shiftViews(S.th);
camera.position.set(...VIEWS.heading.pos);
controls.target.set(...VIEWS.heading.target);
controls.update();
lastFace = S.th;
hud();
let last = performance.now(), hudT = 0;
renderer.setAnimationLoop((now) => {
  const dtReal = Math.min((now - last) / 1000, 1 / 20);
  last = now;
  step(dtReal);
  shiftViews(S.th);
  animate();
  updateCamera(dtReal);
  if ((hudT += dtReal) > 0.2) { hudT = 0; hud(); }
  placeLabels(camera, ui.showLabels.checked);
  renderer.render(scene, camera);
});
