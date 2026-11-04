// Slice B: hard-rock TBMs in the browser. Shared drive, geology, cutting model and console; the machine (open gripper
// or double shield, chosen with ?machine=) builds its own parts and runs its own cycle (gripper.js, double.js).

import {
  tbmPerformance, maxRpm, PRACTICAL_MAX_PENETRATION_MM, DEFAULT_CUTTER, hardRockUtilisation, rmrClass, cuttersPerKm,
  cutterChangeHPerKm, recordCheck,
} from "../../models/js/index.js";
import { THREE, createScene, buildRock, placeLabels, fmt, dl } from "./common.js";
import * as gripperDef from "./gripper.js";
import * as doubleDef from "./double.js";

const KIND = new URLSearchParams(location.search).get("machine") === "double" ? "double" : "gripper";
const DEF = KIND === "double" ? doubleDef : gripperDef;
const M = DEF.M;
const RPM_MAX = maxRpm(M.D);

// Illustrative alignment; strengths, CAI, quartz and RMR typical for the rock types (not a project).
const ZONES = [
  { name: "Gneiss", from: -80, to: 90, ucs: 150, bts: 10, cai: 3.5, quartz: 25, rmr: 70, color: 0x8a8f94 },
  { name: "Granite", from: 90, to: 170, ucs: 180, bts: 12, cai: 4.5, quartz: 30, rmr: 76, color: 0xa39488 },
  { name: "Fault zone (crushed, blocky)", from: 170, to: 215, ucs: 40, bts: 4, cai: 2.5, quartz: 15, rmr: 22, color: 0x6b5848 },
  { name: "Mica schist", from: 215, to: 330, ucs: 90, bts: 7, cai: 2.5, quartz: 15, rmr: 50, color: 0x7d8466 },
  { name: "Gneiss", from: 330, to: 700, ucs: 150, bts: 10, cai: 3.5, quartz: 25, rmr: 68, color: 0x8a8f94 },
];
const zoneAt = (ch) => ZONES.find((z) => ch >= z.from && ch < z.to) ?? ZONES.at(-1);

// ---------------------------------------------------------------- scene
document.title = KIND === "double" ? "Hard-Rock Double Shield TBM" : "Hard-Rock Gripper TBM";
document.getElementById("title").textContent = M.title;
document.getElementById("machineLimits").innerHTML = M.limits.map((t) => `<li>${t}</li>`).join("");
const { renderer, scene, camera, updateCamera } = createScene(DEF.VIEWS);
const machine = new THREE.Group();
scene.add(machine);
const world = new THREE.Group();
scene.add(world);
buildRock(world, ZONES, M.D / 2);
const parts = DEF.build(machine, world);

// ---------------------------------------------------------------- UI and state
const ids = ["machine", "start", "thrust", "rpm", "haulage", "org", "ts", "thrustOut", "rpmOut", "tsOut", "pause", "skip", "reset", "alarms", "cutting",
  "cycle", "rock", "forecast", "showLabels"];
const ui = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));
const val = (id) => +ui[id].value;
ui.machine.value = KIND;
ui.machine.onchange = () => { location.search = `?machine=${ui.machine.value}`; };
ui.rpm.max = RPM_MAX.toFixed(1);

const NAMES = { tbm_breakdown: "TBM repairs", backup: "backup", cutters: "cutter changes", support: KIND === "double" ? "segments and support" : "rock support",
  maintenance: "maintenance", transport: "transport", utilities: "utility extension", survey: "survey", other: "other", regrip: "regrip", boring: "boring" };
const COLORS = { boring: "#3987e5", regrip: "#7f8c99", tbm_breakdown: "#d95926", backup: "#c9a227", cutters: "#b07ad9", support: "#ff7a45",
  maintenance: "#199e70", transport: "#5fa8d3", utilities: "#9ccc65", survey: "#e0a24a", other: "#4b5560" };

let S;
function reset() {
  const start = val("start");
  S = { chainage: start, stroke: 0, mode: "BORING", simTime: 0, paused: false, perf: null, util: null, rpm: 0, regripT: 0,
    stopLeft: 0, stopText: "", boringTime: 0, cuttersUsed: 0 };
  world.position.z = start;
  parts.reset(S, zoneAt);
}
reset();

