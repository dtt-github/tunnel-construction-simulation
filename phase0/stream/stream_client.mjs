// Phase 0: WebSocket particle streaming benchmark (Node client).
// Usage: node stream_client.mjs ws://127.0.0.1:8765
// Decodes every frame into a Float32Array (what a three.js BufferGeometry needs) and prints
// received rate, throughput, latency and decode time as JSON when the server closes.

import { decodeFrame } from "./tsp0.mjs";

const url = process.argv[2] ?? "ws://127.0.0.1:8765";
const ws = new WebSocket(url);
ws.binaryType = "arraybuffer";

let positions = null;
const arrivals = [];
const latency = [];
const decodeMs = [];
let bytes = 0;
let lastFrame = -1;
let dropped = 0;

ws.onmessage = (ev) => {
  const tRecv = Date.now();
  const t0 = performance.now();
  const f = decodeFrame(ev.data, positions);
  positions = f.positions;
  decodeMs.push(performance.now() - t0);
  latency.push(tRecv - f.sendTimeMs);
  arrivals.push(t0);
  bytes += ev.data.byteLength;
  if (lastFrame >= 0 && f.frame !== lastFrame + 1) dropped += f.frame - lastFrame - 1;
  lastFrame = f.frame;
};

const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;
const pct = (a, p) => [...a].sort((x, y) => x - y)[Math.min(a.length - 1, Math.floor((p / 100) * a.length))];

ws.onclose = () => {
  const span = (arrivals.at(-1) - arrivals[0]) / 1000;
  const gaps = arrivals.slice(1).map((t, i) => t - arrivals[i]);
  console.log(
    JSON.stringify({
      client: {
        frames: arrivals.length,
        dropped,
        fps: +((arrivals.length - 1) / span).toFixed(2),
        MB_per_s: +(bytes / 1e6 / span).toFixed(1),
        latency_ms_mean: +mean(latency).toFixed(2),
        latency_ms_p95: pct(latency, 95),
        frame_gap_ms_p95: +pct(gaps, 95).toFixed(2),
        decode_ms_mean: +mean(decodeMs).toFixed(3),
        decode_ms_p95: +pct(decodeMs, 95).toFixed(3),
      },
    }),
  );
};
ws.onerror = (e) => {
  console.error("websocket error", e.message ?? e);
  process.exit(1);
};
