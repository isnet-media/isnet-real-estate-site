"""Read-only, offline asset and link readiness inventory for seven pinned SUPER.* sites.

No network, prices, collectors, hosting or storage writes. This is NOT a browser test
or permission/license verification; publication remains blocked until separately proven.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
from urllib.parse import unquote, urlsplit

CITIES = ("ASHDOD", "BATYAM", "HOLON", "KGAT", "RISHON", "TLV", "YAVNE")
REQUIRED = ("index.html", "compare/index.html", "deals/index.html",
            "recipes/index.html", "smart-shopping/index.html")
STATIC_EXT = {".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".svg",
              ".gif", ".ico", ".woff", ".woff2", ".ttf", ".otf"}
MEDIA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".ico"}
FONT_EXT = {".woff", ".woff2", ".ttf", ".otf"}
CSS_URL = re.compile(r"url\(\s*['\"]?([^'\")]+)", re.I)
REDIRECT = re.compile(r'<meta\\b[^>]*http-equiv\\s*=\\s*["\\\']?refresh', re.I)

class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.resources = []
        self.navigation = []
        self.canonicals = []
        self._style = False
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "style":
            self._style = True
        for prop in ("src", "poster", "data-src"):
            if data.get(prop) and tag in ("script","img","source","video","audio","iframe"):
                self.resources.append(data[prop])
        if tag == "link" and data.get("href"):
            rel=set((data.get("rel") or "").lower().split())
            if rel.intersection({"stylesheet","icon","preload","prefetch","modulepreload"}):
                self.resources.append(data["href"])
            if "canonical" in rel:
                self.canonicals.append(data["href"])
        if tag == "a" and data.get("href"):
            self.navigation.append(data["href"])
        if data.get("srcset"):
            self.resources.extend(p.strip().split()[0] for p in data["srcset"].split(",") if p.strip())
        if data.get("style"):
            self.resources.extend(CSS_URL.findall(data["style"]))
    def handle_endtag(self, tag):
        if tag == "style":
            self._style = False
    def handle_data(self, text):
        if self._style:
            self.resources.extend(CSS_URL.findall(text))

def classify_url(site, origin, raw):
    raw = raw.strip()
    if not raw or raw.startswith(("#", "data:", "blob:", "javascript:", "mailto:", "tel:")):
        return "ignored", None
    if raw.startswith("//"):
        return "external", raw
    parsed = urlsplit(raw)
    if parsed.scheme:
        return "external", raw
    path = unquote(parsed.path).replace("\\", "/")
    if not path:
        return "ignored", None
    if path.startswith("/"):
        segments = path.lstrip("/").split("/")
        if segments[0] == "SUPER." + site:
            path = "/".join(segments[1:])
        else:
            return "origin_route_unverified", raw
    else:
        path = posixpath.join(posixpath.dirname(origin), path)
    normal = posixpath.normpath(path)
    if normal in ("", "."):
        normal = "index.html"
    if normal.startswith("../") or normal == "..":
        return "escapes_city", raw
    return "local", normal

def audit_city(root, city):
    folder = root / ("SUPER." + city)
    if not folder.is_dir():
        return {"city":city, "blocked":True, "errors":["missing city folder"]}
    files = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    html = sorted(name for name in files if name.endswith(".html"))
    missing_required = [] if city == "TLV" else [p for p in REQUIRED if p not in files]
    missing_resources = set()
    external_resources = set()
    unresolved_origin_routes = set()
    root_mounts_required = set()
    legacy_canonicals = set()
    escaped_paths = set()
    seen_resources = 0
    redirects = []
    for name in html:
        if name.startswith("assets/branding/") and name.endswith("/super-shell.html"):
            continue  # This is a generator template with {{ROOT}}, not a served page.
        content = (folder/name).read_text(encoding="utf-8", errors="replace")
        if name == "index.html" and REDIRECT.search(content):
            redirects.append(name)
        parser = ResourceParser()
        parser.feed(content)
        resources = list(parser.resources)
        for link in parser.canonicals:
            if urlsplit(link).netloc.lower() in {"isnet.co.il","tlvnet.com"}:
                legacy_canonicals.add(link)
        # CSS may appear inline, and stylesheets may load additional media and fonts.
        for item in resources:
            kind, relative = classify_url(city, name, item)
            if kind == "ignored": continue
            seen_resources += 1
            if kind == "external": external_resources.add((name,relative))
            elif kind == "origin_route_unverified":
                short=urlsplit(relative).path.lstrip("/")
                if short in files: root_mounts_required.add((name,relative))
                else: unresolved_origin_routes.add((name,relative))
            elif kind == "escapes_city": escaped_paths.add((name,relative))
            elif relative not in files:
                missing_resources.add((name,relative))
    for css in sorted(f for f in files if f.endswith(".css")):
        text = (folder/css).read_text(encoding="utf-8",errors="replace")
        for item in CSS_URL.findall(text):
            kind, relative = classify_url(city, css, item)
            if kind == "ignored":continue
            seen_resources += 1
            if kind == "external": external_resources.add((css,relative))
            elif kind == "origin_route_unverified":
                short=urlsplit(relative).path.lstrip("/")
                if short in files: root_mounts_required.add((css,relative))
                else: unresolved_origin_routes.add((css,relative))
            elif kind == "escapes_city": escaped_paths.add((css,relative))
            elif relative not in files: missing_resources.add((css,relative))
    media = sorted(f for f in files if Path(f).suffix.lower() in MEDIA_EXT)
    fonts = sorted(f for f in files if Path(f).suffix.lower() in FONT_EXT)
    return {
        "city":city, "source_file_count":len(files), "html_count":len(html),
        "static_resource_references_checked":seen_resources,
        "missing_required_pages":missing_required,
        "missing_local_static_resources":[list(x) for x in sorted(missing_resources)],
        "external_static_resources":[list(x) for x in sorted(external_resources)],
        "origin_routes_needing_proxy_review":[list(x) for x in sorted(unresolved_origin_routes)],
        "legacy_absolute_canonical_urls":sorted(legacy_canonicals),
        "root_asset_mounts_needing_proxy_mapping":[list(x) for x in sorted(root_mounts_required)],
        "cross_city_path_escapes":[list(x) for x in sorted(escaped_paths)],
        "meta_or_script_redirect_index":bool(redirects),
        "media_file_count":len(media),"font_file_count":len(fonts),
        "media_rights_verified":False,"font_rights_verified":False,
        "browser_acceptance_verified":False,"production_rollback_verified":False,
        "public_cutover_approved":False,
    }

def audit(root):
    cities = [audit_city(root, city) for city in CITIES]
    return {"format":"isnet-super-private-site-readiness-v1",
            "mode":"offline-static-audit-only",
            "no_public_release":True,"no_license_inference":True,
            "cities":cities,
            "summary":{"cities_examined":len(cities),
                       "source_files_total":sum(c.get("source_file_count",0) for c in cities),
                       "html_pages_total":sum(c.get("html_count",0) for c in cities),
                       "missing_local_resources":sum(len(c.get("missing_local_static_resources",[])) for c in cities),
                       "external_references":sum(len(c.get("external_static_resources",[])) for c in cities),
                       "origin_routes_unverified":sum(len(c.get("origin_routes_needing_proxy_review",[])) for c in cities),
                       "root_mounts_to_map":sum(len(c.get("root_asset_mounts_needing_proxy_mapping",[])) for c in cities),
                       "cities_approved_for_cutover":0}}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=audit(args.root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for c in report["cities"]:
        print(f'{c["city"]}: {c.get("html_count",0)} html, {c.get("source_file_count",0)} files, '
              f'{len(c.get("missing_local_static_resources",[]))} missing assets, '
              f'{len(c.get("external_static_resources",[]))} offsite assets, '
              f'{len(c.get("origin_routes_needing_proxy_review",[]))} unresolved root routes, '
              f'{len(c.get("root_asset_mounts_needing_proxy_mapping",[]))} root asset mounts; '
              'CUTOVER BLOCKED')
    print("Report:",args.output)
    if any(c.get("errors") for c in report["cities"]):
        raise SystemExit("Unusable inventory: missing site folder")
if __name__ == "__main__": main()