const orgClass = () => ui.org.value;
function utilAt(zone, pr) {
  return hardRockUtilisation(Math.max(pr, 0.05), M.D, {
    stroke_m: M.stroke, regrip_min: M.regripMin, ucs_mpa: zone.ucs, rmr: zone.rmr, machine: M.utilMachine(zone), haulage: ui.haulage.value,
    cutter_h_per_km: cutterChangeHPerKm(M.D, zone.cai), maintenance: orgClass(), transport: orgClass(), ...(parts.utilOptions?.(zone) ?? {}),
  });
}

// Shared cycle helpers for the machine modules.
const ctx = {
  zone: null,
  bore(adv) {
    S.stroke += adv;
    S.chainage += adv;
    if (S.perf.rop_m_h > 0) S.boringTime += adv / (S.perf.rop_m_h / 3600);
    S.cuttersUsed += (cuttersPerKm(M.D, ctx.zone.cai) * adv) / 1000;
    parts.muck.add(Math.PI * (M.D / 2) ** 2 * adv * 1.6);
  },
  /** Stop for this stroke's share of the per-km downtime, except the listed categories; hoursDone is time already spent
   * explicitly in the cycle (a ring build) and is taken off the support term. */
  startStop(exclude, hoursDone = 0) {
    const parts2 = Object.entries(S.util.h_per_km).filter(([k]) => !exclude.includes(k)).map(([k, v]) => [k, (v * M.stroke) / 1000]);
    const sup = parts2.find(([k]) => k === "support");
    if (sup) sup[1] = Math.max(sup[1] - hoursDone, 0);
    parts2.sort((a, b) => b[1] - a[1]);
    S.stopLeft = parts2.reduce((a, [, v]) => a + v, 0) * 3600;
    S.stopText = parts2.slice(0, 3).filter(([, v]) => v > 0.005).map(([k, v]) => `${NAMES[k]} ${fmt(v * 60, 0)} min`).join(", ");
    S.mode = "STOPPED";
  },
  stopStep(dt) {
    S.stopLeft -= dt;
    if (S.stopLeft <= 0) { S.mode = "BORING"; S.stopLeft = 0; }
  },
};

function substep(dt) {
  const zone = zoneAt(S.chainage);
  ctx.zone = zone;
  S.rpm = Math.min(val("rpm"), RPM_MAX);
  S.perf = tbmPerformance({ thrust_kn: val("thrust"), rpm: S.rpm, n_cutters: M.nCutters, head_diameter_m: M.D, ucs_mpa: zone.ucs, bts_mpa: zone.bts,
    max_torque_knm: M.torque, max_power_kw: M.power, max_penetration_mm: PRACTICAL_MAX_PENETRATION_MM });
  S.util = utilAt(zone, S.perf.rop_m_h);
  S.simTime += dt;
  if (dt > 0) parts.step(S, dt, ctx);
}
function step(dtReal) {
  if (!S.perf) substep(0); // first frame and after a reset: evaluate the cutting state once
  if (!S.paused) {
    let dt = dtReal * val("ts");
    while (dt > 1e-9) { const h = Math.min(dt, 2); substep(h); dt -= h; }
  }
  parts.afterStep(S, zoneAt);
}

