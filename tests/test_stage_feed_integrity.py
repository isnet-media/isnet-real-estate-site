"""Regression checks for conservative stage deduplication and public-feed ID audit."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import swap_our_stage_events_with_boards as swap
import verify_public_event_readback as readback


def event(event_id, venue, source, **extra):
    return {
        "event_id": event_id,
        "title": "Test stage production",
        "start_date": "2099-11-20",
        "start_time": "20:00",
        "category": "theatre",
        "venue": venue,
        "source": source,
        **extra,
    }


class SafeStageMergeTests(unittest.TestCase):
    def run_swap(self, events):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            collected_path = root / "events-preview/admin/data/unified-stage-events-ashdod-rishon.json"
            report_path = root / "events-preview/admin/data/stage-board-swap-report.json"
            collected_path.parent.mkdir(parents=True)
            collected_path.write_text(json.dumps({"events": []}), encoding="utf-8")
            for city in ("ashdod", "rishon-lezion"):
                path = root / f"events-preview/{city}/data/events.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({"events": events if city == "rishon-lezion" else []}), encoding="utf-8")
            with mock.patch.object(swap, "ROOT", root), mock.patch.object(swap, "COLLECT", collected_path), mock.patch.object(swap, "REPORT", report_path), mock.patch.dict(os.environ, {"STAGE_SWAP_FROM_BOARDS": "YES_MATCHED_EVENTS_ONLY"}), redirect_stdout(io.StringIO()):
                swap.main()
            return json.loads((root / "events-preview/rishon-lezion/data/events.json").read_text())["events"]

    def test_same_title_date_time_but_different_venues_must_both_survive(self):
        before = [event("board_a", "Hall A", "national_stage_boards"), event("auto_b", "Hall B", "agent")]
        self.assertEqual({x["event_id"] for x in self.run_swap(before)}, {"board_a", "auto_b"})

    def test_unknown_venue_must_not_be_deduplicated(self):
        before = [event("board_a", "", "national_stage_boards"), event("auto_b", "", "agent")]
        self.assertEqual(len(self.run_swap(before)), 2)

    def test_matching_venue_and_occurrence_can_remove_unlocked_agent_duplicate(self):
        before = [event("board_a", "Hall A", "national_stage_boards"), event("auto_b", "Hall A", "agent")]
        self.assertEqual([x["event_id"] for x in self.run_swap(before)], ["board_a"])

    def test_editor_locked_card_must_not_be_removed(self):
        before = [event("board_a", "Hall A", "national_stage_boards"), event("auto_b", "Hall A", "agent", human_manual_override=True)]
        self.assertEqual(len(self.run_swap(before)), 2)


class FakeResponse:
    status = 200
    headers = {"Last-Modified": "Sat, 24 Oct 2026 09:40:00 GMT"}

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, limit=-1):
        return self.payload[:limit] if limit > 0 else self.payload


class ReadbackDuplicateAuditTests(unittest.TestCase):
    def test_identical_feeds_can_still_have_colliding_event_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "events-preview/rishon-lezion/data/events.json"
            path.parent.mkdir(parents=True)
            data = {"events": [
                event("board_collision", "Hall A", "mevalim_direct"),
                event("board_collision", "Hall A", "national_stage_boards"),
            ]}
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            path.write_bytes(payload)
            with mock.patch.object(readback.urllib.request, "urlopen", return_value=FakeResponse(payload)):
                result = readback.compare_city("rishon-lezion", root)
            self.assertEqual(result["status"], "match")
            self.assertTrue(result["exact_feed_match"])
            self.assertFalse(result["event_ids_unique"])
            self.assertEqual(result["github_duplicate_event_id_groups"], 1)
            self.assertEqual(result["github_duplicate_event_rows"], 1)
            self.assertEqual(result["github_duplicate_event_id_examples"], ["board_collision"])


if __name__ == "__main__":
    unittest.main()
