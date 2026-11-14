import tempfile
import unittest
from pathlib import Path
from scripts.audit_public_payload import inventory

class PublicPayloadAuditTests(unittest.TestCase):
    def test_counts_without_mutating(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / "index.html").write_bytes(b"abcd")
            (root / "assets").mkdir()
            (root / "assets" / "image.jpg").write_bytes(b"abcdef")
            before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            result = inventory(root)
            self.assertEqual(result["total_bytes"], 10)
            self.assertEqual(result["file_count"], 2)
            self.assertEqual(result["top_level"][0]["path"], "assets")
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()})
    def test_missing_directory_fails(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                inventory(Path(t) / "missing")

if __name__ == "__main__":
    unittest.main()
