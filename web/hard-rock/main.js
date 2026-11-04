// Slice B: hard-rock open gripper (main beam) TBM, laid out front to back after the method card in
// docs/research/methods-reference.md and the "hard-rock-main-beam-9.5m" preset (models/presets/machine-classes.json).
//
// Frame: metres, Y up, tunnel axis at y = 0. The machine stays at the origin with the cutter tips at z = 0 and the
// machine along +z; the world (rock, support) moves by +chainage, so the drive heads towards -z.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  tbmPerformance, maxRpm, PRACTICAL_MAX_PENETRATION_MM, DEFAULT_CUTTER, hardRockUtilisation, rmrClass, cuttersPerKm,
  cutterChangeHPerKm, recordCheck,
} from "../../models/js/index.js";

// ---------------------------------------------------------------- machine and geology
const M = {
  D: 9.58, // m, Gotthard-class main beam (preset, trade press, unverified)
  torque: 5290, power: 3500, thrustMax: 27488, // kNm, kW, kN (preset, unverified)
  nCutters: 62, // assumed: ~85 mm spacing over the face, plus centre and gauge cutters
  stroke: 1.8, // m, assumed (1.2-1.8 m reported only informally)
  regripMin: 4, // min, Farrokh (2018): 2-6 min per regrip
};
const R = M.D / 2;
const RPM_MAX = maxRpm(M.D);
// Illustrative alignment; strengths and RMR typical for the rock types (not a project).
const ZONES = [
  { name: "Gneiss", from: -40, to: 90, ucs: 150, bts: 10, cai: 3.5, quartz: 25, rmr: 70, color: 0x8a8f94 },
  { name: "Granite", from: 90, to: 170, ucs: 180, bts: 12, cai: 4.5, quartz: 30, rmr: 76, color: 0xa39488 },
  { name: "Fault zone (crushed, blocky)", from: 170, to: 215, ucs: 40, bts: 4, cai: 2.5, quartz: 15, rmr: 22, color: 0x6b5848 },
  { name: "Mica schist", from: 215, to: 330, ucs: 90, bts: 7, cai: 2.5, quartz: 15, rmr: 50, color: 0x7d8466 },
  { name: "Gneiss", from: 330, to: 700, ucs: 150, bts: 10, cai: 3.5, quartz: 25, rmr: 68, color: 0x8a8f94 },
];
const zoneAt = (ch) => ZONES.find((z) => ch >= z.from && ch < z.to) ?? ZONES.at(-1);

// Support pattern per RMR class (Bieniawski 1989, as in models/js/hard_rock.js): bolt rows along the tunnel, bolts per
// row over the crown arc, mesh arc, ring beams, shotcrete thickness in the crown (L2). Visual translation of the table.
const PATTERN = {
  I: { rowSpacing: Infinity, bolts: 0, arc: 0, mesh: 0, beams: 0, shot: 0 },
  II: { rowSpacing: 2.5, bolts: 3, arc: 60, mesh: 0, beams: 0, shot: 0.05 },
  III: { rowSpacing: 1.75, bolts: 9, arc: 200, mesh: 120, beams: 0, shot: 0.075 },
  IV: { rowSpacing: 1.25, bolts: 11, arc: 240, mesh: 240, beams: 1.5, shot: 0.125 },
  V: { rowSpacing: 1.0, bolts: 13, arc: 260, mesh: 260, beams: 0.75, shot: 0.175 },
};

// Positions along the machine (TBM frame, m behind the cutter tips)
const Z_HEAD = 0.9, Z_SHIELD1 = 4.2, Z_L1 = 5.2, Z_GRIP = 10.5, Z_LEGS = 19.5, Z_BEAM1 = 21, Z_L2 = 34, Z_INVERT = 27;

// ---------------------------------------------------------------- renderer and views
const canvas = document.getElementById("view");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.localClippingEnabled = true;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x15171a);
const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 800);
const controls = new OrbitControls(camera, canvas);
scene.add(new THREE.HemisphereLight(0xdfe7ef, 0x2a2420, 1.2));
const sun = new THREE.DirectionalLight(0xffffff, 1.5);
sun.position.set(-12, 20, -10);
scene.add(sun);
const lamp = new THREE.PointLight(0xfff1d6, 60, 30);
lamp.position.set(-1, 2, 6);
scene.add(lamp);

