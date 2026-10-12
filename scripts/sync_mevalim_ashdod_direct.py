#!/usr/bin/env python3
"""Publish every Ashdod occurrence sold by Mevalim, without editorial gating."""
import argparse, hashlib, json, re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urljoin
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
URL='https://www.mevalim.co.il/ashdod/'
HEAD={'User-Agent':'ISNET-Ashdod-Mevalim/1.0'}
MAP={'הצגות ילדים':('kids','kids-theatre'),'סטנדאפ':('standup','standup'),'הצגות תיאטרון':('theatre','theatre'),'תיאטרון':('theatre','theatre'),'מחזות זמר,תיאטרון':('theatre','musical'),'הופעות חיות':('music','live'),'מחזות זמר':('theatre','musical'),'מחול ובלט':('music','dance'),'קונצרטים':('music','concert'),'הרצאות':('lecture','lecture'),'סרטים':('cinema','film')}
def clean(x): return re.sub(r'\s+',' ',str(x or '')).strip()
def norm(x): return re.sub(r'[^\w\u0590-\u05ff]','',clean(x).lower())
def venue_key(value):
    n=norm(value)
    if 'דרךארץ8' in n:return 'מונארט'
    for key in ['ידלבנים','משכן','דיונה','מונארט','נאפו','הוטסינמה','סינמהסיטי']:
        if key in n:return key
    return n
def same_show(old,new):
    if old.get('start_date')!=new['start_date'] or str(old.get('start_time') or '')[:5]!=new['start_time']:return False
    if not venue_key(old.get('venue')) or venue_key(old.get('venue'))!=venue_key(new['venue']):return False
    a=clean(old.get('title')).replace('באשדוד','').replace('אימי הגנרלית','אמי הגנרלית')
    b=clean(new['title'])
    ac=norm(re.split(r'\s[-–|]\s',a)[0]);bc=norm(re.split(r'\s[-–|]\s',b)[0])
    return (len(ac)>=5 and ac in norm(b)) or (len(bc)>=5 and bc in norm(a))

OTHER_CITIES=('פתח תקווה','פתח תקוה','תל אביב','ראשון לציון','ירושלים','חיפה','באר שבע','נתניה','הרצליה','רמת גן','גבעתיים','חולון','בת ים','רחובות','יבנה','אשקלון','קרית גת','קריית גת','רעננה','כפר סבא','הוד השרון','מודיעין','נס ציונה','אילת')
def remove_conflicting_address(text):
    removed=[]
    def replace(match):
        line=match.group(0)
        if 'אשדוד' not in line and any(city in line for city in OTHER_CITIES):
            removed.append(clean(line));return ''
        return line
    value=re.sub(r'כתובת\\s*[:：]\\s*[^\\n]+',replace,text or '')
    value=re.sub(r'חשוב לדעת\\s*(?=אודות האירוע)','',value)
    return value.strip(),removed

def get(url):
    r=requests.get(url,headers=HEAD,timeout=45);r.raise_for_status();return BeautifulSoup(r.text,'html.parser')
