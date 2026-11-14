"""Fail-closed unit tests for private committed-delta canary."""
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from stage_super_committed_delta import validate_delta, CITIES

def payloads():
    old={"checked_at":"2026-11-10T10:00:00+02:00","branch_count":2,
         "updated_count":2,"all_sources_updated":True,
         "branches":[{"status":"updated"},{"status":"updated"}]}
    new={"checked_at":"2026-11-11T12:00:00+02:00","branch_count":2,
         "updated_count":1,"all_sources_updated":False,
         "branches":[{"status":"updated"},{"status":"retained_previous"}],
         "coverage_status":"partial"}
    def dump(x):return json.dumps(x).encode()
    blobs={
        "data/refresh-status.json":dump(new),
        "data/prices.json":dump({"branch_count":2,"coverage_complete":False,"retrieved_at":new["checked_at"]}),
        "data/source-status.json":dump({"updated_at":"2026-11-11"})}
    return old,blobs

class CanaryGuards(unittest.TestCase):
    def run_case(self,mutate=lambda old,files:None, fail=False):
        old,files=payloads()
        mutate(old,files)
        baseline={k:b"{}" for k in files}
        baseline["data/refresh-status.json"]=json.dumps(old).encode()
        with patch("stage_super_committed_delta.blob",side_effect=lambda ref,city,name: baseline[name] if ref=="5958cfaca9a61eacfdb1aa216635c3d3ff810850" else files[name]):
            if fail:
                with self.assertRaises(ValueError):validate_delta("YAVNE","a"*40,now=datetime(2026,11,11,13,tzinfo=timezone.utc))
            else:
                entries,status=validate_delta("YAVNE","a"*40,now=datetime(2026,11,11,13,tzinfo=timezone.utc))
                self.assertEqual(len(entries),3)
                self.assertEqual(status["updated_count"],1)
    def test_partial_explicitly_acceptable_for_private_only(self):self.run_case()
    def test_source_timestamp_regression_rejected(self):
        def edit(old,files):
            old["checked_at"]="2026-11-12T10:00:00+02:00"
        self.run_case(edit,fail=True)
    def test_wrong_price_timestamp_rejected(self):
        def edit(old,files):
            p=json.loads(files["data/prices.json"])
            p["retrieved_at"]="2026-11-10T10:00:00+02:00"
            files["data/prices.json"]=json.dumps(p).encode()
        self.run_case(edit,fail=True)
    def test_wrong_price_branch_count_rejected(self):
        def edit(old,files):
            p=json.loads(files["data/prices.json"])
            p["branch_count"]=99
            files["data/prices.json"]=json.dumps(p).encode()
        self.run_case(edit,fail=True)
    def test_wrong_coverage_flag_rejected(self):
        def edit(old,files):
            p=json.loads(files["data/prices.json"])
            p["coverage_complete"]=True
            files["data/prices.json"]=json.dumps(p).encode()
        self.run_case(edit,fail=True)
    def test_unapproved_city_rejected(self):
        self.assertNotIn("TLV",CITIES)
        with self.assertRaises(ValueError):
            validate_delta("TLV","a"*40)
    def test_future_timestamp_rejected(self):
        def edit(old,files):
            v=json.loads(files["data/refresh-status.json"]);v["checked_at"]="2026-11-13T12:00:00+02:00"
            files["data/refresh-status.json"]=json.dumps(v).encode()
        self.run_case(edit,fail=True)

if __name__=="__main__":unittest.main()
