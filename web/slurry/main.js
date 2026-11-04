// Slice C: urban slurry shield (Mixshield) driven by the analytical models (models/js), laid out front to back after
// the method card in docs/research/methods-reference.md and the "urban-mixshield-7m" class preset. Built from the EPB
// page: the screw conveyor and foam give way to a submerged wall, an air cushion in the working chamber, a crusher at
// the suction inlet, feed and discharge lines along the backup, and the slurry-circuit and filter-cake checks.
//
// Frame: metres, Y up, tunnel axis at y = 0. The machine stays at the origin with the cutterhead at z = 0 and the
// shield along +z; the world (ground, rings, surface) moves by +chainage, so the drive heads towards -z.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  wedgeSilo, daubWindow, shieldThrust, cutterheadTorque, toolTorque,
  infiltration as slurryInfiltration, cushion as makeCushion, facePressure, dischargeDensity, drySolidsFlow, theoreticalDryFlow,
  durandVelocity, pipeVelocity, CONTROL_TOLERANCE,
  verticalStress, presetTrough, burlandCategory, referenceInstalled, erf,
  Rng, sample as sampleDist, DIST, SHIFT_PATTERNS, PER_CYCLE_MAINTENANCE_MIN, simulateDrive, recordCheck, EPB_WEEKLY_SURVEY,
  jsceRing, woodInertia, subgradeModulus, ringLoads, sectionStresses, jackingStress, burstingForce, annulusVolume, groutWindow, ITA2000_ALLOWABLE,
} from "../../models/js/index.js";

// ---------------------------------------------------------------- machine and scenario
// Sourced values (see machine-classes.json): diameter, installed torque and power (Crossrail Mixshields), 1.6 m rings with
// 7 segments + key and 6.2 m inner diameter (Crossrail Thames tunnels), DN300 slurry lines at 1000 m^3/h (Herrenknecht
// Mixshield data sheet). Values marked "assumed" are illustrative.
const M = {
  D: 7.08, // m, sourced
  torqueLimit: 3709, // kNm installed, sourced
  power: 1120, // kW installed, sourced
  shieldLength: 9.5, // assumed
  chamberLength: 0.9, // excavation chamber, assumed
  workingChamber: 1.6, // m behind the submerged wall, assumed
  ringWidth: 1.6, // m, sourced
  ringOD: 6.8, ringID: 6.2, // ID sourced, 300 mm segments assumed
  buildMin: 35, // min per ring (same assumption as the EPB page)
  shieldWeight: 4000, backupWeight: 6000, tailSeal: 500, // kN, assumed
  nTools: 80, toolForce: 4, // kN tangential each, assumed
  pipe: 0.3, // DN300 feed and discharge lines, sourced
  slurryWeight: 11.0, // kN/m^3 support slurry (bentonite), assumed within 10.3-12
  feedDensity: 1.05, // t/m^3 fresh slurry, assumed
};
const R = M.D / 2;
const AREA = Math.PI * R * R;
const Z0 = 15; // axis depth, m
const WATER = 1; // water table depth, m: saturated sands and gravels, the slurry machine's ground (DAUB 2025)
const ZONES = [
  { name: "Dense sand", Es: 60e3, from: -60, to: 20, gamma: 20, phi: 35, c: 0, k0: 0.43, k: 0.35, d10: 0.15e-3, rho: 2.0, color: 0xb59a62 },
  { name: "Sandy gravel", Es: 100e3, from: 20, to: 260, gamma: 21, phi: 38, c: 0, k0: 0.38, k: 0.3, d10: 1.0e-3, rho: 2.1, color: 0x8f8a7c },
];
const zoneAt = (ch) => ZONES.find((z) => ch >= z.from && ch < z.to) ?? ZONES.at(-1);
const BUILDINGS = [
  { name: "Building A", x: -4, ch: 45, w: 14, d: 10, h: 12 },
  { name: "Building B", x: 13, ch: 95, w: 12, d: 16, h: 18 },
  { name: "Building C", x: -20, ch: 150, w: 16, d: 12, h: 9 },
];

// Air cushion in the working chamber: plan area at the slurry level and initial air volume, assumed.
const CUSHION = makeCushion(2 * R * M.workingChamber * 0.9);
const AIR0 = 0.35 * Math.PI * R * R * M.workingChamber;
const LEVEL_SP = 0.5; // m above the axis: "slightly above the machine axis" (DAUB 2016)
// Durand limit with the coefficient corrected by sqrt(R_sd) (Miedema: the original graph overestimates by ~1.28)
const DEPOSIT_LIMIT = durandVelocity(M.pipe, 1.34 / Math.sqrt(1.65));

// ---------------------------------------------------------------- renderer and views
const canvas = document.getElementById("view");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.localClippingEnabled = true;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x15171a);
const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 800);
const controls = new OrbitControls(camera, canvas);
scene.add(new THREE.HemisphereLight(0xdfe7ef, 0x2a2420, 0.9));
const sun = new THREE.DirectionalLight(0xffffff, 1.1);
sun.position.set(-12, 25, -10);
scene.add(sun);

const VIEWS = {
  machine: { pos: [18, 5.5, -2], target: [0, -0.6, 6] },
  chamber: { pos: [8.5, 1.0, 0.6], target: [0, -0.3, 1.9] },
  tail: { pos: [10.5, 1.8, 2.5], target: [0, -0.8, 9.5] },
  surface: { pos: [85, 72, -35], target: [0, Z0, 18] },
};
let camAnim = null, currentView = "machine";
// camera position for a view; on portrait screens the camera backs off so the machine still fits
function viewPos(name) {
  const v = VIEWS[name], t = new THREE.Vector3(...v.target);
  const back = Math.min(2, Math.max(1, 1 / camera.aspect));
  return [new THREE.Vector3(...v.pos).sub(t).multiplyScalar(back).add(t), t];
}
function setView(name) {
  const [p1, t1] = viewPos(name);
  camAnim = { t: 0, p0: camera.position.clone(), t0: controls.target.clone(), p1, t1 };
  for (const b of document.querySelectorAll("#views button")) b.classList.toggle("on", b.dataset.view === name);
  currentView = name;
  // the cutterhead is cut away only in the chamber view, so the paste, arms and bulkhead cells show
  for (const m of headMats) m.clippingPlanes = name === "chamber" ? CUT : [];
  for (const m of headMats) m.needsUpdate = true;
}
camera.aspect = innerWidth / innerHeight;
{
  const [p, t] = viewPos("machine");
  camera.position.copy(p);
  controls.target.copy(t);
  controls.update();
}
for (const b of document.querySelectorAll("#views button")) b.onclick = () => setView(b.dataset.view);

function resize() {
  renderer.setSize(innerWidth, innerHeight, false);
  camera.aspect = innerWidth / innerHeight;
  // on wide screens, centre the view in the space left of the console
  if (innerWidth > 640) camera.setViewOffset(innerWidth, innerHeight, Math.min(180, innerWidth * 0.22), 0, innerWidth, innerHeight);
  else camera.setViewOffset(innerWidth, innerHeight, 0, innerHeight * 0.2, innerWidth, innerHeight); // console is a bottom sheet
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

// Cut-away: shells (shield, lining, ground) lose their x > 0 half so the inside is visible.
const CUT = [new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0)];
const mat = (color, o = {}) => new THREE.MeshStandardMaterial({ color, metalness: 0.5, roughness: 0.5, ...o });
const yellow = mat(0xd9a400), steel = mat(0x8b939b, { metalness: 0.7, roughness: 0.35 }), dark = mat(0x3a3f45, { metalness: 0.6 });
const shellMat = mat(0xc89200, { side: THREE.DoubleSide, clippingPlanes: CUT });
const alongZ = (g) => g.rotateX(Math.PI / 2);
const cyl = (r, len, m, seg = 32) => new THREE.Mesh(alongZ(new THREE.CylinderGeometry(r, r, len, seg)), m);
const box = (w, h, d, m) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);

// Labels: HTML tags projected from 3-D anchors.
const labelLayer = document.getElementById("labels");
const labels = [];
function label(text, obj, offset = [0, 0, 0], surfaceTag = false) {
  const el = document.createElement("div");
  el.textContent = text;
  labelLayer.appendChild(el);
  const l = { el, obj, offset: new THREE.Vector3(...offset), surfaceTag };
  labels.push(l);
  return l;
}

// ---------------------------------------------------------------- machine (fixed at the origin)
const machine = new THREE.Group();
scene.add(machine);

