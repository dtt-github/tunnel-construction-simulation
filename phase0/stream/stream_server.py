"""Phase 0: WebSocket particle streaming benchmark (server side).

Serves one client, sends `--seconds` of particle frames at `--hz`, then prints server-side
statistics as JSON. Particle positions live on the GPU and move every frame (a cheap Warp kernel
stands in for the MPM step), so each frame pays the real cost: quantize on the GPU, copy to the
host, pack, send.

Wire format "TSP0" (little endian), one binary WebSocket message per frame:

    offset  type      field
    0       u32       magic 0x30505354 ("TSP0")
    4       u32       frame index
    8       f64       server send time, ms since the Unix epoch
    16      u32       particle count N
    20      u32       encoding: 0 = f32 xyz, 1 = u16 xyz, 2 = u16 xyz + u8 attribute
    24      f32[3]    bounding box minimum (m)
    36      f32[3]    quantization step per axis (m), extent / 65535
    48      payload   f32[3N]  |  u16[3N]  |  u16[3N] then u8[N] (attribute, e.g. speed or material)

Positions decode as  x = min + q * step.  With a fixed box of 10 m the step is 0.15 mm.
"""

import argparse
import asyncio
import json
import math
import struct
import time

import numpy as np
import warp as wp
import websockets

MAGIC = 0x30505354
HEADER = struct.Struct("<IIdII3f3f")
assert HEADER.size == 48


@wp.kernel
def advect(q: wp.array(dtype=wp.vec3), q0: wp.array(dtype=wp.vec3), t: float):
    i = wp.tid()
    p = q0[i]
    s = float(i % 997) * 0.01
    q[i] = p + wp.vec3(0.05 * wp.sin(t * 2.0 + s), 0.05 * wp.cos(t * 1.7 + s), 0.02 * wp.sin(t * 3.1 + s))


@wp.kernel
def quantize(
    q: wp.array(dtype=wp.vec3),
    q_prev: wp.array(dtype=wp.vec3),
    lo: wp.vec3,
    inv_step: wp.vec3,
    inv_dt: float,
    out: wp.array(dtype=wp.uint16),
    attr: wp.array(dtype=wp.uint8),
):
    i = wp.tid()
    p = q[i]
    for k in range(3):
        v = wp.clamp((p[k] - lo[k]) * inv_step[k] + 0.5, 0.0, 65535.0)
        out[3 * i + k] = wp.uint16(int(v))
    speed = wp.length(p - q_prev[i]) * inv_dt  # m/s, 0..2.55 mapped to 0..255
    attr[i] = wp.uint8(int(wp.clamp(speed * 100.0, 0.0, 255.0)))


def load_points(n, src):
    if src:
        pts = np.load(src)["particles"].astype(np.float32)
        reps = math.ceil(n / len(pts))
        pts = np.concatenate([pts + np.float32(0.002 * k) for k in range(reps)])[:n]
    else:
        rng = np.random.default_rng(0)
        pts = rng.uniform([-4, -3, 0], [4, 3, 6], (n, 3)).astype(np.float32)
    return pts


async def run(args):
    wp.init()
    pts = load_points(args.particles, args.source)
    n = len(pts)
    lo = pts.min(axis=0) - 0.5
    hi = pts.max(axis=0) + 0.5
    step = (hi - lo) / 65535.0
    q0 = wp.array(pts, dtype=wp.vec3)
    q = wp.clone(q0)
    q_prev = wp.clone(q0)
    qbuf = wp.zeros(3 * n, dtype=wp.uint16)
    abuf = wp.zeros(n, dtype=wp.uint8)
    qhost = wp.zeros(3 * n, dtype=wp.uint16, device="cpu", pinned=True)
    ahost = wp.zeros(n, dtype=wp.uint8, device="cpu", pinned=True)
    fhost = wp.zeros(n, dtype=wp.vec3, device="cpu", pinned=True)
    enc = {"f32": 0, "u16": 1, "u16a": 2}[args.encoding]
    period = 1.0 / args.hz
    stats = {"encode_ms": [], "send_ms": [], "bytes": []}
    done = asyncio.Event()

    async def handler(ws):
        t_start = time.perf_counter()
        frame = 0
        next_t = t_start
        while time.perf_counter() - t_start < args.seconds:
            t_sim = frame * period
            t0 = time.perf_counter()
            wp.copy(q_prev, q)
            wp.launch(advect, n, inputs=[q, q0, t_sim])
            if enc == 0:
                wp.copy(fhost, q)
                wp.synchronize()
                payload = fhost.numpy().tobytes()
            else:
                wp.launch(quantize, n, inputs=[q, q_prev, wp.vec3(*lo), wp.vec3(*(1.0 / step)), 1.0 / period, qbuf, abuf])
                wp.copy(qhost, qbuf)
                if enc == 2:
                    wp.copy(ahost, abuf)
                wp.synchronize()
                payload = qhost.numpy().tobytes() + (ahost.numpy().tobytes() if enc == 2 else b"")
            msg = HEADER.pack(MAGIC, frame, time.time() * 1000.0, n, enc, *lo, *step) + payload
            t1 = time.perf_counter()
            await ws.send(msg)
            t2 = time.perf_counter()
            stats["encode_ms"].append((t1 - t0) * 1e3)
            stats["send_ms"].append((t2 - t1) * 1e3)
            stats["bytes"].append(len(msg))
            frame += 1
            next_t += period
            await asyncio.sleep(max(0.0, next_t - time.perf_counter()))
        await ws.close()
        done.set()

    # compile the kernels before the client connects
    wp.launch(advect, n, inputs=[q, q0, 0.0])
    wp.launch(quantize, n, inputs=[q, q_prev, wp.vec3(*lo), wp.vec3(*(1.0 / step)), 1.0 / period, qbuf, abuf])
    wp.synchronize()

    compression = "deflate" if args.deflate else None
    async with websockets.serve(handler, "127.0.0.1", args.port, max_size=None, compression=compression, write_limit=2**24):
        print(json.dumps({"ready": args.port}), flush=True)
        await done.wait()

    e = np.array(stats["encode_ms"])
    s = np.array(stats["send_ms"])
    print(
        json.dumps(
            {
                "server": {
                    "particles": n,
                    "encoding": args.encoding,
                    "deflate": args.deflate,
                    "target_hz": args.hz,
                    "frames_sent": len(e),
                    "bytes_per_frame": int(np.mean(stats["bytes"])),
                    "encode_ms_mean": round(float(e.mean()), 3),
                    "encode_ms_p95": round(float(np.percentile(e, 95)), 3),
                    "send_ms_mean": round(float(s.mean()), 3),
                    "send_ms_p95": round(float(np.percentile(s, 95)), 3),
                }
            }
        ),
        flush=True,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--particles", type=int, default=200_000)
    p.add_argument("--hz", type=float, default=30.0)
    p.add_argument("--seconds", type=float, default=10.0)
    p.add_argument("--encoding", choices=["f32", "u16", "u16a"], default="u16")
    p.add_argument("--deflate", action="store_true", help="permessage-deflate (CPU-heavy)")
    p.add_argument("--source", type=str, default=None, help="npz with a 'particles' array to stream")
    p.add_argument("--port", type=int, default=8765)
    asyncio.run(run(p.parse_args()))


if __name__ == "__main__":
    main()
