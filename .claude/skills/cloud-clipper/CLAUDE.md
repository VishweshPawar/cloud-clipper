# Cloud Clipper — Project Notes

## Architecture
100% cloud pipeline via GitHub Actions. Local machine only triggers the workflow; no video/AI processing runs locally.

## FreeLLMAPI Gateway
- Runs at `127.0.0.1:31415`
- Provides access to Groq Whisper API for transcription
- Must be running before triggering the GitHub Actions workflow

## Pipeline Steps (cloud)
1. **Download** — yt-dlp fetches VOD + live chat (YouTube only)
2. **Transcribe** — Groq Whisper via FreeLLMAPI → transcript.json + transcript.txt
3. **Score moments** — find_hype.py (audio + speech + chat signals)
4. **Render shorts** — make_shorts.py (ffmpeg 9:16 + ASS captions)
5. **Publish kit** — AI writes titles, descriptions, hashtags
6. **Artifact upload** — finished shorts in `clipping-project-<id>/shorts/`

## Running locally (optional)
```bash
cd .claude/skills/cloud-clipper
pip install -r requirements.txt
python3 scripts/check_setup.py   # verify FreeLLMAPI + deps
# Trigger GitHub Actions workflow from the repo, or run scripts manually
```

## GitHub Actions workflow
`.github/workflows/cloud-clipper.yml` — triggered by workflow_dispatch with:
- `stream_url` (required)
- `num_clips` (default 8)

## Key conventions
- All timestamps in seconds (float)
- Word objects: `{w, s, e}` → `w`=word, `s`=start, `e`=end
- Layout options: `crop` (center 9:16) or `blur` (pillarbox with blurred sides)
- Captions: ASS format with karaoke highlight
- Audio normalization: -14 LUFS (YouTube Shorts standard)

## Disabled legacy skills
- `.claude/skills/youtube-clip-pipeline-disabled/` — old YouTube-only pipeline
- GTA clipper skill at `C:/Ai/gta-clipper-skill/` — renamed to `-disabled` (folder gone)