// Cutterhead: spoke type with soft-ground tools, rim, hub and fishtail; partial face plates set the opening ratio.
const headYellow = mat(0xd9a400), headDark = mat(0x3a3f45, { metalness: 0.6 }), headRim = mat(0xd9a400, { side: THREE.DoubleSide }), headSteel = mat(0x8b939b, { metalness: 0.7, roughness: 0.35 });
const cutterhead = new THREE.Group();
cutterhead.position.z = 0.25;
machine.add(cutterhead);
cutterhead.add(cyl(0.6, 0.6, headYellow, 24));
const fishtail = new THREE.Mesh(new THREE.ConeGeometry(0.35, 0.7, 4).rotateX(-Math.PI / 2), headDark);
fishtail.position.z = -0.6;
cutterhead.add(fishtail);
const rim = new THREE.Mesh(alongZ(new THREE.CylinderGeometry(R - 0.02, R - 0.02, 0.5, 64, 1, true)), headRim);
cutterhead.add(rim);
const SPOKES = 6, PLATE_DEG = 19;
const toolMat = mat(0x2b2f33, { metalness: 0.8 });
const headMats = [headYellow, headDark, headRim, headSteel, toolMat];
for (let k = 0; k < SPOKES; k++) {
  const a = (k * 2 * Math.PI) / SPOKES;
  const arm = new THREE.Group();
  arm.rotation.z = a;
  const spoke = box(R - 0.6, 0.5, 0.5, headYellow);
  spoke.position.x = 0.6 + (R - 0.6) / 2;
  arm.add(spoke);
  // rippers on the spoke front, scrapers along both edges
  for (let r = 0.9; r < R - 0.1; r += 0.45) {
    const rip = box(0.12, 0.12, 0.18, toolMat);
    rip.position.set(r, 0, -0.33);
    arm.add(rip);
    for (const s of [-1, 1]) {
      const scr = box(0.3, 0.06, 0.1, toolMat);
      scr.position.set(r + 0.1, s * 0.27, -0.28);
      arm.add(scr);
    }
  }
  cutterhead.add(arm);
  // partial face plate between spokes
  const sh = new THREE.Shape();
  const a0 = (Math.PI / SPOKES) - (PLATE_DEG * Math.PI) / 360, a1 = (Math.PI / SPOKES) + (PLATE_DEG * Math.PI) / 360;
  sh.absarc(0, 0, R - 0.15, a0, a1, false);
  sh.absarc(0, 0, 0.7, a1, a0, true);
  const plate = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.12, bevelEnabled: false }), headYellow);
  plate.rotation.z = a;
  plate.position.z = -0.25;
  cutterhead.add(plate);
}
// Opening ratio of the drawn head (spokes, plates, hub, rim); spoke-type heads are ~30-40 % (methods-reference).
// The torque model uses this value, so the picture and the numbers agree.
const closedArea = SPOKES * 0.5 * (R - 0.6) + SPOKES * (PLATE_DEG / 360) * Math.PI * ((R - 0.15) ** 2 - 0.7 ** 2) + Math.PI * 0.6 ** 2 + 2 * Math.PI * R * 0.12;
const drawnOpening = 1 - closedArea / AREA;
// mixing arms (rotors) on the back of the head
for (let k = 0; k < 4; k++) {
  const a = (k * Math.PI) / 2 + Math.PI / 4;
  const rotor = box(0.25, 0.25, 0.55, headSteel);
  rotor.position.set(2.3 * Math.cos(a), 2.3 * Math.sin(a), 0.5);
  cutterhead.add(rotor);
}
label("Cutterhead (spoke type, soft-ground tools)", cutterhead, [0, R + 0.5, -0.3]);
label("Mixing arms", cutterhead, [0, -2.3, 0.6]);

// Excavation chamber full of bentonite slurry.
const paste = new THREE.Mesh(alongZ(new THREE.CylinderGeometry(R - 0.06, R - 0.06, M.chamberLength - 0.1, 48)),
  new THREE.MeshStandardMaterial({ color: 0x5a4128, roughness: 0.5, transparent: true, opacity: 0.6, depthWrite: false, side: THREE.DoubleSide, clippingPlanes: CUT }));
paste.position.z = 0.25 + M.chamberLength / 2 + 0.05;
machine.add(paste);

// Submerged wall with its opening at the invert, then the working chamber (slurry below the air cushion), then the
// pressure bulkhead.
const ZB = 0.25 + M.chamberLength + 0.25; // submerged wall
const ZPB = ZB + M.workingChamber; // pressure bulkhead
const wallShape = new THREE.Shape();
{
  const yCut = -R + 0.9, a = Math.asin(yCut / (R - 0.03));
  wallShape.absarc(0, 0, R - 0.03, a, Math.PI - a, false);
  wallShape.closePath();
}
const bulkhead = new THREE.Mesh(new THREE.ExtrudeGeometry(wallShape, { depth: 0.15, bevelEnabled: false, curveSegments: 48 }), mat(0xb88a00, { clippingPlanes: CUT }));
bulkhead.position.z = ZB - 0.075;
machine.add(bulkhead);
label("Submerged wall (opening at the invert)", bulkhead, [0, 2.6, 0]);
const pressureBulkhead = cyl(R - 0.03, 0.15, mat(0xa07800, { clippingPlanes: CUT }), 64);
pressureBulkhead.position.z = ZPB;
machine.add(pressureBulkhead);
label("Pressure bulkhead", pressureBulkhead, [0, 2.9, 0]);
// working chamber: slurry up to the level, air cushion above (rebuilt when the level moves)
const wcSlurryMat = new THREE.MeshStandardMaterial({ color: 0x5a4128, roughness: 0.5, transparent: true, opacity: 0.85, depthWrite: false, side: THREE.DoubleSide, clippingPlanes: CUT });
const wcAirMat = new THREE.MeshStandardMaterial({ color: 0xcfe8ff, roughness: 0.2, transparent: true, opacity: 0.3, depthWrite: false, side: THREE.DoubleSide, clippingPlanes: CUT });
const wcSlurry = new THREE.Mesh(new THREE.BufferGeometry(), wcSlurryMat), wcAir = new THREE.Mesh(new THREE.BufferGeometry(), wcAirMat);
wcSlurry.position.z = wcAir.position.z = ZB + 0.08;
machine.add(wcSlurry, wcAir);
let wcLevelDrawn = null;
function drawWorkingChamber(level) {
  if (wcLevelDrawn !== null && Math.abs(level - wcLevelDrawn) < 0.02) return;
  wcLevelDrawn = level;
  const r = R - 0.1, y = Math.max(Math.min(level, r - 0.05), -r + 0.05), a = Math.asin(y / r);
  const below = new THREE.Shape(), above = new THREE.Shape();
  below.absarc(0, 0, r, Math.PI - a, 2 * Math.PI + a, false); below.closePath();
  above.absarc(0, 0, r, a, Math.PI - a, false); above.closePath();
  const opts = { depth: M.workingChamber - 0.16, bevelEnabled: false, curveSegments: 32 };
  wcSlurry.geometry.dispose(); wcAir.geometry.dispose();
  wcSlurry.geometry = new THREE.ExtrudeGeometry(below, opts);
  wcAir.geometry = new THREE.ExtrudeGeometry(above, opts);
}
label("Working chamber: air cushion over the slurry", wcAir, [-0.5, 1.6, 0.8]);
const cells = [];
for (const [y, name] of [[R * 0.75, "crown"], [R * 0.4, "upper"], [0, "axis"], [-R * 0.4, "lower"], [-R * 0.75, "invert"]]) {
  const c = cyl(0.13, 0.06, new THREE.MeshStandardMaterial({ color: 0x57c38a, emissive: 0x1a3a28 }), 16);
  c.position.set(-0.9, y, ZB - 0.1);
  machine.add(c);
  cells.push({ mesh: c, y, name });
}
label("Pressure sensors", cells[1].mesh, [0, 0.3, 0]);
for (const a of [Math.PI * 0.1, Math.PI * 1.1]) {
  const st = box(0.22, 0.22, 0.45, steel);
  st.position.set(1.6 * Math.cos(a), 1.6 * Math.sin(a), ZB - 0.3);
  machine.add(st);
}
const drive = cyl(1.7, 1.1, dark, 40);
drive.position.z = ZPB + 0.65;
machine.add(drive);
label("Main drive", drive, [0, 1.9, 0]);
const manlock = new THREE.Group();
for (const dz of [0, 1.6]) {
  const ch = cyl(0.65, 1.5, mat(0x6e7a86), 24);
  ch.position.z = dz;
  manlock.add(ch);
}
manlock.position.set(-1.4, 1.75, ZPB + 1.0);
machine.add(manlock);
label("Man-lock", manlock, [0, 0.9, 0.8]);

// Slurry circuit in the machine: feed line into the upper excavation chamber; suction with intake grid and jaw crusher
// at the invert in front of the submerged wall; both lines run back through the bulkheads and along the backup.
const crusher = box(1.4, 0.7, 0.6, mat(0x5b5f66));
crusher.position.set(0, -R + 0.55, ZB - 0.45);
machine.add(crusher);
label("Jaw crusher and intake grid", crusher, [1.2, 0.2, 0]);
const pipeMat = (c) => mat(c, { metalness: 0.4 });
const curve = (pts) => new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(...p)), false, "catmullrom", 0.1);
const FEED_CURVE = curve([[-1.0, 2.2, ZB - 0.3], [-1.0, 2.2, ZPB + 0.3], [-2.2, 1.4, ZPB + 3], [-1.9, 1.2, 12], [-1.9, 1.2, 95]]);
const DIS_CURVE = curve([[0, -R + 0.55, ZB - 0.2], [0, -R + 0.5, ZPB + 1], [-0.6, -2.4, 9], [-1.4, 0.4, 14], [-1.4, 0.4, 95]]);
const feedPipe = new THREE.Mesh(new THREE.TubeGeometry(FEED_CURVE, 120, 0.17, 10), pipeMat(0x4f7fb0));
const disPipe = new THREE.Mesh(new THREE.TubeGeometry(DIS_CURVE, 140, 0.17, 10), pipeMat(0x8a6a45));
machine.add(feedPipe, disPipe);
label("Feed line (fresh slurry, DN300)", feedPipe, [-1.9, 1.8, 10]);
label("Discharge line (slurry and soil, DN300)", disPipe, [-1.4, 0.9, 13]);

