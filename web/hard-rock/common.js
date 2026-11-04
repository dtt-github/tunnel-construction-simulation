// Shared parts of the hard-rock TBM demos (open gripper and double shield): scene, cut-away planes, helpers, the
// disc cutterhead, muck chute and belts, backup gantries, rock along the drive, and labels.
//
// Frame: metres, Y up, tunnel axis at y = 0. The machine stays at the origin with the cutter tips at z = 0 and the
// machine along +z; the world (rock, support, lining) moves by +chainage, so the drive heads towards -z.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

export { THREE };

// three.js keeps the side a clipping plane's normal points to (signed distance >= 0). CUT keeps the far (x > 0) half,
// so the views from -x look into the machine; the rock tube is kept behind the face (z > 0), the rock block ahead of it.
export const CUT = new THREE.Plane(new THREE.Vector3(1, 0, 0), 0);
export const BEHIND_FACE = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
export const AHEAD_OF_FACE = new THREE.Plane(new THREE.Vector3(0, 0, -1), 0);

export const mat = (color, o = {}) => new THREE.MeshStandardMaterial({ color, metalness: 0.5, roughness: 0.5, ...o });
export const steel = mat(0x8b939b, { metalness: 0.7, roughness: 0.35 });
export const dark = mat(0x3a3f45, { metalness: 0.6 });
export const yellow = mat(0xd9a400);
export const alongZ = (g) => g.rotateX(Math.PI / 2);
export const cyl = (r, len, m, seg = 32) => new THREE.Mesh(alongZ(new THREE.CylinderGeometry(r, r, len, seg)), m);
export const box = (w, h, d, m) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
/** (x, y) at radius r and angle aDeg measured from the crown, positive towards +x. */
export const polar = (r, aDeg) => [r * Math.sin((aDeg * Math.PI) / 180), r * Math.cos((aDeg * Math.PI) / 180)];
/** A cylindrical shell sector between angles from the crown (degrees), along z0..z1. */
export function shell(r, aFrom, aTo, z0, z1, m) {
  const g = new THREE.CylinderGeometry(r, r, z1 - z0, 48, 1, true, (aFrom * Math.PI) / 180, ((aTo - aFrom) * Math.PI) / 180);
  g.rotateX(Math.PI / 2);
  const mesh = new THREE.Mesh(g, m);
  mesh.position.z = (z0 + z1) / 2;
  return mesh;
}

// ---------------------------------------------------------------- scene, camera views, labels
export function createScene(views) {
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
  const lamp = new THREE.PointLight(0xfff1d6, 30, 25);
  lamp.position.set(-1, 2, 6);
  scene.add(lamp);

  let camAnim = null;
  const setView = (name) => {
    const v = views[name];
    camAnim = { t: 0, p0: camera.position.clone(), t0: controls.target.clone(), p1: new THREE.Vector3(...v.pos), t1: new THREE.Vector3(...v.target) };
    for (const b of document.querySelectorAll("#views button")) b.classList.toggle("on", b.dataset.view === name);
  };
  const first = Object.values(views)[0];
  camera.position.set(...first.pos);
  controls.target.set(...first.target);
  controls.update();
  const viewBar = document.getElementById("views");
  const chk = viewBar.querySelector(".chk");
  for (const [name, v] of Object.entries(views)) {
    const b = document.createElement("button");
    b.dataset.view = name;
    b.textContent = v.title;
    if (v === first) b.classList.add("on");
    b.onclick = () => setView(name);
    viewBar.insertBefore(b, chk);
  }
  const resize = () => {
    renderer.setSize(innerWidth, innerHeight, false);
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
  };
  addEventListener("resize", resize);
  resize();
  const updateCamera = (dt) => {
    if (camAnim) {
      camAnim.t = Math.min(camAnim.t + dt / 0.8, 1);
      const e = camAnim.t * camAnim.t * (3 - 2 * camAnim.t);
      camera.position.lerpVectors(camAnim.p0, camAnim.p1, e);
      controls.target.lerpVectors(camAnim.t0, camAnim.t1, e);
      if (camAnim.t >= 1) camAnim = null;
    }
    controls.update();
  };
  return { renderer, scene, camera, updateCamera };
}

