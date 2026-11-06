"""Build Tel Aviv supermarket pages from verified TLV-only official-feed data.

This module intentionally refuses to manufacture a city from another city's
prices. The shared builders, assets and monthly family basket remain canonical.
"""
from pathlib import Path
import json
import re
from super_city_runtime import ROOT, load

SITE = ROOT / "SUPER.TLV"
REGISTRY = ROOT / "scripts/super-tlv/branch-registry.json"

def build():
    if not REGISTRY.exists():
        raise RuntimeError("TLV official branch registry is missing; cannot publish another city's prices")
    reviewed = json.loads(REGISTRY.read_text(encoding="utf-8"))["branches"]
    if not reviewed:
        raise RuntimeError("No officially verified Tel Aviv branches; publication blocked")
    data = SITE / "data"
    catalog_path = data / "catalog.json"
    if not catalog_path.exists():
        raise RuntimeError("TLV official collection missing; cannot generate comparisons")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("city") != "תל אביב":
        raise RuntimeError("Wrong supermarket city")
    by_id = {b["id"] for b in reviewed}
    if len(by_id) != len(reviewed):
        raise RuntimeError("Duplicate branch registration")
    if {b["id"] for b in catalog.get("branches", [])} != by_id:
        raise RuntimeError("Collected TLV branches differ from verified registry")
    if any(b.get("city") != "תל אביב" for b in catalog["branches"]):
        raise RuntimeError("Cross-city price contamination")
    if not list((data / "offers").glob("*.json")):
        raise RuntimeError("No TLV price offers; cannot publish empty comparison")

    basket = load("build_super_city_basket", "TLV")
    variants = {}
    for name, definition in (("family", "city-family-basket.json"), ("basic", "city-basket-products.json")):
        spec = json.loads((ROOT / "scripts/super-tlv" / definition).read_text(encoding="utf-8"))
        variants[name] = basket.build_variant(spec, catalog, name)
    variants["monthly"] = basket.build_monthly_variant(catalog)
    (data / "city-basket.json").write_text(
        json.dumps({"schema_version": 1, "default_variant": "monthly", "variants": variants},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    load("build_super_smart_shopping", "TLV").build()

    shell = load("super_ashdod_shell", "TLV")
    for page in shell.pages():
        original = page.read_text(encoding="utf-8")
        updated = shell.decorate(original, page)
        updated = re.sub(
            r'<script\b[^>]*src="[^"]*assets/ashdod-analytics\.js[^"]*"[^>]*>\s*</script>',
            "", updated)
        if updated != original:
            page.write_text(updated, encoding="utf-8")

if __name__ == "__main__":
    build()
