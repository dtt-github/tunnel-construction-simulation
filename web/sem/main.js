// Slice D: SEM / NATM heading. One crew works the top heading, bench and invert; the sprayed concrete stiffens with age
// (Oreste 2003); the lining load comes from the ageing-ring interaction with the ground reaction curve; monitoring
// sections read convergence with the Sulem et al. (1987) law and Crossrail trigger levels.
//
// Default ground: the Crossrail Farringdon platform tunnels (11 m SCL enlargements of a TBM pilot in Lambeth Group
// and London Clay, about 31 m deep), on the Farringdon - Liverpool Street scenario with Crossrail's undrained design
// parameters. ?ground=rock gives the illustrative weak-rock heading with a fault zone (FHWA 2009 classes).
//
// World frame: metres, Y up, tunnel axis at y = 0, chainage along -z. The ground and lining stay put; the faces advance.

import {
  equivalentMohrCoulomb, groundReaction, ldp, squeezingStrain, squeezingClass, shotcreteModulus, shotcreteStrength,
  earlyStrengthClass, liningInteraction, SEM_ROCK_CLASSES, CYCLE, ringClosureOk, sulemConvergence, SULEM_EXAMPLE, triggerLevel,
  FINAL_LINING_RATE_MM_PER_MONTH, SHOTCRETE, Rng, scenario as loadScenario, crownSettlement, WHOLE_BODY_SETTLEMENT,
} from "../../models/js/index.js";
import { THREE, createScene, label, placeLabels, mat, box, fmt, dl } from "../hard-rock/common.js";

const MODE = new URLSearchParams(location.search).get("ground") === "rock" ? "rock" : "farringdon";
const FARR = MODE === "farringdon";

// ---------------------------------------------------------------- tunnel, ground, sequence
// Farringdon platform tunnels: about 11.4 m wide x 10.6 m high, treated as an 11 m circle [GRM, TEMP]; 400 mm SFRC
// primary lining with no lattice girders [CG Fig. 5; TEMP; VAL].
const D = FARR ? 11 : 10, R = D / 2;
const Y_TH = FARR ? 0.8 : 1.0, Y_BENCH = FARR ? -3.3 : -3.0; // floor of the top heading and of the bench
const H_PER_M = { top_heading: CYCLE.top_heading[1] / CYCLE.top_heading[0], bench: CYCLE.bench[1] / CYCLE.bench[0], invert: CYCLE.invert[1] / CYCLE.invert[0] };
const CYCLE_H_PER_M = H_PER_M.top_heading + H_PER_M.bench + H_PER_M.invert;

// Rock: illustrative siltstone and a crushed fault zone under 100 m of cover.
const COVER = 100, P0_ROCK = COVER * 0.027, NU_ROCK = 0.25; // m, MPa
const ROCK_ZONES = [
  { name: "Siltstone, moderately jointed", from: -80, to: 60, gsi: 45, sci: 30, mi: 9, ei: 8000, cls: "moderately_jointed",
    th: 2.0, bench: 4.0, lining: 0.2, benchLag: 30, canopy: false, color: 0x8b8574 },
  { name: "Crushed fault zone", from: 60, to: 100, gsi: 22, sci: 15, mi: 8, ei: 3000, cls: "crushed_squeezing",
    th: 1.0, bench: 2.0, invert: 2.0, lining: 0.35, benchLag: 4, canopy: true, color: 0x6b5848 },
  { name: "Siltstone, moderately jointed", from: 100, to: 400, gsi: 45, sci: 30, mi: 9, ei: 8000, cls: "moderately_jointed",
    th: 2.0, bench: 4.0, lining: 0.2, benchLag: 30, canopy: false, color: 0x8b8574 },
];

