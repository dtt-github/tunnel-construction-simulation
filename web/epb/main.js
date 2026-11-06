// Slice A: urban EPB shield driven by the analytical models (models/js), laid out front to back after the method card
// in docs/research/methods-reference.md and the "urban-epb-7m" class preset (models/presets/machine-classes.json).
//
// Frame: metres, Y up, tunnel axis at y = 0. The machine stays at the origin with the cutterhead at z = 0 and the
// shield along +z; the world (ground, rings, surface) moves by +chainage, so the drive heads towards -z.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  wedgeSilo, daubWindow, DAUB_DEFAULTS, chamber as makeChamber, screw as makeScrew, shieldThrust, cutterheadTorque, toolTorque,
  verticalStress, presetTrough, twinTroughs, deflectionRatios, deflectionModificationFactor, frameBendingStiffness, relativeBendingStiffness, loadFactor, macklinVolumeLoss, burlandCategory, referenceInstalled, erf,
  Rng, sample as sampleDist, DIST, SHIFT_PATTERNS, PER_CYCLE_MAINTENANCE_MIN, simulateDrive, recordCheck, EPB_WEEKLY_SURVEY,
  jsceRing, woodInertia, subgradeModulus, terzaghiLoads, activeCoefficient, sectionStresses, jackingStress, burstingForce, annulusVolume, groutWindow, ITA2000_ALLOWABLE,
  scenario as loadScenario,
} from "../../models/js/index.js";

// ---------------------------------------------------------------- machine and scenario
// Sourced values (see machine-classes.json): diameter, installed torque and power (Crossrail-class EPB), cutterhead and
// screw speed ranges, ring of 7 segments + key, ring-build time, shield length, DAUB pressure range. Values marked "assumed" are
// illustrative. Crossrail lining and production: King, Thomas & Stenning (2017), Proc. ICE Civil Engineering 170(CE5),
// doi:10.1680/jcien.16.00028 [KING]; shield: Crossrail Learning Legacy, TBM station transits [TRANSIT].
const M = {
  D: 7.08, // m, sourced
  torqueLimit: 9800, // kNm installed, sourced
  power: 1920, // kW installed, sourced
  shieldLength: 12, // m, 12 m shield with mid-shield articulation [TRANSIT]
  chamberLength: 0.9, // assumed
  ringWidth: 1.6, // m, 7 segments + small key, 1.6 m rings [KING]
  ringOD: 6.8, ringID: 6.2, // m, 300 mm SFRC segments [KING]
  buildMin: 32, // min per ring, Crossrail average (Tunnels & Tunnelling, 25 Feb 2021, "Lord of the rings")
  shieldWeight: 4000, backupWeight: 6000, tailSeal: 500, // kN, assumed
  nTools: 80, toolForce: 4, // scrapers and rippers, kN tangential each, assumed
};
const R = M.D / 2;
const AREA = Math.PI * R * R;
// Ground. Default: the Farringdon - Liverpool Street scenario built from open BGS/Crossrail boreholes
// (models/scenarios/london-farringdon-liverpool-street.json): one zone per 10 m of drive with the ground at the face,
// its own axis depth and the pore pressure of its water system. ?ground=illustrative gives the two-zone ground.
const GROUND = new URLSearchParams(location.search).get("ground") === "illustrative" ? "illustrative" : "london";
const SCN = GROUND === "london" ? loadScenario(await (await fetch("../../models/scenarios/london-farringdon-liverpool-street.json")).json()) : null;
const BIN = 10; // m
const GRANULAR = new Set(["RTD", "HF", "TS", "CK"]); // trough width k 0.35 (granular), else 0.5 (clay), O'Reilly & New
let ZONES;
if (SCN) {
  ZONES = [];
  for (let i = 0; i * BIN < SCN.length; i++) {
    const ch = i * BIN + BIN / 2, f = SCN.face(ch, M.D);
    const shares = Object.entries(f.units_on_face).sort((a, b) => b[1] - a[1]);
    ZONES.push({
      key: `b${i}`, from: i * BIN, to: (i + 1) * BIN,
      name: shares.map(([u, sh]) => `${SCN.units[u].name.replace(/ \(.*\)/, "")}${shares.length > 1 ? ` ${Math.round(sh * 100)} %` : ""}`).join(", "),
      gamma: f.gamma, phi: f.phi, c: f.c, k0: f.k0, Es: f.e_soil, z0: f.axis_depth, water: f.water_depth_equiv, u: f.u_axis,
      k: SCN.data.settlement?.k ?? shares.reduce((a, [u, sh]) => a + sh * (GRANULAR.has(u) ? 0.35 : 0.5), 0),
      unit: f.unit_at_axis, color: parseInt(SCN.units[f.unit_at_axis].color.slice(1), 16),
    });
  }
  ZONES[0].from = -60;
} else {
  ZONES = [
    { key: "a", name: "Stiff clay", Es: 50e3, from: -60, to: 70, gamma: 20, phi: 24, c: 10, k0: 0.6, k: 0.5, color: 0x6f6252, z0: 20, water: 3 },
    { key: "b", name: "Clayey sand", Es: 40e3, from: 70, to: 260, gamma: 20, phi: 32, c: 2, k0: 0.45, k: 0.35, color: 0x9a8457, z0: 20, water: 3 },
  ];
}
const zoneAt = (ch) => ZONES.find((z) => ch >= z.from && ch < z.to) ?? ZONES.at(-1);
const Z0 = Math.round(zoneAt(0).z0); // axis depth for the scene and the surface view; the physics uses each zone's own
// Buildings: the scenario's OS OpenMap Local footprints with LIDAR heights and listed status (OGL), or three
// illustrative blocks. x spans the footprint across the line (offset, + to the right of the drive), cz is its middle
// chainage; strain is checked across the full width at the centroid chainage.
const BUILDINGS = SCN?.data.buildings
  ? SCN.data.buildings.map((b) => ({
    name: b.name ?? b.listed?.[0]?.[1]?.replace(/\b\w+/g, (w) => w[0] + w.slice(1).toLowerCase()) ?? `Building at ch ${Math.round(b.chainage)}`,
    grade: b.listed?.[0]?.[0] ?? null, listed: b.listed ?? [], ch: b.chainage, cz: (b.ch_min + b.ch_max) / 2, xmin: b.off_min, xmax: b.off_max,
    x: (b.off_min + b.off_max) / 2, w: Math.min(b.off_max - b.off_min, 150), d: Math.max(b.ch_max - b.ch_min, 3), h: b.height, hSource: b.height_source,
  }))
  : [
  { name: "Building A", x: -4, ch: 45, w: 14, d: 10, h: 12 },
  { name: "Building B", x: 13, ch: 95, w: 12, d: 16, h: 18 },
  { name: "Building C", x: -20, ch: 150, w: 16, d: 12, h: 9 },
].map((b) => ({ ...b, cz: b.ch, xmin: b.x - b.w / 2, xmax: b.x + b.w / 2, listed: [] }));
const CH = makeChamber(Math.PI * R * R * M.chamberLength);
const SCREW = makeScrew({ diameter: 0.9, shaftDiameter: 0.3, pitch: 0.7, length: 11, efficiency: 0.6, decayLength: 3 });
const SCREW_ANGLE = (22 * Math.PI) / 180;

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
  chamber: { pos: [7.0, 1.6, -3.2], target: [0, -0.4, 0.9] },
  tail: { pos: [10.5, 1.8, 2.5], target: [0, -0.8, 9.5] },
  surface: { pos: [150, Z0 + 140, -150], target: [0, Z0, 30] },
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

