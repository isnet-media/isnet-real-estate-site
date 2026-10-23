"""Regression tests: never lose an Ashdod performance through a URL/title collision."""
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mevalim_sync", ROOT / "scripts/sync_mevalim_ashdod_direct.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

def event(identifier, title="Sample show", date="2026-12-09", time="20:30",
          venue="בית יד לבנים אשדוד", ticket="https://tickets.mevalim.co.il/event/abc"):
    return {"event_id": identifier, "title": title, "start_date": date,
            "start_time": time, "venue": venue, "ticket_url": ticket}

class SafeMergeTests(unittest.TestCase):
    def merged(self, existing, incoming):
        dataset = {"events": copy.deepcopy(existing), "stats": {}}
        removed = sync.merge(dataset, copy.deepcopy(incoming))
        return dataset, removed

    def test_same_direct_source_id_replaced_once(self):
        old = event("mevalim_as_1", venue="Old venue")
        new = event("mevalim_as_1", venue="Official venue")
        data, removed = self.merged([old], [new])
        self.assertEqual([x["event_id"] for x in removed], ["mevalim_as_1"])
        self.assertEqual(len(data["events"]), 1)
        self.assertEqual(data["events"][0]["venue"], "Official venue")

    def test_shared_ticket_url_different_showtime_is_preserved(self):
        # Observed on 23 Oct: an 18:30 event disappeared when a 20:30 event
        # was ingested with the same purchase URL.
        original = event("board_18_30", "גברת רביע - טיפול זוגי 5:55", "2026-10-25", "18:30")
        incoming = event("mevalim_as_20_30", "גברת רביע - טיפול זוגי 5:55", "2026-10-25", "20:30")
        data, removed = self.merged([original], [incoming])
        self.assertEqual(removed, [])
        self.assertEqual(len(data["events"]), 2)
        self.assertIn("board_18_30", [e["event_id"] for e in data["events"]])

    def test_same_title_date_and_time_different_venues_preserved(self):
        old = event("local_1", venue="אולם דיונה אשדוד")
        fresh = event("mevalim_as_2", venue="בית יד לבנים אשדוד")
        data, removed = self.merged([old], [fresh])
        self.assertEqual(removed, [])
        self.assertEqual(len(data["events"]), 2)

    def test_generic_title_does_not_erase_show(self):
        old = event("board_bad_listing", title="מבלים")
        fresh = event("mevalim_as_2", title="Sample show")
        data, removed = self.merged([old], [fresh])
        self.assertEqual(removed, [])
        self.assertEqual(len(data["events"]), 2)

    def test_matching_title_date_time_and_venue_deduplicates_cross_source(self):
        old = event("board_1", title="Sample show", venue="בית יד לבנים, אשדוד")
        fresh = event("mevalim_as_1", title="Sample show", venue="בית יד לבנים אשדוד")
        data, removed = self.merged([old], [fresh])
        self.assertEqual([x["event_id"] for x in removed], ["board_1"])
        self.assertEqual(len(data["events"]), 1)
        self.assertEqual(data["stats"]["events"], 1)

    def test_similar_titles_do_not_get_removed_by_substring(self):
        old = event("local_1", title="Sample show - Part 2")
        fresh = event("mevalim_as_2", title="Sample show")
        data, removed = self.merged([old], [fresh])
        self.assertEqual(removed, [])
        self.assertEqual(len(data["events"]), 2)

if __name__ == "__main__":
    unittest.main()
