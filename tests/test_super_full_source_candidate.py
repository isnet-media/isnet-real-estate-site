"""Regression tests for PRIVATE full-tree candidates; never publish a bundle."""
import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.verify_super_full_source_candidate import (
    inspect_city, pinned_commit, stage_candidate, tlv_blocker,
)


class FullCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "ci@localhost"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "CI"], check=True)
        self.city = self.root / "SUPER.ASHDOD"
        (self.city / "data").mkdir(parents=True)
        stamp = "2026-11-11T09:00:00+02:00"
        self.refresh = {
            "checked_at": stamp, "branch_count": 2, "updated_count": 1,
            "all_sources_updated": False,
            "coverage_status": "partial",
            "branches": [
                {"branch_id": "store-1", "status": "updated"},
                {"branch_id": "store-2", "status": "retained_previous"},
            ],
        }
        self.prices = {"retrieved_at": stamp, "branch_count": 2,
                       "coverage_complete": False,
                       "branches": [{"id": "store-1"}, {"id": "store-2"}]}
        self.source_status = {"updated_at": "2026-11-11"}
        for name, data in (("refresh-status", self.refresh), ("prices", self.prices),
                           ("source-status", self.source_status), ("catalog", {"ok": True})):
            (self.city / "data" / (name + ".json")).write_text(json.dumps(data), encoding="utf-8")
        for filename in ("index.html", "compare/index.html", "deals/index.html",
                         "recipes/index.html", "smart-shopping/index.html"):
            p = self.city / filename
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("<!doctype html><html><body>Private source</body></html>", encoding="utf-8")
        self.commit()

    def commit(self):
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "test source"], check=True)
        self.sha = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()

    def rewrite(self, filename, value):
        (self.city / "data" / (filename + ".json")).write_text(json.dumps(value), encoding="utf-8")

    def test_valid_partial_source_builds_separate_private_candidate(self):
        before = (self.city / "data" / "prices.json").read_bytes()
        out = Path(self.temp.name) / "release"
        r = stage_candidate(self.root, out, "ASHDOD", self.sha)
        self.assertEqual(r["updated_count"], 1)
        self.assertEqual(r["retained_previous_count"], 1)
        self.assertEqual(r["committed_main_sha"], self.sha)
        self.assertFalse(r["approved_for_public"])
        self.assertFalse(r["media_rights_verified"])
        self.assertFalse(r["same_url_rollback_proved"])
        self.assertEqual((out / "SUPER.ASHDOD/data/prices.json").read_bytes(), before)
        self.assertEqual((self.city / "data" / "prices.json").read_bytes(), before)
        self.assertTrue((out / "release-manifest.json").is_file())
        self.assertTrue((out / "PRIVATE-REVIEW-ONLY.json").is_file())

    def test_non_pinned_checkout_is_blocked_before_output(self):
        out = Path(self.temp.name) / "release"
        with self.assertRaisesRegex(ValueError, "differs from pinned"):
            stage_candidate(self.root, out, "ASHDOD", "0" * 40)
        self.assertFalse(out.exists())

    def test_inconsistent_retrieval_timestamp_blocked(self):
        self.prices["retrieved_at"] = "2026-11-10T09:00:00+02:00"
        self.rewrite("prices", self.prices)
        self.commit()
        with self.assertRaisesRegex(ValueError, "retrieved_at"):
            inspect_city(self.root, "ASHDOD", self.sha)

    def test_inconsistent_price_branch_ids_blocked(self):
        self.prices["branches"][1]["id"] = "wrong"
        self.rewrite("prices", self.prices)
        self.commit()
        with self.assertRaisesRegex(ValueError, "identities"):
            inspect_city(self.root, "ASHDOD", self.sha)

    def test_future_source_time_blocked(self):
        self.refresh["checked_at"] = "2030-01-01T12:00:00+02:00"
        self.rewrite("refresh-status", self.refresh)
        self.commit()
        with self.assertRaisesRegex(ValueError, "Future-dated"):
            inspect_city(self.root, "ASHDOD", self.sha, now=datetime(2026, 11, 11, tzinfo=timezone.utc))

    def test_tlv_cannot_be_mislabeled_complete(self):
        with self.assertRaisesRegex(ValueError, "not eligible"):
            inspect_city(self.root, "TLV", self.sha)

    def test_tlv_placeholder_report_remains_fail_closed(self):
        tlv = self.root / "SUPER.TLV"
        (tlv / "data").mkdir(parents=True)
        (tlv / "index.html").write_text(
            '<html><meta http-equiv="refresh" content="0;url=https://tlvnet.com/super/">'
            '<p>אינה זמינה כרגע</p></html>', encoding="utf-8")
        status = dict(self.refresh, branch_count=2, updated_count=0,
                      branches=[{"branch_id": "store-1", "status": "retained_previous"},
                                {"branch_id": "store-2", "status": "retained_previous"}])
        (tlv / "data" / "refresh-status.json").write_text(json.dumps(status), encoding="utf-8")
        self.commit()
        r = tlv_blocker(self.root, self.sha)
        self.assertTrue(r["site_placeholder"])
        self.assertFalse(r["full_private_candidate"])
        self.assertFalse(r["public_cutover"])
        self.assertEqual(r["updated_count"], 0)


if __name__ == "__main__":
    unittest.main()
