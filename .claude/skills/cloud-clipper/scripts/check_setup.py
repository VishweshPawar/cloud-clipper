#!/usr/bin/env python3
"""Check that prerequisites for the cloud-clipper run are ready.

- FreeLLMAPI gateway reachable at 127.0.0.1:31415
- Groq Whisper endpoint via the gateway
- yt-dlp available in the system python path
- ffmpeg executable in PATH

The script prints PASS/FAIL for each check.
"""
import json
import os
import shutil
import subprocess
import sys
import urllib.request

BASE_URL = "http://127.0.0.1:31415/v1"


def pinger(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            r.read(1)
        return True
    except Exception:
        return False


def check_gateway():
    url = f"{BASE_URL}/models"
    ok = pinger(url)
    print("FreeLLMAPI gateway", "OK" if ok else "NOT OK")
    return ok


def check_groq():
    url = f"{BASE_URL}/audio/transcribe"
    try:
        req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            r.read(1)
        return True
    except Exception:
        return False


def check_yt_dlp():
    try:
        import yt_dlp  # noqa: F401
        return True
    except Exception:
        return False


def check_ffmpeg():
    return shutil.which("ffmpeg") is not None


def main():
    all_ok = True
    if not check_gateway():
        all_ok = False
    if not check_groq():
        all_ok = False
    if not check_yt_dlp():
        all_ok = False
    if not check_ffmpeg():
        all_ok = False

    if all_ok:
        print("✓ All prerequisites satisfied.")
        sys.exit(0)
    else:
        print("✗ Some prerequisites failed. Fix them before running cloud-clipper.")
        sys.exit(1)


if __name__ == "__main__":
    main()