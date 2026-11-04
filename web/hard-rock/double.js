// Double shield (telescopic) TBM: front shield, inner and outer telescopic shields, gripper shield with gripper shoes,
// tailskin with erector; main thrust cylinders (front shield <- gripper shield), auxiliary cylinders on the last ring;
// precast segment rings with pea gravel in the crown and grout in the invert. Method card: double shield in
// docs/research/methods-reference.md; preset "hard-rock-double-shield-10m" (models/presets/machine-classes.json).
//
// Double-shield mode (RMR >= 50): the grippers react the main cylinders while a ring is built in the tailskin at the
// same time; then a regrip pulls the gripper shield up to the front shield. Single-shield mode (RMR < 50, as in
// faults): the telescope stays closed, the auxiliary cylinders push off the last ring, and boring and ring building
// alternate (Herrenknecht double shield product page; Maggio 2020).

import { shieldFriction, SKIN_FRICTION_ROCK } from "../../models/js/index.js";
import { THREE, CUT, mat, steel, dark, yellow, cyl, box, label, buildCutterhead, buildBackup, createMuck } from "./common.js";

export const M = {
  kind: "double",
  title: "Hard-rock double shield TBM · Ø 9.9 m",
  D: 9.9, // m, Follo Line machines (Herrenknecht reference, verified)
  torque: 11115, power: 4550, // kNm, kW (Follo, verified)
  nCutters: 60, centre: 4, gauge: 10, // 19-inch discs: 4 double centre, 46 face, 10 gauge (10.65 m Brenner machine, Maggio 2020)
  stroke: 1.8, // m: one ring width per stroke (Follo rings 1.8 m, verified)
  regripMin: 10, // min: "a few minutes" (Herrenknecht) to 15-30 min (Maggio 2020) per regrip
  ringBuildMin: 30, // min per ring, assumed (no open source; Follo's 14-20 rings a day bounds the whole cycle)
  segThick: 0.32, // m, Guadarrama value from a search snippet (unverified)
  doubleModeMinRmr: 50, // below: single-shield mode (as in the support-downtime model)
  shieldLength: 13.7, // m, sum of the Brenner shield lengths
  overcut: 0.10, // m radial gap between bore and shield, assumed (Ramoni & Anagnostou's example uses 5-15 cm)
  thrustInstalled: 150, // MN, low end of "up to 150-200 MN" for ~10 m shielded TBMs (Ramoni & Anagnostou, VSS 1341)
  utilMachine: () => "double",
  limits: [
    "Machine diameter, torque, power and ring width are the Follo values (verified); shield lengths and cutter layout come from the 10.65 m Brenner machines. Thrust, gripper force and strokes for a 10 m machine are not published; the stroke is taken equal to the ring width.",
    "Ring-build time (30 min) and segment thickness (320 mm) are assumptions; single-shield mode below RMR 50 follows the support-downtime model, not project data.",
  ],
};
const R = M.D / 2, W = M.stroke;
// Shields sit inside the bore by the overcut; the ring leaves a ~0.18 m annulus to the bore (Guadarrama: 9.51 m bore,
// 8.5 m ring inner diameter, 320 mm segments).
const GAP = M.overcut, OD = M.D - 0.37, ID = OD - 2 * M.segThick;

export const VIEWS = {
  machine: { title: "Machine", pos: [-24, 7, -6], target: [0, -0.5, 12] },
  face: { title: "Cutterhead", pos: [-6, 2.5, -9], target: [0, 0, 0.3] },
  telescope: { title: "Telescope and grippers", pos: [-11, 4, 1], target: [0, 0, 6] },
  tail: { title: "Tailskin and rings", pos: [-10, 3, 6], target: [0, -0.5, 11] },
  backup: { title: "Backup", pos: [-13, 3, 18], target: [0, 0.5, 28] },
};

// Shield layout (m behind the cutter tips), lengths from the Brenner machines: front 1.97, inner telescope 2.35,
// outer telescope 2.93, gripper shield 3.98, tailskin 2.48.
const Z_HEAD = 0.9, Z_FRONT0 = 0.15, Z_FRONT1 = Z_FRONT0 + 1.97, Z_INNER1 = Z_FRONT1 + 2.35, Z_GRIP0 = Z_FRONT1 + 2.93;
const L_GRIP = 3.98, L_TAIL = 2.48, Z_RING = Z_GRIP0 + L_GRIP + 0.35; // ring front face inside the tailskin
const Z_BACKUP = Z_GRIP0 + L_GRIP + L_TAIL + 1.5;
const BELT_Y = 0.25;