const VIEWS = {
  machine: { pos: [-22, 7, -6], target: [0, -0.5, 14] },
  face: { pos: [-6, 2.5, -9], target: [0, 0, 0.3] },
  l1: { pos: [-11, 3, 0], target: [0, 1.5, 6] },
  gripper: { pos: [-9, 6, 4], target: [0, -0.8, 12] },
  l2: { pos: [-13, 3, 22], target: [0, 0.5, 32] },
};
let camAnim = null;
function setView(name) {
  const v = VIEWS[name];
  camAnim = { t: 0, p0: camera.position.clone(), t0: controls.target.clone(), p1: new THREE.Vector3(...v.pos), t1: new THREE.Vector3(...v.target) };
  for (const b of document.querySelectorAll("#views button")) b.classList.toggle("on", b.dataset.view === name);
}
camera.position.set(...VIEWS.machine.pos);
controls.target.set(...VIEWS.machine.target);
controls.update();
for (const b of document.querySelectorAll("#views button")) b.onclick = () => setView(b.dataset.view);
function resize() {
  renderer.setSize(innerWidth, innerHeight, false);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

// three.js keeps the side a clipping plane's normal points to (signed distance >= 0). CUT keeps the far (x > 0) half,
// so the views from -x look into the machine; the rock tube is kept behind the face (z > 0), the rock block ahead of it.
const CUT = new THREE.Plane(new THREE.Vector3(1, 0, 0), 0);
const BEHIND_FACE = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
const AHEAD_OF_FACE = new THREE.Plane(new THREE.Vector3(0, 0, -1), 0);
const mat = (color, o = {}) => new THREE.MeshStandardMaterial({ color, metalness: 0.5, roughness: 0.5, ...o });
const yellow = mat(0xd9a400), steel = mat(0x8b939b, { metalness: 0.7, roughness: 0.35 }), dark = mat(0x3a3f45, { metalness: 0.6 });
const alongZ = (g) => g.rotateX(Math.PI / 2);
const cyl = (r, len, m, seg = 32) => new THREE.Mesh(alongZ(new THREE.CylinderGeometry(r, r, len, seg)), m);
const box = (w, h, d, m) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
const polar = (r, aDeg) => [r * Math.sin((aDeg * Math.PI) / 180), r * Math.cos((aDeg * Math.PI) / 180)]; // angle from the crown

const labelLayer = document.getElementById("labels");
const labels = [];
function label(text, obj, offset = [0, 0, 0]) {
  const el = document.createElement("div");
  el.textContent = text;
  labelLayer.appendChild(el);
  labels.push({ el, obj, offset: new THREE.Vector3(...offset) });
}

// ---------------------------------------------------------------- machine
const machine = new THREE.Group();
scene.add(machine);

// Cutterhead: flat face with a curved gauge (radius 0.5 m), 19-inch discs with radial axles, centre cluster, tilted
// gauge cutters and 8 buckets at the periphery.
const head = new THREE.Group();
machine.add(head);
const EXPOSE = 0.17, GAUGE_R = 0.5, FACE_Z = EXPOSE;
{
  const pts = [new THREE.Vector2(0.01, FACE_Z)];
  pts.push(new THREE.Vector2(R - GAUGE_R, FACE_Z));
  for (let k = 1; k <= 8; k++) {
    const a = (k / 8) * (Math.PI / 2);
    pts.push(new THREE.Vector2(R - GAUGE_R + GAUGE_R * Math.sin(a), FACE_Z + GAUGE_R * (1 - Math.cos(a))));
  }
  pts.push(new THREE.Vector2(R - 0.02, Z_HEAD), new THREE.Vector2(0.01, Z_HEAD));
  const body = new THREE.Mesh(new THREE.LatheGeometry(pts, 72).rotateX(Math.PI / 2), mat(0x3d434a, { metalness: 0.7, roughness: 0.45, side: THREE.DoubleSide }));
  head.add(body);
}
const discGeo = new THREE.CylinderGeometry(0.2413, 0.2413, 0.05, 24).rotateZ(Math.PI / 2); // axle along x before placing
const discMat = mat(0xb7bec6, { metalness: 0.85, roughness: 0.3 });
const saddleMat = mat(0x24282c);
function addCutter(r, aRad, tilt = 0) {
  const g = new THREE.Group();
  g.rotation.z = aRad;
  const holder = new THREE.Group();
  holder.position.set(r, 0, 0);
  holder.rotation.y = -tilt; // gauge cutters tilt outwards
  const disc = new THREE.Mesh(discGeo, discMat);
  disc.position.z = 0.2413; // tip on the cutting plane z = 0, about 0.17 m proud of the face plate
  holder.add(disc);
  const saddle = box(0.22, 0.42, 0.14, saddleMat);
  saddle.position.z = FACE_Z + 0.02;
  holder.add(saddle);
  g.add(holder);
  head.add(g);
}
{
  // centre cluster: 4 twin-disc positions
  for (let k = 0; k < 4; k++) addCutter(0.18 + k * 0.09, k * Math.PI * 0.5);
  // face cutters on a spiral at ~85 mm radial spacing
  const face = M.nCutters - 4 - 8;
  for (let k = 0; k < face; k++) {
    const r = 0.6 + (k / (face - 1)) * (R - GAUGE_R - 0.75);
    addCutter(r, k * 2.399963);
  }
  // gauge cutters on the curved transition, tilted up to ~65 degrees
  for (let k = 0; k < 8; k++) {
    const f = (k + 1) / 9, a = f * 1.13;
    const r = R - GAUGE_R + GAUGE_R * Math.sin(a) - 0.05;
    const g = new THREE.Group();
    g.rotation.z = k * (Math.PI / 4) + 0.2;
    const holder = new THREE.Group();
    holder.position.set(r, 0, FACE_Z + GAUGE_R * (1 - Math.cos(a)) - 0.12);
    holder.rotation.y = -a;
    const disc = new THREE.Mesh(discGeo, discMat);
    holder.add(disc);
    g.add(holder);
    head.add(g);
  }
}
// buckets: recessed openings with grill bars and scraper lips at the periphery
const BUCKETS = 8;
for (let k = 0; k < BUCKETS; k++) {
  const g = new THREE.Group();
  g.rotation.z = (k / BUCKETS) * Math.PI * 2 + Math.PI / BUCKETS;
  const opening = box(0.75, 0.5, 0.25, mat(0x0d0f11, { roughness: 1 }));
  opening.position.set(R - 0.75, 0, FACE_Z + 0.1);
  g.add(opening);
  for (let j = -1; j <= 1; j++) {
    const bar = box(0.7, 0.04, 0.05, steel);
    bar.position.set(R - 0.75, j * 0.14, FACE_Z - 0.02);
    g.add(bar);
  }
  const lip = box(0.7, 0.08, 0.12, mat(0x2b2f33, { metalness: 0.8 }));
  lip.position.set(R - 0.75, -0.3, FACE_Z - 0.03);
  g.add(lip);
  head.add(g);
}
label("Cutterhead: 19-inch discs, curved gauge", head, [0, R + 0.6, 0.4]);
label("Muck buckets with grill bars", head, [R - 0.7, -R + 0.4, 0]);

// Muck ring and chute: buckets drop the muck into a funnel at the centre, onto the machine belt.
const chute = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.35, 1.0, 24, 1, true).rotateX(Math.PI / 2), mat(0x6e5d3a, { side: THREE.DoubleSide }));
chute.position.set(0, 0.6, Z_HEAD + 0.6);
machine.add(chute);
label("Muck ring and chute", chute, [0, 1.0, 0]);

