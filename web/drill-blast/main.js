// Slice E: drill & blast heading for a two-lane road tunnel (Norwegian T10.5 profile). Each round runs the activities
// of the cycle model one after another: survey, drilling with a three-boom jumbo, charging, blast, ventilation,
// scaling, mucking with a loader and trucks, bolting and sprayed concrete by support class (NFF / NGI Q). The round
// pattern and charges come from the round-design model; vibration at a building above uses the scaled-distance law
// and the SS 460 48 66 guide value.
//
// Frame: metres, Y up, the face at z = 0 and the excavated tunnel along +z; the world (rock, support) moves by +chainage.

import {
  designRound, roundCycle, HOURS_PER_WEEK, supportQuantities, SUPPORT_CLASSES, horseshoe, holeCharge, bottomCharge, ppv, maxChargePerDelay,
  ss4604866Limit, NORTHERN_LINK, emptyHolesForDepth, overbreakPercent,
} from "../../models/js/index.js";
import { THREE, createScene, label, placeLabels, mat, box, fmt, dl, CUT, BEHIND_FACE, AHEAD_OF_FACE } from "../hard-rock/common.js";

// ---------------------------------------------------------------- profile, ground, building
// T10.5 road tunnel: theoretical blast area 74.59 m^2 (N500, 2015). Modelled as vertical walls with a semicircular roof
// of the same area: 10.6 m span, 2.9 m walls.
const WIDTH = 10.6, WALL = 2.9, RR = WIDTH / 2;
const [, HEIGHT, AREA] = horseshoe(WIDTH, WALL);
const FY = -3.5; // floor level in the scene
const ZONES = [
  { name: "Gneiss, few joints", from: -60, to: 70, q: "10–40", cls: "I", color: 0x8a8580 },
  { name: "Jointed gneiss", from: 70, to: 100, q: "4–10", cls: "II", color: 0x7f7a73 },
  { name: "Weakness zone", from: 100, to: 125, q: "1–4", cls: "III", color: 0x716a62 },
  { name: "Clay-bearing fault", from: 125, to: 140, q: "0.1–1", cls: "IV", color: 0x5f5750 },
  { name: "Gneiss, few joints", from: 140, to: 600, q: "10–40", cls: "I", color: 0x8a8580 },
];
const zoneAt = (ch) => ZONES.find((z) => ch >= z.from && ch < z.to) ?? ZONES.at(-1);
// A house on rock above chainage 150 m: 25 m of rock over the crown, 12 m to the side (illustrative). Building factors
// as in the published Solna risk analysis (F_b 1.2, F_m 0.75): guide value 63 mm/s times the distance factor.
const BUILDING = { ch: 150, cover: 25, offset: 12, fB: 1.2, fM: 0.75 };
const UPPER_98 = 10 ** (2.054 * NORTHERN_LINK.sigma_log10); // 98 % upper bound of the Northern Link fit
const WORK_ZONE = 50; // m, face work zone; people withdraw beyond it to blast (NFF Publication 27)

// ---------------------------------------------------------------- scene
const VIEWS = {
  face: { title: "Face", pos: [-2.5, 2.2, 17], target: [0.3, -0.8, 0] },
  heading: { title: "Heading", pos: [-24, 7, 24], target: [2, -1, 12] },
  mucking: { title: "Mucking", pos: [-20, 4, 34], target: [1, -2, 16] },
  support: { title: "Support", pos: [-3.2, -2.4, 1.2], target: [2.5, 3.5, 7] },
};
const { renderer, scene, camera, controls, updateCamera } = createScene(VIEWS);
const world = new THREE.Group();
scene.add(world);
const NEAR_AHEAD = new THREE.Plane(new THREE.Vector3(0, 0, 1), 12); // show 12 m of rock ahead of the face

