"""Record particle runs into a compact replay file ("TSR0") for browser playback without a GPU. Taken unchanged
from phase0/replay.py (Phase 0 replays); the browser decoder is in web/epb/ground.js and phase0/replays/index.html.

Layout, gzip-compressed as a whole:

    u32       magic 0x30525354 ("TSR0")
    u32       length of the JSON metadata in bytes (padded with spaces to a multiple of 4)
    bytes     JSON: particle count, frames, fps, bbox minimum, quantization step, per-frame scalars, scene
    u16[3N]   frame 0, positions quantized as  q = round((x - lo) / step)
    i16[3N]   each later frame: q - q_previous   (mostly zero for soil at rest, so it compresses well)

Decode: x = lo + q * step. A 1 mm step keeps 10 m scenes inside u16.
"""

import gzip
import json
import struct

import numpy as np

MAGIC = 0x30525354


class Recorder:
    def __init__(self, lo, hi, step=0.001):
        self.lo = np.asarray(lo, dtype=np.float64)
        self.step = float(step)
        if np.any((np.asarray(hi) - self.lo) / step > 65535):
            raise ValueError("scene too large for a u16 grid at this step")
        self.prev = None
        self.chunks = []
        self.scalars = {}
        self.frames = 0

    def add(self, points, **scalars):
        q = np.clip(np.rint((np.asarray(points, dtype=np.float64) - self.lo) / self.step), 0, 65535).astype(np.int32)
        if self.prev is None:
            self.chunks.append(q.astype(np.uint16).tobytes())
        else:
            self.chunks.append((q - self.prev).astype(np.int16).tobytes())
        self.prev = q
        for k, v in scalars.items():
            self.scalars.setdefault(k, []).append(round(float(v), 4))
        self.frames += 1

    def save(self, path, fps, scene):
        meta = {
            "particles": int(len(self.prev)),
            "frames": self.frames,
            "fps": fps,
            "lo": [round(float(v), 6) for v in self.lo],
            "step": self.step,
            "scalars": self.scalars,
            "scene": scene,
        }
        js = json.dumps(meta, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        with gzip.open(path, "wb", compresslevel=9) as fh:
            fh.write(struct.pack("<II", MAGIC, len(js)))
            fh.write(js)
            for c in self.chunks:
                fh.write(c)
