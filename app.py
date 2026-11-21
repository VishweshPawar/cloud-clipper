import os
import json
import re
import subprocess
import sys
import threading
import time
from flask import Flask, render_template, request, jsonify, send_file
import webbrowser

app = Flask(__name__)

# Configuration
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
DEFAULT_GATEWAY = "http://127.0.0.1:31415"
SKILL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".claude", "skills", "youtube-clip-pipeline")

# Load/save .env config
def load_config():
    config = {
        "api_key": "",
        "gateway_url": DEFAULT_GATEWAY
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        config[key.strip()] = val.strip()
        except Exception:
            pass
    return config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(f"API_KEY={config['api_key']}\n")
            f.write(f"GATEWAY_URL={config['gateway_url']}\n")
    except Exception as e:
        print(f"Error saving config: {e}")

config = load_config()

@app.route("/")
def index():
    return render_template("index.html",
                         api_key=config["api_key"],
                         gateway_url=config["gateway_url"],
                         short_mode=False)

@app.route("/settings", methods=["POST"])
def settings():
    data = request.get_json()
    config["api_key"] = data.get("api_key", "")
    config["gateway_url"] = data.get("gateway_url", DEFAULT_GATEWAY)
    save_config(config)
    return jsonify({"status": "saved"})

@app.route("/test-connection", methods=["POST"])
def test_connection():
    data = request.get_json()
    gateway = data.get("gateway_url", DEFAULT_GATEWAY)
    api_key = data.get("api_key", "")

    if not api_key:
        return jsonify({"status": "error", "message": "API key is required"})

    # Test the FreeLLMAPI gateway
    try:
        import requests
        # Simple health check
        resp = requests.get(f"{gateway}/health", timeout=5)
        if resp.status_code == 200:
            return jsonify({"status": "success", "message": "Gateway connection OK"})
        else:
            return jsonify({"status": "partial", "message": f"Gateway responded: {resp.status_code}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Cannot connect to gateway: {str(e)}"})

@app.route("/make-clips", methods=["POST"])
def make_clips():
    data = request.get_json()
    youtube_url = data.get("youtube_url", "")
    num_clips = int(data.get("num_clips", 5))

    if not youtube_url:
        return jsonify({"status": "error", "message": "YouTube URL is required"})

    # Save config if not already saved
    if not config["api_key"] and data.get("api_key"):
        config["api_key"] = data["api_key"]
        config["gateway_url"] = data.get("gateway_url", DEFAULT_GATEWAY)
        save_config(config)

    # Run the pipeline in a background thread
    thread = threading.Thread(target=run_pipeline, args=(youtube_url, num_clips))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "message": "Pipeline started in background"})