// Cutterhead support with roof shield (fingers), side shields and invert shoe.
const support = cyl(2.6, Z_SHIELD1 - Z_HEAD, dark, 40);
support.position.z = (Z_HEAD + Z_SHIELD1) / 2;
machine.add(support);
label("Main bearing and drive motors", support, [0, -2.9, 0]);
function shell(r, aFrom, aTo, z0, z1, m) {
  // a cylindrical sector between angles from the crown (degrees), along z0..z1
  const g = new THREE.CylinderGeometry(r, r, z1 - z0, 32, 1, true, ((aFrom) * Math.PI) / 180, ((aTo - aFrom) * Math.PI) / 180);
  g.rotateX(Math.PI / 2);
  const mesh = new THREE.Mesh(g, m);
  mesh.position.z = (z0 + z1) / 2;
  return mesh;
}
const shieldMat = mat(0xc89200, { side: THREE.DoubleSide, clippingPlanes: [CUT] });
const roof = shell(R - 0.05, -65, 65, Z_HEAD, Z_SHIELD1, shieldMat);
roof.rotation.z = Math.PI; // CylinderGeometry's theta 0 is +z before rotation; flip so the sector sits at the crown
machine.add(roof);
for (let k = 0; k < 9; k++) {
  const [x, y] = polar(R - 0.08, -56 + k * 14);
  const finger = box(0.25, 0.06, 1.3, mat(0xc89200));
  finger.position.set(x, y, Z_SHIELD1 + 0.6);
  finger.rotation.z = -Math.atan2(x, y);
  machine.add(finger);
}
label("Roof shield with fingers", roof, [0, R + 0.4, 0]);
for (const side of [-1, 1]) {
  const s = shell(R - 0.05, 0, 40, Z_HEAD + 0.4, Z_SHIELD1 - 0.3, shieldMat);
  s.rotation.z = side > 0 ? -Math.PI / 2 - 0.35 : Math.PI / 2 - 0.35;
  machine.add(s);
}
const shoe = shell(R - 0.05, 0, 70, Z_HEAD + 0.2, Z_SHIELD1, shieldMat);
shoe.rotation.z = -0.61;
machine.add(shoe);
label("Invert shoe (steering pivot)", shoe, [0, -R + 0.2, 0]);

// Main beam with the machine belt on top, from the chute back to the backup conveyor.
const beam = box(1.6, 1.4, Z_BEAM1 - Z_SHIELD1, mat(0xd9a400));
beam.position.set(0, -0.6, (Z_SHIELD1 + Z_BEAM1) / 2);
machine.add(beam);
label("Main beam", beam, [0, -1.0, 2]);
const BELT_Y = 0.25;
const belt = box(1.1, 0.12, Z_BEAM1 - Z_HEAD, dark);
belt.position.set(0, BELT_Y, (Z_HEAD + Z_BEAM1) / 2 + 0.5);
machine.add(belt);
label("Machine belt", belt, [0, 0.4, 3]);

// L1 zone: two roof drills, ring-beam erector, mesh handler, probe drill.
const drills = [];
for (const side of [-1, 1]) {
  const g = new THREE.Group();
  g.position.set(0, 0.6, Z_L1 + (side > 0 ? 0.8 : 0));
  const arm = box(0.2, 0.2, 0.2, mat(0x2f6f9f));
  g.add(arm);
  const feed = box(0.18, 2.4, 0.18, mat(0x2f6f9f));
  feed.position.y = 1.6;
  g.add(feed);
  const rod = box(0.05, 1.4, 0.05, steel);
  rod.position.y = 3.2;
  g.add(rod);
  g.userData = { side, rod, feed };
  machine.add(g);
  drills.push(g);
}
label("L1: roof drills (rock bolts)", drills[1], [0, 3.2, 0]);
const ringErector = new THREE.Mesh(new THREE.TorusGeometry(R - 0.55, 0.09, 8, 64, Math.PI * 1.4), mat(0x5b8db8));
ringErector.rotation.z = -Math.PI * 0.2;
ringErector.position.z = Z_L1 + 1.8;
machine.add(ringErector);
label("L1: ring-beam erector and mesh handler", ringErector, [0, R - 0.2, 0]);
const probe = new THREE.Group();
const probeFeed = box(0.18, 0.18, 3.2, mat(0x8a3f2b));
probe.add(probeFeed);
probe.position.set(-1.2, R - 0.9, Z_L1 - 0.4);
probe.rotation.x = -0.12;
machine.add(probe);
label("Probe drill (ahead of the face)", probe, [0, 0.5, 0]);