// Shield: front shield, articulation joint, tail shield with brush seals and grout lines.
const front = new THREE.Mesh(alongZ(new THREE.CylinderGeometry(R - 0.01, R - 0.01, 5.1, 72, 1, true)), shellMat);
front.position.z = 2.55;
machine.add(front);
const artic = new THREE.Mesh(new THREE.TorusGeometry(R - 0.06, 0.06, 8, 72), mat(0x3a3f45, { clippingPlanes: CUT }));
artic.position.z = 5.15;
machine.add(artic);
label("Articulation joint", artic, [0, R + 0.3, 0]);
const tailShield = new THREE.Mesh(alongZ(new THREE.CylinderGeometry(R - 0.04, R - 0.04, M.shieldLength - 5.2, 72, 1, true)), shellMat);
tailShield.position.z = 5.2 + (M.shieldLength - 5.2) / 2;
machine.add(tailShield);
label("Front shield", front, [0, R + 0.4, -1]);
label("Tail shield", tailShield, [0, R + 0.4, 1]);
const brushMat = mat(0x22262a, { metalness: 0.3, roughness: 0.9, clippingPlanes: CUT });
for (const dz of [0, 0.18, 0.36]) {
  const b = new THREE.Mesh(new THREE.TorusGeometry((M.ringOD / 2 + R - 0.04) / 2, 0.05, 6, 72), brushMat);
  b.position.z = M.shieldLength - 0.55 + dz;
  machine.add(b);
}
label("Tail seal (3 rows of greased wire brushes)", tailShield, [0, -R - 0.2, 4.0]);
for (const a of [0.6, 1.3, 1.9, 2.55]) {
  const g = cyl(0.05, 3.6, mat(0x8a5a2b), 8);
  g.position.set((R - 0.1) * Math.cos(a + Math.PI / 2), (R - 0.1) * Math.sin(a + Math.PI / 2), M.shieldLength - 1.8);
  machine.add(g);
}

// Ring build position: the new ring occupies z in [ZR, ZR + w] inside the tail.
const W = M.ringWidth;
const ZR = M.shieldLength - W - 0.75;

// Thrust cylinders: 16 pairs on the ring mid-thickness, pushing on the front face of the last ring.
const N_CYL = 16, RC = (M.ringOD + M.ringID) / 4, BODY0 = ZR - 3.0, BODY1 = ZR - 1.6;
const cylinders = [];
const rodGeo = alongZ(new THREE.CylinderGeometry(0.07, 0.07, 1, 10)).translate(0, 0, 0.5);
const cylBodyMat = mat(0x5b8db8, { clippingPlanes: CUT }), rodMat = mat(0x8b939b, { metalness: 0.7, roughness: 0.35, clippingPlanes: CUT }), shoeMat = mat(0x3a3f45, { clippingPlanes: CUT });
for (let j = 0; j < N_CYL; j++) {
  const a = ((j + 0.5) * 2 * Math.PI) / N_CYL;
  for (const off of [-0.11, 0.11]) {
    const aa = a + off / RC;
    const x = RC * Math.cos(aa), y = RC * Math.sin(aa);
    const body = cyl(0.11, BODY1 - BODY0, cylBodyMat, 12);
    body.position.set(x, y, (BODY0 + BODY1) / 2);
    machine.add(body);
    const rod = new THREE.Mesh(rodGeo, rodMat);
    rod.position.set(x, y, BODY1);
    machine.add(rod);
    const shoe = box(0.24, 0.24, 0.08, shoeMat);
    shoe.position.set(x, y, ZR);
    machine.add(shoe);
    cylinders.push({ a, rod, shoe, z: ZR + W, target: ZR + W });
  }
}
label("Thrust cylinders (push on the last ring)", cylinders[10].shoe, [0, 0.4, -1.2]);

// Erector: rotating ring with an arm and vacuum plate, in front of the build position.
const erector = new THREE.Group();
erector.position.z = ZR - 0.45;
machine.add(erector);
erector.add(new THREE.Mesh(new THREE.TorusGeometry(1.25, 0.12, 8, 40), mat(0xd9a400)));
const erArm = box(0.35, 1.0, 0.35, yellow);
erector.add(erArm);
label("Segment erector", erector, [0, 1.6, 0]);

// Segment feeder at the invert behind the build position.
const feeder = box(1.6, 0.35, 2.4, dark);
feeder.position.set(0, -M.ringID / 2 + 0.55, ZR + W + 2.0);
machine.add(feeder);
label("Segment feeder", feeder, [0, 0.5, 0]);

// Backup: gantries on rails, slurry pumps and lines, grout tanks, control cabin, power pack, ventilation duct.
const RID = M.ringID / 2;
const backup = new THREE.Group();
machine.add(backup);
const railY = -RID + 0.35;
for (const x of [-0.75, 0.75]) {
  const rail = box(0.08, 0.12, 100, steel);
  rail.position.set(x, railY, 60);
  backup.add(rail);
}
const gantryMat = mat(0x4f7f5a, { roughness: 0.6 });
const GANTRY = [
  { z: 14, kit: "Slurry pumps (feed and discharge)" },
  { z: 28, kit: "Grout plant (A and B components)" },
  { z: 42, kit: "Control cabin" },
  { z: 56, kit: "Transformer and hydraulic power pack" },
  { z: 70, kit: "Pipe extension, ventilation fan, cable and hose reels" },
];
for (const g of GANTRY) {
  const grp = new THREE.Group();
  grp.position.z = g.z;
  // open portal frame: posts on wheels, top beams, so the lining stays visible through the gantry
  for (const x of [-1.9, 1.9]) {
    for (const dz of [-5.8, 0, 5.8]) {
      const post = box(0.22, 3.2, 0.22, gantryMat);
      post.position.set(x, railY + 1.75, dz);
      grp.add(post);
    }
    const beam = box(0.22, 0.3, 12.5, gantryMat);
    beam.position.set(x, railY + 3.2, 0);
    grp.add(beam);
  }
  const deck = box(4.0, 0.15, 12.5, gantryMat);
  deck.position.set(0, railY + 3.4, 0);
  grp.add(deck);
  if (g.kit.startsWith("Slurry")) {
    for (const dz of [-2.5, 2.5]) { const pump = cyl(0.6, 1.6, mat(0x2f6f9f), 20); pump.position.set(-1.1, railY + 4.2, dz); grp.add(pump); }
  } else if (g.kit.startsWith("Grout")) {
    for (const x of [-1.2, 1.2]) { const t = cyl(0.55, 4.5, mat(0x9b8f80)); t.position.set(x, railY + 4.05, 0); grp.add(t); }
  } else if (g.kit.startsWith("Control")) {
    const cab = box(1.6, 1.4, 3.0, mat(0xe9e5dc)); cab.position.set(-1.1, railY + 4.2, 0); grp.add(cab);
    const win = box(0.05, 0.5, 2.0, mat(0x9cc7e6, { emissive: 0x24445a })); win.position.set(-0.28, railY + 4.4, 0); grp.add(win);
  } else if (g.kit.startsWith("Transformer")) {
    const tr = box(1.4, 1.2, 2.5, mat(0x6e7a86)); tr.position.set(-1.1, railY + 4.1, -2); grp.add(tr);
    const pp = box(1.2, 1.0, 2.0, mat(0x5b8db8)); pp.position.set(-1.1, railY + 4.0, 2.5); grp.add(pp);
  } else {
    const fan = cyl(0.7, 2.0, mat(0x6e7a86)); fan.position.set(-1.6, 1.7, 2); grp.add(fan);
  }
  backup.add(grp);
  label(g.kit, grp, [-1.1, railY + 5.4, 0]);
}
const duct = cyl(0.55, 70, new THREE.MeshStandardMaterial({ color: 0xe8e4d6, roughness: 1 }), 16);
duct.position.set(-1.6, 1.85, 80 - 35 + 2);
backup.add(duct);
label("Ventilation duct", duct, [0, 0.8, -28]);
// Flow in the slurry lines (visual): dots move along each line at the pipe velocity.
const FLOW_N = 90;
const flowGeo = new THREE.SphereGeometry(0.2, 8, 6); // beads just proud of the pipe wall
const feedDots = new THREE.InstancedMesh(flowGeo, new THREE.MeshBasicMaterial({ color: 0xbfe2ff }), FLOW_N);
const disDots = new THREE.InstancedMesh(flowGeo, new THREE.MeshBasicMaterial({ color: 0xd9b27a }), FLOW_N);
for (const d of [feedDots, disDots]) { d.frustumCulled = false; machine.add(d); }
const flowPhase = { feed: 0, dis: 0 };
const FEED_LEN = FEED_CURVE.getLength(), DIS_LEN = DIS_CURVE.getLength();
// Segment car on the rails
const car = new THREE.Group();
car.position.z = 84;
car.add(box(1.6, 0.4, 6, mat(0x2f6f9f)).translateY(railY + 0.45));
for (let k = 0; k < 3; k++) { const s = box(1.4, 0.3, 1.6, mat(0xb9b9b4)); s.position.set(0, railY + 0.8 + k * 0.32, -1.5); car.add(s); }
backup.add(car);
label("Segment and grout supply train", car, [0, railY + 2.2, 0]);
label("Separation plant at the portal (screens, hydrocyclones, filter press)", car, [0, railY + 3.4, 8]);

// ---------------------------------------------------------------- world: ground, lining, surface
const world = new THREE.Group();
scene.add(world);
for (const z of ZONES) {
  const from = Math.max(z.from, 0), len = z.to - from;
  const b = box(16, 12, len, new THREE.MeshStandardMaterial({ color: z.color, roughness: 1, transparent: true, opacity: 0.4, depthWrite: false,
    clippingPlanes: [new THREE.Plane(new THREE.Vector3(0, 0, -1), 0), CUT[0]] }));
  b.position.set(0, 0, -(from + len / 2));
  world.add(b);
}

