#!/usr/bin/env python3
"""
export_png.py - render an archify-delivered diagram HTML to a clean LinkedIn
PNG (viewer toolbar, dock and guides hidden) using headless Chrome.

Needs Google Chrome or Chromium. Set ARCHIFY_CHROME to override the path.
No Python dependencies.

Usage
  python3 export_png.py diagram.html diagram.png
  python3 export_png.py diagram.html diagram.png --size 1200x675
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]

HIDE_VIEWER_CHROME = (
    "<style>.toolbar,.no-print,.guided-views,[class*='dock'],[id*='dock'],"
    ".diagram-guide,.share-chapter-cue{display:none!important}"
    "html,body{overflow:hidden!important}"
    ".container{padding-top:6px!important;padding-bottom:0!important;max-width:none!important}"
    ".header,.header-row,h1{max-width:none!important;width:auto!important;"
    "white-space:nowrap!important;font-size:26px!important}</style></head>"
)


def find_chrome():
    override = os.environ.get("ARCHIFY_CHROME")
    if override:
        return override if os.path.exists(override) else None
    for c in CHROME_CANDIDATES:
        path = c if os.path.isabs(c) else shutil.which(c)
        if path and os.path.exists(path):
            return path
    return None


def main():
    ap = argparse.ArgumentParser(description="Export an archify diagram HTML to a clean PNG.")
    ap.add_argument("html")
    ap.add_argument("png")
    ap.add_argument("--size", default="1200x675", help="WIDTHxHEIGHT (default 1200x675)")
    args = ap.parse_args()

    chrome = find_chrome()
    if not chrome:
        sys.exit("error: Chrome/Chromium not found. Install it or set ARCHIFY_CHROME.")
    html = open(args.html, encoding="utf-8").read()
    if "</head>" not in html:
        sys.exit("error: input does not look like an archify HTML file.")

    with tempfile.TemporaryDirectory() as tmp:
        wrapped = os.path.join(tmp, "wrapped.html")
        with open(wrapped, "w", encoding="utf-8") as fh:
            fh.write(html.replace("</head>", HIDE_VIEWER_CHROME, 1))
        out = os.path.abspath(args.png)
        cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
               "--force-dark-mode", f"--window-size={args.size.replace('x', ',')}",
               f"--screenshot={out}", f"file://{wrapped}"]
        subprocess.run(cmd, capture_output=True, timeout=60)
    if not os.path.exists(args.png) or os.path.getsize(args.png) == 0:
        sys.exit("error: Chrome produced no screenshot.")
    print(f"wrote {args.png}")


if __name__ == "__main__":
    main()
