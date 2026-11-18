#!/usr/bin/env python3
"""Render viral shorts in 9:16 (1080x1920) with captions using ffmpeg.

Inputs (per clip):
  - source.mp4 (full video)
  - transcript.json (word-level timestamps)
  - clip spec: start, end, title, layout

Outputs:
  - short_XX.mp4 (1080x1920, -14 LUFS, captions burned in)

Layouts:
  - crop: center crop 9:16 (best for gameplay centered action)
  - blur: vertical blur pillarbox (keeps full width, sides blurred)

Caption format: ASS with per-word highlight (karaoke style)
  - Yellow highlight on active word
  - Hook title at top (max ~6 words + 1 emoji)
  - Safe zones: top 10%, bottom 15%, right 12%
"""
import argparse
import json
import os
import subprocess
import sys

TARGET_W, TARGET_H = 1080, 1920  # 9:16
SAFE_TOP = int(TARGET_H * 0.10)
SAFE_BOTTOM = int(TARGET_H * 0.85)
SAFE_RIGHT = int(TARGET_W * 0.88)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ffmpeg error: {r.stderr}", file=sys.stderr)
        r.check_returncode()
    return r


def build_ass(captions, title, layout="crop", hook_lines=1):
    """Generate ASS caption file content."""
    header = f"""[Script Info]
Title: Cloud Clipper Captions
ScriptType: v4.00+
PlayResX: {TARGET_W}
PlayResY: {TARGET_H}
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans,78,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,20,20,{SAFE_BOTTOM},1
Style: Hook,Noto Sans,92,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,8,20,20,{SAFE_TOP},1
Style: Highlight,Noto Sans,78,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,20,20,{SAFE_BOTTOM},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    hook_end = min(3.0, captions[-1]["end"] if captions else 3.0)
    h_start = fmt_time(0)
    h_end = fmt_time(hook_end)
    events.append(f"Dialogue: 1,{h_start},{h_end},Hook,,0,0,0,,{{\an8}}{title}")

    for w in captions:
        s = fmt_time(w["start"])
        e = fmt_time(w["end"])
        word = w["word"].replace("{", "\{").replace("}", "\}").replace("\\", "\\\\")
        events.append(f"Dialogue: 0,{s},{e},Default,,0,0,0,,{{\k{int((w['end']-w['start'])*100)}}}{word}")
        events.append(f"Dialogue: 1,{s},{e},Highlight,,0,0,0,,{{\k{int((w['end']-w['start'])*100)}}}{word}")

    return header + "\n".join(events)


def fmt_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int((t * 100) % 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def render_clip(source, out_path, start, end, title, layout="crop"):
    dur = end - start
    tr = json.load(open(os.path.join(os.path.dirname(source), "transcript.json")))
    words = [w for w in tr.get("words", []) if w.get("s", 0) >= start and w.get("s", 0) < end]
    for w in words:
        w["start"] = w["s"] - start
        w["end"] = w["e"] - start
        w["word"] = w["w"]

    ass_path = out_path + ".ass"
    ass = build_ass(words, title, layout)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass)

    vf = []
    if layout == "crop":
        vf.append(f"crop=ih*9/16:ih:(iw-ih*9/16)/2:0")
    else:
        vf.append(f"split[main][blur];[blur]crop=ih*9/16:ih:(iw-ih*9/16)/2:0,gblur=sigma=30[blurred];[main][blurred]overlay=(W-w)/2:(H-h)/2")
    vf.append(f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=decrease")
    vf.append(f"pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2:color=black")
    vf.append(f"subtitles='{ass_path}'")
    vf = ",".join(vf)

    af = ["loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=-99:measured_TP=-99:measured_LRA=0:measured_thresh=-99:offset=0:linear=true:print_format=summary"]

    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-ss", str(start),
        "-t", str(dur),
        "-i", source,
        "-vf", vf,
        "-af", ",".join(af),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        out_path,
    ]
    run(cmd)
    os.remove(ass_path)
    print(f"✓ {os.path.basename(out_path)} ({dur:.1f}s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("out_dir")
    ap.add_argument("--clips", required=True, help="JSON file with clip specs")
    ap.add_argument("--layout", choices=["crop", "blur"], default="crop")
    a = ap.parse_args()

    clips = json.load(open(a.clips))
    os.makedirs(a.out_dir, exist_ok=True)

    for i, c in enumerate(clips, 1):
        out = os.path.join(a.out_dir, f"short_{i:02d}.mp4")
        render_clip(a.source, out, c["start"], c["end"], c.get("title", ""), a.layout)

    print(f"\n✓ {len(clips)} shorts → {a.out_dir}")


if __name__ == "__main__":
    main()
