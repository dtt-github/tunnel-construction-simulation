"""WP6, face only: live ground physics over a WebSocket (local use only, not on the public site).

Runs the WP2 dry-sand face (Idinger et al. 2011 prototype: D 5 m, C/D 1, half model) on the GPU with the pressure
servo, and lets one or more browsers set the support pressure. The face holds above the limit pressure and gives way
below it. Every few frames it sends:

- a binary TSP0 frame (the Phase 0 wire format, phase0/stream/stream_server.py): the particles in a slice along the
  symmetry plane (the section through the tunnel axis), u16 positions plus a u8 attribute, the displacement since the
  last reset scaled to 0.02 D = 255;
- a JSON text message with the probes: face pressure, target, plate retraction, real-time factor, and the calibration
  label with the references it is checked against (docs/validation/mpm-face-sand.md).

Clients send JSON: {"target_kpa": 12} sets the support pressure; {"reset": true} rebuilds the scene.

    python -m tunnelsim_server.live [--cover 1.0] [--vpd 10] [--port 8765]

The coupling to the EPB demo's own ground and chamber waits on WP3 and WP4 (docs/plans/phase2-mpm-face-chamber.md):
this benchmark face has its own ground and scale, so the browser shows it with its own controls.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import struct
import time
from pathlib import Path

import numpy as np

from .runner import FACE_SOILS
from .scenes.face_sand import Face, FaceSandConfig

MAGIC = 0x30505354
HEADER = struct.Struct("<IIdII3f3f")
RESULTS = Path(__file__).resolve().parent.parent / "results"
LABEL = "Uncalibrated: bracketed. Idinger's measured support pressures lie between the two Drucker-Prager cone matches"


def encode(frame: int, pts: np.ndarray, attr: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> bytes:
    """TSP0 frame, encoding 2 (u16 xyz + u8 attribute)."""
    step = np.maximum(hi - lo, 1e-6) / 65535.0
    q = np.clip(np.rint((pts - lo) / step), 0, 65535).astype("<u2")
    head = HEADER.pack(MAGIC, frame, time.time() * 1000.0, len(pts), 2, *lo.astype(float), *step.astype(float))
    return head + q.tobytes() + attr.astype(np.uint8).tobytes()


def references(cover: float) -> dict:
    """What the face is checked against at this cover, from the WP2 records (re-baselined in WP0b)."""
    out = {"idinger_measured_kPa": {0.5: [3.0, 6.0], 1.0: [4.5, 6.0], 1.5: [6.5, 9.5]}.get(cover)}
    for key, name in (("plane_strain_kPa", f"fs_idinger_c{cover}_d10_r07.json"), ("triaxial_kPa", f"fsb_idinger_c{cover}_d10_tc_r07.json")):
        f = RESULTS / name
        out[key] = json.loads(f.read_text())["result"]["p_5pct_kPa"] if f.exists() else None
    return out


class Session:
    def __init__(self, cover: float, vpd: float, target_kpa: float, slice_over_d: float = 0.3):
        self.cfg = FaceSandConfig(cover=cover, voxel_per_d=vpd, control="pressure")
        self.slice_over_d = slice_over_d
        self.target_kpa = target_kpa
        self.reset_requested = False
        self.build()

    def build(self):
        self.face = Face(self.cfg, FACE_SOILS["idinger"])
        f = self.face
        self.log: list = []
        self.frame = 0
        self.ref = None
        self.slice = f.pts[:, 1] < self.slice_over_d * f.D  # particles near the symmetry plane: the section through the axis
        lo, hi = f.box
        self.lo, self.hi = lo.astype(np.float32), hi.astype(np.float32)
        D, phi = f.D, f.soil.phi_deg
        self.vermeer_kpa = f.gamma * D * (1.0 / (9.0 * math.tan(math.radians(phi))) - 0.05) / 1e3

    def step(self) -> float:
        f, cfg = self.face, self.cfg
        settling = self.frame < cfg.settle
        if self.frame == cfg.settle:
            self.ref = f.s.particle_q.numpy().copy()
        v = 0.0 if settling else f.servo_speed(self.log, self.target_kpa)
        if self.log and self.log[-1][0] > 0.3 * f.D:  # the plate stays inside the shield tube
            v = 0.0
        delta, p, elapsed = f.step(v)
        self.log.append((float(delta), float(p)))
        self.frame += 1
        return elapsed

    def particles(self) -> bytes:
        f = self.face
        q = f.s.particle_q.numpy()
        pts = q[self.slice]
        if self.ref is None:
            attr = np.zeros(len(pts))
        else:
            attr = np.clip(np.linalg.norm(q[self.slice] - self.ref[self.slice], axis=1) / (0.02 * f.D) * 255, 0, 255)
        return encode(self.frame, pts, attr, self.lo, self.hi)

    def probe(self, rtf: float) -> str:
        return json.dumps(self.probe_dict(rtf))

    def probe_dict(self, rtf: float) -> dict:
        f = self.face
        p = float(np.mean([e[1] for e in self.log[-6:]])) / 1e3 if self.log else 0.0
        return {
            "type": "probe", "t": round(self.frame * f.dt, 3), "settling": self.frame < self.cfg.settle,
            "p_face_kPa": round(p, 2), "target_kPa": self.target_kpa,
            "retraction_mm": round(self.log[-1][0] * 1000, 1) if self.log else 0.0,
            "retraction_over_D": round(self.log[-1][0] / f.D, 4) if self.log else 0.0,
            "realtime_factor": round(rtf, 2), "particles": int(len(f.pts)), "shown": int(self.slice.sum()),
            "scene": {"name": "Dry-sand face, Idinger et al. (2011) prototype", "diameter_m": f.D, "cover_over_D": self.cfg.cover,
                      "voxel_per_D": self.cfg.voxel_per_d, "phi_deg": f.soil.phi_deg, "gamma_kN_m3": round(f.gamma / 1e3, 2),
                      "axis_z_m": round(float(f.zc), 3), "surface_z_m": round(float(f.zs), 3), "wall_m": round(float(f.t), 3),
                      "spacing_m": round(float(f.h), 4),
                      "box_m": [[round(float(v), 3) for v in f.box[0]], [round(float(v), 3) for v in f.box[1]]]},
            "label": LABEL, "validation": "docs/validation/mpm-face-sand.md",
            "references": {**references(self.cfg.cover), "vermeer_kPa": round(self.vermeer_kpa, 2)},
        }


async def serve(args):
    import websockets

    sess = Session(args.cover, args.vpd, args.target)
    clients: set = set()

    async def handler(ws):
        clients.add(ws)
        try:
            async for msg in ws:
                try:
                    m = json.loads(msg)
                except (TypeError, ValueError):
                    continue
                if "target_kpa" in m:
                    sess.target_kpa = float(np.clip(float(m["target_kpa"]), 0.0, 60.0))
                if m.get("reset"):
                    sess.reset_requested = True
        finally:
            clients.discard(ws)

    async def broadcast(data):
        for ws in list(clients):
            try:
                await ws.send(data)
            except Exception:  # a client that went away
                clients.discard(ws)

    async with websockets.serve(handler, args.host, args.port, max_size=None, write_limit=2**24):
        print(json.dumps({"ready": True, "url": f"ws://{args.host}:{args.port}", "particles": int(len(sess.face.pts))}), flush=True)
        dt = sess.face.dt
        wall = time.perf_counter()
        sim_times: list[float] = []
        while True:
            if sess.reset_requested:
                sess.reset_requested = False
                await asyncio.to_thread(sess.build)
                wall = time.perf_counter()
            elapsed = await asyncio.to_thread(sess.step)
            sim_times.append(elapsed)
            # no faster than real time; slower if the GPU cannot keep up (the real-time factor says so)
            wall += dt
            lag = wall - time.perf_counter()
            if lag > 0:
                await asyncio.sleep(lag)
            else:
                wall = time.perf_counter()
            if sess.frame % args.every == 0 and clients:
                rtf = min(1.0, dt / max(float(np.mean(sim_times[-30:])), 1e-6))
                await broadcast(await asyncio.to_thread(sess.particles))
                await broadcast(sess.probe(rtf))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--cover", type=float, default=1.0, choices=[0.5, 1.0, 1.5])
    p.add_argument("--vpd", type=float, default=10.0, help="D / voxel")
    p.add_argument("--target", type=float, default=20.0, help="initial support pressure, kPa (above the limit)")
    p.add_argument("--every", type=int, default=3, help="send every n-th frame (60 fps / 3 = 20 Hz)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    asyncio.run(serve(p.parse_args()))


if __name__ == "__main__":
    main()