// Universal ring, 7 segments + key (key inserted last). Pieces are annular sectors centred on angle 0.
const KEY_DEG = 360 / 22, SEG_DEG = (360 - KEY_DEG) / 7;
const pieceGeo = (deg) => {
  const s = new THREE.Shape(), a = (deg * Math.PI) / 360, gap = 0.003;
  s.absarc(0, 0, M.ringOD / 2, -a + gap, a - gap, false);
  s.absarc(0, 0, M.ringID / 2, a - gap, -a + gap, true);
  s.closePath();
  return new THREE.ExtrudeGeometry(s, { depth: W - 0.01, bevelEnabled: false, curveSegments: 10 });
};
const SEG_GEO = pieceGeo(SEG_DEG), KEY_GEO = pieceGeo(KEY_DEG);
const segMats = [0x8e8e89, 0x7c7c77].map((c) => new THREE.MeshStandardMaterial({ color: c, roughness: 1, side: THREE.DoubleSide, clippingPlanes: CUT }));
const keyMat = new THREE.MeshStandardMaterial({ color: 0xa39c83, roughness: 1, side: THREE.DoubleSide, clippingPlanes: CUT });
const groutGeo = (() => {
  const s = new THREE.Shape();
  s.absarc(0, 0, R, 0, Math.PI * 2, false);
  const h = new THREE.Path();
  h.absarc(0, 0, M.ringOD / 2 + 0.005, 0, Math.PI * 2, true);
  s.holes.push(h);
  return new THREE.ExtrudeGeometry(s, { depth: W, bevelEnabled: false, curveSegments: 48 });
})();
const groutMat = new THREE.MeshStandardMaterial({ color: 0x8a6a45, roughness: 1, transparent: true, opacity: 0.55, clippingPlanes: CUT });
const rings = [];
// Key positions of a universal ring: alternate around the crown so joints stagger ring to ring.
const KEY_POS = [0, 2, -2, 1, -1, 3, -3].map((k) => Math.PI / 2 + (k * 2 * Math.PI) / N_CYL);
function ringPieces(n) {
  const key = KEY_POS[((n % KEY_POS.length) + KEY_POS.length) % KEY_POS.length];
  const kd = (KEY_DEG * Math.PI) / 180, sd = (SEG_DEG * Math.PI) / 180;
  const pieces = [];
  for (let i = 1; i <= 7; i++) pieces.push({ angle: key + kd / 2 + sd * (i - 0.5), key: false, i });
  // build order: from the invert outwards in pairs, key last
  const order = [4, 3, 5, 2, 6, 1, 7].map((i) => pieces[i - 1]);
  order.push({ angle: key, key: true, i: 0 });
  return order;
}
function makePiece(p, n) {
  const m = new THREE.Mesh(p.key ? KEY_GEO : SEG_GEO, p.key ? keyMat : segMats[(((n + p.i) % 2) + 2) % 2]); // n < 0 for launch rings
  m.rotation.z = p.angle;
  return m;
}
function addRing(n, zWorld) {
  const g = new THREE.Group();
  g.position.z = zWorld;
  for (const p of ringPieces(n)) g.add(makePiece(p, n));
  const grout = new THREE.Mesh(groutGeo, groutMat);
  grout.visible = false;
  g.add(grout);
  world.add(g);
  rings.push({ g, grout });
  if (rings.length > 80) world.remove(rings.shift().g);
}

// Surface: settlement-coloured ground and buildings.
const SURF = { x0: -45, x1: 45, c0: -60, c1: 200, nx: 72, nc: 160 };
const surfGeo = new THREE.PlaneGeometry(SURF.x1 - SURF.x0, SURF.c1 - SURF.c0, SURF.nx, SURF.nc).rotateX(-Math.PI / 2);
// after rotation: local x = x, local z = -(plane y); place so local z spans world z = -chainage
surfGeo.translate((SURF.x0 + SURF.x1) / 2, 0, -(SURF.c0 + SURF.c1) / 2);
surfGeo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(surfGeo.attributes.position.count * 3), 3));
const surface = new THREE.Mesh(surfGeo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1 }));
surface.position.y = Z0;
world.add(surface);
const SETTLE_RAMP = [[0, [0.80, 0.78, 0.72]], [0.25, [0.93, 0.80, 0.52]], [0.6, [0.86, 0.52, 0.22]], [1, [0.55, 0.20, 0.10]]];
function ramp(t) {
  t = Math.min(Math.max(t, 0), 1);
  for (let k = 1; k < SETTLE_RAMP.length; k++) {
    const [t1, c1] = SETTLE_RAMP[k], [t0, c0] = SETTLE_RAMP[k - 1];
    if (t <= t1) { const s = (t - t0) / (t1 - t0); return c0.map((v, i) => v + (c1[i] - v) * s); }
  }
  return SETTLE_RAMP.at(-1)[1];
}
const CAT_COLORS = [0x57c38a, 0x9ccc65, 0xf2b43a, 0xff7a45, 0xd84343];
for (const b of BUILDINGS) {
  b.mesh = box(b.w, b.h, b.d, new THREE.MeshStandardMaterial({ color: CAT_COLORS[0], roughness: 0.8 }));
  b.mesh.position.set(b.x, Z0 + b.h / 2, -b.ch);
  world.add(b.mesh);
  b.label = label(b.name, b.mesh, [0, b.h / 2 + 1.5, 0], true);
}
const tunnelLine = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.05, SURF.c1), new THREE.MeshBasicMaterial({ color: 0x5b8db8 }));
tunnelLine.position.set(0, Z0 + 0.05, -SURF.c1 / 2);
world.add(tunnelLine);
const faceMarker = new THREE.Mesh(new THREE.ConeGeometry(0.8, 2.5, 4), new THREE.MeshBasicMaterial({ color: 0xf2b43a }));
faceMarker.rotation.x = Math.PI;
faceMarker.position.set(0, Z0 + 1.6, 0);
scene.add(faceMarker);
label("Face position", faceMarker, [0, 1.8, 0], true);

// ---------------------------------------------------------------- UI
const ids = ["adv", "rpm", "disMode", "target", "dis", "feed", "tau", "vl", "ts", "advOut", "rpmOut", "targetOut", "disOut", "feedOut", "tauOut", "vlOut", "tsOut",
  "pause", "reset", "gauge", "chamber", "alarms", "cycle", "bars", "ground", "showLabels", "shift", "haulage", "interventions", "skip", "forecast", "lining", "cake", "circuit"];
const ui = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));
const val = (id) => +ui[id].value;

// ---------------------------------------------------------------- simulation
let S;
const troughCache = new Map();
function trough(zone, vl) {
  const key = `${zone.name}|${vl}`;
  if (!troughCache.has(key)) troughCache.set(key, presetTrough("closed_face_sand", M.D, Z0, { shieldLengthM: M.shieldLength, volumeLoss: vl / 100, k: zone.k }));
  return troughCache.get(key);
}
function windowFor(zone, pasteWeight) {
  const cover = Z0 - R;
  const fs = wedgeSilo(M.D, cover, zone.gamma, zone.phi, zone.c, { waterDepth: WATER });
  return { fs, w: daubWindow(fs, M.D, cover, zone.gamma, { waterDepth: WATER, supportUnitWeight: pasteWeight }) };
}
function reset() {
  for (const r of rings) world.remove(r.g);
  rings.length = 0;
  for (let n = -8; n < 0; n++) addRing(n, ZR - n * W); // launch section behind the build position, already grouted
  for (const r of rings) r.grout.visible = true;
  S = {
    chainage: 0, stroke: 0, mode: "PUSH", ring: 0, pieces: null, piece: 0, pieceT: 0, simTime: 0, paused: false,
    cs: { p_air: val("target") - M.slurryWeight * LEVEL_SP, level: LEVEL_SP, air_volume: AIR0 }, cutRpm: val("rpm"),
    qFeed: 0, qDis: 0, qExc: 0, v: 0, overbreak: 0, trip: "",
    pushTime: 0, lastPush: null, lastBuild: null, grout: 0, excavated: 0, torque: 0, thrust: null, tq: null, stalled: false,
    // downtime (utilisation model): activities after each ring, maintenance shifts, tool interventions
    rng: new Rng(1), actLeft: 0, actText: "", stopLeft: 0, stops: 0, boringTime: 0,
  };
  S.nextStop = sampleDist(DIST.rings_between_stops, S.rng.uniform());
  for (const c of cylinders) c.z = c.target = ZR;
  world.position.z = 0;
  pieceMesh && machine.remove(pieceMesh);
  pieceMesh = null;
  buildGroup.clear();
}
let pieceMesh = null;
// pieces already placed in the ring being built (TBM frame, at the build position)
const buildGroup = new THREE.Group();
buildGroup.position.z = ZR;
machine.add(buildGroup);

const axisPressure = () => facePressure(S.cs.p_air, S.cs.level, 0, M.slurryWeight);
// Filter cake or penetration at the face for the current excess pressure over the pore pressure (DAUB 2016 section 8.1,
// e_max: the steady, conservative penetration).
function cakeAt(zone, p) {
  const { fs } = windowFor(zone, M.slurryWeight);
  const inf = slurryInfiltration(Math.max(p - fs.u_axis, 0), val("tau") / 1000, zone.d10, fs.wedge_length);
  return { fs, inf, sEff: Math.max(p - fs.u_axis, 0) * inf.transfer };
}

const pattern = () => SHIFT_PATTERNS[ui.shift.value];
const inProduction = () => S.simTime % 86400 < pattern().production_h * 3600;

// After a ring is built: general tunnelling activities, train delay (rail haulage) and per-cycle maintenance.
function startActivities() {
  const parts = [];
  let min = sampleDist(DIST.general, S.rng.uniform());
  parts.push(`general activities ${Math.round(min)} min`);
  if (ui.haulage.value === "rail") { const d = sampleDist(DIST.train_delay, S.rng.uniform()); min += d; parts.push(`train delay ${Math.round(d)} min`); }
  if (pattern().per_cycle_maintenance) { min += PER_CYCLE_MAINTENANCE_MIN; parts.push(`maintenance ${PER_CYCLE_MAINTENANCE_MIN} min`); }
  S.mode = "ACTIVITIES";
  S.actLeft = min * 60;
  S.actText = parts.join(", ");
}

