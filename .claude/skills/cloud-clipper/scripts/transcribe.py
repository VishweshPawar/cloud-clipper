#!/usr/bin/env python3
"""Cloud-only transcription using Groq Whisper API directly.

- Splits audio into chunks < 24MB (Groq limit)
- Transcribes via HTTP POST to Groq API
- Synthesizes word timestamps
- Writes transcript.json + transcript.txt

Usage: python3 transcribe.py source.mp4 --groq-key "<key>" [--model whisper-large-v3-turbo] [--language auto]
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request


def groq_post(file_path, groq_key, model="whisper-large-v3-turbo", language="auto"):
    url = "https://api.groq.com/openai/v1/audio/transcriptions"

    # Read file
    with open(file_path, "rb") as f:
        file_data = f.read()

    # Build multipart form data following OpenAI API spec
    boundary = "----GroqBoundary7MA4YWxkTrZu0gW"

    parts = []

    # Model
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\n{model}\r\n'.encode())

    # Response format
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="response_format"\r\n\r\nverbose_json\r\n'.encode())

    # Language (if not auto)
    if language != "auto":
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="language"\r\n\r\n{language}\r\n'.encode())

    # File part
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode())

    # File data + closing boundary
    parts.append(file_data)
    parts.append(f'\r\n--{boundary}--\r\n'.encode())

    data = b''.join(parts)

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Groq API error: {e}", file=sys.stderr)
        return {"segments": [], "text": ""}


def split_audio_chunks(video_path):
    dur = float(subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", video_path],
        capture_output=True, text=True,
    ).stdout.strip())

    chunk_duration = 25.0  # seconds (< 24MB)
    chunks = []
    pos = 0.0
    while pos < dur:
        end = min(pos + chunk_duration, dur)
        chunk_name = f"_chunk_{len(chunks):04d}.mp3"
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-i", video_path,
                "-ss", str(pos),
                "-to", str(end),
                "-vn", "-ac", "1", "-ar", "8000", "-acodec", "libmp3lame",
                "-qscale:a", "2",
                chunk_name,
            ],
            capture_output=True, text=True,
        )
        chunks.append((chunk_name, pos, end))
        pos += chunk_duration
    return chunks


def synthesize_words(segments, chunk_offset=0):
    words = []
    for seg in segments:
        txt = seg.get("text", "").strip()
        if not txt:
            continue
        s = seg.get("start", 0) + chunk_offset
        e = seg.get("end", 0) + chunk_offset
        ws = txt.split()
        if not ws:
            continue
        dur = (e - s) / len(ws)
        for i, w_text in enumerate(ws):
            words.append({
                "w": w_text,
                "s": s + i * dur,
                "e": s + (i + 1) * dur,
            })
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--groq-key", required=True)
    ap.add_argument("--model", default="whisper-large-v3-turbo")
    ap.add_argument("--language", default="auto")
    a = ap.parse_args()

    vid = a.video
    chunks = split_audio_chunks(vid)
    all_words = []
    transcript_parts = []

    for i, (cpath, s, e) in enumerate(chunks):
        print(f"Transcribing chunk {i+1}/{len(chunks)} ({s:.1f}s–{e:.1f}s)…")
        resp = groq_post(cpath, a.groq_key, a.model, a.language)
        segs = resp.get("segments", [])
        words = synthesize_words(segs, chunk_offset=s)
        all_words.extend(words)
        transcript_parts.append(resp.get("text", ""))

        try:
            os.remove(cpath)
        except Exception:
            pass

    transcript_json = {
        "words": all_words,
        "text": " ".join(transcript_parts),
    }
    out_dir = os.path.dirname(vid) or "."
    with open(os.path.join(out_dir, "transcript.json"), "w", encoding="utf-8") as f:
        json.dump(transcript_json, f, ensure_ascii=False, indent=2)

    with open(os.path.join(out_dir, "transcript.txt"), "w", encoding="utf-8") as f:
        f.write(" ".join(transcript_parts))

    print(f"✓ transcript.json + transcript.txt written ({len(all_words)} words)")


if __name__ == "__main__":
    main()