// Gripper unit: carrier, two shoes braced against the walls, propel cylinders to the front of the main beam.
const gripper = new THREE.Group();
machine.add(gripper);
const carrier = box(3.4, 1.6, 2.6, mat(0xd9a400));
carrier.position.y = -0.5;
gripper.add(carrier);
const grips = [];
for (const side of [-1, 1]) {
  const cylG = cyl(0.25, 1, mat(0x5b8db8), 16);
  cylG.rotation.y = Math.PI / 2;
  gripper.add(cylG);
  const shoeG = box(0.35, 2.6, 3.2, mat(0x6e7a86));
  gripper.add(shoeG);
  grips.push({ side, cyl: cylG, shoe: shoeG });
}
label("Gripper shoes (react thrust and torque)", gripper, [-R + 0.5, 1.8, 0]);
const propels = [];
for (const [x, y] of [[-1.0, 0.3], [1.0, 0.3], [-1.0, -1.2], [1.0, -1.2]]) {
  const c = new THREE.Mesh(alongZ(new THREE.CylinderGeometry(0.12, 0.12, 1, 12)).translate(0, 0, 0.5), mat(0x5b8db8));
  c.position.set(x, y, Z_L1 + 2.6);
  machine.add(c);
  propels.push(c);
}
label("Propel (thrust) cylinders", propels[0], [0, 0.4, 2]);
const legs = [];
for (const x of [-1.2, 1.2]) {
  const leg = box(0.35, 1, 0.35, mat(0x6e7a86));
  machine.add(leg);
  legs.push(leg);
}
label("Rear legs", legs[0], [0, -0.6, 0]);

// Backup: gantries on rails over the invert segments, L2 shotcrete robot, invert segment erector, conveyor, duct.
const RAIL_Y = -R + 0.62;
for (const x of [-1.1, 1.1]) {
  const rail = box(0.08, 0.12, 120, steel);
  rail.position.set(x, RAIL_Y, Z_INVERT + 60);
  machine.add(rail);
}
const gantryMat = mat(0x4f7f5a, { roughness: 0.6, clippingPlanes: [CUT] });
for (let k = 0; k < 6; k++) {
  const z = Z_BEAM1 + 2 + k * 13;
  const g = new THREE.Group();
  g.position.z = z + 6;
  // open portal frames: posts at both ends, longitudinal beams and a deck
  for (const x of [-2.6, 2.6]) {
    for (const dz of [-5.6, 5.6]) { const post = box(0.25, 4.2, 0.25, gantryMat); post.position.set(x, RAIL_Y + 2.2, dz); g.add(post); }
    for (const y of [0.5, 4.2]) { const rail = box(0.2, 0.25, 12, gantryMat); rail.position.set(x, RAIL_Y + y, 0); g.add(rail); }
  }
  const deck = box(5.4, 0.12, 12, gantryMat);
  deck.position.y = RAIL_Y + 4.3;
  g.add(deck);
  machine.add(g);
  if (k === 3) { const tr = box(1.6, 1.4, 3, mat(0x6e7a86)); tr.position.set(-1.6, RAIL_Y + 5.1, z + 4); machine.add(tr); label("Transformers and hydraulic power", tr, [0, 1, 0]); }
}
const bconv = box(1.0, 0.12, 80, dark);
bconv.position.set(0, RAIL_Y + 4.6, Z_BEAM1 + 40);
machine.add(bconv);
label("Backup conveyor", bconv, [0, 0.5, -24]);
const transfer = box(1.2, 0.12, 4.5, dark);
transfer.position.set(0, (BELT_Y + RAIL_Y + 4.6) / 2, Z_BEAM1 + 1.8);
transfer.rotation.x = -Math.atan2(RAIL_Y + 4.6 - BELT_Y, 4.5);
machine.add(transfer);
const robot = new THREE.Group();
robot.position.set(0, 1.0, Z_L2);
const rbase = box(0.6, 0.6, 0.6, mat(0xe9e5dc));
robot.add(rbase);
const rarm = box(0.2, 2.6, 0.2, mat(0xe9e5dc));
rarm.position.y = 1.4;
robot.add(rarm);
const spray = new THREE.Mesh(new THREE.ConeGeometry(0.45, 1.0, 16, 1, true), new THREE.MeshBasicMaterial({ color: 0xcfcfc6, transparent: true, opacity: 0.35, side: THREE.DoubleSide }));
spray.position.y = 3.1;
spray.rotation.x = Math.PI;
robot.add(spray);
machine.add(robot);
label("L2: shotcrete robot", robot, [0, 3.0, 0]);
const invertErector = box(2.2, 0.5, 0.6, mat(0x5b8db8));
invertErector.position.set(0, RAIL_Y + 1.2, Z_INVERT - 1.5);
machine.add(invertErector);
label("Invert segment erector", invertErector, [0, 0.6, 0]);
const duct = cyl(0.65, 80, new THREE.MeshStandardMaterial({ color: 0xe8e4d6, roughness: 1 }), 16);
duct.position.set(2.4, 2.6, Z_BEAM1 + 42); // far (kept) side of the cut-away
machine.add(duct);
label("Ventilation duct", duct, [0, 0.9, -30]);

// Muck on the belts (visual; spawn rate follows the excavated volume, bulked 1.6).
const MUCK_MAX = 600;
const muck = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(0.07, 0), new THREE.MeshStandardMaterial({ color: 0x77706a, roughness: 1, flatShading: true }), MUCK_MAX);
muck.count = 0;
muck.frustumCulled = false;
machine.add(muck);
const muckZ = [], muckX = [];

