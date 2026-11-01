"""Bounded source review for broken FRIENDS images; persist URL proof, not invented media."""
import json,requests,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import re
from bs4 import BeautifulSoup
from event_source_media import friends_image,valid_image
ROOT=Path(__file__).resolve().parents[1]
def run():
 candidates={};day=datetime.now(ZoneInfo('Asia/Jerusalem')).date().isoformat()
 for city in ['ashdod','rishon-lezion']:
  data=json.loads((ROOT/'events-preview'/city/'data/events.json').read_text())
  for e in data['events']:
   u=e.get('content_source_url')or''
   if 'friends-hist.co.il/show/' in u and (e.get('start_date')or'')>=day and (str(e.get('image_url','')).startswith('data:') or e.get('image_source')=='friends'):
    candidates.setdefault(u,e)
 def review(pair):
  u,e=pair
  try:
   r=requests.get(u,timeout=20);r.raise_for_status();q=BeautifulSoup(r.text,'html.parser');h=q.find('h1');image=friends_image(q,u)
   if not h or not image or not valid_image(image):return u,None
   normalized=lambda v:re.sub(r'[^א-תa-z0-9]','',str(v).lower())
   if normalized(h.get_text())!=normalized(e['title']):return u,None
   check=requests.get(image,timeout=15,stream=True);check.raise_for_status();kind=check.headers.get('content-type','');check.close()
   if not kind.startswith('image/') or 'svg' in kind:return u,None
   return u,dict(title=e['title'],source_title=h.get_text(' ',strip=True),checked_at=datetime.now(timezone.utc).isoformat(),source_url=u,fields=dict(image_url=image,image_origin_url=image,thumbnail_url=None,thumbnail_ready=False,image_verified=True,image_publishable=True,image_represents_event=True,source_image_kind='source_event_photo',image_strategy='reviewed_event_main_image',image_credit='צילום: אתר FRIENDS',image_rights_status='publisher_directed_source_reuse'))
  except Exception as ex:return u,None
 repairs={};held=[]
 with ThreadPoolExecutor(max_workers=5) as pool:
  for u,row in pool.map(review,candidates.items()):
   if row:repairs[u]=row
   else:held.append(u)
 target=ROOT/'events-preview/shared/data/event-quality-media.json'
 previous=json.loads(target.read_text()) if target.exists() else {}
 previous.update(checked_at=datetime.now(timezone.utc).isoformat(),repairs={**previous.get('repairs',{}),**repairs},unresolved_sources=held)
 target.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n')
 print('Source images reviewed:',len(repairs),'unresolved:',len(held))
if __name__=='__main__':run()
