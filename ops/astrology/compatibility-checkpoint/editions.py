from datetime import date
from html import escape
import json

PERIODS = {"daily": "יומית", "weekly": "שבועית", "monthly": "חודשית"}


def load_editions(path, slugs):
    if not path.exists():
        return {}
    editions = {}
    for edition in json.loads(path.read_text()):
        period = edition["period"]
        start = date.fromisoformat(edition["start"])
        end = date.fromisoformat(edition["end"])
        if period not in PERIODS or end < start or (period == "daily" and start != end):
            raise ValueError(f"Invalid edition period: {period} {start}–{end}")
        if start.isoformat() != edition["start"] or end.isoformat() != edition["end"]:
            raise ValueError("Edition dates must use YYYY-MM-DD")
        entries = edition["entries"]
        if set(entries) != slugs:
            raise ValueError("Every edition must include all 12 signs")
        for paragraphs in entries.values():
            if not isinstance(paragraphs, list) or not paragraphs or any(
                not isinstance(p, str) or not p.strip() for p in paragraphs
            ):
                raise ValueError("Each sign needs a nonempty list of paragraphs")
        key = (period, start)
        if key in editions:
            raise ValueError(f"Duplicate edition: {key}")
        editions[key] = (end, entries)
    return editions


def forecast_html(editions, slug, today, after_daily=""):
    cards = []
    for period, label in PERIODS.items():
        eligible = [(start, end, entries) for (kind, start), (end, entries) in editions.items()
                    if kind == period and start <= today]
        if not eligible:
            continue
        start, end, entries = max(eligible, key=lambda edition: edition[0])
        dates = f'<time datetime="{start}">{start:%d.%m.%Y}</time>'
        if start != end:
            dates += f' עד <time datetime="{end}">{end:%d.%m.%Y}</time>'
        status = " · מהדורה קודמת" if end < today else ""
        paragraphs = "".join(f"<p>{escape(p)}</p>" for p in entries[slug])
        cards.append(f'<article class="edition" id="forecast-{period}"><h2>תחזית {label}</h2>'
                     f'<p class="facts">{dates}{status}</p>{paragraphs}</article>')
        if period == "daily":
            cards.append(after_daily)
    return "".join(cards)