// Slurry circuit and air cushion. While excavating, fresh slurry is fed and the discharge pump holds the working-chamber
// level (or runs at the manual flow); between pushes the circuit runs in bypass, so no flow passes the chamber. Pump
// interlocks trip the feed on a high level and the discharge on a low level.
function circulate(dt, qExc) {
  const excavating = qExc > 0;
  let qFeed = excavating ? val("feed") / 3600 : 0;
  let qDis = 0;
  if (excavating) {
    qDis = ui.disMode.value === "auto" ? Math.max(qFeed + qExc + (S.cs.level - LEVEL_SP) * CUSHION.chamberArea / 20, 0) : val("dis") / 3600;
  }
  S.trip = "";
  if (S.cs.level > R - 0.5 && qFeed + qExc > qDis) { qFeed = 0; S.trip = "Feed pump tripped: working-chamber level high"; }
  if (S.cs.level < -R + 1.1 && qDis > qFeed + qExc) { qDis = 0; S.trip = "Discharge pump tripped: working-chamber level low"; }
  S.qFeed = qFeed; S.qDis = qDis; S.qExc = qExc;
  S.cs = CUSHION.step(S.cs, dt, qFeed, qExc, qDis, val("target") - M.slurryWeight * LEVEL_SP);
}

function substep(dt) {
  // Tool interventions run round the clock; everything else only in production hours.
  if (S.mode === "INTERVENTION") {
    S.cutRpm = S.v = 0; S.tq = S.thrust = null; S.torque = 0; circulate(dt, 0);
    const d = Math.min(dt, S.stopLeft);
    S.stopLeft -= d; S.simTime += d;
    if (S.stopLeft <= 1e-6) S.mode = "PUSH";
    return;
  }
  if (!inProduction()) {
    S.cutRpm = S.v = 0; S.tq = S.thrust = null; S.torque = 0; circulate(dt, 0);
    S.simTime += dt;
    return;
  }
  if (S.mode === "ACTIVITIES") {
    S.cutRpm = S.v = 0; S.tq = S.thrust = null; S.torque = 0; circulate(dt, 0);
    const d = Math.min(dt, S.actLeft);
    S.actLeft -= d; S.simTime += d;
    if (S.actLeft <= 1e-6) {
      if (ui.interventions.checked && S.ring >= S.nextStop) {
        S.mode = "INTERVENTION";
        S.stopLeft = sampleDist(DIST.stop_hours, S.rng.uniform()) * 3600;
        S.stops++;
        S.nextStop = S.ring + sampleDist(DIST.rings_between_stops, S.rng.uniform());
      } else S.mode = "PUSH";
    }
    return;
  }
  const zone = zoneAt(S.chainage);
  const p = axisPressure();
  S.cutRpm = S.mode === "PUSH" ? val("rpm") : 0;
  const sv = verticalStress(Z0, zone.gamma, { waterDepth: WATER });
  // torque at the current pressure: the slurry lubricates the face and the back of the head, so those friction
  // coefficients are lower than for the EPB paste (assumed); the rim uses the effective value fitted on open EPB data.
  // Above the installed limit the head stalls
  S.tq = S.cutRpm > 0 ? cutterheadTorque(M.D, p, (sv * (1 + zone.k0)) / 2, {
    openingRatio: drawnOpening, mu: 0.05, muChamber: 0.02, nArms: 4, armArea: 0.5, armRadius: 2.3, tools: toolTorque(M.nTools, M.toolForce, R), seals: 300,
  }) : null;
  S.torque = S.tq ? S.tq.total : 0;
  S.stalled = S.torque > M.torqueLimit;
  const v = S.mode === "PUSH" && S.cutRpm > 0 && !S.stalled ? val("adv") / 60000 : 0; // m/s
  S.v = v;
  // Over-excavation (illustrative): when the transferred support falls short of the required effective support, the
  // face loosens and more soil enters than the theoretical volume; the dry-mass balance in the circuit detects it.
  const { fs, sEff } = cakeAt(zone, p);
  S.overbreak = v > 0 && fs.s_eff > 0 && sEff < fs.s_eff ? Math.min(0.3 * (1 - sEff / fs.s_eff), 0.3) : 0;
  circulate(dt, AREA * v * (1 + S.overbreak));
  S.thrust = v > 0 ? shieldThrust(M.D, M.shieldLength, Z0, zone.gamma, p, {
    waterDepth: WATER, k0: zone.k0, shieldWeight: M.shieldWeight, tools: 1000, tailSeal: M.tailSeal, backupWeight: M.backupWeight,
  }) : null;
  S.simTime += dt;
  if (S.mode === "PUSH") {
    const adv = Math.min(v * dt, W - S.stroke);
    S.stroke += adv;
    S.chainage += adv;
    S.pushTime += dt;
    if (v > 0) S.boringTime += dt;
    S.excavated += AREA * adv;
    S.grout += Math.PI * (R * R - (M.ringOD / 2) ** 2) * adv; // theoretical annulus, filled during the shove
    if (S.stroke >= W - 1e-9) {
      S.lastPush = S.pushTime;
      S.mode = "BUILD";
      S.pieces = ringPieces(S.ring);
      S.piece = 0;
      S.pieceT = 0;
      S.buildTime = 0;
    }
  } else {
    S.pieceT += dt;
    S.buildTime += dt;
    const per = (M.buildMin * 60) / 8;
    if (S.pieceT >= per) {
      S.pieceT -= per;
      const done = S.pieces[S.piece];
      if (done) buildGroup.add(makePiece(done, S.ring));
      S.piece++;
      if (S.piece >= 8) {
        buildGroup.clear();
        addRing(S.ring, ZR - S.chainage);
        S.ring++;
        S.stroke = 0;
        S.pushTime = 0;
        S.lastBuild = S.buildTime;
        startActivities();
      }
    }
  }
}

function step(dtReal) {
  if (S.paused) return;
  let dt = dtReal * val("ts");
  while (dt > 1e-9) {
    const h = Math.min(dt, 0.5);
    substep(h);
    dt -= h;
  }
}

// ---------------------------------------------------------------- animation of the machine state
const tmp = new THREE.Vector3();
function animate(dtReal) {
  world.position.z = S.chainage;
  cutterhead.rotation.z -= (S.cutRpm / 60) * 2 * Math.PI * dtReal;
  // grout becomes visible once a ring has left the tail
  for (const r of rings) r.grout.visible = r.g.position.z + world.position.z > M.shieldLength - 0.2;
  // cylinders: on the last ring while pushing; per sector retract-place-extend while building
  for (const c of cylinders) {
    if (S.mode === "PUSH") c.target = ZR + S.stroke;
    else {
      const placed = S.pieces.slice(0, S.piece);
      const cur = S.pieces[S.piece];
      const inSector = (p) => Math.abs(Math.atan2(Math.sin(c.a - p.angle), Math.cos(c.a - p.angle))) < ((p.key ? KEY_DEG : SEG_DEG) * Math.PI) / 360 + 0.05;
      if (cur && inSector(cur) && S.pieceT / ((M.buildMin * 60) / 8) < 0.9) c.target = ZR - 0.1;
      else if (placed.some(inSector)) c.target = ZR;
      else c.target = ZR + W;
    }
    c.z += Math.sign(c.target - c.z) * Math.min(Math.abs(c.target - c.z), 0.6 * dtReal * Math.max(1, val("ts") / 30));
    c.rod.scale.z = Math.max(c.z - BODY1, 0.01);
    c.shoe.position.z = c.z - 0.04;
  }
  // segment in the erector
  if (S.mode === "BUILD" && S.pieces[S.piece]) {
    const p = S.pieces[S.piece];
    if (!pieceMesh || pieceMesh.userData.id !== `${S.ring}-${S.piece}`) {
      if (pieceMesh) machine.remove(pieceMesh);
      pieceMesh = makePiece(p, S.ring);
      pieceMesh.material = pieceMesh.material.clone();
      pieceMesh.material.clippingPlanes = [];
      pieceMesh.userData.id = `${S.ring}-${S.piece}`;
      machine.add(pieceMesh);
    }
    const f = Math.min(S.pieceT / ((M.buildMin * 60) / 8), 1);
    const pick = Math.min(f / 0.3, 1), rot = Math.min(Math.max((f - 0.3) / 0.35, 0), 1), ext = Math.min(Math.max((f - 0.65) / 0.3, 0), 1);
    const ease = (t) => t * t * (3 - 2 * t);
    const ang = -Math.PI / 2 + (Math.atan2(Math.sin(p.angle + Math.PI / 2), Math.cos(p.angle + Math.PI / 2))) * ease(rot);
    const dr = 1.9 * (1 - ease(ext));
    pieceMesh.rotation.z = ang;
    pieceMesh.position.set(-dr * Math.cos(ang), -dr * Math.sin(ang), ZR + (1 - ease(pick)) * 2.4);
    erector.rotation.z = ang + Math.PI / 2;
    erArm.position.set(0, -(M.ringID / 2 - 0.4 - dr) / 2 - 0.9, 0);
    erArm.scale.y = Math.max(0.4, (M.ringID / 2 - 1.3 - dr) / 1.0);
  } else if (pieceMesh) {
    machine.remove(pieceMesh);
    pieceMesh = null;
  }
  // flow in the slurry lines at the pipe velocity (real time, not scaled)
  const m4 = new THREE.Matrix4();
  for (const [dots, curveK, len, q, key] of [[feedDots, FEED_CURVE, FEED_LEN, S.qFeed, "feed"], [disDots, DIS_CURVE, DIS_LEN, S.qDis, "dis"]]) {
    dots.count = q > 0 ? FLOW_N : 0;
    if (!q) continue;
    flowPhase[key] = (flowPhase[key] + (pipeVelocity(q, M.pipe) * dtReal) / len) % 1;
    for (let k = 0; k < FLOW_N; k++) {
      curveK.getPointAt((k / FLOW_N + flowPhase[key]) % 1, tmp);
      m4.makeTranslation(tmp.x, tmp.y, tmp.z);
      dots.setMatrixAt(k, m4);
    }
    dots.instanceMatrix.needsUpdate = true;
  }
  drawWorkingChamber(S.cs.level);
  faceMarker.position.z = 0;
}