function profileShape(grow = 0) {
  const r = RR + grow, s = new THREE.Shape();
  s.moveTo(-r, FY - grow * 0.2);
  s.lineTo(r, FY - grow * 0.2);
  s.lineTo(r, FY + WALL);
  s.absarc(0, FY + WALL, r, 0, Math.PI, false);
  s.lineTo(-r, FY - grow * 0.2);
  return s;
}
// rock around the tunnel (kept behind the face) and the solid rock ahead of the face (transparent), per zone
for (const z of ZONES) {
  const len = z.to - z.from;
  const outer = new THREE.Shape();
  outer.moveTo(-16, FY - 6); outer.lineTo(16, FY - 6); outer.lineTo(16, FY + HEIGHT + 8); outer.lineTo(-16, FY + HEIGHT + 8); outer.closePath();
  outer.holes.push(profileShape(0.12));
  const m = new THREE.MeshStandardMaterial({ color: z.color, roughness: 1, side: THREE.DoubleSide, clippingPlanes: [CUT, BEHIND_FACE] });
  const tube = new THREE.Mesh(new THREE.ExtrudeGeometry(outer, { depth: len, bevelEnabled: false, curveSegments: 40 }), m);
  tube.position.z = -z.to;
  world.add(tube);
  const ahead = new THREE.Mesh(new THREE.ExtrudeGeometry(profileShape(0.12), { depth: len, bevelEnabled: false, curveSegments: 40 }),
    new THREE.MeshStandardMaterial({ color: z.color, roughness: 1, transparent: true, opacity: 0.18, depthWrite: false, clippingPlanes: [CUT, AHEAD_OF_FACE, NEAR_AHEAD] }));
  ahead.position.z = -z.to;
  world.add(ahead);
}
// the face itself and the road base (floor) behind it
const faceMat = new THREE.MeshStandardMaterial({ color: 0x8a8580, roughness: 1, side: THREE.DoubleSide });
const faceMesh = new THREE.Mesh(new THREE.ShapeGeometry(profileShape(0.12), 40), faceMat);
faceMesh.position.z = 0.0;
scene.add(faceMesh);
label("Face", faceMesh, [1.5, FY + HEIGHT - 1.2, 0]);
const floor = box(WIDTH + 0.2, 0.3, 400, mat(0x4a4744, { metalness: 0, roughness: 1, clippingPlanes: [CUT] }));
floor.position.set(0, FY - 0.15, 200);
scene.add(floor);

// holes on the face: a dot at the collar and the drilled hole into the rock ahead (instanced)
const MAX_HOLES = 260;
const holeColors = { empty: 0x2b2b2b, cut: 0xff7a45, stoping: 0xf2b43a, helper: 0xc9a227, floor: 0x5aa0e6, contour: 0x57c38a };
const collarGeo = new THREE.CircleGeometry(0.08, 10);
const collars = new THREE.InstancedMesh(collarGeo, new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide }), MAX_HOLES);
collars.frustumCulled = false;
scene.add(collars);
const boreGeo = new THREE.CylinderGeometry(0.024, 0.024, 1, 5).rotateX(Math.PI / 2).translate(0, 0, -0.5);
const bores = new THREE.InstancedMesh(boreGeo, new THREE.MeshBasicMaterial({ color: 0x2d2a26, clippingPlanes: [CUT] }), MAX_HOLES);
bores.frustumCulled = false;
scene.add(bores);

// ---------------------------------------------------------------- equipment (in the face frame)
const yellow = mat(0xd9a400), white = mat(0xe9e5dc), darkM = mat(0x3a3f45), red = mat(0xb8402e);
function vehicle(w, h, l, m, cab = true) {
  const g = new THREE.Group();
  const body = box(w, h, l, m);
  body.position.y = FY + 0.5 + h / 2;
  g.add(body);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 0.45, 16).rotateZ(Math.PI / 2), darkM);
    wh.position.set(sx * (w / 2 - 0.1), FY + 0.6, sz * (l / 2 - 1.0));
    g.add(wh);
  }
  if (cab) { const c = box(w * 0.8, 1.1, 1.6, mat(0x9cc7e6, { emissive: 0x16303f })); c.position.set(0, FY + 0.5 + h + 0.55, 0); g.add(c); }
  g.userData.body = body;
  return g;
}
// Jumbo: three booms (Sandvik DT1132i class: 3 x SB160i booms, 5.27 m hole on the standard 18 ft feed, 3.0 m wide)
const jumbo = vehicle(3.0, 1.6, 9.0, yellow);
const booms = [];
for (let i = 0; i < 3; i++) {
  const feed = box(0.22, 0.22, 7.16, mat(0x4f565e));
  const arm = box(0.28, 0.28, 1, yellow);
  jumbo.add(feed, arm);
  booms.push({ feed, arm, base: new THREE.Vector3([-0.9, 0.9, 0][i], FY + 2.0 + (i === 2 ? 0.6 : 0), 0) });
}
scene.add(jumbo);
label("Three-boom drill jumbo", jumbo.userData.body, [0, 1.8, 0]);
// charging truck with basket (Normet Charmec class), scaling rig, shotcrete sprayer (Spraymec class)
const charger = vehicle(2.6, 1.4, 8, white);
const basket = box(1.2, 0.9, 1.0, red);
charger.add(basket);
scene.add(charger);
label("Charging truck (bulk emulsion)", charger.userData.body, [0, 2.0, 0]);
const scaler = vehicle(2.6, 1.4, 8, yellow);
const hammer = box(0.3, 0.3, 4.5, darkM);
scaler.add(hammer);
scene.add(scaler);
label("Scaling rig", scaler.userData.body, [0, 2.0, 0]);
const sprayer = vehicle(2.6, 1.4, 8.5, white);
const nozzleArm = box(0.25, 0.25, 6, darkM);
sprayer.add(nozzleArm);
scene.add(sprayer);
label("Sprayed-concrete rig", sprayer.userData.body, [0, 2.0, 0]);
const loader = vehicle(3.2, 1.8, 9, yellow);
const bucket = box(3.4, 1.2, 1.2, darkM);
bucket.position.set(0, FY + 1.0, -5.0);
loader.add(bucket);
scene.add(loader);
label("Wheel loader", loader.userData.body, [0, 2.2, 0]);
const trucks = [vehicle(3.0, 2.2, 10, mat(0x7a8a99)), vehicle(3.0, 2.2, 10, mat(0x7a8a99))];
for (const t of trucks) scene.add(t);
label("Dump truck (25–35 t)", trucks[0].userData.body, [0, 2.6, 0]);

