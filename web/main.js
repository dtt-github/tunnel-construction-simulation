// Phase 1 skeleton: hard-rock single-shield TBM driven by analytical models in the browser.
// - CSM disc-cutter model -> penetration, ROP, torque, power (models/js/csm.js)
// - Hoek-Brown / GSI -> rock-mass parameters per geology zone (models/js/hoek_brown.js)
// - Boring / ring-build cycle with 6-segment rings
// - Jolt rigid bodies for the muck falling from the belt into muck cars (real-time, visual-grade)
//
// Frame: metres, Y up. The TBM stays at the origin with its face at z = 0 and the shield along +z;
// the world (rock, rings) moves by +chainage, so excavation direction is -z.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import initJolt from "https://cdn.jsdelivr.net/npm/jolt-physics@1.1.1/dist/jolt-physics.wasm-compat.js";
import { tbmPerformance, hoekBrown, DEFAULT_CUTTER } from "../models/js/index.js";

// ---------------------------------------------------------------- scenario
// Illustrative alignment. Intact values within published ranges for these rock types
// (e.g. Hoek & Brown 1997 mi table); not a real project.
const SCENARIO = {
  machine: { diameter_m: 7.0, n_cutters: 50, max_torque_knm: 4200, shield_length_m: 10.6, ring_width_m: 1.5, ring_build_min: 25 },
  zones: [
    { name: "Granite", from: 0, to: 45, ucs: 180, bts: 12, gsi: 75, mi: 32, ei: 60000, color: 0x8d7f78 },
    { name: "Fault zone (crushed granite)", from: 45, to: 62, ucs: 40, bts: 4, gsi: 30, mi: 20, ei: 15000, color: 0x6b4f3a },
    { name: "Gneiss", from: 62, to: 140, ucs: 140, bts: 10, gsi: 60, mi: 28, ei: 50000, color: 0x5f6b72 },
    { name: "Quartzite", from: 140, to: 220, ucs: 230, bts: 15, gsi: 70, mi: 20, ei: 70000, color: 0xa79b86 },
  ],
};
const M = SCENARIO.machine;
const R = M.diameter_m / 2;
const zoneAt = (ch) => SCENARIO.zones.find((z) => ch >= z.from && ch < z.to) ?? SCENARIO.zones.at(-1);

// ---------------------------------------------------------------- renderer
const canvas = document.getElementById("view");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.localClippingEnabled = true;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x15171a);
const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 500);
camera.position.set(22, 10, -8);
const controls = new OrbitControls(camera, canvas);
controls.target.set(0, -0.5, 8);
controls.update();
scene.add(new THREE.HemisphereLight(0xdfe7ef, 0x2a2420, 1.2));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(10, 20, -15);
scene.add(sun);

function resize() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

// ---------------------------------------------------------------- world (moves with chainage)
const world = new THREE.Group();
scene.add(world);
// Rock ahead of the face (translucent, so the cutterhead stays visible); the shield is cut open on +x.
const clip = [new THREE.Plane(new THREE.Vector3(0, 0, -1), 0), new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0)];
for (const z of SCENARIO.zones) {
  const len = z.to - z.from;
  const box = new THREE.Mesh(
    new THREE.BoxGeometry(18, 14, len),
    new THREE.MeshStandardMaterial({ color: z.color, roughness: 0.95, clippingPlanes: [clip[0]], transparent: true, opacity: 0.45, depthWrite: false }),
  );
  box.position.set(0, 0, -(z.from + len / 2));
  world.add(box);
}
const ringGroup = new THREE.Group();
world.add(ringGroup);

// ---------------------------------------------------------------- machine (fixed at origin)
const steel = new THREE.MeshStandardMaterial({ color: 0xd9a400, metalness: 0.6, roughness: 0.45 });
const dark = new THREE.MeshStandardMaterial({ color: 0x3a3f45, metalness: 0.7, roughness: 0.4 });
const alongZ = (g) => g.rotateX(Math.PI / 2);

const cutterhead = new THREE.Group();
cutterhead.add(new THREE.Mesh(alongZ(new THREE.CylinderGeometry(R, R, 0.6, 64)), steel));
const cutterGeo = alongZ(new THREE.CylinderGeometry(0.24, 0.24, 0.12, 20)).rotateY(Math.PI / 2);
for (let k = 0; k < M.n_cutters; k++) {
  // Spiral layout at roughly constant radial spacing; gauge cutters near the rim.
  const r = Math.min(R - 0.2, 0.25 + (k / (M.n_cutters - 1)) * (R - 0.35));
  const a = k * 2.399963; // golden angle
  const c = new THREE.Mesh(cutterGeo, dark);
  c.position.set(r * Math.cos(a), r * Math.sin(a), -0.33);
  c.rotation.z = a;
  cutterhead.add(c);
}
cutterhead.position.z = 0.3;
scene.add(cutterhead);

