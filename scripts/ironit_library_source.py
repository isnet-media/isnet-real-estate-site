"""Read the library's public cards and published series dates; never publish or mutate storage."""
import copy,re
from datetime import datetime
from urllib.parse import urljoin,urlparse,parse_qs
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
from sync_events_from_sources import HEBREW_DATE,iso_hebrew,HOUR

def explicit_dates(body,year):
    result=set()
    for match in re.finditer(r'(?<!\d)(\d{1,2})[/.](\d{1,2})(?:[/.](\d{4}|\d{2}))?(?![\d/])',body):
        day,month,yr=match.groups();yr=int(yr) if yr else year
        if yr<100:yr+=2000
        try:result.add(datetime(yr,int(month),int(day)).date().isoformat())
        except ValueError:pass
    return sorted(result)

def collect_library(name,spec,page,make,localize,card,future):
    origins=[(spec['url'],page(spec['url']))];issues=[];out=[];seen=set();details=[]
    for a in origins[0][1].select('a[href]'):
        u=urljoin(spec['url'],a['href'])
        if '/type/' in u and 'related_types_term=' in u and 'מופעים' in a.get_text():
            try:origins.append((u,page(u)))
            except Exception as ex:issues.append({'url':u,'error':str(ex)[:200]})
    links=sorted({urljoin(origin,a['href']) for origin,p in origins for a in p.select('a[href]') if '/events/' in a['href']})
    if not links:raise ValueError('Library event cards unavailable; retain existing records')
    for u in links:
        try:
            q=page(u);content=q.select_one('.event-single .content') or q.select_one('main')
            cal=next((a['href'] for a in content.select('a[href]') if 'outlook.live.com/calendar/' in a['href']),None)
            if not cal:issues.append({'url':u,'error':'No verified calendar date/hour'});continue
            params=parse_qs(urlparse(cal).query);start=params.get('startdt',[''])[0]
            if not start:continue
            dt=datetime.fromisoformat(start)
            if dt.tzinfo:dt=dt.astimezone(ZoneInfo('Asia/Jerusalem'))
            body=BeautifulSoup(params.get('body',[''])[0],'html.parser').get_text('\n',strip=True)
            heading=content.select_one('h1');title=heading.get_text(' ',strip=True)
            subtitle=content.select_one('h2')
            if subtitle:title+=' - '+subtitle.get_text(' ',strip=True)
            ages=[a.get_text(' ',strip=True) for a in content.select('a[href]') if '/age/' in a['href']]
            kids=any(a in ('עד 5','6-12') for a in ages)
            buy=next((urljoin(u,a['href'].strip()) for a in content.select('a[href]') if 'smarticket.co.il' in a['href']),None)
            if buy:buy=buy.replace('/iframe/','/')
            image=q.select_one('meta[property="og:image"]');img=urljoin(u,image.get('content','')) if image else None
            base=make(name,title,dt.date().isoformat(),dt.strftime('%H:%M'),params.get('location',[''])[0],u,body,img)
            dates=explicit_dates(body,dt.year)
            # Only a clearly published series list may add separate occurrences.
            if not re.search(r'מועדי המפגשים|בתאריכים',body):dates=[]
            dates=sorted(set(dates+[dt.date().isoformat()]))
            rows=[]
            if buy:
                try:
                    seller=page(buy);base_tag=seller.select_one('base[href]')
                    seller_base=base_tag['href'] if base_tag else buy
                    seller_title=seller.select_one('h1')
                    for tr in seller.select('tr'):
                        cells=tr.select('td');label=cells[0].get_text(' ',strip=True) if cells else ''
                        date=HEBREW_DATE.search(label);time=HOUR.search(label)
                        a=cells[0].select_one('a[href]') if cells else None
                        if not date or not time or not a:continue
                        href=urljoin(seller_base,a['href']).replace('/iframe/','/');day=iso_hebrew(date)
                        if any(e['start_date']==day and e['start_time']==time.group(0) for e in rows):continue
                        row={'title':seller_title.get_text(' ',strip=True) if seller_title else title,'start_date':day,'start_time':time.group(0),'venue':cells[1].get_text(' ',strip=True) if len(cells)>1 else base['venue'],'ticket_url':href}
                        if future(row):rows.append(card(row,name))
                except Exception as ex:
                    issues.append({'url':buy,'error':str(ex)[:200]})
                    buy=None
            if kids and rows:
                # The seller's individual occurrence links outrank a series-start calendar export.
                pass
            else:
                covered={(e['start_date'],e['start_time']) for e in rows}
                for day in dates:
                    if (day,base['start_time']) in covered:continue
                    e=copy.deepcopy(base);e['start_date']=day
                    if buy:e['purchase_url']=e['ticket_url']=buy
                    if len(dates)>1:e['purchase_scope']='series'
                    if future(e):rows.append(localize(e,name))
            details.append({'url':u,'title':title,'kids':kids,'dates':dates,'verified_future_occurrences':len(rows)})
            for e in rows:
                e['source_listing_url']=spec['url'];e['library_program']='kids' if kids else 'adults'
                e.setdefault('crosscheck_sources',[])
                if u not in e['crosscheck_sources']:e['crosscheck_sources'].append(u)
                e['audiences']=list(dict.fromkeys(e.get('audiences',[])+(['kids','families'] if kids else ['adults']+(['seniors'] if '60+' in ages else []))))
                if kids:e.update(category='kids',subcategory='creative-workshops' if 'סדנ' in title else 'kids-shows')
                elif 'מועדון קריאה' in title:e.update(category='workshop',subcategory='reading-clubs')
                elif 'סדנ' in title:e.update(category='workshop',subcategory='creative')
                summary=None
                if not kids and 'מועדון קריאה' in title and 'איריס ארגמן' in title:
                    summary='מפגשי קריאה למבוגרים בהנחיית הסופרת איריס ארגמן, עם דיון בסיפורים קצרים, בנובלות, ברומנים ובשירה. בכל מפגש מתבוננים ביצירה גם דרך ההקשר ההיסטורי והאמנותי שלה. הסדרה מתקיימת אחת לחודש בספרייה העירונית.'
                elif not kids and 'מועדון קריאה' in title and 'שרית חיים' in title:
                    summary='מועדון קריאה למבוגרים בהנחיית הסופרת שרית חיים, המוקדש לספרות רומנטית. המשתתפים משוחחים על העלילה והדמויות, על תפניות בסיפור ועל חוויית הקריאה. המפגשים מתקיימים אחת לחודש בספרייה העירונית.'
                elif not kids and 'כותבים אהבה' in title:
                    summary='סדנת כתיבה רומנטית למבוגרים בהנחיית הסופרת שרית חיים. בארבעת מפגשי הסדרה עובדים על בניית עלילה וקונפליקטים, יצירת נקודות מפנה, עריכת הטקסט והצעדים לקראת פרסום ספר. הפעילות מתקיימת בספרייה העירונית.'
                if summary:
                    e['description']=e['series_description']=e['source_description']=summary
                    e['synopsis_editorial']=True;e['series_dates']=dates
                e['official_age_groups']=ages
                key=(e.get('event_id'),e['start_date'],e['start_time'])
                if future(e) and key not in seen:out.append(e);seen.add(key)
        except Exception as ex:issues.append({'url':u,'error':str(ex)[:200]})
    collect_library.last_details=details
    return out,issues,[]
