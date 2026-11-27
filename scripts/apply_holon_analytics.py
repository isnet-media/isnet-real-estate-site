"""Add the Holon GA4 tag to staged public pages after generators run."""
import re
import sys
from pathlib import Path

TAG = '<script defer src="/assets/holon-ga4.js"></script>'
SCOPES = ('events-preview/holon', 'SUPER.HOLON', 'astrology')

root = Path(sys.argv[1])
for scope in SCOPES:
    pages = [page for page in (root / scope).rglob('*.html')
             if 'assets' not in page.relative_to(root / scope).parts
             and not page.name.startswith('qa-')]
    if not pages:
        raise RuntimeError(f'No public pages found in {scope}')
    for page in pages:
        html = page.read_text(encoding='utf-8')
        html = html.replace(TAG, '')
        head_end = re.search(r'</head\s*>', html, re.IGNORECASE)
        if not head_end:
            # HTML fragments are embedded by their host document.
            continue
        page.write_text(html[:head_end.start()] + TAG + html[head_end.start():], encoding='utf-8')
