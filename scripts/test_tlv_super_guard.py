"""Safety regression checks for Tel Aviv before its first official price load."""
from pathlib import Path
import json
import sys
from super_city_runtime import ROOT, load

site = ROOT / "SUPER.TLV"
registry = ROOT / "scripts/super-tlv/branch-registry.json"
assert site.is_dir()
assert "TLV" in __import__("super_daily_run").CITIES
assert load("refresh_super_prices", "TLV").D == site / "data"
assert load("build_super_city_basket", "TLV").D == site
assert load("build_super_smart_shopping", "TLV").DATA == site / "data"
assert load("super_ashdod_shell", "TLV").SITE == site

if registry.exists():
    branches = json.loads(registry.read_text(encoding="utf-8")).get("branches", [])
    ids = [b["id"] for b in branches]
    assert len(ids) == len(set(ids))
    assert all(b.get("city") == "תל אביב" and b.get("chain_id") and b.get("store_id")
               and b.get("identity_source") and b.get("source_url") for b in branches)
else:
    assert not (site / "data/catalog.json").exists(), (
        "Tel Aviv prices exist without a reviewed local branch registry"
    )
print("TLV is isolated; no cross-city data or unverified branch registration")
