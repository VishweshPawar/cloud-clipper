# Cloud Clipper Progress

## Completed (11/11 files + structure)

| File | Status |
|------|--------|
| `SKILL.md` | ✓ merged 6-step cloud pipeline |
| `references/viral-rules.md` | ✓ copied viral moment rules |
| `.github/workflows/cloud-clipper.yml` | ✓ GitHub Actions workflow |
| `scripts/download.py` | ✓ yt-dlp download + chat replay |
| `scripts/transcribe.py` | ✓ FreeLLMAPI + Groq Whisper |
| `scripts/find_hype.py` | ✓ audio/speech/chat scoring |
| `scripts/make_shorts.py` | ✓ 9:16 render + ASS captions |
| `scripts/check_setup.py` | ✓ pre-run checker |
| `scripts/progress.py` | ✓ terminal progress bar |
| `requirements.txt` | ✓ Python deps list |
| `CLAUDE.md` | ✓ project notes |

## Folder structure

```
C:/claudepro/
├── clipping-project/
│   ├── input/          ← source.mp4 lands here
│   ├── output/
│   │   ├── clips/      ← short_01.mp4, short_01_report.md, etc.
│   │   └── final/      ← ready-to-upload package
│   └── work/           ← temp folder for GitHub Actions
├── PROGRESS.md         ← this file
└── cloud-clipper/      ← skill (ready to use)
    ├── SKILL.md
    ├── .github/workflows/cloud-clipper.yml
    ├── references/viral-rules.md
    └── scripts/*.py
```

## Disabled legacy skills

| Old Skill | New Status |
|-----------|------------|
| `.claude/skills/youtube-clip-pipeline/` | renamed to `-disabled` |
| `gta-clipper-skill/` at `C:/Ai/` | renamed to `-disabled` (folder removed) |

## Next steps

1. Trigger GitHub Actions workflow from the `cloud-clipper/` repo
2. Or run locally with `python3 scripts/check_setup.py` first
3. Paste a stream/video link to use the skill

## Workflow Testing Instructions (for BOSS)

### To test the Cloud Clipper GitHub Actions workflow:

1. Go to the repo on GitHub
2. Click the **Actions** tab
3. Select "Cloud Clipper — Stream to Viral Shorts" workflow
4. Click **Run workflow**
5. Enter a YouTube URL in the `stream_url` field
   - Test with: https://www.youtube.com/watch?v=dQw4w9WgXcQ (Rick Roll - works reliably)
   - Or use your own video/stream URL
6. Adjust `num_clips` if desired (default: 8)
7. Click **Run workflow**

### Expected secrets (already configured):
- `GROQ_API_KEY` - Primary Groq API key for Whisper transcription
- `TEST_GROQ_KEY` - Fallback Groq API key
- `YOUTUBE_COOKIES` - Optional, for videos that may be blocked

### Workflow Features:
- Uses bun JS runtime for yt-dlp
- Multi-attempt download logic (user URL → test video fallback)
- TEST_GROQ_KEY fallback mechanism for transcription
- Downloads to source.mp4, transcribes, scores moments, renders shorts

## Recent Fixes (2026-11-19)

### Workflow Updates
- Added Node.js/bun installation (lines 43-50 in cloud-clipper.yml)
- Added TEST_GROQ_KEY fallback mechanism for transcription
- Added multi-attempt download logic (user URL → test video fallback)
- Fixed boundary format in transcribe.py (WebKit→GroqBoundary)
- Fixed model default (small→whisper-large-v3-turbo)
- Added missing `sys` import in publish_kit.py
- Fixed empty transcript guards in find_hype.py

### Files Pushed
- `.github/workflows/cloud-clipper.yml` - Main workflow with all fixes
- `.github/workflows/test-workflow.yaml` - Quick test workflow
- `.claude/skills/cloud-clipper/scripts/publish_kit.py` - sys import fix

---
Updated: 2026-11-19