def collect_row(row,stamp):
    title=row.get('data-mvlm-event-name') or clean(row.select_one('.rgbcode_table_shortcode_table_event_name').get_text())
    raw=row.get('data-mvlm-event-category') or ''
    date=row.get('data-mvlm-event-date')
    dt=datetime.strptime(date,'%d.%m.%y %H:%M')
    venue=clean(row.select_one('.rgbcode_table_shortcode_table_venue').get_text(' ',strip=True))
    a=row.select_one('a[href]');url=row.get('data-mvlm-event-link-target') or (a.get('href') if a else '')
    uid=row.get('data-mvlm-event-id') or hashlib.sha256((title+date+venue).encode()).hexdigest()[:16]
    category,sub=MAP.get(raw,('other','mevalim-'+hashlib.sha256(raw.encode()).hexdigest()[:10]))
    e={'event_id':'mevalim_as_'+uid,'source':'mevalim_direct','source_event_id':uid,'city':'אשדוד','title':title,'category':category,'subcategory':sub,'source_category':raw,'source_subcategory':raw,'start_date':dt.date().isoformat(),'start_time':dt.strftime('%H:%M'),'venue':venue,'status':'active','ticket_url':url,'purchase_url':url,'content_source_url':url,'last_imported_at':stamp,'description':'','series_description':'','image_url':None,'image_publishable':False,'source_priority':1,'source_content_authoritative':True,'taxonomy_review_required':raw not in MAP,'internal_notes':[]}
    if raw not in MAP:e['internal_notes']=['נפתחה קטגוריה/תת קטגוריה חדשה ממבלים: '+(raw or 'לא זוהתה קטגוריה במקור')]
    price=re.search(r'₪\s*(\d+(?:\.\d+)?)',a.get_text(' ',strip=True) if a else '')
    if price:e['price_min_ils']=float(price.group(1))
    if 'אזלו' in row.get_text():e['ticket_status']='sold_out'
    issues=[]
    if urlparse(url).hostname!='tickets.mevalim.co.il':
        issues.append('no_purchase_detail_link');return e,issues
    try:
        p=get(url)
        sections=[]
        for label in ['חשוב לדעת','אודות האירוע']:
            h=next((h for h in p.select('h2,h3') if clean(h.get_text())==label),None)
            if h:
                block=h.find_parent('section')
                if block:
                    for control in block.select('button,iframe,svg,[role="dialog"]'):control.decompose()
                    sections.append(block.get_text('\n',strip=True).split('טריילר האירוע')[0].strip())
        text='\n\n'.join(dict.fromkeys(sections));e['description']=e['series_description']=text
        if not text:issues.append('detail_description_missing')
        img=p.find('meta',property='og:image')
        image=None
        i=next((i for i in p.select('img[src]') if '/_next/image?' in i['src']),None)
        if i:image=parse_qs(urlparse(i['src']).query).get('url',[None])[0]
        if not image:image=img.get('content') if img else None
        if image:
            e.update(image_url=urljoin(url,image),image_origin_url=urljoin(url,image),image_source='mevalim_direct',image_verified=True,image_publishable=True,image_represents_event=True,image_strategy='official_source_event_image',image_rights_status='publisher_directed_source_reuse',image_verified_at=stamp)
        else:issues.append('detail_image_missing')
        credit=re.search(r'קרדיט תמונה:\s*([^\n]+)',text)
        if credit:e['image_credit']=credit.group(1)
        duration=re.search(r'משך[^\n]*',text)
        if duration:e['source_duration_text']=duration.group()
        ages=re.search(r'מומלץ לגילאים[^\n]*',text)
        if ages:e['source_age_text']=ages.group()
        e['details_verified']=bool(text or image);e['detail_checked_at']=stamp
    except Exception as ex:issues.append(type(ex).__name__+': '+str(ex)[:150])
    return e,issues
