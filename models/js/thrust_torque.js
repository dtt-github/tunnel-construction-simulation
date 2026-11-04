// Shield thrust and cutterhead torque as sums of components (Shi et al. 2011), checked against built machines.
// Twin of models/py/tunnelsim_models/thrust_torque.py, which documents the equations. m, kPa, kN, kNm.

const GAMMA_W = 10;

// Built machines: installed (or stated working) torque and thrust, each with its source (same table as Python).
export const REFERENCE_MACHINES = Object.freeze([
  Object.freeze({"project": "Crossrail, London", "type": "epb", "diameter": 7.08, "torque_knm": 9800.0, "thrust_kn": null, "power_kw": 1920.0, "torque_kind": "installed", "verified": true, "source": "https://herrenknecht.com/en/references/referencesdetail/crossrail-london"}),
  Object.freeze({"project": "Mixed-face EPB (RETC 2019)", "type": "epb", "diameter": 6.6, "torque_knm": 7038.0, "thrust_kn": 45000.0, "power_kw": null, "torque_kind": "working", "verified": true, "source": "https://www.robbinstbm.com/wp-content/uploads/2019/07/RETC2019-14-05_Tunneling-in-Mixed-Face-Conditions.pdf"}),
  Object.freeze({"project": "Crossrail, London", "type": "slurry", "diameter": 7.08, "torque_knm": 3709.0, "thrust_kn": null, "power_kw": 1120.0, "torque_kind": "installed", "verified": true, "source": "https://herrenknecht.com/en/references/referencesdetail/crossrail-london"}),
  Object.freeze({"project": "Tuen Mun-Chek Lap Kok, Hong Kong", "type": "slurry", "diameter": 17.63, "torque_knm": 27722.0, "thrust_kn": null, "power_kw": 5600.0, "torque_kind": "installed", "verified": false, "source": "https://herrenknecht.com/en/references/referencesdetail/hong-kong-tuen-mun-chek-lap-kok-link"}),
  Object.freeze({"project": "Niagara Tunnel", "type": "gripper", "diameter": 14.4, "torque_knm": 18670.0, "thrust_kn": 18462.0, "power_kw": null, "torque_kind": "installed", "verified": false, "source": "https://www.robbinstbm.com/projects/niagara-tunnel-project/"}),
  Object.freeze({"project": "Gotthard Base Tunnel", "type": "gripper", "diameter": 9.33, "torque_knm": 5290.0, "thrust_kn": 27488.0, "power_kw": 3500.0, "torque_kind": "installed", "verified": false, "source": "trade press via search (Tunnelbuilder)"}),
]);

/** Vertical stress at `depth` (kPa); effective by default. */
export function verticalStress(depth, gamma, { gammaSub = null, waterDepth = Infinity, q = 0, effective = true } = {}) {
  const gsub = gammaSub ?? gamma - GAMMA_W;
  const hw = Math.min(Math.max(waterDepth, 0), depth);
  const sv = q + gamma * hw + gsub * (depth - hw);
  return effective ? sv : sv + GAMMA_W * (depth - hw);
}

/** Thrust components (kN). pAxis: support pressure at the axis (kPa); weights in kN. */
export function shieldThrust(diameter, shieldLength, axisDepth, gamma, pAxis, {
  gammaSub = null, waterDepth = Infinity, q = 0, k0 = 0.5, muShield = 0.17, contact = 1, shieldWeight = 0,
  tools = 0, tailSeal = 0, backupWeight = 0, muBackup = 0.1,
} = {}) {
  if (diameter <= 0 || shieldLength <= 0 || axisDepth <= diameter / 2) {
    throw new RangeError("need positive sizes and the axis deeper than the radius");
  }
  const sigmaN = (verticalStress(axisDepth, gamma, { gammaSub, waterDepth, q }) * (1 + k0)) / 2;
  const t = {
    face: (pAxis * Math.PI * diameter ** 2) / 4,
    shield: muShield * (contact * Math.PI * diameter * shieldLength * sigmaN + shieldWeight),
    tools,
    tail_seal: tailSeal,
    backup: muBackup * backupWeight,
  };
  t.total = t.face + t.shield + t.tools + t.tail_seal + t.backup;
  return t;
}

/** Torque of n scrapers/rippers with tangential force Ft (kN) at mean radius f R (kNm). */
export const toolTorque = (nTools, tangentialForce, radius, radiusFactor = 0.5) => nTools * tangentialForce * radiusFactor * radius;

/** Cutterhead torque components (kNm). sigmaN: radial ground stress on the rim (kPa). */
export function cutterheadTorque(diameter, pAxis, sigmaN, {
  openingRatio = 0.3, mu = 0.15, muRim = 0.07, muChamber = 0.1, rimWidth = 0.5, nArms = 0, armArea = 0, armRadius = 0,
  tools = 0, seals = 0,
} = {}) {
  if (!(openingRatio >= 0 && openingRatio < 1)) throw new RangeError("opening ratio must be in [0, 1)");
  const r = diameter / 2;
  const disc = (2 / 3) * Math.PI * (1 - openingRatio) * r ** 3 * pAxis;
  const t = {
    tools,
    face: mu * disc,
    rim: 2 * Math.PI * r * r * rimWidth * muRim * sigmaN,
    back: muChamber * disc,
    arms: nArms * muChamber * pAxis * armArea * armRadius,
    seals,
  };
  t.total = t.tools + t.face + t.rim + t.back + t.arms + t.seals;
  return t;
}

/** Reference machines of one type scaled to `diameter` (torque by D^3, thrust by D^2), in kNm and kN. */
export function referenceInstalled(machineType, diameter, { includeUnverified = false } = {}) {
  const refs = REFERENCE_MACHINES.filter((m) => m.type === machineType && (includeUnverified || m.verified));
  const tq = refs.map((m) => m.torque_knm * (diameter / m.diameter) ** 3);
  const th = refs.filter((m) => m.thrust_kn !== null).map((m) => m.thrust_kn * (diameter / m.diameter) ** 2);
  return {
    torque: tq.length ? [Math.min(...tq), Math.max(...tq)] : null,
    thrust: th.length ? [Math.min(...th), Math.max(...th)] : null,
    machines: refs.map((m) => m.project),
  };
}