// Fraction of the final trough at chainage ch for a tunnel driven from the launch shaft (chainage 0) to the face at c:
// each volume-loss component k (weight w_k, y_k behind the face) acts on the drive from 0 to c - y_k, so
// f = sum_k w_k [Phi((c - y_k - ch) / i_l) - Phi(-ch / i_l)] (Attewell & Woodman's profile, truncated at the shaft).
const Phi = (z) => 0.5 * (1 + erf(z / Math.SQRT2));
function tunnelFraction(t, c, ch) {
  const il = t.i_long ?? t.i;
  let f = 0;
  for (const [w, yk] of t.components) if (c - yk > 0) f += w * (Phi((c - yk - ch) / il) - Phi(-ch / il));
  return Math.max(f, 0);
}

// Surface settlement and building categories.
let surfaceMax = 0;
function updateSurface() {
  const vl = val("vl"), c = S.chainage;
  const pos = surfGeo.attributes.position, col = surfGeo.attributes.color;
  let smax = 0;
  const settle = (x, ch) => {
    const t = trough(zoneAt(ch), vl);
    return t.settlement(x) * tunnelFraction(t, c, ch);
  };
  for (let k = 0; k < pos.count; k++) {
    const x = pos.getX(k), ch = -pos.getZ(k);
    const s = settle(x, ch);
    smax = Math.max(smax, s);
    pos.setY(k, -s * 150); // vertical exaggeration x150 so the trough is visible
    const [r, g, b] = ramp(s / 0.02);
    col.setXYZ(k, r, g, b);
  }
  pos.needsUpdate = col.needsUpdate = true;
  surfGeo.computeVertexNormals();
  surfaceMax = smax;
  for (const b of BUILDINGS) {
    // greenfield horizontal strain under the footprint at the building's chainage: u = -(x/z0) S, eps = du/dx
    let emax = 0;
    for (let x = b.x - b.w / 2; x <= b.x + b.w / 2; x += 0.25) {
      const e = -(settle(x + 0.05, b.ch) * (x + 0.05) - settle(x - 0.05, b.ch) * (x - 0.05)) / (Z0 * 0.1);
      emax = Math.max(emax, e);
    }
    b.strain = emax * 100;
    b.settle = settle(b.x, b.ch);
    const [cat, name] = burlandCategory(b.strain);
    b.cat = cat;
    b.catName = name;
    b.mesh.material.color.setHex(CAT_COLORS[cat]);
    b.mesh.position.y = Z0 + b.h / 2 - b.settle * 150;
    b.label.el.textContent = `${b.name}: cat. ${cat} ${name}`;
  }
}

// ---------------------------------------------------------------- HUD
const fmt = (v, d = 1) => v.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const hms = (s) => `${Math.floor(s / 3600)} h ${String(Math.floor((s % 3600) / 60)).padStart(2, "0")} min`;
const dl = (el, rows) => { el.innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join(""); };
const REF = referenceInstalled("epb", M.D); // no open thrust figure for a slurry machine: the EPB reference is shown

function gaugeSvg(levels, target) {
  const H = 150, top = 8, bot = 22, pmax = 4.5;
  const y = (bar) => top + (H - top - bot) * (1 - Math.min(bar, pmax) / pmax);
  const colW = 70, x0 = 34;
  let s = `<svg viewBox="0 0 280 ${H}" role="img" aria-label="Chamber pressure against the DAUB window">`;
  for (let b = 0; b <= 4; b++) s += `<line x1="${x0 - 4}" x2="272" y1="${y(b)}" y2="${y(b)}" stroke="#2c3138"/><text x="2" y="${y(b) + 3}">${b} bar</text>`;
  levels.forEach((l, i) => {
    const x = x0 + 10 + i * (colW + 14);
    s += `<rect x="${x}" y="${y(l.max)}" width="${colW}" height="${Math.max(y(l.min) - y(l.max), 1)}" fill="rgba(87,195,138,0.18)" stroke="rgba(87,195,138,0.6)"/>`;
    const c = l.p < l.min ? "#f2b43a" : l.p > l.max ? "#ff7a45" : "#e7e9ec";
    s += `<line x1="${x - 4}" x2="${x + colW + 4}" y1="${y(l.p)}" y2="${y(l.p)}" stroke="${c}" stroke-width="3"/>`;
    if (l.name === "Axis") s += `<line x1="${x}" x2="${x + colW}" y1="${y(target)}" y2="${y(target)}" stroke="#f2b43a" stroke-dasharray="4 3"/>`;
    s += `<text x="${x + colW / 2}" y="${H - 6}" text-anchor="middle">${l.name} ${fmt(l.p, 2)}</text>`;
  });
  return s + `</svg>`;
}

function bars(parts, total, limit, unit) {
  const colors = ["#3987e5", "#d95926", "#199e70", "#b07ad9", "#c9a227", "#7f8c99"];
  const scale = Math.max(limit, total) || 1;
  const segs = parts.map(([, v], i) => `<i style="width:${(100 * v) / scale}%;background:${colors[i]}"></i>`).join("");
  const legend = parts.map(([k, v], i) => `<span style="--c:${colors[i]}">${k} ${fmt(v / 1000, 1)}</span>`).join("");
  return `<div class="bar"><span class="k">Total ${unit}</span><span class="t">${segs}</span><span class="v">${fmt(total / 1000, 1)}</span></div><div class="legend">${legend}</div>`;
}

// Segment lining (ITA WG2 2000 elastic equation method, Wood's joint reduction, ITA / DAUB jacking, bursting and
// grout checks). Ground stiffness E_s per zone, concrete E 36 GPa and a 0.2 m shoe pad are assumed.
const SEG = { n: 8, E: 36e6, pad: 0.2, gammaC: 25 };
const SEG_T = (M.ringOD - M.ringID) / 2, SEG_RC = (M.ringOD + M.ringID) / 4;
const liningCache = new Map();
function liningAt(zone) {
  if (!liningCache.has(zone.name)) {
    const [pv, q1, q2] = ringLoads(Z0, M.ringOD / 2, zone.gamma, zone.k0, WATER);
    const eta = woodInertia(1, SEG.n);
    const r = jsceRing(pv, q1, q2, SEG.gammaC * SEG_T, SEG_RC, (SEG.E * SEG_T ** 3) / 12, subgradeModulus(zone.Es, SEG_RC), { eta });
    const iMax = r.moment.indexOf(Math.max(...r.moment)), iMin = r.moment.indexOf(Math.min(...r.moment));
    const sMax = sectionStresses(r.normal[iMax], r.moment[iMax], SEG_T), sMin = sectionStresses(r.normal[iMin], r.moment[iMin], SEG_T);
    liningCache.set(zone.name, { pv, q1, q2, eta, r, iMax, iMin, sigma: Math.max(sMax[0], sMin[0]), sigmaMin: Math.min(sMax[1], sMin[1]),
      oval: (2 * r.deflection) / M.ringID, grout: groutWindow(Z0 - R, zone.gamma, WATER) });
  }
  return liningCache.get(zone.name);
}
function liningRows(zone) {
  const L = liningAt(zone), r = L.r;
  const shoe = S.thrust ? S.thrust.total / N_CYL : null;
  const js = shoe ? jackingStress(shoe, N_CYL, SEG_RC, SEG_T) : null;
  const [tb] = shoe ? burstingForce(shoe, SEG_T, SEG.pad) : [null];
  const rows = [
    ["Ring", `7 + key, ${fmt(SEG_T * 1000, 0)} mm, ${W} m wide; joints cut bending stiffness to ${fmt(L.eta * 100, 0)} % (Wood)`],
    ["Loads at crown / springline", `${fmt(L.pv, 0)} kPa vertical; ${fmt(L.q1, 0)}–${fmt(L.q2, 0)} kPa lateral (earth + water, full overburden)`],
    ["Bending moment", `+${fmt(r.moment[L.iMax], 0)} kNm/m at ${r.angles_deg[L.iMax]}°, ${fmt(r.moment[L.iMin], 0)} kNm/m at ${r.angles_deg[L.iMin]}° from the crown`],
    ["Normal force", `${fmt(Math.min(...r.normal), 0)}–${fmt(Math.max(...r.normal), 0)} kN/m`],
    ["Concrete stress", `${fmt(L.sigma / 1000, 1)} MPa max, ${fmt(L.sigmaMin / 1000, 1)} MPa min${L.sigmaMin < 0 ? ", tension carried by the reinforcement" : ""} (ITA 2000 allowable ${fmt(ITA2000_ALLOWABLE.concrete_42 / 1000, 0)} MPa for C42)`],
    ["Ovalisation", `${fmt(L.oval * 100, 2)} % of the inner diameter (limit 0.5 %, DAUB)`],
    ["Jacking stress per shoe", js ? `${fmt(shoe / 1000, 2)} MN on ${N_CYL} shoes: ${fmt(js / 1000, 1)} MPa (allowable ${fmt((ITA2000_ALLOWABLE.concrete_42 * ITA2000_ALLOWABLE.jacking_factor) / 1000, 1)} MPa while jacking)` : "no thrust on the ring"],
    ["Bursting force per shoe", tb ? `${fmt(tb, 0)} kN (DAUB, 0.2 m pad)` : "—"],
    ["Annulus grout", `${fmt(annulusVolume(M.D, M.ringOD, W), 2)} m³ per ring; pressure at the crown ${fmt(L.grout[0] / 100, 2)}–${fmt(L.grout[1] / 100, 2)} bar (above groundwater, at most 69 kPa over it)`],
  ];
  const alarms = [];
  if (js && js > ITA2000_ALLOWABLE.concrete_42 * ITA2000_ALLOWABLE.jacking_factor) alarms.push(`Jacking stress ${fmt(js / 1000, 1)} MPa above the allowable for the temporary jacking state`);
  if (L.oval > 0.005) alarms.push(`Ring ovalisation ${fmt(L.oval * 100, 2)} % above 0.5 % of the inner diameter`);
  return { rows, alarms };
}