// muck pile: a mound behind the face, scaled by what is left to load
const pileGeo = new THREE.SphereGeometry(1, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2);
const pile = new THREE.Mesh(pileGeo, new THREE.MeshStandardMaterial({ color: 0x4f4a44, roughness: 1, flatShading: true, clippingPlanes: [CUT] }));
scene.add(pile);
label("Muck pile", pile, [0, 2.2, 0]);
// blast fumes: a box that fills the heading and clears during ventilation
const fumes = box(WIDTH, HEIGHT, 60, new THREE.MeshBasicMaterial({ color: 0xd8d2c4, transparent: true, opacity: 0, depthWrite: false, clippingPlanes: [CUT] }));
fumes.position.set(0, FY + HEIGHT / 2, 30);
scene.add(fumes);
const flash = new THREE.PointLight(0xffd29a, 0, 40);
flash.position.set(0, 0, 2);
scene.add(flash);
const ductAnchor = new THREE.Object3D();
ductAnchor.position.set(-RR + 0.8, FY + HEIGHT - 1.2, 20);
scene.add(ductAnchor);
const duct = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 300, 20).rotateX(Math.PI / 2), mat(0xd8d0b0, { metalness: 0, clippingPlanes: [CUT] }));
duct.position.set(-RR + 1.2, FY + WALL + RR * 0.55, 165);
scene.add(duct);
label("Ventilation duct (blowing)", duct, [0, 1.1, -145]);

