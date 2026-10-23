"""Regression checks for image-only Ashdod workflow safety checks.

These tests exercise the *actual inline identifier guard* from the draft
workflow, without contacting event sources, the CMS, or the public site.
"""
import collections
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFRESH_WORKFLOW = ROOT / ".github/workflows/refresh-ashdod-event-images.yml"
ENRICH_WORKFLOW = ROOT / ".github/workflows/enrich-events-images.yml"


def guard_source():
    workflow = REFRESH_WORKFLOW.read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s+python -c '([^'\n]+)'", workflow)
    if not match:
        raise AssertionError("Image workflow is missing the event-ID safety guard")
    return match.group(1)


def check_event_ids(before, after):
    """Run the production inline guard against two isolated JSON fixtures."""
    with tempfile.TemporaryDirectory(prefix="ashdod-image-guard-") as tmp:
        root = Path(tmp)
        source = root / "events-preview/ashdod/data"
        source.mkdir(parents=True)
        snapshot = root / "ashdod-images-before.json"
        snapshot.write_text(json.dumps({"events": before}), encoding="utf-8")
        (source / "events.json").write_text(json.dumps({"events": after}), encoding="utf-8")
        script = guard_source().replace("/tmp/ashdod-images-before.json", str(snapshot))
        return subprocess.run(
            [sys.executable, "-c", script],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )


class ImageSafetyTest(unittest.TestCase):
    def test_both_image_jobs_serialize_without_cancellation(self):
        for path in (REFRESH_WORKFLOW, ENRICH_WORKFLOW):
            body = path.read_text(encoding="utf-8")
            self.assertRegex(body, r"(?m)^\s+group: enrich-ashdod-event-images\s*$")
            self.assertRegex(body, r"(?m)^\s+cancel-in-progress: false\s*$")

    def test_image_only_change_passes(self):
        before = [
            {"event_id": "alpha", "image": "old"},
            {"event_id": "beta", "image": "old"},
        ]
        after = [
            {"event_id": "alpha", "image": "new"},
            {"event_id": "beta", "image": "new"},
        ]
        self.assertEqual(check_event_ids(before, after).returncode, 0)

    def test_removed_record_is_rejected(self):
        before = [{"event_id": "alpha"}, {"event_id": "beta"}]
        result = check_event_ids(before, [{"event_id": "alpha"}])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Safety stop", result.stderr)

    def test_same_count_different_identifier_is_rejected(self):
        before = [{"event_id": "alpha"}, {"event_id": "beta"}]
        self.assertNotEqual(
            check_event_ids(before, [{"event_id": "alpha"}, {"event_id": "gamma"}]).returncode,
            0,
        )

    def test_duplicate_identifier_count_is_preserved(self):
        before = [{"event_id": "alpha"}, {"event_id": "alpha"}, {"event_id": "beta"}]
        after = [{"event_id": "alpha"}, {"event_id": "beta"}, {"event_id": "beta"}]
        self.assertNotEqual(check_event_ids(before, after).returncode, 0)

    def test_retry_path_recomputes_on_remote_head_and_never_forces(self):
        workflow = REFRESH_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("git fetch origin main", workflow)
        self.assertIn("git reset --hard origin/main", workflow)
        self.assertIn("python scripts/recover_event_listing_images.py", workflow)
        self.assertIn("git push origin HEAD:main", workflow)
        self.assertNotIn("git push --force", workflow)
        self.assertNotIn("git push -f", workflow)


if __name__ == "__main__":
    unittest.main()
