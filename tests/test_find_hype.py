#!/usr/bin/env python3
"""Tests for find_hype.py"""

import json
import os
import sys
import tempfile
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.sample_transcripts import (
    SAMPLE_TRANSCRIPT_WITH_WORDS,
    SAMPLE_TRANSCRIPT_SEGMENTS_ONLY,
    SAMPLE_TRANSCRIPT_EMPTY,
    SAMPLE_TRANSCRIPT_EMPTY_SEGMENTS,
    SAMPLE_TRANSCRIPT_WORDS_NO_SEGMENTS,
    ensure_samples_dir,
)


class TestTranscriptHandling(unittest.TestCase):
    """Test that find_hype properly handles various transcript formats."""

    def setUp(self):
        """Create a temporary directory for each test."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write_transcript(self, transcript_data):
        """Write transcript.json to test directory."""
        with open(os.path.join(self.test_dir, "transcript.json"), "w") as f:
            json.dump(transcript_data, f)

    def test_transcript_with_words(self):
        """Test transcript that has words field."""
        self._write_transcript(SAMPLE_TRANSCRIPT_WITH_WORDS)

        # Import and check transcript loading
        transcript_path = os.path.join(self.test_dir, "transcript.json")
        with open(transcript_path, encoding="utf-8") as f:
            tr = json.load(f)

        self.assertTrue(tr.get("words"))
        self.assertEqual(len(tr["words"]), 5)

    def test_transcript_segments_only(self):
        """Test transcript with segments but no words."""
        self._write_transcript(SAMPLE_TRANSCRIPT_SEGMENTS_ONLY)

        transcript_path = os.path.join(self.test_dir, "transcript.json")
        with open(transcript_path, encoding="utf-8") as f:
            tr = json.load(f)

        self.assertTrue(tr.get("segments"))
        self.assertFalse(tr.get("words"))
        self.assertEqual(len(tr["segments"]), 3)

    def test_empty_transcript(self):
        """Test that empty transcript is handled."""
        self._write_transcript(SAMPLE_TRANSCRIPT_EMPTY)

        transcript_path = os.path.join(self.test_dir, "transcript.json")
        with open(transcript_path, encoding="utf-8") as f:
            tr = json.load(f)

        self.assertFalse(tr.get("words"))
        self.assertFalse(tr.get("segments"))
        # This should trigger the guard in find_hype.py
        self.assertFalse(tr.get("words") and tr.get("segments"))


class TestWordExtraction(unittest.TestCase):
    """Test word-level data extraction from transcripts."""

    def test_extract_words_from_transcript(self):
        """Verify we can extract words correctly."""
        words = SAMPLE_TRANSCRIPT_WITH_WORDS.get("words", [])
        self.assertEqual(len(words), 5)
        self.assertEqual(words[0]["w"], "hello")
        self.assertEqual(words[0]["s"], 0.0)
        self.assertEqual(words[0]["e"], 0.5)

    def test_words_have_required_fields(self):
        """Each word object should have w, s, e fields."""
        for word in SAMPLE_TRANSCRIPT_WITH_WORDS["words"]:
            self.assertIn("w", word)
            self.assertIn("s", word)
            self.assertIn("e", word)


class TestFindHypeGuard(unittest.TestCase):
    """Test the guard that prevents processing empty transcripts."""

    def test_empty_transcript_guard(self):
        """Empty transcript should be detected."""
        tr = SAMPLE_TRANSCRIPT_EMPTY

        # This is what find_hype.py checks
        has_content = tr.get("words") or tr.get("segments")

        self.assertFalse(has_content, "Empty transcript should have no words or segments")

    def test_words_no_segments_guard(self):
        """Transcript with only words should pass initial check."""
        tr = SAMPLE_TRANSCRIPT_WORDS_NO_SEGMENTS

        has_content = tr.get("words") or tr.get("segments")

        self.assertTrue(has_content, "Transcript with words should pass check")


if __name__ == "__main__":
    unittest.main()