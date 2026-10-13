"""Apply reviewed Ashdod event classifications only; no network or publication."""
import html,json
from pathlib import Path
def apply_ashdod_category_overrides(events,root):
 path=Path(root)/'events-preview/ashdod/data/category-overrides.json'
 if not path.is_file():return 0
 catalog=json.loads(path.read_text())
 rules={html.unescape(r['title']).strip():r for r in catalog['rules']}
 count=0
 for event in events:
  audience_text=' '.join(str(event.get(k) or '') for k in ('title','organizer','organizer_name'))
  senior_audience=event.get('audience_program')=='gdolot_hachaim' or event.get('local_source_name')=='gdolot_hachaim' or any(x in audience_text for x in ('גדולות מהחיים','אזרחים ותיקים','אזרחים וותיקים'))
  if senior_audience:
   title=str(event.get('title') or '')
   if any(x in title for x in ('פילאטיס','ספורט על כיסא','בודי בלט','בונה עצם')):sub='senior-sport'
   elif 'יריד בריאות' in title:sub='senior-health'
   elif 'ריקוד' in title:sub='senior-dance'
   elif any(x in title for x in ('קנווה','קאנבה','קנבה','בנייד','דיגיטל')):sub='senior-digital'
   elif event.get('category')=='lecture' or any(x in title for x in ('נמרולוג','פאנל','כח המילים','כוח המילים')):sub='senior-lectures'
   elif 'פסטיבל ילד פלא' in title or title.strip()=='גדולות מהחיים':sub='senior-culture'
   elif event.get('category')=='seniors':sub=event.get('subcategory') or 'senior-social'
   else:sub='senior-workshops'
   event.update(category='seniors',subcategory=sub);count+=1
  elif event.get('category')=='sport' and any(x in str(event.get('title') or '') for x in ('פילאטיס','שיעור סאפ','קבוצת גלישה','קבוצת הורה ילד')):
   parent='הורה ילד' in str(event.get('title') or '')
   event.update(category='kids' if parent else 'workshop',subcategory='kids-activities' if parent else 'movement');count+=1
  elif event.get('category')=='tour':
   event.update(category='seniors',subcategory='senior-trips');count+=1
  else:
   rule=rules.get(html.unescape(str(event.get('title') or '')).strip())
   if rule and (rule.get('all_categories') is True or event.get('category')=='community'):
    event.update(category=rule['category'],subcategory=rule['subcategory']);count+=1
 return count
