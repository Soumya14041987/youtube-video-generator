#!/usr/bin/env python3
"""Cut the person out of a photo and save a transparent PNG.

Usage: cutout.py <photo.jpg> <out.png>

macOS 14 or newer: uses Apple's on-device Vision framework through cutout.swift. Nothing is downloaded or uploaded.
Windows and Linux: uses the optional 'rembg' package (pip install rembg). Or cut the photo out in any editor,
save it as a transparent PNG, and use that file as "photo:<path>" in thumbnail-spec.json.
"""
import os, platform, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def mac_cutout(src, dst):
    cache = os.path.join(os.path.expanduser("~"), ".cache", "ytvg")
    exe = os.path.join(cache, "cutout")
    if not os.path.exists(exe):
        if not shutil.which("swiftc"):
            return False, "swiftc not found. Install Xcode Command Line Tools: xcode-select --install"
        os.makedirs(cache, exist_ok=True)
        r = subprocess.run(["swiftc", "-O", os.path.join(HERE, "cutout.swift"), "-o", exe], capture_output=True, text=True)
        if r.returncode:
            return False, r.stderr[-300:]
    r = subprocess.run([exe, src, dst], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def rembg_cutout(src, dst):
    try:
        from rembg import remove
        from PIL import Image
    except ImportError:
        return False, "Install the cutout helper with: pip install rembg   (or cut the photo out in any editor and save a transparent PNG)"
    remove(Image.open(src)).save(dst)
    return True, "cutout written"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    ok, msg = (mac_cutout(src, dst) if platform.system() == "Darwin" else rembg_cutout(src, dst))
    if not ok and platform.system() == "Darwin":
        ok2, msg2 = rembg_cutout(src, dst)
        ok, msg = ok2, (msg2 if ok2 else msg + " | " + msg2)
    print(msg)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