function hud() {
  for (const [id, out, f] of [["adv", "advOut", (v) => `${v} mm/min`], ["rpm", "rpmOut", (v) => `${fmt(v, 1)} rpm`], ["target", "targetOut", (v) => `${fmt(v / 100, 2)} bar`],
    ["dis", "disOut", (v) => `${v} m³/h`], ["feed", "feedOut", (v) => `${v} m³/h`], ["tau", "tauOut", (v) => `${v} Pa`], ["vl", "vlOut", (v) => `${fmt(v, 2)} %`], ["ts", "tsOut", (v) => `×${v}`]]) {
    ui[out].textContent = f(val(id));
  }
  const auto = ui.disMode.value === "auto";
  ui.dis.closest("label").classList.toggle("dim", auto);

  const zone = zoneAt(S.chainage), gs = M.slurryWeight;
  const { w } = windowFor(zone, gs);
  const p = axisPressure(), cs = S.cs;
  const pCrown = facePressure(cs.p_air, cs.level, R, gs), pInv = facePressure(cs.p_air, cs.level, -R, gs);
  ui.gauge.innerHTML = gaugeSvg([
    { name: "Crown", p: pCrown / 100, min: w.p_min_crown / 100, max: w.p_max_crown / 100 },
    { name: "Axis", p: p / 100, min: w.p_min_axis / 100, max: w.p_max_axis / 100 },
    { name: "Invert", p: pInv / 100, min: (w.p_min_axis + gs * R) / 100, max: (w.p_max_axis + gs * R) / 100 },
  ], val("target") / 100);
  const dev = p - val("target");
  dl(ui.chamber, [
    ["DAUB window at axis", `${fmt(w.p_min_axis / 100, 2)} – ${fmt(w.p_max_axis / 100, 2)} bar`],
    ["Air-cushion pressure", `${fmt(cs.p_air / 100, 3)} bar`],
    ["Working-chamber level", `${fmt(cs.level, 2)} m above the axis (set ${fmt(LEVEL_SP, 1)} m)`],
    ["Air volume", `${fmt(cs.air_volume, 1)} m³`],
    ["Deviation from target", `${dev >= 0 ? "+" : ""}${fmt(dev, 1)} kPa (tolerance ±${CONTROL_TOLERANCE.slurry} kPa; EPB ±${CONTROL_TOLERANCE.epb})`],
    ["Feed / excavated / discharge", `${fmt(S.qFeed * 3600, 0)} / ${fmt(S.qExc * 3600, 0)} / ${fmt(S.qDis * 3600, 0)} m³/h`],
    ["Circuit", S.qExc > 0 ? "through the chamber" : "bypass (no flow through the chamber)"],
  ]);

  // filter cake at the face
  const { fs, inf, sEff } = cakeAt(zone, p);
  dl(ui.cake, [
    ["Ground d₁₀", `${fmt(zone.d10 * 1000, 2)} mm`],
    ["Excess pressure over pore water", `${fmt(Math.max(p - fs.u_axis, 0), 0)} kPa`],
    ["Stagnation gradient f_s0", `${fmt(inf.f_s0, 0)} kN/m³ (membrane at ≥ 200)`],
    ["At the face", inf.membrane ? "filter cake (membrane)" : `penetration up to ${fmt(inf.e_max, 2)} m`],
    ["Sliding wedge length", `${fmt(fs.wedge_length, 2)} m`],
    ["Support transferred", `${fmt(inf.transfer * 100, 0)} %`],
    ["Effective support at axis", `${fmt(sEff, 0)} kPa (required ${fmt(Math.max(fs.s_eff, 0), 0)} kPa)`],
  ]);

  // slurry circuit: discharge density, dry-mass balance and pipe velocities
  const vFeed = pipeVelocity(S.qFeed, M.pipe), vDis = pipeVelocity(S.qDis, M.pipe);
  let circ = [["Pipe velocity feed / discharge", `${fmt(vFeed, 2)} / ${fmt(vDis, 2)} m/s (deposit limit ${fmt(DEPOSIT_LIMIT, 2)} m/s)`]];
  let dryRatio = 1;
  if (S.qExc > 0) {
    const [qd, rhoD] = dischargeDensity(S.qFeed, M.feedDensity, AREA, S.qExc / AREA, zone.rho);
    const dry = drySolidsFlow(S.qFeed, M.feedDensity, qd, rhoD), theo = theoreticalDryFlow(AREA, S.v, zone.rho);
    dryRatio = dry / theo;
    circ = [
      ["Discharge density", `${fmt(rhoD, 3)} t/m³ (feed ${fmt(M.feedDensity, 2)})`],
      ["Dry solids, measured", `${fmt(dry * 3600, 1)} m³/h`],
      ["Dry solids, theoretical", `${fmt(theo * 3600, 1)} m³/h (${fmt(dryRatio * 100, 0)} %)`],
      ...circ,
      ["Separation plant load", `${fmt(dry * 3600 * 2.65, 0)} t/h of soil to screens, hydrocyclones and filter press`],
    ];
  }
  dl(ui.circuit, circ);

  const alarms = [];
  if (p < w.p_min_axis) alarms.push(`Axis pressure ${fmt(p / 100, 2)} bar below the DAUB minimum ${fmt(w.p_min_axis / 100, 2)} bar`);
  if (pCrown > w.p_max_crown) alarms.push(`Crown pressure above the blow-out limit ${fmt(w.p_max_crown / 100, 2)} bar`);
  if (Math.abs(dev) > CONTROL_TOLERANCE.slurry) alarms.push(`Support pressure ${fmt(dev, 0)} kPa from target: outside ±${CONTROL_TOLERANCE.slurry} kPa`);
  if (S.trip) alarms.push(S.trip);
  else if (cs.level > LEVEL_SP + 1.0) alarms.push("Working-chamber level high: air cushion shrinking");
  else if (cs.level < -R + 1.5) alarms.push("Working-chamber level low: air may pass under the submerged wall to the face");
  if (!inf.membrane && inf.transfer < 0.9) alarms.push(`Slurry penetrates ${fmt(inf.e_max, 2)} m: only ${fmt(inf.transfer * 100, 0)} % of the support reaches the wedge; raise the yield point`);
  if (fs.s_eff > 0 && sEff < fs.s_eff) alarms.push("Transferred support below the required effective support: face loosening");
  if (S.qDis > 0 && vDis < DEPOSIT_LIMIT) alarms.push(`Discharge velocity ${fmt(vDis, 2)} m/s below the deposit limit: solids settle in the line`);
  if (S.qFeed > 0 && vFeed < DEPOSIT_LIMIT) alarms.push(`Feed velocity ${fmt(vFeed, 2)} m/s below the deposit limit`);
  if (dryRatio > 1.05) alarms.push(`Dry solids ${fmt(dryRatio * 100, 0)} % of theoretical: over-excavation`);
  if (S.stalled) alarms.push(`Torque ${fmt(S.torque, 0)} kNm above the installed ${M.torqueLimit} kNm: cutterhead stalled`);
  if (S.mode === "INTERVENTION") alarms.push("Cutting-tool intervention: slurry level lowered, face held by the air cushion and the filter cake");
  for (const b of BUILDINGS) if (b.cat >= 2) alarms.push(`${b.name}: Burland category ${b.cat} (${b.catName})`);
  const lin = liningRows(zoneAt(S.chainage));
  dl(ui.lining, lin.rows);
  alarms.push(...lin.alarms);
  ui.alarms.innerHTML = alarms.length ? alarms.map((a) => `<div>${a}</div>`).join("") : `<div class="ok">Within limits</div>`;

  const v = val("adv") / 60000;
  const pushMin = v > 0 ? W / v / 60 : Infinity;
  const cycleDay = Number.isFinite(pushMin) ? (W * 24 * 60) / (pushMin + M.buildMin) : 0;
  const tod = S.simTime % 86400;
  const clock = `Day ${Math.floor(S.simTime / 86400) + 1}, ${String(Math.floor(tod / 3600)).padStart(2, "0")}:${String(Math.floor((tod % 3600) / 60)).padStart(2, "0")}`;
  const modeText = S.mode === "INTERVENTION" ? `TOOL INTERVENTION (hyperbaric), ${fmt(S.stopLeft / 3600, 1)} h left`
    : !inProduction() ? `MAINTENANCE SHIFT (production resumes at 00:00)`
      : S.mode === "ACTIVITIES" ? `BETWEEN RINGS: ${S.actText} (${fmt(S.actLeft / 60, 0)} min left)`
        : S.mode === "PUSH" ? (S.stalled ? "PUSH (stalled)" : "PUSH (excavating one ring width)")
          : `RING BUILD (piece ${Math.min(S.piece + 1, 8)} of 8${S.pieces?.[S.piece]?.key ? ", key" : ""})`;
  ui.skip.disabled = !(S.mode === "INTERVENTION" || !inProduction() || S.mode === "ACTIVITIES");
  const days = S.simTime / 86400;
  dl(ui.cycle, [
    ["Mode", modeText],
    ["Clock", clock],
    ["Chainage", `${fmt(S.chainage, 2)} m`],
    ["Rings built", S.ring],
    ["Stroke", `${fmt(S.stroke * 1000, 0)} / ${W * 1000} mm`],
    ["Push time per ring", Number.isFinite(pushMin) ? `${fmt(pushMin, 0)} min` : "—"],
    ["Ring build time", `${M.buildMin} min (7 + key)`],
    ["Cycle-only advance", `${fmt(cycleDay, 1)} m/day (no downtime)`],
    ["Achieved so far", days > 0.05 ? `${fmt(S.chainage / days, 1)} m/day · utilisation ${fmt((S.boringTime / S.simTime) * 100, 0)} %` : "—"],
    ["Next tool intervention", ui.interventions.checked ? `after ring ${Math.ceil(S.nextStop)}` : "off"],
    ["Excavated", `${fmt(S.excavated, 0)} m³ in situ`],
    ["Annulus grout", `${fmt(S.grout, 1)} m³ (${fmt(Math.PI * (R * R - (M.ringOD / 2) ** 2), 2)} m³/m)`],
    ["Simulated time", hms(S.simTime)],
  ]);

  const parts = [];
  let html = "";
  if (S.thrust) {
    const t = S.thrust;
    html += bars([["face", t.face], ["shield", t.shield], ["tools", t.tools], ["tail seal", t.tail_seal], ["backup", t.backup]], t.total, REF.thrust[0], "thrust MN");
  } else html += `<div class="bar"><span class="k">Thrust</span><span class="t"></span><span class="v">holding</span></div>`;
  if (S.tq) {
    const q = S.tq;
    html += bars([["tools", q.tools], ["face", q.face], ["rim", q.rim], ["back", q.back], ["arms", q.arms], ["seals", q.seals]], q.total, M.torqueLimit, "torque MNm");
  } else html += `<div class="bar"><span class="k">Torque</span><span class="t"></span><span class="v">stopped</span></div>`;
  html += `<p class="legend">Installed torque ${fmt(M.torqueLimit / 1000, 1)} MNm. Reference thrust ≈ ${fmt(REF.thrust[0] / 1000, 0)} MN (6.6 m mixed-face EPB scaled; no open slurry figure). Drawn opening ratio ${fmt(drawnOpening * 100, 0)} %.</p>`;
  ui.bars.innerHTML = html;
  scheduleForecast();
  ui.forecast.innerHTML = forecastHtml();
  void parts;

  const t = trough(zone, val("vl"));
  dl(ui.ground, [
    ["Ground at the face", zone.name],
    ["φ′, c′", `${zone.phi}°, ${zone.c} kPa`],
    ["Axis depth, water table", `${Z0} m, ${WATER} m`],
    ["Required effective support", fs.s_eff > 0 ? `${fmt(fs.s_eff / 100, 2)} bar` : "none (self-supporting)"],
    ["Pore pressure at axis", `${fmt(fs.u_axis / 100, 2)} bar`],
    ["Final Smax (this zone)", `${fmt(t.s_max * 1000, 1)} mm`],
    ["Surface settlement now", `${fmt(surfaceMax * 1000, 1)} mm max`],
    ...BUILDINGS.map((b) => [b.name, `${fmt((b.settle ?? 0) * 1000, 1)} mm, ε ${fmt(b.strain ?? 0, 3)} %, cat. ${b.cat ?? 0}`]),
    ["Surface heights", "exaggerated ×150"],
  ]);
}