// Cut-away: shells (shield, lining, ground, screw casing) lose their x > 0 half so the inside is visible.
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

// Chamber contents (conditioned soil paste): opacity follows the fill, colour lightens with foam.
const paste = new THREE.Mesh(alongZ(new THREE.CylinderGeometry(R - 0.06, R - 0.06, M.chamberLength - 0.1, 48)),
  new THREE.MeshStandardMaterial({ color: 0x6b5a45, roughness: 1, transparent: true, opacity: 0.35, depthWrite: false, clippingPlanes: CUT }));
paste.position.z = 0.25 + M.chamberLength / 2 + 0.05;
machine.add(paste);

// Pressure bulkhead with earth-pressure cells, stators, main drive and man-lock.
const ZB = 0.25 + M.chamberLength + 0.25; // bulkhead plane
const bulkhead = cyl(R - 0.03, 0.15, mat(0xb88a00, { clippingPlanes: CUT }), 64);
bulkhead.position.z = ZB;
machine.add(bulkhead);
label("Pressure bulkhead", bulkhead, [0, 2.6, 0]);
const cells = [];
for (const [y, name] of [[R * 0.75, "crown"], [R * 0.4, "upper"], [0, "axis"], [-R * 0.4, "lower"], [-R * 0.75, "invert"]]) {
  const c = cyl(0.13, 0.06, new THREE.MeshStandardMaterial({ color: 0x57c38a, emissive: 0x1a3a28 }), 16);
  c.position.set(-0.9, y, ZB - 0.1);
  machine.add(c);
  cells.push({ mesh: c, y, name });
}
label("Earth-pressure cells", cells[1].mesh, [0, 0.3, 0]);
for (const a of [Math.PI * 0.1, Math.PI * 1.1]) {
  const st = box(0.22, 0.22, 0.45, steel);
  st.position.set(1.6 * Math.cos(a), 1.6 * Math.sin(a), ZB - 0.3);
  machine.add(st);
}
const drive = cyl(1.7, 1.1, dark, 40);
drive.position.z = ZB + 0.65;
machine.add(drive);
label("Main drive", drive, [0, 1.9, 0]);
const manlock = new THREE.Group();
for (const dz of [0, 1.6]) {
  const ch = cyl(0.65, 1.5, mat(0x6e7a86), 24);
  ch.position.z = dz;
  manlock.add(ch);
}
manlock.position.set(-1.4, 1.75, ZB + 1.0);
machine.add(manlock);
label("Man-lock", manlock, [0, 0.9, 0.8]);

// Screw conveyor from the chamber invert, rising to the gate above the belt.
const screwGroup = new THREE.Group();
screwGroup.position.set(0, -R + 0.75, 0.9);
screwGroup.rotation.x = -SCREW_ANGLE;
machine.add(screwGroup);
const casing = new THREE.Mesh(alongZ(new THREE.CylinderGeometry(0.5, 0.5, SCREW.length, 32, 1, true)),
  mat(0x9a7a20, { side: THREE.DoubleSide, clippingPlanes: CUT, transparent: true, opacity: 0.55 }));
casing.position.z = SCREW.length / 2;
screwGroup.add(casing);
const flights = new THREE.Group();
flights.add(cyl(0.15, SCREW.length, steel, 12).translateZ(SCREW.length / 2));
{
  const pts = [];
  const turns = SCREW.length / SCREW.pitch;
  for (let i = 0; i <= turns * 24; i++) {
    const t = i / 24;
    pts.push(new THREE.Vector3(0.32 * Math.cos(t * 2 * Math.PI), 0.32 * Math.sin(t * 2 * Math.PI), t * SCREW.pitch));
  }
  flights.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), pts.length, 0.12, 6), steel));
}
screwGroup.add(flights);
const gate = box(0.9, 0.5, 0.6, dark);
gate.position.set(0, -0.3, SCREW.length + 0.2);
screwGroup.add(gate);
label("Screw conveyor", casing, [0, 0.7, 0]);
label("Screw gate", gate, [0, 0.5, 0]);
const screwOutlet = new THREE.Vector3(0, -R + 0.75 + Math.sin(SCREW_ANGLE) * (SCREW.length + 0.2) - 0.5, 0.9 + Math.cos(SCREW_ANGLE) * (SCREW.length + 0.2));

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

// Backup: gantries on rails, belt conveyor, foam plant, grout tanks, control cabin, power pack, ventilation duct.
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
  { z: 14, kit: "Foam plant (generators, surfactant and polymer tanks)" },
  { z: 28, kit: "Grout plant (A and B components)" },
  { z: 42, kit: "Control cabin" },
  { z: 56, kit: "Transformer and hydraulic power pack" },
  { z: 70, kit: "Ventilation fan, cable and hose reels" },
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
  if (g.kit.startsWith("Foam")) {
    for (const dz of [-3, -1.2, 0.6]) { const t = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 1.5, 16), mat(0xe6e2d8)); t.position.set(-1.1, railY + 4.25, dz); grp.add(t); }
    const fg = box(1.0, 0.9, 2.2, mat(0x2f6f9f)); fg.position.set(-1.1, railY + 3.95, 3); grp.add(fg);
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
// Belt: from under the screw gate along the backup deck.
const BELT_Y = 0.55, BELT_Z0 = screwOutlet.z - 0.3, BELT_Z1 = 95;
const belt = box(1.0, 0.12, BELT_Z1 - BELT_Z0, dark);
belt.position.set(0, BELT_Y, (BELT_Z0 + BELT_Z1) / 2);
backup.add(belt);
label("Belt conveyor (to the portal)", belt, [0, 0.5, -30]);
// Muck on the belt (visual; spawn rate follows the screw discharge).
const MUCK_MAX = 500;
const muck = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(0.09, 0), new THREE.MeshStandardMaterial({ color: 0x5e5040, roughness: 1, flatShading: true }), MUCK_MAX);
muck.count = 0;
backup.add(muck);
const muckZ = [], muckX = [];
// Segment car on the rails
const car = new THREE.Group();
car.position.z = 84;
car.add(box(1.6, 0.4, 6, mat(0x2f6f9f)).translateY(railY + 0.45));
for (let k = 0; k < 3; k++) { const s = box(1.4, 0.3, 1.6, mat(0xb9b9b4)); s.position.set(0, railY + 0.8 + k * 0.32, -1.5); car.add(s); }
backup.add(car);
label("Segment and grout supply train", car, [0, railY + 2.2, 0]);

