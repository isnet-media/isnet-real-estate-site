"""Create an immutable, independently testable supermarket city release bundle.

This deliberately DOES NOT collect prices, publish DNS, rewrite links, or remove
legacy paths. Each city is released as a separate artifact for migration testing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

CITIES = ("ASHDOD", "YAVNE", "KGAT", "RISHON", "HOLON", "BATYAM", "TLV")
REQUIRED = ("data/catalog.json", "data/prices.json", "data/refresh-status.json")
# Shared repo-owned JavaScript explicitly referenced by /SUPER.YAVNE/*.html as
# /assets/yavne-analytics.js. Keep the canonical /SUPER.YAVNE/ route intact.
# Do NOT automatically bundle third-party images, fonts or unreviewed assets.
ROOT_SCRIPT_DEPENDENCIES = {"YAVNE": ("assets/yavne-analytics.js",)}

def stage_city(root: Path, output: Path, city: str):
    if city not in CITIES:
        raise ValueError("Unknown city. No implicit city registration")
    root, output = root.resolve(), output.resolve()
    source = root / ("SUPER." + city)
    destination = output / ("SUPER." + city)
    if not source.is_dir() or root == output or root in output.parents:
        raise ValueError("Invalid source or destination")
    if output.exists():
        raise ValueError("Refusing to overwrite existing artifact directory")
    if any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("Symlinks are not permitted")
    for name in REQUIRED:
        p = source / name
        if not p.is_file():
            raise ValueError("Missing required data: " + name)
        with p.open(encoding="utf-8") as handle:
            json.load(handle)  # validation only; original bytes preserved
    dependencies = ROOT_SCRIPT_DEPENDENCIES.get(city, ())
    for rel in dependencies:
        shared = root / rel
        if not shared.is_file() or shared.is_symlink() or shared.parent.is_symlink():
            raise ValueError("Missing or unsafe first-party script dependency: " + rel)
    output.mkdir(parents=True)
    shutil.copytree(source, destination)
    # Only in the disposable release artifact, never in the source tree.
    # The archive root must be served with /SUPER.YAVNE/ and /assets/ paths.
    for rel in dependencies:
        target = output / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise ValueError("Refusing to overwrite a staged first-party dependency")
        shutil.copyfile(root / rel, target)
    manifest = []
    for path in sorted(output.rglob("*")):
        if not path.is_file():
            continue
        data = path.read_bytes()
        rel = path.relative_to(output).as_posix()
        source_path = root / rel
        if hashlib.sha256(data).digest() != hashlib.sha256(source_path.read_bytes()).digest():
            raise AssertionError("Copy mismatch for " + rel)
        manifest.append({"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    report = {
        "city": city,
        "file_count": len(manifest),
        "payload_bytes": sum(x["bytes"] for x in manifest),
        "price_data_preserved": True,
        "first_party_root_scripts": list(dependencies),
        "required_site_prefix": "/SUPER.YAVNE/" if city == "YAVNE" else None,
        "asset_rights_and_browser_acceptance_unverified": True,
        "standalone_artifact_not_production_deployment": True,
        "files": manifest,
    }
    (output / "release-manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--city", choices=CITIES, required=True)
    p.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = stage_city(a.source, a.output, a.city)
    print(json.dumps({k:v for k,v in result.items() if k!="files"}, ensure_ascii=False))