// ---------------------------------------------------------------- support in the world (bolts, sprayed concrete, RRS)
const boltGeo = new THREE.CylinderGeometry(0.0125, 0.0125, 1, 4).translate(0, 0.5, 0);
const boltMat = mat(0xb0b6bc, { clippingPlanes: [CUT] }), plateMat = mat(0xe2e6ea, { metalness: 0.2, emissive: 0x2a2d30, clippingPlanes: [CUT] });
const shotMat = (cls) => new THREE.MeshStandardMaterial({ color: cls === "IV" ? 0xa9aaa3 : 0xbcbcb3, roughness: 1, side: THREE.DoubleSide, clippingPlanes: [CUT] });
function boltPositions(ch0, pull, cls) {
  const c = SUPPORT_CLASSES[cls], out = [];
  const roof = (s) => {
    const rows = Math.max(1, Math.floor(pull / s + 0.5)), n = Math.max(1, Math.round((Math.PI * RR) / s));
    for (let j = 0; j < rows; j++) for (let k = 0; k < n; k++) {
      const a = (Math.PI * (k + 0.5 + (j % 2) * 0.5)) / (n + 0.5);
      out.push({ z: ch0 + (j + 0.5) * (pull / rows), x: RR * Math.cos(a), y: FY + WALL + RR * Math.sin(a), nx: Math.cos(a), ny: Math.sin(a), len: 4 });
    }
  };
  if (c.roof_bolt) roof(c.roof_bolt);
  else for (let k = 0; k < 4; k++) { const a = Math.PI * (0.3 + 0.13 * k); out.push({ z: ch0 + pull * (0.2 + 0.2 * k), x: RR * Math.cos(a), y: FY + WALL + RR * Math.sin(a), nx: Math.cos(a), ny: Math.sin(a), len: 4 }); }
  if (c.wall_bolt) {
    const rows = Math.max(1, Math.floor(pull / c.wall_bolt + 0.5)), n = Math.max(1, Math.floor(WALL / c.wall_bolt + 0.5));
    for (const side of [-1, 1]) for (let j = 0; j < rows; j++) for (let k = 0; k < n; k++)
      out.push({ z: ch0 + (j + 0.5) * (pull / rows), x: side * RR, y: FY + 0.8 + ((k + 0.5) * (WALL - 0.8)) / n, nx: side, ny: 0, len: 3 });
  }
  return out;
}
function addBolt(b, group) {
  const m = new THREE.Mesh(boltGeo, boltMat);
  m.position.set(b.x, b.y, -b.z);
  m.scale.y = b.len;
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(b.nx, b.ny, 0));
  group.add(m);
  const p = box(0.3, 0.3, 0.03, plateMat); // plate drawn twice its size so the pattern reads
  p.position.set(b.x - b.nx * 0.03, b.y - b.ny * 0.03, -b.z);
  p.lookAt(p.position.x + b.nx, p.position.y + b.ny, p.position.z);
  group.add(p);
}
function shotcreteGeo(ch0, pull, cls) {
  // roof arch, and the walls down to 1.5 m above the floor where the class sprays them; thickness exaggerated x2 for view
  const c = SUPPORT_CLASSES[cls], s = new THREE.Shape(), t = 2 * c.roof_sc, tw = 2 * c.wall_sc;
  const yLow = c.wall_sc > 0 ? FY + 1.5 : FY + WALL;
  s.moveTo(RR, yLow);
  s.lineTo(RR, FY + WALL);
  s.absarc(0, FY + WALL, RR, 0, Math.PI, false);
  s.lineTo(-RR, yLow);
  s.lineTo(-RR + (tw || t), yLow);
  s.lineTo(-RR + (tw || t), FY + WALL);
  s.absarc(0, FY + WALL, RR - t, Math.PI, 0, true);
  s.lineTo(RR - (tw || t), yLow);
  s.closePath();
  const g = new THREE.ExtrudeGeometry(s, { depth: pull, bevelEnabled: false, curveSegments: 32 });
  g.translate(0, 0, -(ch0 + pull));
  return g;
}
// half-barrels: the half of each contour hole left in the wall, visible where the wall is not sprayed
const barrelMat = new THREE.MeshBasicMaterial({ color: 0x3a3632, clippingPlanes: [CUT] });
function halfBarrels(rd, ch0, cls, group) {
  const c = SUPPORT_CLASSES[cls];
  for (const h of rd.holes) {
    if (h.kind !== "contour") continue;
    const y = FY + h.y;
    if (y > FY + WALL || (c.wall_sc > 0 && y > FY + 1.5)) continue; // roof is always sprayed
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.03, rd.pull * 0.92), barrelMat);
    m.position.set(Math.sign(h.x) * (RR - 0.01), y, -(ch0 + rd.pull / 2));
    group.add(m);
  }
}
const support = [];

// ---------------------------------------------------------------- UI and state
const ids = ["start", "design", "depth", "depthOut", "firing", "ob", "obOut", "ts", "tsOut", "pause", "reset", "alarms", "round", "cycle", "support", "vibration",
  "faceSvg", "showLabels"];
const ui = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));
const val = (id) => +ui[id].value;
let S;

function newRound() {
  const zone = zoneAt(S.face);
  const rd = designRound(WIDTH, WALL, val("depth"), { design: ui.design.value });
  const cy = roundCycle(rd, WIDTH, WALL, zone.cls, { overbreak: val("ob") / 100 });
  const qb = bottomCharge(48, 1.15, 0.8);
  rd.kg = rd.holes.map((h) => holeCharge(h, val("depth"), WALL, qb, 48));
  S.rd = rd; S.cy = cy; S.cls = zone.cls; S.step = 0; S.left = cy.steps[0][1] * 3600; S.drilled = 0; S.charged = 0;
  S.bolts = boltPositions(S.face, rd.pull, zone.cls); // the round this cycle blasts, from the face forward
  S.boltsSet = 0; S.roundStart = S.simTime;
}
function reset() {
  for (const g of support.splice(0)) world.remove(g);
  const start = val("start");
  S = { face: start, simTime: 0, paused: false, rounds: 0, metres: 0, lastBlast: null, muckLeft: 0, muckTotal: 0, roundTimes: [] };
  // already excavated and supported behind the start
  for (let ch = start - 60; ch < start - 0.1; ch += 5) {
    const g = new THREE.Group(), cls = zoneAt(ch).cls;
    g.add(new THREE.Mesh(shotcreteGeo(ch, 5, cls), shotMat(cls)));
    for (const b of boltPositions(ch, 5, cls)) addBolt(b, g);
    world.add(g);
    support.push(g);
  }
  newRound();
  S.prevRd = S.rd;
}

