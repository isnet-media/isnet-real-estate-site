#!/usr/bin/env python3
"""Cache actual business gallery/menu photos, excluding directory branding."""
import json,sys,io,re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'events-preview/yavne';DATA=CITY/'data/restaurants.json'
def enrich(p):
 if p.get('image') and '/shared/' not in p['image']:return p
 try:
  r=requests.get(p['source_url'],timeout=12);r.raise_for_status();soup=BeautifulSoup(r.content,'html.parser');candidates=[]
  for im in soup.select('img[src]'):
   u=urljoin(r.url,im['src']);alt=im.get('alt','')
   if 'תמונה של ' in alt and 'media.easy.co.il/images/UserThumbs/' in u:candidates.append(u)

  for u in dict.fromkeys(candidates):
   try:
    r=requests.get(u,timeout=10);r.raise_for_status();im=ImageOps.exif_transpose(Image.open(io.BytesIO(r.content))).convert('RGB')
    if min(im.size)<180:continue
    im.thumbnail((1000,800));dest=CITY/'assets/restaurants'/('photo-'+p['id']+'.webp');dest.parent.mkdir(parents=True,exist_ok=True);im.save(dest,'WEBP',quality=84)
    p.update(image=str(dest.relative_to(CITY)),credit='תמונת העסק / איזי' if 'media.easy.co.il' in u else 'צילום מנה מתפריט המקום',original_image_url=u,image_source_url=p['source_url']);print('PHOTO',p['name'],flush=True);break
   except Exception:continue
 except Exception as ex:print('NO PHOTO',p['name'],str(ex)[:60],flush=True)
 return p
if __name__=='__main__':
 data=json.loads(DATA.read_text())
 with ThreadPoolExecutor(max_workers=8) as pool:data['restaurants']=list(pool.map(enrich,data['restaurants']))
 DATA.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print('PHOTOS',sum(bool(p.get('image')) for p in data['restaurants']),flush=True)