// Farringdon. Sources (Crossrail Learning Legacy, read and cited, not redistributed):
//   GRM  Gakis et al. (2014) Geotechnical risk management for SCL tunnels in Farringdon Crossrail Station
//   SAND Tunnelling in sand in Farringdon Crossrail Station
//   DES  Farringdon Station SCL design: reducing risk at the heart of Crossrail
//   VAL  Crossrail Farringdon Station SCL tunnels: delivering value through innovation and best practice
//   TEMP Temporary sprayed concrete lining tunnels in Farringdon Crossrail Station
//   CG   Gakis, Grau & Schwind (2016) Tunnel deformations caused by compensation grouting at Crossrail Farringdon Station
//   WCH  Staerk et al., Analyses of convergence and utilisation of SCL-tunnels during excavation (Whitechapel)
// Undrained design lines, z = depth below the top of the London Clay [TEMP Table 1; CG Table 2]: cu kPa, E MPa.
const DESIGN = {
  LC: { name: "London Clay", cu: (z) => 85 + 6.5 * z, e: (z) => 40 + 3.7 * z, color: 0x6e6658 },
  LG: { name: "Lambeth Group", cu: (z) => 95 + 10 * z, e: (z) => 36 + 5.9 * z, color: 0x8a6f5a },
};
const NU_CLAY = 0.495, K0_DEFORM = 0.6, K0_LOAD = 1.2; // K0 0.6 gave realistic deformations, 1.2 governed lining stress [TEMP]
const CH0 = 360; // scenario chainage of demo chainage 0 (west end of the platform tunnels; boreholes F32R, F6, F14)
const CLOSURE_X = 7.5; // m behind the face: ring closed 3-5 days after a section was installed at 1.5-2 m/day [CG]
const RATE_PLATFORM = 1.1, RATE_LENS = 0.5; // m/day: platform enlargements, sand-lens zones [VAL 4.6]
// Water-bearing sand lens in the crown: 83 m long, 3-4 m thick, 100 kPa (Lens B, PTE) [SAND]; position illustrative.
const LENS = { from: 150, to: 233, spile: 4, hours: 4 }; // 4 m grouted spiles every second top heading; hours assumed
// mm, platform tunnels PTW/PTE outside the concurrent compensation grouting [CG Table 1]; design 2D FE without grouting [CG Table 4]
const MEASURED_CROWN = { min: 10.3, max: 16.5, meanOut: 13.6, fe: 10 };
const WHOLE_BODY = (WHOLE_BODY_SETTLEMENT[0] + WHOLE_BODY_SETTLEMENT[1]) / 2; // m, whole-ring settlement 2-3 mm [WCH]
const SCN = FARR ? loadScenario(await (await fetch("../../models/scenarios/london-farringdon-liverpool-street.json")).json()) : null;

function farringdonZones() {
  const out = [];
  for (let ch = -80; ch < 400; ch += 10) {
    const sch = Math.min(Math.max(CH0 + ch + 5, 0), SCN.length), f = SCN.face(sch, D);
    const lcTop = SCN.column(sch).find((l) => l.unit === "LC")?.top ?? SCN.axisAt(sch);
    const clay = f.unit_at_axis === "LC" ? "LC" : "LG", z = Math.max(lcTop - SCN.axisAt(sch), 0), d = DESIGN[clay];
    const sv = f.gamma * f.axis_depth, u = f.u_axis; // kPa
    const lens = ch + 5 >= LENS.from && ch + 5 < LENS.to;
    out.push({ name: `${d.name} at the axis`, from: ch, to: ch + 10, sch, clay, z, cu: d.cu(z) / 1000, e: d.e(z), shares: f.units_on_face,
      sv, u, depth: f.axis_depth, kDeform: (K0_DEFORM * (sv - u) + u) / sv, p0Deform: (sv + K0_DEFORM * (sv - u) + u) / 2000, p0Load: (sv + K0_LOAD * (sv - u) + u) / 2000,
      th: 1.0, bench: 2.0, invert: 2.0, lining: 0.4, benchLag: 3, canopy: false, lens, color: d.color,
      rate: (lens ? RATE_LENS : RATE_PLATFORM) / 24 });
  }
  return out;
}
const ZONES = FARR ? farringdonZones() : ROCK_ZONES;
const zoneAt = (ch) => ZONES.find((z) => ch >= z.from && ch < z.to) ?? ZONES.at(-1);
const CANOPY = { length: 12.5, advance: 9, pipes: 40, hours: 20 }; // Fort Canning AGF umbrella; ~2 working days per umbrella
const SECTION_SPACING = 10;
const A_TH = Math.acos(Y_TH / R), A_BENCH = Math.acos(Y_BENCH / R); // half-angles from the crown
// Ring closure: within 0.8 D of the face in the fault zone; at Farringdon the invert follows about 6.5 m behind,
// closing the ring 6.5-8.5 m from the face [CG].
const INVERT_TRIGGER = FARR ? 6.5 : 0.8 * D;
// Hours per metre not covered by the Stepney Green cycle (pilot segment removal, survey, sealing, face pockets,
// depressurisation and stand-downs; not itemised in the sources), so the heading keeps the published average rate.
const extraHoursPerM = (z) => (FARR ? Math.max(24 / (z.rate * 24) - CYCLE_H_PER_M, 0) : 0);

