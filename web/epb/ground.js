// Phase 2, WP6 and WP7: "Ground physics" panel.
//
// It shows the GPU MPM dry-sand face benchmark (Idinger et al. 2011 prototype, D 5 m), not the demo's own ground:
// coupling to the demo's ground and chamber waits on WP3 and WP4 (docs/plans/phase2-mpm-face-chamber.md). Every
// number is shown with its calibration label and the references it is checked against
// (docs/validation/mpm-face-sand.md).
//
// - Recording (default, WP7): plays recordings/face-sand-cd1.tsr.gz, a TSR0 replay recorded on the GPU server
//   (python -m tunnelsim_server.record): support held above the limit, lowered below it, then raised again.
// - Live (local only, WP6): with ?ground=ws://127.0.0.1:8765 and a running live server (python -m
//   tunnelsim_server.live, see server/README.md), the operator sets the support pressure. Wire format: TSP0 frames
//   (phase0/stream/stream_server.py), encoding 2, u16 xyz + u8 attribute (displacement since the last reset,
//   255 = 0.02 D), plus JSON probe messages.

const RECORDING = "recordings/face-sand-cd1.tsr.gz";
const fmt = (v, d = 1) => (v == null || Number.isNaN(v) ? "–" : Number(v).toFixed(d));

function decodeTsp0(buf) {
  const dv = new DataView(buf);
  if (dv.getUint32(0, true) !== 0x30505354 || dv.getUint32(20, true) !== 2) return null;
  const n = dv.getUint32(16, true);
  const lo = [0, 1, 2].map((k) => dv.getFloat32(24 + 4 * k, true));
  const st = [0, 1, 2].map((k) => dv.getFloat32(36 + 4 * k, true));
  const q = new Uint16Array(buf, 48, 3 * n), attr = new Uint8Array(buf, 48 + 6 * n, n);
  const xs = new Float32Array(n), zs = new Float32Array(n);
  for (let i = 0, j = 0; i < n; i++, j += 3) { xs[i] = lo[0] + q[j] * st[0]; zs[i] = lo[2] + q[j + 2] * st[2]; }
  return { n, xs, zs, attr };
}

// TSR0 replay (server/tunnelsim_server/replay.py): gzip; magic, JSON length, JSON, u16[3N] frame 0, i16[3N] deltas
async function loadTsr0(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`could not load ${url} (${res.status})`);
  let buf = await res.arrayBuffer();
  const h = new Uint8Array(buf, 0, 2);
  if (h[0] === 0x1f && h[1] === 0x8b) buf = await new Response(new Blob([buf]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
  const dv = new DataView(buf);
  if (dv.getUint32(0, true) !== 0x30525354) throw new Error("not a TSR0 replay");
  const len = dv.getUint32(4, true);
  const meta = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 8, len)));
  const n = meta.particles, base = 8 + len, stride = 6 * n;
  return { meta, n, frame0: new Uint16Array(buf, base, 3 * n), delta: (k) => new Int16Array(buf, base + k * stride, 3 * n) };
}

