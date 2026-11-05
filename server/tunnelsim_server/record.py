"""WP7: record the live dry-sand face (tunnelsim_server.live) under a scripted support-pressure timeline into a TSR0
replay (tunnelsim_server.replay) that the EPB demo's "Ground physics" panel plays without a GPU.

Default timeline (seconds after settling), at C/D 1: 20 kPa (above the limit, the face holds), 3 kPa from 4 s (below
the limit, the face gives way and the chimney rises to the surface), 20 kPa again from 12 s (the face stops), end at
16 s. The replay stores the particles in a slice along the symmetry plane and, per frame, the time, face pressure,
target and plate retraction; its metadata carries the calibration label, the references, the settings and the run
record (git commit, versions).

    python -m tunnelsim_server.record [--out ../web/epb/recordings/face-sand-cd1.tsr.gz]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .live import Session
from .replay import Recorder
from .runrecord import git_commit, versions

TIMELINE = [(0.0, 20.0), (4.0, 3.0), (12.0, 20.0)]  # (s after settling, target kPa)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--cover", type=float, default=1.0, choices=[0.5, 1.0, 1.5])
    p.add_argument("--vpd", type=float, default=10.0)
    p.add_argument("--end", type=float, default=16.0, help="s after settling")
    p.add_argument("--every", type=int, default=4, help="record every n-th frame (60 fps / 4 = 15 Hz)")
    p.add_argument("--slice", type=float, default=0.15, help="slice half-width / D along the symmetry plane")
    p.add_argument("--out", type=str, default=str(Path(__file__).resolve().parents[2] / "web/epb/recordings/face-sand-cd1.tsr.gz"))
    args = p.parse_args()

    sess = Session(args.cover, args.vpd, TIMELINE[0][1], slice_over_d=args.slice)
    f = sess.face
    lo, hi = f.box
    rec = Recorder(lo, hi, step=0.001)
    settle = sess.cfg.settle
    n_frames = settle + int(round(args.end * sess.cfg.fps))
    control_start = None
    for k in range(n_frames):
        t_ctrl = (k - settle) / sess.cfg.fps
        for t0, target in TIMELINE:
            if t_ctrl >= t0:
                sess.target_kpa = target
        sess.step()
        if k % args.every == 0:
            if control_start is None and k >= settle:
                control_start = rec.frames
            pr = sess.probe_dict(1.0)
            rec.add(f.s.particle_q.numpy()[sess.slice], t=pr["t"], p_face_kPa=pr["p_face_kPa"], target_kPa=pr["target_kPa"],
                    retraction_mm=pr["retraction_mm"])
    pr = sess.probe_dict(1.0)
    scene = {**pr["scene"], "label": pr["label"], "validation": pr["validation"], "references": pr["references"],
             "particles_total": pr["particles"], "slice_over_D": args.slice, "timeline_kPa": TIMELINE, "settle_s": settle / sess.cfg.fps,
             "control_start_frame": control_start, "run": {"git": git_commit(), "versions": versions(), "recorded_every": args.every}}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    rec.save(args.out, sess.cfg.fps / args.every, scene)
    size = Path(args.out).stat().st_size
    print(json.dumps({"out": args.out, "frames": rec.frames, "particles": int(sess.slice.sum()), "bytes": size,
                      "final_retraction_mm": pr["retraction_mm"]}))


if __name__ == "__main__":
    main()