const shield = new THREE.Mesh(
  alongZ(new THREE.CylinderGeometry(R - 0.02, R - 0.05, M.shield_length_m - 0.6, 64, 1, true)),
  new THREE.MeshStandardMaterial({ color: 0xc89200, metalness: 0.5, roughness: 0.5, side: THREE.DoubleSide, clippingPlanes: [clip[1]] }),
);
shield.position.z = 0.6 + (M.shield_length_m - 0.6) / 2;
scene.add(shield);

// Belt conveyor (visual) from the screw/hopper to the discharge above the muck car.
const belt = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.15, 12), dark);
belt.position.set(0, 0.9, 15);
belt.rotation.x = -0.06;
scene.add(belt);

// ---------------------------------------------------------------- rings
const SEGMENTS = 6;
const RI = R - 0.55, RO = R - 0.2;
const segGeo = (() => {
  // Solid annular sector (one segment), extruded along z over the ring width, with a small joint gap.
  const gap = 0.004, a0 = gap, a1 = (2 * Math.PI) / SEGMENTS - gap;
  const s = new THREE.Shape();
  s.absarc(0, 0, RO, a0, a1, false);
  s.absarc(0, 0, RI, a1, a0, true);
  s.closePath();
  const g = new THREE.ExtrudeGeometry(s, { depth: M.ring_width_m - 0.01, bevelEnabled: false, curveSegments: 16 });
  return g.translate(0, 0, -(M.ring_width_m - 0.01) / 2);
})();
const segMats = [0xb9b9b4, 0x9d9d98].map((color) => new THREE.MeshStandardMaterial({ color, roughness: 0.9, side: THREE.DoubleSide }));
function addSegment(ring, i, chainage) {
  const odd = (n) => ((n % 2) + 2) % 2; // ring indices of the launch section are negative
  const m = new THREE.Mesh(segGeo, segMats[odd(ring + i)]);
  m.rotation.z = (i * 2 * Math.PI) / SEGMENTS + odd(ring) * (Math.PI / SEGMENTS); // staggered joints
  // Built inside the tail: TBM-local z = shield_length - ring_width/2 -> group-local z = that - chainage.
  m.position.z = M.shield_length_m - M.ring_width_m / 2 - 0.2 - chainage;
  ringGroup.add(m);
}

// ---------------------------------------------------------------- Jolt (muck)
const Jolt = await initJolt();
const LAYER_STATIC = 0, LAYER_MOVING = 1;
const settings = new Jolt.JoltSettings();
const objectFilter = new Jolt.ObjectLayerPairFilterTable(2);
objectFilter.EnableCollision(LAYER_STATIC, LAYER_MOVING);
objectFilter.EnableCollision(LAYER_MOVING, LAYER_MOVING);
const bpInterface = new Jolt.BroadPhaseLayerInterfaceTable(2, 2);
bpInterface.MapObjectToBroadPhaseLayer(LAYER_STATIC, new Jolt.BroadPhaseLayer(0));
bpInterface.MapObjectToBroadPhaseLayer(LAYER_MOVING, new Jolt.BroadPhaseLayer(1));
settings.mObjectLayerPairFilter = objectFilter;
settings.mBroadPhaseLayerInterface = bpInterface;
settings.mObjectVsBroadPhaseLayerFilter = new Jolt.ObjectVsBroadPhaseLayerFilterTable(bpInterface, 2, objectFilter, 2);
const jolt = new Jolt.JoltInterface(settings);
Jolt.destroy(settings);
const bodyInterface = jolt.GetPhysicsSystem().GetBodyInterface();

function staticBox(half, pos, mat) {
  const shape = new Jolt.BoxShape(new Jolt.Vec3(...half), 0.02, null);
  const bcs = new Jolt.BodyCreationSettings(shape, new Jolt.RVec3(...pos), new Jolt.Quat(0, 0, 0, 1), Jolt.EMotionType_Static, LAYER_STATIC);
  const body = bodyInterface.CreateBody(bcs);
  Jolt.destroy(bcs);
  bodyInterface.AddBody(body.GetID(), Jolt.EActivation_DontActivate);
  if (mat) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(half[0] * 2, half[1] * 2, half[2] * 2), mat);
    mesh.position.set(...pos);
    scene.add(mesh);
  }
}
// Invert (track bed) and an open muck car below the belt discharge.
const CAR = { z: 23.2, floor: -2.2, len: 3.6, w: 1.5, h: 1.1 };
staticBox([2.5, 0.1, 30], [0, -R + 0.45, 30], new THREE.MeshStandardMaterial({ color: 0x4b4640, roughness: 1 }));
const carMat = new THREE.MeshStandardMaterial({ color: 0x2f6f9f, metalness: 0.4, roughness: 0.6 });
staticBox([CAR.w / 2, 0.05, CAR.len / 2], [0, CAR.floor, CAR.z], carMat);
staticBox([0.05, CAR.h / 2, CAR.len / 2], [-CAR.w / 2, CAR.floor + CAR.h / 2, CAR.z], carMat);
staticBox([0.05, CAR.h / 2, CAR.len / 2], [CAR.w / 2, CAR.floor + CAR.h / 2, CAR.z], carMat);
staticBox([CAR.w / 2, CAR.h / 2, 0.05], [0, CAR.floor + CAR.h / 2, CAR.z - CAR.len / 2], carMat);
staticBox([CAR.w / 2, CAR.h / 2, 0.05], [0, CAR.floor + CAR.h / 2, CAR.z + CAR.len / 2], carMat);

