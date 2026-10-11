#!/usr/bin/env python3
"""Audit Ashdod cinema trailer coverage. Non-zero exit if any active film lacks an embed."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
data=json.loads(Path("events-preview/ashdod/data/cinema.json").read_text(encoding="utf-8"))
today=datetime.now(ZoneInfo("Asia/Jerusalem")).date().isoformat()
active=[]
for movie in data.get("movies",[]):
 if any(any(day>=today and times for day,times in (venue.get("schedule") or {}).items()) for venue in movie.get("venues",[])):
  active.append(movie)
missing=[{"id":m["id"],"title":m.get("title"),"official_trailer_page":m.get("trailer_page_url")} for m in active if not m.get("trailer_youtube_id")]
report={"date":today,"active_movies":len(active),"embedded_trailers":len(active)-len(missing),"missing_embeds":missing,"complete":not missing and bool(active)}
Path("cinema-trailer-coverage.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
if not report["complete"]:
 print("::error title=Incomplete cinema trailers::Do not call this a complete automatic import.")
 raise SystemExit(1)
