"""Run the streaming benchmark over particle counts, rates and encodings; write logs/stream.json."""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "..", ".venv-newton", "bin", "python")
SECONDS = 8

CASES = [
    (n, hz, enc, deflate)
    for n in (100_000, 200_000, 300_000)
    for hz in (20, 30)
    for enc, deflate in (("f32", False), ("u16", False), ("u16a", False))
] + [(300_000, 30, "u16", True), (1_000_000, 30, "u16", False)]


def run_case(n, hz, enc, deflate, port=8765):
    cmd = [PY, os.path.join(HERE, "stream_server.py"), "--particles", str(n), "--hz", str(hz), "--encoding", enc, "--seconds", str(SECONDS), "--port", str(port)]
    if deflate:
        cmd.append("--deflate")
    srv = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    for line in srv.stdout:
        if line.startswith('{"ready"'):
            break
    cli = subprocess.run(["node", os.path.join(HERE, "stream_client.mjs"), f"ws://127.0.0.1:{port}"], capture_output=True, text=True, timeout=120)
    out = srv.stdout.read()
    srv.wait(timeout=60)
    res = {}
    for line in (out + cli.stdout).splitlines():
        if line.startswith("{"):
            res.update(json.loads(line))
    if cli.returncode != 0:
        res["client_error"] = cli.stderr[-500:]
    return res


def main():
    results = []
    for case in CASES:
        r = run_case(*case)
        results.append(r)
        s, c = r.get("server", {}), r.get("client", {})
        print(f"{case}: {c.get('fps')} fps, {c.get('MB_per_s')} MB/s, latency {c.get('latency_ms_mean')} ms, encode {s.get('encode_ms_mean')} ms, decode {c.get('decode_ms_mean')} ms", flush=True)
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "logs", "stream.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)


if __name__ == "__main__":
    main()
