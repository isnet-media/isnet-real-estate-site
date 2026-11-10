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
