"""Match official cinematheque film pages to local screenings, retaining source metadata."""
import concurrent.futures,json,re,unicodedata
from urllib.parse import urljoin
import sync_herzliya_events as c
from bs4 import BeautifulSoup
D=c.D
canonical=lambda s:re.sub(r'\s*\((?:שלישי זהב|ללא תשלום למנויים)\)','',s).strip()
norm=lambda s:re.sub(r'[^א-תa-z0-9]','',unicodedata.normalize('NFKD',s).lower())
def main():
 s=c.get('https://www.hcinema.org.il/');links=sorted({a['href'] for a in s.select('a[href*="/movies/"]')});records=[]
 def one(u):
  try:
   soup=c.get(u);h=soup.find('h1');title=c.clean(h.get_text()) if h else ''
   if not title:return
   paras=[c.clean(p.get_text(' ',strip=True)) for p in soup.select('.jet-listing-dynamic-field__content p, .elementor-widget-text-editor p')]
   paras=[p for p in paras if 30<len(p)<2200 and not re.search('עוגיות|הפרטיות|וואטסאפ|Functional|ניוזלטר',p)]
   text='\n\n'.join(dict.fromkeys(paras))[:1000]
   poster=soup.select_one('meta[property="og:image"]');image=c.photo(urljoin(u,poster['content']),u) if poster else None
   full=' '.join(x.get_text(' ',strip=True) for x in soup.select('.jet-listing-dynamic-field__content'));runtime=re.search(r'(\d{2,3})\s*(?:דק|דקות)',full)
   director=re.search(r'במאית?\s*:\s*([^\n()]{3,70})',full)
   trailer=None
   for node in soup.select('iframe[src],a[href], [data-settings]'):
    val=node.get('src') or node.get('href') or node.get('data-settings','');hit=re.search(r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=))([A-Za-z0-9_-]{11})',val)
    if hit:trailer=hit[1];break
   booking=next((a['href'] for a in soup.select('a[href]') if 'hcinema.smarticket.co.il' in a['href']),None)
   return dict(title=title,source_url=u,text=text,image=image,image_origin_url=poster['content'] if poster else None,runtime_minutes=int(runtime[1]) if runtime else None,director=director[1].strip() if director else None,trailer_youtube_id=trailer,booking_url=booking)
  except Exception:return
 if (D/'film-source-metadata.json').exists() and c.read('film-source-metadata')['checked_at'][:10]==c.NOW.date().isoformat() and any(x.get('text') for x in c.read('film-source-metadata')['films']):records=c.read('film-source-metadata')['films']
 else:
  with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:records=[x for x in ex.map(one,links) if x]
 c.save('film-source-metadata',{'checked_at':c.NOW.isoformat(),'films':records})
 raw=c.read('events')
 for e in raw['events']:
  if e['category']!='cinema':continue
  # Match by exact booking destination before a normalized title with known program suffixes.
  key=norm(canonical(e['title']))
  m=next((m for m in records if m.get('booking_url') and m['booking_url'].rstrip('/')==e['source_url'].split('?')[0].rstrip('/')),None)
  if not m:m=next((m for m in records if norm(canonical(m['title']))==key),None)
  if not m:continue
  if m.get('text'):e['description']=m['text'][:850]
  if m.get('image'):e.update(image=m['image'],image_origin_url=m['image_origin_url'],image_source_url=m['source_url'],image_role='official_promotional',image_credit='תמונת הסרט: סינמטק הרצליה')
  for k in ['runtime_minutes','director','trailer_youtube_id']:
   if m.get(k):e[k]=m[k]
  if m.get('trailer_youtube_id'):e['trailer_source_url']=m['source_url']
 c.save('events',raw)
 print('Official film pages:',len(records),'matched local sessions:',sum(bool(e.get('image_source_url')) for e in raw['events'] if e['category']=='cinema'))
if __name__=='__main__':main()