const CAR_CAPACITY_M3 = 14; // loose muck per car
const CHUNKS_PER_CAR = 60;
const BULKING = 1.6;
const muckMat = new THREE.MeshStandardMaterial({ color: 0x7a6e64, roughness: 1, flatShading: true });
const chunkGeo = new THREE.DodecahedronGeometry(0.17, 0);
const chunks = [];
function spawnChunk() {
  const s = 0.12 + Math.random() * 0.06;
  const shape = new Jolt.SphereShape(s);
  const pos = new Jolt.RVec3((Math.random() - 0.5) * 0.3, 1.2, 21.0);
  const bcs = new Jolt.BodyCreationSettings(shape, pos, new Jolt.Quat(0, 0, 0, 1), Jolt.EMotionType_Dynamic, LAYER_MOVING);
  bcs.mFriction = 0.9;
  bcs.mRestitution = 0.05;
  const body = bodyInterface.CreateBody(bcs);
  Jolt.destroy(bcs);
  bodyInterface.AddBody(body.GetID(), Jolt.EActivation_Activate);
  bodyInterface.SetLinearVelocity(body.GetID(), new Jolt.Vec3(0, 0, 1.8));
  const mesh = new THREE.Mesh(chunkGeo, muckMat);
  mesh.scale.setScalar(s / 0.17);
  scene.add(mesh);
  chunks.push({ body, mesh });
}
function clearChunks() {
  for (const { body, mesh } of chunks) {
    bodyInterface.RemoveBody(body.GetID());
    bodyInterface.DestroyBody(body.GetID());
    scene.remove(mesh);
  }
  chunks.length = 0;
}

// ---------------------------------------------------------------- simulation state
const ui = Object.fromEntries(["thrust", "rpm", "timescale", "thrustOut", "rpmOut", "tsOut", "machine", "ground", "alarms", "pause", "reset"].map((id) => [id, document.getElementById(id)]));
let state;
function reset() {
  state = { chainage: 0, stroke: 0, mode: "BORING", buildT: 0, ring: 0, segPlaced: 0, simTime: 0, carsFilled: 0, chunkDebt: 0, perf: null, paused: false };
  ringGroup.clear();
  clearChunks();
  // Pre-built rings behind the TBM (launch section), so the lining is visible from the start.
  for (let k = 6; k >= 1; k--) for (let i = 0; i < SEGMENTS; i++) addSegment(-k, i, -k * M.ring_width_m);
}
reset();
ui.reset.onclick = reset;
ui.pause.onclick = () => { state.paused = !state.paused; ui.pause.textContent = state.paused ? "Resume" : "Pause"; };

const hbCache = new Map();
const rockMass = (z) => hbCache.get(z) ?? hbCache.set(z, hoekBrown(z.gsi, z.mi, z.ucs, 0, z.ei)).get(z);

function step(dtReal) {
  const thrust = +ui.thrust.value, rpm = +ui.rpm.value, ts = +ui.timescale.value;
  const dt = dtReal * ts; // simulated seconds
  state.simTime += dt;
  const zone = zoneAt(state.chainage);
  state.perf = tbmPerformance({
    thrust_kn: thrust, rpm, n_cutters: M.n_cutters, head_diameter_m: M.diameter_m,
    ucs_mpa: zone.ucs, bts_mpa: zone.bts, max_torque_knm: M.max_torque_knm,
  });
  if (state.mode === "BORING") {
    const adv = Math.min((state.perf.rop_m_h / 3600) * dt, M.ring_width_m - state.stroke);
    state.chainage += adv;
    state.stroke += adv;
    cutterhead.rotation.z -= (rpm / 60) * 2 * Math.PI * dtReal; // shown at real speed
    // Muck: solid volume -> loose volume -> chunks (one chunk = car capacity / chunks per car)
    state.chunkDebt += (Math.PI * R * R * adv * BULKING) / (CAR_CAPACITY_M3 / CHUNKS_PER_CAR);
    if (state.stroke >= M.ring_width_m - 1e-9) { state.mode = "RING BUILD"; state.buildT = 0; state.segPlaced = 0; }
  } else {
    state.buildT += dt;
    const due = Math.min(SEGMENTS, Math.floor((state.buildT / (M.ring_build_min * 60)) * SEGMENTS) + 1);
    while (state.segPlaced < due) addSegment(state.ring, state.segPlaced++, state.chainage);
    if (state.buildT >= M.ring_build_min * 60) { state.mode = "BORING"; state.stroke = 0; state.ring++; }
  }
  // Spawn at most a few chunks per frame; the backlog carries over.
  for (let n = 0; n < 4 && state.chunkDebt >= 1; n++, state.chunkDebt--) spawnChunk();
  if (chunks.length >= CHUNKS_PER_CAR) { state.carsFilled++; clearChunks(); }
  world.position.z = state.chainage;
}

