"""Attach the Kiryat Gat Net measurement tag to the published event guide."""
from pathlib import Path
import re

GUIDE = Path(__file__).resolve().parents[1] / "events-preview" / "kiryat-gat"
TAG = '<script src="/assets/kgat-events-analytics.js" defer></script>'


def apply_analytics():
    pages = sorted(GUIDE.rglob("*.html"))
    if not (GUIDE / "index.html").is_file():
        raise FileNotFoundError(GUIDE / "index.html")
    for page in pages:
        if "assets" in page.relative_to(GUIDE).parts or page.name.startswith("qa-"):
            continue
        html = page.read_text(encoding="utf-8")
        if TAG in html:
            continue
        updated, matches = re.subn(r"</head>", TAG + "\n</head>", html, count=1, flags=re.I)
        if not matches:
            raise ValueError(f"Missing head in {page}")
        page.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    apply_analytics()
