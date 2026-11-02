"""Cache verified official cinema poster thumbnails on the same origin as the guide."""
import concurrent.futures,hashlib,io,json
from pathlib import Path
import requests
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'events-preview/herzliya';D=CITY/'data';OUT=CITY/'assets/cinema-covers'
def main():
 data=json.loads((D/'cinema.json').read_text());OUT.mkdir(parents=True,exist_ok=True)
 urls={m['poster_url'] for m in data['movies'] if str(m.get('poster_url','')).startswith('https://') and m.get('poster_verification',{}).get('url')==m.get('poster_url')}
 old=json.loads((D/'cinema-poster-cache.json').read_text()) if (D/'cinema-poster-cache.json').exists() else {}
 def cache(url):
  name=hashlib.sha256(url.encode()).hexdigest()[:20]+'.jpg';target=OUT/name
  try:
   if not target.exists():
    r=requests.get(url,timeout=20);r.raise_for_status();im=Image.open(io.BytesIO(r.content)).convert('RGB');im.thumbnail((480,720));im.save(target,'JPEG',quality=80,optimize=True)
   return url,dict(path='/events-preview/herzliya/assets/cinema-covers/'+name,bytes=target.stat().st_size,source_url=url)
  except Exception:return url,old.get(url)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:records={u:v for u,v in ex.map(cache,urls) if v}
 (D/'cinema-poster-cache.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print('Same-origin poster thumbnails',len(records),'bytes',sum(v['bytes'] for v in records.values()))
if __name__=='__main__':main()
