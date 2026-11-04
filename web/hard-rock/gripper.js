// Open gripper (main beam) TBM: roof shield and fingers, main beam, gripper carrier with propel cylinders, rear legs;
// L1 rock bolts, mesh and ring beams and L2 shotcrete by RMR class; invert segments. Method card: open gripper in
// docs/research/methods-reference.md; preset "hard-rock-main-beam-9.5m" (models/presets/machine-classes.json).

import { rmrClass } from "../../models/js/index.js";
import { THREE, CUT, mat, steel, dark, yellow, cyl, box, polar, shell, label, buildCutterhead, buildBackup, createMuck } from "./common.js";

export const M = {
  kind: "gripper",
  title: "Hard-rock open gripper TBM · Ø 9.58 m",
  D: 9.58, // m, Gotthard-class main beam (preset, trade press, unverified)
  torque: 5290, power: 3500, // kNm, kW (preset, unverified)
  nCutters: 62, // assumed: ~85 mm spacing over the face, plus centre and gauge cutters
  stroke: 1.8, // m, assumed (1.2-1.8 m reported only informally)
  regripMin: 4, // min, Farrokh (2018): 2-6 min per regrip
  utilMachine: () => "open",
  limits: [
    "Machine torque, power and thrust are the Gotthard-class preset values, which come from trade press and are not yet verified. The number of cutters (62) and the stroke (1.8 m) are assumptions.",
    "Support patterns follow the RMR table (Bieniawski 1989); per-bolt installation times are not modelled. The final cast-in-place lining is placed after or behind the drive and is not shown.",
  ],
};
const R = M.D / 2;

export const VIEWS = {
  machine: { title: "Machine", pos: [-22, 7, -6], target: [0, -0.5, 14] },
  face: { title: "Cutterhead", pos: [-6, 2.5, -9], target: [0, 0, 0.3] },
  l1: { title: "L1 support", pos: [-11, 3, 0], target: [0, 1.5, 6] },
  gripper: { title: "Grippers", pos: [-9, 6, 4], target: [0, -0.8, 12] },
  l2: { title: "Backup (L2)", pos: [-13, 3, 22], target: [0, 0.5, 32] },
};

// Support pattern per RMR class (Bieniawski 1989): bolt rows along the tunnel, bolts per row over the crown arc, mesh
// arc, ring-beam spacing, shotcrete thickness in the crown (L2). Visual translation of the table.
const PATTERN = {
  I: { rowSpacing: Infinity, bolts: 0, arc: 0, mesh: 0, beams: 0, shot: 0 },
  II: { rowSpacing: 2.5, bolts: 3, arc: 60, mesh: 0, beams: 0, shot: 0.05 },
  III: { rowSpacing: 1.75, bolts: 9, arc: 200, mesh: 120, beams: 0, shot: 0.075 },
  IV: { rowSpacing: 1.25, bolts: 11, arc: 240, mesh: 240, beams: 1.5, shot: 0.125 },
  V: { rowSpacing: 1.0, bolts: 13, arc: 260, mesh: 260, beams: 0.75, shot: 0.175 },
};
const Z_HEAD = 0.9, Z_SHIELD1 = 4.2, Z_L1 = 5.2, Z_GRIP = 10.5, Z_LEGS = 19.5, Z_BEAM1 = 21, Z_L2 = 34, Z_INVERT = 27;
const BELT_Y = 0.25;

