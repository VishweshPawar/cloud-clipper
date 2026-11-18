#!/usr/bin/env python3
"""Download a stream/VOD (+ live chat replay if available) in the cloud.

Usage:
  download.py "<URL>" --out work/<id> [--section 01:00:00-02:30:00]
                [--max-height 1080] [--no-chat]

Outputs:
  work/<id>/source.mp4         — the video file (max 1080p)
  work/<id>/info.json          — metadata (title, channel, duration, etc.)
  work/<id>/chat.json          — live chat replay (YouTube only, optional)
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

def to_sec(t):
    parts = [float(p) for p in t.split(":")]
    s = 0.0
    for p in parts:
        s = s * 60 + p
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", required=True)
    ap.add_argument("--section", help="start-end, e.g. 01:00:00-02:30:00")
    ap.add_argument("--max-height", type=int, default=1080)
    ap.add_argument("--no-chat", action="store_true", help="Skip chat download entirely (use for Twitch/Kick)")
    a = ap.parse_args()

    try:
        import yt_dlp
    except ImportError:
        sys.exit("yt-dlp missing: pip install yt-dlp")

    os.makedirs(a.out, exist_ok=True)
    base = {"quiet": False, "noprogress": False, "noplaylist": True}

    # 1) Get metadata without downloading
    with yt_dlp.YoutubeDL({**base, "skip_download": True, "quiet": True}) as y:
        info = y.extract_info(a.url, download=False)

    if info.get("is_live"):
        print("⚠ Stream is LIVE — downloading from buffer start.")
        print("   Run again after it ends for best results, or use --section to clip a portion.")

    keep = {k: info.get(k) for k in ("id", "title", "uploader", "channel", "duration",
                                     "webpage_url", "extractor", "upload_date")}
    json.dump(keep, open(os.path.join(a.out, "info.json"), "w"), indent=2, ensure_ascii=False)
    print(f"Title: {keep['title']}  |  Duration: {keep.get('duration')}s")

    # 2) Download video
    h = a.max_height
    opts = {
        **base,
        "format": f"bv*[height<={h}][ext=mp4]+ba[ext=m4a]/bv*[height<={h}]+ba/b[height<={h}]/b",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(a.out, "source.%(ext)s"),
        "live_from_start": True,
    }
    if a.section:
        s, e = a.section.split("-")
        from yt_dlp.utils import download_range_func
        opts["download_ranges"] = download_range_func(None, [(to_sec(s), to_sec(e))])
        opts["force_keyframes_at_cuts"] = True
        json.dump({"offset": to_sec(s)}, open(os.path.join(a.out, "section.json"), "w"))

    with yt_dlp.YoutubeDL(opts) as y:
        y.download([a.url])

    src = [p for p in glob.glob(os.path.join(a.out, "source.*")) if not p.endswith(".part")]
    if not src:
        sys.exit("Download failed — no source file.")
    if not src[0].endswith(".mp4"):
        mp4 = os.path.join(a.out, "source.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src[0], "-c", "copy", mp4], check=True)
        os.remove(src[0])

    # 3) Live chat replay (YouTube only)
    if not a.no_chat:
        try:
            with yt_dlp.YoutubeDL({**base, "skip_download": True, "quiet": True,
                                   "writesubtitles": True, "subtitleslangs": ["live_chat"],
                                   "outtmpl": os.path.join(a.out, "chat")}) as y:
                y.download([a.url])
            found = glob.glob(os.path.join(a.out, "chat*.live_chat.json"))
            if found:
                shutil.move(found[0], os.path.join(a.out, "chat.json"))
                print("✓ Live chat replay saved (chat.json)")
            else:
                print("(no chat replay found — normal for live streams)")
        except Exception as e:
            print(f"(no chat replay: {e} — chat is optional)")

    print(f"✓ Saved {os.path.join(a.out, 'source.mp4')}")

if __name__ == "__main__":
    main()