const labelLayer = document.getElementById("labels");
const labels = [];
export function label(text, obj, offset = [0, 0, 0]) {
  const el = document.createElement("div");
  el.textContent = text;
  labelLayer.appendChild(el);
  labels.push({ el, obj, offset: new THREE.Vector3(...offset) });
}
const tmp = new THREE.Vector3();
export function placeLabels(camera, show) {
  labelLayer.style.display = show ? "" : "none";
  if (!show) return;
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

// ---------------------------------------------------------------- cutterhead
/**
 * Flat hard-rock cutterhead with a curved gauge (radius 0.5 m): 19-inch discs with radial axles, tips on the cutting
 * plane z = 0 and about 0.17 m proud of the face plate; centre cluster, face cutters on a spiral, tilted gauge
 * cutters, and buckets with grill bars at the periphery. Returns the rotating group and the depth of the head body.
 */
export function buildCutterhead(parent, { R, centre = 4, gauge = 8, total = 62, buckets = 8, depth = 0.9 }) {
  const head = new THREE.Group();
  parent.add(head);
  const EXPOSE = 0.17, GAUGE_R = 0.5, FACE_Z = EXPOSE;
  const pts = [new THREE.Vector2(0.01, FACE_Z), new THREE.Vector2(R - GAUGE_R, FACE_Z)];
  for (let k = 1; k <= 8; k++) {
    const a = (k / 8) * (Math.PI / 2);
    pts.push(new THREE.Vector2(R - GAUGE_R + GAUGE_R * Math.sin(a), FACE_Z + GAUGE_R * (1 - Math.cos(a))));
  }
  pts.push(new THREE.Vector2(R - 0.02, depth), new THREE.Vector2(0.01, depth));
  head.add(new THREE.Mesh(new THREE.LatheGeometry(pts, 72).rotateX(Math.PI / 2), mat(0x3d434a, { metalness: 0.7, roughness: 0.45, side: THREE.DoubleSide })));
  const discGeo = new THREE.CylinderGeometry(0.2413, 0.2413, 0.05, 24).rotateZ(Math.PI / 2); // axle along x (radial once placed)
  const discMat = mat(0xb7bec6, { metalness: 0.85, roughness: 0.3 });
  const saddleMat = mat(0x24282c);
  const addCutter = (r, aRad) => {
    const g = new THREE.Group();
    g.rotation.z = aRad;
    const holder = new THREE.Group();
    holder.position.set(r, 0, 0);
    const disc = new THREE.Mesh(discGeo, discMat);
    disc.position.z = 0.2413; // tip on the cutting plane
    holder.add(disc);
    const saddle = box(0.22, 0.42, 0.14, saddleMat);
    saddle.position.z = FACE_Z + 0.02;
    holder.add(saddle);
    g.add(holder);
    head.add(g);
  };
  for (let k = 0; k < centre; k++) addCutter(0.18 + k * 0.09, k * Math.PI * 0.5);
  const face = total - centre - gauge;
  for (let k = 0; k < face; k++) addCutter(0.6 + (k / (face - 1)) * (R - GAUGE_R - 0.75), k * 2.399963);
  for (let k = 0; k < gauge; k++) {
    const a = ((k + 1) / (gauge + 1)) * 1.13; // up to ~65 degrees of tilt on the gauge curve
    const g = new THREE.Group();
    g.rotation.z = k * ((2 * Math.PI) / gauge) + 0.2;
    const holder = new THREE.Group();
    holder.position.set(R - GAUGE_R + GAUGE_R * Math.sin(a) - 0.05, 0, FACE_Z + GAUGE_R * (1 - Math.cos(a)) - 0.12);
    holder.rotation.y = -a;
    holder.add(new THREE.Mesh(discGeo, discMat));
    g.add(holder);
    head.add(g);
  }
  for (let k = 0; k < buckets; k++) {
    const g = new THREE.Group();
    g.rotation.z = (k / buckets) * Math.PI * 2 + Math.PI / buckets;
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
  return head;
}

// ---------------------------------------------------------------- rock along the drive
/** Rock tube and the translucent rock ahead of the face. Zones flagged `closes` are built from 1 m rings whose radius
 * the caller shrinks with the computed closure; returns those rings as [{ mesh, ch }]. */
export function buildRock(world, zones, R) {
  const rings = [];
  for (const z of zones) {
    const len = z.to - z.from;
    const rockMat = new THREE.MeshStandardMaterial({ color: z.color, roughness: 1, side: THREE.DoubleSide, clippingPlanes: [CUT, BEHIND_FACE] });
    if (z.closes) {
      const geo = alongZ(new THREE.CylinderGeometry(R, R, 1.0, 64, 1, true));
      for (let ch = z.from; ch < z.to; ch += 1) {
        const ring = new THREE.Mesh(geo, rockMat);
        ring.position.z = -(ch + 0.5);
        world.add(ring);
        rings.push({ mesh: ring, ch: ch + 0.5 });
      }
    } else {
      const tube = new THREE.Mesh(alongZ(new THREE.CylinderGeometry(R, R, len, 64, 1, true)), rockMat);
      tube.position.z = -(z.from + len / 2);
      world.add(tube);
    }
    const ahead = box(14, 14, len, new THREE.MeshStandardMaterial({ color: z.color, roughness: 1, transparent: true, opacity: 0.22, depthWrite: false,
      clippingPlanes: [AHEAD_OF_FACE, CUT] }));
    ahead.position.z = -(z.from + len / 2);
    world.add(ahead);
  }
  return rings;
}

// ---------------------------------------------------------------- backup
/** Gantries on rails, backup conveyor, transfer belt, power and ventilation. Returns the rail level. */
export function buildBackup(machine, { railY, zStart, beltY, count = 6, extra = () => {} }) {
  for (const x of [-1.1, 1.1]) {
    const rail = box(0.08, 0.12, 120, steel);
    rail.position.set(x, railY, zStart + 50);
    machine.add(rail);
  }
  const gantryMat = mat(0x4f7f5a, { roughness: 0.6, clippingPlanes: [CUT] });
  for (let k = 0; k < count; k++) {
    const z = zStart + 2 + k * 13;
    const g = new THREE.Group();
    g.position.z = z + 6;
    for (const x of [-2.6, 2.6]) {
      for (const dz of [-5.6, 5.6]) { const post = box(0.25, 4.2, 0.25, gantryMat); post.position.set(x, railY + 2.2, dz); g.add(post); }
      for (const y of [0.5, 4.2]) { const r = box(0.2, 0.25, 12, gantryMat); r.position.set(x, railY + y, 0); g.add(r); }
    }
    const deck = box(5.4, 0.12, 12, gantryMat);
    deck.position.y = railY + 4.3;
    g.add(deck);
    machine.add(g);
    extra(k, z, g);
  }
  const conveyorY = railY + 4.6;
  const bconv = box(1.0, 0.12, 80, dark);
  bconv.position.set(0, conveyorY, zStart + 40);
  machine.add(bconv);
  label("Backup conveyor", bconv, [0, 0.5, -24]);
  const transfer = box(1.2, 0.12, 4.5, dark);
  transfer.position.set(0, (beltY + conveyorY) / 2, zStart + 1.8);
  transfer.rotation.x = -Math.atan2(conveyorY - beltY, 4.5);
  machine.add(transfer);
  const duct = cyl(0.65, 80, new THREE.MeshStandardMaterial({ color: 0xe8e4d6, roughness: 1 }), 16);
  duct.position.set(2.4, 2.6, zStart + 42); // far (kept) side of the cut-away
  machine.add(duct);
  label("Ventilation duct", duct, [0, 0.9, -30]);
  return { conveyorY };
}

// ---------------------------------------------------------------- muck on the belts
/** Muck chunks: spawn at the chute, ride the machine belt, the transfer and the backup conveyor at 2.5 m/s. */
export function createMuck(machine, { zChute, beltY, zBeltEnd, conveyorY }) {
  const MAX = 600;
  const muck = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(0.07, 0), new THREE.MeshStandardMaterial({ color: 0x77706a, roughness: 1, flatShading: true }), MAX);
  muck.count = 0;
  muck.frustumCulled = false;
  machine.add(muck);
  const zs = [], xs = [], m4 = new THREE.Matrix4();
  let debt = 0;
  return {
    add(looseM3) { debt = Math.min(debt + looseM3, 1); },
    update(dt) {
      const spawn = Math.min(Math.floor(debt / 0.05), 8);
      debt -= spawn * 0.05;
      for (let k = 0; k < spawn && zs.length < MAX; k++) { zs.push(zChute + Math.random() * 0.4); xs.push((Math.random() - 0.5) * 0.7); }
      let n = 0;
      for (let k = 0; k < zs.length; k++) {
        zs[k] += 2.5 * dt;
        if (zs[k] > zBeltEnd + 78) continue;
        zs[n] = zs[k]; xs[n] = xs[k];
        const z = zs[n];
        const y = z < zBeltEnd ? beltY + 0.12 : z < zBeltEnd + 3.8 ? beltY + 0.12 + ((conveyorY - beltY) * (z - zBeltEnd)) / 3.8 : conveyorY + 0.12;
        m4.makeTranslation(xs[n], y, z);
        muck.setMatrixAt(n++, m4);
      }
      zs.length = xs.length = n;
      muck.count = n;
      muck.instanceMatrix.needsUpdate = true;
    },
  };
}

// ---------------------------------------------------------------- console helpers
export const fmt = (v, d = 1) => (Number.isFinite(v) ? v.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d }) : "—");
export const dl = (el, rows) => { el.innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join(""); };