const STEP_INDEX = (name) => S.cy.steps.findIndex(([n]) => n === name);
function finishStep(name) {
  if (name === "Connect and blast") {
    // the round breaks out: face advances by the pull, the muck lies behind the new face
    S.face += S.rd.pull;
    S.metres += S.rd.pull;
    S.muckTotal = S.muckLeft = S.cy.muck_m3;
    S.lastBlast = { at: S.simTime, maxDelay: chargePerDelay() };
    S.flash = 1;
    S.prevRd = S.rd;
  } else if (name === "Sprayed concrete") {
    const g = new THREE.Group();
    g.add(new THREE.Mesh(shotcreteGeo(S.face - S.rd.pull, S.rd.pull, S.cls), shotMat(S.cls)));
    if (SUPPORT_CLASSES[S.cls].rrs) {
      // one reinforced rib of sprayed concrete (RRS) in the round, over the roof and walls
      const rib = new THREE.Mesh(new THREE.TorusGeometry(RR - 0.32, 0.18, 6, 32, Math.PI), mat(0x9a9b94, { metalness: 0, roughness: 1, clippingPlanes: [CUT] }));
      rib.position.set(0, FY + WALL, -(S.face - S.rd.pull / 2));
      g.add(rib);
    }
    world.add(g);
    support.push(g);
  }
}
function step(dtReal) {
  if (S.paused) return;
  let dt = dtReal * val("ts");
  while (dt > 0) {
    const [name, hours] = S.cy.steps[S.step];
    const h = Math.min(dt, S.left);
    S.left -= h; S.simTime += h; dt -= h;
    const f = hours > 0 ? 1 - S.left / (hours * 3600) : 1;
    if (name === "Drilling") S.drilled = f;
    if (name === "Charging") S.charged = f;
    if (name === "Mucking") S.muckLeft = S.muckTotal * (1 - f);
    if (name === "Bolting") {
      const n = Math.floor(S.bolts.length * f);
      while (S.boltsSet < n) {
        const g = new THREE.Group();
        addBolt(S.bolts[S.boltsSet++], g);
        world.add(g); support.push(g);
      }
    }
    if (S.left <= 1e-6) {
      finishStep(name);
      if (name === "Sprayed concrete") {
        // half-barrels on unsprayed walls of the round just finished
        const g = new THREE.Group();
        halfBarrels(S.rd, S.face - S.rd.pull, S.cls, g);
        world.add(g); support.push(g);
      }
      S.step++;
      if (S.step >= S.cy.steps.length) {
        S.rounds++;
        S.roundTimes.push((S.simTime - S.roundStart) / 3600);
        newRound();
      } else S.left = S.cy.steps[S.step][1] * 3600;
    }
  }
}
function chargePerDelay() {
  if (ui.firing.value === "single") return Math.max(...S.rd.kg);
  const per = new Map();
  S.rd.holes.forEach((h, i) => { if (h.delay) per.set(h.delay, (per.get(h.delay) ?? 0) + S.rd.kg[i]); });
  return Math.max(...per.values());
}

