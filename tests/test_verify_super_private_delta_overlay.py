"""Offline fail-closed checks for the private price-data overlay gate."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_super_private_delta_overlay import (
    CITIES, COMMIT, PINNED, REQUIRED, check_delta_manifest,
    digest, require_checksum, manifest_files,
)

class OverlayManifestSafetyTests(unittest.TestCase):
    def manifest(self, city="YAVNE"):
        return {
            "format": "isnet-super-committed-private-delta-v1",
            "city": city, "source_commit": COMMIT,
            "baseline_release": PINNED[city], "private": True,
            "public_cutover": False, "approved_for_public": False,
            "collector_invoked": False,
            "files": [{"path": rel, "bytes": 3, "sha256": digest(b"abc")} for rel in REQUIRED],
        }

    def test_six_city_allowlist_and_exact_inventory(self):
        for city in CITIES:
            self.assertEqual(set(check_delta_manifest(self.manifest(city), city)), set(REQUIRED))

    def test_block_any_public_approval(self):
        for key in ("public_cutover", "approved_for_public", "collector_invoked"):
            document=self.manifest()
            document[key]=True
            with self.assertRaises(ValueError): check_delta_manifest(document, "YAVNE")

    def test_block_mismatched_commit_and_release(self):
        for key,value in (("source_commit","0"*40), ("baseline_release","0"*40)):
            document=self.manifest()
            document[key]=value
            with self.assertRaises(ValueError): check_delta_manifest(document,"YAVNE")

    def test_block_tlv_and_unknown_city(self):
        with self.assertRaises(ValueError):
            check_delta_manifest(self.manifest(), "TLV")
        with self.assertRaises(ValueError):
            check_delta_manifest(self.manifest(), "UNKNOWN")

    def test_block_missing_and_duplicate_critical_files(self):
        doc=self.manifest()
        doc["files"]=doc["files"][:2]
        with self.assertRaises(ValueError): check_delta_manifest(doc, "YAVNE")
        doc=self.manifest()
        doc["files"].append(doc["files"][0].copy())
        with self.assertRaises(ValueError): manifest_files(doc)

    def test_block_corrupted_bytes_or_hash(self):
        item={"bytes":3,"sha256":digest(b"abc")}
        require_checksum(item,b"abc","example.json")
        for corrupt in ({"bytes": 4, "sha256": digest(b"abc")},
                        {"bytes": 3, "sha256": "a"*64}):
            with self.assertRaises(ValueError):
                require_checksum(corrupt,b"abc","example.json")

if __name__ == "__main__":
    unittest.main()
