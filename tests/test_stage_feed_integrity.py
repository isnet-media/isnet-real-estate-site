"""Regression checks for conservative stage deduplication and public-feed ID audit."""
import io
import hashlib
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
    def run_swap(self, events, candidates=None, include_report=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            collected_path = root / "events-preview/admin/data/unified-stage-events-ashdod-rishon.json"
            report_path = root / "events-preview/admin/data/stage-board-swap-report.json"
            collected_path.parent.mkdir(parents=True)
            collected_path.write_text(json.dumps({"events": candidates or []}), encoding="utf-8")
            for city in ("ashdod", "rishon-lezion"):
                path = root / f"events-preview/{city}/data/events.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({"events": events if city == "rishon-lezion" else []}), encoding="utf-8")
            with mock.patch.object(swap, "ROOT", root), mock.patch.object(swap, "COLLECT", collected_path), mock.patch.object(swap, "REPORT", report_path), mock.patch.dict(os.environ, {"STAGE_SWAP_FROM_BOARDS": "YES_MATCHED_EVENTS_ONLY"}), redirect_stdout(io.StringIO()):
                swap.main()
            result = json.loads((root / "events-preview/rishon-lezion/data/events.json").read_text())["events"]
            if include_report:
                return result, json.loads(report_path.read_text())["cities"]["rishon-lezion"]
            return result

    def test_same_title_date_time_but_different_venues_must_both_survive(self):
        before = [event("board_a", "Hall A", "national_stage_boards"), event("auto_b", "Hall B", "agent")]
        self.assertEqual({x["event_id"] for x in self.run_swap(before)}, {"board_a", "auto_b"})

    def test_unknown_venue_must_not_be_deduplicated(self):
        before = [event("board_a", "", "national_stage_boards"), event("auto_b", "", "agent")]
        self.assertEqual(len(self.run_swap(before)), 2)

    def test_matching_venue_and_occurrence_is_only_flagged_for_cms_review(self):
        before = [event("board_a", "Hall A", "national_stage_boards"), event("auto_b", "Hall A", "agent")]
        after, report = self.run_swap(before, include_report=True)
        self.assertEqual(after, before, "A possible duplicate is not permission to delete a CMS card")
        self.assertEqual(report["duplicate_agent_records_removed"], 0)
        self.assertEqual(report["duplicate_agent_records_review_required"], 1)
        self.assertEqual(report["duplicate_agent_id_examples"], ["auto_b"])

    def test_editor_locked_card_must_not_be_removed(self):
        before = [event("board_a", "Hall A", "national_stage_boards"), event("auto_b", "Hall A", "agent", human_manual_override=True)]
        self.assertEqual(len(self.run_swap(before)), 2)


    def test_new_board_card_must_not_duplicate_an_existing_event_id(self):
        candidate = {
            "city": "rishon-lezion",
            "title": "Test stage production",
            "date_time": "2099-11-20T20:00:00",
            "venue": "Hall A",
            "source_id": "mevalim",
        }
        generated = "board_" + hashlib.sha256(
            "rishon-lezion|test stage production|2099-11-20|20:00".encode()
        ).hexdigest()[:18]
        existing = event(generated, "Hall B", "mevalim_direct", title="Another show")
        after, report = self.run_swap([existing], candidates=[candidate], include_report=True)
        self.assertEqual(after, [existing])
        self.assertEqual(report["new_imported"], 0)
        self.assertEqual(report["id_collisions_skipped"], 1)
        self.assertEqual(report["id_collision_examples"][0]["event_id"], generated)

    def test_new_board_card_without_id_collision_is_still_imported(self):
        candidate = {
            "city": "rishon-lezion",
            "title": "Test stage production",
            "date_time": "2099-11-20T20:00:00",
            "venue": "Hall A",
            "source_id": "mevalim",
        }
        after, report = self.run_swap([], candidates=[candidate], include_report=True)
        self.assertEqual(len(after), 1)
        self.assertTrue(after[0]["event_id"].startswith("board_"))
        self.assertEqual(report["new_imported"], 1)
        self.assertEqual(report["id_collisions_skipped"], 0)

    def test_matching_title_and_date_cannot_overwrite_another_venue(self):
        original = event("auto_a", "Hall A", "agent", description="Keep the original")
        candidate = {
            "city": "rishon-lezion", "title": original["title"],
            "date_time": "2099-11-20T20:00:00", "venue": "Hall B",
            "source_id": "mevalim", "description": "B" * 120,
        }
        after = self.run_swap([original], [candidate])
        self.assertEqual(after, [original])

    def test_matching_title_and_date_cannot_overwrite_another_showtime(self):
        original = event("auto_a", "Hall A", "agent", description="Keep the original")
        candidate = {
            "city": "rishon-lezion", "title": original["title"],
            "date_time": "2099-11-20T21:00:00", "venue": "Hall A",
            "source_id": "mevalim", "description": "B" * 120,
        }
        after = self.run_swap([original], [candidate])
        self.assertIn(original, after)
        self.assertEqual(len(after), 2, "Distinct showtime should be retained as a separate candidate")

    def test_exact_match_does_not_erase_original_copy_or_verified_photo(self):
        original = event("auto_a", "Hall A", "agent",
                         description="Approved local description",
                         series_description="Approved series description",
                         content_source_url="https://example.org/original",
                         image_url="https://example.org/approved.jpg",
                         image_source="official",
                         image_verified=True, image_publishable=True,
                         image_rights_status="approved")
        candidate = {
            "city": "rishon-lezion", "title": original["title"],
            "date_time": "2099-11-20T20:00:00", "venue": "Hall A",
            "source_id": "mevalim", "description": "Short",
            "image_url": "https://example.org/unreviewed.jpg",
            "source_url": "https://example.org/board",
        }
        after, report = self.run_swap([original], [candidate], include_report=True)
        self.assertEqual(len(after), 1)
        self.assertEqual(report["replaced"], 1)
        for key in ("description", "series_description", "content_source_url",
                    "image_url", "image_source", "image_verified",
                    "image_publishable", "image_rights_status"):
            self.assertEqual(after[0].get(key), original.get(key), key)
        self.assertNotIn("image_origin_url", after[0], "Rejected image URL must not leak into provenance")

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
