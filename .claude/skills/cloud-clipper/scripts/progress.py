#!/usr/bin/env python3
"""Terminal progress bar that sits at the BOTTOM of the terminal.

Drawn with carriage returns so it stays pinned to the bottom while other
output scrolls above it. Usage:

    from progress import bar
    for i in range(100):
        bar(i + 1, 100, "Downloading stream")
        time.sleep(0.1)
    bar(100, 100, "Done", done=True)

Also exposes a one-shot helper to show the overall build progress of the
cloud-clipper project itself:

    python3 progress.py            # print the project progress bar once
    python3 progress.py --watch    # live-updating bar (Ctrl-C to exit)
"""
import os
import sys
import time

WIDTH = 28          # bar width in characters
FILLED = "█"
EMPTY = "░"


def _term_width():
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 80


def render(done, total, label="", done_label="", width=WIDTH):
    """Return one full progress-line string (no newline)."""
    pct = 0.0 if total <= 0 else max(0.0, min(1.0, done / total))
    n = int(width * pct)
    bar = FILLED * n + EMPTY * (width - n)
    txt = done_label if (done_label and done >= total) else label
    line = f"\r{bar} {pct * 100:5.1f}%  {txt}"
    pad = max(0, _term_width() - len(line) - 1)
    return line + " " * pad


def bar(done, total, label="", done_label="", end=""):
    """Print (overwrite) the progress line. Call with done>=total to finish."""
    sys.stdout.write(render(done, total, label, done_label))
    sys.stdout.flush()
    if done >= total and total > 0:
        sys.stdout.write(end if end else "\n")
        sys.stdout.flush()


class live:
    """Context manager that keeps a progress bar pinned at the bottom while
    other print() output scrolls above it. Usage:

        with live(100, "Rendering shorts") as p:
            for i in range(100):
                do_work(i)
                p.set(i + 1)
    """

    def __init__(self, total, label="", done_label="", width=WIDTH):
        self.total = total
        self.label = label
        self.done_label = done_label or label
        self.width = width
        self.done = 0
        self._fh = sys.stdout

    def __enter__(self):
        self._draw()
        return self

    def __exit__(self, *exc):
        bar(self.done, self.total, self.label, self.done_label)
        return False

    def set(self, done, label=None):
        self.done = max(0, min(self.total, done))
        if label is not None:
            self.label = label
        self._draw()

    def _draw(self):
        self._fh.write(render(self.done, self.total, self.label, self.done_label, self.width))
        self._fh.flush()


# ---------------------------------------------------------------------------
# Project build progress (for "how much of cloud-clipper is built")
# ---------------------------------------------------------------------------

# (relative path inside the skill, human label)
CHECKLIST = [
    ("SKILL.md", "Skill instructions"),
    ("references/viral-rules.md", "Viral rules reference"),
    (".github/workflows/cloud-clipper.yml", "Cloud pipeline (GitHub Actions)"),
    ("scripts/download.py", "Cloud download"),
    ("scripts/transcribe.py", "Cloud transcription"),
    ("scripts/find_hype.py", "Moment scoring"),
    ("scripts/make_shorts.py", "Short renderer"),
    ("scripts/progress.py", "Terminal progress bar"),
    ("scripts/check_setup.py", "Setup checker"),
    ("requirements.txt", "Dependencies"),
    ("CLAUDE.md", "Project notes"),
]


def project_progress(skill_root=None):
    """Return (done, total, missing) for the cloud-clipper build checklist."""
    if skill_root is None:
        skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    done = 0
    missing = []
    for rel, _label in CHECKLIST:
        if os.path.exists(os.path.join(skill_root, rel)):
            done += 1
        else:
            missing.append(rel)
    return done, len(CHECKLIST), missing


def show_project_bar(skill_root=None, watch=False, width=WIDTH):
    done, total, missing = project_progress(skill_root)
    bar(done, total, "Building cloud-clipper", done_label="cloud-clipper ✓")
    if missing:
        print("  missing:", ", ".join(missing))
    return done, total


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        try:
            while True:
                done, total, _ = project_progress(root)
                bar(done, total, "Building cloud-clipper", done_label="cloud-clipper ✓")
                if done >= total:
                    print()
                    break
                time.sleep(0.5)
        except KeyboardInterrupt:
            print()
    else:
        show_project_bar(root)