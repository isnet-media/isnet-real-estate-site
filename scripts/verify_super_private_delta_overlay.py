"""Read-only rehearsal: verify committed data delta overlay and restore for six cities.

This DOES NOT publish a site, execute price collectors, copy licensed media,
write to Supabase or change the live Pages deployment. This is a private
three-file data rollback rehearsal, NOT a production reverse-proxy rollback.
"""
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from super_committed_delta_preflight import PINNED, REQUIRED, validate_status

PROJECT = "qomkxhafrprooekwgsxf"
BUCKET = "isnet-super-staging"
COMMIT = "8133619b2d37ba514c0a801cb0b998a9b69bd631"
CITIES = ("ASHDOD", "BATYAM", "HOLON", "KGAT", "RISHON", "YAVNE")
BASE = f"https://{PROJECT}.supabase.co/storage/v1/object/"
LIMIT = 256 * 1024

def digest(data):
    return hashlib.sha256(data).hexdigest()

def git_bytes(ref, city, rel):
    return subprocess.check_output(["git", "show", f"{ref}:SUPER.{city}/{rel}"])

def read_private(object_path, key):
    # Explicit fixed bucket and versioned allowlisted paths; no public credentials.
    url = BASE + "authenticated/" + quote(BUCKET + "/" + object_path, safe="/")
    request = Request(url, headers={"apikey": key, "Authorization": "Bearer " + key})
    with urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise ValueError("Private object read failed")
        data = response.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("Storage object unexpectedly large")
    return data

def check_public_denied(object_path):
    url = BASE + "public/" + quote(BUCKET + "/" + object_path, safe="/")
    try:
        with urlopen(Request(url), timeout=20) as response:
            # A publicly-readable object in our private bucket blocks promotion.
            raise ValueError("Private storage object became publicly readable: " + str(response.status))
    except HTTPError as exc:
        if exc.code not in (400, 401, 403, 404):
            raise ValueError("Anonymous storage probe returned unexpected status: " + str(exc.code))

def manifest_files(m):
    entries = m.get("files")
    if not isinstance(entries, list) or len(entries) < 3:
        raise ValueError("Missing manifest file inventory")
    paths = [f.get("path") for f in entries if isinstance(f, dict)]
    if len(paths) != len(entries) or len(paths) != len(set(paths)):
        raise ValueError("Duplicate/invalid manifest paths")
    return {f["path"]: f for f in entries}

def require_checksum(item, payload, path):
    if (type(item.get("bytes")) is not int or item["bytes"] != len(payload)
        or not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64
        or item["sha256"] != digest(payload)):
        raise ValueError("Manifest SHA256/size mismatch: " + path)

def check_delta_manifest(manifest, city):
    if city not in CITIES:
        raise ValueError("City is not approved for delta rehearsal")
    expected = {
        "format": "isnet-super-committed-private-delta-v1",
        "city": city,
        "source_commit": COMMIT,
        "baseline_release": PINNED[city],
        "private": True,
        "public_cutover": False,
        "approved_for_public": False,
        "collector_invoked": False,
    }
    for name, value in expected.items():
        if manifest.get(name) != value or (isinstance(value, bool) and type(manifest[name]) is not bool):
            raise ValueError("Unsafe/mismatched delta manifest field: " + name)
    inventory = manifest_files(manifest)
    if set(inventory) != set(REQUIRED):
        raise ValueError("Unexpected or missing delta files")
    return inventory

