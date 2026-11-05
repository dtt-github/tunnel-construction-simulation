// Phase 2, WP6 (face only): "Ground physics" panel, local use only. It appears only when the page is opened with
// ?ground=ws://127.0.0.1:8765 and a live server is running (python -m tunnelsim_server.live, see server/README.md).
// The public demo is unchanged without it.
//
// It shows the GPU MPM dry-sand face benchmark (Idinger et al. 2011 prototype, D 5 m), not the demo's own ground:
// coupling to the demo's ground and chamber waits on WP3 and WP4 (docs/plans/phase2-mpm-face-chamber.md). The
// operator sets the support pressure; above the limit the face holds, below it the face gives way. Every number is
// shown with its calibration label and the references it is checked against (docs/validation/mpm-face-sand.md).
//
// Wire format: TSP0 frames (phase0/stream/stream_server.py), encoding 2: u16 xyz + u8 attribute, here the
// displacement since the last reset (255 = 0.02 D), plus JSON probe messages.

const MAGIC = 0x30505354;

function decode(buf) {
  const dv = new DataView(buf);
  if (dv.getUint32(0, true) !== MAGIC || dv.getUint32(20, true) !== 2) return null;
  const n = dv.getUint32(16, true);
  const lo = [0, 1, 2].map((k) => dv.getFloat32(24 + 4 * k, true));
  const st = [0, 1, 2].map((k) => dv.getFloat32(36 + 4 * k, true));
  return { n, lo, st, q: new Uint16Array(buf, 48, 3 * n), attr: new Uint8Array(buf, 48 + 6 * n, n) };
}

const fmt = (v, d = 1) => (v == null || Number.isNaN(v) ? "–" : Number(v).toFixed(d));

function start(url) {
  const consoleEl = document.getElementById("console");
  const sec = document.createElement("section");
  sec.id = "groundPhysics";
  sec.innerHTML = `
    <h2>Ground physics (local MPM server)</h2>
    <div><span class="flag warn" id="gpLabel">Uncalibrated</span> <span id="gpStatus" class="flag">connecting…</span></div>
    <p class="note" id="gpScene">Dry-sand face benchmark, not the demo's ground.</p>
    <canvas id="gpView" width="640" height="300" style="width:100%;height:auto;display:block;margin:6px 0;background:#101215;border-radius:6px"></canvas>
    <div class="legend"><span style="--c:#c8b48c">at rest</span><span style="--c:#b2182b">moved ≥ 2 % of D</span><span style="--c:#9aa1aa">shield and support plate</span></div>
    <label>Support pressure at the face <output id="gpTargetOut"></output><input id="gpTarget" type="range" min="0" max="30" step="0.5" value="20"></label>
    <div class="buttons"><button id="gpReset">Reset the face</button></div>
    <dl id="gpProbe"></dl>
    <p class="note" id="gpNote"></p>`;
  consoleEl.insertBefore(sec, consoleEl.querySelector("section"));

  const cv = sec.querySelector("#gpView");
  const ctx = cv.getContext("2d");
  const img = ctx.createImageData(cv.width, cv.height);
  const px = new Uint32Array(img.data.buffer);
  const target = sec.querySelector("#gpTarget");
  const targetOut = sec.querySelector("#gpTargetOut");
  const status = sec.querySelector("#gpStatus");
  let probe = null, frame = null, ws = null;

  // colour ramp from the sand colour to dark red, as ABGR words for the image buffer
  const c0 = [200, 180, 140], c1 = [178, 24, 43];
  const ramp = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    const [r, g, b] = c0.map((a, k) => Math.round(a + (c1[k] - a) * t));
    ramp[i] = (255 << 24) | (b << 16) | (g << 8) | r;
  }

  const send = (m) => { if (ws && ws.readyState === 1) ws.send(JSON.stringify(m)); };
  target.oninput = () => { targetOut.textContent = `${fmt(+target.value, 1)} kPa`; send({ target_kpa: +target.value }); };
  targetOut.textContent = `${fmt(+target.value, 1)} kPa`;
  sec.querySelector("#gpReset").onclick = () => send({ reset: true });

  function connect() {
    ws = new WebSocket(url);
    ws.binaryType = "arraybuffer";
    ws.onopen = () => { status.textContent = "connected"; status.className = "flag ok"; send({ target_kpa: +target.value }); };
    ws.onclose = () => { status.textContent = "no server, retrying"; status.className = "flag bad"; setTimeout(connect, 3000); };
    ws.onmessage = (ev) => {
      if (typeof ev.data === "string") { probe = JSON.parse(ev.data); showProbe(); } else frame = decode(ev.data);
    };
  }
  connect();

  function showProbe() {
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
      ["Speed", `${fmt(p.realtime_factor, 2)}× real time`],
    ];
    sec.querySelector("#gpProbe").innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    sec.querySelector("#gpNote").innerHTML =
      `${p.label}. Section through the tunnel axis (half model), ${p.shown.toLocaleString()} of ${p.particles.toLocaleString()} particles shown. Checks: <a href="https://github.com/dtt-github/tunnel-construction-simulation/blob/main/${p.validation}" target="_blank" rel="noopener">validation page</a>.`;
  }

  function draw() {
    requestAnimationFrame(draw);
    if (!frame || !probe) return;
    const { n, lo, st, q, attr } = frame;
    const W = cv.width, H = cv.height;
    const xmin = lo[0], xmax = lo[0] + st[0] * 65535, zmax = probe.scene.surface_z_m * 1.05;
    const s = Math.min(W / (xmax - xmin), H / zmax);
    const ox = (W - s * (xmax - xmin)) / 2;
    const X = (x) => ox + (x - xmin) * s, Z = (z) => H - z * s;
    const dot = Math.max(1, Math.ceil(probe.scene.spacing_m * s));
    px.fill(0xff151210);
    for (let i = 0, j = 0; i < n; i++, j += 3) {
      const x = lo[0] + q[j] * st[0], z = lo[2] + q[j + 2] * st[2];
      const u = X(x) | 0, v = Z(z) | 0;
      if (u < 0 || v < 0 || u + dot > W || v + dot > H) continue;
      const c = ramp[attr[i]];
      for (let a = 0; a < dot; a++) px.fill(c, (v + a) * W + u, (v + a) * W + u + dot);
    }
    ctx.putImageData(img, 0, 0);
    // shield tube (top and bottom of the bore) and the support plate
    const sc = probe.scene, R = sc.diameter_m / 2, zc = sc.axis_z_m, xp = -probe.retraction_mm / 1000;
    ctx.strokeStyle = "#9aa1aa"; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(X(xmin), Z(zc + R)); ctx.lineTo(X(0), Z(zc + R));
    ctx.moveTo(X(xmin), Z(zc - R)); ctx.lineTo(X(0), Z(zc - R));
    ctx.stroke();
    ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(X(xp), Z(zc - R)); ctx.lineTo(X(xp), Z(zc + R)); ctx.stroke();
    ctx.fillStyle = "#9aa1aa"; ctx.font = "12px system-ui";
    ctx.fillText(`${fmt(probe.p_face_kPa)} kPa on the face · t ${fmt(probe.t, 1)} s`, 8, 16);
  }
  requestAnimationFrame(draw);
}

const url = new URLSearchParams(location.search).get("ground");
if (url) start(url);