// ---------------------------------------------------------------- console
function hud() {
  ui.thrustOut.textContent = `${fmt(val("thrust") / 1000, 2)} MN`;
  ui.rpmOut.textContent = `${fmt(Math.min(val("rpm"), RPM_MAX), 1)} rpm`;
  ui.tsOut.textContent = `×${val("ts")}`;
  const zone = zoneAt(S.chainage), p = S.perf, cls = rmrClass(zone.rmr);
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
  const modeText = parts.modeText(S, fmt) ?? `STOPPED: ${S.stopText} (${fmt(S.stopLeft / 3600, 1)} h left)`;
  ui.skip.disabled = S.mode !== "STOPPED";
  dl(ui.cycle, [
    ["Mode", modeText],
    ["Chainage", `${fmt(S.chainage, 1)} m`],
    ["Simulated time", `${Math.floor(S.simTime / 3600)} h ${String(Math.floor((S.simTime % 3600) / 60)).padStart(2, "0")} min`],
    ["Achieved", days > 0.05 ? `${fmt(S.chainage - val("start"), 1)} m in ${fmt(days, 1)} days = ${fmt((S.chainage - val("start")) / days, 1)} m/day · utilisation ${fmt((S.boringTime / S.simTime) * 100, 0)} %` : "—"],
    ["Cutters used", `${fmt(S.cuttersUsed, 1)} (${fmt(cuttersPerKm(M.D, zone.cai), 0)} per km in this rock)`],
  ]);
  dl(ui.rock, [
    ["Rock at the face", zone.name],
    ["UCS, BTS", `${zone.ucs} MPa, ${zone.bts} MPa`],
    ["CAI, quartz", `${zone.cai}, ${zone.quartz} %`],
    ["RMR, class", `${zone.rmr}, ${cls.class} (${cls.name})`],
    ...parts.supportRows(zone),
    ["Next zone", (() => { const n = ZONES.find((z) => z.from > S.chainage); return n ? `${n.name} in ${fmt(n.from - S.chainage, 0)} m` : "—"; })()],
  ]);
  const alarms = [];
  if (p.cutter_overloaded) alarms.push(`Cutter overload: ${fmt(p.normal_per_cutter_kn, 0)} kN per disc above the ${DEFAULT_CUTTER.max_load_kn} kN rating`);
  if (p.limited_by === "penetration") alarms.push("Penetration at the muck-handling cap: excess thrust is not used; in blocky ground expect overbreak");
  if (p.limited_by === "torque" || p.limited_by === "power") alarms.push(`Cutterhead at its ${p.limited_by} limit: more thrust does not cut faster`);
  if (val("rpm") > RPM_MAX) alarms.push(`Speed held at ${fmt(RPM_MAX, 2)} rpm (gauge-cutter speed limit)`);
  alarms.push(...parts.alarms(zone));
  ui.alarms.innerHTML = alarms.length ? alarms.map((a) => `<div>${a}</div>`).join("") : `<div class="ok">Within limits</div>`;

  const u = S.util;
  const sh = Object.entries(u.h_per_km).filter(([, v]) => v > 0);
  const rec = recordCheck(M.D, u.advance_m_day, u.advance_m_day * 7, u.advance_m_day * 30, KIND);
  ui.forecast.innerHTML = `<dl>
    <dt>In this rock, at this speed</dt><dd>${fmt(u.advance_m_day, 1)} m/day</dd>
    <dt>Utilisation</dt><dd>${fmt(u.utilisation * 100, 0)} %</dd>
    <dt>Total time per km</dt><dd>${fmt(u.total_h_per_km, 0)} h</dd>
    <dt>World record, ${M.D} m class</dt><dd>${fmt(rec.day.world_record, 1)} m best day</dd>
  </dl>
  <div class="shares">${sh.map(([k, v]) => `<i title="${NAMES[k]} ${fmt(v, 0)} h/km" style="width:${(100 * v) / u.total_h_per_km}%;background:${COLORS[k]}"></i>`).join("")}</div>
  <div class="legend">${sh.filter(([, v]) => v / u.total_h_per_km > 0.01).map(([k, v]) => `<span style="--c:${COLORS[k]}">${NAMES[k]} ${fmt(v, 0)}</span>`).join("")}</div>
  <p class="note">Hours per km by activity (Farrokh 2018), at the current rock, penetration rate, haulage and site organisation. Mean rates sit well below the class record, which is a best day.</p>`;
}

ui.pause.onclick = () => { S.paused = !S.paused; ui.pause.textContent = S.paused ? "Resume" : "Pause"; };
ui.reset.onclick = () => { reset(); ui.pause.textContent = "Pause"; };
ui.start.onchange = () => { reset(); ui.pause.textContent = "Pause"; };
ui.skip.onclick = () => { if (S.mode === "STOPPED") { S.simTime += S.stopLeft; S.stopLeft = 0; S.mode = "BORING"; } };
if (innerWidth <= 640) ui.showLabels.checked = false;

// ---------------------------------------------------------------- loop
step(0);
hud();
let last = performance.now(), hudT = 0;
renderer.setAnimationLoop((now) => {
  const dtReal = Math.min((now - last) / 1000, 1 / 20);
  last = now;
  step(dtReal);
  world.position.z = S.chainage;
  parts.animate(S, S.paused ? 0 : dtReal, zoneAt);
  parts.muck.update(S.paused ? 0 : dtReal);
  updateCamera(dtReal);
  if ((hudT += dtReal) > 0.15) { hudT = 0; hud(); }
  placeLabels(camera, ui.showLabels.checked);
  renderer.render(scene, camera);
});
