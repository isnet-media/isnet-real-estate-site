import json
import tempfile
import unittest
from pathlib import Path
from scripts.stage_super_city_release import stage_city

class StageSuperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.src = self.root / "SUPER.ASHDOD"
        (self.src / "data").mkdir(parents=True)
        for name in ("catalog","prices","refresh-status"):
            (self.src/"data"/(name+".json")).write_text('{"date":"2026-11-10", "value": 1}',encoding="utf-8")
        (self.src/"index.html").write_text("<h1>חנות</h1>",encoding="utf-8")
    def test_byte_identical_city_release(self):
        out = Path(self.temp.name)/"out"
        result = stage_city(self.root,out,"ASHDOD")
        self.assertEqual(result["file_count"],4)
        self.assertEqual((out/"SUPER.ASHDOD/data/prices.json").read_bytes(),(self.src/"data/prices.json").read_bytes())
        self.assertTrue(json.loads((out/"release-manifest.json").read_text())["price_data_preserved"])
        self.assertFalse((self.root/"release-manifest.json").exists())
    def _make_yavne(self):
        src = self.root / "SUPER.YAVNE"
        (src / "data").mkdir(parents=True)
        for name in ("catalog", "prices", "refresh-status"):
            (src / "data" / (name + ".json")).write_text('{"date":"2026-11-10"}', encoding="utf-8")
        (src / "index.html").write_text(
            '<script src="/assets/yavne-analytics.js?v=20261022-1"></script>', encoding="utf-8"
        )
        return src

    def test_yavne_first_party_root_analytics_pinned_and_byte_identical(self):
        src = self._make_yavne()
        shared = self.root / "assets" / "yavne-analytics.js"
        shared.parent.mkdir()
        raw = b'/* first party only */ window.yavneAnalytics = true;'
        shared.write_bytes(raw)
        out = Path(self.temp.name) / "out"
        report = stage_city(self.root, out, "YAVNE")
        self.assertEqual((out / "assets" / "yavne-analytics.js").read_bytes(), raw)
        self.assertIn("assets/yavne-analytics.js", report["first_party_root_scripts"])
        self.assertEqual(report["required_site_prefix"], "/SUPER.YAVNE/")
        entry = next(x for x in report["files"] if x["path"] == "assets/yavne-analytics.js")
        self.assertEqual(entry["sha256"], __import__("hashlib").sha256(raw).hexdigest())
        self.assertEqual(report["file_count"], 5)
        self.assertFalse((src / "assets" / "yavne-analytics.js").exists())
        self.assertIn(b'/assets/yavne-analytics.js', (out/"SUPER.YAVNE/index.html").read_bytes())

    def test_yavne_missing_shared_analytics_fails_closed(self):
        self._make_yavne()
        with self.assertRaisesRegex(ValueError, "first-party script dependency"):
            stage_city(self.root, Path(self.temp.name) / "out", "YAVNE")

    def test_yavne_analytics_symlink_rejected(self):
        self._make_yavne()
        p = self.root / "assets" / "yavne-analytics.js"
        p.parent.mkdir()
        p.symlink_to(self.src / "index.html")
        with self.assertRaisesRegex(ValueError, "unsafe"):
            stage_city(self.root, Path(self.temp.name) / "out", "YAVNE")

    def test_unknown_city_rejected(self):
        with self.assertRaises(ValueError):
            stage_city(self.root,Path(self.temp.name)/"out","HAIFA")
    def test_incomplete_source_rejected(self):
        (self.src/"data/catalog.json").unlink()
        with self.assertRaises(ValueError):
            stage_city(self.root,Path(self.temp.name)/"out","ASHDOD")
    def test_output_inside_checkout_rejected(self):
        with self.assertRaises(ValueError):
            stage_city(self.root,self.root/"output","ASHDOD")

if __name__=="__main__":
    unittest.main()
