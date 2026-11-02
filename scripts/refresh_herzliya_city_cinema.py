"""Official Glilot branch schedules for the Herzliya-area cinema edition."""
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import refresh_ashdod_cinema as c
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'events-preview/herzliya/data'
def main():
 c.CACHE=Path('/tmp/isnet-glilot-source-cache');c.CITY_SLUG='glilot';c.VENUES['cinema-city']='סינמה סיטי גלילות'
 try:
  rows=[r for r in c.collect_city() if r.get('sessions')]
  for row in rows:row['schedule']={day:sorted(times) for day,times in row['schedule'].items()}
  (D/'cinema-city-glilot.json').write_text(json.dumps({'status':'ok','checked_at':c.STAMP,'source_url':c.CITY+'/city/glilot','venue_name':'סינמה סיטי גלילות — סמוך להרצליה','movies':rows},ensure_ascii=False,indent=2)+'\n')
  print('Official Glilot snapshot',len(rows),'films',sum(len(r['sessions']) for r in rows),'sessions',flush=True)
  # Branch ID is verified in collect_city against every official session payload.
  with ThreadPoolExecutor(max_workers=6) as pool:
   rows=list(pool.map(c.verify_poster,rows));rows=list(pool.map(c.verify_trailer,rows))
  source={'status':'ok','checked_at':c.STAMP,'source_url':c.CITY+'/city/glilot','venue_name':'סינמה סיטי גלילות — סמוך להרצליה','movies':rows}
  (D/'cinema-city-glilot.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
  (D/'cinema-city-glilot-status.json').write_text(json.dumps({'status':'ok','checked_at':c.STAMP,'films':len(rows),'sessions':sum(len(r['sessions']) for r in rows)},ensure_ascii=False,indent=2)+'\n')
  print('Verified Glilot films',len(rows),'sessions',sum(len(r['sessions']) for r in rows))
 except Exception as ex:
  (D/'cinema-city-glilot-status.json').write_text(json.dumps({'status':'failed','checked_at':c.STAMP,'error':str(ex)[:300]},ensure_ascii=False,indent=2)+'\n')
  print('GLILOT_SOURCE_UNAVAILABLE',str(ex)[:200]);return 2
 return 0

def merge_into(data):
 p=D/'cinema-city-glilot.json'
 if not p.exists():return data
 source=json.loads(p.read_text());c.STAMP=source['checked_at'];c.CITY_SLUG='glilot';c.VENUES['cinema-city']='סינמה סיטי גלילות — סמוך להרצליה'
 merged,_=c.merge(data,{'cinema-city':source})
 merged['city']='הרצליה';merged['source_name']='סינמטק הרצליה וסינמה סיטי גלילות';merged['source_url']='https://isnet.co.il/events-preview/herzliya/cinema.html'
 for m in merged['movies']:
  for v in m['venues']:
   if v['id']=='cinema-city':v.pop('source_branch_id',None);v['locality']='גלילות, רמת השרון';v['nearby_city']=True
 return merged
if __name__=='__main__':raise SystemExit(main())