// ---------------------------------------------------------------- animation
const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), one = new THREE.Vector3(1, 1, 1), v3 = new THREE.Vector3();
const hide = (...gs) => gs.forEach((g) => { g.visible = false; });
function place(g, z, x = 0) { g.visible = true; g.position.set(x, 0, z); }
function animate(dtReal) {
  world.position.z = S.face;
  const name = S.cy.steps[S.step][0];
  const rd = S.rd, depth = val("depth");
  // face holes
  const nShow = name === "Drilling" ? Math.floor(rd.holes.length * S.drilled) : ["Survey and marking"].includes(name) ? 0
    : ["Charging", "Connect and blast"].includes(name) ? rd.holes.length : 0;
  collars.count = bores.count = nShow;
  const col = new THREE.Color();
  for (let i = 0; i < nShow; i++) {
    const h = rd.holes[i];
    m4.compose(v3.set(h.x, FY + h.y, 0.02), q.identity(), one);
    collars.setMatrixAt(i, m4);
    const charged = name === "Connect and blast" || (name === "Charging" && i < rd.holes.length * S.charged);
    col.setHex(h.kind === "empty" ? holeColors.empty : charged ? holeColors[h.kind] : 0xf2efe8);
    collars.setColorAt(i, col);
    m4.compose(v3.set(h.x, FY + h.y, 0), q.identity(), new THREE.Vector3(1, 1, depth));
    bores.setMatrixAt(i, m4);
  }
  collars.instanceMatrix.needsUpdate = bores.instanceMatrix.needsUpdate = true;
  if (collars.instanceColor) collars.instanceColor.needsUpdate = true;
  // equipment by activity
  hide(jumbo, charger, scaler, sprayer, loader, ...trucks);
  if (name === "Drilling" || name === "Bolting") {
    const JZ = name === "Drilling" ? 7.2 : 10.5;
    place(jumbo, JZ);
    booms.forEach((b, i) => {
      const feed = b.feed;
      if (name === "Drilling") {
        // feed against the face at the hole being drilled, along the tunnel axis
        const t = rd.holes[Math.min(Math.floor(rd.holes.length * S.drilled) + i, rd.holes.length - 1)];
        feed.rotation.set(0, 0, 0);
        feed.scale.z = 1;
        feed.position.set(t.x, FY + t.y, 0.25 + 3.58 - JZ);
      } else {
        // feed up against the roof or wall of the new round at the bolt being set
        const t = S.bolts[Math.min(S.boltsSet + i, S.bolts.length - 1)] ?? { x: 0, y: FY + 6, z: S.face - 2, nx: 0, ny: 1 };
        feed.rotation.set(Math.PI / 2, 0, -Math.atan2(t.nx, t.ny));
        feed.scale.z = 0.5;
        feed.position.set(t.x - t.nx * 1.9, t.y - t.ny * 1.9, S.face - t.z - JZ);
        feed.position.z = Math.max(feed.position.z, -JZ + 0.6);
      }
      const start = b.base.clone().add(new THREE.Vector3(0, 0, -4.5));
      const end = feed.position.clone();
      b.arm.position.copy(start.clone().add(end).multiplyScalar(0.5));
      b.arm.scale.z = Math.max(start.distanceTo(end), 0.1);
      b.arm.lookAt(end.add(jumbo.position));
    });
  }
  if (name === "Charging") { place(charger, 6.5); basket.position.set(0, FY + 2.5 + 3 * Math.abs(Math.sin(S.simTime / 900)), -4.6); }
  if (name === "Scaling") { place(scaler, 7); hammer.position.set(0, FY + 4.5, -5); hammer.rotation.x = 0.55 + 0.2 * Math.sin(S.simTime / 300); }
  if (name === "Sprayed concrete") { place(sprayer, 9); nozzleArm.position.set(1.0 * Math.sin(S.simTime / 400), FY + 4.2, -3 - S.rd.pull / 2); nozzleArm.rotation.x = 0.45; }
  if (name === "Mucking") {
    const phase = (S.simTime / 240) % 1; // loader cycle, illustrative
    place(loader, 3.5 + rd.pull + 4.5 + 3 * Math.abs(Math.sin(Math.PI * phase)), -1.5);
    place(trucks[0], 3.5 + rd.pull + 16, 1.8);
    place(trucks[1], 3.5 + rd.pull + 40 + 20 * phase, -1.8);
  }
  // muck pile from the blasted round
  const muckFrac = S.muckTotal > 0 ? S.muckLeft / S.muckTotal : 0;
  pile.visible = muckFrac > 0.01 && ["Ventilation", "Scaling", "Mucking"].includes(name);
  pile.scale.set(RR * 0.95, 2.8 * Math.cbrt(muckFrac), 3 + S.rd.pull * muckFrac);
  pile.position.set(0, FY, 1.5 + S.rd.pull * 0.6);
  // fumes and flash
  const sinceBlast = S.lastBlast ? (S.simTime - S.lastBlast.at) / 3600 : 99;
  const vent = S.cy.steps[STEP_INDEX("Ventilation")][1];
  fumes.material.opacity = name === "Ventilation" ? 0.75 * Math.max(1 - sinceBlast / vent, 0) : 0;
  S.flash = Math.max((S.flash ?? 0) - dtReal * 2, 0);
  flash.intensity = 400 * S.flash;
  faceMat.color.setHex(zoneAt(S.face).color);
}

