#!/usr/bin/env python3
"""Use Groq LLM API to generate titles, descriptions, hashtags, and clips.json specs.

Usage: python3 publish_kit.py <workdir> --num-clips 8 --groq-key "<key>"
"""
import argparse
import json
import os
import sys
import urllib.request


def call_groq(prompt, groq_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq Chat API error: {e}")
        return "[]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--num-clips", type=int, default=8)
    ap.add_argument("--groq-key", required=True)
    a = ap.parse_args()

    hype_path = os.path.join(a.workdir, "hype.json")
    if not os.path.exists(hype_path):
        sys.exit("hype.json missing — run find_hype.py first")

    hype = json.load(open(hype_path, encoding="utf-8"))
    cands = hype.get("candidates", [])[:a.num_clips * 2]  # take top pool

    prompt = f"""You are a professional YouTube Shorts editor.
Here are the top candidate moments from a stream:
{json.dumps(cands, indent=1)}

Select the best {a.num_clips} clips. For each clip, provide:
1. start (seconds, integer)
2. end (seconds, integer) — make duration between 25 and 55 seconds
3. title (catchy hook title under 65 chars, with 1 emoji)
4. description (1-2 lines)
5. tags (5-8 hashtags)

Return ONLY valid JSON array of objects with keys: start, end, title, description, tags. No markdown blocks, just raw JSON.
"""

    resp_text = call_groq(prompt, a.groq_key)
    # Clean markdown if present
    clean = resp_text.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1]
    if clean.endswith("```"):
        clean = clean.rsplit("\n", 1)[0]
    clean = clean.strip()

    try:
        clips = json.loads(clean)
    except Exception:
        # Fallback to top candidates
        clips = []
        for i, c in enumerate(hype.get("candidates", [])[:a.num_clips]):
            clips.append({
                "start": c["start"],
                "end": c["end"],
                "title": f"INSANE MOMENT 💀 #{i+1}",
                "description": c["text"][:150],
                "tags": ["#shorts", "#gaming", "#viral"],
            })

    os.makedirs("shorts", exist_ok=True)
    with open("clips.json", "w", encoding="utf-8") as f:
        json.dump(clips, f, indent=2, ensure_ascii=False)

    for i, c in enumerate(clips, 1):
        report = f"""# Short #{i:02d}

## Title
{c['title']}

## Description
{c.get('description', '')}

## Hashtags
{' '.join(c.get('tags', []))}

## Timing
Start: {c['start']}s | End: {c['end']}s
"""
        with open(os.path.join("shorts", f"short_{i:02d}_report.md"), "w", encoding="utf-8") as f:
            f.write(report)

    print(f"✓ Generated {len(clips)} clip specs + reports")


if __name__ == "__main__":
    main()