export function build(machine, world) {
  const head = buildCutterhead(machine, { R, total: M.nCutters, centre: M.centre, gauge: M.gauge, depth: Z_HEAD });
  const chute = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.35, 1.0, 24, 1, true).rotateX(Math.PI / 2), mat(0x6e5d3a, { side: THREE.DoubleSide }));
  chute.position.set(0, 0.6, Z_HEAD + 0.6);
  machine.add(chute);
  label("Muck ring and chute", chute, [0, 1.0, 0]);
  const drive = cyl(2.8, Z_FRONT1 - Z_HEAD, dark, 40);
  drive.position.z = (Z_HEAD + Z_FRONT1) / 2;
  machine.add(drive);
  label("Main bearing and drive motors", drive, [0, -3.1, 0]);

  const shieldMat = mat(0xc89200, { side: THREE.DoubleSide, clippingPlanes: [CUT] });
  const tube = (r, len, m = shieldMat) => new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, 72, 1, true).rotateX(Math.PI / 2), m);
  const front = tube(R - GAP, Z_FRONT1 - Z_FRONT0);
  front.position.z = (Z_FRONT0 + Z_FRONT1) / 2;
  machine.add(front);
  label("Front shield", front, [0, R + 0.4, 0]);
  const inner = tube(R - GAP - 0.1, Z_INNER1 - Z_FRONT1, mat(0xb07d00, { side: THREE.DoubleSide, clippingPlanes: [CUT] }));
  inner.position.z = (Z_FRONT1 + Z_INNER1) / 2;
  machine.add(inner);
  label("Inner telescopic shield", inner, [0, R + 0.2, 0.6]);

  // gripper shield group: moves back relative to the head while boring (it is braced on the rock), forward on regrip
  const gs = new THREE.Group();
  machine.add(gs);
  const outer = tube(R - GAP, 2.93);
  outer.position.z = -2.93 / 2;
  gs.add(outer);
  const gripShield = tube(R - GAP - 0.02, L_GRIP);
  gripShield.position.z = L_GRIP / 2;
  gs.add(gripShield);
  const tail = tube(R - GAP - 0.04, L_TAIL, mat(0xa87700, { side: THREE.DoubleSide, clippingPlanes: [CUT] }));
  tail.position.z = L_GRIP + L_TAIL / 2;
  gs.add(tail);
  label("Outer telescopic shield", outer, [0, R + 0.4, 0]);
  label("Gripper shield", gripShield, [0, R + 0.4, 0]);
  label("Tailskin", tail, [0, R + 0.4, 0.5]);
  const grips = [];
  for (const side of [-1, 1]) {
    const shoe = box(0.4, 2.4, 2.6, mat(0x6e7a86, { clippingPlanes: [CUT] })); // the near shoe is cut away with its shield
    shoe.position.set(side * (R - 0.2), -0.3, L_GRIP / 2);
    gs.add(shoe);
    grips.push({ side, shoe });
  }
  label("Gripper shoes (in shield windows)", grips[1].shoe, [0, 1.6, 0]);
  const erector = new THREE.Group();
  erector.position.z = L_GRIP - 0.2;
  gs.add(erector);
  erector.add(new THREE.Mesh(new THREE.TorusGeometry(1.4, 0.13, 8, 40), mat(0xd9a400)));
  const erArm = box(0.4, 1.0, 0.4, yellow);
  erector.add(erArm);
  label("Segment erector", erector, [0, 1.8, 0]);
  const feeder = box(1.8, 0.4, 3.0, dark);
  feeder.position.set(0, -ID / 2 + 0.6, L_GRIP + L_TAIL + 1.0);
  gs.add(feeder);
  label("Segment feeder", feeder, [0, 0.5, 0]);

  // main thrust cylinders: front shield -> gripper shield; auxiliary cylinders: gripper shield -> last ring
  const cylMat = mat(0x5b8db8);
  const unitCyl = () => new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 1, 12).rotateX(Math.PI / 2).translate(0, 0, 0.5), cylMat);
  const mains = [], auxs = [];
  for (let k = 0; k < 12; k++) {
    const a = ((k + 0.5) / 12) * Math.PI * 2;
    const c = unitCyl();
    c.position.set((R - 0.55) * Math.cos(a), (R - 0.55) * Math.sin(a), Z_FRONT1 - 0.2);
    machine.add(c);
    mains.push(c);
  }
  const RC = (OD + ID) / 4;
  for (let k = 0; k < 16; k++) {
    const a = ((k + 0.5) / 16) * Math.PI * 2;
    const c = unitCyl();
    c.position.set(RC * Math.cos(a), RC * Math.sin(a), 0);
    machine.add(c);
    auxs.push(c);
  }
  label("Main thrust cylinders (front <- gripper shield)", mains[3], [0, 0.4, 1]);
  label("Auxiliary cylinders (on the last ring)", auxs[5], [0, 0.4, 0.5]);
  const belt = box(1.1, 0.12, Z_BACKUP - Z_HEAD, dark);
  belt.position.set(0, BELT_Y, (Z_HEAD + Z_BACKUP) / 2 + 0.5);
  machine.add(belt);
  label("Machine belt", belt, [0, 0.4, 2]);

  // backup: pea gravel and grout plant, segment crane, power
  const railY = -ID / 2 + 0.35;
  const { conveyorY } = buildBackup(machine, { railY, zStart: Z_BACKUP, beltY: BELT_Y, extra: (k, z) => {
    if (k === 0) { for (const dz of [1, 4]) { const t = cyl(0.6, 2.4, mat(0x9c8b6e)); t.position.set(-1.4, railY + 5.0, z + dz); machine.add(t); } label("Pea gravel and grout plant", machine.children.at(-1), [0, 1, 0]); }
    if (k === 1) { const c = box(4.6, 0.3, 0.4, mat(0x5b8db8)); c.position.set(0, railY + 4.0, z + 3); machine.add(c); label("Segment crane", c, [0, 0.6, 0]); }
    if (k === 3) { const tr = box(1.6, 1.4, 3, mat(0x6e7a86)); tr.position.set(-1.6, railY + 5.1, z + 4); machine.add(tr); label("Transformers and hydraulic power", tr, [0, 1, 0]); }
  } });
  const muck = createMuck(machine, { zChute: Z_HEAD + 0.6, beltY: BELT_Y, zBeltEnd: Z_BACKUP, conveyorY });

  // segment rings (universal 6 + key, key last) and annulus fill
  const KEY_DEG = 360 / 19, SEG_DEG = (360 - KEY_DEG) / 6;
  const pieceGeo = (deg) => {
    const s = new THREE.Shape(), a = (deg * Math.PI) / 360, gap = 0.004;
    s.absarc(0, 0, OD / 2, -a + gap, a - gap, false);
    s.absarc(0, 0, ID / 2, a - gap, -a + gap, true);
    s.closePath();
    return new THREE.ExtrudeGeometry(s, { depth: W - 0.01, bevelEnabled: false, curveSegments: 10 });
  };
  const SEG_GEO = pieceGeo(SEG_DEG), KEY_GEO = pieceGeo(KEY_DEG);
  const segMats = [0xa6a6a1, 0x93938e].map((c) => mat(c, { roughness: 0.9, metalness: 0.05, side: THREE.DoubleSide, clippingPlanes: [CUT] }));
  const keyMat = mat(0xc9c2a8, { roughness: 0.9, metalness: 0.05, side: THREE.DoubleSide, clippingPlanes: [CUT] });
  const annulus = (fromDeg, toDeg) => {
    const s = new THREE.Shape();
    const a0 = ((90 - toDeg) * Math.PI) / 180, a1 = ((90 - fromDeg) * Math.PI) / 180;
    s.absarc(0, 0, R, a0, a1, false);
    s.absarc(0, 0, OD / 2 + 0.003, a1, a0, true);
    s.closePath();
    return new THREE.ExtrudeGeometry(s, { depth: W, bevelEnabled: false, curveSegments: 24 });
  };
  const GRAVEL_GEO = annulus(-120, 120), GROUT_GEO = annulus(120, 240);
  const gravelMat = mat(0x9c8b6e, { roughness: 1, metalness: 0, clippingPlanes: [CUT] });
  const groutMat = mat(0x6f6d68, { roughness: 1, metalness: 0, clippingPlanes: [CUT] });
  const KEY_POS = [0, 2, -2, 1, -1, 3, -3].map((k) => Math.PI / 2 + (k * 2 * Math.PI) / 16);
  const ringPieces = (n) => {
    const key = KEY_POS[((n % KEY_POS.length) + KEY_POS.length) % KEY_POS.length];
    const kd = (KEY_DEG * Math.PI) / 180, sd = (SEG_DEG * Math.PI) / 180;
    const pieces = [];
    for (let i = 1; i <= 6; i++) pieces.push({ angle: key + kd / 2 + sd * (i - 0.5), key: false, i });
    const order = [3, 4, 2, 5, 1, 6].map((i) => pieces[i - 1]);
    order.push({ angle: key, key: true, i: 0 });
    return order;
  };
  const makePiece = (p, n) => { const m = new THREE.Mesh(p.key ? KEY_GEO : SEG_GEO, p.key ? keyMat : segMats[(((n + p.i) % 2) + 2) % 2]); m.rotation.z = p.angle; return m; }; // n < 0 before the start
  const rings = [];
  const addRing = (n, wz, pieces = 7) => {
    const g = new THREE.Group();
    g.position.z = wz;
    ringPieces(n).slice(0, pieces).forEach((p) => g.add(makePiece(p, n)));
    const gravel = new THREE.Mesh(GRAVEL_GEO, gravelMat), grout = new THREE.Mesh(GROUT_GEO, groutMat);
    gravel.visible = grout.visible = false;
    g.add(gravel, grout);
    world.add(g);
    const r = { g, n, wz, gravel, grout, placed: pieces };
    rings.push(r);
    if (rings.length > 70) world.remove(rings.shift().g);
    return r;
  };
  const completeTo = (r, k) => { while (r.placed < k) { r.g.add(makePiece(ringPieces(r.n)[r.placed], r.n)); r.placed++; } };

  const doubleMode = (zone) => zone.rmr >= M.doubleModeMinRmr;
  const buildPer = (M.ringBuildMin * 60) / 7;

  // Skin friction of the closing rock on the shield (screening estimate after Ramoni & Anagnostou), sliding and at restart
  const frictionCache = new Map();
  const friction = (zone, g) => {
    if (!frictionCache.has(zone)) {
      const args = [g.R, M.shieldLength, M.overcut, g.p0, g.mc.e_rm, g.nu, g.mc.phi_deg, g.mc.c];
      frictionCache.set(zone, { sliding: shieldFriction(...args, SKIN_FRICTION_ROCK.sliding), restart: shieldFriction(...args, SKIN_FRICTION_ROCK.static) });
    }
    return frictionCache.get(zone);
  };

  return {
    muck,
    // the shield and then the lining stop the rock at the overcut gap
    closureLimit() { return M.overcut; },
    groundRows(zone, g) {
      const f = friction(zone, g);
      const contact = f.sliding.contact_from === null ? "no contact with the shield" : `rock reaches the shield ${f.sliding.contact_from.toFixed(1)} m behind the face`;
      return [["Rock on the shield (overcut 10 cm)", contact],
        ["Shield skin friction", `${f.sliding.friction_force.toFixed(0)} MN sliding, ${f.restart.friction_force.toFixed(0)} MN to restart, vs about ${M.thrustInstalled} MN installed`]];
    },
    groundAlarms(zone, g) {
      const f = friction(zone, g);
      if (f.sliding.friction_force > M.thrustInstalled) return [`Shield jammed: skin friction ${f.sliding.friction_force.toFixed(0)} MN exceeds the installed thrust; free the shield (by-pass, overcut, lubrication)`];
      if (f.restart.friction_force > M.thrustInstalled) return [`Jamming risk after any standstill: ${f.restart.friction_force.toFixed(0)} MN needed to restart vs ${M.thrustInstalled} MN installed. Keep advancing; avoid stops in this zone`];
      return [];
    },
    reset(S) {
      for (const r of rings) world.remove(r.g);
      rings.length = 0;
      // rings already built behind the start: ring n's front face at TBM-local Z_RING + (k + 1) W
      for (let k = 30; k >= 1; k--) addRing(-k, Z_RING + k * W - S.chainage);
      Object.assign(S, { ring: 0, building: null, buildT: 0, sMain: 0, waitRing: false });
    },
    // Double mode: BORING (ring built at the same time) -> [WAIT RING] -> REGRIP -> STOPPED.
    // Single-shield mode: BORING (aux cylinders on the last ring) -> RING BUILD -> STOPPED.
    step(S, dt, ctx) {
      const zone = ctx.zone, dbl = doubleMode(zone);
      S.dbl = dbl;
      const startRing = () => {
        S.building = addRing(S.ring, Z_RING + S.sMain - S.chainage, 0);
        S.buildT = 0;
      };
      const advanceBuild = (dtb) => {
        if (!S.building) startRing();
        S.buildT += dtb;
        completeTo(S.building, Math.min(7, Math.floor(S.buildT / buildPer)));
        return S.building.placed >= 7;
      };
      if (S.mode === "BORING") {
        const adv = Math.min((S.perf.rop_m_h / 3600) * dt, M.stroke - S.stroke);
        ctx.bore(adv);
        if (dbl) { S.sMain += adv; advanceBuild(dt); }
        if (S.stroke >= M.stroke - 1e-9) {
          if (dbl) S.mode = S.building && S.building.placed >= 7 ? "REGRIP" : "WAIT RING";
          else { S.mode = "RING BUILD"; S.building = null; }
          S.regripT = 0;
        }
      } else if (S.mode === "WAIT RING") {
        if (advanceBuild(dt)) S.mode = "REGRIP";
      } else if (S.mode === "REGRIP") {
        S.regripT += dt;
        S.sMain = M.stroke * Math.max(0, 1 - S.regripT / (M.regripMin * 60));
        if (S.regripT >= M.regripMin * 60) { S.sMain = 0; S.ring++; S.building = null; ctx.startStop(["boring", "regrip"]); S.stroke = 0; }
      } else if (S.mode === "RING BUILD") {
        if (advanceBuild(dt)) { S.ring++; S.building = null; ctx.startStop(["boring", "regrip"], M.ringBuildMin / 60); S.stroke = 0; }
      } else ctx.stopStep(dt);
    },
    afterStep(S) {
      // annulus fill appears once a ring has left the tailskin
      for (const r of rings) { const z = r.g.position.z + S.chainage; r.gravel.visible = r.grout.visible = z > Z_GRIP0 + S.sMain + L_GRIP + L_TAIL - 0.2; }
    },
    modeText(S, fmtv) {
      const mode = S.dbl ? "double-shield mode" : "single-shield mode";
      if (S.mode === "BORING") return `BORING, ${mode} (stroke ${fmtv(S.stroke, 2)} of ${M.stroke} m${S.dbl && S.building ? `; ring ${S.building.placed} of 7 built` : ""})`;
      if (S.mode === "WAIT RING") return `WAITING for the ring build (${S.building?.placed ?? 0} of 7)`;
      if (S.mode === "REGRIP") return `REGRIP: gripper shield pulled up (${fmtv(M.regripMin * 60 - S.regripT, 0)} s left)`;
      if (S.mode === "RING BUILD") return `RING BUILD, single-shield mode (${S.building?.placed ?? 0} of 7 segments)`;
      return null;
    },
    supportRows(zone) {
      return [["Mode in this rock", doubleMode(zone) ? "double shield: rings built while boring" : "single shield: thrust on the rings, bore then build"],
        ["Lining", `6 + key segments, ${W} m rings, ${Math.round(M.segThick * 1000)} mm`], ["Annulus", "pea gravel in the crown, grout in the invert"]];
    },
    alarms(zone) {
      return doubleMode(zone) ? [] : [`Poor rock (RMR ${zone.rmr}): single-shield mode, thrust on the segments; squeezing ground can trap the shield`];
    },
    utilOptions(zone) {
      // single-shield mode has no regrip; the explicit ring build replaces part of the support downtime (see startStop)
      return doubleMode(zone) ? { regrip_min: M.regripMin } : { regrip_min: 0 };
    },
    animate(S, dtReal) {
      head.rotation.z -= ((S.mode === "BORING" ? S.rpm : 0) / 60) * 2 * Math.PI * dtReal;
      gs.position.z = Z_GRIP0 + S.sMain;
      const gripping = S.dbl && (S.mode === "BORING" || S.mode === "WAIT RING");
      for (const g of grips) g.shoe.position.x = g.side * (R - (gripping ? 0.2 : 0.4)); // shoes reach the rock through the windows
      for (const c of mains) c.scale.z = Math.max(gs.position.z - c.position.z - 0.1, 0.3);
      // auxiliary cylinders: from the rear of the gripper shield to the front face of the newest complete ring
      const last = [...rings].reverse().find((r) => r.placed >= 7);
      const zRing = last ? last.g.position.z + S.chainage : Z_RING + W;
      const zBase = gs.position.z + L_GRIP - 0.6;
      for (const c of auxs) { c.position.z = zBase; c.scale.z = Math.max(zRing - zBase, 0.2); }
      const cur = S.building && S.building.placed < 7 ? ringPieces(S.building.n)[S.building.placed] : null;
      erector.rotation.z = cur ? cur.angle - Math.PI / 2 : 0;
      erArm.position.y = cur ? 1.4 + 1.6 : 0.8;
      erArm.scale.y = cur ? 2.2 : 1.0;
    },
  };
}