// ---------------------------------------------------------------- console
function faceSvg() {
  const rd = S.rd, sc = 26, w = (WIDTH + 1) * sc, h = (HEIGHT + 0.8) * sc;
  const X = (x) => (x + WIDTH / 2 + 0.5) * sc, Y = (y) => h - (y + 0.4) * sc;
  const p = `M ${X(-RR)} ${Y(0)} L ${X(RR)} ${Y(0)} L ${X(RR)} ${Y(WALL)} A ${RR * sc} ${RR * sc} 0 0 0 ${X(-RR)} ${Y(WALL)} Z`;
  const dots = rd.holes.map((o) => `<circle cx="${X(o.x).toFixed(1)}" cy="${Y(o.y).toFixed(1)}" r="${o.kind === "empty" ? 3.4 : 2.6}" fill="#${holeColors[o.kind].toString(16).padStart(6, "0")}"/>`).join("");
  const kinds = ["cut", "stoping", "helper", "floor", "contour", "empty"];
  const NAMES = { cut: "cut", stoping: "stoping", helper: "helper row", floor: "lifters", contour: "contour", empty: "empty (102 mm)" };
  const count = (k) => rd.holes.filter((o) => o.kind === k).length;
  return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Drilling pattern of the round"><path d="${p}" fill="#22262c" stroke="#6b7480"/>${dots}</svg>
    <div class="legend">${kinds.map((k) => `<span style="--c:#${holeColors[k].toString(16).padStart(6, "0")}">${NAMES[k]} ${count(k)}</span>`).join("")}</div>`;
}
function hud() {
  ui.tsOut.textContent = `×${val("ts")} (${fmt(val("ts") / 60, 0)} min per s)`;
  ui.depthOut.textContent = `${fmt(val("depth"), 1)} m`;
  ui.obOut.textContent = `${val("ob")} %`;
  const zone = zoneAt(S.face), rd = S.rd, cy = S.cy;
  const [name, hours] = cy.steps[S.step];
  const designKey = `${ui.design.value}|${val("depth")}`;
  if (faceSvg.key !== designKey) { faceSvg.key = designKey; ui.faceSvg.innerHTML = faceSvg(); }
  dl(ui.round, [
    ["Profile", `T10.5 road tunnel, ${fmt(AREA, 1)} m² theoretical (N500)`],
    ["Hole depth and pull", `${fmt(val("depth"), 2)} m → ${fmt(rd.pull, 2)} m (95 %, Holmberg)`],
    ["Empty holes in the cut", `${emptyHolesForDepth(val("depth"))} × 102 mm`],
    ["Charged holes", `${rd.n_charged} (Norwegian rounds of 71–95 m²: 126–158)`],
    ["Drill metres", `${fmt(rd.drill_metres, 0)} m (${fmt(rd.specific_drilling, 2)} m/m³)`],
    ["Explosive", `${fmt(rd.explosive, 0)} kg bulk emulsion, ${fmt(rd.specific_charge, 2)} kg/m³`],
  ]);
  // cycle: step bars with the current position
  const total = cy.total_h, done = cy.steps.slice(0, S.step).reduce((a, [, h]) => a + h, 0) + (hours - S.left / 3600);
  const COLORS = ["#7f8c99", "#3987e5", "#d95926", "#ff7a45", "#b8b2a6", "#c9a227", "#8a6a45", "#199e70", "#b07ad9", "#4b5560"];
  const bars = cy.steps.map(([n, hh], i) => `<i title="${n} ${fmt(hh, 2)} h" style="width:${(100 * hh) / total}%;background:${COLORS[i]};${i === S.step ? "outline:2px solid #e7e9ec;outline-offset:-2px" : ""}"></i>`).join("");
  const legend = cy.steps.map(([n, hh], i) => `<span style="--c:${COLORS[i]}">${n} ${fmt(hh, 1)} h</span>`).join("");
  const days = S.simTime / 86400;
  ui.cycle.innerHTML = `<dl>
      <dt>Now</dt><dd>${name}: ${fmt(S.left / 3600, 1)} h left</dd>
      <dt>Round</dt><dd>${S.rounds + 1}, face at ${fmt(S.face, 1)} m · ${fmt(done, 1)} of ${fmt(total, 1)} h</dd>
      <dt>Advance at ${HOURS_PER_WEEK} h per week</dt><dd>${fmt(cy.m_per_week, 0)} m/week (Tunnelbyggetid model, 74.6 m²: about 48; logged Ulvin, 120 m²: about 23; NFF 40–80)</dd>
      <dt>Achieved so far</dt><dd>${days > 0.2 ? `${fmt(S.metres, 1)} m in ${fmt(S.simTime / 3600, 0)} working hours` : "—"}</dd>
    </dl><div class="shares">${bars}</div><div class="legend">${legend}</div>
    <p class="note">Activities one after another at the face. Rates: NFF Publications 14, 26 and 28 (drilling 2 m/min per boom, mucking 200 m³/h, 12 bolts/h, 6 m³/h sprayed concrete); charging and positioning times assumed.</p>`;
  const sup = supportQuantities(WIDTH, WALL, rd.pull, zone.cls), c = SUPPORT_CLASSES[zone.cls];
  dl(ui.support, [
    ["Ground at the face", `${zone.name}, Q ${zone.q}`],
    ["Support class (NFF, road tunnels)", `${zone.cls}`],
    ["Roof bolts (4 m)", c.roof_bolt ? `${c.roof_bolt} × ${c.roof_bolt} m` : "spot bolting"],
    ["Wall bolts (3 m)", c.wall_bolt ? `${c.wall_bolt} × ${c.wall_bolt} m` : "spot"],
    ["Sprayed concrete", `${c.roof_sc * 1000} mm roof${c.wall_sc ? `, ${c.wall_sc * 1000} mm walls to 1.5 m above the floor` : ", walls scaled only"}${c.rrs ? ", reinforced ribs (RRS)" : ""}`],
    ["Per round", `${sup.bolts} bolts, ${fmt(sup.shotcrete * (1 + val("ob") / 100), 1)} m³ sprayed concrete`],
    ["Muck per round", `${fmt(cy.muck_m3, 0)} m³ solid, including ${fmt(overbreakPercent(AREA * (1 + val("ob") / 100), AREA), 0)} % overbreak`],
  ]);
  // vibration at the building for the next blast
  const dz = BUILDING.ch - S.face, dist = Math.hypot(dz, BUILDING.cover + (HEIGHT - 0.5), BUILDING.offset);
  const qd = chargePerDelay();
  const guide = ss4604866Limit(dist, { fB: BUILDING.fB, fM: BUILDING.fM });
  const v50 = ppv(dist, qd), v98 = v50 * UPPER_98;
  const qAllow = maxChargePerDelay(dist, guide / UPPER_98);
  dl(ui.vibration, [
    ["House above chainage", `${BUILDING.ch} m, ${BUILDING.cover} m of rock over the crown`],
    ["Distance from the face", `${fmt(dist, 0)} m`],
    ["Charge per delay", `${fmt(qd, 1)} kg (${ui.firing.value === "single" ? "one hole per delay" : "one delay per row: contour row together"})`],
    ["PPV, mean / 98 % bound", `${fmt(v50, 1)} / ${fmt(v98, 1)} mm/s (Northern Link fit)`],
    ["Guide value (SS 460 48 66)", `${fmt(guide, 1)} mm/s`],
    ["Allowed charge per delay (98 %)", `${fmt(qAllow, 1)} kg`],
  ]);
  const alarms = [];
  if (v98 > guide) alarms.push(`Vibration: the 98 % bound ${fmt(v98, 1)} mm/s exceeds the guide value ${fmt(guide, 1)} mm/s at the house; ${ui.firing.value === "row" ? "fire one hole per delay or " : ""}cut the charge per delay below ${fmt(qAllow, 1)} kg (shorter rounds put less explosive in each hole)`);
  else if (v50 > 0.5 * guide) alarms.push(`Vibration at the house ${fmt(v50, 1)} mm/s (mean), over half the guide value: monitor`);
  if (name === "Connect and blast" || name === "Ventilation") alarms.push(`Blasting: everyone outside ${WORK_ZONE} m of the face; warning to all work within 200 m (NFF Publication 27)`);
  if (zone.cls === "IV") alarms.push("Class IV: bolts at 1.3 m, 150 mm sprayed concrete and reinforced ribs in every round");
  ui.alarms.innerHTML = alarms.length ? alarms.map((a) => `<div>${a}</div>`).join("") : `<div class="ok">Within limits</div>`;
}

ui.pause.onclick = () => { S.paused = !S.paused; ui.pause.textContent = S.paused ? "Resume" : "Pause"; };
ui.reset.onclick = () => { reset(); ui.pause.textContent = "Pause"; };
ui.start.onchange = ui.reset.onclick;
// a new pattern or round length applies from the next round, as on site
for (const id of ["design", "depth", "ob"]) ui[id].addEventListener("change", () => { if (S.step === 0) newRound(); });
if (innerWidth <= 640) ui.showLabels.checked = false;

// ---------------------------------------------------------------- loop
reset();
hud();
let last = performance.now(), hudT = 0;
renderer.setAnimationLoop((now) => {
  const dtReal = Math.min((now - last) / 1000, 1 / 20);
  last = now;
  step(dtReal);
  animate(dtReal);
  updateCamera(dtReal);
  if ((hudT += dtReal) > 0.2) { hudT = 0; hud(); }
  placeLabels(camera, ui.showLabels.checked);
  renderer.render(scene, camera);
});