// ---------------------------------------------------------------- ground response per zone (cached per shotcrete)
const groundCache = new Map();
function groundAt(zone, shot) {
  const key = `${ZONES.indexOf(zone)}|${shot}`;
  if (!groundCache.has(key)) groundCache.set(key, FARR ? soilGround(zone, shot) : rockGround(zone, shot));
  return groundCache.get(key);
}
function rockGround(zone, shot) {
  const mc = equivalentMohrCoulomb(zone.gsi, zone.mi, zone.sci, zone.ei, P0_ROCK);
  const free = groundReaction(P0_ROCK, 0, R, mc.e_rm, NU_ROCK, mc.phi_deg, mc.c);
  // planned average heading rate from the cycle: top heading rounds plus the bench, invert and canopy work they bring
  const perM = H_PER_M.top_heading + H_PER_M.bench + (zone.invert ? H_PER_M.invert : 0) + (zone.canopy ? CANOPY.hours / CANOPY.advance : 0);
  const rate = 1 / perM; // m/h
  const li = liningInteraction(P0_ROCK, R, mc.e_rm, NU_ROCK, mc.phi_deg, mc.c, zone.lining, zone.th, rate, shot);
  const strain = squeezingStrain(mc.sigma_cm, P0_ROCK);
  return { mc, free, rate, li, strain, squeeze: squeezingClass(strain), predictedMm: 2 * (li.u_final - li.u_install) * 1000 };
}
// Undrained (phi = 0, Tresca) ground reaction with Crossrail's design lines. The lining is taken to carry load once the
// ring is closed (CLOSURE_X behind the face); the open top-heading arch before that is treated as no support. Crown
// settlement is read from the first survey of the section, sprayed at the top heading one round behind the face. The
// ring gives the mean radial movement; the crown takes it times the Kirsch factor for the total-stress ratio (Brady &
// Brown), plus 2-3 mm settlement of the ring as a whole, measured in the Whitechapel enlargements [WCH].
function soilGround(zone, shot) {
  const mc = { phi_deg: 0, c: zone.cu, e_rm: zone.e, sigma_cm: 2 * zone.cu };
  const free = groundReaction(zone.p0Deform, 0, R, zone.e, NU_CLAY, 0, zone.cu);
  const liD = liningInteraction(zone.p0Deform, R, zone.e, NU_CLAY, 0, zone.cu, zone.lining, CLOSURE_X, zone.rate, shot);
  const li = liningInteraction(zone.p0Load, R, zone.e, NU_CLAY, 0, zone.cu, zone.lining, CLOSURE_X, zone.rate, shot);
  const uSurvey = free.u * ldp(zone.th, R, free.r_p);
  // Broms & Bennermark (1967) stability ratio at the open face, N = sigma_v / cu (no face pressure); about 6 is the limit
  const n = zone.sv / 1000 / zone.cu;
  return { mc, free, rate: zone.rate, li, liD, n, ringMm: Math.max(liD.u_final - uSurvey, 0) * 1000,
    predictedMm: crownSettlement(liD.u_final, uSurvey, zone.kDeform, NU_CLAY, WHOLE_BODY) * 1000 };
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
    // lattice girders at 1 m spacing in the sprayed concrete (none at Farringdon: fibre-reinforced only)
    for (let g = 0.5; g < len && !FARR; g += 1) {
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

// Farringdon: 4 m grouted spiles in the crown, every second top heading in the sand lens [SAND].
const spileGeo = new THREE.CylinderGeometry(0.04, 0.04, LENS.spile, 5).rotateX(Math.PI / 2).translate(0, 0, -LENS.spile / 2);
function installSpiles(ch) {
  const g = new THREE.Group();
  g.position.z = -ch;
  for (let k = 0; k < 25; k++) {
    const a = Math.PI / 2 - deg(60) + (k / 24) * deg(120);
    const p = new THREE.Mesh(spileGeo, pipeMat);
    p.position.set((R + 0.1) * Math.cos(a), (R + 0.1) * Math.sin(a), 0);
    p.rotation.set(0.12 * Math.sin(a), -0.12 * Math.cos(a), 0);
    g.add(p);
  }
  world.add(g);
  return g;
}
// The 6.2 m TBM pilot tunnel (300 mm segments) the platform is enlarged from, ahead of the face [GRM; TEMP; CG Fig. 5].
// Drawn on the axis; its position within the section is schematic.
const pilot = new THREE.Mesh(new THREE.CylinderGeometry(3.4, 3.4, 1, 48, 1, true).rotateX(Math.PI / 2).translate(0, 0, -0.5),
  new THREE.MeshStandardMaterial({ color: 0xb8b6ae, roughness: 0.9, transparent: true, opacity: 0.3, depthWrite: false, side: THREE.DoubleSide, clippingPlanes: [CUT] }));
pilot.visible = FARR;
world.add(pilot);
const pilotAnchor = new THREE.Object3D();
world.add(pilotAnchor);
// The water-bearing sand lens in the crown (3.5 m thick), shown ahead of the face.
const lensMesh = box(9, 3.5, LENS.to - LENS.from, new THREE.MeshStandardMaterial({ color: 0xc9b27a, roughness: 1, transparent: true, opacity: 0.6, depthWrite: false, clippingPlanes: [CUT, AHEAD] }));
lensMesh.position.set(0, R + 0.75, -(LENS.from + LENS.to) / 2);
lensMesh.visible = FARR;
world.add(lensMesh);
if (FARR) { label("6.2 m TBM pilot tunnel", pilotAnchor, [0, 3.6, -6]); label("Sand lens in the crown (position illustrative)", lensMesh, [0, 2.2, 0]); }

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
const ids = ["start", "shot", "closure", "closureText", "ts", "tsOut", "pause", "reset", "alarms", "sequence", "ground", "monitor", "showLabels", "title", "limits", "credits", "groundSel"];
const ui = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));
const FARR_TEXT = {
  title: "SEM platform tunnel · Farringdon · 11 m",
  start: [[0, "Chainage 0 m: west end, Lambeth Group"], [130, "Chainage 130 m: sand lens ahead"], [160, "Chainage 160 m: inside the sand lens"], [230, "Chainage 230 m: London Clay coming in"]],
  closure: "Close the ring within one diameter (FHWA)",
  limits: [
    "Ground from the Farringdon – Liverpool Street scenario (BGS boreholes F32R, F6, F14): one zone per 10 m, demo chainage 0 = scenario chainage 360 m. Strength and stiffness are Crossrail's undrained design lines; the clay at the axis sets them, even where Thanet Sand is in the invert.",
    "The 11.4 × 10.6 m section is a circle of radius 5.5 m, and the ground is in plane strain around it (undrained, Tresca). The ring solution gives the mean radial movement; the crown takes it times the elastic (Kirsch) factor for unequal stresses, so in undrained clay it follows the vertical stress. The TBM pilot tunnel the platform is enlarged from is not modelled.",
    "The lining is taken to carry load only once the ring is closed, 7.5 m behind the face. The 2–3 mm settlement of the ring as a whole is taken from the Whitechapel enlargements (London Clay), not computed. The prediction (about 10–14 mm) sits in the measured 10.3–16.5 mm, mostly below the 13.6 mm mean; Crossrail's design FE gave 10 mm.",
    "The sand lens is placed illustratively; its length, thickness, pressure and treatment are those of Lens B under PTE. Time per metre beyond the Stepney Green cycle is set so the heading keeps the published 1.1 m/day (0.5 m/day in the lens); that work is not itemised in the sources. Spile drilling time is assumed.",
    "Readings use the distance-to-face term of Sulem et al. (1987) scaled to the prediction, with ±20 % scatter between sections (illustrative). At Farringdon the readings levelled out 3–5 days after ring closure (CG), so no time term is added; long-term consolidation above the tunnels, which continued for years at Whitechapel, is a surface effect and not shown.",
  ],
  credits: `Ground: Crossrail Learning Legacy papers on the Farringdon SCL tunnels: <a href="https://learninglegacy.crossrail.co.uk/documents/geotechnical-risk-management-for-sprayed-concrete-lining-tunnels-in-farringdon-crossrail-station/">risk management</a>, <a href="https://learninglegacy.crossrail.co.uk/documents/tunnelling-sand-farringdon-crossrail-station/">tunnelling in sand</a>, <a href="https://learninglegacy.crossrail.co.uk/documents/farringdon-station-scl-design-reducing-risk-at-the-heart-of-crossrail/">design</a>, <a href="https://learninglegacy.crossrail.co.uk/documents/crossrail-farringdon-station-scl-tunnels-delivering-value-through-innovation-and-best-practice/">value</a>, <a href="https://learninglegacy.crossrail.co.uk/documents/temporary-sprayed-concrete-lining-tunnels-farringdon-crossrail-station/">temporary tunnels</a>, <a href="https://learninglegacy.crossrail.co.uk/documents/tunnel-deformations-caused-compensation-grouting-crossrail-farringdon-station/">compensation grouting</a>; Whitechapel <a href="https://learninglegacy.crossrail.co.uk/documents/analyses-convergence-utilisation-scl-tunnels-excavation/">convergence</a> (whole-ring settlement); BGS boreholes. Models: undrained ground reaction (Duncan Fama limit), crown factor (Kirsch, Brady & Brown 2006), shotcrete ageing and lining interaction (Oreste 2003), face stability (Broms & Bennermark 1967), convergence law (Sulem et al. 1987), trigger levels (Crossrail). Method card in the <a href="https://github.com/dtt-github/tunnel-construction-simulation/blob/main/docs/research/methods-reference.md">methods reference</a>.`,
};
if (FARR) {
  ui.title.textContent = FARR_TEXT.title;
  ui.start.innerHTML = FARR_TEXT.start.map(([v, t]) => `<option value="${v}">${t}</option>`).join("");
  ui.closureText.textContent = FARR_TEXT.closure;
  ui.limits.innerHTML = FARR_TEXT.limits.map((t) => `<li>${t}</li>`).join("");
  ui.credits.innerHTML = FARR_TEXT.credits;
}
ui.groundSel.value = MODE;
ui.groundSel.onchange = () => { location.search = ui.groundSel.value === "rock" ? "?ground=rock" : ""; };
const val = (id) => +ui[id].value;
let S;
const trash = [];
function reset() {
  for (const o of trash.splice(0)) world.remove(o);
  for (const l of linings.splice(0)) world.remove(l.mesh);
  for (const s of sections.splice(0)) world.remove(s.group);
  for (const t of tempInverts.splice(0)) world.remove(t);
  world.children.filter((c) => c.geometry?.type === "TorusGeometry" || c.userData.canopy || c.userData.spiles).forEach((c) => world.remove(c));
  const start = val("start");
  // faces at the start follow the class there: bench 24 m and flat invert behind in siltstone; bench 4 m and invert
  // 8 m behind (ring closed within one diameter) in the fault zone; bench 3 m and invert 7 m behind at Farringdon
  const z0 = zoneAt(start);
  const [bLag, iLag] = FARR ? [3, 7] : z0.invert ? [4, 8] : [24, 24];
  S = { th: start, bench: start - bLag, invert: start - iLag, canopyEnd: -Infinity, spileEnd: -Infinity, worksDone: false, faceHist: [[0, start]], simTime: 0, task: null, paused: false, rng: new Rng(5), nextSection: Math.ceil(start / SECTION_SPACING) * SECTION_SPACING, done: { th: 0, bench: 0, invert: 0 } };
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
  if (zB.invert && invLag >= zB.invert && (needsClosure(S.invert) ? S.th - S.invert >= INVERT_TRIGGER : S.th - S.invert >= 30))
    return { kind: "invert", len: Math.min(zB.invert, invLag), hours: Math.min(zB.invert, invLag) * H_PER_M.invert };
  if (benchLag >= zoneAt(S.bench).benchLag + zoneAt(S.bench).bench || (zTh.invert && benchLag >= zTh.benchLag)) {
    const len = Math.min(zoneAt(S.bench).bench, benchLag);
    return { kind: "bench", len, hours: len * H_PER_M.bench };
  }
  // Farringdon: spiles every second top heading in the sand lens, then the other work of the round
  if (FARR && zTh.lens && S.th + zTh.th > S.spileEnd - LENS.spile / 2) return { kind: "spiles", len: 0, hours: LENS.hours };
  if (FARR && !S.worksDone) {
    const hours = Math.max(extraHoursPerM(zTh) - (zTh.lens ? LENS.hours / (LENS.spile / 2) : 0), 0) * zTh.th;
    if (hours > 0) return { kind: "works", len: 0, hours };
  }
  return { kind: "top_heading", len: zTh.th, hours: zTh.th * H_PER_M.top_heading };
}
function finishTask(t) {
  if (t.kind === "canopy") { const g = installCanopy(S.th); g.userData.canopy = true; trash.push(g); S.canopyEnd = S.th + CANOPY.length; return; }
  if (t.kind === "spiles") { const g = installSpiles(S.th); g.userData.spiles = true; trash.push(g); S.spileEnd = S.th + LENS.spile; return; }
  if (t.kind === "works") { S.worksDone = true; return; }
  if (t.kind === "top_heading") {
    const z = zoneAt(S.th);
    sprayRound("top_heading", S.th, t.len, z.lining, S.simTime);
    S.worksDone = false;
    if (z.invert && ui.closure.checked && !FARR) { // temporary top-heading invert (Fort Canning practice)
      const slab = box(2 * Math.sqrt(R * R - Y_TH * Y_TH) - 0.4, 0.15, t.len, slabMat);
      slab.position.set(0, Y_TH + 0.08, -(S.th + t.len / 2));
      slab.userData.ch = S.th;
      world.add(slab);
      tempInverts.push(slab);
    }
    S.th += t.len;
    S.done.th += t.len;
    S.faceHist.push([S.simTime, S.th]);
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
// Face position at a past time: the recorded history, or the planned rate before the start.
function faceAt(t) {
  if (t >= S.simTime) return S.th;
  for (let i = S.faceHist.length - 1; i >= 0; i--) if (S.faceHist[i][0] <= t) return S.faceHist[i][1];
  return S.faceHist[0][1] + (t / 3600) * groundAt(zoneAt(S.faceHist[0][1]), ui.shot.value).rate;
}
function reading(sec, atTime = S.simTime) {
  const z = zoneAt(sec.ch), g = groundAt(z, ui.shot.value);
  const x = faceAt(atTime) - sec.ch, days = (atTime - sec.t0) / 86400;
  // Farringdon: distance term only. The undrained prediction is the short-term movement, and Sulem's time term was
  // fitted in claystone; consolidation and creep in the clay are not modelled.
  const m = FARR ? 0 : SULEM_EXAMPLE.m;
  const cInf = g.predictedMm / (1 + m);
  const xRef = SULEM_EXAMPLE.x_over_d * D;
  // no ring closure in a squeezing zone: larger deformation (illustrative factor 1.5, no published value)
  const noClosure = z.invert && !ui.closure.checked ? 1.5 : 1;
  return sec.scatter * noClosure * (sulemConvergence(x, Math.max(days, 0), cInf, xRef, SULEM_EXAMPLE.t_ref, m, SULEM_EXAMPLE.n));
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
  pilot.position.z = pilotAnchor.position.z = -S.th;
  pilot.scale.z = Math.max(400 - S.th, 0.001);
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
  const zTh = zoneAt(S.th), g = groundAt(zTh, ui.shot.value), cls = FARR ? null : SEM_ROCK_CLASSES[zTh.cls];
  const days = S.simTime / 86400;
  const TASK = { top_heading: "excavating and spraying the top heading", bench: "excavating and spraying the bench", invert: "excavating and spraying the invert (ring closure)", canopy: "drilling a pipe canopy (40 pipes, 12.5 m)",
    spiles: "drilling and grouting 4 m spiles in the crown", works: zTh.lens ? "depressurising, sealing and opening the face in pockets" : "breaking out pilot segments, survey and sealing layer" };
  const invLag = S.th - S.invert;
  const rateRow = days > 0.05 ? `${fmt(S.done.th, 1)} m top heading in ${fmt(days, 1)} days = ${fmt(S.done.th / days, 1)} m/day` : "—";
  const shotRows = (ageFace) => [["Shotcrete at 1 h / 24 h", `${fmt(shotcreteStrength(ageFace, ui.shot.value), 1)} MPa (${earlyStrengthClass(ageFace, shotcreteStrength(ageFace, ui.shot.value))}) / ${fmt(shotcreteStrength(24, ui.shot.value), 1)} MPa (${earlyStrengthClass(24, shotcreteStrength(24, ui.shot.value))})`]];
  if (FARR) {
    const shares = Object.entries(zTh.shares).sort((a, b) => b[1] - a[1]).map(([u, f]) => `${u} ${fmt(f * 100, 0)} %`).join(", ");
    dl(ui.sequence, [
      ["Now", S.task ? `${TASK[S.task.kind]} (${fmt(S.task.left / 3600, 1)} h left)` : "—"],
      ["Sequence", "top heading 2 × 1 m, bench 2 m, invert 2 m, faces staggered (TEMP)"],
      ["Top heading face", `${fmt(S.th, 1)} m (scenario chainage ${fmt(CH0 + S.th, 0)} m)`],
      ["Bench face", `${fmt(S.bench, 1)} m, ${fmt(S.th - S.bench, 1)} m behind`],
      ["Invert / ring closure", `${fmt(S.invert, 1)} m, ${fmt(invLag, 1)} m behind the face (Farringdon 5–10 m; FHWA limit ${D} m)`],
      ["Pre-support", zTh.lens ? "sand lens: wellpoints until the residual pore pressure is below 10 kPa and probe inflow below 3 l/min, face in 3–4 pockets, 4 m grouted spiles every second top heading (SAND)" : "none: open face in clay with long stand-up time (SAND)"],
      ["Advance so far", rateRow],
      ["Published rate", `${zTh.lens ? `${RATE_LENS} m/day in sand-lens zones` : `${RATE_PLATFORM} m/day for the platform enlargements`} (VAL)`],
    ]);
    dl(ui.ground, [
      ["Ground on the face", `${shares}; ${fmt(zTh.depth, 1)} m to the axis`],
      ["Design line at the axis", `${DESIGN[zTh.clay].name}, ${fmt(zTh.z, 1)} m below the London Clay top: cu ${fmt(zTh.cu * 1000, 0)} kPa, E ${fmt(zTh.e, 0)} MPa (TEMP, CG)`],
      ["Stress at the axis", `σv ${fmt(zTh.sv, 0)} kPa, pore pressure ${fmt(zTh.u, 0)} kPa (published 100–150 kPa, DES); p0 ${fmt(zTh.p0Deform * 1000, 0)} / ${fmt(zTh.p0Load * 1000, 0)} kPa at K0 ${K0_DEFORM} / ${K0_LOAD}`],
      ["Face stability N = σv / cu", `${fmt(g.n, 2)} (Broms & Bennermark: unstable above about 6)`],
      ["Unsupported closure", `${fmt(g.free.u * 1000, 0)} mm (radial, K0 ${K0_DEFORM}), plastic zone ${fmt(g.free.r_p / R, 2)} R`],
      ["Lining", `${fmt(zTh.lining * 1000, 0)} mm steel-fibre sprayed concrete on a 75 mm sealing layer, no girders`],
      ...shotRows(1),
      ["Lining load (K0 1.2, ring closed)", `${fmt(g.li.p_final, 2)} MPa long term (Oreste)`],
      ["Lining safety (strength / stress)", `${fmt(g.li.min_safety, 1)} at minimum`],
      ["Predicted crown settlement", `${fmt(g.predictedMm, 1)} mm after the top heading is sprayed: ring ${fmt(g.ringMm, 1)} mm × Kirsch crown factor + ${fmt(WHOLE_BODY * 1000, 1)} mm whole ring (ring closed ${CLOSURE_X} m back)`],
      ["Measured, platform tunnels", `${MEASURED_CROWN.min}–${MEASURED_CROWN.max} mm, mean ${MEASURED_CROWN.meanOut} mm outside compensation grouting (CG Table 1); Crossrail design FE ${MEASURED_CROWN.fe} mm`],
    ]);
  } else {
    dl(ui.sequence, [
      ["Now", S.task ? `${TASK[S.task.kind]} (${fmt(S.task.left / 3600, 1)} h left)` : "—"],
      ["Ground class (FHWA)", `${zTh.cls.replaceAll("_", " ")}: ${cls.sequence}`],
      ["Top heading face", `${fmt(S.th, 1)} m (rounds of ${zTh.th} m)`],
      ["Bench face", `${fmt(S.bench, 1)} m, ${fmt(S.th - S.bench, 1)} m behind`],
      ["Invert / ring closure", zTh.invert ? `${fmt(S.invert, 1)} m, ${fmt(invLag, 1)} m behind the face (limit ${D} m)` : "not required in this class"],
      ["Pre-support", cls.presupport],
      ["Advance so far", rateRow],
    ]);
    dl(ui.ground, [
      ["Rock at the face", `${zTh.name} (GSI ${zTh.gsi}, σci ${zTh.sci} MPa)`],
      ["Rock-mass strength, modulus", `${fmt(g.mc.sigma_cm, 1)} MPa, ${fmt(g.mc.e_rm / 1000, 2)} GPa`],
      ["Squeezing (Hoek & Marinos)", `${fmt(g.strain, 2)} %, class ${g.squeeze[0]}`],
      ["Unsupported closure", `${fmt(g.free.u * 1000, 0)} mm (radial), plastic zone ${fmt(g.free.r_p / R, 2)} R`],
      ["Lining", `${fmt(zTh.lining * 1000, 0)} mm shotcrete with lattice girders (FHWA ${cls.lining_mm[0]}–${cls.lining_mm[1]} mm)`],
      ...shotRows(1),
      ["Lining load (closed ring, Oreste)", `${fmt(g.li.p_final, 2)} MPa; 95 % reached after ${hours(g.li.hours_to_95)}`],
      ["Lining safety (strength / stress)", `${fmt(g.li.min_safety, 2)} at minimum, ${hours(g.li.min_safety_age_h)} after spraying`],
      ["Predicted convergence", `${fmt(g.predictedMm, 1)} mm (diametral, after spraying)`],
    ]);
  }

  // monitoring table: the latest sections
  for (const s of sections) {
    const pred = groundAt(zoneAt(s.ch), ui.shot.value).predictedMm;
    s.c = reading(s);
    s.rate = (reading(s, S.simTime) - reading(s, S.simTime - 86400)) * 30; // mm per month over the last day
    s.level = triggerLevel(s.c, pred);
    s.pred = pred;
  }
  const rows = sections.slice(-7).reverse().map((s) => `<tr><td>${s.ch} m</td><td>${fmt(S.th - s.ch, 0)} m</td><td>${fmt(s.c, 1)}</td><td>${fmt(s.pred, 1)}</td><td>${fmt(s.rate, 1)}</td><td><span class="lvl ${s.level}">${s.level}</span></td><td>${s.rate < FINAL_LINING_RATE_MM_PER_MONTH && S.th - s.ch > 3 * D ? "yes" : "no"}</td></tr>`).join("");
  const what = FARR ? "Crown mm" : "Conv. mm";
  ui.monitor.innerHTML = `<table class="mon"><tr><th>Section</th><th>To face</th><th>${what}</th><th>Pred. mm</th><th>mm/month</th><th>Level</th><th>Final lining</th></tr>${rows}</table>
    <p class="note">${FARR ? "Prisms every" : "Five targets per section every"} ${SECTION_SPACING} m${FARR ? ", read by total station (CG)" : ""}. Levels at 75 / 105 / 150 % of the predicted ${FARR ? "crown settlement" : "convergence"} (Crossrail). Final lining once the rate is below ${FINAL_LINING_RATE_MM_PER_MONTH} mm/month (FHWA).</p>`;

  const alarms = [];
  if (zTh.invert && !ringClosureOk(invLag, D)) alarms.push(`Ring not closed within one diameter: invert ${fmt(invLag, 1)} m behind the face (FHWA: within ${D} m in this ground)`);
  if (g.li.min_safety < 1.0) alarms.push(`Lining overstressed in this ground (safety ${fmt(g.li.min_safety, 2)}): thicker lining, yielding elements or earlier closure needed`);
  if (!FARR && g.strain >= 2.5) alarms.push(`Squeezing class ${g.squeeze[0]}: ${g.squeeze[2]}`);
  if (FARR && g.n >= 6) alarms.push(`Stability ratio ${fmt(g.n, 1)} at the open face: face support or ground treatment needed`);
  for (const s of sections.filter((x) => x.level === "red" || x.level === "amber").slice(-3)) {
    alarms.push(s.level === "red" ? `Section ${s.ch} m at RED (${fmt(s.c, 1)} mm, ≥ 150 % of prediction): stop, make the face safe, emergency review` : `Section ${s.ch} m at AMBER (${fmt(s.c, 1)} mm): inspection and engineering review within 24 h`);
  }
  ui.alarms.innerHTML = alarms.length ? alarms.map((a) => `<div>${a}</div>`).join("") : `<div class="ok">Within limits</div>`;
}

ui.pause.onclick = () => { S.paused = !S.paused; ui.pause.textContent = S.paused ? "Resume" : "Pause"; };
// Reset puts the camera back on the heading view at the new face.
const toHeading = () => { shiftViews(S.th); camera.position.set(...VIEWS.heading.pos); controls.target.set(...VIEWS.heading.target); controls.update(); lastFace = S.th; };
ui.reset.onclick = () => { reset(); toHeading(); ui.pause.textContent = "Pause"; };
ui.start.onchange = ui.reset.onclick;
ui.shot.onchange = () => { groundCache.clear(); };
if (innerWidth <= 640) ui.showLabels.checked = false;

// ---------------------------------------------------------------- loop
reset();
const shiftViews = (face) => { for (const v of Object.values(VIEWS)) { v.pos[2] = v.pos0 - face; v.target[2] = v.target0 - face; } };
for (const v of Object.values(VIEWS)) { v.pos0 = v.pos[2]; v.target0 = v.target[2]; }
toHeading();
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
