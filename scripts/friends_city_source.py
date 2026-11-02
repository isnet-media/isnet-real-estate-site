"""FRIENDS occurrences: require exact city, date, time and venue on detail page."""
import re
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor

def collect(city, get):
 base='https://friends-hist.co.il/';listing=get(base+'city_cat/'+city+'/')
 links=sorted({a['href'] for a in listing.select('a[href*="/show/"]')})
 def one(u):
  try:
   s=get(u);h=s.find('h1');title=h.get_text(' ',strip=True) if h else ''
   rows=[]
   for dt in s.select('.date-time-sec'):
    hit=re.search(r'(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2})',dt.get_text(' ',strip=True))
    if not hit:continue
    box=dt
    for _ in range(4):
     if box.parent:box=box.parent
     # Locality and performance venue must be in this occurrence's container.
     text=box.get_text(' ',strip=True)
     if city in text and len(text)<2500:break
    text=box.get_text(' ',strip=True)
    if city not in text or len(text)>2500:continue
    venue=next((x.get_text(' ',strip=True) for x in box.select('.hall,.hall_name,.place,.hall_wrap') if city in x.get_text()),'')
    if not venue:
     parts=[x.strip() for x in box.stripped_strings];venue=next((v for v in parts if city in v and len(v)>len(city) and len(v)<100),city)
    image=s.select_one('meta[property="og:image"]')
    rows.append(dict(title=title,start_date=datetime.strptime(hit[1],'%d/%m/%y').date().isoformat(),start_time=hit[2],venue=venue,ticket_url=u,purchase_url=u,image_origin_url=image.get('content') if image else None))
   return rows
  except Exception:return []
 with ThreadPoolExecutor(max_workers=5) as ex:return [r for batch in ex.map(one,links) for r in batch]