// ---------------------------------------------------------------- world: rock, support, invert segments
const world = new THREE.Group();
scene.add(world);
for (const z of ZONES) {
  const len = z.to - z.from;
  const rockMat = new THREE.MeshStandardMaterial({ color: z.color, roughness: 1, side: THREE.DoubleSide, clippingPlanes: [CUT, BEHIND_FACE] });
  const tube = new THREE.Mesh(alongZ(new THREE.CylinderGeometry(R, R, len, 64, 1, true)), rockMat);
  tube.position.z = -(z.from + len / 2);
  world.add(tube);
  const ahead = box(14, 14, len, new THREE.MeshStandardMaterial({ color: z.color, roughness: 1, transparent: true, opacity: 0.22, depthWrite: false, clippingPlanes: [AHEAD_OF_FACE, CUT] }));
  ahead.position.z = -(z.from + len / 2);
  world.add(ahead);
}
const BOLT_MAX = 6000, BEAM_MAX = 600, INV_MAX = 400;
const bolts = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.05, 0.05, 0.5, 6).translate(0, 0.25, 0), mat(0xc9a227, { metalness: 0.8, clippingPlanes: [CUT] }), BOLT_MAX);
const plates = new THREE.InstancedMesh(new THREE.BoxGeometry(0.22, 0.03, 0.22), mat(0x8b939b, { clippingPlanes: [CUT] }), BOLT_MAX);
const beamsI = new THREE.InstancedMesh(new THREE.TorusGeometry(R - 0.12, 0.11, 6, 48, Math.PI * 1.5).rotateZ(-Math.PI * 0.25), mat(0x7a8590, { metalness: 0.6, roughness: 0.4, clippingPlanes: [CUT] }), BEAM_MAX);
const invI = new THREE.InstancedMesh(new THREE.BoxGeometry(3.6, 0.45, 1.8), mat(0xb0aea6, { roughness: 0.9, clippingPlanes: [CUT] }), INV_MAX);
// instances are added as the drive advances; their bounds are computed once, so never frustum-cull them
for (const im of [bolts, plates, beamsI, invI]) { im.count = 0; im.frustumCulled = false; world.add(im); }
const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e3 = new THREE.Euler(), v3 = new THREE.Vector3(), s3 = new THREE.Vector3(1, 1, 1);

function placeBolt(aDeg, wz) {
  if (bolts.count >= BOLT_MAX) return;
  const [x, y] = polar(R - 0.02, aDeg);
  e3.set(0, 0, -(aDeg * Math.PI) / 180);
  q.setFromEuler(e3);
  // rod points outwards into the rock; plate on the surface
  m4.compose(v3.set(x, y, wz), q, s3);
  bolts.setMatrixAt(bolts.count++, m4);
  plates.setMatrixAt(plates.count++, m4);
}
// Mesh and shotcrete: one piece per metre, geometry shared per arc angle.
const arcGeoCache = new Map();
function arcMesh(kind, arcDeg) {
  const key = `${kind}|${arcDeg}`;
  if (!arcGeoCache.has(key)) {
    const a = (arcDeg * Math.PI) / 180;
    const r = kind === "mesh" ? R - 0.06 : R - 0.02;
    const g = new THREE.CylinderGeometry(r, r, 1.0, 48, 2, true, -a / 2, a).rotateX(Math.PI / 2).rotateZ(Math.PI);
    arcGeoCache.set(key, g);
  }
  return arcGeoCache.get(key);
}
const meshMat = new THREE.MeshBasicMaterial({ color: 0x9aa4ae, wireframe: true, clippingPlanes: [CUT] });
const shotMats = { 0.05: 0xc7c4bb, 0.075: 0xbdbab1, 0.125: 0xb3b0a7, 0.175: 0xa9a69d };
const supportPieces = [];
function addArcPiece(kind, arcDeg, wz, len, thickness) {
  const m = kind === "mesh" ? meshMat : new THREE.MeshStandardMaterial({ color: shotMats[thickness] ?? 0xb9b6ad, roughness: 1, side: THREE.DoubleSide, clippingPlanes: [CUT] });
  const piece = new THREE.Mesh(arcMesh(kind, arcDeg), m);
  piece.position.z = wz;
  piece.scale.z = len;
  if (kind === "shot") piece.scale.x = piece.scale.y = 1 - thickness / R; // thickness inwards
  world.add(piece);
  supportPieces.push(piece);
  if (supportPieces.length > 1400) world.remove(supportPieces.shift());
}

// ---------------------------------------------------------------- UI and state
const ids = ["start", "thrust", "rpm", "haulage", "org", "ts", "thrustOut", "rpmOut", "tsOut", "pause", "skip", "reset", "alarms", "cutting", "cycle", "rock", "forecast", "showLabels"];
const ui = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));
const val = (id) => +ui[id].value;
let S;
function reset() {
  for (const p of supportPieces) world.remove(p);
  supportPieces.length = 0;
  for (const im of [bolts, plates, beamsI, invI]) im.count = 0;
  const start = val("start");
  S = {
    chainage: start, stroke: 0, mode: "BORING", t: 0, simTime: 0, paused: false, perf: null,
    regripT: 0, stopLeft: 0, stopText: "", boringTime: 0, l1Done: start - 60, l2Done: start - 60, invDone: start - 60, nextRow: start - 60, nextBeam: start - 60,
    cuttersUsed: 0, muckDebt: 0, zoneUtil: null,
  };
  world.position.z = start;
  installSupport(); // the 60 m behind the start are already bored and supported
}
reset();

const orgClasses = () => ({ normal: ["normal", "normal"], good: ["good", "good"], poor: ["poor", "poor"] })[ui.org.value];
function utilAt(zone, pr) {
  const [maint, transport] = orgClasses();
  return hardRockUtilisation(Math.max(pr, 0.05), M.D, {
    stroke_m: M.stroke, regrip_min: M.regripMin, ucs_mpa: zone.ucs, rmr: zone.rmr, machine: "open", haulage: ui.haulage.value,
    cutter_h_per_km: cutterChangeHPerKm(M.D, zone.cai), maintenance: maint, transport,
  });
}

