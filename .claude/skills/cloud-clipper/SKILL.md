# Cloud Clipper — Stream → Viral Shorts (100% Cloud)

This skill turns any stream/VOD link (YouTube, Twitch, Kick) into ready-to-post vertical 9:16 Shorts — **entirely in the cloud**. Nothing heavy runs on your PC.

## When Does It Trigger?
Whenever you paste a stream or video link, or ask for shorts/reels/clips, e.g.:

```
Is stream se viral shorts banao 👉 https://www.youtube.com/live/XXXXXXX
```

or

```
Bana de ye video se 5 short clips
```

## How It Works (6-Step Cloud Pipeline)

### Step 1 — Cloud fetches and transcribes the link
- Cloud downloads the video via **yt-dlp** (no local downloading)
- Audio sent to **FreeLLMAPI → Groq Whisper API** for word-level transcription
- Result: `transcript.json` + `transcript.txt` in cloud storage

### Step 2 — AI scores and ranks the best moments
- Your AI (via FreeLLMAPI) reads the transcript and gives each candidate a **score 1‑10** (hook quality, payoff, viral potential)
- AI also ranks by **viral potential** (big emotional reaction, clutch play, fail/karma, funny interaction, story with payoff, hot take)
- Top N clips selected (default: 8‑15 for a 2‑4h stream)

### Step 3 — Cloud cuts the top N clips in vertical 9:16, 1080x1920
- Using **ffmpeg** in the cloud: crop/zoom to 9:16, trim to 20‑59s (sweet spot 25‑45s)
- Audio normalised to -14 LUFS
- No local rendering needed

### Step 4 — Burn in captions (including Hindi)
- Word‑by‑word captions with yellow highlight on active word
- Hook title at top of video (max ~6 words, 1 emoji max)
- Safe zones avoided (top 10%, bottom 15%, right 12%)
- Hindi captions supported via Whisper language code `hi`

### Step 5 — AI writes the publishing package for every clip
- **Title**: hook + emoji + 1 game tag (under 65 chars)
- **Description**: 1‑2 line summary
- **Tags**: 5‑8 hashtags (game + format + streamer + trending)
- **Thumbnail idea**: 1‑sentence description of best frame

### Step 6 — Save in the clipping‑project folder structure
- `clipping-project/input/source.mp4` (original)
- `clipping-project/output/clips/` — one folder per short, containing:
  - `short_01.mp4` (finished vertical video)
  - `short_01_report.md` (title, description, tags, score, reason)
- `clipping-project/output/final/` — ready‑to‑upload package

## Folder Structure (created automatically)

```
cloud-clipper/
├── SKILL.md              ← this file
├── references/
│   └── viral-rules.md    ← moment & hook rules
└── clips.json            ← (created per run, not in repo)
```

When you run the skill, a new folder `clipping‑project‑<stream‑id>/` is created next to this skill, with the structure above.

## What the Skill Does NOT Do on Your PC

- ❌ No local video downloading (cloud does it)
- ❌ No local transcription (FreeLLMAPI + Groq Whisper in cloud)
- ❌ No local ffmpeg rendering (cloud renders)
- ❌ No local face‑tracking (AI chooses zoom moments; cloud renderer applies them)
- ❌ No local GPU/OpenCV processing (everything cloud‑based)
- ❌ No local Whisper model download (uses cloud API only)

## Prerequisites (you already have these)

1. **Claude Code** (included with Claude Pro plan)
2. **FreeLLMAPI running** at `127.0.0.1:31415` with a valid API key — this is your gateway to the Groq Whisper API and other cloud LLM services
3. **Internet connection** for cloud operations

## Running the Skill

Open Claude Code, choose the `cloud-clipper` folder, and type:

```
Is stream se viral shorts banao 👉 https://www.youtube.com/live/XXXXXXX
```

Or simply:

```
Bana ye VOD se 3 short clips
```

Claude will guide you through the cloud pipeline and report progress. When finished, your shorts will be in `clipping-project-<id>/shorts/`.

## Gotcha Sections (read before proceeding)

Each pipeline step has a "Gotcha" box — the most common mistake users make. **Read these before starting.**

### ⚠️ Step 1 — Download Gotcha
- **Mistake:** Waiting for the entire stream to finish before starting
- **Fix:** The cloud pipeline works with live streams too — it downloads the available buffer and can clip sections while the stream is ongoing
- **Why it matters:** You don't have to wait for the stream to end

### ⚠️ Step 2 — Transcribe Gotcha
- **Mistake:** Using the `small` model on Hindi/Hinglish‑heavy streams and getting garbled text
- **Fix:** Use `--language hi` to force Hindi, or `--language auto` for mixed languages
- **Why it matters:** Bad transcripts = bad clip selection = wasted cloud credits

### ⚠️ Step 3 — Moment Scoring Gotcha
- **Mistake:** Scoring clips that need context from earlier in the stream (inside jokes, references)
- **Fix:** Only score clips that are understandable with zero context — read the transcript first!
- **Why it mattered:** Clips that make no sense to new viewers get 0 engagement

### ⚠️ Step 4 — Render Shorts Gotcha
- **Mistake:** Using the default blur layout on gameplay where the action is on the sides, getting cropped out
- **Fix:** The cloud pipeline defaults to `crop` layout for centered 9:16 action; use `--layout blur` only for wide‑angle shots
- **Why it matters:** Important visuals get cut off, making the clip confusing

### ⚠️ Step 5 — Publishing Gotcha
- **Mistake:** Title longer than 65 characters gets truncated in YouTube Shorts upload
- **Fix:** The AI auto‑truncates titles to under 65 chars; keep hook + emoji + game tag under this limit
- **Why it matters:** Viewers can't see the full title in the Shorts feed

### ⚠️ Step 6 — FreeLLMAPI Gotcha
- **Mistake:** FreeLLMAPI gateway not running or invalid API key
- **Fix:** Make sure FreeLLMAPI is running at `127.0.0.1:31415` before starting. Test connection with a simple prompt first
- **Why it matters:** Without FreeLLMAPI, transcription and AI scoring won't work

## Progress Updates (kept short, Hinglish OK)

During the run, you'll see updates like:

- ✓ Cloud download ho raha hai…
- ✓ Transcribe ho raha hai…
- ✓ Moments mil rahe hain (N candidates)
- ● Shorts ban rahe hain (3/5)...
- ✓ Publishing kit likha gaya
- ✓ Shorts saved → clipping-project‑<id>/

## Tips

- First run may take ~10‑20 minutes depending on stream length (transcription is the slow part)
- For Hindi/Hinglish streams: ask Claude to use `--language hi` for better captions
- Only repost streams you own or have permission to clip
- Long streams: transcription time ≈ 5‑15 min per hour of video (in the cloud, not on your PC)
- Everything runs in the cloud; nothing is uploaded to any external service except the finished short videos