// ---------------------------------------------------------------- HUD
const fmt = (v, d = 1) => v.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const hms = (s) => `${Math.floor(s / 3600)} h ${String(Math.floor((s % 3600) / 60)).padStart(2, "0")} min`;
function dl(el, rows) { el.innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join(""); }
function hud() {
  const p = state.perf, zone = zoneAt(state.chainage), hb = rockMass(zone);
  ui.thrustOut.textContent = `${fmt(+ui.thrust.value, 0)} kN`;
  ui.rpmOut.textContent = `${fmt(+ui.rpm.value)} rpm`;
  ui.tsOut.textContent = `×${ui.timescale.value}`;
  dl(ui.machine, [
    ["Mode", state.mode],
    ["Chainage", `${fmt(state.chainage, 2)} m`],
    ["Rings built", state.ring],
    ["Stroke", `${fmt(state.stroke * 1000, 0)} / ${M.ring_width_m * 1000} mm`],
    ["Penetration", `${fmt(p.penetration_mm_rev, 2)} mm/rev`],
    ["Rate of penetration", `${fmt(p.rop_m_h, 2)} m/h`],
    ["Normal load / cutter", `${fmt(p.normal_per_cutter_kn, 0)} kN`],
    ["Cutterhead torque", `${fmt(p.cutterhead_torque_knm, 0)} kNm`],
    ["Cutterhead power", `${fmt(p.cutterhead_power_kw, 0)} kW`],
    ["Muck cars filled", state.carsFilled],
    ["Simulated time", hms(state.simTime)],
  ]);
  const alarms = [];
  if (p.cutter_overloaded) alarms.push(`Cutter overload: ${fmt(p.normal_per_cutter_kn, 0)} kN > ${DEFAULT_CUTTER.max_load_kn} kN rated`);
  if (p.limited_by === "torque") alarms.push(`Torque-limited at ${M.max_torque_knm} kNm: excess thrust is not cutting`);
  if (zone.gsi < 35) alarms.push("Poor rock mass (GSI < 35): face/crown instability and overbreak risk");
  ui.alarms.innerHTML = alarms.length ? alarms.map((a) => `<div>${a}</div>`).join("") : `<div class="ok">Within limits</div>`;
  dl(ui.ground, [
    ["Zone", zone.name],
    ["Intact UCS / BTS", `${zone.ucs} / ${zone.bts} MPa`],
    ["GSI, mi", `${zone.gsi}, ${zone.mi}`],
    ["mb, s, a", `${fmt(hb.mb, 2)}, ${hb.s.toExponential(2)}, ${fmt(hb.a, 3)}`],
    ["Rock-mass strength σcm", `${fmt(hb.sigma_cm, 1)} MPa`],
    ["Rock-mass modulus Erm", `${fmt(hb.e_rm / 1000, 1)} GPa`],
    ["Next zone", (() => { const n = SCENARIO.zones.find((z) => z.from > state.chainage); return n ? `${n.name} in ${fmt(n.from - state.chainage, 1)} m` : "—"; })()],
  ]);
}

// ---------------------------------------------------------------- loop
let last = performance.now(), hudT = 0;
renderer.setAnimationLoop((now) => {
  const dtReal = Math.min((now - last) / 1000, 1 / 20);
  last = now;
  if (!state.paused) {
    step(dtReal);
    jolt.Step(dtReal, dtReal > 1 / 55 ? 2 : 1);
    for (const { body, mesh } of chunks) {
      const p = body.GetPosition(), q = body.GetRotation();
      mesh.position.set(p.GetX(), p.GetY(), p.GetZ());
      mesh.quaternion.set(q.GetX(), q.GetY(), q.GetZ(), q.GetW());
    }
  }
  if ((hudT += dtReal) > 0.1 || !state.perf) { hudT = 0; if (state.perf) hud(); }
  renderer.render(scene, camera);
});
step(0);
hud();