// ---------------------------------------------------------------- world: ground, lining, surface
const world = new THREE.Group();
scene.add(world);
// ground blocks, merging neighbouring zones of the same colour
const blocks = [];
for (const z of ZONES) {
  const last = blocks.at(-1);
  if (last && last.color === z.color && last.to === z.from) last.to = z.to;
  else blocks.push({ from: z.from, to: z.to, color: z.color });
}
for (const z of blocks) {
  const from = Math.max(z.from, 0), len = z.to - from;
  const b = box(16, 12, len, new THREE.MeshStandardMaterial({ color: z.color, roughness: 1, transparent: true, opacity: 0.4, depthWrite: false,
    clippingPlanes: [new THREE.Plane(new THREE.Vector3(0, 0, -1), 0), CUT[0]] }));
  b.position.set(0, 0, -(from + len / 2));
  world.add(b);
}

// Tapered ring, 7 segments + small key (key inserted last, never below the axis [KING]). Pieces are annular sectors
// centred on angle 0.
const N_SEG = 7, KEY_DEG = 360 / 19, SEG_DEG = (360 - KEY_DEG) / N_SEG;
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
  for (let i = 1; i <= N_SEG; i++) pieces.push({ angle: key + kd / 2 + sd * (i - 0.5), key: false, i });
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
// The second bore, shown only with "after both drives": a plain tube at its offset under the surface grid.
const bore2Tube = new THREE.Mesh(alongZ(new THREE.CylinderGeometry(M.D / 2, M.D / 2, SURF.c1 - SURF.c0, 40, 1, true)),
  new THREE.MeshStandardMaterial({ color: 0x8c96a0, transparent: true, opacity: 0.35, side: THREE.DoubleSide, depthWrite: false }));
bore2Tube.position.set(SCN?.data.settlement?.second_bore?.offset_m ?? 0, -Z0, -(SURF.c0 + SURF.c1) / 2);
bore2Tube.visible = false;
surface.add(bore2Tube);
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
  b.mesh = box(b.w, b.h, b.d, new THREE.MeshStandardMaterial({ color: CAT_COLORS[0], roughness: 0.8, transparent: true, opacity: 0.55, depthWrite: false }));
  b.mesh.position.set(b.x, Z0 + b.h / 2, -b.cz);
  world.add(b.mesh);
  const notable = !SCN || b.grade === "I" || b.grade === "II*" || /station|hall|market|church|house/i.test(b.name);
  b.label = notable ? label(b.name, b.mesh, [0, b.h / 2 + 1.5, 0], true) : null;
}
const LINE_LEN = SCN ? SCN.length : SURF.c1;
const tunnelLine = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.05, LINE_LEN), new THREE.MeshBasicMaterial({ color: 0x5b8db8 }));
tunnelLine.position.set(0, Z0 + 0.05, -LINE_LEN / 2);
world.add(tunnelLine);
const faceMarker = new THREE.Mesh(new THREE.ConeGeometry(0.8, 2.5, 4), new THREE.MeshBasicMaterial({ color: 0xf2b43a }));
faceMarker.rotation.x = Math.PI;
faceMarker.position.set(0, Z0 + 1.6, 0);
scene.add(faceMarker);
label("Face position", faceMarker, [0, 1.8, 0], true);

// ---------------------------------------------------------------- UI
const ids = ["adv", "rpm", "screwMode", "target", "screw", "fir", "fer", "vl", "ts", "advOut", "rpmOut", "targetOut", "screwOut", "firOut", "ferOut", "vlOut", "tsOut",
  "pause", "reset", "gauge", "chamber", "alarms", "cycle", "bars", "ground", "showLabels", "shift", "haulage", "interventions", "skip", "forecast", "lining", "section", "groundSel", "bore2"];
const ui = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));
const val = (id) => +ui[id].value;
if (SCN?.data.settlement) { ui.vl.min = 0.1; ui.vl.value = SCN.data.settlement.volume_loss; }
// Crossrail worked two 12 h shifts a day, seven days a week (west: three 8 h shifts) [KING]
if (SCN) ui.shift.value = "2x12h_maintenance_per_cycle";

