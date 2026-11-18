import json
import tempfile
import unittest
from pathlib import Path
from scripts.optimize_public_price_json import optimize

class PriceJsonTests(unittest.TestCase):
    def test_roundtrip_and_no_source_modification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"site"
            file=root/"SUPER.TLV"/"data"/"offers"/"00.json"
            file.parent.mkdir(parents=True)
            data={"כותרת":"מוצר","items":[{"price":2.5,"store":"תל אביב"}]}
            source=json.dumps(data,indent=4,ensure_ascii=False).encode()
            file.write_bytes(source)
            other=root/"events-preview"/"ashdod"/"data"/"events.json"
            other.parent.mkdir(parents=True)
            other.write_bytes(source)
            stats=optimize(root)
            self.assertEqual(stats["files_examined"],1)
            self.assertEqual(stats["files_optimized"],1)
            self.assertGreater(stats["saved_bytes"],0)
            self.assertEqual(json.loads(file.read_bytes()),data)
            self.assertEqual(other.read_bytes(),source)
            self.assertEqual(optimize(root)["saved_bytes"],0)
    def test_invalid_json_is_not_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            file=root/"SUPER.ASHDOD"/"data"/"catalog.json"
            file.parent.mkdir(parents=True)
            file.write_text("{oops")
            outcome=optimize(root)
            self.assertEqual(file.read_text(),"{oops")
            self.assertEqual(len(outcome["invalid_json_preserved"]),1)

if __name__=="__main__":unittest.main()
