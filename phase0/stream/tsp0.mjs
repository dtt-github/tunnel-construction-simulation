// Decoder for the "TSP0" particle frame (see stream_server.py for the layout).
// Shared by the Node benchmark client and the browser test page.

export const MAGIC = 0x30505354;

export function decodeFrame(buf, out) {
  const dv = new DataView(buf);
  if (dv.getUint32(0, true) !== MAGIC) throw new Error("bad magic");
  const frame = dv.getUint32(4, true);
  const sendTimeMs = dv.getFloat64(8, true);
  const n = dv.getUint32(16, true);
  const enc = dv.getUint32(20, true);
  const lo = [dv.getFloat32(24, true), dv.getFloat32(28, true), dv.getFloat32(32, true)];
  const st = [dv.getFloat32(36, true), dv.getFloat32(40, true), dv.getFloat32(44, true)];
  const positions = out && out.length === 3 * n ? out : new Float32Array(3 * n);
  let attr = null;
  if (enc === 0) {
    positions.set(new Float32Array(buf, 48, 3 * n));
  } else {
    const q = new Uint16Array(buf, 48, 3 * n);
    const [lx, ly, lz] = lo;
    const [sx, sy, sz] = st;
    for (let i = 0, j = 0; i < n; i++, j += 3) {
      positions[j] = lx + q[j] * sx;
      positions[j + 1] = ly + q[j + 1] * sy;
      positions[j + 2] = lz + q[j + 2] * sz;
    }
    if (enc === 2) attr = new Uint8Array(buf, 48 + 6 * n, n);
  }
  return { frame, sendTimeMs, n, enc, positions, attr };
}
