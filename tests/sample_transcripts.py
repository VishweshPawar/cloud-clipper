#!/usr/bin/env python3
"""Test samples for the cloud-clipper pipeline."""

import json
import os

# Sample transcript with words
SAMPLE_TRANSCRIPT_WITH_WORDS = {
    "words": [
        {"w": "hello", "s": 0.0, "e": 0.5},
        {"w": "world", "s": 0.5, "e": 1.0},
        {"w": "this", "s": 1.5, "e": 2.0},
        {"w": "is", "s": 2.0, "e": 2.5},
        {"w": "fun", "s": 2.5, "e": 3.0},
    ],
    "text": "hello world this is fun"
}

# Sample transcript with segments only
SAMPLE_TRANSCRIPT_SEGMENTS_ONLY = {
    "segments": [
        {"start": 0.0, "end": 2.5, "text": "hello world this is fun"},
        {"start": 5.0, "end": 7.5, "text": "another segment here"},
        {"start": 10.0, "end": 12.0, "text": "final words"}
    ],
    "text": "hello world this is fun another segment here final words"
}

# Empty transcript
SAMPLE_TRANSCRIPT_EMPTY = {}

# Transcript with empty segments
SAMPLE_TRANSCRIPT_EMPTY_SEGMENTS = {
    "segments": [],
    "text": ""
}

# Transcript with words but no segments
SAMPLE_TRANSCRIPT_WORDS_NO_SEGMENTS = {
    "words": [
        {"w": "test", "s": 0.0, "e": 1.0},
        {"w": "words", "s": 1.0, "e": 2.0}
    ],
    "text": "test words"
}

# Live status JSON
SAMPLE_LIVE_STATUS = {
    "is_live": True,
    "title": "Test Live Stream",
    "requested_url": "https://www.youtube.com/watch?v=test"
}

# Info JSON
SAMPLE_INFO = {
    "id": "test123",
    "title": "Test Video",
    "uploader": "Test Channel",
    "channel": "Test Channel",
    "duration": 120,
    "webpage_url": "https://www.youtube.com/watch?v=test123",
    "extractor": "youtube",
    "upload_date": "20240101"
}

def get_samples_dir():
    """Get the samples directory path."""
    return os.path.join(os.path.dirname(__file__), "samples")

def ensure_samples_dir():
    """Ensure the samples directory exists and has all test files."""
    samples_dir = get_samples_dir()
    os.makedirs(samples_dir, exist_ok=True)

    samples = {
        "transcript_with_words.json": SAMPLE_TRANSCRIPT_WITH_WORDS,
        "transcript_segments_only.json": SAMPLE_TRANSCRIPT_SEGMENTS_ONLY,
        "transcript_empty.json": SAMPLE_TRANSCRIPT_EMPTY,
        "transcript_empty_segments.json": SAMPLE_TRANSCRIPT_EMPTY_SEGMENTS,
        "transcript_words_no_segments.json": SAMPLE_TRANSCRIPT_WORDS_NO_SEGMENTS,
        "live_status.json": SAMPLE_LIVE_STATUS,
        "info.json": SAMPLE_INFO,
    }

    for filename, data in samples.items():
        filepath = os.path.join(samples_dir, filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    return samples_dir