// EPB excavation chamber: support pressure from a volume balance (Boyle's law for foam air), foam conditioning
// (EFNARC 2005) and the screw conveyor (simplified from Merritt & Mair 2006, 2008; entrance drop and decay length
// calibrated on the Botlek screw gauges, Bezuijen et al. 2005).
// Twin of models/py/tunnelsim_models/epb_chamber.py, which documents the equations. m, s, kPa gauge, rpm.

export const P_ATM = 101.325;

/** Foam liquid and foam air (at atmospheric pressure) flows for FIR (fraction) and FER. */
export function foamSplit(qSoil, fir, fer) {
  if (fer < 1) throw new RangeError("FER must be at least 1");
  const qFoam = fir * qSoil;
  return [qFoam / fer, qFoam * (1 - 1 / fer)];
}

export function screw({ diameter = 0.9, shaftDiameter = 0.3, pitch = 0.7, length = 12, efficiency = 0.6, decayLength = 16, entranceFactor = 0.85 } = {}) {
  const theoreticalFlow = (rpm) => ((Math.PI * (diameter ** 2 - shaftDiameter ** 2)) / 4) * pitch * (rpm / 60);
  const discharge = (rpm) => efficiency * theoreticalFlow(rpm);
  const pressureAlong = (s, pIn) => pIn * entranceFactor * Math.exp(-s / decayLength);
  return {
    diameter, shaftDiameter, pitch, length, efficiency, decayLength, entranceFactor,
    theoreticalFlow,
    discharge,
    rpmForFlow: (q) => q / discharge(1),
    pressureAlong,
    outletPressure: (pIn) => pressureAlong(length, pIn),
  };
}

/** Chamber of `volume` m^3; state = { v_inc, v_air } as volumes at atmospheric pressure. */
export function chamber(volume, kSolid = 100000) {
  const pressure = ({ v_inc, v_air }) => {
    const b = v_inc - volume;
    if (b + v_air <= 0) return 0;
    const a = v_inc / kSolid;
    const bb = b - a * P_ATM;
    const cc = P_ATM * (b + v_air);
    if (a === 0) return cc / -bb;
    const disc = Math.sqrt(bb * bb + 4 * a * cc);
    return bb >= 0 ? (bb + disc) / (2 * a) : (2 * cc) / (disc - bb);
  };
  const steadyState = (qExc, qScrew, fir = 0, fer = 10) => {
    const [qLiq, qAir] = foamSplit(qExc, fir, fer);
    return { v_inc: ((qExc + qLiq) * volume) / qScrew, v_air: (qAir * volume) / qScrew };
  };
  return {
    volume,
    kSolid,
    pressure,
    fill: (st) => Math.min((st.v_inc + st.v_air) / volume, 1),
    airFraction: (st) => (st.v_air * P_ATM) / (pressure(st) + P_ATM) / volume,
    stateAt(p, airFraction) {
      const air = airFraction * volume;
      return { v_inc: (volume - air) / (1 - p / kSolid), v_air: (air * (p + P_ATM)) / P_ATM };
    },
    step(st, dt, qExc, qScrew, fir = 0, fer = 10) {
      const [qLiq, qAir] = foamSplit(qExc, fir, fer);
      const k = qScrew / volume;
      if (k <= 0) return { v_inc: st.v_inc + (qExc + qLiq) * dt, v_air: st.v_air + qAir * dt };
      const e = Math.exp(-k * dt);
      const go = (x, s) => x * e + (s / k) * (1 - e);
      return { v_inc: go(st.v_inc, qExc + qLiq), v_air: go(st.v_air, qAir) };
    },
    steadyState,
    screwFlowForPressure(p, qExc, fir = 0, fer = 10) {
      let lo = 1e-9, hi = 1e3;
      for (let n = 0; n < 200; n++) {
        const mid = Math.sqrt(lo * hi);
        if (pressure(steadyState(qExc, mid, fir, fer)) > p) lo = mid;
        else hi = mid;
      }
      return Math.sqrt(lo * hi);
    },
    stiffness(st) {
      const h = 1e-6 * volume;
      return (pressure({ v_inc: st.v_inc + h, v_air: st.v_air }) - pressure({ v_inc: st.v_inc - h, v_air: st.v_air })) / (2 * h);
    },
  };
}

/** Chamber pressure at the crown from the axis value and the paste unit weight (kN/m^3). */
export const crownPressure = (pAxis, radius, unitWeight = 12) => Math.max(pAxis - unitWeight * radius, 0);