function start(url) {
  const consoleEl = document.getElementById("console");
  const sec = document.createElement("section");
  sec.id = "groundPhysics";
  sec.innerHTML = `
    <h2>Ground physics (GPU MPM)</h2>
    <div><span class="flag warn" id="gpLabel">Uncalibrated</span> <span id="gpStatus" class="flag">loading…</span></div>
    <p class="note" id="gpScene">Dry-sand face benchmark, not the demo's ground.</p>
    <canvas id="gpView" width="640" height="300" style="width:100%;height:auto;display:block;margin:6px 0;background:#101215;border-radius:6px"></canvas>
    <div class="legend"><span style="--c:#c8b48c">at rest</span><span style="--c:#b2182b">moved ≥ 2 % of D</span><span style="--c:#9aa1aa">shield and support plate</span></div>
    <label>Support pressure at the face <output id="gpTargetOut"></output><input id="gpTarget" type="range" min="0" max="30" step="0.5" value="20"></label>
    <div class="buttons"><button id="gpReset">Reset the face</button></div>
    <dl id="gpProbe"></dl>
    <p class="note" id="gpNote"></p>`;
  const limits = [...consoleEl.querySelectorAll("section")].find((s) => /Model limits/i.test(s.querySelector("h2")?.textContent || ""));
  consoleEl.insertBefore(sec, limits || null);

  const cv = sec.querySelector("#gpView");
  const ctx = cv.getContext("2d");
  const img = ctx.createImageData(cv.width, cv.height);
  const px = new Uint32Array(img.data.buffer);
  const target = sec.querySelector("#gpTarget");
  const targetOut = sec.querySelector("#gpTargetOut");
  const status = sec.querySelector("#gpStatus");
  const reset = sec.querySelector("#gpReset");
  let probe = null, frame = null;

  // colour ramp from the sand colour to dark red, as ABGR words for the image buffer
  const c0 = [200, 180, 140], c1 = [178, 24, 43];
  const ramp = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    const [r, g, b] = c0.map((a, k) => Math.round(a + (c1[k] - a) * t));
    ramp[i] = (255 << 24) | (b << 16) | (g << 8) | r;
  }

  function showProbe(mode) {
    const p = probe, r = p.references, sc = p.scene;
    sec.querySelector("#gpScene").textContent =
      `${sc.name}: D ${sc.diameter_m} m, C/D ${sc.cover_over_D}, φ′ ${sc.phi_deg}°, γ ${sc.gamma_kN_m3} kN/m³, grid D/${sc.voxel_per_D}. Not the demo's ground.`;
    sec.querySelector("#gpLabel").title = p.label;
    const moving = !p.settling && p.p_face_kPa > p.target_kPa + 0.5;
    const rows = [
      ["Face pressure (MPM)", `${fmt(p.p_face_kPa)} kPa`],
      ["Face movement", `${fmt(p.retraction_mm, 0)} mm, ${fmt(p.retraction_over_D * 100, 2)} % of D${p.settling ? " (settling)" : moving ? " (giving way)" : ""}`],
      ["Measured limit", r.idinger_measured_kPa ? `${r.idinger_measured_kPa[0]}–${r.idinger_measured_kPa[1]} kPa (Idinger 2011)` : "–"],
      ["MPM bracket", `${fmt(r.triaxial_kPa)}–${fmt(r.plane_strain_kPa)} kPa at 5 % of D`],
      ["Analytical", `${fmt(r.vermeer_kPa)} kPa (Vermeer 2002)`],
      mode === "live" ? ["Speed", `${fmt(p.realtime_factor, 2)}× real time`]
        : ["Recording", `${fmt(p.t, 1)} of ${fmt(p.duration, 0)} s, played in real time; recorded on the GPU server at ${p.run.git}`],
    ];
    sec.querySelector("#gpProbe").innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    sec.querySelector("#gpNote").innerHTML =
      `${p.label}. Section through the tunnel axis (half model), ${p.shown.toLocaleString()} of ${p.particles.toLocaleString()} particles shown. ` +
      (mode === "live" ? "" : "To set the pressure yourself, run the live server (server/README.md). ") +
      `Checks: <a href="https://github.com/dtt-github/tunnel-construction-simulation/blob/main/${p.validation}" target="_blank" rel="noopener">validation page</a>.`;
  }

  function draw() {
    requestAnimationFrame(draw);
    if (!frame || !probe) return;
    const { n, xs, zs, attr } = frame;
    const W = cv.width, H = cv.height, sc = probe.scene;
    const xmin = sc.box_m[0][0], xmax = sc.box_m[1][0];
    const s = Math.min(W / (xmax - xmin), H / (sc.surface_z_m * 1.05));
    const ox = (W - s * (xmax - xmin)) / 2;
    const X = (x) => ox + (x - xmin) * s, Z = (z) => H - z * s;
    const dot = Math.max(1, Math.ceil(sc.spacing_m * s));
    px.fill(0xff151210);
    for (let i = 0; i < n; i++) {
      const u = X(xs[i]) | 0, v = Z(zs[i]) | 0;
      if (u < 0 || v < 0 || u + dot > W || v + dot > H) continue;
      const c = ramp[attr[i]];
      for (let a = 0; a < dot; a++) px.fill(c, (v + a) * W + u, (v + a) * W + u + dot);
    }
    ctx.putImageData(img, 0, 0);
    // shield tube (top and bottom of the bore) and the support plate
    const R = sc.diameter_m / 2, zc = sc.axis_z_m, xp = -probe.retraction_mm / 1000;
    ctx.strokeStyle = "#9aa1aa"; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(X(xmin), Z(zc + R)); ctx.lineTo(X(0), Z(zc + R));
    ctx.moveTo(X(xmin), Z(zc - R)); ctx.lineTo(X(0), Z(zc - R));
    ctx.stroke();
    ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(X(xp), Z(zc - R)); ctx.lineTo(X(xp), Z(zc + R)); ctx.stroke();
    ctx.fillStyle = "#e7e9ec"; ctx.font = "12px system-ui";
    ctx.fillText(`support ${fmt(probe.target_kPa)} kPa · face ${fmt(probe.p_face_kPa)} kPa · t ${fmt(probe.t, 1)} s`, 8, 16);
  }
  requestAnimationFrame(draw);

  function live(url) {
    let ws = null;
    const send = (m) => { if (ws && ws.readyState === 1) ws.send(JSON.stringify(m)); };
    target.oninput = () => { targetOut.textContent = `${fmt(+target.value, 1)} kPa`; send({ target_kpa: +target.value }); };
    targetOut.textContent = `${fmt(+target.value, 1)} kPa`;
    reset.onclick = () => send({ reset: true });
    const connect = () => {
      ws = new WebSocket(url);
      ws.binaryType = "arraybuffer";
      ws.onopen = () => { status.textContent = "live, local server"; status.className = "flag ok"; send({ target_kpa: +target.value }); };
      ws.onclose = () => { status.textContent = "no server, retrying"; status.className = "flag bad"; setTimeout(connect, 3000); };
      ws.onmessage = (ev) => {
        if (typeof ev.data === "string") { probe = JSON.parse(ev.data); showProbe("live"); } else frame = decodeTsp0(ev.data) || frame;
      };
    };
    connect();
  }

  async function replay() {
    target.disabled = true;
    reset.textContent = "Restart the recording";
    let rec;
    try {
      rec = await loadTsr0(new URL(RECORDING, import.meta.url));
    } catch (e) {
      status.textContent = "recording not available"; status.className = "flag bad";
      return;
    }
    const { meta, n, frame0, delta } = rec, m = meta.scene, sc = meta.scalars, F = meta.frames;
    status.textContent = "recorded GPU run"; status.className = "flag";
    const lo = meta.lo, step = meta.step, D = m.diameter_m, k0 = m.control_start_frame ?? 0;
    const q = Int32Array.from(frame0);
    const xs = new Float32Array(n), ys = new Float32Array(n), zs = new Float32Array(n), attr = new Uint8Array(n);
    const x0 = new Float32Array(n), y0 = new Float32Array(n), z0 = new Float32Array(n);
    let k = -1, last = performance.now(), acc = Infinity;
    reset.onclick = () => { q.set(frame0); k = -1; acc = Infinity; };
    const decodeInto = (ax, ay, az) => {
      for (let i = 0, j = 0; i < n; i++, j += 3) { ax[i] = lo[0] + q[j] * step; ay[i] = lo[1] + q[j + 1] * step; az[i] = lo[2] + q[j + 2] * step; }
    };
    // move the replay state on to frame k (deltas applied in order; positions at the control start kept for colour)
    const advance = () => {
      k += 1;
      if (k >= F) k = 0; // loop
      if (k === 0) q.set(frame0);
      else { const d = delta(k); for (let j = 0; j < q.length; j++) q[j] += d[j]; }
      if (k === k0) decodeInto(x0, y0, z0);
    };
    const tick = (now) => {
      requestAnimationFrame(tick);
      acc += (now - last) / 1000; last = now;
      if (acc < 1 / meta.fps) return;
      // advance as many recorded frames as real time has passed (a slow display drops frames, not time)
      let steps = Number.isFinite(acc) ? Math.min(Math.floor(acc * meta.fps), 30) : 1;
      acc = Number.isFinite(acc) ? acc - steps / meta.fps : 0;
      while (steps-- > 0) advance();
      decodeInto(xs, ys, zs);
      for (let i = 0; i < n; i++) attr[i] = k < k0 ? 0 : Math.min(255, Math.hypot(xs[i] - x0[i], ys[i] - y0[i], zs[i] - z0[i]) / (0.02 * D) * 255);
      frame = { n, xs, zs, attr };
      probe = {
        scene: m, label: m.label, validation: m.validation, references: m.references, run: m.run, particles: m.particles_total, shown: n,
        t: sc.t[k], duration: sc.t[F - 1], settling: k < k0, p_face_kPa: sc.p_face_kPa[k], target_kPa: sc.target_kPa[k],
        retraction_mm: sc.retraction_mm[k], retraction_over_D: sc.retraction_mm[k] / 1000 / D,
      };
      target.value = sc.target_kPa[k];
      targetOut.textContent = `${fmt(sc.target_kPa[k], 1)} kPa (recorded)`;
      showProbe("replay");
    };
    requestAnimationFrame(tick);
  }

  if (url) live(url); else replay();
}

start(new URLSearchParams(location.search).get("ground"));