export function build(machine, world) {
  const head = buildCutterhead(machine, { R, total: M.nCutters, depth: Z_HEAD });
  const chute = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.35, 1.0, 24, 1, true).rotateX(Math.PI / 2), mat(0x6e5d3a, { side: THREE.DoubleSide }));
  chute.position.set(0, 0.6, Z_HEAD + 0.6);
  machine.add(chute);
  label("Muck ring and chute", chute, [0, 1.0, 0]);

  const support = cyl(2.6, Z_SHIELD1 - Z_HEAD, dark, 40);
  support.position.z = (Z_HEAD + Z_SHIELD1) / 2;
  machine.add(support);
  label("Main bearing and drive motors", support, [0, -2.9, 0]);
  const shieldMat = mat(0xc89200, { side: THREE.DoubleSide, clippingPlanes: [CUT] });
  const roof = shell(R - 0.05, -65, 65, Z_HEAD, Z_SHIELD1, shieldMat);
  roof.rotation.z = Math.PI;
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

  const beam = box(1.6, 1.4, Z_BEAM1 - Z_SHIELD1, yellow);
  beam.position.set(0, -0.6, (Z_SHIELD1 + Z_BEAM1) / 2);
  machine.add(beam);
  label("Main beam", beam, [0, -1.0, 2]);
  const belt = box(1.1, 0.12, Z_BEAM1 - Z_HEAD, dark);
  belt.position.set(0, BELT_Y, (Z_HEAD + Z_BEAM1) / 2 + 0.5);
  machine.add(belt);
  label("Machine belt", belt, [0, 0.4, 3]);

  // L1 zone: roof drills, ring-beam erector, mesh handler, probe drill
  const drills = [];
  for (const side of [-1, 1]) {
    const g = new THREE.Group();
    g.position.set(0, 0.6, Z_L1 + (side > 0 ? 0.8 : 0));
    g.add(box(0.2, 0.2, 0.2, mat(0x2f6f9f)));
    const feed = box(0.18, 2.4, 0.18, mat(0x2f6f9f));
    feed.position.y = 1.6;
    g.add(feed);
    const rod = box(0.05, 1.4, 0.05, steel);
    rod.position.y = 3.2;
    g.add(rod);
    g.userData = { side, rod };
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
  probe.add(box(0.18, 0.18, 3.2, mat(0x8a3f2b)));
  probe.position.set(-1.2, R - 0.9, Z_L1 - 0.4);
  probe.rotation.x = -0.12;
  machine.add(probe);
  label("Probe drill (ahead of the face)", probe, [0, 0.5, 0]);

  // gripper carrier with shoes, propel cylinders, rear legs
  const gripper = new THREE.Group();
  machine.add(gripper);
  const carrier = box(3.4, 1.6, 2.6, yellow);
  carrier.position.y = -0.5;
  gripper.add(carrier);
  const grips = [];
  for (const side of [-1, 1]) {
    const c = cyl(0.25, 1, mat(0x5b8db8), 16);
    c.rotation.y = Math.PI / 2;
    gripper.add(c);
    const s = box(0.35, 2.6, 3.2, mat(0x6e7a86));
    gripper.add(s);
    grips.push({ side, cyl: c, shoe: s });
  }
  label("Gripper shoes (react thrust and torque)", gripper, [-R + 0.5, 1.8, 0]);
  const propels = [];
  for (const [x, y] of [[-1.0, 0.3], [1.0, 0.3], [-1.0, -1.2], [1.0, -1.2]]) {
    const c = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 1, 12).rotateX(Math.PI / 2).translate(0, 0, 0.5), mat(0x5b8db8));
    c.position.set(x, y, Z_L1 + 2.6);
    machine.add(c);
    propels.push(c);
  }
  label("Propel (thrust) cylinders", propels[0], [0, 0.4, 2]);
  const legs = [];
  for (let i = 0; i < 2; i++) { const leg = box(0.35, 1, 0.35, mat(0x6e7a86)); machine.add(leg); legs.push(leg); }
  label("Rear legs", legs[0], [0, -0.6, 0]);

  // backup with L2 shotcrete robot and invert segment erector
  const railY = -R + 0.62;
  const { conveyorY } = buildBackup(machine, { railY, zStart: Z_BEAM1, beltY: BELT_Y, extra: (k, z) => {
    if (k === 3) { const tr = box(1.6, 1.4, 3, mat(0x6e7a86)); tr.position.set(-1.6, railY + 5.1, z + 4); machine.add(tr); label("Transformers and hydraulic power", tr, [0, 1, 0]); }
  } });
  const robot = new THREE.Group();
  robot.position.set(0, 1.0, Z_L2);
  robot.add(box(0.6, 0.6, 0.6, mat(0xe9e5dc)));
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
  invertErector.position.set(0, railY + 1.2, Z_INVERT - 1.5);
  machine.add(invertErector);
  label("Invert segment erector", invertErector, [0, 0.6, 0]);
  const muck = createMuck(machine, { zChute: Z_HEAD + 0.6, beltY: BELT_Y, zBeltEnd: Z_BEAM1, conveyorY });

  // world: rock support instances
  const BOLT_MAX = 6000, BEAM_MAX = 600, INV_MAX = 400;
  const bolts = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.05, 0.05, 0.5, 6).translate(0, 0.25, 0), mat(0xc9a227, { metalness: 0.8, clippingPlanes: [CUT] }), BOLT_MAX);
  const plates = new THREE.InstancedMesh(new THREE.BoxGeometry(0.22, 0.03, 0.22), mat(0x8b939b, { clippingPlanes: [CUT] }), BOLT_MAX);
  const beamsI = new THREE.InstancedMesh(new THREE.TorusGeometry(R - 0.12, 0.11, 6, 48, Math.PI * 1.5).rotateZ(-Math.PI * 0.25), mat(0x7a8590, { metalness: 0.6, roughness: 0.4, clippingPlanes: [CUT] }), BEAM_MAX);
  const invI = new THREE.InstancedMesh(new THREE.BoxGeometry(3.6, 0.45, 1.8), mat(0xb0aea6, { roughness: 0.9, clippingPlanes: [CUT] }), INV_MAX);
  // instances are added as the drive advances; their bounds are computed once, so never frustum-cull them
  for (const im of [bolts, plates, beamsI, invI]) { im.count = 0; im.frustumCulled = false; world.add(im); }
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e3 = new THREE.Euler(), v3 = new THREE.Vector3(), s3 = new THREE.Vector3(1, 1, 1);
  const placeBolt = (aDeg, wz) => {
    if (bolts.count >= BOLT_MAX) return;
    const [x, y] = polar(R - 0.02, aDeg);
    q.setFromEuler(e3.set(0, 0, -(aDeg * Math.PI) / 180));
    m4.compose(v3.set(x, y, wz), q, s3);
    bolts.setMatrixAt(bolts.count++, m4);
    plates.setMatrixAt(plates.count++, m4);
  };
  const arcGeoCache = new Map();
  const arcMesh = (kind, arcDeg) => {
    const key = `${kind}|${arcDeg}`;
    if (!arcGeoCache.has(key)) {
      const a = (arcDeg * Math.PI) / 180, r = kind === "mesh" ? R - 0.06 : R - 0.02;
      arcGeoCache.set(key, new THREE.CylinderGeometry(r, r, 1.0, 48, 2, true, -a / 2, a).rotateX(Math.PI / 2).rotateZ(Math.PI));
    }
    return arcGeoCache.get(key);
  };
  const meshMat = new THREE.MeshBasicMaterial({ color: 0x9aa4ae, wireframe: true, clippingPlanes: [CUT] });
  const shotMats = { 0.05: 0xc7c4bb, 0.075: 0xbdbab1, 0.125: 0xb3b0a7, 0.175: 0xa9a69d };
  const pieces = [];
  const addArcPiece = (kind, arcDeg, wz, len, thickness) => {
    const m = kind === "mesh" ? meshMat : new THREE.MeshStandardMaterial({ color: shotMats[thickness] ?? 0xb9b6ad, roughness: 1, side: THREE.DoubleSide, clippingPlanes: [CUT] });
    const piece = new THREE.Mesh(arcMesh(kind, arcDeg), m);
    piece.position.z = wz;
    piece.scale.z = len;
    if (kind === "shot") piece.scale.x = piece.scale.y = 1 - thickness / R;
    world.add(piece);
    pieces.push(piece);
    if (pieces.length > 1400) world.remove(pieces.shift());
  };

  // Support installation as the rock passes the L1 and L2 zones (TBM-local z = chainage - ch_world).
  function installSupport(S, zoneAt) {
    while (S.l1Done < S.chainage - Z_L1) {
      const ch = S.l1Done + 0.5, p = PATTERN[rmrClass(zoneAt(ch).rmr).class];
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
    while (S.l2Done < S.chainage - Z_L2) {
      const ch = S.l2Done + 0.5, p = PATTERN[rmrClass(zoneAt(ch).rmr).class];
      if (p.shot > 0) addArcPiece("shot", Math.max(p.arc, 120), -ch, 1.02, p.shot);
      S.l2Done += 1;
    }
    while (S.invDone < S.chainage - Z_INVERT && invI.count < INV_MAX) {
      m4.compose(v3.set(0, -R + 0.32, -(S.invDone + 0.9)), q.identity(), s3);
      invI.setMatrixAt(invI.count++, m4);
      S.invDone += 1.8;
    }
    for (const im of [bolts, plates, beamsI, invI]) im.instanceMatrix.needsUpdate = true;
  }

  return {
    muck,
    reset(S, zoneAt) {
      for (const p of pieces) world.remove(p);
      pieces.length = 0;
      for (const im of [bolts, plates, beamsI, invI]) im.count = 0;
      Object.assign(S, { l1Done: S.chainage - 60, l2Done: S.chainage - 60, invDone: S.chainage - 60, nextRow: S.chainage - 60, nextBeam: S.chainage - 60 });
      installSupport(S, zoneAt); // the 60 m behind the start are already bored and supported
    },
    // Cycle: BORING one stroke on the grippers -> REGRIP -> STOPPED for this stroke's other downtime.
    step(S, dt, ctx) {
      if (S.mode === "BORING") {
        ctx.bore(Math.min((S.perf.rop_m_h / 3600) * dt, M.stroke - S.stroke));
        if (S.stroke >= M.stroke - 1e-9) { S.mode = "REGRIP"; S.regripT = 0; }
      } else if (S.mode === "REGRIP") {
        S.regripT += dt;
        if (S.regripT >= M.regripMin * 60) { ctx.startStop(["boring", "regrip"]); S.stroke = 0; }
      } else ctx.stopStep(dt);
    },
    afterStep(S, zoneAt) { installSupport(S, zoneAt); },
    modeText(S, fmtv) {
      return S.mode === "BORING" ? `BORING (stroke ${fmtv(S.stroke, 2)} of ${M.stroke} m)` : S.mode === "REGRIP" ? `REGRIP (${fmtv(M.regripMin * 60 - S.regripT, 0)} s left)` : null;
    },
    supportRows(zone) {
      const c = rmrClass(zone.rmr);
      return [["Bolts", c.bolts], ["Shotcrete", c.shotcrete], ["Steel ribs", c.ribs]];
    },
    alarms(zone) {
      const c = rmrClass(zone.rmr);
      return zone.rmr < 40 ? [`${c.name} rock (RMR ${zone.rmr}): heavy support at L1, ring beams, low wall strength under the grippers`] : [];
    },
    animate(S, dtReal, zoneAt) {
      head.rotation.z -= ((S.mode === "BORING" ? S.rpm : 0) / 60) * 2 * Math.PI * dtReal;
      let gz = Z_GRIP + S.stroke, legDown = 0, gripIn = 0;
      if (S.mode === "REGRIP") {
        const f = S.regripT / (M.regripMin * 60);
        legDown = f < 0.2 ? f / 0.2 : f > 0.85 ? (1 - f) / 0.15 : 1;
        gripIn = f < 0.2 ? 0 : f < 0.35 ? (f - 0.2) / 0.15 : f < 0.75 ? 1 : f < 0.9 ? 1 - (f - 0.75) / 0.15 : 0;
        gz = Z_GRIP + M.stroke * (f < 0.35 ? 1 : f < 0.75 ? 1 - (f - 0.35) / 0.4 : 0);
      }
      gripper.position.z = gz;
      for (const g of grips) {
        g.shoe.position.set(g.side * (R - 0.25 - 0.35 * gripIn), -0.2, 0);
        const len = R - 0.45 - 0.35 * gripIn - 1.7;
        g.cyl.position.set(g.side * (1.7 + len / 2), -0.3, 0);
        g.cyl.scale.y = len;
      }
      for (const c of propels) c.scale.z = Math.max(gz - (Z_L1 + 2.6) - 1.0, 0.2);
      legs.forEach((leg, i) => { const len = 1.2 + 0.9 * legDown; leg.scale.y = len; leg.position.set(i ? 1.2 : -1.2, -1.3 - len / 2, Z_LEGS); });
      const p1 = PATTERN[rmrClass(zoneAt(S.chainage - Z_L1).rmr).class], p2 = PATTERN[rmrClass(zoneAt(S.chainage - Z_L2).rmr).class];
      const tt = performance.now() / 1000;
      for (const d of drills) {
        const active = p1.bolts > 0;
        d.rotation.z = active ? d.userData.side * (0.2 + 0.5 * Math.abs(Math.sin(tt * 0.3 + d.userData.side))) : d.userData.side * 0.15;
        d.userData.rod.scale.y = active ? 0.6 + 0.4 * Math.abs(Math.sin(tt * 0.9)) : 0.3;
      }
      robot.rotation.z = p2.shot > 0 ? Math.sin(tt * 0.7) * 0.9 : 0;
      spray.visible = p2.shot > 0 && S.mode !== "STOPPED";
    },
  };
}