def merge(data,new):
    keys={(norm(e['title']),e['start_date'],e['start_time']) for e in new}
    urls={urlparse(e['ticket_url']).path for e in new if urlparse(e.get('ticket_url','')).hostname=='tickets.mevalim.co.il'}
    kept=[];removed=[]
    for e in data['events']:
        link=e.get('ticket_url') or e.get('purchase_url') or e.get('content_source_url') or ''
        key=(norm(e.get('title')),e.get('start_date'),str(e.get('start_time') or '')[:5])
        match=key in keys or (urlparse(link).hostname=='tickets.mevalim.co.il' and urlparse(link).path in urls) or any(same_show(e,n) for n in new)
        if match:removed.append(e)
        else:kept.append(e)
    data['events']=kept+new;data.setdefault('stats',{})['events']=len(data['events'])
    return removed
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--collect-only',action='store_true');ap.add_argument('--snapshot');args=ap.parse_args()
    stamp=datetime.now(ZoneInfo('Asia/Jerusalem')).isoformat()
    if args.snapshot:
        snap=json.loads(Path(args.snapshot).read_text());new=snap['events'];issues=snap['issues']
    else:
        p=get(URL);table=p.select('table')[0];rows=table.select('tr')
        # A failed or materially incomplete listing must not replace the published dataset.
        assert rows,'Empty source listing'
        with ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(lambda row:collect_row(row,stamp),rows))
        new=[e for e,i in result];issues=[{'event_id':e['event_id'],'title':e['title'],'issues':i} for e,i in result if i]
    # An incomplete detail response must not erase a previously read source card.
    complete=ROOT/'events-preview/admin/data/mevalim-ashdod-last-complete.json'
    prior={e['event_id']:e for e in json.loads(complete.read_text()).get('events',[])} if complete.exists() else {}
    preserved=0
    for e in new:
        old=prior.get(e['event_id'],{})
        if not e.get('description') and old.get('description'):
            e['description']=old['description'];e['series_description']=old['series_description'];e['source_detail_incomplete']=True;preserved+=1
        if not e.get('image_url') and old.get('image_url'):
            for key in ['image_url','image_origin_url','image_source','image_verified','image_publishable','image_represents_event','image_strategy','image_rights_status','image_verified_at','image_credit']:
                if key in old:e[key]=old[key]
        if e.get('source_detail_incomplete'):
            e['details_verified']=old.get('details_verified',False);e['detail_checked_at']=old.get('detail_checked_at')
    for e in new:
        text,removed_addresses=remove_conflicting_address(e.get('description'))
        e['description']=e['series_description']=text
        if removed_addresses:
            e.setdefault('internal_notes',[]).append('הוסרה כתובת של עיר אחרת מהתיאור; מקום האירוע נשמר לפי הפניית הרכישה: '+e['venue'])
            e['removed_conflicting_source_addresses']=removed_addresses
    out=ROOT/'events-preview/admin/data/mevalim-ashdod-direct-snapshot.json'
    out.write_text(json.dumps({'at':stamp,'source':URL,'events':new,'issues':issues},ensure_ascii=False,indent=2)+'\n')
    if not preserved and sum(bool(e.get('description') and e.get('image_url')) for e in new)>=len(new)-1:
        complete.write_text(out.read_text())
    removed=[]
    if not args.collect_only:
        path=ROOT/'events-preview/ashdod/data/events.json';data=json.loads(path.read_text());removed=merge(data,new);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        backup=ROOT/'events-preview/admin/data/mevalim-ashdod-replaced-events.json';backup.write_text(json.dumps({'at':stamp,'events':removed},ensure_ascii=False,indent=2)+'\n')
        path=ROOT/'events-preview/admin/data/taxonomy.json';tax=json.loads(path.read_text())
        categories=[]
        for raw in sorted({e['source_category'] for e in new}):
            example=next(e for e in new if e['source_category']==raw)
            categories.append({'id':example['subcategory'],'label':raw or 'ללא קטגוריה במקור','suggested_category':example['category'],'requires_mapping':example['taxonomy_review_required'],'note':'נפתחה קטגוריה/תת קטגוריה חדשה; נדרש שיוך ידני' if example['taxonomy_review_required'] else ''})
        tax.setdefault('source_taxonomies',{})['mevalim_direct']={'label':'מבלים – אשדוד, רכישה ישירה','categories':categories}
        for e in new:
            cat=next((c for c in tax['primary_categories'] if c['id']==e['category']),None)
            if cat is None:
                cat={'id':e['category'],'label':'מקורות – ממתין לשיוך','subcategories':[]};tax['primary_categories'].append(cat)
            if not any(s['id']==e['subcategory'] for s in cat.get('subcategories',[])):
                cat.setdefault('subcategories',[]).append({'id':e['subcategory'],'label':e['source_category'] or 'לא סווג במקור','requires_mapping':True})
        path.write_text(json.dumps(tax,ensure_ascii=False,indent=2)+'\n')
    report={'at':stamp,'occurrences':len(new),'descriptions':sum(bool(e['description']) for e in new),'images':sum(bool(e['image_url']) for e in new),'preserved_source_cards':preserved,'replaced':len(removed),'issues':issues,'published_to_dataset':not args.collect_only}
    (ROOT/'events-preview/admin/data/mevalim-ashdod-direct-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='issues'},ensure_ascii=False))
if __name__=='__main__':main()