def run_pipeline(youtube_url, num_clips):
    """Run the full clip pipeline using skill scripts"""
    try:
        # Create work directory with video name
        video_id = re.sub(r'[^\w]', '', youtube_url[-11:]) if len(youtube_url) >= 11 else re.sub(r'[^\w]', '', youtube_url[:50])
        work_dir = os.path.join("C:\\claudepro\\output", f"video_{video_id}")
        os.makedirs(work_dir, exist_ok=True)

        print(f"=== Pipeline started for: {youtube_url} ===")
        print(f"Work directory: {work_dir}")

        # Step 1: Download using skill's download.py
        print("Step 1: Downloading stream...")
        download_script = os.path.join(SKILL_DIR, "scripts", "download.py")
        result = subprocess.run([
            sys.executable, download_script, youtube_url,
            "--out", work_dir,
            "--max-height", "1080",
            "--no-chat"  # chat is optional bonus signal
        ], capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            print(f"Download failed: {result.stderr}")
            print(f"Stdout: {result.stdout}")
            return

        print(result.stdout)
        source_file = os.path.join(work_dir, "source.mp4")
        if not os.path.exists(source_file):
            for f in os.listdir(work_dir):
                if f.endswith(".mp4") or f.endswith(".webm"):
                    source_file = os.path.join(work_dir, f)
                    break

        print(f"Downloaded: {source_file}")

        # Step 2: Transcribe using skill's transcribe.py (cloud-only via FreeLLMAPI)
        print("Step 2: Transcribing (cloud-only via FreeLLMAPI)...")
        transcribe_script = os.path.join(SKILL_DIR, "scripts", "transcribe.py")

        # Use FreeLLMAPI gateway for transcription - this is the cloud path
        # Pass the API key and gateway URL
        env = os.environ.copy()
        env["FREELLM_API_KEY"] = config["api_key"]
        env["FREELLM_GATEWAY"] = config["gateway_url"]

        result = subprocess.run([
            sys.executable, transcribe_script, source_file,
            "--model", "small",  # Groq Whisper via FreeLLMAPI
            "--language", "auto"
        ], capture_output=True, text=True, timeout=900, env=env)

        if result.returncode != 0:
            print(f"Transcribe failed: {result.stderr}")
            print(f"Stdout: {result.stdout}")
            return

        print(result.stdout)

        # Step 3: Find hype moments using skill's find_hype.py
        print("Step 3: Finding high-engagement moments...")
        find_hype_script = os.path.join(SKILL_DIR, "scripts", "find_hype.py")
        result = subprocess.run([
            sys.executable, find_hype_script, work_dir,
            "--window", "30",
            "--top", "25"
        ], capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            print(f"Find hype failed: {result.stderr}")
            print(f"Stdout: {result.stdout}")
            return

        print(result.stdout)

        # Step 4: User picks clips - we'll auto-pick top N from hype.json
        # Read hype.json and create clips.json
        hype_path = os.path.join(work_dir, "hype.json")
        if not os.path.exists(hype_path):
            print("No hype.json found")
            return

        with open(hype_path, "r") as f:
            hype_data = json.load(f)

        candidates = hype_data.get("candidates", [])
        clips = []

        # Read transcript for word boundaries
        transcript_path = os.path.join(work_dir, "transcript.json")
        transcript_words = []
        if os.path.exists(transcript_path):
            with open(transcript_path, "r") as f:
                transcript_data = json.load(f)
                transcript_words = transcript_data.get("words", [])

        # Auto-pick top N clips
        for i, cand in enumerate(candidates[:num_clips]):
            start_sec = cand["start"]
            end_sec = cand["end"]

            # Snap to word boundaries
            start_ts = snap_to_word(start_sec, transcript_words, "start")
            end_ts = snap_to_word(end_sec, transcript_words, "end")

            # Ensure 20-59s duration
            duration = end_ts - start_ts
            if duration < 20:
                end_ts = start_ts + 25
            elif duration > 59:
                end_ts = start_ts + 45

            clips.append({
                "id": i + 1,
                "start": format_time(start_ts),
                "end": format_time(end_ts),
                "hook": generate_hook(cand["text"][:100]),
                "title": generate_title(cand["text"][:100]),
                "reason": f"score {cand['score']}: {cand['text'][:80]}",
                "score": cand["score"]
            })

        clips_path = os.path.join(work_dir, "clips.json")
        with open(clips_path, "w") as f:
            json.dump(clips, f, indent=2)

        print(f"Created {len(clips)} clips in clips.json")

        # Step 5: Render shorts using skill's make_shorts.py
        print("Step 5: Rendering shorts...")
        make_shorts_script = os.path.join(SKILL_DIR, "scripts", "make_shorts.py")
        result = subprocess.run([
            sys.executable, make_shorts_script, work_dir,
            "--layout", "crop"  # default to crop for centered action
        ], capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            print(f"Make shorts failed: {result.stderr}")
            print(f"Stdout: {result.stdout}")
            return

        print(result.stdout)

        # Step 6: Generate posting kit (titles, descriptions, tags)
        print("Step 6: Generating posting kit...")
        generate_posting_kit(work_dir, clips, youtube_url)

        print(f"=== Pipeline complete! Clips saved to: {work_dir} ===")

    except subprocess.TimeoutExpired:
        print("Pipeline step timed out")
    except Exception as e:
        print(f"Pipeline error: {e}")
        import traceback
        traceback.print_exc()

def snap_to_word(sec, words, direction):
    """Snap timestamp to nearest word boundary"""
    if not words:
        return sec

    if direction == "start":
        # Find word that starts at or after this second
        for w in words:
            if w.get("s", 0) >= sec:
                return w["s"]
        return words[-1]["s"] if words else sec
    else:
        # Find word that ends at or before this second
        for w in reversed(words):
            if w.get("e", 0) <= sec:
                return w["e"]
        return words[-1]["e"] if words else sec

def format_time(sec):
    """Format seconds as HH:MM:SS.m"""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:04.1f}"

def generate_hook(text):
    """Generate a hook from transcript text"""
    # Simple heuristic: take exciting words
    words = text.split()
    if len(words) <= 6:
        return " ".join(words).upper() + " 😂"
    return " ".join(words[:6]).upper() + " 😂"

def generate_title(text):
    """Generate a title from transcript text"""
    words = text.split()
    base = " ".join(words[:8])
    return f"{base} #shorts"[:65]

def generate_posting_kit(work_dir, clips, youtube_url):
    """Generate posting-kit.md with titles, descriptions, tags"""
    lines = ["# Posting Kit\n"]
    lines.append(f"Source: {youtube_url}\n")

    for clip in clips:
        lines.append(f"## Clip {clip['id']}")
        lines.append(f"**Title:** {clip['title']}")
        lines.append(f"**Hook:** {clip['hook']}")
        lines.append(f"**Time:** {clip['start']} – {clip['end']}")
        lines.append(f"**Reason:** {clip['reason']}")
        lines.append(f"**Hashtags:** #shorts #gaming #viral #fyp #clip #highlights")
        lines.append("")

    # Best clip recommendation
    if clips:
        best = max(clips, key=lambda c: c.get("score", 0))
        lines.append("---")
        lines.append(f"## 🎯 Best Clip to Post First: Clip {best['id']}")
        lines.append(f"Reason: Highest score ({best['score']}) - {best['reason'][:100]}")

    kit_path = os.path.join(work_dir, "posting-kit.md")
    with open(kit_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Posting kit saved to: {kit_path}")

if __name__ == "__main__":
    # Open browser
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:5000")

    t = threading.Thread(target=open_browser)
    t.daemon = True
    t.start()

    app.run(host="127.0.0.1", port=5000, debug=False)