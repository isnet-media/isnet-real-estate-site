#!/usr/bin/env python3
"""Read-only Meta Graph API connection test for TLVNET.

Secrets are supplied via environment variables only. Never print access tokens.
No publishing or paid actions occur in this script.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PAGE_ID = "61596358055015"
GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v26.0")
BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

def api_get(path, token, params=None):
    qs = urllib.parse.urlencode(params or {})
    url = f"{BASE}/{path}" + (f"?{qs}" if qs else "")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            payload = json.load(exc)
            code = payload.get("error", {}).get("code")
            typ = payload.get("error", {}).get("type")
            message = payload.get("error", {}).get("message", "Unknown API error")
            print(f"Meta API error HTTP={exc.code} code={code} type={typ}: {message}", file=sys.stderr)
        except (ValueError, KeyError):
            print(f"Meta API HTTP {exc.code}", file=sys.stderr)
        raise SystemExit(2)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"Meta network error: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(3)

def main():
    token = os.getenv("META_PAGE_ACCESS_TOKEN")
    if not token:
        print("BLOCKED: META_PAGE_ACCESS_TOKEN secret is missing.")
        return 4
    page = api_get(PAGE_ID, token, {"fields": "id,name,instagram_business_account{id,username}"})
    if str(page.get("id")) != PAGE_ID:
        print("BLOCKED: token did not identify the approved TLVNET Facebook Page.")
        return 5
    print(f"Facebook Page confirmed: {page.get('name')} ({PAGE_ID})")
    ig = page.get("instagram_business_account") or {}
    if not ig.get("id"):
        print("BLOCKED: no linked Instagram professional account returned (or missing permissions).")
        return 6
    if ig.get("username", "").lower() != "tlvnet":
        print(f"BLOCKED: linked Instagram username mismatch: {ig.get('username', '(unknown)')}")
        return 7
    print(f"Instagram confirmed: @{ig['username']} (ID {ig['id']})")
    print("READ-ONLY CONNECTION CHECK PASSED.")
    print("Note: This verifies account visibility, NOT publishing permission or autonomous delivery.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