// ---------------------------------------------------------------- simulation
let S;
const troughCache = new Map();
function trough(zone, vl) {
  const key = `${zone.key}|${vl}`;
  if (!troughCache.has(key)) troughCache.set(key, presetTrough("closed_face_clay", M.D, zone.z0, { shieldLengthM: M.shieldLength, volumeLoss: vl / 100, k: zone.k }));
  return troughCache.get(key);
}
// Volume loss from the face (Macklin 1999, quoted from Divall et al. 2023, open; models/js/settlement.js): in London
// Clay the load factor LF = N / N_TC at the face sets a volume loss 0.23 % x exp(4.4 LF). The volume loss used for a
// zone is the larger of the scenario's measured value (slider) and the mean Macklin value while that zone was dug, so
// lowering the face pressure raises the settlement of the ground dug meanwhile. S_u = 85 + 5 z kPa, z below +20 m OD
// (about ground level here), is the Crossrail Paddington design profile (Chandegra & Kokkinou 2016, Learning Legacy),
// carried along the line. Other units (Lambeth Group, sands, Chalk) keep the measured value: Macklin's data are from
// overconsolidated clay.
const suLondonClay = (z) => 85 + 5 * z;
function faceLoadFactor(zone, p) {
  if (!SCN || zone.unit !== "LC") return null;
  return loadFactor(zone.gamma * zone.z0, p, suLondonClay(zone.z0), (zone.z0 - R) / M.D);
}
const macklinDug = new Map(); // zone key -> [sum of Macklin VL (%) x advance, advance]
function vlFor(zone) {
  const r = macklinDug.get(zone.key);
  const vl = r && r[1] > 0 ? Math.max(val("vl"), r[0] / r[1]) : val("vl");
  return Math.round(vl * 1000) / 1000; // 0.001 % steps keep the trough cache small
}
// Second bore, driven after this one (scenario settlement.second_bore): its own trough at offset_m, with the published
// volume-loss ratio and trough widths towards / away from this bore (Hyde Park, Wan et al. 2017; Thames, Cheng & Mikulski 2014).
const BORE2 = SCN?.data.settlement?.second_bore ?? null;
const bothBores = () => BORE2 !== null && ui.bore2.value === "both";
const trough2Cache = new Map();
function trough2(zone, vl) {
  const key = `${zone.key}|${vl}`;
  if (!trough2Cache.has(key)) trough2Cache.set(key, twinTroughs(M.D, zone.z0, BORE2.offset_m, vl / 100, null, zone.k,
    { secondVlFactor: BORE2.vl_ratio, secondInnerK: BORE2.k_inner, secondOuterK: BORE2.k_outer }).second);
  return trough2Cache.get(key);
}
if (BORE2) ui.bore2.closest("label").hidden = false;
function windowFor(zone, pasteWeight) {
  const cover = zone.z0 - R;
  const fs = wedgeSilo(M.D, cover, zone.gamma, zone.phi, zone.c, { waterDepth: zone.water });
  // DAUB (2016) chapter 3: the set point must stay inside the window by the machine's pressure deviation (±30 kPa)
  return { fs, w: daubWindow(fs, M.D, cover, zone.gamma, { waterDepth: zone.water, supportUnitWeight: pasteWeight, deviation: DAUB_DEFAULTS.deviation_epb }) };
}
function reset() {
  macklinDug.clear();
  for (const r of rings) world.remove(r.g);
  rings.length = 0;
  for (let n = -8; n < 0; n++) addRing(n, ZR - n * W); // launch section behind the build position, already grouted
  for (const r of rings) r.grout.visible = true;
  const fir = val("fir") / 100;
  const qe = AREA * (val("adv") / 60000);
  const q = CH.screwFlowForPressure(val("target"), qe || 1e-3, fir, val("fer"));
  S = {
    chainage: 0, stroke: 0, mode: "PUSH", ring: 0, pieces: null, piece: 0, pieceT: 0, simTime: 0, paused: false,
    st: CH.steadyState(qe || 1e-3, q, fir, val("fer")), screwRpm: SCREW.rpmForFlow(q), cutRpm: val("rpm"),
    pushTime: 0, lastPush: null, lastBuild: null, grout: 0, excavated: 0, muckDebt: 0, torque: 0, thrust: null, tq: null, stalled: false,
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

function pasteUnitWeight() {
  return 18 * (1 - CH.airFraction(S.st)); // soil-water paste ~18 kN/m^3, lightened by foam air
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

function substep(dt) {
  // Tool interventions run round the clock; everything else only in production hours.
  if (S.mode === "INTERVENTION") {
    S.cutRpm = S.screwRpm = 0; S.tq = S.thrust = null; S.torque = 0;
    const d = Math.min(dt, S.stopLeft);
    S.stopLeft -= d; S.simTime += d;
    if (S.stopLeft <= 1e-6) S.mode = "PUSH";
    return;
  }
  if (!inProduction()) {
    S.cutRpm = S.screwRpm = 0; S.tq = S.thrust = null; S.torque = 0;
    S.simTime += dt;
    return;
  }
  if (S.mode === "ACTIVITIES") {
    S.cutRpm = S.screwRpm = 0; S.tq = S.thrust = null; S.torque = 0;
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
  const fir = val("fir") / 100, fer = val("fer"), target = val("target");
  const zone = zoneAt(S.chainage);
  const p = CH.pressure(S.st);
  S.cutRpm = S.mode === "PUSH" ? val("rpm") : 0;
  const sv = verticalStress(zone.z0, zone.gamma, { waterDepth: zone.water });
  // torque at the current pressure; above the installed limit the head stalls and the push stops
  S.tq = S.cutRpm > 0 ? cutterheadTorque(M.D, p, (sv * (1 + zone.k0)) / 2, {
    openingRatio: drawnOpening, nArms: 4, armArea: 0.5, armRadius: 2.3, tools: toolTorque(M.nTools, M.toolForce, R), seals: 300,
  }) : null;
  S.torque = S.tq ? S.tq.total : 0;
  S.stalled = S.torque > M.torqueLimit;
  const v = S.mode === "PUSH" && S.cutRpm > 0 && !S.stalled ? val("adv") / 60000 : 0; // m/s
  const qe = AREA * v;
  if (S.mode === "PUSH") {
    if (ui.screwMode.value === "auto") {
      // feed-forward from the steady balance plus proportional correction on the pressure error
      const ff = qe > 0 ? SCREW.rpmForFlow(S.ff ?? 0) : 0;
      S.screwRpm = Math.min(22, Math.max(0, ff + 0.06 * (p - target)));
    } else S.screwRpm = val("screw");
  } else S.screwRpm = 0; // gate closed while the ring is built
  S.st = CH.step(S.st, dt, qe, SCREW.discharge(S.screwRpm), fir, fer);
  S.thrust = v > 0 ? shieldThrust(M.D, M.shieldLength, zone.z0, zone.gamma, p, {
    waterDepth: zone.water, k0: zone.k0, shieldWeight: M.shieldWeight, tools: 1000, tailSeal: M.tailSeal, backupWeight: M.backupWeight,
  }) : null;
  S.simTime += dt;
  if (S.mode === "PUSH") {
    const adv = Math.min(v * dt, W - S.stroke);
    S.stroke += adv;
    S.chainage += adv;
    const lf = faceLoadFactor(zone, p);
    if (lf !== null && adv > 0) {
      const r = macklinDug.get(zone.key) ?? [0, 0];
      r[0] += 100 * macklinVolumeLoss(lf) * adv; r[1] += adv;
      macklinDug.set(zone.key, r);
    }
    S.pushTime += dt;
    if (v > 0) S.boringTime += dt;
    S.excavated += AREA * adv;
    S.grout += Math.PI * (R * R - (M.ringOD / 2) ** 2) * adv; // theoretical annulus, filled during the shove
    S.muckDebt += SCREW.discharge(S.screwRpm) * dt;
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
    const per = (M.buildMin * 60) / (N_SEG + 1);
    if (S.pieceT >= per) {
      S.pieceT -= per;
      const done = S.pieces[S.piece];
      if (done) buildGroup.add(makePiece(done, S.ring));
      S.piece++;
      if (S.piece >= N_SEG + 1) {
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
  const qe = AREA * (val("adv") / 60000);
  S.ff = qe > 0 ? CH.screwFlowForPressure(val("target"), qe, val("fir") / 100, val("fer")) : 0;
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
  flights.rotation.z += (S.screwRpm / 60) * 2 * Math.PI * dtReal;
  // grout becomes visible once a ring has left the tail
  for (const r of rings) r.grout.visible = r.g.position.z + world.position.z > M.shieldLength - 0.2;
  // cylinders: on the last ring while pushing; per sector retract-place-extend while building
  for (const c of cylinders) {
    if (S.mode === "PUSH") c.target = ZR + S.stroke;
    else {
      const placed = S.pieces.slice(0, S.piece);
      const cur = S.pieces[S.piece];
      const inSector = (p) => Math.abs(Math.atan2(Math.sin(c.a - p.angle), Math.cos(c.a - p.angle))) < ((p.key ? KEY_DEG : SEG_DEG) * Math.PI) / 360 + 0.05;
      if (cur && inSector(cur) && S.pieceT / ((M.buildMin * 60) / (N_SEG + 1)) < 0.9) c.target = ZR - 0.1;
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
    const f = Math.min(S.pieceT / ((M.buildMin * 60) / (N_SEG + 1)), 1);
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
  // muck on the belt: one chunk per 0.02 m^3 of discharge (time-scaled), moving at 2.5 m/s
  const spawn = Math.min(Math.floor(S.muckDebt / 0.02), 6);
  S.muckDebt -= spawn * 0.02;
  if (S.muckDebt > 0.5) S.muckDebt = 0.5;
  for (let k = 0; k < spawn && muckZ.length < MUCK_MAX; k++) { muckZ.push(BELT_Z0 + Math.random() * 0.4); muckX.push((Math.random() - 0.5) * 0.6); }
  const m4 = new THREE.Matrix4();
  let n = 0;
  for (let k = 0; k < muckZ.length; k++) {
    muckZ[k] += 2.5 * dtReal;
    if (muckZ[k] > BELT_Z1) continue;
    muckZ[n] = muckZ[k];
    muckX[n] = muckX[k];
    m4.makeTranslation(muckX[n], BELT_Y + 0.12, muckZ[n]);
    muck.setMatrixAt(n++, m4);
  }
  muckZ.length = muckX.length = n;
  muck.count = n;
  muck.instanceMatrix.needsUpdate = true;
  // chamber paste and pressure cells
  const fill = CH.fill(S.st), air = CH.airFraction(S.st);
  paste.material.opacity = 0.12 + 0.4 * fill;
  paste.material.color.setRGB(0.42 + air * 0.9, 0.35 + air * 0.9, 0.27 + air * 0.9);
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

// Building bending (Potts & Addenbrooke 1997, as plotted by Mair 1997 Fig. 4, open): the greenfield deflection ratio
// Delta/L under the footprint from this bore's final trough, and the same with the building's estimated bending
// stiffness (floor slabs every 3.4 m acting together: an assumed upper estimate). Shown only: the damage category stays
// on greenfield horizontal strain, because the factors for horizontal strain are not in any open source.
function buildingBending(b) {
  const zone = zoneAt(b.ch), vl = vlFor(zone), key = `${zone.key}|${vl}`;
  if (b.bending?.key === key) return b.bending;
  const t = trough(zone, vl), width = b.xmax - b.xmin;
  const gf = deflectionRatios((x) => t.settlement(x), b.xmin, b.xmax, t.i_left ?? t.i, t.i_right ?? t.i, 60);
  const storeys = Math.max(1, Math.round((b.h ?? 10) / 3.4));
  const rho = relativeBendingStiffness(frameBendingStiffness(storeys), zone.Es, width), eB = Math.abs(b.x) / width;
  const sag = gf.sag ? gf.sag[1] : 0, hog = gf.hog ? gf.hog[1] : 0;
  const mod = Math.max(sag * deflectionModificationFactor("sag", rho, eB), hog * deflectionModificationFactor("hog", rho, eB));
  return (b.bending = { key, gf: Math.max(sag, hog), mod, rho, storeys });
}
// Surface settlement and building categories.
let surfaceMax = 0;
function bothSmax(zone) {
  const t = trough(zone, vlFor(zone)), t2 = trough2(zone, vlFor(zone));
  let m = 0;
  for (let x = -20; x <= BORE2.offset_m + 20; x += 0.25) m = Math.max(m, t.settlement(x) + t2.settlement(x - BORE2.offset_m));
  return m;
}
function updateSurface() {
  const c = S.chainage;
  // the surface grid covers 260 m of chainage; it follows the face in 50 m steps
  const surfOff = Math.max(Math.floor((c - 60) / 50) * 50, 0);
  surface.position.z = -surfOff;
  const pos = surfGeo.attributes.position, col = surfGeo.attributes.color;
  let smax = 0;
  const both = bothBores();
  bore2Tube.visible = both;
  // after both drives every trough is final; otherwise this bore's trough grows with the face
  const settle = (x, ch) => {
    const zone = zoneAt(ch), zvl = vlFor(zone), t = trough(zone, zvl);
    return both ? t.settlement(x) + trough2(zone, zvl).settlement(x - BORE2.offset_m) : t.settlement(x) * tunnelFraction(t, c, ch);
  };
  for (let k = 0; k < pos.count; k++) {
    const x = pos.getX(k), ch = -pos.getZ(k) + surfOff;
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
    let emax = 0, smaxB = 0;
    for (let x = b.xmin, dx = Math.max((b.xmax - b.xmin) / 200, 0.25); x <= b.xmax; x += dx) {
      const e = -(settle(x + 0.05, b.ch) * (x + 0.05) - settle(x - 0.05, b.ch) * (x - 0.05)) / (zoneAt(b.ch).z0 * 0.1);
      emax = Math.max(emax, e);
      smaxB = Math.max(smaxB, settle(x, b.ch));
    }
    b.strain = emax * 100;
    b.settle = smaxB; // largest settlement under the footprint
    const [cat, name] = burlandCategory(b.strain);
    b.cat = cat;
    buildingBending(b);
    b.catName = name;
    b.mesh.material.color.setHex(CAT_COLORS[cat]);
    b.mesh.position.y = Z0 + b.h / 2 - b.settle * 150;
    if (b.label) b.label.el.textContent = `${b.name}: cat. ${cat} ${name}`;
  }
}

// ---------------------------------------------------------------- HUD
const fmt = (v, d = 1) => v.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const hms = (s) => `${Math.floor(s / 3600)} h ${String(Math.floor((s % 3600) / 60)).padStart(2, "0")} min`;
const dl = (el, rows) => { el.innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join(""); };
const REF = referenceInstalled("epb", M.D);

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
const SEG = { n: N_SEG + 1, E: 36e6, pad: 0.2, gammaC: 25 };
const SEG_T = (M.ringOD - M.ringID) / 2, SEG_RC = (M.ringOD + M.ringID) / 4;
const liningCache = new Map();
function liningAt(zone) {
  if (!liningCache.has(zone.key)) {
    // vertical load reduced by Terzaghi's formula (ITA 2000, 2.2.1); lateral coefficient at both ends of the ITA range
    // (active and at rest), the case with the higher concrete stress governs
    const eta = woodInertia(1, SEG.n), ka = activeCoefficient(zone.phi);
    const cases = [["active", ka], ["at rest", zone.k0]].map(([lamName, lam]) => {
      const [pv, q1, q2] = terzaghiLoads(zone.z0, M.ringOD / 2, zone.gamma, zone.phi, zone.c, lam, zone.water);
      const r = jsceRing(pv, q1, q2, SEG.gammaC * SEG_T, SEG_RC, (SEG.E * SEG_T ** 3) / 12, subgradeModulus(zone.Es, SEG_RC), { eta });
      const iMax = r.moment.indexOf(Math.max(...r.moment)), iMin = r.moment.indexOf(Math.min(...r.moment));
      const sMax = sectionStresses(r.normal[iMax], r.moment[iMax], SEG_T), sMin = sectionStresses(r.normal[iMin], r.moment[iMin], SEG_T);
      return { lamName, lam, pv, q1, q2, eta, r, iMax, iMin, sigma: Math.max(sMax[0], sMin[0]), sigmaMin: Math.min(sMax[1], sMin[1]),
        oval: (2 * r.deflection) / M.ringID };
    });
    const g = cases[0].sigma >= cases[1].sigma ? cases[0] : cases[1];
    liningCache.set(zone.key, { ...g, overburden: zone.gamma * (zone.z0 - M.ringOD / 2), grout: groutWindow(zone.z0 - R, zone.gamma, zone.water) });
  }
  return liningCache.get(zone.key);
}
function liningRows(zone) {
  const L = liningAt(zone), r = L.r;
  const shoe = S.thrust ? S.thrust.total / N_CYL : null;
  const js = shoe ? jackingStress(shoe, N_CYL, SEG_RC, SEG_T) : null;
  const [tb] = shoe ? burstingForce(shoe, SEG_T, SEG.pad) : [null];
  const rows = [
    ["Ring", `${N_SEG} + key, ${fmt(SEG_T * 1000, 0)} mm, ${W} m wide; joints cut bending stiffness to ${fmt(L.eta * 100, 0)} % (Wood)`],
    ["Loads at crown / springline", `${fmt(L.pv, 0)} kPa vertical (Terzaghi-reduced; full overburden ${fmt(L.overburden, 0)} kPa); ${fmt(L.q1, 0)}–${fmt(L.q2, 0)} kPa lateral, ${L.lamName} coefficient ${fmt(L.lam, 2)} governs`],
    ["Bending moment", `+${fmt(r.moment[L.iMax], 0)} kNm/m at ${r.angles_deg[L.iMax]}°, ${fmt(r.moment[L.iMin], 0)} kNm/m at ${r.angles_deg[L.iMin]}° from the crown`],
    ["Normal force", `${fmt(Math.min(...r.normal), 0)}–${fmt(Math.max(...r.normal), 0)} kN/m`],
    ["Concrete stress", `${fmt(L.sigma / 1000, 1)} MPa max, ${fmt(L.sigmaMin / 1000, 1)} MPa min${L.sigmaMin < 0 ? ", tension carried by the reinforcement" : ""} (ITA 2000 allowable ${fmt(ITA2000_ALLOWABLE.concrete_42 / 1000, 0)} MPa for C42)`],
    ["Ovalisation", `${fmt(Math.abs(L.oval) * 100, 2)} % of the inner diameter, ${L.oval >= 0 ? "squatting" : "rising"} (limit 0.5 %, DAUB)`],
    ["Jacking stress per shoe", js ? `${fmt(shoe / 1000, 2)} MN on ${N_CYL} shoes: ${fmt(js / 1000, 1)} MPa (allowable ${fmt((ITA2000_ALLOWABLE.concrete_42 * ITA2000_ALLOWABLE.jacking_factor) / 1000, 1)} MPa while jacking)` : "no thrust on the ring"],
    ["Bursting force per shoe", tb ? `${fmt(tb, 0)} kN (DAUB, 0.2 m pad)` : "—"],
    ["Annulus grout", `${fmt(annulusVolume(M.D, M.ringOD, W), 2)} m³ per ring; pressure at the crown ${fmt(L.grout[0] / 100, 2)}–${fmt(L.grout[1] / 100, 2)} bar (above groundwater, at most 69 kPa over it)`],
  ];
  const alarms = [];
  if (js && js > ITA2000_ALLOWABLE.concrete_42 * ITA2000_ALLOWABLE.jacking_factor) alarms.push(`Jacking stress ${fmt(js / 1000, 1)} MPa above the allowable for the temporary jacking state`);
  if (L.sigma > ITA2000_ALLOWABLE.concrete_42) alarms.push(`Ring concrete stress ${fmt(L.sigma / 1000, 1)} MPa above the ITA 2000 allowable ${fmt(ITA2000_ALLOWABLE.concrete_42 / 1000, 0)} MPa`);
  if (Math.abs(L.oval) > 0.005) alarms.push(`Ring ovalisation ${fmt(Math.abs(L.oval) * 100, 2)} % above 0.5 % of the inner diameter`);
  return { rows, alarms };
}

function hud() {
  for (const [id, out, f] of [["adv", "advOut", (v) => `${v} mm/min`], ["rpm", "rpmOut", (v) => `${fmt(v, 1)} rpm`], ["target", "targetOut", (v) => `${fmt(v / 100, 2)} bar`],
    ["screw", "screwOut", (v) => `${fmt(v, 1)} rpm`], ["fir", "firOut", (v) => `${v} %`], ["fer", "ferOut", (v) => fmt(v, 1)], ["vl", "vlOut", (v) => `${fmt(v, 2)} %`], ["ts", "tsOut", (v) => `×${v}`]]) {
    ui[out].textContent = f(val(id));
  }
  const auto = ui.screwMode.value === "auto";
  ui.target.closest("label").classList.toggle("dim", !auto);
  ui.screw.closest("label").classList.toggle("dim", auto);

  const zone = zoneAt(S.chainage), pw = pasteUnitWeight();
  const { fs, w } = windowFor(zone, pw);
  const p = CH.pressure(S.st), fill = CH.fill(S.st), air = CH.airFraction(S.st);
  const pCrown = Math.max(p - pw * R, 0), pInv = p + pw * R;
  ui.gauge.innerHTML = gaugeSvg([
    { name: "Crown", p: pCrown / 100, min: w.p_min_crown / 100, max: w.p_max_crown / 100 },
    { name: "Axis", p: p / 100, min: w.p_min_axis / 100, max: w.p_max_axis / 100 },
    { name: "Invert", p: pInv / 100, min: (w.p_min_axis + pw * R) / 100, max: (w.p_max_axis + pw * R) / 100 },
  ], val("target") / 100);
  dl(ui.chamber, [
    ["DAUB window at axis", `${fmt(w.p_min_axis / 100, 2)} – ${fmt(w.p_max_axis / 100, 2)} bar`],
    ["Operating range at crown", w.feasible ? `${fmt(w.p_min_crown_operating / 100, 2)} – ${fmt(w.p_max_crown_operating / 100, 2)} bar (±${fmt(w.deviation, 0)} kPa deviation inside the window)` : `none: the window is narrower than ±${fmt(w.deviation, 0)} kPa`],
    ["Chamber fill", `${fmt(fill * 100, 1)} %`],
    ["Air in chamber", `${fmt(air * 100, 1)} %`],
    ["Stiffness", `${fmt(CH.stiffness(S.st) / 100, 2)} bar per m³`],
    ["Screw speed", `${fmt(S.screwRpm, 1)} rpm`],
    ["Screw discharge", `${fmt(SCREW.discharge(S.screwRpm) * 60, 2)} m³/min`],
    ["Screw outlet pressure", `${fmt(SCREW.outletPressure(pInv) / 100, 2)} bar`],
  ]);

  const alarms = [];
  if (fill < 0.999) alarms.push(`Chamber not full (${fmt(fill * 100, 0)} %): face support lost, over-excavation`);
  else if (p < w.p_min_axis) alarms.push(`Axis pressure ${fmt(p / 100, 2)} bar below the DAUB minimum ${fmt(w.p_min_axis / 100, 2)} bar`);
  if (pCrown > w.p_max_crown) alarms.push(`Crown pressure above the blow-out limit ${fmt(w.p_max_crown / 100, 2)} bar`);
  if (!w.feasible) alarms.push(`DAUB window narrower than the ±${fmt(w.deviation, 0)} kPa pressure deviation: no safe set point`);
  if (S.mode === "PUSH" && Math.abs(p - val("target")) > 30 && auto) alarms.push("Pressure more than ±0.3 bar from target");
  if (S.stalled) alarms.push(`Torque ${fmt(S.torque, 0)} kNm above the installed ${M.torqueLimit} kNm: cutterhead stalled`);
  if (val("fir") === 0) alarms.push("No foam: unconditioned soil makes the chamber stiff and pressure hard to control");
  if (S.screwRpm >= 21.9) alarms.push("Screw at maximum speed");
  if (S.mode === "INTERVENTION") alarms.push("Cutting-tool intervention: drive stopped, chamber held under compressed air");
  for (const b of BUILDINGS.filter((x) => x.cat >= 2).sort((p, q) => q.cat - p.cat || q.strain - p.strain).slice(0, 3)) alarms.push(`${b.name}: Burland category ${b.cat} (${b.catName})`);
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
          : `RING BUILD (piece ${Math.min(S.piece + 1, 7)} of 7${S.pieces?.[S.piece]?.key ? ", key" : ""})`;
  ui.skip.disabled = !(S.mode === "INTERVENTION" || !inProduction() || S.mode === "ACTIVITIES");
  const days = S.simTime / 86400;
  dl(ui.cycle, [
    ["Mode", modeText],
    ["Clock", clock],
    ["Chainage", `${fmt(S.chainage, 2)} m`],
    ["Rings built", S.ring],
    ["Stroke", `${fmt(S.stroke * 1000, 0)} / ${W * 1000} mm`],
    ["Push time per ring", Number.isFinite(pushMin) ? `${fmt(pushMin, 0)} min` : "—"],
    ["Ring build time", `${M.buildMin} min (7 segments + key; Crossrail average)`],
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
  html += `<p class="legend">Installed torque ${fmt(M.torqueLimit / 1000, 1)} MNm. Reference thrust for this diameter ≈ ${fmt(REF.thrust[0] / 1000, 0)} MN (6.6 m mixed-face EPB scaled). Drawn opening ratio ${fmt(drawnOpening * 100, 0)} %.</p>`;
  ui.bars.innerHTML = html;
  scheduleForecast();
  ui.forecast.innerHTML = forecastHtml();
  void parts;

  const t = trough(zone, vlFor(zone)), lfNow = faceLoadFactor(zone, CH.pressure(S.st));
  dl(ui.ground, [
    ["Ground at the face", zone.name],
    ["φ′, c′, K0 (face average)", `${fmt(zone.phi, 1)}°, ${fmt(zone.c, 0)} kPa, ${fmt(zone.k0, 2)}`],
    ["Axis depth", `${fmt(zone.z0, 1)} m below ground`],
    ...(SCN ? [["Water at the axis", `${zone.unit && SCN.units[zone.unit].water === "lower" ? "deep aquifer head" : "upper water table"}, ${fmt((zone.u ?? 0) / 100, 2)} bar`],
      ["Nearest borehole", nearestBorehole(S.chainage)]] : [["Water table", `${zone.water} m below ground`]]),
    ["Required effective support", fs.s_eff > 0 ? `${fmt(fs.s_eff / 100, 2)} bar` : "none (self-supporting)"],
    ["Pore pressure at axis", `${fmt(fs.u_axis / 100, 2)} bar`],
    ["Volume loss from the face (Macklin 1999)", lfNow === null ? "not applied: not London Clay at the axis" : `load factor ${fmt(lfNow, 2)} → ${fmt(100 * macklinVolumeLoss(lfNow), 2)} %; this zone ${fmt(vlFor(zone), 2)} % (measured ${fmt(val("vl"), 2)} %)`],
    ["Final Smax (this zone)", `${fmt(t.s_max * 1000, 1)} mm`],
    ...(BORE2 ? [["Second bore", `${fmt(BORE2.offset_m, 1)} m away, VL ×${BORE2.vl_ratio} (${fmt(val("vl") * BORE2.vl_ratio, 2)} %), K ${BORE2.k_inner} towards this bore, ${BORE2.k_outer} away; final Smax of both ${fmt(bothSmax(zone) * 1000, 1)} mm${bothBores() ? " (shown)" : ""}`]] : []),
    ["Surface settlement now", `${fmt(surfaceMax * 1000, 1)} mm max`],
    ...(SCN?.data.settlement ? [["Volume loss, trough width (default)", `${SCN.data.settlement.volume_loss} %, K ${SCN.data.settlement.k} (measured on Crossrail${SCN.data.settlement.measured_smax_mm ? `; Smax ${SCN.data.settlement.measured_smax_mm.join("–")} mm measured` : ", Hyde Park"})`]] : []),
    ["Buildings within 60 m", `${BUILDINGS.length}${SCN ? `, ${BUILDINGS.filter((b) => b.listed.length).length} listed` : ""}; category 2 or worse: ${BUILDINGS.filter((b) => b.cat >= 2).length}`],
    ...BUILDINGS.filter((b) => Math.abs(b.ch - S.chainage) < 150).sort((p, q) => (q.cat ?? 0) - (p.cat ?? 0) || (q.settle ?? 0) - (p.settle ?? 0)).slice(0, 6)
      .map((b) => [`${b.name}${b.grade ? ` (Grade ${b.grade})` : ""}`, `ch ${fmt(b.ch, 0)} m, ${fmt(b.h, 0)} m high: ${fmt((b.settle ?? 0) * 1000, 1)} mm, ε ${fmt(b.strain ?? 0, 3)} %, cat. ${b.cat ?? 0}${b.bending ? `; Δ/L ${fmt(b.bending.gf * 1e4, 2)} → ${fmt(b.bending.mod * 1e4, 2)} ×10⁻⁴ with stiffness (${b.bending.storeys} ${b.bending.storeys === 1 ? "storey" : "storeys"})` : ""}`]),
    ["Surface heights", "exaggerated ×150"],
  ]);
  placeFace();
}

// Geological long section of the scenario: layers sampled every 20 m, the tunnel, both water levels, the boreholes
// and the face position.
function nearestBorehole(ch) {
  const b = SCN.boreholes.reduce((m, x) => (Math.abs(x.chainage - ch) < Math.abs(m.chainage - ch) ? x : m));
  return `${b.id} at chainage ${fmt(b.chainage, 0)} m, ${fmt(Math.abs(b.offset), 0)} m ${b.offset >= 0 ? "north" : "south"} of the line`;
}
function sectionSvg() {
  const Wd = 320, Hd = 170, L = SCN.length;
  const lv = SCN.boreholes.map((b) => b.ground_level).concat(SCN.data.river ? SCN.data.river.level.map((p) => p[1]) : []);
  const top = Math.ceil(Math.max(...lv) / 5) * 5 + 2, bot = Math.floor((Math.min(...SCN.data.alignment.axis_level.map((p) => p[1])) - R - 12) / 5) * 5;
  const X = (ch) => 6 + (ch / L) * (Wd - 12), Y = (lv) => 6 + ((top - lv) / (top - bot)) * (Hd - 30);
  let g = "";
  for (let ch = 0; ch < L; ch += 20) {
    for (const l of SCN.column(ch + 10)) {
      const y0 = Y(Math.min(l.top, top)), y1 = Y(Math.max(l.base, bot));
      if (y1 > y0) g += `<rect x="${X(ch).toFixed(1)}" y="${y0.toFixed(1)}" width="${(X(ch + 20) - X(ch) + 0.4).toFixed(1)}" height="${(y1 - y0).toFixed(1)}" fill="${SCN.units[l.unit].color}"/>`;
    }
  }
  const rv = SCN.data.river;
  if (rv) { // river water above the bed
    const pts = [];
    for (let c = Math.max(rv.from, 0); c <= Math.min(rv.to, L); c += 10) pts.push([c, SCN.surfaceAt(c)]);
    const lvl = (c) => interpPts(rv.level, c);
    g += `<polygon points="${pts.map(([c, z]) => `${X(c).toFixed(1)},${Y(z).toFixed(1)}`).join(" ")} ${pts.slice().reverse().map(([c]) => `${X(c).toFixed(1)},${Y(lvl(c)).toFixed(1)}`).join(" ")}" fill="#3a6f9e" opacity="0.75"/>`;
  }
  const line = (f, attrs) => `<polyline points="${Array.from({ length: 44 }, (_, i) => (i * L) / 43).map((c) => `${X(c).toFixed(1)},${Y(f(c)).toFixed(1)}`).join(" ")}" fill="none" ${attrs}/>`;
  { // the tunnel as a dark band between crown and invert
    const cs = Array.from({ length: 44 }, (_, i) => (i * L) / 43);
    g += `<polygon points="${cs.map((c) => `${X(c).toFixed(1)},${Y(SCN.axisAt(c) + R).toFixed(1)}`).join(" ")} ${cs.slice().reverse().map((c) => `${X(c).toFixed(1)},${Y(SCN.axisAt(c) - R).toFixed(1)}`).join(" ")}" fill="#15171a" fill-opacity="0.55" stroke="#e7e9ec" stroke-width="0.8"/>`;
  }
  g += line((c) => SCN.waterAt(c), 'stroke="#5aa0e6" stroke-dasharray="4 3"');
  if (SCN.data.groundwater.deep_head) g += line((c) => interpPts(SCN.data.groundwater.deep_head, c), 'stroke="#5aa0e6" stroke-dasharray="1 3"');
  for (const b of SCN.boreholes) g += `<line x1="${X(Math.max(b.chainage, 0)).toFixed(1)}" x2="${X(Math.max(b.chainage, 0)).toFixed(1)}" y1="${Y(b.ground_level).toFixed(1)}" y2="${Y(Math.max(b.base_level, bot)).toFixed(1)}" stroke="#15171a" stroke-width="1.2"/>`;
  g += `<line id="faceLine" x1="0" x2="0" y1="4" y2="${Hd - 24}" stroke="#f2b43a" stroke-width="2"/>`;
  for (let l = Math.ceil(bot / 10) * 10; l <= top; l += 10) g += `<text x="${Wd - 4}" y="${Y(l) + 3}" text-anchor="end">${l} m OD</text>`;
  const used = [...new Set(SCN.order.filter((u) => SCN.boreholes.some((b) => u in b.tops)))];
  const ends = SCN.data.alignment.ends ?? ["start", "end"];
  const legend = used.map((u) => `<span style="--c:${SCN.units[u].color}">${SCN.units[u].name.replace(/ \(.*\)/, "")}</span>`).join("");
  return `<svg viewBox="0 0 ${Wd} ${Hd}" role="img" aria-label="Geological long section along the drive">${g}<text x="6" y="${Hd - 8}">${ends[0]}</text><text x="${Wd - 6}" y="${Hd - 8}" text-anchor="end">${ends[1]}</text></svg>
    <div class="legend">${legend}${rv ? '<span style="--c:#3a6f9e">river (high water)</span>' : ""}<span style="--c:#5aa0e6">water table (dashed)${SCN.data.groundwater.deep_head ? ", deep head (dotted)" : ""}</span><span style="--c:#15171a">tunnel, boreholes</span></div>`;
}
function interpPts(d, ch) {
  if (ch <= d[0][0]) return d[0][1];
  for (let i = 0; i + 1 < d.length; i++) if (ch <= d[i + 1][0]) return d[i][1] + ((d[i + 1][1] - d[i][1]) * (ch - d[i][0])) / (d[i + 1][0] - d[i][0]);
  return d.at(-1)[1];
}
if (SCN) {
  ui.section.innerHTML = sectionSvg();
} else ui.section.closest("section").style.display = "none";
ui.groundSel.value = GROUND;
ui.groundSel.onchange = () => { location.search = ui.groundSel.value === "illustrative" ? "?ground=illustrative" : ""; };
function placeFace() {
  if (!SCN) return;
  const x = 6 + (Math.min(Math.max(S.chainage, 0), SCN.length) / SCN.length) * (320 - 12);
  const l = document.getElementById("faceLine");
  if (l) { l.setAttribute("x1", x.toFixed(1)); l.setAttribute("x2", x.toFixed(1)); }
}

ui.skip.onclick = () => {
  // jump over the current stoppage (chamber flows are zero while stopped, so nothing else changes)
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
  FC.check = recordCheck(M.D, FC.bestDay, FC.bestWeek, FC.bestMonth, "epb");
}
function scheduleForecast() {
  const key = JSON.stringify(forecastInputs());
  if (key === forecastKey) return;
  forecastKey = key;
  clearTimeout(forecastTimer);
  forecastTimer = setTimeout(runForecast, 250);
}
// Crossrail drives X (Royal Oak - Farringdon) and Y (Limmo - Farringdon), rings/day of 1.6 m [KING Table 3]
const CROSSRAIL = { exclDelays: ["12.3", "14.9"], inclDelays: ["5.1", "9.0"], bestDay: [33, 59], bestWeek: [169, 216] };
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
    <dt>40-EPB survey (Roby & Willis 2014)</dt><dd>${fmt(sv.mean, 0)} ± ${fmt(sv.sd, 0)} m/week</dd>
    <dt>Crossrail drives X and Y (King et al. 2017)</dt><dd>${CROSSRAIL.exclDelays.join("–")} rings a day without delays; ${CROSSRAIL.inclDelays.join("–")} over whole drives with station transits; best day ${CROSSRAIL.bestDay.join("–")} rings, best week ${CROSSRAIL.bestWeek.join("–")}. This forecast: ${fmt(FC.day / W, 1)} rings a day</dd>
    <dt>Best day</dt><dd>${fmt(FC.bestDay, 1)} m ${flag(FC.check.day)}</dd>
    <dt>Best week</dt><dd>${fmt(FC.bestWeek, 0)} m ${flag(FC.check.week)}</dd>
    <dt>Best month (30 days)</dt><dd>${fmt(FC.bestMonth, 0)} m ${flag(FC.check.month)}</dd>
    <dt>Tool interventions</dt><dd>${fmt(FC.stops, 1)} in 90 days</dd>
  </dl>
  <div class="shares">${sh.map(([k, v]) => `<i title="${SHARE_NAMES[k]} ${fmt(v * 100, 0)} %" style="width:${v * 100}%;background:${SHARE_COLORS[k]}"></i>`).join("")}</div>
  <div class="legend">${sh.map(([k, v]) => `<span style="--c:${SHARE_COLORS[k]}">${SHARE_NAMES[k]} ${fmt(v * 100, 0)} %</span>`).join("")}</div>
  <p class="note">20 runs × 90 days at the current speed, shift pattern and haulage. Best values are medians over the runs. Downtime distributions from a 6.88 m metro EPB (Moosazadeh et al. 2018). Ring times are drawn ring by ring, so whole fast days like Crossrail's best are not reproduced.</p>`;
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
