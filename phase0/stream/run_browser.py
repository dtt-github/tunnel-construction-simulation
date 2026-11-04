"""Open stream/index.html in Chrome while stream_server.py streams to it; print the page's numbers.

Needs Playwright and the locally unpacked Chrome from the sister project (construction-site-simulation/phase0/tools).
Run with that project's venv:  ../../../construction-site-simulation/phase0/.venv-newton/bin/python run_browser.py
"""

import http.server
import json
import os
import subprocess
import sys
import threading
from functools import partial

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "..", ".venv-newton", "bin", "python")
CHROME = os.path.expanduser("~/Documents/construction-site-simulation/phase0/tools/chrome-deb/root/opt/google/chrome/chrome")
WS_PORT = 8790


def run(pw, url, n, hz, enc, seconds=8):
    srv = subprocess.Popen(
        [PY, os.path.join(HERE, "stream_server.py"), "--particles", str(n), "--hz", str(hz), "--encoding", enc, "--seconds", str(seconds), "--port", str(WS_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    for line in srv.stdout:
        if line.startswith('{"ready"'):
            break
    browser = pw.chromium.launch(executable_path=CHROME, headless=False, args=["--enable-features=Vulkan", "--use-angle=vulkan"])
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto(url)
    page.wait_for_function("document.title === 'DONE'", timeout=120_000)
    res = page.evaluate("window.__result")
    if n == 300_000 and enc == "u16":
        page.screenshot(path=os.path.join(HERE, "..", "logs", "stream_browser.png"))
    browser.close()
    out = srv.stdout.read()
    srv.wait(timeout=60)
    for line in out.splitlines():
        if line.startswith('{"server"'):
            res.update(json.loads(line))
    return res


def main():
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=HERE)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/index.html?ws=ws://127.0.0.1:{WS_PORT}"
    results = []
    with sync_playwright() as pw:
        for n, hz, enc in [(100_000, 30, "u16"), (300_000, 30, "u16"), (300_000, 30, "f32"), (1_000_000, 30, "u16")]:
            r = run(pw, url, n, hz, enc)
            r["case"] = {"particles": n, "hz": hz, "encoding": enc}
            results.append(r)
            print(json.dumps(r), flush=True)
    httpd.shutdown()
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "logs", "stream_browser.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)


if __name__ == "__main__":
    main()