// Support installation as the rock passes the L1 and L2 zones (TBM-local z = chainage - ch_world).
function installSupport() {
  // L1: bolts, mesh and ring beams for each metre that has reached the L1 zone
  while (S.l1Done < S.chainage - Z_L1) {
    const ch = S.l1Done + 0.5, zone = zoneAt(ch), cls = rmrClass(zone.rmr).class, p = PATTERN[cls];
    if (ch >= S.nextRow && p.bolts > 0) {
      for (let k = 0; k < p.bolts; k++) placeBolt(-p.arc / 2 + (p.bolts > 1 ? (k * p.arc) / (p.bolts - 1) : 0), -ch);
      S.nextRow = ch + p.rowSpacing;
    }
    if (p.mesh > 0) addArcPiece("mesh", p.mesh, -ch, 1.0, 0);
    if (p.beams > 0 && ch >= S.nextBeam && beamsI.count < BEAM_MAX) {
      m4.compose(v3.set(0, 0, -ch), q.identity(), s3);
      beamsI.setMatrixAt(beamsI.count++, m4);
      S.nextBeam = ch + p.beams;
    }
    S.l1Done += 1;
  }
  // L2: shotcrete in the crown, thickness by class
  while (S.l2Done < S.chainage - Z_L2) {
    const ch = S.l2Done + 0.5, p = PATTERN[rmrClass(zoneAt(ch).rmr).class];
    if (p.shot > 0) addArcPiece("shot", Math.max(p.arc, 120), -ch, 1.02, p.shot);
    S.l2Done += 1;
  }
  // invert segments behind the gripper, every 1.8 m
  while (S.invDone < S.chainage - Z_INVERT && invI.count < INV_MAX) {
    const ch = S.invDone + 0.9;
    m4.compose(v3.set(0, -R + 0.32, -ch), q.identity(), s3);
    invI.setMatrixAt(invI.count++, m4);
    S.invDone += 1.8;
  }
  for (const im of [bolts, plates, beamsI, invI]) im.instanceMatrix.needsUpdate = true;
}

function substep(dt) {
  const zone = zoneAt(S.chainage);
  const rpm = Math.min(val("rpm"), RPM_MAX);
  S.perf = tbmPerformance({ thrust_kn: val("thrust"), rpm, n_cutters: M.nCutters, head_diameter_m: M.D, ucs_mpa: zone.ucs, bts_mpa: zone.bts,
    max_torque_knm: M.torque, max_power_kw: M.power, max_penetration_mm: PRACTICAL_MAX_PENETRATION_MM });
  S.zoneUtil = utilAt(zone, S.perf.rop_m_h);
  S.simTime += dt;
  if (S.mode === "BORING") {
    const adv = Math.min((S.perf.rop_m_h / 3600) * dt, M.stroke - S.stroke);
    S.stroke += adv;
    S.chainage += adv;
    S.boringTime += dt;
    S.cuttersUsed += (cuttersPerKm(M.D, zone.cai) * adv) / 1000;
    S.muckDebt += Math.PI * R * R * adv * 1.6;
    if (S.stroke >= M.stroke - 1e-9) { S.mode = "REGRIP"; S.regripT = 0; }
  } else if (S.mode === "REGRIP") {
    S.regripT += dt;
    if (S.regripT >= M.regripMin * 60) {
      // all other downtime of this stroke, from the per-km breakdown at the current rock and penetration rate
      const h = S.zoneUtil.h_per_km;
      const parts = Object.entries(h).filter(([k]) => k !== "boring" && k !== "regrip").map(([k, v]) => [k, (v * M.stroke) / 1000]);
      const total = parts.reduce((a, [, v]) => a + v, 0);
      parts.sort((a, b) => b[1] - a[1]);
      S.stopLeft = total * 3600;
      S.stopText = parts.slice(0, 3).map(([k, v]) => `${NAMES[k]} ${fmt(v * 60, 0)} min`).join(", ");
      S.mode = "STOPPED";
      S.stroke = 0;
    }
  } else {
    S.stopLeft -= dt;
    if (S.stopLeft <= 0) { S.mode = "BORING"; S.stopLeft = 0; }
  }
}
function step(dtReal) {
  if (!S.perf) substep(0); // first frame and after a reset: evaluate the cutting state once
  if (S.paused) return;
  let dt = dtReal * val("ts");
  while (dt > 1e-9) { const h = Math.min(dt, 2); substep(h); dt -= h; }
  installSupport();
}

// ---------------------------------------------------------------- animation
const NAMES = { tbm_breakdown: "TBM repairs", backup: "backup", cutters: "cutter changes", support: "rock support", maintenance: "maintenance", transport: "transport",
  utilities: "utility extension", survey: "survey", other: "other", regrip: "regrip", boring: "boring" };
