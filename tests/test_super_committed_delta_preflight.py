"""Regression gates for read-only supermarket committed-data preflight."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from super_committed_delta_preflight import evaluate, validate_status

NOW = datetime(2026,11,11,9,0,tzinfo=timezone.utc)

def report(ts="2026-11-10T09:00:00+02:00",updated=1,total=2):
    return {
        "checked_at":ts, "updated_count":updated, "branch_count":total,
        "all_sources_updated": updated==total,
        "branches":[{"status":"updated" if i<updated else "retained_previous"} for i in range(total)]
    }

class PreflightTests(unittest.TestCase):
    def test_no_change(self):
        a=report()
        self.assertEqual(evaluate(a,a,[],NOW)[0],"unchanged")
    def test_data_with_new_timestamp_must_still_be_reviewed(self):
        a=report()
        b=report("2026-11-11T08:00:00+02:00",2,2)
        self.assertEqual(evaluate(a,b,["data/prices.json"],NOW)[0],"private_candidate_review")
    def test_same_timestamp_price_mutation_fails_closed(self):
        a=report()
        self.assertEqual(evaluate(a,a,["data/prices.json"],NOW)[0],"blocked")
    def test_regressed_timestamp_fails(self):
        a=report()
        b=report("2026-11-09T09:00:00+02:00")
        self.assertEqual(evaluate(a,b,["index.html"],NOW)[0],"blocked")
    def test_future_date_fails(self):
        a=report()
        b=report("2026-11-12T09:00:00+02:00")
        self.assertEqual(evaluate(a,b,["index.html"],NOW)[0],"blocked")
    def test_inconsistent_branch_counts_fail(self):
        a=report()
        a["updated_count"]=2
        with self.assertRaises(ValueError):
            validate_status(a)
    def test_missing_timezone_fails(self):
        a=report("2026-11-10T09:00:00")
        with self.assertRaises(ValueError):
            validate_status(a)
    def test_partial_status_not_mislabeled(self):
        a=report()
        b=report("2026-11-11T08:00:00+02:00")
        self.assertEqual(evaluate(a,b,["data/refresh-status.json"],NOW)[0],"private_candidate_review")

if __name__=="__main__":
    unittest.main()