def check_coverage(manifest, data):
    refresh = json.loads(data["data/refresh-status.json"])
    prices = json.loads(data["data/prices.json"])
    status = json.loads(data["data/source-status.json"])
    checked = validate_status(refresh)
    if (checked > datetime.now(timezone.utc) + timedelta(minutes=5)
        or refresh["checked_at"] != manifest["source_checked_at"]
        or refresh["updated_count"] != manifest["updated_branches"]
        or refresh["branch_count"] != manifest["total_branches"]
        or refresh.get("coverage_status") != manifest.get("coverage_status")
        or refresh["all_sources_updated"] is not manifest["all_sources_updated"]
        or prices.get("branch_count") != refresh["branch_count"]
        or prices.get("coverage_complete") is not refresh["all_sources_updated"]
        or prices.get("retrieved_at") != refresh["checked_at"]
        or status.get("updated_at") != checked.astimezone(ZoneInfo("Asia/Jerusalem")).date().isoformat()):
        raise ValueError("Inconsistent price coverage/provenance; block overlay")
    return refresh

def rehearse(city, key):
    release = PINNED[city]
    root = f"releases/{city}/{release}/"
    delta = f"previews/committed-deltas/{city}/{COMMIT}/"
    base_manifest = json.loads(read_private(root + "release-manifest.json", key))
    delta_manifest = json.loads(read_private(delta + "delta-manifest.json", key))
    if (base_manifest.get("city") != city or base_manifest.get("release") != release
        or base_manifest.get("private") is not True or base_manifest.get("public_cutover") is not False):
        raise ValueError("Untrusted baseline manifest")
    old_entries = manifest_files(base_manifest)
    new_entries = check_delta_manifest(delta_manifest, city)
    originals, replacements = {}, {}
    for rel in REQUIRED:
        source_path = f"SUPER.{city}/{rel}"
        if source_path not in old_entries:
            raise ValueError("Baseline manifest lacks critical file")
        old = read_private(root + source_path, key)
        new = read_private(delta + rel, key)
        require_checksum(old_entries[source_path], old, source_path)
        require_checksum(new_entries[rel], new, rel)
        if old != git_bytes(release, city, rel) or new != git_bytes(COMMIT, city, rel):
            raise ValueError("Storage object differs from pinned Git history")
        if new == old:
            raise ValueError("Delta must not masquerade as unchanged data")
        originals[rel], replacements[rel] = old, new
    refresh = check_coverage(delta_manifest, replacements)
    check_public_denied(delta + "data/prices.json")
    # Disk-only rehearsal. We deliberately never modify remote storage or live files.
    with tempfile.TemporaryDirectory(prefix="isnet-super-overlay-") as temporary:
        base = Path(temporary)
        for rel, old in originals.items():
            target = base / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(old)
        for rel, new in replacements.items():
            target = base / rel
            temporary_file = target.with_suffix(target.suffix + ".candidate")
            temporary_file.write_bytes(new)
            temporary_file.replace(target)
            if digest(target.read_bytes()) != digest(new):
                raise ValueError("Simulated overlay readback mismatch")
        # Rehearse rollback of each critical file, preserving its original checksum.
        for rel, old in originals.items():
            target = base / rel
            target.write_bytes(old)
            if digest(target.read_bytes()) != digest(old):
                raise ValueError("Simulated rollback readback mismatch")
    return {
        "city": city, "source_commit": COMMIT,
        "updated_branches": refresh["updated_count"],
        "total_branches": refresh["branch_count"],
        "source_checked_at": refresh["checked_at"],
        "delta_files_verified": len(REQUIRED),
        "data_only_overlay_rehearsal": "passed",
        "data_only_rollback_rehearsal": "passed",
        "anonymous_storage_access": "denied",
        "production_cutover": False,
    }

def main():
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if os.getenv("SUPABASE_URL", "").rstrip("/") != f"https://{PROJECT}.supabase.co" or not key:
        raise RuntimeError("Missing credentials for expected private Supabase project")
    report = [rehearse(city, key) for city in CITIES]
    print(json.dumps({"success": True, "verified": len(report), "cities": report,
                      "storage_mutations": 0, "collector_runs": 0,
                      "public_cutover": False,
                      "real_production_rollback_proven": False}, ensure_ascii=False))

if __name__ == "__main__":
    main()
