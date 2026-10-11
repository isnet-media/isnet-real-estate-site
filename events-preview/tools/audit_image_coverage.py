#!/usr/bin/env python3
"""Audit event illustration coverage against the CMS taxonomy. Read-only."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
taxonomy_path = root / "events-preview/admin/data/taxonomy.json"
images = root / "events-preview/shared/images/defaults"
taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
report = {"categories": [], "missing_subcategories": [], "missing_primary": []}
for category in taxonomy["primary_categories"]:
    cat = category["id"]
    primary = images / f"category-{cat}.svg"
    if not primary.is_file():
        report["missing_primary"].append(cat)
    subs = []
    for sub in category.get("subcategories", []):
        path = images / f"{cat}-{sub['id']}.svg"
        found = path.is_file()
        subs.append({"id": sub["id"], "label": sub.get("label"), "exists": found, "file": str(path.relative_to(root))})
        if not found:
            report["missing_subcategories"].append({"category": cat, "subcategory": sub["id"], "label": sub.get("label")})
    report["categories"].append({"id": cat, "primary_exists": primary.is_file(), "subcategories": subs})
report["summary"] = {
    "primary_total": len(report["categories"]),
    "primary_missing": len(report["missing_primary"]),
    "subcategory_total": sum(len(c["subcategories"]) for c in report["categories"]),
    "subcategory_missing": len(report["missing_subcategories"]),
}
print(json.dumps(report, ensure_ascii=False, indent=2))
