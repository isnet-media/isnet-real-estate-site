#!/usr/bin/env python3
"""Refresh verified Cinema City and Planet Rishon sessions; retain a failed source's data."""
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import refresh_ashdod_cinema as c
import planet_rishon_source as planet
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'events-preview/rishon-lezion/data/cinema.json';QA=DATA.with_name('cinema-refresh-status.json')
def main():
 c.CITY_SLUG='rishon-lezion';c.VENUES['cinema-city']='סינמה סיטי ראשל"צ';c.VENUES['planet']='פלאנט ראשון לציון'
 original=json.loads(DATA.read_text());source={}
 try:
  rows=c.collect_city()
  for row in rows:row['source_branch_id']=1173
  with ThreadPoolExecutor(max_workers=4)as pool:
   rows=list(pool.map(c.verify_trailer,rows));rows=list(pool.map(c.verify_poster,rows))
  source['cinema-city']={'status':'ok','movies':rows,'sessions':sum(len(x.get('sessions',[]))for x in rows)}
 except Exception as ex:source['cinema-city']={'status':'failed','error':str(ex)[:300],'movies':[]}
 try:
  rows=planet.collect()
  with ThreadPoolExecutor(max_workers=4)as pool:
   rows=list(pool.map(c.verify_trailer,rows));rows=list(pool.map(planet.verify_poster,rows))
  source['planet']={'status':'ok','movies':rows,'sessions':sum(len(x.get('sessions',[]))for x in rows),'source_url':planet.BRANCH_URL}
 except Exception as ex:source['planet']={'status':'failed','error':str(ex)[:300],'movies':[],'source_url':planet.BRANCH_URL}
 updated,report=c.merge(original,source);updated['city']='ראשון לציון';updated['source_url']=c.CITY+'/city/'+c.CITY_SLUG;updated['source_name']='סינמה סיטי ופלאנט ראשון לציון — הקרנות מאומתות';report['city']='ראשון לציון'
 for movie in updated.get('movies',[]):
  for venue in movie.get('venues',[]):
   if venue.get('id')=='cinema-city':venue['source_branch_id']=1173
 updated['refresh_policy']['schedule_utc']='35 5 * * *'
 updated['stats']['planet_movies']=sum(any(v['id']=='planet'and any(d>=c.TODAY and t for d,t in v.get('schedule',{}).items())for v in m['venues'])for m in updated['movies'])
 DATA.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n');QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='missing'},ensure_ascii=False))
 return 0 if any(s['status']=='ok'for s in source.values())else 2
if __name__=='__main__':raise SystemExit(main())