function animate(dtReal) {
  world.position.z = S.chainage;
  const rpm = S.mode === "BORING" ? Math.min(val("rpm"), RPM_MAX) : 0;
  head.rotation.z -= (rpm / 60) * 2 * Math.PI * dtReal;
  // grippers: fixed to the rock while boring (carrier slides back along the beam), repositioned during the regrip
  let gz = Z_GRIP + S.stroke, legDown = 0, gripIn = 0;
  if (S.mode === "REGRIP") {
    const f = S.regripT / (M.regripMin * 60);
    legDown = f < 0.2 ? f / 0.2 : f > 0.85 ? (1 - f) / 0.15 : 1;
    gripIn = f < 0.2 ? 0 : f < 0.35 ? (f - 0.2) / 0.15 : f < 0.75 ? 1 : f < 0.9 ? 1 - (f - 0.75) / 0.15 : 0;
    gz = Z_GRIP + M.stroke * (f < 0.35 ? 1 : f < 0.75 ? 1 - (f - 0.35) / 0.4 : 0);
  }
  gripper.position.z = gz;
  for (const g of grips) {
    const x = g.side * (R - 0.25 - 0.35 * gripIn);
    g.shoe.position.set(x, -0.2, 0);
    g.cyl.position.set(g.side * (1.7 + (R - 0.45 - 0.35 * gripIn - 1.7) / 2), -0.3, 0);
    g.cyl.scale.y = R - 0.45 - 0.35 * gripIn - 1.7;
  }
  for (const c of propels) c.scale.z = Math.max(gz - (Z_L1 + 2.6) - 1.0, 0.2);
  for (const [i, leg] of legs.entries()) {
    const len = 1.2 + 0.9 * legDown;
    leg.scale.y = len;
    leg.position.set(i ? 1.2 : -1.2, -1.3 - len / 2, Z_LEGS);
  }
  // roof drills work while the rock at L1 needs bolts; the shotcrete robot sweeps while L2 needs shotcrete
  const p1 = PATTERN[rmrClass(zoneAt(S.chainage - Z_L1).rmr).class], p2 = PATTERN[rmrClass(zoneAt(S.chainage - Z_L2).rmr).class];
  const tt = performance.now() / 1000;
  for (const d of drills) {
    const active = p1.bolts > 0;
    d.rotation.z = active ? d.userData.side * (0.2 + 0.5 * Math.abs(Math.sin(tt * 0.3 + d.userData.side))) : d.userData.side * 0.15;
    d.userData.rod.scale.y = active ? 0.6 + 0.4 * Math.abs(Math.sin(tt * 0.9)) : 0.3;
  }
  robot.rotation.z = p2.shot > 0 ? Math.sin(tt * 0.7) * 0.9 : 0;
  spray.visible = p2.shot > 0 && S.mode !== "STOPPED";
  // muck: one chunk per 0.05 m^3 loose, up the chute and along both belts at 2.5 m/s
  const spawn = Math.min(Math.floor(S.muckDebt / 0.05), 8);
  S.muckDebt = Math.min(S.muckDebt - spawn * 0.05, 1);
  for (let k = 0; k < spawn && muckZ.length < MUCK_MAX; k++) { muckZ.push(Z_HEAD + 0.6 + Math.random() * 0.4); muckX.push((Math.random() - 0.5) * 0.7); }
  let n = 0;
  const mm = new THREE.Matrix4();
  for (let k = 0; k < muckZ.length; k++) {
    muckZ[k] += 2.5 * dtReal;
    if (muckZ[k] > Z_BEAM1 + 78) continue;
    muckZ[n] = muckZ[k]; muckX[n] = muckX[k];
    const z = muckZ[n];
    const y = z < Z_BEAM1 ? BELT_Y + 0.12 : z < Z_BEAM1 + 3.8 ? BELT_Y + 0.12 + ((RAIL_Y + 4.6 - BELT_Y) * (z - Z_BEAM1)) / 3.8 : RAIL_Y + 4.72;
    mm.makeTranslation(muckX[n], y, z);
    muck.setMatrixAt(n++, mm);
  }
  muckZ.length = muckX.length = n;
  muck.count = n;
  muck.instanceMatrix.needsUpdate = true;
}

// ---------------------------------------------------------------- HUD
const fmt = (v, d = 1) => (Number.isFinite(v) ? v.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d }) : "—");
const dl = (el, rows) => { el.innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join(""); };
const COLORS = { boring: "#3987e5", regrip: "#7f8c99", tbm_breakdown: "#d95926", backup: "#c9a227", cutters: "#b07ad9", support: "#ff7a45",
  maintenance: "#199e70", transport: "#5fa8d3", utilities: "#9ccc65", survey: "#e0a24a", other: "#4b5560" };