ui.skip.onclick = () => {
  // jump over the current stoppage (the circuit is in bypass while stopped, so nothing else changes)
  if (S.mode === "INTERVENTION") { S.simTime += S.stopLeft; S.stopLeft = 0; S.mode = "PUSH"; }
  else if (!inProduction()) S.simTime = Math.ceil(S.simTime / 86400) * 86400;
  else if (S.mode === "ACTIVITIES") { S.simTime += S.actLeft; S.actLeft = 0.001; }
};

// Forecast: 20 runs of 90 days at the current settings (ring build 35 min as in the class preset).
let forecastKey = "", forecastTimer = null, FC = null;
function forecastInputs() {
  const v = val("adv") / 60000;
  return { adv: val("adv"), shift: ui.shift.value, haulage: ui.haulage.value, iv: ui.interventions.checked, boring: v > 0 ? W / v / 60 : null };
}
function runForecast() {
  const f = forecastInputs();
  if (!f.boring) { FC = null; return; }
  const runs = [];
  for (let seed = 1; seed <= 20; seed++) {
    runs.push(simulateDrive({ ring_length: W, boring_min: f.boring, ring_build: { kind: "fixed", value: M.buildMin }, shift_pattern: f.shift,
      haulage: f.haulage, interventions: f.iv }, 90, seed));
  }
  const mean = (k) => runs.reduce((a, r) => a + r[k], 0) / runs.length;
  const med = (k) => { const xs = runs.map((r) => r[k]).sort((a, b) => a - b); return (xs[9] + xs[10]) / 2; };
  const shares = {};
  for (const r of runs) for (const [k, v] of Object.entries(r.shares)) shares[k] = (shares[k] ?? 0) + v / runs.length;
  FC = { util: mean("utilisation"), day: mean("mean_m_per_day"), week: mean("mean_m_per_week"), bestDay: med("best_day"), bestWeek: med("best_week"),
    bestMonth: med("best_month"), stops: mean("interventions"), shares };
  FC.check = recordCheck(M.D, FC.bestDay, FC.bestWeek, FC.bestMonth, "slurry");
}
function scheduleForecast() {
  const key = JSON.stringify(forecastInputs());
  if (key === forecastKey) return;
  forecastKey = key;
  clearTimeout(forecastTimer);
  forecastTimer = setTimeout(runForecast, 250);
}
const SHARE_COLORS = { boring: "#3987e5", ring_build: "#d95926", general: "#199e70", train_delay: "#b07ad9", maintenance_per_cycle: "#c9a227", intervention: "#ff7a45", maintenance_shift_and_idle: "#4b5560" };
const SHARE_NAMES = { boring: "boring", ring_build: "ring build", general: "general activities", train_delay: "train delays", maintenance_per_cycle: "maintenance per cycle", intervention: "tool interventions", maintenance_shift_and_idle: "maintenance shift" };
function forecastHtml() {
  if (!FC) return `<p class="note">Set an advance speed above zero to forecast.</p>`;
  const flag = (c) => c.above_world_record ? `<span class="flag bad">above world record ${fmt(c.world_record, 0)} m</span>`
    : c.above_epb_reference ? `<span class="flag warn">above best EPB reference ${fmt(c.epb_reference, 1)} m</span>` : `<span class="flag ok">plausible</span>`;
  const sh = Object.entries(FC.shares).filter(([, v]) => v > 0.002);
  const sv = EPB_WEEKLY_SURVEY;
  return `<dl>
    <dt>Utilisation (boring / calendar time)</dt><dd>${fmt(FC.util * 100, 0)} %</dd>
    <dt>Mean advance</dt><dd>${fmt(FC.day, 1)} m/day · ${fmt(FC.week, 0)} m/week</dd>
    <dt>40-EPB survey for comparison (Roby & Willis 2014)</dt><dd>${fmt(sv.mean, 0)} ± ${fmt(sv.sd, 0)} m/week</dd>
    <dt>Best day</dt><dd>${fmt(FC.bestDay, 1)} m ${flag(FC.check.day)}</dd>
    <dt>Best week</dt><dd>${fmt(FC.bestWeek, 0)} m ${flag(FC.check.week)}</dd>
    <dt>Best month (30 days)</dt><dd>${fmt(FC.bestMonth, 0)} m ${flag(FC.check.month)}</dd>
    <dt>Tool interventions</dt><dd>${fmt(FC.stops, 1)} in 90 days</dd>
  </dl>
  <div class="shares">${sh.map(([k, v]) => `<i title="${SHARE_NAMES[k]} ${fmt(v * 100, 0)} %" style="width:${v * 100}%;background:${SHARE_COLORS[k]}"></i>`).join("")}</div>
  <div class="legend">${sh.map(([k, v]) => `<span style="--c:${SHARE_COLORS[k]}">${SHARE_NAMES[k]} ${fmt(v * 100, 0)} %</span>`).join("")}</div>
  <p class="note">20 runs × 90 days at the current speed, shift pattern and haulage. Best values are medians over the runs. Downtime distributions from a 6.88 m metro EPB (Moosazadeh et al. 2018), applied to this slurry machine as an assumption.</p>`;
}

ui.pause.onclick = () => { S.paused = !S.paused; ui.pause.textContent = S.paused ? "Resume" : "Pause"; };
ui.reset.onclick = () => { reset(); ui.pause.textContent = "Pause"; };
ui.showLabels.onchange = () => { labelLayer.style.display = ui.showLabels.checked ? "" : "none"; };
if (innerWidth <= 640) { ui.showLabels.checked = false; labelLayer.style.display = "none"; } // too crowded on phones

function placeLabels() {
  if (!ui.showLabels.checked) return;
  const wpx = innerWidth, hpx = innerHeight;
  for (const l of labels) {
    l.obj.getWorldPosition(tmp);
    tmp.add(l.offset);
    const d = tmp.distanceTo(camera.position);
    tmp.project(camera);
    const vis = tmp.z < 1 && Math.abs(tmp.x) < 1 && Math.abs(tmp.y) < 1 && (currentView === "surface" ? l.surfaceTag : !l.surfaceTag && d < 32 * Math.min(2, Math.max(1, 1 / camera.aspect)));
    l.el.style.display = vis ? "" : "none";
    if (vis) l.el.style.left = `${((tmp.x + 1) / 2) * wpx}px`, l.el.style.top = `${((1 - tmp.y) / 2) * hpx}px`;
  }
}

// ---------------------------------------------------------------- loop
reset();
step(0);
updateSurface();
hud();
let last = performance.now(), hudT = 0, surfT = 0;
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
  if ((surfT += dtReal) > 0.5) { surfT = 0; updateSurface(); }
  if ((hudT += dtReal) > 0.15) { hudT = 0; hud(); }
  placeLabels();
  renderer.render(scene, camera);
});