function hud() {
  ui.thrustOut.textContent = `${fmt(val("thrust") / 1000, 2)} MN`;
  ui.rpmOut.textContent = `${fmt(Math.min(val("rpm"), RPM_MAX), 1)} rpm`;
  ui.tsOut.textContent = `×${val("ts")}`;
  const zone = zoneAt(S.chainage), p = S.perf, cls = rmrClass(zone.rmr), pat = PATTERN[cls.class];
  const LIMIT = { thrust: "thrust", penetration: `penetration cap ${PRACTICAL_MAX_PENETRATION_MM} mm/rev (muck handling)`, torque: "installed torque", power: "installed power" };
  dl(ui.cutting, [
    ["Penetration", `${fmt(p.penetration_mm_rev, 2)} mm/rev`],
    ["Penetration rate", `${fmt(p.rop_m_h, 2)} m/h`],
    ["Limited by", LIMIT[p.limited_by]],
    ["Load per cutter", `${fmt(p.normal_per_cutter_kn, 0)} kN (rated ${DEFAULT_CUTTER.max_load_kn})`],
    ["Thrust used by cutters", `${fmt(p.thrust_used_kn / 1000, 2)} of ${fmt(val("thrust") / 1000, 2)} MN`],
    ["Torque", `${fmt(p.cutterhead_torque_knm, 0)} of ${fmt(p.torque_available_knm, 0)} kNm available`],
    ["Power", `${fmt(p.cutterhead_power_kw, 0)} of ${M.power} kW`],
    ["Speed limit (gauge cutters)", `${fmt(RPM_MAX, 2)} rpm`],
  ]);
  const days = S.simTime / 86400;
  const modeText = S.mode === "BORING" ? `BORING (stroke ${fmt(S.stroke, 2)} of ${M.stroke} m)` : S.mode === "REGRIP" ? `REGRIP (${fmt(M.regripMin * 60 - S.regripT, 0)} s left)`
    : `STOPPED: ${S.stopText} (${fmt(S.stopLeft / 3600, 1)} h left)`;
  ui.skip.disabled = S.mode !== "STOPPED";
  dl(ui.cycle, [
    ["Mode", modeText],
    ["Chainage", `${fmt(S.chainage, 1)} m`],
    ["Simulated time", `${Math.floor(S.simTime / 3600)} h ${String(Math.floor((S.simTime % 3600) / 60)).padStart(2, "0")} min`],
    ["Achieved", days > 0.05 ? `${fmt(S.chainage / days, 1)} m/day · utilisation ${fmt((S.boringTime / S.simTime) * 100, 0)} %` : "—"],
    ["Cutters used", `${fmt(S.cuttersUsed, 1)} (${fmt(cuttersPerKm(M.D, zone.cai), 0)} per km in this rock)`],
  ]);
  dl(ui.rock, [
    ["Rock at the face", zone.name],
    ["UCS, BTS", `${zone.ucs} MPa, ${zone.bts} MPa`],
    ["CAI, quartz", `${zone.cai}, ${zone.quartz} %`],
    ["RMR, class", `${zone.rmr}, ${cls.class} (${cls.name})`],
    ["Bolts", cls.bolts],
    ["Shotcrete", cls.shotcrete],
    ["Steel ribs", cls.ribs],
    ["Next zone", (() => { const n = ZONES.find((z) => z.from > S.chainage); return n ? `${n.name} in ${fmt(n.from - S.chainage, 0)} m` : "—"; })()],
  ]);
  const alarms = [];
  if (p.cutter_overloaded) alarms.push(`Cutter overload: ${fmt(p.normal_per_cutter_kn, 0)} kN per disc above the ${DEFAULT_CUTTER.max_load_kn} kN rating`);
  if (p.limited_by === "penetration") alarms.push("Penetration at the muck-handling cap: excess thrust is not used; in blocky ground expect overbreak");
  if (p.limited_by === "torque" || p.limited_by === "power") alarms.push(`Cutterhead at its ${p.limited_by} limit: more thrust does not cut faster`);
  if (val("rpm") > RPM_MAX) alarms.push(`Speed held at ${fmt(RPM_MAX, 2)} rpm (gauge-cutter speed limit)`);
  if (zone.rmr < 40) alarms.push(`${cls.name} rock (RMR ${zone.rmr}): heavy support at L1, ring beams, low wall strength under the grippers`);
  ui.alarms.innerHTML = alarms.length ? alarms.map((a) => `<div>${a}</div>`).join("") : `<div class="ok">Within limits</div>`;

  const u = S.zoneUtil;
  const sh = Object.entries(u.h_per_km);
  const rec = recordCheck(M.D, u.advance_m_day, u.advance_m_day * 7, u.advance_m_day * 30, "gripper");
  ui.forecast.innerHTML = `<dl>
    <dt>In this rock, at this speed</dt><dd>${fmt(u.advance_m_day, 1)} m/day</dd>
    <dt>Utilisation</dt><dd>${fmt(u.utilisation * 100, 0)} %</dd>
    <dt>Total time per km</dt><dd>${fmt(u.total_h_per_km, 0)} h</dd>
    <dt>World record, ${M.D} m class</dt><dd>${fmt(rec.day.world_record, 1)} m/day best day</dd>
  </dl>
  <div class="shares">${sh.map(([k, v]) => `<i title="${NAMES[k]} ${fmt(v, 0)} h/km" style="width:${(100 * v) / u.total_h_per_km}%;background:${COLORS[k]}"></i>`).join("")}</div>
  <div class="legend">${sh.filter(([, v]) => v / u.total_h_per_km > 0.01).map(([k, v]) => `<span style="--c:${COLORS[k]}">${NAMES[k]} ${fmt(v, 0)}</span>`).join("")}</div>
  <p class="note">Hours per km by activity (Farrokh 2018), at the current rock, penetration rate, haulage and site organisation. Mean rates sit well below the class record, which is a best day.</p>`;
}

ui.pause.onclick = () => { S.paused = !S.paused; ui.pause.textContent = S.paused ? "Resume" : "Pause"; };
ui.reset.onclick = () => { reset(); ui.pause.textContent = "Pause"; };
ui.start.onchange = () => { reset(); ui.pause.textContent = "Pause"; };
ui.skip.onclick = () => { if (S.mode === "STOPPED") { S.simTime += S.stopLeft; S.stopLeft = 0; S.mode = "BORING"; } };
ui.showLabels.onchange = () => { labelLayer.style.display = ui.showLabels.checked ? "" : "none"; };
if (innerWidth <= 640) { ui.showLabels.checked = false; labelLayer.style.display = "none"; }

const tmp = new THREE.Vector3();
function placeLabels() {
  if (!ui.showLabels.checked) return;
  for (const l of labels) {
    l.obj.getWorldPosition(tmp);
    tmp.add(l.offset);
    const d = tmp.distanceTo(camera.position);
    tmp.project(camera);
    const vis = tmp.z < 1 && Math.abs(tmp.x) < 1 && Math.abs(tmp.y) < 1 && d < 30;
    l.el.style.display = vis ? "" : "none";
    if (vis) { l.el.style.left = `${((tmp.x + 1) / 2) * innerWidth}px`; l.el.style.top = `${((1 - tmp.y) / 2) * innerHeight}px`; }
  }
}

// ---------------------------------------------------------------- loop
step(0);
hud();
let last = performance.now(), hudT = 0;
renderer.setAnimationLoop((now) => {
  const dtReal = Math.min((now - last) / 1000, 1 / 20);
  last = now;
  step(dtReal);
  animate(S.paused ? 0 : dtReal);
  if (camAnim) {
    camAnim.t = Math.min(camAnim.t + dtReal / 0.8, 1);
    const e = camAnim.t * camAnim.t * (3 - 2 * camAnim.t);
    camera.position.lerpVectors(camAnim.p0, camAnim.p1, e);
    controls.target.lerpVectors(camAnim.t0, camAnim.t1, e);
    if (camAnim.t >= 1) camAnim = null;
  }
  controls.update();
  if ((hudT += dtReal) > 0.15) { hudT = 0; hud(); }
  placeLabels();
  renderer.render(scene, camera);
});
